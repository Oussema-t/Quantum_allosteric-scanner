# TASK-0131 Permutation null for the ceiling search — decides the competence map's only positive claim

## Context

- ID: TASK-0131
- Title: `ceiling.ceiling_search`/`ceiling_search_batched.py` report the
  **maximum** AUC over 60 blind random draws against the real pocket
  label, and `COMPETENCE_MAP.md` reads "ceiling clears floor" (+0.122
  KRAS_G12C, +0.090 BCR_ABL1, +0.064 CARDIAC_MYOSIN) as evidence of real
  headroom in `H_new`'s physical-scalar space — the document's only
  nonnegative claim. A maximum over K noisy draws is upward-biased by
  construction (the winner's curse / look-elsewhere effect), independent
  of whether real signal exists. Run the identical search protocol
  against permuted/randomized pocket labels to establish what pure noise
  produces under this exact procedure, and report every real margin as a
  percentile of that null.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/REVIEW-panel-2026-07-17.md` §2.1, §4 P0-2, §6.3
  action #2. Estimated a preliminary version of this null on a
  reconstructed `H_new` surrogate (not this repo's real `potentials.py`,
  and on 3MHT/1UBI, not this project's real targets, sandbox couldn't
  reach RCSB) — found median null ceiling-minus-floor +0.044 to +0.072,
  max +0.15, with all three real reported margins falling inside that
  range (p ≈ 0.08–0.50 depending on pocket size, none reaching p<0.05).
  This task is the real version, against the real code and real targets,
  that the review's own estimate cannot substitute for.
- Priority: **P0.** This is the single highest-value experiment
  currently unscoped in the plan — it decides whether the competence
  map's one positive statement survives.

## Intent Contract

- Outcome: `ceiling_search_batched.py` run **unchanged** (same
  `_PARAM_RANGES`, same 60-draw budget per replicate — matching the
  exact shipped procedure, not a "fixed" one; if [[TASK-0116]]'s
  `_PARAM_RANGES` correction lands first, re-run under the corrected
  ranges too and report both, since the null must match whatever
  procedure actually produced the headline number) against **permuted**
  pocket labels — shuffle which residues count as the true pocket,
  keeping the same pocket *size* per target, ≥200 replicates per target
  (per the review's own stated resolution requirement: 12 replicates
  gives p-value resolution of only ~0.083, enough to place a margin in
  the null's bulk but not to put a tight p on it; 200 replicates is
  needed for that). Report each target's real ceiling-minus-floor margin
  (+0.122/+0.090/+0.064, or whatever [[TASK-0129]]'s successor produces)
  as an explicit percentile of its own target's null distribution.
- In Scope:
  - All 3 mandatory targets, using the real `ceiling_search_batched.py`
    and real `potentials.py`/`build_H_new` (not a surrogate — this
    task's own job is to be the thing the review's estimate is a stand-in
    for).
  - Report the null's own summary statistics (median, sd, max) per
    target, not just a single p-value, so the shape of the bias is
    visible, not just its significance threshold.
  - Correct `REVIEW-2026-07-15b-ceiling-search-methodology.md`'s own
    stated rule ("N=60 blind random search... would be perfectly
    adequate evidence for a positive finding, a single lucky trial
    clearing the floor is real regardless of how the rest of the space
    looks") — this reasoning is correct for an *existence* claim (does
    any point in the space score highly against the real label) but
    wrong for the *maximum-over-K* statistic actually reported; add a
    dated correction to that review file's own text (additive, not a
    silent edit) so the same asymmetry — rigor demanded for negative
    claims, not for positive ones — doesn't recur next time this task's
    search space changes.
- Out Of Scope:
  - Changing the ceiling search's own methodology beyond running it
    against permuted labels — this task measures the existing
    procedure's null, it does not redesign the procedure (that's
    [[TASK-0116]]'s scope, if pursued).
  - Any change to `_PARAM_RANGES` itself — [[TASK-0116]]'s scope; this
    task runs whatever ranges are currently shipped (and, if TASK-0116
    lands first, the corrected ones too, reported separately).
- Constraints And Invariants: permutation must preserve pocket *size*
  per target (shuffling residue identity, not residue count) — a
  differently-sized random pocket is not a valid null for a fixed-size
  real one.
- Planned Validation: the null distribution itself, per target, plus the
  real margin's percentile within it — this task's entire output *is*
  its own validation artifact.

## In Progress

None

## TODO

- [ ] Run `ceiling_search_batched.py` unchanged against permuted pocket
      labels, ≥200 replicates per target, all 3 mandatory targets.
- [ ] Report each target's real margin as a percentile of its own null.
- [ ] Report null summary statistics (median/sd/max) per target.
- [ ] Correct `REVIEW-2026-07-15b`'s "lucky trial" rule text, additively.
- [ ] If [[TASK-0116]] has landed by the time this runs, also report the
      null under corrected `_PARAM_RANGES`.

## Dependency

- Soft: [[TASK-0116]] (if it lands first, re-run under corrected ranges
  too; not a hard block — this task's primary job is nulling the
  *currently shipped* procedure).
- Feeds directly into whatever recompute [[TASK-0130]] (closed-form
  clock fix) produces — the null should ultimately be reported against
  whichever headline numbers are current at submission time.

## Open Questions

- None — scope and replicate count are fully specified by the review's
  own stated resolution requirement.

## Done

(not yet)
