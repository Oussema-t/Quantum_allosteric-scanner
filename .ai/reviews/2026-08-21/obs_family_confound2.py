"""
v2 fixes: (i) protein-like mean degree ~8 (v1 had <k>=38, graph diameter 3 -- not a protein),
(ii) off-centre seed so that seed-proximity is not collinear with burial,
(iii) partial Spearman controlling for burial, so "confound" means proximity, not depth.
"""
import numpy as np
from scipy.linalg import eigh, expm
from scipy.stats import spearmanr, rankdata
from scipy.sparse.csgraph import shortest_path

rng = np.random.default_rng(11)

def random_hamiltonian_path(L=7, tries=4000):
    dirs = [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
    N = L**3
    for _ in range(tries):
        start = tuple(rng.integers(0, L, 3)); path=[start]; used={start}; ok=True
        while len(path) < N:
            c = path[-1]; cand=[]
            for d in dirs:
                n=(c[0]+d[0],c[1]+d[1],c[2]+d[2])
                if all(0<=x<L for x in n) and n not in used:
                    deg=sum(1 for d2 in dirs
                            if all(0<=n[k]+d2[k]<L for k in range(3))
                            and (n[0]+d2[0],n[1]+d2[1],n[2]+d2[2]) not in used)
                    cand.append((deg+rng.random()*0.1, n))
            if not cand: ok=False; break
            cand.sort(key=lambda t:t[0]); path.append(cand[0][1]); used.add(cand[0][1])
        if ok: return np.array(path,float)
    raise RuntimeError

coords = random_hamiltonian_path()*3.8
coords += rng.normal(0, 0.9, coords.shape)          # break lattice degeneracy
N = len(coords)
D = np.linalg.norm(coords[:,None,:]-coords[None,:,:],axis=-1)

# tune cutoff to <k> ~ 8 (typical CA 8.5A protein graph)
for cut in np.arange(4.0, 9.0, 0.05):
    A=((D<cut)&(D>0)).astype(float)
    for i in range(N-1): A[i,i+1]=A[i+1,i]=1.0
    if A.sum(1).mean() >= 8.0: break
deg=A.sum(1); Lap=np.diag(deg)-A
gdist=shortest_path(A, unweighted=True)

centroid=coords.mean(0)
burial = -np.linalg.norm(coords-centroid,axis=1)     # higher = more buried
# seed: partially buried, off-centre -> decorrelates proximity from depth
r=np.linalg.norm(coords-centroid,axis=1)
seed=int(np.argsort(np.abs(r-np.percentile(r,65)))[0])
gd=gdist[seed]; ed=D[seed]
print(f"N={N} cutoff={cut:.2f} <k>={deg.mean():.2f} diam={int(gdist.max())} seed={seed} "
      f"seed_r={r[seed]:.1f} (max_r={r.max():.1f})")
print(f"collinearity check  rho(euclid_d_to_seed, burial) = {spearmanr(ed,burial).statistic:+.3f}")

scores={}
for name,H in [("CTQW_adj",A),("CTQW_lap",Lap)]:
    w,V=eigh(H); e_s=V[seed]
    for T in (5.,25.,100.):
        ts=np.linspace(0.1,T,80); p=np.zeros(N)
        for t in ts:
            psi=V@(np.exp(-1j*w*t)*e_s); p+=np.abs(psi)**2
        scores[f"{name}_T{int(T)}"]=p/len(ts)
for T in (1.,5.,25.):
    scores[f"heat_T{int(T)}"]=expm(-Lap*T)[seed]

Lpi=np.linalg.pinv(Lap); vol=deg.sum()
scores["MRW_commute_neg"]=-np.array([vol*(Lpi[seed,seed]+Lpi[j,j]-2*Lpi[seed,j]) for j in range(N)])

w,V=eigh(Lap); nz=w>1e-8
Cov=(V[:,nz]/w[nz])@V[:,nz].T
scores["GNM_corr_seed"]=Cov[seed]/np.sqrt(np.diag(Cov)*Cov[seed,seed])
# low-mode restriction (their dcc_low / prs_low analogue): 10 softest modes
idx=np.flatnonzero(nz)[:10]
Cl=(V[:,idx]/w[idx])@V[:,idx].T
scores["GNM_corr_seed_low10"]=Cl[seed]/np.sqrt(np.abs(np.diag(Cl)*Cl[seed,seed]))

base_logdet=np.sum(np.log(w[nz])); base_msf=Cov[seed,seed]; STIFF=3.0
dS=np.zeros(N); dM=np.zeros(N)
for j in range(N):
    shell=np.append(np.flatnonzero(A[j]),j)
    Ap=A.copy(); s=np.ix_(shell,shell); Ap[s]=Ap[s]*STIFF; np.fill_diagonal(Ap,0.)
    L2=np.diag(Ap.sum(1))-Ap; w2,V2=eigh(L2); nz2=w2>1e-8
    dS[j]=-0.5*(np.sum(np.log(w2[nz2]))-base_logdet)
    C2=(V2[:,nz2]/w2[nz2])@V2[:,nz2].T
    dM[j]=base_msf-C2[seed,seed]
scores["dS_vib_global"]=dS          # seed-blind, Cooper-Dryden flavour
scores["dMSF_at_seed"]=dM           # seed-referencing entropic coupling

def pspear(x,y,z):
    """partial Spearman of x,y controlling z"""
    rx,ry,rz=rankdata(x),rankdata(y),rankdata(z)
    res=lambda a: a-np.polyval(np.polyfit(rz,a,1),rz)
    return np.corrcoef(res(rx),res(ry))[0,1]

print(f"\n{'observable':22s} {'rho(gd)':>8s} {'rho(ed)':>8s} {'rho(burial)':>12s} {'partial ed|burial':>18s}")
print("-"*74)
for k,v in scores.items():
    print(f"{k:22s} {spearmanr(v,gd).statistic:8.3f} {spearmanr(v,ed).statistic:8.3f} "
          f"{spearmanr(v,burial).statistic:12.3f} {pspear(v,ed,burial):18.3f}")
