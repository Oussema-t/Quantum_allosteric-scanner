"""TASK-0010 coverage -- report.py verdict template, hit list, and Jaccard
stability metric. Synthetic scores/results only, per the task's Planned
Validation.
"""
import numpy as np
import pytest

from allostery import protocol
from allostery.labels import Labels
from allostery.report import assemble_hit_list, hit_list, jaccard_stability, no_ground_truth_report, verdict_template


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

    def test_decoherent_limit_disclosure_present_before_the_auc_values(self):
        """TASK-0097 / REVIEW-2026-07-13 P2-B: a reader must encounter the
        "this is the decoherent/time-averaged limit, not a coherent walk"
        disclosure alongside the AUC numbers, not buried in a code comment
        only -- and specifically *before* the values, not after."""
        text = verdict_template(self.FULL_RESULTS, provenance="frozen")
        assert "decoherent" in text
        assert "not a coherent quantum-walk snapshot" in text

        headline_idx = text.index("HEADLINE VERDICT")
        disclosure_idx = text.index("decoherent")
        first_value_idx = text.index("AUC_apo_Hnew_default")
        assert headline_idx < disclosure_idx < first_value_idx

    def test_decoherent_limit_disclosure_present_even_with_no_results(self):
        """The disclosure is about what the metric *is*, not about which
        keys happen to be populated -- must render unconditionally."""
        text = verdict_template({}, provenance="frozen")
        assert "decoherent" in text

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

    def test_ci_overlap_caveats_a_meaningful_gain(self):
        """TASK-0370 (external adversarial review, item 6): a shipped report
        called a gain "meaningful"/"CTQW genuinely helps" in its
        DECISION-SUPPORT section while the HEADLINE block, a few lines
        above in the same file, already said NO_SIGNAL_IN_APO with
        overlapping CIs -- contradicting the Concept Proposal's own
        disclosed negative. Both qualifying lines must carry the
        reconciling caveat when `_diagnosis_ci_overlap` is True."""
        results = dict(self.FULL_RESULTS)
        results["_diagnosis_ci_overlap"] = True
        text = verdict_template(results, provenance="frozen")
        assert "(meaningful)" in text
        assert "CTQW genuinely helps" in text
        assert text.count("not statistically distinguishable from the trivial floor") == 2

    def test_no_ci_overlap_key_leaves_lines_unqualified(self):
        """Backward compatibility: a `results` dict with no
        `_diagnosis_ci_overlap` key (e.g. no diagnosis was computed at all)
        renders exactly as before -- the caveat is additive, not a change
        to the default rendering."""
        text = verdict_template(self.FULL_RESULTS, provenance="frozen")
        assert "not statistically distinguishable" not in text

    def test_ci_overlap_false_leaves_lines_unqualified(self):
        results = dict(self.FULL_RESULTS)
        results["_diagnosis_ci_overlap"] = False
        text = verdict_template(results, provenance="frozen")
        assert "not statistically distinguishable" not in text

    def test_ci_overlap_does_not_caveat_a_noise_level_gain(self):
        """A gain already classified "noise-level" needs no reconciling
        caveat -- it never claimed anything to reconcile."""
        results = dict(self.FULL_RESULTS)
        results["AUC_apo_Hnew_optimised"] = 0.605  # 0.005 gap -> noise-level
        results["_diagnosis_ci_overlap"] = True
        text = verdict_template(results, provenance="frozen")
        assert "(noise-level)" in text
        line1 = next(l for l in text.split("\n") if l.startswith("1)"))
        assert "not statistically distinguishable" not in line1

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
        assert "CTQW vs ground-state relaxation" not in text

    def test_no_header_by_default(self):
        """Backward compatibility: omitting target_name/structure renders
        exactly as before -- additive, not a new requirement on callers."""
        text = verdict_template(self.FULL_RESULTS, provenance="frozen")
        assert "Target:" not in text

    def test_target_and_structure_header_when_given(self):
        """TASK-0370 (external adversarial review, item 25): "three of four
        [shipped report.txt] files have no target or PDB header." Header
        renders before HEADLINE VERDICT when the caller supplies it."""
        text = verdict_template(
            self.FULL_RESULTS, provenance="frozen",
            target_name="KRAS_G12C", structure="4LDJ (apo)",
        )
        assert "Target: KRAS_G12C" in text
        assert "Structure: 4LDJ (apo)" in text
        assert text.index("Target:") < text.index("HEADLINE VERDICT")

    def test_line_2_never_claims_classical_diffusion(self):
        """TASK-0095 / REVIEW-2026-07-13 P1-B: the AUC_heat_mean side of
        this comparison is propagators.ground_state_relaxation's score on
        (usually indefinite) H_new, not classical diffusion -- the report
        must never say so, with or without a full results dict."""
        text = verdict_template(self.FULL_RESULTS, provenance="frozen")
        assert "classical heat" not in text
        assert "classical diffusion" not in text
        assert "CTQW vs ground-state relaxation" in text


