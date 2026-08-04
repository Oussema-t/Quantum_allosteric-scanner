"""TASK-0199 coverage -- observable_effective_rank.py's own new logic
(alignment assertion, correlation-matrix/rank computation, confound
projection) plus the Planned Validation's positive/negative controls on
synthetic data. Per-observable scoring functions themselves (dcc_low,
transmission_from_source, etc.) are already tested elsewhere -- this
file covers only what this script adds. Synthetic data only, no network.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from observable_effective_rank import (  # noqa: E402
    align_and_stack,
    correlation_matrix_and_rank,
    run_controls,
)


class TestAlignAndStack:
    def test_aligned_vectors_stack_cleanly(self):
        observables = {"a": np.arange(10.0), "b": np.arange(10.0)[::-1], "c": np.ones(10)}
        names, matrix = align_and_stack(observables)
        assert names == ["a", "b", "c"]
        assert matrix.shape == (10, 3)

    def test_misaligned_lengths_raise(self):
        """The exact defect this task's own Constraint names as 'the
        obvious failure mode' -- e.g. an H13-shaped 3N vector silently
        correlated against N-length ones. Must raise, not silently
        truncate or broadcast."""
        observables = {"a": np.arange(10.0), "b": np.arange(30.0)}
        with pytest.raises(ValueError, match="misaligned"):
            align_and_stack(observables)


class TestCorrelationMatrixAndRank:
    def test_identical_columns_give_rank_one(self):
        rng = np.random.default_rng(0)
        base = rng.normal(size=200)
        matrix = np.column_stack([base, base, base, base])
        report = correlation_matrix_and_rank(matrix)
        assert report["participation_ratio_rank"] == pytest.approx(1.0, abs=1e-6)
        assert report["variance_explained_90"] == 1

    def test_independent_columns_give_near_full_rank(self):
        """Negative control (Planned Validation): N independent random
        score vectors -> effective rank ~= N."""
        rng = np.random.default_rng(1)
        N_OBS, N_RESIDUES = 12, 500
        matrix = rng.normal(size=(N_RESIDUES, N_OBS))
        report = correlation_matrix_and_rank(matrix)
        # Finite-sample Spearman noise keeps this a few units below N_OBS,
        # not exactly N_OBS -- a wide, honest tolerance, not a tight one
        # that would be sensitive to the rng seed.
        assert report["participation_ratio_rank"] >= N_OBS - 3
        assert report["variance_explained_95"] >= N_OBS - 4

    def test_eff_rank_and_participation_ratio_both_reported(self):
        rng = np.random.default_rng(2)
        matrix = rng.normal(size=(100, 6))
        report = correlation_matrix_and_rank(matrix)
        assert "participation_ratio_rank" in report
        assert "eff_rank_entropy" in report
        assert 1.0 <= report["participation_ratio_rank"] <= report["M"]


class TestPositiveControlOnNearUniformBase:
    """The strict, textbook '+1 for an orthogonal addition' check --
    run here on a controlled, near-uniform base matrix (unlike
    `observable_effective_rank.run_controls`'s own real-data version,
    which found and documented that this exact intuition does not hold
    numerically on a highly-skewed real spectrum -- a property of the
    formula, not a bug, verified in that script's own docstring)."""

    def test_orthogonal_addition_raises_rank_by_about_one_on_uniform_base(self):
        rng = np.random.default_rng(3)
        n_residues = 2000
        n_obs = 6
        # Near-uniform base: 6 independent random columns (correlation
        # matrix close to identity, not dominated by one huge eigenvalue).
        base = rng.normal(size=(n_residues, n_obs))
        base_rank = correlation_matrix_and_rank(base)["participation_ratio_rank"]

        orthogonal = rng.normal(size=n_residues)
        extended = np.column_stack([base, orthogonal])
        extended_rank = correlation_matrix_and_rank(extended)["participation_ratio_rank"]

        assert extended_rank - base_rank == pytest.approx(1.0, abs=0.5)

    def test_duplicate_addition_does_not_raise_rank(self):
        rng = np.random.default_rng(4)
        base = rng.normal(size=(2000, 6))
        base_rank = correlation_matrix_and_rank(base)["participation_ratio_rank"]
        duplicate = np.column_stack([base, base[:, 0]])
        duplicate_rank = correlation_matrix_and_rank(duplicate)["participation_ratio_rank"]
        assert duplicate_rank <= base_rank + 0.1


class TestRunControlsOnRealisticSkewedMatrix:
    """Reproduces the exact real-data finding (documented in
    `observable_effective_rank.run_controls`'s own docstring): on a
    matrix with one dominant component among many observables, the
    orthogonal-addition delta is small but still positive and
    measurable -- confirming `run_controls`'s own looser, direction-based
    tolerance is correct, not a cover for a broken statistic."""

    def test_controls_pass_on_a_skewed_synthetic_matrix(self):
        rng = np.random.default_rng(5)
        n_residues, n_obs = 500, 20
        shared = rng.normal(size=n_residues)
        # 20 observables all mostly following one shared signal plus a
        # little independent noise each -- mimics a low-rank real matrix.
        matrix = np.column_stack([shared + 0.1 * rng.normal(size=n_residues) for _ in range(n_obs)])
        report = correlation_matrix_and_rank(matrix)
        assert report["participation_ratio_rank"] < 3.0  # genuinely low-rank by construction

        controls = run_controls(matrix)
        assert controls["duplicate_control_ok"] is True
        assert controls["random_control_ok"] is True
        assert controls["random_delta"] < 1.0  # small, per the documented skewed-spectrum property
