# TASK-0077 WIP graduation part 2: one CI, one green bar

## Context

- ID: TASK-0077
- Title: Single CI workflow running `backend/` and `allostery/` suites
  together, ending the "two test worlds" split.
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 3, item 3.2 —
  "Ends the 'two test worlds' split and makes the repo-wide bar real (the
  standards-memo commitment)."

## Intent Contract

- Outcome: one CI workflow (GitHub Actions or whatever the repo already
  uses/needs to add) runs both `backend/`'s test suite and `allostery/`'s
  test suite on every push/PR, with a single pass/fail signal — not two
  separate, independently-checked pipelines.
- In Scope: the CI workflow file itself; wiring both suites' runners
  (`backend/`'s existing `pytest`-based tests, `allostery/`'s existing
  suite) into one job or one workflow with both as required checks.
- Out Of Scope: writing new tests — this task only unifies how existing
  tests run; TASK-0072's golden-value drift test should be included once
  it lands, but this task doesn't write it.
- Acceptance Scenarios:
  - Given a PR that breaks a `backend/` test, when CI runs, then the
    single workflow fails (not silently green because only `allostery/`
    was checked, or vice versa).
  - Given a clean PR, then CI reports one green status covering both
    suites.
- Constraints And Invariants: depends on TASK-0076 landing first (the
  package must already be promoted to `allostery/` at top level — CI
  should target the final path, not the `__WORK_IN_PROGRESS__/` staging
  path).
- Planned Validation: a deliberately-broken test on each side, confirming
  CI catches both.

## Dependency

- Depends on TASK-0076 (package promotion) landing first.
- Precedes TASK-0078 (dissolve the folder) per the plan's ordering.
- Should incorporate TASK-0072's golden-value cross-tree drift test once
  that lands (not blocking, but worth doing together if timing allows).

## Open Questions

- Does the repo have any existing CI configuration to extend, or is this
  greenfield? Check for `.github/workflows/` before assuming greenfield.

## Done

(not yet)
