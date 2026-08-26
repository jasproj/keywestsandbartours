#!/usr/bin/env python3
"""s51-kwst-backfill-2 — apply the class rulings on the 22 rows #250 HELD for ruling.

DETERMINISTIC. No network. Every anchor below is asserted against the committed live evidence
(data/s51-kwst-backfill/probe.json, the 4-date probe of 2026-08-26) before a byte is written; one
failed assert aborts the run. The published figure is the floor of the anchor tier across every
sampled reading (observedPriceRange stamped when it moved).

CLASS RULINGS (Jason, 2026-08-26, applied per row):
  (a) duration-only ladders — unit derivation chain in order: tier label -> description quoted
      verbatim in priceBasis -> product name quoted verbatim. A per-hour/per-day (rental) shape:
      floor tier anchors with the tier label verbatim as unit. No unit from any source: stays HELD.
  (b) unit+increment ladders — the base unit anchors; the increment never (add-on logic, D-637/D-629).
      Escalate only if the increment is the only purchasable entry (none here).
  (c) "Shared" listings with a charter-shaped tier — the shared per-person tier anchors (D-624); the
      charter tier is the whole-boat variant of the same product and never anchors on a shared listing.
  (d) 574540 (headcount conflict) and 481847 (no unit) stay HELD, named gaps.

STAMPS: priceSource s51-kwst-backfill-2, priceCustomerType, priceTierCount, priceTiers, excludedTiers,
priceMinPartySize, priceVerifiedAt 2026-08-26, priceBasis (ruling + verbatim source + evidence),
priceUnit + unitEvidence, observedPriceRange when the anchor moved; priceConfidence high; priceHold removed.
Rows that stay HELD get their priceHold reason re-stated with the class ruling that kept them held.

usage: python3 scripts/s51-kwst-backfill-2.py [--dry-run]
"""
import collections, hashlib, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOURS = REPO / 'tours-data.json'
EV = REPO / 'data' / 's51-kwst-backfill'
SOURCE, PREV, DAY = 's51-kwst-backfill-2', 's51-kwst-backfill', '2026-08-26'
PROBE_SHA = '186bcb42971bcaa30fa5245da45a83a46c5ee61c28548ffe0831b9ce1bd8a351'


def money(n): return f'${n:,.0f}' if abs(n - round(n)) < 0.005 else f'${n:,.2f}'


