# SEAM-0006 `pathways.py` output shape matches what `viz.py` renders

- units: `pathways.edge_propensity` / `pathways.extract_pathway` (TASK-0012, Done) -> `viz.py` (TASK-0014, not yet built)
- invariant: `viz.py`'s rendering of the current-flow field/path assumes the
  exact shapes `pathways.py` actually returns —
  `edge_propensity` -> `{(i, j): float}` for `i < j` only (undirected,
  half the (N,N) matrix, non-negative), and `extract_pathway` ->
  `{"nodes": [...], "edges": [(i, j), ...], "reached_target": bool,
  "propensity": {(i, j): float}}` — not a different convention (e.g.
  directed edges, a dense (N,N) array, or 1-indexed residues) that looks
  plausible but silently mismatches
- owner: [[TASK-0014]]
- seam-test: `tests/test_seam_0006_pathways_viz.py` —
  `TestSeam0006PathwaysVizConsumption` (3 tests): real
  `pathways.edge_propensity`/`extract_pathway` output (not a hand-built
  dict assuming the shape) fed directly into `viz.plot_pathway_overlay`,
  covering the reached and not-reached cases. `viz.py`'s own
  `_validate_edge_propensity`/`_validate_pathway` are the executable form
  of this seam's invariant (i < j, non-negative, the exact 4 `pathway`
  keys) — checked against `pathways.py`'s source directly while writing
  `viz.py`, not re-derived from memory.
- status: VERIFIED
- provenance: found by [[TASK-0057]] while applying the newly-adopted Seam
  Protocol ([[TASK-0050]]) retroactively to [[TASK-0012]], which closed to
  DONE one commit before the seam gate existed and was never checked
  against it. `pathways.py`'s own docstring already flags this consumer
  ("for viz.py (TASK-0014) to render the full field alongside the traced
  path") but flagging in a docstring is not the same as a registered,
  owned seam per `SEAM_PROTOCOL.md`'s own distinction (docstring ≠
  contract). Closed 2026-07-12 by [[TASK-0014]] (same task that owns it —
  the consumer landing and the seam closing are the same event here,
  unlike SEAM-0005 where the seam-test predates its still-missing
  consumer).
