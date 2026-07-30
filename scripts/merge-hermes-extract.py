#!/usr/bin/env python3
"""
Merge a FareHarbor extraction (tours-data-new.json) into tours-data.json.

KWST port of the script the six Wander repos have carried since 2026-05-27.
Ported, not copied: the USVI original slugifies `island` and tests region
membership against a flat slug list, which would discard all 972 KWST records.
See "Region handling" below.

Output: tours-data-merged.json. THIS SCRIPT NEVER WRITES tours-data.json.
Review the merged file, then promote it deliberately.

MERGE RULES
  pk in BOTH      start from OUR record. Backfill galleryImages / tags / image
                  only where ours is empty. Our price and description are never
                  touched — they are enrichment work the extract cannot beat.
  pk only in NEW  add it, flagged needsEnrichment: true.
  pk only in OURS keep it, untouched, byte-identical.

RETIREMENT IS NOT IN SCOPE — READ THIS BEFORE CHANGING THE `kept` BRANCH.
  Records that have vanished upstream SURVIVE this merge by design. At the time
  of writing 83 of our 972 are absent from the extract, 62 of them confirmed
  deleted at FareHarbor. This script does not touch them. Retiring dead
  inventory belongs to the soft-delete engine
  (_tools/scripts/auto-rot-cleanup/), which has its own bucketing, its own
  evidence thresholds and its own restore path. Folding retirement in here
  would turn an additive tool into a destructive one, and a bad extract — one
  timeout, one 429 storm — would silently delete live inventory.

REGION HANDLING
  island is the LOWERCASED FULL LOCATION PATH, never a slug. KWST stores
  "united states/florida/key west" on 972 of 972 records. normalize_island()
  therefore returns location.lower() unchanged; it does NOT slugify. Emitting
  "key-west" would fork the dataset convention and break every consumer that
  keys on island.

  Keys membership is tested on the LAST PATH SEGMENT against MONROE.
  A blank island is KEPT, never dropped.
  Non-Keys Florida records route to fst-routing-candidates.json for Florida
  Sandbar Tours, which uses the identical convention (788/788 island ==
  location.lower()). Out-of-state records are reported, never silently binned.

lastUpdated is stamped ONLY on records this merge actually changed. Stamping
every record would produce a full-file diff on a no-op run and destroy the
"assert semantic equality on untouched records" check.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

MONROE = [
    "key largo", "tavernier", "islamorada", "long key", "layton", "grassy key",
    "conch key", "duck key", "key colony beach", "marathon", "bahia honda",
    "summerland key", "little torch key", "big pine key", "ramrod key",
    "cudjoe key", "sugarloaf key", "big coppitt key", "stock island", "key west",
]
KEYS_GENERIC = ["florida keys", "the keys"]

# Fields the extract may legitimately backfill. price and description are
# deliberately absent: ours are enrichment output, the extract's are not.
BACKFILL = ("galleryImages", "tags", "image")


def normalize_island(island_raw, location_raw=""):
    """Path form, lowercased. Never a slug. Never reshaped."""
    v = (island_raw or "").strip()
    if v:
        return v.lower()
    return (location_raw or "").strip().lower()


def last_segment(island):
    return (island or "").strip().lower().split("/")[-1].strip()


def is_keys(island):
    """Blank counts as in-region — see REGION HANDLING."""
    seg = last_segment(island)
    if not seg:
        return True
    if seg in MONROE or seg in KEYS_GENERIC:
        return True
    # tolerate a bare country path such as "united states"
    return (island or "").strip().lower() in ("united states", "united states/florida")


def is_florida(island):
    return "florida" in (island or "").lower()


def main():
    current_data = json.loads((REPO / "tours-data.json").read_text())
    new_data = json.loads((REPO / "tours-data-new.json").read_text())
    current = current_data["tours"]
    incoming = new_data["tours"]

    print(f"Current tours: {len(current)}")
    print(f"Extract tours: {len(incoming)}")

    current_by_pk = {int(t["pk"]): t for t in current if t.get("pk")}

    keys_new, fst_candidates, out_of_region = [], [], []
    for t in incoming:
        isl = normalize_island(t.get("island"), t.get("location"))
        if is_keys(isl):
            keys_new.append(t)
        elif is_florida(isl):
            fst_candidates.append(t)
        else:
            out_of_region.append(t)

    print("\nExtract filtered:")
    print(f"  Keys (keeping):      {len(keys_new)}")
    print(f"  Florida -> FST:      {len(fst_candidates)}")
    print(f"  Out of region:       {len(out_of_region)}")

    new_by_pk = {int(t["pk"]): t for t in keys_new if t.get("pk")}
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    merged = []
    stats = {"updated": 0, "unchanged": 0, "new": 0, "kept": 0}
    backfilled = {k: 0 for k in BACKFILL}

    for t in keys_new:
        pk = int(t["pk"])
        existing = current_by_pk.get(pk)
        if existing is None:
            rec = dict(t)
            rec["island"] = normalize_island(t.get("island"), t.get("location"))
            rec["needsEnrichment"] = True
            rec["lastUpdated"] = stamp
            merged.append(rec)
            stats["new"] += 1
            continue

        rec = dict(existing)                      # ours wins by default
        changed = False
        for field in BACKFILL:
            if not rec.get(field) and t.get(field):
                rec[field] = t[field]
                backfilled[field] += 1
                changed = True
        isl = normalize_island(existing.get("island"), existing.get("location"))
        if rec.get("island") != isl:
            rec["island"] = isl
            changed = True
        if changed:
            rec["lastUpdated"] = stamp              # ruling 5: only if modified
            stats["updated"] += 1
        else:
            rec = existing                          # identical object, untouched
            stats["unchanged"] += 1
        merged.append(rec)

    # Records only in ours. Kept verbatim — retirement is not this pass.
    for pk, t in current_by_pk.items():
        if pk not in new_by_pk:
            merged.append(t)
            stats["kept"] += 1

    print("\n=== MERGE STATS ===")
    print(f"  new from extract      {stats['new']}")
    print(f"  updated (backfilled)  {stats['updated']}")
    print(f"  unchanged (in both)   {stats['unchanged']}")
    print(f"  kept (ours only)      {stats['kept']}   <- absent upstream, untouched by design")
    print(f"  total merged          {len(merged)}")
    print(f"  backfilled fields     {backfilled}")

    needs = [t for t in merged if t.get("needsEnrichment")]
    print(f"\n  needsEnrichment       {len(needs)}")
    print(f"  null price            {sum(1 for t in merged if t.get('price') in (None, ''))}")

    output = {
        "schemaVersion": current_data.get("schemaVersion", "1.0.8"),
        "lastNormalized": current_data.get("lastNormalized"),
        "tours": merged,
    }
    (REPO / "tours-data-merged.json").write_text(json.dumps(output, indent=2) + "\n")
    if fst_candidates:
        (REPO / "fst-routing-candidates.json").write_text(
            json.dumps(fst_candidates, indent=2) + "\n")
    if out_of_region:
        (REPO / "out-of-region-rejects.json").write_text(
            json.dumps(out_of_region, indent=2) + "\n")

    print("\nWritten: tours-data-merged.json")
    print("tours-data.json NOT modified. Promote only after review.")


if __name__ == "__main__":
    main()
