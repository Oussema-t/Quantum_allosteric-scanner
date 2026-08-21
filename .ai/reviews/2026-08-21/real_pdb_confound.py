"""
Observable-family proximity-confound test on REAL PDB structures.

Claim under test: the proximity confound is a property of seed-referencing scoring on a
static contact graph, not of the CTQW propagator, not of quantumness, and not of the
correlation-vs-entropy distinction.

Structures are those bundled with prody / MDAnalysisTests (this container has no rcsb.org
egress). None are challenge targets. RE-RUN ON 4OBE / 1OPL / 5TBY / 1NKP / PTP1B apo.
"""
import os, warnings, json
warnings.filterwarnings("ignore")
import numpy as np
from scipy.linalg import eigh, expm
from scipy.stats import spearmanr, rankdata
from scipy.sparse.csgraph import shortest_path, connected_components
from prody import parsePDB, confProDy
confProDy(verbosity='none')

D_PR = '/usr/local/lib/python3.12/dist-packages/prody/tests/datafiles/'
D_MD = '/usr/local/lib/python3.12/dist-packages/MDAnalysisTests/data/'
TARGETS = [("1UBI", D_PR+'pdb1ubi.pdb', 'A'), ("ADK", D_MD+'adk_oplsaa.pdb', None),
           ("1R19", D_PR+'pdb1r19_dssp.pdb','A'), ("7PBL", D_PR+'pdb7pbl.pdb','A'),
           ("3HSY", D_PR+'pdb3hsy.pdb','A'),      ("6FLR", D_PR+'pdb6flr.pdb','A'),
           ("3P3W", D_PR+'pdb3p3w.pdb','A'),      ("3O21", D_PR+'pdb3o21.pdb','A'),
           ("3ENL", D_PR+'addH_pdb3enl.pdb','A')]
CUT, STIFF, NSEED = 8.5, 3.0, 4

def pspear(x, y, z):
    rx, ry, rz = rankdata(x), rankdata(y), rankdata(z)
    r = lambda a: a - np.polyval(np.polyfit(rz, a, 1), rz)
    return float(np.corrcoef(r(rx), r(ry))[0, 1])

rows, meta = [], []
for name, path, ch in TARGETS:
    st = parsePDB(path, subset='ca', model=1)
    if ch is not None: st = st.select(f'chain {ch}')
    co = st.getCoords().astype(float); N = len(co)
    D = np.linalg.norm(co[:, None] - co[None], axis=-1)
    A = ((D < CUT) & (D > 0)).astype(float)
    for i in range(N-1): A[i, i+1] = A[i+1, i] = 1.0
    nc, _ = connected_components(A)
    deg = A.sum(1); Lap = np.diag(deg) - A
    gdist = shortest_path(A, unweighted=True)
    cen = co.mean(0); r = np.linalg.norm(co - cen, axis=1); burial = -r
    meta.append(dict(name=name, N=N, k=round(float(deg.mean()),2),
                     diam=int(np.nanmax(gdist[np.isfinite(gdist)])), comps=int(nc)))

    w, V = eigh(Lap); nz = w > 1e-8
    Cov = (V[:, nz]/w[nz]) @ V[:, nz].T
    idx = np.flatnonzero(nz)[:10]
    Cl = (V[:, idx]/w[idx]) @ V[:, idx].T
    wa, Va = eigh(A)

    # perturbation sweep once per protein (seed-independent inner loop)
    base_ld = float(np.sum(np.log(w[nz])))
    dS = np.zeros(N); diagP = np.zeros((N, N))
    for j in range(N):
        sh = np.append(np.flatnonzero(A[j]), j)
        Ap = A.copy(); ix = np.ix_(sh, sh); Ap[ix] = Ap[ix]*STIFF; np.fill_diagonal(Ap, 0.)
        L2 = np.diag(Ap.sum(1)) - Ap
        w2, V2 = eigh(L2); n2 = w2 > 1e-8
        dS[j] = -0.5*(float(np.sum(np.log(w2[n2]))) - base_ld)
        diagP[j] = np.einsum('ik,ik->i', V2[:, n2]/w2[n2], V2[:, n2])

    rng = np.random.default_rng(abs(hash(name)) % 2**31)
    pool = np.flatnonzero((r > np.percentile(r, 35)) & (r < np.percentile(r, 80)))
    for seed in rng.choice(pool, size=min(NSEED, len(pool)), replace=False):
        seed = int(seed); ed = D[seed]
        sc = {}
        es = Va[seed]
        for T in (5., 25.):
            ts = np.linspace(.1, T, 60); p = np.zeros(N)
            for t in ts: p += np.abs(Va @ (np.exp(-1j*wa*t)*es))**2
            sc[f"CTQW_adj_T{int(T)}"] = p/len(ts)
        sc["heat_T5"] = expm(-Lap*5.)[seed]
        Lpi = np.linalg.pinv(Lap); vol = deg.sum()
        sc["MRW_commute"] = -vol*(Lpi[seed, seed] + np.diag(Lpi) - 2*Lpi[seed])
        sc["GNM_corr_seed"] = Cov[seed]/np.sqrt(np.diag(Cov)*Cov[seed, seed])
        sc["GNM_corr_low10"] = Cl[seed]/np.sqrt(np.abs(np.diag(Cl)*Cl[seed, seed]))
        sc["dS_vib_global"] = dS
        sc["dMSF_at_seed"] = Cov[seed, seed] - diagP[:, seed]
        for k, v in sc.items():
            rows.append(dict(prot=name, seed=seed, obs=k,
                             rho_gd=float(spearmanr(v, gdist[seed]).statistic),
                             rho_ed=float(spearmanr(v, ed).statistic),
                             rho_burial=float(spearmanr(v, burial).statistic),
                             partial=pspear(v, ed, burial)))
    print(f"done {name} N={N}")

json.dump(dict(meta=meta, rows=rows), open('real_pdb_confound.json','w'), indent=1)
obs = sorted({x['obs'] for x in rows})
print(f"\nn_replicates = {len({(x['prot'],x['seed']) for x in rows})} "
      f"across {len(meta)} chains\n")
print(f"{'observable':18s} {'|partial rho(ed|burial)|':>26s} {'|rho_ed|':>10s} {'rho_burial':>11s}")
print("-"*70)
for o in obs:
    p = np.abs([x['partial'] for x in rows if x['obs']==o])
    e = np.abs([x['rho_ed'] for x in rows if x['obs']==o])
    b = np.array([x['rho_burial'] for x in rows if x['obs']==o])
    print(f"{o:18s} {p.mean():14.3f} +- {p.std():.3f} [{p.min():.2f},{p.max():.2f}]"
          f" {e.mean():8.3f} {b.mean():11.3f}")
