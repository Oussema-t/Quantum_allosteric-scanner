"""TASK-0006 coverage -- the DEV/FROZEN leakage firewall and
leave-one-protein-out protocol.

Synthetic apo/holo coordinate pairs only, no network fetch, no prody.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.hamiltonians import laplacian  # noqa: E402
from allostery.labels import LigandGroup  # noqa: E402
from allostery.protocol import (  # noqa: E402
    LeakageError,
    ProtocolRoster,
    assert_readable,
    ceiling_context,
    current_context,
    frozen_context,
    get_functional_indices,
    get_labels,
    get_pocket_mask,
    get_superpose_report,
    leave_one_protein_out,
    run_frozen_verdict,
    select_frozen_config,
    stamp_provenance,
    verify_frozen_stamp,
)
from allostery.diagnostics import FAILURE_CATEGORIES  # noqa: E402
from allostery.select import unsupervised_score  # noqa: E402


def _helix_coords(n: int) -> np.ndarray:
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


N = 12
COORDS = _helix_coords(N)
_SEQ3 = ["ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE", "LEU", "LYS"]


class _Struct:
    def __init__(self, coords, resnums, resnames, chain_ids=None, ligand_groups=None, b_mean=20.0):
        self.coords = coords
        self.resnums = np.asarray(resnums)
        self.resnames = list(resnames)
        self.chain_ids = list(chain_ids) if chain_ids is not None else ["A"] * len(resnums)
        self.ligand_groups = ligand_groups or []
        self.b_mean = b_mean


def _apo_holo_with_ligand():
    """Two disjoint ligands -- LIG (drug, near residue index 5) and FUNC
    (functional/orthosteric, near residue index 10) -- so
    `get_pocket_mask`'s assembled label (TASK-0070) has a real,
    non-overlapping active_site to exclude instead of falling through to
    the top-degree fallback, which on this 12-residue synthetic helix
    happens to swallow index 5 whole (verified empirically while writing
    this fixture)."""
    apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
    drug_ligand = LigandGroup("LIG", 501, "A", np.array([COORDS[5]]), 1)
    func_ligand = LigandGroup("FUNC", 502, "A", np.array([COORDS[10]]), 1)
    holo = _Struct(
        COORDS.copy(), resnums=list(range(1, N + 1)), resnames=_SEQ3,
        ligand_groups=[drug_ligand, func_ligand],
    )
    return apo, holo


_TARGET_CONFIG = {"drug_ligand": "LIG", "func_ligand": ["FUNC"]}


# ---------------------------------------------------------------------------
# Context managers
# ---------------------------------------------------------------------------

class TestContexts:
    def test_unguarded_by_default(self):
        assert current_context().mode == "unguarded"
        assert_readable("ANYTHING")  # must not raise

    def test_ceiling_context_blocks_nothing(self):
        with ceiling_context() as ctx:
            assert ctx.mode == "ceiling"
            assert_readable("KRAS_G12C")  # must not raise

    def test_frozen_context_blocks_named_target(self):
        with frozen_context("KRAS_G12C"):
            with pytest.raises(LeakageError):
                assert_readable("KRAS_G12C")

    def test_frozen_context_permits_other_targets(self):
        with frozen_context("KRAS_G12C"):
            assert_readable("BCR_ABL1")  # must not raise

    def test_frozen_context_accepts_iterable_of_targets(self):
        with frozen_context({"KRAS_G12C", "BCR_ABL1"}):
            with pytest.raises(LeakageError):
                assert_readable("BCR_ABL1")

    def test_context_releases_after_exit(self):
        with frozen_context("KRAS_G12C"):
            pass
        assert_readable("KRAS_G12C")  # must not raise -- block released

    def test_nested_context_innermost_wins(self):
        with frozen_context("KRAS_G12C"):
            with ceiling_context():
                assert_readable("KRAS_G12C")  # ceiling nested inside: not blocked
            with pytest.raises(LeakageError):
                assert_readable("KRAS_G12C")  # back to the outer frozen context


# ---------------------------------------------------------------------------
# Gated accessors
# ---------------------------------------------------------------------------

class TestGatedAccessors:
    def test_get_pocket_mask_raises_when_target_blocked(self):
        apo, holo = _apo_holo_with_ligand()
        with frozen_context("T1"):
            with pytest.raises(LeakageError):
                get_pocket_mask(apo, holo, "T1", _TARGET_CONFIG)

    def test_get_pocket_mask_succeeds_in_ceiling_context(self):
        apo, holo = _apo_holo_with_ligand()
        with ceiling_context():
            mask = get_pocket_mask(apo, holo, "T1", _TARGET_CONFIG)
        assert mask is not None and mask.any()

    def test_get_pocket_mask_succeeds_unguarded(self):
        apo, holo = _apo_holo_with_ligand()
        mask = get_pocket_mask(apo, holo, "T1", _TARGET_CONFIG)
        assert mask is not None

    def test_get_pocket_mask_returns_assembled_not_raw(self):
        """TASK-0070: get_pocket_mask must return the assembled (active-
        site/terminal-excluded) pocket, not labels.holo_pocket_mask's raw
        ligand-contact mask -- the defect this task fixes."""
        apo, holo = _apo_holo_with_ligand()
        from allostery.labels import build_labels

        mask = get_pocket_mask(apo, holo, "T1", _TARGET_CONFIG)
        expected = build_labels(apo, holo, _TARGET_CONFIG).pocket
        np.testing.assert_array_equal(mask, expected)

    def test_get_labels_gated(self):
        apo, holo = _apo_holo_with_ligand()
        with frozen_context("T1"):
            with pytest.raises(LeakageError):
                get_labels(apo, holo, "T1", _TARGET_CONFIG)

        labels = get_labels(apo, holo, "T1", _TARGET_CONFIG)
        assert labels.pocket is not None and labels.pocket.any()
        assert not (labels.pocket & labels.active_site).any()

    def test_get_functional_indices_gated(self):
        apo, holo = _apo_holo_with_ligand()
        with frozen_context("T1"):
            with pytest.raises(LeakageError):
                get_functional_indices(apo.coords, holo.ligand_groups, "T1", {"func_ligand": ["LIG"]})

        idx, provenance = get_functional_indices(
            apo.coords, holo.ligand_groups, "T1", {"func_ligand": ["LIG"]}
        )
        assert len(idx) > 0

    def test_get_functional_indices_forwards_heavy_atom_params(self):
        """TASK-0063: get_functional_indices must forward heavy_atom_coords/
        heavy_atom_seq_index to labels.functional_indices, not silently drop
        them -- confirmed by a case where the two approximations actually
        diverge (same construction as test_labels.py::
        TestContactResidueIndicesHeavyAtomFix, exercised through the gated
        protocol.py wrapper instead of labels.py directly, so this fails if
        the gate ever drops the parameters again even though labels.py's own
        tests would still pass)."""
        # residue 0's Calpha sits 6.0 A from the func ligand (outside the
        # default 4.5 A contact cutoff); a heavy atom on that same residue
        # sits right on top of it.
        ca_coords = np.array([[6.0, 0.0, 0.0], [50.0, 0.0, 0.0]])
        func_ligand = LigandGroup("FUNC", 502, "A", np.array([[0.0, 0.0, 0.0]]), 1)
        target_config = {"func_ligand": ["FUNC"]}

        idx_default, prov_default = get_functional_indices(
            ca_coords, [func_ligand], "T1", target_config,
        )
        assert prov_default == "top-degree fallback"  # Calpha-only misses the contact

        heavy_coords = np.array([[6.0, 0.0, 0.0], [0.2, 0.0, 0.0], [50.0, 0.0, 0.0]])
        heavy_seq_idx = np.array([0, 0, 1])  # first two heavy atoms both belong to residue 0
        idx_heavy, prov_heavy = get_functional_indices(
            ca_coords, [func_ligand], "T1", target_config,
            heavy_atom_coords=heavy_coords, heavy_atom_seq_index=heavy_seq_idx,
        )
        assert prov_heavy == "func_ligand-contact:FUNC"
        assert list(idx_heavy) == [0]
        assert prov_default != prov_heavy  # the two approximations genuinely diverge

    def test_get_superpose_report_gated(self):
        apo, holo = _apo_holo_with_ligand()
        with frozen_context("T1"):
            with pytest.raises(LeakageError):
                get_superpose_report(apo, holo, "T1", {"drug_ligand": "LIG"}, n_modes=5, cutoff=10.0)

        report = get_superpose_report(apo, holo, "T1", {"drug_ligand": "LIG"}, n_modes=5, cutoff=10.0)
        assert report["kappa"] > 0

    def test_gate_only_blocks_the_named_target_not_others(self):
        apo, holo = _apo_holo_with_ligand()
        with frozen_context("OTHER_TARGET"):
            mask = get_pocket_mask(apo, holo, "T1", _TARGET_CONFIG)  # T1 is not blocked
        assert mask is not None


# ---------------------------------------------------------------------------
# select_frozen_config (TASK-0064, closes SEAM-0009)
# ---------------------------------------------------------------------------

def _path_adjacency(n: int) -> np.ndarray:
    A = np.zeros((n, n))
    for i in range(n - 1):
        A[i, i + 1] = A[i + 1, i] = 1.0
    return A


def _star_adjacency(n: int) -> np.ndarray:
    A = np.zeros((n, n))
    for i in range(1, n):
        A[0, i] = A[i, 0] = 1.0
    return A


class TestSelectFrozenConfig:
    def test_picks_the_real_unsupervised_score_winner(self):
        """The winner must trace to unsupervised_score's actual ranking,
        not e.g. always-pick-first -- per SEAM-0009's own note that
        absence-of-leak alone is necessary but not sufficient evidence the
        wiring is real. Path vs. star (N=10, source=0, t=5.0) is a known,
        maximally-discriminating case (scores [-1, 1], star wins) --
        checked empirically before being hardcoded here, not guessed."""
        n = 10
        path_H = laplacian(_path_adjacency(n))
        star_H = laplacian(_star_adjacency(n))
        candidates = [
            {"H": path_H, "source": 0, "t": 5.0},
            {"H": star_H, "source": 0, "t": 5.0},
        ]

        winner = select_frozen_config(lambda: candidates, "T1")

        direct_scores = unsupervised_score(candidates)
        assert winner["index"] == int(direct_scores.argmax()) == 1
        assert winner["score"] == pytest.approx(direct_scores[1])
        assert winner["H"] is star_H  # caller's own keys survive untouched

    def test_picks_a_winner_with_a_real_multi_index_source(self):
        """TASK-0090: `select_frozen_config`'s real end-to-end path (not
        just `unsupervised_score` in isolation) must accept a multi-index
        `source` -- the actual candidate shape `protocol.run_frozen_verdict`
        wants to offer (`labels.Labels.active_site`, typically several
        residues), the reason TASK-0079.004 had to route around this
        module with a single-representative-seed workaround in the first
        place (see TASK-0090's own Context)."""
        n = 10
        path_H = laplacian(_path_adjacency(n))
        star_H = laplacian(_star_adjacency(n))
        candidates = [
            {"H": path_H, "source": np.array([0, 1]), "t": 5.0},
            {"H": star_H, "source": np.array([0, 1]), "t": 5.0},
        ]

        winner = select_frozen_config(lambda: candidates, "T1")

        direct_scores = unsupervised_score(candidates)
        assert np.all(np.isfinite(direct_scores))
        assert winner["index"] == int(direct_scores.argmax())
        assert winner["score"] == pytest.approx(direct_scores[winner["index"]])

    def test_blocks_a_candidate_builder_that_reads_the_held_out_target(self):
        """Candidate *construction*, not just scoring, must run inside the
        frozen_context -- unsupervised_score itself never touches labels,
        so only gating the scoring call could never catch a leaky builder.
        A poisoned builder that reads T1's assembled pocket via the gated
        accessor must raise, proving the gate actually wraps construction."""
        apo, holo = _apo_holo_with_ligand()

        def poisoned_build():
            get_pocket_mask(apo, holo, "T1", _TARGET_CONFIG)  # leaky read
            return [{"H": np.eye(4), "source": 0, "t": 1.0}]

        with pytest.raises(LeakageError):
            select_frozen_config(poisoned_build, "T1")

    def test_does_not_block_a_different_targets_read(self):
        """The gate is scoped to held_out_target only -- a builder reading
        some other, non-held-out target must succeed (mirrors
        test_gate_only_blocks_the_named_target_not_others)."""
        apo, holo = _apo_holo_with_ligand()

        def build():
            get_pocket_mask(apo, holo, "OTHER_TARGET", _TARGET_CONFIG)
            return [{"H": np.eye(4), "source": 0, "t": 1.0}]

        winner = select_frozen_config(build, "T1")
        assert winner["index"] == 0


# ---------------------------------------------------------------------------
# stamp_provenance / verify_frozen_stamp (TASK-0088, closes SEAM-0004)
# ---------------------------------------------------------------------------

class TestProvenanceStamp:
    def test_raises_outside_frozen_context(self):
        assert current_context().mode == "unguarded"
        with pytest.raises(RuntimeError):
            stamp_provenance({"AUC_apo_Hnew_optimised": 0.9})

    def test_raises_inside_ceiling_context_too(self):
        """Only mode == "frozen" counts -- ceiling_context is a different
        phase (leakage is explicitly the goal there), not a substitute."""
        with ceiling_context():
            with pytest.raises(RuntimeError):
                stamp_provenance({"AUC_apo_Hnew_optimised": 0.9})

    def test_stamped_results_verify_true(self):
        with frozen_context("T1"):
            stamped = stamp_provenance({"AUC_apo_Hnew_optimised": 0.9})
        assert verify_frozen_stamp(stamped) is True

    def test_does_not_mutate_the_input_dict(self):
        original = {"AUC_apo_Hnew_optimised": 0.9}
        with frozen_context("T1"):
            stamped = stamp_provenance(original)
        assert "_frozen_stamp" not in original
        assert stamped is not original

    def test_forged_token_does_not_verify(self):
        assert verify_frozen_stamp({"_frozen_stamp": "not-a-real-token"}) is False

    def test_missing_stamp_does_not_verify(self):
        assert verify_frozen_stamp({"AUC_apo_Hnew_optimised": 0.9}) is False

    def test_two_stamps_are_distinct_tokens(self):
        with frozen_context("T1"):
            a = stamp_provenance({"x": 1})
            b = stamp_provenance({"x": 2})
        assert a["_frozen_stamp"] != b["_frozen_stamp"]
        assert verify_frozen_stamp(a) and verify_frozen_stamp(b)


# ---------------------------------------------------------------------------
# ProtocolRoster
# ---------------------------------------------------------------------------

class TestProtocolRoster:
    def test_splits_dev_and_frozen(self):
        roster = ProtocolRoster.from_mapping({
            "KRAS_G12C": "frozen",
            "BCR_ABL1": "dev",
            "PTP1B": "dev",
        })
        assert roster.is_frozen("KRAS_G12C")
        assert not roster.is_dev("KRAS_G12C")
        assert roster.is_dev("BCR_ABL1")
        assert roster.is_dev("PTP1B")

    def test_rejects_unknown_phase_value(self):
        with pytest.raises(ValueError):
            ProtocolRoster.from_mapping({"KRAS_G12C": "maybe"})

    def test_unknown_target_is_neither(self):
        roster = ProtocolRoster.from_mapping({"KRAS_G12C": "frozen"})
        assert not roster.is_dev("SOME_OTHER_TARGET")
        assert not roster.is_frozen("SOME_OTHER_TARGET")


# ---------------------------------------------------------------------------
# leave_one_protein_out
# ---------------------------------------------------------------------------

class TestLeaveOneProteinOut:
    def test_every_target_held_out_exactly_once(self):
        targets = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "MYC_MAX"]
        held_outs = [held for _, held in leave_one_protein_out(targets)]
        assert sorted(held_outs) == sorted(targets)
        assert len(held_outs) == len(targets)

    def test_train_set_excludes_held_out(self):
        targets = ["A", "B", "C"]
        for train, held_out in leave_one_protein_out(targets):
            assert held_out not in train
            assert sorted(train + [held_out]) == sorted(targets)

    def test_empty_targets_yields_nothing(self):
        assert list(leave_one_protein_out([])) == []

    def test_does_not_itself_block_anything(self):
        """leave_one_protein_out is a plain generator -- no frozen_context
        is entered automatically (composability over magic, see docstring)."""
        for _train, held_out in leave_one_protein_out(["A", "B"]):
            assert_readable(held_out)  # must not raise -- no auto-guard

    def test_composes_with_frozen_context_then_releases_for_scoring(self):
        """The intended usage pattern: selection happens inside
        frozen_context (held-out blocked), scoring happens after it exits
        (held-out label now readable) -- both in the same loop body."""
        apo, holo = _apo_holo_with_ligand()
        targets = ["T1"]
        for _train, held_out in leave_one_protein_out(targets):
            with frozen_context({held_out}):
                with pytest.raises(LeakageError):
                    get_pocket_mask(apo, holo, held_out, _TARGET_CONFIG)
            # frozen_context has exited -- scoring against the true label
            # is legitimate here, not a firewall bypass.
            mask = get_pocket_mask(apo, holo, held_out, _TARGET_CONFIG)
            assert mask is not None


