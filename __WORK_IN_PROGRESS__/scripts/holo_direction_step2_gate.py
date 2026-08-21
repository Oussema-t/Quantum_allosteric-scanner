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


# Contact-graph cutoff sweep for the shortcut component -- the project's
# own default `enm_cutoff` (typically 8.0 A) is one point on a real KNOB,
# not a fixed physical constant (INV-0001/cumulative_overlap_gate's own
# precedent: cutoff is swept, never picked once and trusted). 4.5 A
# matches this project's own pocket-labeling cutoff (already established
# elsewhere, not a new arbitrary number); 10.0 A is this module's own
# ANM cutoff default. Bracket a tight-to-loose range rather than trust
# one target-configured value, since a spot check found the "active site
# and pocket already adjacent" reading is cutoff-robust for some targets
# and a pure artifact of the 8.0 A default for others (BCR_ABL1, PTP1B,
# CASPASE7 -- real hop 5-10 at 4.5-6.0 A, collapsing to 1-2 only at
# 8.0-10.0 A).
CONTACT_CUTOFF_GRID = (4.5, 6.0, 8.0, 10.0)


def run_one(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))

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

    chain_map = chain_map_from_config(target_config)
    grid = {}
    for cutoff in CONTACT_CUTOFF_GRID:
        r = go_no_go_gate(
            apo, holo, target_config, labels_obj.active_site, labels_obj.pocket, family,
            cutoff=cutoff, chain_map=chain_map,
        )
        grid[cutoff] = r
        _log(f"{target_name} @ cutoff={cutoff}: verdict={r['verdict']} "
             f"(CO={r['co_final']:.4f}, apo_hop={r['apo_hop_min']:.1f}->{r['best_hop_min']:.1f}, "
             f"shortcut={r['shortcut_found']}, {r['n_candidates_with_shortcut']}/{r['n_admissible']})")

    shortcuts = [g["shortcut_found"] for g in grid.values()]
    if all(shortcuts):
        shortcut_verdict = "GO"
    elif not any(shortcuts):
        shortcut_verdict = "NO_GO"
    else:
        shortcut_verdict = "UNSTABLE"  # depends on which cutoff was run -- never collapsed to a point estimate

    return {
        "target": target_name,
        "n_residues": len(apo.resnums),
        "pocket_size": int(labels_obj.pocket.sum()),
        "active_site_size": int(labels_obj.active_site.sum()),
        "cutoff_grid": {str(c): r for c, r in grid.items()},
        "shortcut_verdict_across_grid": shortcut_verdict,
        "co_final": grid[CONTACT_CUTOFF_GRID[-1]]["co_final"],  # CO doesn't depend on contact cutoff, same at every grid point
    }


def main():
    results = {}
    for t in TARGETS:
        try:
            results[t] = run_one(t)
        except Exception as e:
            import traceback
            traceback.print_exc()
            results[t] = {"target": t, "error": repr(e)}

    out_dir = Path(__file__).resolve().parent.parent / "RESULTS" / "results/tasks/0015_step2_gate"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "step2_gate.json", "w") as f:
        json.dump(results, f, indent=2, default=lambda o: float(o) if isinstance(o, np.floating) else str(o))
    _log(f"wrote {out_dir / 'step2_gate.json'}")

    print("\n=== TASK-0015 Step 2 go/no-go gate ===")
    print(f"protocol: n_modes={PERTURBATION_PROTOCOL['n_modes']}, "
          f"amplitude_scales={PERTURBATION_PROTOCOL['amplitude_scales']}")
    co_threshold = 0.5
    for t, r in results.items():
        if "error" in r:
            print(f"{t}: ERROR {r['error']}")
            continue
        co_go = r["co_final"] >= co_threshold if r["co_final"] == r["co_final"] else False  # NaN-safe
        per_cutoff = ", ".join(
            f"{c}A:hop{g['apo_hop_min']:.0f}->{g['best_hop_min']:.0f}"
            for c, g in r["cutoff_grid"].items()
        )
        print(f"{t}: shortcut_verdict={r['shortcut_verdict_across_grid']} CO={r['co_final']:.4f} (go={co_go}) "
              f"[{per_cutoff}]")


if __name__ == "__main__":
    main()
