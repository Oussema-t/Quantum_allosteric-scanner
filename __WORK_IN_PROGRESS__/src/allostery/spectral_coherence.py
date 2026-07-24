"""TASK-0146 -- frequency-domain / spectral coherence observable.

Every propagator this project has scored on real data
(`time_averaged_ctqw_converged`, `ground_state_relaxation`, `haken_strobl`'s
ENAQT sweep) explicitly time-averages away phase information --
`time_averaged_ctqw_converged` (TASK-0130) is *provably* phase-free at the
converged limit (its own closed form sums `|<v_k|psi0>|^2 |v_k(j)|^2` over
modes, discarding every cross term). This module deliberately does the
opposite: track the *un-averaged*, finite-time coherent trajectory

    c_j(t) = <j| exp(-iHt) |psi0>

between the source (seed) and every candidate residue `j`, and asks whether
the *frequency content* of that trajectory -- not its time-average --
carries coupling information the converged limit destroys.

**Real design decision, not obvious from the physics alone (Intent
Contract's own explicit instruction to state and justify it)**: the task's
own Context describes the signal of interest as "quantum beating, dominated
by Bohr frequencies `w_k - w_l`." The raw complex amplitude `c_j(t)` is a
sum of terms oscillating at the *single* frequencies `w_k` (linear in
`exp(-i*w_k*t)`) -- it is the *occupation probability* `p_j(t) = |c_j(t)|^2`
whose Fourier spectrum genuinely contains the cross-term beat frequencies
`w_k - w_l` (from expanding `|sum_k a_k exp(-i*w_k*t)|^2`). This module
Fourier-analyzes `p_j(t)`, not the raw amplitude, so that "spectral power at
nonzero frequency" means exactly the quantum-beating content the task's own
physics description points at.

**Score definition, chosen and justified (Intent Contract: "state the exact
scoring definition chosen... this is a real design decision")**: total AC
spectral power, `sum_{f != 0} |FFT(p_j(t))_f|^2`. The DC bin (f=0) of
`p_j(t)`'s spectrum is, by construction, exactly `time_averaged_ctqw_
converged`'s own headline quantity (the time average of `p_j(t)`) -- already
scored and already documented to carry the proximity confound. Excluding
it isolates the genuinely new information this task exists to test: how
much residue `j`'s population *oscillates* at all, which requires real
overlap with >=2 distinct eigenmodes at well-separated eigenvalues (a
residue weakly/singly coupled to the source has a nearly time-invariant
`p_j(t)`, near-zero AC power, regardless of its time-averaged occupation).
An alternative (peak-counting: how many frequency bins clear some noise
threshold) was considered and not chosen -- it introduces an extra,
unjustified free parameter (the peak-detection threshold) that total power
does not need, and by Parseval's theorem total AC power already equals
`Var_t[p_j(t)]` up to a normalization constant, an interpretable quantity
in its own right ("how much does this residue's population move").

**Time window / sampling rate, chosen and justified (Intent Contract /
Constraints: "fixed once, stated, and blind to labels", "reuse
`propagators.min_adequate_n_steps`-style reasoning rather than picking an
arbitrary window")**: `min_adequate_t_max`'s own existing formula
(`T ~ O(1/gap)`) already establishes the right functional form for "how
long a window resolves a given frequency gap," but its literal prescription
for `H_new`'s real spectra is TASK-0110's own already-documented
infeasibility (a full-decoherence `t_max` 145,000x-3,950,000x the shipped
default) -- driven by pathologically small near-degenerate gaps (median
gap 0.0015-0.0062 across the 3 mandatory targets, but the single smallest
observed gap is 3-4 orders of magnitude below that). Chasing the literal
smallest gap is neither tractable nor, per TASK-0129/0137's own
near-degeneracy handling for the closed-form quantity, physically
meaningful (near-exact degeneracies are numerically fragile, not a real
distinguishing feature). This module instead fixes a single, real-data-
checked, tractable `T=5000` -- chosen so `min_adequate_n_steps(H,
t_max=5000)` stays in the low thousands on every mandatory target (checked
directly, not assumed: ~3980 steps on CARDIAC_MYOSIN, the largest/densest
spectrum), the same reused Nyquist-adequacy formula as everywhere else in
this module's own family. This resolves (Δf = 2*pi/T ~= 0.00126) the
majority of real Bohr gaps on every mandatory target (~95th-percentile-and-
above on KRAS_G12C, ~75th-and-above on BCR_ABL1, ~50th-and-above on
CARDIAC_MYOSIN, the limiting case) -- reported honestly as a real,
target-dependent limitation, not glossed over.
"""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from .propagators import Source, _quantum_initial_coeffs, min_adequate_n_steps

