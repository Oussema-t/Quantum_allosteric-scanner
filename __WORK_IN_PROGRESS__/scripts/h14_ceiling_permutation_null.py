#!/usr/bin/env python3
"""TASK-0138 -- permutation null for H14_anm_pinv_trace's ceiling search.

TASK-0126 found, incidentally, that `H14_anm_pinv_trace`'s cutoff-only
ceiling search beats `H_new`'s own TASK-0130 closed-form ceiling on
BCR_ABL1 (+0.0503) -- not on KRAS_G12C or CARDIAC_MYOSIN under the same
convention (see that task's own committed Done section; an earlier
in-session draft of TASK-0126, computed under the since-superseded
TASK-0129 finite-`t_max` convention, had reported H14 beating `H_new` on
all 3 targets -- not what actually landed). Before this BCR_ABL1 margin
informs anything, `TASK-0131`'s own precedent applies here too: a
**maximum** over 60 blind random `cutoff` draws is upward-biased by
construction (the winner's curse), independent of whether real signal
exists. This script runs H14's identical 60-trial cutoff-only search
protocol against permuted pocket labels to measure what pure noise
produces under this exact procedure.

**Reuses TASK-0131's own null-construction methodology, not a new
convention** (per this task's own In Scope instruction: "do not invent a
second, incompatible null-testing convention"): permuted pocket is a
uniformly random subset of residues of the *same size* as the real
pocket (shuffled identity, fixed cardinality); `source` (active site) is
left real/unchanged, isolating the search procedure's own bias from any
seed question; both null floor (max of the 3 baseline AUCs against the
permuted label) and null ceiling (H14's own 60-trial `cutoff_only_
ceiling_search`) are computed per replicate, against the actual
ceiling-minus-floor margin statistic `COMPETENCE_MAP.md`/TASK-0126 cite,
not the ceiling AUC alone.

**Not a literal call into TASK-0131's own script**: that script nulls
`ceiling.ceiling_search`'s 8-dimensional `H_new` search specifically;
H14 goes through TASK-0126's own `h13_ceiling_comparison.
cutoff_only_ceiling_search` (a 1-dimensional `cutoff`-only search) --
structurally different search spaces, so this is a *compatible* null
(same construction, statistics, and reporting), imported from that
module rather than duplicated by hand.

Parallelized across replicates via `multiprocessing.Pool`, same
BLAS-pinning discipline as TASK-0131's own script (each worker pinned to
1 BLAS thread to avoid oversubscription across the pool).
"""
from __future__ import annotations

import argparse
import json
import multiprocessing
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

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0138_h14_permutation_null"
CEILING_N_TRIALS = 60
N_REPLICATES_DEFAULT = 200


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _worker_init() -> None:
    for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[_v] = "1"


def _prepare_target(target_name: str):
    from h13_ceiling_comparison import _prepare_target as _prep

    apo, labels_obj, source, floor, cutoff = _prep(target_name)
    return {
        "coords": apo.coords, "source": source,
        "n_residues": len(apo.resnums), "pocket_size": int(labels_obj.pocket.sum()),
        "cutoff": cutoff,
    }


def _run_one_replicate(args: tuple) -> dict:
    """Module-level function (not a closure) -- required for
    `multiprocessing.Pool.map` picklability."""
    target_name, replicate_idx, coords, source, n_residues, pocket_size, cutoff, perm_seed, search_seed = args

    from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed
    from allostery.hamiltonians import H14_anm_pinv_trace
    from allostery.metrics import auc as _auc
    from allostery.propagators import time_averaged_ctqw_converged
    from h13_ceiling_comparison import cutoff_only_ceiling_search

    perm_rng = np.random.default_rng(perm_seed)
    permuted_idx = perm_rng.choice(n_residues, size=pocket_size, replace=False)
    permuted_pocket = np.zeros(n_residues, dtype=bool)
    permuted_pocket[permuted_idx] = True
    pocket_int = permuted_pocket.astype(int)

    floor_candidates = [
        degree_centrality(coords, cutoff=cutoff),
        euclid_from_seed_centroid(coords, source),
        hop_from_seed(coords, source, cutoff=cutoff),
    ]
    floor_null = float(max(_auc(f, pocket_int) for f in floor_candidates))

    def _score_h14(H):
        occ = time_averaged_ctqw_converged(H, source=source, coherent=False)
        return _auc(occ, pocket_int)

    t0 = time.monotonic()
    result = cutoff_only_ceiling_search(
        lambda c: H14_anm_pinv_trace(coords, cutoff=c), _score_h14, cutoff,
        n_trials=CEILING_N_TRIALS, seed=int(search_seed),
    )
    ceiling_null = float(result["best"]["auc"])
    elapsed = time.monotonic() - t0

    return {
        "replicate": replicate_idx, "floor_null": floor_null, "ceiling_null": ceiling_null,
        "margin_null": ceiling_null - floor_null, "elapsed_s": round(elapsed, 1),
    }


