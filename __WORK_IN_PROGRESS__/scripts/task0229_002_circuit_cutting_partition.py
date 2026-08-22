#!/usr/bin/env python3
"""TASK-0229.002 -- real (not guessed) island-partition cut count for the
[10] circuit-cutting resource estimate (Mitarai & Fujii 2021, Quantum
5:388 -- verified directly, see the task file's own Done section).

Classical-only: partitions each mandatory target's real H_new coupling
graph into NISQ-sized islands via `coarse.coarse_grain`'s existing
Louvain machinery (already used, unmodified, for TASK-0182's own
resource accounting -- not re-derived), then counts how many coupling
edges cross island boundaries using the exact same nonzero-upper-
triangular convention `coarse.trotter_cost` already uses for its own
`n_terms`. This count is the number of two-qubit gates that would need
to be *cut* (simulated via quasiprobability, rather than executed
directly) to run the full circuit as a set of NISQ-sized sub-circuits --
the input `n` to ref [10]'s O(9^n)/O(4^n) sampling-overhead formula.

No circuit execution, no quantum simulation -- this task is explicitly
paper-level (Out of Scope: running either route).
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
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from allostery.clean import load_target_config  # noqa: E402
from allostery.coarse import _graph_weights, coarse_grain  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402

from hop_distance_generalization_audit import _load_apo_holo  # noqa: E402

MANDATORY_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
MYC_MAX = "MYC_MAX"  # TASK-0182's own 4th target (no ground truth, still scored for resources)
ISLAND_SIZE = 14  # midpoint of TASK-0182's own ~12-16 node NISQ budget framing


def _cut_edge_count(W: np.ndarray, labels: np.ndarray) -> int:
    """Number of nonzero coupling edges (i, j), i<j, with labels[i] !=
    labels[j] -- the same `np.triu(W, k=1)` nonzero convention
    `coarse.trotter_cost` uses for its own `n_terms`, restricted to
    cross-cluster pairs."""
    ii, jj = np.nonzero(np.triu(W, k=1))
    cross = labels[ii] != labels[jj]
    return int(cross.sum())


def partition_one(name: str) -> dict:
    target_config = load_target_config(name)
    if name == MYC_MAX:
        from allostery.clean import clean_from_config
        apo = clean_from_config(name, role="apo")
    else:
        apo, _holo = _load_apo_holo(name, target_config)
    cutoff = float(target_config.get("enm_cutoff", 10.0))
    H0 = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    n = len(apo.resnums)

    n_islands = max(1, round(n / ISLAND_SIZE))
    result = coarse_grain(H0, method="louvain", n_target=n_islands)
    labels = result.labels
    n_clusters_actual = result.n_clusters

    W = _graph_weights(H0)
    n_cut = _cut_edge_count(W, labels)

    sizes = np.bincount(labels)
    island_qubits = int(sizes.max())

    return {
        "target": name,
        "n_residues": int(n),
        "n_islands_requested": n_islands,
        "n_islands_actual": n_clusters_actual,
        "island_sizes": sizes.tolist(),
        "max_island_qubits": island_qubits,
        "n_cut_edges": n_cut,
    }


def main() -> int:
    out = []
    for name in MANDATORY_TARGETS + [MYC_MAX]:
        print(f"{name}: partitioning...", file=sys.stderr)
        r = partition_one(name)
        print(f"{name}: {r}", file=sys.stderr)
        out.append(r)

    out_dir = Path(__file__).resolve().parent.parent / "results/tasks/0229_002_circuit_cutting_partition"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {out_path}")

    print("\n=== summary ===")
    for r in out:
        n = r["n_cut_edges"]
        log10_9n = n * np.log10(9.0)
        log10_4n = n * np.log10(4.0)
        print(
            f"{r['target']:16s} N={r['n_residues']:4d}  islands={r['n_islands_actual']:3d}  "
            f"max_island_qubits={r['max_island_qubits']:3d}  n_cut_edges={n:5d}  "
            f"log10(overhead, 9^n)={log10_9n:.1f}  log10(overhead, 4^n)={log10_4n:.1f}"
        )
        r["log10_overhead_9n"] = float(log10_9n)
        r["log10_overhead_4n"] = float(log10_4n)

    out_path.write_text(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
