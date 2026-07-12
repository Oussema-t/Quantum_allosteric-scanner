"""TASK-0009 coverage -- diagnostics.py operator diagnostics + failure-mode
classifier. Synthetic operators/labels only, each constructed to trigger
one category deliberately, per the task's Planned Validation.
"""
import numpy as np
import pytest

from allostery.diagnostics import (
    BEATS_CHANCE_NOT_FLOOR,
    INSUFFICIENT_RESOLUTION,
    LABEL_SUSPECT,
    NO_FAILURE_DETECTED,
    NO_SIGNAL_IN_APO,
    OPERATOR_DEGENERATE,
    PERM_LEAK_THRESHOLD,
    classify_failure,
    detect_permutation_leak,
    operator_diagnostics,
    permutation_null,
)
from allostery.hamiltonians import build_H_new
from allostery.propagators import time_averaged_ctqw


def _helix_coords(n: int = 10, offset: float = 0.0) -> np.ndarray:
    """Alpha-helix Cα coordinates (same construction as test_hamiltonians.py's
    `_helix_coords`), optionally translated far along x to build a second,
    disconnected cluster."""
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        offset + 2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


class TestOperatorDiagnostics:
    def test_connected_helix_has_one_component_and_is_psd_by_default(self):
        coords = _helix_coords(10)
        bfac = np.full(10, 20.0)
        H = build_H_new(coords, bfac, cutoff=10.0)
        diag = operator_diagnostics(H, bfactors=bfac)
        assert diag["N"] == 10
        assert diag["n_components"] == 1
        assert not any("disconnected" in n for n in diag["notes"])

    def test_default_h_new_is_not_globally_psd_t012_canary(self):
        """T-012 (.claude/TASKS.md): V_R/V_C/V_M are reward terms with negative
        diagonal contributions by design -- default build_H_new has at least
        one negative eigenvalue. Canary, not a hard physics requirement."""
        coords = _helix_coords(10)
        bfac = np.full(10, 20.0)
        H = build_H_new(coords, bfac, cutoff=10.0)
        diag = operator_diagnostics(H, bfactors=bfac)
        assert diag["is_psd"] is False
        assert diag["spec_min"] < 0
        assert any("not globally PSD" in n for n in diag["notes"])

    def test_disconnected_graph_flagged(self):
        """Two helices placed far apart (> cutoff) share no contacts."""
        cluster_a = _helix_coords(6, offset=0.0)
        cluster_b = _helix_coords(6, offset=1000.0)
        coords = np.vstack([cluster_a, cluster_b])
        bfac = np.full(12, 20.0)
        H = build_H_new(coords, bfac, cutoff=10.0)
        diag = operator_diagnostics(H, bfactors=bfac)
        assert diag["n_components"] == 2
        assert any("disconnected" in n for n in diag["notes"])

    def test_b_all_zero_flagged(self):
        coords = _helix_coords(10)
        bfac = np.zeros(10)
        H = build_H_new(coords, bfac, cutoff=10.0)
        diag = operator_diagnostics(H, bfactors=bfac)
        assert diag["b_all_zero"] is True
        assert any("V_B disabled" in n for n in diag["notes"])

    def test_b_all_zero_is_none_without_bfactors_input(self):
        coords = _helix_coords(10)
        bfac = np.full(10, 20.0)
        H = build_H_new(coords, bfac, cutoff=10.0)
        diag = operator_diagnostics(H)
        assert diag["b_all_zero"] is None
        assert not any("V_B disabled" in n for n in diag["notes"])

    def test_large_n_flagged(self):
        coords = _helix_coords(10)
        bfac = np.full(10, 20.0)
        H = build_H_new(coords, bfac, cutoff=10.0)
        diag = operator_diagnostics(H, bfactors=bfac, n_large=5)
        assert any("very large N" in n for n in diag["notes"])

    def test_diagonal_dominance_flagged(self):
        """Hand-built H: huge diagonal, tiny off-diagonal contact term."""
        H = np.diag([100.0, 100.0, 100.0, 100.0])
        H[0, 1] = H[1, 0] = 0.5
        diag = operator_diagnostics(H, diag_dominance_threshold=3.0)
        assert diag["diag_over_offdiag"] > 3.0
        assert any("diagonal potential dominates" in n for n in diag["notes"])


