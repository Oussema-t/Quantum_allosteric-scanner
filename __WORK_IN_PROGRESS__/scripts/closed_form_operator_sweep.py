#!/usr/bin/env python3
"""TASK-0130 -- re-run TASK-0101's 96-cell operator sweep, and TASK-0106's
BCR_ABL1 CTQW-trapping reproduction, under `time_averaged_ctqw_converged`'s
exact infinite-time closed form -- no per-operator `t*`/`n_steps` to
derive at all (unlike TASK-0119/0129's `fix_clock_operator_sweep.py`,
which this script parallels but does not extend in place: that script's
own per-cell `t*`/`n_steps`-capping logic is specific to the finite-time
convention and has nothing left to do once the closed form replaces it).

Three-way comparison per cell: `old` (TASK-0101, single-index seed,
shared `t_max=15`), `combined` (TASK-0129, full-array incoherent seed,
per-operator `t*`), `closed_form` (this task, full-array incoherent seed,
exact infinite-time limit, no clock at all) -- loaded from TASK-0101's
and TASK-0129's own already-computed results, not recomputed.
`ground_state` propagator rows are recomputed under `t_max=15` (the
convention `use_converged_limit` does not touch, per its own docstring)
using the full-array/incoherent seed for a fair apples-to-apples
comparison against `combined`'s own `ground_state` rows.
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

from allostery.analysis import operator_sweep  # noqa: E402
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import H2_combinatorial_laplacian, build_H10, build_H_new  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc, ipr as _ipr  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from sweep_operators import ALL_OPERATORS, ALL_PROPAGATORS, DEFAULT_TARGETS  # noqa: E402
from fix_clock_operator_sweep import _load_old_cell  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo/DEFAULT_CUTOFF
from run_challenge import DEFAULT_CUTOFF, DEFAULT_POCKET_CUTOFF  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0130_competence"
COMBINED_DIR = Path(__file__).resolve().parent.parent / "results_task0129"  # TASK-0129's own combined sweep


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


_COMBINED_CACHE: dict = {}


def _load_combined_cell(target: str, op_name: str, prop_name: str):
    if not _COMBINED_CACHE:
        path = COMBINED_DIR / "combined_sweep.json"
        _COMBINED_CACHE.update(json.loads(path.read_text()) if path.exists() else {})
    for row in _COMBINED_CACHE.get(target, []):
        if row.get("operator") == op_name and row.get("propagator") == prop_name:
            return row.get("combined")
    return None


def _prepare_target(target_name: str):
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
    _log(f"{target_name}: preparing (fetch + clean + labels)...")
    coords, bfactors, source, pocket_label, floor_scores, cutoff = _prepare_target(target_name)

    t0 = time.monotonic()
    new_rows = operator_sweep(
        coords, bfactors, source, pocket_label, floor_scores,
        cutoff=cutoff, coherent=False, use_converged_limit=True,
    )
    _log(f"{target_name}: 32-cell sweep (16 operators x 2 propagators) done in {time.monotonic()-t0:.1f}s")

    rows = []
    for new_row in new_rows:
        op_name, prop_name = new_row["operator"], new_row["propagator"]
        old = _load_old_cell(target_name, op_name, prop_name)
        combined = _load_combined_cell(target_name, op_name, prop_name)
        rows.append({
            "target": target_name, "operator": op_name, "tier": new_row["tier"], "propagator": prop_name,
            "old": old, "combined": combined, "closed_form": new_row,
        })
        old_diag = old["diagnosis"] if old else "N/A"
        combined_diag = combined["diagnosis"] if combined else "N/A"
        _log(
            f"{target_name} {op_name} {prop_name}: old_diag={old_diag} combined_diag={combined_diag} -> "
            f"closed_form_diag={new_row['diagnosis']} old_auc={old['auc'] if old else None} "
            f"combined_auc={combined['auc'] if combined else None} closed_form_auc={new_row['auc']}"
        )
    return rows


def render_report(all_rows: dict) -> str:
    lines = [
        "# TASK-0130 -- closed-form (infinite-time) 96-cell operator sweep",
        "",
        "old = TASK-0101, shared t_max=15, single-index seed.",
        "combined = TASK-0129, per-operator t*, full-array incoherent-mixture seed.",
        "closed_form = this task: exact infinite-time limit (`ctqw`), full-array",
        "incoherent-mixture seed, no t_max/t*/n_steps at all. `ground_state` rows",
        "still use t_max=15 (unaffected, out of this task's scope).",
        "",
    ]
    floor_status_changed = []
    for target_name, rows in all_rows.items():
        lines.append(f"## {target_name}")
        lines.append("")
        lines.append("| operator | propagator | old AUC/diag | combined AUC/diag | closed_form AUC/diag | changed vs combined |")
        lines.append("|---|---|---|---|---|---|")
        for r in rows:
            old, combined, cf = r.get("old"), r.get("combined"), r.get("closed_form")
            old_s = f"{old['auc']:.3f}/{old['diagnosis']}" if old and old.get("auc") is not None else "-"
            combined_s = f"{combined['auc']:.3f}/{combined['diagnosis']}" if combined and combined.get("auc") is not None else "-"
            cf_error = cf.get("error") if cf else None
            cf_s = f"{cf['auc']:.3f}/{cf['diagnosis']}" if cf and cf.get("auc") is not None else (cf_error or "-")
            changed = ""
            if combined and cf and combined.get("floor_cleared") != cf.get("floor_cleared"):
                changed = "**YES**"
                floor_status_changed.append((target_name, r["operator"], r["propagator"], combined.get("floor_cleared"), cf.get("floor_cleared")))
            lines.append(f"| {r['operator']} | {r['propagator']} | {old_s} | {combined_s} | {cf_s} | {changed} |")
        lines.append("")

    lines.append("## Floor-clearance status changes: closed_form vs. combined (TASK-0129)")
    lines.append("")
    if floor_status_changed:
        for target, op, prop, old_fc, new_fc in floor_status_changed:
            lines.append(f"- {target} {op}/{prop}: floor_cleared {old_fc} -> {new_fc}")
    else:
        lines.append("- None -- removing the clock entirely did not flip any floor-clearance status in this 96-cell sweep.")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# TASK-0106's BCR_ABL1 CTQW-trapping reproduction, under the closed form.
# ---------------------------------------------------------------------------

_H_NEW_DEFAULT_LAMBDAS = dict(lam_B=0.08, lam_T=0.16, lam_R=0.08, lam_C=0.04, lam_M=0.04)  # TASK-0121


def _build_h_new_scaled(coords, bfactors, cutoff: float, lam: float):
    scaled = {k: lam * v for k, v in _H_NEW_DEFAULT_LAMBDAS.items()}
    return build_H_new(coords, bfactors, cutoff=cutoff, **scaled)


def transport_diagnostics(occ: np.ndarray, coords: np.ndarray, source, cutoff: float) -> dict:
    from allostery.propagators import _source_indices

    idx = _source_indices(source)
    from scipy.spatial.distance import cdist

    dmat = cdist(coords, coords)
    hop = dmat[idx].mean(axis=0)  # Euclidean proxy, matches ctqw_trapping_reproduction.py's own convention
    mean_hop = float(np.sum(occ * hop))
    return {"participation_ratio": float(_ipr(occ)), "mean_hop_from_seed": mean_hop}


def run_bcr_abl1_trapping_reproduction_closed_form() -> dict:
    """Re-run TASK-0106's BCR_ABL1 CTQW-trapping reproduction using the
    exact infinite-time limit directly -- no `t*`/`n_steps` at all,
    unlike TASK-0119/0129's own `run_bcr_abl1_trapping_reproduction_
    combined` (which this mirrors structurally). Same 4-operator family
    and transport diagnostics (`ipr`, occupation-weighted mean distance
    from seed) as both prior reproductions."""
    target_name = "BCR_ABL1"
    coords, bfactors, source, pocket_label, floor_scores, cutoff = _prepare_target(target_name)
    pocket_int = pocket_label.astype(int)
    floor = max(_auc(f, pocket_int) for f in floor_scores)

    operators = {
        "H_new_default": build_H_new(coords, bfactors, cutoff=cutoff),
        "H_new_lambda=0.25": _build_h_new_scaled(coords, bfactors, cutoff, 0.25),
        "H10_disorder_suppressed": build_H10(coords, bfactors, cutoff=cutoff),
        "H2_combinatorial_laplacian": H2_combinatorial_laplacian(coords, cutoff=cutoff),
    }

    rows = {}
    for name, H in operators.items():
        occ = time_averaged_ctqw_converged(H, source=source, coherent=False)
        auc = _auc(occ, pocket_int)
        diag = transport_diagnostics(occ, coords, source, cutoff)
        rows[name] = {
            "auc": auc, "floor_cleared": bool(not np.isnan(auc) and auc > floor),
            **diag,
        }
        _log(
            f"BCR_ABL1 trapping-repro (closed_form) {name}: AUC={auc:.4f} "
            f"PR(ipr)={diag['participation_ratio']:.4f} <hop>={diag['mean_hop_from_seed']:.3f}"
        )

    combined_path = Path(__file__).resolve().parent.parent / "results_task0129" / "trapping_reproduction_combined.json"
    combined = json.loads(combined_path.read_text()) if combined_path.exists() else None

    return {"target": target_name, "floor": floor, "rows": rows, "combined_2026-07-18": combined}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=None)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--skip-sweep", action="store_true")
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
        with open(args.output_dir / "closed_form_sweep.json", "w") as f:
            json.dump(all_rows, f, indent=2)
        report = render_report(all_rows)
        with open(args.output_dir / "sweep_report.md", "w") as f:
            f.write(report)
        print(report)

    if not args.skip_trapping_repro:
        trapping_result = run_bcr_abl1_trapping_reproduction_closed_form()
        with open(args.output_dir / "trapping_reproduction_closed_form.json", "w") as f:
            json.dump(trapping_result, f, indent=2)
        print(json.dumps(trapping_result, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
