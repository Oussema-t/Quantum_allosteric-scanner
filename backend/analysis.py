"""
GNM site-potential analysis (notebook §5b) — adapted to this app's structures.

From the Cα contact network we build the Gaussian Network Model (GNM / Kirchhoff
operator) and derive five per-residue "site-potential" descriptors. Each is
z-scored across the protein so they're comparable, and (when an active site is
known) we report how elevated each term is AT the site vs the bulk — the biological
signal that flags allosteric/cryptic pockets.

  V_B  B-factor flexibility     crystallographic mobility (high = flexible)
  V_T  terminal / exposure      chain-end proximity + solvent exposure proxy
  V_R  rigidity                 high degree + clustering, low fluctuation (rigid core)
  V_C  dynamic coupling         GNM covariance — how dynamically correlated a residue is
  V_M  slow-mode participation  involvement in the slowest collective (global) modes

This is structure-based only (the elastic-network hypothesis); no MD, no quantum.
"""
import numpy as np
from scipy.spatial.distance import cdist

from .data_layer import load_structure, res_indices


def _z(x):
    x = np.asarray(x, float)
    s = x.std()
    return (x - x.mean()) / (s + 1e-9) if s > 0 else np.zeros_like(x)


def _coordination(coords, cutoff):
    """Per-residue coordination number (contacts within cutoff)."""
    D = cdist(coords, coords)
    return ((D < cutoff) & (D > 1e-8)).sum(1).astype(float)


def _kabsch_rotate(mobile, ref):
    """Rotate `mobile` (N,3) onto `ref` (N,3) by least squares; return aligned mobile."""
    mc = mobile - mobile.mean(0)
    rc = ref - ref.mean(0)
    U, _S, Vt = np.linalg.svd(mc.T @ rc)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    return mc @ R.T + ref.mean(0)


def gnm_context(coords, bfac, cutoff=8.0):
    """Kirchhoff (GNM) operator and the quantities the five terms are built from."""
    N = len(coords)
    D = cdist(coords, coords)
    A = ((D < cutoff) & (D > 1e-8)).astype(float)
    deg = A.sum(1)
    K = np.diag(deg) - A                          # Kirchhoff = GNM operator
    w, U = np.linalg.eigh(K)
    nz = w > 1e-9
    winv = np.zeros_like(w)
    winv[nz] = 1.0 / w[nz]
    msf = ((U ** 2) * winv).sum(1)                # mean-square fluctuation (high = flexible)
    tri = np.diag(A @ A @ A)
    with np.errstate(invalid="ignore", divide="ignore"):
        clust = np.where(deg > 1, tri / (deg * (deg - 1)), 0.0)
    return dict(N=N, A=A, deg=deg, U=U, nz=nz, winv=winv, msf=msf,
                clust=clust, beta=np.asarray(bfac, float), eigs=w)


def V_Bfactor(c):
    b = c["beta"].astype(float)
    if np.allclose(b, 0):
        return np.zeros(c["N"])
    return _z((b - b.min()) / (b.max() - b.min() + 1e-9))


def V_terminal(c, n_term=8, rsa_cut=18):
    N = c["N"]
    pos = np.arange(N)
    t_term = np.exp(-np.minimum(pos, N - 1 - pos) / n_term)   # chain termini
    rsa = np.clip(1.0 - c["deg"] / rsa_cut, 0, 1)             # exposure proxy
    return _z(0.5 * t_term + 0.5 * rsa)


def V_rigidity(c):
    return _z(_z(c["deg"]) + _z(c["clust"]) + (-_z(c["msf"])))


def V_covariance(c):
    Cov = (c["U"] * c["winv"]) @ c["U"].T          # GNM covariance = Kirchhoff pseudo-inverse
    d = np.sqrt(np.clip(np.diag(Cov), 1e-12, None))
    nDCC = Cov / np.outer(d, d)
    np.fill_diagonal(nDCC, 0.0)
    return _z(np.abs(nDCC).sum(1))


def V_modeparticipation(c, n_low=10):
    idx = np.where(c["nz"])[0][:n_low]
    return _z((c["U"][:, idx] ** 2).sum(1))


TERMS = [
    ("V_B", "B-factor flexibility", V_Bfactor),
    ("V_T", "terminal / exposure", V_terminal),
    ("V_R", "rigidity", V_rigidity),
    ("V_C", "dynamic coupling", V_covariance),
    ("V_M", "slow-mode participation", V_modeparticipation),
]


