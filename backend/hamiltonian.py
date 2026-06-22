"""
Hamiltonian library (notebook §2).

The residue contact network defines a graph operator H (the system "Hamiltonian").
Each family encodes a different physical prior — pure contact topology (GNM),
anisotropic directionality (ANM), low-frequency collective modes (LMS), or
B-factor / disorder weighting. All are returned as a normalized graph Laplacian so
the downstream propagators see a consistent spectral scale.
"""
import numpy as np
from scipy.spatial.distance import cdist

FAMILIES = ["GNM", "GNM_bfactor", "ANM", "LMS", "H10", "H10_disorder_supp",
            "H10B_disorder_bfactor", "rigidity_laplacian", "terminal_suppressed"]


def normalized_laplacian(W):
    """L = I - D^-1/2 W D^-1/2 ; isolated nodes kept inert (no NaN)."""
    W = W.copy()
    np.fill_diagonal(W, 0.0)
    d = W.sum(1)
    nz = d > 1e-12
    dinv = np.zeros_like(d)
    dinv[nz] = 1.0 / np.sqrt(d[nz])
    A = (dinv[:, None] * W) * dinv[None, :]
    L = np.eye(len(d)) - A
    L[~nz, :] = 0.0
    L[:, ~nz] = 0.0
    return L


def contact_weight(coords, cutoff, power=1.0):
    """Inverse-distance contact weights within `cutoff` Angstrom."""
    D = cdist(coords, coords)
    np.fill_diagonal(D, np.inf)
    return np.where(D < cutoff, 1.0 / (D ** power), 0.0)


def build_anm_3n(coords, cutoff):
    """Anisotropic Network Model 3N×3N Hessian (directional spring couplings)."""
    N = len(coords)
    H = np.zeros((3 * N, 3 * N))
    diff = coords[:, None, :] - coords[None, :, :]
    dist = np.linalg.norm(diff, axis=-1)
    for i in range(N):
        for j in range(i + 1, N):
            if 1e-8 < dist[i, j] < cutoff:
                e = diff[i, j] / dist[i, j]
                K = np.outer(e, e)
                H[3 * i:3 * i + 3, 3 * j:3 * j + 3] = -K
                H[3 * j:3 * j + 3, 3 * i:3 * i + 3] = -K
                H[3 * i:3 * i + 3, 3 * i:3 * i + 3] += K
                H[3 * j:3 * j + 3, 3 * j:3 * j + 3] += K
    return H


def project_3n(H3n, method="trace"):
    """Collapse a 3N×3N anisotropic operator to an N×N scalar coupling matrix."""
    N = H3n.shape[0] // 3
    W = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            if i == j:
                continue
            b = H3n[3 * i:3 * i + 3, 3 * j:3 * j + 3]
            if method == "trace":
                W[i, j] = abs(np.trace(b))
            elif method == "fro":
                W[i, j] = np.linalg.norm(b)
            elif method == "maxsv":
                W[i, j] = np.linalg.svd(b, compute_uv=False)[0]
    return W


def build_hamiltonian(coords, bfac, family, p):
    """Build the N×N Hamiltonian for the requested `family`. `p` carries cutoff and
    family-specific knobs (power, mu, k_modes, proj, term_frac)."""
    N = len(coords)
    cutoff = p["cutoff"]
    bn = (bfac - bfac.min()) / (np.ptp(bfac) + 1e-9)   # 0 rigid .. 1 disordered
    D = cdist(coords, coords)
    np.fill_diagonal(D, np.inf)

    if family == "GNM":
        return normalized_laplacian(contact_weight(coords, cutoff, p.get("power", 1.0)))
    if family == "GNM_bfactor":
        Bm = bfac[:, None] + bfac[None, :] + 1e-2
        return normalized_laplacian((D < cutoff).astype(float) / Bm)
    if family == "ANM":
        return normalized_laplacian(
            project_3n(build_anm_3n(coords, cutoff), p.get("proj", "trace")))
    if family == "LMS":
        H3 = build_anm_3n(coords, cutoff)
        w, V = np.linalg.eigh(H3)
        w, V = w[6:], V[:, 6:]
        k = min(p.get("k_modes", 20), len(w))
        inv = 1.0 / (w[:k] + 1e-8)
        Cov = (V[:, :k] * inv) @ V[:, :k].T
        W = np.zeros((N, N))
        for i in range(N):
            for j in range(N):
                if i != j:
                    W[i, j] = abs(np.trace(Cov[3 * i:3 * i + 3, 3 * j:3 * j + 3]))
        return normalized_laplacian(W)
    if family == "H10":
        W = contact_weight(coords, cutoff, p.get("power", 1.0))
        deg = (D < cutoff).sum(1).astype(float)
        return normalized_laplacian(W) + np.diag(-p.get("mu", 0.0) * (deg / (deg.max() + 1e-9)))
    if family == "H10_disorder_supp":
        W = contact_weight(coords, cutoff, p.get("power", 1.0))
        return normalized_laplacian(W) + np.diag(p.get("mu", 1.0) * bn)
    if family == "H10B_disorder_bfactor":
        rij = 1.0 / (bfac[:, None] + bfac[None, :] + 1e-2)
        return normalized_laplacian((D < cutoff).astype(float) * rij) + np.diag(p.get("mu", 0.5) * bn)
    if family == "rigidity_laplacian":
        rij = 2.0 / (bfac[:, None] + bfac[None, :] + 1e-2)
        return normalized_laplacian((D < cutoff).astype(float) * rij)
    if family == "terminal_suppressed":
        W = contact_weight(coords, cutoff, p.get("power", 1.0))
        f = p.get("term_frac", 0.08)
        k = max(1, int(f * N))
        pot = np.zeros(N)
        pot[:k] = p.get("mu", 1.0)
        pot[-k:] = p.get("mu", 1.0)
        return normalized_laplacian(W) + np.diag(pot)
    raise ValueError(family)


def spectral_filter(H, lam_exp, lam_ln):
    """Reshape the eigenvalue spectrum (emphasize slow collective modes)."""
    w, V = np.linalg.eigh(H)
    mx = np.abs(w).max() + 1e-12
    nw = np.abs(w) / mx
    w2 = w * np.exp(-lam_exp * nw ** 2) * (1 + lam_ln * np.log1p(nw))
    return (V * w2) @ V.T
