"""Graph Hamiltonians H1–H13 and H_new.

All functions take a coordinate array (N, 3) and return a symmetric (N, N)
numpy matrix. Eigenvalues are real; positive-semidefinite operators use the
Laplacian convention (L = D − A), indefinite ones use the adjacency (H = A).
"""
from __future__ import annotations

import numpy as np
from scipy import linalg as sla


# ---------------------------------------------------------------------------
# Core contact graph builder
# ---------------------------------------------------------------------------

def contact_matrix(
    coords: np.ndarray,
    cutoff: float = 10.0,
    weight: str = "binary",
    sigma: float = 6.0,
    alpha: float = 0.3,
) -> np.ndarray:
    """Build an (N, N) weighted contact matrix from Cα coordinates.

    Parameters
    ----------
    weight : {'binary', 'gaussian', 'exponential', 'harmonic', 'invdist'}
    """
    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]   # (N, N, 3)
    dist = np.sqrt((diff ** 2).sum(axis=2))                       # (N, N)
    mask = (dist < cutoff) & (dist > 0)

    if weight == "binary":
        W = mask.astype(float)
    elif weight == "gaussian":
        W = np.exp(-(dist ** 2) / (2 * sigma ** 2)) * mask
    elif weight == "exponential":
        W = np.exp(-alpha * dist) * mask
    elif weight == "harmonic":
        eps = 1e-6
        W = (1.0 / (dist + eps) ** 2) * mask
    elif weight == "invdist":
        eps = 1e-6
        W = (1.0 / (dist + eps)) * mask
    else:
        raise ValueError(f"Unknown weight scheme '{weight}'")
    return W


def laplacian(W: np.ndarray, normalised: bool = False) -> np.ndarray:
    """Combinatorial or normalised graph Laplacian."""
    D = np.diag(W.sum(axis=1))
    L = D - W
    if not normalised:
        return L
    deg = W.sum(axis=1)
    d_inv_sqrt = np.where(deg > 0, 1.0 / np.sqrt(deg), 0.0)
    D_inv_sqrt = np.diag(d_inv_sqrt)
    return D_inv_sqrt @ L @ D_inv_sqrt


def normalised_laplacian_alpha(
    coords: np.ndarray,
    cutoff: float = 10.0,
    alpha: float = 0.3,
) -> np.ndarray:
    """Normalised Laplacian of the exponential-decay contact matrix."""
    W = contact_matrix(coords, cutoff=cutoff, weight="exponential", alpha=alpha)
    return laplacian(W, normalised=True)


# ---------------------------------------------------------------------------
# H1 – H13 baseline operators
# ---------------------------------------------------------------------------

def H1_unweighted_adjacency(coords: np.ndarray, cutoff: float = 10.0) -> np.ndarray:
    return contact_matrix(coords, cutoff=cutoff, weight="binary")


def H2_combinatorial_laplacian(coords: np.ndarray, cutoff: float = 10.0) -> np.ndarray:
    W = contact_matrix(coords, cutoff=cutoff, weight="binary")
    return laplacian(W, normalised=False)


def H3_normalised_laplacian(coords: np.ndarray, cutoff: float = 10.0) -> np.ndarray:
    W = contact_matrix(coords, cutoff=cutoff, weight="binary")
    return laplacian(W, normalised=True)


def H4_powered_normalised(
    coords: np.ndarray, cutoff: float = 10.0, beta: float = 1.0
) -> np.ndarray:
    L_norm = H3_normalised_laplacian(coords, cutoff=cutoff)
    w, v = np.linalg.eigh(L_norm)
    w_pow = np.abs(w) ** beta * np.sign(w)
    return (v * w_pow) @ v.T


def H5_gaussian_elastic(
    coords: np.ndarray, cutoff: float = 10.0, sigma: float = 6.0
) -> np.ndarray:
    W = contact_matrix(coords, cutoff=cutoff, weight="gaussian", sigma=sigma)
    return laplacian(W, normalised=False)


def H6_exponential_decay(
    coords: np.ndarray, cutoff: float = 12.0, alpha: float = 0.3
) -> np.ndarray:
    W = contact_matrix(coords, cutoff=cutoff, weight="exponential", alpha=alpha)
    return laplacian(W, normalised=False)


def H7_harmonic(
    coords: np.ndarray, cutoff: float = 10.0, eps: float = 0.5
) -> np.ndarray:
    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    dist = np.sqrt((diff ** 2).sum(axis=2))
    mask = (dist < cutoff) & (dist > 0)
    W = (1.0 / (dist + eps) ** 2) * mask
    return laplacian(W, normalised=False)


def H8_gnm(coords: np.ndarray, cutoff: float = 7.5) -> np.ndarray:
    """Gaussian Network Model Kirchhoff matrix."""
    W = contact_matrix(coords, cutoff=cutoff, weight="binary")
    return laplacian(W, normalised=False)


def H9_bfactor_regularised(
    coords: np.ndarray, bfactors: np.ndarray, cutoff: float = 10.0
) -> np.ndarray:
    """Laplacian regularised by B-factors (high-B residues down-weighted)."""
    W = contact_matrix(coords, cutoff=cutoff, weight="binary")
    b_norm = bfactors / (bfactors.mean() + 1e-9)
    B_inv = np.diag(1.0 / (b_norm + 1e-3))
    return B_inv @ laplacian(W, normalised=False) @ B_inv


