# TASK-0074 Characterization tests for `backend/analysis.py`

## Context

- ID: TASK-0074
- Title: Golden-output tests pinning the *current* live public surface of
  `backend/analysis.py` (`gnm_context`, `site_potentials`,
  `quantum_seed_readiness`, `connectivity_change`) before any convergence
  work (TASK-0066/0072) touches it.
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 4, item 4.2 —
  "Safety net for TASK-0066." Phase 4's hard rule: **4.1 (TASK-0021) and
  4.2 (this task) land BEFORE any Phase-2 code touches `backend/`** —
  "Convergence into an untested live service with no golden values is how
  a deployed app silently changes its numbers."

## Intent Contract

- Outcome: a test file exercising `backend/analysis.py`'s public functions
  on a fixed benchmark protein (e.g. KRAS_G12C), asserting the *current*
  numeric outputs as golden values — not testing correctness against a
  ground truth (this is characterization, not validation), just pinning
  what the live service returns today.
- In Scope: `gnm_context`, `site_potentials`, `quantum_seed_readiness`,
  `connectivity_change` at minimum (the four the plan names); extend to
  other public functions in `analysis.py` (`V_rigidity`, `V_covariance`,
  `morph_frames`, `seed_readiness_shift`, etc.) if time allows — the plan
  only requires the four blocking ones.
- Out Of Scope: testing correctness of the physics itself — that's a
  research-validation question (TASK-0067/labels.py benchmark territory),
  not this task's job. This task only prevents *silent* numeric drift.
- Acceptance Scenarios:
  - Given KRAS_G12C (or another fixed benchmark target) run through
    `backend/analysis.py`'s public functions today, when the test suite
    runs, then it asserts the current output values and passes.
  - Given a hypothetical future edit to `gnm_context`'s cutoff constant
    (e.g. if TASK-0066/0072's convergence work changes it), when the test
    suite runs, then it fails loudly, forcing an explicit acknowledgment
    of the changed output rather than a silent shift.
- Constraints And Invariants: **must land before TASK-0066/TASK-0072
  touch `backend/`** per the plan's Phase 4 hard rule — check this task's
  status before starting either of those.
- Planned Validation: the tests themselves are the validation artifact;
  run via whatever `backend/` test runner already exists
  (`backend/test_geometry.py` is the current precedent — 3 tests, this
  task should follow the same pattern/conventions).

## Dependency

- Blocks TASK-0066 and TASK-0072 from touching `backend/` (Phase 4's hard
  rule) — should land first or in parallel, not after.
- Related to TASK-0021 (backend API test baseline, Phase 4.1) — same
  phase, different layer (API smoke floor vs. function-level
  characterization); do together, not identical scope.

## Open Questions

- None — scope and target functions are named explicitly in the plan.

## Done

(not yet)
