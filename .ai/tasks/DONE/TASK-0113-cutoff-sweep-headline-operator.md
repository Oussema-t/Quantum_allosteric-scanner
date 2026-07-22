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
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-22
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

- [x] Build the `H_new`-based cutoff/weight-scheme grid (reuse
      TASK-0101's chunkable-sweep pattern if convenient, not required).
      Cutoff-only — no weight-scheme knob exists for `H_new` (see Done).
- [x] Run on KRAS_G12C + BCR_ABL1, both propagators.
- [x] Compare against TASK-0067's bare-Laplacian conclusion; report
      agreement/disagreement explicitly. Agrees in aggregate, disagrees
      on a real per-target case (BCR_ABL1 GSR floor-flip).
- [x] If disagreement found, flag any headline `RESULTS.md` number that
      may need re-checking (do not silently correct it here — cross-link
      per this project's own convention). Cross-linked into row 1/23.

## Dependency

- TASK-0067 (Done) — this task's direct precedent/comparison target.
- TASK-0096 (Done, H14) — if time permits, worth checking whether H14's
  cutoff sensitivity differs from H_new's, but not required scope.

## Open Questions

- None — scope fully specified.

## Done

**2026-07-22, Implementer B.** Re-ran TASK-0067's cutoff question
directly against `H_new` (both propagators), on the same 2 targets.
**Result: agrees with TASK-0067 in aggregate, disagrees on a real,
headline-relevant per-target case** (`scripts/h_new_cutoff_sweep.py`,
`results_task0113_h_new_cutoff_sweep/`).

### A real, structural finding checked before running anything

TASK-0067's own sweep varies cutoff *and* weight scheme
(`contact_matrix(..., weight=scheme)`: binary/gaussian/exponential/
harmonic/invdist) on a bare Laplacian. Read `hamiltonians.py` before
writing the script, not assumed: `H_new`'s own base Laplacian
(`normalised_laplacian_alpha`) hardcodes `weight="exponential"` — there
is no equivalent weight-scheme knob on `build_H_new`. Adding one would
be exactly the operator-redesign this task's own Constraints exclude
("reuse `build_H_new`... this is a cutoff/propagator sweep, not an
operator-weight sweep"). **Decision, stated per this task's own
convention for such calls**: sweep cutoff only for `H_new` — the one
real, shared knob between the two operators — rather than forcing
TASK-0067's 2-axis grid shape onto an operator that doesn't have a
matching second axis.

### Method and cross-validation

`H_new` (default potential weights) built at cutoff ∈ {7.5, 8.0, 10.0}
Å on KRAS_G12C/BCR_ABL1 (CARDIAC_MYOSIN excluded, inheriting TASK-0067's
own data-quality exclusion, not re-litigated), scored via
`time_averaged_ctqw_converged` (TASK-0130's closed form) and
`ground_state_relaxation` (`t_max=15`). TASK-0094's floor baselines
recomputed per cutoff too (cutoff-dependent themselves). **Cross-
validated directly**: the cutoff=8.0 Å row (shipped default) reproduces
[[TASK-0130]]'s own independently-computed closed-form numbers for
BCR_ABL1 exactly (ctqw 0.5266, ground_state 0.6766) — confirms this
script measures the same quantity the production pipeline reports.

### Results

| Target | Cutoff (Å) | Floor | AUC (ctqw) | Cleared? | AUC (ground_state) | Cleared? |
|---|---|---|---|---|---|---|
| KRAS_G12C | 7.5 | 0.482 | 0.635 | Yes | 0.356 | No |
| KRAS_G12C | 8.0 | 0.482 | 0.590 | Yes | 0.375 | No |
| KRAS_G12C | 10.0 | 0.501 | 0.597 | Yes | 0.431 | No |
| BCR_ABL1 | 7.5 | 0.583 | 0.486 | No | 0.675 | **Yes** |
| BCR_ABL1 | 8.0 | 0.582 | 0.527 | No | 0.677 | **Yes** |
| BCR_ABL1 | 10.0 | 0.647 | 0.517 | No | 0.638 | **No** |

Aggregate (mean across both targets):

| Cutoff (Å) | Mean AUC (ctqw) | Mean AUC (ground_state) | TASK-0067 bare-Laplacian |
|---|---|---|---|
| 7.5 | 0.560 | 0.515 | 0.423 |
| 8.0 | 0.558 | 0.526 | 0.420 |
| 10.0 | 0.557 | 0.535 | 0.432 |

### Headline

1. **Aggregate cutoff sensitivity is if anything smaller than the bare
   Laplacian's** (ctqw range 0.003, ground_state range 0.020, vs.
   TASK-0067's own 0.0124) — agrees with, reinforces, "no significant
   aggregate difference."
2. **That aggregate stability is a coincidence of cancellation, checked
   directly, not assumed.** Per-target, `ctqw`'s AUC moves ~0.04-0.05
   across the grid for *each* target individually — KRAS_G12C and
   BCR_ABL1 move in **opposite** directions as cutoff increases, which
   is what keeps the 2-target mean flat. Exactly the failure mode this
   task's own Planned Validation warned against.
3. **Real, decisive floor-crossing flip**: BCR_ABL1's `ground_state_
   relaxation` clears the proximity floor at 7.5/8.0 Å (shipped
   default — matches this project's current headline, 0.677) but does
   **not** clear it at 10.0 Å (0.638 vs. a floor that itself jumps to
   0.647). Both AUC and floor move with cutoff; their relative ordering
   flips. Directly touches BCR_ABL1's own "apo-computable structural
   prior" finding ([[TASK-0091]]/[[TASK-0102]]/[[TASK-0104]]) — that
   finding's floor-clearing status is not robust to the GNM cutoff
   choice. Not silently corrected — cross-linked into `RESULTS.md`'s
   open-questions row 1 and new row 23, per this project's own
   convention. TASK-0102's own "largely seed-independent" finding is a
   different robustness axis (seed convention) and is unaffected.
4. **`time_averaged_ctqw`'s own floor-crossing story is fully stable**
   across the grid for both targets (KRAS_G12C always clears; BCR_ABL1
   never clears, all 3 cutoffs) — the flip above is specific to
   `ground_state_relaxation`.
5. **`H_new` scores meaningfully higher than the bare GNM Kirchhoff at
   every matching cutoff** — confirms the two sweeps measure
   meaningfully different operators, not a restatement.

### Docs updated additively

`RESULTS.md`: new "Re-running the GNM cutoff sweep against the headline
operator" section; open-questions row 1 (BCR_ABL1 GSR) gets a dated
caveat; new row 23. `EXECUTION_PLAN.md`: Phase 2.1 (TASK-0067) row and
the pre-Phase-1 TASK-0113 bullet both updated in place with the Done
result.

### Not attempted / left for a follow-up task

- Did not re-litigate TASK-0067's own bare-Laplacian result, per this
  task's own Out Of Scope — it remains correct for the narrower
  question it was built to answer.
- Did not add a weight-scheme knob to `build_H_new`/`normalised_
  laplacian_alpha` — would be an operator-redesign, explicitly out of
  this task's own Constraints.
- Did not investigate BCR_ABL1's GSR floor-flip mechanism further (why
  the 10.0 Å floor jumps specifically) — flagged as a real, open
  robustness gap for whoever next revisits that target's structural-
  prior claim, not chased to a mechanism here.
- Did not check TASK-0096's H14 cutoff sensitivity (this task's own
  Dependency section listed it as "if time permits, not required
  scope") — left for a follow-up task if H14's own ceiling numbers
  (TASK-0126/0138) warrant it.
