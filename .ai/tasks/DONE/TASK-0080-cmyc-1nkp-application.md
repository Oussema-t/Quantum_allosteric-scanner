# TASK-0080 c-Myc / 1NKP application (no-holo-ground-truth target)

## Context

- ID: TASK-0080
- Title: Handle the c-Myc (1NKP) required minimum-set target, which has
  no holo ground truth — score on consensus + theoretical docking
  viability instead of AUC/ceiling.
- Status: Done
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 5, item 5.7 —
  "Required minimum-set target with **no holo ground truth** — scored on
  consensus + theoretical docking viability. Needs its own handling: no
  AUC, no ceiling; report prediction + confidence honestly."

## Intent Contract

- Outcome: c-Myc/1NKP runs through the pipeline with an explicit
  no-ground-truth code path — it does not attempt to compute AUC or a
  ceiling (both require a labeled holo comparison that doesn't exist for
  this target), and instead reports a prediction with an honest
  consensus-based confidence statement and theoretical docking
  viability.
- In Scope: whatever branch/flag the pipeline needs to recognize "this
  target has no holo structure" and route to the alternative reporting
  path rather than crashing or silently reporting a meaningless AUC.
- Out Of Scope: sourcing new docking-viability tooling from scratch if
  none exists — check what's available (the plan says "theoretical
  docking viability," implying some existing method/heuristic should be
  used, not a new docking engine built for this task).
- Acceptance Scenarios:
  - Given 1NKP run through the pipeline, when it reaches the scoring
    stage, then it does not attempt AUC/ceiling computation and instead
    emits a prediction + confidence + docking-viability statement.
  - Given the same target, then the report clearly states *why* no
    AUC/ceiling is reported (no holo ground truth) rather than silently
    omitting the numbers.
