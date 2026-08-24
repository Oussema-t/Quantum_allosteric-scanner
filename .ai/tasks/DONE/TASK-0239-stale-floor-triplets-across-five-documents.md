# TASK-0239 — Refresh the stale floor/actual triplets cited across five documents

- Status: Done
- Assignee: unassigned (suggest Implementer; mechanical, but needs judgment on
  historical-vs-current citations)
- Priority: **High — one of the stale numbers is in the Phase 1 submission draft**
- Filed: 2026-08-24 by Reviewer
- Parent: [[TASK-0238]] Leg B1
- Related: [[TASK-0217.001]] (the commit that caused the drift), [[TASK-0184]]
  (submission document), [[TASK-0195]] (RESULTS.md write protection)

## Context

[[TASK-0238]]'s wiring check ran `scripts/run_challenge.py` fresh on all three
mandatory targets and found the published floor/actual triplets no longer
reproduce:

| target | floor pub | floor now | AUC pub | AUC now | margin pub | margin now |
|---|---|---|---|---|---|---|
| KRAS_G12C | 0.4818 | 0.5296 | 0.5901 | 0.5565 | +0.1083 | **+0.0269** |
| BCR_ABL1 | 0.5817 | 0.5031 | 0.5266 | 0.5408 | −0.0551 | **+0.0377** |
| CARDIAC_MYOSIN | 0.5679 | 0.4538 | 0.5176 | 0.5485 | −0.0503 | **+0.0947** |

Cause: commit `1924e5e` ([[TASK-0217.001]]) fixed a live array-correspondence
bug in `labels.functional_indices` (holo-space heavy-atom contact indices used
as apo-space indices; 10 of 13 targets exposed). That commit re-pinned
fpocket's golden AUC correctly but did not refresh the headline triplets.

`grep -rn "0\.4818\|0\.5817\|0\.5679" --include="*.md"` returns **56 hits**
across `EXECUTION_PLAN.md`, `ALGORITHM_REGISTER.md`, `RESULTS.md`,
`COMPETENCE_MAP.md`, and `documentation/PHASE1_SUBMISSION_DRAFT.md`.

## Why this matters

1. **`documentation/PHASE1_SUBMISSION_DRAFT.md:146` cites 0.4818** as a current
   number. It goes to the challenge organisers.
2. **`COMPETENCE_MAP.md:240`** claims KRAS_G12C's actual "now clears its own
   floor by +73.7%". The current margin is +0.0269, roughly 4× weaker.
3. **Two targets flip sign.** BCR_ABL1 and CARDIAC_MYOSIN are described
   throughout as failing the floor. Under current code their point estimates
   clear it; their negative diagnoses (`NO_SIGNAL_IN_APO`, re-confirmed) come
   from the chance bar instead. Any text attributing their negatives to the
   floor gate is now wrong.

## Scope

- Not a blanket find-and-replace. `RESULTS.md`'s own preamble mandates that a
  prior run's numbers are never overwritten — the methodology delta *is*
  sometimes the finding. Historical citations stay; **current-claim** citations
  must be corrected or annotated.
