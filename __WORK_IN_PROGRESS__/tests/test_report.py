"""TASK-0010 coverage -- report.py verdict template, hit list, and Jaccard
stability metric. Synthetic scores/results only, per the task's Planned
Validation.
"""
import numpy as np
import pytest

from allostery import protocol
from allostery.labels import Labels
from allostery.report import assemble_hit_list, hit_list, jaccard_stability, verdict_template


class TestHitList:
    def test_top_k_by_score_descending(self):
        scores = np.array([1.0, 5.0, 3.0, 4.0, 2.0, 0.5])
        out = hit_list(scores, k=3)
        assert list(out["indices"]) == [1, 3, 2]
        np.testing.assert_allclose(out["scores"], [5.0, 4.0, 3.0])

    def test_k_larger_than_n_truncates(self):
        scores = np.array([1.0, 2.0])
        out = hit_list(scores, k=5)
        assert len(out["indices"]) == 2

    def test_exclude_idx_removes_source_residues(self):
        scores = np.array([9.0, 8.0, 7.0, 6.0])
        out = hit_list(scores, k=2, exclude_idx=[0])
        assert 0 not in out["indices"]
        assert list(out["indices"]) == [1, 2]

    def test_resnums_mapping(self):
        scores = np.array([1.0, 3.0, 2.0])
        resnums = np.array([101, 102, 103])
        out = hit_list(scores, k=1, resnums=resnums)
        assert list(out["resnums"]) == [102]

    def test_resnums_none_when_not_given(self):
        out = hit_list(np.array([1.0, 2.0]), k=1)
        assert out["resnums"] is None


class TestAssembleHitList:
    """TASK-0079.002: labels.Labels -> hit_list's raw-array interface."""

    @staticmethod
    def _labels(active_site: np.ndarray) -> Labels:
        n = len(active_site)
        return Labels(
            pocket=np.zeros(n, dtype=bool),
            pocket_raw=np.zeros(n, dtype=bool),
            active_site=active_site,
            terminal=np.zeros(n, dtype=bool),
            functional_provenance="test",
            drug_ligand=None,
        )

    def test_active_site_residues_excluded_from_hit_list(self):
        scores = np.array([9.0, 8.0, 7.0, 6.0, 5.0])
        active_site = np.zeros(5, dtype=bool)
        active_site[0] = True  # would otherwise be the top hit
        labels = self._labels(active_site)

        out = assemble_hit_list(scores, labels, k=2)
        assert 0 not in out["indices"]
        assert list(out["indices"]) == [1, 2]

    def test_no_active_site_residues_behaves_like_plain_hit_list(self):
        scores = np.array([1.0, 5.0, 3.0])
        labels = self._labels(np.zeros(3, dtype=bool))
        out = assemble_hit_list(scores, labels, k=2)
        assert list(out["indices"]) == list(hit_list(scores, k=2)["indices"])

    def test_resnums_forwarded(self):
        scores = np.array([1.0, 3.0, 2.0])
        resnums = np.array([101, 102, 103])
        labels = self._labels(np.zeros(3, dtype=bool))
        out = assemble_hit_list(scores, labels, resnums=resnums, k=1)
        assert list(out["resnums"]) == [102]


class TestJaccardStability:
    def test_identical_hit_lists_similarity_one(self):
        result = jaccard_stability([[1, 2, 3, 4, 5], [1, 2, 3, 4, 5]])
        assert result["mean"] == pytest.approx(1.0)
        assert result["min"] == pytest.approx(1.0)

    def test_disjoint_hit_lists_similarity_zero(self):
        result = jaccard_stability([[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]])
        assert result["mean"] == pytest.approx(0.0)
        assert result["min"] == pytest.approx(0.0)

    def test_partial_overlap(self):
        # 2 shared out of 8 union -> 0.25
        result = jaccard_stability([[1, 2, 3, 4], [3, 4, 5, 6]])
        assert result["mean"] == pytest.approx(2 / 6)

    def test_single_hit_list_is_trivially_stable(self):
        result = jaccard_stability([[1, 2, 3]])
        assert result["mean"] == 1.0
        assert result["pairwise"] == []

    def test_three_way_pairwise_reports_all_combinations(self):
        result = jaccard_stability([[1, 2], [1, 2], [3, 4]])
        assert len(result["pairwise"]) == 3
        pairs = {(p["i"], p["j"]) for p in result["pairwise"]}
        assert pairs == {(0, 1), (0, 2), (1, 2)}


