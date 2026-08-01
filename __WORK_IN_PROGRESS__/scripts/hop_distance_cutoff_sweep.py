#!/usr/bin/env python3
"""TASK-0188 -- spatial contact-graph hop-cutoff robustness sweep.

Question: TASK-0186's hop-distance findings (min/median/frac<=1/frac<=2 per
target) and TASK-0177's C6 distality criterion both reuse the 8.0 A
contact-graph cutoff -- but that value was only ever benchmarked (TASK-0067)
for a *different* metric (GNM-eigendecomposition AUC) over a narrower range
(7.5/8.0/10.0 A). This script re-runs TASK-0186's spatial hop-distance
measurement across a wider cutoff grid to check whether its headline claims
are cutoff-robust or a knob-choice artifact.

Read-only diagnostic, no source-code changes. Reuses
`hop_distance_generalization_audit.py`'s target-loading path
(`_load_apo_holo`, `TARGETS`) verbatim -- do not re-derive it.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from allostery.baselines import hop_from_seed  # noqa: E402
from allostery.hamiltonians import contact_matrix  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402

from hop_distance_generalization_audit import TARGETS, DEFAULT_POCKET_CUTOFF, _load_apo_holo  # noqa: E402

# Brackets TASK-0067's tested 7.5/8.0/10.0 A, extended below 7.5 A (the
# concerning direction -- a sparser graph inflates hop-counts, which would
# *understate* triviality, not overstate it) and lightly above 8.0 A.
CUTOFF_GRID = [6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0]


def _n_components(coords: np.ndarray, cutoff: float) -> int:
    """Count connected components of the binary contact graph at `cutoff`."""
    import networkx as nx

    A = contact_matrix(coords, cutoff=cutoff, weight="binary")
    G = nx.from_numpy_array(A)
    return nx.number_connected_components(G)


def _summ(values: np.ndarray, reachable: np.ndarray, thresholds=(1, 2, 3)) -> dict:
    v = values[reachable]
    if not reachable.any():
        out = {"min": None, "mean": None, "median": None, "max": None}
        out.update({f"frac_le_{t}": None for t in thresholds})
        return out
    out = {
        "min": float(np.min(v)),
        "mean": float(np.mean(v)),
        "median": float(np.median(v)),
        "max": float(np.max(v)),
    }
    out.update({f"frac_le_{t}": float(np.mean(v <= t)) for t in thresholds})
    return out


def sweep_one(name: str) -> dict:
    t0 = time.monotonic()
    target_config = load_target_config(name)
    apo, holo = _load_apo_holo(name, target_config)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)

    if labels_obj.pocket is None or not labels_obj.pocket.any():
        return {"target": name, "ok": False, "reason": "no resolvable pocket label"}
    if not labels_obj.active_site.any():
        return {"target": name, "ok": False, "reason": "no resolvable active site"}

    active_idx = np.where(labels_obj.active_site)[0]
    pocket_idx = np.where(labels_obj.pocket)[0]
    n = len(apo.resnums)
    unreachable_penalty = float(n + 1)

    rows = []
    for cutoff in CUTOFF_GRID:
        n_components = _n_components(apo.coords, cutoff)
        connected = n_components == 1

        neg_hops = hop_from_seed(apo.coords, source=active_idx, cutoff=cutoff)
        spatial_hops = (-neg_hops)[pocket_idx]
        reachable = spatial_hops < unreachable_penalty

        rows.append(
            {
                "cutoff_A": cutoff,
                "n_connected_components": n_components,
                "single_component": connected,
                "n_pocket_unreachable": int((~reachable).sum()),
                "spatial_hop": _summ(spatial_hops, reachable),
            }
        )

    return {
        "target": name,
        "ok": True,
        "label": "incumbent",
        "pocket_contact_cutoff_A": pocket_cutoff,
        "n_residues": int(n),
        "n_active_site": int(len(active_idx)),
        "n_pocket": int(len(pocket_idx)),
        "grid": rows,
        "elapsed_s": round(time.monotonic() - t0, 1),
    }


def main() -> int:
    out = []
    for name in TARGETS:
        print(f"{name}: running...", file=sys.stderr)
        try:
            r = sweep_one(name)
        except Exception as exc:  # noqa: BLE001 -- diagnostic script, report and continue
            r = {"target": name, "ok": False, "reason": f"{type(exc).__name__}: {exc}"}
        print(f"{name}: ok={r.get('ok')}", file=sys.stderr)
        out.append(r)

    out_dir = Path(__file__).resolve().parent.parent / "results_task0188_hop_cutoff_sweep"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {out_path}")

    print("\n=== summary (incumbent 4.5A pocket label; spatial hop-graph cutoff swept) ===")
    for r in out:
        if not r.get("ok"):
            print(f"{r['target']:16s} FAILED: {r.get('reason')}")
            continue
        print(f"{r['target']}: n_pocket={r['n_pocket']}")
        for row in r["grid"]:
            sh = row["spatial_hop"]
            conn = "OK" if row["single_component"] else f"FRAGMENTED({row['n_connected_components']} comps)"
            print(
                f"  {row['cutoff_A']:>4.1f}A  conn={conn:16s}  "
                f"min/med={sh['min']}/{sh['median']}  <=1:{sh['frac_le_1']}  <=2:{sh['frac_le_2']}  "
                f"unreachable={row['n_pocket_unreachable']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
