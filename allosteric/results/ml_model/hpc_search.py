#!/usr/bin/env python3
"""Architecture + optimizer search for Model 2 (221 CTQW cells -> allosteric probability).
Leave-one-FAMILY-out GroupKFold(5). Reports pooled AUC AND families cleared at P@5>=0.8/0.6.
Sharded; checkpoints after every config."""
import os,json,itertools,time,numpy as np,warnings
warnings.filterwarnings("ignore")
from sklearn.linear_model import LogisticRegression,SGDClassifier
from sklearn.ensemble import RandomForestClassifier,HistGradientBoostingClassifier,ExtraTreesClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score
from collections import defaultdict
SHARD=int(os.environ.get("SHARD","0")); NS=int(os.environ.get("NSHARD","1")); OUT=os.environ.get("OUT","search.json")
D=np.load("model2_data.npz",allow_pickle=True)
X=D["X"];Xt=D["Xt"];y=D["y"];g=D["g"];pid=D["pid"]
stats=np.column_stack([X.mean(1),X.std(1),X.max(1),X.min(1),np.median(X,1),(X>0.9).sum(1),(X>0.75).sum(1),(X>0.5).sum(1)]).astype(np.float32)
FEATS={"cells":X,"cells+stats":np.hstack([X,stats]),"cells+topo":np.hstack([X,Xt]),
       "cells+stats+topo":np.hstack([X,stats,Xt]),"stats":stats,"stats+topo":np.hstack([stats,Xt])}
def build(name,hp):
    if name=="logistic": return make_pipeline(StandardScaler(),LogisticRegression(C=hp["C"],penalty=hp["pen"],solver="liblinear" if hp["pen"]=="l1" else "lbfgs",max_iter=1000,class_weight="balanced"))
    if name=="sgd":      return make_pipeline(StandardScaler(),SGDClassifier(loss="log_loss",alpha=hp["alpha"],learning_rate=hp["lr"],eta0=0.01,max_iter=800,class_weight="balanced",random_state=0))
    if name=="hgb":      return HistGradientBoostingClassifier(max_iter=hp["it"],max_depth=hp["d"],learning_rate=hp["lr"],l2_regularization=hp["l2"],min_samples_leaf=hp["leaf"],random_state=0)
    if name=="rf":       return RandomForestClassifier(n_estimators=hp["n"],max_depth=hp["d"],min_samples_leaf=hp["leaf"],class_weight="balanced",random_state=0,n_jobs=2)
    if name=="et":       return ExtraTreesClassifier(n_estimators=hp["n"],max_depth=hp["d"],min_samples_leaf=hp["leaf"],class_weight="balanced",random_state=0,n_jobs=2)
    if name=="mlp":      return make_pipeline(StandardScaler(),MLPClassifier(hidden_layer_sizes=hp["h"],alpha=hp["alpha"],solver=hp["opt"],learning_rate_init=hp["lr"],max_iter=hp["it"],early_stopping=True,n_iter_no_change=10,random_state=0))
CONFIGS=[]
for f in FEATS:
    for pen,C in itertools.product(["l1","l2"],[0.002,0.005,0.02,0.05,0.2,1.0]): CONFIGS.append((f,"logistic",{"pen":pen,"C":C}))
    for a,lr in itertools.product([1e-5,1e-4,1e-3],["optimal","adaptive"]): CONFIGS.append((f,"sgd",{"alpha":a,"lr":lr}))
    for it,d,lr,l2,leaf in itertools.product([200,400],[4,6,10],[0.03,0.08],[0.0,1.0],[20,50]): CONFIGS.append((f,"hgb",{"it":it,"d":d,"lr":lr,"l2":l2,"leaf":leaf}))
    for n,d,leaf in itertools.product([300],[10,16,None],[3,10]): CONFIGS.append((f,"rf",{"n":n,"d":d,"leaf":leaf}))
    for n,d,leaf in itertools.product([300],[14,None],[3,10]): CONFIGS.append((f,"et",{"n":n,"d":d,"leaf":leaf}))
    for h,a,opt in itertools.product([(128,64),(256,128,64),(64,)],[1e-3,1e-2],["adam","sgd"]): CONFIGS.append((f,"mlp",{"h":h,"alpha":a,"opt":opt,"lr":1e-3,"it":300}))
mine=[c for i,c in enumerate(CONFIGS) if i%NS==SHARD]
print("shard %d/%d: %d of %d configs"%(SHARD,NS,len(mine),len(CONFIGS)),flush=True)
gkf=GroupKFold(5); res=json.load(open(OUT)) if os.path.exists(OUT) else {}
t0=time.time()
for k,(fn,mn,hp) in enumerate(mine,1):
    key="%s|%s|%s"%(fn,mn,json.dumps(hp,sort_keys=True))
    if key in res: continue
    Xf=FEATS[fn]
    try:
        p=np.zeros(len(y))
        for tr,te in gkf.split(Xf,y,g):
            m=build(mn,hp); m.fit(Xf[tr],y[tr]); p[te]=m.predict_proba(Xf[te])[:,1]
        auc=roc_auc_score(y,p)
        f8=defaultdict(bool); f6=defaultdict(bool)
        for n in set(pid):
            msk=pid==n; yy=y[msk]; ss=p[msk]
            if yy.sum()==0 or yy.sum()==len(yy): continue
            o=np.argsort(-ss); p5=yy[o[:5]].sum()/5.0; a=roc_auc_score(yy,ss)
            fam=g[msk][0]; f8[fam]|=(a>=0.6 and p5>=0.8); f6[fam]|=(a>=0.6 and p5>=0.6)
        res[key]=dict(auc=float(auc),fam8=int(sum(f8.values())),fam6=int(sum(f6.values())),feat=fn,model=mn,hp=hp)
        print("  %-17s %-9s auc=%.4f fam8=%3d fam6=%3d (%d/%d %.0fs)"%(fn,mn,auc,res[key]["fam8"],res[key]["fam6"],k,len(mine),time.time()-t0),flush=True)
    except Exception as e:
        res[key]={"error":str(e)[:80],"feat":fn,"model":mn,"hp":hp}
    json.dump(res,open(OUT,"w"))
print("SHARD %d DONE (%.0fs)"%(SHARD,time.time()-t0),flush=True)
