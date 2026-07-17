#!/usr/bin/env python3
"""TASK-0119 -- re-run TASK-0101's 96-cell operator sweep under a
per-operator clock instead of the shared `t_max=15.0`.

**TASK-0129 (2026-07-17): extended in place to also apply TASK-0118's
seed-convention fix (full active-site array, incoherent statistical
mixture, `coherent=False`) at the same time** -- TASK-0119's own Done
section flagged this as the necessary next step ("a further re-run
combining the corrected clock... and the corrected seed... is needed
before either fix's numbers are read as this project's final,
submission-facing state"), and TASK-0129's own Intent Contract explicitly
authorizes extending this script in place rather than building a third
one ("Implementer's call on which script is the better base to extend").
Every number this script now produces is under **both** fixes at once;
the pre-TASK-0129 clock-only numbers this script used to produce remain
on disk unchanged at `results_task0119/` (loaded below as a second
comparison column, not overwritten) -- see `OUTPUT_DIR`.

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
`results/<target>/sweep_cells/*.json` (unchanged, not recomputed), plus
TASK-0119's own clock-only-fix result from `results_task0119/
clock_fix_sweep.json` (also unchanged, not recomputed) -- a three-way
old / clock-fix-only / combined comparison per cell, not just old-vs-new.
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
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.propagators import min_adequate_n_steps, min_adequate_t_max  # noqa: E402
from sweep_operators import ALL_OPERATORS, ALL_PROPAGATORS, DEFAULT_TARGETS  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo/DEFAULT_CUTOFF, not re-derived
from run_challenge import DEFAULT_CUTOFF, DEFAULT_POCKET_CUTOFF  # noqa: E402

TOL = 1e-2  # matches TASK-0109's own check_convergence/min_adequate_* default
OLD_SWEEP_DIR = Path(__file__).resolve().parent.parent / "results"
CLOCK_ONLY_DIR = Path(__file__).resolve().parent.parent / "results_task0119"  # TASK-0119, pre-TASK-0129
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0129"

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


_CLOCK_ONLY_CACHE: dict = {}


def _load_clock_only_cell(target: str, op_name: str, prop_name: str):
    """TASK-0119's own clock-fix-only result (per-operator t*, pre-
    TASK-0129 single-index seed) -- the second comparison column, loaded
    once per process from `results_task0119/clock_fix_sweep.json`."""
    if target not in _CLOCK_ONLY_CACHE:
        path = CLOCK_ONLY_DIR / "clock_fix_sweep.json"
        _CLOCK_ONLY_CACHE.update(json.loads(path.read_text()) if path.exists() else {})
    for row in _CLOCK_ONLY_CACHE.get(target, []):
        if row.get("operator") == op_name and row.get("propagator") == prop_name:
            return row.get("new")
    return None


def _prepare_target_combined(target_name: str):
    """TASK-0118's seed convention (full active-site array), not TASK-0090's
    single-index workaround `sweep_operators._prepare_target` still uses --
    this is TASK-0129's own combined-fix source of truth for this script,
    kept local rather than mutating `sweep_operators.py`'s shared helper
    (that function is also TASK-0101's own original-sweep record; changing
    it in place would silently alter what "old" means for future re-reads).

    Returns (coords, bfactors, source, pocket_label, floor_scores, cutoff).
    """
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")

    active_site_idx = np.where(labels_obj.active_site)[0]
    if len(active_site_idx) == 0:
        raise RuntimeError(f"{target_name}: no resolvable active-site seed")
    source = np.sort(active_site_idx)  # full array, TASK-0118/INV-0006

    floor_scores = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    return apo.coords, apo.bfactors, source, labels_obj.pocket, floor_scores, cutoff


def run_target(target_name: str) -> list:
    _log(f"{target_name}: preparing (fetch + clean + labels, TASK-0118 full-array seed)...")
    coords, bfactors, source, pocket_label, floor_scores, cutoff = _prepare_target_combined(target_name)
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
                    "clock_only": _load_clock_only_cell(target_name, op_name, prop_name),
                    "combined": None, "error": f"H shape {H.shape} incompatible with {len(coords)} residues",
                })
            continue

        w = np.linalg.eigvalsh(H)
        gap = float(w[1] - w[0]) if len(w) > 1 and w[1] > w[0] else None
        t_star = min_adequate_t_max(w=w, kind="ground_state_relaxation", tol=TOL) if gap else None
        n_star = min_adequate_n_steps(w=w, t_max=t_star) if (t_star and np.isfinite(t_star)) else None

        for prop_name in ALL_PROPAGATORS:
            old = _load_old_cell(target_name, op_name, prop_name)
            clock_only = _load_clock_only_cell(target_name, op_name, prop_name)
            if t_star is None or not np.isfinite(t_star):
                rows.append({
                    "target": target_name, "operator": op_name, "tier": tier, "propagator": prop_name,
                    "gap": gap, "t_star": t_star, "n_star": n_star,
                    "old": old, "clock_only": clock_only, "combined": None,
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
                t_max=t_star, n_steps=n_steps_used, coherent=False,
            )
            combined = new_rows[0]
            rows.append({
                "target": target_name, "operator": op_name, "tier": tier, "propagator": prop_name,
                "gap": gap, "t_star": t_star, "n_star": n_star, "n_steps_used": n_steps_used,
                "n_steps_capped": n_steps_capped,
                "old": old, "clock_only": clock_only, "combined": combined, "error": None,
            })
            old_diag = old["diagnosis"] if old else "N/A"
            clock_only_diag = clock_only["diagnosis"] if clock_only else "N/A"
            cap_note = f" [n_steps CAPPED {n_star}->{n_steps_used}]" if n_steps_capped else ""
            _log(
                f"{target_name} {op_name} {prop_name}: t*={t_star:.3g}{cap_note} "
                f"old_diag={old_diag} clock_only_diag={clock_only_diag} -> combined_diag={combined['diagnosis']} "
                f"old_auc={old['auc'] if old else None} clock_only_auc={clock_only['auc'] if clock_only else None} "
                f"combined_auc={combined['auc']}"
            )

    return rows


def render_report(all_rows: dict) -> str:
    lines = [
        "# TASK-0129 -- combined seed (TASK-0118) + clock (TASK-0119) re-run",
        "",
        "old = shared t_max=15, single-index seed (TASK-0101, original).",
        "clock_only = per-operator t*, single-index seed (TASK-0119, pre-TASK-0129).",
        "combined = per-operator t*, full-array incoherent-mixture seed (this task).",
        "",
    ]
    floor_status_changed_vs_old = []
    floor_status_changed_vs_clock_only = []
    for target_name, rows in all_rows.items():
        lines.append(f"## {target_name}")
        lines.append("")
        lines.append("| operator | propagator | t* | n_steps | old AUC/diag | clock_only AUC/diag | combined AUC/diag | changed vs old | changed vs clock_only |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            old, clock_only, combined = r.get("old"), r.get("clock_only"), r.get("combined")
            old_s = f"{old['auc']:.3f}/{old['diagnosis']}" if old and old.get("auc") is not None else "-"
            clock_only_s = f"{clock_only['auc']:.3f}/{clock_only['diagnosis']}" if clock_only and clock_only.get("auc") is not None else "-"
            combined_error = (combined.get("error") if combined else None) or r.get("error")
            combined_s = (
                f"{combined['auc']:.3f}/{combined['diagnosis']}"
                if combined and combined.get("auc") is not None
                else (combined_error or "-")
            )
            changed_old = ""
            if old and combined and old.get("floor_cleared") != combined.get("floor_cleared"):
                changed_old = "**YES**"
                floor_status_changed_vs_old.append((target_name, r["operator"], r["propagator"], old.get("floor_cleared"), combined.get("floor_cleared")))
            changed_clock = ""
            if clock_only and combined and clock_only.get("floor_cleared") != combined.get("floor_cleared"):
                changed_clock = "**YES**"
                floor_status_changed_vs_clock_only.append((target_name, r["operator"], r["propagator"], clock_only.get("floor_cleared"), combined.get("floor_cleared")))
            t_star_str = f"{r['t_star']:.3g}" if r.get("t_star") else "-"
            n_steps_str = str(r["n_steps_used"]) + (" (capped)" if r.get("n_steps_capped") else "") if r.get("n_steps_used") else "-"
            lines.append(
                f"| {r['operator']} | {r['propagator']} | {t_star_str} | {n_steps_str} | "
                f"{old_s} | {clock_only_s} | {combined_s} | {changed_old} | {changed_clock} |"
            )
        lines.append("")

    lines.append("## Floor-clearance status changes: combined vs. old (shared clock, single-index seed)")
    lines.append("")
    if floor_status_changed_vs_old:
        for target, op, prop, old_fc, new_fc in floor_status_changed_vs_old:
            lines.append(f"- {target} {op}/{prop}: floor_cleared {old_fc} -> {new_fc}")
    else:
        lines.append("- None.")
    lines.append("")
    lines.append("## Floor-clearance status changes: combined vs. clock_only (TASK-0119, single-index seed)")
    lines.append("")
    lines.append("This isolates the seed fix's own marginal effect, holding the clock fix constant.")
    lines.append("")
    if floor_status_changed_vs_clock_only:
        for target, op, prop, old_fc, new_fc in floor_status_changed_vs_clock_only:
            lines.append(f"- {target} {op}/{prop}: floor_cleared {old_fc} -> {new_fc}")
    else:
        lines.append("- None -- the seed fix alone did not flip any floor-clearance status in this 96-cell sweep.")
    return "\n".join(lines) + "\n"


def run_bcr_abl1_trapping_reproduction_combined() -> dict:
    """Re-run TASK-0106's BCR_ABL1 CTQW-trapping reproduction under both
    fixes at once: each operator's own per-operator `t*` (TASK-0119) AND
    the full active-site array, incoherent mixture (TASK-0118) -- unlike
    TASK-0119's own re-run, which kept TASK-0106's original single-index
    seed unchanged (explicitly flagged there as the reason this further
    re-run is needed). Same transport diagnostics (`metrics.ipr`,
    occupation-weighted mean hop) as both prior reproductions, reusing
    `ctqw_trapping_reproduction.py`'s own building blocks."""
    import ctqw_trapping_reproduction as trap

    target_name = "BCR_ABL1"
    target_config = trap.load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", trap.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", trap.DEFAULT_POCKET_CUTOFF))

    apo, holo = trap.run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = trap.build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    active_site_idx = np.where(labels_obj.active_site)[0]
    source = np.sort(active_site_idx)  # full array, TASK-0118/INV-0006
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
        occ = trap.time_averaged_ctqw(H, t_star, source=source, n_steps=n_steps_used, coherent=False)
        auc = trap._auc(occ, pocket_int)
        diag = trap.transport_diagnostics(occ, apo.coords, source, cutoff)
        rows[name] = {
            "t_star": t_star, "n_steps_used": n_steps_used,
            "auc": auc, "floor_cleared": bool(not np.isnan(auc) and auc > floor),
            **diag,
        }
        _log(f"BCR_ABL1 trapping-repro (combined) {name}: t*={t_star:.3g} AUC={auc:.4f} PR(ipr)={diag['participation_ratio']:.4f} <hop>={diag['mean_hop_from_seed']:.3f}")

    old = None
    old_path = Path(__file__).resolve().parent.parent / "results_task0106" / "BCR_ABL1" / "reproduction.json"
    if old_path.exists():
        with open(old_path) as f:
            old = json.load(f)

    clock_only = None
    clock_only_path = CLOCK_ONLY_DIR / "trapping_reproduction_fixed_clock.json"
    if clock_only_path.exists():
        with open(clock_only_path) as f:
            clock_only = json.load(f).get("new_per_operator_t_star")

    return {
        "target": target_name, "floor": floor,
        "old_t_max_15_single_index": old,
        "clock_only_t_star_single_index": clock_only,
        "combined_t_star_full_array": rows,
    }


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
        with open(args.output_dir / "combined_sweep.json", "w") as f:
            json.dump(all_rows, f, indent=2)
        report = render_report(all_rows)
        with open(args.output_dir / "report.md", "w") as f:
            f.write(report)
        print(report)

    if not args.skip_trapping_repro:
        trapping_result = run_bcr_abl1_trapping_reproduction_combined()
        with open(args.output_dir / "trapping_reproduction_combined.json", "w") as f:
            json.dump(trapping_result, f, indent=2)
        print(json.dumps(trapping_result, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
