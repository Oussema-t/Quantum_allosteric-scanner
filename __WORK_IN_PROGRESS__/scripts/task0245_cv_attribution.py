"""Cross-validated re-do of TASK-0238's variance attribution.

TASK-0238 reported geometry/CTQW/unexplained shares from an IN-SAMPLE OLS
stack (4 parameters, 16-17 positives) and flagged the numbers as an
optimistic ceiling, with the explicit warning that cross-validation would
lower the stack AUC and therefore RAISE the unexplained share. This runs that
check instead of continuing to cite the caveat.

5-fold stratified CV over residues (seed rows excluded, as everywhere). Two
nested models per fold, fitted on train, scored on held-out test:
    geometry      = OLS(degree, euclid_from_seed, hop_from_seed)
    geometry+CTQW = the same plus the converged incoherent CTQW occupation
Shares of discrimination above chance: (AUC - 0.5) / 0.5.

Also reports CTQW's incremental AUC over hop_from_seed ALONE, because
[[TASK-0244]] found CTQW and a plain hop ranker indistinguishable in the
two-stage design (mean rank 5.71 both) -- so the question "does CTQW add
anything over proximity specifically" deserves its own number rather than
being folded into a three-baseline block.
"""
from __future__ import annotations
import sys, json, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT/"src", _ROOT/"scripts", _ROOT.parent):
    if str(_p) not in sys.path: sys.path.insert(0, str(_p))
import yaml, prody; prody.confProDy(verbosity="none")
CAND = yaml.safe_load((_ROOT/"config"/"candidate_targets_task0216.yaml").read_text())["targets"]
from allostery import clean as _clean
_o=_clean.load_target_config
_clean.load_target_config=lambda n,p=None: CAND[n] if n in CAND else _o(n,p)
from task0242_two_stage_dryrun import prep
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed
from allostery.hamiltonians import build_H_new
from allostery.propagators import time_averaged_ctqw_converged
from allostery.metrics import auc
from sklearn.model_selection import StratifiedKFold

TARGETS = ["KRAS_G12C","BCR_ABL1","CARDIAC_MYOSIN","HIV1_RT",
           "PTP1B","GLUCOKINASE","CASPASE7","GLUR2_TRU","GLUK1_BPAM"]
N_FOLD, N_REP = 5, 20

def z(v):
    v=np.asarray(v,float); s=v.std(); return (v-v.mean())/(s if s>1e-12 else 1.0)

def cv_auc(X, y, rng):
    """Mean out-of-fold AUC over N_REP repeats of stratified K-fold."""
    out=[]
    for rep in range(N_REP):
        skf=StratifiedKFold(n_splits=N_FOLD, shuffle=True, random_state=rep)
        oof=np.zeros(len(y))
        for tr,te in skf.split(X,y):
            b,*_=np.linalg.lstsq(np.column_stack([X[tr],np.ones(len(tr))]), y[tr].astype(float), rcond=None)
            oof[te]=np.column_stack([X[te],np.ones(len(te))])@b
        out.append(float(auc(oof,y)))
    return float(np.mean(out)), float(np.std(out))

print(f"{'target':<16}{'geom_cv':>9}{'stack_cv':>10}{'dCTQW':>8} | {'hop_cv':>8}{'hop+q_cv':>10}{'dCTQW|hop':>10}")
res={}
for t in TARGETS:
    cfg, apo, seed, pocket = prep(t)
    c=apo.coords; cut=float(cfg.get("enm_cutoff",8.0)); n=len(c)
    m=np.ones(n,bool); m[seed]=False
    y=pocket.astype(int)[m]
    if y.sum()<5: print(f"{t:<16} SKIP (only {y.sum()} positives)"); continue
    hop=z(hop_from_seed(c,seed,cutoff=cut))[m]
    G=np.column_stack([z(degree_centrality(c,cutoff=cut))[m],
                       z(euclid_from_seed_centroid(c,seed))[m], hop])
    q=z(time_averaged_ctqw_converged(build_H_new(c,apo.bfactors,cutoff=cut),source=seed,coherent=False))[m]
    rng=np.random.default_rng(0)
    g,_=cv_auc(G,y,rng); s,_=cv_auc(np.column_stack([G,q]),y,rng)
    h,_=cv_auc(hop.reshape(-1,1),y,rng); hq,_=cv_auc(np.column_stack([hop,q]),y,rng)
    res[t]={"geom_cv":g,"stack_cv":s,"d_ctqw":s-g,"hop_cv":h,"hopq_cv":hq,"d_ctqw_over_hop":hq-h,
            "share_geom":(g-0.5)/0.5,"share_ctqw":(s-g)/0.5,"share_unexplained":(1-s)/0.5,
            "n_pocket":int(y.sum())}
    print(f"{t:<16}{g:>9.4f}{s:>10.4f}{s-g:>+8.4f} | {h:>8.4f}{hq:>10.4f}{hq-h:>+10.4f}")

print(f"\n{'target':<16}{'geometry':>10}{'CTQW':>8}{'unexplained':>13}")
for t,r in res.items():
    print(f"{t:<16}{100*max(0,r['share_geom']):>9.0f}%{100*r['share_ctqw']:>7.0f}%{100*r['share_unexplained']:>12.0f}%")
gs=[max(0,r['share_geom']) for r in res.values()]; cs=[r['share_ctqw'] for r in res.values()]
us=[r['share_unexplained'] for r in res.values()]
print(f"\n  geometry     {100*min(gs):.0f}-{100*max(gs):.0f}%  (median {100*np.median(gs):.0f}%)")
print(f"  CTQW         {100*min(cs):+.0f} to {100*max(cs):+.0f}%  (median {100*np.median(cs):+.0f}%)")
print(f"  unexplained  {100*min(us):.0f}-{100*max(us):.0f}%  (median {100*np.median(us):.0f}%)")
n_pos=sum(1 for x in cs if x>0)
print(f"\n  CTQW's cross-validated increment is POSITIVE on {n_pos}/{len(cs)} targets")
print(f"  CTQW increment over hop ALONE positive on "
      f"{sum(1 for r in res.values() if r['d_ctqw_over_hop']>0)}/{len(res)} targets")
(_ROOT/"results/tasks/0245_cv_attribution").mkdir(parents=True,exist_ok=True)
(_ROOT/"results/tasks/0245_cv_attribution/results.json").write_text(json.dumps(res,indent=1))
