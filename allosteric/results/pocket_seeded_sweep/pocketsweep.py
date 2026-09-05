#!/usr/bin/env python3
"""Section-14 style, at scale: seed from the top-N fpocket pockets, walk to the active site,
score with the full battery, across 12 Hamiltonians. Resumable -- checkpoints every 10.

Per protein:  fpocket -> top-N pockets -> pocket residues as seeds -> drop seeds < MIN_HOP
              from the active site -> for each of 12 operators, score every seed by
              p_avg, p_peak, R, residual(LOG/RAW), Green x3 -> AUC + P@5 vs the drug pocket.
"""
import json, os, re, glob, shutil, subprocess, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from scipy import stats as st
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from sklearn.metrics import roc_auc_score

CACHE="pdb_cache"; OUT=os.environ.get("OUT","pocket_sweep.json"); CKPT=10
N_POCKETS=int(os.environ.get("N_POCKETS","10")); MIN_HOP=int(os.environ.get("MIN_HOP","2"))
SHARD=int(os.environ.get("SHARD","0")); NSHARD=int(os.environ.get("NSHARD","1"))
CUTOFF=10.0; ALPHA=0.3; SIGMA=6.0; EPS=0.5; NT=48; C_T=1.0
WEIGHTS=["binary","exp","gauss","harm"]; NORMS=["adj","comb","sym"]
GREEN=[("zero",0.05),("zero",0.01),("lmax",0.05)]
FP=shutil.which("fpocket")
AA3={"ALA","ARG","ASN","ASP","CYS","GLN","GLU","GLY","HIS","ILE","LEU","LYS","MET",
     "PHE","PRO","SER","THR","TRP","TYR","VAL","MSE"}

def fetch(pid):
    p=os.path.join(CACHE,pid+".pdb")
    if os.path.exists(p) and os.path.getsize(p)>0: return p
    t=p+".part%d"%SHARD
    for a in range(4):
        try:
            with urllib.request.urlopen("https://files.rcsb.org/download/%s.pdb"%pid,timeout=30) as r,open(t,"wb") as f:
                while True:
                    c=r.read(1<<16)
                    if not c: break
                    f.write(c)
            os.replace(t,p); return p
        except Exception: time.sleep(1.5**a)
    return None

def ca(path,chain):
    ch={}; seen=set()
    with open(path,errors="replace") as fh:
        for l in fh:
            if l.startswith("ENDMDL"): break
            if l[:6].strip() not in ("ATOM","HETATM"): continue
            rn=l[17:20].strip()
            if l[:6].strip()=="HETATM" and rn not in AA3: continue
            if l[12:16].strip()!="CA": continue
            c=l[21:22]
            try: k=(c,int(l[22:26]),l[26:27])
            except ValueError: continue
            if k in seen: continue
            seen.add(k)
            try: ch.setdefault(c,[]).append((int(l[22:26]),[float(l[30:38]),float(l[38:46]),float(l[46:54])],float(l[60:66] or 0.0)))
            except ValueError: pass
    if not ch: return None,None,None
    c=chain if chain in ch else max(ch,key=lambda k:len(ch[k]))
    return (np.array([x for _,x,_ in ch[c]],float),
            {r:i for i,r in enumerate([r for r,_,_ in ch[c]])},c,
            np.array([b for _,_,b in ch[c]],float))