def site_potentials(coords, bfac, resnums, cutoff=8.0, site_idx=None):
    """Per-residue z-scored site potentials + optional pocket-vs-bulk enrichment."""
    c = gnm_context(coords, bfac, cutoff)
    terms = {k: fn(c) for k, _lab, fn in TERMS}
    out = {
        "cutoff": cutoff,
        "resnums": [int(r) for r in resnums],
        "labels": {k: lab for k, lab, _ in TERMS},
        "terms": {k: [round(float(v), 4) for v in vals] for k, vals in terms.items()},
        "l_eigs": [round(float(x), 4) for x in c["eigs"]],   # Kirchhoff/Laplacian spectrum
    }
    if site_idx is not None and len(site_idx):
        site_idx = np.asarray(site_idx, int)
        N = c["N"]
        n_site = len(site_idx)
        nb = N - n_site
        rng = np.random.default_rng(0)
        n_perm = 1000
        enr, sig = {}, {}
        for k, vals in terms.items():
            v = np.asarray(vals, float)
            total, site_sum = v.sum(), v[site_idx].sum()
            obs = site_sum / n_site - ((total - site_sum) / nb if nb else 0.0)
            # permutation null: random residue sets of the same size as the active site
            null = np.empty(n_perm)
            for p in range(n_perm):
                ps = v[rng.choice(N, n_site, replace=False)].sum()
                null[p] = ps / n_site - ((total - ps) / nb if nb else 0.0)
            pval = float((np.abs(null) >= abs(obs)).mean())
            enr[k] = round(float(obs), 3)
            sig[k] = {"p": round(pval, 4), "sig": bool(pval < 0.05)}
        out["enrichment"] = enr
        out["enrichment_sig"] = sig
    return out


def _dcc(coords, cutoff):
    """GNM dynamic cross-correlation (normalized covariance = Kirchhoff pseudo-inverse)."""
    D = cdist(coords, coords)
    A = ((D < cutoff) & (D > 1e-8)).astype(float)
    K = np.diag(A.sum(1)) - A
    w, U = np.linalg.eigh(K)
    nz = w > 1e-9
    winv = np.zeros_like(w)
    winv[nz] = 1.0 / w[nz]
    Cov = (U * winv) @ U.T
    s = np.sqrt(np.clip(np.diag(Cov), 1e-12, None))
    return Cov / np.outer(s, s)


