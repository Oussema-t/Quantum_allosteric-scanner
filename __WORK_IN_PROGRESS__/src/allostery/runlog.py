"""TASK-0135: shared run-logging convention -- environment fingerprint +
incremental per-step JSONL logging with wall-clock AND CPU-time.

Motivation, two coupled gaps found on the same day (2026-07-18):
1. INV-0008 -- does a fixed, seeded computation give the same numeric
   output across repeated invocations in this environment? Answering
   this for any future discrepancy needs an environment fingerprint
   recorded *at the time each run happened*, not reconstructed after the
   fact from memory.
2. P-0005/TASK-0134 -- "did not return within N wall-clock hours" is not
   evidence of computational infeasibility by itself; only CPU-seconds
   consumed is. `RunLogger.step()` records both every time it's called,
   not just a final summary, so a partially-completed or killed run still
   leaves a usable trace (same discipline `ceiling_search_batched.py`'s
   own JSONL checkpoint file already established for a different reason
   -- one line per step, flushed and fsync'd immediately).

Not a new checkpoint/resume mechanism -- scripts that need resumability
(like `ceiling_search_batched.py`) keep their own checkpoint format; this
module is for the diagnostic trace (environment + timing) any script can
emit alongside whatever it already does, real or checkpointed.
"""
from __future__ import annotations

import json
import os
import platform
import socket
import sys
import time
from pathlib import Path
from typing import Any, Optional, Union

_VERSIONED_MODULES = ("numpy", "scipy", "optuna")
_THREAD_ENV_VARS = (
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
)


def environment_fingerprint() -> dict:
    """One-shot snapshot of everything that could plausibly explain a
    run-to-run numerical or timing difference: BLAS thread env vars
    (this project's own existing thread-capping precedent in
    `run_challenge.py`/`sweep_operators.py`), hostname, PID, key library
    versions, python version, wall-clock timestamp.

    Deliberately does NOT attempt to fingerprint CPU model/core count or
    concurrent host load at call time -- those are real candidate causes
    too (TASK-0111's own prior finding) but are not reliably introspectable
    from inside a sandboxed process the same way env vars and versions
    are; `RunLogger`'s own per-step CPU-vs-wall-clock timing is the
    diagnostic for contention, not this function.
    """
    thread_env = {var: os.environ.get(var) for var in _THREAD_ENV_VARS}
    versions = {"python": sys.version.split()[0]}
    for mod_name in _VERSIONED_MODULES:
        try:
            mod = __import__(mod_name)
            versions[mod_name] = getattr(mod, "__version__", "unknown")
        except ImportError:
            versions[mod_name] = None
    return {
        "hostname": socket.gethostname(),
        "pid": os.getpid(),
        "platform": platform.platform(),
        "thread_env": thread_env,
        "versions": versions,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


class RunLogger:
    """Incremental JSONL run logger -- one line per step, flushed and
    fsync'd immediately.

    Usage::

        log = RunLogger("results/tasks/XXXX/run.jsonl", run_name="my_search")
        for i, trial in enumerate(trials):
            ... do work ...
            log.step(f"trial_{i}", value=trial_value)
        log.finish(best=best_value)

    Each record includes `wall_elapsed_s` (`time.monotonic()`-based) and
    `cpu_elapsed_s` (`time.process_time()`-based, this *process's* CPU
    time only) since the logger was constructed -- a large, growing gap
    between the two across steps is direct evidence of contention or
    suspension during the run (P-0005), not just a slow computation.
    """

    def __init__(self, path: Union[str, Path], run_name: str, extra: Optional[dict] = None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._wall_start = time.monotonic()
        self._cpu_start = time.process_time()
        header: dict = {
            "event": "run_start",
            "run_name": run_name,
            "environment": environment_fingerprint(),
        }
        if extra:
            header["extra"] = extra
        self._write(header)

    def step(self, label: str, **fields: Any) -> None:
        record = {
            "event": "step",
            "label": label,
            "wall_elapsed_s": round(time.monotonic() - self._wall_start, 3),
            "cpu_elapsed_s": round(time.process_time() - self._cpu_start, 3),
            **fields,
        }
        self._write(record)

    def finish(self, **fields: Any) -> None:
        record = {
            "event": "run_finish",
            "wall_elapsed_s": round(time.monotonic() - self._wall_start, 3),
            "cpu_elapsed_s": round(time.process_time() - self._cpu_start, 3),
            **fields,
        }
        self._write(record)

    def _write(self, record: dict) -> None:
        with open(self.path, "a") as f:
            f.write(json.dumps(record) + "\n")
            f.flush()
            os.fsync(f.fileno())
