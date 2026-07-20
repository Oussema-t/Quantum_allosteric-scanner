"""TASK-0141 coverage -- `propagators.haken_strobl`'s new `coherent` kwarg
(closing the gap where Haken-Strobl had no incoherent-mixture source
option, unlike `ctqw`/`time_averaged_ctqw` since TASK-0118) and the new
`haken_strobl_time_averaged` function (the discrimination-relevant
time-averaged occupation this task's own Intent Contract scores, not a
single arbitrary snapshot).
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.propagators import (  # noqa: E402
    haken_strobl,
    haken_strobl_time_averaged,
    time_averaged_ctqw,
)


def _random_symmetric_H(n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(n, n))
    return (A + A.T) / 2


def _incoherent_haken_strobl_reference(H, t, gamma, source, **kwargs):
    """Slow, independent reference for the incoherent mixture: average of
    `k` separate single-seed `haken_strobl` calls (valid because the
    Lindblad equation is linear in rho -- see `_haken_strobl_rho0`'s own
    docstring), computed without reusing any of the module's internal
    helpers."""
    idx = np.atleast_1d(np.asarray(source, dtype=int))
    occs = [haken_strobl(H, t, gamma, source=int(i), coherent=True, **kwargs) for i in idx]
    return np.mean(occs, axis=0)


class TestHakenStroblCoherentKwarg:
    def test_default_is_coherent_true_byte_identical(self):
        """No pre-TASK-0141 caller passes `coherent=` -- the default must
        stay exactly the original (only) behavior."""
        H = _random_symmetric_H(10, seed=1)
        default = haken_strobl(H, t=3.0, gamma=1.0, source=[1, 3, 5])
        explicit = haken_strobl(H, t=3.0, gamma=1.0, source=[1, 3, 5], coherent=True)
        np.testing.assert_array_equal(default, explicit)

    def test_scalar_source_coherent_and_incoherent_identical(self):
        H = _random_symmetric_H(8, seed=2)
        coherent = haken_strobl(H, t=2.0, gamma=0.5, source=4, coherent=True)
        incoherent = haken_strobl(H, t=2.0, gamma=0.5, source=4, coherent=False)
        np.testing.assert_allclose(coherent, incoherent, rtol=1e-8, atol=1e-10)

    def test_coherent_and_incoherent_genuinely_differ_for_multi_index(self):
        H = _random_symmetric_H(12, seed=3)
        coherent = haken_strobl(H, t=2.0, gamma=0.3, source=[2, 3, 4], coherent=True)
        incoherent = haken_strobl(H, t=2.0, gamma=0.3, source=[2, 3, 4], coherent=False)
        assert not np.allclose(coherent, incoherent)

    def test_incoherent_matches_manual_average_of_single_seeds(self):
        """The linearity argument in `_haken_strobl_rho0`'s docstring,
        checked directly rather than trusted on derivation alone."""
        H = _random_symmetric_H(10, seed=4)
        source = [1, 4, 7]
        actual = haken_strobl(H, t=2.5, gamma=0.4, source=source, coherent=False)
        reference = _incoherent_haken_strobl_reference(H, t=2.5, gamma=0.4, source=source)
        np.testing.assert_allclose(actual, reference, rtol=1e-6, atol=1e-8)

    def test_incoherent_output_is_a_valid_probability_vector(self):
        H = _random_symmetric_H(9, seed=5)
        p = haken_strobl(H, t=3.0, gamma=1.0, source=[0, 2, 5], coherent=False)
        assert p.shape == (9,)
        assert (p >= -1e-10).all()
        assert p.sum() == pytest.approx(1.0, abs=1e-6)


class TestHakenStroblTimeAveraged:
    def test_trace_and_non_negativity(self):
        H = _random_symmetric_H(8, seed=6)
        for gamma in (0.1, 1.0, 5.0):
            p = haken_strobl_time_averaged(H, t_max=6.0, gamma=gamma, source=2, n_snapshots=20)
            assert p.shape == (8,)
            assert (p >= -1e-10).all()
            assert p.sum() == pytest.approx(1.0, abs=1e-6)

    def test_matches_manual_average_of_independent_snapshots(self):
        """Cross-checks the single-solve-with-t_eval implementation against
        the slow, obviously-correct approach: call `haken_strobl`
        independently at each snapshot time and average -- must agree
        (same physics, same trajectory, just computed once vs. many
        times) to solver tolerance, not just 'close'."""
        H = _random_symmetric_H(6, seed=7)
        t_max, n_snapshots, gamma, source = 4.0, 12, 0.7, 1
        actual = haken_strobl_time_averaged(
            H, t_max=t_max, gamma=gamma, source=source, n_snapshots=n_snapshots,
            rtol=1e-9, atol=1e-11,
        )
        # Matches the implementation's own grid exactly: t=0 excluded
        # (see `haken_strobl_time_averaged`'s docstring/inline comment).
        times = np.linspace(0.0, t_max, n_snapshots + 1)[1:]
        manual = np.mean(
            [haken_strobl(H, t=t, gamma=gamma, source=source, rtol=1e-9, atol=1e-11)
             for t in times],
            axis=0,
        )
        np.testing.assert_allclose(actual, manual, rtol=1e-4, atol=1e-5)

    def test_gamma_zero_coherent_matches_time_averaged_ctqw(self):
        """At gamma=0 the Lindblad dephasing term vanishes and the master
        equation reduces exactly to unitary evolution -- the open-system
        time-average must match the closed-form `time_averaged_ctqw` to
        the ODE solver's own tolerance, confirming the new function's
        physics against an independently-implemented (eigh-based, not
        ODE-based) propagator, not just internal self-consistency.

        `n_snapshots`/`n_steps` set generously (500, not this file's usual
        small values) and compared at `atol=1e-3`, not solver-tight
        tolerance: the two functions deliberately use offset grids
        (`haken_strobl_time_averaged` excludes `t=0`, `time_averaged_ctqw`
        includes it -- see the former's own docstring) so the two
        Riemann-sum approximations of the same continuous integral differ
        by `O(1/n)`, verified directly (~0.008 at n=40, ~0.0003 at n=1000)
        before picking these values -- not a discrepancy either function
        is wrong about."""
        H = _random_symmetric_H(7, seed=8)
        t_max, n_snapshots, source = 5.0, 500, [1, 3]
        via_ode = haken_strobl_time_averaged(
            H, t_max=t_max, gamma=0.0, source=source, n_snapshots=n_snapshots,
            coherent=True, rtol=1e-10, atol=1e-12,
        )
        via_closed_form = time_averaged_ctqw(
            H, t_max=t_max, source=source, n_steps=n_snapshots, coherent=True,
        )
        np.testing.assert_allclose(via_ode, via_closed_form, atol=1e-3)

    def test_gamma_zero_incoherent_matches_time_averaged_ctqw(self):
        """Same offset-grid caveat as the coherent test above."""
        H = _random_symmetric_H(7, seed=9)
        t_max, n_snapshots, source = 5.0, 500, [0, 2, 4]
        via_ode = haken_strobl_time_averaged(
            H, t_max=t_max, gamma=0.0, source=source, n_snapshots=n_snapshots,
            coherent=False, rtol=1e-10, atol=1e-12,
        )
        via_closed_form = time_averaged_ctqw(
            H, t_max=t_max, source=source, n_steps=n_snapshots, coherent=False,
        )
        np.testing.assert_allclose(via_ode, via_closed_form, atol=1e-3)

    def test_dephasing_time_average_approaches_uniform_once_equilibrated(self):
        """Sanity anchor matching `test_physics.py`'s own
        `test_haken_strobl_steady_state` -- but a *time average* only
        approaches the uniform steady state if `t_max` is long relative to
        the equilibration time AND the snapshot grid is fine enough that
        the single `t=0` delta-function sample (weight `1/n_snapshots` in
        this Riemann-sum-style average, same discretization convention as
        `time_averaged_ctqw`) doesn't dominate. Uses gamma=2.0
        (`test_physics.py`'s own 'mid' case, tau_eq~12.5) rather than the
        Zeno-regime gamma=20 case -- at gamma=20, tau_eq~125, and a
        `t_max` short relative to that gives a genuinely biased time
        average (verified directly while writing this test, not assumed),
        not a discretization bug."""
        import networkx as nx

        N = 5
        A = nx.adjacency_matrix(nx.path_graph(N)).toarray().astype(float)
        p = haken_strobl_time_averaged(A, t_max=300.0, gamma=2.0, source=0, n_snapshots=200)
        np.testing.assert_allclose(p, 1.0 / N, atol=0.02)
