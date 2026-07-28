"""REFERENCE PROTOTYPE for TASK-0167.001 -- external panel review, 2026-07-28.
(Filed as TASK-0170.001/TASK-0170 by the review itself, which numbered from
a stale count; the next actually-free ID at filing time was TASK-0167, not
TASK-0170. Renumbered 2026-07-28, Architect/Planner -- no content changed,
see each renamed task file's own provenance note.)

This script EXISTS and RUNS (numpy 2.4.4 / scipy 1.17.1 / networkx 3.6.1).
It is the executed evidence behind TASK-0167's design table, not a sketch.
Run: python3 plant_prototype_REFERENCE.py

SCOPE / WHAT IT DOES NOT DO -- stated so it is not over-trusted:
  * synthetic two-lobe fold, NOT a real apo structure
  * bare combinatorial Laplacian, NOT H_new
  * plain converged CTQW, NOT the verdict pipeline (no floor CI, no null,
    no Bonferroni)
It establishes (a) confound-orthogonality holds EXACTLY under weight-only
edits, and (b) a detection threshold exists and is measurable. It does NOT
establish the LOD value -- that is TASK-0170.002's job on real targets.
"""
import numpy as np, networkx as nx
from scipy.stats import rankdata

def two_lobe(N=260, seed=3):
    """Elongated two-domain fold: real proteins of this size have hop diameter 8-14."""
    r=np.random.default_rng(seed); pts=[]
    centres=[np.array([-16.,0,0]), np.array([16.,0,0])]
    while len(pts)<N:
        cc=centres[len(pts)%2]
        p=cc+r.normal(scale=8.5,size=3)
        if not pts or np.min(np.linalg.norm(np.array(pts)-p,axis=1))>4.2: pts.append(p)
    return np.array(pts)

def auc(s,l):
    p,n=s[l],s[~l]; r=rankdata(np.concatenate([p,n])); n1,n0=len(p),len(n)
    return (r[:n1].sum()-n1*(n1+1)/2)/(n1*n0)

coords=two_lobe(260)
D=np.linalg.norm(coords[:,None]-coords[None],axis=2); np.fill_diagonal(D,np.inf)
W0=np.where(D<9.0, 1.0/D, 0.0)
G=nx.from_numpy_array((W0>0).astype(float))
keep=sorted(max(nx.connected_components(G),key=len))
coords,W0=coords[keep],W0[np.ix_(keep,keep)]
N=len(W0); G=nx.from_numpy_array((W0>0).astype(float))
hop=dict(nx.all_pairs_shortest_path_length(G))
print("N=%d  <deg>=%.1f  hop diameter=%d"%(N,(W0>0).sum(1).mean(),
      max(max(v.values()) for v in hop.values())))

lobeL=np.where(coords[:,0]<0)[0]; lobeR=np.where(coords[:,0]>=0)[0]
sc=lobeL[np.argmin(coords[lobeL,0])]
seed_idx=np.array(sorted(lobeL, key=lambda i: np.linalg.norm(coords[i]-coords[sc])))[:14]
pc=lobeR[np.argmax(coords[lobeR,0])]
pocket=np.array(sorted(lobeR, key=lambda i: np.linalg.norm(coords[i]-coords[pc])))[:16]
lab=np.zeros(N,bool); lab[pocket]=True
hfs=np.array([min(hop[s][j] for s in seed_idx) for j in range(N)])
print("planted pocket mean hop from seed = %.1f  (max %d)  -- genuinely distal"%(hfs[pocket].mean(),hfs.max()))

def dcc(W):
    L=np.diag(W.sum(1))-W; w,v=np.linalg.eigh(L)
    inv=(v[:,1:]/w[1:])@v[:,1:].T; d=np.sqrt(np.diag(inv)); return inv/np.outer(d,d)

def plant(W0,seed_idx,pocket,strength,n_paths=10,rng=None):
    rng=rng or np.random.default_rng(0); W=W0.copy()
    Gd=nx.from_numpy_array(np.where(W0>0,1.0/np.maximum(W0,1e-9),0.0))
    for _ in range(n_paths):
        s=int(seed_idx[rng.integers(len(seed_idx))]); t=int(pocket[rng.integers(len(pocket))])
        try: p=nx.shortest_path(Gd,s,t,weight='weight')
        except Exception: continue
        for a,b in zip(p[:-1],p[1:]):
            W[a,b]*= (1+strength); W[b,a]=W[a,b]
    return W

def ctqw_conv(W, src):
    L=np.diag(W.sum(1))-W
    w,v=np.linalg.eigh(L); V2=v**2
    p=np.zeros(len(L))
    for i in src: p+=V2@V2[i]
    return p/p.sum()

euc=np.linalg.norm(coords-coords[seed_idx].mean(0),axis=1); deg=(W0>0).sum(1)
floor=max(auc(-hfs,lab),auc(-euc,lab),auc(deg,lab))
print("\nproximity floor against the planted (distal) label = %.3f\n"%floor)
print("%-9s %-12s %-11s %-11s %-11s %-9s"%("strength","DCC ratio","CTQW AUC","hop AUC","euclid AUC","detect?"))
for s in (0.0,0.5,1.5,4.0,10.0,30.0):
    W=plant(W0,seed_idx,pocket,s); d=dcc(W)
    cp=np.abs(d[np.ix_(seed_idx,pocket)]).mean()
    bg=np.abs(d[np.ix_(seed_idx,np.setdiff1d(np.arange(N),np.r_[seed_idx,pocket]))]).mean()
    a=auc(ctqw_conv(W,seed_idx),lab)
    hf=np.array([min(hop[x][j] for x in seed_idx) for j in range(N)])  # recompute: unchanged
    print("%-9.1f %-12.2f %-11.3f %-11.3f %-11.3f %-9s"
          %(s,cp/bg,a,auc(-hf,lab),auc(-euc,lab),"YES" if a>floor else "no"))
