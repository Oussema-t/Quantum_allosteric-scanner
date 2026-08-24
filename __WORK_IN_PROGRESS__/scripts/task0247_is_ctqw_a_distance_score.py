"""Is the CTQW score anything more than a re-encoded distance-from-seed?

Three measurements, weakest to most decisive:

  1. Rank correlation between the CTQW occupation vector and BFS hop distance.
  2. R^2 of CTQW regressed on hop -- linear, and as one-hot shell indicators
     (the fully flexible form: how much of CTQW is a pure function of WHICH
     SHELL a residue sits in, with no assumption about shape).
  3. THE DECISIVE ONE: conditional (within-shell) AUC. Stratify residues by
     hop shell; inside each shell, distance-from-seed is held constant. If
     CTQW carries information beyond distance, within-shell AUC stays above
     0.5. If it is a distance score in disguise, it collapses to ~0.5.
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
from scipy import stats
CAND = yaml.safe_load((_ROOT/"config"/"candidate_targets_task0216.yaml").read_text())["targets"]
from allostery import clean as _clean
_o=_clean.load_target_config
_clean.load_target_config=lambda n,p=None: CAND[n] if n in CAND else _o(n,p)
from task0242_two_stage_dryrun import prep
from allostery.baselines import hop_from_seed
from allostery.hamiltonians import build_H_new
from allostery.propagators import time_averaged_ctqw_converged
from allostery.metrics import auc

TARGETS = ["KRAS_G12C","BCR_ABL1","CARDIAC_MYOSIN","HIV1_RT","PTP1B",
           "GLUCOKINASE","CASPASE7","GLUR2_TRU","GLUK1_BPAM"]

print(f"{'target':<16}{'rho(q,hop)':>12}{'R2 lin':>8}{'R2 shell':>10} | "
      f"{'AUC uncond':>12}{'AUC in-shell':>14}{'drop':>8}")
rows={}
for t in TARGETS:
    cfg, apo, seed, pocket = prep(t)
    c=apo.coords; cut=float(cfg.get("enm_cutoff",8.0)); n=len(c)
    m=np.ones(n,bool); m[seed]=False
    y=pocket.astype(int)[m]
    if y.sum()<5: continue
    hop=(-hop_from_seed(c,seed,cutoff=cut))[m]
    q=time_averaged_ctqw_converged(build_H_new(c,apo.bfactors,cutoff=cut),
                                   source=seed,coherent=False)[m]
    rho=float(stats.spearmanr(q,hop).statistic)
    X1=np.column_stack([hop,np.ones(len(hop))])
    b1,*_=np.linalg.lstsq(X1,q,rcond=None); r2_lin=1-((q-X1@b1)**2).sum()/((q-q.mean())**2).sum()
    sh=sorted(set(hop.astype(int)))
    X2=np.column_stack([(hop.astype(int)==k).astype(float) for k in sh])
    b2,*_=np.linalg.lstsq(X2,q,rcond=None); r2_sh=1-((q-X2@b2)**2).sum()/((q-q.mean())**2).sum()
    uncond=float(auc(q,y))
    num=den=0.0; per_shell=[]
    for k in sh:
        s=(hop.astype(int)==k)
        if y[s].sum()==0 or y[s].sum()==s.sum(): continue
        a=float(auc(q[s],y[s])); w=float(y[s].sum()*(s.sum()-y[s].sum()))
        num+=a*w; den+=w
        per_shell.append({"hop":int(k),"auc":a,"n":int(s.sum()),"n_pocket":int(y[s].sum())})
    cond=num/den if den else float("nan")
    rows[t]={"rho":rho,"r2_linear":float(r2_lin),"r2_shell":float(r2_sh),
             "auc_uncond":uncond,"auc_within_shell":cond,"per_shell":per_shell}
    print(f"{t:<16}{rho:>12.3f}{r2_lin:>8.3f}{r2_sh:>10.3f} | {uncond:>12.4f}{cond:>14.4f}{cond-uncond:>+8.4f}")

R=[r["r2_shell"] for r in rows.values()]; U=[r["auc_uncond"] for r in rows.values()]
C=[r["auc_within_shell"] for r in rows.values()]
print(f"\n  median |rho(ctqw, hop)|      {np.median([abs(r['rho']) for r in rows.values()]):.3f}")
print(f"  median R2 (shell indicators) {np.median(R):.3f}  <- share of CTQW that is a pure function of hop shell")
print(f"  median AUC unconditional     {np.median(U):.4f}")
print(f"  median AUC WITHIN hop shell  {np.median(C):.4f}   (0.5 = no information beyond distance)")
print(f"  within-shell AUC > 0.55 on {sum(1 for x in C if x>0.55)}/{len(C)} targets;"
      f" > 0.50 on {sum(1 for x in C if x>0.50)}/{len(C)}")
print(f"  one-sample Wilcoxon, within-shell AUC vs 0.5: p={stats.wilcoxon(np.array(C)-0.5).pvalue:.4f}")
(_ROOT/"results/tasks/0247_ctqw_vs_distance").mkdir(parents=True,exist_ok=True)
(_ROOT/"results/tasks/0247_ctqw_vs_distance/results.json").write_text(json.dumps(rows,indent=1))

# ---------------------------------------------------------------------------
# Follow-up: CTQW retains real within-shell discrimination (above), yet its
# incremental CV AUC over the full geometry block is ~0 (TASK-0245). Those are
# only consistent if CTQW's non-distance information is already carried by the
# OTHER two geometric baselines. Tested directly: same within-shell AUC, for
# every feature, so they are compared on equal footing with distance held fixed.
# ---------------------------------------------------------------------------
from allostery.baselines import degree_centrality, euclid_from_seed_centroid

def within_shell(v, hop, y):
    num=den=0.0
    for k in sorted(set(hop.astype(int))):
        s=(hop.astype(int)==k)
        if y[s].sum()==0 or y[s].sum()==s.sum(): continue
        w=float(y[s].sum()*(s.sum()-y[s].sum())); num+=float(auc(v[s],y[s]))*w; den+=w
    return num/den if den else float("nan")

print("\nWITHIN-SHELL AUC BY FEATURE (distance held constant)")
print(f"  {'target':<16}{'ctqw':>8}{'degree':>9}{'euclid':>9}{'best geom':>11}{'ctqw-best':>11}")
comp={}
for t in TARGETS:
    cfg, apo, seed, pocket = prep(t)
    c=apo.coords; cut=float(cfg.get("enm_cutoff",8.0)); n=len(c)
    m=np.ones(n,bool); m[seed]=False
    y=pocket.astype(int)[m]
    if y.sum()<5: continue
    hop=(-hop_from_seed(c,seed,cutoff=cut))[m]
    q=time_averaged_ctqw_converged(build_H_new(c,apo.bfactors,cutoff=cut),source=seed,coherent=False)[m]
    dg=degree_centrality(c,cutoff=cut)[m]; eu=euclid_from_seed_centroid(c,seed)[m]
    aq,ad,ae=within_shell(q,hop,y),within_shell(dg,hop,y),within_shell(eu,hop,y)
    ad,ae=max(ad,1-ad),max(ae,1-ae)      # orient baselines favourably
    comp[t]={"ctqw":aq,"degree":ad,"euclid":ae}
    print(f"  {t:<16}{aq:>8.4f}{ad:>9.4f}{ae:>9.4f}{max(ad,ae):>11.4f}{aq-max(ad,ae):>+11.4f}")
Q=[v["ctqw"] for v in comp.values()]; G=[max(v["degree"],v["euclid"]) for v in comp.values()]
print(f"\n  median ctqw {np.median(Q):.4f}  vs  median best-geometry {np.median(G):.4f}")
print(f"  ctqw beats best geometry within-shell on {sum(1 for a,b in zip(Q,G) if a>b)}/{len(Q)} targets")
print(f"  Wilcoxon ctqw vs best geometry: p={stats.wilcoxon(np.array(Q)-np.array(G)).pvalue:.4f}")
(_ROOT/"results/tasks/0247_ctqw_vs_distance/within_shell_by_feature.json").write_text(json.dumps(comp,indent=1))
