"""TASK-0079.004 coverage -- run_challenge.py's control flow and
file-writing logic, against a synthetic/mocked target (no network, no
prody), per this task's own Planned Validation. The real network-backed
run against KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN is TASK-0079.005's job, not
this file's.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
for _p in (_SRC, _SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from allostery.labels import LigandGroup  # noqa: E402
from allostery.protocol import verify_frozen_stamp  # noqa: E402

import run_challenge  # noqa: E402


def _helix_coords(n: int) -> np.ndarray:
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


N = 12
_SEQ3 = ["ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE", "LEU", "LYS"]


class _Struct:
    def __init__(self, coords, resnums, resnames, chain_ids=None, ligand_groups=None, bfactors=None):
        self.coords = coords
        self.resnums = np.asarray(resnums)
        self.resnames = list(resnames)
        self.chain_ids = list(chain_ids) if chain_ids is not None else ["A"] * len(resnums)
        self.ligand_groups = ligand_groups or []
        self.bfactors = bfactors if bfactors is not None else np.full(len(resnums), 20.0)


def _synthetic_apo_holo():
    """Same helix/ligand-placement convention as
    test_protocol.py::_apo_holo_with_ligand -- LIG (drug) near residue 5,
    FUNC (functional/active-site) near residue 10 -- reused here rather
    than invented fresh, since that exact configuration is already known
    (from test_protocol.py's own passing suite) to give build_labels a
    real, non-empty pocket and active_site on this synthetic helix.
    apo/holo share one coordinate frame by construction (this is a
    synthetic control-flow test, not a real cross-PDB frame case -- that
    real-target concern is TASK-0079.005's, not this file's)."""
    coords = _helix_coords(N)
    apo = _Struct(coords, resnums=list(range(1, N + 1)), resnames=_SEQ3)
    drug_ligand = LigandGroup("LIG", 501, "A", np.array([coords[5]]), 1)
    func_ligand = LigandGroup("FUNC", 502, "A", np.array([coords[10]]), 1)
    holo = _Struct(
        coords.copy(), resnums=list(range(1, N + 1)), resnames=_SEQ3,
        ligand_groups=[drug_ligand, func_ligand],
    )
    return apo, holo


_TARGET_CONFIG = {
    "drug_ligand": "LIG", "func_ligand": ["FUNC"], "holo_pdb": "SYNTH_HOLO",
    "enm_cutoff": 10.0, "pocket_contact_cutoff": 4.5,
}


@pytest.fixture
def mocked_target(monkeypatch):
    apo, holo = _synthetic_apo_holo()
    monkeypatch.setattr(run_challenge, "load_target_config", lambda name: dict(_TARGET_CONFIG))
    monkeypatch.setattr(run_challenge, "_load_apo_holo", lambda name, cfg: (apo, holo))
    return apo, holo


class TestRunTarget:
    def test_writes_all_four_deliverables(self, mocked_target, tmp_path):
        result = run_challenge.run_target("SYNTH", tmp_path)
        assert result["ok"] is True

        target_dir = tmp_path / "SYNTH"
        assert (target_dir / "connectivity_matrix.npz").exists()
        assert (target_dir / "hit_list.json").exists()
        assert (target_dir / "report.txt").exists()
        assert (target_dir / "verdict.json").exists()

    def test_connectivity_matrix_is_square_symmetric_zero_diagonal(self, mocked_target, tmp_path):
        run_challenge.run_target("SYNTH", tmp_path)
        with np.load(tmp_path / "SYNTH" / "connectivity_matrix.npz") as npz:
            M = npz["matrix"]
        assert M.shape == (N, N)
        np.testing.assert_allclose(M, M.T)
        assert np.all(np.diag(M) == 0.0)

    def test_hit_list_has_up_to_five_real_resnums(self, mocked_target, tmp_path):
        run_challenge.run_target("SYNTH", tmp_path)
        with open(tmp_path / "SYNTH" / "hit_list.json") as f:
            hits = json.load(f)
        assert 0 < len(hits["indices"]) <= 5
        assert hits["resnums"] is not None
        assert len(hits["resnums"]) == len(hits["indices"])

    def test_report_renders_frozen_with_no_dev_banner(self, mocked_target, tmp_path):
        run_challenge.run_target("SYNTH", tmp_path)
        text = (tmp_path / "SYNTH" / "report.txt").read_text()
        assert "DEV/CEILING" not in text
        assert "HEADLINE VERDICT" in text

    def test_verdict_json_carries_a_verifiable_stamp_and_diagnosis(self, mocked_target, tmp_path):
        run_challenge.run_target("SYNTH", tmp_path)
        with open(tmp_path / "SYNTH" / "verdict.json") as f:
            verdict = json.load(f)
        assert verify_frozen_stamp(verdict) is True
        assert "_diagnosis" in verdict
        assert "_winner_index" in verdict

    def test_a_config_load_failure_writes_error_txt_and_does_not_raise(self, monkeypatch, tmp_path):
        def _boom(name):
            raise KeyError(f"Unknown target '{name}'.")

        monkeypatch.setattr(run_challenge, "load_target_config", _boom)

        result = run_challenge.run_target("NOT_A_REAL_TARGET", tmp_path)
        assert result["ok"] is False
        assert (tmp_path / "NOT_A_REAL_TARGET" / "error.txt").exists()

    def test_no_drug_ligand_resolved_is_a_handled_failure_not_a_crash(self, monkeypatch, tmp_path):
        apo, holo = _synthetic_apo_holo()
        holo.ligand_groups = []  # LIG never resolves -> build_labels.pocket is None
        monkeypatch.setattr(run_challenge, "load_target_config", lambda name: dict(_TARGET_CONFIG))
        monkeypatch.setattr(run_challenge, "_load_apo_holo", lambda name, cfg: (apo, holo))

        result = run_challenge.run_target("SYNTH", tmp_path)
        assert result["ok"] is False
        assert "pocket=None" in result["error"]
        assert (tmp_path / "SYNTH" / "error.txt").exists()


class TestMain:
    def test_dry_run_reports_valid_and_invalid_targets_without_network(self, capsys):
        rc = run_challenge.main(["--target", "KRAS_G12C", "NOT_A_REAL_TARGET", "--dry-run"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "KRAS_G12C: OK" in out
        assert "NOT_A_REAL_TARGET: CONFIG ERROR" in out

    def test_main_writes_output_and_returns_zero_on_success(self, mocked_target, tmp_path):
        rc = run_challenge.main(["--target", "SYNTH", "--output-dir", str(tmp_path)])
        assert rc == 0
        assert (tmp_path / "SYNTH" / "report.txt").exists()

    def test_main_returns_nonzero_if_any_target_fails(self, monkeypatch, tmp_path):
        def _boom(name):
            raise KeyError("nope")

        monkeypatch.setattr(run_challenge, "load_target_config", _boom)
        rc = run_challenge.main(["--target", "BAD", "--output-dir", str(tmp_path)])
        assert rc == 1
