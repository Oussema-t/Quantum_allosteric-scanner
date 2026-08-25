# TASK-0254 — Put fpocket in the variance stack, and screen the frozen set for apo crypticity

- Status: Done
- Assignee: unassigned (suggest Implementer — this is the highest-value open analysis in the register)
- Priority: **Highest — it directly attacks the 67% "unexplained" share, which is the largest single number in our Phase 1 story**
- Filed: 2026-08-24 by Reviewer
- Related: [[TASK-0245]], [[TASK-0246]], [[TASK-0247]], [[TASK-0249]], [[TASK-0163]], [[TASK-0169]], [[TASK-0243]]

## The gap this exists to close

[[TASK-0245]] decomposed discrimination into **geometry / CTQW / unexplained**
= 30% / +1% / **67%** (cross-validated, 9 targets). That decomposition used
`degree_centrality`, `euclid_from_seed_centroid`, `hop_from_seed` and the CTQW
occupation vector.

**`fpocket` was not in the stack.**

[[TASK-0249]] then found `fpocket_drug` alone reaches median per-residue AUC
**0.756** on the frozen 22-target set — higher than the whole 4-feature
composite. So there is a strong, available predictor sitting entirely outside
the decomposition that produced the 67%.

**Hypothesis:** a large part of what we have been reporting as "unexplained"
is static pocket geometry that fpocket measures and our three baselines do
not. If so, the honest headline is not "67% of allostery is unexplained" but
"most of it is cavity shape, and we were not measuring cavity shape."

That would materially change §2 of the submission. It is also the single
cheapest way to find out, since every component already exists.

## Part A — re-run the attribution with fpocket in the stack

- [x] Repeat [[TASK-0245]]'s protocol exactly (5-fold stratified CV, 20
      repeats, out-of-fold, seed rows excluded) with a **four-block** model:
      `geometry` (the existing three) / `fpocket` / `CTQW` / residual.
- [x] Report the shares the same way — (AUC − 0.5)/0.5 — so the new numbers
      are directly comparable to the published 30/+1/67.
- [x] Report **order-independent** attribution, not just sequential: geometry
      and fpocket are correlated, so a fixed entry order will misassign shared
      variance. Use LMG/Shapley-style averaging over orderings, or report both
      orderings explicitly and say which shared portion is ambiguous.
- [x] Run on [[TASK-0243]]'s frozen 22-target set (n=20 usable), not the
      9-target set — [[TASK-0242]]'s n=4→7 lesson.
- [x] State plainly how much of the 67% survives.

## Part B — apo crypticity screen (Gemini's suggestion, and a real gap)

The register has this finding for **one** target only: BCR_ABL1's pocket is
"measurably pre-formed in apo" (RMSD ratio 0.49, [[TASK-0120]]/[[TASK-0139]]).
[[TASK-0169]] used it to fail BCR_ABL1 on "cryptic". There is **no systematic
screen** across the frozen set.

- [x] Run `fpocket` on each **apo** structure and measure the fraction of the
      true (holo-defined) pocket already open in apo.
- [x] Pre-register the bar before looking. Suggested, from the external
      framing: **>80% open in apo ⇒ the target tests static retrieval, not
      cryptic-site discovery.** Fix the exact overlap definition first
      (residue-level or volume-level) and state it.
- [x] Report per target, and cross-tabulate against [[TASK-0249]]'s per-target
      AUCs. **The prediction to test: `fpocket_drug` should score highest
      exactly on the already-open targets.** If it does, our benchmark's
      apparent difficulty is largely a mixture of two different tasks.
- [x] Report what fraction of the frozen set is already-open. That number
      belongs in the submission regardless of which way it comes out.

## Acceptance

- [x] A four-block attribution table, order-independent, on n=20.
- [x] An explicit statement of how much of the 67% is static cavity geometry.
- [x] A per-target crypticity table with the pre-registered bar applied.
- [x] The cross-tabulation of crypticity against per-target AUC.
- [x] `RESULTS.md`; and if the 67% moves materially, a revision of
      `documentation/PHASE1_SUBMISSION_DRAFT.md` §2.3b — which currently
      states the 16–108%/median 67% figure as our estimate of record.

