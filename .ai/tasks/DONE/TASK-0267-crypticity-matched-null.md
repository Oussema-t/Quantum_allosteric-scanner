# TASK-0267 — A crypticity-matched null

- Status: Done
- Assignee: **Implementer D** (same thread as TASK-0266, which decides whether this runs)
- Priority: Medium — conditional on TASK-0266
- Filed: 2026-08-25 by Reviewer
- Related: [[TASK-0266]], [[TASK-0158]], [[TASK-0167]], [[TASK-0143]], `src/allostery/nulls.py`

## What is missing from our null family

`nulls.py` rejection-samples matched nulls on **size** and **radius of
gyration** (`compact_patch_matched`, `graph_walk_patch_matched`). Nothing
matches on **burial or apo openness**.

That gap matters for cryptic-pocket claims specifically: if the true pocket is
closed in apo and the decoys are open, then *any* score preferring closed
regions wins, and we would call it cryptic-site detection when it is burial
detection. [[TASK-0266]] tests that confound directly at the feature level;
this tests it at the null level, which is the stronger form.

## Design

- [x] ~~Add a **crypticity-matched** patch null...~~ **Not built — see Done.
      Gated off by this task's own Constraint.**
- [x] ~~Match on: size, compactness, apo openness...~~ **N/A, not run.**
- [x] ~~Report feasibility per target.~~ **N/A, not run.**
- [x] ~~Run CTQW, geometry, fpocket and SASA against it...~~ **N/A, not run.**

## Two structural limits — state them in the write-up, do not discover them late

1. **A candidate-based null is impossible here.** Genuinely cryptic pockets
   are by definition not in fpocket's apo candidate list — that *is* the 36%
   stage-1 failure ([[TASK-0253]]). So this must be a residue-patch null and
   cannot reuse the two-stage apparatus.
2. **The decoys may not be true negatives.** H9 ([[TASK-0229.001]]) argues
   allostery may be intrinsic to all dynamic proteins; if any patch can become
   cryptic, a matched decoy is not a clean negative. This bounds what a
   positive can mean and must be said in the result, not buried.

## Acceptance

- [x] ~~New matched-null function in `nulls.py`...~~ **N/A — gated off.**
- [x] ~~Feasibility table per target.~~ **N/A — gated off.**
- [x] ~~p-values for every score arm...~~ **N/A — gated off.**
- [x] Explicit statement of both limits above — **stated in Done, for the
      record, even though the null itself was never built.**

## Constraint

Only run this if [[TASK-0266]] says the cryptic lean survives burial control.
If burial explains it, this null tests a signal already known not to exist,
and the effort belongs on [[TASK-0269]] instead.

## Done

**2026-08-26, Implementer D.**

**Gating condition checked directly against [[TASK-0266]]'s own actual
Done section, not assumed from a summary** — that task's own explicit
recommendation: *"[[TASK-0267]] (crypticity-matched null) is not worth
running — no significant signal left to protect."* The measured result
this task's own Constraint gates on: CTQW's crypticity-stratified,
cluster-robust added-last lean was **p=0.0736 uncontrolled** (never
clearing even an uncorrected 0.05 bar) and weakened further to **p=0.239**
once real SASA burial was controlled for — the cryptic-vs-open gap
roughly halved (+5.53%/−0.10% → +2.17%/+0.01%). Per this task's own
Constraint, worded precisely for exactly this outcome ("if burial
explains it, this null tests a signal already known not to exist"): **not
built, not run.**

**Not a rubber-stamp close — checked, not just cited**: [[TASK-0266]]'s
own verdict was explicitly *not* a clean "vanishes" (a small positive
residual remained, +2.17% vs. +0.01%, direction held) — the Constraint's
own literal wording ("if the lean survives... run this") could be read as
technically satisfied by direction alone. Rejected that reading: the
Constraint's own accompanying sentence ("a signal already known not to
exist") makes clear the gate is about *significance*, not sign — and the
lean was never significant, before or after the control. A null built to
test a p=0.24 residual with no prior significance to protect would not be
distinguishing a real effect from a matched confound; it would be
characterising noise at higher cost. This reasoning is recorded here
explicitly rather than left as an unstated judgment call.

**This task's own two structural limits, stated for the record per its
own Acceptance, independent of whether the null was ever built** (both
apply to *any* future attempt at this null, should the gating condition
ever flip on a re-measurement):
1. **A candidate-based null is impossible here** — genuinely cryptic
   pockets are by construction absent from fpocket's own apo candidate
   list (the 36% stage-1 failure, [[TASK-0253]]), so any future attempt
   must be a residue-patch null and cannot reuse the two-stage apparatus.
2. **The decoys may not be true negatives** — H9 ([[TASK-0229.001]])
   argues allostery may be intrinsic to all dynamic proteins; if any
   patch can become cryptic, a matched decoy is not a clean negative,
   bounding what a future positive result could mean.

**Recommendation, per this task's own Constraint**: effort redirected to
[[TASK-0269]] (PocketMiner environment + run), already filed and assigned
to a different implementer thread — the actual open question left by
[[TASK-0260]] is whether the *purpose-built* cryptic-opening predictor
closes the residual, not a further null construction around a signal that
was never there.

Tests: none — no code written, per this task's own Constraint gating the
entire build.

Artifacts: none new. This file's own Done section is the artifact.
