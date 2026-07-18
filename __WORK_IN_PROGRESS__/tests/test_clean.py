"""TASK-0127 coverage -- clean_from_config's per-role chains override.

No network access: load_target_config/clean are monkeypatched so this
tests only the chain-selection logic clean_from_config itself owns.
"""
from unittest.mock import patch

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
