"""TASK-0123 -- unit tests for `metrics.stratified_auc`/`stratified_auc_
summary`. No dedicated `test_metrics.py` existed before this task (`auc`/
`precision_at_k`/etc. are exercised indirectly through other modules'
tests) -- scoped to the two new functions this task adds, not a
retroactive full-module test file.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.metrics import auc, stratified_auc, stratified_auc_summary  # noqa: E402


class TestStratifiedAuc:
    def test_isolates_the_pocket_from_a_pure_distance_confound(self):
        """The core case this task exists for: scores are *exactly* a
        function of shell (mimicking real occupation-decays-with-distance
        propagator behavior) and labels happen to cluster in the nearest
        shell -- whole-graph AUC is inflated by pure distance, but no
        real within-shell signal exists (every residue in a shell has an
        identical score), so every scorable shell's stratified AUC must
        be exactly 0.5 (no discrimination possible from tied scores),
        the panel's own "observable dead" signature."""
        shells = np.array([0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2])
        scores = -shells.astype(float)  # occupation decays with distance
        labels = np.array([1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0])  # cluster near shell 0

        whole_graph_auc = auc(scores, labels)
        assert whole_graph_auc > 0.8, "fixture must actually show the confound"

        result = stratified_auc(scores, labels, shells)
        assert set(result) == {0.0, 1.0}  # shell 2 has zero positives -- excluded
        for shell_stats in result.values():
            assert shell_stats["auc"] == pytest.approx(0.5)

    def test_reveals_a_real_within_shell_signal(self):
        """Same shell/label structure as above, but this time a real,
        shell-independent signal is added on top of the distance
        baseline (positive residues score slightly higher *within their
        own shell*) -- stratified AUC in the shells that contain both
        labels must now clear 0.5, proving the metric can see real
        signal the confound would otherwise mask entirely."""
        shells = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        labels = np.array([1, 1, 0, 0, 1, 1, 0, 0])
        # distance baseline + a real within-shell bump for positives
        scores = -shells.astype(float) + 0.5 * labels

        result = stratified_auc(scores, labels, shells)
        assert set(result) == {0.0, 1.0}
        for shell_stats in result.values():
            assert shell_stats["auc"] == pytest.approx(1.0)

    def test_excludes_shells_with_no_positives_or_no_negatives(self):
        shells = np.array([0, 0, 1, 1, 1])
        labels = np.array([1, 1, 0, 0, 0])  # shell 0 all-positive, shell 1 all-negative
        scores = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        result = stratified_auc(scores, labels, shells)
        assert result == {}

    def test_respects_min_pos_min_neg_thresholds(self):
        shells = np.array([0, 0, 0, 1, 1, 1])
        labels = np.array([1, 0, 0, 1, 1, 0])
        scores = np.array([0.9, 0.1, 0.2, 0.8, 0.7, 0.1])
        # shell 0: 1 pos / 2 neg -- scorable at defaults
        # shell 1: 2 pos / 1 neg -- scorable at defaults
        default = stratified_auc(scores, labels, shells)
        assert set(default) == {0.0, 1.0}
        # requiring 2 positives excludes shell 0 (only 1 positive)
        strict = stratified_auc(scores, labels, shells, min_pos=2)
        assert set(strict) == {1.0}

    def test_n_pos_n_neg_reported_correctly(self):
        shells = np.array([0, 0, 0, 0])
        labels = np.array([1, 1, 0, 0])
        scores = np.array([0.9, 0.8, 0.2, 0.1])
        result = stratified_auc(scores, labels, shells)
        assert result[0.0]["n_pos"] == 2
        assert result[0.0]["n_neg"] == 2

    def test_returns_empty_dict_when_no_shell_is_scorable(self):
        shells = np.array([0, 0, 1, 1])
        labels = np.array([1, 1, 1, 1])  # no negatives anywhere
        scores = np.array([0.1, 0.2, 0.3, 0.4])
        assert stratified_auc(scores, labels, shells) == {}


class TestStratifiedAucSummary:
    def test_empty_input_gives_nan_not_a_crash(self):
        summary = stratified_auc_summary({})
        assert summary["n_scorable_shells"] == 0
        assert np.isnan(summary["mean_auc"])
        assert np.isnan(summary["max_auc"])
        assert summary["max_shell"] is None

    def test_picks_the_max_shell_correctly(self):
        stratified = {
            0.0: {"auc": 0.5, "n_pos": 2, "n_neg": 2},
            1.0: {"auc": 0.9, "n_pos": 2, "n_neg": 2},
            2.0: {"auc": 0.6, "n_pos": 2, "n_neg": 2},
        }
        summary = stratified_auc_summary(stratified)
        assert summary["n_scorable_shells"] == 3
        assert summary["max_auc"] == pytest.approx(0.9)
        assert summary["max_shell"] == 1.0
        assert summary["mean_auc"] == pytest.approx((0.5 + 0.9 + 0.6) / 3)

    def test_ignores_nan_shell_aucs_in_the_summary(self):
        """A shell's own AUC can itself be NaN in principle (degenerate
        within-shell labels slipping through a caller-supplied `shells`
        array that wasn't built via `stratified_auc` itself) -- the
        summary must not let a stray NaN poison mean/max."""
        stratified = {
            0.0: {"auc": float("nan"), "n_pos": 2, "n_neg": 0},
            1.0: {"auc": 0.7, "n_pos": 2, "n_neg": 2},
        }
        summary = stratified_auc_summary(stratified)
        assert summary["mean_auc"] == pytest.approx(0.7)
        assert summary["max_auc"] == pytest.approx(0.7)
        assert summary["max_shell"] == 1.0
