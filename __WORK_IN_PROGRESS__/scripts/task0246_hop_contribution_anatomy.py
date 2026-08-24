"""How much of the geometric contribution is hop distance, and HOW does it
contribute?

Two separate questions, answered separately:

  A. HOW MUCH.
     - each geometric baseline alone, cross-validated (out-of-fold AUC)
     - leave-one-out inside the geometry block: refit without hop and measure
       the drop. That is hop's *incremental* value given the other two, which
       is not the same as its solo AUC (degree and euclid are correlated with
       it).

  B. HOW. A solo AUC says a ranker works, not what rule it encodes. So:
     - direction: `baselines.hop_from_seed` returns NEGATED BFS distance, so
       AUC > 0.5 means CLOSER residues are more likely to be pocket. Verified
       explicitly rather than inferred from the sign convention.
     - the hop-shell enrichment profile: for each integer BFS shell k,
       P(pocket | hop = k) / P(pocket), pooled across targets. This
       distinguishes a monotonic "closer is better" rule from a banded
       "pockets live at a characteristic distance" rule -- which matters,
       because this project's whole premise is that allosteric sites are
       DISTAL to the active site.
"""
from __future__ import annotations
import sys, json, warnings
from pathlib import Path
from collections import defaultdict
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
from allostery.metrics import auc
from sklearn.model_selection import StratifiedKFold

TARGETS = ["KRAS_G12C","BCR_ABL1","CARDIAC_MYOSIN","HIV1_RT","PTP1B",
           "GLUCOKINASE","CASPASE7","GLUR2_TRU","GLUK1_BPAM"]
N_FOLD, N_REP = 5, 20

def z(v):
    v=np.asarray(v,float); s=v.std(); return (v-v.mean())/(s if s>1e-12 else 1.0)

def cv_auc(X, y):
    X=np.asarray(X)
    if X.ndim==1: X=X.reshape(-1,1)
    out=[]
    for rep in range(N_REP):
        oof=np.zeros(len(y))
        for tr,te in StratifiedKFold(N_FOLD,shuffle=True,random_state=rep).split(X,y):
            b,*_=np.linalg.lstsq(np.column_stack([X[tr],np.ones(len(tr))]),y[tr].astype(float),rcond=None)
            oof[te]=np.column_stack([X[te],np.ones(len(te))])@b
        out.append(float(auc(oof,y)))
    return float(np.mean(out))

shells=defaultdict(lambda:[0,0]); rows={}
print(f"{'target':<16}{'degree':>8}{'euclid':>8}{'hop':>7} | {'block':>7}{'no-hop':>8}{'hop incr':>9} | {'medHop+':>8}{'medHop-':>8}")
for t in TARGETS:
    cfg, apo, seed, pocket = prep(t)
    c=apo.coords; cut=float(cfg.get("enm_cutoff",8.0)); n=len(c)
    m=np.ones(n,bool); m[seed]=False
    y=pocket.astype(int)[m]
    if y.sum()<5: continue
    hop_raw = -hop_from_seed(c,seed,cutoff=cut)
    d=z(degree_centrality(c,cutoff=cut))[m]; e=z(euclid_from_seed_centroid(c,seed))[m]
    h=z(hop_from_seed(c,seed,cutoff=cut))[m]
    a_d,a_e,a_h = cv_auc(d,y), cv_auc(e,y), cv_auc(h,y)
    blk  = cv_auc(np.column_stack([d,e,h]),y)
    nohop= cv_auc(np.column_stack([d,e]),y)
    hr=hop_raw[m]
    for k,yy in zip(hr.astype(int),y):
        shells[k][0]+=1; shells[k][1]+=int(yy)
    rows[t]={"degree":a_d,"euclid":a_e,"hop":a_h,"block":blk,"no_hop":nohop,
             "hop_increment":blk-nohop,"med_hop_pocket":float(np.median(hr[y==1])),
             "med_hop_other":float(np.median(hr[y==0])),"n_pocket":int(y.sum())}
    print(f"{t:<16}{a_d:>8.4f}{a_e:>8.4f}{a_h:>7.4f} | {blk:>7.4f}{nohop:>8.4f}{blk-nohop:>+9.4f} |"
          f"{np.median(hr[y==1]):>8.1f}{np.median(hr[y==0]):>8.1f}")