def run_fpocket(pdb,chain,tmp=None):
    tmp=tmp or ("/tmp/fp%d"%SHARD)
    """Top pockets on ONE chain, sorted by druggability. [] if the binary is missing."""
    if not FP: return []
    os.makedirs(tmp,exist_ok=True)
    w=os.path.join(tmp,"in.pdb")
    with open(pdb,errors="replace") as a, open(w,"w") as b:
        for l in a:
            if l.startswith("ENDMDL"): break
            if l[:6].strip() in ("ATOM","HETATM") and l[21:22]==chain: b.write(l)
        b.write("END\n")
    for d in glob.glob(os.path.join(tmp,"in_out")): shutil.rmtree(d,ignore_errors=True)
    subprocess.run([FP,"-f",w],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False,timeout=300)
    info=os.path.join(tmp,"in_out","in_info.txt")
    if not os.path.exists(info): return []
    drug={}; pid=None
    for l in open(info):
        m=re.match(r"Pocket\s+(\d+)",l)
        if m: pid=int(m.group(1))
        if "Druggability Score" in l and pid is not None:
            try: drug[pid]=float(l.split(":")[1])
            except Exception: pass
    out=[]
    for f in glob.glob(os.path.join(tmp,"in_out","pockets","pocket*_atm.pdb")):
        m=re.search(r"pocket(\d+)_atm",f)
        if not m: continue
        i=int(m.group(1))+1
        rs=set()
        for l in open(f,errors="replace"):
            if l.startswith(("ATOM","HETATM")):
                try: rs.add(int(l[22:26]))
                except ValueError: pass
        if rs: out.append(dict(id=i,drug=drug.get(i,0.0),residues=sorted(rs)))
    return sorted(out,key=lambda p:-p["drug"])

SELECTOR=os.environ.get("SELECTOR","fpocket")   # "fpocket" | "consensus"
JACCARD=float(os.environ.get("JACCARD","0.5"))
PASSER=json.load(open("passer_cache.json")) if os.path.exists("passer_cache.json") else {}

def passer_residues(sel,chain=None):
    """PASSer returns a VMD selection string; keep only our chain, return int resnums."""
    out=set()
    for ch,nums in re.findall(r"chain\s+(\S+)\s+and\s+resid\s+([0-9eE.+\-\s]+)",sel):
        if chain and ch!=chain: continue
        for tok in nums.split():
            try:
                v=float(tok)
                if abs(v-round(v))<1e-6 and v>0: out.add(int(round(v)))
            except ValueError: pass
    return out

def passer_pockets(pdb,chain):
    """-> [(rank, prob, set(residues))] ordered by PASSer allostery rank (1 = best)."""
    rec=PASSER.get("%s|%s|ensemble"%(pdb.lower(),chain))
    if not rec: return []
    out=[]
    for k,v in rec.items():
        try: rk=int(k)
        except ValueError: continue
        if not isinstance(v,dict): continue
        sel=v.get("residues") or v.get("resid") or ""
        rs=passer_residues(sel,chain) if isinstance(sel,str) else set()
        if rs:
            try: pr=float(str(v.get("prob","0")).replace("%","").strip())
            except Exception: pr=0.0
            out.append((rk,pr,rs))
    return sorted(out,key=lambda t:t[0])

def select_pockets(pk,pdb,chain,n):
    """fpocket: top-n by druggability. consensus: minrank over (druggability, allostery)
    -- a pocket is only as good as its WORSE rank, so it must be BOTH."""
    if SELECTOR!="consensus": return pk[:n],{}
    pa=passer_pockets(pdb,chain)
    if not pa: return [],{"reason":"no PASSer entry"}
    sel=[];dbg={"n_passer":len(pa),"matched":0}
    for rk_fp,q in enumerate(pk,1):                 # pk already sorted by druggability
        fs=set(q["residues"]); best=None
        for rk_pa,prob,rs in pa:
            j=len(fs&rs)/max(1,len(fs|rs))
            if j>=JACCARD and (best is None or rk_pa<best[0]): best=(rk_pa,prob,j)
        if best is None: continue
        dbg["matched"]+=1
        q=dict(q,rk_fp=rk_fp,rk_pa=best[0],jaccard=round(best[2],3)); sel.append((max(rk_fp,best[0]),rk_fp,best[0],best[2],q))   # minrank
    sel.sort(key=lambda t:t[0])
    dbg["selected"]=len(sel[:n])
    return [t[4] for t in sel[:n]],dbg

def build(X,weight,norm):
    D2=((X[:,None,:]-X[None,:,:])**2).sum(-1); d=np.sqrt(D2); m=(d<CUTOFF)&(d>0)
    if   weight=="binary": W=m.astype(float)
    elif weight=="gauss":  W=np.where(m,np.exp(-D2/(2*SIGMA**2)),0.0)
    elif weight=="harm":   W=np.where(m,1.0/(d+EPS)**2,0.0)
    else:                  W=np.where(m,np.exp(-ALPHA*d),0.0)
    np.fill_diagonal(W,0.0)
    if norm=="adj":  return W
    if norm=="comb": return np.diag(W.sum(1))-W
    dg=W.sum(1); s=1.0/np.sqrt(np.where(dg>0,dg,1.0))
    return np.eye(len(W))-(W*s[:,None])*s[None,:]