- Classify each of the 56 hits as *historical record* (leave, optionally
  annotate with a pointer to TASK-0238's section) or *live claim* (correct).
- `PHASE1_SUBMISSION_DRAFT.md` and `COMPETENCE_MAP.md` are certainly live
  claims. `EXECUTION_PLAN.md`'s completed-row narratives are largely historical.
- Re-run `scripts/run_challenge.py --target KRAS_G12C BCR_ABL1 CARDIAC_MYOSIN`
  and take the triplets from that run, not from TASK-0238's table, so the
  refresh has its own provenance.
- Fix the prose wherever a negative is attributed to the floor gate on
  BCR_ABL1 / CARDIAC_MYOSIN.
- Second, smaller inconsistency to resolve while in here: CARDIAC_MYOSIN's
  floor is cited as **0.7921** at `EXECUTION_PLAN.md:265` and **0.5679** at
  `ALGORITHM_REGISTER.md:154`. Both predate the drift; at least one was already
  wrong.

## Acceptance

- [x] Fresh `run_challenge.py` triplets recorded with a date and commit SHA.
- [x] All 62 hits (56 grew to 62 during this task, other threads still
      active) classified historical vs live; live ones corrected.
- [x] `PHASE1_SUBMISSION_DRAFT.md` carries current numbers.
- [x] `COMPETENCE_MAP.md:240`'s +73.7% claim addressed — **not literally
      restated as a new percentage** (that figure is ceiling-relative,
      `(actual−floor)/(ceiling−floor)`, and this task did not re-run
      ceiling — out of scope, flagged explicitly, not silently assumed
      unchanged). The corrected simple point-estimate margin (+0.0269,
      ~4× weaker) is stated, with an explicit note that +73.7% cannot be
      honestly restated without a fresh ceiling search.
- [x] Floor-attributed negatives for BCR_ABL1 / CARDIAC_MYOSIN re-attributed
      to the chance bar, everywhere corrected; verified no other prose in
      the 5 documents makes this attribution uncorrected.
- [x] CARDIAC_MYOSIN 0.7921-vs-0.5679 discrepancy resolved: **not an
      error** — two legitimate, correctly-dated historical vintages either
      side of TASK-0124's structural re-anchor.
- [x] Guard proposed (not built, per this item's own text): pinned-golden
      regression test over the 3-target triplet, mirroring TASK-0206's
      fpocket pin.

## Constraint

Report drift in **both** directions with equal prominence. Two of the three
corrections make this project's results look *better* than currently published.
That is exactly as reportable as the KRAS_G12C weakening.

## Done

**2026-08-24, Implementer D.**

**Provenance**: fresh `python3 scripts/run_challenge.py --target KRAS_G12C
BCR_ABL1 CARDIAC_MYOSIN` at commit `821dbfb`, output in `/tmp/task0239_run/`
(not committed — scratch). Independently reproduces [[TASK-0238]] Leg B1's
own numbers to 3-4 decimals (floor 0.5296/0.5031/0.4538, actual
0.5565/0.5408/0.5485) — two separate code paths agree, not a single
measurement trusted alone.

**All 62 hits classified.** `RESULTS.md` (~55 of the 62): every one checked
is a dated historical row describing the pipeline's actual state on the day
it ran — correctly so, since most predate both [[TASK-0124]]'s structural
re-anchor and [[TASK-0217.001]]'s bug fix. Left untouched, per this file's
own explicit no-silent-overwrite preamble; new row 80 added recording this
task's own resolution (does not edit any prior row). `documentation/
PHASE1_SUBMISSION_DRAFT.md` (1 hit, Finding 3): the one document where the
stale triplet is presented as *current*, not historical — corrected in
place (not annotated), plus a dated banner entry and a fix to §2.5's own
footnote (see below). `COMPETENCE_MAP.md` (21 hits): a genuinely "live"
document with its own established convention (stacked, dated, non-
destructive `SUPERSEDED`/`CAVEAT` blockquotes — confirmed by reading its
existing TASK-0155/TASK-0193/TASK-0206 precedents before adding anything).
3 new CAVEATs added in that exact style: the headline KRAS_G12C/BCR_ABL1
table, the CARDIAC_MYOSIN section's own declared-current ending, and the
discriminability-audit table. No prior number edited in place, matching
every existing CAVEAT in the document. `ALGORITHM_REGISTER.md` (1 hit) /
`EXECUTION_PLAN.md` (5 hits, 1 corrected): the fpocket-comparison
paragraphs already carried a [[TASK-0206]]-dated superseding annotation for
fpocket's *own* AUC drift (an unrelated, earlier correction) — added a
second, parallel annotation for the quantum floor/actual drift, same
convention. `EXECUTION_PLAN.md`'s other 4 hits (1C.20/TASK-0132 row, the
TPE ceiling-search row, the TASK-0130 headline row) are dated "Done"
narratives correctly describing their own day's pipeline state — left
untouched, per this task's own Scope note that this file's completed-row
narratives are largely historical.

**Both directions reported with equal prominence, per this task's own
Constraint** — every one of the 5 new/edited citations states plainly:
KRAS_G12C's margin is ~4× weaker than published; BCR_ABL1 and
CARDIAC_MYOSIN both flip from below-floor to above-floor, with their
`NO_SIGNAL_IN_APO` diagnosis (re-confirmed this run, unchanged) now
correctly attributed to the chance bar (CI-overlap / permutation null)
rather than the floor gate. Searched all 5 documents directly for any
other prose attributing either target's negative to the floor gate
specifically — none found beyond what's now corrected.

**Second inconsistency resolved, not silently fixed as an error**:
0.7921 (`EXECUTION_PLAN.md:265`, TASK-0132, dated 2026-07-19) and 0.5679
(`ALGORITHM_REGISTER.md`, TASK-0163, dated 2026-07-27/28) are two
legitimate historical vintages either side of [[TASK-0124]]'s 2026-07-20
CARDIAC_MYOSIN apo re-anchor (5TBY→8QYP) — confirmed by date, and
independently confirmed in prose already present in `COMPETENCE_MAP.md`'s
own CARDIAC_MYOSIN section ("floor drops 0.7921→0.5679"). Not a citation
bug; `ALGORITHM_REGISTER.md`'s 0.5679 is simply the later of the two, and
itself now further superseded by this task's own TASK-0217.001 correction
(→0.4538).

**Guard proposed, not built** (per this task's own item text): a
pinned-golden regression test over the 3-target floor/actual/margin
triplet through `run_challenge.py`'s real path, checked-in JSON, tolerance-
bounded assertion — mirroring [[TASK-0206]]'s already-working fpocket pin
(`tools/fpocket/PROVENANCE.json`). Would have caught this exact drift at
the moment [[TASK-0217.001]] landed rather than 10 days later via a
reviewer's independent wiring check. Flagged as the concrete next task, not
implemented here (per this task's own item text, "not necessarily built").

**Mid-task complication, handled**: this branch is a shared, multi-thread
working tree (per this project's own operating convention) — `HEAD` moved
from `1539d45` to `96ba8f0` (6 intervening commits from other threads)
while this task was in progress. Checked each: none touch
`labels.py`/`run_challenge.py`'s floor/actual path (TASK-0235's own
"BCR_ABL1 ceiling reverses" is a *different* machinery, the ANM-ceiling
backbone-fidelity line of work, confirmed by reading its own commit's file
list before assuming it was relevant) — this task's own numbers remain
valid. `RESULTS.md`'s own Leg B1 section, initially encountered as another
thread's (TASK-0238, Reviewer-thread Opus) uncommitted work, was
independently committed by the time this task finished — re-based row 80's
insertion onto the final, clean, committed `HEAD` rather than the earlier
uncommitted snapshot, avoiding a repeat of [[TASK-0229.004]]'s own
commit-collision mistake. `documentation/PHASE1_SUBMISSION_DRAFT.md`'s own
concurrent addition (TASK-0238's new §2.3b, still uncommitted as of this
task's own close) was not touched — surgical-splice procedure used
throughout (restore clean `HEAD`, edit, verify diff, stage, restore the
mixed working-tree file) so neither thread's work is lost or misattributed.

Tests: no `src/` code changed (documentation-only task) — full suite not
re-run (nothing to regress).

Artifacts: `RESULTS.md` row 80; `documentation/PHASE1_SUBMISSION_DRAFT.md`
(Finding 3 corrected, banner entry, §2.5 footnote fixed); `COMPETENCE_MAP.md`
(3 CAVEATs); `ALGORITHM_REGISTER.md`/`EXECUTION_PLAN.md` (1 superseding
annotation each).
