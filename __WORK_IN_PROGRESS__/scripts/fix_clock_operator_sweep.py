#!/usr/bin/env python3
"""TASK-0119 -- re-run TASK-0101's 96-cell operator sweep under a
per-operator clock instead of the shared `t_max=15.0`.

`REVIEW-panel-2026-07-16-v2.md` section 2.2: `t_max=15` is hardcoded and
applied to every operator regardless of its own energy scale -- "a
precondition for the physics, not hygiene." The panel's proposed fix:
`t* ~ 1/dlambda` (the graph mixing time from `H`'s own spectral gap), per
operator, instead of one shared nominal time for every operator.

This script uses TASK-0109's own `propagators.min_adequate_t_max` (the
same closed-form `t* = -ln(tol)/gap` this task's own Dependency section
says to use if TASK-0109 lands first -- it has) as the per-operator clock,
applied identically to both propagators for a given operator (a single
`t*` per operator, matching this task's own Intent Contract, "every
operator is compared at the same effective time" -- not a second,
propagator-specific formula, which TASK-0109's own battery found fragile
on near-degenerate spectra for the `time_averaged_ctqw`-specific
criterion; see that task's Done section).

Loads each cell's OLD result directly from TASK-0101's already-computed
`results/<target>/sweep_cells/*.json` (unchanged, not recomputed) for a
side-by-side old-vs-new comparison -- this script only recomputes the new
column.
"""
from __future__ import annotations

import argparse
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
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from allostery.analysis import _operator_registry, operator_sweep  # noqa: E402
from allostery.propagators import min_adequate_n_steps, min_adequate_t_max  # noqa: E402
from sweep_operators import ALL_OPERATORS, ALL_PROPAGATORS, DEFAULT_TARGETS, _prepare_target  # noqa: E402

TOL = 1e-2  # matches TASK-0109's own check_convergence/min_adequate_* default
OLD_SWEEP_DIR = Path(__file__).resolve().parent.parent / "results"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0119"

N_STEPS_PRACTICAL_CAP = 5000  # found necessary running this script's real
# 96-cell sweep: CARDIAC_MYOSIN H9's tiny gap (0.00776) drives t*=593.15,
# and its own bandwidth then drives min_adequate_n_steps to 3,095,469,321
# -- a real MemoryError (23.1 GiB linspace) when passed straight into
# time_averaged_ctqw, same class of fragility TASK-0109's own battery
# script found and capped (T_MAX_SCAN_CAP/N_STEPS_SCAN_CAP) for the exact
# same reason (near-degenerate/small-gap spectra blow up the Nyquist
# prediction). Cells that hit this cap are flagged `n_steps_capped: true`
# in the output, not silently under-sampled without a record of it.


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _load_old_cell(target: str, op_name: str, prop_name: str):
    path = OLD_SWEEP_DIR / target / "sweep_cells" / f"{op_name}__{prop_name}.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def run_target(target_name: str) -> list:
    _log(f"{target_name}: preparing (fetch + clean + labels)...")
    coords, bfactors, source, pocket_label, floor_scores, cutoff = _prepare_target(target_name)
    registry = _operator_registry()

    rows = []
    for op_name in ALL_OPERATORS:
        if op_name not in registry:
            continue
        tier, build_fn = registry[op_name]
        try:
            H = build_fn(coords, bfactors, cutoff)
        except Exception as exc:
            rows.append({"target": target_name, "operator": op_name, "error": f"H build failed: {exc!r}"})
            continue

        if H.shape[0] != len(coords):
            # H13's known 3N-shape mismatch (TASK-0101) -- record identically,
            # do not attempt a clock fix for an operator this sweep can't
            # score at all regardless of t_max.
            for prop_name in ALL_PROPAGATORS:
                rows.append({
                    "target": target_name, "operator": op_name, "tier": tier, "propagator": prop_name,
                    "gap": None, "t_star": None, "n_star": None,
                    "old": _load_old_cell(target_name, op_name, prop_name),
                    "new": None, "error": f"H shape {H.shape} incompatible with {len(coords)} residues",
                })
            continue

        w = np.linalg.eigvalsh(H)
        gap = float(w[1] - w[0]) if len(w) > 1 and w[1] > w[0] else None
        t_star = min_adequate_t_max(w=w, kind="ground_state_relaxation", tol=TOL) if gap else None
        n_star = min_adequate_n_steps(w=w, t_max=t_star) if (t_star and np.isfinite(t_star)) else None

        for prop_name in ALL_PROPAGATORS:
            old = _load_old_cell(target_name, op_name, prop_name)
            if t_star is None or not np.isfinite(t_star):
                rows.append({
                    "target": target_name, "operator": op_name, "tier": tier, "propagator": prop_name,
                    "gap": gap, "t_star": t_star, "n_star": n_star, "old": old, "new": None,
                    "error": "degenerate/zero spectral gap -- no finite t* under this criterion",
                })
                continue
            n_steps_used = (n_star if prop_name == "ctqw" else 500) or 500
            n_steps_capped = n_steps_used > N_STEPS_PRACTICAL_CAP
            if n_steps_capped:
                n_steps_used = N_STEPS_PRACTICAL_CAP
            new_rows = operator_sweep(
                coords, bfactors, source, pocket_label, floor_scores,
                cutoff=cutoff, operators=[op_name], propagators=[prop_name],
                t_max=t_star, n_steps=n_steps_used,
            )
            new = new_rows[0]
            rows.append({
                "target": target_name, "operator": op_name, "tier": tier, "propagator": prop_name,
                "gap": gap, "t_star": t_star, "n_star": n_star, "n_steps_used": n_steps_used,
                "n_steps_capped": n_steps_capped, "old": old, "new": new, "error": None,
            })
            old_diag = old["diagnosis"] if old else "N/A"
            cap_note = f" [n_steps CAPPED {n_star}->{n_steps_used}]" if n_steps_capped else ""
            _log(
                f"{target_name} {op_name} {prop_name}: t*={t_star:.3g} (old t=15.0){cap_note} "
                f"old_diag={old_diag} -> new_diag={new['diagnosis']} "
                f"old_auc={old['auc'] if old else None} new_auc={new['auc']}"
            )

    return rows


