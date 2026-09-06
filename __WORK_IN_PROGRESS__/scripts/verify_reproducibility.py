#!/usr/bin/env python3
"""TASK-0333 -- asserts, does not eyeball, the one named reproducibility
target this task's own Planned Validation specifies: [[TASK-0318]]'s
residualised-ceiling mean AUC.

Run AFTER `scripts/task0318_input_space_ceiling.py --phase-b-only` (see
`REPRODUCIBILITY.md` for the exact command sequence). Compares the
freshly-written `results/tasks/0318_input_space_ceiling/ceiling_result.json`
against the value committed alongside this script -- exit 0 only on an
exact match to the tolerance below, exit 1 otherwise, with the actual vs
expected values printed either way.

The committed expected value was captured by running this exact check
in a clean venv, built only from `pyproject.toml`'s pinned dependencies
(`requirements-lock.txt` is that venv's own full `pip freeze`), against
the feature cache committed under `results/tasks/0318_input_space_ceiling/
feature_cache/` -- not assumed to reproduce, checked directly before
this script was written.
"""
import json
import sys
from pathlib import Path

EXPECTED = 0.5948718035160693  # TASK-0318's committed headline, to full float precision
TOL = 1e-9  # exact reproduction expected -- not a "close enough" band
RESULT_PATH = Path("results/tasks/0318_input_space_ceiling/ceiling_result.json")


def main() -> int:
    if not RESULT_PATH.exists():
        print(f"FAIL: {RESULT_PATH} does not exist -- run "
              f"scripts/task0318_input_space_ceiling.py --phase-b-only first.")
        return 1
    d = json.loads(RESULT_PATH.read_text())
    actual = d["residual_ceiling"]["mean"]
    diff = abs(actual - EXPECTED)
    ok = diff <= TOL
    print(f"expected : {EXPECTED!r}")
    print(f"actual   : {actual!r}")
    print(f"|diff|   : {diff:.3e}  (tolerance {TOL:.0e})")
    print("RESULT: PASS -- byte-identical reproduction" if ok
          else "RESULT: FAIL -- does not reproduce")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
