# TASK-0324 — Hypothesis verdict back-fill (whatever TASK-0323 leaves genuinely untested)

- Status: TODO — **blocked on [[TASK-0323]]**, do not start early
- Owner: Implementer (physics/science judgment calls may need Architect input,
  same convention as `POC_SPRINT_PLAN.md`'s own team-split note)
- Priority: Medium — real, but sequenced behind the cheaper option
- Filed: 2026-09-03 by Architect/Planner, split out of [[TASK-0321]] (pathway B
  — "not maintained")
- Related: [[TASK-0321]], [[TASK-0323]]

## Why this exists, and why it waits

[[TASK-0321]] found 14 of 21 hypotheses with no dated status. The naive fix is
a backfill sprint. [[TASK-0323]] exists because some unknown fraction of those
14 were probably already tested by a Done task that never wrote its verdict
back — discovering that is cheaper than re-deriving it. **This task is scoped
to whatever [[TASK-0323]] reports as genuinely never tested, not the full 14
blind.** If [[TASK-0323]] resolves all 14 via linking, this task closes with
nothing left to do — that is a good outcome, not a failure to find work.

## Intent Contract

- Outcome: every hypothesis [[TASK-0323]] reports as genuinely untested gets a
  dated status — including legitimate non-PASS/FAIL verdicts (`SUPERSEDED`,
  `NEVER TESTED — reason`, `ABANDONED`), which TASK-0321 already names as
  acceptable verdicts in their own right.
- Why required, not assumed: TASK-0321's own point — a reader consulting the
  most-cited hypothesis in the register (HYP-P1, 16 citations) currently
  learns only what was once proposed, never whether it survived.
- In Scope: hypotheses on [[TASK-0323]]'s "genuinely never tested" list only.
- Out Of Scope: hypotheses [[TASK-0323]] already resolved by linking (apply
  those edits as part of closing that task, not this one); designing new
  experiments beyond what's needed to reach a verdict — if a hypothesis needs
  substantial new science to judge, that's its own task, file it rather than
  absorbing it here.
- Constraints And Invariants: same as [[TASK-0321]]'s own — do not rewrite a
  hypothesis's claim while adding its verdict; add the status, don't relitigate
  the framing.
- Planned Validation: after this task closes, TASK-0322's checker (once it
  exists) should show 0 unjudged hypotheses among the ones this task touched.

## TODO

- [ ] Wait for [[TASK-0323]]'s findings.
- [ ] For each hypothesis on the genuinely-untested list: run or commission
      the minimum work needed to reach a dated verdict.
- [ ] Write the dated status line into the relevant `.claude/hypotheses/*.md`
      file.

## Dependency

- [[TASK-0323]] — hard blocker, this task's own scope is defined by that
  task's output.

## Done

(not yet)
