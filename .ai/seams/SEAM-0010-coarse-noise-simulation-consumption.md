# SEAM-0010 `coarse.py` output shape matches what the NISQ noise-model simulation consumes

- units: `coarse.coarse_grain` / `coarse.trotter_cost` (TASK-0013, Done) -> TASK-0068's noise-model simulation (not yet built)
- invariant: the noise simulation's qubit-to-node mapping and depth sweep
  assume the exact shapes `coarse.py` actually returns —
  `coarse_grain` -> `CoarseGrainResult(labels: (N,) int array, n_clusters:
  int, H_coarse: (n_clusters, n_clusters) symmetric float array, zero
  diagonal)`, and `trotter_cost` -> `TrotterCostResult(n_qubits, n_terms,
  trotter_steps, circuit_depth, two_qubit_gates, energy_scale)` — not a
  different convention (e.g. a directed/asymmetric coarse graph, a
  non-zero diagonal carrying a self-energy term, or `trotter_steps` read
  as a depth rather than a step count) that looks plausible but silently
  mismatches. In particular: `trotter_cost`'s `circuit_depth` (not
  `trotter_steps`) is what a depth sweep should vary over — a consumer
  that sweeps `trotter_steps` directly would silently skip the
  `layers_per_step` (max-degree) factor `coarse.py` already accounts for.
- owner: [[TASK-0068]]
- seam-test: not yet written — cannot be written for real until TASK-0068
  exists to be the other side of the boundary (same precedent as
  SEAM-0004/SEAM-0005/SEAM-0006 pointing at not-yet-landed consumers);
  when TASK-0068 starts, its first step should assert against
  `coarse.py`'s actual return shapes documented above, not re-derive an
  assumed one.
- status: OPEN
- provenance: opened by TASK-0013 at initial landing (not retroactively —
  TASK-0013 lands after the Seam Protocol's adoption, so the
  Definition-of-done addendum applies directly: coarse.py's output is
  explicitly built for a consumer named in its own Out Of Scope line
  ("that consumes this module's output but is a separate deliverable"),
  so the seam is opened, registered, and its consumer task (TASK-0068)
  filed in the same pass, rather than left as a docstring-only mention
  the way `pathways.py`/SEAM-0006 was before the retroactive TASK-0057
  sweep caught it.
