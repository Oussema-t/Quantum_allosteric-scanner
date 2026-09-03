# TASK-0322 — Hypothesis-register consultation enforcement (checker + index)

- Status: Done
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

- [x] Build the one-screen status index (id, one-line claim, dated status or
      "no verdict recorded", citation count) at the top of the register (or
      as a separate generated file the register's own top links to — Architect
      call if it matters, don't block on it).
- [x] Build the checker, staleness class.
- [x] Build the checker, uncited-claim class — pattern set intentionally
      starts narrow; document known gaps rather than over-fitting.
- [x] Seeded-violation test for both classes.
- [x] Wire into whatever this repo's existing pre-commit/CI-equivalent check
      point is (see how [[TASK-0319]]'s checker is invoked; match it, don't
      invent a second convention).
- [x] Run once against the real register + real docs; record what it finds
      (do not fix findings as part of this task unless trivial — report them
      to [[TASK-0323]]/[[TASK-0324]] instead, this task is the gate, not the
      cleanup).

## Dependency

- [[TASK-0319]] — checker precedent and the seeded-violation-test requirement.
- Independent of [[TASK-0323]]/[[TASK-0324]] — do not wait on either.

## Done

**2026-09-03, Implementer A.** Built `.ai/tools/hyp_register_check.py`
(checker + `--build-index`) and `.ai/tools/test_hyp_register_check.py`
(16 tests, all passing — every rule paired with a negative control per
[[TASK-0319]]'s standing finding; `test_catches_the_real_incident`
specifically reconstructs the TASK-0320 incident language recorded in
[[TASK-0321]]'s own filing, since the literal draft bytes were never
committed to git — confirmed via `git log --all -- REVERSE_CTQW_BRIEF.html`,
one commit only, the file was created already-fixed).

**Scope correction found before writing any code**: the "4 files, 21
hypotheses" framing in this task's own header is imprecise. Only
`physics.md` (HYP-P1..P14) and `search_complexity.md` (HYP-S1..S7) define
`HYP-P*`/`HYP-S*` ids — 21 exactly, matching [[TASK-0321]]'s count.
`ceiling.md` defines none of its own (cross-references only).
`reference_register.md` defines none in this namespace either — it
already carries its **own** self-contained "Coverage summary" index over
a *different*, pre-existing id namespace (H9, H6.1, H4.1, ...). Building
a second index over that file would have duplicated an already-solved
problem, not fixed one. The index below covers exactly the 21 that
[[TASK-0321]] measured.

**Index**: `.claude/hypotheses/INDEX.md`, generated (not hand-copied) by
`--build-index`, sorted by citation count. One-line pointer added to the
top of `physics.md` and `search_complexity.md` (no hypothesis content
touched, per this task's and [[TASK-0321]]'s shared constraint). The
checker's own drift class (`index-drift`) fails if the checked-in file
and a fresh regeneration disagree, so it cannot silently fall behind its
own source files.

**Wiring**: matched [[TASK-0319]]'s own precedent exactly rather than
inventing a second convention — `doc_parity.py` is itself **not** in
`.ai/tools/pytest_local.py`'s `PRESETS` (checked directly); it is run
standalone (`python3 -m pytest .ai/tools/test_doc_parity.py`, per its own
docstring). This checker follows the same shape: standalone script +
standalone test, same invocation convention, not added to `PRESETS`. This
repo has no git pre-commit hook and no CI config (checked: `.git/hooks/`
has only samples, no `.yml`/`.yaml` workflow files exist) — "the existing
pre-commit/CI-equivalent check point" *is* this doctest-style standalone
convention, not a hook to attach to.

**Pattern-set calibration (Planned Validation)**: ran the claim-language
patterns against the real corpus before trusting them. Two real false
positives found and fixed: `is closed` matching `closed-form` (a
mathematical sense, added a negative-lookahead) and `closed by
definition` in `WORKFLOW.md`, which the naive per-line exclusion missed
because the phrase line-wraps (`closed by\n  definition`) — fixed by
normalising whitespace before matching, not by adding more patterns.
Known remaining false positive, documented rather than chased: "remains
open"/"remain open" in `2026-08-26-organiser-clarifications.md` refers to
organiser Q&A items, not a hypothesis route — left in `_FALSE_POSITIVE_
CONTEXT_RE`'s known-gaps comment rather than over-fit with a third regex
tuned to one file.

**Run once against the real register + real docs** (results:
`__WORK_IN_PROGRESS__/results/tasks/0322_hyp_consultation_enforcement/
findings.json`), not fixed, per this task's own scope:

- **Staleness (2)**: `HYP-P10` (status 2026-07-22) and `HYP-P12` (status
  2026-07-24) are each cited by a same-day-2026-09-03 task
  ([[TASK-0323]], [[TASK-0321]] respectively) newer than their own dated
  verdict. Neither is a fresh contradicting finding on inspection —
  [[TASK-0323]] explicitly marks `HYP-P10` "already dated, not in scope"
  and [[TASK-0321]]'s citation of `HYP-P12` is itself the meta-measurement
  that led to filing this task — but both are exactly the mechanical
  shape the staleness class exists to surface for human review, not to
  silently resolve.
- **Uncited-claim (4)**, most notable: `REVERSE_CTQW_BRIEF.html` (the
  document [[TASK-0321]]'s own incident was about) line 235 —
  "**Closed**, and this corrects an earlier draft... is not an open
  route" — states the correct, current verdict but still never cites
  `[[HYP-P9]]` anywhere in the file. **The checker would have caught the
  original wrong-direction claim, and still flags the corrected version
  today** for the same missing-citation reason — direct confirmation this
  gate catches the real incident's shape, not just a synthetic
  reconstruction of it. `CTQW_CONTRIBUTION_BRIEF.html`'s "objection is
  now closed" (re: ENM validity, adjacent to HYP-P8/HYP-P9 territory) is
  a second plausible real instance. The other two
  (`2026-08-26-organiser-clarifications.md`, "remains open" ×2) are the
  documented false positive above, left in the findings file rather than
  silently dropped so a human can confirm the calibration judgment.

**Measurement discrepancy noted, not corrected** (past Done task,
immutable per this session's norm): [[TASK-0321]]'s own "7 of 21 have a
dated Status" and per-hypothesis citation counts (e.g. `HYP-P1`: 16) do
not reproduce under this checker's stricter definitions — a dated Status
requires the date to sit inside the bold `**Status...**` clause itself
(this checker finds 4: `HYP-P5`, `HYP-P9`, `HYP-P10`, `HYP-P12`; `HYP-P14`'s
"2026-09-01" belongs to a separate `**Filed:**` line, not its Status,
which literally reads "hypothesis, not finding"), and citation counts
using a real id-boundary match (`HYP-P1` matched as `HYP-P1\b`, not as a
prefix of `HYP-P10`..`HYP-P19`) are lower than a loose substring match
would give (3 exact vs 19 substring-inflated, close to TASK-0321's own 16
+ 3 new same-day citing tasks). Both readings are plausible measurement
methodology differences, not accusations — flagged so a future reader
doesn't treat either number as more authoritative than the method behind
it.

**Not done, deliberately out of scope**: fixing any of the findings above
(TASK-0323/TASK-0324's territory for the staleness/verdict class; the
uncited-claim class currently has no owning task — an Architect call
whether one is warranted, not decided here).

Files: `.ai/tools/hyp_register_check.py`,
`.ai/tools/test_hyp_register_check.py`, `.claude/hypotheses/INDEX.md`,
`__WORK_IN_PROGRESS__/results/tasks/0322_hyp_consultation_enforcement/findings.json`.
Edited (pointer line only): `.claude/hypotheses/physics.md`,
`.claude/hypotheses/search_complexity.md`.

**Correction, 2026-09-03 (Architect, filing TASK-0326):** `STATUS_RE`
matched only `**Status,`/`**Status:` — missing every verdict actually
phrased `**Status update,`/`**Status confirmed,`/`**Correction,`/
`**Resolved ...` in the real register (HYP-S1/S2/S3/S4/S5/S6/P6, several
written by [[TASK-0323]]/[[TASK-0324]] themselves, using exactly the
phrasing this checker didn't recognize). Undercounted 7 of 21 hypotheses
as "no verdict recorded." This is the checker's own version of the
problem it exists to catch — found while manually verifying TASK-0324's
"21/21 now dated" claim against a freshly-rebuilt index for the repo
owner, not by the checker's own tests (which only exercised the
patterns the code already handled). Fixed
(`\*\*(?:Status\w*|Correction|Resolved)\b[^*]*\*\*`), two regression
tests added (positive: all four missed phrasings; negative: a
descriptive "**Status in the literature:**" bold span with no date
still correctly parses as undated). True count after the fix: **18/21
dated**, not 21/21 (TASK-0324's claim) or 11/21 (this checker's own
pre-fix output). Genuinely undated: HYP-P7, HYP-P13, HYP-P14 — the
latter two are this week's newest hypotheses, plausibly still open
rather than missed.