class TestVerdictTemplate:
    FULL_RESULTS = {
        "AUC_apo_Hnew_default": 0.70,
        "AUC_apo_H10_baseline": 0.60,
        "AUC_apo_Hnew_optimised": 0.75,
        "AUC_holo_Hnew_optimised": 0.72,
        "AUC_ctqw_mean": 0.71,
        "AUC_heat_mean": 0.65,
        "most_impactful_term": "V_R",
        "least_impactful_term": "V_M",
        "mean_rho_apo_holo": 0.6,
        "mean_jacc20": 0.4,
    }

    def test_dev_provenance_prepends_banner(self):
        text = verdict_template(self.FULL_RESULTS, provenance="dev")
        assert "NOT THE FROZEN SUBMISSION VERDICT" in text

    def test_frozen_provenance_has_no_banner(self):
        """TASK-0088: provenance="frozen" alone is no longer sufficient --
        results must also carry a stamp actually issued by
        protocol.stamp_provenance from inside a real frozen_context."""
        with protocol.frozen_context({"SOME_HELD_OUT_TARGET"}):
            stamped = protocol.stamp_provenance(self.FULL_RESULTS)
        text = verdict_template(stamped, provenance="frozen")
        assert "NOT THE FROZEN SUBMISSION VERDICT" not in text

    def test_frozen_provenance_without_a_stamp_still_shows_banner(self):
        """The pre-TASK-0088 behavior (plain provenance="frozen", no
        stamp) is now the leaky case SEAM-0004 named -- must render with
        the banner, not without it."""
        text = verdict_template(self.FULL_RESULTS, provenance="frozen")
        assert "NOT THE FROZEN SUBMISSION VERDICT" in text

    def test_headline_section_present(self):
        text = verdict_template(self.FULL_RESULTS, provenance="frozen")
        assert "HEADLINE VERDICT" in text
        assert "AUC_apo_Hnew_optimised" in text

    def test_meaningful_gain_classification(self):
        text = verdict_template(self.FULL_RESULTS, provenance="frozen")
        assert "(meaningful)" in text  # 0.75-0.60=0.15 > 0.05

    def test_marginal_gain_classification(self):
        results = dict(self.FULL_RESULTS)
        results["AUC_apo_Hnew_optimised"] = 0.63  # 0.63-0.60=0.03
        text = verdict_template(results, provenance="frozen")
        assert "(marginal)" in text

    def test_noise_level_gain_classification(self):
        results = dict(self.FULL_RESULTS)
        results["AUC_apo_Hnew_optimised"] = 0.605  # 0.005 gap
        text = verdict_template(results, provenance="frozen")
        assert "(noise-level)" in text

    def test_ctqw_genuinely_helps_classification(self):
        text = verdict_template(self.FULL_RESULTS, provenance="frozen")
        assert "CTQW genuinely helps" in text  # 0.71-0.65=0.06 > 0.05

    def test_ctqw_within_noise_classification(self):
        results = dict(self.FULL_RESULTS)
        results["AUC_ctqw_mean"] = 0.66  # 0.01 gap
        text = verdict_template(results, provenance="frozen")
        assert "within graph-kernel noise" in text

    def test_transfers_cleanly_above_threshold(self):
        text = verdict_template(self.FULL_RESULTS, provenance="frozen")
        assert "transfers cleanly" in text  # rho=0.6 > 0.5

    def test_transferability_partial_below_threshold(self):
        results = dict(self.FULL_RESULTS)
        results["mean_rho_apo_holo"] = 0.3
        text = verdict_template(results, provenance="frozen")
        assert "Transferability is partial" in text

    def test_missing_keys_render_na_and_skip_dependent_lines(self):
        text = verdict_template({}, provenance="frozen")
        assert "N/A" in text
        assert "Operator gain over H10 baseline" not in text
        assert "CTQW vs classical heat" not in text
