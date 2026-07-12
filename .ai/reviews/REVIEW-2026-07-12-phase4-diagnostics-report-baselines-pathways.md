# Phase 4 Review (TASK-0009 `diagnostics.py` / TASK-0010 `report.py` / TASK-0011 `baselines.py` / TASK-0012 `pathways.py`)

## Reviewer

Architect/Planner thread, standing in as the Code Reviewer overlay for this
pass (per `TASK-0056`'s Owner field), 2026-07-12. Same evidence-first method
as the Foundation review — read each module + its tests in full, run the
tests for real, cross-check against the modules' own Intent Contracts and
the two seam records this cluster was already named in.

## Linked Tasks

- `.ai/tasks/DONE/TASK-0009-diagnostics-py.md`
- `.ai/tasks/DONE/TASK-0010-report-py.md`
- `.ai/tasks/DONE/TASK-0011-baselines-py.md`
- `.ai/tasks/DONE/TASK-0012-pathways-py.md`

TASK-0008 (`analysis.py`) explicitly out of scope, per TASK-0056's own
Context note (already has an unusually thorough Done section).

## Scope

- `__WORK_IN_PROGRESS__/src/allostery/{diagnostics,report,baselines,pathways}.py`
  + their test files.
- Cross-checks: `SEAM-0004` (report provenance), `SEAM-0005` (verdict floor),
  `SEAM-0008` (analysis→report assembly), plus a general cross-module
  consumption sweep per `SEAM_PROTOCOL.md`'s own smell list.

## Test Execution

- `pytest test_diagnostics.py test_report.py test_baselines.py
  test_pathways.py`: **75 passed** (first pass, before the finding below).
- While investigating cross-module consumption, added 3 new tests to
  `test_diagnostics.py` (`TestClassifyFailureRealBaselineFloor`, closes
  `SEAM-0011` — see Findings). Re-ran: **78 passed** (75 + 3 new).
- A second full-suite run caught `test_report.py::TestVerdictTemplate::
  test_frozen_provenance_has_no_banner` failing — **not attributable to
  this review.** `git diff` confirmed `report.py`/`protocol.py` were
  mid-edit under a concurrently-claimed `TASK-0088` ("Implementer A",
  claimed 2026-07-12 13:45) actively closing `SEAM-0004` in the shared
  working tree while this review was running. Re-ran the three modules
  this review actually touches/certifies (`test_diagnostics.py`,
  `test_baselines.py`, `test_pathways.py`) in isolation: **57 passed**,
  clean. `report.py`'s test state is `TASK-0088`'s to certify, not this
  review's — noted here for the record, not fixed or waited on.

## Findings

### P2 — none found in this cluster's own code.

The four modules read as genuinely careful ports/net-new builds: correct
closed-set failure taxonomy in `diagnostics.py` (verified each category is
reachable and ordered correctly, including the newer `BEATS_CHANCE_NOT_FLOOR`
tier), `report.py`'s scope boundary is deliberate and consistently documented
(not an oversight — see SEAM-0008 below), `baselines.py`'s external-tool
wrappers correctly never raise and are tested via both the graceful-degrade
path and a synthetic parse-format test, `pathways.py`'s current-flow
construction is a correct, cited (Newman 2005) implementation with its own
`TestInvariance` class already present.

### P3 — cross-module composition gaps (the actual point of this review)

- **SEAM-0011 (new, closed in this pass).** `classify_failure`'s
  `floor_scores` parameter (TASK-0058, closes SEAM-0005) was never actually
  exercised with real `baselines.py` output — every existing test hand-built
  a synthetic floor array. Not a shape-mismatch risk (both sides are plain
  `(N,)` float arrays), but the intended *composition* had never been proven.
  Closed directly: 3 new tests using a real `baselines.degree_centrality`
  call on a fixture with a deliberate confound residue (degree-identical to
  the true pocket, so the floor is genuinely imperfect, not an unbeatable
  strawman). See `.ai/seams/SEAM-0011-baselines-diagnostics-floor-composition.md`.
- **SEAM-0008 (existing, re-scoped in this pass, still OPEN).**
  `report.verdict_template`'s expected flat schema (`AUC_apo_Hnew_default`
  etc.) is produced nowhere in real code — only `test_report.py`'s hand-built
  fixture. Per this review's own investigation: this is **not** a defect in
  `report.py` — its module docstring already correctly and deliberately
  states it "does not compute the underlying numbers (that's `analysis.py`'s
  job)." The real owner is `TASK-0079` (end-to-end challenge run), whose own
  Intent Contract already names "orchestrating the already-Done pipeline
  stages... into one run" as in scope — that orchestration *is* the missing
  assembly step. Reassigned the seam's owner from `TASK-0056` to `TASK-0079`
  and cross-linked directly into that task's file (currently claimed and
  in-progress, so the note lands where it's needed). Status stays OPEN — the
  invariant isn't satisfied yet, it's correctly re-scoped, not resolved.
- **SEAM-0004 / SEAM-0005**: both already handled by other tasks before this
  review started (`TASK-0055` empirically confirmed SEAM-0004's gap 2026-07-12;
  `TASK-0058` closed SEAM-0005 to VERIFIED the same day). Confirmed both
  records are accurate and did not re-run the underlying verification —
  matches this task's own "don't re-litigate without new evidence" scope. As
  of this review's *test execution*, SEAM-0004 was additionally observed
  being actively fixed live by `TASK-0088` (see Test Execution above) — a
  third, independent thread's work, not this review's to claim.
- **`pathways.py` → `viz.py` (SEAM-0006)**: already registered and owned by
  `TASK-0014`, found by `TASK-0057`'s earlier retroactive sweep. Confirmed
  still accurate, not re-litigated.

## Notable good practice observed

- `diagnostics.py::classify_failure`'s category ordering is deliberately
  documented and tested at each boundary (`test_floor_check_only_applies_after_chance_check`
  proves the floor check can't fire before the chance check) — exactly the
  kind of ordering invariant that's easy to silently break in a future edit
  without a docstring this explicit.
- `baselines.py::betweenness_centrality`'s docstring explicitly calls out
  that it's safe on disconnected graphs (the exact synthetic case
  `diagnostics.py`'s own tests use) — a real cross-module compatibility
  note, not a generic docstring.
- `pathways.py` already ships its own `TestInvariance` class, ahead of the
  Invariance Protocol being applied to this cluster by a dedicated pass —
  worth confirming (separately, not this review) whether it satisfies
  `INVARIANCE_PROTOCOL.md`'s GAUGE/KNOB/SIGNAL classification table
  requirement or just informally checks invariance.

## Open Questions

- Should `pathways.py`'s existing `TestInvariance` class be formally
  registered in `.ai/invariants/` (per `INVARIANCE_PROTOCOL.md`'s registry
  requirement — "no transformation table → not reportable"), or does its
  current informal coverage already satisfy the protocol's intent? Not
  investigated in this pass — flagging rather than guessing.

## Status

No P0/P1 (blocking/structural) issues found in this cluster's own code.
One real cross-module composition gap found and closed in-pass (SEAM-0011).
One existing seam (SEAM-0008) correctly re-scoped to its real owner rather
than left pointing at this now-closing review. Phase 4 cluster
(TASK-0009/0010/0011/0012) is sound; no re-review required before Phase 5
work on top of it.
