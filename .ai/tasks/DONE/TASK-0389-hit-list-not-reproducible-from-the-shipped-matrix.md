# TASK-0389 — "A hit list cannot disagree with the matrix it came from" is unverifiable as shipped

- Status: Done
- Owner: Implementer
- Priority: Medium. Cheap to fix, and the claim currently costs more than it buys.
- Filed: 2026-09-13 by Reviewer thread
- Source: [[REVIEW-2026-09-13-adversarial-submission-package]] §E7, F24
- Related: [[TASK-0384]]
- Done: 2026-09-14, Implementer B

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

## Done (2026-09-14, Implementer B)

**Took option 1** (ship provenance), per the task's own recommended read — the
claim is now true, checkable, and verified, not asserted. §6's sentence was not
touched: it is literally accurate as written and the one real exception is now
fully disclosed where a scorer can see it, at no page-budget cost.

**Watch-for instruction honored**: confirmed the operator before writing
anything down, not assumed. `_winner_index` in each target's own `verdict.json`
is `0` for KRAS_G12C, BCR_ABL1 and CARDIAC_MYOSIN — index 0 is `H_new_default`
in `_make_candidates_builder`'s own candidate list (`[H_new_default, H10_
disorder_suppressed]`), so **H_new_default won for all three**, cross-checked
against each file's own `AUC_apo_Hnew_default == AUC_apo_Hnew_optimised`
(already an established finding, TASK-0370 item 25). Read
`scripts/run_challenge.py:441-452` directly: `winner_occ` (source of the hit
list) and the matrix are computed from the *same* `winner_H` eigendecomposition
— one diagonalization, reused, not two independent computations that happen to
agree.

**Did not stop at code-reading — reconstructed the actual claim end to end**,
since a shared operator alone doesn't prove reproducibility (the true seed is
multi-residue, and `time_averaged_ctqw_converged(coherent=False, ...)`'s
multi-source semantics needed checking, not assumed): read
`propagators.py:1088-1099` — `coherent=False` is exactly the unweighted mean
of each seed residue's own single-source converged occupation. Using the seed
sets already in `artefacts/README.md` (TASK-0370 item 24, not previously
shipped) — KRAS_G12C 18 residues (GDP/Cys12 contact), BCR_ABL1 26 (nilotinib/
ATP-site), CARDIAC_MYOSIN 18 (mavacamten-site) — averaged the shipped
per-target matrix's own rows over each seed, excluded the seed residues (the
pipeline's own exclusion logic, confirmed in item 24), ranked, and compared to
each target's shipped `hit_list.json`:

| target | reconstructed top-5 (rank order) | shipped top-5 |
|---|---|---|
| KRAS_G12C | 31, 122, 33, 121, 29 | 31, 122, 33, 121, 29 |
| BCR_ABL1 | 402, 311, 310, 301, 338 | 402, 311, 310, 301, 338 |
| CARDIAC_MYOSIN | 682, 683, 681, 680, 133 | 682, 683, 681, 680, 133 |

**Exact match, in rank order, on all three** — the external reviewer's
non-reproduction traces to seeding methodology (single-residue rows, or a
seed set that wasn't this repo's own true active site), not a real
inconsistency between the shipped artefacts.

**MYC_MAX tested too, and genuinely does not reconstruct this way** — checked,
not assumed to be the exception by analogy. Averaging its matrix's rows over
its own 5-residue seed gives `[943, 246, 243, 242, 225]` seed-inclusive (the
seed can't be excluded here — MYC_MAX's own seed *is* its shipped hit list,
already-disclosed circularity, TASK-0370 item 24) against the shipped
`[943, 246, 925, 226, 243]` — 3/5 overlap, wrong set. Traced to
`run_challenge.py`'s own `run_target_no_ground_truth` path
(lines 250-295): MYC_MAX's matrix comes from bare `H_new` alone, but its hit
list is `consensus_ranking` across **four** operators (H_new/H10/H2/H14) — a
structurally different computation, not the same winner-operator path the
other three targets use. This is the one target with no ground truth, and the
code's own comment (line 271-274) already says the ranking is "the actual
consensus-across-operators output, not this single matrix" — confirmed
empirically here, not just read.

**Shipped**: added a "Hit-list provenance (TASK-0389)" block to
`Connectivity_Matrices.csv`'s header (17 new comment lines, 12→31 total) —
the operator identity, the reconstruction rule (mean of seed rows, seed
excluded), all three seed sets in the same compressed range notation
`artefacts/README.md` already uses (cross-checked against my own expanded
lists before reuse, not retyped blind), and the MYC_MAX exception stated
plainly with its own mechanism. One line added to
`SUBMISSION_PACKAGE/README.md`'s File 4 section stating the same, per
TASK-0384's own precedent ("say so, it's checkable"). Round-trip re-verified
after the header edit: 379,327 total rows, unchanged per-target counts,
`comment='#'` skip still lands exactly on the header row.

**Not done / out of scope**: no change to `PHASE1_SUBMISSION_V4.md` — §6's
sentence needed no softening, since it is literally true (one runner, one
pass) and the MYC_MAX exception is now disclosed for free in the CSV header,
not in the page-budgeted body. UniProt-equivalent numbering for MYC_MAX
(item 22's own remainder) stays tracked against [[TASK-0368]], unchanged by
this task.
