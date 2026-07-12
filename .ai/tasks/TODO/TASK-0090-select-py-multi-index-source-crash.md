# TASK-0090 `select.py::ballistic_exponent` crashes on a multi-index `source`

## Context

- ID: TASK-0090
- Title: `select.unsupervised_score`/`ballistic_exponent`/
  `_hop_distances_from_source` raise `ValueError: The truth value of an
  array with more than one element is ambiguous` when a candidate's
  `"source"` is a multi-residue index array — despite `unsupervised_score`'s
  own docstring precedent ("focusing"/"source_specificity" both support a
  multi-index seed, mirroring `propagators.py`'s "a multi-index source is
  a uniform mass split" convention) implying the whole module does.
- Status: TODO
- Owner: Implementer
- Source: found while implementing TASK-0079.004 (the end-to-end
  orchestrator). `protocol.run_frozen_verdict`'s `candidates_builder`
  naturally wants to offer `select_frozen_config` the same seed
  (`labels.Labels.active_site`, typically several residues — every
  `func_ligand` contact) that `analysis.benchmark`/`ablation`/
  `quantum_vs_classical` already accept fine as a multi-index array
  (confirmed working via `test_analysis.py`'s real KRAS_G12C test,
  `apo_src_idx`). `select.py`'s own scoring path cannot, so `.004` had to
  route around it (single representative seed index for the
  *selection* step only) rather than pass the real multi-residue seed —
  see `run_challenge.py`'s own docstring for that decision.
- Reproduction (empirically confirmed 2026-07-12, not hypothetical):
  ```python
  from allostery.select import ballistic_exponent
  from allostery.hamiltonians import laplacian
  import numpy as np
  H = laplacian(path_adjacency(12))
  ballistic_exponent(H, np.array([2, 3]))   # returns fine, single-seed BFS silently uses only [source] as one opaque list element
  from allostery.select import unsupervised_score
  unsupervised_score([{"H": H, "source": np.array([2, 3]), "t": 5.0}])
  # ValueError: The truth value of an array with more than one element is ambiguous
  ```
  Root cause: `_hop_distances_from_source(H, source)` does
  `dist[source] = 0; frontier = [source]` — for an array `source` this
  wraps the *whole array* as a single list element instead of seeding a
  BFS frontier with each of its residues, and later code
  (`adjacency[node]` / `if dist[nb] == -1`) breaks on that shape. Note
  `ballistic_exponent` alone (called directly, not through
  `unsupervised_score`) does not itself raise — it silently returns a
  number computed from the wrong/degenerate frontier; the crash above is
  `unsupervised_score`'s own `_zscore`/downstream path making that hidden
  wrong-shape state finally explicit. **Both are bugs** — the crash is
  just the visible one.

## Intent Contract

- Outcome: `ballistic_exponent`/`_hop_distances_from_source` correctly
  support a multi-index `source` — BFS frontier seeded from *every* index
  in `source`, `dist[source] = 0` for all of them, matching
  `propagators.py`'s and `analysis.py`'s already-established multi-index
  convention this module's own docstring claims to mirror.
- In Scope: `select.py`'s `_hop_distances_from_source`/`ballistic_exponent`
  only. A regression test with a real multi-index `source` (e.g. two
  residues on a path/star graph, asserting a real, non-degenerate
  `alpha` exponent, not just "does not crash") plus a
  `unsupervised_score`/`select_frozen_config` end-to-end multi-index
  candidate test.
- Out Of Scope: `focusing`/`source_specificity` (already correct, use
  `time_averaged_ctqw` which handles multi-index natively) — do not
  touch code that isn't broken.
- Constraints And Invariants: scalar `source` behavior must stay
  byte-identical (existing tests, e.g. `test_select.py`, must keep
  passing unmodified) — this is a widening fix, not a rewrite.
- Planned Validation: `test_select.py`'s existing suite unchanged +ex new
  multi-index tests; re-run `TASK-0079.004`'s `run_challenge.py` with the
  real multi-residue `source` (removing the single-index workaround this
  task's own fix makes unnecessary) once this lands, to confirm the
  workaround can be safely deleted, not just that the new tests pass in
  isolation.

## Dependency

- [[TASK-0007]] (`select.py`, Done) — the module with the bug.
- [[TASK-0079.004]] — found this while implementing it; that script's own
  single-seed workaround becomes deletable once this is fixed.

## Open Questions

- None yet.

## Done

(not yet)
