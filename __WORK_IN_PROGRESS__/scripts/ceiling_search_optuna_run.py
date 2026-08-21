#!/usr/bin/env python3
"""TASK-0116 -- real-target driver for `ceiling.ceiling_search_optuna`
(the TPE strategy-upgrade companion to `ceiling_search`'s blind random
search), over the corrected `sum(lam_i) <= 0.4` parameter space.

Reuses `ceiling_search_batched.py`'s own apo-loading recipe (apo-only,
holo unused -- matches TASK-0046's own KRAS_G12C cross-check scope).
Not checkpointed (unlike the batched random-search script): a TPE study
runs a single `optuna.Study.optimize` call end-to-end, so there is no
natural per-trial resume point the way independent random draws have.

Run: python3 scripts/ceiling_search_optuna_run.py --target KRAS_G12C \
       --n-trials 60 --seed 7
Output: __WORK_IN_PROGRESS__/results/tasks/0116/<target>/optuna_ceiling.json
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

from allostery.ceiling import ceiling_search_optuna  # noqa: E402
from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.labels import build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0116"


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _load_apo(target_name: str, target_config: dict):
    """Identical recipe to `ceiling_search_batched.py::_load_apo` -- not
    imported from there to avoid a scripts-importing-scripts dependency;
    kept in sync deliberately, same discipline as that script's own
    apo-only-ceiling framing."""
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


def run(target_name: str, n_trials: int, seed: int, output_dir: Path, coherent: bool = False) -> dict:
    """`coherent=False` default matches TASK-0118/INV-0006's declared
    convention, same as `ceiling_search_batched.py::run`'s own default."""
    target_config = load_target_config(target_name)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", 4.5))

    _log(f"{target_name}: fetching + cleaning apo (holo unused, apo-only ceiling per TASK-0046)...")
    t0 = time.monotonic()
    apo, holo = _load_apo(target_name, target_config)
    _log(f"{target_name}: apo ready in {time.monotonic() - t0:.1f}s (N={len(apo.resnums)})")

    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label, cannot run a ceiling search")
    source = np.where(labels_obj.active_site)[0]
    if len(source) == 0:
        raise RuntimeError(f"{target_name}: empty active_site mask")

    _log(f"{target_name}: running {n_trials} TPE trials (seed={seed}, coherent={coherent})...")
    t0 = time.monotonic()
    out = ceiling_search_optuna(
        target_name, apo.coords, apo.bfactors, source, labels_obj.pocket,
        n_trials=n_trials, seed=seed, coherent=coherent,
    )
    elapsed = time.monotonic() - t0
    _log(f"{target_name}: done in {elapsed:.1f}s -- best S={out['best']['S']:.4f} "
         f"auc_apo={out['best']['auc_apo']:.4f} ({out['n_trials_scored']}/{out['n_trials_run']} scored)")

    target_dir = output_dir / target_name
    target_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "target": target_name,
        "n_trials": n_trials,
        "seed": seed,
        "coherent": coherent,
        "elapsed_s": round(elapsed, 1),
        "best": out["best"],
        "n_trials_scored": out["n_trials_scored"],
    }
    # seed in the filename: a second confirmatory run at a different seed
    # (this task's own Planned Validation) must not silently overwrite the
    # first -- found the hard way running this script's own seed=7 then
    # seed=42 confirmatory pair back to back.
    with open(target_dir / f"optuna_ceiling_seed{seed}.json", "w") as f:
        json.dump(record, f, indent=2)
    return record


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--n-trials", type=int, default=60)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--coherent", action="store_true", default=False)
    args = parser.parse_args(argv)

    run(args.target, args.n_trials, args.seed, args.output_dir, coherent=args.coherent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