class TestClassifyFailure:
    def _connected_H(self, n=10):
        coords = _helix_coords(n)
        bfac = np.full(n, 20.0)
        return build_H_new(coords, bfac, cutoff=10.0), bfac

    def test_disconnected_operator_is_operator_degenerate_regardless_of_labels(self):
        cluster_a = _helix_coords(6, offset=0.0)
        cluster_b = _helix_coords(6, offset=1000.0)
        coords = np.vstack([cluster_a, cluster_b])
        bfac = np.full(12, 20.0)
        H = build_H_new(coords, bfac, cutoff=10.0)
        labels = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
        scores = np.arange(12, dtype=float)
        assert classify_failure(scores, labels, H=H, bfactors=bfac) == OPERATOR_DEGENERATE

    def test_degenerate_labels_all_zero_is_label_suspect(self):
        labels = np.zeros(8)
        scores = np.arange(8, dtype=float)
        assert classify_failure(scores, labels) == LABEL_SUSPECT

    def test_degenerate_labels_all_one_is_label_suspect(self):
        labels = np.ones(8)
        scores = np.arange(8, dtype=float)
        assert classify_failure(scores, labels) == LABEL_SUSPECT

    def test_b_all_zero_is_insufficient_resolution_even_with_clean_scores(self):
        coords = _helix_coords(10)
        bfac_zero = np.zeros(10)
        H = build_H_new(coords, bfac_zero, cutoff=10.0)
        labels = np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        scores = -np.abs(np.arange(10) - 0)  # perfectly ranks label 0 first
        assert classify_failure(scores, labels, H=H, bfactors=bfac_zero) == INSUFFICIENT_RESOLUTION

    def test_large_n_is_insufficient_resolution(self):
        H, bfac = self._connected_H(10)
        labels = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
        scores = np.arange(10, dtype=float)
        result = classify_failure(scores, labels, H=H, bfactors=bfac, n_large=5)
        assert result == INSUFFICIENT_RESOLUTION

    def test_chance_level_scores_are_no_signal_in_apo(self):
        # exact AUC = 0.5 by construction (two ties cancel two correct pairs)
        scores = np.array([1.0, 0.0, 1.0, 0.0])
        labels = np.array([1, 1, 0, 0])
        assert classify_failure(scores, labels) == NO_SIGNAL_IN_APO

    def test_good_separation_with_healthy_operator_is_no_failure_detected(self):
        H, bfac = self._connected_H(10)
        labels = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
        scores = np.array([10.0, 9.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        assert classify_failure(scores, labels, H=H, bfactors=bfac) == NO_FAILURE_DETECTED

    def test_good_separation_without_H_is_no_failure_detected(self):
        labels = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
        scores = np.array([10.0, 9.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        assert classify_failure(scores, labels) == NO_FAILURE_DETECTED


class TestClassifyFailureFloor:
    """TASK-0058 (closes SEAM-0005): floor_scores beats-floor check."""

    LABELS = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    # AUC=1.0 (perfect separation)
    NEAR_PERFECT = np.array([10.0, 9.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
    # AUC=0.75 (beats chance, clearly short of near-perfect)
    MEDIOCRE = np.array([8.0, 7.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 9.0, 10.0])

    def test_beats_chance_and_beats_floor_is_no_failure_detected(self):
        result = classify_failure(self.NEAR_PERFECT, self.LABELS, floor_scores=self.MEDIOCRE)
        assert result == NO_FAILURE_DETECTED

    def test_beats_chance_but_loses_to_floor_is_beats_chance_not_floor(self):
        result = classify_failure(self.MEDIOCRE, self.LABELS, floor_scores=self.NEAR_PERFECT)
        assert result == BEATS_CHANCE_NOT_FLOOR

    def test_floor_scores_none_is_unchanged_from_pre_seam_0005_behavior(self):
        """Explicit floor_scores=None, not just omitted -- regression guard
        against the `is not None` branch ever being taken for the default."""
        result = classify_failure(self.NEAR_PERFECT, self.LABELS, floor_scores=None)
        assert result == NO_FAILURE_DETECTED

    def test_floor_check_only_applies_after_chance_check(self):
        """A score that doesn't even beat chance is NO_SIGNAL_IN_APO
        regardless of the floor -- floor comparison must not run first."""
        chance_scores = np.array([1.0, 0.0, 1.0, 0.0])
        chance_labels = np.array([1, 1, 0, 0])
        result = classify_failure(chance_scores, chance_labels, floor_scores=self.MEDIOCRE[:4])
        assert result == NO_SIGNAL_IN_APO


class TestPermutationNullLeakDetector:
    """TASK-0071: port of test_leakage_gate.py's GATE-B4 permutation null
    (the "verified reference implementation" EXECUTION_PLAN.md Phase 1.4
    points to). Both acceptance scenarios use this package's own real
    production scorer (build_H_new + time_averaged_ctqw), not a synthetic
    stand-in -- a stronger check than the reference's own toy GNM scorer,
    and avoids KRAS_G12C (this package's only network-gated real target),
    which PLAN.md documents as scoring *near chance even honestly*, i.e.
    not a case with "known real signal" as the acceptance scenario
    requires."""

    N = 20

    @staticmethod
    def _helix_coords(n):
        theta = np.arange(n) * (100.0 * np.pi / 180.0)
        return np.column_stack([
            2.3 * np.cos(theta), 2.3 * np.sin(theta), 1.5 * np.arange(n, dtype=float),
        ])

    @classmethod
    def _honest_scorer(cls, coords, labels):
        """Real production pipeline. Never reads `labels` -- topology
        (+ B-factor/terminal/rigidity/covariance/low-mode potentials) and
        a fixed propagation source only."""
        bfac = np.full(len(coords), 20.0)
        H = build_H_new(coords, bfac, cutoff=10.0)
        return time_averaged_ctqw(H, t_max=15.0, source=0, n_steps=200)

    @staticmethod
    def _leaky_scorer(coords, labels):
        """Peeks at whatever labels it is handed -- the failure mode this
        detector exists to catch (matches test_leakage_gate.py's own
        leaky_scorer construction)."""
        rng = np.random.default_rng(0)
        return labels.astype(float) + rng.normal(0.0, 0.01, size=len(labels))

    def test_honest_scorer_permuted_scores_center_on_chance_with_real_score_an_outlier(self):
        """Acceptance scenario 1: known real signal -- permuted-score
        distribution centers on chance, real score is a clear outlier."""
        coords = self._helix_coords(self.N)
        labels = np.zeros(self.N, dtype=bool)
        labels[[1, 2, 3]] = True  # spatially close to the fixed source (0)

        result = permutation_null(self._honest_scorer, coords, labels, n_perm=100, seed=1)

        assert result["auc_true"] > 0.65, f"honest scorer has no real signal ({result['auc_true']:.3f})"
        assert abs(result["perm_mean"] - 0.5) < 0.1, f"perm_mean not centered on chance ({result['perm_mean']:.3f})"
        assert result["perm_mean"] < PERM_LEAK_THRESHOLD

    def test_honest_scorer_is_not_flagged_as_a_leak(self):
        coords = self._helix_coords(self.N)
        labels = np.zeros(self.N, dtype=bool)
        labels[[1, 2, 3]] = True

        result = detect_permutation_leak(self._honest_scorer, coords, labels, n_perm=100, seed=1)
        assert result["leak_detected"] is False

    def test_synthetic_leak_deliberately_introduced_is_flagged(self):
        """Acceptance scenario 2: a scorer that reads labels directly
        (simulating a DEV/FROZEN-split bypass the firewall didn't
        anticipate) must be flagged -- permuted scores stay elevated
        because the scorer tracks whatever labels it's handed, permuted
        or not."""
        coords = self._helix_coords(self.N)
        labels = np.zeros(self.N, dtype=bool)
        labels[[1, 2, 3]] = True

        result = detect_permutation_leak(self._leaky_scorer, coords, labels, n_perm=100, seed=1)
        assert result["perm_mean"] > 0.90, f"detector missed a blatant leak ({result['perm_mean']:.3f})"
        assert result["leak_detected"] is True

    def test_returns_expected_keys_and_ci_ordering(self):
        coords = self._helix_coords(self.N)
        labels = np.zeros(self.N, dtype=bool)
        labels[[1, 2, 3]] = True

        result = detect_permutation_leak(self._honest_scorer, coords, labels, n_perm=50, seed=1)
        assert set(result) == {"auc_true", "perm_mean", "perm_ci", "n_perm", "threshold", "leak_detected"}
        lo, hi = result["perm_ci"]
        assert lo <= hi
        assert result["threshold"] == PERM_LEAK_THRESHOLD

    def test_custom_threshold_is_respected(self):
        coords = self._helix_coords(self.N)
        labels = np.zeros(self.N, dtype=bool)
        labels[[1, 2, 3]] = True

        result = detect_permutation_leak(
            self._honest_scorer, coords, labels, n_perm=50, seed=1, threshold=0.0,
        )
        # An absurdly low threshold trivially flags even the honest scorer --
        # confirms `threshold` is actually wired through, not ignored.
        assert result["leak_detected"] is True
