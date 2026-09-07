#!/usr/bin/env python3
"""THE DECISIVE TEST: does the CTQW beat a pure PROXIMITY baseline on the 630-protein set?

For every protein the pipeline scored, rank its seed residues by graph distance (hops) from the
active site -- no quantum walk, no physics, just "closer to the active site = more likely".
That is the proximity floor. Then compare, on the SAME residues and the SAME labels:
   floor      : AUC of -hop
   CTQW fixed : AUC of one configuration chosen in advance (gauss/sym + neg_dE)
   CTQW best  : AUC of the best of 221 cells (selection ceiling)
Reported per protein and aggregated per FAMILY, with a paired sign test across families.
This is the test Bartosz's mandatory-target work applies; the 1022-protein set has never had it."""
import os,sys,json,gzip,numpy as np,importlib.util
from collections import defaultdict
os.environ["SELECTOR"]="passer_only"
spec=importlib.util.spec_from_file_location("ps","pocketsweep.py"); ps=importlib.util.module_from_spec(spec)
try: spec.loader.exec_module(ps)
except SystemExit: pass
from sklearn.metrics import roc_auc_score
W={w["name"]:w for w in json.load(open("operator_worklist.json"))}
SHARD=int(os.environ.get("SHARD","0")); NS=int(os.environ.get("NSHARD","1"))
OUT=os.environ.get("OUT","prox.json"); CUT=8.0
os.makedirs("pdb_cache",exist_ok=True)   # fetch() writes here; missing dir made every download fail silently
R2=json.load(gzip.open("r2_minhop1.json.gz","rt"))
prot=[n for n,v in R2.items() if "cells" in v and n in W]
prot=[n for i,n in enumerate(sorted(prot)) if i%NS==SHARD]
FIX="gauss|sym|neg_dE"
res=json.load(open(OUT)) if os.path.exists(OUT) else {}
print("shard %d/%d: %d proteins"%(SHARD,NS,len(prot)),flush=True)
for k,n in enumerate(prot,1):
    if n in res: continue
    v=R2[n]; w=W[n]
    try:
        p=ps.fetch(w["pdb"])
        X,idx,ch,bf=ps.ca(p,w["chain"])     # coords, resnum->index, chain, bfactors
        if X is None: res[n]={"err":"no CA"}; continue
        A=[idx[r] for r in w["active"] if r in idx]
        seeds=[idx[r] for r in v["seed_resnum"] if r in idx]
        if not A or len(seeds)!=len(v["seed_resnum"]): res[n]={"err":"index"}; continue
        # contact graph + BFS hops from the active site
        D=np.sqrt(((X[:,None,:]-X[None,:,:])**2).sum(-1)); Adj=(D<CUT)&(D>0)
        NN=len(X); hop=np.full(NN,1e9); q=list(A)
        for a in A: hop[a]=0
        while q:
            u=q.pop(0)
            for w2 in np.where(Adj[u])[0]:
                if hop[w2]>hop[u]+1: hop[w2]=hop[u]+1; q.append(w2)
        y=np.array(v["y"]); h=hop[seeds]
        if y.sum()==0 or y.sum()==len(y): res[n]={"err":"degenerate"}; continue
        floor=roc_auc_score(y,-h)                       # proximity baseline
        fix=v["cells"][FIX][0] if FIX in v["cells"] else None
        best=max(a for a,_ in v["cells"].values())
        res[n]=dict(cluster=w["cluster"],is_distal=bool(w["is_distal"]),n_seeds=len(y),n_drug=int(y.sum()),
                    floor_auc=float(floor),ctqw_fixed_auc=(float(fix) if fix is not None else None),
                    ctqw_best_auc=float(best),mean_hop_drug=float(h[y==1].mean()),mean_hop_other=float(h[y==0].mean()))
    except Exception as e:
        res[n]={"err":str(e)[:60]}
    if k%10==0: json.dump(res,open(OUT,"w")); print("  %d/%d"%(k,len(prot)),flush=True)
json.dump(res,open(OUT,"w"))
print("SHARD %d DONE: %d scored, %d err"%(SHARD,sum(1 for x in res.values() if "floor_auc" in x),sum(1 for x in res.values() if "err" in x)),flush=True)
