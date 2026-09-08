#!/usr/bin/env python3
"""THE FAIR COMPARISON. Every baseline here is SEEDED AT THE ACTIVE SITE, exactly like the
Seeded-CTQW-pipeline. This isolates whether COHERENCE does anything, which is the question the
challenge actually asks.

  quantum  : e^{-iHt}, amplitudes, time-averaged  (our p_avg / neg_dE cell)
  classical: e^{-Lt}   heat kernel -- the EXACT classical twin, probabilities not amplitudes
             personalised PageRank from the active site
             communicability e^A between residue and active site
             hop distance (already had this)
Same graph, same seed, same residues, same labels."""
import os,json,gzip,importlib.util,numpy as np,warnings
warnings.filterwarnings("ignore")
from scipy.linalg import eigh
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from sklearn.metrics import roc_auc_score
os.environ["SELECTOR"]="passer_only"
spec=importlib.util.spec_from_file_location("ps","pocketsweep.py"); ps=importlib.util.module_from_spec(spec)
try: spec.loader.exec_module(ps)
except SystemExit: pass
FR=os.environ.get("FR","/Users/t/Quantum_allosteric-scanner/allosteric/results/full_run_1022")  # "." on the node
W={w["name"]:w for w in json.load(open("operator_worklist.json"))}
R=json.load(gzip.open(f"{FR}/r2_minhop1.json.gz","rt"))
FIX="gauss|sym|neg_dE"
SHARD=int(os.environ.get("SHARD","0")); NS=int(os.environ.get("NSHARD","1")); OUT=os.environ.get("OUT","sc.json")
prot=[n for n,v in R.items() if "cells" in v and n in W and FIX in v.get("cells",{})]
prot=[n for i,n in enumerate(sorted(prot)) if i%NS==SHARD]
res=json.load(open(OUT)) if os.path.exists(OUT) else {}
print("shard %d/%d: %d proteins"%(SHARD,NS,len(prot)),flush=True)
for k,n in enumerate(prot,1):
    if n in res: continue
    try:
        v=R[n]; w=W[n]
        p=ps.fetch(w["pdb"]); X,idx,ch,BF=ps.ca(p,w["chain"])
        if X is None: res[n]={"err":"noCA"}; continue
        A_idx=[idx[r] for r in w["active"] if r in idx]
        seeds=[idx[r] for r in v["seed_resnum"] if r in idx]
        if not A_idx or len(seeds)!=len(v["seed_resnum"]): res[n]={"err":"idx"}; continue
        y=np.array(v["y"])
        if y.sum()==0 or y.sum()==len(y): res[n]={"err":"degen"}; continue
        D2=((X[:,None,:]-X[None,:,:])**2).sum(-1); Adj=((D2<64.0)&(D2>0)).astype(float)
        deg=Adj.sum(1); L=np.diag(deg)-Adj
        ev,V=eigh(L)                                  # Laplacian spectrum, shared by both walks
        gap=max(float(np.diff(np.sort(ev))[np.diff(np.sort(ev))>1e-9].min()) if (np.diff(np.sort(ev))>1e-9).any() else 1e-4,1e-4)
        ts=np.linspace(0.0,1.0/gap,48)
        # CLASSICAL HEAT KERNEL e^{-Lt}, seeded at the active site, time-averaged
        heat=np.zeros(len(seeds))
        for t in ts:
            K=(V*np.exp(-ev*t))@V.T
            heat+=K[np.ix_(seeds,A_idx)].sum(1)
        heat/=len(ts)
        # CLASSICAL RANDOM WALK long-time (personalised PageRank from the active site)
        P=Adj/np.maximum(deg,1e-9)[:,None]
        r=np.zeros(len(X)); r[A_idx]=1.0/len(A_idx); pr=r.copy()
        for _ in range(60): pr=0.85*(P.T@pr)+0.15*r
        # COMMUNICABILITY e^{A} between residue and active site (Estrada)
        eva,Va=eigh(Adj); Ecomm=(Va*np.exp(eva-eva.max()))@Va.T
        comm=Ecomm[np.ix_(seeds,A_idx)].sum(1)
        # ---- v2 notebook's own "same-condition classical" set, ported verbatim from
        # classical_coupling_scores(): weighted graph, each residue scored by coupling to the
        # ACTIVE SITE. Only the operator differs from e^{-iHt}.
        act=np.array(sorted(A_idx))
        mu,U=eigh(Adj)                                        # weighted communicability expm(W)
        Gc=(U*np.exp(mu-mu.max()))@U.T
        v2_comm=Gc[:,act].mean(1)[seeds]
        Cinv=np.linalg.pinv(L)                                # GNM covariance, zero mode dropped
        dd=np.sqrt(np.clip(np.diag(Cinv),1e-12,None))
        v2_dcc=((Cinv/np.outer(dd,dd))[:,act].mean(1))[seeds]  # Bahar GNM cross-correlation
        v2_prs=((Cinv[:,act]**2).mean(1))[seeds]               # Atilgan 2009 perturbation response
        dC=np.diag(Cinv)
        v2_cmt=(-(dC[:,None]+dC[None,:]-2.0*Cinv)[:,act].mean(1))[seeds]  # -effective resistance
        # unseeded centralities, so every baseline lands in one table
        import networkx as _nx
        _G=_nx.from_numpy_array(Adj)
        _ev=_nx.eigenvector_centrality_numpy(_G); _cl=_nx.closeness_centrality(_G)
        u_eig=np.array([_ev[i] for i in seeds]); u_clo=np.array([_cl[i] for i in seeds])
        u_deg=deg[seeds]
        _wg,_Vg=eigh(L); _nz=np.where(_wg>1e-8)[0][:10]
        u_gnm=((_Vg[:,_nz]**2).sum(1))[seeds] if len(_nz) else np.zeros(len(seeds))
        # hop distance (seeded, already known)
        adj=csr_matrix((Adj>0).astype(np.int8))
        hop=dijkstra(adj,directed=False,indices=A_idx,unweighted=True,min_only=True)[seeds]
        ns=len(y); ctqw=1.0-(np.asarray(v["ranks"][FIX],float)-1)/max(ns-1,1)
        def p5(v):
            o=np.argsort(-np.asarray(v,float)); return float(y[o[:5]].sum())/5.0
        # ---- SITE LEVEL: aggregate residue scores into pockets (pipeline rule = pocket's BEST
        # residue), rank pockets, and ask whether the DRUG pocket comes out on top.
        sp=v.get("seed_pocket") or []
        pk_of=np.array(sp) if len(sp)==len(y) else None
        pk_ids=sorted(set(sp)) if pk_of is not None else []
        # the true pocket = the one holding the most drug residues
        truth_pk=None
        if pk_of is not None and len(pk_ids)>1:
            nd={q:int(y[pk_of==q].sum()) for q in pk_ids}
            truth_pk=max(nd,key=nd.get)
            if nd[truth_pk]==0: truth_pk=None
        def site(v):
            """returns (rank_of_true_pocket, n_pockets) using the pipeline's best-residue rule"""
            if truth_pk is None or pk_of is None: return None
            vv=np.asarray(v,float)
            sc={q:float(vv[pk_of==q].max()) for q in pk_ids}
            order=sorted(pk_ids,key=lambda q:-sc[q])
            return order.index(truth_pk)+1,len(pk_ids)
        row={"cluster":w["cluster"],"is_distal":bool(w["is_distal"]),"n":int(ns),
             "n_drug":int(y.sum()),
             "ctqw_auc":float(roc_auc_score(y,ctqw)),"ctqw_p5":p5(ctqw)}
        _s=site(ctqw)
        if _s: row["n_pockets"]=_s[1]; row["ctqw_site_rank"]=_s[0]
        for nm,vec in (("heat_kernel",heat),("pagerank",pr[seeds]),("communicability",comm),("neg_hop",-hop),
                       ("v2_communicability",v2_comm),("v2_gnm_dcc",v2_dcc),("v2_gnm_prs",v2_prs),("v2_commute_time",v2_cmt),
                       ("u_eigenvector",u_eig),("u_closeness",u_clo),("u_degree",u_deg),("u_gnm_lowmode",u_gnm),
                       ("pos_hop",hop)):
            vec=np.nan_to_num(np.asarray(vec,float))
            row[nm+"_auc"]=float(roc_auc_score(y,vec)); row[nm+"_p5"]=p5(vec)
            _t=site(vec)
            if _t: row[nm+"_site_rank"]=_t[0]
        res[n]=row
    except Exception as e: res[n]={"err":str(e)[:50]}
    if k%15==0: json.dump(res,open(OUT,"w")); print("  %d/%d"%(k,len(prot)),flush=True)
json.dump(res,open(OUT,"w"))
print("SHARD %d DONE: %d scored"%(SHARD,sum(1 for x in res.values() if "ctqw_auc" in x)),flush=True)
