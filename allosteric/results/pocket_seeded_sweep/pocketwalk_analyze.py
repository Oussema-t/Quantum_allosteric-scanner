#!/usr/bin/env python3
"""Pocket-seeded walk: can the method put the TRUE drug pocket at rank 1?
Per cell (Hamiltonian x score x coherent/incoherent): rank of the best true pocket among the
protein's pockets. Top-1 hit rate per Hamiltonian, per score, coherent vs incoherent, vs the exact
chance rate k/n per protein; best-of-all-cells vs a label-permutation null."""
import json,glob,sys
import numpy as np, pandas as pd
def load(pat):
    R={}
    for f in sorted(glob.glob(pat)): R.update(json.load(open(f)))
    return R
def truth_vector(v,rule):
    """strict: drug_frac>0.5 (sec 14).  argmax: the single pocket with the most drug residues,
    accepted only if its drug_frac >= MINFRAC.  Returns None if the rule yields no true pocket."""
    P=v["pockets"]
    if rule=="strict":
        y=np.array([1 if q["drug_frac"]>0.5 else 0 for q in P])
    else:
        fr=np.array([q["drug_frac"] for q in P]); nd=np.array([q["n_drug"] for q in P])
        if nd.max()==0 or fr.max()<MINFRAC: return None
        y=np.zeros(len(P),int); y[int(np.argmax(nd+1e-3*fr))]=1
    if y.sum()==0 or y.sum()==len(y): return None
    return y
MINFRAC=float(__import__("os").environ.get("MINFRAC","0.25"))

def analyse(R,label,rule="strict"):
    ok={k:v for k,v in R.items() if "cells" in v}
    err={}
    for v in R.values():
        if "cells" not in v:
            e=str(v.get("error","")); key=("no TRUE pocket (drug_frac>0.5) among selected" if e.startswith("pockets") and " true 0" in e
                 else "all pockets TRUE" if e.startswith("pockets") else e[:40]); err[key]=err.get(key,0)+1
    rows=[]; chance=[]; best_rank=[]; null_best=[]
    rng=np.random.default_rng(0)
    for n,v in ok.items():
        y=truth_vector(v,rule)
        if y is None: err["no true pocket under rule=%s"%rule]=err.get("no true pocket under rule=%s"%rule,0)+1; continue
        k=int(y.sum()); npk=len(y); chance.append(k/npk)
        M=[]
        for c,vec in v["cells"].items():
            w,nm,s,mode=c.split("|"); vec=np.asarray(vec,float)
            order=np.argsort(-vec); rank=np.empty(npk,int); rank[order]=np.arange(1,npk+1)
            r_true=int(rank[y==1].min())                    # best true pocket's rank
            rows.append(dict(protein=n,cluster=v["cluster"],op=w+"/"+nm,score=s,mode=mode,
                             rank_true=r_true,top1=r_true==1,top3=r_true<=3,n_pockets=npk,k=k))
            M.append(vec)
        M=np.vstack(M)                                       # cells x pockets
        rk=np.argsort(np.argsort(-M,axis=1),axis=1)+1       # rank matrix
        best_rank.append(int(rk[:,y==1].min()))              # best-of-all-cells rank of a true pocket
        nb=[]
        for _ in range(200):
            perm=rng.permutation(npk); nb.append(int(rk[:,perm[:k]].min()))
        null_best.append(float(np.mean(np.array(nb)==1)))
    D=pd.DataFrame(rows,columns=["protein","cluster","op","score","mode","rank_true","top1","top3","n_pockets","k"])
    if D.empty:
        print("="*78); print("%s | truth rule = %s | %d proteins with cells, 0 usable under this rule"%(label,rule,len(ok)))
        for e,c in sorted(err.items(),key=lambda x:-x[1]): print("   not scored: %-50s %d"%(e,c))
        return D,pd.DataFrame()
    print("="*78); print("%s | truth rule = %s | %d proteins with cells, %d usable under this rule"%(label,rule,len(ok),len(set(D.protein)) if rows else 0))
    for e,c in sorted(err.items(),key=lambda x:-x[1]): print("   not scored: %-50s %d"%(e,c))
    ch=float(np.mean(chance))
    print("\nCHANCE top-1 rate (mean k/n over proteins): %.1f%%   | pockets per protein: median %d, true pockets: median %d"%(
        100*ch,D.groupby("protein").n_pockets.first().median(),D.groupby("protein").k.first().median()))
    print("\n--- TOP-1 HIT RATE per Hamiltonian (best score) and per score (best Hamiltonian), coherent vs incoherent ---")
    for mode in ("coh","inc"):
        d=D[D["mode"]==mode]
        print("  [%s]"%("COHERENT pocket superposition" if mode=="coh" else "INCOHERENT (mean of residue walks)"))
        g=d.groupby(["op","score"]).top1.mean().unstack()
        print(("      "+g.round(2).to_string().replace("\n","\n      ")))
        print("      mean over all cells: top-1 %.1f%%  top-3 %.1f%%   (chance top-1 %.1f%%)"%(100*d.top1.mean(),100*d.top3.mean(),100*ch))
    # per protein: fraction of cells with the true pocket at rank 1
    P=D.groupby("protein").agg(frac_top1=("top1","mean"),n_cells=("top1","size"),k=("k","first"),n=("n_pockets","first"),cluster=("cluster","first"))
    P["chance"]=P.k/P.n
    P["excess"]=P.frac_top1-P.chance
    print("\n--- PER PROTEIN: fraction of the %d cells that put the TRUE pocket at rank 1 ---"%int(P.n_cells.median()))
    for th in (0.9,0.75,0.5):
        print("   >= %.0f%% of cells: %d proteins"%(100*th,(P.frac_top1>=th).sum()))
    print("   proteins where rank-1 rate exceeds chance by >0.25: %d"%(P.excess>0.25).sum())
    print("   proteins where NO cell puts the true pocket first: %d"%(P.frac_top1==0).sum())
    top=P.sort_values("frac_top1",ascending=False).head(12)
    print("\n   %-12s %-26s %8s %7s %5s"%("protein","family","top1frac","chance","k/n"))
    for n,r in top.iterrows(): print("   %-12s %-26s %8.2f %7.2f %2d/%-2d"%(n,str(r.cluster)[:26],r.frac_top1,r.chance,r.k,r.n))
    print("\n--- BEST-OF-ALL-CELLS: is SOME cell putting the true pocket first? ---")
    br=np.array(best_rank); nbp=np.array(null_best)
    print("   observed: true pocket at rank 1 in some cell for %d/%d proteins (%.0f%%)"%((br==1).sum(),len(br),100*(br==1).mean()))
    print("   null    : expected %.0f%% of proteins by label permutation (same cells)"%(100*nbp.mean()))
    return D,P
if __name__=="__main__":
    pats=sys.argv[1:] or ["pwr2_*.json","pwr1_*.json"]
    for pat in pats:
        if not glob.glob(pat): continue
        for rule in ("strict","argmax"):
            D,P=analyse(load(pat),"POCKET-SEEDED WALK "+pat,rule); P.to_csv(pat.replace("_*.json","_%s_per_protein.csv"%rule))
