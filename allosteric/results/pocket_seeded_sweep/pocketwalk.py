#!/usr/bin/env python3
"""POCKET-seeded CTQW: the initial state is the WHOLE pocket (uniform superposition over its
residues), the walk goes to the active site, one score per pocket, pockets ranked directly.
Same pocket selection (fpocket n PASSer, minrank), same 13 Hamiltonians, same 8 scores as the
residue sweep; plus an INCOHERENT baseline (mean of the per-residue walks) for every score.
Truth: pocket is the drug pocket if drug_frac > 0.5 (sec 14 rule). Sharded + checkpointed."""
import os,sys,json,time
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
import pocketsweep as ps

OUT=os.environ.get("OUT","pocketwalk.json"); CKPT=10
def rz(r):
    r=np.asarray(r,float); m=np.median(r); return (r-m)/(1.4826*np.median(np.abs(r-m))+1e-12)

def score_pockets(H,A,members,cov):
    """-> {score: (coherent vector over pockets, incoherent vector)} for one operator."""
    ev,V=np.linalg.eigh(H); Va=V[A,:]                       # (|A|, N)
    wA=(Va**2).sum(0)                                        # sum_a |v_k(a)|^2  per mode
    sq=V*V; res_pavg=(sq*wA).sum(1)                          # per-residue p_avg to A (closed form)
    gaps=np.diff(np.sort(ev)); gap=max(float(gaps[gaps>1e-9].min()) if (gaps>1e-9).any() else 1e-4,1e-4)
    ts=np.linspace(0.0,ps.C_T/gap,ps.NT)
    C=np.stack([V[m,:].sum(0)/np.sqrt(len(m)) for m in members])      # (P, N) eigen-amplitudes of |psi0>
    pavg_c=((np.abs(C)**2)*wA).sum(1)                        # T->inf average, non-degenerate approx (same as residue version)
    pavg_i=np.array([res_pavg[m].mean() for m in members])
    # time grid: P(t)=sum_a |<a|U(t)|psi0>|^2 ; incoherent: mean over members of per-residue transfer
    pk_c=np.zeros(len(members)); pk_i=np.zeros(len(members))
    for t in ts:
        ph=np.exp(-1j*ev*t)
        amp=(Va*ph)@C.T                                      # (|A|, P)
        pk_c=np.maximum(pk_c,(np.abs(amp)**2).sum(0))
        U_A=(Va*ph)@V.T                                      # (|A|, N) transfer amplitude residue->A
        tr=(np.abs(U_A)**2).sum(0)                           # per-residue transfer prob at t
        pk_i=np.maximum(pk_i,np.array([tr[m].mean() for m in members]))
    out={"p_avg":(pavg_c,pavg_i),"p_peak":(pk_c,pk_i),
         "R":(pk_c/np.clip(pavg_c,1e-300,None),pk_i/np.clip(pavg_i,1e-300,None))}
    for em,eta in ps.GREEN:
        E={"zero":0.0,"lmax":float(ev.max())}[em]
        Gc=(Va/((E+1j*eta)-ev))@C.T;  gc=(np.abs(Gc)**2).sum(0)
        Gr=(Va/((E+1j*eta)-ev))@V.T;  gr=(np.abs(Gr)**2).sum(0); gi=np.array([gr[m].mean() for m in members])
        out["green_%s_%g"%(em,eta)]=(gc,gi)
    # proximity/size correction at POCKET level: log p ~ 1 + mean_hop + log_size
    Xd=cov
    for tag,(vc,vi) in list(out.items()):
        if tag!="p_avg": continue
        for name,v in (("residLOG",np.log(np.clip(vc,1e-300,None))),("residRAW",vc)):
            b,*_=np.linalg.lstsq(Xd,v,rcond=None); rc=rz(v-Xd@b)
            vv=np.log(np.clip(vi,1e-300,None)) if name=="residLOG" else vi
            b2,*_=np.linalg.lstsq(Xd,vv,rcond=None); ri=rz(vv-Xd@b2)
            out[name]=(rc,ri)
    return out

