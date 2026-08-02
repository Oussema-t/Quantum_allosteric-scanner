"""Bartosz's reframing: cryptic-pocket prediction is a CONFORMATIONAL SEARCH
problem, not a residue-scoring problem. A cryptic pocket is by definition
ABSENT in apo -- so every static apo scorer in the register is trying to
detect something that is not there.

Question this script answers: under ENM-mode-restricted sampling (legal --
no MD trajectories), how RARE is a pocket-open conformation? The rarity p
decides whether quantum search/sampling has anything to offer:
  classical rejection sampling ~ O(1/p)
  amplitude amplification      ~ O(1/sqrt(p))
"""
import numpy as np, networkx as nx
from scipy.spatial import ConvexHull

def two_lobe_with_cleft(N=240, seed=5):
    """Two lobes joined by a hinge, with a cleft between them that can open."""
    r=np.random.default_rng(seed); pts=[]
    for cc in (np.array([-13.,0,0]), np.array([13.,0,0])):
        n=0
        while n < N//2:
            p=cc+r.normal(scale=7.5,size=3)
            if abs(p[0]-cc[0])<1.5 and abs(p[1])<6: continue   # carve the cleft
            if not pts or np.min(np.linalg.norm(np.array(pts)-p,axis=1))>4.0:
                pts.append(p); n+=1
    return np.array(pts)

coords0=two_lobe_with_cleft()
N=len(coords0)
D=np.linalg.norm(coords0[:,None]-coords0[None],axis=2); np.fill_diagonal(D,np.inf)
A=((D<10.0)).astype(float)
G=nx.from_numpy_array(A); keep=sorted(max(nx.connected_components(G),key=len))
coords0=coords0[keep]; N=len(coords0)
print("N=%d residues"%N)

# --- ANM (3N) Hessian, standard Tirion/Bahar form -------------------------
def anm_hessian(coords, cutoff=10.0, gamma=1.0):
    n=len(coords); H=np.zeros((3*n,3*n))
    for i in range(n):
        for j in range(i+1,n):
            d=coords[j]-coords[i]; r=np.linalg.norm(d)
            if r>cutoff: continue
            k=gamma/r**2; blk=k*np.outer(d,d)
            H[3*i:3*i+3,3*j:3*j+3]-=blk; H[3*j:3*j+3,3*i:3*i+3]-=blk
            H[3*i:3*i+3,3*i:3*i+3]+=blk; H[3*j:3*j+3,3*j:3*j+3]+=blk
    return H

H=anm_hessian(coords0)
w,v=np.linalg.eigh(H)
nz=w>1e-8
print("ANM: %d zero modes (expect 6), %d nonzero"%((~nz).sum(), nz.sum()))
modes=v[:,nz]; freqs=w[nz]

# --- the "cryptic pocket": cleft between the lobes -----------------------
cleft=np.where(np.abs(coords0[:,0])<7.0)[0]
def cleft_volume(c):
    """Proxy for pocket openness: convex-hull volume of the cleft-lining
    residues minus the volume they actually occupy."""
    try: return ConvexHull(c[cleft]).volume
    except Exception: return 0.0
V0=cleft_volume(coords0)
print("apo cleft hull volume = %.0f A^3"%V0)

# --- Boltzmann sampling in ENM mode space (NO MD) -------------------------
def sample(n_modes, n_samp, kT=1.0, rng=None):
    """Equipartition: amplitude_k ~ N(0, sqrt(kT/lambda_k)). This is the exact
    Gaussian equilibrium ensemble of the ENM -- generated in closed form, no
    trajectory, no integrator. Legal under the challenge's no-MD constraint."""
    rng=rng or np.random.default_rng(0)
    idx=np.argsort(freqs)[:n_modes]          # the SOFTEST modes
    lam=freqs[idx]; U=modes[:,idx]
    a=rng.normal(size=(n_samp,n_modes))*np.sqrt(kT/lam)
    return (U@a.T).T.reshape(n_samp,-1,3)

print("\nHow RARE is a pocket-open conformation in the ENM equilibrium ensemble?")
print("(open = cleft hull volume exceeds apo by the stated margin)\n")
print("%-9s %-9s %-12s %-12s %-12s"%("n_modes","kT","p(+10%)","p(+25%)","p(+50%)"))
rng=np.random.default_rng(1)
for n_modes in (5,10,20,40):
    for kT in (20.0,):
        d=sample(n_modes,4000,kT,rng)
        V=np.array([cleft_volume(coords0+dd) for dd in d])
        p10=(V>1.10*V0).mean(); p25=(V>1.25*V0).mean(); p50=(V>1.50*V0).mean()
        print("%-9d %-9.0f %-12.4f %-12.4f %-12.4f"%(n_modes,kT,p10,p25,p50))

# --- the search-space / speedup argument ---------------------------------
print("\nDiscrete search space if each mode amplitude is binned:")
print("%-9s %-14s %-16s %-16s"%("n_modes","levels/mode","space size","log10(size)"))
for k in (10,20,40):
    for m in (8,16):
        print("%-9d %-14d %-16.3e %-16.1f"%(k,m,float(m)**k,k*np.log10(m)))

# --- the REALISTIC constraint: not "a cleft opens" but "THE pocket forms
#     with druggable properties" -- a CONJUNCTION, which is where p collapses
print("\n\nRealistic constraint set (all must hold simultaneously):")
print("  C1 volume in a druggable band (not too small, not a canyon)")
print("  C2 buried  (enclosed, not a surface dimple)")
print("  C3 the SPECIFIC site, not any cleft")
print("  C4 conformation energetically accessible (within kT budget)\n")

def energy(a, lam):  return 0.5*np.sum(lam*a**2)

def eval_constraints(n_modes, n_samp, kT, rng, e_budget):
    idx=np.argsort(freqs)[:n_modes]; lam=freqs[idx]; U=modes[:,idx]
    a=rng.normal(size=(n_samp,n_modes))*np.sqrt(kT/lam)
    disp=(U@a.T).T.reshape(n_samp,-1,3)
    hits=np.zeros((n_samp,4),bool)
    for s in range(n_samp):
        c=coords0+disp[s]
        V=cleft_volume(c)
        hits[s,0]= 1.15*V0 < V < 1.45*V0                      # C1 band
        # C2 buriedness: cleft residues keep enough neighbours
        d=np.linalg.norm(c[cleft][:,None]-c[None],axis=2)
        hits[s,1]= ((d<10.0).sum(1).mean() > 0.85*((np.linalg.norm(
            coords0[cleft][:,None]-coords0[None],axis=2)<10.0).sum(1).mean()))
        # C3 specificity: opening localised to the cleft, not global expansion
        gl=np.linalg.norm(c-c.mean(0),axis=1).mean()/np.linalg.norm(
            coords0-coords0.mean(0),axis=1).mean()
        hits[s,2]= gl < 1.05
        hits[s,3]= energy(a[s],lam) < e_budget
    return hits

rng=np.random.default_rng(7)
for n_modes in (10,20,40):
    h=eval_constraints(n_modes, 3000, 20.0, rng, e_budget=1.2*n_modes*20.0/2)
    marg=h.mean(0); joint=h.all(1).mean()
    print("n_modes=%-3d  C1=%.3f C2=%.3f C3=%.3f C4=%.3f | JOINT p=%.5f"
          %(n_modes,*marg,joint), end="")
    if joint>0:
        print("   classical ~%.0f draws | amplitude-amp ~%.0f"%(1/joint, 1/np.sqrt(joint)))
    else:
        print("   JOINT = 0 in 3000 draws  (p < 3.3e-4)")