# ---- H_new, ported verbatim from notebook cell 39 (build_H_new + V_B..V_M) ----
ALPHA=0.3; LAMBDAS=dict(B=0.08,T=0.16,R=0.08,C=0.04,M=0.04)
TERM_FRAC=0.05; N_LOW_MODES=10

def _zscore(x): return (x-x.mean())/(x.std()+1e-9)
def _contact(X,cut,weight="binary",sigma=6.0,alpha=ALPHA):
    d=np.sqrt(((X[:,None,:]-X[None,:,:])**2).sum(2)); m=(d<cut)&(d>0)
    if weight=="binary": return m.astype(float)
    if weight=="gaussian": return np.exp(-(d**2)/(2*sigma**2))*m
    return np.exp(-alpha*d)*m
def _lap(W,normalised=False):
    L=np.diag(W.sum(1))-W
    if not normalised: return L
    dg=W.sum(1); dis=np.where(dg>0,1.0/np.sqrt(dg),0.0)
    return (L*dis[:,None])*dis[None,:]
def _kirch(X,cut):
    A=_contact(X,cut,"binary"); w,U=np.linalg.eigh(_lap(A))
    nz=w>1e-9; winv=np.where(nz,1.0/np.where(nz,w,1.0),0.0)
    return A,w,U,nz,winv
def V_B(bf): return _zscore(bf.astype(float))
def V_T(n,tf=TERM_FRAC):
    k=max(1,int(n*tf)); m=np.zeros(n); m[:k]=1.0; m[-k:]=1.0; return _zscore(m)
def V_R(X,cut):
    A=_contact(X,cut,"binary"); deg=A.sum(1); tri=np.diag(A@(A@A))
    clust=tri/np.maximum(deg*(deg-1),1.0)
    _A,_w,U,_nz,winv=_kirch(X,cut); msf=np.diag((U*winv)@U.T)
    return _zscore(-(_zscore(deg)+_zscore(clust)-_zscore(msf)))
def V_C(X,cut):
    _A,_w,U,_nz,winv=_kirch(X,cut); Cov=(U*winv)@U.T
    d=np.sqrt(np.clip(np.diag(Cov),1e-12,None)); nD=Cov/np.outer(d,d)
    np.fill_diagonal(nD,0.0); return -_zscore(np.abs(nD).sum(1))
def V_M(X,cut,nm=N_LOW_MODES):
    _A,w,v,_nz,_wi=_kirch(X,cut); i0=max(1,int(np.searchsorted(w,1e-8)))
    return -_zscore((v[:,i0:i0+nm]**2).mean(1))
def build_H_new(X,bf,cut=10.0,alpha=ALPHA,lam=LAMBDAS):
    L=_lap(_contact(X,cut,"exponential",alpha=alpha),normalised=True)
    diag=(lam["B"]*V_B(bf)+lam["T"]*V_T(len(X),TERM_FRAC)+lam["R"]*V_R(X,cut)
          +lam["C"]*V_C(X,cut)+lam["M"]*V_M(X,cut))
    return L+np.diag(diag)

def rz(r):
    r=np.asarray(r,float); m=np.median(r)
    return (r-m)/(1.4826*np.median(np.abs(r-m))+1e-12)

