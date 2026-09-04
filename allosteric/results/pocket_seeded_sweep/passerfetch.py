#!/usr/bin/env python3
"""Fetch PASSer allosteric-pocket rankings for every distal protein. Cached on disk,
polite concurrency, resumable. Same endpoint/parse as notebook sec 7b."""
import json,os,re,sys,time,urllib.request,urllib.parse,threading
from concurrent.futures import ThreadPoolExecutor
CACHE="passer_cache.json"; MODEL="ensemble"
lock=threading.Lock()
cache=json.load(open(CACHE)) if os.path.exists(CACHE) else {}
work=[w for w in json.load(open("operator_worklist.json")) if w["is_distal"]]
def key(w): return "%s|%s|%s"%(w["pdb"].lower(),w["chain"],MODEL)
def fetch(w):
    k=key(w)
    with lock:
        if k in cache: return "cached"
    d={"pdb":w["pdb"].lower(),"model":MODEL,"top":"all","chain":w["chain"]}
    for a in range(3):
        try:
            req=urllib.request.Request("https://passer.smu.edu/api",
                data=urllib.parse.urlencode(d).encode(),method="POST")
            r=json.load(urllib.request.urlopen(req,timeout=180))
            with lock: cache[k]=r
            return "ok(%d)"%len(r)
        except Exception as e:
            if a==2: return "FAIL %s"%type(e).__name__
            time.sleep(2*(a+1))
t0=time.time(); done=0
with ThreadPoolExecutor(4) as ex:
    for w,r in zip(work,ex.map(fetch,work)):
        done+=1
        if done%20==0:
            with lock: json.dump(cache,open(CACHE,"w"))
            print("  %d/%d (%.0fs)"%(done,len(work),time.time()-t0),flush=True)
        if r.startswith("FAIL"): print("   %s %s"%(w["pdb"],r),flush=True)
json.dump(cache,open(CACHE,"w"))
got=sum(1 for w in work if key(w) in cache)
print("PASSer: %d/%d proteins have rankings (%.0fs)"%(got,len(work),time.time()-t0))
