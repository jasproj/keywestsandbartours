#!/usr/bin/env python3
"""D-574 — repair the priceLabel=='charter' rows that stored a ladder CEILING.

DETERMINISTIC (D-581). No network. Every value written is asserted against the
committed live evidence in data/charter-ladders-2026-08-24.json before any byte
is changed; a single failed assert aborts the whole run and writes nothing.

WHAT WENT WRONG
  extract-price-v5.2.js:114-125 (and extract-price-v5.js:135-146) selects
  `Math.max(...allPrices)` whenever the page text matches /private charter|
  full day charter|half day charter/. Every other price writer in this network
  selects the floor. `priceLabel: 'charter'` is that branch's unique fingerprint
  — no other writer emits it — so the 48 rows carrying it are the complete
  population, bounded from the code rather than by sampling stored values.

WHY THIS IS NOT "REPRICE EVERY CHARTER ROW"
  Storing the ceiling is only wrong when the product is not the thing the top
  tier names. Three dispositions, each decided from the live ladder:

  (a) CORRECT-BY-CONSTRUCTION — the row's own name or durationText names the
      tier stored, or the ladder has exactly one purchasable tier so ceiling and
      floor coincide. `Math.max` happened to land on the right number. Left
      alone. Repricing these to a floor would MANUFACTURE the duration/price
      mispairing that PR #206 (f44ce828) was opened to remove.
  (b) MAX-TIER DEFECT — stored == ceiling of a ladder whose top tier the product
      does not name. Rewritten to the ladder floor.
  (c) INSUFFICIENT — fewer than 3 date-valid readings. Left untouched.

  (d) DURATION-MATCHED — stored == ceiling, but the row's durationText names a
      MIDDLE tier, so the floor and the named tier are different numbers. These
      were held at first review and adjudicated by the operator: they follow the
      PR #206 / f44ce828 rule, "correct the PRICE to the variant the duration
      names, never the duration to match the cheap price". 104492 -> $1,750 (the
      10 Hour Charter its durationText names, not the $1,950 12-hour ceiling and
      not the $1,050 floor); 635625 -> $1,040 (Six Hour, not the $1,270 Eight
      Hour ceiling and not the $405 floor).

WHAT IS WRITTEN
  price            -> the ladder floor (min across date-valid readings)
  priceConfidence  -> 'high'
  priceLabel       -> UNCHANGED ('charter'). app.js renders priceUnit, not
                      priceLabel; the render vocabulary is out of scope here.
  _unknownFields   -> priceSource / priceCustomerType / priceTierCount /
                      excludedTiers. All four already exist in this file's
                      vocabulary. tours-data.json has NO priceBreakdown field
                      and one is NOT invented; excludedTiers carries the ladder.
                      priceUnit is deliberately NOT written: app.js:147-150
                      renders it, and this commit changes no render vocabulary.

RENDERED PAGES
  Swept separately by scripts/sweep-charter-figures.py. Run that before this.
"""
import argparse, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOURS = REPO / "tours-data.json"
LADDERS = REPO / "data" / "charter-ladders-2026-08-24.json"
SRC = "fh-price-preview-charter-2026-08-24"
MIN_VALID = 3

