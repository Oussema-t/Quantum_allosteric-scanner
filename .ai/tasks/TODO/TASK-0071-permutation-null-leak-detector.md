# TASK-0071 Permutation-null leak detector

## Context

- ID: TASK-0071
- Title: Add a label-permutation null to `diagnostics.py` as a catch-all
  leakage *detector*, backstopping the DEV/FROZEN firewall's *preventive*
  role.
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 1, item 1.4 — "The
  firewall *prevents* known leak vectors; nothing *detects* an unforeseen
  one. Shuffle labels, re-run, flag anything still scoring. Home:
  `diagnostics.py`. Verified reference implementation exists" (i.e. the
  notebook already has a version of this to port from).

## Intent Contract

- Outcome: a function in `diagnostics.py` that shuffles the true labels
  (breaking any real signal), re-runs the scoring pipeline, and flags if
  the permuted-label score is still significantly above chance — which
  would indicate a leak the firewall didn't anticipate (e.g. an index
  alignment bug that leaks structure rather than label identity).
- In Scope: `diagnostics.py` — new permutation-null function; wiring it as
  a check callable alongside `classify_failure`/`operator_diagnostics`.
- Out Of Scope: fixing any leak it finds — this task builds the detector;
  a leak found by running it becomes its own bug-fix task.
- Acceptance Scenarios:
  - Given a target with known real signal (a benchmark protein scoring
    above chance honestly), when labels are permuted N times and the
    pipeline re-scores each permutation, then the permuted-score
    distribution should center on chance (~0.5 AUC) with the real score
    a clear outlier — this is the sanity check that the detector itself
    works before trusting it to catch real bugs.
  - Given a synthetic leak deliberately introduced (e.g. skip the
    DEV/FROZEN split), when the permutation null runs, then it flags the
    leak (permuted scores also elevated).
- Constraints And Invariants: port the "verified reference implementation"
  mentioned in the plan from the research notebook — cite the section.
- Planned Validation: the two acceptance scenarios above, run against at
  least one real benchmark target and one synthetic-leak fixture.

## Dependency

- Reads `diagnostics.py` (TASK-0009, Done), `protocol.py`'s DEV/FROZEN
  split (TASK-0006, Done).
- Related to TASK-0056 (Phase 4 review of `diagnostics.py` et al.) — worth
  reading together since both touch the same module.

## Open Questions

- Which notebook section is the "verified reference implementation" the
  plan refers to? Locate and cite before implementing from scratch.

## Done

(not yet)
