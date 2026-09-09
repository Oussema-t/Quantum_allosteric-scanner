# TASK-0352 — An index of where decisions live, and a three-way consistency check. Not a search tool.

- Status: TODO
- Owner: **Toolsmith**
- Priority: Medium — **do not start before 2026-09-15**
- Filed: 2026-09-09 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0321]], [[TASK-0322]], [[TASK-0323]], [[TASK-0326]], [[TASK-0270]], [[TASK-0349]]

## Why this is an index and not a search tool

The repo owner proposed a search tool and flagged it as risky in the same breath.
That instinct is right and the task is scoped around it.

**A search tool makes a *negative* result authoritative.** *"I ran the register
search and found nothing"* reads far stronger than *"I grepped and found
nothing"* — and if coverage is incomplete, that confident negative **licenses**
the assumption it was built to prevent. Strictly worse than no tool.

This register has produced that exact failure repeatedly: the page counter wrong
by >2× ([[TASK-0344]]), the appendix marker that never compiled ([[TASK-0349]]),
the bootstrap LRT re-seeding bug ([[TASK-0319]]), `hyp_register_check`'s own
status-detection bug. Every one was a checker trusted because it existed.

**Search cost is also not the binding constraint.** A grep over four directories
takes seconds; [[TASK-0321]] measured a **9% citation rate**. That is not "grep
was too slow", it is "nobody looked". A faster grep does not fix that.

**The decisive property**: an index can be checked for staleness. A search cannot
be checked for completeness. Build the thing that can be verified.

## Part B first — the three-way reconciliation (cheap, mechanical, do this one)

Three sources of truth about live work disagree silently today:

| source | what it knows |
|---|---|
| `.ai/tasks/.locks/*.lock` | who holds what |
| `.ai/tasks/{TODO,IN_PROGRESS,DONE}/` | what state the file claims |
| `.ai/COMMON.md` Active Work Registry | what a fresh session actually reads |

**Measured 2026-09-09, the incident that prompted this**: [[TASK-0350]] was
claimed and *running*, its file still under `TODO/`, and it had **no registry row
at all** — nor did [[TASK-0347]] or [[TASK-0351]]. All three were filed by the
Reviewer thread, which omitted the rows despite COMMON.md's own explicit rule.
The lock prevented a collision; **the coordination hub simply did not know the
work existed.**

- Outcome: one command reporting every disagreement — claimed but no registry
  row, registry row but no file, file in `DONE/` with a live claim, `Status:`
  line disagreeing with its folder, row `Status` disagreeing with either.
- This is a consistency check over **structured** data. It is deterministic,
  needs no judgement, and would have caught the incident above the moment the
  task was filed. **It should ship even if Part A never does.**
- Reuse `claim.py`'s own lock-reading and disk-scan (`task_locate.py` already
  does this for a single id — generalise it, do not write a second scanner).

## Part A — the decision index (harder, judgement-laden, gated on B)

Where the four recent assumption failures actually had their answers:

| assumed | where the answer was |
|---|---|
| "just run the suggested `8S8C`" | **`config/targets.yaml` inline comment** |
| "KRAS numbering looks like an index bug" | targets.yaml + the PDB itself |
| "the chiral walk was the only interference test" | [[TASK-0130]], cited by four tasks |
| "consistent with the JACS ρ≈0.95" | nowhere — genuinely unmeasured |

**Two of four sat in a config file's comments**, which no task-file search would
reach and which nobody thinks to grep. That is not a search problem — it is that
**decisions and their reasons are scattered across places nobody enumerates.**

- Outcome: a generated index, one line per recorded decision: *what was decided,
  when, and **where the reason lives*** — pointing at least at `config/targets.yaml`,
  `documentation/2026-08-26-organiser-clarifications.md`,
  `.claude/hypotheses/*`, the retraction record, and DONE task verdicts.
- **Record the pointer, never restate the reason.** A restatement drifts from its
  source and then there are two answers, which is worse than one hard-to-find
  one. This is the single most important constraint in this task.
- [[TASK-0322]] built exactly this shape for hypotheses. Follow that precedent
  rather than inventing a second one.

## Constraints And Invariants

- **Ships with a test that fails on a seeded gap** — remove a registry row, the
  check must go red. [[TASK-0319]]'s standing rule, and the specific reason Part
  B is trustworthy where a search tool would not be.
- **Never summarise or rank.** If any output is truncated it must say so
  explicitly and print how many were withheld.
- Read-only. It reports drift; it does not repair it. Auto-repair of a contended
  file is how the Active Work Registry got reverted twice in one session
  (COMMON.md's own 2026-07-04 note).
- No new source of truth. The index is *derived*; if it and the source disagree,
  the source wins and the index is stale.

## Timing, and the honest reason to wait

**Do not start before 2026-09-15.** [[TASK-0350]] and [[TASK-0351]] are unstarted
and the deadline is six days out; this is tooling, not submission work.

There is also a real epistemic reason: **the standing "check the register before
you assume" rule landed on 2026-09-08 and nobody has yet had a chance to follow
it.** If agents keep assuming with the rule in front of them, that is the evidence
Part A is needed — and the failures will say what to index. Building it now means
guessing at the index's contents from four data points.
