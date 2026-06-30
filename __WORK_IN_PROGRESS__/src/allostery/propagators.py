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

import numpy as np
from scipy import linalg as sla
from scipy.integrate import solve_ivp


def ctqw(
    H: np.ndarray,
    t: float,
    source: int = 0,
) -> np.ndarray:
    """CTQW occupation probabilities at time t, starting from |source⟩.

    p_j(t) = |⟨j| e^{−iHt} |source⟩|²

    Parameters
    ----------
    H      : (N, N) real symmetric Hamiltonian.
    t      : propagation time.
    source : starting node index.

    Returns
    -------
    p : (N,) non-negative array summing to 1.
    """
    N = H.shape[0]
    w, v = np.linalg.eigh(H)
    # U|source⟩ = Σ_k e^{-iw_k t} v_k (v_k · e_{source})
    amplitudes = v @ (np.exp(-1j * w * t) * v[source, :])
    p = np.abs(amplitudes) ** 2
    p /= p.sum() + 1e-300  # normalise against floating-point drift
    return p


def heat(
    H: np.ndarray,
    t: float,
    source: int = 0,
) -> np.ndarray:
    """Heat-kernel (classical diffusion) occupation at time t.

    p_j(t) = [e^{−Ht}]_{j,source}

    H should be a positive-semidefinite Laplacian. The result is clipped to
    non-negative and re-normalised to handle floating-point noise.

    Returns
    -------
    p : (N,) non-negative array summing to 1.
    """
    w, v = np.linalg.eigh(H)
    exp_w = np.exp(-w * t)
    col = v @ (exp_w * v[source, :])
    p = np.clip(col, 0.0, None)
    s = p.sum()
    return p / (s + 1e-300)


def haken_strobl(
    H: np.ndarray,
    t: float,
    gamma: float,
    source: int = 0,
    rtol: float = 1e-6,
    atol: float = 1e-8,
) -> np.ndarray:
    """Open-system CTQW with Haken–Strobl dephasing.

    Lindblad master equation (dephasing-only):
        dρ/dt = −i[H, ρ] − γ · (ρ − diag(ρ) · I)

    Starting from ρ₀ = |source⟩⟨source|, integrates to time t and returns
    the diagonal of the density matrix (occupation probabilities).

    Parameters
    ----------
    gamma : dephasing rate in units of the Hamiltonian energy scale.
            gamma=0 recovers pure CTQW; gamma→∞ gives classical diffusion.

    Returns
    -------
    p : (N,) diagonal of ρ(t), non-negative, sums to 1.
    """
    N = H.shape[0]
    rho0 = np.zeros((N, N), dtype=complex)
    rho0[source, source] = 1.0

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
    source: int = 0,
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
