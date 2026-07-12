# TASK-0074 Characterization tests for `backend/analysis.py`

## Context

- ID: TASK-0074
- Title: Golden-output tests pinning the *current* live public surface of
  `backend/analysis.py` (`gnm_context`, `site_potentials`,
  `quantum_seed_readiness`, `connectivity_change`) before any convergence
  work (TASK-0066/0072) touches it.
- Status: Done
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

- 2026-07-12, Implementer A. Found mid-TASK-0066 (this task's own hard
  rule wasn't checked before starting that one — a gap in TASK-0066's own
  Dependency section, since this task was filed after it) after TASK-0066's
  refactor was already written and verified byte-identical via an ad hoc
  git-stash diff. User's explicit direction: stop, do not commit TASK-0066,
  claim and land this task properly first.
- Added `backend/test_analysis_characterization.py`: 8 golden-output tests
  pinning `gnm_context`, `site_potentials`, `quantum_seed_readiness`, and
  `connectivity_change`'s **current** live output on KRAS_G12C (apo 4OBE,
  chain A per `backend/systems.py::SYSTEMS`) — real network fetch, not
  mocked, values captured 2026-07-12. `morph_frames`/`seed_readiness_shift`/
  `site_potential_shift` (the "if time allows" extras) were not added —
  none of them call any of the Kirchhoff/DCC math TASK-0066 touches
  (`gnm_context`/`_dcc`/`V_covariance`/`_abs_coupling`), so they carry no
  incremental drift risk from that specific follow-up work; the plan's own
  text only requires the four blocking functions.
- **Verified this genuinely lands "before" TASK-0066**, not just nominally:
  scoped `git stash push -- backend/analysis.py
  __WORK_IN_PROGRESS__/src/allostery/potentials.py` (leaving this task's
  new test file untouched) and re-ran the suite against the *unmodified*
  HEAD `analysis.py` — 8/8 passed identically, confirming the pinned
  values are the pre-refactor baseline, then `git stash pop` restored
  TASK-0066's changes.
- Widened the whitelisted `.ai/tools/pytest_local.py`'s `backend`/`all`
  presets to include the new file (previously hardcoded to
  `backend/test_geometry.py` only, so `pytest_local.py backend` silently
  wouldn't have picked up any new `backend/test_*.py` file — a small,
  mechanical, obviously-safe tooling gap, fixed directly rather than
  filed, mirroring TASK-0026.005's own precedent for this exact tool).
  Docstring's "the two real test surfaces" line updated from
  `backend/test_geometry.py` (singular) to `backend/test_*.py` (the real,
  now-plural, pattern).
- Validation: `python3 .ai/tools/pytest_local.py backend --json` — 11
  passed (3 `test_geometry.py` + 8 this task's own), 0 failed.
- This task's own file is committed **separately from, and before,**
  TASK-0066's commit — the actual git history reflects the hard rule, not
  just this Done section's narrative.
