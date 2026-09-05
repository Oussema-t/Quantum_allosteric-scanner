#!/usr/bin/env python3
"""Section-14 CONSENSUS block, verbatim logic, applied to every protein in the sweep.
Per SCORE: rank matrix Rk (seeds x operators, 1=best) -> Kendall's W + Friedman p;
each operator votes for the pocket with the lowest MEDIAN rank of its residues;
most-recurrent pocket = most votes; TRUE drug pocket = drug_frac > 0.5.
Then 'DO THE SCORES AGREE?': which pocket each score elects, how many elect a TRUE pocket."""
import json,glob,sys
import numpy as np
from scipy.stats import chi2
SC=["p_avg","p_peak","R","residLOG","residRAW","green_zero_0.05","green_zero_0.01","green_lmax_0.05"]
OPS=["binary/adj","binary/comb","binary/sym","exp/adj","exp/comb","exp/sym",
     "gauss/adj","gauss/comb","gauss/sym","harm/adj","harm/comb","harm/sym","hnew/full"]

def consensus(v,score):
    """exactly sec 14 _consensus() for one scoring definition."""
    y=np.array(v["y"],float); sp=v["seed_pocket"]; n=len(y)
    pmem={}
    for k,q in enumerate(sp): pmem.setdefault(q,[]).append(k)
    pdrug={q:float(np.mean(y[ix])) for q,ix in pmem.items()}
    ops=[o for o in OPS if "%s|%s"%(o.replace("/","|"),score) in v["ranks"]]
    if len(ops)<2: return None
    m=len(ops); Rk=np.zeros((n,m))
    for j,o in enumerate(ops): Rk[:,j]=v["ranks"]["%s|%s"%(o.replace("/","|"),score)]
    Rsum=Rk.sum(1)
    W=(12.0*((Rsum-Rsum.mean())**2).sum()/(m**2*(n**3-n))) if n>1 else float("nan")
    p=float(chi2.sf(m*(n-1)*W,n-1))
    TOPK=max(5,int(round(0.10*n)))
    pvote={q:0 for q in pmem}; pvoters={q:[] for q in pmem}
    for j in range(m):
        wq=min(pmem,key=lambda q:np.median(Rk[pmem[q],j]))
        pvote[wq]+=1; pvoters[wq].append(ops[j])
    pmed={q:float(np.median(Rk[ix,:])) for q,ix in pmem.items()}
    bp=max(pmem,key=lambda q:(pvote[q],-pmed[q]))
    true_pockets=[q for q in pmem if pdrug[q]>0.5]
    return dict(best_pocket=bp,votes=pvote[bp],n_ops=m,W=W,p=p,drug_frac=pdrug[bp],
                is_true=pdrug[bp]>0.5,pocket_votes=pvote,pvoters=pvoters,pmed=pmed,pdrug=pdrug,
                n_pockets=len(pmem),true_pockets=true_pockets,
                true_votes=sum(pvote[q] for q in true_pockets))

def analyse(R,verbose_for=()):
    ok={k:v for k,v in R.items() if "ranks" in v}
    per_score={s:dict(elect_true=0,agree=0,n=0,true_votes=0,total_votes=0) for s in SC}
    per_protein=[]
    for name,v in ok.items():
        C={}
        for s in SC:
            c=consensus(v,s)
            if c is None: continue
            C[s]=c; d=per_score[s]; d["n"]+=1
            d["elect_true"]+=c["is_true"]; d["agree"]+=(c["p"]<0.05 and c["W"]>1.0/c["n_ops"])
            d["true_votes"]+=c["true_votes"]; d["total_votes"]+=c["n_ops"]
        if not C: continue
        picks={}
        for s,c in C.items(): picks.setdefault(c["best_pocket"],[]).append(s)
        n_true=sum(1 for c in C.values() if c["is_true"])
        has_true=any(c["true_pockets"] for c in C.values())
        per_protein.append(dict(protein=name,cluster=v["cluster"],n_scores=len(C),
            scores_electing_true=n_true,pockets_elected=len(picks),
            unanimous=(len(picks)==1),unanimous_true=(len(picks)==1 and n_true==len(C)),
            has_true_pocket=has_true,n_pockets=next(iter(C.values()))["n_pockets"],
            n_true_pockets=len(next(iter(C.values()))["true_pockets"])))
        if name in verbose_for:
            print("=== %s (%s) ==="%(name,v["cluster"]))
            print("    ===== DO THE SCORES AGREE? top pocket elected by each scoring definition =====")
            print("      %-18s %-8s %-8s %-10s %-7s"%("score","pocket","votes","drug_frac","W"))
            for s,c in C.items():
                print("      %-18s P%-7s %2d/%-5d %-10.2f %-7.3f%s"%(s,str(c["best_pocket"]),c["votes"],c["n_ops"],
                      c["drug_frac"],c["W"],"   <- TRUE" if c["is_true"] else ""))
            print("      >>> pockets elected: %s"%{("P%s"%k):len(x) for k,x in picks.items()})
            print("      >>> scores electing a TRUE drug pocket: %d/%d\n"%(n_true,len(C)))
    return per_score,per_protein

if __name__=="__main__":
    R={}
    for f in sorted(glob.glob(sys.argv[1] if len(sys.argv)>1 else "pv_*.json")): R.update(json.load(open(f)))
    ps,pp=analyse(R,verbose_for=set(sys.argv[2:]))
    N=len(pp); ht=sum(1 for r in pp if r["has_true_pocket"])
    print("proteins analysed: %d | with a TRUE drug pocket (drug_frac>0.5) among the seed pockets: %d"%(N,ht))
    print("\n===== PER SCORE: across %d proteins, does the 13-operator consensus elect the TRUE drug pocket? ====="%N)
    print("%-18s %14s %16s %22s"%("score","elects TRUE","operators AGREE","operator votes to TRUE"))
    for s in SC:
        d=ps[s]
        if d["n"]==0: continue
        print("%-18s %6d/%-3d (%3.0f%%) %7d/%-3d (%3.0f%%) %10d/%-5d (%4.1f%%)"%(s,d["elect_true"],d["n"],100*d["elect_true"]/d["n"],
              d["agree"],d["n"],100*d["agree"]/d["n"],d["true_votes"],d["total_votes"],100*d["true_votes"]/max(1,d["total_votes"])))
    print("\n===== PER PROTEIN: how many of the 8 scores elect the TRUE drug pocket? =====")
    from collections import Counter
    c=Counter(r["scores_electing_true"] for r in pp)
    for k in sorted(c,reverse=True): print("   %d/8 scores -> %3d proteins"%(k,c[k]))
    print("\n   all 8 scores elect the SAME pocket (unanimous): %d proteins; of which it is the TRUE pocket: %d"%(
        sum(r["unanimous"] for r in pp),sum(r["unanimous_true"] for r in pp)))
    print("   proteins where >=4/8 scores elect TRUE: %d"%sum(1 for r in pp if r["scores_electing_true"]>=4))
    print("   proteins where 0/8 scores elect TRUE : %d"%sum(1 for r in pp if r["scores_electing_true"]==0))
    print("\n   proteins with >=4/8: %s"%sorted((r["protein"],r["scores_electing_true"]) for r in pp if r["scores_electing_true"]>=4))
    json.dump(pp,open("sec14_consensus_per_protein.json","w"),indent=1)
