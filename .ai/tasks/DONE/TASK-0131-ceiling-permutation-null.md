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
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-19
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

- [x] Run the shipped ceiling-search procedure against permuted pocket
      labels, ≥200 replicates per target, all 3 mandatory targets.
      (`ceiling_search_batched.py` superseded by TASK-0130's closed
      form before this task started — nulled the actual current
      procedure, `ceiling_search(use_converged_limit=True)`, per this
      task's own Dependency note; see Done section.)
- [x] Report each target's real margin as a percentile of its own null.
- [x] Report null summary statistics (median/sd/max) per target.
- [x] Correct `REVIEW-2026-07-15b`'s "lucky trial" rule text, additively.
- [x] If [[TASK-0116]] has landed by the time this runs, also report the
      null under corrected `_PARAM_RANGES`. (Landed already; there is
      only one current procedure — item is moot, not skipped.)

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

**2026-07-19, Implementer B.** Real permutation null, all 3 mandatory
targets, 200 replicates each (600 replicates x 60 trials = 36,000
ceiling-search trials total). Decisive, target-specific answer: the
competence map's "ceiling clears floor" claim is real for one target,
inconclusive for another, and fully explained by search bias for the
third.

### Which procedure was nulled (Implementer's call, stated per this
task's own convention)

The task file names `ceiling_search_batched.py` (T_max=15, N_steps=500
finite-time convention) because that was the shipped procedure when
this task was filed (`REVIEW-panel-2026-07-17.md`, before [[TASK-0130]]
landed 2026-07-18). TASK-0130 replaced that finite-time approximation
with the exact infinite-time closed form for every headline "ctqw"
number, including the ceiling — the real margins being nulled here
(+0.147/+0.085/+0.038) were produced by `ceiling.ceiling_search(
use_converged_limit=True)`, not the old finite-time script. Per this
task's own Dependency note ("the null should ultimately be reported
against whichever headline numbers are current at submission time"),
nulled the actual current procedure (`ceiling_search(use_converged_
limit=True, coherent=False)`) rather than literally re-invoking the
now-superseded script — nulling the old procedure would test a
different statistic than the one actually reported (apples-to-oranges),
not a stricter reproduction of "the shipped procedure." New script
`scripts/ceiling_permutation_null.py`, parallelized across replicates
(`multiprocessing.Pool`, each worker pinned to 1 BLAS thread) — real
wall-clock: KRAS_G12C 231.2s (3.9min), BCR_ABL1 1248.6s (20.8min),
CARDIAC_MYOSIN 5550.1s (92.5min) (12 workers, 16-core box), ~117min total.

[[TASK-0116]] (ceiling search coverage / `_PARAM_RANGES` correction)
had already landed before this task started — `sample_params` is
already the single, current, corrected version. The task's own
conditional item ("if TASK-0116 lands first, also report under
corrected ranges") is moot, not skipped: there is no separate "old
ranges" procedure left to null in addition.

### Null construction

Per replicate: `apo_pocket` replaced by a uniformly random subset of
residues of the *same size* as the real pocket (shuffled identity,
fixed cardinality — the task's own Constraint); `apo_source` (active
site) left real/unchanged, isolating the search procedure's own bias
from any seed question. Both null floor (max of the 3 baseline AUCs
against the *same* permuted label) and null ceiling (60-trial search
against the same permuted label) computed per replicate, so the null
is of the actual statistic `COMPETENCE_MAP.md` cites — ceiling-minus-
floor margin — not the ceiling AUC alone. Independent, reproducible
per-replicate seed streams (permutation draw and the search's own
internal RNG seeded separately via `numpy.random.SeedSequence`).

### Results

| Target | Real margin | Null median | Null SD | Null max | Percentile | p (n=200) | Bonferroni (x3) |
|---|---|---|---|---|---|---|---|
| KRAS_G12C | 0.1470 | 0.0545 | 0.0512 | 0.1941 | 95.5th | **0.045** | 0.135 |
| BCR_ABL1 | 0.0854 | 0.0316 | 0.0568 | 0.1450 | 90.0th | 0.100 | 0.300 |
| CARDIAC_MYOSIN | 0.0375 | 0.0326 | 0.0453 | 0.1546 | 55.0th | 0.450 | 1.000 |

All 200/200 replicates scored successfully per target (no NaN/error
trials); all `ceiling_null` values sane (0-1 range, no anomalies).
Full null distributions: `results_task0131_permutation_null/
permutation_null.json`.

**Headline, real and target-specific, not uniform**:
- **CARDIAC_MYOSIN's "ceiling clears floor" headroom claim (carried in
  this document since TASK-0082) is fully explained by the winner's-
  curse bias alone** — its real margin sits at the 55th percentile of
  pure noise running the identical procedure, i.e. indistinguishable
  from what a genuinely null operator family produces under a 60-trial
  max-search. This is a real retraction of an implicit claim this
  document has carried, unflagged, across 3 prior recomputes.
- **KRAS_G12C's margin is real and uncorrected-significant (p=0.045)**
  — the one target where genuine headroom in the operator family is
  plausible. Does not survive a naive Bonferroni correction for testing
  3 targets (p=0.135) — reported as such, not overclaimed as decided.
  200 replicates give p-value resolution 0.005 (vs. the review's own
  preliminary 12-replicate estimate's ~0.083) — precise enough to
  actually place this number, not just bound it.
- **BCR_ABL1 is intermediate and inconclusive** (p=0.10/0.30 corrected)
  — above the null's median, not distinguishable from noise at any
  conventional threshold.

This does not change any `classify_failure` diagnosis category (those
compare *actual* vs. floor/chance, a different comparison) — it changes
how confidently the *ceiling* numbers specifically should be read.

### Docs

- `COMPETENCE_MAP.md`: new "Permutation null for the ceiling" section
  (full results table + interpretation); new TASK-0130/0131-recomputed
  "Cross-target reading" paragraph (the prior TASK-0129-only version
  had not been updated when TASK-0130 landed and still asserted "real
  headroom exists... for all three targets" — corrected here, TASK-0129's
  own text kept below, marked superseded, not deleted); corrected 3
  stale TASK-0116/TASK-0112 "(open)" tags found while touching this
  document (both actually Done) — additive fixes, not silent edits, each
  dated.
- `REVIEW-2026-07-15b-ceiling-search-methodology.md`: dated correction
  appended to Finding 1's own text — "a single lucky trial clearing the
  floor is real regardless of how the rest of the space looks" is right
  for an existence claim, wrong for the maximum-over-K statistic this
  project actually reports (per this task's own In Scope instruction).

### Not attempted / left for a follow-up task

- Did not change `_PARAM_RANGES`/the search methodology itself (Out Of
  Scope, explicitly — this task measures the existing procedure's null,
  it does not redesign the procedure).
- Did not apply a more sophisticated multiple-comparison correction
  than Bonferroni (e.g. Benjamini-Hochberg) — Bonferroni is the more
  conservative choice, reported alongside the uncorrected p per target
  rather than picking one number to report; a follow-up could use FDR
  control if more targets are added later.
- Did not re-run the 96-cell operator sweep's own per-operator ceiling
  numbers (this task's own Intent Contract scopes to the 3 mandatory
  targets' headline `H_new` ceiling specifically, matching what
  `COMPETENCE_MAP.md` actually reports as "the ceiling").
