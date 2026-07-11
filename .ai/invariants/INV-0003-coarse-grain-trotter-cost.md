# INV-0003 `coarse_grain(H, method, n_target)` / `trotter_cost(H, t, error_budget)` -- `coarse.py`

## GAUGE

| Transformation | Test | Status |
|---|---|---|
| SE(3) (rotation+translation) on the coordinates feeding `H` | `coarse.py` never takes coordinates directly, only `H` -- invariant by construction whenever `H` itself is (same reasoning as INV-0002's first row for `pathways.py`). Not separately tested here; would be re-verified compositionally the same way INV-0002 was, if/when a coordinate-consuming caller of `coarse_grain` is added. | **GAUGE-VERIFIED** (by construction) |
| Residue relabeling (`H' = P H Pᵀ`), `coarse_grain`'s partition | `test_coarse.py::TestCoarseGrainPermutationInvariance::test_partition_invariant_under_relabeling` -- permutes a 20-node two-community synthetic graph, confirms the recovered partition (as a **set of node sets**, not raw cluster-id values, since ids are an arbitrary labeling artifact) is identical after mapping back through the permutation, for both `method="louvain"` and `method="spectral"`. Measured empirically before asserting (per the protocol's own rule of engagement), not assumed from the algorithm description. | **GAUGE-VERIFIED** |
| Residue relabeling, `trotter_cost`'s scalar outputs | `test_coarse.py::TestTrotterCostPermutationInvariance::test_scalars_invariant_under_relabeling` -- `n_terms`, `trotter_steps`, `circuit_depth`, `two_qubit_gates`, `energy_scale` are all pure functions of the (permutation-invariant) multiset of edge weights and the degree sequence, confirmed identical after permuting a 20-node graph. | **GAUGE-VERIFIED** |

## KNOB

- `method` (`"louvain"` vs `"spectral"`) -- an explicit modeling choice.
  Both recover the same obvious two-community structure on the seed
  fixture (`test_coarse.py::TestCoarseGrainCommunityRecovery`), but are
  not characterized as a spread on a harder/ambiguous partition case.
  **OPEN.**
- `n_target` (the node budget) -- by definition changes the answer
  (coarser graph, fewer clusters); not a spread-reportable knob in the
  usual sense since the NISQ study's qubit budget (`N <= ~12-16`,
  `ALGORITHM_REGISTER.md` SS H) fixes it externally rather than sweeping it
  for a go/no-go decision. Not characterized further here.
- `error_budget`/`t` in `trotter_cost` -- deliberately **SIGNAL**, not
  KNOB (see below); listed here only to note they are not also being
  double-counted as a KNOB spread.
- The commutator-norm approximation in `trotter_cost` (`||[H_i,H_j]|| ~=
  energy_scale^2` rather than an exact operator norm per pair) is a
  modeling simplification, not characterized against an exact commutator
  computation. **OPEN** -- flagged in the function's own docstring as an
  estimate, not silently precise.

## SIGNAL

- `error_budget` in `trotter_cost` -- must change the answer (monotonic:
  tighter budget -> more Trotter steps -> higher depth/gate-count).
  Asserted directly: `test_coarse.py::TestTrotterCost::
  test_tighter_error_budget_increases_cost` (this task's own Planned
  Validation, restated as a hard assert rather than an eyeballed number).
  **SIGNAL-VERIFIED.**
- `t` (propagation time) in `trotter_cost` -- must also increase cost
  (`t^2` scaling in the error bound). Asserted:
  `test_longer_time_increases_cost`. **SIGNAL-VERIFIED.**
- Null control for `coarse_grain` (a structureless graph with no real
  community structure -- e.g. a uniform random graph -- should not
  produce a confidently "obvious" partition the way the two-community
  fixture does) -- not yet run. **OPEN.**

## Status

Mixed, same shape as INV-0001/INV-0002 at their own seeding: both GAUGE
rows testable within this module's own scope (no dependency on the
not-yet-built NISQ noise-model consumer) are verified for real, and both
of `trotter_cost`'s intended-to-move knobs are confirmed as real SIGNAL,
not accidentally inert. The KNOB spread (method choice on an ambiguous
graph) and the SIGNAL null control for `coarse_grain` are registered
**OPEN** rather than silently assumed, per the protocol's own instruction
not to let an unclassified transformation pass as covered.

## Provenance

Seeded 2026-07-12 by TASK-0013 (`coarse.py`), applying the Invariance
Protocol ([[TASK-0051]]) at initial landing rather than retroactively
(TASK-0012/`pathways.py` landed one commit before the gate existed and
needed the retroactive TASK-0057 pass; TASK-0013 lands after, so this
module's invariants are seeded in the same commit as the code, per the
Definition-of-done addendum). GAUGE permutation tests were verified
empirically (numeric check run before the assertions were written) before
being asserted, matching `INVARIANCE_PROTOCOL.md`'s own rule of
engagement.
