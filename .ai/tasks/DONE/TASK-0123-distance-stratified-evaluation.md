# TASK-0123 Adopt distance-stratified evaluation (distance-matched decoys)

## Context

- ID: TASK-0123
- Title: Score pocket residues against distance-matched non-pocket
  decoys (same hop-shell from the seed), not against all residues — the
  standard way to evaluate a signal under a known, confirmed
  distance confound, and the only way an occupation-based signal
  *inside* a given shell can become visible at all.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-19
- Source: `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §2.3, §5 P1-7, §6.
- Priority: **P1 — weeks 2-4.**

## Intent Contract

- Outcome: a distance-stratified AUC metric — for each pocket residue,
  match it against non-pocket residues at the same hop-distance (or a
  binned equivalent) from the seed, and compute discrimination *within*
  that shell rather than across the whole residue set. This directly
  answers the panel's own falsification test (§6): "distance-matched-
  decoy AUC on all targets... stratified AUC ≈ 0.5 in every shell →
  observable dead, switch to co-participation/ENAQT."
- Why this is required, not optional, per §2.3: plain whole-graph AUC is
  mechanically dominated by the fact that "occupation of a walk seeded
  at a point is a monotonically-decreasing function of distance from
  that point — for any operator, at any time" (table reproduced in the
  review: ρ(occ,−dist) = +0.83 to +0.97 depending on t, on a bare
  disorder-free Laplacian with zero potential). A whole-graph AUC cannot
  distinguish "this operator found the pocket" from "this operator found
  distance," structurally. Distance-stratification is the fix that lets
  a real signal *inside* the confound become visible, if one exists.
- In Scope:
  - Implement hop-shell (or Euclidean-shell) binning and within-shell
    AUC computation, reusable across every operator/propagator already
    in the register — a metrics-layer addition, not a per-operator patch.
  - Apply to all 3 mandatory targets, current `H_new`/`H10`/other
    register operators, both propagators (`time_averaged_ctqw`/
    `ground_state_relaxation`).
  - Apply to whatever new observable(s) [[TASK-0122]] produces, once
    available — this metric is the intended evaluation lens for
    `mode_coparticipation`, not just a patch for the existing register.
- Out Of Scope:
  - Building new observables — [[TASK-0122]]'s scope; this task builds
    the evaluation method, applicable to any observable.
  - Changing which operator ships — Tier-2 gated, unaffected by this
    task's own findings per [[TASK-0100]].
- Constraints And Invariants: shell binning must be defined once and
  reused identically across every operator comparison in this task — a
  different binning per operator would reintroduce exactly the kind of
  unexamined-knob problem this whole review is about.
- Planned Validation: reproduce the panel's own predicted kill criterion
  directly — if stratified AUC ≈ 0.5 in every shell for the current
  register, report that as the finding (observable dead, per the
  panel's own framing) rather than searching for a shell where it isn't.

## In Progress

None

## TODO

- [x] Implement hop-shell (or Euclidean-shell) binning in the metrics
      layer.
- [x] Implement within-shell AUC computation.
- [x] Apply to all 3 mandatory targets × current register operators ×
      both propagators.
- [x] Report whether stratified AUC clears 0.5 in any shell, for any
      operator — the panel's own kill/pass criterion. Found: real
      values above 0.5 exist, but the statistic itself needed a
      permutation-null correction before trusting that (see Done).
- [x] Re-apply once [[TASK-0122]]'s `mode_coparticipation` is available.

## Dependency

- None hard — can start immediately on the existing register.
- Soft: should be re-applied once [[TASK-0121]]/[[TASK-0122]] land, since
  those change what's being evaluated.

## Open Questions

- Exact shell-binning granularity (single-hop bins vs. coarser bands) —
  Implementer's call, state the choice and why in Done; report
  sensitivity to this choice if it materially changes the conclusion.

## Done

**2026-07-19, Implementer B.** Implemented, applied to the full register
on all 3 real targets, and — found necessary while writing this up, not
assumed — corrected against a real permutation null before trusting the
naive reading. **Result: real, uncorrected suggestive signal in 2 of 9
tested cells; neither the panel's own "observable dead" prediction nor
a clean reversal of this project's other floor findings.**

### Implementation

New `metrics.stratified_auc(scores, labels, shells, min_pos=1,
min_neg=1)` — AUC computed independently within each unique `shells`
value, so a scorable shell's AUC cannot be driven by distance (every
compared residue is equidistant from the seed by construction). A
shell needs both label classes present to be scorable (excluded, not
scored as a degenerate NaN — matches `metrics.auc`'s own convention at
the shell level). `stratified_auc_summary` collapses the per-shell dict
into `{n_scorable_shells, mean_auc, max_auc, max_shell}`, the panel's
own pass/kill statistic. **Binning granularity (Open Question,
Implementer's call)**: single-hop-distance bins, per the panel's own
literal "same hop-shell" framing — not swept against a coarser banding,
since the real result (below) turned out to hinge on a different
methodological correction (the permutation null), not the binning
choice; a sensitivity check on binning is flagged as a real remaining
gap, not silently resolved.

### Tests

New `tests/test_metrics.py` (no dedicated metrics test file existed
before this task) — 9 tests: the core illustrative case (a pure
distance confound where whole-graph AUC is inflated by proximity but
every scorable shell's stratified AUC is exactly 0.5, since scores are
tied within each shell); a real-within-shell-signal case where
stratified AUC correctly recovers a shell-independent signal a
whole-graph AUC would leave masked; degenerate-shell exclusion;
`min_pos`/`min_neg` threshold behavior; `n_pos`/`n_neg` reporting;
empty-input handling; summary NaN-robustness.

### Real-target application (new `scripts/distance_stratified_evaluation.py`,
`results/tasks/0123_distance_stratified/`)

Applied to all 16 operators in `analysis._operator_registry()` x both
propagators (`ctqw` via [[TASK-0130]]'s closed form -- the actual
current procedure behind every other headline number in this repo, not
the now-superseded finite-`t_max` convention; `ground_state` at
`t_max=15`, unaffected by TASK-0130) x all 3 mandatory targets (96
cells), plus [[TASK-0122]]'s `mode_coparticipation` (this task's own In
Scope: "apply to whatever new observable TASK-0122 produces"). Hop-shell
binning (`baselines.hop_from_seed`) computed once per target, reused
identically across every operator/propagator/observable in that
target's row (this task's own Constraint).

**Naive reading, checked and found to overclaim**: 40 (target,
operator, propagator) cells with a well-powered shell (`n_pos>=3`)
clear stratified AUC > 0.65 across the register, on every mandatory
target. Read naively this looks like a striking reversal of nearly
every other "no mandatory target's actual clears its own floor" finding
elsewhere in this project.

**That reading does not survive a real check.** `stratified_auc_
summary` takes the *maximum* over several shells per cell -- the same
winner's-curse/look-elsewhere structure [[TASK-0131]] already
identified for the ceiling search's max-over-60-trials statistic.
Built a permutation null (label a same-sized random residue subset
"pocket," re-score the *same, fixed, already-computed* occupation
vector, 1000 replicates -- cheap, unlike TASK-0131's own null, since no
re-optimization/re-diagononalization is needed per replicate) for 3
representative cases per target (`H_new`/ctqw, `H_new`/ground_state,
`mode_coparticipation` -- the two propagators plus TASK-0122's own
observable). **The null's own median well-powered-max AUC is
0.56-0.64, not 0.5** -- most of the naive ">0.65" list sits inside or
barely above what pure noise produces under this exact max-over-shells
procedure.

### Corrected results (9 tests: 3 representative cases x 3 targets)

| Target | Representative | Real max AUC (shell) | Null median | p |
|---|---|---|---|---|
| KRAS_G12C | `H_new`/ctqw | 0.710 (1) | 0.643 | 0.269 |
| KRAS_G12C | `H_new`/ground_state | 0.518 (3) | 0.635 | 0.851 |
| KRAS_G12C | `mode_coparticipation` | 0.405 (3) | 0.640 | 0.982 |
| BCR_ABL1 | `H_new`/ctqw | 0.741 (4) | 0.609 | 0.153 |
| BCR_ABL1 | `H_new`/ground_state | 0.820 (4) | 0.620 | 0.053 |
| BCR_ABL1 | `mode_coparticipation` | 0.906 (2) | 0.619 | **0.012** |
| CARDIAC_MYOSIN | `H_new`/ctqw | 0.581 (1) | 0.560 | 0.451 |
| CARDIAC_MYOSIN | `H_new`/ground_state | 0.890 (1) | 0.569 | **0.010** |
| CARDIAC_MYOSIN | `mode_coparticipation` | 0.604 (2) | 0.570 | 0.400 |

2/9 clear p<0.05 uncorrected; **neither survives Bonferroni correction**
for 9 tests (threshold 0.0056). The panel's own literal kill criterion
("stratified AUC ~= 0.5 in every shell") does not strictly fire -- real
values well above 0.5 exist -- but the panel's own criterion did not
anticipate that the statistic itself (a max over several shells) needs
the same null treatment TASK-0131 established for the ceiling search.

**Secondary observation**: the same shell clears >0.65 across nearly
every register operator simultaneously for a given target (e.g.
BCR_ABL1's shell 4, `n_pos=3`/`n_neg=76`) -- consistent with a shared
structural property of that shell, not independent per-operator
discoveries (most register operators share structural inputs and would
correlate under any real signal) -- itself part of why the naive
40-cell count overstates independent evidence even before the
permutation-null correction.

### Verdict

Real, uncorrected suggestive signal in 2 of 9 tested cells (BCR_ABL1's
`mode_coparticipation` at shell 2; CARDIAC_MYOSIN's `H_new`/ground_state
at shell 1) -- candidates for targeted follow-up, not confirmed
findings. Neither the panel's own predicted "observable dead" outcome
nor a clean reversal of this project's other floor/ceiling results.
Per this task's own Out Of Scope, no operator-selection decision is
made from this result -- Tier-2 gating ([[TASK-0100]]) applies
unchanged.

### Not attempted / left for a follow-up task

- Did not run the permutation null against the full 16-operator x
  2-propagator register (96 cells) -- 9 representative tests (both
  propagators + TASK-0122's observable, on real `H_new`) directly
  address this task's own headline question; a full 96-cell null would
  be a substantially larger undertaking and is flagged, not silently
  skipped.
- Did not sweep coarser hop-shell banding as a sensitivity check (this
  task's own Open Question permitted deferring it) -- the real
  methodological correction that mattered was the permutation null, not
  the binning granularity; binning sensitivity remains a real,
  unchecked assumption.
- Did not follow up on the 2 suggestive (uncorrected p<0.05) cells with
  a dedicated, deeper investigation -- flagged for whoever picks up
  BCR_ABL1's `mode_coparticipation`/shell-2 or CARDIAC_MYOSIN's `H_new`
  ground-state/shell-1 signal next.
