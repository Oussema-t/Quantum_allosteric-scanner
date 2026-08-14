"""TASK-0083 -- the versioned result artifact `allostery` emits and
`backend` consumes. See `RESULT_ARTIFACT_CONTRACT.md` for the full schema
and the reasoning behind every field and both hashes; this module is the
reference writer only, per that task's own Out Of Scope ("a reference
writer/reader stub, not the full API").

Every value this module writes is caller-supplied, already computed by an
existing, already-tested function elsewhere in this package
(`analysis.assemble_verdict_results`, `report.assemble_hit_list`,
`pathways.edge_propensity_to_matrix`, `superpose.cumulative_overlap_gate`,
`diagnostics.classify_failure`) -- this module performs no science, only
assembly, hashing, and serialization.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .clean import load_target_config

SCHEMA_VERSION = "1.0"


def _git_commit() -> str | None:
    """Best-effort current commit hash -- `None`, not a raised exception,
    if this isn't a git checkout or `git` isn't on PATH (e.g. a stripped
    deployment image)."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            timeout=5, cwd=Path(__file__).resolve().parent,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:  # noqa: BLE001 -- best-effort, never blocks a write
        pass
    return None


def _canonical_json_bytes(obj) -> bytes:
    """Sorted-keys, no-whitespace JSON -- the same input always hashes to
    the same digest regardless of dict insertion order."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def compute_config_hash(target_name: str) -> str:
    """SHA256 over `{resolved target config, current git commit}` --
    answers "which pipeline/config state produced this artifact," not
    "has the artifact file itself been altered" (`content_hash`'s job).
    A consumer with a live checkout can recompute this for the *current*
    state of `targets.yaml` and compare against a stored artifact's own
    `config_hash` to detect drift (RESULT_ARTIFACT_CONTRACT.md's own
    "stale... run" scenario)."""
    config = load_target_config(target_name)
    payload = {"target": target_name, "config": config, "git_commit": _git_commit()}
    return _sha256_hex(_canonical_json_bytes(payload))


def write_result_artifact(
    target_name: str,
    *,
    out_dir: Path,
    verdict: dict | None = None,
    diagnosis: dict | None = None,
    hit_list: dict | None = None,
    connectivity_matrix: np.ndarray | None = None,
    stability_gate: dict | None = None,
    competence: dict | None = None,
    metadata: dict | None = None,
    no_ground_truth: dict | None = None,
    pipeline_mode: str = "dev",
    frozen_verified: bool = False,
) -> dict:
    """Assemble and write `artifact_v1.json` + `connectivity_v1.npz` for
    one target into `out_dir / target_name /`. Every keyword argument is
    independently optional and simply omitted from the written JSON when
    `None` (`verdict_template`'s own "missing key renders N/A" philosophy,
    extended to this artifact) -- a caller with only a subset of upstream
    analyses available still gets a valid, if partial, artifact.

    `competence`, if given, must already carry a computed `headroom` (a
    float) or `headroom` omitted with a `headroom_reason` string set for
    the degenerate `ceiling <= floor` case -- this function does not
    compute the floor/ceiling/actual/headroom arithmetic itself (Out Of
    Scope: that is COMPETENCE_MAP.md's/TASK-0082's own computation, this
    module only serializes it).

    Returns the written JSON dict (before the file is re-read), so a
    caller can inspect what was actually written without a round-trip.
    """
    target_dir = Path(out_dir) / target_name
    target_dir.mkdir(parents=True, exist_ok=True)

    body: dict = {
        "schema_version": SCHEMA_VERSION,
        "target": target_name,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provenance": {
            "pipeline_mode": pipeline_mode,
            "frozen_verified": bool(frozen_verified),
            "git_commit": _git_commit(),
            "config_hash": compute_config_hash(target_name),
        },
    }
    if verdict is not None:
        body["verdict"] = verdict
    if diagnosis is not None:
        body["diagnosis"] = diagnosis
    if hit_list is not None:
        body["hit_list"] = {
            "indices": [int(x) for x in hit_list["indices"]],
            "resnums": ([int(x) for x in hit_list["resnums"]]
                        if hit_list.get("resnums") is not None else None),
            "scores": [float(x) for x in hit_list["scores"]],
        }
    if stability_gate is not None:
        body["stability_gate"] = stability_gate
    if competence is not None:
        body["competence"] = competence
    if metadata is not None:
        body["metadata"] = metadata
    if no_ground_truth is not None:
        body["no_ground_truth"] = no_ground_truth

    if connectivity_matrix is not None:
        M = np.asarray(connectivity_matrix, dtype=float)
        if M.ndim != 2 or M.shape[0] != M.shape[1]:
            raise ValueError(f"connectivity_matrix must be square (n, n), got {M.shape}")
        npz_path = target_dir / "connectivity_v1.npz"
        np.savez_compressed(npz_path, M=M)
        body.setdefault("metadata", {})["n_residues"] = int(M.shape[0])
        body["connectivity_matrix_ref"] = {
            "file": "connectivity_v1.npz",
            "array_key": "M",
            "shape": list(M.shape),
            "sha256": _sha256_hex(npz_path.read_bytes()),
        }

    # content_hash covers everything above -- computed last, over the
    # fully-assembled body, so it changes if any prior field changes.
    body["provenance"]["content_hash"] = _sha256_hex(_canonical_json_bytes(body))

    json_path = target_dir / "artifact_v1.json"
    json_path.write_text(json.dumps(body, indent=2, sort_keys=True))
    return body


def verify_content_hash(artifact: dict) -> bool:
    """Recompute `content_hash` over `artifact` with `provenance.
    content_hash` itself excluded, and compare -- `True` iff they match.
    Reused by both this module's own round-trip test and (per
    RESULT_ARTIFACT_CONTRACT.md) `backend/artifact_reader.py`'s own
    verification -- that module does not reimplement this hashing logic,
    it re-derives the same digest independently by following this exact
    recipe, since it cannot import this function (no allostery import
    allowed in backend/)."""
    stored = artifact.get("provenance", {}).get("content_hash")
    if stored is None:
        return False
    stripped = json.loads(json.dumps(artifact))  # deep copy
    stripped["provenance"] = dict(stripped["provenance"])
    del stripped["provenance"]["content_hash"]
    recomputed = _sha256_hex(_canonical_json_bytes(stripped))
    return recomputed == stored
