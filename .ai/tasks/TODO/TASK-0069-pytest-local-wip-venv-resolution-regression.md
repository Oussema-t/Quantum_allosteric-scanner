# TASK-0069 `pytest_local.py`'s `wip-*` presets resolve the wrong venv now that a root `.venv` exists

## Context

- ID: TASK-0069
- Title: `.ai/tools/pytest_local.py`'s interpreter resolution
  (`REPO_ROOT/.venv/bin/python3`) now silently picks the top-level
  `backend/`-oriented venv for `wip-*` presets too, instead of
  `__WORK_IN_PROGRESS__/.venv`
- Status: TODO
- Owner: Toolsmith
- Source: found live, TASK-0014 session, 2026-07-12 — `python3
  .ai/tools/pytest_local.py wip-all` failed with `ModuleNotFoundError: No
  module named 'matplotlib'` immediately after `viz.py`'s tests were added,
  even though `matplotlib` had just been installed into
  `__WORK_IN_PROGRESS__/.venv` specifically for that task.
- Scope: `.ai/tools/pytest_local.py`'s `_python_executable()` (or
  equivalent resolver) only — no change to preset definitions, `--json`
  output shape, or any other subcommand.

## Intent Contract

- Outcome: `wip-*` presets always run against
  `__WORK_IN_PROGRESS__/.venv/bin/python3` when it exists, regardless of
  whether a *different* venv also exists at the repo root; the `backend`/
  `all` presets keep using the root venv for the `backend/` half as today.
- In Scope:
  - Fix `_python_executable()` (TASK-0026.005's own function, per that
    task's Done section) to resolve per-preset, not repo-root-wide: `wip-*`
    presets (and `all`'s WIP half, if `all` runs both suites through one
    interpreter today — check before assuming) should prefer
    `__WORK_IN_PROGRESS__/.venv/bin/python3`, falling back to
    `REPO_ROOT/.venv/bin/python3` then `sys.executable` only if the WIP
    venv is absent — same fallback *shape* TASK-0026.005 already
    established, just scoped to the right directory per preset.
- Out Of Scope:
  - Reconciling `__WORK_IN_PROGRESS__/.venv`'s numpy/scipy versions
    (2.5.0/1.18.0) against the root venv's pinned
    `requirements.txt` versions (1.26.4/1.13.1) — that's a separate,
    possibly-intentional divergence (WIP is explicitly a research scaffold,
    not pinned to backend's production requirements); flagged as an Open
    Question below, not assumed either way.
  - Any change to which packages are installed in either venv.
- Constraints And Invariants:
  - Must not regress TASK-0026.005's original fix (no root `.venv` present
    -> `sys.executable` unchanged, e.g. a CI environment with no venv at
    all).
  - Python stdlib only, no new dependency (matches every other `.ai/tools/`
    script's constraint).
- Planned Validation:
  1. With both `.venv/` (root) and `__WORK_IN_PROGRESS__/.venv/` present
     (today's actual state): `wip-all` must resolve to
     `__WORK_IN_PROGRESS__/.venv/bin/python3` — assert on the resolved path
     directly (e.g. via `--json`'s `cmd` field, not just "tests pass",
     since the whole bug was a *silent* wrong-venv pick that still ran
     *something* without erroring until a WIP-only dependency was needed).
  2. `backend` preset still resolves to the root venv in the same
     environment.
  3. Regression check: temporarily rename/hide the root `.venv` (or test in
     a fixture repo layout without one) and confirm `wip-*` still falls
     back correctly.

## In Progress

None

## TODO

- [ ] Read `pytest_local.py`'s current `_python_executable()` (or
      equivalent) and preset-to-directory mapping in full before changing
      anything — confirm exactly how `backend`/`all`/`wip-*` currently
      share (or don't) the resolved interpreter.
- [ ] Make resolution preset-scoped per the Intent Contract.
- [ ] Add the resolved-path assertion test from Planned Validation #1 — the
      original bug was invisible to a "did pytest exit 0" check alone.
- [ ] Manually re-run `wip-all`/`backend`/`all` after the fix and confirm
      against real installed-package lists (`pip list` in each venv), not
      just exit codes.

## Dependency

- TASK-0026.005 (Done) — this task's own prior interpreter-resolution fix;
  read its Done section for the original design reasoning before changing
  it further, don't re-derive from scratch.
- TASK-0026.004 (`repo.test.pytest-local` capability entry in
  `CAPABILITIES.md`) — update that row's notes if the resolution behavior
  description there goes stale after this fix.

## Open Questions

- Should `__WORK_IN_PROGRESS__/.venv`'s numpy/scipy be reconciled to the
  root venv's pinned versions, or is the divergence intentional (research
  scaffold vs. production backend)? Not this task's call — flagging so a
  future Architect/Planner pass (or TASK-0044's Python-version
  reconciliation work) picks it up with this data point in hand, not
  starting blind.
- Was the root-level `.venv` created intentionally (someone following
  `CLAUDE.md`'s own setup instructions for `backend/` work) or is its mere
  existence itself worth a `.gitignore`/documentation note so the next
  thread doesn't rediscover this exact interpreter-shadowing surprise a
  different way? Recommend a one-line callout in `CLAUDE.md`'s "Run & test
  locally" section once this task's fix lands, cross-referencing both
  venvs' purposes — not in this task's scope to write, but worth a
  follow-up note for whoever closes it.

## Done

(not yet)