DEFAULT_T_MAX = 5000.0


def amplitude_trajectories(
    H: np.ndarray,
    source: Source = 0,
    *,
    t_max: float = DEFAULT_T_MAX,
    n_steps: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Coherent amplitude trajectories `c_j(t) = <j|exp(-iHt)|psi0>` for
    every residue `j`, sampled uniformly on `[0, t_max)`.

    `n_steps` defaults to `propagators.min_adequate_n_steps`'s own
    Nyquist-adequate sample count for `H`'s full spectral bandwidth at
    `t_max` (this module's own DEFAULT_T_MAX docstring justifies the
    `t_max` choice; `n_steps` here is the reused, not re-derived,
    sampling-rate side of that same pair).

    Returns `(t, C)`: `t` shape `(n_steps,)`, `C` shape `(n_steps, N)`
    complex, `C[i, j] == c_j(t[i])`.
    """
    w, v = np.linalg.eigh(H)
    if n_steps is None:
        n_steps = min_adequate_n_steps(w=w, t_max=t_max)
    n_steps = max(int(n_steps), 2)
    coeffs = _quantum_initial_coeffs(v, source)
    t = np.linspace(0.0, t_max, n_steps, endpoint=False)
    phase = np.exp(-1j * np.outer(t, w))  # (n_steps, n_modes)
    C = (phase * coeffs[None, :]) @ v.T  # (n_steps, N)
    return t, C


def spectral_coherence_score(
    H: np.ndarray,
    source: Source = 0,
    *,
    t_max: float = DEFAULT_T_MAX,
    n_steps: Optional[int] = None,
) -> np.ndarray:
    """Per-residue coupling score, `(N,)`: total AC (non-DC) spectral
    power of the occupation trajectory `p_j(t) = |c_j(t)|^2`. See this
    module's own docstring for the full justification of both the score
    and the `t_max`/`n_steps` choice. Higher = residue `j`'s population
    oscillates more strongly over the sampled window -- genuine multi-mode
    coupling to the source, not proximity or a large converged occupation
    on its own (both of those live in the excluded DC bin).
    """
    t, C = amplitude_trajectories(H, source, t_max=t_max, n_steps=n_steps)
    P = np.abs(C) ** 2  # (n_steps, N) real occupation trajectories
    # Full (two-sided) FFT, not `rfft` -- `rfft` returns only the
    # non-negative-frequency half, and naively summing `|rfft[1:]|**2`
    # double-undercounts relative to the true two-sided Parseval sum
    # (each non-Nyquist positive-frequency bin has an equal-magnitude
    # mirror at the corresponding negative frequency that must also be
    # counted). Using the full FFT sidesteps that bookkeeping entirely
    # and is confirmed exact against `Var_t[p_j(t)]` by this module's own
    # test suite, not just asserted from the derivation.
    spectrum = np.fft.fft(P, axis=0)  # (n_steps, N)
    n_steps_actual = P.shape[0]
    # Parseval: sum_k |FFT_k|^2 / n = sum_t |p(t)|^2. Excluding the DC
    # bin (k=0) and dividing by n once more converts the remainder into
    # exactly Var_t[p_j(t)] -- normalized so the score is n_steps-
    # invariant (comparable across targets/n_steps), not an artifact of
    # how many samples happened to be taken.
    ac_power = (np.abs(spectrum[1:]) ** 2).sum(axis=0) / (n_steps_actual ** 2)
    return ac_power
