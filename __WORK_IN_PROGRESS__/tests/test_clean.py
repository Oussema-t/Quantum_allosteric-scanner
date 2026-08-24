"""TASK-0127 coverage -- clean_from_config's per-role chains override.
TASK-0038 coverage -- clean()'s connectivity check is warn-only, matching
the (corrected) module docstring, not the raise the docstring used to
claim.

No network access: load_target_config/clean are monkeypatched so this
tests only the chain-selection logic clean_from_config itself owns.
"""
from unittest.mock import patch

import numpy as np
import pytest

from allostery import clean as clean_mod


def _patched(cfg, role):
    """Call clean_from_config with cfg injected via load_target_config,
    capturing the `chains` kwarg clean() actually receives."""
    captured = {}

    def fake_clean(pdb_id, chains=None, keep_nucleic=False):
        captured["pdb_id"] = pdb_id
        captured["chains"] = chains
        return "SENTINEL_RESULT"

    with patch.object(clean_mod, "load_target_config", return_value=cfg), \
         patch.object(clean_mod, "clean", side_effect=fake_clean):
        result = clean_mod.clean_from_config("FAKE_TARGET", role=role)
    return result, captured


class TestCleanFromConfigChainOverride:
    def test_falls_back_to_shared_chains_when_no_per_role_override(self):
        """Every pre-existing target config only ever sets `chains` --
        must be completely unaffected by the new override fields."""
        cfg = {"apo_pdb": "1AAA", "holo_pdb": "1BBB", "chains": ["A"]}
        result, captured = _patched(cfg, role="apo")
        assert result == "SENTINEL_RESULT"
        assert captured["chains"] == ["A"]

    def test_apo_chains_override_takes_precedence_for_apo_role(self):
        cfg = {
            "apo_pdb": "1V4S", "holo_pdb": "3H1V",
            "chains": None, "apo_chains": ["A"], "holo_chains": ["X"],
        }
        _, captured = _patched(cfg, role="apo")
        assert captured["pdb_id"] == "1V4S"
        assert captured["chains"] == ["A"]

    def test_holo_chains_override_takes_precedence_for_holo_role(self):
        cfg = {
            "apo_pdb": "1V4S", "holo_pdb": "3H1V",
            "chains": None, "apo_chains": ["A"], "holo_chains": ["X"],
        }
        _, captured = _patched(cfg, role="holo")
        assert captured["pdb_id"] == "3H1V"
        assert captured["chains"] == ["X"]

    def test_missing_role_override_falls_back_to_shared_chains(self):
        """Only one role overridden -- the other role still falls back to
        the shared `chains` field, not to None."""
        cfg = {
            "apo_pdb": "1AAA", "holo_pdb": "1BBB",
            "chains": ["A", "B"], "holo_chains": ["X"],
        }
        _, captured_apo = _patched(cfg, role="apo")
        assert captured_apo["chains"] == ["A", "B"]
        _, captured_holo = _patched(cfg, role="holo")
        assert captured_holo["chains"] == ["X"]

    def test_missing_pdb_id_still_raises(self):
        cfg = {"apo_pdb": "1AAA", "holo_pdb": None, "chains": ["A"]}
        try:
            _patched(cfg, role="holo")
            assert False, "expected ValueError"
        except ValueError as e:
            assert "holo_pdb" in str(e)


