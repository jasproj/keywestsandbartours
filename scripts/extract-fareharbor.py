#!/usr/bin/env python3
"""
Extract the current FareHarbor catalogue for every operator KWST already carries.

This is the ADDITIVE half of the pipeline. Its counterpart is
`merge-hermes-extract.py`, which the six Wander repos have and KWST never got.
Together they replace the manual "Add files via upload" that last refreshed
tours-data.json on 2026-01-09.

SCOPE — read this before assuming what it does.

  IN SCOPE   Enumerating the full public catalogue of operators we ALREADY
             carry, via the public FareHarbor item API. No credentials needed.

  NOT IN SCOPE — DISCOVERING NEW OPERATORS. There is no unauthenticated
             endpoint that lists DN companies by region: /api/v1/companies/
             returns {"companies":[]} and fareharbor.com/marketplace/ is
             login-gated. An operator we have never carried (Fury Water
             Adventures, shortname `furycat`, is a confirmed live example)
             is invisible to this script. Closing that gap needs a DN
             marketplace export supplied by hand.

  NOT IN SCOPE — RETIRING DEAD RECORDS. This script and the merge are purely
             additive. Records that have vanished upstream survive the merge
             untouched, by design. Retirement belongs to the soft-delete
             engine (_tools/scripts/auto-rot-cleanup/), a separate pass.
             Conflating the two would make an additive tool destructive.

Output: tours-data-new.json — the input `merge-hermes-extract.py` expects.
        Envelope {schemaVersion, lastNormalized, tours[]}, schemaVersion 1.0.8,
        35 fields per record in KWST's exact key order.

This script NEVER writes tours-data.json.

Region handling
  - island is the LOWERCASED FULL LOCATION PATH, never a slug. KWST stores
    "united states/florida/key west" on 972 of 972 records; emitting
    "key-west" would fork the convention and break every consumer.
  - Keys membership is tested on the last path segment against MONROE below.
  - A blank item location is KEPT, not dropped, and falls back to the
    operator's own modal region. 530 of 735 gap items have no location; a
    drop-on-blank rule would discard most of the recoverable inventory.
    (Same precedent as USVI_GENERIC's empty string in the merge script.)
  - Non-Keys FLORIDA items route to fst-routing-candidates.json for Florida
    Sandbar Tours, which uses the identical island convention (788/788
    island == location.lower()). Out-of-state items are discarded.
"""

import json
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 WanderRenderMonitor/1.0 (+internal-qa)"}
AFFILIATE = "walktheplankadventures"

# Monroe County, north to south. Matched against the final path segment.
MONROE = [
    "key largo", "tavernier", "islamorada", "long key", "layton", "grassy key",
    "conch key", "duck key", "key colony beach", "marathon", "bahia honda",
    "summerland key", "little torch key", "big pine key", "ramrod key",
    "cudjoe key", "sugarloaf key", "big coppitt key", "stock island", "key west",
]
KEYS_GENERIC = ["florida keys", "the keys"]

# Positive out-of-state signals. A hand-written hint list is not enough: it let
# "E Pratt Street, Baltimore, MD" and "25 Union Street Boston, MA" through to the
# review bucket, where they inherited a Keys location. Match every US state by
# postal abbreviation and by full name, Florida excluded.
_STATES = ("AL AK AZ AR CA CO CT DE GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS "
           "MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA "
           "WV WI WY DC").split()
_STATE_NAMES = ("alabama alaska arizona arkansas california colorado connecticut "
                "delaware georgia hawaii idaho illinois indiana iowa kansas kentucky "
                "louisiana maine maryland massachusetts michigan minnesota mississippi "
                "missouri montana nebraska nevada ohio oklahoma oregon pennsylvania "
                "tennessee texas utah vermont virginia washington wisconsin wyoming").split()
# Only in address context: ", MD" / ", MD 21202" / "Boston, MA 02108".
# A bare \bMD\b would fire on ordinary words — IN, OR, ME, OK, DE are all
# state codes and all common English — so the comma or the ZIP is required.
STATE_ADDR_RE = re.compile(r",\s*(" + "|".join(_STATES) + r")\b|\b(" +
                           "|".join(_STATES) + r")\s+\d{5}\b")
