"""TASK-0231 -- the test suite was blind to config-level breakage:
`func_ligand`'s human-readable-description defect ([[TASK-0216]]) shipped
on 9/13 targets with the full suite green throughout, because nothing
ever asserted on `functional_indices`'s own provenance tier. Demonstrated
directly: reverting GLUCOKINASE's `func_ligand` to the pre-fix value and
re-running the suite -- 1208 passed, 0 failures, 0 warnings surfaced as
failures.

Four guards, matching this task's own Intent Contract:
  1. Provenance assertion (`labels.assert_functional_provenance_allowed`,
     wired into `build_labels` itself -- real pipeline runs are protected,
     not just this test file).
  2. Config-integrity: every declared `func_ligand` code, for every real
     target, actually resolves to a ligand present in that target's own
     (chain-restricted) holo entry.
  3. Golden-value pins on the label pipeline (pocket size / active-site
     size / provenance) for the mandatory + ASD-verified targets.
  4. The GLUCOKINASE mutation itself, encoded as a permanent regression
     test -- the guard is verified to actually fire, not assumed to.

Real network throughout (RCSB fetch) -- same skip-on-fetch-failure
convention as `test_fpocket_pin.py`/`test_analysis_characterization.py`:
try the real thing, `pytest.skip` if the environment can't provide it,
never silently pass on a mock standing in for a real number.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
_SCRIPTS = _ROOT / "scripts"
for _p in (_SRC, _SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from allostery.clean import load_target_config  # noqa: E402
from allostery.labels import (  # noqa: E402
    assert_functional_provenance_allowed,
    build_labels,
)

CONFIG_PATH = _ROOT / "config" / "targets.yaml"

# Targets whose `func_ligand` is genuinely empty (no functional/substrate
# ligand exists in the holo entry at all) -- resolved instead via
# `active_site_uniprot` (tier 2). Confirmed, not assumed: `functional_
# indices`'s own docstring names exactly these three (TASK-0217.003).
NO_FUNC_LIGAND_TARGETS = {"PTP1B", "CASPASE1", "CASPASE7"}

# TASK-0231's own live finding (2026-08-23, not anticipated when this task
# was filed): CARDIAC_MYOSIN_TABLE1's own func_ligand=["ADP","ATP"] never
# resolves either -- ADP is real in 6C1H but bound to the actin chains
# (A-E), not the myosin-Ib chain (P) this config restricts holo to, so
# `ligand_groups` is empty under this config's own chain restriction.
# Corrected the config's own (wrong) comment and added the explicit
# `allow_topdegree_fallback` opt-in this task's guard now requires --
# see targets.yaml's own updated comment for the full explanation.
CHAIN_RESTRICTED_NO_MATCH_TARGETS = {"CARDIAC_MYOSIN_TABLE1"}

MANDATORY_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
ASD_VERIFIED_TARGETS = ["PTP1B", "CASPASE7", "CASPASE1", "GLUCOKINASE"]
PINNED_TARGETS = MANDATORY_TARGETS + ASD_VERIFIED_TARGETS


def _all_real_targets() -> list:
    import yaml

    with open(CONFIG_PATH) as f:
        data = yaml.safe_load(f)
    names = []
    for name, cfg in data["targets"].items():
        if cfg.get("holo_pdb"):  # MYC_MAX has none -- build_labels can't run
            names.append(name)
    return names


def _load_real_apo_holo(name: str, target_config: dict):
    """Same real-fetch shape `task0230_ceiling_and_brittleness._load_apo_holo`
    uses (imported, not copied) -- apo/holo CleanResult + holo.ligand_groups
    populated for a real `build_labels` call."""
    from task0230_ceiling_and_brittleness import _load_apo_holo

    return _load_apo_holo(name, target_config)


# ---------------------------------------------------------------------------
# 1. Provenance assertion -- fast, synthetic, no network (the guard's own logic)
# ---------------------------------------------------------------------------

class TestFunctionalProvenanceGuard:
    def test_raises_on_fallback_without_optin(self):
        with pytest.raises(ValueError, match="top-degree fallback"):
            assert_functional_provenance_allowed("top-degree fallback", {}, target_name="FAKE")

    def test_allows_fallback_with_explicit_optin(self):
        assert_functional_provenance_allowed(
            "top-degree fallback", {"allow_topdegree_fallback": True}, target_name="FAKE"
        )  # must not raise

    def test_does_not_fire_on_real_tiers(self):
        for prov in ("func_ligand-contact:GDP", "active_site_uniprot"):
            assert_functional_provenance_allowed(prov, {}, target_name="FAKE")  # must not raise

    def test_error_names_the_target(self):
        with pytest.raises(ValueError, match="FAKE_TARGET_NAME"):
            assert_functional_provenance_allowed(
                "top-degree fallback", {}, target_name="FAKE_TARGET_NAME"
            )


# ---------------------------------------------------------------------------
# 2. Config-integrity -- every declared func_ligand code resolves to a real
#    ligand present in that target's own (chain-restricted) holo entry.
# ---------------------------------------------------------------------------

class TestConfigIntegrityFuncLigandResolves:
    @pytest.mark.parametrize("name", sorted(set(_all_real_targets()) - NO_FUNC_LIGAND_TARGETS - CHAIN_RESTRICTED_NO_MATCH_TARGETS))
    def test_func_ligand_resolves_to_real_holo_ligand(self, name):
        target_config = load_target_config(name)
        declared = target_config.get("func_ligand") or []
        if not declared:
            pytest.skip(f"{name}: func_ligand is empty and not in the known-empty set -- "
                        "investigate before assuming this belongs in NO_FUNC_LIGAND_TARGETS")
        try:
            apo, holo = _load_real_apo_holo(name, target_config)
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")
        real_resnames = {g.resname for g in holo.ligand_groups}
        matched = [code for code in declared if code in real_resnames]
        assert matched, (
            f"{name}: none of declared func_ligand {declared!r} present in holo's own "
            f"ligand_groups {sorted(real_resnames)!r} (chain-restricted per this target's "
            "own config) -- config-level breakage, exactly TASK-0231's own class of defect."
        )

    @pytest.mark.parametrize("name", sorted(NO_FUNC_LIGAND_TARGETS))
    @pytest.mark.xfail(reason=(
        "func_ligand is genuinely empty -- this holo entry contains no "
        "functional/substrate ligand at all (TASK-0217.003); the active "
        "site is resolved instead via active_site_uniprot (tier 2), not "
        "checked by this test. Expected failure, not a defect."
    ), strict=True)
    def test_func_ligand_resolves_to_real_holo_ligand_known_empty(self, name):
        target_config = load_target_config(name)
        declared = target_config.get("func_ligand") or []
        assert declared, f"{name}: func_ligand is non-empty -- update NO_FUNC_LIGAND_TARGETS"

    @pytest.mark.parametrize("name", sorted(CHAIN_RESTRICTED_NO_MATCH_TARGETS))
    @pytest.mark.xfail(reason=(
        "TASK-0231 (2026-08-23): func_ligand is declared and the ligand is "
        "real in the holo PDB entry, but bound to a chain this target's "
        "own config excludes from holo_chains -- ligand_groups is "
        "genuinely empty under this config's own restriction. Consistent "
        "with TASK-0222's own already-accepted NO_SIGNAL_IN_APO verdict "
        "for this target, made explicit via allow_topdegree_fallback "
        "rather than silent. Expected failure, not a defect."
    ), strict=True)
    def test_func_ligand_resolves_to_real_holo_ligand_chain_restricted(self, name):
        target_config = load_target_config(name)
        try:
            apo, holo = _load_real_apo_holo(name, target_config)
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")
        declared = target_config.get("func_ligand") or []
        real_resnames = {g.resname for g in holo.ligand_groups}
        matched = [code for code in declared if code in real_resnames]
        assert matched, f"{name}: confirmed still unresolved under chain restriction"


# ---------------------------------------------------------------------------
# 3. Golden-value pins -- pocket size / active-site size / provenance,
#    mandatory + ASD-verified targets. Pinned 2026-08-23 against real,
#    live-fetched RCSB structures (this task's own run, recorded here so a
#    future divergence is traceable to "when and from what").
# ---------------------------------------------------------------------------

_GOLDEN = {
    # name: (pocket_size, active_site_size, provenance)
    "KRAS_G12C": (17, 18, "func_ligand-contact:GDP"),
    "BCR_ABL1": (16, 26, "func_ligand-contact:NIL"),
    "CARDIAC_MYOSIN": (13, 18, "func_ligand-contact:ADP"),
    "PTP1B": (14, 9, "active_site_uniprot"),
    "CASPASE7": (7, 2, "active_site_uniprot"),
    "CASPASE1": (6, 2, "active_site_uniprot"),
    "GLUCOKINASE": (17, 16, "func_ligand-contact:GLC"),
}


class TestLabelPipelineGoldenValues:
    @pytest.mark.parametrize("name", PINNED_TARGETS)
    def test_pocket_and_active_site_size_pinned(self, name):
        target_config = load_target_config(name)
        try:
            apo, holo = _load_real_apo_holo(name, target_config)
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")

        cutoff = target_config.get("pocket_contact_cutoff", 4.5)
        labels_obj = build_labels(apo, holo, target_config, cutoff=cutoff, target_name=name)

        pocket_size = int(labels_obj.pocket.sum()) if labels_obj.pocket is not None else None
        active_size = int(labels_obj.active_site.sum())
        provenance = labels_obj.functional_provenance

        exp_pocket, exp_active, exp_prov = _GOLDEN[name]
        assert (pocket_size, active_size, provenance) == (exp_pocket, exp_active, exp_prov), (
            f"{name}: label pipeline drifted from its 2026-08-23 pin -- "
            f"got (pocket={pocket_size}, active_site={active_size}, "
            f"provenance={provenance!r}), pinned "
            f"(pocket={exp_pocket}, active_site={exp_active}, provenance={exp_prov!r}). "
            "If this is a deliberate, understood change (e.g. a func_ligand/"
            "active_site_uniprot correction), update _GOLDEN with a dated note "
            "explaining why -- never silently re-pin without recording the reason "
            "(TASK-0206's own established convention for this class of test)."
        )


# ---------------------------------------------------------------------------
# 4. The mutation test itself, as a permanent artifact.
# ---------------------------------------------------------------------------

class TestGlucokinaseMutationGuarded:
    """TASK-0231's own literal demonstration, automated: reintroducing
    TASK-0216's defect (func_ligand reverted to a non-code) must now fail
    loudly, not silently produce a green suite."""

    def test_real_config_does_not_fall_back(self):
        """Control: the real, current GLUCOKINASE config must NOT trigger
        the guard -- proves the guard doesn't false-positive on a
        legitimate real target before checking that it fires on a broken one."""
        target_config = load_target_config("GLUCOKINASE")
        try:
            apo, holo = _load_real_apo_holo("GLUCOKINASE", target_config)
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")
        labels_obj = build_labels(apo, holo, target_config, target_name="GLUCOKINASE")
        assert labels_obj.functional_provenance == "func_ligand-contact:GLC"

    def test_reverted_func_ligand_is_caught_not_silent(self):
        """The mutation: func_ligand=['NotARealCode'] (TASK-0216's own
        exact pre-fix defect shape -- a non-resolving marker instead of a
        real chem-comp code). Must raise, not silently fall back."""
        target_config = dict(load_target_config("GLUCOKINASE"))
        target_config["func_ligand"] = ["NotARealCode"]
        try:
            apo, holo = _load_real_apo_holo("GLUCOKINASE", target_config)
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")
        with pytest.raises(ValueError, match="top-degree fallback"):
            build_labels(apo, holo, target_config, target_name="GLUCOKINASE (mutated)")
