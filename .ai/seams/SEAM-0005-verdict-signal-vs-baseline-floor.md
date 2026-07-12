# SEAM-0005 classify_failure/verdict "signal" means beats-floor, not beats-chance

- units: `baselines` (floor definition) -> `analysis`/report `classify_failure`/verdict consumer
- invariant: "signal" in a reported verdict means the method beats the strongest trivial
  structural baseline (floor), not merely beats chance (AUC > 0.5) or beats one specific
  comparison method (H10)
- owner: [[TASK-0011]] (Done) for the floor; [[TASK-0058]] (Done) for actually closing
  this seam
- seam-test: `__WORK_IN_PROGRESS__/tests/test_seam_0005_baseline_floor.py::test_beating_chance_but_not_the_surface_floor_is_not_no_failure_detected`
  — passes for real now (`xfail` removed, not left in place over a passing test).
  `classify_failure` accepts `floor_scores: np.ndarray | None = None` and returns the new
  `BEATS_CHANCE_NOT_FLOOR` category when the method clears chance but not the floor's AUC.
- status: VERIFIED
- provenance: seeded from `SEAM_PROTOCOL.md`'s own table at adoption ([[TASK-0050]],
  2026-07-11). Floor landed ([[TASK-0011]], 2026-07-11) — `baselines.py`'s
  `random_baseline`/`surface_baseline`/`degree_centrality`/`betweenness_centrality` are real.
  Per this record's own prior instruction ("file one at that point rather than assuming this
  record's existence is enough"), [[TASK-0058]] was filed the same session to wire
  floor-comparison into `classify_failure`.
  **Corroborated by [[TASK-0053]]'s sweep (2026-07-11), from the `diagnostics.py` side**
  (prior evidence was from `baselines.py`'s side): confirmed the pre-fix signature had no
  `floor_scores` parameter, directly rather than inferring it.
  **Closed 2026-07-12 by [[TASK-0058]]**: `floor_scores` is keyword-only, checked after the
  existing chance check and before `NO_FAILURE_DETECTED` (a result that doesn't beat chance
  is `NO_SIGNAL_IN_APO` regardless of the floor — verified by a dedicated test,
  `test_floor_check_only_applies_after_chance_check`). `floor_scores=None` (the default) is
  byte-identical to pre-TASK-0058 behavior — verified by an explicit regression test, not
  just by omission. Full local run:
  `python3 .ai/tools/pytest_local.py wip-all --json` → 398 passed, 0 failed (one pre-existing,
  unrelated `xpass` elsewhere in the suite, not touched by this task).
