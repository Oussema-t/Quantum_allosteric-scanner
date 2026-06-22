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
                clust=clust, beta=np.asarray(bfac, float))


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
    }
    if site_idx is not None and len(site_idx):
        site_idx = np.asarray(site_idx, int)
        bulk = np.setdiff1d(np.arange(c["N"]), site_idx)
        out["enrichment"] = {
            k: round(float(vals[site_idx].mean()
                           - (vals[bulk].mean() if len(bulk) else 0.0)), 3)
            for k, vals in terms.items()
        }
    return out


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

    return {
        "labels": a["labels"],
        "active_site": sorted(siteset),
        "apo": a,
        "holo": h,
        "delta": {"resnums": shared, "terms": delta_terms,
                  "labels": a["labels"], "enrichment": delta_enr},
        "n_shared": len(shared),
    }
