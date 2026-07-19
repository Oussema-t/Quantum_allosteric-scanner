#!/usr/bin/env python3
"""TASK-0135 Part 1(a) -- real, logged reproducibility audit of `H_new`'s
spectral gap on BCR_ABL1, the one headline quantity with a confirmed
historical discrepancy (INV-0008: 0.0374 vs. 0.1933).

Re-runs the same computation (fresh RCSB fetch each time -- not a cached
object) multiple times, in fresh processes, and reports whether the
result reproduces exactly. Adopts `runlog.RunLogger` (TASK-0135 Part 2)
for its own environment fingerprint + per-run wall/CPU timing, rather
than the ad-hoc `print(f"[{time.strftime(...)}] ...")` pattern duplicated
across ~10 other scripts in this directory.

Run: python3 scripts/reproducibility_audit.py --target BCR_ABL1 --repeats 3
Output: __WORK_IN_PROGRESS__/results_task0135/<target>/spectral_gap_audit.jsonl
"""
from __future__ import annotations

import argparse
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

from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.runlog import RunLogger  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo, not re-derived

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0135"


def spectral_gap_once(target_name: str) -> dict:
    """One fresh, independent computation: fetch + clean apo, build
    `H_new` at current defaults, compute the gap between the two smallest
    non-negative eigenvalues -- `metrics.spectral_gap`'s own definition,
    not re-derived."""
    target_config = load_target_config(target_name)
    apo, _holo = run_challenge._load_apo_holo(target_name, target_config)
    cutoff = float(target_config.get("enm_cutoff", 10.0))
    H = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    w = np.linalg.eigvalsh(H)
    pos = w[w >= -1e-10]
    gap = float(pos[1] - pos[0])
    return {"N": len(apo.coords), "cutoff": cutoff, "gap": gap}


def run(target_name: str, repeats: int, output_dir: Path) -> list:
    target_dir = output_dir / target_name
    log = RunLogger(
        target_dir / "spectral_gap_audit.jsonl",
        run_name=f"spectral_gap_repro_{target_name}",
        extra={"repeats": repeats},
    )
    results = []
    for i in range(repeats):
        t0 = time.monotonic()
        result = spectral_gap_once(target_name)
        elapsed = time.monotonic() - t0
        print(f"[{time.strftime('%H:%M:%S')}] repeat {i}: gap={result['gap']!r} ({elapsed:.1f}s)", flush=True)
        log.step(f"repeat_{i}", elapsed_s=round(elapsed, 2), **result)
        results.append(result)

    gaps = [r["gap"] for r in results]
    identical = len(set(gaps)) == 1
    spread = max(gaps) - min(gaps) if len(gaps) > 1 else 0.0
    log.finish(identical=identical, spread=spread, gaps=gaps)
    print(f"[{time.strftime('%H:%M:%S')}] {target_name}: {'IDENTICAL' if identical else 'DIFFERS'} "
          f"across {repeats} repeats -- spread={spread!r}", flush=True)
    return results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="BCR_ABL1")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)

    run(args.target, args.repeats, args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
