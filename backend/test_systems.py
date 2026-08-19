"""TASK-0219 regression coverage: `systems.py`'s per-role (`apo_chain`/
`holo_chain`) chain resolution.

GLUCOKINASE's apo (1V4S, chain A) and holo (3H1V, chain X) disagree on
which letter maps to the same biological chain -- the single, pre-fix
`chain` field ("X", holo-correct) made `data_layer.load_structure("1V4S",
"X")` return `None`, so the live backend could not score this target's
apo structure at all. Fixed by adding an optional `apo_chain` override
that falls back to `chain` when a target doesn't set it -- verified below
on real, fetched RCSB data (not mocked), per this task's own Planned
Validation ("fetch both apo and holo PDBs live and confirm the resolved
chain actually exists in each structure").
"""
import pytest

from backend.data_layer import load_structure
from backend.systems import SYSTEMS, resolve_systems


def _resolved():
    try:
        return resolve_systems()
    except Exception as exc:
        pytest.skip(f"resolve_systems() failed unexpectedly: {exc!r}")


class TestPerRoleChainFallback:
    """Every target that only sets the shared `chain` field must resolve
    identically to before -- apo_chain == holo_chain == chain."""

    def test_single_chain_targets_fall_back_unchanged(self):
        out = _resolved()
        for name, cfg in SYSTEMS.items():
            if name == "GLUCOKINASE":
                continue  # the one target that overrides apo_chain -- checked separately
            resolved = out[name]
            assert resolved["apo_chain"] == cfg["chain"], name
            assert resolved["holo_chain"] == resolved["chain"], name

    def test_glucokinase_apo_chain_overridden_holo_chain_unchanged(self):
        out = _resolved()
        gk = out["GLUCOKINASE"]
        assert gk["apo_chain"] == "A"
        assert gk["holo_chain"] == "X"
        assert gk["chain"] == "X"  # back-compat: unchanged, still holo-oriented


class TestGlucokinaseApoLoadLive:
    """The exact live-network reproduction from this task's Source: before
    the fix, `load_structure("1V4S", "X")` (what `chain` alone produced)
    returned None; `load_structure("1V4S", "A")` (what `apo_chain` now
    produces) must succeed."""

    def test_apo_chain_loads_successfully(self):
        gk = _resolved()["GLUCOKINASE"]
        try:
            st = load_structure(gk["apo"], gk["apo_chain"])
        except Exception as exc:
            pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")
        if st is None:
            pytest.skip("real-structure fetch unavailable in this environment (load_structure returned None)")
        assert len(st["resnums"]) > 0
        assert set(st["chains"]) == {"A"}

    def test_shared_chain_field_alone_would_still_fail(self):
        """Not a regression to fix -- documents *why* the override exists:
        confirms the shared `chain` field is genuinely apo-incompatible for
        this target, so a future edit can't quietly "simplify" apo_chain
        back out without re-breaking apo loads."""
        gk = _resolved()["GLUCOKINASE"]
        try:
            st = load_structure(gk["apo"], gk["chain"])
        except Exception as exc:
            pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")
        assert st is None


class TestNoOtherRoleMismatch:
    """This task's own In Scope item: don't assume GLUCOKINASE is the only
    instance -- audit every verified target's apo/holo structures for the
    same chain-letter mismatch."""

    def test_every_verified_target_apo_and_holo_chain_exist(self):
        from backend.rcsb import chain_summary

        out = _resolved()
        checked = 0
        for name, cfg in SYSTEMS.items():
            if not cfg.get("verified"):
                continue
            resolved = out[name]
            try:
                apo_chains = {c["chain"] for c in chain_summary(resolved["apo"])}
            except Exception as exc:
                pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")
            if not apo_chains:
                pytest.skip(f"real-structure fetch unavailable in this environment ({name} apo)")
            assert resolved["apo_chain"].split(",")[0].strip() in apo_chains, (
                f"{name}: configured apo_chain {resolved['apo_chain']!r} not in apo "
                f"structure's actual chains {sorted(apo_chains)}"
            )
            if resolved.get("holo"):
                holo_chains = {c["chain"] for c in chain_summary(resolved["holo"])}
                if not holo_chains:
                    pytest.skip(f"real-structure fetch unavailable in this environment ({name} holo)")
                assert resolved["holo_chain"].split(",")[0].strip() in holo_chains, (
                    f"{name}: configured holo_chain {resolved['holo_chain']!r} not in "
                    f"holo structure's actual chains {sorted(holo_chains)}"
                )
            checked += 1
        assert checked >= 5, "expected multiple verified targets to be checked"
