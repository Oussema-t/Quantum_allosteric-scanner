#!/usr/bin/env python3
"""THE UNCONSTRAINED TEST — no pipeline funnel.
Every algorithm ranks ALL residues of the protein, not the ~40 the pipeline pre-selected.
Truth = drug-binding residues (<=4.5 A from the drug in holo). Active site excluded from scoring.

This asks: is the result coming from the quantum walk, or from PASSer + veto + MIN_HOP doing the
selection? Reported alongside the constrained numbers so the funnel's contribution is visible."""
import os,json,gzip,importlib.util,numpy as np,warnings
warnings.filterwarnings("ignore")
import networkx as nx
from scipy.linalg import eigh
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from sklearn.metrics import roc_auc_score
os.environ["SELECTOR"]="passer_only"
spec=importlib.util.spec_from_file_location("ps","pocketsweep.py"); ps=importlib.util.module_from_spec(spec)
try: spec.loader.exec_module(ps)
except SystemExit: pass
FR=os.environ.get("FR",".")
W={w["name"]:w for w in json.load(open("operator_worklist.json"))}
R=json.load(gzip.open(f"{FR}/r2_minhop1.json.gz","rt"))
SHARD=int(os.environ.get("SHARD","0")); NS=int(os.environ.get("NSHARD","1")); OUT=os.environ.get("OUT","un.json")
prot=[n for n,v in R.items() if "cells" in v and n in W]
prot=[n for i,n in enumerate(sorted(prot)) if i%NS==SHARD]
res=json.load(open(OUT)) if os.path.exists(OUT) else {}
print("shard %d/%d: %d proteins"%(SHARD,NS,len(prot)),flush=True)
for k,n in enumerate(prot,1):
    if n in res: continue
    try:
        w=W[n]; p=ps.fetch(w["pdb"]); X,idx,ch,BF=ps.ca(p,w["chain"])
        if X is None or len(X)<30: res[n]={"err":"noCA"}; continue
        A_idx=[idx[r] for r in w["active"] if r in idx]
        T=set(idx[r] for r in w["truth"] if r in idx)
        if not A_idx or not T: res[n]={"err":"sites"}; continue
        # ALL residues except the active site itself -- no pipeline funnel
        cand=[i for i in range(len(X)) if i not in set(A_idx)]
        y=np.array([1 if i in T else 0 for i in cand])
        if y.sum()==0 or y.sum()==len(y): res[n]={"err":"degen"}; continue
        D2=((X[:,None,:]-X[None,:,:])**2).sum(-1); Adj=((D2<64.0)&(D2>0)).astype(float)
        deg=Adj.sum(1); L=np.diag(deg)-Adj
        G=nx.from_numpy_array(Adj)
        ev=nx.eigenvector_centrality_numpy(G); cl=nx.closeness_centrality(G)
        act=np.array(sorted(A_idx))
        evl,V=eigh(L)
        gaps=np.diff(np.sort(evl)); gp=max(float(gaps[gaps>1e-9].min()) if (gaps>1e-9).any() else 1e-4,1e-4)
        heat=np.zeros(len(X))
        for t in np.linspace(0.0,1.0/gp,32): heat+=((V*np.exp(-evl*t))@V.T)[:,act].sum(1)
        Cinv=np.linalg.pinv(L); dd=np.sqrt(np.clip(np.diag(Cinv),1e-12,None))
        dcc=(Cinv/np.outer(dd,dd))[:,act].mean(1)
        adj=csr_matrix((Adj>0).astype(np.int8))
        hop=dijkstra(adj,directed=False,indices=A_idx,unweighted=True,min_only=True)
        hop=np.where(np.isfinite(hop),hop,hop[np.isfinite(hop)].max()+1)
        sc={"closeness":np.array([cl[i] for i in cand]),
            "eigenvector":np.array([ev[i] for i in cand]),
            "degree":deg[cand],
            "heat_kernel":heat[cand],
            "gnm_dcc":dcc[cand],
            "neg_hop":-hop[cand]}
        row={"cluster":w["cluster"],"is_distal":bool(w["is_distal"]),
             "n_candidates":len(cand),"n_drug":int(y.sum())}
        for nm,v_ in sc.items():
            v_=np.nan_to_num(np.asarray(v_,float))
            o=np.argsort(-v_)
            row[nm+"_auc"]=float(roc_auc_score(y,v_)); row[nm+"_p5"]=float(y[o[:5]].sum())/5.0
        res[n]=row
    except Exception as e: res[n]={"err":str(e)[:50]}
    if k%15==0: json.dump(res,open(OUT,"w")); print("  %d/%d"%(k,len(prot)),flush=True)
json.dump(res,open(OUT,"w"))
print("SHARD %d DONE: %d scored"%(SHARD,sum(1 for x in res.values() if "closeness_auc" in x)),flush=True)
