# TASK-0117 Re-check TASK-0046's ceiling number once TASK-0109's convergence gate exists

## Context

- ID: TASK-0117
- Title: `ceiling.consistency_score` defaults to the same unvalidated
  `t_max=15.0`/`n_steps=500` that TASK-0108/0109/0110 (filed 2026-07-15)
  exist to check the validity of — TASK-0046's real KRAS_G12C ceiling
  run (60 trials, N=169) used these fixed values with no convergence
  check, and no CI/uncertainty measure, yet its "does not clear chance,
  very little headroom" finding is flagged as the number TASK-0082
  (competence map) should read directly.
- Status: TODO
- Owner: Implementer
- Source: `REVIEW-2026-07-15b-ceiling-search-methodology.md`, finding #2.
- Crit Ref: `ceiling.py:97-98`'s `t_max: float = 15.0, n_steps: int = 500`
  parameters are passed unchanged into `time_averaged_ctqw` for every one
  of the 60 trials `ceiling_search` ran. `TASK-0109`'s own Crit Ref
  (in `TASK-0108`) already flags this exact literal pair as applied
  identically across very differently-sized systems with zero validity
  check.

## Intent Contract

- Outcome: once TASK-0109's `check_convergence` (or equivalent) lands,
  run it against `H_new` at KRAS_G12C's scale (N=169) and confirm
  whether `t_max=15`/`n_steps=500` was adequate for the ceiling search's
  60 real trials. If inadequate, re-run TASK-0046's real cross-check
  (or a representative subset) at corrected parameters and report
  whether the near-chance conclusion holds.
- In Scope:
  - apply TASK-0109's convergence check to the specific `H_new`
    instances TASK-0046's cross-check produced (or a representative
    resample at the same parameter ranges) at KRAS_G12C's N=169 scale.
  - if convergence fails, re-run enough of TASK-0046's 60 trials at
    corrected `t_max`/`n_steps` to determine whether the best `S` found
    changes meaningfully; report both old and new values, don't
    overwrite.
  - if convergence holds (the fixed values turn out adequate at this
    scale), state that explicitly and close this task without a re-run
    — a confirmatory null result here is as useful as a corrective one.
  - cross-link the finding into `TASK-0046`'s own Done section (additive,
    per this project's no-silent-overwrite convention) and into
    `TASK-0082` if the competence map has already consumed the number by
    the time this lands.
- Out Of Scope:
  - the search-coverage question (`TASK-0116`) — this task is about
    numerical validity of a fixed evaluation, not about how well the
    parameter space was explored. Independent, can land in either order.
  - re-deriving a convergence criterion — use TASK-0109's, don't invent
    a second one.
- Constraints And Invariants: hard-blocked on TASK-0109 landing first —
  do not invent an ad hoc convergence check to unblock this task early.
- Planned Validation: TASK-0109's own convergence report applied to a
  real `H_new(KRAS_G12C, ...)` instance at the parameter values TASK-0046
  actually used; a clear pass/fail statement, not just a number.

## In Progress

None

## TODO

- [ ] Wait for TASK-0109 to land.
- [ ] Apply its convergence check to `H_new` at KRAS_G12C's scale, at
      `t_max=15`/`n_steps=500`.
- [ ] If inadequate: re-run a representative subset of TASK-0046's 60
      trials at corrected values; report old vs. new best `S`.
- [ ] If adequate: state so explicitly in Done, close without a re-run.
- [ ] Cross-link the outcome into TASK-0046 and (if already consumed)
      TASK-0082.

## Dependency

- TASK-0109 (TODO) — hard blocker, this task's own convergence check
  comes from there.
- TASK-0046 (Done) — the ceiling run this task re-validates.

## Open Questions

- None — scope fully specified; blocked, not undecided.

## Done

(not yet)
