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
- seam-test: not yet written — cannot be written for real until `viz.py`
  exists to be the other side of the boundary (same precedent as
  SEAM-0004/SEAM-0005 pointing at not-yet-landed consumers); when TASK-0014
  starts, its first step should assert against `pathways.py`'s actual
  return shapes documented above, not re-derive an assumed one
- status: OPEN
- provenance: found by [[TASK-0057]] while applying the newly-adopted Seam
  Protocol ([[TASK-0050]]) retroactively to [[TASK-0012]], which closed to
  DONE one commit before the seam gate existed and was never checked
  against it. `pathways.py`'s own docstring already flags this consumer
  ("for viz.py (TASK-0014) to render the full field alongside the traced
  path") but flagging in a docstring is not the same as a registered,
  owned seam per `SEAM_PROTOCOL.md`'s own distinction (docstring ≠
  contract).
