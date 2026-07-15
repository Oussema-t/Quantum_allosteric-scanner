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
from typing import Sequence, Union

import numpy as np
from scipy import linalg as sla
from scipy.integrate import solve_ivp

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
    formula `ctqw`/`time_averaged_ctqw` both need (TASK-0111). Never
    called directly by anything outside this module; `ctqw` computes
    `(w, v)` itself for a single call, `time_averaged_ctqw` computes it
    once and reuses it across its whole time grid."""
    coeffs = _quantum_initial_coeffs(v, source)
    amplitudes = v @ (np.exp(-1j * w * t) * coeffs)
    p = np.abs(amplitudes) ** 2
    p /= p.sum() + 1e-300  # normalise against floating-point drift
    return p


def ctqw(
    H: np.ndarray,
    t: float,
    source: Source = 0,
) -> np.ndarray:
    """CTQW occupation probabilities at time t, starting from |source⟩.

    p_j(t) = |⟨j| e^{−iHt} |psi0⟩|²

    Parameters
    ----------
    H      : (N, N) real symmetric Hamiltonian.
    t      : propagation time.
    source : starting node index, or a sequence of indices -- a multi-index
             source is a coherent equal-amplitude superposition over those
             nodes (the functional/active-site seed set is rarely a single
             atom), not a scalar reduction of one.

    Returns
    -------
    p : (N,) non-negative array summing to 1.
    """
    w, v = np.linalg.eigh(H)
    return _ctqw_from_eigh(w, v, t, source)


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
) -> np.ndarray:
    """Time-average of CTQW occupation from 0 to t_max.

    Useful as a parameter-free (decoherent-limit) baseline.

    Computes `eigh(H)` once and reuses it across the whole `n_steps` time
    grid (TASK-0111) -- `H` does not change across this loop, so calling
    `ctqw` directly here (which would recompute `eigh(H)` on every one of
    `n_steps` iterations) was pure redundant work with no effect on the
    result; this is a performance fix only, not a behavior change (see
    `test_propagators.py::TestTimeAveragedCtqwEighCaching`).
    """
    w, v = np.linalg.eigh(H)
    times = np.linspace(0.0, t_max, n_steps)
    acc = np.zeros(H.shape[0])
    for t in times:
        acc += _ctqw_from_eigh(w, v, t, source)
    return acc / n_steps