def run_target(target_name: str, n_replicates: int, workers: int, base_seed: int) -> dict:
    _log(f"{target_name}: preparing (fetch + clean + labels)...")
    prep = _prepare_target(target_name)
    _log(
        f"{target_name}: N={prep['n_residues']} pocket_size={prep['pocket_size']} "
        f"n_seed={len(prep['source'])} -- running {n_replicates} null replicates "
        f"({CEILING_N_TRIALS} trials each) across {workers} worker(s)"
    )

    ss = np.random.SeedSequence([base_seed, hash(target_name) & 0xFFFFFFFF])
    perm_seeds, search_seeds = ss.spawn(2)
    perm_seed_list = perm_seeds.generate_state(n_replicates)
    search_seed_list = search_seeds.generate_state(n_replicates)

    tasks = [
        (
            target_name, i, prep["coords"], prep["source"],
            prep["n_residues"], prep["pocket_size"], prep["cutoff"],
            int(perm_seed_list[i]), int(search_seed_list[i]),
        )
        for i in range(n_replicates)
    ]

    t0 = time.monotonic()
    results = []
    if workers <= 1:
        for i, t in enumerate(tasks):
            r = _run_one_replicate(t)
            results.append(r)
            if (i + 1) % 10 == 0 or i == 0:
                _log(f"{target_name}: replicate {i+1}/{n_replicates} done, margin_null={r['margin_null']:.4f}")
    else:
        with multiprocessing.Pool(processes=workers, initializer=_worker_init) as pool:
            for i, r in enumerate(pool.imap_unordered(_run_one_replicate, tasks, chunksize=1)):
                results.append(r)
                if (i + 1) % 10 == 0 or i == 0:
                    elapsed_so_far = time.monotonic() - t0
                    _log(f"{target_name}: {i+1}/{n_replicates} replicates done ({elapsed_so_far:.0f}s elapsed, "
                         f"~{elapsed_so_far/(i+1)*(n_replicates-i-1):.0f}s remaining)")
    elapsed = time.monotonic() - t0
    _log(f"{target_name}: all {n_replicates} replicates done in {elapsed:.1f}s")

    margins = np.array([r["margin_null"] for r in results])
    return {
        "target": target_name,
        "n_residues": prep["n_residues"],
        "pocket_size": prep["pocket_size"],
        "n_replicates": n_replicates,
        "n_trials_per_replicate": CEILING_N_TRIALS,
        "null_margin_median": float(np.median(margins)),
        "null_margin_sd": float(np.std(margins)),
        "null_margin_max": float(np.max(margins)),
        "null_margin_min": float(np.min(margins)),
        "replicates": results,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"])
    parser.add_argument("--n-replicates", type=int, default=N_REPLICATES_DEFAULT)
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument("--base-seed", type=int, default=138)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "permutation_null.json")
    args = parser.parse_args(argv)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    all_results = {}
    if args.output.exists():
        with open(args.output) as f:
            all_results = json.load(f)
        _log(f"loaded {len(all_results)} existing target(s) from {args.output} -- merging, not overwriting")

    for name in args.target:
        try:
            all_results[name] = run_target(name, args.n_replicates, args.workers, args.base_seed)
        except Exception as exc:
            all_results[name] = {"error": str(exc)}
            _log(f"{name}: FAILED -- {exc!r}")

        # Write after every target, not just at the end -- a long multi-target
        # run (CARDIAC_MYOSIN alone can run for hours) must not lose already-
        # completed targets' results if a later target is killed/interrupted.
        with open(args.output, "w") as f:
            json.dump(all_results, f, indent=2)
        _log(f"{name}: wrote checkpoint to {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
