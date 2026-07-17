"""Diagonal potential terms V_B, V_T, V_R, V_C, V_M for H_new.

Each function returns an (N, N) diagonal matrix (as a 2-D array) that is
added onto the base normalised Laplacian in hamiltonians.build_H_new.

Physical motivation (see PLAN §Phase 0):
  V_B – B-factor penalty: penalise intrinsically flexible (high-B) residues
        that are unlikely to be stable allosteric hubs.
  V_T – Terminal/disorder suppression: penalise N- and C-terminal segments
        which are often disordered and not part of the structured core.
  V_R – Rigidity reward: reward residues that are buried, clustered, and
        have low mean-square fluctuation – hallmarks of rigid, signal-carrying nodes.
  V_C – Covariance-centrality reward: reward residues that are strongly
        co-fluctuating with the rest of the network, measured via GNM
        dynamic cross-correlation (DCC) from the Kirchhoff pseudo-inverse.
  V_M – Low-mode participation reward: reward residues with high overlap
        with the slowest ANM modes (most likely to carry global signals).

TASK-0121: every term below is z-scored (mean 0, std 1) as its final step,
before `hamiltonians.build_H_new` applies the `lam_*` weights. Before this
fix, V_B/V_T were unnormalised (mean-ratio / 0-1 mask) and V_C/V_M were
max-normalised to [-1, 0] -- on real targets this made V_R (already an
internal sum of 3 z-scores, sigma ~= 1.9) ~30x larger than V_C/V_M
(sigma ~= 0.06), so V_R alone carried 88.8% of the potential's variance and
lam_C/lam_M were unreachable knobs (REVIEW-panel-2026-07-16-v2.md §2.4).
Z-scoring first makes every term commensurate (sigma = 1) so the `lam_*`
weights chosen in `build_H_new` are the only thing controlling each term's
share of the combined potential's variance.
"""
from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _zscore(x: np.ndarray) -> np.ndarray:
    """Z-score normalisation; safe against near-zero standard deviation."""
    std = x.std()
    return (x - x.mean()) / (std + 1e-9)


def _kirchhoff_eigh(coords: np.ndarray, cutoff: float):
    """Binary contact matrix -> Kirchhoff (`hamiltonians.laplacian`) ->
    eigendecomposition -> Moore-Penrose pseudo-inverse ingredients
    (TASK-0066).

    Shared by `_gnm_msf`/`V_C`/`V_M` -- previously three independent
    re-derivations of the same binary-Kirchhoff eigendecomposition
    (`V_M`'s own copy went through `hamiltonians.H8_gnm`, mathematically
    identical to this function's `A`/`K` construction -- same `weight=
    "binary"`, same `laplacian(..., normalised=False)` default -- just a
    second call site for it). Ported analogue of
    `backend/analysis.py::_kirchhoff_eigh` -- same math, independent
    implementation per TASK-0018's backend<->allostery boundary (no
    cross-package import). Returns `(A, w, U, nz, winv)`.
    """
    from .hamiltonians import contact_matrix, laplacian

    A = contact_matrix(coords, cutoff=cutoff, weight="binary")
    K = laplacian(A)
    w, U = np.linalg.eigh(K)
    nz = w > 1e-9
    winv = np.where(nz, 1.0 / np.where(nz, w, 1.0), 0.0)
    return A, w, U, nz, winv


def _normalized_dcc(U: np.ndarray, winv: np.ndarray) -> np.ndarray:
    """Normalized GNM dynamic cross-correlation matrix from the Kirchhoff
    pseudo-inverse's eigenvectors/inverted-eigenvalues (TASK-0066).

    Diagonal is left as computed (self-correlation = 1), not zeroed --
    `V_C` zeroes it itself before summing, matching its own pre-existing
    convention.
    """
    Cov = (U * winv) @ U.T                            # GNM covariance = Kirchhoff pseudo-inverse
    d = np.sqrt(np.clip(np.diag(Cov), 1e-12, None))
    return Cov / np.outer(d, d)


def _gnm_msf(coords: np.ndarray, cutoff: float) -> np.ndarray:
    """GNM mean-square fluctuation = diagonal of the Kirchhoff pseudo-inverse.

    Returns (N,) array of per-residue predicted MSF values.
    """
    _A, _w, U, _nz, winv = _kirchhoff_eigh(coords, cutoff)
    return np.diag((U * winv) @ U.T)


# ---------------------------------------------------------------------------
# Public potential functions
# ---------------------------------------------------------------------------

def V_B(bfactors: np.ndarray) -> np.ndarray:
    """Diagonal B-factor penalty, z-scored (TASK-0121).

    High-B residues get a large positive diagonal → they are energetically
    penalised in the Hamiltonian, reducing their apparent connectivity.
    Low-B residues get a negative diagonal (mild reward) as a consequence
    of z-scoring around the mean, not a separate design choice.

    Returns (N, N) diagonal matrix, mean 0 / std 1.
    """
    b = bfactors.astype(float)
    return np.diag(_zscore(b))


