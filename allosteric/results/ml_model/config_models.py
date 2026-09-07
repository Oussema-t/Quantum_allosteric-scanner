#!/usr/bin/env python3
"""THE TWO MODELS FOR THE BEST PIPELINE.  Input = protein topology.  Output = the configuration to run.
  Model 1: topology -> MIN_HOP
  Model 2: topology -> (Hamiltonian, score) pair        [joint: they interact, not factorizable]
Same protein set for both: round-2 testable (after PocketMiner veto) = the best-pipeline output.
Leave-one-FAMILY-out GroupKFold(5).  Scored by what matters: the AUC / P@5 you actually get
when you RUN the predicted configuration on held-out proteins."""
import json,gzip,numpy as np,joblib,csv,warnings
warnings.filterwarnings("ignore")
from sklearn.ensemble import RandomForestClassifier,RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score
from collections import Counter,defaultdict
FR="../full_run_1022"
W={w["name"]:w for w in json.load(open("/Users/t/Downloads/datasets/operator_worklist.json"))}
TOPO=json.load(open("/Users/t/Downloads/datasets/topology_features.json"))
FK=['n_residues','n_edges','mean_degree','degree_var','degree_cv','clustering_coefficient','graph_diameter','algebraic_connectivity','spectral_radius']
def load(p): return json.load(gzip.open(p,"rt"))
R2={H:load(f"{FR}/r2_minhop{H}.json.gz") for H in (1,2,3,4)}
cells=sorted(next(v for v in R2[1].values() if "cells" in v)["cells"])
def topo(n):
    t=TOPO.get("%s|%s|8.0"%(W[n]["pdb"],W[n]["chain"]))
    return [float(t.get(k,0) or 0) for k in FK] if t else None
# ---- common protein set: round-2 testable at any MIN_HOP, with topology
prot=sorted({n for H in R2 for n,v in R2[H].items() if "cells" in v and n in W and topo(n)})
X=np.array([topo(n) for n in prot]); G=np.array([W[n]["cluster"] for n in prot])
dist=np.array([1 if W[n]["is_distal"] else 0 for n in prot])
print("COMMON SET: %d proteins / %d families | input = %d topology features\n"%(len(prot),len(set(G)),len(FK)))
gkf=GroupKFold(5)
# ================= MODEL 1: topology -> MIN_HOP
# target = the MIN_HOP that actually gives the best AUC for the protein (from the data, not a rule)
best_hop=np.zeros(len(prot),int)
for i,n in enumerate(prot):
    sc={H:max(a for a,p in R2[H][n]["cells"].values()) for H in R2 if n in R2[H] and "cells" in R2[H][n]}
    best_hop[i]=max(sc,key=sc.get)
p1=np.zeros(len(prot),int); pd1=np.zeros(len(prot))
for tr,te in gkf.split(X,best_hop,G):
    m=RandomForestClassifier(n_estimators=300,max_depth=8,min_samples_leaf=5,class_weight="balanced",random_state=0,n_jobs=-1)
    m.fit(X[tr],best_hop[tr]); p1[te]=m.predict(X[te])
    m2=RandomForestClassifier(n_estimators=300,max_depth=8,class_weight="balanced",random_state=0,n_jobs=-1)
    m2.fit(X[tr],dist[tr]); pd1[te]=m2.predict_proba(X[te])[:,1]
acc=(p1==best_hop).mean(); base=Counter(best_hop).most_common(1)[0][1]/len(prot)
print("MODEL 1  topology -> MIN_HOP   (leave-one-family-out)")
print("  target distribution (best MIN_HOP per protein): %s"%dict(sorted(Counter(best_hop).items())))
print("  exact-MIN_HOP accuracy : %.3f   (always-guess-commonest baseline %.3f)"%(acc,base))
print("  near-vs-distal AUC     : %.3f   (this is what sets MIN_HOP 1 vs 3)"%roc_auc_score(dist,pd1))
# what you GET by running at the predicted MIN_HOP (best cell at that hop) vs fixed hops
def auc_at(n,H):
    v=R2[H].get(n); return max(a for a,p in v["cells"].values()) if v and "cells" in v else np.nan
got=np.array([auc_at(n,p1[i]) for i,n in enumerate(prot)])
print("  mean best-cell AUC when running at the PREDICTED MIN_HOP : %.3f"%np.nanmean(got))
for H in (1,2,3):
    print("  mean best-cell AUC when always running MIN_HOP=%d        : %.3f  (n=%d testable)"%(H,np.nanmean([auc_at(n,H) for n in prot]),sum(~np.isnan([auc_at(n,H) for n in prot]))))
