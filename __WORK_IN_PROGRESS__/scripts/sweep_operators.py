#!/usr/bin/env python3
"""TASK-0101 -- Tier-1 operator sweep CLI.

Runs `analysis.operator_sweep` (16 named operators x 2 propagators) across
the mandatory targets and writes one result table per target. Tier-1
(descriptive) only -- no `frozen_context`, no operator selection; see
`analysis.operator_sweep`'s own docstring and TASK-0100's architecture
decision for why.

Chunking and resumability (TASK-0101's own hard requirement): each
(target, operator, propagator) cell is computed and written to its own
JSON file immediately, before moving to the next cell -- a killed or
crashed run loses at most the one in-flight cell. Re-running the same
command is idempotent by default (existing cell files are skipped, not
recomputed); `--force` recomputes only the cells the current
--target/--operator/--propagator filters select, leaving every other
cell's file untouched. Two invocations with disjoint --target filters can
run on separate machines with no shared state beyond each writing its own
`results/<target>/sweep_cells/` -- copy both trees together and
`--aggregate` renders the combined table without recomputing anything.

Usage
-----
  python scripts/sweep_operators.py                      # full grid, all 3 targets, aggregates at the end
  python scripts/sweep_operators.py --target BCR_ABL1     # one target only
  python scripts/sweep_operators.py --target KRAS_G12C --operator H_new H10 --propagator ctqw
  python scripts/sweep_operators.py --force --target BCR_ABL1 --operator H_new --propagator ground_state
  python scripts/sweep_operators.py --aggregate           # render tables from whatever cell files already exist, compute nothing
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Must run before `import numpy` (this file's or any transitively-imported
# allostery module's) -- BLAS reads these at first use, not reconfigurable
# after. Found 2026-07-14: two uncapped processes (this script +
# run_challenge.py) run concurrently on a 16-core box each spawned BLAS
# threads across all cores, oversubscribing 2-4x and slowing a 32-cell
# sweep from an observed ~50 min/32-cells (TASK-0101's original single-job
# run) to ~50 min/cell. 4 is not derived from anything -- it is chosen so
# up to 4 concurrent heavy jobs (this repo runs several agent threads
# against the same machine) stay within 16 cores without starving each
# other; override with the env var directly if a caller wants otherwise.
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

# Reuses run_challenge.py's own real fetch/clean/label glue -- not
# reimplemented (this task's own Constraint).
from run_challenge import DEFAULT_CUTOFF, DEFAULT_POCKET_CUTOFF, T_MAX, N_STEPS, _load_apo_holo  # noqa: E402

DEFAULT_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
ALL_OPERATORS = list(_operator_registry())
ALL_PROPAGATORS = ["ctqw", "ground_state"]
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results"


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _cell_path(output_dir: Path, target: str, operator: str, propagator: str) -> Path:
    return output_dir / target / "sweep_cells" / f"{operator}__{propagator}.json"


def _prepare_target(target_name: str):
    """One real fetch/clean/label pass per target per invocation.

    Network fetches are cached by prody's own local PDB cache
    (`pdb_cache/`, already an established gitignored directory in this
    repo) -- multiple invocations against the same target, even from
    separate parallel processes, do not each re-download from RCSB. The
    local clean()/build_labels() CPU cost still re-runs per invocation;
    this is deliberately not cached further -- it is cheap relative to
    the eigendecomposition cost per cell, so a second caching layer here
    would be disproportionate engineering for this task's scope.

    Returns (coords, bfactors, source, pocket_label, floor_scores, cutoff).
    """
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))

    apo, holo = _load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")

    active_site_idx = np.where(labels_obj.active_site)[0]
    if len(active_site_idx) == 0:
        raise RuntimeError(f"{target_name}: no resolvable active-site seed")
    # Single representative seed index -- same TASK-0090 workaround
    # run_challenge.py already documents and uses, kept identical here so
    # this sweep's cells are comparable to the real submission run's own
    # H_new/H10 numbers (same seeding convention).
    source = int(np.sort(active_site_idx)[0])

    floor_scores = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    return apo.coords, apo.bfactors, source, labels_obj.pocket, floor_scores, cutoff


def run_sweep(
    targets: list[str],
    operators: list[str],
    propagators: list[str],
    output_dir: Path,
    force: bool = False,
) -> tuple[list[Path], list[Path]]:
    """Compute and write whatever cells the filters select, skipping
    cells that already exist unless `force`. Returns (written, skipped)
    cell paths. Never raises past a single target or cell -- a
    target-level failure (e.g. no network) skips that target's cells
    entirely and continues to the next target; a cell-level failure is
    already caught inside `operator_sweep` itself and written as an
    error row, not raised here."""
    written: list[Path] = []
    skipped: list[Path] = []

    for target_name in targets:
        pending = [
            (op, prop)
            for op in operators
            for prop in propagators
            if force or not _cell_path(output_dir, target_name, op, prop).exists()
        ]
        if not pending:
            print(f"{target_name}: all requested cells already computed, skipping fetch")
            continue

        _log(f"{target_name}: preparing (fetch + clean + labels)...")
        prep_start = time.monotonic()
        try:
            coords, bfactors, source, pocket_label, floor_scores, cutoff = _prepare_target(target_name)
        except Exception as exc:
            print(f"{target_name}: SKIP (target-level failure): {exc!r}")
            continue
        _log(f"{target_name}: prepared in {time.monotonic() - prep_start:.1f}s -- {len(pending)} cell(s) pending")

        total = len(pending)
        cell_durations: list[float] = []
        for i, (op_name, prop_name) in enumerate(pending, start=1):
            cell_path = _cell_path(output_dir, target_name, op_name, prop_name)
            if cell_path.exists() and not force:
                skipped.append(cell_path)
                continue

            cell_start = time.monotonic()
            rows = operator_sweep(
                coords, bfactors, source, pocket_label, floor_scores,
                cutoff=cutoff, operators=[op_name], propagators=[prop_name],
                t_max=T_MAX, n_steps=N_STEPS,
            )
            duration = time.monotonic() - cell_start
            cell_durations.append(duration)

            row = rows[0]
            cell_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cell_path, "w") as f:
                json.dump(row, f, indent=2)
            written.append(cell_path)

            mean_duration = sum(cell_durations) / len(cell_durations)
            remaining = total - i
            eta = f"{mean_duration * remaining / 60:.0f} min" if remaining else "0 min"
            _log(
                f"[{target_name} {i}/{total}] {op_name} {prop_name}: "
                f"AUC={row['auc']} floor_cleared={row['floor_cleared']} "
                f"diagnosis={row['diagnosis']} err={row['error']} "
                f"-- took {duration:.1f}s, avg {mean_duration:.1f}s/cell, "
                f"ETA {eta} for {remaining} remaining cell(s) in this target"
            )

    return written, skipped


def aggregate(targets: list[str], output_dir: Path) -> dict:
    """Read every `sweep_cells/*.json` file under each target directory
    and render `results/<target>/operator_sweep.md` -- pure table
    assembly, no computation. Missing cells (never run) are shown as
    such, not silently omitted, so a partial sweep's table makes its own
    incompleteness visible."""
    tables: dict[str, str] = {}
    for target_name in targets:
        cells_dir = output_dir / target_name / "sweep_cells"
        rows = []
        for op_name in ALL_OPERATORS:
            for prop_name in ALL_PROPAGATORS:
                cell_path = _cell_path(output_dir, target_name, op_name, prop_name)
                if not cell_path.exists():
                    rows.append({
                        "operator": op_name, "tier": None, "propagator": prop_name,
                        "auc": None, "floor_cleared": None, "diagnosis": "NOT_RUN",
                        "transport_pr": None, "error": None,
                    })
                    continue
                with open(cell_path) as f:
                    rows.append(json.load(f))

        lines = [
            "| operator | tier | propagator | AUC | floor_cleared | diagnosis | transport_pr | error |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for r in rows:
            auc_str = f"{r['auc']:.3f}" if r["auc"] is not None else "-"
            pr_str = f"{r['transport_pr']:.3f}" if r.get("transport_pr") is not None else "-"
            err_str = (r.get("error") or "")[:60]
            lines.append(
                f"| {r['operator']} | {r['tier'] or '-'} | {r['propagator']} | {auc_str} | "
                f"{r['floor_cleared']} | {r['diagnosis'] or '-'} | {pr_str} | {err_str} |"
            )
        table = "\n".join(lines)
        tables[target_name] = table

        out_path = output_dir / target_name / "operator_sweep.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            f.write(f"# Operator sweep -- {target_name}\n\n{table}\n")
        print(f"{target_name}: wrote {out_path} ({len(rows)} rows)")

    return tables


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=None, help="target(s); default: all 3 mandatory targets")
    parser.add_argument("--operator", nargs="+", default=None, help="operator name(s); default: all 16")
    parser.add_argument("--propagator", nargs="+", default=None, help="propagator(s); default: both")
    parser.add_argument("--force", action="store_true", help="recompute selected cells even if already present")
    parser.add_argument("--aggregate", action="store_true", help="render tables from existing cell files; if combined with filters, aggregates after computing")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)

    no_filters = args.target is None and args.operator is None and args.propagator is None
    targets = args.target or DEFAULT_TARGETS
    operators = args.operator or ALL_OPERATORS
    propagators = args.propagator or ALL_PROPAGATORS

    unknown_ops = set(operators) - set(ALL_OPERATORS)
    if unknown_ops:
        print(f"ERROR: unknown operator(s) {sorted(unknown_ops)}; known: {ALL_OPERATORS}")
        return 1

    if not args.aggregate or args.target or args.operator or args.propagator:
        run_sweep(targets, operators, propagators, args.output_dir, force=args.force)

    if args.aggregate or no_filters:
        aggregate(targets, args.output_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
