#!/usr/bin/env python3
"""s51 — apply the 2026-08-26 would-hide ruling: hidden:true on 50 rows.

Jason's ruling on the s51 would-hide packet (scripts/sweep-availability.py --report,
251 rows at nullConsecutiveSweeps == 2 on sweeps #169 2026-08-08 + #249 2026-08-26):
  bucket A  47 dated / seasonal event listings (4th of July, Lighted Boat Parade, Air Show,
            holiday brunch sails, Lobsterfest, Fantasy Fest, NYE ...) -> hidden
  bucket D  3 catalogue-junk rows -> hidden: 517674 "No Trips - Stay Tuned for Updates!!",
            39898 "Retail ***STAFF USE ONLY***", 561410 "Free Ride"
  buckets B / rest of D  UNTOUCHED — they wait for sweep 3 (dead-operator standard).
  bucket C  allowlisted at operator level in data/operator-allowlist.json (same PR).

MECHANISM. `hidden: true` + `hiddenReason` + `hiddenAt` on the row. app.js drops hidden rows
from cards and the draw pool (same filter line as status/bookingDead). The sweep clears the
hide when a bookable date returns. Nothing is deleted; status stays 'active'.

DETERMINISTIC: the 50 pks are listed here; each is asserted active, nextAvailableDate null,
nullConsecutiveSweeps >= 2, not allowlisted, not already hidden. Exactly 50 rows may change.
usage: python3 scripts/s51-kwst-hide-apply.py [--dry-run]
"""
import json, re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent; TOURS = REPO / 'tours-data.json'
DAY = '2026-08-26'
A = [650888, 445535, 655130, 39948, 273060, 607486, 549352, 620075, 685945, 131757, 238249, 238240, 238251, 686249,
     360003, 129095, 363616, 35191, 11946, 509589, 670042, 359857, 515246, 679443, 488807, 477729, 194193, 743742,
     203677, 343967, 555403, 204565, 350981, 572478, 629507, 635844, 550488, 620549, 621612, 596326, 587427, 674556,
     555056, 743149, 731081, 271043, 271041]
D = {517674: 'placeholder listing "No Trips - Stay Tuned for Updates!!"', 39898: 'operator-internal SKU "Retail ***STAFF USE ONLY***"',
     561410: '"Free Ride" — not a product'}
assert len(A) == 47 and len(set(A)) == 47
rx = re.compile(r'fareharbor\.com/embeds/book/([^/]+)/items/')
def main():
    dry = '--dry-run' in sys.argv
    raw = TOURS.read_text(encoding='utf-8'); doc = json.loads(raw)
    assert json.dumps(doc, indent=2, ensure_ascii=True) + '\n' == raw, 'round-trip'
    allow = set(json.load(open(REPO / 'data' / 'operator-allowlist.json'))['operators'])
    rows = {t['pk']: t for t in doc['tours']}
    before = {pk: json.dumps(t, sort_keys=True) for pk, t in rows.items()}
    for pk in A + list(D):
        t = rows[pk]; sn = rx.search(t['bookingUrl']).group(1)
        assert t['status'] == 'active' and t.get('nextAvailableDate') is None and (t.get('nullConsecutiveSweeps') or 0) >= 2, pk
        # The allowlist exempts an operator from AUTOMATED hide logic; a human ruling still hides a
        # dated listing. Three bucket-A rows are namastekw (allowlisted in this same PR): 555403
        # "...3 DAY TRAINING - 2024 & beyond", 204565 / 350981 New Year's Eve sound baths.
        assert (sn not in allow or pk in (555403, 204565, 350981)) and not t.get('hidden'), pk
        why = (f'bucket A: dated/seasonal event listing' if pk in A else f'bucket D junk: {D[pk]}')
        t['hidden'] = True; t['hiddenAt'] = DAY
        t['hiddenReason'] = (f's51 would-hide ruling {DAY} ({why}); nextAvailableDate null on sweeps 2026-08-08 (#169) and '
                             f'2026-08-26 (#249), nullConsecutiveSweeps={t["nullConsecutiveSweeps"]}; price-preview absent 4/4 dates 2026-08-26 '
                             f'where probed. Reversible: scripts/sweep-availability.py clears hidden when a bookable date returns.')
    changed = [pk for pk, t in rows.items() if json.dumps(t, sort_keys=True) != before[pk]]
    assert sorted(changed) == sorted(A + list(D)) and len(changed) == 50, len(changed)
    if not dry: TOURS.write_text(json.dumps(doc, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
    print('hidden rows written:', len(changed), 'DRY' if dry else 'WRITTEN')
if __name__ == '__main__': main()
