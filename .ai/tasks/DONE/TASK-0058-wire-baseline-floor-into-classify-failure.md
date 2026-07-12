# TASK-0058 Wire baseline-floor comparison into `classify_failure` (closes SEAM-0005)

## Context

- ID: TASK-0058
- Title: Give `diagnostics.py::classify_failure` a `floor_scores` parameter and a
  beats-floor check, so "signal" means "beats the strongest trivial structural
  baseline," not merely "beats chance"
- Status: Done
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

- `floor_scores: np.ndarray | None = None` added to `classify_failure`'s
  signature (keyword-only, after the existing keyword params, matching
  this module's convention). Default `None` preserves byte-identical
  behavior — verified by an explicit regression test, not just by
  omission (`test_floor_scores_none_is_unchanged_from_pre_seam_0005_behavior`).
- New closed-set category `BEATS_CHANCE_NOT_FLOOR`, added to
  `FAILURE_CATEGORIES`. Checked after the existing chance check and
  before `NO_FAILURE_DETECTED`, per the Intent Contract's ordering —
  verified by `test_floor_check_only_applies_after_chance_check` (a
  chance-level score returns `NO_SIGNAL_IN_APO` regardless of a
  passed-in floor, floor check never reached).
  Comparison is `score_auc <= floor_auc` (a tie does not count as
  beating the floor).
- `test_seam_0005_baseline_floor.py`'s `xfail(strict=True)` removed; the
  test now passes for real, unchanged apart from the marker/docstring
  (per the task's own instruction, "no changes to the test itself").
- Two new direct unit tests added to `test_diagnostics.py`
  (`TestClassifyFailureFloor`): beats-chance-and-floor →
  `NO_FAILURE_DETECTED`; beats-chance-not-floor → `BEATS_CHANCE_NOT_FLOOR`
  — both with hand-verified AUCs (0.75 mediocre vs. 1.0 near-perfect),
  computed and checked before being hardcoded into the assertions, not
  guessed.
- `SEAM-0005` flipped to `VERIFIED`
  (`.ai/seams/SEAM-0005-verdict-signal-vs-baseline-floor.md`), per this
  task's own record and not auto-flipped from elsewhere.
- Full local run: `python3 .ai/tools/pytest_local.py wip-all --json` →
  398 passed, 0 failed (one pre-existing `xpass` elsewhere in the suite,
  unrelated to this task, not investigated here — out of scope).
- Not done, deliberately: `report.py::verdict_template`'s separate
  meaningful/marginal/noise-level classification (Out Of Scope above);
  no benchmark-orchestration code was added to actually call
  `baselines.py` and pass its output into `classify_failure` for a real
  target — this task only makes the function *capable* of the
  comparison, per its own Out Of Scope.
- **Staging/commit deferred** — held per the user's manual Stage-Commit-Queue
  coordination (this thread was 3rd in queue at claim time); code and
  tests are complete and locally green, not yet staged.
