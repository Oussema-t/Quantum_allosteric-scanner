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
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
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

- [ ] Promote `_true_diagonal_ensemble` from the validation script into
      a real `propagators.py` function (or option), with the
      degenerate-spectrum grouping guard.
- [ ] Regression-pin agreement with the current `t_max=15` approximation
      (Spearman ≥ 0.9998, matching the already-measured value).
- [ ] Cross-check against a brute-force finite-`t_max` loop on a small
      synthetic system.
- [ ] Update `check_convergence`/`min_adequate_t_max` docs to note the
      closed-form escape hatch.
- [ ] Recompute floor/ceiling/actual (all 3 targets), the 96-cell sweep,
      and the BCR_ABL1 trapping reproduction under the closed form.
- [ ] Wire TASK-0112's bootstrap CI into this same recompute pass.
- [ ] Fix `ALGORITHM_REGISTER.md`/`HOLO_DIRECTION_MODULE.md`'s stale
      KRAS Switch-II predictions, additively.
- [ ] Stack a new `SUPERSEDED` banner on `COMPETENCE_MAP.md`; close
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

(not yet)
