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
- Priority: **P1.** Not blocking [[TASK-0129]]'s combined re-run (which
  uses `n_steps` capped at a practical ceiling, per TASK-0119's own
  `N_STEPS_PRACTICAL_CAP=5000` precedent) — but means every
  `time_averaged_ctqw` number this project has ever reported, including
  post-TASK-0118/0119 ones, is running at an `n_steps` far short of
  this criterion's own prescription, silently capped rather than
  validated.

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
  - Add a closed-form infinite-time-average path to `propagators.py`
    (new function or a `t_max=None`/`converged=True`-style option on
    the existing one — Implementer's call, state the API decision and
    why in Done).
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
- Out Of Scope:
  - Changing `ground_state_relaxation`'s own convergence criterion or
    default `t_max` — unaffected, different propagator, different
    mechanism (exponential convergence to a single ground state, not a
    time-average).
  - Re-running every past `time_averaged_ctqw`-based result under the
    new closed form — a separate follow-up once this lands and is
    trusted, not this task's own scope.
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

- [ ] Implement the closed-form infinite-time-average CTQW occupation.
- [ ] Regression-pin agreement with the current `t_max=15` approximation
      (Spearman ≥ 0.9998, matching the already-measured value).
- [ ] Cross-check against a brute-force finite-`t_max` loop on a small
      synthetic system.
- [ ] Update `check_convergence`/`min_adequate_t_max` docs to note the
      closed-form escape hatch.

## Dependency

- [[TASK-0109]] (Done) — the criterion this task's finding responds to.
- [[TASK-0110]] (Done) — found the infeasibility this task fixes.
- Not blocking [[TASK-0129]] — that task uses the existing practical
  cap, this task is a deeper, independent fix.

## Open Questions

- Whether to expose this as a new function name or a parameter on the
  existing `time_averaged_ctqw` — Implementer's call, state the API
  decision and why in Done.

## Done

(not yet)