# pk -> (disposition, stored_now, new_price_or_None, floor_tier_singular, why)
# Every ruling states the fact that decided it. Verified against the ladders file
# by assert below — a stale ruling cannot survive a re-probe.
RULINGS = {
    # ---- (b) MAX-TIER DEFECT, duration axis: durationText names the FLOOR tier,
    #      stored is the 8h/10h ceiling. Floor and durationText agree, so the
    #      rewrite removes the ceiling pick without creating a mispairing.
    532140: ("b", 2195.0, 1395.0, "6 Hour Private Charter",
             "durationText '6 Hour' == floor tier '6 Hour Private Charter'; stored was the 10 Hour ceiling"),
    554262: ("b", 1895.0, 1395.0, "6 Hour Private Charter",
             "durationText '6 Hour' == floor tier '6 Hour Private Charter'; stored was the 10 Hour ceiling"),
    563185: ("b", 1670.0, 1295.0, "6 Hour Private Charter",
             "durationText '6 Hour' == floor tier '6 Hour Private Charter'; stored was the 10 Hour ceiling"),
    541394: ("b", 1795.0, 1395.0, "Half-Day Charter",
             "durationText '4 hours' == floor tier 'Half-Day Charter' (note '4 hours'); stored was the Full-Day 8h ceiling"),

    # ---- (b) MAX-TIER DEFECT, vessel axis: every tier is the SAME duration on a
    #      DIFFERENT boat (ARIA 42ft vs ZODIAC 60ft). The product names no vessel,
    #      so the ceiling is the bigger boat, not this product. House convention
    #      is already the cheaper vessel: sunset-cruises.html has shipped
    #      "ARIA $1,200 or ZODIAC $2,200" with a $1,200 card price since #220.
    105623: ("b", 2200.0, 1200.0, "Private Charter - ARIA",
             "vessel axis; both tiers are the 3 Hour Charter this row names; stored was the ZODIAC ceiling"),
    105610: ("b", 2400.0, 1400.0, "Private Charter - ARIA",
             "vessel axis; both tiers are the 4 Hour Sail this row names; stored was the ZODIAC ceiling"),
    113331: ("b", 2800.0, 1800.0, "Private Charter - ARIA",
             "vessel axis; both tiers are the 8 Hours this row names; stored was the ZODIAC ceiling"),
    105631: ("b", 6200.0, 5200.0, "Private Charter - ARIA",
             "vessel axis; both tiers are All Inclusive Wedding; row names no vessel; stored was the ZODIAC ceiling"),
    105635: ("b", 6200.0, 5200.0, "Private Charter - ARIA",
             "vessel axis; both tiers are Special Memorial; row names no vessel; stored was the ZODIAC ceiling"),
    105639: ("b", 6200.0, 5200.0, "Private Charter - ARIA",
             "vessel axis; both tiers differ only by vessel; row names no vessel; stored was the ZODIAC ceiling"),

    # ---- (d) DURATION-MATCHED. durationText names a MIDDLE tier, so the floor
    #      and the named tier are different numbers. Operator ruling: follow
    #      PR #206 / f44ce828 and take the tier the duration names. Asserted
    #      below to be a real purchasable tier whose name shares a duration digit
    #      with the row's durationText. The floor assert used for (b) would be
    #      the WRONG check here and is deliberately not applied to (d).
    104492: ("d", 1950.0, 1750.0, "10 Hour Charter",
             "durationText '10 Hour Charter' names the $1,750 tier; stored was the $1,950 12-hour ceiling; floor $1,050 is the 4-hour tier"),
    635625: ("d", 1270.0, 1040.0, "Six Hour",
             "durationText '6 Hour charter' names the $1,040 Six Hour tier; stored was the $1,270 Eight Hour ceiling; floor $405 is the 2-hour tier"),
}

WORD_DIGITS = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
               "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
               "eleven": "11", "twelve": "12", "half": "4"}


def duration_tokens(text):
    """Duration numbers a string commits to. '10 Hour Charter' -> {'10'};
    'Six Hour' -> {'6'}, so a word-spelled tier still matches a digit-spelled
    durationText."""
    import re as _re
    low = (text or "").lower()
    out = set(_re.findall(r"\d+", low))
    for w, d in WORD_DIGITS.items():
        if _re.search(r"\b" + w + r"\b", low):
            out.add(d)
    return out


def load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))


