"""TASK-0003 coverage -- config/targets.yaml structure and
clean.py::load_target_config() integration.

No prody/network dependency: load_target_config() only parses YAML and does
dict lookups, so these run everywhere pyyaml is installed.
"""
import sys
from pathlib import Path

import pytest
import yaml

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.clean import load_target_config  # noqa: E402

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "targets.yaml"

MANDATORY_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "MYC_MAX"]
# PTP1B/CASPASE7 promoted to `verified` by TASK-0081 (2026-07-15);
# CASPASE1/GLUCOKINASE promoted to `verified` by TASK-0127 (2026-07-18) --
# each independently RCSB-reconfirmed (real chain IDs, real hetero ligand
# records checked directly, not trusted from either source doc) and run
# for real through the end-to-end pipeline as this project's ASD
# generalization set -- no longer draft/unverified. GLUCOKINASE's apo/holo
# use different chain letters for the same biological chain (apo_chains/
# holo_chains, not the shared `chains` field -- see Q-0001/clean.py).
ASD_VERIFIED_TARGETS = ["PTP1B", "CASPASE7", "CASPASE1", "GLUCOKINASE"]
ASD_DRAFT_TARGETS = [
    "ATCase", "HEMOGLOBIN",
    "TAR_RECEPTOR", "GLYCOGEN_PHOSPHORYLASE", "PFK", "GROEL_SUBUNIT",
]
ALL_TARGETS = MANDATORY_TARGETS + ASD_VERIFIED_TARGETS + ASD_DRAFT_TARGETS

# The central rule from SYSTEMS_allosteric_corrected_v2.md: no field that
# would require a hand-transcribed residue number belongs in this file.
_FORBIDDEN_RESIDUE_FIELDS = {
    "pocket_full", "pocket_distal", "active_site", "covalent_anchor",
    "top5_full", "top5_distal", "top5_full_named", "top5_distal_named",
}


@pytest.fixture(scope="module")
def raw_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def test_schema_version_present(raw_config):
    assert raw_config["schema_version"] == 1


def test_all_expected_targets_present(raw_config):
    targets = raw_config["targets"]
    for name in ALL_TARGETS:
        assert name in targets, f"{name} missing from targets.yaml"


def test_ldh_omitted_not_silently_dropped(raw_config):
    assert "LDH" not in raw_config["targets"]
    omitted = raw_config.get("omitted_targets", {})
    assert "LDH" in omitted
    assert omitted["LDH"].get("reason")


@pytest.mark.parametrize("name", ALL_TARGETS)
def test_load_target_config_succeeds(name):
    cfg = load_target_config(name, config_path=CONFIG_PATH)
    assert "apo_pdb" in cfg


def test_load_target_config_unknown_target_raises():
    with pytest.raises(KeyError):
        load_target_config("NOT_A_REAL_TARGET", config_path=CONFIG_PATH)


@pytest.mark.parametrize("name", ALL_TARGETS)
def test_no_hand_transcribed_pocket_residues(name):
    cfg = load_target_config(name, config_path=CONFIG_PATH)
    present = _FORBIDDEN_RESIDUE_FIELDS & cfg.keys()
    assert not present, f"{name} carries forbidden residue field(s): {present}"


def test_mandatory_targets_are_not_quarantined():
    for name in MANDATORY_TARGETS:
        cfg = load_target_config(name, config_path=CONFIG_PATH)
        assert cfg.get("quarantine") is False


def test_draft_targets_are_not_verified():
    for name in ASD_DRAFT_TARGETS:
        cfg = load_target_config(name, config_path=CONFIG_PATH)
        assert cfg["status"] == "draft"
        assert cfg["verified"] is False


def test_asd_verified_targets_are_verified_with_resolvable_drug_ligand():
    for name in ASD_VERIFIED_TARGETS:
        cfg = load_target_config(name, config_path=CONFIG_PATH)
        assert cfg["status"] == "verified"
        assert cfg["verified"] is True
        # TASK-0127: `chains` is None for a target using the per-role
        # apo_chains/holo_chains override instead (GLUCOKINASE) -- either
        # form must resolve real chains, not just the shared field.
        has_shared_chains = cfg.get("chains") is not None
        has_per_role_chains = cfg.get("apo_chains") is not None and cfg.get("holo_chains") is not None
        assert has_shared_chains or has_per_role_chains, (
            f"{name}: neither `chains` nor both `apo_chains`/`holo_chains` resolved"
        )
        assert cfg["drug_ligand"] is not None
        assert isinstance(cfg["drug_ligand"], str)  # TASK-0081: PTP1B's
        # unquoted `892` silently parsed as a YAML int and never matched
        # any real ligand resname -- guard against the same class of bug
        # recurring for any future verified numeric-only ligand code.


# --- RCSB-reconfirmed facts (2026-07-06), pinned as regression checks ---

def test_kras_g12c_anchors():
    cfg = load_target_config("KRAS_G12C", config_path=CONFIG_PATH)
    assert cfg["apo_pdb"] == "4OBE"
    assert cfg["holo_pdb"] == "6OIM"
    assert cfg["drug_ligand"] == "MOV"


def test_bcr_abl1_ligand_code_resolved():
    cfg = load_target_config("BCR_ABL1", config_path=CONFIG_PATH)
    assert cfg["holo_pdb"] == "5MO4"
    assert cfg["drug_ligand"] == "AY7"  # resolves v2's ASCIMINIB placeholder
    assert "NIL" in cfg["func_ligand"]


def test_cardiac_myosin_uses_validation_structure_for_pocket_derivation():
    cfg = load_target_config("CARDIAC_MYOSIN", config_path=CONFIG_PATH)
    assert cfg["holo_pdb"] == "8QYR"            # real mavacamten contacts
    assert cfg["holo_challenge_pdb"] == "6C1H"  # confirmed unusable
    assert cfg["drug_ligand"] == "XB2"
    assert cfg["quarantine"] is False
    # TASK-0124 (2026-07-20): apo replaced 5TBY (20 A IHM homology model) ->
    # 8QYP (2.76 A X-ray, same paper/species as the 8QYR holo) -- the
    # confidence-suppressing concern this test used to pin is resolved, not
    # just re-scored, so confidence is promoted to parity with the other 3
    # mandatory targets rather than held below 0.9.
    assert cfg["apo_pdb"] == "8QYP"
    assert cfg["confidence"] >= 0.9


def test_myc_max_pocket_not_applicable():
    cfg = load_target_config("MYC_MAX", config_path=CONFIG_PATH)
    assert cfg["holo_pdb"] is None
    assert cfg.get("allosteric_pocket_exists") is False
    assert cfg["chains"] == ["A", "B"]
    assert cfg["keep_nucleic"] is True
