# TASK-0086 Execution/trigger path

## Context

- ID: TASK-0086
- Title: Decide and implement how a run is launched — offline batch
  producing artifacts (preferred) vs. an async job queue.
- Status: TODO
- Owner: Architect/Planner
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 6, item 6.4 —
  "Records the decision; the artifact contract makes either viable."

## Intent Contract

- Outcome: a recorded decision on how `allostery/`'s pipeline (TASK-0079's
  end-to-end run) actually gets triggered to produce the artifacts
  `backend/` serves (TASK-0084) — offline batch (run ahead of time,
  commit/deploy the artifacts) versus an async job queue (user-triggered,
  computed on demand, polled for completion) — plus whatever
  implementation the decision requires.
- In Scope: the decision itself and its implementation (a batch script,
  or a job-queue mechanism, depending on which is chosen); this is a
  decision-plus-execution task, not decision-only, since the plan frames
  it as "decide and implement."
- Out Of Scope: the artifact format (TASK-0083) and the serving endpoints
  (TASK-0084) — this task only decides/implements *how the artifact gets
  produced/refreshed*, not its shape or how it's read.
- Acceptance Scenarios:
  - Given the decision is made, when documented, then it states explicitly
    why offline-batch or async-job-queue was chosen, referencing the
    plan's stated preference ("offline batch — no compute in the request
    path, works on free-tier Render").
  - Given the chosen mechanism, when a target's artifact needs producing
    or refreshing, then there's a working, documented way to do it
    (a script to run, or a queue to submit to).
- Constraints And Invariants: per the plan's stated preference, offline
  batch is favored specifically because Render's free tier can't sustain
  heavy compute in the request path — deviating from that preference
  needs an explicit justification recorded in this task's Done section.
- Planned Validation: successfully producing/refreshing at least one
  target's artifact via the chosen mechanism, end-to-end.

## Dependency

- Depends on TASK-0083 (artifact contract) — needs to know what it's
  producing.
- Feeds TASK-0084 (backend results API) — the API's assumptions about
  artifact freshness/availability depend on this decision.

## Open Questions

- None beyond the core decision itself, which this task owns making.

## Done

(not yet)
