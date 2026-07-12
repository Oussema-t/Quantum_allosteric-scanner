# TASK-0080 c-Myc / 1NKP application (no-holo-ground-truth target)

## Context

- ID: TASK-0080
- Title: Handle the c-Myc (1NKP) required minimum-set target, which has
  no holo ground truth — score on consensus + theoretical docking
  viability instead of AUC/ceiling.
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 5, item 5.7 —
  "Required minimum-set target with **no holo ground truth** — scored on
  consensus + theoretical docking viability. Needs its own handling: no
  AUC, no ceiling; report prediction + confidence honestly."

## Intent Contract

- Outcome: c-Myc/1NKP runs through the pipeline with an explicit
  no-ground-truth code path — it does not attempt to compute AUC or a
  ceiling (both require a labeled holo comparison that doesn't exist for
  this target), and instead reports a prediction with an honest
  consensus-based confidence statement and theoretical docking
  viability.
- In Scope: whatever branch/flag the pipeline needs to recognize "this
  target has no holo structure" and route to the alternative reporting
  path rather than crashing or silently reporting a meaningless AUC.
- Out Of Scope: sourcing new docking-viability tooling from scratch if
  none exists — check what's available (the plan says "theoretical
  docking viability," implying some existing method/heuristic should be
  used, not a new docking engine built for this task).
- Acceptance Scenarios:
  - Given 1NKP run through the pipeline, when it reaches the scoring
    stage, then it does not attempt AUC/ceiling computation and instead
    emits a prediction + confidence + docking-viability statement.
  - Given the same target, then the report clearly states *why* no
    AUC/ceiling is reported (no holo ground truth) rather than silently
    omitting the numbers.
- Constraints And Invariants: "report honestly" — this must not present a
  degraded or missing metric as if it were a normal score; the absence of
  ground truth is itself information to surface, per the plan's framing
  ("a per-target honest NO is a publishable result, not a failure to
  hide" — from TASK-0082's rationale, same spirit applies here).
- Planned Validation: manual review of 1NKP's report output confirming it
  reads as an honest, confidence-qualified prediction, not a masked gap.

## Dependency

- Uses the same orchestration as TASK-0079 (end-to-end challenge run) but
  needs its own branch — coordinate on the pipeline's entry point.
- Feeds TASK-0082 (competence map synthesis) — c-Myc's row in that table
  needs this task's no-ground-truth handling to be meaningful.

## Open Questions

- What "theoretical docking viability" method is available/expected —
  is there existing tooling in the repo or research notebook for this,
  or does it need to be sourced/decided as part of this task?

## Done

(not yet)
