#!/usr/bin/env python3
"""Apply buckets (a) and (b) to tours-data.json. Writes ONLY those rows."""
import json, sys, collections
S='/tmp/claude-501/-Users-jasondudney-repos-keywestsandbartours/d33ebf2f-0774-41a0-a9fa-faff89978da0/scratchpad/bf'
REPO='/Users/jasondudney/repos/keywestsandbartours'
DRY = '--execute' not in sys.argv

cls=json.load(open(S+'/classified2.json'))
writes={e['pk']:e for e in cls if e['bucket'] in ('a','b')}
raw=open(REPO+'/tours-data.json').read()
doc=json.loads(raw)

assert json.dumps(doc, indent=2, ensure_ascii=True)+'\n' == raw, 'serialization does not round-trip'

n=0; byconf=collections.Counter()
for t in doc['tours']:
    e=writes.get(t['pk'])
    if not e: continue
    assert t['price'] is None, f"pk {t['pk']} is not unpriced — refusing to overwrite {t['price']!r}"
    t['price']=e['price']
    t['priceConfidence']=e['confidence']
    t['priceLabel']=e['pick']                      # the FareHarbor customer type name
    uf=t.get('_unknownFields') or {}
    uf['priceSource']='fh-price-preview-v2-2026-08-20'
    uf['priceCustomerType']=e['pick']
    uf['priceTierCount']=e['n_tiers']
    t['_unknownFields']=uf
    n+=1; byconf[e['confidence']]+=1

print(f'rows to write: {len(writes)}  applied: {n}')
for k,v in byconf.most_common(): print(f'   priceConfidence={k}: {v}')
if DRY:
    print('DRY RUN — nothing written. Pass --execute to apply.')
else:
    out=json.dumps(doc, indent=2, ensure_ascii=True)+'\n'
    open(REPO+'/tours-data.json','w').write(out)
    print('WRITTEN')
