"""TASK-0216 step 5 -- rerun TASK-0201's OWN statistic for PTP1B under the
corrected (UniProt) active site.

TASK-0201's surviving positive is PTP1B `dcc_low` k=10, p=0.0027 against a
pre-registered bar of 0.05/16 = 0.003125, measured as a **stratified
well-powered-max AUC** against a graph-walk Rg-matched permutation null at
20,000 replicates.

TASK-0216 found PTP1B's active site is the top-5 highest-degree residues, not
a functional site. The earlier whole-graph comparison in
`task0216_ptp1b_real_seed.py` established the seed change is material
(overlap 1/9, dAUC -0.133) but is **not comparable** to TASK-0201's number --
a different statistic. This script recomputes TASK-0201's actual statistic.

The seed enters in three places, all of which must move together:
  1. `source` -- `dcc_low`'s own seed argument.
  2. `shells` -- `-hop_from_seed(source)`, i.e. the stratification the
     well-powered-max is taken over. Changing the seed changes which shells
     exist and which residues fall in them.
  3. `pocket` -- `build_labels` assembles `pocket_raw & ~active_site &
     ~terminal`, so a different active site excludes different residues.

Everything else is reused byte-for-byte from the original harness: the same
`graph_walk_null`, `K_MODES_GRID`, `FINAL_N_REPS=20_000`, `PERM_SEED`,
`TOL`, `WALK_CUTOFF`, and the same pre-registered survival bar (0.05/16).
Only the seed changes. Both configurations are reported side by side.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402
prody.confProDy(verbosity="none")

import graph_walk_matched_null_rerun as GW  # noqa: E402
from compact_null_rerun import K_MODES_GRID, _lowmode_prepare_target  # noqa: E402
from allostery.baselines import hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.labels import holo_pocket_mask, terminal_mask  # noqa: E402
from allostery.lowmode_predictor import dcc_low  # noqa: E402
from allostery.nulls import build_adjacency, radius_of_gyration  # noqa: E402
from backend import active_site as backend_active_site  # noqa: E402
import run_challenge  # noqa: E402

TARGET = "PTP1B"
BAR = GW.SURVIVAL_BARS[TARGET]           # 0.05/16, unchanged
OUT = _ROOT / "results_task0216_new_pair_scoring" / "task0201_rerun_real_seed.json"


def _log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def prepare_real_seed() -> dict:
    """`_lowmode_prepare_target`, with the active site taken from UniProt
    instead of the top-degree fallback. Rebuilds `source`, `shells` and
    `pocket` consistently from that seed."""
    cfg = load_target_config(TARGET)
    cutoff = float(cfg.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(cfg.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))
    apo, holo = run_challenge._load_apo_holo(TARGET, cfg)

    ch = cfg.get("apo_chains") or cfg.get("chains")
    det = backend_active_site.detect_active_site(cfg["apo_pdb"], chain=ch[0])
    if det.get("source") != "uniprot" or not det.get("active_site"):
        raise RuntimeError(f"no UniProt active site for {TARGET}: {det.get('source')!r}")
    resnums = np.asarray(apo.resnums)
    source = np.sort(np.where(np.isin(resnums, list(det["active_site"])))[0])
    if len(source) == 0:
        raise RuntimeError("UniProt active-site resnums do not map onto the apo array")

    pocket_raw = holo_pocket_mask(apo, holo, cfg["drug_ligand"], cutoff=pocket_cutoff)
    if pocket_raw is None:
        raise RuntimeError("holo_pocket_mask returned None")
    n = len(resnums)
    active = np.zeros(n, dtype=bool)
    active[source] = True
    pocket = (pocket_raw & ~active & ~terminal_mask(n, 0.05)).astype(int)

    return {
        "coords": apo.coords, "source": source, "pocket": pocket, "cutoff": cutoff,
        "shells": -hop_from_seed(apo.coords, source, cutoff=cutoff),
        "n_residues": n,
        "_seed_resnums": [int(x) for x in resnums[source]],
    }


def evaluate(prep: dict, tag: str) -> dict:
    coords = prep["coords"]
    adjacency = build_adjacency(coords, GW.WALK_CUTOFF)
    pocket_idx = np.where(prep["pocket"])[0]
    target_rg = radius_of_gyration(coords, pocket_idx)
    _log(f"{tag}: seed={len(prep['source'])} res, pocket={int(prep['pocket'].sum())}, "
         f"pocket_Rg={target_rg:.3f}")

    cells = {}
    for k in K_MODES_GRID:
        score = dcc_low(coords, prep["source"], cutoff=prep["cutoff"], k_modes=k)
        res = GW.graph_walk_null(score, prep, adjacency,
                                 target_rg=target_rg, n_reps=GW.FINAL_N_REPS)
        p = res["p_value"]
        cells[k] = {"p_value": p,
                    "real_well_powered_max_auc": res["real_well_powered_max_auc"],
                    "real_shell": res["real_shell"],
                    "survives_bar": bool(p < BAR)}
        _log(f"  k={k}: auc={res['real_well_powered_max_auc']:.3f} p={p:.5f} "
             f"{'SURVIVES' if p < BAR else 'fails'} (bar {BAR:.6f})")
    return {"tag": tag, "n_seed": int(len(prep["source"])),
            "seed_resnums": prep.get("_seed_resnums"),
            "n_pocket": int(prep["pocket"].sum()), "pocket_rg": float(target_rg),
            "cells": cells,
            "any_survives": any(c["survives_bar"] for c in cells.values())}


def main() -> int:
    _log(f"{TARGET}: bar = {BAR:.6f} (0.05/16, TASK-0151), reps = {GW.FINAL_N_REPS}")

    _log("--- configuration 1: top-degree fallback (what TASK-0201 used) ---")
    fb = evaluate(_lowmode_prepare_target(TARGET), "top-degree fallback")

    _log("--- configuration 2: UniProt catalytic site (corrected) ---")
    real = evaluate(prepare_real_seed(), "UniProt catalytic site")

    out = {"target": TARGET, "bar": BAR, "n_reps": GW.FINAL_N_REPS,
           "fallback": fb, "real": real,
           "seed_overlap": int(len(set(map(int, _lowmode_prepare_target(TARGET)["source"]))
                                   & set(map(int, prepare_real_seed()["source"]))))}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=str))

    print("\n=== TASK-0201 rerun: PTP1B dcc_low, stratified well-powered-max, graph-walk null ===")
    print(f"{'k':>4} {'fallback auc':>13} {'fallback p':>12} {'real auc':>10} {'real p':>10} {'bar':>10}")
    for k in K_MODES_GRID:
        a, b = fb["cells"][k], real["cells"][k]
        print(f"{k:>4} {a['real_well_powered_max_auc']:>13.3f} {a['p_value']:>12.5f} "
              f"{b['real_well_powered_max_auc']:>10.3f} {b['p_value']:>10.5f} {BAR:>10.6f}")
    print(f"\nfallback survives at any k: {fb['any_survives']}")
    print(f"real     survives at any k: {real['any_survives']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