hs=[r["hop"] for r in rows.values()]; inc=[r["hop_increment"] for r in rows.values()]
print(f"\nA. HOW MUCH")
print(f"  hop alone (CV AUC):       {min(hs):.3f}-{max(hs):.3f}, median {np.median(hs):.3f}")
print(f"  hop incremental in block: {min(inc):+.4f} to {max(inc):+.4f}, median {np.median(inc):+.4f}")
print(f"  hop is the strongest single baseline on "
      f"{sum(1 for r in rows.values() if r['hop']>=max(r['degree'],r['euclid']))}/{len(rows)} targets")
print(f"\n  share of the geometry block's above-chance AUC attributable to hop:")
for t,r in rows.items():
    tot=r["block"]-0.5
    s=f"{100*r['hop_increment']/tot:>6.0f}%" if tot>0.005 else "   n/a (block at/below chance)"
    print(f"    {t:<16} block {tot:+.4f} | hop incr {r['hop_increment']:+.4f}  {s}")

print(f"\nB. HOW  --  AUC>0.5 on a NEGATED-distance score means CLOSER = more pocket-like")
print("  median BFS hops (pocket / non-pocket): "
      + ", ".join(f"{t.split('_')[0]} {r['med_hop_pocket']:.0f}/{r['med_hop_other']:.0f}" for t,r in rows.items()))
base=sum(v[1] for v in shells.values())/sum(v[0] for v in shells.values())
print(f"\n  pooled hop-shell enrichment, base rate P(pocket)={base:.4f}")
print(f"  {'hop':>4}{'n_res':>8}{'n_pocket':>10}{'P(pocket)':>11}{'enrich':>9}")
for k in sorted(shells):
    nn,npk=shells[k]
    if nn<20: continue
    p=npk/nn
    print(f"  {k:>4}{nn:>8}{npk:>10}{p:>11.4f}{p/base:>8.2f}x")
(_ROOT/"results/tasks/0246_hop_anatomy").mkdir(parents=True,exist_ok=True)
(_ROOT/"results/tasks/0246_hop_anatomy/results.json").write_text(json.dumps(
    {"per_target":rows,"shells":{str(k):v for k,v in shells.items()},"base_rate":base},indent=1))

# ---------------------------------------------------------------------------
# C. The shell profile above is BANDED (peak at hop 2, depleted at 1, empty
# past 7), but `baselines.hop_from_seed` is a MONOTONIC linear ranker. A
# monotonic feature on a banded target is mis-specified, so hop's measured AUC
# understates what hop DISTANCE can do -- and the register's proximity floor is
# correspondingly too low. Tested directly: same CV, three encodings.
#   linear      -- what the floor uses today (negated distance)
#   band        -- -(|hop - 2.5|), a single-parameter shell-distance feature
#   onehot      -- one indicator per shell 1..8, the fully flexible form
# ---------------------------------------------------------------------------
print("\nC. IS THE FLOOR MIS-SPECIFIED?  (CV AUC by hop encoding)")
print(f"  {'target':<16}{'linear':>9}{'band':>8}{'onehot':>9}{'best-linear':>13}")
enc_rows={}
for t in TARGETS:
    cfg, apo, seed, pocket = prep(t)
    c=apo.coords; cut=float(cfg.get("enm_cutoff",8.0)); n=len(c)
    m=np.ones(n,bool); m[seed]=False
    y=pocket.astype(int)[m]
    if y.sum()<5: continue
    hr=(-hop_from_seed(c,seed,cutoff=cut))[m]
    lin=cv_auc(z(-hr),y)
    band=cv_auc(z(-np.abs(hr-2.5)),y)
    oh=np.column_stack([(hr==k).astype(float) for k in range(1,9)])
    onehot=cv_auc(oh,y)
    enc_rows[t]={"linear":lin,"band":band,"onehot":onehot}
    print(f"  {t:<16}{lin:>9.4f}{band:>8.4f}{onehot:>9.4f}{max(band,onehot)-lin:>+13.4f}")
L=[r["linear"] for r in enc_rows.values()]; B=[r["band"] for r in enc_rows.values()]
O=[r["onehot"] for r in enc_rows.values()]
print(f"\n  median: linear {np.median(L):.4f}  band {np.median(B):.4f}  onehot {np.median(O):.4f}")
print(f"  band beats linear on {sum(1 for a,b in zip(B,L) if b>a)}/{len(L)} targets"
      f"; onehot beats linear on {sum(1 for a,b in zip(O,L) if b>a)}/{len(L)}")
(_ROOT/"results/tasks/0246_hop_anatomy/encodings.json").write_text(json.dumps(enc_rows,indent=1))