def ladder_facts(entry):
    """Floor, ceiling and purchasable tier count from date-valid readings."""
    tiers = entry["tiers"]
    if not tiers:
        return None, None, 0
    mins = [t["priceMin"] for t in tiers]
    return min(mins), max(mins), len(tiers)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--execute", action="store_true",
                    help="write tours-data.json; without it this is a dry run")
    args = ap.parse_args()

    lad = load_json(LADDERS)
    raw = TOURS.read_text(encoding="utf-8")
    doc = json.loads(raw)
    rows = doc["tours"]

    # The file must round-trip, or a whole-file reformat would hide inside the diff.
    assert json.dumps(doc, indent=2, ensure_ascii=True) + "\n" == raw, \
        "tours-data.json does not round-trip under json.dumps(indent=2, ensure_ascii=True)"

    charter = [t for t in rows if t.get("priceLabel") == "charter"]
    assert len(charter) == 48, f"expected the 48-row charter population, found {len(charter)}"

    by_pk = {t["pk"]: t for t in rows}
    planned = []

    for pk, (disp, stored_expected, new_price, floor_name, why) in sorted(RULINGS.items()):
        entry = lad["items"].get(str(pk))
        assert entry is not None, f"pk {pk} has no live evidence in {LADDERS.name}"
        row = by_pk.get(pk)
        assert row is not None, f"pk {pk} absent from tours-data.json"
        assert row.get("priceLabel") == "charter", f"pk {pk} is not in the charter population"

        # The tree must still hold the value the ruling was made against.
        assert float(row["price"]) == stored_expected, \
            f"pk {pk} stored {row['price']} but the ruling was made against {stored_expected}"
        assert entry["validReadings"] >= MIN_VALID, \
            f"pk {pk} has {entry['validReadings']} date-valid readings, need >= {MIN_VALID}"

        floor, ceil, ntiers = ladder_facts(entry)
        assert float(stored_expected) == ceil, \
            f"pk {pk}: stored {stored_expected} is not the observed ceiling {ceil}"
        assert ceil != floor, f"pk {pk}: ceiling == floor, there is no ladder to be wrong about"

        tier_prices = {t["priceMin"] for t in entry["tiers"]}
        assert float(new_price) in tier_prices, \
            f"pk {pk}: ruling price {new_price} is not a purchasable tier {sorted(tier_prices)}"
        names = [t["singular"] for t in entry["tiers"] if t["priceMin"] == float(new_price)]
        assert floor_name in names, \
            f"pk {pk}: tier at {new_price} is {names}, ruling named {floor_name!r}"

        if disp == "b":
            assert float(new_price) == floor, \
                f"pk {pk}: (b) ruling says {new_price} but the observed floor is {floor}"
        elif disp == "d":
            # The whole point of (d) is that the answer is NOT the floor.
            assert float(new_price) != floor, \
                f"pk {pk}: (d) ruling equals the floor — it should have been classed (b)"
            dur = duration_tokens(by_pk[pk].get("durationText"))
            tier = duration_tokens(floor_name)
            assert dur and tier and (tier & dur), (
                f"pk {pk}: durationText {by_pk[pk].get('durationText')!r} does not name "
                f"tier {floor_name!r} — the duration rule cannot be applied here")
        else:
            raise AssertionError(f"pk {pk}: unknown disposition {disp!r}")

        planned.append((pk, disp, new_price, floor_name, why, floor, ceil, ntiers))

    print("=== PLAN ===")
    writes = 0
    for pk, disp, new_price, floor_name, why, floor, ceil, ntiers in planned:
        row = by_pk[pk]
        how = "ceil -> floor" if disp == "b" else "ceil -> tier the duration names"
        print(f"  WRITE ({disp}) pk={pk:<7d} ${row['price']:>9,.2f} -> ${new_price:>9,.2f}  "
              f"({how}, {ntiers} tiers)  {row['name'][:42]!r}")
        print(f"        {why}")
        writes += 1

        entry = lad["items"][str(pk)]
        # Excluded relative to the tier ACTUALLY CHOSEN, not to the floor. On a
        # (d) row the chosen tier is not the floor, so keying this on `floor`
        # would list the chosen tier as excluded and omit the real floor.
        excluded = [f"{t['singular']} ${t['priceMin']:.2f}"
                    + (f" ({t['note']})" if t["note"] else "")
                    for t in entry["tiers"] if t["priceMin"] != float(new_price)]
        row["price"] = new_price
        row["priceConfidence"] = "high"
        # priceLabel deliberately unchanged — see module docstring.
        uf = row.get("_unknownFields") or {}
        uf["priceSource"] = SRC
        uf["priceCustomerType"] = floor_name
        uf["priceTierCount"] = ntiers
        uf["excludedTiers"] = excluded
        if disp == "d":
            # Same field PR #225 used to record a duration-based tier ruling.
            uf["priceTierExclusion"] = (
                f"durationText {row['durationText']!r} names {floor_name!r} "
                f"${float(new_price):,.2f}; the ${floor:,.2f} floor is a shorter "
                f"variant and the ${ceil:,.2f} ceiling is a longer one. Priced to "
                f"the variant the duration names, per PR #206 (f44ce828).")
        row["_unknownFields"] = uf

    nb = sum(1 for p in planned if p[1] == "b")
    nd = sum(1 for p in planned if p[1] == "d")
    print(f"\n  rows to write: {writes}   (b) ceiling->floor: {nb}   (d) duration-matched: {nd}")

    if not args.execute:
        print("\nDRY RUN — tours-data.json NOT written.")
        return

    out = json.dumps(doc, indent=2, ensure_ascii=True) + "\n"
    TOURS.write_text(out, encoding="utf-8")
    print(f"\nWROTE {TOURS}  ({len(raw)} -> {len(out)} bytes)")


if __name__ == "__main__":
    main()
