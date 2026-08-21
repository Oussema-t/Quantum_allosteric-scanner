"""
ANM subspace reachability probe.

Q: can low-frequency ANM modes EXPRESS the deformation required to open a local pocket?
This measures the actuator, independent of how many search iterations are run.

Controls included (collective hinge, smooth field, single-residue kick) to verify the
harness: a broken harness returns ~0 for everything.

RE-RUN ON REAL APO->HOLO PAIRS (4OBE->6OIM, 1OPL->5MO4, 5TBY->6C1H) with the TRUE
displacement vector in place of the synthetic opening vector. See TASK-0211 section 5.1.
No rcsb.org egress in the container this was written in.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
from scipy.linalg import eigh
from prody import parsePDB, confProDy; confProDy(verbosity='none')

def anm_subspace(co, cutoff=15.0):
    N = len(co); H = np.zeros((3*N, 3*N))
    D = np.linalg.norm(co[:, None]-co[None], axis=-1)
    for i in range(N):
        for j in range(i+1, N):
            d = D[i, j]
            if 0 < d < cutoff:
                dv = co[j]-co[i]; K = np.outer(dv, dv)/d**2
                H[3*i:3*i+3, 3*j:3*j+3] -= K; H[3*j:3*j+3, 3*i:3*i+3] -= K
                H[3*i:3*i+3, 3*i:3*i+3] += K; H[3*j:3*j+3, 3*j:3*j+3] += K
    w, V = eigh(H)
    return V[:, np.flatnonzero(w > 1e-6)], D          # rigid-body modes removed

def cumulative_overlap(Vn, v, ks=(5, 10, 20, 50, 100)):
    v = Vn @ (Vn.T @ v); v = v/np.linalg.norm(v); p = Vn.T @ v
    return {k: float((p[:k]**2).sum()) for k in ks}

def local_opening(co, D, j, shell_r=10.0):
    sh = np.append(np.flatnonzero((D[j] < shell_r) & (D[j] > 0)), j)
    d = np.zeros_like(co); u = co[sh]-co[sh].mean(0)
    n = np.linalg.norm(u, axis=1, keepdims=True); n[n < 1e-6] = 1
    d[sh] = u/n
    return d.ravel()

if __name__ == "__main__":
    P = '/usr/local/lib/python3.12/dist-packages/'
    for name, path, ch in [("ADK", P+'MDAnalysisTests/data/adk_oplsaa.pdb', None),
                           ("1R19", P+'prody/tests/datafiles/pdb1r19_dssp.pdb', 'A'),
                           ("3HSY", P+'prody/tests/datafiles/pdb3hsy.pdb', 'A'),
                           ("3ENL", P+'prody/tests/datafiles/addH_pdb3enl.pdb', 'A')]:
        st = parsePDB(path, subset='ca', model=1)
        if ch: st = st.select(f'chain {ch}')
        co = st.getCoords().astype(float); N = len(co)
        Vn, D = anm_subspace(co)
        r = np.linalg.norm(co-co.mean(0), axis=1)
        surf = np.flatnonzero(r > np.percentile(r, 50))
        rng = np.random.default_rng(0)
        sites = rng.choice(surf, size=min(40, len(surf)), replace=False)
        acc = {}
        for j in sites:
            for k, v in cumulative_overlap(Vn, local_opening(co, D, int(j))).items():
                acc.setdefault(k, []).append(v)
        print(f"{name:5s} N={N:4d} local-opening overlap  " +
              "  ".join(f"k={k}:{np.mean(v):.3f}" for k, v in acc.items()))