class TestResultsMdDecoherentDisclosure:
    """TASK-0097 / REVIEW-2026-07-13 P2-B, Acceptance Scenario: a reader of
    RESULTS.md's AUC tables must encounter the decoherent-limit disclosure
    before or alongside the numbers, not buried in a code comment only.
    Turns this task's own "manual review" Planned Validation into a durable
    check, same practice as TASK-0095's grep-based framing test."""

    def test_disclosure_present_before_the_first_auc_table(self):
        from pathlib import Path

        results_md = Path(__file__).resolve().parent.parent / "RESULTS.md"
        assert results_md.exists()
        text = results_md.read_text()

        assert "decoherent" in text
        assert "not a coherent quantum-walk snapshot" in text

        disclosure_idx = text.index("decoherent")
        first_table_idx = text.index("### KRAS_G12C")
        assert disclosure_idx < first_table_idx, (
            "decoherent-limit disclosure must appear before the first AUC "
            "table, not after it"
        )


# ---------------------------------------------------------------------------
# no_ground_truth_report (TASK-0080 -- c-Myc/1NKP)
# ---------------------------------------------------------------------------

def _synth_consensus(n=6, k=3):
    consensus_count = np.array([4, 4, 2, 1, 0, 0])
    mean_occupancy = np.array([0.30, 0.25, 0.15, 0.10, 0.10, 0.10])
    order = np.lexsort((-mean_occupancy, -consensus_count))[:k]
    return {
        "operators": ["H_new_default", "H10_disorder_suppressed", "H2_combinatorial_laplacian", "H14_anm_pinv_trace"],
        "occupancy": {},
        "top_k_per_operator": {},
        "consensus_count": consensus_count,
        "mean_occupancy": mean_occupancy,
        "consensus_ranked_indices": order,
        "n_operators": 4,
        "k": k,
    }


class TestNoGroundTruthReport:
    def test_never_mentions_auc_or_ceiling(self):
        text = no_ground_truth_report("MYC_MAX", _synth_consensus(), {"error": "fpocket binary not found on PATH"})
        assert "AUC" not in text.replace("No AUC", "")  # the one deliberate mention is the disclosure itself
        assert "no auc" in text.lower()

    def test_states_the_reason_explicitly(self):
        text = no_ground_truth_report(
            "MYC_MAX", _synth_consensus(), {"error": "x"},
            reason="no holo/bound structure exists for this allosteric question",
        )
        assert "no holo/bound structure exists" in text

    def test_renders_consensus_ranked_hits_with_resnums(self):
        resnums = np.array([101, 102, 103, 104, 105, 106])
        text = no_ground_truth_report("MYC_MAX", _synth_consensus(), {"error": "x"}, resnums=resnums)
        assert "residue 101" in text
        assert "residue 102" in text
        assert "4/4" in text

    def test_full_agreement_reads_unverified_not_high(self):
        """TASK-0370 (external adversarial review, item 6): full cross-operator
        agreement used to render "Confidence: high", which the Concept
        Proposal itself contradicts by calling this target's prediction
        "unverified" -- agreement among operators the CP's own §2 measures
        as correlated distance detectors is not validated confidence."""
        text = no_ground_truth_report("MYC_MAX", _synth_consensus(), {"error": "x"})
        assert "Confidence: unverified" in text
        assert "Confidence: high" not in text
        assert "not validated confidence" in text

    def test_docking_error_rendered_honestly_not_hidden(self):
        text = no_ground_truth_report(
            "MYC_MAX", _synth_consensus(), {"error": "fpocket binary not found on PATH"},
        )
        assert "unavailable -- fpocket binary not found on PATH" in text

    def test_docking_pockets_rendered_when_present(self):
        docking = {"pockets": [{"id": 1, "score": 0.7, "druggability_score": 0.5}]}
        text = no_ground_truth_report("MYC_MAX", _synth_consensus(), docking)
        assert "pocket 1" in text
        assert "druggability_score=0.5" in text