# pk -> (class, anchor tier singular, expected price, priceUnit, unitEvidence, note-for-basis)
RULINGS = {
    # ---- (a) duration-only ladders: description "Up to N Passengers" quoted verbatim (in-repo precedent:
    #      315237 / 739260 unitEvidence "description: 'Up to 6 People'"); floor tier anchors.
    499277: ('a', 'Four Hours', 699.0, 'whole boat · up to 4 passengers', "description: 'Up to 4 Passengers'", 'per-duration ladder (Four/Eight Hours); description "Starting at $699 • Up to 4 Passengers • 4-8 Hours"'),
    499289: ('a', 'Six Hours', 1000.0, 'whole boat · up to 6 passengers', "description: 'Up to 6 Passengers'", 'per-duration ladder (Six/Eight Hours); description "Up to 6 Passengers • 6-8 Hours"'),
    499297: ('a', 'Four Hours', 650.0, 'whole boat · up to 6 passengers', "description: 'Up to 6 Passengers'", 'per-duration ladder (Four/Six/Eight Hours); description "Up to 6 Passengers • 4-8 Hours"'),
    499303: ('a', 'Four Hours', 650.0, 'whole boat · up to 6 passengers', "description: 'Up to 6 Passengers'", 'per-duration ladder (Four/Six/Eight Hours); description "Up to 6 Passengers • 4-8 Hours"'),
    460374: ('a', '3/4 Day', 1500.0, 'whole boat · up to 6 passengers', "description: 'Up to 6 Passengers'", 'per-duration ladder (3/4 Day 6 Hours / Full Day 8 Hours); description "For all ages! • 6-8 hours • Up to 6 Passengers"'),
    460378: ('a', 'Half Day Reef', 950.0, 'whole boat · up to 6 passengers', "description: 'Up to 6 Passengers'", 'per-duration ladder (Half Day 4h / 3/4 Day 6h / Full Day 8h); description "For all ages! • 4-8 hours • Up to 6 Passengers"'),
    # ---- (a) per-day rental shape, no headcount in label/description/product name: floor tier anchors,
    #      tier label verbatim as unit.
    659695: ('a', '3/4 Day Trip', 1595.0, '3/4 day trip', "tier label: '3/4 Day Trip' (note '6 Hours')", 'per-day ladder (3/4 Day 6h / Full Day 8h / Ten Hour 10h); no headcount or per-person wording in label, description or product name'),
    659699: ('a', '3/4 Day Trip', 1595.0, '3/4 day trip', "tier label: '3/4 Day Trip' (note '6 Hours')", 'per-day ladder (3/4 Day 6h / Full Day 8h / Ten Hour 10h); no headcount or per-person wording in label, description or product name'),
    692953: ('a', '2-Hour Sunset Cruise', 150.0, '2-hour sunset cruise', "tier label: '2-Hour Sunset Cruise'", 'per-hour ladder of 11 duration/activity tiers ($150 2-Hour Sunset Cruise .. $3,000 Deep Drop); floor tier anchors; description empty; product name "45\' Hatteras Express" carries no unit'),
    # ---- (b) unit + increment: base unit anchors, increment never.
    167087: ('b', 'Bachelor/ette or Birthday Group', 300.0, 'flat rate for up to 10 people', "tier note: 'Flat rate for up to 10 people'", 'increment tier "Additional Participant" $25 (11 or more people) never anchors; description says "Starting at $250" — live base $300 (D-649 conflict flagged, live wins)'),
    167094: ('b', 'Bachelor/ette or Birthday Group', 400.0, 'flat rate for up to 10 people', "tier note: 'Flat rate for up to 10 people'", 'increment tier "Additional Participant" $37.50 never anchors; description says "Starting at $375" — live base $400 (D-649 conflict flagged, live wins)'),
    395018: ('b', 'Bachelor/ette or Birthday Group', 400.0, 'flat rate for up to 10 people', "tier note: 'Flat rate for up to 10 people'", 'increment tier "Additional Participant" $37.50 never anchors; description says "Starting at $375" — live base $400 (D-649 conflict flagged, live wins)'),
    395019: ('b', 'Bachelor/ette or Birthday Group', 300.0, 'flat rate for up to 10 people', "tier note: 'Flat rate for up to 10 people'", 'increment tier "Additional Participant" $25 never anchors; description says "Starting at $250" — live base $300 (D-649 conflict flagged, live wins)'),
    232507: ('b', 'Four Hours', 1299.0, 'whole boat · base rate for 8 people', "product name: 'Salty Bottom Party Boat'; tier note: 'Base rate for 8 People'", 'increment is note-only ("If more than 8 people attending, please advise in the drop-down"), no purchasable increment tier; base rate anchors'),
    698002: ('b', 'Two Hour Sunset', 425.0, 'whole boat · up to 6 passengers', "product name: 'Salty Max Center Console (up to 6 Passengers)'", 'floor tier "Two Hour Sunset" carries no note; the Four/Six Hours tiers say "Base rate for 8 People" on a product named "up to 6 Passengers" (D-649 conflict flagged, product name quoted as the unit source)'),
    279365: ('b', 'Private Tour up to 4 People for 1.5 Hours', 275.0, 'private tour · up to 4 people', "tier label: 'Private Tour up to 4 People for 1.5 Hours'", 'increment tier "Additional Person" $39 never anchors; walking tour, not a vessel'),
    639774: ('b', 'Private Tour For Up to 6 people', 879.0, 'private tour · up to 6 people', "tier label: 'Private Tour For Up to 6 people'", 'increment tier "Additional Person" $49 never anchors; road tour, not a vessel'),
    # ---- (c) shared listing: the shared per-person tier anchors.
    587954: ('c', 'Shared Snorkeling Tour for 1-6 Persons Minimum 3 Persons 89.00', 98.11, 'per person', "tier note: '$89.00 per person 1-6 persons 3 person minimum'", 'shared per-person tier is the only tier; live price $98.11 vs "$89.00" in label/note (D-649 conflict flagged, live wins); min party 3'),
}
STAY_HELD = {
    742608: ('a', 'stays HELD (class a): "One Session" $45 / "Two Session" $55 — no unit in tier label, no description, product name "Aquabana 1HR" names no unit; per-session is not a per-hour/per-day rental shape; not guessed'),
    611751: ('c', 'stays HELD (class c, escalated): the only live tier is the charter-shaped "Four Hour Charter" $135; no shared per-person tier exists in the ladder, and a charter tier never anchors on a "Shared" listing. Description: "Starting at $135 • Up to 6 People • 4 Hour Shared Option & 4 or 6 Hour Private Tour Options"'),
    574540: ('d', 'stays HELD (class d, named gap): label "Dinner Cruise 6 People" vs note/description "Up to 12 People" — conflicting headcounts'),
    481847: ('d', 'stays HELD (class d, named gap): "Private Trip • One to Two People" $700 ladder has no vessel/vehicle word in label, description ("For all ages! • 4 hours • Up to 4 People") or product name'),
}


