"""TASK-0083 -- reference reader stub for the result artifact contract
(`__WORK_IN_PROGRESS__/RESULT_ARTIFACT_CONTRACT.md`). Proves `backend/`
can parse what `allostery/`'s pipeline writes without importing
`allostery` -- the seam TASK-0018 established, extended by this task to
cover data, not just code.

This is a stub, not the results API: TASK-0084 owns the actual
`/api/results/{target}` etc. endpoints and whatever caching/error-handling
a real API needs. This module exists to validate the contract is
parseable from `backend/`'s side at all, per TASK-0083's own Planned
Validation ("a stub reader confirming backend/ could parse it without
importing allostery").

No import from `allostery` anywhere in this file -- checked by
`backend/test_analysis.py`'s own convention of asserting this file's
compiled bytecode names, not just by inspection (a comment alone can go
stale; a test cannot silently drift the same way).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _canonical_json_bytes(obj) -> bytes:
    """Byte-for-byte the same recipe `allostery.artifact._canonical_json_bytes`
    uses -- duplicated, not imported (that import is exactly what this
    module must not have), so `content_hash` can be independently
    re-derived here rather than trusted from the writer's own side."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def verify_content_hash(artifact: dict) -> bool:
    """Independent re-implementation of the writer's own integrity check
    -- if this ever silently drifts from `allostery.artifact.
    verify_content_hash`'s recipe, `tests/test_artifact.py`'s cross-check
    (writes an artifact, verifies it via *both* implementations) catches
    it, not a passive assumption that the two stay in sync."""
    stored = artifact.get("provenance", {}).get("content_hash")
    if stored is None:
        return False
    stripped = json.loads(json.dumps(artifact))
    stripped["provenance"] = dict(stripped["provenance"])
    del stripped["provenance"]["content_hash"]
    return _sha256_hex(_canonical_json_bytes(stripped)) == stored


def read_result_artifact(results_dir: Path | str, target_name: str) -> dict:
    """Read `artifact_v1.json` + `connectivity_v1.npz` for `target_name`
    under `results_dir`, verify `content_hash`, and return a plain dict
    with the connectivity matrix loaded inline (as a nested list, not a
    numpy array -- numpy is a real dependency here for `.npz` loading,
    but the *returned* shape stays framework-agnostic JSON-safe types,
    since a results API's eventual JSON response is exactly what this
    return value is standing in for).

    Raises `FileNotFoundError` if the artifact doesn't exist,
    `ValueError` if `content_hash` doesn't verify (RESULT_ARTIFACT_
    CONTRACT.md's own "hand-edited artifact is detectable" scenario) or
    the schema_version isn't the one this reader understands.
    """
    target_dir = Path(results_dir) / target_name
    json_path = target_dir / "artifact_v1.json"
    if not json_path.exists():
        raise FileNotFoundError(f"no artifact for target {target_name!r} at {json_path}")

    artifact = json.loads(json_path.read_text())

    if artifact.get("schema_version") != "1.0":
        raise ValueError(
            f"unsupported schema_version {artifact.get('schema_version')!r} "
            "-- this reader understands 1.0 only"
        )

    if not verify_content_hash(artifact):
        raise ValueError(
            f"content_hash mismatch for {target_name!r} -- artifact_v1.json "
            "has been modified since it was written, or is corrupt"
        )

    matrix_ref = artifact.get("connectivity_matrix_ref")
    if matrix_ref is not None:
        npz_path = target_dir / matrix_ref["file"]
        npz_bytes = npz_path.read_bytes()
        actual_hash = _sha256_hex(npz_bytes)
        if actual_hash != matrix_ref["sha256"]:
            raise ValueError(
                f"connectivity matrix file hash mismatch for {target_name!r} -- "
                f"{npz_path} has been modified since the artifact was written"
            )
        import numpy as np  # local: only this branch needs numpy at all

        with np.load(npz_path) as npz:
            artifact["connectivity_matrix"] = npz[matrix_ref["array_key"]].tolist()

    return artifact