def connectivity_change(apo_pdb, apo_chain, holo_pdb, holo_chain=None, cutoff=8.0,
                        site_resnums=None, max_n=400, r0=7.0):
    """apo→holo network reorganization on shared residues (notebook §8d), topology only:
      * DDM    distance-difference matrix  ΔD_ij = |r_ij|_holo − |r_ij|_apo
      * rewire binary contacts gained (+1) / lost (−1) at the cutoff
      * ΔDCC   change in GNM dynamic cross-correlation (allosteric coupling)
    Returns the matrices (down-sampled to max_n for display), summary stats computed on
    the FULL set, and the apo + Kabsch-aligned holo coords for the browser morph."""
    apo = load_structure(apo_pdb, apo_chain)
    holo = load_structure(holo_pdb, holo_chain or apo_chain)
    if apo is None or holo is None:
        raise ValueError(f"could not load apo {apo_pdb} or holo {holo_pdb}")
    common = np.intersect1d(apo["resnums"], holo["resnums"])
    if len(common) < 10:
        raise ValueError(f"only {len(common)} common residues between {apo_pdb}/{holo_pdb} "
                         f"— need ≥10 to compute the connectivity change")
    ia = np.array([np.where(apo["resnums"] == r)[0][0] for r in common])
    ib = np.array([np.where(holo["resnums"] == r)[0][0] for r in common])
    Ca, Ch = apo["coords"][ia], holo["coords"][ib]
    n = len(common)
    Chk = _kabsch_rotate(Ch, Ca)                       # aligned holo, for the morph

    Da, Dh = cdist(Ca, Ca), cdist(Ch, Ch)
    DDM = Dh - Da
    Aa = (Da < cutoff) & (Da > 1e-8)
    Ah = (Dh < cutoff) & (Dh > 1e-8)
    rewire = Ah.astype(int) - Aa.astype(int)
    dDCC = _dcc(Ch, cutoff) - _dcc(Ca, cutoff)

    mob = np.sqrt((DDM ** 2).mean(1))                  # per-residue reorganization
    hot = np.argsort(mob)[::-1][:5]
    summary = {
        "n_shared": int(n),
        "ddm_max": round(float(np.abs(DDM).max()), 2),
        "contacts_formed": int((rewire > 0).sum() // 2),
        "contacts_broken": int((rewire < 0).sum() // 2),
        "mean_abs_ddcc": round(float(np.abs(dDCC).mean()), 3),
        "most_reorganized": [int(common[i]) for i in hot],
    }

    # down-sample matrices/coords for the payload if large (summary stays on full set)
    if n > max_n:
        idx = np.unique(np.linspace(0, n - 1, max_n).astype(int))
    else:
        idx = np.arange(n)
    sub = np.ix_(idx, idx)
    site = set(int(r) for r in (site_resnums or []))
    common_sub = [int(common[i]) for i in idx]
    site_positions = [k for k, r in enumerate(common_sub) if r in site]

    return {
        "apo": apo_pdb, "holo": holo_pdb, "cutoff": cutoff, "r0": r0,
        "n_shared": int(n), "downsampled": bool(n > max_n),
        "resnums": common_sub,
        "site_positions": site_positions,
        "summary": summary,
        "ddm": np.round(DDM[sub], 2).tolist(),
        "rewire": rewire[sub].astype(int).tolist(),
        "ddcc": np.round(dDCC[sub], 3).tolist(),
        "apo_coords": np.round(Ca[idx], 3).tolist(),
        "holo_coords": np.round(Chk[idx], 3).tolist(),
    }


def site_potential_shift(apo_pdb, apo_chain, holo_pdb, holo_chain=None,
                         site_resnums=None, cutoff=8.0):
    """Site potentials for apo and holo, plus the apo->holo shift on shared residues
    (notebook §5c). Each structure is z-scored within itself, then subtracted, so the
    shift captures how the drug binding reshapes the dynamic network per residue."""
    apo = load_structure(apo_pdb, apo_chain)
    holo = load_structure(holo_pdb, holo_chain or apo_chain)
    if apo is None or holo is None:
        raise ValueError(f"could not load apo {apo_pdb} or holo {holo_pdb}")

    site = list(site_resnums or [])
    a = site_potentials(apo["coords"], apo["bfac"], apo["resnums"], cutoff,
                        site_idx=res_indices(apo, site) if site else None)
    h = site_potentials(holo["coords"], holo["bfac"], holo["resnums"], cutoff,
                        site_idx=res_indices(holo, site) if site else None)

    keys = list(a["terms"].keys())
    a_map = {k: dict(zip(a["resnums"], a["terms"][k])) for k in keys}
    h_map = {k: dict(zip(h["resnums"], h["terms"][k])) for k in keys}
    shared = sorted(set(a["resnums"]) & set(h["resnums"]))

    delta_terms = {k: [round(h_map[k][r] - a_map[k][r], 4) for r in shared] for k in keys}
    siteset = set(site)
    sidx = [i for i, r in enumerate(shared) if r in siteset]
    bidx = [i for i, r in enumerate(shared) if r not in siteset]
    delta_enr = {}
    if sidx:
        for k in keys:
            v = np.array(delta_terms[k], float)
            delta_enr[k] = round(float(v[sidx].mean()
                                       - (v[bidx].mean() if bidx else 0.0)), 3)

    # §5d: apo->holo Cα displacement (Kabsch) + coordination-number change
    structural = None
    if len(shared) >= 5:
        a_idx = {int(r): i for i, r in enumerate(apo["resnums"])}
        h_idx = {int(r): i for i, r in enumerate(holo["resnums"])}
        P = np.array([apo["coords"][a_idx[r]] for r in shared], float)   # apo
        Q = np.array([holo["coords"][h_idx[r]] for r in shared], float)  # holo
        disp = np.linalg.norm(P - _kabsch_rotate(Q, P), axis=1)
        deg_a = _coordination(apo["coords"], cutoff)
        deg_h = _coordination(holo["coords"], cutoff)
        dcoord = np.array([deg_h[h_idx[r]] - deg_a[a_idx[r]] for r in shared], float)
        structural = {
            "resnums": shared,
            "ca_displacement": [round(float(x), 3) for x in disp],
            "d_coordination": [round(float(x), 1) for x in dcoord],
            "ca_rmsd": round(float(np.sqrt((disp ** 2).mean())), 3),
            "max_disp": round(float(disp.max()), 3),
        }

    return {
        "labels": a["labels"],
        "active_site": sorted(siteset),
        "apo": a,
        "holo": h,
        "delta": {"resnums": shared, "terms": delta_terms,
                  "labels": a["labels"], "enrichment": delta_enr},
        "structural": structural,
        "n_shared": len(shared),
    }
