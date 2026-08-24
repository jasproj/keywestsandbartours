#!/usr/bin/env python3
"""D-574 — sweep every rendered spelling of a stale charter ceiling figure.

DETERMINISTIC (D-581). No network. Reports before it writes, and by default
writes nothing.

A price published in one place is published in seven, so this looks in all of
them: <title>, meta description, og:/twitter: description, h1, hero stat,
JSON-LD (ItemList / Offer / AggregateOffer / FAQPage answers), offer cards,
tour cards, price badges, tables, headings and accordion bodies. Four spellings
of every figure are searched ($2,195 / $2195 / 2,195 / 2195) because the same
number is written differently in a meta tag and in JSON-LD.

WHAT IT WILL NOT DO — the reason this is not a global find/replace
  The ceiling figure is frequently CORRECT where it appears. These pages publish
  the whole ladder: key-west-fishing-charter.html carries $1,395 / $1,595 /
  $1,795 as three offer cards, each next to the duration it buys, under a
  "from $1,395" title. $1,795 there is the Full-Day price sitting beside the
  words "Full-Day Charter" — true, and blanket-replacing it would publish a lie.
  Likewise sunset-cruises.html renders "whole boat · ARIA $1,200 or ZODIAC
  $2,200"; the $2,200 is the named 60ft boat, not this row's from-price.

  So an occurrence is replaced only when BOTH hold:
    1. it is inside a region owned by a class (b) pk (nearest enclosing
       items/<pk> reference), or in a page-level slot on a page whose primary
       product is that pk; AND
    2. no QUALIFIER naming a different ladder tier or vessel appears within the
       occurrence's element or its adjacent sibling text.
  Every occurrence is reported with the rule that fired, kept or skipped.

SELF-TEST (--self-test)
  Plants a known stale figure into a temp copy of a real page, in a slot that
  must be caught, and asserts it is caught; then asserts the page's genuine
  from-price figure is NOT flagged. A detector that cannot fail is not a
  detector, so this runs before any real sweep.
"""
import argparse, json, re, shutil, sys, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# pk -> {stale ceiling, correct floor, and the qualifiers that make the stale
#        figure CORRECT where it appears}
#
# TWO KINDS OF QUALIFIER, because they behave differently:
#   nearQualifiers — a ladder-tier name ("Full-Day Charter", "10 Hour"). It only
#     licenses the figure when it sits beside it, so it is searched in the
#     element plus a sibling window. These pages print the WHOLE ladder, so a
#     page-wide test would suppress every genuine catch: key-west-fishing-
#     charter.html says "Full-Day" in an offer card while its hero stat must
#     still read the $1,395 floor.
#   pageQualifiers — a VESSEL name ("ZODIAC"). Naming the boat is a statement
#     about which product is being sold, and it holds for the whole page. A page
#     that says "Private charter aboard ZODIAC" is quoting the 60ft boat
#     everywhere on it, including in prose that divides that figure per head.
#     Rewriting the number without rewriting the boat and the arithmetic would
#     publish a worse page, so these are reported and held, never swept.
TARGETS = {
    532140: {"stale": 2195, "floor": 1395, "near": ["10 Hour", "10-Hour", "Ten Hour"], "page": []},
    554262: {"stale": 1895, "floor": 1395, "near": ["10 Hour", "10-Hour", "Ten Hour"], "page": []},
    563185: {"stale": 1670, "floor": 1295, "near": ["10 Hour", "10-Hour", "Ten Hour"], "page": []},
    541394: {"stale": 1795, "floor": 1395, "near": ["Full-Day", "Full Day", "8 hour", "8 Hour", "Eight Hour"], "page": []},
    105623: {"stale": 2200, "floor": 1200, "near": [], "page": ["ZODIAC", "Zodiac"]},
    105610: {"stale": 2400, "floor": 1400, "near": [], "page": ["ZODIAC", "Zodiac"]},
    113331: {"stale": 2800, "floor": 1800, "near": [], "page": ["ZODIAC", "Zodiac"]},
    105631: {"stale": 6200, "floor": 5200, "near": [], "page": ["ZODIAC", "Zodiac"]},
    105635: {"stale": 6200, "floor": 5200, "near": [], "page": ["ZODIAC", "Zodiac"]},
    105639: {"stale": 6200, "floor": 5200, "near": [], "page": ["ZODIAC", "Zodiac"]},
    # (d) duration-matched rows. `floor` here is the tier the row's durationText
    # names, not the ladder floor — the sweep only ever maps a stale figure to
    # the value now stored, so the key keeps its name. Neither pk is referenced
    # on any page today; both are listed so a future render cannot ship the
    # stale ceiling unnoticed.
    104492: {"stale": 1950, "floor": 1750, "near": ["12 Hour", "12-Hour", "Twelve Hour"], "page": []},
    635625: {"stale": 1270, "floor": 1040, "near": ["8 Hour", "8-Hour", "Eight Hour"], "page": []},
}

