"""Quantum and classical propagators.

All propagators take a Hamiltonian H (N×N, real symmetric) and return an
occupation probability vector p of shape (N,) with p.sum() ≈ 1.

Three propagators (same H, different physics):
  ctqw                   – Continuous-Time Quantum Walk: exp(−iHt), coherent.
  ground_state_relaxation – exp(−Ht) applied to an initial distribution.
                            **Classical diffusion only when H is positive-
                            semidefinite** (e.g. a combinatorial/GNM
                            Laplacian) -- on an indefinite operator (e.g.
                            `H_new`, whose V_R/V_C/V_M terms contribute
                            negative diagonals by design) this is imaginary-
                            time Schrodinger evolution and converges to the
                            operator's ground-state density, not a diffusion
                            process. See TASK-0095 /
                            `REVIEW-2026-07-13-proximity-confound-and-
                            propagator-semantics.md` (finding P1-B): this
                            function was formerly named `heat` and its
                            docstring asserted diffusion semantics
                            unconditionally, which is false for indefinite H
                            -- `Spearman(old-heat(H_new, t=20), |ground
                            state|^2) = 0.998` on real data. Renamed rather
                            than split in two, since the *computation* is
                            identical either way; only the physical
                            interpretation depends on H's spectrum, which is
                            why `_warn_if_indefinite` below makes that
                            dependency visible instead of silent.
  haken_strobl            – Open-system CTQW with dephasing: Lindblad master
                            equation.

The dephasing sweep in Phase 0a tests that AUC is flat across gamma values,
confirming coherence adds nothing beyond topology for these protein graphs.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
from scipy import linalg as sla
from scipy.integrate import solve_ivp

from .hamiltonians import laplacian

Source = Union[int, Sequence[int]]


def _source_indices(source: Source) -> np.ndarray:
    """Normalize a scalar or sequence `source` into a 1-D int index array."""
    return np.atleast_1d(np.asarray(source, dtype=int))


def _quantum_initial_coeffs(v: np.ndarray, source: Source) -> np.ndarray:
    """<v_k | psi0> for a coherent equal-amplitude superposition psi0 over
    `source` index/indices (a scalar reduces to the single-source delta
    state |source>, matching the original single-index formula exactly)."""
    idx = _source_indices(source)
    return v[idx, :].sum(axis=0) / np.sqrt(len(idx))


def _classical_initial_weights(v: np.ndarray, source: Source) -> np.ndarray:
    """<v_k | p0> for a uniform *probability* mass split over `source`
    index/indices (linear in p0, unlike the quantum amplitude case above --
    classical mixtures add probabilities, not amplitudes)."""
    idx = _source_indices(source)
    return v[idx, :].sum(axis=0) / len(idx)


def _ctqw_from_eigh(w: np.ndarray, v: np.ndarray, t: float, source: Source) -> np.ndarray:
    """CTQW occupation at time `t`, given `H`'s already-computed
    eigendecomposition `(w, v)` -- the shared post-`eigh` evolution
    formula `ctqw`/`time_averaged_ctqw` both need (TASK-0111). Computes
    the *coherent* equal-amplitude superposition over `source` (a single
    seed reduces to the same thing trivially) -- see `_ctqw_mixture_
    from_eigh` for the *incoherent* alternative (TASK-0118). Never called
    directly by anything outside this module."""
    coeffs = _quantum_initial_coeffs(v, source)
    amplitudes = v @ (np.exp(-1j * w * t) * coeffs)
    p = np.abs(amplitudes) ** 2
    p /= p.sum() + 1e-300  # normalise against floating-point drift
    return p


def _ctqw_mixture_from_eigh(w: np.ndarray, v: np.ndarray, t: float, source: Source) -> np.ndarray:
    """CTQW occupation at time `t` for an *incoherent* statistical mixture
    over `source`'s indices -- `rho0 = (1/k) * sum_i |i><i|`, physically
    distinct from `_ctqw_from_eigh`'s coherent superposition `psi0 =
    (1/sqrt(k)) * sum_i |i>` (whose density matrix carries off-diagonal
    coherences/relative phase between every pair of seed residues).

    Unitary evolution is linear in the density matrix, so this is exactly
    the average of `k` independent single-seed CTQW occupations -- no new
    eigendecomposition, reuses the shared `(w, v)` the same way
    `_ctqw_from_eigh` does (TASK-0111's caching intact).

    TASK-0118 (REVIEW-panel-2026-07-16-v2 Sec.5 P0-1): a multi-residue
    functional/active site has no biophysical basis for a specific
    relative quantum phase between its residues -- the coherent
    superposition asserts one anyway (an implementation artifact of
    `_quantum_initial_coeffs`'s original single-seed-generalizing
    formula, not a deliberate physical modeling choice). This is the
    "defensible object" the panel review recommends instead. For a
    scalar `source`, identical to `_ctqw_from_eigh` by construction (a
    one-element mixture has no coherence to differ over).
    """
    idx = _source_indices(source)
    return np.mean([_ctqw_from_eigh(w, v, t, int(i)) for i in idx], axis=0)


def ctqw(
    H: np.ndarray,
    t: float,
    source: Source = 0,
    *,
    coherent: bool = True,
) -> np.ndarray:
    """CTQW occupation probabilities at time t, starting from |source⟩.

    p_j(t) = |⟨j| e^{−iHt} |psi0⟩|²

    Parameters
    ----------
    H        : (N, N) real symmetric Hamiltonian.
    t        : propagation time.
    source   : starting node index, or a sequence of indices.
    coherent : `True` (default, unchanged from every prior release) --
               a multi-index `source` is a coherent equal-amplitude
               superposition over those nodes. `False` (TASK-0118) --
               an incoherent statistical mixture instead (`rho0 = (1/k)
               sum_i |i><i|`), the panel-recommended convention for a
               multi-residue seed with no biophysical basis for a
               specific relative phase; see `_ctqw_mixture_from_eigh`.
               Identical output either way for a scalar `source`.

    Returns
    -------
    p : (N,) non-negative array summing to 1.
    """
    w, v = np.linalg.eigh(H)
    if coherent:
        return _ctqw_from_eigh(w, v, t, source)
    return _ctqw_mixture_from_eigh(w, v, t, source)


def _warn_if_indefinite(w: np.ndarray, tol: float, strict: bool, fn_name: str) -> None:
    """Guard for TASK-0095 / REVIEW-2026-07-13 finding P1-B: `exp(-Ht)` is
    classical diffusion only when `H` is positive-semidefinite. Called with
    `H`'s already-computed eigenvalues `w` (never re-decomposes).

    Default (`strict=False`) emits a `UserWarning` rather than raising --
    computing `ground_state_relaxation` on an indefinite H (e.g. `H_new`) is
    a legitimate, deliberate operation (TASK-0091's re-filed question is
    exactly "what does this compute on `H_new`"), so this must not break
    existing callers. What it must never do again is let that computation
    pass *silently* as if it were diffusion -- the loud diagnostic is the
    fix, not a hard block. `strict=True` raises instead, for a call site
    that specifically wants to assert diffusion semantics and treat a
    violation as a bug.
    """
    min_eig = float(w.min())
    if min_eig >= -tol:
        return
    message = (
        f"{fn_name}: H is indefinite (min eigenvalue {min_eig:.3g} < -{tol:.0e}) -- "
        "exp(-Ht) is NOT classical diffusion here, it evolves toward H's "
        "ground-state density (TASK-0095, REVIEW-2026-07-13 finding P1-B). "
        "Do not report this output as a diffusion/classical-heat comparison."
    )
    if strict:
        raise ValueError(message)
    warnings.warn(message, UserWarning, stacklevel=3)


def ground_state_relaxation(
    H: np.ndarray,
    t: float,
    source: Source = 0,
    *,
    strict: bool = False,
    tol: float = 1e-9,
) -> np.ndarray:
    """`exp(-Ht)` applied to an initial distribution over `source`.

    p_j(t) = [e^{−Ht} p0]_j, p0 uniform over `source` index/indices.

    **This is classical diffusion only when `H` is positive-semidefinite**
    (a combinatorial/GNM Laplacian, or any operator with no negative
    eigenvalues). On an indefinite `H` (e.g. `H_new`, whose V_R/V_C/V_M
    potential terms contribute negative diagonals), this converges to the
    density of `H`'s ground state as `t` grows -- a real, well-defined
    quantity, just not a diffusion process. See this module's docstring and
    TASK-0095 for the finding that motivated this name (formerly `heat`,
    which asserted diffusion semantics unconditionally).

    By default, an indefinite `H` triggers a `UserWarning` (`_warn_if_
    indefinite`) rather than silently proceeding -- pass `strict=True` to
    raise instead. Either way the *numeric* output for a genuinely
    positive-semidefinite `H` is unchanged from the original `heat`.

    The result is clipped to non-negative and re-normalised to handle
    floating-point noise (this clipping is what previously masked a
    13-order-of-magnitude L1-norm divergence on indefinite `H` -- the
    warning above is the fix for that, not a change to the clipping itself).

    Returns
    -------
    p : (N,) non-negative array summing to 1.
    """
    w, v = np.linalg.eigh(H)
    _warn_if_indefinite(w, tol, strict, "ground_state_relaxation")
    coeffs = _classical_initial_weights(v, source)
    exp_w = np.exp(-w * t)
    col = v @ (exp_w * coeffs)
    p = np.clip(col, 0.0, None)
    s = p.sum()
    return p / (s + 1e-300)


def haken_strobl(
    H: np.ndarray,
    t: float,
    gamma: float,
    source: Source = 0,
    rtol: float = 1e-6,
    atol: float = 1e-8,
) -> np.ndarray:
    """Open-system CTQW with Haken–Strobl dephasing.

    Lindblad master equation (dephasing-only):
        dρ/dt = −i[H, ρ] − γ · (ρ − diag(ρ) · I)

    Starting from ρ₀ = |psi0⟩⟨psi0| (psi0 a coherent equal-amplitude
    superposition over `source` index/indices -- a scalar `source` recovers
    the original single-index ρ₀ = |source⟩⟨source| exactly), integrates to
    time t and returns the diagonal of the density matrix (occupation
    probabilities).

    Parameters
    ----------
    gamma : dephasing rate in units of the Hamiltonian energy scale.
            gamma=0 recovers pure CTQW; gamma→∞ gives classical diffusion.

    Returns
    -------
    p : (N,) diagonal of ρ(t), non-negative, sums to 1.
    """
    N = H.shape[0]
    idx = _source_indices(source)
    psi0 = np.zeros(N, dtype=complex)
    psi0[idx] = 1.0 / np.sqrt(len(idx))
    rho0 = np.outer(psi0, psi0.conj())

    def rhs(t_: float, rho_flat: np.ndarray) -> np.ndarray:
        rho = rho_flat.reshape(N, N)
        commutator = -1j * (H @ rho - rho @ H)
        dephasing = -gamma * (rho - np.diag(np.diag(rho)))
        return (commutator + dephasing).flatten()

    sol = solve_ivp(
        rhs,
        [0.0, t],
        rho0.flatten(),
        method="RK45",
        rtol=rtol,
        atol=atol,
        dense_output=False,
    )
    rho_t = sol.y[:, -1].reshape(N, N)
    p = np.real(np.diag(rho_t))
    p = np.clip(p, 0.0, None)
    return p / (p.sum() + 1e-300)


def time_averaged_ctqw(
    H: np.ndarray,
    t_max: float,
    source: Source = 0,
    n_steps: int = 500,
    *,
    coherent: bool = True,
) -> np.ndarray:
    """Time-average of CTQW occupation from 0 to t_max.

    Useful as a parameter-free (decoherent-limit) baseline.

    Computes `eigh(H)` once and reuses it across the whole `n_steps` time
    grid (TASK-0111) -- `H` does not change across this loop, so calling
    `ctqw` directly here (which would recompute `eigh(H)` on every one of
    `n_steps` iterations) was pure redundant work with no effect on the
    result; this is a performance fix only, not a behavior change (see
    `test_propagators.py::TestTimeAveragedCtqwEighCaching`).

    `coherent`: same meaning and same default as `ctqw`'s own parameter
    (TASK-0118) -- `False` averages each `source` index's independent
    occupation (incoherent mixture) at every time step instead of using
    the coherent multi-index superposition; identical output either way
    for a scalar `source`.
    """
    w, v = np.linalg.eigh(H)
    fn = _ctqw_from_eigh if coherent else _ctqw_mixture_from_eigh
    times = np.linspace(0.0, t_max, n_steps)
    acc = np.zeros(H.shape[0])
    for t in times:
        acc += fn(w, v, t, source)
    return acc / n_steps


# ---------------------------------------------------------------------------
# TASK-0126 -- 3N-native propagation (`hamiltonians.H13_3N_anm_hessian`,
# IMP-H7's "Option B"). Deliberately *not* a change to `ctqw`/
# `time_averaged_ctqw` themselves: both already operate on `H` of any
# size, indexed however the caller wants -- the only 3N-specific thing is
# what a "residue" seed/occupation *means* in that space (3 spatial DOF
# per residue, not 1). These two functions are a thin translation layer
# around the existing, unmodified propagators, not a refactor of them.
# ---------------------------------------------------------------------------

def residue_source_to_3n(source: Source) -> np.ndarray:
    """Expand a residue-index `source` (scalar or sequence) into the
    matching 3N-space index set, exciting all 3 spatial DOF of each seed
    residue with equal weight -- an isotropic initial perturbation at that
    residue, not favoring any particular bond direction (a stated modeling
    choice, not the only possible one: weighting by each residue's own
    local mode shape would be an alternative, more expensive design left
    for a future task if this one shows it matters)."""
    idx = _source_indices(source)
    return np.concatenate([[3 * int(i), 3 * int(i) + 1, 3 * int(i) + 2] for i in idx])


def reduce_3n_occupation(p_3n: np.ndarray) -> np.ndarray:
    """Sum each residue's 3 spatial-DOF occupation components back to a
    per-residue occupation vector (IMP-H7 Option B's own prescription:
    `p_residue[i] = p_3N[3i] + p_3N[3i+1] + p_3N[3i+2]`). `p_3n` must have
    length `3*n_residues`; raises on any other shape rather than silently
    truncating or padding."""
    if len(p_3n) % 3 != 0:
        raise ValueError(f"reduce_3n_occupation: length {len(p_3n)} is not a multiple of 3")
    return p_3n.reshape(-1, 3).sum(axis=1)


def ctqw_3n_native(H_3n: np.ndarray, t: float, source: Source, **kwargs) -> np.ndarray:
    """`ctqw` on a 3N x 3N operator (e.g. `hamiltonians.H13_3N_anm_hessian`),
    with `source` given in *residue* indices (not 3N-space) and the
    returned occupation already reduced back to one value per residue --
    see `residue_source_to_3n`/`reduce_3n_occupation` for the two
    translations this wraps. `ctqw` itself is called completely unchanged;
    `**kwargs` (e.g. `coherent`) pass straight through to it."""
    p_3n = ctqw(H_3n, t, source=residue_source_to_3n(source), **kwargs)
    return reduce_3n_occupation(p_3n)


def time_averaged_ctqw_3n_native(H_3n: np.ndarray, t_max: float, source: Source, **kwargs) -> np.ndarray:
    """`time_averaged_ctqw` on a 3N x 3N operator -- see `ctqw_3n_native`
    for the residue-source/occupation translation this wraps (identical
    convention, time-averaged instead of a single snapshot)."""
    p_3n = time_averaged_ctqw(H_3n, t_max, source=residue_source_to_3n(source), **kwargs)
    return reduce_3n_occupation(p_3n)


def time_averaged_ctqw_converged_3n_native(H_3n: np.ndarray, source: Source, **kwargs) -> np.ndarray:
    """`time_averaged_ctqw_converged` (TASK-0130's exact infinite-time
    closed form) on a 3N x 3N operator -- same residue-source/occupation
    translation as `ctqw_3n_native`/`time_averaged_ctqw_3n_native`, no
    `t_max`/`n_steps` (there is none for the closed form). Added the same
    day TASK-0130 landed (concurrently with this task's own H13-native
    work) once it became clear the closed form also sidesteps the O(
    n_steps) time-stepping cost that made a full H13-native cutoff search
    infeasible for BCR_ABL1/CARDIAC_MYOSIN under the old finite-`t_max`
    convention (TASK-0126's own Done section has the timing numbers).
    `time_averaged_ctqw_converged`'s own degenerate-eigenvalue grouping
    (`degenerate_tol`, default 1e-6 of `H_3n`'s bandwidth) also transparently
    absorbs H13's 6 near-machine-precision rigid-body zero modes -- no
    separate nullspace-skipping step is needed here the way the old
    `min_adequate_t_max`-based path required (see that function's own
    TASK-0126 docstring caveat)."""
    p_3n = time_averaged_ctqw_converged(H_3n, source=residue_source_to_3n(source), **kwargs)
    return reduce_3n_occupation(p_3n)


@dataclass
class ConvergenceReport:
    """Result of `check_convergence`. `ok` is True only if every check that
    ran passed (a check that didn't apply -- e.g. no `n_steps` given -- is
    recorded with `"applicable": False`, not silently skipped, so a caller
    can see what was and wasn't verified, not just a bare bool)."""
    ok: bool
    checks: Dict[str, Dict[str, Any]]
    notes: List[str] = field(default_factory=list)


def check_convergence(
    H: Optional[np.ndarray] = None,
    t_max: Optional[float] = None,
    n_steps: Optional[int] = None,
    gamma: Optional[float] = None,
    *,
    kind: str = "ground_state_relaxation",
    tol: float = 1e-2,
    strict: bool = False,
    w: Optional[np.ndarray] = None,
) -> ConvergenceReport:
    """Numerical-validity check for `time_averaged_ctqw`/`ground_state_
    relaxation`'s `t_max`/`n_steps` parameters (TASK-0109). Generalizes
    TASK-0102's one-off manual check (BCR_ABL1's spectral gap computed and
    compared to `exp(-gap*t_max)` by hand, after the fact) into something
    callable before trusting any operator's output on any target.

    Two independent, physically distinct checks (do not conflate them --
    each is only meaningful for the propagator it names):

    1. **Nyquist check for `n_steps`** (applies whenever `n_steps` is
       given, either `kind`). `time_averaged_ctqw` does not integrate an
       ODE -- it evaluates the *exact* closed-form `p(t)` at `n_steps`
       sampled points and Riemann-sums them to approximate the continuous
       time-average integral. That sum contains oscillatory cross terms
       `exp(-i(w_k-w_l)t)` for every eigenvalue pair; the fastest one is
       bounded by `H`'s full spectral bandwidth `w.max()-w.min()`. Per the
       ordinary sampling theorem, the sample spacing `dt=t_max/(n_steps-1)`
       must satisfy `dt <= pi/bandwidth` (>=2 samples per period of the
       fastest cross term) or the discrete sum aliases and does not
       converge to the continuous integral as naively expected, however
       large `n_steps` looks. This is a direct, elementary consequence of
       the propagator's own closed-form definition, not a citation-backed
       result on its own -- the literature grounding below is for the
       *magnitude* of the resulting time-averaging error, not this bound.
    2. **`kind="ground_state_relaxation"`: spectral-gap check for
       `t_max`.** `ground_state_relaxation` computes
       `exp(-Ht)p0 = sum_k exp(-w_k t) <v_k|p0> v_k`; as `t` grows this is
       dominated by the smallest `w_k`, and the first-excited-state's
       relative contribution decays as `exp(-(w_1-w_0)*t)` (`w_1-w_0` = the
       spectral gap). This is the same exponential-convergence mechanism
       as the classical power method (dominant/subdominant eigenvalue
       ratio governs convergence rate -- standard numerical linear
       algebra, e.g. Golub & Van Loan, *Matrix Computations*) and as
       imaginary-time ground-state projection in quantum chemistry (e.g.
       Auer, Kammerlander & Brumer, *J. Chem. Phys.* 139, 124117 (2013),
       "Solving the Schrodinger eigenvalue problem by the imaginary time
       propagation technique" -- convergence rate set by the spectral gap
       to the first excited state). `check_convergence` flags `t_max` as
       inadequate when `exp(-gap*t_max) > tol`.
    3. **`kind="time_averaged_ctqw"`: time-averaging-mixing check for
       `t_max`.** A *different* criterion from (2) -- `time_averaged_ctqw`
       is not relaxing toward a ground state, it is averaging out
       oscillatory cross terms to approach the decoherent/infinite-time
       limit `sum_k |v_k(j)|^2 |v_k(source)|^2` (this pipeline's own
       documented headline quantity, see `RESULTS.md`). Aharonov, Ambainis,
       Kempe & Vazirani, "Quantum Walks on Graphs" (STOC 2001,
       quant-ph/0012090), Lemma 4.3, prove for the discrete-time walk's
       time-averaged distribution `P_bar_T`:
       `||P_bar_T - pi|| <= 2 * sum_{i,j: lambda_i != lambda_j}
       |a_i|^2 / (T |lambda_i - lambda_j|)`
       -- i.e. convergence to the time-average limit is controlled by
       `1/(T * gap)`, `gap` the smallest eigenvalue difference with
       nonzero overlap. The continuous-time analog follows directly by
       elementary calculus: `(1/T) integral_0^T exp(-i(w_k-w_l)t) dt =
       (1 - exp(-i(w_k-w_l)T)) / (i(w_k-w_l)T)`, magnitude `<= 2 /
       (|w_k-w_l| T)` -- the identical `1/(gap*T)` structure, derived here
       rather than asserted, grounded in AAKV's discrete-time result for
       the same physical mechanism (oscillatory cross-term cancellation
       under time-averaging). `check_convergence` uses the smallest
       nonzero eigenvalue gap `min_gap` and flags `t_max` as inadequate
       when `2/(min_gap*t_max) > tol`. **TASK-0130**: on every real target
       checked so far, satisfying this criterion is computationally
       infeasible with `time_averaged_ctqw`'s current implementation
       (see `min_adequate_t_max`'s own escape-hatch note) -- a caller
       who wants the converged/decoherent-limit value this criterion is
       trying to certify should use `time_averaged_ctqw_converged`
       instead, which computes that exact limit directly and has no
       `t_max`/`n_steps` to validate at all.

    `gamma` is accepted for signature symmetry with `haken_strobl` but has
    no dedicated check here -- `gamma` interacts with `solve_ivp`'s own
    `rtol`/`atol`, a different numerical-error source (ODE integration,
    not eigendecomposition-based analytic evolution) than what this task's
    Nyquist/spectral-gap/time-averaging criteria target. Out of scope
    (TASK-0109's own Out Of Scope).

    Parameters
    ----------
    H, w : supply one. `w` is `H`'s already-computed eigenvalues (a
           propagator that already called `eigh(H)` should pass `w`, not
           `H`, per this task's own Constraint against re-decomposing).
    kind : "ground_state_relaxation" (default) or "time_averaged_ctqw" --
           selects which `t_max` criterion applies (2 vs 3 above).
    tol  : convergence tolerance for both gap-based checks -- a
           conventional 1% bound (round, clearly-labeled, not derived
           for this codebase specifically; tighten or loosen per call
           site's own accuracy needs, same spirit as
           `LARGE_N_THRESHOLD`'s post-correction documentation: state
           what a constant is and isn't, don't dress up a convention as
           a derivation).
    strict : warn (default) or raise, following `_warn_if_indefinite`'s
             existing convention in this module.

    Returns
    -------
    ConvergenceReport(ok, checks, notes)
    """
    if w is None:
        if H is None:
            raise ValueError("check_convergence needs either H or a precomputed eigenvalue array w")
        w = np.linalg.eigvalsh(H)
    w = np.sort(np.asarray(w, dtype=float))
    bandwidth = float(w[-1] - w[0]) if len(w) > 1 else 0.0

    checks: Dict[str, Dict[str, Any]] = {}
    notes: List[str] = []
    ok = True

    if n_steps is not None and t_max is not None:
        dt = t_max / max(n_steps - 1, 1)
        nyquist_dt = (np.pi / bandwidth) if bandwidth > 0 else np.inf
        min_n_steps = int(np.ceil(t_max * bandwidth / np.pi)) + 1 if bandwidth > 0 else 1
        nyquist_ok = dt <= nyquist_dt
        checks["nyquist"] = {
            "applicable": True, "dt": dt, "bandwidth": bandwidth,
            "nyquist_dt": nyquist_dt, "min_n_steps": min_n_steps, "ok": nyquist_ok,
        }
        ok = ok and nyquist_ok
        if not nyquist_ok:
            notes.append(
                f"n_steps={n_steps} under-samples H's spectral bandwidth "
                f"({bandwidth:.3g}) at t_max={t_max:.3g}: dt={dt:.3g} > "
                f"Nyquist bound {nyquist_dt:.3g} (need n_steps>={min_n_steps}) "
                "-- the discrete time-average may alias, not just be noisy."
            )
    else:
        checks["nyquist"] = {"applicable": False}

    if kind == "ground_state_relaxation":
        if len(w) < 2 or t_max is None:
            checks["spectral_gap"] = {"applicable": False}
        else:
            gap = float(w[1] - w[0])
            residual = float(np.exp(-gap * t_max)) if gap > 0 else 1.0
            gap_ok = residual <= tol
            checks["spectral_gap"] = {
                "applicable": True, "gap": gap, "residual": residual,
                "tol": tol, "ok": gap_ok,
            }
            ok = ok and gap_ok
            if not gap_ok:
                notes.append(
                    f"ground_state_relaxation at t_max={t_max:.3g}: gap={gap:.3g}, "
                    f"exp(-gap*t_max)={residual:.3g} > tol={tol:.3g} -- the "
                    "first-excited-state contribution has not decayed enough; "
                    "the seed/source still matters more than full ground-state "
                    "convergence implies (TASK-0102's own precedent check)."
                )
    elif kind == "time_averaged_ctqw":
        if len(w) < 2 or t_max is None:
            checks["time_average_mixing"] = {"applicable": False}
        else:
            gaps = np.abs(w[:, None] - w[None, :])
            nonzero = gaps[gaps > 1e-12]
            min_gap = float(nonzero.min()) if nonzero.size else 0.0
            bound = (2.0 / (min_gap * t_max)) if min_gap > 0 else np.inf
            mix_ok = bound <= tol
            checks["time_average_mixing"] = {
                "applicable": True, "min_gap": min_gap, "bound": bound,
                "tol": tol, "ok": mix_ok,
            }
            ok = ok and mix_ok
            if not mix_ok:
                notes.append(
                    f"time_averaged_ctqw at t_max={t_max:.3g}: min eigenvalue "
                    f"gap={min_gap:.3g}, AAKV-style bound 2/(min_gap*t_max)="
                    f"{bound:.3g} > tol={tol:.3g} -- oscillatory cross terms may "
                    "not have averaged out; the result may still be closer to a "
                    "coherent snapshot than the decoherent/infinite-time limit."
                )
    else:
        raise ValueError(f"check_convergence: unknown kind {kind!r}")

    report = ConvergenceReport(ok=ok, checks=checks, notes=notes)
    if not ok:
        message = f"check_convergence({kind}): " + "; ".join(report.notes)
        if strict:
            raise ValueError(message)
        warnings.warn(message, UserWarning, stacklevel=2)
    return report


def min_adequate_t_max(
    H: Optional[np.ndarray] = None,
    *,
    kind: str = "ground_state_relaxation",
    tol: float = 1e-2,
    w: Optional[np.ndarray] = None,
) -> float:
    """Prescriptive companion to `check_convergence`: the smallest `t_max`
    that satisfies this module's own gap-based criterion for `kind`, given
    `H` (or its already-computed eigenvalues `w`).

    Solves each `check_convergence` inequality for `t_max` directly (no
    search needed -- both are closed-form):
      - `ground_state_relaxation`: `exp(-gap*t_max) <= tol` =>
        `t_max = -ln(tol) / gap`.
      - `time_averaged_ctqw`: `2/(min_gap*t_max) <= tol` =>
        `t_max = 2 / (min_gap * tol)`.

    This directly operationalizes `REVIEW-panel-2026-07-16-v2.md` P0#2
    ("set `t*` per operator from its spectral gap, `t ~ 1/dlambda`, the
    graph mixing time... `t_max=15` is hardcoded and applied to every
    operator regardless of its energy scale") -- both formulas above are
    exactly `O(1/gap)`, matching that review's own recommendation up to
    the `-ln(tol)`/`2/tol` constant this module makes explicit rather than
    leaving as an unstated proportionality. `check_convergence` diagnoses
    a *given* `t_max`; this prescribes one, so a caller does not have to
    hand-derive the inverse of its own formula. Does not change any
    existing default (`analysis.py`/`ceiling.py`/`run_challenge.py`'s
    `t_max=15.0` is untouched by this function's existence) -- per
    TASK-0109's own Out Of Scope, applying this prescription anywhere is a
    separate, follow-up decision.

    Returns `np.inf` if the relevant gap is zero (degenerate spectrum --
    no finite `t_max` achieves the criterion; a caller should treat this
    as "cannot converge by this criterion," not silently proceed).

    **Rigid-body nullspace caveat (TASK-0126)**: this `inf` guard only
    catches an *exactly* zero gap. A genuine mechanical Hessian like
    `H13_3N_anm_hessian` has 6 rigid-body translation/rotation zero modes
    that are zero *in theory* but land a few ULPs apart in practice (e.g.
    `-2.2e-15` vs `-1.8e-15`) -- `gap > 0` is technically true, so this
    function silently returns an astronomical, physically meaningless
    `t_max` (measured: `9.8e14` for KRAS_G12C's H13) instead of `inf`. A
    caller feeding a multi-DOF-per-node operator's raw spectrum here must
    drop the near-zero nullspace first (same `count(w < 1e-8*max(|w|,1))`
    threshold `superpose._check_anm_rigid_body_nullspace`/TASK-0005/
    TASK-0128 already use) before calling -- see `h13_ceiling_comparison.
    py::_drop_rigid_body_zero_modes` for the pattern. `H2`/`H14`'s own
    single trivial (Laplacian all-ones) zero mode is *not* affected by
    this -- `w[1]` is already their true first non-trivial gap by
    construction, no truncation needed.

    **`kind="time_averaged_ctqw"` escape hatch (TASK-0130)**: on every
    real target this project has checked, this prescription is
    computationally infeasible to actually satisfy with `time_averaged_
    ctqw`'s O(n_steps) explicit time loop -- TASK-0110 measured
    145,000x-3,950,000x the shipped `t_max=15` default, and a single call
    at the prescribed `n_steps` did not return after 2+ hours on real
    KRAS_G12C data. If the caller's actual goal is the converged/
    decoherent-limit value (not a genuine finite-time snapshot), use
    `time_averaged_ctqw_converged` instead -- it computes that exact
    limit directly from `H`'s spectrum, sidestepping this `t_max`/
    `n_steps` question entirely rather than chasing an ever-larger
    practical cap. This function and `check_convergence(kind=
    "time_averaged_ctqw")` remain correct and useful for a caller who
    specifically wants a bounded finite-time snapshot; they are not
    superseded, just not the right tool for the converged-limit case.
    """
    if w is None:
        if H is None:
            raise ValueError("min_adequate_t_max needs either H or a precomputed eigenvalue array w")
        w = np.linalg.eigvalsh(H)
    w = np.sort(np.asarray(w, dtype=float))
    if len(w) < 2:
        return np.inf

    # 1+1e-9 safety margin: the closed-form inversion solves the check's
    # inequality at exact equality, which floating-point exp/log roundtrip
    # can land a few ULPs on the wrong side of -- without this, re-checking
    # the prescribed value with `check_convergence` sporadically fails its
    # own criterion by ~1e-17, not because the prescription is wrong.
    margin = 1.0 + 1e-9
    if kind == "ground_state_relaxation":
        gap = float(w[1] - w[0])
        return float(-np.log(tol) / gap) * margin if gap > 0 else np.inf
    elif kind == "time_averaged_ctqw":
        gaps = np.abs(w[:, None] - w[None, :])
        nonzero = gaps[gaps > 1e-12]
        min_gap = float(nonzero.min()) if nonzero.size else 0.0
        return float(2.0 / (min_gap * tol)) * margin if min_gap > 0 else np.inf
    else:
        raise ValueError(f"min_adequate_t_max: unknown kind {kind!r}")


def min_adequate_n_steps(
    H: Optional[np.ndarray] = None,
    t_max: float = None,
    *,
    w: Optional[np.ndarray] = None,
) -> int:
    """Prescriptive companion to `check_convergence`'s Nyquist check: the
    smallest `n_steps` (for `time_averaged_ctqw`'s `linspace(0, t_max,
    n_steps)` sampling) whose sample spacing resolves `H`'s full spectral
    bandwidth at the given `t_max`. Same closed-form inversion as
    `min_adequate_t_max`, for the sampling-rate side of the same pair of
    parameters."""
    if w is None:
        if H is None:
            raise ValueError("min_adequate_n_steps needs either H or a precomputed eigenvalue array w")
        w = np.linalg.eigvalsh(H)
    w = np.sort(np.asarray(w, dtype=float))
    bandwidth = float(w[-1] - w[0]) if len(w) > 1 else 0.0
    if bandwidth <= 0:
        return 1
    return int(np.ceil(t_max * bandwidth / np.pi)) + 1


# ---------------------------------------------------------------------------
# TASK-0130 -- `time_averaged_ctqw`'s closed-form infinite-time limit.
#
# TASK-0110 measured that `min_adequate_t_max(kind="time_averaged_ctqw")`
# prescribes t_max 145,000x-3,950,000x the shipped default on real targets
# -- a single call at the prescribed n_steps did not return after 2+ hours,
# with the current O(n_steps) explicit time-loop. But the quantity every
# caller actually wants (the decoherent/infinite-time-average limit, this
# pipeline's own documented headline quantity, RESULTS.md) has a known
# closed form -- no time loop needed at all:
#
#   P_infinity(j | source) = sum_k |v_k(j)|^2 |<v_k|psi0>|^2
#
# (promoted from scripts/propagator_convergence_battery.py's private
# `_true_diagonal_ensemble`, which already used this for a scalar source
# to validate `check_convergence`'s predictions against ground truth).
#
# Correctness note (REVIEW-panel-2026-07-17.md P0-1): the index-wise sum
# above is exact only for a non-degenerate spectrum -- derivation: the
# time-averaged occupation is `sum_k sum_l v_k(j) v_l(j) c_k c_l* <exp(-i
# (w_k-w_l)t)>_T`; as T -> infinity the time-average kills every
# cross term with w_k != w_l, leaving `sum_k |v_k(j)|^2 |c_k|^2` -- but
# for (near-)degenerate w_k, w_l, that cross term does NOT average away
# (its phase stays ~stationary), so it must be kept, not dropped. The
# rigorous object groups eigenvalues into blocks of (near-)exact
# degeneracy and sums *amplitudes* within a block before squaring
# (Godsil's average mixing matrix, M = sum_r E_r o E_r over spectral
# idempotents E_r). `_group_degenerate_eigenvalues`/`_block_projected_
# diagonal` below implement exactly that; in the fully non-degenerate
# case (every block a singleton) this reduces algebraically to the plain
# index-wise formula above, so it strictly generalizes rather than
# replaces it. This project's real spectra are near-degenerate, not
# exactly degenerate (confirmed by TASK-0129's BCR_ABL1 finding and by
# this review's own §2.3 BLAS-order-instability flag), so the plain
# formula would likely be numerically fine as-is -- but per the review's
# explicit instruction ("assert a minimum gap or group eigenvalues within
# tolerance... do not inherit a new silent bug while fixing an old one"),
# this implementation groups rather than assumes.
# ---------------------------------------------------------------------------

def _group_degenerate_eigenvalues(w: np.ndarray, tol: float) -> List[np.ndarray]:
    """Partition ascending-sorted eigenvalues `w` into blocks of
    (near-)exact degeneracy: consecutive eigenvalues whose gap is `<=
    tol` join the same block. `tol` is meant to be tiny relative to the
    spectrum's own bandwidth (callers below scale it that way) -- this
    groups true/near-exact degeneracies (e.g. TASK-0128's ANM
    rigid-body-nullspace zero modes, or symmetry-induced degeneracies),
    not merely closely-spaced eigenvalues in a dense real spectrum, which
    the non-degenerate limit of this formula already handles correctly.
    Returns a list of index arrays into `w`/`v`'s eigenvector axis, in
    ascending order, covering every index exactly once."""
    n = len(w)
    blocks = []
    start = 0
    for i in range(1, n):
        if w[i] - w[i - 1] > tol:
            blocks.append(np.arange(start, i))
            start = i
    blocks.append(np.arange(start, n))
    return blocks


def _block_projected_diagonal(v: np.ndarray, blocks: List[np.ndarray], psi0: np.ndarray) -> np.ndarray:
    """`sum_r (E_r @ psi0)^2`, `E_r = V_r @ V_r.T` the projector onto
    degeneracy block `r`'s eigenspace (`V_r` = `v`'s columns in that
    block) -- the block-wise generalization of the plain index-wise
    `sum_k (v_k(j) * <v_k|psi0>)^2` formula (identical to it when every
    block is a singleton). `psi0` real (this module's initial states
    never carry a relative phase, see `_quantum_initial_coeffs`'s own
    docstring), so no complex arithmetic is needed here despite this
    being a genuinely quantum-coherent-superposition calculation."""
    p = np.zeros(v.shape[0])
    for block in blocks:
        V_r = v[:, block]
        c_r = V_r.T @ psi0
        p += (V_r @ c_r) ** 2
    return p


def time_averaged_ctqw_converged(
    H: Optional[np.ndarray] = None,
    source: Source = 0,
    *,
    coherent: bool = True,
    degenerate_tol: float = 1e-6,
    w: Optional[np.ndarray] = None,
    v: Optional[np.ndarray] = None,
) -> np.ndarray:
    """The exact t_max -> infinity limit of `time_averaged_ctqw`, computed
    directly from `H`'s spectral decomposition -- no time loop, no
    `t_max`/`n_steps` validity question, because there is no finite time
    parameter to choose. Supersedes `min_adequate_t_max(kind=
    "time_averaged_ctqw")`'s infeasible prescription for any caller who
    wants the converged/decoherent-limit value rather than a genuine
    finite-time snapshot (TASK-0130; see `min_adequate_t_max`'s own
    docstring for the pointer here).

    A new function rather than a `time_averaged_ctqw(t_max=None, ...)`
    option: `time_averaged_ctqw`'s existing signature/behavior is
    untouched (ADD-only, no existing call site's output can change), and
    a caller reading `time_averaged_ctqw_converged(H, source)` does not
    need to know this project's own t_max-infeasibility history to
    understand what it computes.

    Parameters
    ----------
    H : (N, N) real symmetric Hamiltonian. Optional if both `w` and `v`
        (an already-computed `eigh(H)` decomposition) are supplied --
        this function never re-decomposes `H` when the caller already
        has one (same reuse discipline as `check_convergence`'s own `w`
        parameter, per this task's own Constraint).
    source : starting node index, or a sequence of indices.
    coherent : same meaning as `ctqw`'s own parameter -- `True` (default,
        matching `ctqw`/`time_averaged_ctqw`'s own default): a coherent
        equal-amplitude superposition over `source`, cross-source
        interference terms included. `False`: an incoherent statistical
        mixture (mean of each source index's own single-seed limit,
        TASK-0118's panel-recommended convention for a multi-residue
        seed). Identical either way for a scalar `source`.
    degenerate_tol : eigenvalue-gap tolerance, as a *fraction of H's own
        spectral bandwidth* (`w.max()-w.min()`), below which consecutive
        eigenvalues are treated as exactly degenerate and grouped before
        squaring (see module-level comment above this function). Default
        1e-6 catches true/near-machine-precision degeneracies (e.g.
        TASK-0128's ANM zero modes, spaced ~1e-16 apart on a spectrum
        spanning O(1)-O(10)) without merging this project's real,
        near-continuum-but-distinct spectra (e.g. the BCR_ABL1 gap
        REVIEW-panel-2026-07-17.md §2.3 flags as BLAS-order-unstable,
        ~0.03-0.2 apart -- five to six orders of magnitude above this
        default's threshold on that target's own bandwidth, so untouched
        by it).

    Returns
    -------
    p : (N,) non-negative array summing to 1.
    """
    if w is None or v is None:
        if H is None:
            raise ValueError(
                "time_averaged_ctqw_converged needs either H or a precomputed (w, v) eigh(H) pair"
            )
        w, v = np.linalg.eigh(H)
    idx = _source_indices(source)
    bandwidth = float(w[-1] - w[0]) if len(w) > 1 else 0.0
    tol = degenerate_tol * bandwidth if bandwidth > 0 else degenerate_tol
    blocks = _group_degenerate_eigenvalues(w, tol)
    n = v.shape[0]

    if coherent:
        psi0 = np.zeros(n)
        psi0[idx] = 1.0 / np.sqrt(len(idx))
        p = _block_projected_diagonal(v, blocks, psi0)
    else:
        p = np.zeros(n)
        for i in idx:
            psi0 = np.zeros(n)
            psi0[i] = 1.0
            p += _block_projected_diagonal(v, blocks, psi0)
        p /= len(idx)

    p /= p.sum() + 1e-300
    return p


def build_gapped_synthetic_network(N: int, well_depth: float, *, seed: int = 0) -> np.ndarray:
    """Build an `(N, N)` combinatorial-Laplacian-plus-well operator for
    TASK-0109's convergence-characterization battery: a ring-plus-random-
    chords weighted graph (a single connected component, not a bare
    unweighted cycle) with an optional single-node negative-diagonal trap
    that controls the spectral gap.

    Reuses TASK-0103's own randomization precedent for this kind of
    synthetic construction (`test_dumbbell_negative_control.py`'s
    `build_dumbbell_network`: rng-seeded edge weights in `[0.7, 1.3]`, not
    a bare unweighted graph -- that module's own regression test,
    `test_seeds_actually_vary_the_network`, exists because an earlier
    unweighted/deterministic prototype silently produced identical
    networks across "different" seeds). Not a call to that function
    directly: `build_dumbbell_network` is a fixed 44-node, fixed-topology
    two-lobe construction (TASK-0103's own falsification-suite need, not
    parametrized by `N`), so reusing it here would mean forcing this
    task's `N in {20, 50, 100, 200, 500}` sweep through an unrelated,
    non-scalable shape -- this is a new, minimal construction following
    the same principle, not a second, unrelated copy of the same idea.

    `well_depth`: the diagonal trap depth on node 0 -- `0` leaves a clean
    ring+chords Laplacian (a small ground-gap, set by graph topology
    alone); larger values split off an isolated low eigenvalue whose gap
    to the rest of the spectrum grows with `well_depth`, giving direct,
    monotonic control over the ground-state spectral gap this task's
    battery needs to sweep, independent of `N`.
    """
    if N < 3:
        raise ValueError(f"build_gapped_synthetic_network: N={N} too small for a ring topology")
    rng = np.random.default_rng(seed)
    W = np.zeros((N, N))
    for i in range(N):
        j = (i + 1) % N
        W[i, j] = W[j, i] = rng.uniform(0.7, 1.3)
    n_chords = max(N // 4, 1)
    for _ in range(n_chords):
        i, j = rng.choice(N, size=2, replace=False)
        W[i, j] = W[j, i] = rng.uniform(0.7, 1.3)
    L = laplacian(W, normalised=False)
    if well_depth > 0:
        L[0, 0] -= well_depth
    return L
