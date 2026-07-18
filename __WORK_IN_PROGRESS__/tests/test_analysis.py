"""TASK-0008 coverage -- quantum-vs-classical, ablation, apo/holo
consistency, spectral enrichment, dephasing sweep, and the default-
parameter benchmark.

Notebook-oracle gap: `notebooks/H_new_engineering (4) CLEAN.ipynb` has all
cell outputs cleared -- there is nothing to "read directly" from Sec.7/9/
10/11/12 (same pre-existing gap as `.claude/TASKS.md` T-004/T-017's
eff_rank(KRAS)~=117.7 placeholder). The real-target checks below compute
fresh numbers from this package's own modules against real RCSB structures
and pin *those*, explicitly labelled as such -- not copied from the
notebook.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.analysis import (  # noqa: E402
    ablation,
    apo_holo_consistency,
    assemble_verdict_results,
    benchmark,
    coherence_sensitivity,
    consensus_ranking,
    dephasing_sweep,
    gnm_cutoff_weight_sweep,
    operator_sweep,
    quantum_vs_classical,
    spectral_enrichment,
)
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.report import verdict_template  # noqa: E402
from allostery.hamiltonians import (  # noqa: E402
    H2_combinatorial_laplacian,
    build_H_new,
    build_H10,
)


def _helix_coords(n: int) -> np.ndarray:
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


N = 16
COORDS = _helix_coords(N)
BFACTORS = np.full(N, 20.0)
LABELS = np.zeros(N, dtype=bool)
LABELS[[3, 4, 5]] = True  # a synthetic "pocket"


# ---------------------------------------------------------------------------
# quantum_vs_classical
# ---------------------------------------------------------------------------

class TestQuantumVsClassical:
    def test_returns_occupation_vectors_without_labels(self):
        L = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        out = quantum_vs_classical(L, source=0, t_max=5.0, n_steps=50)
        assert set(out) == {"ctqw", "heat"}
        assert out["ctqw"].shape == (N,)
        assert out["heat"].shape == (N,)
        assert out["ctqw"].sum() == pytest.approx(1.0, abs=1e-6)
        assert out["heat"].sum() == pytest.approx(1.0, abs=1e-6)

    def test_returns_metric_packs_with_labels(self):
        L = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        out = quantum_vs_classical(L, source=0, labels=LABELS, t_max=5.0, n_steps=50)
        assert "AUC" in out["ctqw"]
        assert "AUC" in out["heat"]

    def test_multi_index_source_does_not_crash(self):
        L = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        out = quantum_vs_classical(L, source=[0, 1, 2], t_max=5.0, n_steps=50)
        assert out["ctqw"].sum() == pytest.approx(1.0, abs=1e-6)

    def test_coherent_flag_passes_through_and_defaults_true(self):
        """TASK-0118: `coherent` reaches `time_averaged_ctqw` -- the
        default (unset) call must match an explicit `coherent=True` call
        exactly, and `coherent=False` must differ for a genuine
        multi-index source (the whole point of the parameter)."""
        L = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        default = quantum_vs_classical(L, source=[0, 1, 2], t_max=5.0, n_steps=50)
        explicit_true = quantum_vs_classical(L, source=[0, 1, 2], t_max=5.0, n_steps=50, coherent=True)
        incoherent = quantum_vs_classical(L, source=[0, 1, 2], t_max=5.0, n_steps=50, coherent=False)
        np.testing.assert_array_equal(default["ctqw"], explicit_true["ctqw"])
        assert not np.allclose(default["ctqw"], incoherent["ctqw"])
        assert incoherent["ctqw"].sum() == pytest.approx(1.0, abs=1e-6)

    def test_use_converged_limit_default_false_is_byte_identical(self):
        """TASK-0130: the new flag must not change a single existing
        caller's output -- default (unset) must equal an explicit
        `use_converged_limit=False` call exactly."""
        L = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        default = quantum_vs_classical(L, source=0, t_max=5.0, n_steps=50)
        explicit_false = quantum_vs_classical(L, source=0, t_max=5.0, n_steps=50, use_converged_limit=False)
        np.testing.assert_array_equal(default["ctqw"], explicit_false["ctqw"])

    def test_use_converged_limit_true_matches_the_closed_form_directly(self):
        """`use_converged_limit=True` must produce exactly
        `propagators.time_averaged_ctqw_converged`'s own output, not an
        approximation of it -- and must differ from the finite-`t_max`
        default (ignoring `t_max`/`n_steps` entirely, per the docstring),
        proving the flag actually switches propagators rather than being
        accepted and silently ignored."""
        from allostery.propagators import time_averaged_ctqw_converged

        L = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        finite = quantum_vs_classical(L, source=0, t_max=5.0, n_steps=50)
        converged = quantum_vs_classical(L, source=0, t_max=5.0, n_steps=50, use_converged_limit=True)
        expected = time_averaged_ctqw_converged(L, source=0)
        np.testing.assert_allclose(converged["ctqw"], expected)
        assert not np.allclose(finite["ctqw"], converged["ctqw"])
        # heat (ground_state_relaxation) is unaffected by this flag.
        np.testing.assert_array_equal(finite["heat"], converged["heat"])


# ---------------------------------------------------------------------------
# ablation
# ---------------------------------------------------------------------------

class TestAblation:
    def test_returns_all_terms_plus_baseline(self):
        result = ablation(COORDS, BFACTORS, source=0, labels=LABELS, t_max=5.0, n_steps=50)
        assert set(result) == {"L_only", "B", "T", "R", "C", "M"}
        for pack in result.values():
            assert "AUC" in pack

    def test_each_term_pack_has_occupation_vector(self):
        result = ablation(COORDS, BFACTORS, source=0, labels=LABELS, t_max=5.0, n_steps=50)
        for pack in result.values():
            assert pack["occ"].shape == (N,)


# ---------------------------------------------------------------------------
# benchmark
# ---------------------------------------------------------------------------

class TestBenchmark:
    def test_returns_both_operators(self):
        result = benchmark(COORDS, BFACTORS, source=0, labels=LABELS, t_max=5.0, n_steps=50)
        assert set(result) == {"H_new_default", "H10_disorder_suppressed"}
        assert "AUC" in result["H_new_default"]
        assert "AUC" in result["H10_disorder_suppressed"]

    def test_coherent_flag_passes_through_to_both_operators(self):
        multi_source = [0, 1, 2]
        coherent = benchmark(COORDS, BFACTORS, source=multi_source, labels=LABELS, t_max=5.0, n_steps=50, coherent=True)
        incoherent = benchmark(COORDS, BFACTORS, source=multi_source, labels=LABELS, t_max=5.0, n_steps=50, coherent=False)
        assert not np.allclose(coherent["H_new_default"]["occ"], incoherent["H_new_default"]["occ"])
        assert not np.allclose(coherent["H10_disorder_suppressed"]["occ"], incoherent["H10_disorder_suppressed"]["occ"])

    def test_use_converged_limit_matches_closed_form_for_both_operators(self):
        from allostery.propagators import time_averaged_ctqw_converged

        result = benchmark(COORDS, BFACTORS, source=0, labels=LABELS, t_max=5.0, n_steps=50, use_converged_limit=True)
        expected_new = time_averaged_ctqw_converged(build_H_new(COORDS, BFACTORS, cutoff=10.0), source=0)
        expected_10 = time_averaged_ctqw_converged(build_H10(COORDS, BFACTORS, cutoff=10.0), source=0)
        np.testing.assert_allclose(result["H_new_default"]["occ"], expected_new)
        np.testing.assert_allclose(result["H10_disorder_suppressed"]["occ"], expected_10)


# ---------------------------------------------------------------------------
# apo_holo_consistency
# ---------------------------------------------------------------------------

class TestApoHoloConsistency:
    def test_identical_occupation_gives_perfect_agreement(self):
        occ = np.abs(np.random.default_rng(0).normal(size=N))
        idx = np.arange(N)
        result = apo_holo_consistency(occ, occ, idx, idx, k=5)
        assert result["spearman_rho"] == pytest.approx(1.0, abs=1e-9)
        assert result["top_k_jaccard"] == 1.0

    def test_reversed_ranking_gives_negative_correlation(self):
        occ_apo = np.arange(N, dtype=float)
        occ_holo = occ_apo[::-1].copy()
        idx = np.arange(N)
        result = apo_holo_consistency(occ_apo, occ_holo, idx, idx, k=5)
        assert result["spearman_rho"] < 0
        assert result["top_k_jaccard"] < 1.0

    def test_respects_common_index_subset(self):
        occ_apo = np.arange(N, dtype=float)
        occ_holo = np.arange(N, dtype=float)
        apo_idx = np.array([0, 1, 2, 3])
        holo_idx = np.array([0, 1, 2, 3])
        result = apo_holo_consistency(occ_apo, occ_holo, apo_idx, holo_idx, k=2)
        assert result["k"] == 2


# ---------------------------------------------------------------------------
# spectral_enrichment
# ---------------------------------------------------------------------------

class TestSpectralEnrichment:
    def test_returns_expected_keys(self):
        H = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        result = spectral_enrichment(H, LABELS, n_modes=5)
        assert set(result) >= {"auc", "eff_rank", "ipr_slowest_mode", "spectral_gap", "participation"}
        assert result["participation"].shape == (N,)

    def test_eff_rank_and_gap_are_finite(self):
        H = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        result = spectral_enrichment(H, LABELS, n_modes=5)
        assert np.isfinite(result["eff_rank"])
        assert np.isfinite(result["spectral_gap"])


# ---------------------------------------------------------------------------
# dephasing_sweep
# ---------------------------------------------------------------------------

class TestDephasingSweep:
    def test_shape_matches_omega_range(self):
        L = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        omega_range = np.linspace(0.0, 1.0, 4)
        result = dephasing_sweep(
            L, omega_range, LABELS, source=0, t_max=5.0, rtol=1e-3, atol=1e-5
        )
        assert result["omega"].shape == (4,)
        assert result["auc"].shape == (4,)
        assert isinstance(result["is_flat"], bool)

    def test_gamma_zero_recovers_pure_ctqw_auc(self):
        from allostery.propagators import haken_strobl, ctqw
        from allostery.metrics import auc as _auc

        L = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        p_hs = haken_strobl(L, t=5.0, gamma=0.0, source=0)
        p_ctqw = ctqw(L, t=5.0, source=0)
        np.testing.assert_allclose(p_hs, p_ctqw, atol=1e-4)

    def test_all_same_label_gives_nan_auc_and_none_is_flat(self):
        L = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        all_false = np.zeros(N, dtype=bool)
        result = dephasing_sweep(
            L, [0.0, 0.5], all_false, source=0, t_max=5.0, rtol=1e-3, atol=1e-5
        )
        assert np.all(np.isnan(result["auc"]))
        assert result["is_flat"] is None

    def test_return_occ_false_by_default(self):
        L = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        result = dephasing_sweep(L, [0.0, 0.5], LABELS, source=0, t_max=5.0, rtol=1e-3, atol=1e-5)
        assert "occ" not in result

    def test_return_occ_true_adds_one_vector_per_omega(self):
        L = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        result = dephasing_sweep(
            L, [0.0, 0.5], LABELS, source=0, t_max=5.0, rtol=1e-3, atol=1e-5, return_occ=True
        )
        assert len(result["occ"]) == 2
        assert result["occ"][0].shape == (N,)
        assert result["occ"][1].shape == (N,)


# ---------------------------------------------------------------------------
# coherence_sensitivity (TASK-0099 -- formal dephasing_sweep verdict wiring)
# ---------------------------------------------------------------------------

class TestCoherenceSensitivity:
    def test_gamma_zero_point_matches_direct_ctqw(self):
        from allostery.propagators import ctqw
        from allostery.metrics import auc as _auc

        H = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        out = coherence_sensitivity(
            H, BFACTORS, source=0, labels=LABELS, gamma_scale=0.01,
            t_max=5.0, multipliers=(0.0,), rtol=1e-3, atol=1e-5,
        )
        expected = _auc(ctqw(H, 5.0, source=0), LABELS.astype(int))
        assert out["auc_at_gamma0"] == pytest.approx(expected)
        assert out["gammas"] == [0.0]

    def test_one_diagnosis_per_gamma_point(self):
        H = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        out = coherence_sensitivity(
            H, BFACTORS, source=0, labels=LABELS, gamma_scale=0.05,
            t_max=5.0, rtol=1e-3, atol=1e-5,
        )
        assert len(out["diagnoses"]) == len(out["floor_cleared"]) == len(out["gammas"]) == 4

    def test_flat_sweep_without_floor_scores_is_not_significant(self):
        # gamma_scale ~ 0 keeps every swept gamma essentially coherent --
        # AUC barely moves, this module's own "coherence adds ~nothing"
        # finding reproduced on the synthetic fixture too. is_flat alone
        # is enough to classify NOT_SIGNIFICANT, no floor needed.
        H = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        out = coherence_sensitivity(
            H, BFACTORS, source=0, labels=LABELS, gamma_scale=1e-6,
            t_max=5.0, rtol=1e-3, atol=1e-5,
        )
        assert out["is_flat"] is True
        assert out["classification"] == "COHERENCE_NOT_SIGNIFICANT"

    def test_non_flat_sweep_without_floor_scores_is_unresolved(self, monkeypatch):
        H = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        occ_hi = LABELS.astype(float)      # AUC = 1.0
        occ_lo = (~LABELS).astype(float)   # AUC = 0.0
        monkeypatch.setattr("allostery.propagators.ctqw", lambda H, t, source=0: occ_hi)
        monkeypatch.setattr(
            "allostery.propagators.haken_strobl",
            lambda H, t, gamma, source=0, rtol=1e-6, atol=1e-8: occ_lo,
        )
        out = coherence_sensitivity(
            H, BFACTORS, source=0, labels=LABELS, gamma_scale=1.0, t_max=5.0,
        )
        assert out["is_flat"] is False
        # no floor_scores supplied -- geometry confound can't be ruled out,
        # so this must NOT be silently assumed insignificant either.
        assert out["classification"] is None

    def test_floor_gate_promotes_to_dependent_signal_when_status_flips(self, monkeypatch):
        H = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        occ_hi = LABELS.astype(float)      # AUC = 1.0, clears a 0.5 floor
        occ_lo = (~LABELS).astype(float)   # AUC = 0.0, does not
        monkeypatch.setattr("allostery.propagators.ctqw", lambda H, t, source=0: occ_hi)
        monkeypatch.setattr(
            "allostery.propagators.haken_strobl",
            lambda H, t, gamma, source=0, rtol=1e-6, atol=1e-8: occ_lo,
        )
        floor_scores = np.full(N, 5.0)  # constant score -> AUC 0.5 exactly
        out = coherence_sensitivity(
            H, BFACTORS, source=0, labels=LABELS, gamma_scale=1.0, t_max=5.0,
            floor_scores=floor_scores,
        )
        assert out["auc_range"] == pytest.approx(1.0)
        assert out["floor_cleared"] == [True, False, False, False]
        assert out["classification"] == "COHERENCE_DEPENDENT_SIGNAL"

    def test_floor_gate_stays_not_significant_when_status_never_flips(self, monkeypatch):
        # occ_mid clears the same 0.5 floor as occ_hi (AUC ~0.833 vs 1.0) --
        # the raw AUC moves a lot (not flat) but never changes which side
        # of the floor the result lands on, so this is the "confounded by
        # geometry" case, not a real coherence-dependent finding.
        H = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        occ_hi = LABELS.astype(float)
        occ_mid = LABELS.astype(float).copy()
        occ_mid[3] = 0.0  # one of the three pocket residues ties the negatives
        monkeypatch.setattr("allostery.propagators.ctqw", lambda H, t, source=0: occ_hi)
        monkeypatch.setattr(
            "allostery.propagators.haken_strobl",
            lambda H, t, gamma, source=0, rtol=1e-6, atol=1e-8: occ_mid,
        )
        floor_scores = np.full(N, 5.0)  # constant score -> AUC 0.5 exactly
        out = coherence_sensitivity(
            H, BFACTORS, source=0, labels=LABELS, gamma_scale=1.0, t_max=5.0,
            floor_scores=floor_scores,
        )
        assert out["auc_range"] > out["flat_threshold"]
        assert all(out["floor_cleared"])
        assert out["classification"] == "COHERENCE_NOT_SIGNIFICANT"


# ---------------------------------------------------------------------------
# gnm_cutoff_weight_sweep (TASK-0067)
# ---------------------------------------------------------------------------

class TestGnmCutoffWeightSweep:
    def test_returns_one_metric_pack_per_combination(self):
        result = gnm_cutoff_weight_sweep(
            COORDS, source=0, labels=LABELS,
            cutoffs=(7.5, 10.0), weight_schemes=("binary", "gaussian"), t_max=5.0,
        )
        assert set(result) == {
            (7.5, "binary"), (7.5, "gaussian"), (10.0, "binary"), (10.0, "gaussian"),
        }
        for pack in result.values():
            assert "AUC" in pack
            assert pack["occ"].shape == (N,)

    def test_default_grid_covers_all_three_live_cutoffs_and_five_schemes(self):
        """The three cutoffs actually in production use (backend 8.0,
        H8_gnm 7.5, potentials.py 10.0 -- TASK-0018's finding) and all five
        contact_matrix weight schemes must all be swept by default, not a
        subset a caller has to remember to ask for."""
        result = gnm_cutoff_weight_sweep(COORDS, source=0, labels=LABELS, t_max=5.0)
        cutoffs_seen = {c for c, _ in result}
        schemes_seen = {s for _, s in result}
        assert cutoffs_seen == {7.5, 8.0, 10.0}
        assert schemes_seen == {"binary", "gaussian", "exponential", "harmonic", "invdist"}
        assert len(result) == 15

    def test_all_combinations_are_finite_and_non_degenerate_on_a_connected_helix(self):
        result = gnm_cutoff_weight_sweep(
            COORDS, source=0, labels=LABELS,
            cutoffs=(10.0,), weight_schemes=("binary", "harmonic", "invdist"), t_max=5.0,
        )
        for pack in result.values():
            assert np.isfinite(pack["AUC"])


# ---------------------------------------------------------------------------
# operator_sweep (TASK-0101)
# ---------------------------------------------------------------------------

class TestOperatorSweep:
    FLOOR_SOURCE = 0

    @classmethod
    def _floor_scores(cls, cutoff=10.0):
        return [
            degree_centrality(COORDS, cutoff=cutoff),
            euclid_from_seed_centroid(COORDS, cls.FLOOR_SOURCE),
            hop_from_seed(COORDS, cls.FLOOR_SOURCE, cutoff=cutoff),
        ]

    def test_default_sweep_covers_all_16_operators_x_2_propagators(self):
        rows = operator_sweep(
            COORDS, BFACTORS, self.FLOOR_SOURCE, LABELS, self._floor_scores(),
            cutoff=10.0, t_max=5.0, n_steps=50,
        )
        assert len(rows) == 32
        operators_seen = {r["operator"] for r in rows}
        assert operators_seen == {
            "H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9", "H10",
            "H11", "H12", "H13", "H14", "H_new", "build_H10",
        }
        propagators_seen = {r["propagator"] for r in rows}
        assert propagators_seen == {"ctqw", "ground_state"}

    def test_tier_a_operators_are_exactly_h10_h14_hnew_buildh10(self):
        rows = operator_sweep(
            COORDS, BFACTORS, self.FLOOR_SOURCE, LABELS, self._floor_scores(),
            cutoff=10.0, t_max=5.0, n_steps=50,
        )
        tier_a = {r["operator"] for r in rows if r["tier"] == "A"}
        tier_b = {r["operator"] for r in rows if r["tier"] == "B"}
        assert tier_a == {"H10", "H14", "H_new", "build_H10"}
        assert tier_b == {"H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9", "H11", "H12", "H13"}

    def test_h13_shape_mismatch_is_caught_not_raised(self):
        """H13 returns a 3N x 3N Hessian -- must be recorded as an error
        row for both propagators, must not crash the whole sweep (this
        task's own Acceptance Scenario)."""
        rows = operator_sweep(
            COORDS, BFACTORS, self.FLOOR_SOURCE, LABELS, self._floor_scores(),
            cutoff=10.0, t_max=5.0, n_steps=50,
        )
        h13_rows = [r for r in rows if r["operator"] == "H13"]
        assert len(h13_rows) == 2
        for r in h13_rows:
            assert r["error"] is not None
            assert r["auc"] is None
        # every other operator still produced a real result
        non_h13 = [r for r in rows if r["operator"] != "H13"]
        assert all(r["error"] is None for r in non_h13)

    def test_use_converged_limit_changes_ctqw_rows_not_ground_state_rows(self):
        """TASK-0130: `use_converged_limit=True` must swap the `"ctqw"`
        propagator to the closed form (different AUC than the finite
        `t_max=5.0` default, in general) while leaving `"ground_state"`
        rows byte-identical (unaffected by this flag, per the docstring)."""
        finite = operator_sweep(
            COORDS, BFACTORS, self.FLOOR_SOURCE, LABELS, self._floor_scores(),
            cutoff=10.0, operators=["H10"], propagators=["ctqw", "ground_state"],
            t_max=5.0, n_steps=50,
        )
        converged = operator_sweep(
            COORDS, BFACTORS, self.FLOOR_SOURCE, LABELS, self._floor_scores(),
            cutoff=10.0, operators=["H10"], propagators=["ctqw", "ground_state"],
            t_max=5.0, n_steps=50, use_converged_limit=True,
        )
        finite_ctqw = next(r for r in finite if r["propagator"] == "ctqw")
        converged_ctqw = next(r for r in converged if r["propagator"] == "ctqw")
        finite_gs = next(r for r in finite if r["propagator"] == "ground_state")
        converged_gs = next(r for r in converged if r["propagator"] == "ground_state")
        assert finite_ctqw["auc"] != converged_ctqw["auc"]
        assert finite_gs["auc"] == converged_gs["auc"]

    def test_h10_and_build_h10_agree_exactly(self):
        """build_H10 is a convenience alias for H10_disorder_suppressed --
        registered as a separate row deliberately (TASK-0101's own 16-name
        enumeration), so this is a free consistency check that the alias
        is faithful."""
        rows = operator_sweep(
            COORDS, BFACTORS, self.FLOOR_SOURCE, LABELS, self._floor_scores(),
            cutoff=10.0, operators=["H10", "build_H10"], t_max=5.0, n_steps=50,
        )
        by_key = {(r["operator"], r["propagator"]): r["auc"] for r in rows}
        assert by_key[("H10", "ctqw")] == pytest.approx(by_key[("build_H10", "ctqw")])
        assert by_key[("H10", "ground_state")] == pytest.approx(by_key[("build_H10", "ground_state")])

    def test_operators_filter_restricts_the_sweep(self):
        rows = operator_sweep(
            COORDS, BFACTORS, self.FLOOR_SOURCE, LABELS, self._floor_scores(),
            cutoff=10.0, operators=["H_new"], propagators=["ctqw"], t_max=5.0, n_steps=50,
        )
        assert len(rows) == 1
        assert rows[0]["operator"] == "H_new"
        assert rows[0]["propagator"] == "ctqw"

    def test_unknown_operator_name_is_an_error_row_not_a_crash(self):
        rows = operator_sweep(
            COORDS, BFACTORS, self.FLOOR_SOURCE, LABELS, self._floor_scores(),
            cutoff=10.0, operators=["NOT_A_REAL_OPERATOR"], t_max=5.0, n_steps=50,
        )
        assert len(rows) == 2  # one per propagator
        assert all(r["error"] is not None for r in rows)

    def test_floor_cleared_reuses_classify_failure_precedence(self):
        """A result that beats chance but not the floor must not be
        marked floor_cleared -- reuses diagnostics.classify_failure,
        does not invent a second comparison."""
        rows = operator_sweep(
            COORDS, BFACTORS, self.FLOOR_SOURCE, LABELS, self._floor_scores(),
            cutoff=10.0, t_max=5.0, n_steps=50,
        )
        for r in rows:
            if r["error"] is not None:
                continue
            if r["floor_cleared"]:
                assert r["diagnosis"] == "NO_FAILURE_DETECTED"
            else:
                assert r["diagnosis"] != "NO_FAILURE_DETECTED"

    def test_transport_pr_is_bounded_in_unit_interval(self):
        rows = operator_sweep(
            COORDS, BFACTORS, self.FLOOR_SOURCE, LABELS, self._floor_scores(),
            cutoff=10.0, operators=["H2", "H_new"], t_max=5.0, n_steps=50,
        )
        for r in rows:
            assert r["error"] is None
            assert 0.0 < r["transport_pr"] <= 1.0 + 1e-9

    def test_apo_holo_consistency_is_always_none_pending_task_0092(self):
        rows = operator_sweep(
            COORDS, BFACTORS, self.FLOOR_SOURCE, LABELS, self._floor_scores(),
            cutoff=10.0, operators=["H_new"], t_max=5.0, n_steps=50,
        )
        assert all(r["apo_holo_consistency"] is None for r in rows)

    def test_coherent_flag_reaches_ctqw_not_ground_state(self, monkeypatch):
        """TASK-0118/TASK-0129: defaults to `coherent=True`, and the flag
        reaches `time_averaged_ctqw`'s `ctqw`-row call but never
        `ground_state_relaxation` (already an incoherent classical mixture
        by construction) -- checked via a spy, not an AUC-level difference
        (AUC is rank-based and happens to be invariant to this specific
        perturbation on this small synthetic fixture, same caveat as
        `test_ceiling.py`/`test_protocol.py`'s equivalent fixes)."""
        from allostery import propagators as propagators_mod

        seen = []
        real_fn = propagators_mod.time_averaged_ctqw

        def _spy(*args, **kwargs):
            seen.append(kwargs.get("coherent", True))
            return real_fn(*args, **kwargs)

        monkeypatch.setattr(propagators_mod, "time_averaged_ctqw", _spy)
        multi_source = [0, 1, 2]
        floor_scores = [
            degree_centrality(COORDS, cutoff=10.0),
            euclid_from_seed_centroid(COORDS, multi_source),
            hop_from_seed(COORDS, multi_source, cutoff=10.0),
        ]
        operator_sweep(
            COORDS, BFACTORS, multi_source, LABELS, floor_scores,
            cutoff=10.0, operators=["H_new"], propagators=["ctqw"], t_max=5.0, n_steps=50,
        )
        assert seen == [True]
        seen.clear()
        operator_sweep(
            COORDS, BFACTORS, multi_source, LABELS, floor_scores,
            cutoff=10.0, operators=["H_new"], propagators=["ctqw"], t_max=5.0, n_steps=50,
            coherent=False,
        )
        assert seen == [False]

    def test_disconnected_operator_is_flagged_operator_degenerate(self):
        """Regression guard: an earlier version of operator_sweep did not
        pass H/bfactors into classify_failure at all, which silently
        disabled its OPERATOR_DEGENERATE and INSUFFICIENT_RESOLUTION
        checks -- found by reading the real 96-cell sweep's own output
        (CARDIAC_MYOSIN, N=950>800, came back NO_FAILURE_DETECTED instead
        of INSUFFICIENT_RESOLUTION), not by inspection alone."""
        cluster_a = _helix_coords(6)
        theta = np.arange(6) * (100.0 * np.pi / 180.0)
        cluster_b = np.column_stack([
            1000.0 + 2.3 * np.cos(theta), 2.3 * np.sin(theta), 1.5 * np.arange(6, dtype=float),
        ])
        coords = np.vstack([cluster_a, cluster_b])
        bfac = np.full(12, 20.0)
        labels = np.zeros(12, dtype=bool)
        labels[[7, 8]] = True
        source = 0
        floor_scores = [
            degree_centrality(coords, cutoff=10.0),
            euclid_from_seed_centroid(coords, source),
            hop_from_seed(coords, source, cutoff=10.0),
        ]
        rows = operator_sweep(
            coords, bfac, source, labels, floor_scores,
            cutoff=10.0, operators=["H_new", "H2"], t_max=5.0, n_steps=50,
        )
        assert all(r["diagnosis"] == "OPERATOR_DEGENERATE" for r in rows)
        assert all(r["floor_cleared"] is False for r in rows)


# ---------------------------------------------------------------------------
# consensus_ranking (TASK-0080 -- c-Myc/1NKP no-ground-truth handling)
# ---------------------------------------------------------------------------

class TestConsensusRanking:
    def test_returns_expected_keys_and_shapes(self):
        out = consensus_ranking(COORDS, BFACTORS, source=0, cutoff=10.0, t_max=5.0, n_steps=50, k=5)
        assert set(out) == {
            "operators", "occupancy", "top_k_per_operator", "consensus_count",
            "mean_occupancy", "consensus_ranked_indices", "n_operators", "k",
        }
        assert out["n_operators"] == 4
        assert len(out["operators"]) == 4
        assert out["consensus_count"].shape == (N,)
        assert out["mean_occupancy"].shape == (N,)
        assert len(out["consensus_ranked_indices"]) == 5

    def test_no_auc_or_labels_needed(self):
        # Signature-level check: consensus_ranking never takes a `labels`
        # argument at all -- this is the point (TASK-0080's whole reason
        # to exist is scoring with no pocket ground truth available).
        import inspect
        params = inspect.signature(consensus_ranking).parameters
        assert "labels" not in params

    def test_consensus_count_bounded_by_operator_count(self):
        out = consensus_ranking(COORDS, BFACTORS, source=0, cutoff=10.0, t_max=5.0, n_steps=50, k=5)
        assert out["consensus_count"].min() >= 0
        assert out["consensus_count"].max() <= out["n_operators"]

    def test_k_larger_than_n_clamps(self):
        out = consensus_ranking(COORDS, BFACTORS, source=0, cutoff=10.0, t_max=5.0, n_steps=50, k=10_000)
        assert out["k"] == N
        assert len(out["consensus_ranked_indices"]) == N

    def test_ranking_prefers_higher_consensus_count_over_mean_occupancy(self):
        out = consensus_ranking(COORDS, BFACTORS, source=0, cutoff=10.0, t_max=5.0, n_steps=50, k=5)
        ranked = out["consensus_ranked_indices"]
        counts = out["consensus_count"][ranked]
        # consensus_count must be non-increasing along the ranked list --
        # the primary sort key, mean_occupancy only breaks ties within it.
        assert np.all(np.diff(counts) <= 0)


# ---------------------------------------------------------------------------
# assemble_verdict_results (TASK-0079.001 -- closes SEAM-0008)
# ---------------------------------------------------------------------------

class TestAssembleVerdictResults:
    def _real_outputs(self):
        bench = benchmark(COORDS, BFACTORS, source=0, labels=LABELS, t_max=5.0, n_steps=50)
        abl = ablation(COORDS, BFACTORS, source=0, labels=LABELS, t_max=5.0, n_steps=50)
        L = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        qvc = quantum_vs_classical(L, source=0, labels=LABELS, t_max=5.0, n_steps=50)
        occ = np.abs(np.random.default_rng(0).normal(size=N))
        idx = np.arange(N)
        consistency = apo_holo_consistency(occ, occ, idx, idx, k=20)
        # gamma_scale ~0 -> flat sweep -> classification resolves without
        # needing floor_scores wired through this synthetic fixture too.
        coherence = coherence_sensitivity(
            L, BFACTORS, source=0, labels=LABELS, gamma_scale=1e-6,
            t_max=5.0, rtol=1e-3, atol=1e-5,
        )
        return bench, abl, qvc, consistency, coherence

    def test_full_assembly_populates_every_verdict_template_key(self):
        bench, abl, qvc, consistency, coherence = self._real_outputs()
        results = assemble_verdict_results(
            benchmark_out=bench,
            ablation_out=abl,
            qvc_out=qvc,
            consistency_out=consistency,
            coherence_out=coherence,
            auc_apo_optimised=0.55,
            auc_holo_optimised=0.60,
        )
        expected_keys = {
            "AUC_apo_Hnew_default", "AUC_apo_H10_baseline",
            "AUC_apo_Hnew_optimised", "AUC_holo_Hnew_optimised",
            "AUC_ctqw_mean", "AUC_heat_mean",
            "most_impactful_term", "least_impactful_term",
            "mean_rho_apo_holo", "mean_jacc20",
            "coherence_auc_range", "coherence_auc_at_gamma0", "coherence_classification",
        }
        assert expected_keys <= set(results)
        for key in expected_keys:
            assert results[key] is not None

    def test_render_has_no_na_for_any_populated_key(self):
        bench, abl, qvc, consistency, coherence = self._real_outputs()
        results = assemble_verdict_results(
            benchmark_out=bench,
            ablation_out=abl,
            qvc_out=qvc,
            consistency_out=consistency,
            coherence_out=coherence,
            auc_apo_optimised=0.55,
            auc_holo_optimised=0.60,
        )
        rendered = verdict_template(results, provenance="dev")
        assert "N/A" not in rendered

    def test_most_impactful_term_is_v_prefixed_and_not_l_only(self):
        _, abl, _, _, _ = self._real_outputs()
        results = assemble_verdict_results(ablation_out=abl)
        assert results["most_impactful_term"].startswith("V_")
        assert results["least_impactful_term"].startswith("V_")
        assert results["most_impactful_term"] != "V_L_only"

    def test_every_argument_is_independently_omittable(self):
        assert assemble_verdict_results() == {}
        bench, _, _, _, _ = self._real_outputs()
        results = assemble_verdict_results(benchmark_out=bench)
        assert set(results) == {"AUC_apo_Hnew_default", "AUC_apo_H10_baseline"}

    def test_coherence_out_populates_only_its_own_keys(self):
        _, _, _, _, coherence = self._real_outputs()
        results = assemble_verdict_results(coherence_out=coherence)
        assert set(results) == {
            "coherence_auc_range", "coherence_auc_at_gamma0", "coherence_classification",
        }

    def test_optimised_aucs_pass_through_directly_not_from_benchmark(self):
        results = assemble_verdict_results(auc_apo_optimised=0.77, auc_holo_optimised=0.81)
        assert results["AUC_apo_Hnew_optimised"] == 0.77
        assert results["AUC_holo_Hnew_optimised"] == 0.81

    def test_nan_auc_is_omitted_not_rendered_as_nan(self):
        all_false = np.zeros(N, dtype=bool)
        bench = benchmark(COORDS, BFACTORS, source=0, labels=all_false, t_max=5.0, n_steps=50)
        assert np.isnan(bench["H_new_default"]["AUC"])
        results = assemble_verdict_results(benchmark_out=bench)
        assert "AUC_apo_Hnew_default" not in results
        rendered = verdict_template(results, provenance="dev")
        assert "nan" not in rendered.lower()


# ---------------------------------------------------------------------------
# Real-target check (KRAS_G12C) -- skipped where prody/network is unavailable
# ---------------------------------------------------------------------------

def test_kras_g12c_real_target_near_chance_and_flat_dephasing():
    """Freshly computed (not extracted from the notebook -- see module
    docstring) KRAS_G12C default-parameter benchmark + a short dephasing
    sweep. Cross-checks PLAN.md's two qualitative headline findings
    ("near chance even with the answer key", "coherence adds ~nothing")
    against this package's own ported modules, using a real GDP-contact
    functional-site seed (mapped apo<->holo via superpose.align_apo_holo,
    NOT the mismatched-frame call that silently falls through to the
    top-degree fallback and gives noisier numbers -- verified by hand
    while writing this test).
    """
    pytest.importorskip("prody")
    from allostery.clean import clean
    from allostery.labels import ligand_groups_from_atomgroup, holo_pocket_mask, functional_indices
    from allostery.superpose import align_apo_holo

    try:
        apo = clean("4OBE", chains=["A"])
        holo = clean("6OIM", chains=["A"])
    except Exception as exc:  # network/RCSB fetch unavailable in this sandbox
        pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")

    import prody

    prody.confProDy(verbosity="none")
    holo_struct = prody.parsePDB("6OIM", compressed=False).select("chain A")
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)

    pocket_mask = holo_pocket_mask(apo, holo, "MOV", cutoff=4.5)
    assert pocket_mask is not None and pocket_mask.any()

    # functional_indices must be called in a single co-registered frame --
    # here, the holo frame (coords + ligand_groups both from 6OIM) -- then
    # mapped to apo via the alignment's common-residue correspondence.
    holo_src_idx, provenance = functional_indices(
        holo.coords, holo.ligand_groups, {"func_ligand": ["GDP"]}
    )
    assert provenance == "func_ligand-contact:GDP"

    alignment = align_apo_holo(apo, holo)
    holo_to_apo = dict(zip(alignment.holo_idx.tolist(), alignment.apo_idx.tolist()))
    apo_src_idx = np.array([holo_to_apo[i] for i in holo_src_idx if i in holo_to_apo])
    assert len(apo_src_idx) > 0

    bench = benchmark(apo.coords, apo.bfactors, apo_src_idx, pocket_mask, t_max=15.0, n_steps=500)
    auc_new = bench["H_new_default"]["AUC"]
    auc_10 = bench["H10_disorder_suppressed"]["AUC"]
    # "near chance even with the answer key" -- both default-parameter
    # operators land close to 0.5, not a strong discriminator. This is a
    # wide, documented sanity band around a freshly-computed 2026-07-07
    # value (~0.51 / ~0.53), not the *optimized* Sec.8 AUC~=0.53 PLAN.md
    # quotes (that optimizer is out of this task's scope).
    assert 0.3 < auc_new < 0.7
    assert 0.3 < auc_10 < 0.7

    H_new = build_H_new(apo.coords, apo.bfactors, cutoff=10.0)
    sweep = dephasing_sweep(
        H_new,
        omega_range=[0.0, 0.5, 1.0],
        labels=pocket_mask,
        source=apo_src_idx,
        t_max=8.0,
        rtol=1e-3,
        atol=1e-5,
    )
    # "coherence adds ~nothing" -- AUC barely moves across the sweep.
    assert sweep["auc_range"] < 0.1
    assert sweep["is_flat"] is True


def test_kras_g12c_dephasing_flat_survives_kappa_calibration():
    """PLAN-01.07.26.md's explicit caveat: the blind omega in [0,1] sweep's
    "flat" finding "must be re-tested with gamma calibrated from
    vibrational timescales... before we state it." TASK-0005 (superpose.py)
    now provides exactly that calibration (`calibrate_kappa` +
    `mode_energetics`'s `relaxation_time`) -- this test re-runs the sweep
    at a gamma scale derived from it instead of an arbitrary blind range,
    and confirms the finding survives (2026-07-07: even tighter, AUC range
    ~0.0035 vs the blind sweep's ~0.015-0.067 depending on functional-seed
    quality)."""
    pytest.importorskip("prody")
    from allostery.clean import clean
    from allostery.labels import ligand_groups_from_atomgroup, holo_pocket_mask, functional_indices
    from allostery.superpose import align_apo_holo, calibrate_kappa, anm_modes, mode_energetics

    try:
        apo = clean("4OBE", chains=["A"])
        holo = clean("6OIM", chains=["A"])
    except Exception as exc:
        pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")

    import prody

    prody.confProDy(verbosity="none")
    holo_struct = prody.parsePDB("6OIM", compressed=False).select("chain A")
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)

    holo_src_idx, _ = functional_indices(holo.coords, holo.ligand_groups, {"func_ligand": ["GDP"]})
    alignment = align_apo_holo(apo, holo)
    holo_to_apo = dict(zip(alignment.holo_idx.tolist(), alignment.apo_idx.tolist()))
    apo_src_idx = np.array([holo_to_apo[i] for i in holo_src_idx if i in holo_to_apo])
    pocket_mask = holo_pocket_mask(apo, holo, "MOV", cutoff=4.5)

    kappa = calibrate_kappa(apo.coords, apo.b_mean, cutoff=10.0)
    eigvals, eigvecs = anm_modes(apo.coords, cutoff=10.0, n_modes=20)
    common_idx = np.arange(len(apo.coords))
    # relaxation_time depends only on kappa/eigvals, not on any specific
    # delta_r, so a zero placeholder is fine for this gamma-scale purpose.
    energetics = mode_energetics(np.zeros(3 * len(common_idx)), eigvals, eigvecs, common_idx, kappa)
    gamma_scale = 1.0 / np.mean(energetics["relaxation_time"][:20])

    H_new = build_H_new(apo.coords, apo.bfactors, cutoff=10.0)
    calibrated_range = np.array([0.5 * gamma_scale, gamma_scale, 2.0 * gamma_scale])
    sweep = dephasing_sweep(
        H_new, calibrated_range, pocket_mask, source=apo_src_idx, t_max=8.0, rtol=1e-3, atol=1e-5
    )
    assert sweep["auc_range"] < 0.05
    assert sweep["is_flat"] is True


