#!/usr/bin/env python3
"""s51 follow-up: pk 611751 — Jason's ruling 2026-08-26: the sole live tier anchors (sole-tier rule,
D-640 lineage). $135 "Four Hour Charter", unit from the tier label verbatim, priceBasis quoting the
description conflict. DETERMINISTIC, no network; asserted against data/s51-kwst-backfill/probe.json."""
import hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent; TOURS = REPO / 'tours-data.json'; EV = REPO / 'data' / 's51-kwst-backfill'
PK, LABEL, PRICE, DAY, SOURCE = 611751, 'Four Hour Charter', 135.0, '2026-08-26', 's51-kwst-611751'
raw = TOURS.read_text(encoding='utf-8'); doc = json.loads(raw)
assert json.dumps(doc, indent=2, ensure_ascii=True) + '\n' == raw
assert hashlib.sha256((EV / 'probe.json').read_bytes()).hexdigest().startswith('186bcb42971bcaa3')
obs = json.load(open(EV / 'probe.json'))['obs'][str(PK)]
sampled = [r for r in obs.values() if r['status'] in ('OK', 'FALLBACK')]
tiers = {(c['singular'], c['price']) for r in sampled for c in r['customer_types']}
assert tiers == {(LABEL, 13500)}, tiers                     # one tier, one price, every sampled reading
valid = sum(1 for r in sampled if r['status'] == 'OK')
t = next(x for x in doc['tours'] if x['pk'] == PK); x = t['_unknownFields']
assert t['price'] is None and x.get('priceHold') == 'shared_named_charter'
before = {y['pk']: json.dumps(y, sort_keys=True) for y in doc['tours']}
t['price'] = PRICE; t['priceLabel'] = LABEL; t['priceConfidence'] = 'high'
x.pop('priceHold', None)
x.update(priceSource=SOURCE, priceVerifiedAt=DAY, priceCustomerType=LABEL, priceTierCount=1, priceTiers=[f'{LABEL} $135'],
         excludedTiers=[], priceMinPartySize=1, priceUnit='four hour charter', unitEvidence=f"tier label: '{LABEL}'",
         priceBasis=(f'{SOURCE} ({DAY}): Jason ruling 2026-08-26 — sole-tier rule (D-640 lineage): the only live tier '
                     f'"{LABEL}" $135 anchors; unit from the tier label verbatim. Description conflict quoted, not resolved: '
                     '"Starting at $135 • Up to 6 People • 4 Hour Shared Option & 4 or 6 Hour Private Tour Options" '
                     '(multiple products named, one purchasable tier; product name says "Shared", tier label says "Charter"). '
                     f'{len(sampled)}/4 dated readings 2026-08-26 ({valid} date-valid), include_breakdown=yes, probe.json sha256 186bcb42971b; '
                     'supersedes s51-kwst-backfill-2 hold shared_named_charter.'))
after = {y['pk']: json.dumps(y, sort_keys=True) for y in doc['tours']}
assert [pk for pk in after if after[pk] != before[pk]] == [PK]
if '--dry-run' not in sys.argv: TOURS.write_text(json.dumps(doc, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
print('611751 -> $135 four hour charter', 'DRY' if '--dry-run' in sys.argv else 'WRITTEN')
