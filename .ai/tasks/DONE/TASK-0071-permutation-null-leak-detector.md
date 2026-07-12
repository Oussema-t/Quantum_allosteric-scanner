# TASK-0071 Permutation-null leak detector

## Context

- ID: TASK-0071
- Title: Add a label-permutation null to `diagnostics.py` as a catch-all
  leakage *detector*, backstopping the DEV/FROZEN firewall's *preventive*
  role.
- Status: Done
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
  **Resolved:** not the research notebook at all — grepping it for
  "permut"/"shuffle" found nothing (only JSON `"execution_count": null`
  noise). The real reference is
  `__WORK_IN_PROGRESS__/tests/test_leakage_gate.py`'s GATE-B4
  `permutation_null` + `PERM_LEAK_THRESHOLD = 0.60`, explicitly
  self-validated there by
  `test_meta_permutation_detector_discriminates` against both a
  synthetic honest and a synthetic leaky scorer. That file's own
  CONTRACT section (updated by TASK-0052) confirms directly: "GATE-B4's
  `permutation_null`... [is] this file's own reference implementation...
  not a claim that `protocol.py` has [it]" — i.e. it existed only as a
  self-validating test fixture until this task ported it into production.

## Done

- Ported `permutation_null(scorer, coords, labels, n_perm=200, seed=1)`
  and `detect_permutation_leak(...)` into `diagnostics.py`, citing
  GATE-B4 as the source in the module comment. `PERM_LEAK_THRESHOLD =
  0.60` carried over verbatim, not re-derived. Takes a `scorer(coords,
  labels) -> scores` callable (re-invoked per permutation), not a
  precomputed score array — deliberately matches the reference exactly,
  since a leak baked into the scorer itself (reads labels directly) can
  only be caught by actually re-running it, not by permuting a
  already-computed score array.
- Both acceptance scenarios validated using this package's own real
  production scorer (`hamiltonians.build_H_new` +
  `propagators.time_averaged_ctqw`) on a synthetic helix structure, not
  a toy stand-in:
  - Honest signal: `auc_true=0.94`, `perm_mean=0.47` (centered on
    chance, well under threshold) → `leak_detected=False`.
  - Deliberately leaky scorer (reads labels directly): `perm_mean=1.0`
    → `leak_detected=True`.
  - Deliberately did **not** add a network-gated KRAS_G12C test here
    (unlike TASK-0047/TASK-0008's precedent) — `PLAN.md` documents
    KRAS_G12C as scoring *near chance even with the answer key*, so it
    is not a "known real signal" case the first acceptance scenario
    needs; using it would have tested the wrong thing. The real
    production scorer is exercised regardless — this substitutes the
    synthetic-structure choice for the real-target choice, not real
    physics for synthetic physics.
- 5 new tests in `test_diagnostics.py::TestPermutationNullLeakDetector`,
  covering both acceptance scenarios plus return-shape and
  custom-threshold regression checks.
- Full local run: `python3 .ai/tools/pytest_local.py wip-all --json` →
  407 passed, 1 xfailed (TASK-0055's own SEAM-0004 test, expected), 1
  xpassed (pre-existing, unrelated), 0 failed.
- Not wired into `classify_failure` itself — Intent Contract's own
  scope is "a check callable alongside `classify_failure`/
  `operator_diagnostics`," i.e. a sibling entry point, not a change to
  either existing function's control flow.
- **Staging/commit deferred** — held per the user's manual
  Stage-Commit-Queue coordination (2nd in queue at completion time);
  code and tests are complete and locally green, not yet staged.
