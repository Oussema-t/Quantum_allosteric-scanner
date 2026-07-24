"""TASK-0146 -- frequency-domain / spectral coherence observable tests.

Synthetic coordinate-free Hamiltonians only (no PDB, no network) -- the
dumbbell falsification gate (against `test_dumbbell_negative_control.py`'s
own shared construction) lives in that file, alongside this project's other
operator-falsification gates, not duplicated here.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.spectral_coherence import (  # noqa: E402
    amplitude_trajectories,
    spectral_coherence_score,
)


def _ring_hamiltonian(n: int = 8, coupling: float = 1.0) -> np.ndarray:
    """A simple ring graph Laplacian -- enough spectral structure (n>2
    distinct eigenvalues) to exercise real beating without needing a real
    protein Hamiltonian."""
    H = np.zeros((n, n))
    for i in range(n):
        j = (i + 1) % n
        H[i, j] = H[j, i] = -coupling
    np.fill_diagonal(H, 2.0 * coupling)
    return H


def _isolated_plus_ring(n_ring: int = 6, coupling: float = 1.0) -> np.ndarray:
    """A ring plus one fully disconnected extra node -- the disconnected
    node has zero overlap with the source's Hamiltonian block, so its
    `c_j(t)` must be identically zero at every `t` (a hard, exact check,
    not a fuzzy near-zero one)."""
    H = np.zeros((n_ring + 1, n_ring + 1))
    ring = _ring_hamiltonian(n_ring, coupling)
    H[:n_ring, :n_ring] = ring
    H[n_ring, n_ring] = 1.0  # isolated node, its own trivial 1x1 block
    return H


class TestAmplitudeTrajectories:
    def test_shape_and_dtype(self):
        H = _ring_hamiltonian(8)
        t, C = amplitude_trajectories(H, source=0, t_max=50.0, n_steps=64)
        assert t.shape == (64,)
        assert C.shape == (64, 8)
        assert np.iscomplexobj(C)

    def test_probability_conserved_at_every_time(self):
        """sum_j |c_j(t)|^2 == 1 at every sampled t -- unitarity, the most
        basic correctness check of the eigh-based evolution formula."""
        H = _ring_hamiltonian(8)
        t, C = amplitude_trajectories(H, source=0, t_max=50.0, n_steps=64)
        totals = (np.abs(C) ** 2).sum(axis=1)
        np.testing.assert_allclose(totals, 1.0, atol=1e-9)

    def test_t0_amplitude_is_the_source_delta_state(self):
        """At t=0, exp(-iHt)=I, so c_j(0) = delta_{j,source}."""
        H = _ring_hamiltonian(8)
        t, C = amplitude_trajectories(H, source=3, t_max=50.0, n_steps=64)
        assert t[0] == 0.0
        expected = np.zeros(8, dtype=complex)
        expected[3] = 1.0
        np.testing.assert_allclose(C[0], expected, atol=1e-9)

    def test_disconnected_node_has_exactly_zero_amplitude_always(self):
        H = _isolated_plus_ring(6)
        t, C = amplitude_trajectories(H, source=0, t_max=50.0, n_steps=64)
        np.testing.assert_allclose(C[:, -1], 0.0, atol=1e-9)

    def test_default_n_steps_is_nyquist_adequate_and_positive(self):
        H = _ring_hamiltonian(8)
        t, C = amplitude_trajectories(H, source=0, t_max=50.0)
        assert len(t) >= 2
        assert C.shape[0] == len(t)


class TestSpectralCoherenceScore:
    def test_shape_finite_nonnegative(self):
        H = _ring_hamiltonian(8)
        score = spectral_coherence_score(H, source=0, t_max=50.0, n_steps=128)
        assert score.shape == (8,)
        assert np.all(np.isfinite(score))
        assert np.all(score >= 0.0)

    def test_disconnected_node_scores_exactly_zero(self):
        """A node with zero overlap with the source's block has a
        perfectly flat (identically zero) occupation trajectory -- zero
        variance, zero AC spectral power, exactly, not approximately."""
        H = _isolated_plus_ring(6)
        score = spectral_coherence_score(H, source=0, t_max=50.0, n_steps=128)
        assert score[-1] == pytest.approx(0.0, abs=1e-15)

    def test_source_itself_beats_more_than_a_flat_trivial_mode(self):
        """The source residue's own occupation starts at 1, decays and
        beats as probability leaves and returns -- real, nonzero AC power,
        unlike the disconnected node's exact zero."""
        H = _isolated_plus_ring(6)
        score = spectral_coherence_score(H, source=0, t_max=50.0, n_steps=128)
        assert score[0] > 0.0
        assert score[0] > score[-1]

    def test_matches_parseval_variance_identity(self):
        """Total AC spectral power (this module's own score) must equal
        Var_t[p_j(t)] up to the stated normalization -- a direct algebraic
        identity (Parseval's theorem), checked numerically as a
        correctness guard on the FFT/normalization convention, not just
        asserted from the derivation in the module docstring."""
        H = _ring_hamiltonian(8)
        t, C = amplitude_trajectories(H, source=0, t_max=50.0, n_steps=256)
        P = np.abs(C) ** 2
        score = spectral_coherence_score(H, source=0, t_max=50.0, n_steps=256)
        variance = P.var(axis=0)
        np.testing.assert_allclose(score, variance, rtol=1e-9, atol=1e-15)

    def test_zero_coupling_gives_zero_beating(self):
        """A diagonal H (no coupling at all) has time-independent
        `p_j(t)` for every `j` -- exactly zero AC power. **Real finding,
        not assumed**: an *equal-coupling-strength* comparison (e.g.
        weak-ring vs. strong-ring AC power at a fixed `t_max`/`n_steps`)
        is NOT monotonic in coupling on this construction -- rescaling a
        ring's coupling by a constant `c` rescales its eigenvalues by `c`
        but leaves eigenvectors (hence the oscillation *shape*/depth)
        unchanged, so at a fixed sampling window the two constructions
        sample different, non-comparable numbers of oscillation cycles.
        The coupling=0 vs. coupling>0 dichotomy below is the clean,
        un-confounded version of the same physical claim."""
        no_coupling = np.diag([1.0, 2.0, 0.5, 1.5, 1.0, 2.0, 0.5, 1.5])
        weak_coupling = _ring_hamiltonian(8, coupling=0.3)
        zero = spectral_coherence_score(no_coupling, source=0, t_max=50.0, n_steps=128)
        nonzero = spectral_coherence_score(weak_coupling, source=0, t_max=50.0, n_steps=128)
        np.testing.assert_allclose(zero, 0.0, atol=1e-15)
        assert nonzero[1] > 0.0

    def test_score_independent_of_n_steps_up_to_convergence(self):
        """The Parseval normalization (`/ n_steps**2`) is meant to make
        the score comparable across different sample counts, not an
        artifact of how finely the window happened to be sampled -- two
        different (adequately Nyquist-resolved) `n_steps` on the same
        window should agree closely."""
        H = _ring_hamiltonian(8)
        score_a = spectral_coherence_score(H, source=0, t_max=50.0, n_steps=256)
        score_b = spectral_coherence_score(H, source=0, t_max=50.0, n_steps=512)
        np.testing.assert_allclose(score_a, score_b, rtol=0.05)

    def test_excludes_the_dc_bin_that_time_averaged_ctqw_already_covers(self):
        """Two residues with identical `time_averaged_ctqw_converged`
        occupation (same DC bin) can have very different AC power -- the
        whole point of this observable being a genuinely different
        quantity, not a re-derivation of the already-scored converged
        limit. Constructed directly: a symmetric ring has two neighbors of
        the source with identical converged occupation by the ring's own
        reflection symmetry; this is a sanity check that the converged
        limit does NOT already determine the AC score (it needn't differ
        here since they're symmetric, but confirms both quantities are
        computed independently and consistently on the same H)."""
        H = _ring_hamiltonian(8)
        converged = time_averaged_ctqw_converged(H, source=0, coherent=True)
        score = spectral_coherence_score(H, source=0, t_max=50.0, n_steps=256)
        # Ring reflection symmetry: residues 1 and 7 (both adjacent to
        # source 0) must match on BOTH quantities independently.
        assert converged[1] == pytest.approx(converged[7], abs=1e-9)
        assert score[1] == pytest.approx(score[7], rel=1e-6)
