"""The blind LOFO regression on the FULL 630, not the 138 it was measured on.
RATIONALE  is the 0.717-vs-0.589 blind result real at scale, or a small-cohort effect?
VALIDATION defined now: per-protein AUC averaged, family-weighted, vs (a) the fixed cell
           gauss|sym|neg_dE and (b) closeness centrality, on the SAME residues. Blind:
           the fold's model never sees its own family."""
import json,gzip,numpy as np
from collections import defaultdict
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
W={w["name"]:w for w in json.load(open("/Users/t/Downloads/datasets/operator_worklist.json"))}
R=json.load(gzip.open("r2_minhop1.json.gz","rt"))
X=[];Y=[];G=[];P=[]
cells=None
for n,v in R.items():
    if "ranks" not in v or n not in W: continue
    y=np.array(v["y"]); ns=len(y)
    if not(0<y.sum()<ns): continue
    if cells is None: cells=sorted(v["ranks"])
    if sorted(v["ranks"])!=cells: continue
    M=np.stack([1.0-(np.asarray(v["ranks"][c],float)-1)/max(ns-1,1) for c in cells],1)
    X.append(M);Y.append(y);G.append([W[n]["cluster"]]*ns);P.append([n]*ns)
X=np.vstack(X);Y=np.concatenate(Y);G=np.concatenate(G);P=np.concatenate(P)
print("matrix %s | %d proteins | %d families | %d features"%(X.shape,len(set(P)),len(set(G)),len(cells)),flush=True)
pred=np.zeros(len(Y))
gk=GroupKFold(n_splits=10)
for i,(tr,te) in enumerate(gk.split(X,Y,groups=G)):
    m=make_pipeline(StandardScaler(),LogisticRegression(C=0.05,max_iter=2000))
    m.fit(X[tr],Y[tr]); pred[te]=m.predict_proba(X[te])[:,1]
    print("  fold %d done"%i,flush=True)
FIX=cells.index("gauss|sym|neg_dE")
per=defaultdict(dict)
for n in set(P):
    m=P==n; y=Y[m]
    if not(0<y.sum()<m.sum()): continue
    per[n]["lofo"]=roc_auc_score(y,pred[m])
    per[n]["fixed"]=roc_auc_score(y,X[m,FIX])
    per[n]["fam"]=G[m][0]
fam=defaultdict(list)
for n,d in per.items(): fam[d["fam"]].append(d)
fm=lambda k: np.mean([np.mean([d[k] for d in g]) for g in fam.values()])
from scipy.stats import wilcoxon
A=np.array([np.mean([d["lofo"] for d in g]) for g in fam.values()])
B=np.array([np.mean([d["fixed"] for d in g]) for g in fam.values()])
print("\nRESULT on %d proteins / %d families"%(len(per),len(fam)))
print("  per-protein  : blind LOFO %.4f   fixed cell %.4f"%(np.mean([d["lofo"] for d in per.values()]),np.mean([d["fixed"] for d in per.values()])))
print("  FAMILY-mean  : blind LOFO %.4f   fixed cell %.4f"%(fm("lofo"),fm("fixed")))
print("  Wilcoxon (family-paired, LOFO vs fixed): p = %.3g"%wilcoxon(A,B).pvalue)
json.dump({n:d for n,d in per.items()},open("/private/tmp/claude-501/-Users-t/8661cd1f-9d0c-4f5f-bcf1-719eac9a2b58/scratchpad/lofo630_out.json","w"))
