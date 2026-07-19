"""TASK-0132 -- GNM-based transfer entropy, a published classical baseline
for allosteric-site detection (no MD, no quantum), independent of this
project's own CTQW/H_new operator family.

Citations checked directly against PubMed before implementing (not
assumed from the review's one-line summary that filed this task):

- Hacisuleyman & Erman, *Proteins* 85(6):1056-1064 (2017), PMID 28241380
  -- "Causality, transfer entropy, and allosteric communication
  landscapes in proteins with harmonic interactions." Confirms: combines
  Schreiber's transfer-entropy concept with the Gaussian Network Model
  (GNM/"dGNM"); directional causal-flow signal from harmonic (contact-
  topology) interactions alone, no MD trajectory needed.
- **Correction to the filing task's own citation**: PMID 35644497
  ("Subsets of Slow Dynamic Modes Reveal Global Information Sources as
  Allosteric Sites," *J Mol Biol* 434(17), 2022) is real and matches the
  claimed method (GNM+TE over slow-mode subsets, a "TECol" collectivity
  score, a 20-protein benchmark recovering known allosteric/active
  sites) -- but its authors are **Altintel, Acar, Erman, Haliloglu**, not
  "Kaynak & Bahar" as the task file states. Flagged, not silently
  corrected in the task file's own Context (historical record); this
  module's own citation is the verified one.

Exact closed-form used (this task's own required disclosure -- several
transfer-entropy formulations exist in the literature, the review's
one-line summary is not a full method spec): the linear-Gaussian
transfer entropy / Granger-causality equivalence (Barnett, Barrett &
Seth, *Phys. Rev. Lett.* 103:238701, 2009): for jointly Gaussian
variables, T_{Y->X} = 0.5*ln(Sigma_X / Sigma_{X|Y}), where Sigma_X is the
residual variance predicting X's future from X's own past alone, and
Sigma_{X|Y} is the residual variance predicting X's future from both X's
and Y's past. GNM fluctuations are exactly multivariate Gaussian by
construction, so this exact closed form applies directly -- no histogram-
based Shannon-entropy estimation (the MD-trajectory papers' own
approach, e.g. the earlier Hacisuleyman/Erman *PLOS Comput Biol* 2017
paper) is needed.

The GNM time-lagged covariance function C_ij(tau) = Cov(R_i(t+tau),
R_j(t)) for the overdamped Langevin/Ornstein-Uhlenbeck GNM dynamics is
C(tau) = U @ diag(exp(-w*tau)/w) @ U.T (w, U from the Kirchhoff
eigendecomposition, zero mode excluded) -- reduces to the existing
`potentials._normalized_dcc`'s own static covariance at tau=0, confirming
consistency with what this codebase already computes.

**A genuine subtlety worked out here, not assumed**: for the pure
(reversible, detailed-balance) GNM Langevin process, C_ij(tau) =
C_ji(tau) exactly (the lagged covariance matrix is symmetric -- provable
directly from the eigendecomposition, since it is a sum of symmetric
rank-1 terms u_k u_k^T). This means the *cross-term* alone carries no
directional information for this process -- unlike an MD trajectory's
empirically-estimated correlations, which can pick up genuine asymmetry
from nonlinear/non-Markovian effects the linear GNM does not have.
Directionality in T_{Y->X} vs. T_{X->Y} survives anyway, because the two
formulas use *different self-prediction baselines* (Sigma_X depends on
residue X's own marginal relaxation properties, Sigma_Y on residue Y's,
generally different) -- confirmed numerically, not just derived on paper,
before trusting this on real data (see `tests/test_transfer_entropy.py`).
"""
from __future__ import annotations

import numpy as np


def _gnm_lagged_covariance(w: np.ndarray, U: np.ndarray, tau: float) -> np.ndarray:
    """C(tau) = U @ diag(exp(-w*tau)/w) @ U.T, zero mode already excluded
    from `w`/`U` (matches `potentials._kirchhoff_eigh`'s own `nz`-masked
    convention). `tau=0` reduces to the Kirchhoff pseudo-inverse
    (`potentials._normalized_dcc`'s own un-normalized covariance)."""
    decay = np.exp(-w * tau) / w
    return (U * decay) @ U.T


def gnm_relaxation_time(coords: np.ndarray, cutoff: float = 10.0) -> float:
    """tau* = 1/gap, the slowest non-trivial GNM mode's relaxation time --
    this module's own choice of lag (Open Question, Implementer's call):
    the cited papers do not specify a single universal tau (their MD-
    trajectory-based predecessor uses whatever lag the simulation
    provides; the exact dGNM lag is not accessible from the abstracts
    alone). Chosen to match this project's own established spectral-gap-
    derived-timescale convention (TASK-0109/0119/0130's `t* = 1/gap` for
    the propagator clock) rather than inventing an unrelated rule --
    `gap` here is the GNM Kirchhoff spectrum's own smallest nonzero
    eigenvalue, the network's own slowest relaxation mode.
    """
    from .potentials import _kirchhoff_eigh

    _A, w, _U, nz, _winv = _kirchhoff_eigh(coords, cutoff)
    w_nz = w[nz]
    if len(w_nz) == 0:
        return float("inf")
    return float(1.0 / w_nz.min())