def test_kras_g12c_coherence_sensitivity_reproduces_kappa_calibration():
    """TASK-0099 Acceptance Scenario 3: the formal `coherence_sensitivity`
    wiring (used by `assemble_verdict_results`/`verdict_template`) must
    reproduce (or closely match) the already-validated ~0.0035 AUC range
    above, on the same real target and the same calibration recipe -- not
    a fresh, silently-diverging computation. Also exercises the
    TASK-0094 proximity-floor gate end to end on real data: an
    unambiguously flat sweep must classify COHERENCE_NOT_SIGNIFICANT."""
    pytest.importorskip("prody")
    from allostery.clean import clean
    from allostery.labels import ligand_groups_from_atomgroup, holo_pocket_mask, functional_indices
    from allostery.superpose import align_apo_holo, calibrate_kappa, anm_modes, mode_energetics

    try:
        apo = clean("4OBE", chains=["A"])
        holo = clean("6OIM", chains=["A"])
    except Exception as exc:
        pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")

    import prody

    prody.confProDy(verbosity="none")
    holo_struct = prody.parsePDB("6OIM", compressed=False).select("chain A")
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)

    holo_src_idx, _ = functional_indices(holo.coords, holo.ligand_groups, {"func_ligand": ["GDP"]})
    alignment = align_apo_holo(apo, holo)
    holo_to_apo = dict(zip(alignment.holo_idx.tolist(), alignment.apo_idx.tolist()))
    apo_src_idx = np.array([holo_to_apo[i] for i in holo_src_idx if i in holo_to_apo])
    pocket_mask = holo_pocket_mask(apo, holo, "MOV", cutoff=4.5)

    kappa = calibrate_kappa(apo.coords, apo.b_mean, cutoff=10.0)
    eigvals, eigvecs = anm_modes(apo.coords, cutoff=10.0, n_modes=20)
    common_idx = np.arange(len(apo.coords))
    energetics = mode_energetics(np.zeros(3 * len(common_idx)), eigvals, eigvecs, common_idx, kappa)
    gamma_scale = 1.0 / np.mean(energetics["relaxation_time"][:20])

    H_new = build_H_new(apo.coords, apo.bfactors, cutoff=10.0)
    floor_scores = [
        degree_centrality(apo.coords, cutoff=10.0),
        euclid_from_seed_centroid(apo.coords, apo_src_idx),
        hop_from_seed(apo.coords, apo_src_idx, cutoff=10.0),
    ]
    out = coherence_sensitivity(
        H_new, apo.bfactors, apo_src_idx, pocket_mask, gamma_scale,
        floor_scores=floor_scores, t_max=8.0, rtol=1e-3, atol=1e-5,
    )
    assert out["auc_range"] < 0.05
    assert out["is_flat"] is True
    assert out["classification"] == "COHERENCE_NOT_SIGNIFICANT"