STATE_NAME_RE = re.compile(r"\b(" + "|".join(_STATE_NAMES) + r")\b")
# Out-of-state city names that appear without a state token. Spelled-out names
# matter: "HunkOMania Male Revue Show - New York City" carries no state code.
NON_FL_CITY_HINTS = ("andalusia", "manteo", "atlantic city", "baltimore", "boston",
                     "chicago", "cleveland", "nashville", "denver", "las vegas",
                     "philadelphia", "charlotte", "phoenix", "pittsburgh",
                     "san diego", "seattle", "portland", "austin", "houston",
                     "new york city", "new york", "los angeles", "san francisco",
                     "washington dc", "new orleans", "minneapolis", "detroit",
                     "st. louis", "saint louis", "kansas city", "salt lake city",
                     "san antonio", "columbus", "indianapolis", "milwaukee",
                     "raleigh", "richmond", "hartford", "providence", "buffalo")

# Mainland-Florida springs country: Fannings Spring, Manatee Springs and the
# rest sit hundreds of miles north of Monroe County. FST, not a discard.
NON_KEYS_FL_EXTRA = ("fanning", "manatee spring", "rainbow river", "ginnie spring",
                     "ichetucknee", "silver spring", "blue spring", "weeki wachee",
                     "homosassa", "devil's den", "troy spring")

# --- non-inventory filters -------------------------------------------------
# is_retail is the primary signal. These name guards exist only for operators
# who do not set it. Deliberately conservative: bare "shirt" and bare "card"
# are NOT here, because real products contain them ("Shirt Tail Charters").
MERCH_RE = re.compile(
    r"gift\s*card|gift\s*certificate|gift\s*cert\b|giftcard"
    r"|sweatshirt|hoodie|\bhoody\b|t-shirt|tee shirt|\btees?\b|tank top"
    r"|\bhat\b|\bfleece\b|uv shirt|long sleeve shirt"
    r"|coozie|koozie|\bsticker\b|\bmug\b|\btowel\b|tote bag|\bvisor\b"
    r"|keychain|\bmagnet\b|\bposter\b|apparel|merchandise|\bmerch\b",
    re.I)
# Deposits, add-ons and fee-only SKUs are not bookable experiences.
FEE_RE = re.compile(
    r"\bdeposit\b|\badd-?on\b|\bupgrade fee\b|\bbooking fee\b|\bfuel surcharge\b"
    r"|\bgratuity\b|\bdonation\b|sponsorship|\bbalance due\b"
    r"|\bcancellation (fee|insurance)\b|\btravel insurance\b|rent-a-hunk",
    re.I)
VIRTUAL_LOCS = {"online", "virtual", "on-line", "zoom", "remote"}

# review_no_segment operators whose products are real Keys inventory. Everything
# else in that bucket is dropped rather than inheriting a Keys location.
REVIEW_ACCEPT = {
    "barefootbillyskw", "ridethelagoon", "glassbottomboatsofislamorada",
    "saltysandbars", "clearkayaking", "laidbackkeywest", "keywestfishing-charters",
    "robertthedollexperience", "conchconciergeweddings", "sailargonavis",
    "sail-keywest", "sunsetwatersportskeywest", "casualmondaycharters",
    "fishmonstermax", "gorillaboats", "keywestpromotions",
    "paradisewatersportsrentals", "tntchartersflkeys", "southpointdiverskw",
    "keywesthunt",
    # Real Key West private charters; the location fields are a bare "Slip"
    # and a Google Maps URL, neither of which names a town. We already hold
    # 7 records from this operator.
    "nudecharters",
}
NON_KEYS_FL_HINTS = ("naples", "goodland", "miami", "fort lauderdale", "destin",
                     "st. augustine", "saint augustine", "crystal river",
                     "panama city", "fort walton", "marco island", "tampa",
                     "st. petersburg", "saint petersburg", "orlando", "sarasota",
                     "clearwater", "jacksonville", "daytona", "cocoa", "stuart",
                     "jupiter", "boca raton", "west palm", "pompano", "hollywood")


