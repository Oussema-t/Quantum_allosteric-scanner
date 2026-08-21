# TASK-0130 `time_averaged_ctqw`'s own literature-grounded convergence criterion is computationally infeasible to satisfy

## Context

- ID: TASK-0130
- Title: [[TASK-0109]]'s `min_adequate_t_max(kind="time_averaged_ctqw")`
  (AAKV-style time-averaging bound) is mathematically sound but, per
  [[TASK-0110]]'s real-data check (`.ai/invariants/INV-0005-propagator-
  time-parameters.md`), prescribes `t_max` = 4.82e6 (KRAS_G12C),
  2.18e6 (BCR_ABL1), 5.92e7 (CARDIAC_MYOSIN) — 145,000x to 3,950,000x
  the shipped default of 15. A single `time_averaged_ctqw` call at the
  prescribed `n_steps` did not return after 2+ hours on real KRAS_G12C
  data (confirmed still computing, not hung, before being killed). The
  module's current `O(n_steps)` explicit-loop implementation cannot
  evaluate its own literature-grounded validity criterion on any real
  target at all.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-18
- Source: found by [[TASK-0110]] while running the Optuna floor scan;
  documented in `.ai/invariants/INV-0005-propagator-time-parameters.md`'s
  own KNOB row. Not yet filed as its own task before this.
- Priority: **Escalated to P0, 2026-07-18** — per
  `.ai/reviews/REVIEW-panel-2026-07-17.md` §2.3, §4 P0-1, §6.3 action #1.
  Independently confirmed by this Architect/Planner thread: `fix_clock_
  operator_sweep.py:181,325` (the script [[TASK-0119]]/[[TASK-0129]] both
  built on) calls `min_adequate_t_max(..., kind="ground_state_
  relaxation", ...)` to derive `t*`, then feeds that `t*` into a
  `time_averaged_ctqw(...)` call — the *other* branch's criterion, the
  one this task's own infeasibility finding is about, is never satisfied.
  `COMPETENCE_MAP.md` calls the resulting numbers the "fully corrected
  convention" with no disclosure of this residual gap anywhere in the
  document (checked directly, grepped for "AAKV"/convergence caveats —
  none found). This was a deliberate, documented tradeoff by TASK-0119
  (avoiding the AAKV criterion's own practical infeasibility, exactly
  this task's finding) — not a fresh instance of the seed bug's
  unnoticed-inconsistency shape — but its cost never propagated into the
  headline document, which is the actual problem this escalation fixes.
  **Landing this task correctly closes [[TASK-0108]], [[TASK-0109]],
  [[TASK-0110]], [[TASK-0117]], [[TASK-0119]], [[TASK-0129]] and
  [[Q-0003]] at once** — every one of them exists to manage a clock
  parameter this task's own fix removes the need for entirely.

## Intent Contract

- Outcome: `time_averaged_ctqw` computed via its own already-known
  closed form at the true infinite-time limit —
  `P_∞(i,j) = Σ_k |⟨i|k⟩|²|⟨j|k⟩|²` (already noted in `RESULTS.md`
  and `.claude/hypotheses/physics.md`'s HYP-P6, and empirically
  confirmed Spearman 0.9998 against the current finite-`t_max=15`
  approximation, per `REVIEW-panel-2026-07-16-v2.md` §1.1) — replacing
  the current `O(n_steps)` explicit time-loop for the specific case
  where the caller wants the converged/time-averaged value, not a
  finite-time snapshot.
- Why this is the right fix, not just a bigger cap: this project's own
  documentation already treats `time_averaged_ctqw` at `t_max=15` as
  "effectively decoherent" / a proxy for the infinite-time limit — if
  that's the actual quantity of scientific interest, computing it
  directly (via eigenvector overlaps, already available from the same
  `eigh` call every propagator performs) is both cheaper and exact,
  removing the `n_steps`/`t_max` validity question for this specific
  propagator entirely rather than chasing an ever-larger practical cap.
- In Scope:
  - **Do not build this from scratch — promote what already exists.**
    `scripts/propagator_convergence_battery.py::_true_diagonal_ensemble`
    (lines ~129-134) already implements this exact formula —
    `(v**2) @ (v[source,:]**2)`, normalized — as real, working code, used
    to validate `check_convergence`'s own predictions against ground
    truth. It is a private helper in a validation script, not a public
    production function. This task's actual job is exposing it properly
    in `propagators.py` (new function or a `t_max=None`/`converged=True`
    option on `time_averaged_ctqw` — Implementer's call, state the API
    decision and why in Done), not re-deriving the math.
  - **Correctness note the panel review insists on, not optional**: the
    index-wise formula `Σ_k |v_k(j)|²|v_k(source)|²` is exact only for a
    non-degenerate spectrum. The rigorous object groups by eigenvalue —
    `M = Σ_r E_r ∘ E_r` over spectral idempotents (Godsil's average
    mixing matrix). This project's real spectra are near-degenerate, not
    exactly degenerate (confirmed independently by both TASK-0129's own
    BCR_ABL1 finding and this review's §2.3), so the plain index formula
    is numerically fine as a first implementation — but given §2.2's
    already-confirmed BLAS-order sensitivity on near-continuum spectra,
    assert a minimum gap or group near-equal eigenvalues within a stated
    tolerance before trusting the result on any target with a
    near-degenerate spectrum. Do not inherit a new silent bug while
    fixing the old one.
  - Verify it matches the current finite-`t_max=15` approximation to
    within the already-measured Spearman 0.9998 (regression-pin this
    exact number as a sanity check, not just "looks similar").
  - Verify it matches a direct, brute-force finite-`t_max` calculation
    in the limit of large `t_max` on a small synthetic system where the
    explicit loop is still tractable (cross-check the closed form
    against the thing it's replacing, not just against itself).
  - Update `check_convergence`/`min_adequate_t_max(kind="time_averaged_
    ctqw")`'s own documentation to note that the closed form sidesteps
    this criterion entirely for callers who adopt it, rather than
    leaving the infeasibility as a dead end.
  - **Recompute the full competence map** (floor/ceiling/actual, all 3
    mandatory targets, the 96-cell operator sweep, the BCR_ABL1 trapping
    reproduction) under the closed form — no `t_max`/`t*`/seed-clock
    convention left to disclose or get wrong, since there is no longer a
    finite-time parameter for `time_averaged_ctqw` at all. This
    supersedes [[TASK-0129]]'s own combined-convention numbers, additive
    per the no-silent-overwrite convention (stack a new `SUPERSEDED`
    banner on `COMPETENCE_MAP.md`, do not delete the prior layers).
  - **Wire in [[TASK-0112]]'s bootstrap CI while recomputing** — that
    mechanism already exists (`diagnostics.classify_failure(return_
    ci=True)`) and has been run once already (on the pre-TASK-0129
    numbers); apply it to this task's own recompute directly rather than
    doing a second, separate CI-only pass afterward.
  - **Fix two stale predictions found by the panel review while touching
    this**: `ALGORITHM_REGISTER.md:30` ("KRAS Switch-II likely fails")
    and `HOLO_DIRECTION_MODULE.md:69` ("KRAS Switch-II is the expected NO
    case") both still contradict [[TASK-0120]]'s own measured
    `LEARNABLE`/CO=0.638 result — correct both additively while this
    task is already updating cross-referenced documents.
- Out Of Scope:
  - Changing `ground_state_relaxation`'s own convergence criterion or
    default `t_max` — unaffected, different propagator, different
    mechanism (exponential convergence to a single ground state, not a
    time-average).
  - [[TASK-0131]]'s permutation null and [[TASK-0116]]'s `_PARAM_RANGES`
    fix — this task recomputes the ceiling under the closed form, it
    does not add a null or fix the search bounds; both are separate,
    parallel-safe tasks whose own results should be read against
    whatever numbers this task produces, not against the old ones.
- Constraints And Invariants: the closed-form result must be
  deterministic and reuse the already-computed `eigh` decomposition
  where the caller has one available (same reuse discipline as
  `check_convergence`'s own existing convention).
- Planned Validation: the Spearman-0.9998 regression pin, plus the
  small-synthetic-system brute-force cross-check, both required before
  this replaces (or is offered as an alternative to) any existing call
  site.

## In Progress

None

## TODO

- [x] Promote `_true_diagonal_ensemble` from the validation script into
      a real `propagators.py` function (or option), with the
      degenerate-spectrum grouping guard.
- [x] Regression-pin agreement with the current `t_max=15` approximation
      (Spearman ≥ 0.9998, matching the already-measured value). Found:
      the claim was about the AAKV-adequate t_max, not the shipped
      default (t_max=15 itself only reaches ~0.634) — both pinned.
- [x] Cross-check against a brute-force finite-`t_max` loop on a small
      synthetic system.
- [x] Update `check_convergence`/`min_adequate_t_max` docs to note the
      closed-form escape hatch.
- [x] Recompute floor/ceiling/actual (all 3 targets), the 96-cell sweep,
      and the BCR_ABL1 trapping reproduction under the closed form.
- [x] Wire TASK-0112's bootstrap CI into this same recompute pass.
- [x] Fix `ALGORITHM_REGISTER.md`/`HOLO_DIRECTION_MODULE.md`'s stale
      KRAS Switch-II predictions, additively.
- [x] Stack a new `SUPERSEDED` banner on `COMPETENCE_MAP.md`; close
      [[Q-0003]] with a final pointer to this task if still open.

## Dependency

- [[TASK-0109]] (Done) — the criterion this task's finding responds to.
- [[TASK-0110]] (Done) — found the infeasibility this task fixes.
- Supersedes [[TASK-0129]]'s own combined-convention numbers — that
  task's own results remain on record, additive, not deleted.
- Parallel-safe with [[TASK-0131]] (ceiling permutation null) and
  [[TASK-0116]] (ceiling search range fix) — neither blocks this task,
  and this task's recompute is what their own results should ultimately
  be read against.

## Open Questions

- Whether to expose this as a new function name or a parameter on the
  existing `time_averaged_ctqw` — Implementer's call, state the API
  decision and why in Done.

## Done

**2026-07-18, Implementer B.** Closed form implemented, tested, and
promoted; full competence-map/96-cell-sweep/trapping-reproduction
recompute done; TASK-0112 CI wired in directly; both stale docs fixed;
`COMPETENCE_MAP.md` SUPERSEDED banner stacked; Q-0003 fully closed.

### Closed-form implementation

New `propagators.time_averaged_ctqw_converged(H, source=0, *, coherent,
degenerate_tol, w, v)` — a new function, not a `time_averaged_ctqw(
t_max=None, ...)` option (Open Question, resolved: keeps
`time_averaged_ctqw`'s existing signature/behavior untouched, ADD-only;
a caller reading the new name does not need this project's own
t_max-infeasibility history to understand what it computes). Promoted
`scripts/propagator_convergence_battery.py`'s private
`_true_diagonal_ensemble` formula (`sum_k |v_k(j)|^2|v_k(source)|^2`)
rather than re-deriving it, per the task's own In Scope instruction.

**Correctness note the Intent Contract insisted on, addressed for
real, not assumed away**: the plain index-wise formula is exact only
for a non-degenerate spectrum. Implemented `_group_degenerate_
eigenvalues`/`_block_projected_diagonal` — groups (near-)exactly
degenerate eigenvalues into blocks (tolerance = `degenerate_tol *
H`'s own bandwidth, default `1e-6`, small enough to only catch true/
near-machine-precision degeneracies like TASK-0128's ANM zero modes,
not this project's real near-continuum-but-distinct spectra) and sums
amplitudes *within* a block before squaring (Godsil's average mixing
matrix, `M = sum_r E_r o E_r`), rather than dropping cross terms
within a degenerate block the way the naive formula would. Reduces
algebraically to the plain formula when every block is a singleton
(verified exactly, `test_matches_true_diagonal_ensemble_formula_
directly`). Regression test `test_degenerate_block_result_is_
invariant_to_the_chosen_eigenbasis` constructs two different valid
eigenbases of the same exactly-degenerate synthetic H by hand (a
"localized" one and a rotated/mixed one) and proves: the grouped
formula gives an identical, basis-independent answer either way; the
naive ungrouped formula does not (and is concretely wrong for the
mixed basis) — this is the real bug class the correctness note warned
about, not a hypothetical.

### Tests (both files, `test_propagators.py` new `TestTimeAveragedCtqwConverged`
class + 2 standalone real-target tests, plus new tests in
`test_analysis.py`/`test_ceiling.py`/`test_protocol.py` for the new
`use_converged_limit` flag — 703+ total suite, all green, see below)

- Brute-force cross-check against `time_averaged_ctqw` at a large
  `t_max` on a small non-degenerate synthetic system.
- Exact-formula match against the promoted `_true_diagonal_ensemble`
  formula directly.
- Precomputed-`(w,v)`-reuse test (spies `np.linalg.eigh`, confirms zero
  calls) — the task's own Constraint ("reuse the already-computed eigh
  decomposition where the caller has one available").
- `ValueError` without `H` or `(w,v)`.
- Coherent/incoherent behavior matches `ctqw`'s own convention (scalar
  source: identical either way; multi-index: differ, matching
  TASK-0118's panel-recommended incoherent-mixture convention).
- Degenerate-eigenbasis invariance (described above), both via the
  private helpers directly and through the public function end-to-end.

**Planned-Validation finding, not assumed** (Spearman-0.9998 pin):
measured directly on real KRAS_G12C `H_new` (post-TASK-0121
renormalization) that the pipeline's *shipped default* `t_max=15`
achieves only **Spearman~0.634** against this closed form — nowhere
near 0.9998. Traced the discrepancy, not just reported it: Spearman
climbs monotonically as `t_max` grows and crosses 0.9998 right around
`t_max~15,000` (measured 0.998804 at 1,500; 0.999779 at 15,000) — the
same order of magnitude as TASK-0110's own AAKV-prescribed scale-up.
Conclusion: the historical "0.9998... at the operating t_max" claim
(`REVIEW-panel-2026-07-16-v2.md` §1.1) referred to the AAKV-*adequate*
t_max, not the hardcoded default — both pinned as separate, permanent
regression tests (`test_..._vs_adequate_t_max` asserts >=0.9998 at
t_max=15000; `test_shipped_default_t_max_15_is_far_from_converged`
asserts <0.9 at t_max=15, real value ~0.634) so this finding cannot
silently regress back to "looks fine either way" without a test
noticing. This also independently re-confirms the closed form is the
correct limit the finite average is provably converging to.

### `use_converged_limit` (ADD-only, default `False`, ADD-only across all changes)

Threaded a new `use_converged_limit: bool = False` parameter through
`analysis.quantum_vs_classical`/`analysis.benchmark`/`analysis.
operator_sweep`, `ceiling.consistency_score`/`ceiling.ceiling_search`,
and `protocol.run_frozen_verdict` — `False` is byte-identical to every
existing call site (verified: full existing suite green, zero
modification to any existing test); `True` swaps the `"ctqw"` side to
`time_averaged_ctqw_converged`, ignoring `t_max`/`n_steps` for that
propagator only (`ground_state_relaxation`/`"ground_state"` rows are
unaffected either way, out of this task's own scope). New regression
tests per function (spy-based, confirming the actual function called
changes, not just an AUC-level difference) — see `test_analysis.py`/
`test_ceiling.py`/`test_protocol.py`'s new `test_use_converged_limit_*`
tests. `run_frozen_verdict`'s own `ablation()`/`select_frozen_config`
calls are deliberately unaffected (documented, same boundary as the
existing `coherent` flag) — this parameter changes what gets
*reported* once a candidate has won, not candidate selection itself.

### Full recompute (new scripts, standalone, do not touch live-pipeline
defaults — same discipline as TASK-0129's own scripts)

- `scripts/closed_form_competence_map_rerun.py`: floor/ceiling/actual,
  all 3 mandatory targets, via `protocol.run_frozen_verdict`/`ceiling.
  ceiling_search(use_converged_limit=True)`. TASK-0112's CI comes free
  from `run_frozen_verdict` (already wired into its own return value,
  `_diagnosis_score_ci`/`_diagnosis_floor_ci`/`_diagnosis_ci_overlap`)
  for "actual"; added `metrics.block_bootstrap_ci` directly for
  "ceiling" (recomputes the winning trial's occupation once more, since
  `ceiling_search` doesn't retain raw occupation vectors) and "floor".
  Real results (`results/tasks/0130_competence/closed_form_competence.json`):

  | Target | Floor [95% CI] | Ceiling [95% CI] | Actual [95% CI] | Diagnosis | Headroom | CI overlaps floor? |
  |---|---|---|---|---|---|---|
  | KRAS_G12C | 0.4818 [0.333,0.675] | 0.6288 [0.466,0.773] | 0.5901 [0.373,0.748] | `NO_FAILURE_DETECTED` | +73.7% | Yes |
  | BCR_ABL1 | 0.5817 [0.414,0.720] | 0.6671 [0.530,0.784] | 0.5266 [0.381,0.662] | `NO_SIGNAL_IN_APO` | -64.5% | Yes |
  | CARDIAC_MYOSIN | 0.7921 [0.577,0.913] | 0.8297 [0.615,0.926] | 0.7272 [0.549,0.853] | `BEATS_CHANCE_NOT_FLOOR` | -173.0% | Yes |

  **Headline, real and unforced**: KRAS_G12C's point-estimate diagnosis
  flips `NO_SIGNAL_IN_APO` (TASK-0129) -> `NO_FAILURE_DETECTED` here —
  actual clears its own floor by a real point-estimate margin once the
  clock gauge is fully removed rather than merely corrected. **Not
  overclaimed**: the 95% CI still overlaps the floor's own CI for all
  three targets — none of the three is a *statistically decided* win,
  same overall conclusion as TASK-0129 ("no mandatory target's shipped
  actual result is a decided win"), reached with zero remaining
  clock-gauge uncertainty this time.
- `scripts/closed_form_operator_sweep.py`: 96-cell sweep (16 operators
  x 2 propagators x 3 targets, `analysis.operator_sweep(
  use_converged_limit=True)`) + BCR_ABL1's TASK-0106 trapping
  reproduction, both under the closed form. Cross-validated against the
  competence-map script independently: KRAS_G12C `H_new`/`ctqw` AUC
  agrees to 3 decimals (0.590) via two separate code paths. Full
  results/report: `results/tasks/0130_competence/closed_form_sweep.json`/
  `sweep_report.md`, `trapping_reproduction_closed_form.json`.

  **Secondary finding, real, not chased further (flagged for whoever
  next touches the trapping question)**: at the true infinite-time
  limit, `H_new_default`'s participation ratio (0.0079) on BCR_ABL1 is
  no longer distinguishable in kind from `H10`/`H2`'s (0.0077-0.0079)
  — the localization/trapping *contrast* TASK-0106/TASK-0119 measured
  at finite `t_max`/`t*` (PR 0.299 vs. comparable) largely washes out
  once every eigenmode has had time to contribute. Does not retract
  TASK-0119's own finding (real and gauge-robust at the timescale it
  measured) — shows that timescale is not the converged endpoint, a
  distinct fact from "is the localization real."

### Docs

- `check_convergence`/`min_adequate_t_max` (`propagators.py`): both
  docstrings now note the closed-form escape hatch and point to
  `time_averaged_ctqw_converged` for a caller who wants the converged
  value rather than a bounded finite-time snapshot (both functions
  remain correct and useful for the latter case, not superseded).
- `COMPETENCE_MAP.md`: new SUPERSEDED banner (3rd layer) + new primary
  table + trapping-reproduction finding; TASK-0129's own table kept
  intact below, not deleted; "Open items" section updated additively —
  TASK-0110/BCR_ABL1 short-`t_max` tension, the BCR_ABL1 gap
  reproducibility flag, TASK-0117, and `H10`'s own `t*` all marked
  **MOOT** (not "resolved" — the numerical questions they raised no
  longer have an object to be about, since no clock is computed for
  this quantity anymore), each kept below for the record per this
  document's own convention.
- `ALGORITHM_REGISTER.md`/`HOLO_DIRECTION_MODULE.md`: both stale "KRAS
  Switch-II likely fails"/"expected NO case" predictions corrected
  additively against TASK-0120's own measured `LEARNABLE`/CO=0.638
  result (unrelated stale content elsewhere in either file untouched).
- Q-0003 (`.ai/memory/questions/architect-planner/answered/Q-0003-...
  md`): appended a 2026-07-18 update declaring it fully closed — the
  framing has now been exercised under three successive gauge
  corrections (seed, clock, clock-removal) and held up each time,
  including honestly surfacing this task's own new, not-yet-decided
  finding rather than manufacturing a clean win.

### Tasks this closes (per the task file's own Priority note)

TASK-0108/0109/0110/0117/0119/0129 and Q-0003 all existed to manage a
clock parameter this task's own fix removes the need for entirely —
each now has nothing further to do on the clock axis specifically
(their own scientific findings at the time they landed stand on
their own merits, not retracted).

### Not attempted / left for a follow-up task

- `quantum_vs_classical`/`benchmark`/etc.'s `ground_state_relaxation`
  side is unaffected by design (Out Of Scope, explicitly) — its own
  convergence criterion and default `t_max=15` are untouched.
- `ablation()` was not given a `use_converged_limit` option — it is not
  part of floor/ceiling/actual/the 96-cell sweep/the trapping
  reproduction (this task's own In Scope enumeration), and adding it
  would be scope creep beyond what any of this task's own deliverables
  needed.
- TASK-0116 (ceiling search coverage, 60 blind random draws) remains
  its own separate, genuinely open question — never part of what this
  task or Q-0003 addressed; explicitly noted as still open in
  `COMPETENCE_MAP.md`'s own updated Open Items.
- Did not re-run TASK-0081's generalization-set (ASD) rows under the
  closed form — out of this task's own named scope (floor/ceiling/
  actual/96-cell-sweep/trapping-reproduction only).
