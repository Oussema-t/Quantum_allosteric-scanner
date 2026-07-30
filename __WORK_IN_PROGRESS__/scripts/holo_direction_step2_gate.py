#!/usr/bin/env python3
"""TASK-0015 -- HOLO_DIRECTION_MODULE.md's own "First action": run Step 2's
go/no-go gate on all training targets *before* building Steps 3-5 or any
circuit work.

Loads apo/holo + pocket/active-site labels the same way run_challenge.py
does, builds Step 1's admissible deformation family per target, and runs
Step 2's gate (holo_direction.go_no_go_gate). Records every target's
verdict -- this script's own output is what decides whether Steps 3-5 are
built at all, and for which targets.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.holo_direction import PERTURBATION_PROTOCOL, build_deformation_family, go_no_go_gate  # noqa: E402
from allostery.labels import build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402
from allostery.superpose import chain_map_from_config  # noqa: E402

DEFAULT_POCKET_CUTOFF = 4.5

# All `status: verified` targets with a real holo_pdb (MYC_MAX excluded --
# holo_pdb: null, no ground truth to gate against at all) -- same set
# TASK-0166 used for its own "all pocket-scoreable verified targets" run.
TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "PTP1B", "GLUCOKINASE", "CASPASE1", "CASPASE7"]


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _load_apo_holo(target_name: str, target_config: dict):
    import prody

    apo = clean_from_config(target_name, role="apo")
    holo = clean_from_config(target_name, role="holo")

    prody.confProDy(verbosity="none")
    holo_id = target_config["holo_pdb"]
    chains = target_config.get("chains") or sorted(set(holo.chain_ids))
    chain_sel = " or ".join(f"chain {c}" for c in chains)
    holo_struct = prody.parsePDB(holo_id, compressed=False).select(chain_sel)
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, chains, holo.resnums
    )
    return apo, holo


def run_one(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    contact_cutoff = float(target_config.get("enm_cutoff", 10.0))

    apo, holo = _load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None:
        return {"target": target_name, "error": "build_labels returned pocket=None"}

    _log(f"{target_name}: N={len(apo.resnums)}, pocket={int(labels_obj.pocket.sum())}, "
         f"active_site={int(labels_obj.active_site.sum())} -- building deformation family...")
    t0 = time.monotonic()
    try:
        family = build_deformation_family(apo.coords, apo.b_mean)
    except ValueError as exc:
        return {"target": target_name, "error": f"build_deformation_family: {exc!r}"}
    _log(f"{target_name}: family built in {time.monotonic() - t0:.1f}s "
         f"({len(family['admissible'])} admissible, {len(family['rejected'])} rejected)")

    result = go_no_go_gate(
        apo, holo, target_config, labels_obj.active_site, labels_obj.pocket, family,
        cutoff=contact_cutoff, chain_map=chain_map_from_config(target_config),
    )
    result["target"] = target_name
    result["n_residues"] = len(apo.resnums)
    result["pocket_size"] = int(labels_obj.pocket.sum())
    result["active_site_size"] = int(labels_obj.active_site.sum())
    _log(f"{target_name}: verdict={result['verdict']} "
         f"(CO={result['co_final']:.4f}, right_edges={result['right_edges_found']}, "
         f"{result['n_candidates_with_new_edges']}/{result['n_admissible']} admissible candidates)")
    return result


def main():
    results = {}
    for t in TARGETS:
        try:
            results[t] = run_one(t)
        except Exception as e:
            import traceback
            traceback.print_exc()
            results[t] = {"target": t, "error": repr(e)}

    out_dir = Path(__file__).resolve().parent.parent / "RESULTS" / "results_task0015_step2_gate"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "step2_gate.json", "w") as f:
        json.dump(results, f, indent=2, default=lambda o: float(o) if isinstance(o, np.floating) else str(o))
    _log(f"wrote {out_dir / 'step2_gate.json'}")

    print("\n=== TASK-0015 Step 2 go/no-go gate ===")
    print(f"protocol: n_modes={PERTURBATION_PROTOCOL['n_modes']}, "
          f"amplitude_scales={PERTURBATION_PROTOCOL['amplitude_scales']}")
    for t, r in results.items():
        if "error" in r:
            print(f"{t}: ERROR {r['error']}")
            continue
        print(f"{t}: {r['verdict']} -- CO={r['co_final']:.4f} (go={r['co_go']}), "
              f"right_edges={r['right_edges_found']} "
              f"({r['n_candidates_with_new_edges']}/{r['n_admissible']} candidates)")


if __name__ == "__main__":
    main()