class TestAssertConnectedIsWarnOnly:
    """TASK-0038: `_assert_connected` must warn, not raise, on a
    disconnected Cα graph -- and the warning must actually name the
    problem, not just fire silently. Synthetic two-cluster input, per the
    task's own Planned Validation."""

    def _two_disconnected_clusters(self):
        # Cluster A: 4 points near the origin, all pairwise < 10 Å apart.
        # Cluster B: 4 points near (1000, 0, 0), same local spacing, but
        # far enough from cluster A that no cross-cluster pair is within
        # the default 10 Å cutoff -- two components, unambiguous.
        cluster_a = np.array([[0.0, 0.0, 0.0], [3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [3.0, 3.0, 0.0]])
        cluster_b = cluster_a + np.array([1000.0, 0.0, 0.0])
        return np.vstack([cluster_a, cluster_b])

    def test_disconnected_input_does_not_raise(self):
        coords = self._two_disconnected_clusters()
        warn_list: list[str] = []
        clean_mod._assert_connected(coords, "FAKE_PDB", warn_list)
        # No exception -- if this ever raises, that's the TASK-0038
        # behavior change and must be a deliberate decision, not a
        # silent regression this test fails to catch.

    def test_disconnected_input_appends_a_warning_naming_the_problem(self):
        coords = self._two_disconnected_clusters()
        warn_list: list[str] = []
        clean_mod._assert_connected(coords, "FAKE_PDB", warn_list)
        assert len(warn_list) == 1
        assert "FAKE_PDB" in warn_list[0]
        assert "2 connected" in warn_list[0]

    def test_connected_input_appends_no_warning(self):
        """Sanity check on the fixture/function pairing itself: a single
        compact cluster must NOT trip the warning, or the two tests above
        would be meaningless."""
        coords = np.array([[0.0, 0.0, 0.0], [3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [3.0, 3.0, 0.0]])
        warn_list: list[str] = []
        clean_mod._assert_connected(coords, "FAKE_PDB", warn_list)
        assert warn_list == []


class TestAltlocHighestOccupancy:
    """TASK-0039: `clean()`'s own docstring promises "only the 'A' alt-loc
    (or highest occupancy) is kept" -- the code used to unconditionally
    select 'A' with no comparison at all. Real structures used throughout
    (not mocks) -- ProDy's own `AtomGroup` has enough surface area that a
    hand-rolled mock would either be unfaithful or nearly as much code as
    the real parse; this project's own established preference (TASK-0235/
    TASK-0241) is real data over mocks when a real regression case exists.

    8QYR (this register's own CARDIAC_MYOSIN `holo_pdb`) supplies a REAL,
    not synthetic, case where a non-'A' label has the highest occupancy --
    stronger evidence than a synthetic fixture would be, found via direct
    survey (`scripts/task0039_altloc_survey.py`) before writing this test,
    not assumed. Also confirms the deeper root cause this task's own filing
    did not anticipate: ProDy's `parsePDB` default (`altloc="A"`) silently
    drops every non-'A' conformer before `clean()`'s own selection code
    ever runs -- `clean()` must call it with `altloc="all"` for any
    occupancy comparison to be possible at all.
    """

    def test_8qyr_chain_b_residue_616_keeps_highest_occupancy_conformer(self):
        """Raw PDB (`pdb_cache/8qyr.pdb`): CA altloc A occupancy 0.25,
        B occupancy 0.25, C occupancy 0.50 -- C must win, not the
        previously-hardcoded 'A' (occupancy 0.25, half of C's)."""
        result = clean_mod.clean("8QYR", chains=["B"])
        assert 616 in result.resnums
        idx = list(result.resnums).index(616)
        # Real coordinate for the CA C altloc, read directly off the raw
        # PDB record (`ATOM 4582 CA CMET B 616 -3.392 -13.193 -5.627`) --
        # not the A altloc's (-3.375, -13.202, -5.622).
        expected_c = np.array([-3.392, -13.193, -5.627])
        assert result.coords[idx] == pytest.approx(expected_c, abs=1e-3)
        assert any("B616(altloc=C)" in w for w in result.warnings)

    def test_8qyr_flags_exactly_the_one_non_a_residue_found_by_direct_survey(self):
        """Guards against over-flagging: the direct survey
        (`task0039_altloc_survey.py`) found exactly 1 non-'A'-wins residue
        in 8QYR (of 3 multi-altloc residues total) -- not 0, not all 3."""
        result = clean_mod.clean("8QYR", chains=["B"])
        non_a_warnings = [w for w in result.warnings if "non-'A' alt-loc" in w]
        assert len(non_a_warnings) == 1
        assert "1 residue(s)" in non_a_warnings[0]

    def test_5mo4_keeps_a_where_a_genuinely_has_higher_occupancy(self):
        """Regression: 5MO4 (this register's own BCR_ABL1 `holo_pdb`) has
        real alt-locs where 'A' IS the genuinely correct highest-occupancy
        pick (confirmed by direct survey) -- must not spuriously flag a
        non-'A' winner just because alt-locs are present at all."""
        result = clean_mod.clean("5MO4", chains=["A"])
        assert result.n_residues == 429
        assert any("alternate locations detected" in w for w in result.warnings)
        assert not any("non-'A' alt-loc" in w for w in result.warnings)

    def test_4obe_no_altloc_present_unaffected(self):
        """Regression: a real benchmark target (KRAS_G12C `holo_pdb`) with
        NO alt-locs at all must produce zero alt-loc-related warnings and
        its already-known residue count, completely unaffected by this
        task's own change (the block is a pure no-op when `getAltlocs()`
        has no non-blank entries)."""
        result = clean_mod.clean("4OBE", chains=["A"])
        assert result.n_residues == 169
        assert not any("altloc" in w.lower() or "alternate location" in w.lower() for w in result.warnings)
