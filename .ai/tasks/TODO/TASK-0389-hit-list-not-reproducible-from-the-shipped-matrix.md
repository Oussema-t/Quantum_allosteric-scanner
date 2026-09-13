# TASK-0389 — "A hit list cannot disagree with the matrix it came from" is unverifiable as shipped

- Status: TODO
- Owner: Implementer
- Priority: Medium. Cheap to fix, and the claim currently costs more than it buys.
- Filed: 2026-09-13 by Reviewer thread
- Source: [[REVIEW-2026-09-13-adversarial-submission-package]] §E7, F24
- Related: [[TASK-0384]]

## The problem

§6 claims *"a hit list cannot disagree with the matrix it came from."* The
external reviewer scanned **every single-residue seed row of all four matrices**,
plus GDP-contact, P-loop and switch-II seed sets for KRAS, under both
seed-inclusive and seed-exclusive ranking. **None reproduces any shipped top-5.**

This independently confirms item 24 from the 2026-09-11 review, which was left
open: the seed set is not shipped.

## The likely explanation is benign

The matrix is the **default operator**; the hit list is `H_new` with the five
potentials. Different operators, so different rankings — no inconsistency, just
two artefacts from two configurations with nothing in the package saying so.

**But the claim as written is falsifiable-sounding and a reader cannot verify
it**, so it is worth less than the sentence costs. A reviewer who tries what the
external reviewer tried concludes the deliverables disagree.

## Two fixes, pick one

1. **Ship the provenance.** Add the seed residue set and the operator identity to
   the CSV header (folds into [[TASK-0384]] Part 2, same edit, no extra cost) —
   then the claim becomes true *and* checkable, which is strictly the best
   outcome.
2. **Soften the claim** to "emitted in one pass from one runner", dropping the
   falsifiable-sounding "cannot disagree".

Reviewer's read: **do 1, and keep the strong sentence.** We are already editing
that header for [[TASK-0384]]; adding two more lines converts our weakest
verifiability claim into one of the strongest. Option 2 is the fallback if the
operator/seed provenance cannot be established quickly from the run config.

## Watch for

If option 1 is taken, **confirm the shipped matrix really was produced by the
default operator** before writing it down. Writing the wrong operator into the
header is worse than the current vague claim — it converts an unverifiable
sentence into a checkably false one.

## Done when

Either the header carries verified seed + operator provenance, or §6's sentence
is softened. Not both, and not neither.