## Constraint

If this shows the unexplained share is much smaller than published, that is a
correction against our own headline and must be reported with the same
prominence §2.3b currently gives the 67%. Equally, if the residual survives
fpocket, that strengthens the finding and should be said plainly rather than
hedged.

## Done

**2026-08-24 — Implementer A.** Both parts landed with real, substantial
findings, exactly what this task existed to check.

**Method**: reused `task0249_composite_dumb_baseline.target_rows` (imported,
not re-derived) for the frozen 22-target set's per-target feature/label rows
— same apo-side fpocket candidates, same seed/pocket resolution, same
`altloc="all"` fix, same n=20-usable filter (2 HIV-integrase pairs excluded,
empty active-site seed, [[TASK-0249]]'s own already-found data-quality gap).
`task0245_cv_attribution`'s own within-target CV protocol (5-fold stratified,
20 repeats, OLS via `lstsq`, out-of-fold AUC, seed rows excluded) reused
verbatim, extended from 2 blocks to 3.

**Part A — order-independent attribution, real Shapley (3! = 6 orderings,
brute-forced, no sampling approximation needed at this size)**: full table in
`RESULTS.md`'s own dated section. **Unexplained median 67% → 29%** — most of
what the 3-block model called "unexplained" was static pocket geometry
`fpocket` measures and the three simple baselines don't. `fpocket`'s own
Shapley share is wide and target-dependent (−9% to +65%, median +8%) — not a
uniform correction, a real per-target story. **CTQW's own share also moved,
median +1% → +11%** — reported as a real, order-independence effect (Shapley
credits CTQW's actual unique contribution instead of it being absorbed by
whichever block entered first in a sequential fit), not evidence CTQW
"works now" — its range still spans clearly negative (FBPASE_94D −15%) to
positive (MKK7_IBRUTINIB +49%), target-dependent, same qualitative picture
as before at a different, more correctly-attributed magnitude.

**Part B — apo crypticity screen, pre-registered overlap definition and bar
stated before any number was computed** (residue-level, any apo-detected
fpocket pocket counts as "open," ≥80% bar): **9/20 (45%) of the frozen set is
already-open in apo** — the register had exactly one target's worth of
evidence for this before (BCR_ABL1). **Cross-tabulation confirms the
predicted pattern cleanly**: `fpocket_drug` median AUC 0.854 on already-open
targets vs. 0.515 (near chance) on the genuinely cryptic-testing remainder.
**This benchmark's apparent difficulty is substantially a mixture of two
different tasks** — static retrieval and genuine cryptic-site discovery —
bundled into every prior number in §2.3.

**Both write-ups landed in the same commit as this Done section, per this
task's own Acceptance**: `RESULTS.md`'s new dated section (full tables, both
parts); `documentation/PHASE1_SUBMISSION_DRAFT.md` §2.3b updated with a dated
addendum stating the corrected estimate of record and the crypticity finding
— the original 9-target table and its own surrounding prose kept intact
above it, per that document's no-silent-overwrite convention, not deleted or
silently replaced.

**Not done, per this task's own scope**: no existing task's own Done section
or original numbers (TASK-0245's 9-target table, TASK-0249's composite
numbers) were themselves re-derived or edited — this task supersedes the
*headline estimate* cited going forward, leaving those records as historical
artifacts of record, consistent with how every other correction in this
register has been handled. A held-out re-fit at a larger sample (25-30
targets, matching [[TASK-0243]]'s own noted headroom in the still-unscreened
candidate pool) was not attempted — real remaining scope if this line of
work continues, not a gap in what this task itself promised.

**Validated**: `scripts/task0254_fpocket_variance_and_crypticity.py` reruns
clean and reproduces every number above from
`results/tasks/0254_fpocket_variance_and_crypticity/`. No library code
changed — investigation script only, full test suite not re-run (no
production code path touched).