print("  oracle (true best MIN_HOP)                              : %.3f"%np.nanmean([auc_at(n,best_hop[i]) for i,n in enumerate(prot)]))
# ================= MODEL 2: topology -> (Hamiltonian, score) pair
# target: the AUC of each of the 221 cells, at the protein's best MIN_HOP; regress all 221 from topology; run the predicted best
A=np.array([[R2[best_hop[i]][n]["cells"][c][0] for c in cells] for i,n in enumerate(prot)])
P5=np.array([[R2[best_hop[i]][n]["cells"][c][1] for c in cells] for i,n in enumerate(prot)])
pred=np.zeros_like(A)
for tr,te in gkf.split(X,A,G):
    m=RandomForestRegressor(n_estimators=300,max_depth=10,min_samples_leaf=5,random_state=0,n_jobs=-1)
    m.fit(X[tr],A[tr]); pred[te]=m.predict(X[te])
pick=pred.argmax(1)
got_a=A[np.arange(len(prot)),pick]; got_p=P5[np.arange(len(prot)),pick]
fixed=A.mean(0).argmax(); fix_a=A[:,fixed]; fix_p=P5[:,fixed]
rng=np.random.default_rng(0); rnd=A[np.arange(len(prot)),rng.integers(0,len(cells),len(prot))]
def fams(a,p,thr):
    f=defaultdict(bool)
    for i in range(len(prot)): f[G[i]]|=(a[i]>=0.6 and p[i]>=thr)
    return sum(f.values())
print("\nMODEL 2  topology -> (Hamiltonian, score)   (leave-one-family-out, at each protein's MIN_HOP)")
print("  %-44s %8s %10s %10s"%("cell chosen by","mean AUC","fam P@5>=.8","fam P@5>=.6"))
print("  %-44s %8.3f %10d %10d"%("random cell",rnd.mean(),fams(rnd,P5[np.arange(len(prot)),rng.integers(0,len(cells),len(prot))],0.8),0))
print("  %-44s %8.3f %10d %10d"%("one FIXED cell for all: %s"%cells[fixed].replace("|","/"),fix_a.mean(),fams(fix_a,fix_p,0.8),fams(fix_a,fix_p,0.6)))
print("  %-44s %8.3f %10d %10d"%("PREDICTED from topology (Model 2)",got_a.mean(),fams(got_a,got_p,0.8),fams(got_a,got_p,0.6)))
print("  %-44s %8.3f %10d %10d"%("oracle (true best cell per protein)",A.max(1).mean(),fams(A.max(1),P5[np.arange(len(prot)),A.argmax(1)],0.8),fams(A.max(1),P5[np.arange(len(prot)),A.argmax(1)],0.6)))
pk=Counter(cells[k].split("|")[0]+"/"+cells[k].split("|")[1] for k in pick); ps=Counter(cells[k].split("|",2)[2] for k in pick)
print("  Model 2 predicts Hamiltonian:",dict(pk.most_common(4)))
print("  Model 2 predicts score      :",dict(ps.most_common(4)))
# ================= FINAL FIT ON ALL 597 + SAVE
M1=RandomForestClassifier(n_estimators=300,max_depth=8,min_samples_leaf=5,class_weight="balanced",random_state=0,n_jobs=-1).fit(X,best_hop)
M2=RandomForestRegressor(n_estimators=300,max_depth=10,min_samples_leaf=5,random_state=0,n_jobs=-1).fit(X,A)
joblib.dump(dict(model1_minhop=M1,model2_cell_auc=M2,topo_features=FK,cells=cells,n_proteins=len(prot),n_families=len(set(G)),
  cv=dict(model1_minhop_acc=float(acc),model1_baseline=float(base),model1_distal_auc=float(roc_auc_score(dist,pd1)),
          model2_pred_auc=float(got_a.mean()),model2_fixed_auc=float(fix_a.mean()),model2_oracle_auc=float(A.max(1).mean()),
          model2_fam8=fams(got_a,got_p,0.8),fixed_fam8=fams(fix_a,fix_p,0.8))),"config_models.joblib")
with open("config_predictions.csv","w",newline="") as fh:
    w=csv.writer(fh); w.writerow(["protein","family","is_distal","true_best_minhop","pred_minhop","pred_cell","auc_of_pred_cell","p5_of_pred_cell","true_best_cell","oracle_auc"])
    for i,n in enumerate(prot): w.writerow([n,G[i],dist[i],best_hop[i],p1[i],cells[pick[i]],round(got_a[i],3),got_p[i],cells[A[i].argmax()],round(A[i].max(),3)])
print("\nSAVED: config_models.joblib (both models, fit on all %d) + config_predictions.csv (per-protein held-out predictions)"%len(prot))
