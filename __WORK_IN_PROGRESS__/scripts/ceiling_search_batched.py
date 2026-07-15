#!/usr/bin/env python3
"""TASK-0082 -- checkpointed, resumable ceiling search for targets where a
full 60-trial `ceiling.ceiling_search` run is too expensive for one sitting
(BCR_ABL1: N=451, ~14h estimated at 60 trials; extrapolated from
TASK-0046's real KRAS_G12C timing, ~44s/trial at N=169, scaled by the
dominant O(N^3) eigendecomposition cost -- (451/169)^3 ~= 19x).

Each trial is appended to a JSONL checkpoint file **immediately** after it
completes (success or failure), not batched in memory -- a crash mid-run
loses at most the one in-flight trial, never previously-completed ones.
Re-running this script (same `--target`/`--seed`/`--n-trials`) is always
safe: it reads how many trials are already checkpointed and only computes
the remainder, replaying (not recomputing physics for) the RNG draws
already consumed so the parameter sequence stays bit-identical to a single
non-batched `ceiling_search(..., seed=seed)` call of the same total trial
count. Running it again after completion is a no-op that just reports the
existing best.

Run: python3 scripts/ceiling_search_batched.py --target BCR_ABL1 \
       --n-trials 60 --batch-size 5 --seed 7
Checkpoint: __WORK_IN_PROGRESS__/results_task0082/<target>/ceiling_trials.jsonl
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

from allostery.ceiling import consistency_score, sample_params  # noqa: E402
from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.labels import build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402
from allostery.protocol import ceiling_context  # noqa: E402

DEFAULT_CHECKPOINT_DIR = Path(__file__).resolve().parent.parent / "results_task0082"
T_MAX = 15.0
N_STEPS = 500


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _load_apo(target_name: str, target_config: dict):
    """apo-only load (this search does not use holo -- TASK-0046's own
    scope; matches its real KRAS_G12C cross-check, which was apo-only)."""
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


def _read_checkpoint(path: Path) -> list:
    if not path.exists():
        return []
    trials = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                trials.append(json.loads(line))
    return trials


def _append_checkpoint(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")
        f.flush()
        os.fsync(f.fileno())


def run(target_name: str, n_trials: int, batch_size: int, seed: int, checkpoint_dir: Path) -> dict:
    target_config = load_target_config(target_name)
    cutoff_cfg = float(target_config.get("enm_cutoff", 10.0))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", 4.5))

    checkpoint_path = checkpoint_dir / target_name / "ceiling_trials.jsonl"
    completed = _read_checkpoint(checkpoint_path)
    _log(f"{target_name}: {len(completed)}/{n_trials} trials already checkpointed at {checkpoint_path}")

    if len(completed) >= n_trials:
        scored = [t for t in completed if t.get("S") is not None and np.isfinite(t["S"])]
        best = max(scored, key=lambda t: t["S"]) if scored else None
        _log(f"{target_name}: already complete, no recomputation. best={best}")
        return {"target": target_name, "best": best, "n_trials_run": len(completed), "checkpoint_path": str(checkpoint_path)}

    _log(f"{target_name}: fetching + cleaning apo (holo unused, apo-only ceiling per TASK-0046)...")
    t0 = time.monotonic()
    apo, _holo = _load_apo(target_name, target_config)
    _log(f"{target_name}: apo ready in {time.monotonic() - t0:.1f}s (N={len(apo.resnums)})")

    labels_obj = build_labels(apo, _holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label, cannot run a ceiling search")
    source = np.where(labels_obj.active_site)[0]
    if len(source) == 0:
        raise RuntimeError(f"{target_name}: empty active_site mask")

    # Fast-forward the RNG past already-completed trials -- cheap (just RNG
    # draws, no physics) -- so the resumed parameter sequence is identical
    # to what a single, non-batched, same-seed run would have drawn.
    rng = np.random.default_rng(seed)
    for _ in range(len(completed)):
        sample_params(rng)

    remaining = n_trials - len(completed)
    this_batch = min(batch_size, remaining)
    _log(f"{target_name}: running {this_batch} trial(s) this invocation "
         f"({remaining} remaining of {n_trials} total)...")

    with ceiling_context():
        for i in range(this_batch):
            trial_idx = len(completed) + i
            params = sample_params(rng)
            t0 = time.monotonic()
            try:
                result = consistency_score(
                    apo.coords, apo.bfactors, source, labels_obj.pocket, params,
                    t_max=T_MAX, n_steps=N_STEPS,
                )
                elapsed = time.monotonic() - t0
                record = {"trial": trial_idx, "elapsed_s": round(elapsed, 1), **result}
                _log(f"{target_name}: trial {trial_idx} done in {elapsed:.1f}s -- S={result['S']:.4f} AUC_apo={result['auc_apo']:.4f}")
            except Exception as exc:
                elapsed = time.monotonic() - t0
                record = {"trial": trial_idx, "elapsed_s": round(elapsed, 1), "S": None, "error": repr(exc), "params": params}
                _log(f"{target_name}: trial {trial_idx} FAILED after {elapsed:.1f}s -- {exc!r}")
            _append_checkpoint(checkpoint_path, record)

    completed = _read_checkpoint(checkpoint_path)
    scored = [t for t in completed if t.get("S") is not None and np.isfinite(t["S"])]
    best = max(scored, key=lambda t: t["S"]) if scored else None
    _log(f"{target_name}: batch done. {len(completed)}/{n_trials} total trials checkpointed. "
         f"best so far: S={best['S']:.4f} params={best['params']}" if best else f"{target_name}: no successful trials yet")
    return {"target": target_name, "best": best, "n_trials_run": len(completed), "checkpoint_path": str(checkpoint_path)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", required=True)
    parser.add_argument("--n-trials", type=int, default=60)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--checkpoint-dir", type=Path, default=DEFAULT_CHECKPOINT_DIR)
    args = parser.parse_args(argv)

    run(args.target, args.n_trials, args.batch_size, args.seed, args.checkpoint_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
