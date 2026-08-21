import numpy as np, warnings
warnings.filterwarnings("ignore")
from scipy.linalg import eigh, expm
from scipy.stats import spearmanr, rankdata
from scipy.sparse.csgraph import shortest_path
src=open('obs_family_confound2.py').read()

def build(seed_rng):
    rng=np.random.default_rng(seed_rng)
    dirs=[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]; L=7; N=L**3
    while True:
        start=tuple(rng.integers(0,L,3)); path=[start]; used={start}; ok=True
        while len(path)<N:
            c=path[-1]; cand=[]
            for d in dirs:
                n=(c[0]+d[0],c[1]+d[1],c[2]+d[2])
                if all(0<=x<L for x in n) and n not in used:
                    dg=sum(1 for d2 in dirs if all(0<=n[k]+d2[k]<L for k in range(3))
                           and (n[0]+d2[0],n[1]+d2[1],n[2]+d2[2]) not in used)
                    cand.append((dg+rng.random()*0.1,n))
            if not cand: ok=False; break
            cand.sort(key=lambda t:t[0]); path.append(cand[0][1]); used.add(cand[0][1])
        if ok: break
    co=np.array(path,float)*3.8+rng.normal(0,0.9,(N,3))
    D=np.linalg.norm(co[:,None]-co[None],axis=-1)
    for cut in np.arange(4.0,9.0,0.05):
        A=((D<cut)&(D>0)).astype(float)
        for i in range(N-1): A[i,i+1]=A[i+1,i]=1.0
        if A.sum(1).mean()>=8.0: break
    return co,D,A,rng

def pspear(x,y,z):
    rx,ry,rz=rankdata(x),rankdata(y),rankdata(z)
    r=lambda a:a-np.polyval(np.polyfit(rz,a,1),rz)
    return np.corrcoef(r(rx),r(ry))[0,1]

acc={}
for rep in range(6):
    co,D,A,rng=build(100+rep); N=len(co)
    deg=A.sum(1); Lap=np.diag(deg)-A
    cen=co.mean(0); r=np.linalg.norm(co-cen,axis=1); burial=-r
    w,V=eigh(Lap); nz=w>1e-8; Cov=(V[:,nz]/w[nz])@V[:,nz].T
    for s_i in range(4):
        seed=int(rng.choice(np.flatnonzero((r>np.percentile(r,40))&(r<np.percentile(r,80)))))
        ed=D[seed]; sc={}
        wa,Va=eigh(A); es=Va[seed]
        ts=np.linspace(.1,25,60); p=np.zeros(N)
        for t in ts: p+=np.abs(Va@(np.exp(-1j*wa*t)*es))**2
        sc["CTQW_adj_T25"]=p/len(ts)
        sc["heat_T5"]=expm(-Lap*5.)[seed]
        Lpi=np.linalg.pinv(Lap); vol=deg.sum()
        sc["MRW_commute"]=-np.array([vol*(Lpi[seed,seed]+Lpi[j,j]-2*Lpi[seed,j]) for j in range(N)])
        sc["GNM_corr_seed"]=Cov[seed]/np.sqrt(np.diag(Cov)*Cov[seed,seed])
        idx=np.flatnonzero(nz)[:10]; Cl=(V[:,idx]/w[idx])@V[:,idx].T
        sc["GNM_corr_low10"]=Cl[seed]/np.sqrt(np.abs(np.diag(Cl)*Cl[seed,seed]))
        base=Cov[seed,seed]; bl=np.sum(np.log(w[nz])); dS=np.zeros(N); dM=np.zeros(N)
        for j in range(N):
            sh=np.append(np.flatnonzero(A[j]),j); Ap=A.copy(); ix=np.ix_(sh,sh)
            Ap[ix]=Ap[ix]*3.0; np.fill_diagonal(Ap,0.)
            L2=np.diag(Ap.sum(1))-Ap; w2,V2=eigh(L2); n2=w2>1e-8
            dS[j]=-0.5*(np.sum(np.log(w2[n2]))-bl)
            C2=(V2[:,n2]/w2[n2])@V2[:,n2].T; dM[j]=base-C2[seed,seed]
        sc["dS_vib_global"]=dS; sc["dMSF_at_seed"]=dM
        for k,v in sc.items():
            acc.setdefault(k,[]).append(abs(pspear(v,ed,burial)))
print(f"{'observable':18s} {'|partial rho(dist|burial)|  mean +- sd  (n=24)':>46s}")
print("-"*66)
for k,v in acc.items():
    v=np.array(v); print(f"{k:18s} {v.mean():>28.3f} +- {v.std():.3f}   [{v.min():.2f},{v.max():.2f}]")
