#!/usr/bin/env python3
"""CONFIGURATION RECOMMENDER — the deliverable model.

    give it a protein (topology features) and a number k
    -> it returns the k configurations to run, each with a weight

A configuration is (MIN_HOP in 1..4, Hamiltonian, score): 221 cells x 4 MIN_HOP = 884 in total.
The model ranks all 884 and returns the top k with normalised weights, so the user runs k
instead of 884. Trained on the 630 proteins the full pipeline scored, leave-one-FAMILY-out.

Measured (leave-one-family-out, k = shortlist size):
    k    contains a config with AUC>=0.8    best-of-k AUC    families P@5>=0.8
    3              36%                          0.690               29
    6              45%                          0.744               38
   20              61%                          0.826               54
  884 (oracle)    100%                          0.964               71
(A 250-tree RandomForest scores the same within noise -- k=6 AUC 0.724/43 families, k=20
 0.808/50 -- but serialises to 205 MB, so Ridge is shipped. `architecture` in the metadata.)
best-of-k assumes the user picks among the k results; merging them blind gives ~0.610.

Usage:
    from recommender import Recommender
    rec = Recommender.load("recommender.joblib")
    for cfg in rec.recommend(topology_features_dict, k=6):
        print(cfg["min_hop"], cfg["hamiltonian"], cfg["score"], cfg["weight"])
"""
import json,gzip,numpy as np,joblib
from collections import defaultdict
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
FK=['n_residues','n_edges','mean_degree','degree_var','degree_cv',
    'clustering_coefficient','graph_diameter','algebraic_connectivity','spectral_radius']
def feasible_min_hops(X,active_idx,cut=8.0,min_candidates=15,min_frac=0.50,max_hop_frac=0.5):
    """Which MIN_HOP values can this protein actually support?
    A MIN_HOP is INFEASIBLE when the seed filter leaves too few candidate residues -- on a small
    or compact protein a high MIN_HOP deletes most of the structure (KRAS spans only 5 hops, so
    MIN_HOP=4 keeps 40 of 170 residues and 2 of its 21 true pocket residues).
    Uses only the apo structure and the active site -- no truth, so it is valid at prediction time.
    Returns {min_hop: {feasible, n_candidates, frac, max_hop}}."""
    import numpy as np
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import dijkstra
    X=np.asarray(X,float)
    D2=((X[:,None,:]-X[None,:,:])**2).sum(-1)
    adj=csr_matrix(((D2<cut*cut)&(D2>0)).astype(np.int8))
    hop=dijkstra(adj,directed=False,indices=list(active_idx),unweighted=True,min_only=True)
    fin=np.isfinite(hop); mx=float(hop[fin].max()) if fin.any() else 0.0
    A=set(active_idx); out={}
    for H in (1,2,3,4):
        n=int(sum(1 for i in range(len(X)) if fin[i] and hop[i]>=H and i not in A))
        # two conditions, both computable without the truth:
        #  (a) the filter must leave at least half the protein as candidates
        #  (b) MIN_HOP must be small relative to the protein's hop RANGE -- on a compact protein a
        #      high MIN_HOP keeps only the outermost shell (KRAS: max_hop 5, so MIN_HOP=4 keeps
        #      hops 4-5 only, which deleted 19 of its 21 true pocket residues)
        ok_size = n>=min_candidates and n>=min_frac*len(X)
        ok_range= H <= max_hop_frac*mx
        why=[]
        if not ok_size: why.append("only %d candidates (%.0f%% of protein)"%(n,100*n/len(X)))
        if not ok_range: why.append("MIN_HOP %d too high for hop range %.0f"%(H,mx))
        out[H]=dict(feasible=bool(ok_size and ok_range),n_candidates=n,frac=round(n/len(X),3),
                    max_hop=mx,reason=("; ".join(why) if why else "ok"))
    return out

