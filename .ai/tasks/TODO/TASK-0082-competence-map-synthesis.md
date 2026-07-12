# TASK-0082 Competence map synthesis

## Context

- ID: TASK-0082
- Title: Assemble the per-target floor/ceiling/headroom table into the
  submission's central claim — the honest per-target competence map.
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 5, item 5.2 —
  "The strategic differentiator. 'We close X% of the gap knowing the
  answer would close, on these targets; ~0 on those, and here is why.' A
  per-target honest NO is a publishable result, not a failure to hide."
  Third link in the critical path (`... → 5.1 → 5.2 → 6.1`).

## Intent Contract

- Outcome: a synthesized table/report, one row per target, showing floor
  score, ceiling score (TASK-0046), actual pipeline score, and headroom
  (how much of the floor-to-ceiling gap the pipeline closes) — with an
  honest narrative for targets where headroom closure is ~0, explaining
  why rather than hiding the result.
- In Scope: consuming TASK-0079's end-to-end run output (all mandatory
  targets), TASK-0080's c-Myc no-ground-truth handling, and TASK-0046's
  ceiling values; producing the synthesized competence map as a document
  or report artifact.
- Out Of Scope: computing the floor/ceiling scores themselves (TASK-0011
  baselines.py, TASK-0046 ceiling search — both inputs, not this task's
  job to (re)implement).
- Acceptance Scenarios:
  - Given TASK-0079's per-target results and TASK-0046's ceiling values,
    when synthesized, then every mandatory target has a stated
    floor/ceiling/actual/headroom row.
  - Given a target where the pipeline's actual score is close to floor
    (near-zero headroom closure), then the synthesis states this
    explicitly with a reason, rather than omitting or burying the target.
- Constraints And Invariants: this is explicitly the "strategic
  differentiator" per the plan — treat honest NOs as first-class content,
  not something to minimize.
- Planned Validation: manual review confirming every mandatory target
  (plus c-Myc's special case) has a row and the low-headroom cases have
  stated reasons.

## Dependency

- Depends on TASK-0079 (end-to-end challenge run), TASK-0080 (c-Myc
  handling), and TASK-0046 (ceiling coordinate-descent search) — all
  three feed this synthesis.
- Feeds TASK-0083 (result artifact contract) and TASK-0085 (frontend
  research visualization, "competence panel: floor / method / ceiling
  bars") — the critical path continues into Phase 6.

## Open Questions

- What document/artifact format does this synthesis take — is it part of
  TASK-0083's artifact contract directly, or a separate report that
  TASK-0083 then references? Decide when TASK-0083 is scoped.

## Done

(not yet)
