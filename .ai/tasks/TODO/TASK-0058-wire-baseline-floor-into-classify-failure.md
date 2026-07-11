# TASK-0058 Wire baseline-floor comparison into `classify_failure` (closes SEAM-0005)

## Context

- ID: TASK-0058
- Title: Give `diagnostics.py::classify_failure` a `floor_scores` parameter and a
  beats-floor check, so "signal" means "beats the strongest trivial structural
  baseline," not merely "beats chance"
- Status: TODO
- Owner: Implementer
- Source: [[SEAM-0005]] (`.ai/seams/SEAM-0005-verdict-signal-vs-baseline-floor.md`),
  filed per that record's own instruction once TASK-0011 (`baselines.py`) landed.
  A seam-test already exists and is `xfail(strict=True)`:
  `__WORK_IN_PROGRESS__/tests/test_seam_0005_baseline_floor.py::test_beating_chance_but_not_the_surface_floor_is_not_no_failure_detected`
  — it fails today with `TypeError` because `classify_failure` has no
  `floor_scores` parameter at all.
- Scope: `__WORK_IN_PROGRESS__/src/allostery/diagnostics.py::classify_failure`
  only. Does not touch `report.py::verdict_template` (item 1's "meaningful/
  marginal/noise-level" classification is a separate surface, compares against
  H10 specifically, not the SEAM-0005 floor — out of scope unless a future seam
  record says otherwise) or `baselines.py` itself (already correct).

## Intent Contract

- Outcome: `classify_failure` accepts an optional `floor_scores` array (the
  strongest available baseline for this target — caller's choice which
  baseline, this function doesn't pick one). When beats-chance succeeds but
  the method does not beat the floor's AUC, return a new closed-set category
  rather than `NO_FAILURE_DETECTED` — matching PLAN.md's "a ceiling that node
  degree also reaches is structure, not your method" bar.
- In Scope:
  - add `floor_scores: np.ndarray | None = None` to `classify_failure`'s
    signature (keyword-only, after the existing `H`/`bfactors` positional-or-
    keyword params, matching this module's existing parameter ordering
    convention).
  - a new closed-set category, e.g. `BEATS_CHANCE_NOT_FLOOR` (name is this
    task's call, not fixed by the seam record) added to `FAILURE_CATEGORIES`.
  - priority: floor check happens *after* the existing chance check (a result
    that doesn't even beat chance is `NO_SIGNAL_IN_APO` regardless of the
    floor; the floor check only matters once chance is already cleared) and
    *before* returning `NO_FAILURE_DETECTED`.
  - when `floor_scores is None` (the default), behavior is byte-identical to
    today — this is what keeps every existing `classify_failure` call site
    and this module's own `test_diagnostics.py` suite passing unchanged.
  - flip `__WORK_IN_PROGRESS__/tests/test_seam_0005_baseline_floor.py`'s
    `@pytest.mark.xfail` off (or remove the decorator) once the test passes
    for real — do not leave a passing test marked `xfail` (that reads as
    still-broken to the next reader).
  - update `.ai/seams/SEAM-0005-verdict-signal-vs-baseline-floor.md`'s
    `status` to `VERIFIED` once the seam-test passes and this lands.
- Out Of Scope:
  - deciding which baseline(s) count as "the floor" for a real benchmark run
    (random vs. surface vs. degree vs. betweenness vs. max-of-all) — that's a
    scoring-protocol/orchestration decision for whatever future task wires
    `analysis.py`/a benchmark runner to actually call `baselines.py` and pass
    its output into `classify_failure`. This task only makes `classify_failure`
    *capable* of the comparison when given a floor array.
  - `report.py::verdict_template` — separate surface, not this seam per
    Scope above.
- Constraints And Invariants:
  - must not change `classify_failure`'s return value for any existing call
    (no `floor_scores` argument) — this is the load-bearing backward-
    compatibility guarantee `test_diagnostics.py`'s existing 15 tests rely on.
  - `floor_scores`, if given, must be the same length as `scores`/`labels` —
    validate or let a natural shape-mismatch error surface; don't silently
    truncate/broadcast.
- Planned Validation: `test_seam_0005_baseline_floor.py`'s existing test
  passes once `xfail` is removed; full suite via
  `python3 .ai/tools/pytest_local.py all --json` still green; add at least
  one direct unit test in `test_diagnostics.py` for the new category
  (beats-chance, beats-floor -> NOT the new category; beats-chance,
  loses-to-floor -> the new category; `floor_scores=None` -> unchanged
  behavior, already covered by the existing 15 tests but worth one explicit
  regression assertion).

## In Progress

None

## Dependency

- [[TASK-0011]] (Done) — `baselines.py`, the floor this task compares against.
- [[TASK-0009]] (Done) — `diagnostics.py`, the module this task extends.
- [[SEAM-0005]] — this task exists to close it; do not mark that record
  `VERIFIED` from any task other than this one without re-reading its own
  "do not auto-flip" warnings.

## Open Questions

- Should `floor_scores` accept a dict of multiple baselines (take the max
  AUC across all of them as "the floor") rather than one pre-selected array?
  Recommend keeping it a single array for this task — the caller (a future
  benchmark-orchestration task) is better positioned to decide "strongest
  baseline" than this function; a dict-of-baselines API can be added later
  without breaking this one (`floor_scores` stays the single-array fast
  path, an additional `floor_candidates` param could be added additively).

## Done

(not yet)