def main():
    dry = '--dry-run' in sys.argv
    raw = TOURS.read_text(encoding='utf-8'); doc = json.loads(raw)
    assert json.dumps(doc, indent=2, ensure_ascii=True) + '\n' == raw, 'round-trip'
    assert hashlib.sha256((EV / 'probe.json').read_bytes()).hexdigest() == PROBE_SHA, 'probe.json drifted'
    ev = json.load(open(EV / 'probe.json'))
    held = {t['pk']: t for t in doc['tours'] if (t.get('_unknownFields') or {}).get('priceSource') == PREV
            and (t.get('_unknownFields') or {}).get('priceHold') not in (None, 'UNSAMPLED', 'zero_price')}
    assert set(held) == set(RULINGS) | set(STAY_HELD) and len(held) == 22, sorted(held)
    before = {t['pk']: json.dumps(t, sort_keys=True) for t in doc['tours']}
    summary = []
    for pk, (cls, label, expect, unit, uev, why) in RULINGS.items():
        t = held[pk]; x = t['_unknownFields']
        assert t['price'] is None
        sampled = [r for r in ev['obs'][str(pk)].values() if r['status'] in ('OK', 'FALLBACK')]
        prices = [c['price'] / 100 for r in sampled for c in (r.get('customer_types') or []) if c.get('singular') == label and c.get('price')]
        assert prices, f'{pk}: anchor {label!r} not in live evidence'
        lo, hi = min(prices), max(prices)
        assert lo == expect, f'{pk}: floor {lo} != ruled {expect}'
        maj = collections.Counter(json.dumps([[c.get('singular'), c.get('note'), c.get('price'), c.get('min_party_size')] for c in r.get('customer_types') or []]) for r in sampled).most_common(1)[0][0]
        tiers = [{'singular': a, 'note': b or '', 'price': (c or 0) / 100, 'min': d} for a, b, c, d in json.loads(maj)]
        anchor = next(q for q in tiers if q['singular'] == label)
        def tstr(q): return f"{q['singular']} {money(q['price'])}" + (f" ({q['note']})" if q['note'] else '') + (f" (min {q['min']})" if q.get('min') and q['min'] > 1 else '')
        pos = [q for q in tiers if q['price'] > 0]
        t['price'] = float(lo); t['priceLabel'] = label; t['priceConfidence'] = 'high'
        x['priceSource'] = SOURCE; x['priceVerifiedAt'] = DAY; x.pop('priceHold', None)
        x['priceCustomerType'] = label; x['priceTierCount'] = len(pos); x['priceTiers'] = [tstr(q) for q in tiers]
        x['excludedTiers'] = [tstr(q) for q in pos if q is not anchor]; x['priceMinPartySize'] = anchor.get('min')
        x['priceUnit'] = unit; x['unitEvidence'] = uev
        if hi > lo: x['observedPriceRange'] = [lo, hi]
        valid = sum(1 for r in sampled if r['status'] == 'OK')
        x['priceBasis'] = (f'{SOURCE} ({DAY}): class ({cls}) ruling — "{label}" {money(lo)}' + (f' (note "{anchor["note"]}")' if anchor['note'] else '')
                           + f', unit "{unit}" ({uev}); {why}' + (f'; not anchoring: {", ".join(x["excludedTiers"])}' if x['excludedTiers'] else '')
                           + (f'; anchor varied {money(lo)}-{money(hi)} (floor published)' if hi > lo else '')
                           + f'; {len(sampled)}/4 dated readings 2026-08-26 ({valid} date-valid), include_breakdown=yes, probe.json sha256 {PROBE_SHA[:12]}; supersedes {PREV} hold')
        summary.append({'pk': pk, 'class': cls, 'name': t['name'], 'price': t['price'], 'label': label, 'unit': unit, 'disposition': 'priced'})
    for pk, (cls, why) in STAY_HELD.items():
        t = held[pk]; x = t['_unknownFields']
        x['priceSource'] = SOURCE; x['priceVerifiedAt'] = DAY
        x['priceBasis'] = f'{SOURCE} ({DAY}): {why}. Prior: {x["priceBasis"]}'
        summary.append({'pk': pk, 'class': cls, 'name': t['name'], 'price': None, 'disposition': 'HELD'})
    after = {t['pk']: json.dumps(t, sort_keys=True) for t in doc['tours']}
    changed = [pk for pk in after if after[pk] != before[pk]]
    assert set(changed) == set(held), 'rows outside the 22 changed'
    json.dump({'stampedOn': DAY, 'rowsChanged': len(changed), 'priced': len(RULINGS), 'held': len(STAY_HELD), 'summary': summary},
              open(EV / ('backfill-2-summary.dryrun.json' if dry else 'backfill-2-summary.json'), 'w'), indent=1)
    if not dry: TOURS.write_text(json.dumps(doc, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
    print(f'changed {len(changed)} priced {len(RULINGS)} held {len(STAY_HELD)}', 'DRY' if dry else 'WRITTEN')


if __name__ == '__main__':
    main()
