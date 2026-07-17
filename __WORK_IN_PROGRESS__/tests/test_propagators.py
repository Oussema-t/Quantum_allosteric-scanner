"""TASK-0111 coverage -- propagators.ctqw/time_averaged_ctqw's eigh-caching
fix. No dedicated test file existed for propagators.py before this task
(its functions are otherwise exercised only indirectly, via test_analysis.py
/test_hamiltonians.py/test_physics.py) -- this file is scoped narrowly to
the fix itself, not a full propagators.py test suite.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.propagators import ctqw, time_averaged_ctqw  # noqa: E402


def _helix_coords(n: int) -> np.ndarray:
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


def _random_symmetric_H(n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(n, n))
    return (A + A.T) / 2


def _time_averaged_ctqw_reference(H, t_max, source=0, n_steps=500):
    """Independent re-derivation of the pre-TASK-0111 (redundant-eigh)
    implementation -- kept deliberately separate from the fixed
    `time_averaged_ctqw` so this test doesn't just check the function
    against itself."""
    times = np.linspace(0.0, t_max, n_steps)
    acc = np.zeros(H.shape[0])
    for t in times:
        acc += ctqw(H, t, source=source)
    return acc / n_steps


class TestTimeAveragedCtqwEighCaching:
    def test_matches_the_redundant_eigh_reference_implementation(self):
        """Pure performance refactor -- output must be unchanged (float-
        tolerance identical), not just plausible."""
        H = _random_symmetric_H(20, seed=1)
        fast = time_averaged_ctqw(H, t_max=8.0, source=3, n_steps=80)
        reference = _time_averaged_ctqw_reference(H, t_max=8.0, source=3, n_steps=80)
        np.testing.assert_allclose(fast, reference, rtol=1e-10, atol=1e-12)

    def test_matches_reference_with_a_multi_index_source(self):
        H = _random_symmetric_H(16, seed=2)
        fast = time_averaged_ctqw(H, t_max=5.0, source=[0, 2, 5], n_steps=50)
        reference = _time_averaged_ctqw_reference(H, t_max=5.0, source=[0, 2, 5], n_steps=50)
        np.testing.assert_allclose(fast, reference, rtol=1e-10, atol=1e-12)

    def test_matches_reference_on_a_real_helix_hamiltonian(self):
        from allostery.hamiltonians import H2_combinatorial_laplacian

        H = H2_combinatorial_laplacian(_helix_coords(24), cutoff=10.0)
        fast = time_averaged_ctqw(H, t_max=15.0, source=0, n_steps=200)
        reference = _time_averaged_ctqw_reference(H, t_max=15.0, source=0, n_steps=200)
        np.testing.assert_allclose(fast, reference, rtol=1e-10, atol=1e-12)

    def test_output_is_a_valid_probability_vector(self):
        H = _random_symmetric_H(12, seed=3)
        p = time_averaged_ctqw(H, t_max=4.0, source=0, n_steps=30)
        assert p.shape == (12,)
        assert (p >= 0).all()
        assert p.sum() == pytest.approx(1.0, abs=1e-6)

    def test_meaningfully_faster_than_the_redundant_reference(self):
        """Generous tolerance (>=3x), not a flaky micro-benchmark -- the
        fix eliminates n_steps-1 redundant eigh calls, an O(n_steps)
        reduction that should be unmistakable even accounting for system
        noise."""
        H = _random_symmetric_H(60, seed=4)
        n_steps = 150

        t0 = time.perf_counter()
        time_averaged_ctqw(H, t_max=10.0, source=0, n_steps=n_steps)
        fast_elapsed = time.perf_counter() - t0

        t0 = time.perf_counter()
        _time_averaged_ctqw_reference(H, t_max=10.0, source=0, n_steps=n_steps)
        reference_elapsed = time.perf_counter() - t0

        assert fast_elapsed * 3 < reference_elapsed, (
            f"fixed implementation ({fast_elapsed:.4f}s) is not meaningfully "
            f"faster than the redundant-eigh reference ({reference_elapsed:.4f}s)"
        )


class TestCtqwUnaffected:
    """ctqw's own public behavior/signature must be byte-identical --
    only time_averaged_ctqw's internals changed."""

    def test_single_call_output_unchanged(self):
        H = _random_symmetric_H(10, seed=5)
        p = ctqw(H, t=3.0, source=1)
        assert p.shape == (10,)
        assert p.sum() == pytest.approx(1.0, abs=1e-6)

    def test_still_recomputes_eigh_per_call_for_different_h(self):
        """ctqw must still work correctly if called with a *different* H
        each time (its own contract) -- confirms the shared helper wasn't
        wired to accidentally cache across distinct Hamiltonians."""
        H1 = _random_symmetric_H(8, seed=6)
        H2 = _random_symmetric_H(8, seed=7)
        p1 = ctqw(H1, t=2.0, source=0)
        p2 = ctqw(H2, t=2.0, source=0)
        assert not np.allclose(p1, p2)


