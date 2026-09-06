#!/usr/bin/env python3
"""TASK-0333 -- runs the one named reproducibility target end to end and
emits STRUCTURED (JSON-lines) logs for it, without touching
`task0318_input_space_ceiling.py` itself: this task's own Constraint is
packaging, not science, and the safest way to honor "don't fix a
reproducibility gap by adjusting the pipeline" is to not edit the
pipeline script at all, even for logging. This wraps it externally
instead -- same subprocess a human would run by hand, captured.

Emits one JSON object per line to
`results/tasks/0318_input_space_ceiling/run_log.jsonl`:
  - {"event": "start", ...}       -- command, env, timestamp
  - {"event": "stdout", "line": ...}  -- one per line of the wrapped run's output
  - {"event": "result", ...}      -- parsed residual_ceiling.mean + verify verdict
  - {"event": "end", ...}         -- exit code, wall time

Run: python3 scripts/run_reproducible_headline.py
(equivalent by hand: PYTHONHASHSEED=0 python3 scripts/task0318_input_space_ceiling.py --phase-b-only
 followed by: python3 scripts/verify_reproducibility.py)
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

OUT = Path("results/tasks/0318_input_space_ceiling")
LOG_PATH = OUT / "run_log.jsonl"


def emit(fh, **fields):
    fields.setdefault("ts", time.time())
    fh.write(json.dumps(fields) + "\n")
    fh.flush()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"  # TASK-0333's own seeding convention, set explicitly, not inherited
    cmd = [sys.executable, "scripts/task0318_input_space_ceiling.py", "--phase-b-only"]

    with open(LOG_PATH, "w") as fh:
        emit(fh, event="start", cmd=cmd, python=sys.executable,
             python_version=sys.version, PYTHONHASHSEED=env["PYTHONHASHSEED"], cwd=os.getcwd())
        t0 = time.monotonic()
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in proc.stdout:
            print(line, end="")
            emit(fh, event="stdout", line=line.rstrip("\n"))
        proc.wait()
        dt = time.monotonic() - t0
        emit(fh, event="pipeline_exit", returncode=proc.returncode, wall_seconds=round(dt, 1))

        if proc.returncode != 0:
            emit(fh, event="end", ok=False, reason="pipeline exited non-zero")
            return proc.returncode

        result_path = OUT / "ceiling_result.json"
        residual_mean = None
        if result_path.exists():
            residual_mean = json.loads(result_path.read_text())["residual_ceiling"]["mean"]
        emit(fh, event="result", residual_ceiling_mean=residual_mean)

        verify = subprocess.run([sys.executable, "scripts/verify_reproducibility.py"],
                                capture_output=True, text=True)
        print(verify.stdout, end="")
        emit(fh, event="verify", returncode=verify.returncode, stdout=verify.stdout.strip())
        emit(fh, event="end", ok=(verify.returncode == 0), wall_seconds=round(dt, 1))
        print(f"\nstructured log written -> {LOG_PATH}")
        return verify.returncode


if __name__ == "__main__":
    sys.exit(main())