- Constraints And Invariants: "report honestly" — this must not present a
  degraded or missing metric as if it were a normal score; the absence of
  ground truth is itself information to surface, per the plan's framing
  ("a per-target honest NO is a publishable result, not a failure to
  hide" — from TASK-0082's rationale, same spirit applies here).
- Planned Validation: manual review of 1NKP's report output confirming it
  reads as an honest, confidence-qualified prediction, not a masked gap.

## Dependency

- Uses the same orchestration as TASK-0079 (end-to-end challenge run) but
  needs its own branch — coordinate on the pipeline's entry point.
- Feeds TASK-0082 (competence map synthesis) — c-Myc's row in that table
  needs this task's no-ground-truth handling to be meaningful.

## Open Questions

- **Resolved**: `baselines.fpocket_baseline` already exists (TASK-0011),
  real and tested (not a stub) — checked directly rather than assumed.
  It wraps the external `fpocket` cavity-detection binary
  (`ALGORITHM_REGISTER.md` Sec.F, rated 4/4), apo-computable, no ground
  truth needed. The binary itself is **not installed in this
  environment** (confirmed: `shutil.which("fpocket")` returns `None`) —
  `fpocket_baseline` already degrades gracefully to `{"error": ...}`
  rather than raising, exactly the behavior this task needed; used
  as-is, no new docking tooling built (per Out Of Scope).

## Done

**No holo-detection branch added to `run_challenge.py`**
(`run_target_no_ground_truth`, dispatched from `run_target` when
`target_config.get("holo_pdb") is None`, checked *before* any
holo-dependent call — previously this crashed inside `clean_from_config
(role="holo")`'s own `ValueError` for any null-`holo_pdb` target,
caught only by the generic `except Exception` handler and written to
`error.txt` as an undifferentiated failure, not a recognized target
class). Purely additive: every existing (holo-having) target's code
path is byte-identical to before this change.

**Consensus ranking** (`analysis.consensus_ranking`, new function):
adapts `HOLO_DIRECTION_MODULE.md` Step 5's "consensus across
perturbations" idea (*"is the predicted pocket the same region across
[an ensemble]? ... Computable with no holo at all"*) from an ensemble
of admissible apo deformations (`TASK-0015`, not built) to an ensemble
of 4 already-built, independently-designed operators
(`H_new_default`/`H10_disorder_suppressed`/`H2_combinatorial_laplacian`/
`H14_anm_pinv_trace`) run on the *same* fixed apo topology — real,
available, and in the same holo-free spirit, not a reinvention of that
task's own scope. Reports per-residue cross-operator top-k agreement
(`consensus_count`) plus mean occupancy as a tie-breaker.

**Seed resolution**: `labels.functional_indices(apo.coords, [], ...)` —
an empty `ligand_groups` list (this target has no holo/bound-ligand
structure fetched at all) trivially fails `func_ligand=["DNA"]`'s tier-1
contact match, falling through to the function's own already-documented,
already-tested tier-2 fallback (top-5 contact-degree residues). Verified
live: `provenance == 'top-degree fallback'` on the real run below — an
existing, honest degradation this task reuses, not new machinery.

**Report** (`report.no_ground_truth_report`, new function): explicitly
states *why* no AUC/ceiling/floor is computed (this target's own
`config/targets.yaml` status: `holo_pdb: null`,
`allosteric_pocket_exists: false`), never silently renders a blank or
N/A metric in their place. `verdict_template` is not reused with missing
keys — a deliberately distinct report shape, per this task's own
Constraint ("must not present a degraded or missing metric as if it
were a normal score").

**Real run** (`MYC_MAX`/1NKP, `python3 scripts/run_challenge.py --target
MYC_MAX --output-dir results_task0080`, live RCSB fetch, 45.7s total,
full per-stage timing logged): apo N=171 (Myc+Max heterodimer, chains
A/B per `targets.yaml`'s own resolved chain-pairing choice). Seed: 5
residues via `'top-degree fallback'`, as predicted. Consensus (35.2s,
the eigendecomposition-dominated stage): top hit residue 943, 3/4
operators agree, mean occupancy 0.0634; overall confidence classified
`"moderate"` (best agreement 3/4, not unanimous). Docking: `fpocket`
unavailable in this environment, reported as such, not masked.
Deliverables verified by direct load, not assumed from the writer code:
`connectivity_matrix.npz` is `(171, 171)`, symmetric, zero diagonal;
`hit_list.json` has 5 real resnums (943, 246, 925, 243, 226) with scores
and `consensus_count`; `report.txt` renders the full honest-NO narrative
above; `verdict.json` carries `"no_ground_truth": true` and the reason,
so `TASK-0082`'s competence-map synthesis can detect this target's class
programmatically rather than string-matching the report text.

**Tests**: `TestConsensusRanking` (`test_analysis.py`, 5 cases) +
`TestNoGroundTruthReport` (`test_report.py`, 6 cases), synthetic/offline.
`.venv/bin/python3 -m pytest -q tests/test_analysis.py tests/test_report.py
-k "not real_target and not kras"` — 73 passed, 0 failed (full-file run,
confirms no regression in either module from these additions).

**Acceptance Scenarios**: both met on the real run above — no AUC/ceiling
attempted or rendered; the report states explicitly, in its own first
paragraph, that this is because no holo ground truth exists for this
target, not a silent omission.

**Addendum, found 2026-07-15 while running TASK-0081's full-suite check**:
the dispatch condition (`if target_config.get("holo_pdb") is None:`)
matches both a real, explicit `holo_pdb: null` (MYC_MAX) *and* a config
dict that simply omits the `holo_pdb` key entirely — the pre-existing
`test_run_challenge.py::mocked_target` fixture (TASK-0079.004, predates
this task) does the latter, since it never needed the key before this
branch existed, and started silently routing through the no-ground-truth
path instead of the normal one (7 test failures). Every real
`config/targets.yaml` entry always sets `holo_pdb` explicitly (even
MYC_MAX sets it to `null`, never omits it), so this is not a live bug
against real data — but it is a real fixture/schema-shape gap the new
branch exposed. Fixed in the fixture (`_TARGET_CONFIG` now sets
`"holo_pdb": "SYNTH_HOLO"`, matching real schema shape), not by loosening
the dispatch check, since a config that is missing the key entirely
arguably *should* be treated the same as one that sets it to `null` (both
mean "no holo declared") — the fixture was the thing out of sync with the
real schema, not the new code. Full suite: 581 passed after the fix.
