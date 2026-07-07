"""Quantum and classical propagators.

All propagators take a Hamiltonian H (N×N, real symmetric) and return an
occupation probability vector p of shape (N,) with p.sum() ≈ 1.

Three propagators (same H, different physics):
  ctqw        – Continuous-Time Quantum Walk: exp(−iHt), coherent.
  heat        – Classical heat / diffusion kernel: exp(−Ht).
  haken_strobl – Open-system CTQW with dephasing: Lindblad master equation.

The dephasing sweep in Phase 0a tests that AUC is flat across gamma values,
confirming coherence adds nothing beyond topology for these protein graphs.
"""
from __future__ import annotations

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
    coeffs = _quantum_initial_coeffs(v, source)
    amplitudes = v @ (np.exp(-1j * w * t) * coeffs)
    p = np.abs(amplitudes) ** 2
    p /= p.sum() + 1e-300  # normalise against floating-point drift
    return p


def heat(
    H: np.ndarray,
    t: float,
    source: Source = 0,
) -> np.ndarray:
    """Heat-kernel (classical diffusion) occupation at time t.

    p_j(t) = [e^{−Ht} p0]_j, p0 uniform over `source` index/indices.

    H should be a positive-semidefinite Laplacian. The result is clipped to
    non-negative and re-normalised to handle floating-point noise.

    Returns
    -------
    p : (N,) non-negative array summing to 1.
    """
    w, v = np.linalg.eigh(H)
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
    """
    times = np.linspace(0.0, t_max, n_steps)
    acc = np.zeros(H.shape[0])
    for t in times:
        acc += ctqw(H, t, source=source)
    return acc / n_steps
