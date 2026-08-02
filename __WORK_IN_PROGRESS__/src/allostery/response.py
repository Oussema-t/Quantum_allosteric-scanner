"""TASK-0178 -- binding-response coupling: the exact Gaussian-network
allosteric coupling free energy, and the distance-normalised specificity
statistic that makes it scoreable.

Physical picture (the orchestrating collaborator's own framing, 2026-07-29):
a ligand binds, the accessible conformational ensemble changes, and the
active site *responds* -- typically losing propensity for its own motion.
This is a response to a constraint, not a propagating signal, which is the
shape every other observable in this register has. For a Gaussian network
with energy `(1/2) x^T K x`, a ligand at site S is a set of added
cross-links `P_S` (mechanically what binding does), and the coupling free
energy between two sites A and B is exact and closed-form:

    ddG(A,B) = F(K+P_A+P_B) - F(K+P_A) - F(K+P_B) + F(K)
    F(K) = (kT/2) ln pdet(K)        [pseudo-determinant: nullspace excluded]

**This is classical** (log-determinants of a Kirchhoff matrix), not a
quantum observable -- see this task's own Open Questions for the honest
framing.

Reciprocity (`ddG` is a mixed second derivative of a free energy, hence
exactly symmetric) is this module's *correctness gate*, not a result to
discover -- see `tests/test_response.py`.

**Raw |ddG| is proximity-confounded** (elastic response decays with
distance) -- never report its AUC as a result. `coupling_specificity`
(shell-normalised residual against `hop`) is the scoreable statistic.

GNM/Kirchhoff only (not ANM/3N) -- a plain connected contact-graph
Laplacian has exactly one zero eigenvalue (the uniform-translation mode),
so the pseudo-determinant is well-conditioned; ANM's 3N Hessian can carry
extra near-machine-precision zeros on floppy multi-chain targets
([[TASK-0128]]), which would make this fragile.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Ligand stiffness -- a bound site is a clique of springs
# ---------------------------------------------------------------------------

def ligand_stiffness(n: int, patch_idx, kappa: float = 1.0) -> np.ndarray:
    """Full-graph (N,N) Laplacian of a complete graph over `patch_idx`,
    scaled by `kappa` -- the mechanical model of a rigid ligand cross-
    linking every pair of residues it contacts.

    Same nullspace as any graph Laplacian (rows sum to zero, the uniform
    vector is always annihilated) -- asserted in tests, not just claimed.
    A complete graph's Laplacian has the closed form `kappa*(m*I - J)` on
    its own `m` nodes (`J` = all-ones); `coupling_profile`'s low-rank
    shortcut relies on this exact structure.
    """
    idx = np.asarray(patch_idx, dtype=int)
    m = len(idx)
    P = np.zeros((n, n))
    if m < 2:
        return P
    for a in idx.tolist():
        for b in idx.tolist():
            if a < b:
                P[a, b] -= kappa
                P[b, a] -= kappa
                P[a, a] += kappa
                P[b, b] += kappa
    return P


# ---------------------------------------------------------------------------
# Pseudo-determinant free energy
# ---------------------------------------------------------------------------

@dataclass
class _Basis:
    """Cached eigendecomposition of one Kirchhoff-like matrix, plus its
    pseudo-log-determinant -- the base every low-rank profile update reuses
    (TASK-0145's own O(N^4)->O(N^2) precedent for this exact pattern)."""

    w: np.ndarray          # (N,) eigenvalues
    V: np.ndarray          # (N,N) eigenvectors
    nz: np.ndarray         # (N,) bool mask, nonzero eigenvalues
    w_nz: np.ndarray       # (r,) nonzero eigenvalues
    V_nz: np.ndarray       # (N,r) corresponding eigenvectors
    logdet: float          # 0.5 * sum(log(w_nz))
    n_zero: int


def _basis(M: np.ndarray, tol_rel: float = 1e-8) -> _Basis:
    """Eigendecompose once; null tolerance derived from the spectrum's own
    scale (TASK-0128's precedent), not a bare `1e-9` -- a plain connected
    GNM Kirchhoff matrix has exactly one near-zero eigenvalue (the uniform
    mode), but a disconnected graph (the zero-coupling gate's own test
    case) has more, and this must detect that correctly rather than assume
    a fixed count."""
    w, V = np.linalg.eigh(M)
    scale = float(np.abs(w).max())
    tol = tol_rel * scale if scale > 0 else tol_rel
    nz = w > tol
    w_nz = w[nz]
    V_nz = V[:, nz]
    logdet = 0.5 * float(np.sum(np.log(w_nz))) if w_nz.size else 0.0
    return _Basis(w=w, V=V, nz=nz, w_nz=w_nz, V_nz=V_nz, logdet=logdet, n_zero=int((~nz).sum()))


def free_energy(K: np.ndarray, tol_rel: float = 1e-8) -> float:
    """`F(K) = (kT/2) ln pdet(K)`, kT=1 -- the pseudo-determinant free
    energy of one Gaussian-network Kirchhoff matrix."""
    return _basis(K, tol_rel=tol_rel).logdet


def coupling_free_energy(
    K: np.ndarray,
    A,
    B,
    kappa: float = 1.0,
    tol_rel: float = 1e-8,
) -> float:
    """`ddG(A,B) = F(K+P_A+P_B) - F(K+P_A) - F(K+P_B) + F(K)` -- the exact
    Gaussian-network allosteric coupling free energy between sites A and B.
    Brute-force (4 full eigendecompositions); `coupling_profile` below is
    the O(N^2)-per-profile shortcut for scanning every candidate site B
    against a fixed A.
    """
    n = len(K)
    PA = ligand_stiffness(n, A, kappa)
    PB = ligand_stiffness(n, B, kappa)
    F_AB = free_energy(K + PA + PB, tol_rel=tol_rel)
    F_A = free_energy(K + PA, tol_rel=tol_rel)
    F_B = free_energy(K + PB, tol_rel=tol_rel)
    F_0 = free_energy(K, tol_rel=tol_rel)
    return F_AB - F_A - F_B + F_0


# ---------------------------------------------------------------------------
# Low-rank profile shortcut (verified against brute force to <1e-10,
# see tests/test_response.py::TestLowRankShortcut)
# ---------------------------------------------------------------------------

def _patch_correction_logdet(basis: _Basis, patch_idx: np.ndarray, kappa: float) -> float:
    """`0.5 * logdet(I_m + L_local @ (U^T basis.pseudo_inverse U))` -- the
    matrix-determinant-lemma correction for adding a clique-of-springs
    patch Laplacian on top of the matrix `basis` was built from, without
    re-diagonalizing. Valid because `basis`'s matrix and the patch
    Laplacian are BOTH graph Laplacians (rows sum to zero), so their sum
    shares exactly `basis`'s own nullspace (adding edges cannot disconnect
    an already-connected graph) -- the generalized matrix-determinant
    lemma for a pseudo-inverse then applies exactly, not approximately.
    """
    m = len(patch_idx)
    L_local = kappa * (m * np.eye(m) - np.ones((m, m)))
    Vp = basis.V_nz[patch_idx, :]           # (m, r)
    Gamma = (Vp / basis.w_nz) @ Vp.T        # (m, m) == U^T @ pinv(basis) @ U
    sign, corr = np.linalg.slogdet(np.eye(m) + L_local @ Gamma)
    if sign <= 0:
        raise FloatingPointError(
            f"_patch_correction_logdet: non-positive determinant sign={sign} "
            "-- the rank-update assumption (shared nullspace) has broken down "
            "for this patch; do not trust the result."
        )
    return 0.5 * float(corr)


def coupling_profile(
    K: np.ndarray,
    A,
    coords: np.ndarray,
    kappa: float = 1.0,
    patch_size: int = 6,
    tol_rel: float = 1e-8,
) -> np.ndarray:
    """`ddG(A, patch_j)` for every residue j's own `patch_size`-nearest
    compact patch (same "score every residue by its own local ligand-sized
    neighbourhood" convention as the reference prototype) -- the O(N^2)
    shortcut (two eigendecompositions total, not `2N`), verified against
    brute force to <1e-10 (`tests/test_response.py`).
    """
    n = len(K)
    A_idx = np.asarray(A, dtype=int)
    PA = ligand_stiffness(n, A_idx, kappa)
    M = K + PA
    base_K = _basis(K, tol_rel=tol_rel)
    base_M = _basis(M, tol_rel=tol_rel)

    F0 = base_K.logdet
    FA = base_M.logdet

    diff = coords[:, None, :] - coords[None, :, :]
    dist = np.sqrt((diff ** 2).sum(axis=2))

    out = np.zeros(n)
    for j in range(n):
        patch = np.argsort(dist[j])[:patch_size]
        F_AB = FA + _patch_correction_logdet(base_M, patch, kappa)
        F_B = F0 + _patch_correction_logdet(base_K, patch, kappa)
        out[j] = F_AB - FA - F_B + F0
    return out


# ---------------------------------------------------------------------------
# Active-site rigidification ("loss of propensity")
# ---------------------------------------------------------------------------

def _msf(basis: _Basis, idx: np.ndarray) -> float:
    """Mean GNM mean-square-fluctuation over `idx`, from an already-built
    `_Basis` -- `diag(pinv(M))` restricted to `idx`, averaged."""
    Vp = basis.V_nz[idx, :]
    return float(((Vp ** 2) / basis.w_nz).sum(axis=1).mean())


def active_site_rigidification(
    K: np.ndarray,
    A,
    coords: np.ndarray,
    kappa: float = 1.0,
    patch_size: int = 6,
    tol_rel: float = 1e-8,
) -> np.ndarray:
    """Fractional loss of active-site MSF, `(msf_A(K) - msf_A(K+P_j)) / msf_A(K)`,
    for a ligand-sized patch at every candidate residue j -- the direct
    "loss of propensity" form of the collaborator's own phrasing. Brute
    force per patch (MSF needs a fresh pseudo-inverse each time, no
    matrix-determinant-lemma shortcut applies to a diagonal-sum quantity
    the way it does to a log-determinant) -- `patch_size` residues cheaper
    per call than `coupling_profile`'s log-det route, but still O(N)
    eigendecompositions; kept separate rather than forced through the same
    shortcut.
    """
    n = len(K)
    A_idx = np.asarray(A, dtype=int)
    base = _basis(K, tol_rel=tol_rel)
    base_msf = _msf(base, A_idx)

    diff = coords[:, None, :] - coords[None, :, :]
    dist = np.sqrt((diff ** 2).sum(axis=2))

    out = np.zeros(n)
    for j in range(n):
        patch = np.argsort(dist[j])[:patch_size]
        Pj = ligand_stiffness(n, patch, kappa)
        basis_j = _basis(K + Pj, tol_rel=tol_rel)
        msf_j = _msf(basis_j, A_idx)
        out[j] = (base_msf - msf_j) / base_msf if base_msf else 0.0
    return out


# ---------------------------------------------------------------------------
# Coupling specificity -- the scoreable, distance-normalised statistic
# ---------------------------------------------------------------------------

def coupling_specificity(profile: np.ndarray, hop_distance: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """Shell-normalised residual: `(y_j - mean(y over same hop shell)) /
    (std(y over same hop shell) + eps)`, `y = log10|profile|`.

    Raw coupling magnitude decays with distance (elastic response), so it
    ranks by proximity -- this residual removes the distance trend by
    comparing each residue only to same-hop peers, using ONLY apo-topology
    hop distance (no label information, no leakage). Shells with <=2
    members are left at 0 (undefined residual, not manufactured).
    """
    y = np.log10(np.maximum(np.abs(profile), 1e-18))
    resid = np.zeros_like(y)
    for h in np.unique(hop_distance):
        m = hop_distance == h
        if m.sum() > 2:
            resid[m] = (y[m] - y[m].mean()) / (y[m].std() + eps)
    return resid