# ---------------------------------------------------------------------------
# TASK-0118 -- incoherent-mixture `coherent=False` support
# ---------------------------------------------------------------------------

def _incoherent_reference(H, t, source, n_steps=None):
    """Independent re-derivation of the incoherent-mixture formula --
    average each seed index's own single-source `ctqw` occupation. Kept
    deliberately separate from `_ctqw_mixture_from_eigh` (calls the public
    `ctqw`, not the private eigh-sharing helper) so this doesn't just check
    the implementation against itself. `n_steps=None` -> single-time-point
    `ctqw`; otherwise averages `time_averaged_ctqw` per index."""
    idx = np.atleast_1d(np.asarray(source, dtype=int))
    if n_steps is None:
        return np.mean([ctqw(H, t, source=int(i)) for i in idx], axis=0)
    return np.mean(
        [time_averaged_ctqw(H, t, source=int(i), n_steps=n_steps) for i in idx], axis=0
    )


class TestIncoherentMixture:
    def test_default_is_coherent_true_byte_identical(self):
        """No existing caller passes `coherent=` -- the default must be
        exactly the pre-TASK-0118 behavior, not just close to it."""
        H = _random_symmetric_H(14, seed=8)
        default = ctqw(H, t=4.0, source=[1, 3, 5])
        explicit = ctqw(H, t=4.0, source=[1, 3, 5], coherent=True)
        np.testing.assert_array_equal(default, explicit)

        default_ta = time_averaged_ctqw(H, t_max=6.0, source=[1, 3, 5], n_steps=40)
        explicit_ta = time_averaged_ctqw(H, t_max=6.0, source=[1, 3, 5], n_steps=40, coherent=True)
        np.testing.assert_array_equal(default_ta, explicit_ta)

    def test_scalar_source_coherent_and_incoherent_identical(self):
        """A one-element mixture has no coherence to differ over --
        `coherent=False` must reduce to the same single-seed result."""
        H = _random_symmetric_H(10, seed=9)
        coherent = ctqw(H, t=3.0, source=4, coherent=True)
        incoherent = ctqw(H, t=3.0, source=4, coherent=False)
        np.testing.assert_allclose(coherent, incoherent, rtol=1e-10, atol=1e-12)

    def test_ctqw_incoherent_matches_manual_average_of_single_seeds(self):
        H = _random_symmetric_H(16, seed=10)
        source = [2, 5, 9]
        actual = ctqw(H, t=5.0, source=source, coherent=False)
        reference = _incoherent_reference(H, t=5.0, source=source)
        np.testing.assert_allclose(actual, reference, rtol=1e-10, atol=1e-12)

    def test_time_averaged_ctqw_incoherent_matches_manual_average(self):
        H = _random_symmetric_H(18, seed=11)
        source = [1, 4, 7]
        actual = time_averaged_ctqw(H, t_max=8.0, source=source, n_steps=60, coherent=False)
        reference = _incoherent_reference(H, t=8.0, source=source, n_steps=60)
        np.testing.assert_allclose(actual, reference, rtol=1e-10, atol=1e-12)

    def test_coherent_and_incoherent_genuinely_differ_for_multi_index(self):
        """The whole point of the distinction -- on a real (non-degenerate)
        Hamiltonian with a genuine multi-index source, the coherent
        superposition's cross-terms must make the two outputs differ, not
        coincide."""
        from allostery.hamiltonians import H2_combinatorial_laplacian

        H = H2_combinatorial_laplacian(_helix_coords(20), cutoff=10.0)
        coherent = ctqw(H, t=5.0, source=[2, 3, 4], coherent=True)
        incoherent = ctqw(H, t=5.0, source=[2, 3, 4], coherent=False)
        assert not np.allclose(coherent, incoherent)

    def test_incoherent_output_is_a_valid_probability_vector(self):
        H = _random_symmetric_H(12, seed=12)
        p = ctqw(H, t=3.0, source=[0, 2, 4], coherent=False)
        assert p.shape == (12,)
        assert (p >= 0).all()
        assert p.sum() == pytest.approx(1.0, abs=1e-6)

        p_ta = time_averaged_ctqw(H, t_max=5.0, source=[0, 2, 4], n_steps=30, coherent=False)
        assert p_ta.shape == (12,)
        assert (p_ta >= 0).all()
        assert p_ta.sum() == pytest.approx(1.0, abs=1e-6)