def get(url, tries=6):
    """GET with backoff. FareHarbor rate-limits aggressively at ~180 rapid calls."""
    delay = 3
    for _ in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.status, r.read().decode("utf8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(delay)
                delay = min(delay * 2, 60)
                continue
            return e.code, ""
        except Exception:
            time.sleep(delay)
            delay = min(delay * 2, 60)
    return 429, ""


def shortname_of(booking_url):
    m = re.search(r"book/([^/]+)/items", booking_url or "")
    return m.group(1) if m else None


def canonical_segment(raw):
    """Return the Monroe County segment a free-text location names, or None."""
    s = (raw or "").lower()
    if not s.strip():
        return None
    for place in MONROE:                      # longest-first would matter if any
        if place in s:                        # name contained another; none do
            return place
    for g in KEYS_GENERIC:
        if g in s:
            return g
    return None


# --- franchise place-suffix rule -------------------------------------------
# A blank location plus a name ending "- <Place>" is how multi-city franchises
# present themselves ("Hunk-O-Mania Male Revue Show - Honolulu"). Rejecting on
# a city LIST never converges; three separate runs leaked a new city each time.
#
# But the same "- <suffix>" shape is also how Keys operators name a VESSEL or a
# DEPARTURE POINT: "- Andiamo", "- Still Dreamin'", "- PERRY MARINA",
# "- Casa Marina". Rejecting every non-Monroe suffix drops those too — it would
# have deleted 628106, 672481 and 637746, all of which are already published.
#
# The discriminator is cardinality, not vocabulary. A franchise carries MANY
# distinct suffixes; a vessel or dock carries one or two, repeated. So the rule
# only arms for operators showing >= FRANCHISE_MIN distinct place-like suffixes.
FRANCHISE_MIN = 5
_SUFFIX_STOP = set(
    "tour tours charter charters cruise cruises sail sailing snorkel snorkeling "
    "dive diving trip trips rental rentals special specials package packages "
    "experience adventure adventures party class lesson lessons course combo "
    "pass ticket tickets only option options hour hours day days night nights "
    "am pm bird early late private shared group family kids adult adults deluxe "
    "premium classic ultimate full half self guided included gear boat boats "
    "water sunset sunrise morning afternoon evening reef sandbar bar bay "
    "island islands key keys".split())


def place_suffix(name):
    """The '- <Place>' tail of a product name, or None if it is not place-shaped."""
    parts = re.split(r"\s[-–—]\s", name or "")
    if len(parts) < 2:
        return None
    s = parts[-1].strip().rstrip("!.,")
    # tolerate a trailing state code: "Key West, FL"
    s = re.sub(r",\s*[A-Z]{2}$", "", s).strip()
    if not s or len(s) > 28 or not s[0].isupper():
        return None
    words = s.split()
    if not (1 <= len(words) <= 3):
        return None
    if not all(re.fullmatch(r"[A-Za-z.'’]+", w) for w in words):
        return None
    if any(w.lower() in _SUFFIX_STOP for w in words):
        return None
    return s


def is_out_of_state(text):
    """True only on a POSITIVE non-Florida signal."""
    if not text:
        return False
    low = text.lower()
    if any(h in low for h in NON_FL_CITY_HINTS):
        return True
    if STATE_NAME_RE.search(low):
        return True
    return bool(STATE_ADDR_RE.search(text.upper()))


def classify(raw_location, fallback_segment, name=""):
    """
    -> (bucket, segment)
    bucket is one of: keys, keys_blank, fst, discard, review
    """
    s = (raw_location or "").strip()
    if not s:
        # Ruling 3: blank is kept and inherits the operator's own region.
        # A blank address on a product whose NAME names another state is
        # still out of region.
        if is_out_of_state(name):
            return "discard", None
        return ("keys_blank", fallback_segment) if fallback_segment else ("review", None)
    low = s.lower()
    seg = canonical_segment(low)
    if seg:
        return "keys", seg
    # The product name carries the region when the address is a bare street:
    # "Diva Royale - Drag Queen Show Baltimore" at "E Pratt Street".
    if is_out_of_state(s) or is_out_of_state(name):
        return "discard", None
    if (any(h in low for h in NON_KEYS_FL_HINTS)
            or any(h in low for h in NON_KEYS_FL_EXTRA)
            or re.search(r"\bfl\b|florida", low)):
        return "fst", None
    # Ruling 2: an unrecognised location is an UNKNOWN region, not an
    # out-of-region one. Only a positive out-of-state signal discards.
    # "Robbie's Marina" is in Islamorada and names neither city nor state.
    return ("review", fallback_segment) if fallback_segment else ("review", None)


def fl_city(raw):
    """Best-effort Florida city from a free-text FareHarbor location string."""
    s = (raw or "").strip()
    low = s.lower()
    for hint in NON_KEYS_FL_HINTS:
        if hint in low:
            return title_segment(hint)
    # "123 Some St, Naples, FL 34114" -> take the token before the state
    m = re.search(r",\s*([A-Za-z .'-]+),\s*(?:FL|Florida)\b", s)
    if m:
        return title_segment(m.group(1).strip().lower())
    m = re.match(r"^([A-Za-z .'-]+),\s*(?:FL|Florida)\b", s)
    if m:
        return title_segment(m.group(1).strip().lower())
    return "Unknown"


def title_segment(seg):
    """'key west' -> 'Key West'. Keeps 'St.'-style tokens intact if ever added."""
    return " ".join(w if w.endswith(".") else w.capitalize() for w in seg.split())


def booking_url(sn, pk):
    return (f"https://fareharbor.com/embeds/book/{sn}/items/{pk}/"
            f"?asn=fhdn&asn-ref={AFFILIATE}&ref={AFFILIATE}"
            f"&bookable-only=yes&full-items=yes&marketplace=yes&flow=no")


# KWST's exact key order. The merge carries unread fields through verbatim, so
# every key is emitted even where the value is empty — a missing key would
# propagate into tours-data.json and nothing downstream would repair it.
def build_record(item, sn, company, segment):
    pk = int(item["pk"])
    location = f"United States/Florida/{title_segment(segment)}"
    images = item.get("images") or []
    gallery = [i.get("image_cdn_url") or i.get("image_url")
               for i in images if isinstance(i, dict)]
    gallery = [g for g in gallery if g]
    desc = (item.get("description_text") or "").strip() or (item.get("headline") or "").strip()
    cap = item.get("maximum_initial_party_size")
    return {
        "id": str(pk),
        "pk": pk,
        "name": (item.get("name") or "").strip(),
        "company": company,
        "bookingUrl": booking_url(sn, pk),
        "category": "",
        "location": location,
        "island": location.lower(),          # ruling 1: path form, never a slug
        "price": None,                       # needs the 17-date sweep
        "priceLabel": "",
        "priceConfidence": "",
        "qualityScore": 0,
        "currency": "USD",
        "duration": "",                      # needs the availability window
        "durationText": "",
        "description": desc,
        "descriptionRaw": "",
        "descriptionQuality": "",
        "highlights": [],
        "tags": [],
        "image": (item.get("image_cdn_url") or item.get("image_url") or ""),
        "galleryImages": gallery,
        "rating": None,
        "reviewCount": None,
        "ratingSource": "tripadvisor",
        "freeCancellation": False,
        "timeOfDay": "",
        "capacity": cap if isinstance(cap, int) else None,
        "enrichmentSource": "",
        "status": "active",
        "statusReason": None,
        "statusFirstSeen": None,
        "statusConsecutiveRuns": None,
        "lastUpdated": "",                   # ruling 5: merge stamps only what it changes
        "_unknownFields": {},
    }


def main():
    current = json.loads((REPO / "tours-data.json").read_text())["tours"]
    ours_by_pk = {int(t["pk"]): t for t in current if t.get("pk")}

    # Operator -> shortname, company, and modal region (the blank-location fallback)
    by_sn = {}
    for t in current:
        sn = shortname_of(t.get("bookingUrl"))
        if not sn:
            continue
        d = by_sn.setdefault(sn, {"company": t.get("company"), "segments": Counter()})
        seg = canonical_segment(t.get("island"))
        if seg:
            d["segments"][seg] += 1
    for d in by_sn.values():
        d["fallback"] = d["segments"].most_common(1)[0][0] if d["segments"] else None

    shortnames = sorted(by_sn)
    print(f"operators in tours-data.json: {len(shortnames)}")

    keys_records, fst_records = [], []
    stats = Counter()
    dead_operators, review_rows, discard_rows = [], [], []
    retail_rows, fee_rows, virtual_rows, review_drop_rows = [], [], [], []
    franchise_rows, franchise_ops = [], {}

    for n, sn in enumerate(shortnames, 1):
        status, body = get(f"https://fareharbor.com/api/v1/companies/{sn}/items/")
        if status != 200 or not body:
            dead_operators.append((sn, status))
            stats["operator_unresolved"] += 1
            time.sleep(1.2)
            continue
        try:
            items = json.loads(body).get("items") or []
        except Exception:
            dead_operators.append((sn, "parse-error"))
            stats["operator_unresolved"] += 1
            time.sleep(1.2)
            continue

        company = by_sn[sn]["company"]
        fallback = by_sn[sn]["fallback"]
        # franchise detection, per operator, over its blank-location records
        sufs = {place_suffix((i.get("name") or "").strip())
                for i in items if not (i.get("location") or "").strip()}
        sufs.discard(None)
        franchise = len(sufs) >= FRANCHISE_MIN
        if franchise:
            franchise_ops[sn] = len(sufs)
        for it in items:
            stats["enumerated"] += 1
            if it.get("is_archived"):
                stats["dropped_archived"] += 1
                continue
            if it.get("is_private"):
                stats["dropped_private"] += 1
                continue
            if it.get("is_unlisted"):
                stats["dropped_unlisted"] += 1
                continue
            nm = (it.get("name") or "").strip()
            loc_raw = (it.get("location") or "").strip()
            # 1. the flag, primary
            if it.get("is_retail"):
                stats["dropped_retail_flag"] += 1
                retail_rows.append((sn, int(it["pk"]), nm[:52], "is_retail"))
                continue
            # 2. name guard for operators who do not set the flag
            if MERCH_RE.search(nm):
                stats["dropped_merch_name"] += 1
                retail_rows.append((sn, int(it["pk"]), nm[:52], "name-guard"))
                continue
            # deposits / add-ons / fee-only SKUs
            if FEE_RE.search(nm):
                stats["dropped_fee_only"] += 1
                fee_rows.append((sn, int(it["pk"]), nm[:52]))
                continue
            # 3. virtual / online products are not Keys inventory
            if loc_raw.lower() in VIRTUAL_LOCS:
                stats["dropped_virtual"] += 1
                virtual_rows.append((sn, int(it["pk"]), loc_raw, nm[:48]))
                continue
            # franchise place-suffix rule: only arms for franchise operators
            if franchise and not loc_raw:
                suf = place_suffix(nm)
                if suf and not canonical_segment(suf.lower()):
                    stats["dropped_franchise_city"] += 1
                    franchise_rows.append((sn, int(it["pk"]), suf, nm[:48]))
                    continue
            bucket, seg = classify(loc_raw, fallback, nm)
            if bucket == "keys":
                stats["keys_kept"] += 1
                keys_records.append(build_record(it, sn, company, seg))
            elif bucket == "keys_blank":
                stats["keys_kept_blank_location"] += 1
                keys_records.append(build_record(it, sn, company, seg))
            elif bucket == "fst":
                stats["fst_routed"] += 1
                # FST uses the identical convention (island == location.lower(),
                # path form, 788/788), so emit a path, not the raw FH string.
                city = fl_city(it.get("location"))
                rec = build_record(it, sn, company, "key west")
                rec["location"] = f"United States/Florida/{city}"
                rec["island"] = rec["location"].lower()
                fst_records.append(rec)
            elif bucket == "review":
                # The location names a venue, not a town. Accepted only for
                # operators confirmed to sell real Keys inventory; the rest
                # would otherwise inherit a Keys location they do not have.
                # Accepted records get the RESOLVED path, not the raw marina
                # string, so location/island stay canonical.
                if sn in REVIEW_ACCEPT:
                    stats["review_accepted"] += 1
                    review_rows.append((sn, int(it["pk"]), loc_raw[:30], nm[:46]))
                    keys_records.append(build_record(it, sn, company, seg or "key west"))
                else:
                    stats["review_rejected"] += 1
                    review_drop_rows.append((sn, int(it["pk"]), loc_raw[:30], nm[:46]))
            else:
                stats["discarded_out_of_state"] += 1
                discard_rows.append((sn, int(it["pk"]), (it.get("location") or "")[:40]))
        if n % 25 == 0:
            print(f"  {n}/{len(shortnames)}", flush=True)
        time.sleep(1.2)

    # de-dupe: an item can only appear once per pk
    seen, deduped = set(), []
    for r in keys_records:
        if r["pk"] in seen:
            stats["duplicate_pk_dropped"] += 1
            continue
        seen.add(r["pk"])
        deduped.append(r)

    new_pks = {r["pk"] for r in deduped}
    overlap = new_pks & set(ours_by_pk)
    only_new = new_pks - set(ours_by_pk)
    only_ours = set(ours_by_pk) - new_pks

    out = {
        "schemaVersion": "1.0.8",
        "lastNormalized": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tours": deduped,
    }
    (REPO / "tours-data-new.json").write_text(json.dumps(out, indent=2) + "\n")
    (REPO / "fst-routing-candidates.json").write_text(json.dumps(fst_records, indent=2) + "\n")

    print("\n=== EXTRACTION ===")
    for k in ("enumerated", "dropped_archived", "dropped_private", "dropped_unlisted",
              "dropped_retail_flag", "dropped_merch_name", "dropped_fee_only",
              "dropped_virtual", "dropped_franchise_city", "keys_kept", "keys_kept_blank_location",
              "review_accepted", "review_rejected", "fst_routed",
              "discarded_out_of_state", "duplicate_pk_dropped",
              "operator_unresolved"):
        print(f"  {k:28s} {stats[k]}")
    print(f"  {'records written':28s} {len(deduped)}")

    print("\n=== PK OVERLAP vs our 972 ===")
    print(f"  already in tours-data.json      {len(overlap)}")
    print(f"  NEW to us                       {len(only_new)}")
    print(f"  ours not present in extract     {len(only_ours)}   (retirement is NOT this pass)")

    if dead_operators:
        print(f"\n=== OPERATORS UNRESOLVED ({len(dead_operators)}) ===")
        for sn, st in dead_operators:
            print(f"  {sn:36s} {st}")

    if franchise_rows:
        print(f"\n=== FRANCHISE CITY-SUFFIX DROPPED ({len(franchise_rows)}) ===")
        print(f"    armed for: {franchise_ops}")
        for sn, pk, suf, nm in franchise_rows:
            print(f"  {sn:26s} pk={pk:<8} suffix={suf!r:18s} {nm}")
    if retail_rows:
        byop = Counter(sn for sn, _, _, _ in retail_rows)
        ng = [r for r in retail_rows if r[3] == "name-guard"]
        print(f"\n=== RETAIL / MERCH DROPPED ({len(retail_rows)}) ===")
        for sn, cnt in byop.most_common(12):
            print(f"  {sn:30s} {cnt:4d}")
        print(f"  -- of which by NAME GUARD (auditable), {len(ng)}:")
        for sn, pk, nm, _ in ng:
            print(f"     {sn:28s} pk={pk:<8} {nm}")
    if fee_rows:
        print(f"\n=== DEPOSIT / ADD-ON / FEE-ONLY DROPPED ({len(fee_rows)}) ===")
        for sn, pk, nm in fee_rows:
            print(f"  {sn:28s} pk={pk:<8} {nm}")
    if virtual_rows:
        print(f"\n=== VIRTUAL / ONLINE DROPPED ({len(virtual_rows)}) ===")
        for sn, pk, loc, nm in virtual_rows:
            print(f"  {sn:28s} pk={pk:<8} loc={loc!r:12s} {nm}")
    if review_drop_rows:
        print(f"\n=== REVIEW BUCKET REJECTED ({len(review_drop_rows)}) ===")
        for sn, pk, loc, nm in review_drop_rows:
            print(f"  {sn:28s} pk={pk:<8} loc={loc!r:34s} {nm}")
    if discard_rows:
        # Every discard is data loss, so it is listed, not just counted.
        by_op = Counter(sn for sn, _, _ in discard_rows)
        print(f"\n=== DISCARDED — positive out-of-state signal ({len(discard_rows)}) ===")
        for sn, cnt in by_op.most_common():
            sample = next(loc for s, _, loc in discard_rows if s == sn)
            print(f"  {sn:30s} {cnt:4d}   eg {sample!r}")
    if review_rows:
        print(f"\n=== REVIEW BUCKET ACCEPTED — resolved to Keys path ({len(review_rows)}) ===")
        for sn, pk, loc, name in review_rows[:20]:
            print(f"  {sn:28s} pk={pk:<8} loc={loc!r:32s} {name}")
    print("\ntours-data-new.json written. Merge NOT run. tours-data.json untouched.")


if __name__ == "__main__":
    main()