def main():
    if not FP: sys.exit("fpocket binary not found -- refusing to run a pocket-seeded sweep without pockets")
    work=[w for w in json.load(open("operator_worklist.json")) if w["is_distal"]]
    work=[w for i,w in enumerate(work) if i%NSHARD==SHARD]
    os.makedirs(CACHE,exist_ok=True)
    todo=[] if SHARD else sorted({w["pdb"] for w in work if not os.path.exists(os.path.join(CACHE,w["pdb"]+".pdb"))})
    if todo:
        print("prefetch %d"%len(todo),flush=True)
        with ThreadPoolExecutor(16) as ex: list(ex.map(fetch,todo))
    res=json.load(open(OUT)) if os.path.exists(OUT) else {}
    print("fpocket=%s | %d proteins | %d already done"%(FP,len(work),len(res)),flush=True)
    t0=time.time()
    for k,w in enumerate(work,1):
        if w["name"] in res: continue
        try:
            p=fetch(w["pdb"])
            X,idx,ch,BF=ca(p,w["chain"]) if p else (None,None,None,None)
            if X is None or len(X)<30: res[w["name"]]={"error":"no CA"}; continue
            A=[idx[r] for r in w["active"] if r in idx]
            T=set(idx[r] for r in w["truth"] if r in idx)
            if len(A)<1 or not T: res[w["name"]]={"error":"sites"}; continue
            pk_all=run_fpocket(p,ch)
            if not pk_all: res[w["name"]]={"error":"fpocket none"}; continue
            pk,seldbg=select_pockets(pk_all,w["pdb"],ch,N_POCKETS)
            if not pk: res[w["name"]]={"error":"selector empty: %s"%seldbg}; continue
            D2=((X[:,None,:]-X[None,:,:])**2).sum(-1)
            adj=csr_matrix(((D2<CUTOFF**2)&(D2>0)).astype(np.int8))
            hop=dijkstra(adj,directed=False,indices=A,unweighted=True,min_only=True)
            act_pk=max(pk,key=lambda q:len({idx[r] for r in q["residues"] if r in idx}&set(A)))["id"]
            seeds=sorted({idx[r] for q in pk if q["id"]!=act_pk for r in q["residues"]
                          if r in idx and idx[r] not in set(A) and hop[idx[r]]>=MIN_HOP})
            y=np.array([1.0 if s in T else 0.0 for s in seeds])
            # --- pocket bookkeeping: which seeds belong to which pocket, how "drug" each pocket is
            sidx={r:i for i,r in enumerate(seeds)}
            POCK=[]
            for q in pk:
                if q["id"]==act_pk: continue
                mem=[sidx[idx[r]] for r in q["residues"] if r in idx and idx[r] in sidx]
                if not mem: continue
                nd=int(y[mem].sum())
                POCK.append(dict(id=q["id"],n=len(mem),n_drug=nd,drug_frac=round(nd/len(mem),3),
                                 rk_fp=q.get("rk_fp"),rk_pa=q.get("rk_pa"),drug=q["drug"],mem=mem))
            def top_pocket(v):
                """pocket ranking for one score vector: pocket score = mean residue score."""
                sc=[(float(np.mean(v[p["mem"]])),p["id"]) for p in POCK]
                sc.sort(reverse=True)
                return [pid for _,pid in sc[:3]]
            INV={i:r for r,i in idx.items()}
            SEED2P={}
            for p in POCK:
                for k in p["mem"]: SEED2P.setdefault(k,p["id"])
            RANKS={}
            if len(seeds)<8 or not (0<y.sum()<len(y)):
                res[w["name"]]={"error":"seeds %d drug %d"%(len(seeds),int(y.sum()))}; continue
            hp=hop[seeds]; f=np.isfinite(hp); hp=np.where(f,hp,(np.nanmax(hp[f]) if f.any() else 1)+1)
            deg=np.asarray(((D2<CUTOFF**2)&(D2>0)).sum(1),float)[seeds]
            Xd=np.column_stack([np.ones(len(seeds)),hp,deg])
            cells={}; VEC=[]
            OPS=[(wt,nm) for wt in WEIGHTS for nm in NORMS]+[("hnew","full")]
            for wt,nm in OPS:
                if True:
                    H=build_H_new(X,BF) if wt=="hnew" else build(X,wt,nm)
                    ev,V=np.linalg.eigh(H)
                    Vs=V[seeds,:]; Va=V[A,:]; sq=V*V
                    pa=(sq@sq.T)[np.ix_(seeds,A)].sum(1)
                    gaps=np.diff(np.sort(ev)); gap=max(float(gaps[gaps>1e-9].min()) if (gaps>1e-9).any() else 1e-4,1e-4)
                    ts=np.linspace(0.0,C_T/gap,NT)
                    pk_w=np.zeros(len(seeds))
                    for t in ts:
                        amp=(Va*np.exp(-1j*ev*t))@Vs.T
                        pk_w=np.maximum(pk_w,(np.abs(amp)**2).sum(0))
                    def put(tag,v):
                        try:
                            o=np.argsort(-v)
                            cells["%s|%s|%s"%(wt,nm,tag)]=[float(roc_auc_score(y,v)),
                                                           float(y[o[:5]].sum())/5.0]
                            VEC.append(np.asarray(v,float))
                            od=np.argsort(-np.asarray(v,float)); rr=np.empty(len(od),int); rr[od]=np.arange(1,len(od)+1)
                            RANKS["%s|%s|%s"%(wt,nm,tag)]=rr.tolist()
                        except Exception: pass
                    put("p_avg",pa); put("p_peak",pk_w)
                    put("R",pk_w/np.clip(pa,1e-300,None))
                    lg=np.log(np.clip(pa,1e-300,None))
                    b1,*_=np.linalg.lstsq(Xd,lg,rcond=None); put("residLOG",rz(lg-Xd@b1))
                    b2,*_=np.linalg.lstsq(Xd,pa,rcond=None);  put("residRAW",rz(pa-Xd@b2))
                    for em,eta in GREEN:
                        E={"zero":0.0,"lmax":float(ev.max())}[em]
                        Gm=(Va/((E+1j*eta)-ev))@Vs.T
                        put("green_%s_%g"%(em,eta),(np.abs(Gm)**2).sum(0))
            # --- correlation-preserving null: permute y against the SAME score vectors.
            # AUC via rank-sum so 200 permutations x len(VEC) cells is cheap and exact.
            n=len(y); kpos=int(y.sum()); B=200
            S=np.vstack(VEC)                                   # (cells, n_seeds)
            RK=np.apply_along_axis(lambda r: st.rankdata(r), 1, S)
            TOP5=np.argsort(-S,axis=1)[:,:5]
            denom=kpos*(n-kpos); off=kpos*(kpos+1)/2.0
            nma=np.empty(B); nmp=np.empty(B)
            rng=np.random.default_rng(abs(hash(w["name"]))%(2**32))
            for bb in range(B):
                pos=rng.permutation(n)[:kpos]
                nma[bb]=((RK[:,pos].sum(1)-off)/denom).max()
                nmp[bb]=(np.isin(TOP5,pos).sum(1)/5.0).max()
            obs_a=max(c[0] for c in cells.values()); obs_p=max(c[1] for c in cells.values())
            res[w["name"]]=dict(cells=cells,pockets=[{k:v for k,v in p.items() if k!="mem"} for p in POCK],ranks=RANKS,seed_pocket=[SEED2P.get(k) for k in range(len(seeds))],seed_resnum=[int(INV[k]) for k in seeds],y=y.astype(int).tolist(),n_seeds=len(seeds),n_drug=int(y.sum()),
                                base=float(y.mean()),n_pockets=len(pk),n_pockets_all=len(pk_all),selector=SELECTOR,seldbg=seldbg,
                                cluster=w["cluster"],source=w["source"],truth_type=w["truth_type"],
                                obs_max_auc=float(obs_a),obs_max_p5=float(obs_p),
                                null_max_auc=float(nma.mean()),null_max_p5=float(nmp.mean()),
                                p_auc=float((nma>=obs_a).mean()),p_p5=float((nmp>=obs_p).mean()))
        except Exception as e:
            res[w["name"]]={"error":"%s: %s"%(type(e).__name__,e)}
        if k%CKPT==0:
            json.dump(res,open(OUT,"w"))
            done=sum(1 for v in res.values() if "cells" in v)
            print("  CKPT %d/%d scored=%d (%.0fs)"%(k,len(work),done,time.time()-t0),flush=True)
    json.dump(res,open(OUT,"w"))
    ok=[v for v in res.values() if "cells" in v]
    print("DONE %d scored, %d errors, %.0fs"%(len(ok),len(res)-len(ok),time.time()-t0),flush=True)

if __name__=="__main__": main()
