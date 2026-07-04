# TASK-0016 Add test for `heat()` behavior on indefinite `H_new` output

## Context

- ID: TASK-0016
- Title: Add a test confirming `heat()` either raises or is documented as
  unsupported when given `H_new`'s indefinite spectrum
- Status: TODO
- Owner: Implementer
- Source: `.claude/improvements/test_coverage.md` ("Missing: Propagators"
  section) explicitly says this test is "**Not yet in TASKS.md — must be
  added**" and points to `.claude/improvements/hamiltonian_code.md` IMP-H4.
  It never received a `T-NNN` ID and was still dangling when TASK-0002
  (2026-07-04) audited the scaffold for orphaned work. Per the Task Ledger
  Boundary decided in TASK-0002 (`.ai/COMMON.md`), it is filed here as a
  `TASK-XXXX` rather than as a new `T-022` in `.claude/TASKS.md`, which is
  now closed to new entries.
- Scope: `__WORK_IN_PROGRESS__/tests/test_propagators.py` (or wherever
  `heat()` is currently tested — confirm exact file before editing) + at
  most a small guard/docstring change in
  `__WORK_IN_PROGRESS__/src/allostery/propagators.py::heat` if Option 1 or 2
  below is chosen instead of Option 3.

## Intent Contract

- Outcome: `heat()`'s behavior on indefinite input (which `H_new` produces
  by design via its `V_R`/`V_C`/`V_M` reward terms — negative eigenvalues
  make `exp(-w*t)` grow unboundedly for large `t`) is either guarded against
  or explicitly documented as unsupported, and a test locks in whichever
  choice is made.
- In Scope:
  - read `.claude/improvements/hamiltonian_code.md` IMP-H4 for the three
    fix options (1: raise `ValueError` if `(w < -1e-8).any()`; 2: clip
    negative eigenvalues with a warning; 3: docstring-only, direct callers
    to `ctqw()`/`haken_strobl()` instead)
  - pick one option (IMP-H4 already recommends Option 3 as sufficient for
    now, Option 1 as the safer long-term fix — Implementer should state
    which was chosen and why in this file's Done section)
  - write a test that exercises the chosen behavior deterministically:
    build a small `H_new` (or any indefinite Hamiltonian) with a known
    negative eigenvalue, call `heat()`, and assert the documented
    behavior (raises / clips+warns / caller-beware docstring exists and a
    smoke test still runs without asserting boundedness)
- Out Of Scope: broader refactors of `propagators.py`; the other six IMP-H
  items in `hamiltonian_code.md` (separate concerns, not test gaps).
- Acceptance Scenarios:
  - Given an `H_new`-shaped indefinite Hamiltonian, when `heat()` is called
    with a large `t`, then the chosen documented behavior (raise, clip, or
    explicit unsupported-docstring) is exercised by an automated test.
  - Given `.claude/TESTS.md`'s standards, when this new test is added, then
    it states the property it verifies (not just "runs without error") and
    follows the synthetic-data-preference convention.
- Constraints And Invariants:
  - keep `.claude/TESTS.md` conventions (seeded RNG if any, explained
    tolerances, synthetic small graphs preferred).
  - additive — do not touch unrelated propagators or existing passing
    tests.
- Planned Validation: `pytest` on the touched test file; confirm the new
  test fails against the *pre-fix* `heat()` (if Option 1/2 chosen) to prove
  it isn't vacuous.

## In Progress

(not started)

## TODO

- [x] Locate current `heat()` tests and confirm there's no existing
      coverage of this exact behavior. **Done (TASK-0002 follow-up pass,
      2026-07-04):** there is no `test_propagators.py` — `heat()` is
      exercised in `tests/test_hamiltonians.py` (lines ~522-582, all
      against a PSD Laplacian `L`, never an indefinite matrix) and
      `tests/test_physics.py` (line ~199, same). Ran the full suite
      (`pytest tests/` from `__WORK_IN_PROGRESS__`, venv with
      numpy/scipy/scikit-learn/networkx/pyyaml/pytest installed):
      **123 passed, 1 skipped** (the skip is `test_eff_rank_kras_regression`
      / T-004/T-017, missing `prody` — an unrelated, already-known,
      correctly-tracked blocker, not this task's concern). Confirms this
      gap is real and still open, not already covered.
- [ ] Choose Option 1, 2, or 3 from IMP-H4; state the choice and reasoning.
      **Note:** `heat()`'s docstring already says "H should be a
      positive-semidefinite Laplacian" — Option 3's documentation half is
      partially in place. What's still missing is (a) an explicit warning
      that `H_new` specifically violates this and callers should use
      `ctqw()`/`haken_strobl()` instead, and (b) the test itself either way.
- [ ] Implement the guard/docstring change if Option 1 or 2.
- [ ] Add the test; run `pytest` locally.

## Dependency

- None. Independent of TASK-0003…TASK-0015 (those are new-module builds;
  this is a gap in existing, already-`[have]` `propagators.py`).

## Open Questions

- Should this also cross-reference `H10_disorder_supp` or any other
  operator that might produce indefinite spectra, or is `H_new` the only
  current indefinite operator in the codebase? Confirm via
  `hamiltonians.py` before assuming scope is `H_new`-only.

## Done

(not yet)
