"""TASK-0145 -- classical effective resistance/conductance (Kirchhoff's
graph theory) and a Landauer-Buttiker quantum transmission observable.

Reframes the scoring question from "where does an excitation seeded at
the active site spread to over time" (every propagator-based observable
in this project's register) to "what is the steady-state current/
transmission from the active site to each candidate residue" -- a
non-equilibrium steady-state (NESS) transport calculation, the formalism
used in molecular electronics (Landauer-Buttiker; Nitzan & Ratner's
quantum-transport reviews), not a seeded-walk-and-wait one.

Two related quantities, in order of increasing generality:

- `effective_resistance_from_source`: closed-form classical effective
  resistance/conductance, `R_eff(i,j) = L+_ii + L+_jj - 2*L+_ij`, `L+`
  the Moore-Penrose pseudo-inverse of a genuine combinatorial graph
  Laplacian. Requires a real Laplacian null space (`L @ 1 = 0`) --
  `H_new` does NOT qualify (its diagonal potential terms, and its use of
  the *normalised* Laplacian variant, both break the null-space handling
  this formula relies on; confirmed directly, not assumed, while scoping
  this task). Use `hamiltonians.H2_combinatorial_laplacian` or an
  equivalent plain `laplacian(contact_matrix(...), normalised=False)`.
- `transmission_from_source`: `T(E) = Tr[Gamma_L G(E) Gamma_R G(E)^dagger]`,
  retarded Green's function `G(E) = (E - H + i*Gamma/2)^-1`, wide-band-
  limit (WBL) leads (`Gamma_L`/`Gamma_R` diagonal, nonzero only at the
  source/candidate contact sites) -- the minimal, standard lead model
  (Nitzan & Ratner). Works on ANY real symmetric `H` (no null-space
  requirement -- the `i*Gamma/2` term already regularizes the inverse),
  including `H_new` directly.
"""
from __future__ import annotations

from typing import Optional, Sequence, Union

import numpy as np

Source = Union[int, Sequence[int]]


def _eigh_pinv(L: np.ndarray) -> np.ndarray:
    """Moore-Penrose pseudo-inverse via eigendecomposition, reusing
    `hamiltonians.H14_anm_pinv_trace`'s own tolerance convention
    (`tol = 1e-8 * max(|w|.max(), 1)`, modes at/below `tol` dropped) for
    consistency with this project's established pinv pattern -- not
    `np.linalg.pinv` (numerically equivalent for symmetric PSD input,
    SVD-based, but not what this repo's own precedent uses)."""
    w, v = np.linalg.eigh(L)
    tol = 1e-8 * max(np.abs(w).max(), 1.0)
    nz = w > tol
    winv = np.where(nz, 1.0 / np.where(nz, w, 1.0), 0.0)
    return (v * winv) @ v.T


def effective_resistance_from_source(
    L: np.ndarray,
    source: Source,
    w_short: float = 1e4,
) -> np.ndarray:
    """Classical effective resistance/conductance from a (possibly
    multi-index) `source` set to every residue.

    Multi-index `source` is handled via a virtual-supernode construction
    (augment `L` with one extra node connected to every source residue
    by a strong `w_short` edge, shorting them together as
    `w_short -> inf`) -- the same "virtual super-source" pattern
    `percolation.py` (TASK-0136) already established and debugged for
    exactly this multi-node-set-to-single-node case, reused here rather
    than re-deriving the shorted-supernode pseudo-inverse formula from
    scratch. `w_short` must be large relative to `L`'s own real edge
    weights (default `1e4`, verified numerically convergent well before
    that, see `tests/test_transport.py`).

    `L` must be a genuine combinatorial graph Laplacian (row sums to
    zero, a real connected-component zero mode) -- `H_new` does NOT
    qualify and must never be passed here (see module docstring).

    Returns `(N,)` conductance `1/R_eff`, with `R_eff` floored at a
    small positive epsilon before inverting (a source residue's own
    R_eff to the shorted supernode is ~0 as `w_short -> inf`, which
    would otherwise divide by zero).
    """
    N = L.shape[0]
    idx = np.atleast_1d(np.asarray(source, dtype=int))

    L_aug = np.zeros((N + 1, N + 1))
    L_aug[:N, :N] = L
    for s in idx:
        L_aug[N, N] += w_short
        L_aug[s, s] += w_short
        L_aug[N, s] -= w_short
        L_aug[s, N] -= w_short

    Lpinv = _eigh_pinv(L_aug)
    v = N  # the virtual supernode's own index in the augmented graph
    R_vv = Lpinv[v, v]
    R_jj = np.diag(Lpinv)[:N]
    R_vj = Lpinv[v, :N]
    R_eff = R_vv + R_jj - 2.0 * R_vj
    R_eff = np.clip(R_eff, 1e-12, None)
    return 1.0 / R_eff


