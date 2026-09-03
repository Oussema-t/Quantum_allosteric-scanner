# TASK-0322 — Hypothesis-register consultation enforcement (checker + index)

- Status: TODO
- Owner: Implementer
- Priority: High
- Filed: 2026-09-03 by Architect/Planner, split out of [[TASK-0321]] (pathway A —
  "not consulted")
- Related: [[TASK-0321]], [[TASK-0319]] (`doc_parity.py` precedent), [[HYP-P9]],
  [[TASK-0320]] (the triggering incident)

## Why this exists

[[TASK-0321]] measured that the hypothesis register (`.claude/hypotheses/*.md`,
21 hypotheses across 4 files) is cited by only 9% of task files and 2 of 12
outward-facing documents. The triggering incident: a collaborator brief claimed
a route was "open" that [[HYP-P9]] had recorded `FAIL` on, current and correct,
in a file the same session had already opened. Protocol text alone will not fix
this — the same session was presumably diligent and still missed it. This task
builds the mechanical gate; see [[TASK-0321]]'s Done section for why this
pathway was chosen over relying on discipline.

## Intent Contract

- Outcome: (1) a one-screen status index at the top of the hypothesis register
  (id · one-line claim · dated status, sorted by citation count) so consulting
  it is a single read, not four file-opens; (2) a checker script, in the shape
  of `.ai/tools/doc_parity.py`, that flags two distinct violation classes.
- Why required, not assumed: [[TASK-0321]]'s diagnosis — writing better
  hypotheses does not fix non-consultation; only something that runs and fails
  loudly does, matching [[TASK-0319]]'s own standing precedent.
- In Scope:
  1. **Staleness class**: a hypothesis id whose most-recent citing task
     post-dates its own last dated status line (the register said X, a task
     since then found something newer, the register was never updated).
  2. **Uncited-claim class**: an outward-facing document (start with
     `__WORK_IN_PROGRESS__/documentation/*.md` and any collaborator-facing
     brief such as `CTQW_CONTRIBUTION_BRIEF.html`) containing an open/closed/
     untested-shaped claim about a route or mechanism with no adjacent
     hypothesis id. This is the class that would have caught [[TASK-0320]]'s
     actual error — pattern-match claim-shaped language
     ("is an open route", "remains untested", "has not been ruled out", etc.;
     refine the pattern list against real false positives/negatives before
     trusting it), not just missing citations of existing ids.
- Out Of Scope: rewriting any hypothesis's content (TASK-0321's own
  constraint, inherited here); backfilling verdicts ([[TASK-0324]]); the
  audit of past tasks for unlinked findings ([[TASK-0323]] — independent,
  do not block on it).
- Constraints And Invariants:
  - Must ship with a test that proves it **fails on a seeded violation** —
    [[TASK-0319]]'s standing finding, repeated here because it is exactly the
    kind of checker that is easy to ship silently-inert.
  - The index is generated/maintained, not hand-copied — decide whether it's
    a build step reading the 4 files' own `## HYP-` headers + status lines, or
    a checked-in table the checker also validates for drift against the
    source files. Either is acceptable; silent drift between index and source
    is not.
- Planned Validation: run the checker against the current register + current
  `TASK-0320` brief content (pre-fix, if recoverable from git history) and
  confirm it would have flagged the actual incident. If it would not have
  caught the real, known violation, the pattern set is not done.

## TODO

- [ ] Build the one-screen status index (id, one-line claim, dated status or
      "no verdict recorded", citation count) at the top of the register (or
      as a separate generated file the register's own top links to — Architect
      call if it matters, don't block on it).
- [ ] Build the checker, staleness class.
- [ ] Build the checker, uncited-claim class — pattern set intentionally
      starts narrow; document known gaps rather than over-fitting.
- [ ] Seeded-violation test for both classes.
- [ ] Wire into whatever this repo's existing pre-commit/CI-equivalent check
      point is (see how [[TASK-0319]]'s checker is invoked; match it, don't
      invent a second convention).
- [ ] Run once against the real register + real docs; record what it finds
      (do not fix findings as part of this task unless trivial — report them
      to [[TASK-0323]]/[[TASK-0324]] instead, this task is the gate, not the
      cleanup).

## Dependency

- [[TASK-0319]] — checker precedent and the seeded-violation-test requirement.
- Independent of [[TASK-0323]]/[[TASK-0324]] — do not wait on either.

## Done

(not yet)
