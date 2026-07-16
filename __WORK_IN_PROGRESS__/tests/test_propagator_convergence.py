"""TASK-0109 -- propagator convergence-validity check + synthetic
power-law characterization + literature grounding.

Covers `propagators.check_convergence`/`min_adequate_t_max`/
`min_adequate_n_steps`/`build_gapped_synthetic_network` (see that
module's own docstrings for the physics/derivation of each check) plus a
permanent reproduction of the literature bound this task cites (Aharonov,
Ambainis, Kempe & Vazirani, "Quantum Walks on Graphs," STOC 2001,
quant-ph/0012090, Lemma 4.3) and a small, fast subset of
`scripts/propagator_convergence_battery.py`'s own empirical-vs-analytic
scaling check (the full N in {20,50,100,200,500} x well_depth sweep lives
in that script, not here -- this file keeps only what a fast, deterministic
regression suite needs).
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.propagators import (  # noqa: E402
    build_gapped_synthetic_network,
    check_convergence,
    ground_state_relaxation,
    min_adequate_n_steps,
    min_adequate_t_max,
    time_averaged_ctqw,
)


class TestCheckConvergenceSpectralGap:
    """`kind="ground_state_relaxation"`: exp(-gap*t_max) <= tol."""

    def test_reproduces_task_0102_bcr_abl1_number(self):
        """TASK-0102's own precedent, done by hand: gap=0.1933,
        t_max=15.0 -> exp(-gap*t_max)=0.055. `check_convergence`
        generalizes that one-off computation -- this pins the exact
        number so a future change to the formula is caught."""
        w = np.array([0.0, 0.1933, 5.0, 8.0])
        with pytest.warns(UserWarning):
            report = check_convergence(w=w, t_max=15.0, kind="ground_state_relaxation", tol=0.01)
        assert report.checks["spectral_gap"]["gap"] == pytest.approx(0.1933)
        assert report.checks["spectral_gap"]["residual"] == pytest.approx(0.05505, abs=1e-4)
        assert report.ok is False

    def test_adequate_t_max_passes_cleanly(self):
        w = np.array([0.0, 5.0, 8.0])  # large gap -> converges fast
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            report = check_convergence(w=w, t_max=15.0, kind="ground_state_relaxation", tol=0.01)
        assert report.ok is True
        assert report.checks["spectral_gap"]["ok"] is True

    def test_strict_raises_instead_of_warning(self):
        w = np.array([0.0, 0.1933, 5.0])
        with pytest.raises(ValueError, match="check_convergence"):
            check_convergence(w=w, t_max=15.0, kind="ground_state_relaxation", tol=0.01, strict=True)

    def test_not_applicable_without_t_max(self):
        w = np.array([0.0, 0.1933, 5.0])
        report = check_convergence(w=w, kind="ground_state_relaxation")
        assert report.checks["spectral_gap"] == {"applicable": False}
        assert report.ok is True

    def test_not_applicable_with_fewer_than_two_eigenvalues(self):
        report = check_convergence(w=np.array([1.0]), t_max=15.0, kind="ground_state_relaxation")
        assert report.checks["spectral_gap"] == {"applicable": False}


class TestCheckConvergenceTimeAveragedCtqw:
    """`kind="time_averaged_ctqw"`: the AAKV-style 2/(min_gap*T) bound
    (distinct criterion from ground_state_relaxation's -- see
    `check_convergence`'s own docstring for why they must not be
    conflated)."""

    def test_small_min_gap_is_flagged(self):
        w = np.array([0.0, 1e-6, 5.0, 8.0])  # near-degenerate pair
        with pytest.warns(UserWarning):
            report = check_convergence(w=w, t_max=15.0, kind="time_averaged_ctqw", tol=0.01)
        assert report.ok is False
        assert report.checks["time_average_mixing"]["min_gap"] == pytest.approx(1e-6)

    def test_large_min_gap_and_time_passes(self):
        w = np.array([0.0, 5.0, 8.0, 12.0])
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            report = check_convergence(w=w, t_max=1000.0, kind="time_averaged_ctqw", tol=0.01)
        assert report.ok is True

    def test_unknown_kind_raises(self):
        with pytest.raises(ValueError, match="unknown kind"):
            check_convergence(w=np.array([0.0, 1.0]), t_max=1.0, kind="not_a_real_kind")


class TestCheckConvergenceNyquist:
    def test_undersampled_n_steps_is_flagged(self):
        w = np.array([0.0, 0.1933, 5.0, 8.0])  # bandwidth=8.0
        with pytest.warns(UserWarning):
            report = check_convergence(
                w=w, t_max=15.0, n_steps=5, kind="ground_state_relaxation", tol=0.01,
            )
        assert report.checks["nyquist"]["ok"] is False
        assert report.checks["nyquist"]["min_n_steps"] > 5

    def test_adequately_sampled_n_steps_passes(self):
        w = np.array([0.0, 5.0, 8.0])
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            report = check_convergence(
                w=w, t_max=15.0, n_steps=500, kind="ground_state_relaxation", tol=0.01,
            )
        assert report.checks["nyquist"]["ok"] is True

    def test_not_applicable_without_n_steps(self):
        report = check_convergence(w=np.array([0.0, 5.0]), t_max=15.0)
        assert report.checks["nyquist"] == {"applicable": False}


class TestMinAdequateHelpers:
    """`min_adequate_t_max`/`min_adequate_n_steps` are the closed-form
    inverse of `check_convergence`'s own criteria -- round-trip: the
    prescribed value must always re-pass its own check (not just
    approximately, exactly, modulo the documented floating-point
    safety margin)."""

    @pytest.mark.parametrize("kind", ["ground_state_relaxation", "time_averaged_ctqw"])
    def test_prescribed_t_max_passes_its_own_check(self, kind):
        w = np.array([0.0, 0.3, 1.7, 4.2, 9.0])
        t_star = min_adequate_t_max(w=w, kind=kind, tol=0.01)
        assert np.isfinite(t_star)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            report = check_convergence(w=w, t_max=t_star, kind=kind, tol=0.01)
        assert report.ok is True

    def test_prescribed_n_steps_passes_nyquist(self):
        """`t_max=15.0` here is not an arbitrary test fixture value -- it
        is this project's own real default (`T_MAX` in `analysis.py`/
        `ceiling.py`/`run_challenge.py`, applied to every real target/
        operator, per `REVIEW-panel-2026-07-16-v2.md` section 2.2's own
        critique: "t_max=15 is hardcoded and applied to every operator
        regardless of its energy scale"). This fixture's gap (0.3) is a
        deliberate illustration of exactly that critique, not a coincidence
        to suppress: `exp(-0.3*15)=0.0111` legitimately fails
        `check_convergence`'s spectral-gap criterion (just over the
        default `tol=0.01`) at this real default t_max -- asserted
        explicitly below, not hidden behind a blanket warnings filter --
        while this test's own subject (the Nyquist `n_steps` criterion) is
        a *separate, independent* check that this fixture does pass."""
        w = np.array([0.0, 0.3, 1.7, 4.2, 9.0])
        n_star = min_adequate_n_steps(w=w, t_max=15.0)
        with pytest.warns(UserWarning, match="ground_state_relaxation at t_max=15"):
            report = check_convergence(w=w, t_max=15.0, n_steps=n_star, kind="ground_state_relaxation")
        assert report.checks["nyquist"]["ok"] is True
        assert report.checks["spectral_gap"]["ok"] is False, (
            "this fixture's gap should legitimately fail the spectral-gap "
            "criterion at the real T_MAX=15.0 default -- if this ever starts "
            "passing, the fixture no longer illustrates the review panel's point"
        )

    def test_degenerate_spectrum_returns_infinite_t_max(self):
        w = np.array([1.0, 1.0, 1.0])  # zero gap
        assert min_adequate_t_max(w=w, kind="ground_state_relaxation") == np.inf

    def test_single_eigenvalue_returns_infinite_t_max(self):
        assert min_adequate_t_max(w=np.array([1.0]), kind="ground_state_relaxation") == np.inf

    def test_flat_spectrum_returns_n_steps_one(self):
        assert min_adequate_n_steps(w=np.array([1.0, 1.0]), t_max=15.0) == 1

    def test_needs_h_or_w(self):
        with pytest.raises(ValueError, match="needs either"):
            min_adequate_t_max(kind="ground_state_relaxation")
        with pytest.raises(ValueError, match="needs either"):
            min_adequate_n_steps(t_max=15.0)
        with pytest.raises(ValueError, match="needs either"):
            check_convergence(t_max=15.0)


class TestBuildGappedSyntheticNetwork:
    """Construction sanity -- not physics assertions, mirrors TASK-0103's
    own `TestBuildDumbbellNetwork` pattern for the same kind of reusable
    synthetic-construction helper."""

    def test_shape_and_symmetry(self):
        H = build_gapped_synthetic_network(30, 5.0, seed=0)
        assert H.shape == (30, 30)
        np.testing.assert_allclose(H, H.T)

    def test_seeds_actually_vary_the_network(self):
        H0 = build_gapped_synthetic_network(30, 5.0, seed=0)
        H1 = build_gapped_synthetic_network(30, 5.0, seed=1)
        assert not np.allclose(H0, H1)

    def test_well_depth_increases_the_gap(self):
        """The one property this construction exists for: `well_depth` is
        this task's chosen lever for controlling the spectral gap
        independent of `N` -- confirm it actually does, monotonically,
        for a representative `N`."""
        gaps = []
        for depth in [0.0, 5.0, 20.0, 100.0]:
            H = build_gapped_synthetic_network(50, depth, seed=0)
            w = np.linalg.eigvalsh(H)
            gaps.append(w[1] - w[0])
        assert gaps == sorted(gaps), f"gap not monotonic in well_depth: {gaps}"

    def test_too_small_n_raises(self):
        with pytest.raises(ValueError, match="too small"):
            build_gapped_synthetic_network(2, 1.0)


class TestLiteratureReproductionAAKV:
    """Reproduces Aharonov-Ambainis-Kempe-Vazirani (STOC 2001,
    quant-ph/0012090) Lemma 4.3's convergence mechanism -- the discrete-
    time walk's own bound is `||P_bar_T - pi|| <= 2 sum_{i,j: lambda_i!=
    lambda_j} |a_i|^2/(T|lambda_i-lambda_j|)`; the continuous-time analog
    this module derives and uses (`check_convergence`'s own docstring,
    section 3) is `<= 2/(min_gap*T)`. This test verifies that bound is a
    real, honest upper bound on `time_averaged_ctqw`'s actual numerical
    error against the true infinite-time limit -- not merely that the
    formula is coded correctly (a unit test could pass with a bug in the
    physics), but that the *cited criterion's prediction holds on real
    data*, this task's own explicit Planned Validation requirement.

    Uses a small (N=10) generic random symmetric H (not `build_gapped_
    synthetic_network`'s ring topology): found empirically 2026-07-15
    that the ring construction's near-degenerate eigenvalue pairs (min
    gap ~1/N^2, see `scripts/propagator_convergence_battery.py`'s own
    `T_MAX_SCAN_CAP` comment) make the bound's prediction impractically
    large to scan at any battery-relevant N -- itself a real, reported
    finding about this criterion's fragility, not swept under the rug
    (see this task's Done section) -- so this dedicated reproduction
    uses a topology where the bound is informative instead.
    """

    def test_aakv_bound_upper_bounds_actual_convergence_error(self):
        rng = np.random.default_rng(0)
        N = 10
        A = rng.uniform(-1.0, 1.0, (N, N))
        H = (A + A.T) / 2.0
        w, v = np.linalg.eigh(H)
        gaps = np.abs(w[:, None] - w[None, :])
        nonzero = gaps[gaps > 1e-9]
        min_gap = float(nonzero.min())
        assert min_gap > 0.05, "test fixture's own sanity check: needs a non-degenerate spectrum"

        source = 0
        true_limit = (v ** 2) @ (v[source, :] ** 2)
        true_limit /= true_limit.sum()

        violations = []
        for T in [1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0]:
            n_steps = max(int(np.ceil(T * (w[-1] - w[0]) / np.pi)) + 1, 50)
            p = time_averaged_ctqw(H, T, source=source, n_steps=n_steps)
            actual_tv = float(np.abs(p - true_limit).sum() / 2.0)
            predicted_bound = 2.0 / (min_gap * T)
            if actual_tv > predicted_bound:
                violations.append((T, actual_tv, predicted_bound))

        assert not violations, f"AAKV-style bound violated at: {violations}"

    def test_both_actual_error_and_bound_decay_with_time(self):
        """The bound's own qualitative prediction (not just "always an
        upper bound," which a trivially-loose bound could satisfy):
        both the true error and the predicted ceiling should shrink as
        T grows."""
        rng = np.random.default_rng(1)
        N = 8
        A = rng.uniform(-1.0, 1.0, (N, N))
        H = (A + A.T) / 2.0
        w, v = np.linalg.eigh(H)
        source = 0
        true_limit = (v ** 2) @ (v[source, :] ** 2)
        true_limit /= true_limit.sum()

        errs = []
        for T in [2.0, 20.0, 200.0]:
            n_steps = max(int(np.ceil(T * (w[-1] - w[0]) / np.pi)) + 1, 50)
            p = time_averaged_ctqw(H, T, source=source, n_steps=n_steps)
            errs.append(float(np.abs(p - true_limit).sum() / 2.0))
        assert errs[0] > errs[1] > errs[2], f"error did not monotonically decay with T: {errs}"


class TestEmpiricalVsAnalyticGsrScaling:
    """Fast, deterministic subset of `scripts/propagator_convergence_
    battery.py`'s own empirical-vs-analytic characterization: confirms
    the *direction and rough magnitude* of the closed-form t_max
    prediction against a real numerical convergence search, on a small
    grid (not the full N in {20..500} sweep, which belongs in that
    script, not a fast test suite)."""

    def test_analytic_prediction_is_in_the_right_ballpark(self):
        for depth in [0.0, 5.0, 20.0]:
            H = build_gapped_synthetic_network(30, depth, seed=0)
            w, v = np.linalg.eigh(H)
            analytic_t = min_adequate_t_max(w=w, kind="ground_state_relaxation", tol=0.05)

            true_limit = np.clip(v[:, 0] * v[0, 0], 0.0, None)
            true_limit /= true_limit.sum() + 1e-300
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                p_at_analytic_t = ground_state_relaxation(H, analytic_t, source=0)
            tv_at_analytic_t = float(np.abs(p_at_analytic_t - true_limit).sum() / 2.0)
            assert tv_at_analytic_t <= 0.05 + 1e-6, (
                f"depth={depth}: analytic t_max={analytic_t:.3g} did not actually "
                f"achieve its own predicted tolerance (tv={tv_at_analytic_t:.4g})"
            )
