"""TASK-0009 coverage -- diagnostics.py operator diagnostics + failure-mode
classifier. Synthetic operators/labels only, each constructed to trigger
one category deliberately, per the task's Planned Validation.
"""
import numpy as np
import pytest

from allostery.diagnostics import (
    INSUFFICIENT_RESOLUTION,
    LABEL_SUSPECT,
    NO_FAILURE_DETECTED,
    NO_SIGNAL_IN_APO,
    OPERATOR_DEGENERATE,
    classify_failure,
    operator_diagnostics,
)
from allostery.hamiltonians import build_H_new


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
