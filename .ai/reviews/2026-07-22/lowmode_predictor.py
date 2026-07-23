"""Low-mode (slow-mode) allosteric predictors — the observable the
learnability gate points at but which was never scored as a *predictor*.

Rationale (REVIEW-panel-2026-07-17 action #4, RESULTS.md row 17): the
apo->holo displacement lives in ~20 soft ANM modes (CO(20)=0.58-0.79),
while the CTQW seed-occupation observable integrates over all N modes,
where the fast/localized modes carry the proximity confound this project
has documented (metrics ~0.85-0.97 Spearman vs graph-hop). These functions
restrict the observable to the slow-mode subspace so that a residue scores
high for *collective dynamic coupling to the seed*, not for being nearby.

Two observables, both apo-only, both proximity-orthogonal by construction:

  prs_low   : low-mode Perturbation Response Scanning (Atilgan 2009 / Ikeguchi
              2005 LRT). Response of residue j to a force at the seed,
              computed from the ANM pseudo-inverse restricted to the k
              lowest non-trivial modes.
  dcc_low   : low-mode GNM dynamic cross-correlation magnitude between the
              seed and residue j (communication through slow collective
              modes).

Neither imports the CTQW propagator family; they are an independent
observable, not a re-parameterization of the confounded one. Uses
`superpose.anm_modes` and `potentials._kirchhoff_eigh` (this package's own,
already-tested ANM/GNM primitives) rather than re-deriving either.
"""
from __future__ import annotations

import numpy as np

from .superpose import anm_modes
from .potentials import _kirchhoff_eigh


def _source_idx(source) -> np.ndarray:
    return np.atleast_1d(np.asarray(source, dtype=int))


def prs_low(
    coords: np.ndarray,
    source,
    *,
    cutoff: float = 10.0,
    k_modes: int = 20,
) -> np.ndarray:
    """Low-mode Perturbation Response Scanning score, (N,).

    Builds the ANM pseudo-inverse from the k lowest non-trivial modes only:
        Hinv_k = sum_{i<=k} (1/w_i) v_i v_i^T           (3N x 3N)
    The response of residue j to an isotropic unit force at seed residue s is
    the Frobenius norm of the 3x3 (j,s) block of Hinv_k; summed over all seed
    residues. Higher = more dynamically responsive to a perturbation at the
    seed, *through the slow collective modes*.

    A directional (seed-anchored), low-mode-restricted quantity: unlike a
    walk seeded at a point, its magnitude is governed by mode participation,
    not by graph-hop distance — which is exactly the property under test.
    """
    idx = _source_idx(source)
    w, v = anm_modes(coords, cutoff=cutoff, n_modes=k_modes)   # v: (3N, k)
    n = coords.shape[0]
    # Hinv_k without forming the full 3N x 3N matrix: response block (j,s)
    # = sum_i (1/w_i) V_i[j-block] outer V_i[s-block].
    inv_w = 1.0 / w                                            # (k,)
    V = v * np.sqrt(inv_w)[None, :]                            # (3N, k), folds 1/w in
    score = np.zeros(n)
    for s in idx:
        Vs = V[3 * s : 3 * s + 3, :]                           # (3, k)
        # block(j,s) = Vj (3xk) @ Vs^T (kx3); ||block||_F^2 = sum over 3x3.
        # ||Vj @ Vs^T||_F^2 = trace( (Vj Vs^T)(Vs Vj^T) ) = trace( Vj (Vs^T Vs) Vj^T )
        M = Vs.T @ Vs                                          # (k, k)
        for j in range(n):
            Vj = V[3 * j : 3 * j + 3, :]                       # (3, k)
            score[j] += float(np.einsum("ak,kl,al->", Vj, M, Vj))
    return score


def dcc_low(
    coords: np.ndarray,
    source,
    *,
    cutoff: float = 10.0,
    k_modes: int = 20,
) -> np.ndarray:
    """Low-mode GNM dynamic cross-correlation magnitude to the seed, (N,).

    |sum_{i<=k} (1/lam_i) u_i(s) u_i(j)| averaged over seed residues s, using
    the scalar GNM Kirchhoff's lowest k non-zero modes. Communication through
    slow collective fluctuations; sign discarded (a strongly anti-correlated
    distal domain is as much a communication partner as a co-moving one).
    """
    idx = _source_idx(source)
    _A, w, U, nz, _winv = _kirchhoff_eigh(coords, cutoff=cutoff)
    order = np.argsort(w)
    nz_sorted = [o for o in order if nz[o]]
    low = nz_sorted[:k_modes]
    lam = w[low]
    Uk = U[:, low]                                            # (N, k)
    inv_lam = 1.0 / lam
    cov = (Uk * inv_lam[None, :]) @ Uk.T                      # (N, N) low-mode covariance
    d = np.sqrt(np.clip(np.diag(cov), 1e-12, None))
    corr = cov / np.outer(d, d)
    return np.abs(corr[idx, :]).mean(axis=0)
