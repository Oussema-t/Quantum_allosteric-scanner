# TASK-0066 Shared Kirchhoff-context + DCC numpy helper

## Context

- ID: TASK-0066
- Title: Extract a shared, unit-tested "binary-Kirchhoff-context + DCC"
  helper so `backend/analysis.py::gnm_context`/`_dcc` and
  `__WORK_IN_PROGRESS__/src/allostery/potentials.py::_gnm_msf`/`V_R`/`V_C`/
  `V_M` stop independently re-deriving the same pseudo-inverse math.
- Status: Done
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
- **TASK-0074 (Done) — hard-rule prerequisite, added retroactively.**
  EXECUTION_PLAN.md Phase 4's rule requires TASK-0074's characterization
  tests to land before any convergence work (this task) touches
  `backend/` — omitted from this section originally since TASK-0074 was
  filed after this task; found and honored mid-implementation (see Done
  section), not before starting. Landed first, as its own earlier commit.

## Open Questions

- None yet — scope is narrow and precedent (TASK-0030) is direct.

## Done

- 2026-07-12, Implementer A. **Sequencing note**: started this task
  before checking EXECUTION_PLAN.md Phase 4's hard rule ("4.1/4.2 land
  before any Phase-2 code touches `backend/`") — a gap in this task's own
  Dependency section, since TASK-0074 (the prerequisite) was filed after
  this one. Caught before committing; user's direction was to stop, land
  TASK-0074 properly first (commit `2ea0224`), then return here. This
  task's own commit lands strictly after that one.
- **`backend/analysis.py`**: extracted `_kirchhoff_eigh(coords, cutoff) ->
  (A, deg, w, U, nz, winv)` and `_normalized_dcc(U, winv) -> ndarray`.
  `gnm_context` and `_dcc` (the two named in this task) both now call
  `_kirchhoff_eigh`; `V_covariance` and `_abs_coupling` (found while
  reading the file — a **third and fourth** independent re-derivation of
  the exact same "Cov→normalize→zero-diagonal→abs-sum" block, not just
  the two the task named) now call `_normalized_dcc`. `gnm_context`'s own
  cheap `msf = ((U**2)*winv).sum(1)` shortcut is unchanged (not routed
  through a full-Cov path — would have been a needless O(N³) regression
  for no dedup benefit `_kirchhoff_eigh` doesn't already provide).
- **`__WORK_IN_PROGRESS__/src/allostery/potentials.py`**: extracted the
  ported analogue `_kirchhoff_eigh`/`_normalized_dcc` (same math,
  independent implementation, no cross-import — TASK-0018). `_gnm_msf`,
  `V_C`, and `V_M` (all three named in this task) now share it — `V_M`'s
  own copy previously went through `hamiltonians.H8_gnm` + a second
  independent `eigh` call; confirmed `H8_gnm(coords, cutoff)` is
  mathematically identical to `_kirchhoff_eigh`'s own `K` construction
  (same `contact_matrix(..., weight="binary")` + `laplacian(...,
  normalised=False)`) before routing it through, not assumed. `V_R` was
  deliberately left untouched — it already only calls `_gnm_msf` as a
  black box, so it benefits from the dedup automatically with zero edits
  to its own body, and its own output is verified unchanged below.
- `_gnm_msf` keeps its exact original `np.diag((U*winv)@U.T)` formula
  (did **not** switch to the cheaper `((U**2)*winv).sum(1)` shortcut
  backend's `gnm_context` already uses) — deliberately conservative,
  since introducing a different (if mathematically equivalent)
  floating-point summation order wasn't needed to satisfy this task's own
  scope and only adds unnecessary drift risk to `V_R`'s pinned test
  expectations.
- **Verified byte-identical, not just formula-argued**: a real (not
  ad hoc — scoped `git stash push -- <paths>`, captured, `git stash
  pop`) pre/post diff on live data for both sides —
  `backend/analysis.py::site_potentials`/`connectivity_change` on
  KRAS_G12C (4OBE apo, 6OIM holo, real RCSB fetch) and
  `potentials.py::V_R`/`V_C`/`V_M` on a synthetic 16-residue helix —
  identical before and after in both cases.
- Tests: `backend/test_analysis.py` (11 new — `_kirchhoff_eigh`/
  `_normalized_dcc` against an independently-rederived reference, `_dcc`
  against the old inline formula, `gnm_context`'s msf-shortcut identity,
  `_abs_coupling`'s pre-z-score relationship to `V_covariance`, plus a
  real KRAS_G12C regression pin for `site_potentials`/
  `connectivity_change`); `__WORK_IN_PROGRESS__/tests/test_potentials.py`
  (+6 — `_kirchhoff_eigh` against an independent reference *and* against
  `H8_gnm`+`eigh` directly, `_normalized_dcc`, `_gnm_msf`'s full-Cov
  identity).
- Widened `.ai/tools/pytest_local.py`'s `backend`/`all` presets to
  include `backend/test_analysis.py` (`backend/test_analysis_
  characterization.py` was already added by TASK-0074's own, earlier
  commit).
- Validation: `python3 .ai/tools/pytest_local.py all --json` — 488
  passed, 1 xpassed, 0 failed.
- No public function signature, return shape, or sign convention changed
  on either side — pure internal dedup, per this task's own Out Of Scope.
