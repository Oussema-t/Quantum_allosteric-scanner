# SEAM-0011 `baselines.py` output was never proven to compose with `diagnostics.classify_failure`'s `floor_scores`

- units: `baselines.py` (`degree_centrality`, `surface_baseline`, `betweenness_centrality`, `random_baseline`) -> `diagnostics.classify_failure`'s `floor_scores` parameter (TASK-0058, closes SEAM-0005)
- invariant: a real `baselines.py` function's output is usable, end-to-end, as `classify_failure`'s `floor_scores` — not just a type-compatible stand-in array
- owner: [[TASK-0056]] (this review — closed directly, not reassigned; small enough to fix in-scope, matching TASK-0047's precedent of adding tests during a gap-bridging review rather than filing a follow-up for something this contained)
- seam-test: `test_diagnostics.py::TestClassifyFailureRealBaselineFloor` (3 tests: fixture sanity — the floor is genuinely imperfect, not a strawman AUC=1.0 — plus a beats-the-real-floor case and a does-not-beat-it case) — all 3 passing
- status: VERIFIED
- provenance: found by [[TASK-0056]]'s Phase 4 review (2026-07-12) while checking
  cross-module consumption per its own Intent Contract ("do `diagnostics.py`/
  `report.py` consume `pathways.py`/`baselines.py` output in a way that assumes
  a specific shape neither side's own unit tests would catch"). Confirmed by
  reading `test_diagnostics.py::TestClassifyFailureFloor` (TASK-0058's own
  SEAM-0005-closing tests): every case there hand-builds `floor_scores` as a
  synthetic array (`NEAR_PERFECT`, `MEDIOCRE`) — none calls a real `baselines.py`
  function. The type contract is trivial ((N,) float arrays, both sides), so
  this was never a shape-*mismatch* risk — but the intended *composition*
  (baselines.py's real output flowing into diagnostics.py) had literally never
  been exercised. Closed directly in this same review: added
  `TestClassifyFailureRealBaselineFloor` to `test_diagnostics.py`, using
  `baselines.degree_centrality` on a coordinate fixture deliberately built with
  a confound (a non-pocket residue degree-identical to the true pocket) so the
  floor is genuinely imperfect rather than an unbeatable AUC=1.0 strawman. All
  3 new tests pass; full `test_diagnostics.py` + `test_baselines.py` +
  `test_pathways.py` suite (57 tests) confirmed clean in the same pass.
