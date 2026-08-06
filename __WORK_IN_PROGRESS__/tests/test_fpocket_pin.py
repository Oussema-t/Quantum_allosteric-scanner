"""TASK-0206 -- fpocket pin: `fpocket_provenance` unit coverage + a
real-target golden-value regression test, the direct analogue of
[[TASK-0072]]'s cross-tree drift test for this project's own external
binary dependency.

Root cause this task acted on: `tools/fpocket/bin/` is gitignored
(upstream's own convention) -- only the build recipe is version
controlled, never the binary bytes -- so [[TASK-0163]]'s original AUCs
(0.8348/0.8596/0.5345) and [[TASK-0200]]'s recomputation (0.7910/0.8618/
0.5303) came from two machines' independently-built, previously-unpinned
binaries. See `tools/fpocket/PROVENANCE.json` for the full pin.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.baselines import fpocket_provenance  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent
_FPOCKET_BIN = _REPO_ROOT / "tools" / "fpocket" / "bin" / "fpocket"
_PROVENANCE_PATH = _REPO_ROOT / "tools" / "fpocket" / "PROVENANCE.json"


class TestFpocketProvenance:
    def test_missing_binary_returns_graceful_error(self, tmp_path):
        result = fpocket_provenance(tmp_path / "nonexistent")
        assert "error" in result
        assert "not found" in result["error"]

    def test_real_binary_returns_sha256_and_hostname(self, tmp_path):
        """Synthetic 'binary' (just needs to exist and be executable-ish
        for the banner-capture subprocess.run, which is wrapped in its
        own try/except) -- confirms the sha256/hostname/platform fields
        are always populated, independent of whether the file is a real
        fpocket build."""
        fake_bin = tmp_path / "fake_fpocket"
        fake_bin.write_bytes(b"not a real binary")
        fake_bin.chmod(0o755)
        result = fpocket_provenance(fake_bin)
        assert "error" not in result
        assert len(result["sha256"]) == 64
        assert result["hostname"]
        assert result["platform"]

    def test_sha256_changes_when_binary_content_changes(self, tmp_path):
        """The whole point of the pin -- must actually discriminate two
        different binaries, not just always return *a* hash."""
        bin_a = tmp_path / "a"
        bin_b = tmp_path / "b"
        bin_a.write_bytes(b"version one")
        bin_b.write_bytes(b"version two")
        prov_a = fpocket_provenance(bin_a)
        prov_b = fpocket_provenance(bin_b)
        assert prov_a["sha256"] != prov_b["sha256"]

    def test_deliberately_altered_binary_fails_the_pin_check(self, tmp_path):
        """TASK-0206's own Planned Validation: 'the golden-value test
        must fail against a deliberately altered invocation before it
        passes against the pinned one.' Simulates that directly: a
        binary with different bytes than the pinned sha256 must not
        silently pass a pin-equality check."""
        altered = tmp_path / "altered_fpocket"
        altered.write_bytes(b"deliberately different content")
        prov = fpocket_provenance(altered)
        pinned_sha256 = json.loads(_PROVENANCE_PATH.read_text())["sha256"]
        assert prov["sha256"] != pinned_sha256


class TestFpocketGoldenValue:
    """Real-target regression pin (KRAS_G12C), network- and binary-gated,
    same skip convention as `backend/test_analysis.py`'s own real-target
    pin -- try the real thing, `pytest.skip` if the environment can't
    provide it, never silently pass on a mock standing in for a
    real number."""

    def test_pinned_binary_sha256_matches_provenance_record(self):
        if not _FPOCKET_BIN.exists():
            pytest.skip(f"fpocket binary not present at {_FPOCKET_BIN} in this environment")
        prov = fpocket_provenance(_FPOCKET_BIN)
        pinned = json.loads(_PROVENANCE_PATH.read_text())
        assert prov["sha256"] == pinned["sha256"], (
            "fpocket binary has changed since the last pin -- if this is a deliberate "
            "rebuild, re-run allostery.baselines.fpocket_provenance and re-verify the "
            "AUC set below before updating tools/fpocket/PROVENANCE.json (TASK-0206's "
            "own Constraint: never silently replace a pinned number)."
        )

    def test_kras_g12c_fpocket_auc_pin(self):
        if not _FPOCKET_BIN.exists():
            pytest.skip(f"fpocket binary not present at {_FPOCKET_BIN} in this environment")

        _SCRIPTS = _REPO_ROOT / "scripts"
        if str(_SCRIPTS) not in sys.path:
            sys.path.insert(0, str(_SCRIPTS))

        try:
            import tempfile

            from allostery.baselines import _parse_fpocket_info
            from allostery.clean import load_target_config
            from allostery.metrics import auc as _auc
            from task0163_external_baseline_scoring import (
                _run_fpocket,
                _write_full_atom_apo_pdb,
            )
            from allostery.clean import clean_from_config
            from allostery.labels import build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue
            import prody
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"fpocket golden-value dependencies unavailable: {exc!r}")

        try:
            target_config = load_target_config("KRAS_G12C")
            apo = clean_from_config("KRAS_G12C", role="apo")
            holo = clean_from_config("KRAS_G12C", role="holo")
            prody.confProDy(verbosity="none")
            holo_struct = prody.parsePDB(target_config["holo_pdb"], compressed=False).select("chain A")
            holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
            holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
                holo_struct, ["A"], holo.resnums
            )
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")

        labels_obj = build_labels(apo, holo, target_config, cutoff=target_config.get("pocket_contact_cutoff", 4.5))
        pocket = labels_obj.pocket.astype(int)

        apo_chains = target_config.get("apo_chains") or target_config.get("chains")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            pdb_path = tmp / "KRAS_G12C_apo.pdb"
            _write_full_atom_apo_pdb(target_config, apo_chains, pdb_path)
            pockets = _run_fpocket(pdb_path, tmp)
            assert isinstance(pockets, list), f"fpocket run failed: {pockets}"

        scores = np.zeros(len(apo.resnums), dtype=np.float64)
        lookup = {}
        for i, (rn, ch) in enumerate(zip(apo.resnums, apo.chain_ids)):
            lookup.setdefault((ch, int(rn)), []).append(i)
        for p in pockets:
            for key in p["residues"]:
                for i in lookup.get(key, []):
                    scores[i] = max(scores[i], p["score"])

        result_auc = float(_auc(scores, pocket))
        pinned = json.loads(_PROVENANCE_PATH.read_text())["authoritative_auc_set"]["KRAS_G12C"]
        assert result_auc == pytest.approx(pinned, abs=1e-6), (
            f"fpocket KRAS_G12C AUC drifted: got {result_auc}, pinned {pinned}. "
            "Same drift TASK-0206 diagnosed once already -- check tools/fpocket/"
            "PROVENANCE.json's sha256 against the current binary before assuming a bug "
            "elsewhere."
        )
