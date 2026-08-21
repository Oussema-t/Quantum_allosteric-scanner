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
- seam-test: `test_noise.py::TestCoarseGrainSeamConsumption` (4 tests,
  2026-07-14) — asserts `coarse_grain`'s real `H_coarse` is symmetric/
  zero-diagonal and shaped `(n_clusters, n_clusters)`; the walk circuit's
  qubit count matches `n_clusters`, not the original node count; a seed
  *residue* maps to its qubit via `cg.labels[residue]`, not its own
  original index (the confusion this seam explicitly warns a naive
  consumer could make); and `circuit_depth >= trotter_steps` always
  (never conflated).
- status: VERIFIED, with one documented, deliberate deviation from this
  seam's own recommendation — **not silently glossed over**:
  `noise.py`'s depth sweep varies `trotter_steps` (Trotter repetitions),
  not `trotter_cost`'s `circuit_depth` estimate, because
  `build_xy_walk_circuit` emits gates edge-by-edge with no parallel-layer
  scheduling of its own (the `max_degree + 1` graph-coloring
  `circuit_depth` assumes is never actually implemented in the circuit
  builder) — so `circuit_depth` as `trotter_cost` computes it does not
  correspond to this circuit's real depth without that scheduling being
  added, which is out of TASK-0068's time budget this session. Both
  `trotter_steps` and `circuit_depth` are reported side by side in every
  real run's output (`results/tasks/0068/<target>/noise_sweep.json`) so a
  reader sees the real gap, not a silently-mislabeled axis. Flagged as a
  natural follow-up (parallel-layer gate scheduling in the circuit
  builder), not filed as its own task here.
- provenance: opened by TASK-0013 at initial landing (not retroactively —
  TASK-0013 lands after the Seam Protocol's adoption, so the
  Definition-of-done addendum applies directly: coarse.py's output is
  explicitly built for a consumer named in its own Out Of Scope line
  ("that consumes this module's output but is a separate deliverable"),
  so the seam is opened, registered, and its consumer task (TASK-0068)
  filed in the same pass, rather than left as a docstring-only mention
  the way `pathways.py`/SEAM-0006 was before the retroactive TASK-0057
  sweep caught it.