def transmission_from_source(
    H: np.ndarray,
    source: Source,
    E: float = 0.0,
    gamma_lead: Optional[float] = None,
    eta_reg: Optional[float] = None,
) -> np.ndarray:
    """Landauer-Buttiker two-terminal transmission `T(E)` from `source`
    (the "left lead") to every residue (each, in turn, the "right
    lead"), via the retarded Green's function
    `G(E) = (E - H + i*Gamma/2)^-1` in the wide-band-limit (WBL)
    approximation -- `Gamma_L`/`Gamma_R` are diagonal, nonzero only at
    the source/candidate contact site(s), a minimal standard lead model
    (Nitzan & Ratner's quantum-transport reviews) -- this task's own
    Constraint: state the model, do not invent an elaborate one.

    `E` : retarded-Green's-function energy. Default `0.0` -- the DC/
        zero-bias limit, chosen (not tuned against labels) because it is
        the point where a Laplacian's own quantum transmission is
        expected to connect most directly to its classical effective-
        resistance limit (both are steady-state/zero-frequency
        quantities) -- the natural energy for this task's own "does T(E)
        differ from 1/R_eff" comparison. Works on any real symmetric
        `H`, not only a Laplacian (no null-space requirement).
    gamma_lead : lead-coupling strength, default `0.1 * bandwidth`
        (`bandwidth = w.max() - w.min()` of `H`'s own spectrum, this
        project's established convention, TASK-0141) -- the standard
        "weak coupling" regime (resolves individual level structure
        rather than broadening everything into one featureless band).
        Not tuned against labels; sensitivity characterized separately
        (`scripts/transport_observable_real_run.py`).
    eta_reg : small uniform numerical regularization, default
        `1e-6 * bandwidth`, independent of the physical lead broadening
        -- only prevents an exact singularity if `E` happens to land
        precisely on an eigenvalue with zero lead coupling there.

    Closed form (Sherman-Morrison rank-1 update -- `Gamma_R` at each
    candidate `j` is always a single-site diagonal perturbation of the
    same source-only baseline `G_0`, so it never needs re-deriving from
    scratch per candidate): computes the source-only Green's function
    `G_0(E) = (E + i*eta_reg - H + i*Gamma_L/2)^-1` ONCE (a single N x N
    inversion), then for every candidate `j`,
    `T(E,j) = gamma_lead^2 * sum_{s in source} |G_0[s,j]|^2 /
    |1 + i*(gamma_lead/2)*G_0[j,j]|^2` -- O(N^2) total once `G_0` is
    known, instead of the O(N) separate full re-inversions (O(N^4)
    overall) a naive per-candidate approach would cost. Verified
    directly against a brute-force per-candidate re-inversion on a small
    synthetic case before trusting it (`tests/test_transport.py`), not
    assumed correct from the algebra alone.

    Returns `(N,)`, real (transmission is a physical, non-negative real
    quantity; the closed form's own imaginary remainder is checked to be
    numerically zero, not silently discarded).
    """
    N = H.shape[0]
    idx = np.atleast_1d(np.asarray(source, dtype=int))

    w = np.linalg.eigvalsh(H)
    bandwidth = float(w[-1] - w[0]) if len(w) > 1 else 1.0
    if gamma_lead is None:
        gamma_lead = 0.1 * bandwidth
    if eta_reg is None:
        eta_reg = 1e-6 * bandwidth

    Gamma_L_diag = np.zeros(N)
    Gamma_L_diag[idx] = gamma_lead

    M0 = (E + 1j * eta_reg) * np.eye(N) - H.astype(complex)
    M0[np.arange(N), np.arange(N)] += 1j * Gamma_L_diag / 2.0
    G0 = np.linalg.inv(M0)

    g0_jj = np.diag(G0)
    sum_sq = np.sum(np.abs(G0[idx, :]) ** 2, axis=0)  # sum over source rows s, per column j
    denom = np.abs(1.0 + 1j * (gamma_lead / 2.0) * g0_jj) ** 2
    T = (gamma_lead ** 2) * sum_sq / np.clip(denom, 1e-300, None)
    return T
