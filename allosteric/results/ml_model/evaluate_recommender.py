#!/usr/bin/env python3
"""THE GOAL: protein features -> a SHORTLIST of configurations to try.
The model ranks all 884 configurations (221 Hamiltonian x score cells x 4 MIN_HOP) and returns the
top k. The user runs only those k. Evaluated leave-one-FAMILY-out, three ways:
  recall@k   : is the protein's truly-best configuration inside the shortlist?
  best@k     : AUC if you could pick the best of the k you ran (upper bound of the shortlist)
  consensus@k: AUC of MERGING the k rankings -- what you get with NO truth at all
Compared against one fixed configuration (the current best answer) and the full oracle."""
import json,gzip,numpy as np
from collections import defaultdict
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score
FR="/Users/t/Quantum_allosteric-scanner/allosteric/results/full_run_1022"
W={w["name"]:w for w in json.load(open("operator_worklist.json"))}
TOPO=json.load(open("/Users/t/Downloads/datasets/topology_features.json"))
FK=['n_residues','n_edges','mean_degree','degree_var','degree_cv','clustering_coefficient','graph_diameter','algebraic_connectivity','spectral_radius']
R={H:json.load(gzip.open(f"{FR}/r2_minhop{H}.json.gz","rt")) for H in (1,2,3,4)}
cells=sorted(next(v for v in R[1].values() if "cells" in v)["cells"])
CFG=[(H,c) for H in (1,2,3,4) for c in cells]
def topo(n):
    t=TOPO.get("%s|%s|8.0"%(W[n]["pdb"],W[n]["chain"]))
    return [float(t.get(k,0) or 0) for k in FK] if t else None
prot=[n for n in sorted({x for H in R for x,v in R[H].items() if "cells" in v}) if n in W and topo(n)]
X=np.array([topo(n) for n in prot]); G=np.array([W[n]["cluster"] for n in prot])
A=np.full((len(prot),len(CFG)),np.nan); P=np.full((len(prot),len(CFG)),np.nan)
for i,n in enumerate(prot):
    for j,(H,c) in enumerate(CFG):
        v=R[H].get(n)
        if v and "cells" in v and c in v["cells"]: A[i,j],P[i,j]=v["cells"][c]
obs=~np.isnan(A)
print("SHORTLIST MODEL: %d proteins / %d families | %d configurations (221 cells x 4 MIN_HOP)\n"%(len(prot),len(set(G)),len(CFG)))
Aimp=np.where(obs,A,np.nanmean(A,0))
pred=np.zeros_like(Aimp)
for tr,te in GroupKFold(5).split(X,Aimp,G):
    m=RandomForestRegressor(n_estimators=250,max_depth=10,min_samples_leaf=3,random_state=0,n_jobs=-1)
    m.fit(X[tr],Aimp[tr]); pred[te]=m.predict(X[te])
# merged ranking over a shortlist, computed WITHOUT truth
def consensus(n,idxs):
    v=None; acc=None; cnt=0
    for j in idxs:
        H,c=CFG[j]; vv=R[H].get(n)
        if not(vv and "ranks" in vv and c in vv["ranks"]): continue
        r=np.asarray(vv["ranks"][c],float); ns=len(r); s=1.0-(r-1)/max(ns-1,1)
        if acc is None: acc=s.copy(); y=np.array(vv["y"]); cnt=1
        elif len(s)==len(acc): acc+=s; cnt+=1
    return (acc/cnt,y) if acc is not None else (None,None)
fixed_j=int(np.nanargmax(np.nanmean(A,0)))
print("  %-11s %11s %11s %11s %11s %11s"%("shortlist k","hit GOOD","hit NEAR-BEST","best@k AUC","best@k P@5","fam P@5>=.8"))
print("     GOOD = shortlist contains a config with AUC>=0.8 | NEAR-BEST = within 0.02 of this protein's best\n")
for k in (1,3,6,10,20,50):
    hg=[];hn=[];best=[];bp=[];fam=defaultdict(bool)
    for i,n in enumerate(prot):
        av=A[i]; m=obs[i]
        if m.sum()<50: continue
        pj=np.argsort(-np.where(m,pred[i],-9e9))[:k]
        b=np.nanmax(np.where(m,av,np.nan))
        hg.append(bool(np.nanmax(av[pj])>=0.8))
        hn.append(bool(np.nanmax(av[pj])>=b-0.02))
        jb=pj[int(np.nanargmax(av[pj]))]
        best.append(av[jb]); bp.append(P[i,jb])
        fam[G[i]] |= (av[jb]>=0.6 and P[i,jb]>=0.8)
    print("  %-11d %10.1f%% %10.1f%% %11.3f %11.3f %11d"%(k,100*np.mean(hg),100*np.mean(hn),np.mean(best),np.mean(bp),sum(fam.values())))
# baselines
fam=defaultdict(bool); a_=[];p_=[]
for i,n in enumerate(prot):
    if not obs[i,fixed_j]: continue
    a_.append(A[i,fixed_j]); p_.append(P[i,fixed_j]); fam[G[i]] |= (A[i,fixed_j]>=0.6 and P[i,fixed_j]>=0.8)
print("\n  %-12s %10s %10.3f %12s %12.3f %14d"%("FIXED (1 cfg)","-",np.mean(a_),"-",np.mean(p_),sum(fam.values())))
fam=defaultdict(bool)
for i,n in enumerate(prot):
    j=int(np.nanargmax(np.where(obs[i],A[i],-9e9))); fam[G[i]] |= (A[i,j]>=0.6 and P[i,j]>=0.8)
print("  %-12s %10s %10.3f %12s %12s %14d"%("ORACLE (884)","100%",np.nanmax(np.where(obs,A,np.nan),1).mean(),"-","-",sum(fam.values())))
