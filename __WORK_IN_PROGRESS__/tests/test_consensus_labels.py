"""TASK-0177 coverage -- consensus-label assembly logic and the
target-level distality helper, synthetic-only (no network/fpocket/
freesasa dependency -- those criteria are exercised by the real 7-target
run in `scripts/task0177_consensus_labels.py`, not here)."""
import numpy as np
import pytest

from allostery.consensus_labels import (
    CriterionResult,
    _apply_exclusions,
    assemble_consensus,
    chain_hop_from_seed,
    criterion_c6_distality,
)


def _mask(n: int, idx) -> np.ndarray:
    m = np.zeros(n, dtype=bool)
    m[list(idx)] = True
    return m


class TestAssembleConsensus:
    def test_all_four_agree_is_core_and_consensus(self):
        n = 10
        criteria = {
            name: CriterionResult(name, _mask(n, [2, 3, 4]), True)
            for name in ("C1_contact", "C2_dsasa", "C3_fpocket_holo", "C4_depositor_site")
        }
        out = assemble_consensus(criteria, n)
        assert out["n_criteria_available"] == 4
        np.testing.assert_array_equal(out["core"], _mask(n, [2, 3, 4]))
        np.testing.assert_array_equal(out["consensus"], _mask(n, [2, 3, 4]))
        assert not out["shell"].any()
        assert out["resolution"] == 0.0

    def test_partial_agreement_produces_shell(self):
        n = 10
        criteria = {
            "C1_contact": CriterionResult("C1_contact", _mask(n, [0, 1, 2]), True),
            "C2_dsasa": CriterionResult("C2_dsasa", _mask(n, [0, 1]), True),
            "C3_fpocket_holo": CriterionResult("C3_fpocket_holo", _mask(n, [0, 1, 3]), True),
            "C4_depositor_site": CriterionResult("C4_depositor_site", _mask(n, [0]), True),
        }
        out = assemble_consensus(criteria, n)
        # residue 0: 4 votes (core); 1: 3 votes (consensus, not core);
        # 2: 1 vote; 3: 1 vote -- neither in consensus.
        np.testing.assert_array_equal(out["core"], _mask(n, [0]))
        np.testing.assert_array_equal(out["consensus"], _mask(n, [0, 1]))
        np.testing.assert_array_equal(out["shell"], _mask(n, [1]))
        assert out["resolution"] == 1.0  # |shell|=1 / |core|=1

    def test_unavailable_criteria_excluded_not_treated_as_no_vote(self):
        n = 6
        criteria = {
            "C1_contact": CriterionResult("C1_contact", _mask(n, [0, 1]), True),
            "C2_dsasa": CriterionResult("C2_dsasa", _mask(n, [0, 1]), True),
            "C3_fpocket_holo": CriterionResult("C3_fpocket_holo", _mask(n, [0, 1]), True),
            "C4_depositor_site": CriterionResult("C4_depositor_site", None, False, {"reason": "unavailable"}),
        }
        out = assemble_consensus(criteria, n)
        assert out["n_criteria_available"] == 3
        # min(3, n_available=3) == 3 -- unanimous agreement of the 3
        # available criteria required for BOTH core and consensus.
        np.testing.assert_array_equal(out["core"], out["consensus"])
        assert out["resolution"] == 0.0

    def test_empty_core_reports_inf_resolution_not_a_crash(self):
        n = 6
        criteria = {
            "C1_contact": CriterionResult("C1_contact", _mask(n, [0]), True),
            "C2_dsasa": CriterionResult("C2_dsasa", _mask(n, [1]), True),
            "C3_fpocket_holo": CriterionResult("C3_fpocket_holo", _mask(n, [2]), True),
            "C4_depositor_site": CriterionResult("C4_depositor_site", _mask(n, [3]), True),
        }
        out = assemble_consensus(criteria, n)
        assert not out["core"].any()
        assert out["resolution"] == float("inf")

    def test_no_criteria_available_returns_none(self):
        n = 6
        criteria = {
            name: CriterionResult(name, None, False, {"reason": "x"})
            for name in ("C1_contact", "C2_dsasa", "C3_fpocket_holo", "C4_depositor_site")
        }
        out = assemble_consensus(criteria, n)
        assert out["core"] is None
        assert out["consensus"] is None
        assert out["n_criteria_available"] == 0
        assert out["resolution"] != out["resolution"]  # nan


class TestApplyExclusions:
    def test_active_site_and_terminal_removed(self):
        n = 10
        pocket = _mask(n, [1, 2, 3, 8])
        active_site = _mask(n, [2])
        terminal = _mask(n, [8, 9])
        out = _apply_exclusions(pocket, active_site, terminal)
        np.testing.assert_array_equal(out, _mask(n, [1, 3]))


class TestChainHopFromSeed:
    def test_within_chain_is_index_distance(self):
        chain_ids = ["A"] * 5 + ["B"] * 5
        dist = chain_hop_from_seed(chain_ids, source=np.array([2]), n=10)
        assert dist[0] == 2.0
        assert dist[4] == 2.0
        assert dist[2] == 0.0

    def test_cross_chain_is_unreachable(self):
        chain_ids = ["A"] * 5 + ["B"] * 5
        n = 10
        dist = chain_hop_from_seed(chain_ids, source=np.array([2]), n=n)
        assert dist[7] == float(n + 1)

    def test_multi_source_takes_minimum(self):
        chain_ids = ["A"] * 6
        dist = chain_hop_from_seed(chain_ids, source=np.array([0, 5]), n=6)
        # residue 3 is 3 away from source 0, 2 away from source 5 -- min is 2.
        assert dist[3] == 2.0


class TestCriterionC6Distality:
    def test_reports_unavailable_on_empty_masks(self):
        class _FakeApo:
            coords = np.zeros((4, 3))
            chain_ids = ["A"] * 4

        out = criterion_c6_distality(_FakeApo(), np.zeros(4, dtype=bool), np.zeros(4, dtype=bool))
        assert out["available"] is False

    def test_euclid_and_hop_on_a_simple_line(self):
        # 5 residues on a line, 3.8 A apart (typical Ca-Ca spacing) -- active
        # site at residue 0, pocket at residue 4.
        coords = np.column_stack([np.arange(5) * 3.8, np.zeros(5), np.zeros(5)])

        class _FakeApo:
            pass

        apo = _FakeApo()
        apo.coords = coords
        apo.chain_ids = ["A"] * 5
        apo.resnums = np.arange(5)
        active_site = _mask(5, [0])
        pocket = _mask(5, [4])
        out = criterion_c6_distality(apo, active_site, pocket)
        assert out["available"] is True
        assert out["euclid_min_A"] == pytest.approx(4 * 3.8)
        assert out["n_pocket"] == 1
