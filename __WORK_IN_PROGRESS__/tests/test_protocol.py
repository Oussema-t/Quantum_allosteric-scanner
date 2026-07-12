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
)


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
