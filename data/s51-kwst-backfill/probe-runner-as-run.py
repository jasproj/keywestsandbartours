#!/usr/bin/env python3
"""s51 backfill probe. READ-ONLY. 4 dates, include_breakdown=yes, 1 req/s, <=20 pks/batch,
bounded retries (3, backoff), exact reconciliation: every (pk,date) gets exactly one status."""
import json, sys, time, collections, urllib.request, urllib.error
S=sys.argv[1]; DATES=["2026-08-29","2026-09-05","2026-09-19","2026-10-10"]
API="https://fareharbor.com/api/embed/{sn}/price-preview/per-item/v2/?item_pks={pks}&include_breakdown=yes&date={date}"
UA="WanderRenderMonitor/1.0 (+internal-qa)"; BATCH=20; SLEEP=1.0; RETRIES=3
def fetch(sn,pks,day):
    url=API.format(sn=sn,pks=",".join(map(str,pks)),date=day)
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json","Referer":f"https://fareharbor.com/embeds/book/{sn}/"})
    for a in range(RETRIES):
        try:
            with urllib.request.urlopen(req,timeout=30) as r: return r.status,r.read().decode("utf-8","replace"),None,a
        except urllib.error.HTTPError as e:
            if e.code in (400,404): return e.code,None,f"HTTP {e.code}",a
            err=f"HTTP {e.code}"
        except Exception as e: err=str(e)[:140]
        time.sleep(SLEEP*(2**a))
    return None,None,err,RETRIES
targets=json.load(open(S+"/targets.json"))
bysn=collections.defaultdict(list)
for t in targets: bysn[t["sn"]].append(t["pk"])
c,_,e,_=fetch("definitely-not-a-real-fh-shortname-zzz",[1],DATES[0]); print("[control]",c,e,file=sys.stderr)
if c==200: sys.exit("not falsifiable")
obs=collections.defaultdict(dict); http={}; nreq=0; retries=0
for day in DATES:
    for sn in sorted(bysn):
        pks=sorted(set(bysn[sn]))
        for j in range(0,len(pks),BATCH):
            chunk=pks[j:j+BATCH]; st,body,err,a=fetch(sn,chunk,day); nreq+=1; retries+=a
            http[(sn,day,j)]=st
            if err or not body or not body.lstrip().startswith("{"):
                for pk in chunk: obs[pk][day]={"status":"ERROR","http":st,"err":err or "non-JSON"}
                time.sleep(SLEEP); continue
            data=json.loads(body); seen={int(it.get("id",-1)):it for it in data.get("items") or []}
            for pk in chunk:
                it=seen.get(pk)
                if it is None: obs[pk][day]={"status":"UNSAMPLED","http":st}; continue
                av=it.get("availability") or {}; sa=av.get("start_at"); valid=bool(sa) and sa[:10]==day
                pr=it.get("price") or {}; br=pr.get("breakdown") or {}
                obs[pk][day]={"status":"OK" if valid else "FALLBACK","http":st,"start_at":sa,"end_at":av.get("end_at"),
                    "low":pr.get("low"),"high":pr.get("high"),"capacity":av.get("capacity"),
                    "customer_types":br.get("customer_types"),"raw_keys":sorted(it.keys()),"av_keys":sorted(av.keys()),"pr_keys":sorted(pr.keys()),"br_keys":sorted(br.keys())}
            time.sleep(SLEEP)
    print("date",day,"done reqs",nreq,file=sys.stderr)
# reconcile
miss=[(t["pk"],d) for t in targets for d in DATES if d not in obs[t["pk"]]]
assert not miss, miss
assert len(obs)==len(targets)
json.dump({"dates":DATES,"probedAt":time.strftime("%Y-%m-%dT%H:%M:%S"),"requests":nreq,"retries":retries,"control":{"code":c,"falsifiable":c!=200},
           "http":{f"{k[0]}|{k[1]}|{k[2]}":v for k,v in http.items()},"obs":{str(k):v for k,v in obs.items()}},open(S+"/probe_s51.json","w"),indent=1)
print("DONE",nreq,"requests",retries,"retries",file=sys.stderr)