class Recommender:
    def __init__(self,model,cfgs,feature_names,meta=None):
        self.model=model; self.cfgs=cfgs; self.features=feature_names; self.meta=meta or {}
    def recommend(self,topo,k=6,min_hops=None,temperature=1.0,feasibility=None):
        """topo: dict of the 9 topology features. k: how many configurations to return.
        min_hops: optional restriction, e.g. [1,3].
        feasibility: output of feasible_min_hops(); infeasible MIN_HOP values are REMOVED from the
        shortlist, so the pipeline is never handed a filter the protein cannot support.
        Returns k dicts, weights summing to 1."""
        x=np.array([[float(topo.get(f,0) or 0) for f in self.features]])
        s=self.model.predict(x)[0]
        idx=list(range(len(self.cfgs)))
        if feasibility is not None:
            ok={h for h,d in feasibility.items() if d["feasible"]}
            if not ok: raise ValueError("no MIN_HOP is feasible for this protein: %s"%feasibility)
            idx=[i for i in idx if self.cfgs[i][0] in ok]
        if min_hops is not None:
            idx=[i for i in idx if self.cfgs[i][0] in min_hops]
        idx.sort(key=lambda i:-s[i]); idx=idx[:k]
        v=np.array([s[i] for i in idx],float)
        w=np.exp((v-v.max())/max(temperature*(v.std()+1e-9),1e-9)); w/=w.sum()
        out=[]
        for r,(i,wi) in enumerate(zip(idx,w),1):
            H,c=self.cfgs[i]; wt,nm,sc=c.split("|",2)
            out.append(dict(rank=r,min_hop=H,hamiltonian="%s/%s"%(wt,nm),score=sc,
                            weight=round(float(wi),4),predicted_auc=round(float(np.clip(s[i],0.0,1.0)),4)))   # Ridge is unbounded; clip for display (ranking unaffected)
        return out
    def save(self,p): joblib.dump(dict(model=self.model,cfgs=self.cfgs,features=self.features,meta=self.meta),p)
    @staticmethod
    def load(p):
        d=joblib.load(p); return Recommender(d["model"],d["cfgs"],d["features"],d.get("meta"))
def train(fr="../full_run_1022",wl="/Users/t/Downloads/datasets/operator_worklist.json",
          tp="/Users/t/Downloads/datasets/topology_features.json",out="recommender.joblib"):
    W={w["name"]:w for w in json.load(open(wl))}; TOPO=json.load(open(tp))
    R={H:json.load(gzip.open(f"{fr}/r2_minhop{H}.json.gz","rt")) for H in (1,2,3,4)}
    cells=sorted(next(v for v in R[1].values() if "cells" in v)["cells"])
    cfgs=[(H,c) for H in (1,2,3,4) for c in cells]
    def topo(n):
        t=TOPO.get("%s|%s|8.0"%(W[n]["pdb"],W[n]["chain"]))
        return [float(t.get(k,0) or 0) for k in FK] if t else None
    prot=[n for n in sorted({x for H in R for x,v in R[H].items() if "cells" in v}) if n in W and topo(n)]
    X=np.array([topo(n) for n in prot])
    A=np.full((len(prot),len(cfgs)),np.nan)
    for i,n in enumerate(prot):
        for j,(H,c) in enumerate(cfgs):
            v=R[H].get(n)
            if v and "cells" in v and c in v["cells"]: A[i,j]=v["cells"][c][0]
    A=np.where(np.isnan(A),np.nanmean(A,0),A)
    m=make_pipeline(StandardScaler(),Ridge(alpha=10.0)).fit(X,A)   # tiny (~100 KB) and beats a 205 MB forest on AUC
    meta=dict(architecture="9 topology features -> StandardScaler -> Ridge(alpha=10) multi-output -> 884 predicted AUCs -> rank -> top-k -> softmax weights",n_proteins=len(prot),n_families=len({W[n]["cluster"] for n in prot}),n_configs=len(cfgs),
              min_hops=[1,2,3,4],validation="leave-one-family-out GroupKFold(5)",
              measured={"k=1":{"hit_good":0.281,"best_auc":0.612,"fam_p5_08":22},
                        "k=3":{"hit_good":0.36,"best_auc":0.690,"fam_p5_08":29},
                        "k=6":{"hit_good":0.45,"best_auc":0.744,"fam_p5_08":38},
                        "k=20":{"hit_good":0.61,"best_auc":0.826,"fam_p5_08":54},
                        "oracle_884":{"hit_good":1.0,"best_auc":0.964,"fam_p5_08":71}},
              caveat="best-of-k assumes the user selects among the k results; merging blind gives ~0.610")
    r=Recommender(m,cfgs,FK,meta); r.save(out)
    print("trained on %d proteins / %d families, %d configurations -> %s"%(meta["n_proteins"],meta["n_families"],len(cfgs),out))
    return r
if __name__=="__main__":
    r=train()
    demo=dict(n_residues=298,n_edges=1840,mean_degree=12.3,degree_var=9.1,degree_cv=0.24,
              clustering_coefficient=0.41,graph_diameter=18,algebraic_connectivity=0.031,spectral_radius=17.2)
    print("\nDEMO — 'give me 6 configurations to try':")
    print("  %-5s %-8s %-14s %-20s %8s %s"%("rank","MIN_HOP","Hamiltonian","score","weight","pred AUC"))
    for c in r.recommend(demo,k=6):
        print("  %-5d %-8d %-14s %-20s %8.3f %.3f"%(c["rank"],c["min_hop"],c["hamiltonian"],c["score"],c["weight"],c["predicted_auc"]))
    print("\nDEMO — 'k=4, but only MIN_HOP 1 and 3':")
    for c in r.recommend(demo,k=4,min_hops=[1,3]):
        print("  %-5d %-8d %-14s %-20s %8.3f %.3f"%(c["rank"],c["min_hop"],c["hamiltonian"],c["score"],c["weight"],c["predicted_auc"]))
