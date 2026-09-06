#!/usr/bin/env python3
"""Load per-residue CTQW features for the leave-one-family-out regression.
Each rN_minhopH.json.gz: {protein: {cells:{op|score:[AUC,P@5]}, ranks:{op|score:[rank per seed]},
y:[0/1 per seed], seed_resnum, seed_pocket, cluster, pockets:[...]}}.
Feature matrix X (seeds x 221): normalized rank (1=best residue) for each of 13 Ham x 17 scores.
Label y = seed in the drug pocket. GROUP = cluster (family) -> use GroupKFold / leave-one-family-out."""
import json,gzip,glob,numpy as np
def load(path): return json.load(gzip.open(path,"rt"))
def feature_matrix(rec):
    cells=sorted(rec["ranks"].keys()); y=np.array(rec["y"]); ns=len(y)
    X=np.zeros((ns,len(cells)))
    for j,c in enumerate(cells):
        r=np.asarray(rec["ranks"][c],float); X[:,j]=1.0-(r-1)/max(ns-1,1)
    return X,y,cells,rec["cluster"]
if __name__=="__main__":
    R=load("r1_minhop2.json.gz"); ok={k:v for k,v in R.items() if "ranks" in v}
    print("proteins with features:",len(ok),"| families:",len({v['cluster'] for v in ok.values()}))
    X,y,cells,cl=feature_matrix(next(iter(ok.values())))
    print("one protein:",X.shape,"seeds x",len(cells),"features (13 Ham x 17 scores); e.g.",cells[:2])
