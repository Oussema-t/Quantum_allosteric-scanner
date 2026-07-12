# TASK-0089 Classify `select.py`'s reported quantities (closes `INV-0004`)

## Context

- ID: TASK-0089
- Title: Close the `GAUGE`/`KNOB`/`SIGNAL` rows [[INV-0004]] seeds for
  `unsupervised_score`/`focusing`/`source_specificity`/`ballistic_exponent`
- Status: TODO
- Owner: Implementer
- Source: flagged by [[TASK-0064]] (closing [[SEAM-0009]], wiring
  `unsupervised_score` into a real FROZEN-loop consumer via
  `protocol.select_frozen_config`) — that task's own Constraints noted
  `select.py` has zero `.ai/invariants/` coverage per
  [[TASK-0051]]'s Invariance Protocol ("No transformation table → not
  reportable"), and deliberately did not build it inline, same
  in-scope/out-of-scope split [[TASK-0054]]/[[TASK-0055]] already use
  against [[INV-0001]].
- Scope: `__WORK_IN_PROGRESS__/src/allostery/select.py`'s four scoring
  functions and [[INV-0004]]'s seeded rows only. No change to `select.py`
  itself expected unless a real GAUGE violation is found (then: fix and
  regression-test it, same as `superpose.py`'s `w[6:]` precedent
  `INVARIANCE_PROTOCOL.md` documents).

## Intent Contract

- Outcome: every row [[INV-0004]] seeds moves from `OPEN` to
  `GAUGE-VERIFIED` / `KNOB-CHARACTERIZED` / a documented `SIGNAL` null
  control — or, if a row turns out not to apply, an explicit note saying
  why, not silent removal.
- In Scope:
  - **GAUGE**: residue-relabeling invariance (permute `H`'s indices +
    `source` consistently, assert every score unchanged to `atol≈1e-9`);
    RNG-seed stability for `source_specificity`'s `n_alt`-sample step
    (report a CI/spread across seeds, or prove it's deterministic given a
    fixed `rng`); candidate-list-order stability for `unsupervised_score`
    (reorder `candidates`, assert the same winner by content, not index).
  - **KNOB**: characterize `t`/`t_max`/`n_steps`/`n_alt`/`t_values` as a
    spread over a small grid on a synthetic case (per
    `INVARIANCE_PROTOCOL.md` Tier 2 — report the spread, don't assert a
    point estimate).
  - **SIGNAL**: a shuffled/randomized-`H` null control (a garbage
    candidate must not out-score a real structural one); document the
    single-candidate degenerate case.
- Out Of Scope: `protocol.select_frozen_config`'s own gating behavior
  (TASK-0064's own seam-tests already cover that) — this task audits
  `select.py`'s scoring functions themselves, not their FROZEN-loop
  wiring.
- Constraints And Invariants: per `INVARIANCE_PROTOCOL.md`'s own rule of
  engagement, "invariant on our test set" is not a green light — widen
  the transformation group actually tested (real permutations, not one
  fixed relabeling) rather than asserting on a single convenient case.
- Planned Validation: `INV-0004`'s own rows, each with a named passing
  test; existing `test_select.py` suite unchanged.

## In Progress

None

## Dependency

- [[TASK-0007]] (`select.py`, Done) — the module under audit.
- [[TASK-0064]] (Done) — found and flagged this gap; seeded [[INV-0004]].
- [[INV-0001]]/[[TASK-0054]] — the precedent this task's split follows.

## Open Questions

- None yet — surface once the permutation/RNG tests are actually written;
  [[INV-0004]]'s seed rows are candidate transformations reasoned from
  each function's signature, not yet verified as complete or correct.

## Done

(not yet)