# Sibling window around a price element in which a nearQualifier still counts.
# An offer-card prints its duration ~40 chars after the price; a tour-card-meta
# trails its price by ~300; a lead paragraph can precede it by ~300.
NEAR_BEFORE, NEAR_AFTER = 320, 330

# Element-level patterns. Each captures the figure so the replacement is scoped
# to one element, never to the raw page text.
PRICE_ELEMENTS = [
    ("json-ld",        re.compile(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>.*?</script>', re.S | re.I)),
    ("title",          re.compile(r'<title>.*?</title>', re.S | re.I)),
    ("meta",           re.compile(r'<meta[^>]*(?:name|property)=["\'](?:description|og:description|og:title|twitter:description|twitter:title)["\'][^>]*>', re.I)),
    ("h1",             re.compile(r'<h1[^>]*>.*?</h1>', re.S | re.I)),
    ("h2",             re.compile(r'<h2[^>]*>.*?</h2>', re.S | re.I)),
    ("h3",             re.compile(r'<h3[^>]*>.*?</h3>', re.S | re.I)),
    ("hero-stat",      re.compile(r'<span class="hero-stat-value">.*?</span>', re.S | re.I)),
    ("offer-price",    re.compile(r'<div class="offer-price">.*?</div>', re.S | re.I)),
    ("tour-card-price", re.compile(r'<span class="tour-card-price">.*?</span>', re.S | re.I)),
    ("tour-price",     re.compile(r'<p class="tour-price">.*?</p>', re.S | re.I)),
    ("card-meta",      re.compile(r'<div class="tour-card-meta">.*?</div>', re.S | re.I)),
    ("table-cell",     re.compile(r'<td[^>]*>.*?</td>', re.S | re.I)),
    ("accordion",      re.compile(r'<(?:details|summary|dd|dt)[^>]*>.*?</(?:details|summary|dd|dt)>', re.S | re.I)),
    ("paragraph",      re.compile(r'<p[^>]*>.*?</p>', re.S | re.I)),
    ("list-item",      re.compile(r'<li[^>]*>.*?</li>', re.S | re.I)),
]


def spellings(n):
    """Every way this repo writes the same integer price."""
    return sorted({f"${n:,}", f"${n}", f"{n:,}", f"{n}"}, key=len, reverse=True)


def figure_re(n):
    """Element-level regex: the figure not glued to other digits."""
    alts = "|".join(re.escape(s) for s in spellings(n))
    return re.compile(r'(?<![0-9.,])(' + alts + r')(?![0-9])')


def owning_pk(text, pos, pks):
    """Nearest items/<pk> reference around pos, searching outward."""
    window = 2600
    lo, hi = max(0, pos - window), min(len(text), pos + window)
    best, bestd = None, None
    for pk in pks:
        for m in re.finditer(r'items/' + str(pk) + r'(?![0-9])', text[lo:hi]):
            d = abs((lo + m.start()) - pos)
            if bestd is None or d < bestd:
                best, bestd = pk, d
    return best


def scan_page(path, text, only_pk=None):
    """Every stale-figure occurrence with its element, owner and disposition."""
    pks = [pk for pk in TARGETS if only_pk is None or pk == only_pk]
    page_pks = [pk for pk in pks if re.search(r'items/' + str(pk) + r'(?![0-9])', text)]
    if not page_pks:
        return []
    primary = max(page_pks, key=lambda pk: len(re.findall(r'items/' + str(pk) + r'(?![0-9])', text)))
    page_qual = {}
    for pk in page_pks:
        page_qual[pk] = next((q for q in TARGETS[pk]["page"] if q in text), None)
    found = []
    seen = set()
    for kind, pat in PRICE_ELEMENTS:
        for em in pat.finditer(text):
            el = em.group(0)
            for pk in page_pks:
                spec = TARGETS[pk]
                stale, floor = spec["stale"], spec["floor"]
                for fm in figure_re(stale).finditer(el):
                    abs_pos = em.start() + fm.start()
                    key = (abs_pos, fm.group(1))
                    if key in seen:
                        continue
                    seen.add(key)
                    owner = owning_pk(text, abs_pos, page_pks)
                    if owner is None and kind in ("title", "meta"):
                        owner = primary
                    win = text[max(0, abs_pos - NEAR_BEFORE):
                               min(len(text), abs_pos + NEAR_AFTER)]
                    near = next((q for q in spec["near"] if q.lower() in win.lower()), None)
                    if owner != pk:
                        disp, why = "skip", f"element belongs to pk {owner}, not {pk}"
                    elif page_qual[pk]:
                        disp, why = "hold", (f"page names vessel {page_qual[pk]!r} — the figure is that "
                                             f"boat's price, not this row's floor; a change here is a "
                                             f"content rewrite, not a figure sweep")
                    elif near:
                        disp, why = "skip", f"tier qualifier {near!r} beside it — figure is correct as written"
                    else:
                        disp, why = "replace", f"unqualified {stale} in {kind} owned by pk {pk}"
                    found.append({"path": str(path), "kind": kind, "pk": pk,
                                  "figure": fm.group(1), "stale": stale, "floor": floor,
                                  "pos": abs_pos, "disposition": disp, "why": why,
                                  "element": re.sub(r"\s+", " ", el)[:190]})
    return found


def apply_replacements(text, hits):
    """Apply, right-to-left so earlier offsets stay valid."""
    n = 0
    for h in sorted([x for x in hits if x["disposition"] == "replace"],
                    key=lambda x: -x["pos"]):
        old = h["figure"]
        new = old.replace(f"{h['stale']:,}", f"{h['floor']:,}").replace(str(h["stale"]), str(h["floor"]))
        assert text[h["pos"]:h["pos"] + len(old)] == old, "offset drift — aborting"
        text = text[:h["pos"]] + new + text[h["pos"] + len(old):]
        n += 1
    return text, n


def html_files():
    out = []
    for p in sorted(REPO.rglob("*.html")):
        if ".git" in p.parts or "node_modules" in p.parts:
            continue
        out.append(p)
    return out


def self_test():
    """Corruption control: plant a stale figure, prove it is caught; prove a
    genuine figure on the same page is not."""
    page = REPO / "key-west-fishing-charter.html"
    original = page.read_text(encoding="utf-8")
    print("=== SELF-TEST (corruption control) ===")
    print(f"  page: {page.name}")

    # Baseline: the page today must produce zero replacements.
    base = scan_page(page, original)
    base_rep = [h for h in base if h["disposition"] == "replace"]
    print(f"  baseline replacements on the untouched page: {len(base_rep)}")
    assert not base_rep, f"baseline is not clean: {base_rep}"

    # NEGATIVE: the page's genuine from-price ($1,395) must never be flagged.
    assert "$1,395" in original, "expected the genuine from-price on this page"
    genuine = [h for h in base if h["figure"] in ("$1,395", "1,395")]
    print(f"  genuine from-price $1,395 occurrences flagged: {len(genuine)}  (must be 0)")
    assert not genuine, "detector flagged a correct figure"

    # POSITIVE: plant an unqualified stale ceiling in a pk-owned hero stat.
    planted = original.replace(
        '<span class="hero-stat-value">$1,395</span>',
        '<span class="hero-stat-value">$1,795</span>', 1)
    assert planted != original, "plant did not take"
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / page.name
        tmp.write_text(planted, encoding="utf-8")
        hits = scan_page(tmp, planted)
        rep = [h for h in hits if h["disposition"] == "replace"]
        print(f"  planted stale $1,795 in hero-stat -> replacements detected: {len(rep)}")
        for h in rep:
            print(f"      CAUGHT {h['kind']} pk={h['pk']} {h['figure']} -> {h['floor']}  ({h['why']})")
        assert len(rep) == 1 and rep[0]["kind"] == "hero-stat", \
            f"corruption control failed: {rep}"
        fixed, n = apply_replacements(planted, hits)
        assert n == 1 and '<span class="hero-stat-value">$1,395</span>' in fixed, \
            "replacement did not restore the correct figure"
        print("  replacement restored $1,395 in the planted slot")

    # NEGATIVE 2: the real qualified $1,795 offer card must stay skipped.
    qual = [h for h in base if h["figure"] == "$1,795" and h["disposition"] == "skip"]
    print(f"  real qualified $1,795 offer card: {len(qual)} occurrence(s), all skipped")
    for h in qual:
        print(f"      SKIPPED {h['kind']}: {h['why']}")
    assert qual, "expected the genuine qualified $1,795 to be seen and skipped"
    print("  SELF-TEST PASS\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()

    self_test()
    if args.self_test:
        return

    print("=== SWEEP ===")
    total_found = total_rep = 0
    per_page = {}
    for p in html_files():
        text = p.read_text(encoding="utf-8")
        hits = scan_page(p.relative_to(REPO), text)
        if not hits:
            continue
        rel = str(p.relative_to(REPO))
        rep = [h for h in hits if h["disposition"] == "replace"]
        per_page[rel] = (len(hits), len(rep))
        total_found += len(hits)
        total_rep += len(rep)
        print(f"\n  {rel}   found={len(hits)}  to-replace={len(rep)}")
        for h in hits:
            tag = "REPLACE" if h["disposition"] == "replace" else "keep   "
            print(f"      {tag} [{h['kind']}] pk={h['pk']} {h['figure']}  {h['why']}")
            print(f"              {h['element'][:150]}")
        if rep and args.execute:
            new, n = apply_replacements(text, hits)
            p.write_text(new, encoding="utf-8")
            print(f"      WROTE {rel} ({n} replacements)")

    print(f"\n=== TOTALS ===")
    print(f"  pages carrying a stale-figure spelling : {len(per_page)}")
    print(f"  occurrences found                      : {total_found}")
    print(f"  occurrences replaced                   : {total_rep if args.execute else 0}"
          f"{'' if args.execute else f' (dry run; {total_rep} would be replaced)'}")
    for rel, (f, r) in sorted(per_page.items()):
        print(f"    {rel:<52s} found={f:2d}  replace={r}")


if __name__ == "__main__":
    main()
