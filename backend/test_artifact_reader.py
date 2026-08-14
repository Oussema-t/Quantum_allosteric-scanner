"""Tests for `backend/artifact_reader.py` (TASK-0083's own reference
reader stub) -- no fixture generation here, it consumes artifacts written
by `allostery.artifact.write_result_artifact` (via a plain dict, not an
import: the whole point being tested is that this module doesn't need
that import to consume what `allostery` produces).
"""
import ast
import hashlib
import json
from pathlib import Path

import pytest

from backend.artifact_reader import read_result_artifact, verify_content_hash


def _write_fixture_artifact(tmp_path: Path, target: str = "TESTTARGET") -> Path:
    """Hand-assembles a minimal but schema-valid artifact + matrix,
    replicating `allostery.artifact.write_result_artifact`'s own hashing
    recipe by hand (not by importing it -- this test file lives under
    `backend/`, which must not import `allostery` either)."""
    import numpy as np

    target_dir = tmp_path / target
    target_dir.mkdir(parents=True)

    M = np.array([[0.0, 1.0], [1.0, 0.0]])
    npz_path = target_dir / "connectivity_v1.npz"
    np.savez_compressed(npz_path, M=M)
    npz_sha = "sha256:" + hashlib.sha256(npz_path.read_bytes()).hexdigest()

    body = {
        "schema_version": "1.0",
        "target": target,
        "generated_at": "2026-08-14T00:00:00Z",
        "provenance": {
            "pipeline_mode": "dev", "frozen_verified": False,
            "git_commit": None, "config_hash": "sha256:deadbeef",
        },
        "verdict": {"AUC_apo_Hnew_default": 0.5},
        "competence": {"floor": 0.4, "ceiling": 0.6, "actual": 0.5, "headroom": 0.5,
                        "headroom_reason": None},
        "connectivity_matrix_ref": {
            "file": "connectivity_v1.npz", "array_key": "M",
            "shape": [2, 2], "sha256": npz_sha,
        },
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    body["provenance"]["content_hash"] = "sha256:" + hashlib.sha256(canonical).hexdigest()

    (target_dir / "artifact_v1.json").write_text(json.dumps(body, indent=2, sort_keys=True))
    return tmp_path


class TestNoAllosteryImport:
    def test_artifact_reader_imports_nothing_from_allostery(self):
        """Mechanized, not eyeballed: parse this module's own AST and
        assert no `import allostery` / `from allostery...` statement
        exists anywhere in it -- a comment alone can go stale silently;
        this cannot, since it reads the actual file on every run."""
        source = Path(__file__).resolve().parent / "artifact_reader.py"
        tree = ast.parse(source.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("allostery"), (
                        f"artifact_reader.py imports {alias.name!r}"
                    )
            elif isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("allostery"), (
                    f"artifact_reader.py imports from {node.module!r}"
                )


class TestReadResultArtifact:
    def test_round_trip(self, tmp_path):
        results_dir = _write_fixture_artifact(tmp_path)
        art = read_result_artifact(results_dir, "TESTTARGET")
        assert art["target"] == "TESTTARGET"
        assert art["verdict"]["AUC_apo_Hnew_default"] == 0.5
        assert art["connectivity_matrix"] == [[0.0, 1.0], [1.0, 0.0]]

    def test_missing_target_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_result_artifact(tmp_path, "NOPE")

    def test_tampered_json_field_detected(self, tmp_path):
        results_dir = _write_fixture_artifact(tmp_path)
        p = results_dir / "TESTTARGET" / "artifact_v1.json"
        d = json.loads(p.read_text())
        d["competence"]["actual"] = 0.999
        p.write_text(json.dumps(d))
        with pytest.raises(ValueError, match="content_hash mismatch"):
            read_result_artifact(results_dir, "TESTTARGET")

    def test_tampered_matrix_file_detected(self, tmp_path):
        import numpy as np

        results_dir = _write_fixture_artifact(tmp_path)
        npz_path = results_dir / "TESTTARGET" / "connectivity_v1.npz"
        np.savez_compressed(npz_path, M=np.array([[0.0, 9.0], [9.0, 0.0]]))
        with pytest.raises(ValueError, match="hash mismatch"):
            read_result_artifact(results_dir, "TESTTARGET")

    def test_unsupported_schema_version_rejected(self, tmp_path):
        results_dir = _write_fixture_artifact(tmp_path)
        p = results_dir / "TESTTARGET" / "artifact_v1.json"
        d = json.loads(p.read_text())
        d["schema_version"] = "2.0"
        # content_hash now stale for this mutation too, but schema_version
        # is checked first -- confirms the version gate fires before hash
        # verification, not after.
        p.write_text(json.dumps(d))
        with pytest.raises(ValueError, match="schema_version"):
            read_result_artifact(results_dir, "TESTTARGET")

    def test_verify_content_hash_directly(self, tmp_path):
        results_dir = _write_fixture_artifact(tmp_path)
        art = json.loads((results_dir / "TESTTARGET" / "artifact_v1.json").read_text())
        assert verify_content_hash(art) is True
        art["target"] = "MODIFIED"
        assert verify_content_hash(art) is False
