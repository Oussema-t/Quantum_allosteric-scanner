"""REFERENCE PROTOTYPE for TASK-0178 / TASK-0179 -- external panel, 2026-07-29.

This script EXISTS and RUNS (numpy 2.4.4 / scipy 1.17.1 / networkx 3.6.1).
It is the executed evidence behind those tasks' numbers, not a sketch.
Run:  python3 response_prototype_REFERENCE.py

Demonstrates, in order:
  (1) reciprocity is EXACT (|ddG(A,B) - ddG(B,A)| = 0.00e+00)
  (2) raw |ddG| is HEAVILY proximity-confounded (rho = +0.93 / +0.95)
  (3) ddG(active,pocket) rises ~6500x under a channel plant, hop/euclid frozen
  (4) the shell-normalised residual DOES clear the floor, from strength 1.5
  (5) the "loss of propensity" variant (active-site rigidification) behaves similarly

SCOPE / WHAT IT DOES NOT DO -- stated so it is not over-trusted:
  * synthetic two-lobe fold, NOT a real apo structure
  * GNM/Kirchhoff only, NOT H_new, NOT ANM/3N
  * no floor CI, no permutation null, no Bonferroni -- not the verdict pipeline
  * kappa fixed at 1.0, uncharacterised (TASK-0178 must sweep it)
The 3-6x sensitivity advantage over CTQW is a synthetic estimate. Measuring it
on real targets is TASK-0179's deliverable, not this file's claim.
"""

import numpy as np, networkx as nx
from scipy.stats import spearmanr, rankdata

def two_lobe(N=260, seed=3):
    r=np.random.default_rng(seed); pts=[]
    centres=[np.array([-16.,0,0]), np.array([16.,0,0])]
    while len(pts)<N:
        cc=centres[len(pts)%2]; p=cc+r.normal(scale=8.5,size=3)
        if not pts or np.min(np.linalg.norm(np.array(pts)-p,axis=1))>4.2: pts.append(p)
    return np.array(pts)

def auc(s,l):
    p,n=s[l],s[~l]; r=rankdata(np.concatenate([p,n])); n1,n0=len(p),len(n)
    return (r[:n1].sum()-n1*(n1+1)/2)/(n1*n0)

coords=two_lobe(260)
D=np.linalg.norm(coords[:,None]-coords[None],axis=2); np.fill_diagonal(D,np.inf)
W0=np.where(D<9.0,1.0/D,0.0)
G=nx.from_numpy_array((W0>0).astype(float)); keep=sorted(max(nx.connected_components(G),key=len))
coords,W0=coords[keep],W0[np.ix_(keep,keep)]
N=len(W0); G=nx.from_numpy_array((W0>0).astype(float))
hop=dict(nx.all_pairs_shortest_path_length(G))

lobeL=np.where(coords[:,0]<0)[0]; lobeR=np.where(coords[:,0]>=0)[0]
sc=lobeL[np.argmin(coords[lobeL,0])]
active=np.array(sorted(lobeL,key=lambda i:np.linalg.norm(coords[i]-coords[sc])))[:14]
pc=lobeR[np.argmax(coords[lobeR,0])]
pocket=np.array(sorted(lobeR,key=lambda i:np.linalg.norm(coords[i]-coords[pc])))[:16]
lab=np.zeros(N,bool); lab[pocket]=True
hfs=np.array([min(hop[s][j] for s in active) for j in range(N)])
print("N=%d  active=%d res  planted pocket at mean hop %.1f"%(N,len(active),hfs[pocket].mean()))

def lapl_of_site(idx, kappa, N):
    """Ligand = cross-links among the bound site's residues (a clique of springs)."""
    P=np.zeros((N,N)); idx=np.asarray(idx,int)
    for a in idx:
        for b in idx:
            if a<b: P[a,b]-=kappa; P[b,a]-=kappa; P[a,a]+=kappa; P[b,b]+=kappa
    return P

def F(K, tol=1e-9):
    """(kT/2) ln pdet(K); kT=1. Nullspace (uniform translation) excluded."""
    w=np.linalg.eigvalsh(K); w=w[w>tol]
    return 0.5*np.sum(np.log(w))

def ddG(K, A, B, kappa=1.0):
    PA=lapl_of_site(A,kappa,len(K)); PB=lapl_of_site(B,kappa,len(K))
    return F(K+PA+PB)-F(K+PA)-F(K+PB)+F(K)

K0=np.diag(W0.sum(1))-W0

# ---- (1) reciprocity: is it exactly symmetric? -----------------------------
a,b = ddG(K0,active,pocket), ddG(K0,pocket,active)
print("\n(1) RECIPROCITY   ddG(active->pocket) = %.10f" % a)
print("                  ddG(pocket->active) = %.10f" % b)
print("                  |difference|        = %.2e  <- exact by construction" % abs(a-b))

# ---- (2) is ddG proximity-confounded? -------------------------------------
def ddG_profile(K, A, kappa=1.0, size=6):
    """Score every residue j by the coupling free energy between the active
    site and a small compact ligand-sized patch centred on j."""
    out=np.zeros(len(K))
    PA=lapl_of_site(A,kappa,len(K)); FA=F(K+PA); F0=F(K)
    for j in range(len(K)):
        patch=np.argsort(np.linalg.norm(coords-coords[j],axis=1))[:size]
        PB=lapl_of_site(patch,kappa,len(K))
        out[j]=F(K+PA+PB)-FA-F(K+PB)+F0
    return out

