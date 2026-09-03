# TASK-0323 — Audit existing tasks for hypothesis verdicts that were never written back

- Status: TODO
- Owner: Explorer, handing off to Implementer for the linking edits
- Priority: High
- Filed: 2026-09-03 by Architect/Planner, split out of [[TASK-0321]] (pathway C
  — a failure mode surfaced in discussion, upstream of A and B)
- Related: [[TASK-0321]], [[TASK-0307]] (same shape: captured knowledge, never
  consulted where it mattered), [[TASK-0324]] (gated on this task's findings)

## Why this exists

Discussing [[TASK-0321]], the repo owner raised a distinct worry: of the 14
hypotheses with no dated status, some may not be genuinely untested — a task
may already have tested and falsified (or confirmed) the underlying claim,
written its finding into `RESULTS.md` / its own Done section, and simply never
connected that finding back to the hypothesis it was actually deciding. That
would not be a research gap (needing new work) but a **linking gap**
(needing an edit to `.claude/hypotheses/*.md`) — the same shape [[TASK-0307]]
already found for the submission drafts (13 Done tasks categorically absent
from both), just recurring in a second artifact.

**This must run before, or at minimum feed into, [[TASK-0324]]'s backfill.**
Discovering an answer already sitting in a Done task is cheaper than
re-deriving it, and blindly commissioning fresh backfill work risks
re-running something this repo has already paid for once.

## Intent Contract

- Outcome: for each of the 14 currently-unjudged hypotheses (see [[TASK-0321]]
  for the list; HYP-P1 and HYP-P13 are the two highest-value by citation
  count, 16 and 8 respectively — start there if a bounded pilot is needed
  before committing to all 14), either (a) a specific Done task identified as
  already having tested it, with a proposed dated-status line and citation to
  add, or (b) an explicit "genuinely never tested" finding.
- Why required, not assumed: the register's own measured citation rate (9%)
  means an untested-looking hypothesis and an already-tested-but-unlinked one
  currently look identical from the register alone — this task exists to tell
  them apart before anyone commissions new work.
- In Scope: reading task files (prioritize `.ai/tasks/DONE/`, 339 total, most
  not citing any hypothesis) for findings whose subject matches an unjudged
  hypothesis's claim, even where the task never names the hypothesis id.
  Matching is a judgment call — record the reasoning, not just the verdict,
  so [[TASK-0324]] (or the Architect) can sanity-check the mapping rather than
  take it on faith.
- Out Of Scope: writing the actual status lines into the hypothesis files
  (propose them here; [[TASK-0324]] or a follow-up commit applies them, kept
  separate so this task's own judgment calls are reviewable before they
  become the register's authoritative content — matches [[TASK-0321]]'s own
  "do not close this by rewriting the hypotheses" constraint in spirit).
  Auditing the 310 non-citing tasks against hypotheses *not yet in the
  unjudged-14 list* — out of scope unless a clear match surfaces incidentally;
  don't go looking for it.
- Constraints And Invariants:
  - A proposed match needs the same evidentiary bar the register already
    holds itself to elsewhere — a specific result, not a vibe. If a task is
    merely adjacent to a hypothesis's subject without actually deciding its
    claim, say so and leave the hypothesis unjudged; a wrong verdict is worse
    than a missing one.
  - Where a hypothesis maps to more than one task with results in tension,
    report the tension explicitly — do not silently pick the more convenient
    one.
- Planned Validation: spot-check 3 proposed mappings against the actual cited
  task's own Done section before treating the batch as reliable; if any of
  the 3 don't hold up on a close read, widen the spot-check before handing
  results to [[TASK-0324]].

## TODO

- [ ] Pilot pass: HYP-P1 and HYP-P13 only. Confirm the approach finds real
      matches (or confirms genuine absence) before committing to the full 14.
- [ ] Full pass: remaining 12 unjudged hypotheses.
- [ ] Write findings as a table (hypothesis id → matched task id(s) → proposed
      status line → confidence), handed to [[TASK-0324]].
- [ ] Flag any hypothesis where matched tasks disagree with each other.

## Dependency

- [[TASK-0321]] — the 14-item unjudged list and citation counts this task
  starts from.
- Feeds [[TASK-0324]] — do not let that task's backfill start blind on a
  hypothesis this task hasn't checked yet.

## Done

(not yet)
