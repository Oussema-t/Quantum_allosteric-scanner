#!/usr/bin/env python3
"""Whitelisted pytest runner: named presets only, no free-form pytest args.

Built for TASK-0026.004 (`repo.test.pytest-local` in CAPABILITIES.md) so any
thread that just touched `backend/` or `__WORK_IN_PROGRESS__/src/allostery/`
can get a real pass/fail answer without reconstructing pytest CLI flags each
time and without hitting a permission prompt for an ad hoc `python3 -m
pytest ...` invocation. A thread picks a preset name; it cannot smuggle
arbitrary pytest/shell arguments through this wrapper -- that is the actual
safety property `.claude/settings.json` whitelists.

Scoped to the real, currently-existing local Python test surfaces:
`__WORK_IN_PROGRESS__/tests/` (research code), `backend/test_*.py`
(product/QAS code), and (TASK-0072) `test_golden_value_cross_tree_drift.py`
at the repo root -- the cross-tree drift regression guard, which needs
both trees importable at once (hence `WIP_SRC` on `PYTHONPATH` even though
its own file lives outside `__WORK_IN_PROGRESS__/`). Playwright-based
UI/API presets (TASK-0021, TASK-0022) are a separate, still-blocked effort
(TASK-0026.002/TASK-0026 parent recovery of `agents-tools/capability-
runner.sh`) and are intentionally out of scope here -- no Playwright
config or test files exist in this repo yet.

No third-party dependencies -- stdlib only. Always runs against the local
working tree, never against Render.

Interpreter resolution (TASK-0026.005): prefers `REPO_ROOT/.venv/bin/python3`
if it exists on disk, so this works from a cold Bash call regardless of
whether the invoking shell happens to have a venv active (it can't, across
separate tool calls -- shell state doesn't persist). Falls back to
`sys.executable` unchanged when no `.venv/` is present, so environments
where the ambient interpreter already has the test deps keep working
exactly as before -- purely additive, not a behavior change for that case.

Usage:
    pytest_local.py <preset> [--json]
    pytest_local.py --list

Presets:
    wip-labels        __WORK_IN_PROGRESS__/tests/test_labels.py
    wip-hamiltonians  __WORK_IN_PROGRESS__/tests/test_hamiltonians.py
    wip-physics       __WORK_IN_PROGRESS__/tests/test_physics.py
    wip-potentials    __WORK_IN_PROGRESS__/tests/test_potentials.py
    wip-all           __WORK_IN_PROGRESS__/tests/ (whole directory)
    backend           backend/test_geometry.py backend/test_analysis.py backend/test_analysis_characterization.py
    cross-tree        test_golden_value_cross_tree_drift.py (TASK-0072 -- needs both trees, hence WIP_SRC too)
    all               wip-all + backend + cross-tree
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WIP_SRC = str(REPO_ROOT / "__WORK_IN_PROGRESS__" / "src")


def _resolve_interpreter():
    # type: () -> str
    """`.venv/bin/python3` if present, else `sys.executable` unchanged."""
    venv_python = REPO_ROOT / ".venv" / "bin" / "python3"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable

# extra_pythonpath: the `allostery` package under __WORK_IN_PROGRESS__/src has
# no editable install/conftest.py, so its tests need src/ on PYTHONPATH.
# backend/ imports as a top-level package from the repo root, so it needs none.
PRESETS = {
    "wip-labels": (["__WORK_IN_PROGRESS__/tests/test_labels.py"], WIP_SRC),
    "wip-hamiltonians": (["__WORK_IN_PROGRESS__/tests/test_hamiltonians.py"], WIP_SRC),
    "wip-physics": (["__WORK_IN_PROGRESS__/tests/test_physics.py"], WIP_SRC),
    "wip-potentials": (["__WORK_IN_PROGRESS__/tests/test_potentials.py"], WIP_SRC),
    "wip-all": (["__WORK_IN_PROGRESS__/tests"], WIP_SRC),
    "backend": (
        ["backend/test_geometry.py", "backend/test_analysis.py", "backend/test_analysis_characterization.py"],
        None,
    ),
    "cross-tree": (["test_golden_value_cross_tree_drift.py"], WIP_SRC),
    "all": (
        ["__WORK_IN_PROGRESS__/tests", "backend/test_geometry.py", "backend/test_analysis.py",
         "backend/test_analysis_characterization.py", "test_golden_value_cross_tree_drift.py"],
        WIP_SRC,
    ),
}


def run_preset(name):
    targets, extra_pythonpath = PRESETS[name]
    interpreter = _resolve_interpreter()
    cmd = [interpreter, "-m", "pytest", "-q"] + targets
    env = os.environ.copy()
    if extra_pythonpath:
        env["PYTHONPATH"] = extra_pythonpath + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, env=env)
    if result.returncode != 0 and "No module named pytest" in result.stderr:
        result.stderr += (
            f"\n\npytest_local.py: resolved interpreter {interpreter!r} has no "
            "pytest installed. If .venv/ doesn't exist yet, build it per "
            "CLAUDE.md: python3 -m venv .venv && source .venv/bin/activate "
            "&& pip install -r requirements.txt && pip install pytest"
        )
    return cmd, result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("preset", nargs="?", choices=sorted(PRESETS))
    parser.add_argument("--list", action="store_true", help="print available presets and exit")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable summary instead of raw pytest output")
    args = parser.parse_args()

    if args.list or not args.preset:
        for name, (targets, _) in sorted(PRESETS.items()):
            print(f"{name}: {' '.join(targets)}")
        sys.exit(0 if args.list else 2)

    cmd, result = run_preset(args.preset)

    if args.json:
        print(json.dumps({
            "preset": args.preset,
            "cmd": cmd,
            "returncode": result.returncode,
            "passed": result.returncode == 0,
            "stdout_tail": result.stdout.strip().splitlines()[-20:],
            "stderr_tail": result.stderr.strip().splitlines()[-20:],
        }, indent=2))
    else:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
