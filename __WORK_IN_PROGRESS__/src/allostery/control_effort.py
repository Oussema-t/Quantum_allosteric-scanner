"""TASK-0156 -- minimum control-energy reachability scanning.

Ranks residues by the minimum control energy

    E_i = min_u  integral ||u(t)||^2 dt
    s.t. fidelity(psi(T), |i>) >= F, under H(t) = H_0 + sum_m u_m(t) H_m

required to steer population from the active-site seed to residue `i`
within a fixed horizon `T`, rather than by where the *uncontrolled* walk
deposits probability. `H_0` is this project's existing operator
(`hamiltonians.build_H_new`); `H_m` are local node-potential shifts
(diagonal, single-site energy detuning). This is a standard minimum-
energy optimal-control problem (GRAPE: Khaneja, Reiss, Kehlet,
Schulte-Herbruggen, Glaser 2005, J. Magn. Reson. 172, 296-305,
DOI 10.1016/j.jmr.2004.11.004 -- verified against the live article before
implementing, see the task file's own Done section), solved here via a
one-sided (hinge) fidelity penalty rather than GRAPE's original
unconstrained-fidelity-maximization objective, since the quantity wanted
here is minimum energy at a *fixed* fidelity floor, not maximum fidelity
at fixed energy.

## Why this task exists (see TASK-0156's own "Correction" section)

The original request ("use control to reduce CTQW trapping, then read
where probability lands") is not well-posed: destructive interference is
not gauge-invariant (Correction #1), and a control field strong enough to
redirect population anywhere makes the final state reflect the control,
not the protein (Correction #2, the "controllability paradox" --
Albertini & D'Alessandro 2012, Math. Control Signals Syst. 24, 321-349,
DOI 10.1007/s00498-012-0084-0 -- **verification note**: that paper's own
scope is *discrete-time coined* quantum walks, not the continuous-time
Hamiltonian control `H(t) = H_0 + sum_m u_m(t) H_m` used here; the
qualitative claim it is cited for ("a sufficiently connected/controllable
system can be driven to any reachable state") is nonetheless correct for
continuous-time bilinear quantum control via the standard dynamical-Lie-
algebra controllability theorem (Schirmer/Solomon/Leahy-family results,
a different and more standard citation for this exact setting) -- flagged
here rather than silently treated as a scope match, per this project's
citation-verification discipline).

The reformulation that survives both objections: do not use control to
*improve* the walk. Read out the *cost of control itself*. The control
field never sees any label; `E_i` is computed identically, blind, for
every candidate residue -- non-circular by construction.

## Control-operator set (Implementer's call, TASK-0156's own Open Question)

Local node-potential shifts restricted to the **active-site seed
residues only** -- not all N residues, and not coupling (edge) modulation.
Three reasons, stated explicitly per this project's convention:

1. **Physically motivated.** "Steer population *from* the seed" reads
   naturally as modulating the field strength *at the point of
   stimulation*, not at arbitrary distal nodes the walk has not reached
   yet.
2. **Tractable.** `n_controls = |seed|` (5-26 residues across this
   project's benchmark set) rather than N (169-704) -- makes a per-
   residue optimization over all N candidate targets, on all 3 mandatory
   targets, computationally feasible in-session.
3. **Strengthens the controllability-paradox defense.** A handful of
   control channels concentrated only at the seed is a far weaker
   "can this field reach anywhere" claim than N independent full-graph
   channels would be -- a low `E_i` under this restricted control set is
   a more convincing coupling signal, not an artifact of overwhelming
   control power.

## Horizon: finite T, not the converged/infinite-time limit

Unlike this project's other propagator-based observables (which use the
`t -> infinity` converged limit, TASK-0130), a converged-limit control
problem does not make sense here: given unbounded time, even an
infinitesimal sustained control field can eventually reach any connected
node, which would defeat the entire point of measuring a *cost*. `T` is a
fixed, stated, finite horizon (Implementer's call, TASK-0156's other Open
Question) -- ranking sensitivity to `T` (and to `F`) is checked directly,
per the task's own Constraint ("a ranking that flips with T is not a
measurement").

Single-excitation subspace, real symmetric `H_0` -- the same subspace
this project's CTQW propagators already operate in. Classically
simulable; no quantum-speedup claim (a positive result here is a better
*observable*, not evidence of a quantum advantage -- stated explicitly
wherever this module's results are reported, per the task file's own
Report constraint).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _free_propagator(H0: np.ndarray, dt: float) -> np.ndarray:
    """One-Trotter-slice free-evolution propagator `P = exp(-i H0 dt)`,
    built once via eigendecomposition of `H0` (fixed across every target
    residue and every gradient-descent iteration -- this is the only
    O(N^3) operation in the whole module, done exactly once)."""
    w, v = np.linalg.eigh(H0)
    phase = np.exp(-1j * w * dt)
    return (v * phase[None, :]) @ v.T


def _seed_state(n: int, source: np.ndarray) -> np.ndarray:
    """Equal-amplitude coherent superposition over `source`, matching
    `propagators._quantum_initial_coeffs`'s own convention exactly (same
    normalization, not re-derived)."""
    psi0 = np.zeros(n, dtype=complex)
    psi0[source] = 1.0 / np.sqrt(len(source))
    return psi0


@dataclass
class ControlEffortResult:
    """Per-residue minimum-control-energy scan result, (N,) arrays."""

    energy: np.ndarray
    fidelity: np.ndarray
    feasible: np.ndarray  # bool -- achieved fidelity >= F - tol within the iteration budget
    horizon_T: float
    n_slices: int
    fidelity_target: float
    penalty_weight: float
    control_indices: np.ndarray


def _forward_backward(
    u: np.ndarray, psi0: np.ndarray, P: np.ndarray, control_idx: np.ndarray,
    target_idx: np.ndarray, dt: float,
):
    """Batched forward/backward GRAPE pass -- one target residue per row
    of the batch dimension, all sharing the same free propagator `P`.

    Returns `(fidelity, grad_fidelity)`: `fidelity` is (T,) real,
    `grad_fidelity` is (T, K, n_controls) real, the analytic gradient of
    fidelity w.r.t. each control amplitude (first-order GRAPE gradient,
    Khaneja et al. 2005 eq. 19-family; exact for the piecewise-constant
    control this module uses, not a finite-difference approximation).
    """
    n_targets, n_slices, n_controls = u.shape
    n = P.shape[0]

    psi = np.tile(psi0[None, :], (n_targets, 1))
    psi_list = []
    for k in range(n_slices):
        psi_list.append(psi)
        c = np.exp(-1j * u[:, k, :] * dt)
        full_diag = np.ones((n_targets, n), dtype=complex)
        full_diag[:, control_idx] = c
        psi = (psi * full_diag) @ P.T

    rows = np.arange(n_targets)
    a = psi[rows, target_idx]
    fidelity = np.abs(a) ** 2

    lam = np.zeros((n_targets, n), dtype=complex)
    lam[rows, target_idx] = 1.0
    conj_a = np.conj(a)
    P_conj = np.conj(P)

    grad = np.zeros_like(u)
    for k in range(n_slices - 1, -1, -1):
        c = np.exp(-1j * u[:, k, :] * dt)
        full_diag = np.ones((n_targets, n), dtype=complex)
        full_diag[:, control_idx] = c

        mu = lam @ P_conj
        psi_before = psi_list[k]

        mu_ctrl = mu[:, control_idx]
        psi_ctrl = psi_before[:, control_idx]
        term = conj_a[:, None] * c * psi_ctrl * np.conj(mu_ctrl)
        grad[:, k, :] = 2.0 * dt * np.imag(term)

        lam = np.conj(full_diag) * mu

    return fidelity, grad


def scan_control_effort(
    H0: np.ndarray,
    source,
    *,
    T: float = 15.0,
    n_slices: int = 24,
    fidelity_target: float = 0.5,
    penalty_weight: float = 400.0,
    n_iters: int = 300,
    lr: float = 0.05,
    fidelity_tol: float = 0.02,
    target_indices=None,
    chunk_size: int = 200,
    seed: int = 0,
) -> ControlEffortResult:
    """Minimum control-energy scan: for every residue in `target_indices`
    (default: all N), find `u(t)` minimizing `integral ||u||^2 dt` subject
    to `fidelity(psi(T), |i>) >= fidelity_target`, control channels
    restricted to `source` (the active-site seed, see module docstring).

    Solved as a single gradient-descent run per target on the hinge
    objective `J(u) = E(u) + penalty_weight * max(0, F_target - F(u))^2`
    (not GRAPE's original unconstrained-fidelity-maximization objective,
    and not a bisection/continuation search over `penalty_weight` --
    the hinge's own gradient structure already does the right thing:
    once `F(u) >= F_target`, the penalty term and its gradient vanish and
    only the pure energy-minimization gradient remains, driving `u`
    toward the lowest-energy point *on* the feasible boundary, without a
    per-target bisection state machine). `penalty_weight` is fixed once,
    identically for every residue -- calibrated on the synthetic dumbbell
    gate (see the task file's Done section for the calibration run), not
    per-target-tuned.

    All N target residues (or `target_indices` if given) are optimized in
    one shared computational graph (batched `(n_targets, n_slices,
    n_controls)` control tensor), processed in `chunk_size`-sized chunks
    to bound peak memory on the largest targets (CARDIAC_MYOSIN, N=704).

    Residues that never reach `fidelity_target - fidelity_tol` within the
    iteration budget are marked `feasible=False` with the energy at
    whatever fidelity was actually reached -- reported as infeasible-at-
    this-(T,F), never silently treated as a valid low-energy result.
    """
    H0 = np.asarray(H0, dtype=float)
    n = H0.shape[0]
    source_idx = np.atleast_1d(np.asarray(source, dtype=int))
    control_idx = np.sort(np.unique(source_idx))
    n_controls = len(control_idx)
    dt = T / n_slices

    if target_indices is None:
        target_indices = np.arange(n)
    target_indices = np.asarray(target_indices, dtype=int)
    n_targets = len(target_indices)

    P = _free_propagator(H0, dt)
    psi0 = _seed_state(n, source_idx)

    rng = np.random.default_rng(seed)
    energy_out = np.full(n_targets, np.nan)
    fidelity_out = np.full(n_targets, np.nan)
    feasible_out = np.zeros(n_targets, dtype=bool)

    for start in range(0, n_targets, chunk_size):
        chunk_targets = target_indices[start : start + chunk_size]
        m = len(chunk_targets)
        u = 0.01 * rng.standard_normal((m, n_slices, n_controls))

        # Adam (Kingma & Ba 2015) rather than plain gradient descent: the
        # hinge objective's landscape (energy term pulling toward u=0,
        # penalty term pulling toward high fidelity, switching on/off
        # sharply at the fidelity_target boundary) makes plain fixed-lr
        # GD oscillate rather than converge -- confirmed directly by
        # instrumenting per-iteration fidelity/energy on a real target
        # before switching optimizers (see the task file's own Done
        # section for the diagnostic run). Adam's per-parameter adaptive
        # step size damps exactly this kind of oscillation.
        m1 = np.zeros_like(u)
        v1 = np.zeros_like(u)
        beta1, beta2, adam_eps = 0.9, 0.999, 1e-8
        for it in range(1, n_iters + 1):
            fidelity, grad_f = _forward_backward(u, psi0, P, control_idx, chunk_targets, dt)
            shortfall = np.clip(fidelity_target - fidelity, 0.0, None)
            grad_energy = 2.0 * u * dt
            grad_penalty = -2.0 * penalty_weight * shortfall[:, None, None] * grad_f
            grad_total = grad_energy + grad_penalty

            m1 = beta1 * m1 + (1 - beta1) * grad_total
            v1 = beta2 * v1 + (1 - beta2) * grad_total ** 2
            m_hat = m1 / (1 - beta1 ** it)
            v_hat = v1 / (1 - beta2 ** it)
            u = u - lr * m_hat / (np.sqrt(v_hat) + adam_eps)

        fidelity, _ = _forward_backward(u, psi0, P, control_idx, chunk_targets, dt)
        energy = (u ** 2).sum(axis=(1, 2)) * dt
        feasible = fidelity >= (fidelity_target - fidelity_tol)

        sl = slice(start, start + m)
        energy_out[sl] = energy
        fidelity_out[sl] = fidelity
        feasible_out[sl] = feasible

    energy_reported = np.where(feasible_out, energy_out, np.nan)

    return ControlEffortResult(
        energy=energy_reported,
        fidelity=fidelity_out,
        feasible=feasible_out,
        horizon_T=T,
        n_slices=n_slices,
        fidelity_target=fidelity_target,
        penalty_weight=penalty_weight,
        control_indices=control_idx,
    )


def control_effort_score(result: ControlEffortResult) -> np.ndarray:
    """Convert a `ControlEffortResult` into a ranking score where HIGHER
    = MORE likely allosteric, matching every other observable's ranking
    convention in this project (`metrics.auc` etc. expect "high score =
    positive class"). `E_i` itself is a cost (lower = more strongly
    coupled), so the score is `-E_i` for feasible residues; infeasible
    residues (never reached `fidelity_target` within the iteration
    budget) get the worst possible score (more negative than any finite
    `-E_i`), reflecting that "could not reach it even at maximum control
    effort" is the strongest possible *negative* evidence, not a missing
    value to impute or drop -- dropping them would silently discard
    exactly the residues this method finds least coupled, biasing any
    downstream AUC upward.
    """
    energy = result.energy
    finite = energy[result.feasible]
    worst = -(finite.max() * 2.0 + 1.0) if finite.size else -1.0
    return np.where(result.feasible, -energy, worst)
