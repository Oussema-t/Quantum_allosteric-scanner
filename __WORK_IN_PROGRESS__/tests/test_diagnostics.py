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
    FailureClassification,
    assert_gate_reachable,
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
        """Note wording corrected 2026-07-14: LARGE_N_THRESHOLD's original
        "anisotropic ANM channel may dominate" claim had no derivation
        anywhere (checked directly against its cited notebook source) --
        the note now describes a computational-scaling ceiling, not an
        unmeasured model-validity claim."""
        coords = _helix_coords(10)
        bfac = np.full(10, 20.0)
        H = build_H_new(coords, bfac, cutoff=10.0)
        diag = operator_diagnostics(H, bfactors=bfac, n_large=5)
        assert any("exceeds" in n and "computational-scaling ceiling" in n for n in diag["notes"])

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


class TestClassifyFailureMultipleFloors:
    """TASK-0094 (REVIEW-2026-07-13 P1-A): `floor_scores` widened to accept
    several stacked candidates, floor = max AUC among them -- a single
    `degree_centrality` floor is not the confounding variable the review
    found (proximity-to-seed), so "beats the floor" must mean "beats the
    strongest of all trivial baselines available", not just one of them.
    """

    LABELS = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    NEAR_PERFECT = np.array([10.0, 9.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])  # AUC=1.0
    MEDIOCRE = np.array([8.0, 7.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 9.0, 10.0])       # AUC=0.75
    WEAK = np.array([5.0, 4.0, 6.0, 7.0, 3.0, 2.0, 1.0, 8.0, 9.0, 10.0])           # weaker still

    def test_sequence_of_floors_uses_the_strongest_one(self):
        """A score beating the weak floors but not the strong one must
        still be flagged -- the max, not the first or the mean, governs."""
        result = classify_failure(
            self.MEDIOCRE, self.LABELS,
            floor_scores=[self.WEAK, self.NEAR_PERFECT],
        )
        assert result == BEATS_CHANCE_NOT_FLOOR

    def test_2d_array_of_floors_behaves_the_same_as_a_list(self):
        stacked = np.vstack([self.WEAK, self.NEAR_PERFECT])
        result = classify_failure(self.MEDIOCRE, self.LABELS, floor_scores=stacked)
        assert result == BEATS_CHANCE_NOT_FLOOR

    def test_score_beating_every_floor_is_no_failure_detected(self):
        result = classify_failure(
            self.NEAR_PERFECT, self.LABELS,
            floor_scores=[self.WEAK, self.MEDIOCRE],
        )
        assert result == NO_FAILURE_DETECTED

    def test_single_array_floor_still_works_unchanged(self):
        """Backward compatibility: a plain (N,) array (pre-TASK-0094 shape)
        is still accepted and behaves exactly as before."""
        result = classify_failure(self.MEDIOCRE, self.LABELS, floor_scores=self.NEAR_PERFECT)
        assert result == BEATS_CHANCE_NOT_FLOOR


