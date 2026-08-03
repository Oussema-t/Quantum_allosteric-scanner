# TASK-0196 `pytest_local.py` single-file selector for untracked test modules

## Context

- ID: TASK-0196
- Title: add a validated `--file <basename>` selector to `pytest_local.py`
  so any test file under `__WORK_IN_PROGRESS__/tests/` gets a fast,
  whitelisted, targeted run — not just the 4 modules with a hand-named
  preset — without loosening the tool's "named/validated selection only,
  no free-form pytest args" safety property.
- Status: Done
- Owner: Implementer (Architect starting it directly, this session)
- Claimed By: Architect
- Claimed At: 2026-08-03 15:52
- Source: orchestrating collaborator (Bartosz), 2026-08-03 — flagged an
  ad hoc `cd __WORK_IN_PROGRESS__ && PYTHONPATH=src ../.venv/bin/python3
  -m pytest -q tests/ | tail -20` invocation that cannot match any
  whitelist pattern (chained/piped commands defeat pattern matching, the
  same class of issue as [[TASK-0042]]'s bare-`status`/`sync` fix earlier
  this session) and asked what to tell implementers to avoid it.
- Priority: **P2.** Cheap, no new dependency, directly reduces permission
  friction for every implementer thread running tests during iteration —
  not on any science critical path.

## Why this matters — the tool's preset list is 5 weeks stale

`pytest_local.py` (TASK-0026.004) already solves exactly this problem in
principle — a whitelisted wrapper so no thread hits a permission prompt
for an ad hoc `pytest` invocation. But its preset dict has 4 hand-named
single-file entries (`wip-labels`, `wip-hamiltonians`, `wip-physics`,
`wip-potentials`), dating from when `__WORK_IN_PROGRESS__/tests/` had far
fewer files. **It now has 53 test files** — `test_response.py`,
`test_selection.py`, `test_shortcuts.py`, `test_sites.py`,
`test_consensus_labels.py`, `test_plant.py`, `test_nulls.py`, and more
from this session's own work have no dedicated preset. An implementer
iterating on one module has exactly two whitelisted options today: a
4-module allowlist that doesn't include their module, or the full
`wip-all` (confirmed ~126s this session) — too slow for a tight
edit-test loop, and it will only get slower as the suite grows.

Adding a 54th, 55th, ... hand-named preset every time a new test file
appears is the wrong shape of fix — it is a maintenance burden that will
silently fall behind again. A validated *selector* fixes the whole class
at once.

## Intent Contract

