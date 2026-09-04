#!/usr/bin/env python3
"""Consume pocket_sweep.json: which (Hamiltonian, score) cells clear the bar,
which Hamiltonian wins per protein, do winners cluster by protein features,
and what H_new parameters those winners correspond to."""
import json,glob,sys,collections
import numpy as np, pandas as pd

R={}
for f in sorted(glob.glob(sys.argv[1] if len(sys.argv)>1 else "sweep_*.json")):
    R.update(json.load(open(f)))
ok={k:v for k,v in R.items() if "cells" in v}
err=collections.Counter(str(v.get("error"))[:40] for k,v in R.items() if "cells" not in v)
print("proteins scored: %d / %d"%(len(ok),len(R)))
for e,c in err.most_common(8): print("   err %-42s %d"%(e,c))
if not ok: sys.exit()

rows=[]
for name,v in ok.items():
    for cell,(auc,p5) in v["cells"].items():
        w,n,s=cell.split("|",2)
        rows.append(dict(protein=name,weight=w,norm=n,score=s,op="%s/%s"%(w,n),
                         auc=auc,p5=p5,cluster=v["cluster"],source=v["source"],
                         truth_type=v["truth_type"],n_seeds=v["n_seeds"],
                         base=v["base"],n_drug=v["n_drug"]))
df=pd.DataFrame(rows); df.to_csv("pocket_sweep_cells.csv",index=False)
print("\ncells: %d  (%d ops x %d scores x %d proteins)"%(
    len(df),df.op.nunique(),df.score.nunique(),df.protein.nunique()))

# ---- 1. marginal performance of every (operator, score) cell, family-clustered
print("\n=== MEAN AUC / P@5 per (operator, score), averaged over protein FAMILIES ===")
fam=df.groupby(["op","score","cluster"])[["auc","p5"]].mean().reset_index()
tab=fam.groupby(["op","score"])[["auc","p5"]].mean().reset_index()
tab["n_hit"]=[int(((df.op==o)&(df.score==s)&(df.auc>0.6)&(df.p5>=0.8)).sum())
              for o,s in zip(tab.op,tab.score)]
print(tab.sort_values("auc",ascending=False).head(20).to_string(index=False,
      float_format=lambda x:"%.3f"%x))
print("\nbest-by-P@5:")
print(tab.sort_values("p5",ascending=False).head(10).to_string(index=False,
      float_format=lambda x:"%.3f"%x))
print("\nAUC pivot (rows=operator, cols=score):")
print(tab.pivot(index="op",columns="score",values="auc").to_string(float_format=lambda x:"%.3f"%x))
print("\nP@5 pivot:")
print(tab.pivot(index="op",columns="score",values="p5").to_string(float_format=lambda x:"%.3f"%x))

# ---- 2. the bar: AUC > 0.6 AND P@5 in {0.8, 1.0}
BAR=df[(df.auc>0.6)&(df.p5>=0.8)]
print("\n=== CELLS CLEARING AUC>0.6 AND P@5>=0.8: %d cells, %d/%d proteins ==="%(
    len(BAR),BAR.protein.nunique(),df.protein.nunique()))
print("  P@5=1.0: %d cells / %d proteins"%((BAR.p5>=1.0).sum(),BAR[BAR.p5>=1.0].protein.nunique()))
print("\ntop operators among clearing cells:")
print(BAR.op.value_counts().head(12).to_string())
print("\ntop scores among clearing cells:")
print(BAR.score.value_counts().head(12).to_string())

# ---- 3. per-protein winning Hamiltonian (best AUC over scores), then group
best=df.loc[df.groupby("protein").auc.idxmax()]
best.to_csv("pocket_sweep_winners.csv",index=False)
print("\n=== WINNING OPERATOR PER PROTEIN (max AUC over all scores) ===")
print(best.op.value_counts().to_string())
print("\nwinner x score:")
print(pd.crosstab(best.op,best.score).to_string())
print("\nmean winning AUC %.3f | proteins with winner AUC>0.6: %d"%(
    best.auc.mean(),(best.auc>0.6).sum()))

# ---- 4. do winners separate by protein features?
try:
    T=pd.DataFrame(json.load(open("topology_features.json")))
    key="name" if "name" in T.columns else T.columns[0]
    M=best.merge(T,left_on="protein",right_on=key,how="left")
    num=[c for c in T.columns if pd.api.types.is_numeric_dtype(T[c])]
    print("\n=== PROTEIN FEATURES BY WINNING OPERATOR (n>=5 groups) ===")
    g=M.groupby("op")
    keep=[k for k,v in g if len(v)>=5]
    if keep and num:
        sub=M[M.op.isin(keep)]
        print(sub.groupby("op")[num[:12]].mean().to_string(float_format=lambda x:"%.2f"%x))
        print("\ngroup sizes:", sub.op.value_counts().to_dict())
        from scipy import stats as st
        print("\nKruskal-Wallis: does the feature differ across winning operators?")
        for c in num[:14]:
            arrs=[v[c].dropna().values for _,v in sub.groupby("op") if v[c].notna().sum()>=4]
            if len(arrs)>=2:
                try:
                    h,p=st.kruskal(*arrs)
                    print("   %-24s H=%7.2f  p=%.4f %s"%(c,h,p,"  <-- separates" if p<0.05 else ""))
                except Exception: pass
except FileNotFoundError:
    print("\n(topology_features.json absent - skipping feature analysis)")

# ---- 5. winner -> H_new parameter translation
print("""
=== WINNER -> H_new TRANSLATION ===
H_new = L_norm(cutoff, alpha) + diag(sum_k lambda_k V_k)
An operator (weight,norm) maps onto H_new only through its STRUCTURAL axes:
   norm=sym  -> H_new's own normalisation                      (exactly reachable, lambda=0)
   norm=comb -> combinatorial Laplacian                        (NOT reachable: different D scaling)
   norm=adj  -> adjacency                                      (NOT reachable: sign/diagonal differ)
   weight=exp   -> H_new kernel with alpha as-is               (exactly reachable)
   weight=binary-> alpha -> 0                                  (exactly reachable in the limit)
   weight=gauss -> exp(-D^2/2s^2) is NOT exp(-alpha*d)         (NOT reachable)
   weight=harm  -> 1/(d+eps)^2 is NOT exp(-alpha*d)            (NOT reachable)
So H_new spans {binary,exp} x {sym} only; the other 8 operators need a kernel
generalisation (build_H_general's weight/norm switches) to be expressible.""")
reach=best.op.isin(["exp/sym","binary/sym"])
print("proteins whose winner IS already reachable by H_new: %d/%d (%.0f%%)"%(
    reach.sum(),len(best),100*reach.mean()))
print("proteins needing a kernel/normalisation H_new does not have: %d"%(~reach).sum())
print("\nof the unreachable winners, what is missing:")
u=best[~reach]
print("   non-sym normalisation : %d"%(u.norm!="sym").sum())
print("   non-exp/binary kernel : %d"%(~u.weight.isin(["exp","binary"])).sum())
