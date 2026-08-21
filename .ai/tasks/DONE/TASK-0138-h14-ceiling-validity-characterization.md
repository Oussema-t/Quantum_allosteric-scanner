# TASK-0138 Characterize `H14_anm_pinv_trace` at ceiling with the same rigor `H_new` has been through

## Context

- ID: TASK-0138
- Title: [[TASK-0126]] found, incidentally (while checking H13 against
  `H_new`), that `H14_anm_pinv_trace` beats `H_new`'s combined-convention
  ceiling on **all 3 mandatory targets** by a real, consistent margin
  (+0.032 KRAS_G12C, +0.0699 BCR_ABL1, +0.0612 CARDIAC_MYOSIN). `H14` is
  already implemented, already Tier-A (selection-eligible per
  [[TASK-0100]]'s own tiering), already in the 96-cell operator sweep —
  this finding was sitting unexamined in existing infrastructure, not a
  new build. Before this can inform anything, it needs the same
  parameter-validity/search-coverage/reproducibility scrutiny `H_new`'s
  own ceiling numbers have been through this month.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer A (this thread)
- Claimed At: 2026-07-19 18:02
- Source: [[TASK-0126]]'s own Done section, explicit recommendation:
  "a strong signal for a dedicated follow-up task to characterize `H14`
  at ceiling across the same parameter-validity/reproducibility scrutiny
  `H_new` has already been through (TASK-0116/0117/0129), before any
  reselection decision is made."
- Priority: **P1.** Not urgent enough to precede TASK-0131 (the
  permutation null still owed to `H_new`'s own ceiling claim) but real
  — a candidate operator beating the current baseline at ceiling,
  unscrutinized, is exactly the kind of claim this project's own culture
  doesn't let stand unchecked.

## Intent Contract

- Outcome: `H14`'s ceiling numbers (currently: single 60-trial,
  cutoff-only random searches, per [[TASK-0126]]'s own stated caveat)
  re-examined under the same checks `H_new`'s own ceiling has
  accumulated: (1) a permutation null (same shape as [[TASK-0131]] —
  reuse that task's own methodology/script once it lands rather than
  building a second one); (2) parameter-validity — is `H14`'s own
  `t*`/`n*` (per-operator clock, already computed correctly per
  [[TASK-0126]]'s own Done section) actually adequate, or does
  [[TASK-0130]]'s closed-form fix apply here too (it should — `H14` uses
  the same `time_averaged_ctqw` propagator family, `use_converged_limit`
  is already wired into `ceiling.ceiling_search` and should be used
  directly rather than re-deriving clock validity from scratch); (3)
  search coverage — `H14` only has one search dimension (`cutoff`) per
  [[TASK-0126]]'s own script, so [[TASK-0116]]'s multi-dimensional
  budget-simplex concern doesn't directly transfer, but the single-
  dimension search's own trial count/density should still be stated and
  justified, not assumed adequate by analogy to `H_new`'s 60-trial
  precedent.
- Why this matters beyond one operator's number: if `H14` survives this
  scrutiny and still beats `H_new`, that is a real, load-bearing finding
  for whatever this project's Phase 1 proposal claims about its own
  operator choice — either as a concrete "here is a promising Phase 2
  direction" data point, or (if it doesn't survive) as one more
  confirmed instance of a headline number being an artifact of
  under-scrutiny, consistent with this project's own recent history.
- In Scope:
  - Run [[TASK-0131]]'s permutation null against `H14`'s ceiling search
    once that task's own methodology exists (soft dependency, not a
    block — build a compatible null if TASK-0131 hasn't landed yet, but
    do not invent a second, incompatible null-testing convention).
  - Re-run `H14`'s ceiling search using [[TASK-0130]]'s
    `use_converged_limit=True` closed form rather than the finite-`t_max`
    approximation [[TASK-0126]]'s original run used.
  - State and justify the single-dimension (`cutoff`) search's own trial
    density explicitly.
  - Re-run on all 3 mandatory targets (already done once by TASK-0126;
    this task's job is applying the additional scrutiny above, not
    re-deriving the base numbers from scratch unless the closed-form
    switch changes them enough to warrant a full re-run).
- Out Of Scope:
  - Reselecting `H14` as the submission operator — Tier-2-gated per
    [[TASK-0100]], unaffected by this task's own findings regardless of
    outcome.
  - Extending `H14`'s own search to additional dimensions beyond
    `cutoff` (e.g. `n_low`, if `H14`'s formula has any other tunable
    parameters) — flag as a real gap if found, do not silently expand
    scope to close it here.
- Constraints And Invariants: report `H14`'s post-scrutiny numbers with
  the same caveat density `H_new`'s own ceiling numbers currently carry
  in `COMPETENCE_MAP.md` — no lighter-touch standard for the newer,
  more favorable-looking candidate.
- Planned Validation: the permutation null result and the closed-form
  re-run are this task's own validation — report whether `H14`'s margin
  over `H_new` survives both, whichever way it comes out.

## In Progress

**2026-07-19, Implementer A.** Claimed. **Premise correction, found
immediately on re-reading this task's own Context against what
TASK-0126 actually committed** (`73c38ee`): this task's Context/Source
section describes TASK-0126 finding H14 beats `H_new`'s ceiling on
**all 3 mandatory targets** (+0.032/+0.0699/+0.0612) — that was an
earlier, in-session draft of TASK-0126's own numbers, computed under
the since-superseded TASK-0129 finite-`t_max` convention. TASK-0126
switched conventions mid-task (TASK-0130's closed form landed
concurrently) and its actually-committed Done section reports a
narrower finding: **H14 beats `H_new` on BCR_ABL1 only** (0.7174 vs
0.6671, +0.0503) — not on KRAS_G12C (0.5732 vs 0.6288) or CARDIAC_MYOSIN
(0.7703 vs 0.8297). This task's own scope (permutation null + trial-
density justification, already using the closed form since TASK-0126's
own script already switched to it) is unaffected by the correction, but
the "why this matters" framing narrows to one target, not three. Also
found: TASK-0126's own `h13_ceiling_comparison.py::cutoff_only_ceiling_
search` already uses `time_averaged_ctqw_converged` (the closed form) —
this task's TODO item 1 ("re-run under `use_converged_limit=True`") is
therefore already satisfied by TASK-0126's existing committed numbers,
not separate work needed here.

## TODO

- [x] Re-run `H14`'s ceiling search under [[TASK-0130]]'s
      `use_converged_limit=True`, all 3 mandatory targets. (Already
      satisfied by TASK-0126's committed numbers, see In Progress note.)
- [x] Run a permutation null against `H14`'s ceiling search (reuse
      [[TASK-0131]]'s methodology if landed; build a compatible one if not).
- [x] State and justify the single-dimension search's own trial density.
- [x] Report whether `H14`'s margin over `H_new` survives both checks,
      per target, whichever way it comes out.

## Dependency

- [[TASK-0126]] (in progress/near-Done) — the finding this task
  scrutinizes.
- Soft: [[TASK-0131]] (permutation null) and [[TASK-0130]] (Done, closed
  form already available) — reuse rather than duplicate.

## Open Questions

- None — scope is fully specified by TASK-0126's own recommendation.

## Done

**Headline: H14's own ceiling-clears-floor claim does not survive permutation-null
scrutiny on any of the 3 mandatory targets** — the same "no lighter-touch standard for
the newer, more favorable-looking candidate" this task's own Constraints demanded.

### Permutation null (compatible construction, reusing TASK-0131's methodology)

New `scripts/h14_ceiling_permutation_null.py` — same null construction as TASK-0131's
own `ceiling_permutation_null.py` (permuted pocket label, same size, shuffled identity;
real `source`/active-site seed unchanged; null floor = max of the 3 baseline AUCs
against the permuted label; null ceiling = a full 60-trial search against the same
permuted label; both computed per replicate so the null is of the actual
ceiling-minus-floor margin statistic, not the ceiling AUC alone) — not a literal call
into that script, since H14 goes through TASK-0126's own 1-dimensional `cutoff_only_
ceiling_search`, not `ceiling.ceiling_search`'s 8-dimensional `H_new` search; a
compatible null, imported from `h13_ceiling_comparison.py` rather than duplicated by
hand.

**Real feasibility problem found and fixed along the way**: an initial full 3-target,
200-replicate run at `workers=12` (matching TASK-0131's own worker count) hit severe
contention on CARDIAC_MYOSIN specifically — the first batch of 12 concurrent replicates
took 2073s (vs. a clean 2-worker probe's 360s/replicate), a ~5.8x slowdown, most likely
memory-bandwidth contention from 12 concurrent large (950-dim) `eigh` calls rather than
simple CPU oversubscription. Projected ~9.7 hours for CARDIAC_MYOSIN alone at that
worker count. **Also found**: the script only wrote its output JSON once, after all
targets finished — killing the contended run would have discarded KRAS_G12C's and
BCR_ABL1's already-completed 200-replicate results too. **Fixed**: `main()` now loads
and merges any existing output file and writes a checkpoint after every target, not
just at the end. Re-ran KRAS_G12C/BCR_ABL1 at `workers=12` (confirmed fast, no
contention: 356.7s/3404.7s respectively for 200 replicates each) and CARDIAC_MYOSIN
separately at `workers=4` (measured throughput-optimal via a small timing test:
1148.1s for 8 replicates, vs. 12-worker's severe slowdown).

**CARDIAC_MYOSIN run at a reduced 30 replicates, not 200 -- a scoped, justified
decision, not a silent cut.** H14's CARDIAC_MYOSIN ceiling (0.7703) is already *below*
its own floor (0.7921) -- the real margin is negative (-0.0218) before any null
correction is even applied. A permutation null tests whether a positive-looking margin
survives winner's-curse scrutiny; there is no positive claim here to scrutinize, and a
full 200-replicate run (~8 hours at the measured throughput) would only have confirmed
what the point estimate already shows. The 30-replicate run confirms this directly:
the real margin sits at the **0th percentile** of the null distribution (below every
one of the 30 null replicates, including the null's own minimum of -0.0057) -- not
just "not significant," but worse than what pure noise typically produces under this
exact search procedure.

### Results

| Target | H14 ceiling−floor margin | Null median | Null SD | Null max | Percentile | p (uncorrected) | Bonferroni (×3) |
|---|---|---|---|---|---|---|---|
| KRAS_G12C | 0.0914 | 0.0605 | 0.0526 | 0.1921 | 70.0th (n=200) | 0.300 | 0.900 |
| BCR_ABL1 | 0.1357 | 0.0848 | 0.0611 | 0.2920 | 79.0th (n=200) | 0.210 | 0.630 |
| CARDIAC_MYOSIN | −0.0218 | 0.0904 | — | 0.2286 | 0.0th (n=30, reduced) | not computed (negative real margin) | — |

**Neither positive margin (KRAS_G12C, BCR_ABL1) reaches conventional significance**,
even before multiple-comparison correction. This is the same qualitative outcome
TASK-0131 found for `H_new`'s own CARDIAC_MYOSIN margin (55th percentile, fully
noise-explained) — except here it affects H14's numbers on the two targets where a
positive claim existed at all. TASK-0126's finding that H14's *point estimate* beats
`H_new`'s on BCR_ABL1 (+0.0503) is not retracted by this — the point estimate is real
and correctly computed — but the null shows H14's own ceiling-clears-floor claim on
that target is itself statistically weak (79th percentile, p=0.21), which further
weakens any confidence in a comparison built on top of it.

### Trial-density justification (single-dimension `cutoff` search)

New `scripts/h14_trial_density_check.py` -- runs one long 300-trial random search per
target (same RNG stream `cutoff_only_ceiling_search` itself uses) and computes the
running-max AUC at checkpoints (10/20/30/60/100/150/200/300) from that single ordered
sequence, to check whether the existing 60-trial convention (chosen by analogy to
`H_new`'s own 8-dimensional convention, not derived for this 1-D search) has actually
converged.

- **KRAS_G12C: not converged at 60 trials.** Running max: 0.5570 (n=10) → 0.5640 (n=30)
  → 0.5732 (n=60) → **0.5949 (n=150)**, plateaus 150-300. A real +0.0217 gain exists
  between 60 and 150 trials -- the 60-trial convention understates this target's true
  H14 ceiling (though even the converged 0.5949 still does not beat `H_new`'s 0.6288).
- **BCR_ABL1: much closer to converged.** Running max: 0.6904 (n=10) → 0.7174 (n=60) →
  0.7213 (n=150), plateaus 150-300 -- only a +0.0039 gain beyond 60 trials. The
  reported margin over `H_new` (+0.0503) is not an artifact of under-sampling; if
  anything it is a mild underestimate of the true (~300-trial) ceiling.
- **CARDIAC_MYOSIN: not run.** Given the ceiling is already below floor at 60 trials
  and more trials can only raise a max (never lower it), a convergence check here could
  only make the already-negative margin closer to zero or positive -- worth flagging as
  a real gap (not silently closed) rather than spending the compute to confirm a
  qualitative conclusion (does not beat `H_new`) that a plateau either way would not
  change, since `H_new`'s own margin over H14 here is large (0.0594) relative to any
  plausible convergence gain (KRAS_G12C's own largest observed gain was 0.0217).

**Justification for keeping 60 trials as the reported convention despite KRAS_G12C's
non-convergence**: not re-derived upward here (out of scope -- this task characterizes
the existing convention's validity, it does not redesign the search budget). Flagged
explicitly, matching this task's own Constraint to report with the same caveat density
`H_new`'s numbers carry, not silently corrected in place.

### Answer to this task's own central question

**H14's margin over `H_new` does not clearly survive scrutiny on any target.**
KRAS_G12C and CARDIAC_MYOSIN never had a positive margin to defend in the first place
(CARDIAC_MYOSIN's is negative; KRAS_G12C's H14 ceiling, even at its likely-converged
~0.595, still trails `H_new`'s 0.6288). BCR_ABL1's positive point-estimate margin
(+0.0503) is real and not a trial-density artifact, but H14's own ceiling-clears-floor
claim there is not statistically distinguishable from the winner's-curse noise this
exact search procedure produces (79th percentile, p=0.21 uncorrected). Per this
project's own recent history (`ceiling.md`'s 2026-07-18 status update, TASK-0131's own
CARDIAC_MYOSIN finding), this is one more instance of a headline-looking number not
surviving the scrutiny `H_new`'s own numbers have already been through -- reported as
such, not softened. Consistent with, not contradicted by, TASK-0126's own numbers.

Files touched: `__WORK_IN_PROGRESS__/scripts/h14_ceiling_permutation_null.py` (new),
`__WORK_IN_PROGRESS__/scripts/h14_trial_density_check.py` (new). Results:
`__WORK_IN_PROGRESS__/results/tasks/0138_h14_permutation_null/permutation_null.json`.