def V_T(n_residues: int, terminal_fraction: float = 0.05) -> np.ndarray:
    """Diagonal terminal-residue suppression, z-scored (TASK-0121).

    Before z-scoring: 1.0 on terminal residues, 0.0 elsewhere. z-scoring
    this binary mask keeps termini scoring strictly higher (worse) than
    the core while giving the term mean 0 / std 1, commensurate with the
    other four terms.

    Returns (N, N) diagonal matrix, mean 0 / std 1.
    """
    N = n_residues
    n_term = max(1, int(N * terminal_fraction))
    mask = np.zeros(N)
    mask[:n_term] = 1.0
    mask[-n_term:] = 1.0
    return np.diag(_zscore(mask))


def V_R(
    coords: np.ndarray,
    cutoff: float = 10.0,
) -> np.ndarray:
    """Rigidity reward: three-term z-score combining connectivity, local
    topology, and GNM mean-square fluctuation (matches QAS V_rigidity).

    score = -(z(degree) + z(clustering) − z(msf)), re-z-scored (TASK-0121)

    High degree + high clustering + low MSF → rigid hub → negative diagonal
    (lowers effective energy). The B-factor term from the old formulation is
    absent here — it is already captured by the independent V_B term.

    Clustering is the local clustering coefficient:
        C_i = diag(A³)[i] / (deg_i × (deg_i − 1))
    which counts triangles relative to all possible neighbor-pair edges.
    Nodes with degree < 2 get clustering = 0.

    The inner sum of three z-scores has std ~= 1.9 on real targets (not 1,
    since the three components are correlated, not independent) --
    TASK-0121 re-z-scores the combined score so V_R's std matches the other
    four terms' std of 1 exactly, instead of assuming three z-scores summed
    is already commensurate.

    Returns (N, N) diagonal matrix, mean 0 / std 1.
    """
    from .hamiltonians import contact_matrix

    A = contact_matrix(coords, cutoff=cutoff, weight="binary")
    degree = A.sum(axis=1)

    # Local clustering coefficient: diag(A³) = 2 × triangles at each node
    tri = np.diag(A @ (A @ A))
    clust = tri / np.maximum(degree * (degree - 1), 1.0)

    msf = _gnm_msf(coords, cutoff=cutoff)

    score = -(_zscore(degree) + _zscore(clust) - _zscore(msf))
    return np.diag(_zscore(score))


def V_C(
    coords: np.ndarray,
    cutoff: float = 10.0,
) -> np.ndarray:
    """Covariance-centrality reward via GNM dynamic cross-correlation (DCC).

    Computes the Kirchhoff pseudo-inverse to obtain the GNM covariance matrix,
    then scores each residue by its mean absolute normalised DCC with all other
    residues. This is the standard measure of allosteric coupling (Haliloglu &
    Bahar 1999) and physically distinct from a static contact centrality.

    TASK-0121: previously max-normalised to [-1, 0] (std ~= 0.06 on real
    targets, ~30x smaller than V_R), which made lam_C an unreachable knob --
    now z-scored like the other four terms so lam_C actually controls this
    term's share of the combined potential's variance.

    Returns (N, N) diagonal matrix, mean 0 / std 1 (negative = reward for
    high DCC coupling).
    """
    _A, _w, U, _nz, winv = _kirchhoff_eigh(coords, cutoff)
    nDCC = _normalized_dcc(U, winv)
    np.fill_diagonal(nDCC, 0.0)                       # exclude self-coupling

    centrality = np.abs(nDCC).sum(axis=1)             # mean absolute DCC per residue
    return np.diag(-_zscore(centrality))


def V_M(
    coords: np.ndarray,
    cutoff: float = 10.0,
    n_modes: int = 10,
) -> np.ndarray:
    """Low-mode participation reward.

    Computes the n_modes lowest non-trivial eigenvectors of the GNM Kirchhoff
    matrix, then scores each residue by its mean squared participation across
    those modes. High participation in slow modes → signal-carrying → rewarded.

    TASK-0121: previously max-normalised to [-1, 0] (std ~= 0.06 on real
    targets, ~30x smaller than V_R), which made lam_M an unreachable knob --
    now z-scored like the other four terms so lam_M actually controls this
    term's share of the combined potential's variance.

    Returns (N, N) diagonal matrix, mean 0 / std 1 (negative = reward).
    """
    _A, w, v, _nz, _winv = _kirchhoff_eigh(coords, cutoff)

    # Skip the zero mode (rigid body); take next n_modes
    idx_start = max(1, np.searchsorted(w, 1e-8))
    idx_end = min(idx_start + n_modes, len(w))
    low_modes = v[:, idx_start:idx_end]           # (N, n_modes)

    participation = (low_modes ** 2).mean(axis=1)  # (N,)
    return np.diag(-_zscore(participation))
