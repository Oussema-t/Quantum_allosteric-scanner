# TASK-0113 Re-run the GNM cutoff/weight sweep against the actual headline operator

## Context

- ID: TASK-0113
- Title: TASK-0067's cutoff/weight-scheme sweep (`analysis.py::
  gnm_cutoff_weight_sweep`) scores a bare contact-Laplacian via
  `ground_state_relaxation`, not `H_new` or `time_averaged_ctqw` — the
  two functions that actually produce every headline AUC in
  `RESULTS.md`. The "8.0 Å is fine, no significant difference"
  conclusion has never been checked against the operator the submission
  reports.
- Status: TODO
- Owner: Implementer
- Source: `REVIEW-2026-07-15-execution-plan-gap-audit.md`, finding #2.
- Crit Ref: `analysis.py:420-453`'s own docstring states the choice was
  deliberate for *that* sweep's purpose ("comparing operator
  construction, not propagator choice") — this is not a bug in
  TASK-0067, it is a gap in what the plan's progress tracker implies
  the sweep covers. EXECUTION_PLAN.md's Phase 2.1 row reads "Cutoff: no
  significant difference across 7.5/8.0/10.0 Å... backend's 8.0 Å
  default does not need to change" with no caveat that this used a
  different operator than `H_new`.

## Intent Contract

- Outcome: the cutoff/weight-scheme question re-answered using the
  actual scored pipeline (`H_new` + `time_averaged_ctqw` and `H_new` +
  `ground_state_relaxation`, both propagators per TASK-0101's own
  precedent of scoring through both) on the same real targets TASK-0067
  used (KRAS_G12C, BCR_ABL1).
- In Scope:
  - extend or duplicate `gnm_cutoff_weight_sweep`'s grid
    (7.5/8.0/10.0 Å × the weight schemes already tested) but build
    `H_new` at each cutoff instead of the bare Laplacian, score via both
    `time_averaged_ctqw` and `ground_state_relaxation`.
  - compare the result against TASK-0067's existing conclusion: report
    agreement or disagreement explicitly, per this project's own
    "report both, don't silently reconcile" convention (same as
    TASK-0110's cross-check requirement).
  - if the cutoff *does* matter for `H_new` specifically (unlike the
    bare Laplacian), flag whether this changes anything already reported
    in `RESULTS.md` for KRAS_G12C/BCR_ABL1's headline AUCs.
- Out Of Scope:
  - re-litigating TASK-0067's own bare-Laplacian result, which stands
    as-is for the purpose it was built for.
  - CARDIAC_MYOSIN (excluded from TASK-0067 for the same data-quality
    reason recorded there — inherit, don't re-litigate).
- Constraints And Invariants: reuse `hamiltonians.build_H_new` and the
  existing default potential-weight coefficients — this task is a
  cutoff/propagator sweep, not an operator-weight sweep (that's
  TASK-0046's territory).
- Planned Validation: the sweep runs on real KRAS_G12C/BCR_ABL1 data;
  results reported per-cutoff, per-weight-scheme, per-propagator — not
  collapsed into a single "still fine" summary if the data shows
  otherwise.

## In Progress

None

## TODO

- [ ] Build the `H_new`-based cutoff/weight-scheme grid (reuse
      TASK-0101's chunkable-sweep pattern if convenient, not required).
- [ ] Run on KRAS_G12C + BCR_ABL1, both propagators.
- [ ] Compare against TASK-0067's bare-Laplacian conclusion; report
      agreement/disagreement explicitly.
- [ ] If disagreement found, flag any headline `RESULTS.md` number that
      may need re-checking (do not silently correct it here — cross-link
      per this project's own convention).

## Dependency

- TASK-0067 (Done) — this task's direct precedent/comparison target.
- TASK-0096 (Done, H14) — if time permits, worth checking whether H14's
  cutoff sensitivity differs from H_new's, but not required scope.

## Open Questions

- None — scope fully specified.

## Done

(not yet)
