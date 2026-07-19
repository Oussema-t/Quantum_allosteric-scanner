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
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
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

None

## TODO

- [ ] Re-run `H14`'s ceiling search under [[TASK-0130]]'s
      `use_converged_limit=True`, all 3 mandatory targets.
- [ ] Run a permutation null against `H14`'s ceiling search (reuse
      [[TASK-0131]]'s methodology if landed; build a compatible one if not).
- [ ] State and justify the single-dimension search's own trial density.
- [ ] Report whether `H14`'s margin over `H_new` survives both checks,
      per target, whichever way it comes out.

## Dependency

- [[TASK-0126]] (in progress/near-Done) — the finding this task
  scrutinizes.
- Soft: [[TASK-0131]] (permutation null) and [[TASK-0130]] (Done, closed
  form already available) — reuse rather than duplicate.

## Open Questions

- None — scope is fully specified by TASK-0126's own recommendation.

## Done

(not yet)
