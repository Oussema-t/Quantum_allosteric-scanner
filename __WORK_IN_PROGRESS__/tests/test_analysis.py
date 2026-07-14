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
        return bench, abl, qvc, consistency

    def test_full_assembly_populates_every_verdict_template_key(self):
        bench, abl, qvc, consistency = self._real_outputs()
        results = assemble_verdict_results(
            benchmark_out=bench,
            ablation_out=abl,
            qvc_out=qvc,
            consistency_out=consistency,
            auc_apo_optimised=0.55,
            auc_holo_optimised=0.60,
        )
        expected_keys = {
            "AUC_apo_Hnew_default", "AUC_apo_H10_baseline",
            "AUC_apo_Hnew_optimised", "AUC_holo_Hnew_optimised",
            "AUC_ctqw_mean", "AUC_heat_mean",
            "most_impactful_term", "least_impactful_term",
            "mean_rho_apo_holo", "mean_jacc20",
        }
        assert expected_keys <= set(results)
        for key in expected_keys:
            assert results[key] is not None

    def test_render_has_no_na_for_any_populated_key(self):
        bench, abl, qvc, consistency = self._real_outputs()
        results = assemble_verdict_results(
            benchmark_out=bench,
            ablation_out=abl,
            qvc_out=qvc,
            consistency_out=consistency,
            auc_apo_optimised=0.55,
            auc_holo_optimised=0.60,
        )
        rendered = verdict_template(results, provenance="dev")
        assert "N/A" not in rendered

    def test_most_impactful_term_is_v_prefixed_and_not_l_only(self):
        _, abl, _, _ = self._real_outputs()
        results = assemble_verdict_results(ablation_out=abl)
        assert results["most_impactful_term"].startswith("V_")
        assert results["least_impactful_term"].startswith("V_")
        assert results["most_impactful_term"] != "V_L_only"

    def test_every_argument_is_independently_omittable(self):
        assert assemble_verdict_results() == {}
        bench, _, _, _ = self._real_outputs()
        results = assemble_verdict_results(benchmark_out=bench)
        assert set(results) == {"AUC_apo_Hnew_default", "AUC_apo_H10_baseline"}

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