- Outcome: `pytest_local.py --file <basename>` runs exactly that one file
  under `__WORK_IN_PROGRESS__/tests/`, with the same `PYTHONPATH`/venv
  resolution the existing presets already get, whitelisted under the
  existing `Bash(python3 .ai/tools/pytest_local.py *)` pattern (no new
  `.claude/settings.json` entry needed — confirm this before assuming it,
  don't just assert it).
- Why required, not assumed: the 4 fixed single-file presets are stale by
  49 files; a flat validated selector doesn't need updating as the test
  directory grows.

- In Scope:
  - `--file BASENAME` argparse option, usable instead of (not alongside)
    the existing `preset` positional — mutually exclusive, clear error if
    both or neither given.
  - Validation, both checks required, not just one:
    1. format — matches `^test_[A-Za-z0-9_]+\.py$` exactly (rejects any
       path separator, `..`, or non-test-module name outright, before
       ever touching the filesystem).
    2. existence — the exact basename must be a real file directly under
       `__WORK_IN_PROGRESS__/tests/` (`Path.is_file()`, not just a regex
       match) — a well-formed but nonexistent/typo'd name fails with a
       clear message, not a silent no-op or a confusing pytest
       "file not found."
  - Reuses the existing `WIP_SRC` `PYTHONPATH` plumbing and
    `_resolve_interpreter()` — no parallel code path.
  - `--json` output for `--file` mode uses the same schema as preset mode
    (`preset` field can read `"wip-file:<basename>"` so the two modes are
    distinguishable in machine-readable output without a schema change).
  - `--list`/no-args help text mentions `--file` exists alongside the
    fixed preset list.

- Out Of Scope:
  - Removing or consolidating the 4 existing single-file presets — cheap
    to leave as aliases, not this task's concern to tidy.
  - A `--file` equivalent for `backend/test_*.py` — no gap reported there
    (product-layer test count is small and stable); add only if a real
    need shows up.
  - Any change to `wip-all`/`backend`/`cross-tree`/`all`'s existing
    behavior.
  - Directory/glob selectors (`--file 'test_r*.py'`) — basename-exact
    only, deliberately, to keep the validation trivial to audit.

- Constraints And Invariants:
  - **The safety property this tool exists for must not regress**: no
    path traversal, no shell metacharacters reaching `subprocess.run`
    (already list-form, not `shell=True` — keep it that way), no way to
    smuggle extra pytest flags through `--file`'s value.
  - Stdlib only, matching the tool's existing constraint.

- Planned Validation:
  - `--file test_response.py` (a real, current file) runs and passes.
  - `--file test_nonexistent_xyz.py` (well-formed, absent) fails with a
    clear "no such file" message, not a pytest traceback.
  - `--file ../../../etc/passwd` or `--file test_x.py/../../evil` (path
    traversal attempts) rejected by the format check before any
    filesystem access.
  - `--file test_response.py wip-all` (both given) — argparse refuses
    cleanly, doesn't silently pick one.
  - Confirm no new `.claude/settings.json` whitelist entry is actually
    needed (test the exact invocation shape once implemented, don't just
    assume the existing wildcard covers it).

## In Progress

- 2026-08-03 (Architect): implementing directly, same session as filing —
  small, well-scoped, no design ambiguity left after the Intent Contract
  above.

## TODO

- [x] Add `--file` argparse option, mutually exclusive with `preset`.
- [x] Format + existence validation, in that order (cheap check first).
- [x] Wire into `run_preset`-equivalent execution path (reuse, don't fork)
      — new shared `_run_targets()` helper, both `run_preset`/`run_file`
      call it, no duplicated subprocess/env logic.
- [x] `--json` output schema check (distinguishable `preset` field value)
      — `"wip-file:<basename>"`.
- [x] Update module docstring's `Usage`/preset-list block.
- [x] Run the 5 Planned Validation cases above — all 5 passed as specified.
- [x] Confirm whitelist coverage — no new `.claude/settings.json` entry
      needed, confirmed by running `--file test_response.py --json`
      directly; the existing `Bash(python3 .ai/tools/pytest_local.py *)`
      wildcard already covers it (unlike TASK-0042's bare-`status`/`sync`
      case, `--file X` always has a trailing argument, so the `* `
      pattern matches).

## Dependency

- [[TASK-0026.004]] (Done) — the tool this extends.
- [[TASK-0042]] (Done) — same session's precedent for a whitelist-pattern
  gap (bare `status`/`sync`) found and fixed the same way: identify the
  exact failing invocation, fix the narrowest thing that closes it.

## Open Questions

- Should `--file` also accept a bare module name without `test_`/`.py`
  (e.g. `--file response` instead of `--file test_response.py`) for less
  typing? Recommend no — exact basename match is the simplest thing to
  audit for the safety property this tool exists to preserve, and typing
  the full filename is a small cost. Flag if this proves annoying in
  practice; easy to loosen later, harder to have shipped loose from day one.

## Done

**2026-08-03, Architect.** `--file BASENAME` added to `pytest_local.py`,
mutually exclusive with the `preset` positional. Format check
(`^test_[A-Za-z0-9_]+\.py$`, anchored) runs before any filesystem access;
existence check (`Path.is_file()` under `__WORK_IN_PROGRESS__/tests/`)
runs second. Both `run_preset`/`run_file` now call a shared
`_run_targets()` helper (interpreter resolution, `PYTHONPATH` plumbing,
pytest-missing diagnostic) — no duplicated execution logic between the
two selection modes.

All 5 Planned Validation cases confirmed directly:
- `--file test_response.py` → runs, passes (14 passed in 1.81s — vs.
  `wip-all`'s ~126s for the same effective check on this one module).
- `--file test_nonexistent_xyz.py` (well-formed, absent) → clear
  "does not exist" message, not a pytest traceback.
- `--file "../../../etc/passwd"` and `--file "test_x.py/../../evil"`
  (two path-traversal shapes) → both rejected by the format check,
  before any `Path`/filesystem call.
- `--file test_response.py wip-all` (both given) → argparse refuses
  cleanly (`error: give either a preset or --file, not both`), no silent
  pick-one.
- Whitelist coverage confirmed empirically, not assumed: ran
  `pytest_local.py --file test_response.py --json` directly: no new
  `.claude/settings.json` entry needed — the existing
  `Bash(python3 .ai/tools/pytest_local.py *)` wildcard already covers it,
  since `--file X` always has a trailing argument (unlike TASK-0042's
  bare-`status`/`sync` case, which had none).

Regression-checked: `--list` still enumerates all 8 presets unchanged,
now with one added line noting `--file` exists; `wip-labels --json`
(an existing preset) still produces byte-identical schema/behavior
(33 passed in 2.25s).

No new dependency, no change to any existing preset's targets or
behavior, no `.claude/settings.json` edit.
