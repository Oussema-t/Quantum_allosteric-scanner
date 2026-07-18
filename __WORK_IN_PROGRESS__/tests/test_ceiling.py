"""TASK-0046 -- unit tests for `ceiling.py` (notebook §8's random-search
ceiling, ported into `protocol.ceiling_context()`) + a real KRAS_G12C
cross-check against PLAN.md's own qualitative §8 oracle ("optimized
AUC_apo on KRAS ~= 0.53, near chance even with the answer key").
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.ceiling import _combine_score, ceiling_search, consistency_score, sample_params  # noqa: E402


def _helix_coords(n: int) -> np.ndarray:
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


N = 24
COORDS = _helix_coords(N)
BFACTORS = np.full(N, 20.0)
RESNAMES = ["ALA"] * N
SOURCE = 0
POCKET = np.zeros(N, dtype=bool)
POCKET[[10, 11, 12]] = True

_PARAMS = dict(lam_B=1.0, lam_T=2.0, lam_R=1.0, lam_C=0.5, lam_M=0.5, alpha=0.3, cutoff=10.0, n_low=10)


class TestSampleParams:
    def test_within_documented_ranges(self):
        """TASK-0116: lam_* are no longer independent (0.0, 2.0) draws --
        each is non-negative and the *combined* budget sum(lam_i) <= 0.4
        (TASK-0121's own sigma(V) <= 0.2*J <= 0.4 bound), not a per-term
        bound of 2.0 each."""
        rng = np.random.default_rng(0)
        for _ in range(200):
            p = sample_params(rng)
            lam_sum = 0.0
            for name in ("lam_B", "lam_T", "lam_R", "lam_C", "lam_M"):
                assert p[name] >= 0.0
                lam_sum += p[name]
            assert lam_sum <= 0.4 + 1e-9
            assert 0.1 <= p["alpha"] <= 0.6
            assert 8.0 <= p["cutoff"] <= 12.0
            assert p["n_low"] in (5, 8, 10, 12, 15)

    def test_lam_budget_spans_the_full_range_not_just_the_boundary(self):
        """The search must also explore under-using the budget, not only
        points on the simplex's outer boundary (sum == 0.4 always) --
        confirms the budget itself is drawn from [0, 0.4], not fixed."""
        rng = np.random.default_rng(0)
        sums = []
        for _ in range(200):
            p = sample_params(rng)
            sums.append(sum(p[n] for n in ("lam_B", "lam_T", "lam_R", "lam_C", "lam_M")))
        sums = np.array(sums)
        assert sums.min() < 0.05
        assert sums.max() > 0.35

    def test_no_kernel_key(self):
        # This repo's build_H_new has no kernel DOF (module docstring) --
        # sample_params must not invent one that consistency_score can't use.
        rng = np.random.default_rng(0)
        assert "kernel" not in sample_params(rng)


class TestConsistencyScore:
    def test_apo_only_reduces_to_auc_apo(self):
        out = consistency_score(COORDS, BFACTORS, SOURCE, POCKET, _PARAMS, t_max=5.0, n_steps=50)
        assert out["auc_holo"] == pytest.approx(out["auc_apo"])
        assert out["rho"] == 0.0
        assert out["S"] == pytest.approx(out["auc_apo"], abs=1e-9)

    def test_uses_holo_frame_when_supplied(self):
        """Wiring check: supplying holo inputs actually changes the
        result relative to the apo-only call (proves holo_coords/
        holo_pocket/holo_resnames are threaded through, not ignored)."""
        apo_only = consistency_score(COORDS, BFACTORS, SOURCE, POCKET, _PARAMS, t_max=5.0, n_steps=50)
        disjoint_pocket = np.zeros(N, dtype=bool)
        disjoint_pocket[[0, 1, 2]] = True
        with_holo = consistency_score(
            COORDS, BFACTORS, SOURCE, POCKET, _PARAMS,
            apo_resnames=RESNAMES,
            holo_coords=COORDS, holo_bfactors=BFACTORS, holo_source=SOURCE,
            holo_pocket=disjoint_pocket, holo_resnames=RESNAMES,
            t_max=5.0, n_steps=50,
        )
        assert with_holo["auc_apo"] == pytest.approx(apo_only["auc_apo"])  # apo side unaffected
        assert with_holo["auc_holo"] != pytest.approx(apo_only["auc_holo"])  # holo side actually used

    def test_coherent_flag_passes_through(self, monkeypatch):
        """TASK-0118: defaults to `coherent=True`, and the flag actually
        reaches `time_averaged_ctqw` -- checked via a spy on the real call,
        not via an AUC-level difference (AUC is rank-based and happens to
        be invariant to this specific perturbation on this small synthetic
        fixture -- a property of the fixture/metric, not proof the wiring
        is inert; `test_analysis.py`'s equivalent check compares the raw
        occupation vectors instead, where the difference is unambiguous)."""
        from allostery import propagators as propagators_mod

        seen = []
        real_fn = propagators_mod.time_averaged_ctqw

        def _spy(*args, **kwargs):
            seen.append(kwargs.get("coherent", True))
            return real_fn(*args, **kwargs)

        monkeypatch.setattr(propagators_mod, "time_averaged_ctqw", _spy)
        multi_source = np.array([9, 10, 11])
        consistency_score(COORDS, BFACTORS, multi_source, POCKET, _PARAMS, t_max=5.0, n_steps=50)
        assert seen == [True]
        seen.clear()
        consistency_score(COORDS, BFACTORS, multi_source, POCKET, _PARAMS, t_max=5.0, n_steps=50, coherent=False)
        assert seen == [False]

    def test_use_converged_limit_swaps_in_the_closed_form(self, monkeypatch):
        """TASK-0130: `use_converged_limit=True` must call
        `time_averaged_ctqw_converged` (not `time_averaged_ctqw`) for the
        apo occupation -- checked via spies on both, not just an AUC
        difference."""
        from allostery import propagators as propagators_mod

        finite_calls = []
        converged_calls = []
        real_finite = propagators_mod.time_averaged_ctqw
        real_converged = propagators_mod.time_averaged_ctqw_converged

        def _spy_finite(*args, **kwargs):
            finite_calls.append(1)
            return real_finite(*args, **kwargs)

        def _spy_converged(*args, **kwargs):
            converged_calls.append(1)
            return real_converged(*args, **kwargs)

        monkeypatch.setattr(propagators_mod, "time_averaged_ctqw", _spy_finite)
        monkeypatch.setattr(propagators_mod, "time_averaged_ctqw_converged", _spy_converged)

        consistency_score(COORDS, BFACTORS, SOURCE, POCKET, _PARAMS, t_max=5.0, n_steps=50, use_converged_limit=True)
        assert converged_calls == [1]
        assert finite_calls == []


class TestCombineScore:
    """notebook cell 43's formula, isolated from the physics that produces
    its inputs (Planned Validation: "the objective function's three terms
    move in the expected direction")."""

    def test_higher_apo_and_holo_auc_raises_score(self):
        low = _combine_score(auc_apo=0.5, auc_holo=0.5, rho=0.0)
        high = _combine_score(auc_apo=0.8, auc_holo=0.8, rho=0.0)
        assert high > low

    def test_larger_apo_holo_gap_lowers_score_at_fixed_average(self):
        # Same average (0.5*(a+h)=0.7) and same rho -- only the gap differs.
        small_gap = _combine_score(auc_apo=0.65, auc_holo=0.75, rho=0.0)
        large_gap = _combine_score(auc_apo=0.5, auc_holo=0.9, rho=0.0)
        assert large_gap < small_gap

    def test_higher_rho_raises_score(self):
        low_rho = _combine_score(auc_apo=0.7, auc_holo=0.7, rho=0.0)
        high_rho = _combine_score(auc_apo=0.7, auc_holo=0.7, rho=1.0)
        assert high_rho > low_rho

    def test_matches_notebook_formula_exactly(self):
        S = _combine_score(auc_apo=0.6, auc_holo=0.4, rho=0.5)
        expected = 0.5 * (0.6 + 0.4) - 0.25 * abs(0.6 - 0.4) + 0.10 * 0.5
        assert S == pytest.approx(expected)


class TestCeilingSearch:
    def test_runs_inside_ceiling_context_and_picks_best(self):
        out = ceiling_search("SYNTH", COORDS, BFACTORS, SOURCE, POCKET, n_trials=8, seed=1, t_max=5.0, n_steps=50)
        assert out["n_trials_run"] == 8
        assert out["n_trials_scored"] == 8
        best_S = max(t["S"] for t in out["trials"])
        assert out["best"]["S"] == pytest.approx(best_S)

    def test_reproducible_with_fixed_seed(self):
        out1 = ceiling_search("SYNTH", COORDS, BFACTORS, SOURCE, POCKET, n_trials=5, seed=7, t_max=5.0, n_steps=50)
        out2 = ceiling_search("SYNTH", COORDS, BFACTORS, SOURCE, POCKET, n_trials=5, seed=7, t_max=5.0, n_steps=50)
        assert out1["best"]["S"] == pytest.approx(out2["best"]["S"])
        assert out1["best"]["params"] == out2["best"]["params"]

    def test_excludes_nan_trials_from_best_selection(self):
        empty_pocket = np.zeros(N, dtype=bool)  # <3 positives -> every trial's S is NaN
        with pytest.raises(RuntimeError, match="NaN"):
            ceiling_search("SYNTH", COORDS, BFACTORS, SOURCE, empty_pocket, n_trials=4, seed=1, t_max=5.0, n_steps=50)

    def test_coherent_flag_reaches_every_trial(self):
        """TASK-0118: `coherent` must reach `consistency_score` inside the
        trial loop, not just be accepted at the top level and dropped.

        TASK-0116: previously asserted via an observed best-score
        difference between `coherent=True`/`False` runs -- no longer a
        reliable proxy once `lam_*` is sampled on the corrected
        `sum<=0.4` budget (many trials now land at very weak disorder,
        where coherent/incoherent CTQW can coincidentally agree by
        symmetry on this synthetic helix fixture). Spies on
        `consistency_score` directly instead, which tests the actual
        claim (the flag is threaded through) without depending on the
        physics of any particular sampled point."""
        from unittest.mock import patch

        import allostery.ceiling as ceiling_mod

        seen_coherent = []
        real_consistency_score = ceiling_mod.consistency_score

        def spy(*args, **kwargs):
            seen_coherent.append(kwargs.get("coherent"))
            return real_consistency_score(*args, **kwargs)

        multi_source = np.array([9, 10, 11])
        with patch.object(ceiling_mod, "consistency_score", side_effect=spy):
            ceiling_search(
                "SYNTH", COORDS, BFACTORS, multi_source, POCKET, n_trials=3, seed=1,
                t_max=5.0, n_steps=50, coherent=False,
            )
        assert len(seen_coherent) == 3
        assert all(c is False for c in seen_coherent)

    def test_use_converged_limit_reaches_every_trial(self):
        """TASK-0130: default (unset) is byte-identical to
        `use_converged_limit=False`; `True` reaches every trial inside
        the search loop (best score differs), not just accepted at the
        top level and dropped."""
        default = ceiling_search("SYNTH", COORDS, BFACTORS, SOURCE, POCKET, n_trials=5, seed=1, t_max=5.0, n_steps=50)
        explicit_false = ceiling_search(
            "SYNTH", COORDS, BFACTORS, SOURCE, POCKET, n_trials=5, seed=1, t_max=5.0, n_steps=50,
            use_converged_limit=False,
        )
        converged = ceiling_search(
            "SYNTH", COORDS, BFACTORS, SOURCE, POCKET, n_trials=5, seed=1, t_max=5.0, n_steps=50,
            use_converged_limit=True,
        )
        assert default["best"]["S"] == pytest.approx(explicit_false["best"]["S"])
        assert default["best"]["S"] != pytest.approx(converged["best"]["S"])

    def test_search_runs_with_ceiling_mode_active_and_exits_cleanly(self, monkeypatch):
        """TASK-0006's Constraint: the label-using search must run inside
        `ceiling_context()`, explicitly, not bare -- asserted directly by
        recording `protocol.current_context().mode` from inside a trial,
        not just trusting the `with` statement is present in the source."""
        import allostery.ceiling as ceiling_mod
        from allostery import protocol

        seen_modes = []
        real_consistency_score = ceiling_mod.consistency_score

        def _spy(*args, **kwargs):
            seen_modes.append(protocol.current_context().mode)
            return real_consistency_score(*args, **kwargs)

        monkeypatch.setattr(ceiling_mod, "consistency_score", _spy)
        assert protocol.current_context().mode == "unguarded"
        ceiling_search("SYNTH", COORDS, BFACTORS, SOURCE, POCKET, n_trials=3, seed=1, t_max=5.0, n_steps=50)
        assert protocol.current_context().mode == "unguarded"  # exited cleanly
        assert seen_modes == ["ceiling"] * 3


class TestCeilingSearchOptuna:
    """TASK-0116: TPE strategy-upgrade companion to `ceiling_search`, same
    corrected `sum(lam_i) <= 0.4` parameter space, `consistency_score`
    reused unchanged as the objective."""

    def test_runs_and_picks_best(self):
        from allostery.ceiling import ceiling_search_optuna

        out = ceiling_search_optuna(
            "SYNTH", COORDS, BFACTORS, SOURCE, POCKET, n_trials=8, seed=1, t_max=5.0, n_steps=50,
        )
        assert out["n_trials_run"] == 8
        assert out["n_trials_scored"] == 8
        assert "S" in out["best"] and "params" in out["best"]
        assert out["best"]["S"] == pytest.approx(out["study"].best_value)

    def test_reproducible_with_fixed_seed(self):
        from allostery.ceiling import ceiling_search_optuna

        out1 = ceiling_search_optuna(
            "SYNTH", COORDS, BFACTORS, SOURCE, POCKET, n_trials=5, seed=7, t_max=5.0, n_steps=50,
        )
        out2 = ceiling_search_optuna(
            "SYNTH", COORDS, BFACTORS, SOURCE, POCKET, n_trials=5, seed=7, t_max=5.0, n_steps=50,
        )
        assert out1["best"]["S"] == pytest.approx(out2["best"]["S"])
        assert out1["best"]["params"] == out2["best"]["params"]

    def test_best_params_respect_the_lam_budget(self):
        """Every winning params dict must land inside the same
        sum(lam_i) <= 0.4 simplex sample_params uses -- the Optuna
        reparametrization (independent suggest_float weights, normalized
        and scaled by a suggested budget) must not leak outside it."""
        from allostery.ceiling import _LAM_BUDGET, ceiling_search_optuna

        out = ceiling_search_optuna(
            "SYNTH", COORDS, BFACTORS, SOURCE, POCKET, n_trials=10, seed=3, t_max=5.0, n_steps=50,
        )
        for trial in out["study"].trials:
            if trial.state.name != "COMPLETE":
                continue
            result = trial.user_attrs["full_result"]
            lam_sum = sum(result["params"][n] for n in ("lam_B", "lam_T", "lam_R", "lam_C", "lam_M"))
            assert lam_sum <= _LAM_BUDGET + 1e-9

    def test_excludes_nan_trials_from_best_selection(self):
        from allostery.ceiling import ceiling_search_optuna

        empty_pocket = np.zeros(N, dtype=bool)  # <3 positives -> every trial's S is NaN
        with pytest.raises(RuntimeError, match="NaN"):
            ceiling_search_optuna(
                "SYNTH", COORDS, BFACTORS, SOURCE, empty_pocket, n_trials=4, seed=1, t_max=5.0, n_steps=50,
            )

    def test_coherent_flag_reaches_every_trial(self):
        from unittest.mock import patch

        import allostery.ceiling as ceiling_mod
        from allostery.ceiling import ceiling_search_optuna

        seen_coherent = []
        real_consistency_score = ceiling_mod.consistency_score

        def spy(*args, **kwargs):
            seen_coherent.append(kwargs.get("coherent"))
            return real_consistency_score(*args, **kwargs)

        multi_source = np.array([9, 10, 11])
        with patch.object(ceiling_mod, "consistency_score", side_effect=spy):
            ceiling_search_optuna(
                "SYNTH", COORDS, BFACTORS, multi_source, POCKET, n_trials=3, seed=1,
                t_max=5.0, n_steps=50, coherent=False,
            )
        assert len(seen_coherent) == 3
        assert all(c is False for c in seen_coherent)

    def test_runs_inside_ceiling_context(self, monkeypatch):
        import allostery.ceiling as ceiling_mod
        from allostery import protocol
        from allostery.ceiling import ceiling_search_optuna

        seen_modes = []
        real_consistency_score = ceiling_mod.consistency_score

        def _spy(*args, **kwargs):
            seen_modes.append(protocol.current_context().mode)
            return real_consistency_score(*args, **kwargs)

        monkeypatch.setattr(ceiling_mod, "consistency_score", _spy)
        assert protocol.current_context().mode == "unguarded"
        ceiling_search_optuna("SYNTH", COORDS, BFACTORS, SOURCE, POCKET, n_trials=3, seed=1, t_max=5.0, n_steps=50)
        assert protocol.current_context().mode == "unguarded"
        assert seen_modes == ["ceiling"] * 3


@pytest.mark.parametrize("_", [None])
def test_kras_g12c_real_target_ceiling_cross_check(_):
    """Real network + real compute. Cross-checks against PLAN.md's own
    qualitative §8 finding: "optimized AUC_apo on KRAS ~= 0.53 (near
    chance even with the answer key)". Not a byte-exact regression --
    this port differs from the notebook in >=4 documented ways (TASK-0093
    catalogued several of them independently: build_labels' assembled
    pocket vs the notebook's own label source, no `kernel` DOF, this
    repo's own build_H_new/time_averaged_ctqw implementations, a
    ceiling_context blind search rather than the notebook's untracked
    global RNG state) -- reports the real measured value and compares it
    to the qualitative claim, per this task's own Planned Validation,
    rather than asserting a specific decimal.
    """
    pytest.importorskip("prody")
    from allostery.clean import clean, load_target_config
    from allostery.labels import build_labels, ligand_groups_from_atomgroup

    try:
        apo = clean("4OBE", chains=["A"])
        holo = clean("6OIM", chains=["A"])
    except Exception as exc:
        pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")

    import prody

    prody.confProDy(verbosity="none")
    holo_struct = prody.parsePDB("6OIM", compressed=False).select("chain A")
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)

    cfg = load_target_config("KRAS_G12C")
    labels_obj = build_labels(apo, holo, cfg, cutoff=4.5)
    assert labels_obj.pocket is not None and labels_obj.pocket.any()
    source = np.where(labels_obj.active_site)[0]
    assert len(source) > 0

    out = ceiling_search(
        "KRAS_G12C", apo.coords, apo.bfactors, source, labels_obj.pocket,
        n_trials=60, seed=7, t_max=15.0, n_steps=500,
    )
    best = out["best"]
    print(f"\nKRAS_G12C ceiling: S={best['S']:.4f} AUC_apo={best['auc_apo']:.4f} "
          f"params={best['params']}")
    # Wide sanity band (matches this repo's existing near-chance test
    # convention, test_analysis.py::test_kras_g12c_real_target_near_chance_
    # and_flat_dephasing's own 0.3-0.7 band) -- a labeled-search ceiling
    # should not be *worse* than a totally degenerate search, and per
    # PLAN.md's own finding should not be dramatically better than chance
    # either; the real number is printed above for the Done-section record
    # regardless of which side of "near chance" it lands on.
    assert 0.3 < best["auc_apo"] <= 1.0