def main():
    if not ps.FP: sys.exit("fpocket binary not found -- refusing to run")
    work=[w for w in json.load(open("operator_worklist.json")) if w["is_distal"]]
    work=[w for i,w in enumerate(work) if i%ps.NSHARD==ps.SHARD]
    os.makedirs(ps.CACHE,exist_ok=True)
    res=json.load(open(OUT)) if os.path.exists(OUT) else {}
    print("pocketwalk | fpocket=%s | %d proteins | %d done | MIN_HOP=%d SELECTOR=%s"%(ps.FP,len(work),len(res),ps.MIN_HOP,ps.SELECTOR),flush=True)
    t0=time.time()
    for k,w in enumerate(work,1):
        if w["name"] in res: continue
        try:
            p=ps.fetch(w["pdb"]); X,idx,ch,BF=ps.ca(p,w["chain"]) if p else (None,None,None,None)
            if X is None or len(X)<30: res[w["name"]]={"error":"no CA"}; continue
            A=[idx[r] for r in w["active"] if r in idx]; T=set(idx[r] for r in w["truth"] if r in idx)
            if len(A)<1 or not T: res[w["name"]]={"error":"sites"}; continue
            pk_all=ps.run_fpocket(p,ch)
            if not pk_all: res[w["name"]]={"error":"fpocket none"}; continue
            pk,seldbg=ps.select_pockets(pk_all,w["pdb"],ch,ps.N_POCKETS)
            if not pk: res[w["name"]]={"error":"selector empty: %s"%seldbg}; continue
            D2=((X[:,None,:]-X[None,:,:])**2).sum(-1); adjm=(D2<ps.CUTOFF**2)&(D2>0)
            hop=dijkstra(csr_matrix(adjm.astype(np.int8)),directed=False,indices=A,unweighted=True,min_only=True)
            deg=adjm.sum(1).astype(float); Aset=set(A)
            act_pk=max(pk,key=lambda q:len({idx[r] for r in q["residues"] if r in idx}&Aset))["id"]
            P=[]
            for q in pk:
                if q["id"]==act_pk: continue
                mem=sorted({idx[r] for r in q["residues"] if r in idx and idx[r] not in Aset and hop[idx[r]]>=ps.MIN_HOP})
                if len(mem)<2: continue
                nd=sum(1 for i in mem if i in T)
                P.append(dict(id=q["id"],n=len(mem),n_drug=nd,drug_frac=round(nd/len(mem),3),
                              rk_fp=q.get("rk_fp"),rk_pa=q.get("rk_pa"),drug=q["drug"],mem=mem,
                              mean_hop=float(np.mean([hop[i] if np.isfinite(hop[i]) else 99 for i in mem])),
                              mean_deg=float(deg[mem].mean())))
            y=np.array([1 if q["drug_frac"]>0.5 else 0 for q in P])
            # gate only on "there is something to rank": >=3 pockets and >=1 drug residue somewhere.
            # The TRUTH RULE (strict drug_frac>0.5 vs argmax) is applied in the analysis, not here.
            if len(P)<3 or sum(q["n_drug"] for q in P)==0 or y.sum()==len(y):
                res[w["name"]]={"error":"pockets %d true %d"%(len(P),int(y.sum()) if len(P) else 0),
                                "pockets":[{k2:v2 for k2,v2 in q.items() if k2!="mem"} for q in P]}; continue
            cov=np.column_stack([np.ones(len(P)),[q["mean_hop"] for q in P],np.log([q["n"] for q in P])])
            members=[q["mem"] for q in P]
            cells={}
            OPS=[(wt,nm) for wt in ps.WEIGHTS for nm in ps.NORMS]+[("hnew","full")]
            for wt,nm in OPS:
                H=ps.build_H_new(X,BF) if wt=="hnew" else ps.build(X,wt,nm)
                sc=score_pockets(H,A,members,cov)
                for tag,(vc,vi) in sc.items():
                    cells["%s|%s|%s|coh"%(wt,nm,tag)]=[float(x) for x in vc]
                    cells["%s|%s|%s|inc"%(wt,nm,tag)]=[float(x) for x in vi]
            res[w["name"]]=dict(cells=cells,y=y.tolist(),
                                pockets=[{k2:v2 for k2,v2 in q.items() if k2!="mem"} for q in P],
                                cluster=w["cluster"],source=w["source"],truth_type=w["truth_type"],
                                n_active=len(A),selector=ps.SELECTOR,min_hop=ps.MIN_HOP)
        except Exception as e:
            res[w["name"]]={"error":"%s: %s"%(type(e).__name__,e)}
        if k%CKPT==0:
            json.dump(res,open(OUT,"w")); print("  CKPT %d/%d (%.0fs)"%(k,len(work),time.time()-t0),flush=True)
    json.dump(res,open(OUT,"w"))
    ok=sum(1 for v in res.values() if "cells" in v)
    print("DONE %d scored, %d errors, %.0fs"%(ok,len(res)-ok,time.time()-t0),flush=True)

if __name__=="__main__": main()
