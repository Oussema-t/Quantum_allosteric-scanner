# TASK-0072 Golden-value cross-tree drift test

## Context

- ID: TASK-0072
- Title: Fix a reference structure and assert `backend/` and `allostery/`
  produce numerically identical output for every shared-primitive pair,
  so "ported, not cross-imported" code cannot silently diverge again.
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 2, item 2.3 — "The
  anti-drift mechanism [TASK-0066] needs: fix a reference structure,
  assert both trees produce numerically identical output. Without it
  'ported' decays back into 'duplicated' — exactly how 8.0 vs 10.0
  happened." Must land after TASK-0067 (2.1, picks the constant) and
  alongside/after TASK-0066 (2.2, extracts the shared helper).

## Intent Contract

- Outcome: a test (or test suite) that runs both `backend/`'s and
  `allostery/`'s implementation of each shared primitive (Kirchhoff/GNM
  context, DCC, z-score, and whatever else TASK-0066 covers) on the same
  fixed reference structure and asserts the numeric outputs match within
  float tolerance. Runs in CI so any future edit to either side that
  breaks parity is caught immediately, not rediscovered by another
  architecture-reconciliation pass.
- In Scope: the primitives TASK-0066 identifies and ports (Kirchhoff
  context, DCC, z-score helper) plus the GNM cutoff constant TASK-0067
  resolves.
- Out Of Scope: this is not itself the dedup (TASK-0066) — it's the
  regression guard that keeps the dedup honest going forward. Can be
  written test-first, alongside TASK-0066's implementation.
- Acceptance Scenarios:
  - Given the fixed reference structure, when `backend`'s and
    `allostery`'s versions of a shared primitive both run, then their
    outputs are numerically identical within a stated float tolerance.
  - Given a deliberate one-line divergence introduced into either side
    (e.g. change a constant), when the test suite runs, then it fails —
    proving the test actually detects drift rather than trivially
    passing.
- Constraints And Invariants: depends on TASK-0067's chosen cutoff
  constant being landed first (per the plan's explicit ordering) —
  otherwise this test pins the wrong number as "golden."
- Planned Validation: the acceptance scenarios above; include this suite
  in whatever CI TASK-0077 (Phase 3, one CI) eventually sets up.

## Dependency

- Depends on TASK-0067 (GNM cutoff benchmark — must resolve the constant
  first) and TASK-0066 (shared Kirchhoff/DCC helper — this task pins its
  output).
- Feeds TASK-0077 (single CI workflow) once that lands.

## Open Questions

- None yet — scope is fully determined by TASK-0066/0067's outputs; defer
  the exact primitive list until those land.

## Done

(not yet)
