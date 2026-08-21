#!/usr/bin/env python3
"""TASK-0177 -- build the consensus holo-pocket label for all 7
pocket-scoreable `status: verified` targets, run the negative control, and
re-score the headline observable (`H_new` + `time_averaged_ctqw_converged`,
[[TASK-0130]]/[[TASK-0159]]'s already-shipped convention) against the
incumbent/core/consensus labels side by side.

`frozen_context` per the task's own Constraint: `allostery.consensus_labels`
itself never reads a score. This script is the one place score and label
meet, and only after both are independently built.
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import numpy as np  # noqa: E402

from allostery.clean import load_target_config  # noqa: E402
from allostery.consensus_labels import build_consensus_label  # noqa: E402
from allostery.baselines import (  # noqa: E402
    degree_centrality,
    euclid_from_seed_centroid,
    hop_from_seed,
)
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.metrics import auc  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402

TARGETS = [
    "KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "PTP1B",
    "GLUCOKINASE", "CASPASE1", "CASPASE7",
]

# Real buffer/cryoprotectant HET groups confirmed present in the holo entry
# (grepped live against each target's actual ligand_groups, not guessed) --
# used as the negative control's deliberately-wrong "drug_ligand".
NEGATIVE_CONTROL_LIGANDS = {
    "KRAS_G12C": "MG",
    "CARDIAC_MYOSIN": "EDO",
}


def _mask_summary(mask):
    if mask is None:
        return {"available": False, "n": None}
    return {"available": True, "n": int(mask.sum())}


def _to_jsonable(obj):
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, float) and (obj != obj or obj in (float("inf"), float("-inf"))):
        return str(obj)
    return obj


def _score_observable(apo, active_site_idx: np.ndarray, cutoff: float) -> np.ndarray:
    """H_new + converged infinite-time occupation from the active-site
    seed, this project's shipped headline convention (TASK-0130/TASK-0159,
    same `cutoff=enm_cutoff` call shape as `run_challenge.py`)."""
    H = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    source = np.sort(active_site_idx)
    occ = time_averaged_ctqw_converged(H, source, coherent=False)
    return occ


def run_target(name: str) -> dict:
    t0 = time.monotonic()
    print(f"[task0177] {name}: building consensus label...", file=sys.stderr)
    cfg = load_target_config(name)
    cl = build_consensus_label(name, cfg)

    criteria_summary = {
        n: {"available": c.available, "n": (int(c.mask.sum()) if c.mask is not None else None), "detail": c.detail}
        for n, c in cl.criteria.items()
    }

    result = {
        "target": name,
        "criteria": criteria_summary,
        "core": _mask_summary(cl.core),
        "consensus": _mask_summary(cl.consensus),
        "shell": _mask_summary(cl.shell),
        "incumbent": _mask_summary(cl.incumbent),
        "resolution_shell_over_core": cl.resolution,
        "task_validity": cl.task_validity,
    }

    # --- Re-score headline observable against all three labels, side by side ---
    try:
        from allostery.clean import clean_from_config
        apo = clean_from_config(name, role="apo")
        active_idx = np.where(cl.active_site)[0]
        enm_cutoff = float(cfg.get("enm_cutoff", 8.0))
        occ = _score_observable(apo, active_idx, cutoff=enm_cutoff)

        floor_scores = {
            "degree_centrality": degree_centrality(apo.coords, cutoff=enm_cutoff),
            "euclid_from_seed_centroid": euclid_from_seed_centroid(apo.coords, active_idx),
            "hop_from_seed": hop_from_seed(apo.coords, active_idx, cutoff=enm_cutoff),
        }
        floor_auc = max(auc(s, cl.incumbent.astype(int)) for s in floor_scores.values()) if cl.incumbent is not None and cl.incumbent.any() else None

        rescore = {}
        for label_name, mask in (("incumbent", cl.incumbent), ("core", cl.core), ("consensus", cl.consensus)):
            if mask is None or not mask.any():
                rescore[label_name] = {"available": False}
                continue
            rescore[label_name] = {
                "available": True,
                "n_pocket": int(mask.sum()),
                "auc_H_new_ctqw_converged": auc(occ, mask.astype(int)),
            }
        result["rescore_headline_observable"] = rescore
        result["floor_auc_max_vs_incumbent"] = floor_auc
    except Exception as exc:  # noqa: BLE001 -- report, don't abort the whole run
        import traceback
        traceback.print_exc()
        result["rescore_headline_observable"] = {"error": f"{type(exc).__name__}: {exc}"}

    result["elapsed_s"] = round(time.monotonic() - t0, 1)
    print(f"[task0177] {name}: done in {result['elapsed_s']}s", file=sys.stderr)
    return result


def run_negative_control(name: str, decoy_ligand: str) -> dict:
    """Re-run the consensus machinery with `drug_ligand` swapped to a real
    buffer/cryoprotectant HET group present in the same holo entry. The
    criteria must FAIL to converge -- a consensus procedure that
    "converges" on glycerol/Mg/EDO is not measuring a pocket."""
    print(f"[task0177] negative control {name} vs decoy '{decoy_ligand}'...", file=sys.stderr)
    cfg = dict(load_target_config(name))
    cfg["drug_ligand"] = decoy_ligand
    # `name` (real target key) is required here, not a synthetic label --
    # `build_consensus_label` fetches apo/holo via `clean_from_config(name)`
    # internally, which looks the key up in targets.yaml regardless of what
    # `target_config` dict is passed; only `target_config["drug_ligand"]`
    # needs to be the decoy.
    cl = build_consensus_label(name, cfg)
    return {
        "target": name,
        "decoy_ligand": decoy_ligand,
        "criteria": {
            n: {"available": c.available, "n": (int(c.mask.sum()) if c.mask is not None else None), "detail": c.detail}
            for n, c in cl.criteria.items()
        },
        "core": _mask_summary(cl.core),
        "consensus": _mask_summary(cl.consensus),
        "resolution_shell_over_core": cl.resolution,
    }


def main() -> int:
    out = {"targets": {}, "negative_controls": {}}
    for name in TARGETS:
        try:
            out["targets"][name] = run_target(name)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            out["targets"][name] = {"target": name, "error": f"{type(exc).__name__}: {exc}"}

    for name, decoy in NEGATIVE_CONTROL_LIGANDS.items():
        try:
            out["negative_controls"][name] = run_negative_control(name, decoy)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            out["negative_controls"][name] = {"target": name, "error": f"{type(exc).__name__}: {exc}"}

    out_dir = Path(__file__).resolve().parent.parent / "results/tasks/0177_consensus_labels"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(_to_jsonable(out), indent=2, default=str))
    print(f"\nWrote {out_path}")

    print("\n=== TASK-0177 consensus label summary ===")
    for name, r in out["targets"].items():
        if "error" in r:
            print(f"{name:16s} ERROR: {r['error']}")
            continue
        print(
            f"{name:16s} incumbent={r['incumbent']['n']:>4}  "
            f"core={r['core']['n']:>4}  consensus={r['consensus']['n']:>4}  "
            f"shell={r['shell']['n']:>4}  resolution(shell/core)={r['resolution_shell_over_core']}"
        )

    print("\n=== negative controls (should NOT converge) ===")
    for name, r in out["negative_controls"].items():
        if "error" in r:
            print(f"{name:16s} ERROR: {r['error']}")
            continue
        print(
            f"{name:16s} decoy={r['decoy_ligand']:5s} "
            f"core={r['core']['n']}  consensus={r['consensus']['n']}  "
            f"resolution={r['resolution_shell_over_core']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