def pairwise_transfer_entropy(coords: np.ndarray, cutoff: float = 10.0, tau: float | None = None) -> np.ndarray:
    """`(N, N)` transfer-entropy matrix `T[i, j] = T_{j->i}` -- information
    flow *from* residue `j` *to* residue `i` (row = receiver, column =
    source; matches this project's own row/column reward convention
    elsewhere, e.g. `potentials.V_C`'s own DCC row-sum-per-residue
    pattern, not re-derived here, followed for consistency).

    `tau`: lag in the GNM's own relaxation-time units; defaults to
    `gnm_relaxation_time` (this module's own choice, see that function's
    docstring).

    Closed form (module docstring): for each ordered pair `(source=j,
    receiver=i)`, builds the 3x3 joint Gaussian covariance of
    `(R_i(t+tau), R_i(t), R_j(t))` from `C(0)` and `C(tau)`, computes the
    Schur-complement residual variances, and returns
    `0.5*ln(Sigma_X / Sigma_X_given_Y)`. Diagonal is set to 0 (no
    self-transfer-entropy; undefined/degenerate for `i == j`).
    """
    from .potentials import _kirchhoff_eigh

    A, w, U, nz, _winv = _kirchhoff_eigh(coords, cutoff)
    w_nz = w[nz]
    U_nz = U[:, nz]
    if tau is None:
        tau = float(1.0 / w_nz.min()) if len(w_nz) else 1.0

    C0 = _gnm_lagged_covariance(w_nz, U_nz, 0.0)
    Ct = _gnm_lagged_covariance(w_nz, U_nz, tau)

    N = C0.shape[0]
    var0 = np.diag(C0)  # C_ii(0) for every residue, reused for every pair

    T = np.zeros((N, N))
    for i in range(N):
        Cii0 = var0[i]
        Ciit = Ct[i, i]
        # Sigma_X: residual variance of R_i(t+tau) predicted from R_i(t) alone.
        sigma_x = Cii0 - (Ciit ** 2) / Cii0
        if sigma_x <= 1e-14:
            continue  # residue i's own future is already ~deterministic from its past
        for j in range(N):
            if i == j:
                continue
            Cjj0 = var0[j]
            Cij0 = C0[i, j]     # Cov(R_i(t), R_j(t))
            Cijt = Ct[i, j]     # Cov(R_i(t+tau), R_j(t))
            # 2x2 predictor covariance [[R_i(t), R_j(t)]] and its inverse
            # (Schur complement of the 3x3 joint covariance of
            # (R_i(t+tau), R_i(t), R_j(t))).
            pred_cov = np.array([[Cii0, Cij0], [Cij0, Cjj0]])
            det = Cii0 * Cjj0 - Cij0 ** 2
            if det <= 1e-14:
                continue  # degenerate predictor covariance (i, j perfectly correlated)
            pred_inv = np.array([[Cjj0, -Cij0], [-Cij0, Cii0]]) / det
            cross = np.array([Ciit, Cijt])
            sigma_xy = Cii0 - cross @ pred_inv @ cross
            if sigma_xy <= 1e-14:
                continue
            # Sigma_{X|Y} must not exceed Sigma_X (conditioning on more
            # information cannot increase residual variance); clip tiny
            # float overshoot rather than letting T go slightly negative.
            sigma_xy = min(sigma_xy, sigma_x)
            T[i, j] = 0.5 * np.log(sigma_x / sigma_xy)
    return T


def transfer_entropy_source_score(coords: np.ndarray, cutoff: float = 10.0, tau: float | None = None) -> np.ndarray:
    """Per-residue "information source strength" -- mean outgoing transfer
    entropy `T_{i->j}` averaged over all receivers `j != i`. High score =
    residue `i` is a strong causal source for the rest of the network's
    dynamics, the natural per-residue ranking for allosteric-site
    detection (matches the review's own framing, "entropy sink-source
    relations," and the 2022 paper's own "global information sources as
    allosteric sites").

    Returns `(N,)`.
    """
    T = pairwise_transfer_entropy(coords, cutoff=cutoff, tau=tau)
    N = T.shape[0]
    # T[i, j] = T_{j->i}; residue i's OUTGOING flow to every other residue
    # k is T_{i->k} = T[k, i] -- the i-th COLUMN, not row.
    outgoing = T.copy()
    np.fill_diagonal(outgoing, 0.0)
    return outgoing.sum(axis=0) / max(N - 1, 1)
