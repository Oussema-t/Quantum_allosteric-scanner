"""Replicate the 0.717 on the cohort it was actually measured on: the 138 is_distal proteins.
Sweep regularisation, since the original C was not recorded. Compare blind LOFO vs best single
cell AND vs the reversed-distance floor that the distal subset actually has."""
import json,gzip,numpy as np
from collections import defaultdict
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut
W={w["name"]:w for w in json.load(open("/Users/t/Downloads/datasets/operator_worklist.json"))}
R=json.load(gzip.open("r2_minhop1.json.gz","rt"))
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
prot=sorted(set(P)); fams=sorted(set(G))
print("DISTAL cohort: %d proteins / %d families / %d features / %d residues"%(len(prot),len(fams),len(cells),len(Y)),flush=True)
def perprot(score):
    out={}
    for n in prot:
        m=P==n; y=Y[m]
        if 0<y.sum()<m.sum(): out[n]=roc_auc_score(y,score[m])
    return out
def famw(d):
    f=defaultdict(list)
    for n,a in d.items(): f[G[P==n][0]].append(a)
    return np.mean([np.mean(v) for v in f.values()]), len(f)
# best single cell (this is SELECTION - the number the 0.717 was compared against)
singles={c:famw(perprot(X[:,i]))[0] for i,c in enumerate(cells)}
bc=max(singles,key=singles.get)
print("  best single cell (selected on the same data): %-24s %.4f"%(bc,singles[bc]))
print("  fixed pre-registered cell gauss|sym|neg_dE  : %.4f"%singles["gauss|sym|neg_dE"])
logo=LeaveOneGroupOut()
for C in (0.01,0.05,0.2,1.0):
    pred=np.zeros(len(Y))
    for tr,te in logo.split(X,Y,groups=G):
        m=make_pipeline(StandardScaler(),LogisticRegression(C=C,max_iter=3000))
        m.fit(X[tr],Y[tr]); pred[te]=m.predict_proba(X[te])[:,1]
    d=perprot(pred); fw,nf=famw(d)
    print("  blind LOFO C=%-5s : per-protein %.4f | FAMILY-mean %.4f  (%d families)"%(C,np.mean(list(d.values())),fw,nf),flush=True)
