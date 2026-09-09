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

Interpreter resolution (TASK-0026.005, scoped per-preset by TASK-0069):
works from a cold Bash call regardless of whether the invoking shell has a
venv active (it can't, across separate tool calls -- shell state doesn't
persist). Every preset except `backend` (plus `--file` mode) prefers
`__WORK_IN_PROGRESS__/.venv/bin/python3` first -- the research tree has
its own pinned lock (`requirements-lock.txt`, TASK-0333) and a WIP-only
dependency going missing under the root `.venv/` was the original live
symptom (TASK-0069). The `backend` preset prefers `REPO_ROOT/.venv/bin/
python3` (built to `requirements.txt`'s backend pins). Both then fall
back to the root `.venv/`, then `sys.executable` unchanged -- a checkout
with only one venv (today's actual state) or none (CI) behaves exactly as
before, purely additive.

Usage:
    pytest_local.py <preset> [--json]
    pytest_local.py --file <test_module.py> [--json]
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

--file <basename> (TASK-0196): run exactly one test module under
__WORK_IN_PROGRESS__/tests/ by exact basename, e.g.
`--file test_response.py` -- for any of the (currently 53, growing)
test files that don't have a hand-named preset above, without waiting on
the full `wip-all` run. Validated, not free-form: the basename must match
`test_*.py` exactly (no path separators, no `..`) AND must exist on disk
-- a well-formed but wrong/typo'd name fails with a clear message rather
than a silent no-op or a confusing pytest error. Mutually exclusive with
the positional preset. Reuses the same PYTHONPATH/interpreter resolution
as every preset above -- not a second code path.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WIP_SRC = str(REPO_ROOT / "__WORK_IN_PROGRESS__" / "src")
WIP_TESTS_DIR = REPO_ROOT / "__WORK_IN_PROGRESS__" / "tests"

# TASK-0026.005 / TASK-0069: two possible repo-local venvs. The research
# tree carries its own pinned lock (`__WORK_IN_PROGRESS__/requirements-
# lock.txt`, TASK-0333) and may be provisioned into its own venv; the root
# `.venv/` is the one built to `requirements.txt`'s backend pins.
REPO_VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python3"
WIP_VENV_PYTHON = REPO_ROOT / "__WORK_IN_PROGRESS__" / ".venv" / "bin" / "python3"

# TASK-0196: basename-exact, no path separators or traversal reach this --
# `^test_...\.py$` anchored on the full string, checked before any
# filesystem access.
_TEST_FILE_RE = re.compile(r"^test_[A-Za-z0-9_]+\.py$")


def _resolve_interpreter(prefer_wip, wip_venv_python=WIP_VENV_PYTHON, repo_venv_python=REPO_VENV_PYTHON):
    # type: (bool, Path, Path) -> str
    """Resolve a real venv interpreter for a cold Bash call -- no venv can
    be active across separate tool calls, so the ambient `sys.executable`
    is usually the bare system python with no test deps (TASK-0026.005).

    `prefer_wip=True` -- every preset except `backend`, plus `--file`
    mode: try `__WORK_IN_PROGRESS__/.venv/bin/python3` first. TASK-0069:
    once a root `.venv/` existed, the old repo-root-wide resolver silently
    picked it for `wip-*` presets too, so a WIP-only dependency
    (matplotlib, installed into the WIP venv for `viz.py`'s tests) went
    missing with `ModuleNotFoundError` even though it was right there in
    the venv the WIP suite is supposed to use.

    `prefer_wip=False` -- the `backend` preset only: the root `.venv/`
    first, since that's the one built to `requirements.txt`'s backend
    pins.

    Both then fall back to the root `.venv/`, then `sys.executable`
    unchanged -- a checkout with only one venv (today's actual state: no
    `__WORK_IN_PROGRESS__/.venv/`), or none at all (CI), behaves exactly
    as before this change. TASK-0026.005's own Constraint, preserved.
    """
    candidates = []
    if prefer_wip:
        candidates.append(wip_venv_python)
    candidates.append(repo_venv_python)
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
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


def _run_targets(targets, extra_pythonpath):
    # type: (list, object) -> tuple
    """Shared execution path: same interpreter resolution, PYTHONPATH
    plumbing, and pytest-missing diagnostic for both preset mode and
    `--file` mode (TASK-0196) -- one code path, not two.

    `prefer_wip` (TASK-0069) is derived from `extra_pythonpath`: every
    WIP-oriented preset and `--file` mode already passes `WIP_SRC` here,
    `backend` passes `None` -- so the same signal that decides the
    PYTHONPATH also decides which venv to prefer, with no third field
    added to the PRESETS table. `all`/`cross-tree` run both trees through
    one interpreter (unchanged -- this task is resolver-only, not an
    execution-model change) and so get the WIP venv when it exists: the
    more-likely-complete superset for a combined run; the backend/WIP
    numpy-version divergence is a separately-flagged Open Question, not
    this task's call."""
    prefer_wip = extra_pythonpath is not None
    interpreter = _resolve_interpreter(prefer_wip)
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


def run_preset(name):
    targets, extra_pythonpath = PRESETS[name]
    return _run_targets(targets, extra_pythonpath)


def validate_test_file(basename):
    # type: (str) -> Path
    """TASK-0196: format check first (cheap, no filesystem access), then
    existence -- in that order, so a path-traversal-shaped argument is
    rejected before it ever reaches `Path.is_file()`. Raises SystemExit
    with a clear, specific reason on either failure; returns the resolved
    Path only when both checks pass."""
    if not _TEST_FILE_RE.match(basename):
        raise SystemExit(
            f"error: --file {basename!r} is not a valid test module name -- "
            "must match test_<name>.py exactly (no path separators, no '..', "
            "basename only)"
        )
    path = WIP_TESTS_DIR / basename
    if not path.is_file():
        raise SystemExit(
            f"error: --file {basename!r} does not exist under "
            f"{WIP_TESTS_DIR.relative_to(REPO_ROOT)}/ -- check spelling; "
            "`pytest_local.py --list` does not enumerate individual files, "
            "only presets, so a typo here is not caught by that list"
        )
    return path


def run_file(basename):
    # type: (str) -> tuple
    path = validate_test_file(basename)
    rel = path.relative_to(REPO_ROOT).as_posix()
    return _run_targets([rel], WIP_SRC)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("preset", nargs="?", choices=sorted(PRESETS))
    parser.add_argument(
        "--file",
        metavar="BASENAME",
        help="run exactly one test_*.py file under __WORK_IN_PROGRESS__/tests/ "
        "by basename (TASK-0196) -- mutually exclusive with the preset "
        "positional; validated (format + existence), not free-form",
    )
    parser.add_argument("--list", action="store_true", help="print available presets and exit")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable summary instead of raw pytest output")
    args = parser.parse_args()

    if args.preset and args.file:
        parser.error("give either a preset or --file, not both")

    if args.list or not (args.preset or args.file):
        for name, (targets, _) in sorted(PRESETS.items()):
            print(f"{name}: {' '.join(targets)}")
        print("--file <basename>: any test_*.py under __WORK_IN_PROGRESS__/tests/ (TASK-0196)")
        sys.exit(0 if args.list else 2)

    if args.file:
        selector = f"wip-file:{args.file}"
        cmd, result = run_file(args.file)
    else:
        selector = args.preset
        cmd, result = run_preset(args.preset)

    if args.json:
        print(json.dumps({
            "preset": selector,
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