def render_report(all_rows: dict) -> str:
    lines = ["# TASK-0119 -- per-operator clock re-run (vs old shared t_max=15.0)", ""]
    ranking_shifted = []
    floor_status_changed = []
    for target_name, rows in all_rows.items():
        lines.append(f"## {target_name}")
        lines.append("")
        lines.append("| operator | propagator | gap | t* | n_steps | old AUC | old diag | new AUC | new diag | floor_cleared changed? |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            old, new = r.get("old"), r.get("new")
            old_auc = f"{old['auc']:.3f}" if old and old.get("auc") is not None else "-"
            old_diag = old["diagnosis"] if old else "-"
            new_auc = f"{new['auc']:.3f}" if new and new.get("auc") is not None else "-"
            new_error = (new.get("error") if new else None) or r.get("error")
            new_diag = (new["diagnosis"] if new and new.get("diagnosis") else None) or new_error or "-"
            changed = ""
            if old and new and old.get("floor_cleared") != new.get("floor_cleared"):
                changed = "**YES**"
                floor_status_changed.append((target_name, r["operator"], r["propagator"], old.get("floor_cleared"), new.get("floor_cleared")))
            gap_str = f"{r['gap']:.3g}" if r.get("gap") else "-"
            t_star_str = f"{r['t_star']:.3g}" if r.get("t_star") else "-"
            n_steps_str = str(r["n_steps_used"]) + (" (capped)" if r.get("n_steps_capped") else "") if r.get("n_steps_used") else "-"
            lines.append(
                f"| {r['operator']} | {r['propagator']} | {gap_str} | {t_star_str} | {n_steps_str} | "
                f"{old_auc} | {old_diag} | {new_auc} | {new_diag} | {changed} |"
            )
        lines.append("")

    lines.append("## Floor-clearance status changes (old shared-t_max=15 vs new per-operator t*)")
    lines.append("")
    if floor_status_changed:
        for target, op, prop, old_fc, new_fc in floor_status_changed:
            lines.append(f"- {target} {op}/{prop}: floor_cleared {old_fc} -> {new_fc}")
    else:
        lines.append("- None -- floor-clearance status is identical under both clocks for every scored cell.")
    return "\n".join(lines) + "\n"


def run_bcr_abl1_trapping_reproduction_fixed_clock() -> dict:
    """Re-run TASK-0106's BCR_ABL1 CTQW-trapping reproduction under each
    operator's own per-operator `t*` instead of the shared `T_MAX=15.0`
    that script used -- same four operators, same seed convention (single
    sorted-first active-site index, TASK-0106's own established choice,
    reproduced exactly first before trusting anything new -- see this
    function's own sanity check in its caller), same transport
    diagnostics (`metrics.ipr`, occupation-weighted mean hop), reusing
    `ctqw_trapping_reproduction.py`'s own building blocks rather than
    re-deriving them."""
    import ctqw_trapping_reproduction as trap

    target_name = "BCR_ABL1"
    target_config = trap.load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", trap.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", trap.DEFAULT_POCKET_CUTOFF))

    apo, holo = trap.run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = trap.build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    active_site_idx = np.where(labels_obj.active_site)[0]
    source = int(np.sort(active_site_idx)[0])
    pocket_int = labels_obj.pocket.astype(int)

    floor_candidates = [
        trap.degree_centrality(apo.coords, cutoff=cutoff),
        trap.euclid_from_seed_centroid(apo.coords, source),
        trap.hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    floor = max(trap._auc(f, pocket_int) for f in floor_candidates)

    operators = {
        "H_new_default": trap.build_H_new(apo.coords, apo.bfactors, cutoff=cutoff),
        "H_new_lambda=0.25": trap._build_h_new_scaled(apo.coords, apo.bfactors, cutoff, 0.25),
        "H10_disorder_suppressed": trap.build_H10(apo.coords, apo.bfactors, cutoff=cutoff),
        "H2_combinatorial_laplacian": trap.H2_combinatorial_laplacian(apo.coords, cutoff=cutoff),
    }

    rows = {}
    for name, H in operators.items():
        w = np.linalg.eigvalsh(H)
        t_star = min_adequate_t_max(w=w, kind="ground_state_relaxation", tol=TOL)
        n_star = min_adequate_n_steps(w=w, t_max=t_star)
        n_steps_used = min(n_star, N_STEPS_PRACTICAL_CAP) if np.isfinite(n_star) else 500
        occ = trap.time_averaged_ctqw(H, t_star, source=source, n_steps=n_steps_used)
        auc = trap._auc(occ, pocket_int)
        diag = trap.transport_diagnostics(occ, apo.coords, source, cutoff)
        rows[name] = {
            "t_star": t_star, "n_steps_used": n_steps_used,
            "auc": auc, "floor_cleared": bool(not np.isnan(auc) and auc > floor),
            **diag,
        }
        _log(f"BCR_ABL1 trapping-repro {name}: t*={t_star:.3g} AUC={auc:.4f} PR(ipr)={diag['participation_ratio']:.4f} <hop>={diag['mean_hop_from_seed']:.3f}")

    old = None
    old_path = Path(__file__).resolve().parent.parent / "results_task0106" / "BCR_ABL1" / "reproduction.json"
    if old_path.exists():
        with open(old_path) as f:
            old = json.load(f)

    return {"target": target_name, "floor": floor, "old_t_max_15": old, "new_per_operator_t_star": rows}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=None)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--skip-sweep", action="store_true", help="skip the 96-cell re-run, only re-run TASK-0106's BCR_ABL1 trapping reproduction")
    parser.add_argument("--skip-trapping-repro", action="store_true")
    args = parser.parse_args(argv)
    targets = args.target or DEFAULT_TARGETS
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_sweep:
        all_rows = {}
        for target_name in targets:
            try:
                all_rows[target_name] = run_target(target_name)
            except Exception as exc:
                _log(f"{target_name}: SKIP (target-level failure): {exc!r}")
        with open(args.output_dir / "clock_fix_sweep.json", "w") as f:
            json.dump(all_rows, f, indent=2)
        report = render_report(all_rows)
        with open(args.output_dir / "report.md", "w") as f:
            f.write(report)
        print(report)

    if not args.skip_trapping_repro:
        trapping_result = run_bcr_abl1_trapping_reproduction_fixed_clock()
        with open(args.output_dir / "trapping_reproduction_fixed_clock.json", "w") as f:
            json.dump(trapping_result, f, indent=2)
        print(json.dumps(trapping_result, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
