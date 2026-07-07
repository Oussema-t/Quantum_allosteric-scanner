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
    apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
    ligand = LigandGroup("LIG", 501, "A", np.array([COORDS[5]]), 1)
    holo = _Struct(COORDS.copy(), resnums=list(range(1, N + 1)), resnames=_SEQ3, ligand_groups=[ligand])
    return apo, holo


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
                get_pocket_mask(apo, holo, "T1", "LIG")

    def test_get_pocket_mask_succeeds_in_ceiling_context(self):
        apo, holo = _apo_holo_with_ligand()
        with ceiling_context():
            mask = get_pocket_mask(apo, holo, "T1", "LIG")
        assert mask is not None and mask.any()

    def test_get_pocket_mask_succeeds_unguarded(self):
        apo, holo = _apo_holo_with_ligand()
        mask = get_pocket_mask(apo, holo, "T1", "LIG")
        assert mask is not None

    def test_get_functional_indices_gated(self):
        apo, holo = _apo_holo_with_ligand()
        with frozen_context("T1"):
            with pytest.raises(LeakageError):
                get_functional_indices(apo.coords, holo.ligand_groups, "T1", {"func_ligand": ["LIG"]})

        idx, provenance = get_functional_indices(
            apo.coords, holo.ligand_groups, "T1", {"func_ligand": ["LIG"]}
        )
        assert len(idx) > 0

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
            mask = get_pocket_mask(apo, holo, "T1", "LIG")  # T1 is not blocked
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
                    get_pocket_mask(apo, holo, held_out, "LIG")
            # frozen_context has exited -- scoring against the true label
            # is legitimate here, not a firewall bypass.
            mask = get_pocket_mask(apo, holo, held_out, "LIG")
            assert mask is not None