# ---------------------------------------------------------------------------
# run_frozen_verdict (TASK-0079.003)
# ---------------------------------------------------------------------------

_VERDICT_BFACTORS = np.full(N, 20.0)
_VERDICT_LABELS = np.zeros(N, dtype=bool)
_VERDICT_LABELS[[3, 4, 5]] = True


def _verdict_candidates():
    path_H = laplacian(_path_adjacency(N))
    star_H = laplacian(_star_adjacency(N))
    return [
        {"H": path_H, "source": 0, "t": 5.0},
        {"H": star_H, "source": 0, "t": 5.0},
    ]


class TestRunFrozenVerdict:
    def test_blocks_a_poisoned_candidate_builder(self):
        """Same 'poisoned builder' pattern as TestSelectFrozenConfig --
        candidate *construction* must run inside the gate this function
        opens, not just the scoring that follows."""
        apo, holo = _apo_holo_with_ligand()

        def poisoned_build():
            get_pocket_mask(apo, holo, "T1", _TARGET_CONFIG)  # leaky read
            return _verdict_candidates()

        with pytest.raises(LeakageError):
            run_frozen_verdict(
                "T1", poisoned_build, COORDS, _VERDICT_BFACTORS, 0,
                _VERDICT_LABELS, t_max=5.0, n_steps=50,
            )

    def test_does_not_block_a_different_targets_read(self):
        apo, holo = _apo_holo_with_ligand()

        def build():
            get_pocket_mask(apo, holo, "OTHER_TARGET", _TARGET_CONFIG)
            return _verdict_candidates()

        result = run_frozen_verdict(
            "T1", build, COORDS, _VERDICT_BFACTORS, 0,
            _VERDICT_LABELS, t_max=5.0, n_steps=50,
        )
        assert verify_frozen_stamp(result) is True

    def test_returns_a_verifiably_stamped_result(self):
        result = run_frozen_verdict(
            "T1", _verdict_candidates, COORDS, _VERDICT_BFACTORS, 0,
            _VERDICT_LABELS, t_max=5.0, n_steps=50,
        )
        assert verify_frozen_stamp(result) is True

    def test_gate_releases_after_the_call_returns(self):
        run_frozen_verdict(
            "T1", _verdict_candidates, COORDS, _VERDICT_BFACTORS, 0,
            _VERDICT_LABELS, t_max=5.0, n_steps=50,
        )
        assert_readable("T1")  # must not raise -- block released on return

    def test_composes_with_dot001_assembly(self):
        result = run_frozen_verdict(
            "T1", _verdict_candidates, COORDS, _VERDICT_BFACTORS, 0,
            _VERDICT_LABELS, t_max=5.0, n_steps=50,
        )
        for key in (
            "AUC_apo_Hnew_default", "AUC_apo_H10_baseline",
            "AUC_apo_Hnew_optimised", "AUC_ctqw_mean", "AUC_heat_mean",
            "most_impactful_term", "least_impactful_term",
        ):
            assert key in result

    def test_optimised_auc_traces_to_the_winning_candidate_not_a_fixed_one(self):
        """AUC_apo_Hnew_optimised must come from quantum_vs_classical on
        the winning candidate's own H -- swapping which candidate wins
        (star vs. path) must change the number, proving it is not
        silently reusing benchmark()'s fixed H_new_default value."""
        result = run_frozen_verdict(
            "T1", _verdict_candidates, COORDS, _VERDICT_BFACTORS, 0,
            _VERDICT_LABELS, t_max=5.0, n_steps=50,
        )
        winner_H = _verdict_candidates()[result["_winner_index"]]["H"]
        from allostery.analysis import quantum_vs_classical

        expected = quantum_vs_classical(
            winner_H, 0, _VERDICT_LABELS, t_max=5.0, n_steps=50,
        )["ctqw"]["AUC"]
        assert result["AUC_apo_Hnew_optimised"] == pytest.approx(expected)

    def test_coherent_flag_reaches_benchmark_and_the_winner_qvc(self, monkeypatch):
        """TASK-0118: defaults to `coherent=True`, and the flag reaches
        both `benchmark`'s and the winning candidate's `quantum_vs_
        classical`'s `time_averaged_ctqw` calls -- checked via a spy, not
        an AUC-level difference (AUC is rank-based and this small
        synthetic fixture's optimised-candidate AUC happens to be
        invariant to this specific perturbation, same caveat as
        `test_ceiling.py`'s equivalent fix)."""
        from allostery import propagators as propagators_mod

        seen = []
        real_fn = propagators_mod.time_averaged_ctqw

        def _spy(*args, **kwargs):
            seen.append(kwargs.get("coherent", True))
            return real_fn(*args, **kwargs)

        monkeypatch.setattr(propagators_mod, "time_averaged_ctqw", _spy)
        multi_source = np.array([2, 3, 4])
        run_frozen_verdict(
            "T1", _verdict_candidates, COORDS, _VERDICT_BFACTORS, multi_source,
            _VERDICT_LABELS, t_max=5.0, n_steps=50,
        )
        # select_frozen_config's own unsupervised_score/ablation() calls
        # are unaffected by this parameter (out of scope, see this
        # function's own docstring) and always coherent=True -- so the
        # default run must show no False at all.
        n_calls_default = len(seen)
        assert all(seen)
        seen.clear()
        run_frozen_verdict(
            "T1", _verdict_candidates, COORDS, _VERDICT_BFACTORS, multi_source,
            _VERDICT_LABELS, t_max=5.0, n_steps=50, coherent=False,
        )
        # Same total call count (same functions run either way); benchmark's
        # 2 calls + quantum_vs_classical's 1 call flip to False -- everything
        # else (select_frozen_config, ablation) stays True.
        assert len(seen) == n_calls_default
        assert seen.count(False) == 3
        assert seen.count(True) == n_calls_default - 3

    def test_use_converged_limit_reaches_benchmark_and_the_winner_qvc(self, monkeypatch):
        """TASK-0130: `use_converged_limit=True` must swap `benchmark`'s 2
        calls and the winning candidate's `quantum_vs_classical` call (3
        total, same call sites `test_coherent_flag_reaches_benchmark_and_
        the_winner_qvc` counts above) from `time_averaged_ctqw` to
        `time_averaged_ctqw_converged` -- checked via spies on both, not
        an AUC-level difference. `ablation()`'s own 6 `time_averaged_ctqw`
        calls (L_only + 5 terms) are legitimately unaffected -- out of
        this parameter's scope, same "select_frozen_config/ablation
        unaffected" boundary the `coherent` flag's own test documents
        above -- so `finite_calls` is not asserted empty, only that the 3
        benchmark/qvc call sites specifically moved."""
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

        run_frozen_verdict(
            "T1", _verdict_candidates, COORDS, _VERDICT_BFACTORS, 0,
            _VERDICT_LABELS, t_max=5.0, n_steps=50, use_converged_limit=True,
        )
        assert len(converged_calls) == 3
        n_calls_default = len(finite_calls)
        finite_calls.clear()
        converged_calls.clear()
        run_frozen_verdict(
            "T1", _verdict_candidates, COORDS, _VERDICT_BFACTORS, 0,
            _VERDICT_LABELS, t_max=5.0, n_steps=50, use_converged_limit=False,
        )
        # Same ablation/select_frozen_config calls (unaffected) plus the 3
        # benchmark/qvc calls, now on the finite side instead.
        assert len(finite_calls) == n_calls_default + 3
        assert converged_calls == []

    def test_diagnosis_and_winner_metadata_present(self):
        result = run_frozen_verdict(
            "T1", _verdict_candidates, COORDS, _VERDICT_BFACTORS, 0,
            _VERDICT_LABELS, t_max=5.0, n_steps=50,
        )
        assert result["_diagnosis"] in FAILURE_CATEGORIES
        assert result["_winner_index"] in (0, 1)
        assert isinstance(result["_winner_score"], float)

    def test_floor_scores_feeds_into_diagnosis(self):
        """A floor identical to the winning config's own score always
        satisfies classify_failure's `score_auc <= floor_auc` -- so
        re-running with floor_scores set to the actual winner's own
        occupation vector must flip a NO_FAILURE_DETECTED baseline to
        BEATS_CHANCE_NOT_FLOOR (SEAM-0005), proving floor_scores is
        actually threaded through to classify_failure, not silently
        dropped. Skipped if the baseline itself isn't a clean pass (a
        legitimate NO_SIGNAL_IN_APO/LABEL_SUSPECT result on this small
        synthetic fixture wouldn't reach the floor check at all, per
        classify_failure's own documented check order)."""
        from allostery.analysis import quantum_vs_classical
        from allostery.diagnostics import BEATS_CHANCE_NOT_FLOOR, NO_FAILURE_DETECTED

        baseline = run_frozen_verdict(
            "T1", _verdict_candidates, COORDS, _VERDICT_BFACTORS, 0,
            _VERDICT_LABELS, t_max=5.0, n_steps=50,
        )
        if baseline["_diagnosis"] != NO_FAILURE_DETECTED:
            pytest.skip(f"baseline diagnosis was {baseline['_diagnosis']!r}, not a clean pass")

        winner_H = _verdict_candidates()[baseline["_winner_index"]]["H"]
        winner_occ = quantum_vs_classical(winner_H, 0, t_max=5.0, n_steps=50)["ctqw"]

        result = run_frozen_verdict(
            "T1", _verdict_candidates, COORDS, _VERDICT_BFACTORS, 0,
            _VERDICT_LABELS, t_max=5.0, n_steps=50,
            floor_scores=winner_occ,
        )
        assert result["_diagnosis"] == BEATS_CHANCE_NOT_FLOOR

    def test_holo_side_omitted_without_holo_inputs(self):
        result = run_frozen_verdict(
            "T1", _verdict_candidates, COORDS, _VERDICT_BFACTORS, 0,
            _VERDICT_LABELS, t_max=5.0, n_steps=50,
        )
        assert "AUC_holo_Hnew_optimised" not in result
        assert "mean_rho_apo_holo" not in result
        assert "mean_jacc20" not in result

    def test_holo_side_populated_when_supplied(self):
        holo_H = laplacian(_path_adjacency(N))
        idx = np.arange(N)
        result = run_frozen_verdict(
            "T1", _verdict_candidates, COORDS, _VERDICT_BFACTORS, 0,
            _VERDICT_LABELS, t_max=5.0, n_steps=50,
            holo_H=holo_H, holo_source=0, holo_labels=_VERDICT_LABELS,
            apo_idx=idx, holo_idx=idx,
        )
        assert "AUC_holo_Hnew_optimised" in result
        assert "mean_rho_apo_holo" in result
        assert "mean_jacc20" in result
