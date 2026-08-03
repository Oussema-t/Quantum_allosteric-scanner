# TASK-0195 `RESULTS.md` has no concurrent-write protection — two silent losses already in history

## Context

- ID: TASK-0195
- Title: extend the project's existing claim/lock discipline to `RESULTS.md`'s
  shared tables, and replace row-number cross-references with task-ID ones so
  a renumber cannot silently invalidate a pointer.
- Status: TODO
- Owner: Toolsmith (with Architect/Planner on the convention half)
- Claimed By: —
- Claimed At: —
- Source: Architect/Planner incident report, 2026-08-03 (open-questions rows
  47–53 lost in the [[TASK-0171]] merge, recovered in `61b8096`); Reviewer
  thread, 2026-08-03, finding F3 (the [[TASK-0167.003]] section lost the same
  way, not yet recovered — see [[TASK-0191]]).
- Priority: **P1 — two confirmed silent losses in one week, on the document
  that is the submission's primary synthesis, with cross-machine concurrent
  work now the norm.**
- Dependency: [[TASK-0065]] (SCQ, Done), [[TASK-0024]]/[[TASK-0107]] (claim
  tooling, Done) — this task extends existing mechanisms rather than inventing
  one.

## Why this matters

Two distinct silent losses, both in `RESULTS.md`, both inside one week:

1. **Open-questions rows 47–53** — two independent lines of work
   ([[TASK-0182]], [[TASK-0185]]) both landed at row 51; a later batch built
   against an older snapshot ([[TASK-0015]]/[[TASK-0167.002]]/[[TASK-0155]]/
   [[TASK-0171]]) overwrote rows 47–53 on merge, taking out eight tasks' index
   entries plus a cross-reference note. **It merged clean — no conflict
   markers, nothing to catch it at commit time.** Recovered from `f5430de` and
   renumbered 52–59 (`61b8096`). [[TASK-0182]]'s own citation pointed at "row
   51" — accurate when written, silently invalidated by the collision.
2. **The [[TASK-0167.003]] section** — written, deliberately withheld from
   commit `92aa669` to avoid clobbering a concurrent thread's uncommitted
   `RESULTS.md` edit, follow-up never filed, content now gone. See
   [[TASK-0191]].

Neither was catastrophic: the `.ai/tasks/DONE/` records survived intact in
both cases. **That is the point** — the underlying ledger is protected and the
synthesis is not.

This is the same failure class `Q-0001` and [[TASK-0107]] already document for
`COMMON.md`, and that file got protection ([[TASK-0017]] claim columns,
[[TASK-0024]] claim tool, [[TASK-0045]] atomic ID reservation). `RESULTS.md`
has **none** — no claim, no lock, no numbering authority — despite being
edited by every thread that closes a task, now across machines.

Two independent weaknesses, and they need different fixes:

- **Write collisions** on a large append-mostly file that merges clean.
- **Positional cross-references**: `RESULTS.md` cites its own open questions
  by row number. Row numbers are not stable identifiers. Every renumber
  silently invalidates every pointer to them, with no way to detect it.

## Intent Contract

- Outcome: (a) a lightweight, whitelisted mechanism that makes a concurrent
  `RESULTS.md` edit visible before it merges; (b) a stated convention that
  cross-references cite task IDs, not row numbers; (c) a check that catches a
  dangling or positional reference.
- Why required, not assumed: two losses in one week, both silent, both
  merging clean. Convention alone did not prevent either — the withheld
  section in loss #2 was a thread *following* good practice and losing the
  content anyway.
- In Scope:
  - **Convention (cheap, do first):** cross-references cite `[[TASK-XXXX]]`,
    never "row N". Where a row number is genuinely needed, pair it with the
    task ID so a renumber degrades to a stale-but-traceable pointer rather
    than a silently-wrong one. Sweep the existing open-questions table and
    [[TASK-0182]]'s citation.
  - **Tooling (evaluate, then build the smallest thing that works):** extend
    `claim.py` with a whole-file resource claim covering `RESULTS.md` —
    [[TASK-0024.001]] already exists for exactly this and is TODO. Consider
    closing it here rather than duplicating it.
  - **Detection:** a check (test or pre-commit) that every `[[TASK-XXXX]]`
    reference in `RESULTS.md` resolves to a real file in `.ai/tasks/`, and
    that no open-questions row number is cited from outside its own table.
  - Assess whether the open-questions table should move to append-only with
    **stable, never-reused** IDs — the same discipline `claim.py reserve-next`
    already enforces for task numbers. Renumbering on collision is what turned
    loss #1 into invalidated pointers.
- Out Of Scope:
  - Splitting `RESULTS.md` into per-task files. Tempting, large, and it would
    lose the single-document synthesis value the project deliberately built.
    Name it as an option; do not do it here.
  - Hook enforcement — [[TASK-0042]] owns that.
- Constraints And Invariants:
  - Extend existing mechanisms. This scaffold already has three overlapping
    coordination tools; a fourth parallel one is a worse outcome than the bug.
  - The convention half must land even if the tooling half is deferred — it is
    free and it prevents the more insidious of the two failure modes.
- Planned Validation:
  - Replay loss #1: does the proposed mechanism actually surface it? A
    protection that would not have caught the incident that motivated it is
    not worth landing. **Demonstrate this, do not assert it.**
  - The dangling-reference check must fail against a deliberately broken
    reference before it passes against the real file.

## In Progress

—

## TODO

- [ ] Convention: task-ID cross-references. Write it into `.ai/COMMON.md`.
- [ ] Sweep the open-questions table + [[TASK-0182]]'s "row 51" citation.
- [ ] Evaluate closing [[TASK-0024.001]] here vs. separately.
- [ ] Build the dangling/positional-reference check; failing-first.
- [ ] Replay loss #1 against the mechanism. Report honestly if it would not have caught it.
- [ ] Decide + record: stable never-reused open-question IDs, or keep renumbering?

## Dependency

- [[TASK-0024.001]] (TODO) — whole-file resource locks. Likely subsumes the
  tooling half.
- [[TASK-0065]] (Done) — SCQ visibility.
- [[TASK-0191]] — the loss this task is meant to prevent recurring.

## Open Questions

- Is a lock the right shape at all for an append-mostly file? The real
  failure was a **stale-snapshot merge**, not two simultaneous writes — a lock
  would not have caught loss #1. A staleness check ("is your `RESULTS.md` base
  the current HEAD?") might be the actually-correct mechanism. **Resolve this
  before building anything**; it changes the design entirely.
- Should the answer just be a hard convention — never edit `RESULTS.md`
  without an immediately-preceding `git pull --rebase` — enforced by
  [[TASK-0042]]'s hook rather than by new tooling?

## Done

—
