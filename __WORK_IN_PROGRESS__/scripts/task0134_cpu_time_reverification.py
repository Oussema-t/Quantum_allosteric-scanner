#!/usr/bin/env python3
"""TASK-0134 Part 1 -- CPU-time re-verification of TASK-0110's
"time_averaged_ctqw did not return after 2+ hours" claim.

TASK-0110's own original observation was a single process-state check
(`R`, "genuinely computing") at the moment it was killed -- proof of
activity at that instant, not proof of continuous execution across the
full elapsed interval. This script instruments the *same* call
(real KRAS_G12C, `H_new`, AAKV-prescribed t_max/n_steps from
`propagators.min_adequate_t_max`/`min_adequate_n_steps`) with
`runlog.RunLogger`'s incremental wall-clock + CPU-time sampling
(TASK-0135's own module, built with this exact question in mind --
see its docstring), reusing `propagators.ctqw`'s private eigh-based
per-step helper directly (not the public `time_averaged_ctqw`, which
has no internal hook) so partial progress can be logged mid-loop.

Deliberately NOT a full reproduction of the original run: this task's
own priority note downgrades Part 1 to "optional/historical-record-only"
since TASK-0130 replaced the finite-time approximation with an exact
closed form for every real call site -- nobody runs the code path this
originally exercised anymore. Also found live, before deciding how to
scope this: `H_new`'s spectrum has changed since TASK-0110's original
measurement (TASK-0121's potential renormalization landed after it) --
the *same* AAKV formula on the *same* target now prescribes ~878K steps,
not the original ~13M. Re-running the literal old scenario is therefore
not even well-defined anymore; this script instead runs a real, bounded
chunk of the *current* prescription with periodic logging, which is
enough to answer the actual question this task cares about (does
CPU-time track wall-clock, or is there a gap consistent with contention/
suspension), without committing an hour+ of session wall-clock to a
now-superseded scenario.

BLAS threads capped to 4, matching `scripts/optuna_parameter_scan.py`'s
own environment (the actual script that produced the original claim) --
an uncapped calibration run this task's own scratch check did first
showed CPU-time ~16x wall-clock (this machine has 16 cores), which is
multithreaded BLAS parallelism, NOT contention -- a real methodological
finding in its own right (see this task's own Done section).
"""
from __future__ import annotations

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
from allostery.labels import build_labels  # noqa: E402
from allostery.propagators import (  # noqa: E402
    _ctqw_mixture_from_eigh,
    min_adequate_n_steps,
    min_adequate_t_max,
)
from allostery.runlog import RunLogger  # noqa: E402

import run_challenge  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0134_cpu_time"
TARGET_NAME = "KRAS_G12C"
# Bounded window, not the full ~878K-step prescription (would take
# ~50min at the calibrated rate below) -- this task's own Part 1 is
# downgraded to optional/historical, so a real, sustained multi-minute
# window with periodic sampling is proportionate; see module docstring.
SAMPLE_EVERY = 2000  # steps between RunLogger.step() calls
# A first bounded 60,000-step calibration run (thread-capped to 4, matching
# the original TASK-0110 script's own environment) measured a stable
# ~960 steps/s -- the full ~878K-step prescription is feasible in
# ~15min at that rate, not the hours a naive extrapolation from the
# uncapped (16-thread) calibration would have suggested. Uncapped:
# run to completion, not a bound -- this task's own Constraint requires
# reaching a real conclusion, not truncating early.
MAX_STEPS_TO_RUN = 10_000_000


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main() -> int:
    target_config = load_target_config(TARGET_NAME)
    cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(TARGET_NAME, target_config)
    H = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    source = np.sort(np.where(labels_obj.active_site)[0])

    t_max = min_adequate_t_max(H, kind="time_averaged_ctqw")
    n_steps_prescribed = min_adequate_n_steps(H, t_max)
    _log(f"N={H.shape[0]} t_max={t_max:.6g} n_steps_prescribed={n_steps_prescribed} "
         f"(TASK-0110's own original run needed ~1.3e7 on this same target/formula -- "
         f"see this task's Done section for the discrepancy)")

    n_run = min(MAX_STEPS_TO_RUN, n_steps_prescribed)
    _log(f"running a bounded {n_run}-step chunk of the {n_steps_prescribed}-step full "
         f"prescription, sampled every {SAMPLE_EVERY} steps")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log = RunLogger(
        OUTPUT_DIR / "cpu_time_reverification.jsonl",
        run_name="task0134_part1_reverification",
        extra={
            "target": TARGET_NAME, "N": int(H.shape[0]), "t_max": t_max,
            "n_steps_prescribed": int(n_steps_prescribed), "n_steps_run": int(n_run),
            "sample_every": SAMPLE_EVERY,
        },
    )

    w, v = np.linalg.eigh(H)
    times = np.linspace(0.0, t_max, n_steps_prescribed)[:n_run]
    acc = np.zeros(H.shape[0])
    t0_wall = time.monotonic()
    for i, t in enumerate(times):
        acc += _ctqw_mixture_from_eigh(w, v, t, source)
        if (i + 1) % SAMPLE_EVERY == 0:
            log.step(f"step_{i + 1}", steps_done=i + 1, steps_total=int(n_steps_prescribed))
            _log(f"{i + 1}/{n_run} steps -- wall={time.monotonic() - t0_wall:.1f}s")

    log.finish(steps_done=int(n_run), steps_total=int(n_steps_prescribed), completed_full_prescription=bool(n_run >= n_steps_prescribed))
    _log(f"done -- wrote {OUTPUT_DIR / 'cpu_time_reverification.jsonl'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
