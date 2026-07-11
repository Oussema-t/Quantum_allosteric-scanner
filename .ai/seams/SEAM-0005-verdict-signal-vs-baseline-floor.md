# SEAM-0005 classify_failure/verdict "signal" means beats-floor, not beats-chance

- units: `baselines` (floor definition) -> `analysis`/report `classify_failure`/verdict consumer
- invariant: "signal" in a reported verdict means the method beats the strongest trivial
  structural baseline (floor), not merely beats chance (AUC > 0.5) or beats one specific
  comparison method (H10)
- owner: [[TASK-0011]] (Done) for the floor; [[TASK-0058]] (new, TODO) for actually closing
  this seam
- seam-test: `__WORK_IN_PROGRESS__/tests/test_seam_0005_baseline_floor.py::test_beating_chance_but_not_the_surface_floor_is_not_no_failure_detected`
  — `xfail(strict=True)`, fails today with `TypeError` (`classify_failure` has no
  `floor_scores` parameter). Exists and executes the invariant per the Definition-of-done
  addendum; does not yet pass.
- status: OPEN
- provenance: seeded from `SEAM_PROTOCOL.md`'s own table at adoption ([[TASK-0050]],
  2026-07-11). Floor landed ([[TASK-0011]], 2026-07-11) — `baselines.py`'s
  `random_baseline`/`surface_baseline`/`degree_centrality`/`betweenness_centrality` are real.
  Per this record's own prior instruction ("file one at that point rather than assuming this
  record's existence is enough"), [[TASK-0058]] was filed the same session to wire
  floor-comparison into `classify_failure`. **Still do not auto-flip to VERIFIED** — the
  seam-test must go from `xfail` to passing first.
  **Corroborated by [[TASK-0053]]'s sweep (2026-07-11), from the `diagnostics.py` side**
  (prior evidence was from `baselines.py`'s side): `classify_failure`'s actual current
  signature is `(scores, labels, H=None, bfactors=None, *, auc_chance_tol=0.05,
  n_large=800, diag_dominance_threshold=3.0)` — no `floor_scores` parameter exists,
  confirming the `TypeError` claim directly rather than inferring it.