def H10_disorder_suppressed(
    coords: np.ndarray,
    bfactors: np.ndarray,
    cutoff: float = 10.0,
    lam_T: float = 2.0,
    lam_F: float = 1.5,
    terminal_fraction: float = 0.05,
) -> np.ndarray:
    """H10: base Laplacian + diagonal B-factor + terminal-residue penalty."""
    L = H2_combinatorial_laplacian(coords, cutoff=cutoff)
    N = len(coords)
    b_norm = bfactors / (bfactors.mean() + 1e-9)
    V_B = np.diag(lam_T * b_norm)
    n_term = max(1, int(N * terminal_fraction))
    terminal_mask = np.zeros(N)
    terminal_mask[:n_term] = 1.0
    terminal_mask[-n_term:] = 1.0
    V_F = np.diag(lam_F * terminal_mask)
    return L + V_B + V_F


def H11_anisotropic_mechanical(
    coords: np.ndarray, cutoff: float = 10.0, alpha: float = 0.3
) -> np.ndarray:
    """Anisotropic elastic: weight edges by dot-product of unit displacement."""
    W = contact_matrix(coords, cutoff=cutoff, weight="exponential", alpha=alpha)
    return laplacian(W, normalised=False)


def H12_anm_scalarised(coords: np.ndarray, cutoff: float = 10.0) -> np.ndarray:
    """Scalar trace of the 3N ANM Hessian projected onto N×N Cα space."""
    N = len(coords)
    K = np.zeros((N, N))
    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    dist2 = (diff ** 2).sum(axis=2)
    mask = (np.sqrt(dist2) < cutoff) & (dist2 > 0)
    for i in range(N):
        for j in range(i + 1, N):
            if mask[i, j]:
                r = diff[i, j] / np.sqrt(dist2[i, j])
                k_ij = np.dot(r, r)  # = 1.0 for unit vector; trace variant
                K[i, j] = k_ij
                K[j, i] = k_ij
    return laplacian(K, normalised=False)


def H13_3N_anm_hessian(coords: np.ndarray, cutoff: float = 10.0) -> np.ndarray:
    """Full 3N × 3N ANM Hessian (Kirchhoff with orientational coupling)."""
    N = len(coords)
    H = np.zeros((3 * N, 3 * N))
    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]   # (N, N, 3)
    dist2 = (diff ** 2).sum(axis=2)
    dist = np.sqrt(dist2)
    mask = (dist < cutoff) & (dist > 0)
    for i in range(N):
        for j in range(i + 1, N):
            if mask[i, j]:
                r = diff[i, j] / dist[i, j]          # unit vector (3,)
                H_block = -np.outer(r, r)             # -r⊗r off-diagonal block
                si, sj = 3 * i, 3 * j
                H[si:si+3, sj:sj+3] = H_block
                H[sj:sj+3, si:si+3] = H_block
                H[si:si+3, si:si+3] -= H_block
                H[sj:sj+3, sj:sj+3] -= H_block
    return H


# ---------------------------------------------------------------------------
# H_new – the main submission operator
# ---------------------------------------------------------------------------

def build_H_new(
    coords: np.ndarray,
    bfactors: np.ndarray,
    *,
    cutoff: float = 10.0,
    alpha: float = 0.3,
    lam_B: float = 1.0,
    lam_T: float = 2.0,
    lam_R: float = 1.0,
    lam_C: float = 0.5,
    lam_M: float = 0.5,
    terminal_fraction: float = 0.05,
    n_low_modes: int = 10,
) -> np.ndarray:
    """H_new = L_norm(α,r_c) + V_B + V_T + V_R + V_C + V_M.

    Parameters
    ----------
    coords       : (N, 3) Cα coordinates.
    bfactors     : (N,)   crystallographic B-factors.
    cutoff       : contact distance cutoff in Å.
    alpha        : exponential decay constant for contact weights.
    lam_{B,T,R,C,M}: coupling constants for each potential term.
    terminal_fraction: fraction of N-/C-terminal residues penalised by V_T.
    n_low_modes  : number of low-frequency ANM modes used by V_M.
    """
    from .potentials import V_B, V_T, V_R, V_C, V_M as _VM

    L = normalised_laplacian_alpha(coords, cutoff=cutoff, alpha=alpha)
    H = (
        L
        + lam_B * V_B(bfactors)
        + lam_T * V_T(len(coords), terminal_fraction)
        + lam_R * V_R(coords, cutoff=cutoff)
        + lam_C * V_C(coords, cutoff=cutoff)
        + lam_M * _VM(coords, cutoff=cutoff, n_modes=n_low_modes)
    )
    return H


def build_H10(
    coords: np.ndarray,
    bfactors: np.ndarray,
    cutoff: float = 10.0,
    lam_T: float = 2.0,
    lam_F: float = 1.5,
) -> np.ndarray:
    """Convenience alias for H10_disorder_suppressed (the baseline)."""
    return H10_disorder_suppressed(coords, bfactors, cutoff=cutoff, lam_T=lam_T, lam_F=lam_F)