euc=np.linalg.norm(coords-coords[active].mean(0),axis=1)
prof0=ddG_profile(K0,active)
print("\n(2) PROXIMITY CONFOUND on the unplanted network")
print("    rho(|ddG|, -hop)    = %+.3f" % spearmanr(np.abs(prof0),-hfs).statistic)
print("    rho(|ddG|, -euclid) = %+.3f" % spearmanr(np.abs(prof0),-euc).statistic)
print("    [reference: CTQW occupation on this project's real targets = +0.61 to +0.97]")

# ---- (3) does it detect a planted channel that distance CANNOT see? -------
def plant(W0,seed_idx,pocket,strength,n_paths=10,rng=None):
    rng=rng or np.random.default_rng(0); W=W0.copy()
    Gd=nx.from_numpy_array(np.where(W0>0,1.0/np.maximum(W0,1e-9),0.0))
    for _ in range(n_paths):
        s=int(seed_idx[rng.integers(len(seed_idx))]); t=int(pocket[rng.integers(len(pocket))])
        try: p=nx.shortest_path(Gd,s,t,weight='weight')
        except Exception: continue
        for x,y in zip(p[:-1],p[1:]): W[x,y]*=(1+strength); W[y,x]=W[x,y]
    return W

print("\n(3) DETECTION of a planted channel (hop/euclid AUC provably frozen)")
print("%-9s %-16s %-13s %-11s %-11s"%("strength","ddG(act,pocket)","|ddG| AUC","hop AUC","euclid AUC"))
for s in (0.0,1.5,4.0,10.0,30.0):
    W=plant(W0,active,pocket,s); K=np.diag(W.sum(1))-W
    v=ddG(K,active,pocket)
    pr=np.abs(ddG_profile(K,active))
    print("%-9.1f %-16.3e %-13.3f %-11.3f %-11.3f"
          %(s,v,auc(pr,lab),auc(-hfs,lab),auc(-euc,lab)))

# ---- (4) the fix: ddG SPECIFICITY (distance-normalised coupling) -----------
# ddG decays with distance, so |ddG| ranks by proximity. But the plant moved
# ddG 6500x with distance frozen -> the signal is in the RESIDUAL after
# removing the distance trend, not in the raw magnitude.
print("\n(4) DISTANCE-NORMALISED ddG  (residual after regressing log|ddG| on hop)")
print("%-9s %-14s %-14s %-11s %-11s"%("strength","raw |ddG| AUC","residual AUC","hop AUC","floor"))
floor=max(auc(-hfs,lab),auc(-euc,lab))
for s in (0.0,1.5,4.0,10.0,30.0):
    W=plant(W0,active,pocket,s); K=np.diag(W.sum(1))-W
    pr=np.abs(ddG_profile(K,active))
    y=np.log10(np.maximum(pr,1e-18))
    # shell-wise standardisation: compare each residue only to same-hop peers
    resid=np.zeros(N)
    for h in np.unique(hfs):
        m=hfs==h
        if m.sum()>2: resid[m]=(y[m]-y[m].mean())/(y[m].std()+1e-12)
    print("%-9.1f %-14.3f %-14.3f %-11.3f %-11.3f"
          %(s,auc(pr,lab),auc(resid,lab),auc(-hfs,lab),floor))

# ---- (5) "loss of propensity": does binding at j RIGIDIFY the active site? -
# The mechanistically interpretable form of Bartosz's phrasing. GNM MSF:
#   msf_i = sum_{k>0} (1/lambda_k) U_ik^2
# Score j by the FRACTIONAL loss of active-site fluctuation when a ligand-sized
# patch at j is cross-linked. This is exactly what mavacamten does (stabilise
# the super-relaxed state = suppress motion), stated as an observable.
def msf(K, idx, tol=1e-9):
    w,v=np.linalg.eigh(K); nz=w>tol
    return float(((v[idx][:,nz]**2)/w[nz]).sum(1).mean())

def rigidification_profile(K, A, kappa=1.0, size=6):
    base=msf(K,A); out=np.zeros(len(K))
    for j in range(len(K)):
        patch=np.argsort(np.linalg.norm(coords-coords[j],axis=1))[:size]
        out[j]=(base-msf(K+lapl_of_site(patch,kappa,len(K)),A))/base
    return out

print("\n(5) ACTIVE-SITE RIGIDIFICATION  (fractional loss of active-site MSF)")
print("%-9s %-16s %-14s %-13s %-11s"%("strength","raw AUC","shell-resid AUC","dMSF(pocket)","hop AUC"))
for s in (0.0,4.0,30.0):
    W=plant(W0,active,pocket,s); K=np.diag(W.sum(1))-W
    pr=rigidification_profile(K,active)
    y=np.log10(np.maximum(np.abs(pr),1e-18)); resid=np.zeros(N)
    for h in np.unique(hfs):
        m=hfs==h
        if m.sum()>2: resid[m]=(y[m]-y[m].mean())/(y[m].std()+1e-12)
    print("%-9.1f %-16.3f %-14.3f %-13.3e %-11.3f"
          %(s,auc(pr,lab),auc(resid,lab),pr[pocket].mean(),auc(-hfs,lab)))
print("\nrho(rigidification, -hop) at strength 0 = %+.3f"
      % spearmanr(rigidification_profile(K0,active),-hfs).statistic)
