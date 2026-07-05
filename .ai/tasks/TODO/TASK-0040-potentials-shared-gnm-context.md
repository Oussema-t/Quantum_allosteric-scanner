# TASK-0040 `potentials.py` recomputes the GNM eigendecomposition redundantly

## Context

- ID: TASK-0040
- Title: `_gnm_msf`, `V_C`, and `V_M` each independently rebuild
  `contact_matrix → laplacian → eigh` from scratch — no shared context,
  unlike `backend/analysis.py::gnm_context()` which computes once and
  passes a context dict to all five `V_*` functions
- Status: TODO
- Owner: Implementer
- Source: review of all `Bartosz`/`bchmura`-authored commits, 2026-07-05
  session — Medium-severity finding #4
- Scope: `__WORK_IN_PROGRESS__/src/allostery/potentials.py`,
  `__WORK_IN_PROGRESS__/src/allostery/hamiltonians.py::build_H_new` (caller)

## ⚠️ Before implementing

**Do a short review before refactoring** — confirm this is actually worth
fixing now vs. later: `build_H_new` calls all five `V_*` functions once
per Hamiltonian evaluation, so the redundant O(N³) eigendecomposition cost
multiplies with however many times `build_H_new` gets called (once per
target in a simple pipeline run, but potentially hundreds/thousands of
times inside a future hyperparameter search or ceiling-optimization loop —
TASK-0008's `analysis.py::benchmark`/ablation work, or the notebook §8's
coordinate-descent search once that's ported). If nothing calls
`build_H_new` in a hot loop yet, this may be worth deferring until that
work actually lands, to avoid optimizing prematurely.

## Intent Contract

- Outcome: `build_H_new` computes the shared GNM context (contact matrix,
  Kirchhoff, eigendecomposition) once per call and passes it to whichever
  of `V_R`/`V_C`/`V_M` need it, mirroring `backend/analysis.py::gnm_context`'s
  already-proven pattern — same public function signatures for `V_B`/`V_T`
  (which don't need the GNM context at all), but `V_R`/`V_C`/`V_M` gain an
  optional pre-computed-context parameter.
- In Scope:
  - add a `gnm_context(coords, cutoff)` helper to `potentials.py` (or
    import/adapt the shape from `backend/analysis.py`'s — port the
    pattern, not the code, per this repo's cross-package convention
    already established in TASK-0005/TASK-0030).
  - update `_gnm_msf`, `V_R`, `V_C`, `V_M` to accept an optional
    pre-computed context, falling back to computing their own if none is
    passed (keeps each function independently callable/testable, which
    the existing unit tests rely on).
  - update `build_H_new` to compute the context once and pass it through.
- Out Of Scope: touching `backend/analysis.py::gnm_context` itself, or
  merging the two implementations — per TASK-0018's established
  principle, port the pattern across the `backend/`↔`allostery/`
  boundary, don't share code.
- Constraints And Invariants: must not change any existing test's
  expected output — `test_potentials.py`'s current assertions call
  `V_R`/`V_C`/`V_M` directly with just `(coords, cutoff)`; those call
  signatures must keep working unchanged (context stays optional).
- Planned Validation: existing `test_potentials.py` suite passes
  unchanged; a new test confirms `build_H_new`'s output is numerically
  identical before/after the refactor on a synthetic fixture; a rough
  timing comparison (not necessarily a formal benchmark) showing the
  eigendecomposition count actually dropped from 3 to 1 per `build_H_new`
  call.

## TODO

- [ ] Confirm whether this is worth doing now or deferring (see callout).
- [ ] Add the optional shared-context parameter to `_gnm_msf`/`V_R`/`V_C`/`V_M`.
- [ ] Wire `build_H_new` to compute once and pass through.
- [ ] Re-run `test_potentials.py`; add the numerical-equivalence + timing
      checks.

## Dependency

- None (self-contained within `potentials.py`/`hamiltonians.py`); loosely
  related to TASK-0018/TASK-0008 (whichever eventually drives repeated
  `build_H_new` calls makes this fix more urgent, not more necessary).

## Open Questions

- Defer entirely until TASK-0008 (or the ceiling/hyperparameter-search
  work) actually creates a hot loop calling `build_H_new` repeatedly? Or
  fix now since it's cheap and self-contained regardless? Leaning toward
  "fix now, it's small," but flagging since the Constraints section
  already asks the same question from a different angle.

## Done

(not yet)
