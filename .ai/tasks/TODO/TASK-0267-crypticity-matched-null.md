# TASK-0267 — A crypticity-matched null

- Status: TODO (**blocked on [[TASK-0266]]** — do not start until its verdict lands)
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

- [ ] Add a **crypticity-matched** patch null, following the existing
      rejection-sampling convention exactly (`compact_patch_matched`'s
      `target_*` + `tol` + `max_attempts` shape, and its discipline of raising
      `RuntimeError` on infeasibility rather than silently returning an
      unmatched draw).
- [ ] Match on: size, compactness, **apo openness** (fpocket-derived fraction
      of the patch already open in apo, the same quantity [[TASK-0254]] part B
      computes), and optionally hop distance from the seed.
- [ ] Report **feasibility per target**. [[TASK-0143]]'s structural-graph null
      was INFEASIBLE on 4/7 real targets under a tight convention — a matched
      null that cannot be drawn is a reportable result, not a failure to hide.
- [ ] Run CTQW, geometry, fpocket and SASA against it on the cryptic targets.
      The question: does any score prefer the *true* pocket over equally-closed
      decoys?

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

- [ ] New matched-null function in `nulls.py`, with tests matching that
      module's existing conventions.
- [ ] Feasibility table per target.
- [ ] p-values for every score arm against the new null, cluster-robust.
- [ ] Explicit statement of both limits above.

## Constraint

Only run this if [[TASK-0266]] says the cryptic lean survives burial control.
If burial explains it, this null tests a signal already known not to exist,
and the effort belongs on [[TASK-0269]] instead.
