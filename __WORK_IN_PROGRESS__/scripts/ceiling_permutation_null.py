#!/usr/bin/env python3
"""TASK-0131 -- permutation null for the ceiling search.

`ceiling.ceiling_search` reports the **maximum** AUC over 60 blind random
draws against the real pocket label, and `COMPETENCE_MAP.md` reads
"ceiling clears floor" as evidence of real headroom in `H_new`'s
physical-scalar space -- the document's only nonnegative claim. A maximum
over K noisy draws is upward-biased by construction (the winner's curse),
independent of whether real signal exists. This script runs the identical
60-trial search protocol against **permuted** pocket labels (same pocket
*size* per target, shuffled identity) to measure what pure noise produces
under this exact procedure, so every real margin can be read as a
percentile of that null rather than assumed significant.

**Which procedure is "the identical search protocol" (Implementer's call,
stated here per this task's own convention for such calls)**: the task
file names `ceiling_search_batched.py` (T_max=15, N_steps=500 finite-time
convention) because that was the shipped procedure when this task was
filed (`REVIEW-panel-2026-07-17.md`, before TASK-0130 landed). TASK-0130
(2026-07-18) replaced that finite-time approximation with `time_averaged_
ctqw`'s exact closed form for every headline "ctqw" number, including the
ceiling -- the real margins this task nulls (+73.7%/-64.5%/-173.0%,
`results_task0130_competence/closed_form_competence.json`) were produced
by `ceiling.ceiling_search(use_converged_limit=True)`, not the old finite-
time script. Per this task's own Dependency note ("the null should
ultimately be reported against whichever headline numbers are current at
submission time"), this script uses `ceiling_search(use_converged_
limit=True, coherent=False)` -- the actual procedure that produced the
numbers being tested. Using the old finite-time script here would null a
different statistic than the one being reported (apples-to-oranges), not
a stricter or more faithful reproduction of "the shipped procedure."

TASK-0116 (ceiling search coverage / `_PARAM_RANGES` correction) already
landed before this task started -- `sample_params` is already the
corrected, single, current version. There is no separate "old ranges"
null to run in addition (the task's own conditional item is moot, not
skipped).

**Null construction**: for each replicate, `apo_pocket` is replaced by a
uniformly random subset of residues of the *same size* as the real
pocket (shuffled identity, fixed cardinality -- the Constraint this task
names). `apo_source` (the active-site seed) is left real/unchanged --
only the label being searched against is permuted, isolating the
winner's-curse bias in the *search procedure itself* from any question
about the seed. Both the null floor (max of the 3 baseline AUCs against
the *same* permuted label) and the null ceiling (60-trial search against
the same permuted label) are computed per replicate, so the reported null
is of the actual statistic COMPETENCE_MAP.md cites -- ceiling-minus-floor
margin -- not of the ceiling AUC alone.

Parallelized across replicates (each fully independent) via
`multiprocessing.Pool` -- CARDIAC_MYOSIN's real ceiling_search costs
~87s/replicate serially (TASK-0130's own measurement), making 200
replicates ~4.8h serial; each worker pins BLAS to 1 thread to avoid
oversubscription across the pool.
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

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0131_permutation_null"
CEILING_N_TRIALS = 60
N_REPLICATES_DEFAULT = 200


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _worker_init() -> None:
    """Pin BLAS to 1 thread per worker process -- with N worker processes
    on a 16-core box, letting each also spawn 4 BLAS threads (this
    module's own top-level default, meant for a single serial run)
    would oversubscribe by up to 4x."""
    for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[_v] = "1"


def _prepare_target(target_name: str):
    from allostery.clean import load_target_config
    from allostery.labels import build_labels

    import run_challenge

    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")
    source = np.sort(np.where(labels_obj.active_site)[0])
    if len(source) == 0:
        raise RuntimeError(f"{target_name}: empty active-site seed")

    return {
        "coords": apo.coords, "bfactors": apo.bfactors, "source": source,
        "n_residues": len(apo.resnums), "pocket_size": int(labels_obj.pocket.sum()),
        "cutoff": cutoff,
    }


def _run_one_replicate(args: tuple) -> dict:
    """One full null replicate: permute the pocket label, compute null
    floor + null ceiling (60-trial search) against it. Module-level
    function (not a closure/lambda) -- required for `multiprocessing.
    Pool.map` picklability."""
    target_name, replicate_idx, coords, bfactors, source, n_residues, pocket_size, cutoff, perm_seed, search_seed = args

    from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed
    from allostery.ceiling import ceiling_search
    from allostery.metrics import auc as _auc

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

    t0 = time.monotonic()
    result = ceiling_search(
        target_name, coords, bfactors, source, permuted_pocket,
        n_trials=CEILING_N_TRIALS, seed=int(search_seed), coherent=False,
        use_converged_limit=True,
    )
    ceiling_null = float(result["best"]["auc_apo"])
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

    # Independent, reproducible per-replicate seed streams (permutation draw
    # and the search's own internal RNG are seeded separately, both derived
    # from one master SeedSequence per target so a re-run is deterministic).
    ss = np.random.SeedSequence([base_seed, hash(target_name) & 0xFFFFFFFF])
    perm_seeds, search_seeds = ss.spawn(2)
    perm_seed_list = perm_seeds.generate_state(n_replicates)
    search_seed_list = search_seeds.generate_state(n_replicates)

    tasks = [
        (
            target_name, i, prep["coords"], prep["bfactors"], prep["source"],
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
                    _log(f"{target_name}: {i+1}/{n_replicates} replicates done so far...")
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
    parser.add_argument("--base-seed", type=int, default=131)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "permutation_null.json")
    args = parser.parse_args(argv)

    all_results = {}
    for name in args.target:
        try:
            all_results[name] = run_target(name, args.n_replicates, args.workers, args.base_seed)
        except Exception as exc:
            all_results[name] = {"error": str(exc)}
            _log(f"{name}: FAILED -- {exc!r}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(all_results, f, indent=2)
    _log(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
