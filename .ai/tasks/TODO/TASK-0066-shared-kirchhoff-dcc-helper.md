# TASK-0066 Shared Kirchhoff-context + DCC numpy helper

## Context

- ID: TASK-0066
- Title: Extract a shared, unit-tested "binary-Kirchhoff-context + DCC"
  helper so `backend/analysis.py::gnm_context`/`_dcc` and
  `__WORK_IN_PROGRESS__/src/allostery/potentials.py::_gnm_msf`/`V_R`/`V_C`/
  `V_M` stop independently re-deriving the same pseudo-inverse math.
- Status: TODO
- Owner: Implementer
- Source: TASK-0018's decision doc (Done section, potentials row) —
  identical intermediate math (binary Kirchhoff pseudo-inverse → normalized
  DCC → row-sum) computed twice, diverging only at the final
  z-score-vs-max-normalize/sign step each side needs for its own consumer.
  Same pattern TASK-0030 already fixed for Kabsch/SVD — this is the same
  fix applied to the GNM/DCC axis.

## Intent Contract

- Outcome: one shared, ported (not cross-imported — `backend/` and
  `allostery/` stay independently deployable per TASK-0018's Constraints)
  numpy helper per side, each computing: binary contact matrix at a given
  cutoff → Kirchhoff (`D-A`) → pseudo-inverse → normalized DCC matrix. Each
  side's existing final-step logic (backend: z-score row-sum; allostery:
  max-normalize + negate for `V_C`, similarly for `V_R`/`V_M`) stays as a
  thin wrapper around the shared core.
- In Scope: `backend/analysis.py::gnm_context`/`_dcc`;
  `allostery/potentials.py::_gnm_msf`/`V_R`/`V_C`/`V_M`.
- Out Of Scope: changing the cutoff values themselves (that's TASK-0067);
  changing any function's public return shape/sign convention — this is a
  pure internal-implementation dedup, ADD-only in spirit even though it's
  research-scaffold code, not the live API.
- Acceptance Scenarios:
  - Given the same coordinates and cutoff, the shared helper's raw DCC
    matrix must be bit-for-bit (or float-tolerance) identical to what
    `backend/analysis.py::_dcc` and `potentials.py`'s inlined `nDCC`
    computation currently produce independently.
  - Existing call sites' final outputs (z-scored, max-normalized) must be
    unchanged before/after — a smoke test against a benchmark protein
    (e.g. KRAS_G12C) should show identical `V_rigidity`/`V_covariance`/
    `V_R`/`V_C` output pre/post refactor.
- Constraints And Invariants: port, don't share code across
  `backend/`↔`allostery/` (TASK-0018's Constraints section, unchanged
  rationale — different deployment/dependency footprints).
- Planned Validation: unit tests for the shared helper (analogous to
  `backend/test_geometry.py`) plus a before/after smoke-test diff on one
  benchmark protein per side.

## Dependency

- TASK-0018 (Done) — decision doc that found this gap and filed this task.
- TASK-0030 (Done) — same pattern, already-landed precedent
  (`backend/geometry.py`).

## Open Questions

- None yet — scope is narrow and precedent (TASK-0030) is direct.

## Done

(not yet)
