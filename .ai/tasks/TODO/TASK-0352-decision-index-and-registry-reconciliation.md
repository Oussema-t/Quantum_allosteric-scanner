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

## Hold released — 2026-09-09, Reviewer thread

**The Toolsmith may pick this up now.** The "do not start before 2026-09-15" line
above is superseded; it is left in place rather than deleted so the reasoning
stays visible.

That hold rested on two arguments. Both are now discharged, but not equally.

**Argument 1 — deadline pressure — is gone.** [[TASK-0350]] and [[TASK-0351]] were
the unstarted submission work it was protecting; both are Done, [[TASK-0353]] with
them. V3 is built and out for adversarial review, and the team has agreed the
first upload waits for a meeting rather than for more work. Genuine slack, not
manufactured slack.

**Argument 2 — "wait for evidence about what to index" — was only ever about
Part A**, and it applies less than it did. Part B never depended on it: its
evidence ([[TASK-0347]]/[[TASK-0350]]/[[TASK-0351]] filed with no registry rows,
a task claimed and running while its file sat in `TODO/`) was already complete
when this was filed. **Part B should start now regardless.**

For Part A there is now more evidence than the four incidents originally listed,
and it points somewhere slightly different from what this task assumed:

- The glyph-coverage and citation checks added to `submission_build_latex.py` on
  2026-09-09 each found a real defect **within seconds of existing** — a
  tofu-rendered `≈`, and three references listed but never cited — in a document
  three people had already read closely.
- The same day, a first reading of that PDF produced a *wrong* conclusion
  (`10¹⁴` "corrupted"), corrected only by checking the renderer rather than
  trusting the extraction.

**What that suggests for the design, offered as input rather than as a
requirement:** a check that fails loudly at the moment of building beat both a
prose rule and three careful human readings. Part A's index is passive by
construction — it helps only someone who chooses to consult it, which is
[[TASK-0321]]'s measured 9%. **If there is a way to make part of the decision
index assert itself at a natural moment — as a check something already runs —
that is likely worth more than making the index more complete.** The Toolsmith is
better placed than this thread to judge whether that is feasible.

**Unchanged, and still the point of the task**: an index can be checked for
staleness, a search cannot be checked for completeness; record the pointer, never
restate the reason; ship with a test that fails on a seeded gap; never summarise
or rank; read-only.

**One honest caveat on the evidence.** The standing "check the register before you
assume" rule is one day old and has not had time to be tested. Nothing here shows
it failing — only that *checks* have succeeded quickly. Do not read this addendum
as evidence the rule does not work.