class TestClassifyFailureRealBaselineFloor:
    """SEAM-0011 (TASK-0056's review): `floor_scores` is designed to accept
    real `baselines.py` output, not just a hand-built stand-in array --
    TestClassifyFailureFloor above never actually calls `baselines.py`, so
    nothing proved the real composition works end-to-end. Both types are
    trivially compatible ((N,) float arrays), so this isn't a shape bug --
    but the *composition* itself was untested until now.

    Coords: residues 0-2 form a tight triangle (mutual degree 3, since
    residue 3 sits close enough to join the clique too); residues 4-9 sit
    30 units apart from everything (degree 0). Residue 3 is a deliberate
    confound -- labelled non-pocket but degree-indistinguishable from the
    true pocket -- so `degree_centrality` is a genuinely imperfect floor
    (not a strawman AUC=1.0 that nothing could ever beat), matching what a
    real structural baseline actually looks like.
    """

    COORDS = np.array([
        [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 0.0],
        [30.0, 0.0, 0.0], [60.0, 0.0, 0.0], [90.0, 0.0, 0.0],
        [120.0, 0.0, 0.0], [150.0, 0.0, 0.0], [180.0, 0.0, 0.0],
    ])
    LABELS = np.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 0])

    def _floor(self):
        from allostery.baselines import degree_centrality

        return degree_centrality(self.COORDS, cutoff=3.0)

    def test_real_degree_centrality_is_an_imperfect_floor(self):
        """Sanity check on the fixture itself: degree_centrality must NOT
        already be a perfect (AUC=1.0) separator, or the "beats the floor"
        assertion below would be untestable by construction."""
        from allostery.metrics import auc

        floor = self._floor()
        assert list(floor) == [3.0, 3.0, 3.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        floor_auc = auc(floor, self.LABELS)
        assert floor_auc < 1.0, "fixture must be an imperfect floor, not a strawman"

    def test_scorer_that_resolves_the_confound_beats_the_real_floor(self):
        """A scorer that correctly separates residue 3 (the confound) from
        the true pocket -- something degree_centrality structurally cannot
        do, since 3 is degree-identical to 0/1/2 -- genuinely beats the
        real floor, not a hand-built one."""
        floor = self._floor()
        resolves_confound = np.array([10.0, 9.0, 8.0, 1.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0])
        result = classify_failure(resolves_confound, self.LABELS, floor_scores=floor)
        assert result == NO_FAILURE_DETECTED

    def test_scorer_no_better_than_the_real_floor_is_flagged(self):
        """The floor compared against itself cannot beat itself."""
        floor = self._floor()
        result = classify_failure(floor, self.LABELS, floor_scores=floor)
        assert result == BEATS_CHANCE_NOT_FLOOR


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


class TestClassifyFailureBootstrapCI:
    """TASK-0112 -- wires `metrics.block_bootstrap_ci` into `classify_
    failure` via `return_ci=True`, so a floor-vs-score verdict can state
    whether it's statistically decisive, not just which point estimate is
    larger. `return_ci=False` (the default, every pre-existing call site)
    must stay byte-identical to pre-TASK-0112 behavior -- checked first,
    below, before anything about the new path."""

    N = 80
    _rng = np.random.default_rng(7)
    LABELS = np.zeros(N, dtype=int)
    LABELS[:20] = 1

    def test_default_return_ci_false_is_unchanged_bare_str(self):
        """Regression guard: return_ci defaults to False, and every
        existing caller (protocol.py/analysis.py, none of which pass
        return_ci) must keep getting a bare category string, not the new
        dataclass -- this is the actual backward-compatibility contract,
        not just a docstring claim."""
        scores = self._rng.normal(0, 1, self.N)
        result = classify_failure(scores, self.LABELS)
        assert isinstance(result, str)
        assert result in (NO_SIGNAL_IN_APO, BEATS_CHANCE_NOT_FLOOR, NO_FAILURE_DETECTED)

    def test_return_ci_true_gives_failure_classification_with_same_category(self):
        scores = self._rng.normal(0, 1, self.N)
        bare = classify_failure(scores, self.LABELS)
        rich = classify_failure(scores, self.LABELS, return_ci=True)
        assert isinstance(rich, FailureClassification)
        assert rich.category == bare  # CI annotation must not change the verdict itself

    def test_technical_failure_categories_never_get_a_ci(self):
        """OPERATOR_DEGENERATE/LABEL_SUSPECT/INSUFFICIENT_RESOLUTION have no
        well-formed AUC to bootstrap -- return_ci=True must not silently
        fabricate one."""
        disconnected = _helix_coords(6)
        far = _helix_coords(6, offset=1000.0)
        coords = np.vstack([disconnected, far])
        H = build_H_new(coords, np.full(12, 20.0), cutoff=10.0)
        labels = np.zeros(12, dtype=int)
        labels[[1, 7]] = 1
        result = classify_failure(np.zeros(12), labels, H=H, return_ci=True)
        assert result.category == OPERATOR_DEGENERATE
        assert result.score_ci is None
        assert result.floor_ci is None
        assert result.ci_overlap is None

        all_zero_labels = np.zeros(self.N, dtype=int)
        result2 = classify_failure(self._rng.normal(0, 1, self.N), all_zero_labels, return_ci=True)
        assert result2.category == LABEL_SUSPECT
        assert result2.score_ci is None

    def test_decisive_separation_gives_non_overlapping_cis(self):
        """Planned Validation, case 1: a case where the true floor/score
        gap is known to be decisive -- CI must NOT overlap."""
        scores = self.LABELS * 3.0 + self._rng.normal(0, 0.3, self.N)
        floor = self._rng.normal(0, 1, self.N)  # pure noise, no real signal
        result = classify_failure(scores, self.LABELS, floor_scores=floor, return_ci=True)
        assert result.category == NO_FAILURE_DETECTED
        assert result.ci_overlap is False
        score_auc, score_lo, score_hi = result.score_ci
        floor_auc, floor_lo, floor_hi = result.floor_ci
        assert score_lo > floor_hi  # score's CI sits entirely above the floor's

    def test_noise_level_gap_gives_overlapping_cis(self):
        """Planned Validation, case 2: a case where the true floor/score
        gap is known to be within noise -- CI must overlap, proving the
        wiring is sensitive in both directions, not just plumbed through."""
        scores = self.LABELS * 0.05 + self._rng.normal(0, 1, self.N)
        floor = self.LABELS * 0.03 + self._rng.normal(0, 1, self.N)
        result = classify_failure(scores, self.LABELS, floor_scores=floor, return_ci=True)
        assert result.ci_overlap is True

    def test_floor_ci_is_the_winning_candidate_not_an_average(self):
        """Multiple floor_scores candidates: floor_ci must be computed on
        whichever single candidate classify_failure's own point-estimate
        logic already selects as the winner (max AUC), matching
        BEATS_CHANCE_NOT_FLOOR's own existing "beats the strongest
        baseline" semantics (TASK-0094) -- not a blend across candidates."""
        scores = self.LABELS * 0.4 + self._rng.normal(0, 1, self.N)
        weak_floor = self._rng.normal(0, 1, self.N)
        strong_floor = self.LABELS * 1.5 + self._rng.normal(0, 0.3, self.N)
        result = classify_failure(
            scores, self.LABELS, floor_scores=[weak_floor, strong_floor], return_ci=True,
        )
        from allostery.metrics import auc as _auc, block_bootstrap_ci as _bbci
        expected_floor_ci = _bbci(strong_floor, self.LABELS)
        assert result.floor_ci == expected_floor_ci

    def test_ci_reproducible_with_explicit_rng_seed(self):
        """Same seed in, same CI out -- block_bootstrap_ci's own
        reproducibility contract must survive being wired through here."""
        scores = self._rng.normal(0, 1, self.N)
        r1 = classify_failure(scores, self.LABELS, return_ci=True, ci_rng=np.random.default_rng(3))
        r2 = classify_failure(scores, self.LABELS, return_ci=True, ci_rng=np.random.default_rng(3))
        assert r1.score_ci == r2.score_ci


class TestAssertGateReachable:
    """TASK-0189 -- the reachability guard that would have caught
    `zero_plant_specificity.py:154`'s Bonferroni-family bug mechanically.
    Demonstrates the failure against the *actual* buggy constants first
    (this task's own Planned Validation: "demonstrate it, don't assert
    it"), then confirms it passes against the corrected ones.
    """

    def test_fails_against_the_actual_bug_found_in_zero_plant_specificity(self):
        """The exact constants at fault: ALPHA=0.05, family=len(STRENGTHS)*
        N_SEEDS=8*20=160 (0.05/160=3.125e-4), N_PERM_REPS=1000
        (1/1000=1e-3 > 3.125e-4) -- unreachable, must raise."""
        with pytest.raises(ValueError, match="unreachable"):
            assert_gate_reachable(alpha=0.05, family_size=160, n_reps=1000)

    def test_fails_against_the_matched_null_variant_too(self):
        """MATCHED_N_PERM_REPS=200 (1/200=5e-3) is even further from
        reachable at the same buggy family size."""
        with pytest.raises(ValueError, match="unreachable"):
            assert_gate_reachable(alpha=0.05, family_size=160, n_reps=200)

    def test_passes_against_the_corrected_constants(self):
        """REAL_BONFERRONI_ALPHA = 0.05/3 = 0.01667 (TASK-0145's own
        across-targets convention) is comfortably above both reachable
        floors (1e-3, 5e-3) -- no re-run of the expensive collection
        pass was needed, confirmed here, not assumed."""
        assert assert_gate_reachable(alpha=0.05, family_size=3, n_reps=1000) is True
        assert assert_gate_reachable(alpha=0.05, family_size=3, n_reps=200) is True

    def test_boundary_is_strict_not_inclusive(self):
        """alpha/family exactly equal to 1/n_reps is still unreachable --
        a gate that can only ever fire at its own single smallest
        possible p-value is not meaningfully testing that alpha."""
        with pytest.raises(ValueError):
            assert_gate_reachable(alpha=0.1, family_size=1, n_reps=10)  # 0.1 == 1/10
