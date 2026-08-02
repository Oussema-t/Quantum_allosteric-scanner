#!/usr/bin/env python3
"""TASK-0182 Steps 4-5 -- couple `hardware_resource_accounting.py`'s
resource numbers to a signal-retention metric, and turn both into an
explicit per-target/per-resolution feasibility verdict.

Classical-only (no qiskit simulation) -- fast, run as a separate pass over
`results_task0182_hardware_resource_accounting/results.json`.

Step 4 -- retention metric: TASK-0172 (the register's own planned
retention metric) has not landed, so this uses the documented naive
fallback from TASK-0182's own Dependency section ("report naive Louvain
retention if 0172 has not landed, and say which was used"). Naive
definition: coarse-grain, broadcast the coarse graph's exact converged
occupation back onto every original residue in its cluster, and compare
that projection to the full-resolution exact converged occupation via
`noise.top_k_overlap` (top-10 Jaccard) and Spearman rank correlation. A
resource number with no retention number next to it is meaningless (this
task's own Intent Contract) -- this is the number that goes next to it.

Step 5 -- feasibility verdict: `EXECUTABLE_NOW` / `EXECUTABLE_COARSE` /
`FAULT_TOLERANT_ONLY` per target, from a simple, disclosed circuit-fidelity
estimate `(1 - median_2q_gate_error) ** two_qubit_gate_count` using
`hardware_resource_accounting.py`'s own real IBM-FakeSherbrooke-transpiled
gate counts and that backend's real, cited 2-qubit (ECR) gate error
calibration. Threshold (0.5, a conventional informal "does more than half
the circuit's coherence survive" NISQ-usability bar) is a disclosed
judgment call, not derived -- flagged as such, not hidden in the code.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from allostery.clean import load_target_config  # noqa: E402
from allostery.coarse import coarse_grain  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.noise import top_k_overlap  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402

from hardware_resource_accounting import (  # noqa: E402
    COARSE_SIZE_SIMULATABLE,
    COARSE_SIZE_TRANSPILE_ONLY,
    TARGETS,
    _load_apo_and_active_site,
    _representative_cluster,
)

FIDELITY_THRESHOLD = 0.5  # disclosed judgment call, see module docstring
RESULTS_PATH = Path(__file__).resolve().parent.parent / "results_task0182_hardware_resource_accounting" / "results.json"


def _real_ibm_median_2q_error() -> float:
    from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

    b = FakeSherbrooke()
    props = b.target["ecr"]
    errs = [p.error for p in props.values() if p is not None and p.error is not None]
    return float(np.median(errs))


def retention_metric(H_full: np.ndarray, active_idx_full: np.ndarray, n_target: int) -> dict:
    cg = coarse_grain(H_full, method="louvain", n_target=n_target, seed=0)
    source_cluster = _representative_cluster(cg.labels, active_idx_full)

    exact_full = time_averaged_ctqw_converged(H_full, source=active_idx_full)
    exact_coarse = time_averaged_ctqw_converged(cg.H_coarse, source=source_cluster)
    projected = exact_coarse[cg.labels]  # broadcast each residue's cluster occupation back onto it

    from scipy.stats import spearmanr

    rho, _ = spearmanr(exact_full, projected)
    return {
        "n_target": n_target,
        "n_clusters_actual": cg.n_clusters,
        "top10_jaccard_retention": top_k_overlap(exact_full, projected, k=10),
        "spearman_retention": float(rho),
    }


def feasibility_verdict(resource_row: dict, median_2q_error: float) -> dict:
    def fidelity(n_2q_gates: int) -> float:
        return float((1.0 - median_2q_error) ** n_2q_gates)

    full = resource_row["full_resolution"]
    full_fidelity = fidelity(full["two_qubit_gates"])
    full_ok = full_fidelity >= FIDELITY_THRESHOLD

    coarse_results = []
    any_coarse_ok = False
    for c in resource_row["coarse_grained"]:
        n_2q = c["transpiled_ibm_sherbrooke"]["two_qubit_gate_count"]
        fid = fidelity(n_2q)
        ok = fid >= FIDELITY_THRESHOLD
        any_coarse_ok = any_coarse_ok or ok
        coarse_results.append({
            "n_target": c["n_target"],
            "n_qubits_actual": c["n_clusters_actual"],
            "transpiled_two_qubit_gates_ibm": n_2q,
            "estimated_circuit_fidelity": fid,
            "clears_threshold": ok,
        })

    if full_ok:
        verdict = "EXECUTABLE_NOW"
    elif any_coarse_ok:
        verdict = "EXECUTABLE_COARSE"
    else:
        verdict = "FAULT_TOLERANT_ONLY"

    return {
        "full_resolution": {
            "n_qubits": full["n_qubits"],
            "two_qubit_gates_analytic": full["two_qubit_gates"],
            "estimated_circuit_fidelity": full_fidelity,
            "clears_threshold": full_ok,
        },
        "coarse_grained": coarse_results,
        "verdict": verdict,
    }


def main() -> int:
    if not RESULTS_PATH.exists():
        print(f"error: {RESULTS_PATH} not found -- run hardware_resource_accounting.py first", file=sys.stderr)
        return 1
    results = json.loads(RESULTS_PATH.read_text())

    median_2q_error = _real_ibm_median_2q_error()
    print(f"IBM FakeSherbrooke median ECR (2-qubit) gate error: {median_2q_error:.5f}", file=sys.stderr)

    out = {"median_2q_error_ibm_sherbrooke": median_2q_error, "fidelity_threshold": FIDELITY_THRESHOLD, "targets": {}}

    for name in TARGETS:
        print(f"{name}: retention + verdict...", file=sys.stderr)
        target_config = load_target_config(name)
        apo, active_idx, provenance = _load_apo_and_active_site(name, target_config)
        cutoff = float(target_config.get("enm_cutoff", 10.0))
        H_full = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)

        retention = [
            retention_metric(H_full, active_idx, n_target)
            for n_target in (COARSE_SIZE_SIMULATABLE, COARSE_SIZE_TRANSPILE_ONLY)
        ]

        resource_row = next(r for r in results["step3_resource_table"] if r["target"] == name)
        verdict = feasibility_verdict(resource_row, median_2q_error)

        out["targets"][name] = {
            "active_site_provenance": provenance,
            "retention": retention,
            "feasibility": verdict,
        }
        print(f"  {name}: verdict={verdict['verdict']}", file=sys.stderr)

    out_path = RESULTS_PATH.parent / "feasibility_verdict.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {out_path}")

    print("\n=== feasibility summary ===")
    for name, t in out["targets"].items():
        print(f"{name}: {t['feasibility']['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
