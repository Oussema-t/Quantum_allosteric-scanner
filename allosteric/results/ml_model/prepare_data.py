#!/usr/bin/env python3
"""Rebuild the ML training data from the saved CTQW results (../full_run_1022/).
Outputs model2_data.npz (residue matrix) and best_per_protein.csv (best config per protein)."""
import json,gzip,glob,os,csv,numpy as np
FR="../full_run_1022"
WL="/Users/t/Downloads/datasets/operator_worklist.json"
TOPOF="/Users/t/Downloads/datasets/topology_features.json"
def load(p): return json.load(gzip.open(p,"rt"))
W={w["name"]:w for w in json.load(open(WL))}
TOPO=json.load(open(TOPOF))
FK=['n_residues','n_edges','mean_degree','degree_var','degree_cv','clustering_coefficient','graph_diameter','algebraic_connectivity','spectral_radius']
R1={H:load(f"{FR}/r1_minhop{H}.json.gz") for H in (1,3)}
R2={H:load(f"{FR}/r2_minhop{H}.json.gz") for H in (1,2,3,4)}
cells=sorted(next(v for v in R1[1].values() if "cells" in v)["cells"])
def topo(n):
    t=TOPO.get("%s|%s|8.0"%(W[n]["pdb"],W[n]["chain"]))
    return [float(t.get(k,0) or 0) for k in FK] if t else None
# --- residue matrix for Model 2 (each protein at its distance-matched MIN_HOP)
X=[];Xt=[];y=[];g=[];pid=[]
for n in R1[1]:
    if n not in W or topo(n) is None: continue
    H=3 if W[n]["is_distal"] else 1
    v=R1[H].get(n)
    if not(v and "cells" in v) or set(v["ranks"])!=set(cells): continue
    yy=np.array(v["y"]); ns=len(yy)
    X.append(np.column_stack([1.0-(np.asarray(v["ranks"][c],float)-1)/max(ns-1,1) for c in cells]))
    Xt.append(np.tile(topo(n),(ns,1))); y.append(yy); g+=[W[n]["cluster"]]*ns; pid+=[n]*ns
X=np.vstack(X).astype(np.float32); Xt=np.vstack(Xt).astype(np.float32); y=np.concatenate(y).astype(np.int8)
np.savez_compressed("model2_data.npz",X=X,Xt=Xt,y=y,g=np.array(g),pid=np.array(pid),cells=np.array(cells),topo_features=np.array(FK))
print("model2_data.npz: %d residues x %d cells | %d families | %.1f MB"%(X.shape[0],X.shape[1],len(set(g)),os.path.getsize("model2_data.npz")/1e6))
# --- best config per protein (best Hamiltonian, score, MIN_HOP)
rows=[]
prots=set()
for R in R2.values(): prots|={n for n,v in R.items() if "cells" in v}
for n in sorted(prots):
    if n not in W: continue
    best=None
    for H,R in R2.items():
        v=R.get(n)
        if not(v and "cells" in v): continue
        c,(a,p)=max(v["cells"].items(),key=lambda kv:kv[1][0])
        if best is None or a>best[0]: best=(a,p,c,H)
    if best:
        a,p,c,H=best; w_,nm,s=c.split("|",2)
        rows.append(dict(protein=n,cluster=W[n]["cluster"],is_distal=int(W[n]["is_distal"]),
                         best_ham=w_+"/"+nm,best_score=s,best_minhop=H,auc=round(a,4),p5=p))
with open("best_per_protein.csv","w",newline="") as fh:
    wr=csv.DictWriter(fh,fieldnames=["protein","cluster","is_distal","best_ham","best_score","best_minhop","auc","p5"]); wr.writeheader(); wr.writerows(rows)
print("best_per_protein.csv: %d proteins, %d families"%(len(rows),len({r['cluster'] for r in rows})))
