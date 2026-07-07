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


def _gnm_msf(coords: np.ndarray, cutoff: float) -> np.ndarray:
    """GNM mean-square fluctuation = diagonal of the Kirchhoff pseudo-inverse.

    Returns (N,) array of per-residue predicted MSF values.
    """
    from .hamiltonians import contact_matrix, laplacian

    A = contact_matrix(coords, cutoff=cutoff, weight="binary")
    K = laplacian(A)
    w, U = np.linalg.eigh(K)
    nz = w > 1e-9
    winv = np.where(nz, 1.0 / np.where(nz, w, 1.0), 0.0)
    return np.diag((U * winv) @ U.T)


# ---------------------------------------------------------------------------
# Public potential functions
# ---------------------------------------------------------------------------

def V_B(bfactors: np.ndarray) -> np.ndarray:
    """Diagonal B-factor penalty.

    High-B residues get a large positive diagonal → they are energetically
    penalised in the Hamiltonian, reducing their apparent connectivity.

    Returns (N, N) diagonal matrix.
    """
    b = bfactors.astype(float)
    b_norm = b / (b.mean() + 1e-9)
    return np.diag(b_norm)


def V_T(n_residues: int, terminal_fraction: float = 0.05) -> np.ndarray:
    """Diagonal terminal-residue suppression (uniform penalty on termini).

    Returns (N, N) diagonal matrix with 1.0 on terminal residues, 0 elsewhere.
    """
    N = n_residues
    n_term = max(1, int(N * terminal_fraction))
    mask = np.zeros(N)
    mask[:n_term] = 1.0
    mask[-n_term:] = 1.0
    return np.diag(mask)


def V_R(
    coords: np.ndarray,
    cutoff: float = 10.0,
) -> np.ndarray:
    """Rigidity reward: three-term z-score combining connectivity, local
    topology, and GNM mean-square fluctuation (matches QAS V_rigidity).

    score = -(z(degree) + z(clustering) − z(msf))

    High degree + high clustering + low MSF → rigid hub → negative diagonal
    (lowers effective energy). The B-factor term from the old formulation is
    absent here — it is already captured by the independent V_B term.

    Clustering is the local clustering coefficient:
        C_i = diag(A³)[i] / (deg_i × (deg_i − 1))
    which counts triangles relative to all possible neighbor-pair edges.
    Nodes with degree < 2 get clustering = 0.

    Returns (N, N) diagonal matrix.
    """
    from .hamiltonians import contact_matrix

    A = contact_matrix(coords, cutoff=cutoff, weight="binary")
    degree = A.sum(axis=1)

    # Local clustering coefficient: diag(A³) = 2 × triangles at each node
    tri = np.diag(A @ (A @ A))
    clust = tri / np.maximum(degree * (degree - 1), 1.0)

    msf = _gnm_msf(coords, cutoff=cutoff)

    score = -(_zscore(degree) + _zscore(clust) - _zscore(msf))
    return np.diag(score)


def V_C(
    coords: np.ndarray,
    cutoff: float = 10.0,
) -> np.ndarray:
    """Covariance-centrality reward via GNM dynamic cross-correlation (DCC).

    Computes the Kirchhoff pseudo-inverse to obtain the GNM covariance matrix,
    then scores each residue by its mean absolute normalised DCC with all other
    residues. This is the standard measure of allosteric coupling (Haliloglu &
    Bahar 1999) and physically distinct from a static contact centrality.

    Returns (N, N) diagonal matrix (negative = reward for high DCC coupling).
    """
    from .hamiltonians import contact_matrix, laplacian

    A = contact_matrix(coords, cutoff=cutoff, weight="binary")
    K = laplacian(A)
    w, U = np.linalg.eigh(K)

    # Pseudo-inverse: invert all non-zero eigenvalues
    nz = w > 1e-9
    winv = np.where(nz, 1.0 / np.where(nz, w, 1.0), 0.0)
    Cov = (U * winv) @ U.T                            # GNM covariance (Kirchhoff⁺)

    # Normalised DCC: C_ij / sqrt(C_ii * C_jj)
    d = np.sqrt(np.clip(np.diag(Cov), 1e-12, None))
    nDCC = Cov / np.outer(d, d)
    np.fill_diagonal(nDCC, 0.0)                       # exclude self-coupling

    centrality = np.abs(nDCC).sum(axis=1)             # mean absolute DCC per residue
    centrality_norm = centrality / (centrality.max() + 1e-9)
    return np.diag(-centrality_norm)


def V_M(
    coords: np.ndarray,
    cutoff: float = 10.0,
    n_modes: int = 10,
) -> np.ndarray:
    """Low-mode participation reward.

    Computes the n_modes lowest non-trivial eigenvectors of the GNM Kirchhoff
    matrix, then scores each residue by its mean squared participation across
    those modes. High participation in slow modes → signal-carrying → rewarded.

    Returns (N, N) diagonal matrix (negative = reward).
    """
    from .hamiltonians import H8_gnm

    L = H8_gnm(coords, cutoff=cutoff)
    w, v = np.linalg.eigh(L)

    # Skip the zero mode (rigid body); take next n_modes
    idx_start = max(1, np.searchsorted(w, 1e-8))
    idx_end = min(idx_start + n_modes, len(w))
    low_modes = v[:, idx_start:idx_end]           # (N, n_modes)

    participation = (low_modes ** 2).mean(axis=1)  # (N,)
    part_norm = participation / (participation.max() + 1e-9)
    return np.diag(-part_norm)
