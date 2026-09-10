"""The decisive test: does the blind LOFO model beat the REVERSED-DISTANCE floor on distal,
on the same residues, family-paired? The floor there is 0.773, not 0.227."""
import json,gzip,numpy as np
from collections import defaultdict
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut
from scipy.stats import wilcoxon, binomtest
import networkx as nx
from Bio.PDB import PDBParser
W={w["name"]:w for w in json.load(open("/Users/t/Downloads/datasets/operator_worklist.json"))}
FL={r["name"] if "name" in r else k:r for k,r in
    (lambda R: (R.items() if isinstance(R,dict) else [(x.get("name",i),x) for i,x in enumerate(R)]))(
    json.load(open("/Users/t/Quantum_allosteric-scanner/allosteric/results/proximity_floor/proximity_floor_results.json")))}
R=json.load(gzip.open("/Users/t/Quantum_allosteric-scanner/allosteric/results/full_run_1022/r2_minhop1.json.gz","rt"))
X=[];Y=[];G=[];P=[];cells=None
for n,v in R.items():
    if "ranks" not in v or n not in W or not W[n].get("is_distal"): continue
    y=np.array(v["y"]); ns=len(y)
    if not(0<y.sum()<ns): continue
    if cells is None: cells=sorted(v["ranks"])
    if sorted(v["ranks"])!=cells: continue
    M=np.stack([1.0-(np.asarray(v["ranks"][c],float)-1)/max(ns-1,1) for c in cells],1)
    X.append(M);Y.append(y);G.append([W[n]["cluster"]]*ns);P.append([n]*ns)
X=np.vstack(X);Y=np.concatenate(Y);G=np.concatenate(G);P=np.concatenate(P)
prot=sorted(set(P))
pred=np.zeros(len(Y))
for tr,te in LeaveOneGroupOut().split(X,Y,groups=G):
    m=make_pipeline(StandardScaler(),LogisticRegression(C=0.01,max_iter=3000))
    m.fit(X[tr],Y[tr]); pred[te]=m.predict_proba(X[te])[:,1]
rows=[]
for n in prot:
    m=P==n; y=Y[m]
    if not(0<y.sum()<m.sum()): continue
    f=FL.get(n)
    if f is None or "floor_auc" not in f: continue
    rows.append((G[m][0], roc_auc_score(y,pred[m]), 1.0-float(f["floor_auc"]), float(f["ctqw_fixed_auc"])))
print("paired on %d distal proteins"%len(rows))
fam=defaultdict(list)
for c,a,b,d in rows: fam[c].append((a,b,d))
L=np.array([np.mean([x[0] for x in g]) for g in fam.values()])
F=np.array([np.mean([x[1] for x in g]) for g in fam.values()])
C=np.array([np.mean([x[2] for x in g]) for g in fam.values()])
print("\nFAMILY-WEIGHTED AUC on the distal subset (%d families)\n"%len(fam))
print("  blind LOFO model (221 quantum+classical scores) : %.4f"%L.mean())
print("  REVERSED-distance floor (rank by FAR from site) : %.4f"%F.mean())
print("  single fixed CTQW cell                          : %.4f"%C.mean())
w=int((L>F).sum())
print("\n  LOFO beats the floor in %d of %d families"%(w,len(F)))
print("  Wilcoxon (family-paired) p = %.4g"%wilcoxon(L,F).pvalue)
print("  sign test                p = %.4g"%binomtest(w,len(F),0.5).pvalue)
print("\n  mean difference LOFO - floor = %+.4f"%(L-F).mean())
