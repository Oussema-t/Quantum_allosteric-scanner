#!/usr/bin/env python3
"""THE MANDATORY ABLATION (Mohtashim/Sajjan/Kais, JACS 2026, DOI 10.1021/jacs.6c08053).
They report CTQW centrality correlates with classical EIGENVECTOR centrality at rho~0.95 on
residue interaction networks. If that holds on our data, the quantum layer is decorative.

Test on OUR 630-protein benchmark, same residues, same labels:
  - CTQW score (our best fixed cell)
  - eigenvector centrality, closeness, betweenness, degree  (all free, all classical)
  - GNM low-mode participation (the ENM baseline the challenge's own text targets)
Report (a) the correlation between CTQW and each, and (b) whether CTQW beats them at the task."""
import os,json,gzip,importlib.util,numpy as np,warnings
warnings.filterwarnings("ignore")
import networkx as nx
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
from collections import defaultdict
os.environ["SELECTOR"]="passer_only"
spec=importlib.util.spec_from_file_location("ps","pocketsweep.py"); ps=importlib.util.module_from_spec(spec)
try: spec.loader.exec_module(ps)
except SystemExit: pass
FR="/Users/t/Quantum_allosteric-scanner/allosteric/results/full_run_1022"
W={w["name"]:w for w in json.load(open("operator_worklist.json"))}
R=json.load(gzip.open(f"{FR}/r2_minhop1.json.gz","rt"))
FIX="gauss|sym|neg_dE"
SHARD=int(os.environ.get("SHARD","0")); NS=int(os.environ.get("NSHARD","1"))
OUT=os.environ.get("OUT","cent.json")
prot=[n for n,v in R.items() if "cells" in v and n in W and FIX in v.get("cells",{})]
prot=[n for i,n in enumerate(sorted(prot)) if i%NS==SHARD]
res=json.load(open(OUT)) if os.path.exists(OUT) else {}
print("shard %d/%d: %d proteins"%(SHARD,NS,len(prot)),flush=True)
for k,n in enumerate(prot,1):
    if n in res: continue
    try:
        v=R[n]; w=W[n]
        p=ps.fetch(w["pdb"]); X,idx,ch,BF=ps.ca(p,w["chain"])
        if X is None: res[n]={"err":"noCA"}; continue
        seeds=[idx[r] for r in v["seed_resnum"] if r in idx]
        if len(seeds)!=len(v["seed_resnum"]): res[n]={"err":"idx"}; continue
        y=np.array(v["y"])
        if y.sum()==0 or y.sum()==len(y): res[n]={"err":"degen"}; continue
        D=np.sqrt(((X[:,None,:]-X[None,:,:])**2).sum(-1)); A=(D<8.0)&(D>0)
        G=nx.from_numpy_array(A.astype(float))
        ev=nx.eigenvector_centrality_numpy(G)
        cl=nx.closeness_centrality(G); bt=nx.betweenness_centrality(G,k=min(80,len(X)),seed=0)
        deg=A.sum(1).astype(float)
        # GNM: Kirchhoff matrix, low-mode participation (the ENM baseline)
        K=np.diag(A.sum(1).astype(float))-A.astype(float)
        wv,V=np.linalg.eigh(K); nz=np.where(wv>1e-8)[0][:10]
        gnm=(V[:,nz]**2).sum(1) if len(nz) else np.zeros(len(X))
        ns=len(y)
        ctqw=1.0-(np.asarray(v["ranks"][FIX],float)-1)/max(ns-1,1)
        base={"eigenvector":np.array([ev[i] for i in seeds]),
              "closeness":np.array([cl[i] for i in seeds]),
              "betweenness":np.array([bt[i] for i in seeds]),
              "degree":deg[seeds],"gnm_lowmode":gnm[seeds]}
        row={"cluster":w["cluster"],"is_distal":bool(w["is_distal"]),"n":int(ns),
             "ctqw_auc":float(roc_auc_score(y,ctqw))}
        for bn,bv in base.items():
            row[bn+"_auc"]=float(roc_auc_score(y,bv))
            row[bn+"_rho"]=float(spearmanr(ctqw,bv).correlation)
        res[n]=row
    except Exception as e:
        res[n]={"err":str(e)[:50]}
    if k%20==0: json.dump(res,open(OUT,"w")); print("  %d/%d"%(k,len(prot)),flush=True)
json.dump(res,open(OUT,"w"))
print("SHARD %d DONE: %d scored"%(SHARD,sum(1 for x in res.values() if "ctqw_auc" in x)),flush=True)
