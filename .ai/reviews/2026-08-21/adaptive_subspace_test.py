"""
Adaptive vs static ENM subspace reachability (TASK-0212 section 2).

Q: does a per-step-recomputed (adaptive) mode basis reach deformations that a fixed
apo basis of the SAME DIMENSION cannot? Equal-dimension comparison is essential --
otherwise any gain is a dimension artefact.

OBSERVED on ADK: adaptive 0.229 +- 0.164 vs static 0.024 +- 0.023 (dim 110) = 9.4x.

RE-RUN ON REAL PAIRS: replace `local_opening` with the true superposed apo->holo
displacement for 4OBE->6OIM, 1OPL->5MO4, 5TBY->6C1H. No rcsb egress where this was written.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
from scipy.linalg import eigh
from prody import parsePDB, confProDy; confProDy(verbosity='none')

def hessian(co, cutoff=15.0):
    N = len(co); H = np.zeros((3*N, 3*N))
    D = np.linalg.norm(co[:, None]-co[None], axis=-1)
    for i in range(N):
        for j in range(i+1, N):
            d = D[i, j]
            if 0 < d < cutoff:
                dv = co[j]-co[i]; K = np.outer(dv, dv)/d**2
                H[3*i:3*i+3, 3*j:3*j+3] -= K; H[3*j:3*j+3, 3*i:3*i+3] -= K
                H[3*i:3*i+3, 3*i:3*i+3] += K; H[3*j:3*j+3, 3*j:3*j+3] += K
    return H, D

def modes(co, k):
    H, D = hessian(co); w, V = eigh(H); nz = np.flatnonzero(w > 1e-6)
    return V[:, nz[:k]], V[:, nz], D

def adaptive_union(co, k=10, n_modes_stepped=5, amp=6.0):
    """Union of top-k modes at apo and at structures stepped +/- along modes 1..n."""
    M0, _, _ = modes(co, k); N = len(co); cols = [M0]
    for m in range(n_modes_stepped):
        for s in (+1, -1):
            d = M0[:, m].reshape(N, 3); d = s*d/np.linalg.norm(d)*np.sqrt(N)*amp
            Mi, _, _ = modes(co+d, k); cols.append(Mi)
    return np.linalg.qr(np.column_stack(cols))[0]

def captured(S, v):
    return float(np.linalg.norm(S @ (S.T @ v))**2)

def local_opening(co, D, j, shell_r=10.0):
    sh = np.append(np.flatnonzero((D[j] < shell_r) & (D[j] > 0)), j)
    d = np.zeros_like(co); u = co[sh]-co[sh].mean(0)
    d[sh] = u/np.linalg.norm(u, axis=1, keepdims=True)
    return d.ravel()

if __name__ == "__main__":
    st = parsePDB('/usr/local/lib/python3.12/dist-packages/MDAnalysisTests/data/adk_oplsaa.pdb',
                  subset='ca', model=1)
    co = st.getCoords().astype(float)
    _, Vfull, D = modes(co, 10)
    ADAPT = adaptive_union(co); dim = ADAPT.shape[1]
    STATIC = Vfull[:, :dim]                       # equal dimension -- do not omit
    rng = np.random.default_rng(0)
    r = np.linalg.norm(co-co.mean(0), axis=1)
    sites = rng.choice(np.flatnonzero(r > np.percentile(r, 50)), 40, replace=False)
    a, s = [], []
    for j in sites:
        v = Vfull @ (Vfull.T @ local_opening(co, D, int(j)))   # strip rigid-body
        v /= np.linalg.norm(v)
        a.append(captured(ADAPT, v)); s.append(captured(STATIC, v))
    print(f"dim={dim}  static {np.mean(s):.4f}+-{np.std(s):.4f}   "
          f"adaptive {np.mean(a):.4f}+-{np.std(a):.4f}   ratio {np.mean(a)/np.mean(s):.2f}x")
