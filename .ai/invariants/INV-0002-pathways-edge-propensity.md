# INV-0002 `edge_propensity(H, source)` / `extract_pathway(H, source, target)` -- `pathways.py`

## GAUGE

| Transformation | Test | Status |
|---|---|---|
| SE(3) (rotation+translation) on the coordinates feeding `H` | `pathways.py` never takes coordinates directly, only `H` — invariant by construction whenever `H` itself is (true of `hamiltonians.py`'s distance-based contact graphs). Verified compositionally, not just asserted: `test_pathways.py::TestInvariance::test_se3_invariance_composed_with_hamiltonians` rotates+translates coords, rebuilds `H` via `hamiltonians.H2_combinatorial_laplacian`, confirms `edge_propensity` output identical to `atol=1e-9` (measured: exact, `max diff == 0.0`). | **GAUGE-VERIFIED** |
| Residue relabeling (`H' = P H Pᵀ`) | `test_pathways.py::TestInvariance::test_permutation_invariance_edge_propensity` — permutes an 8-node synthetic graph, confirms every edge's propensity value matches its relabeled counterpart to `atol=1e-9`. | **GAUGE-VERIFIED** |
| Residue relabeling, `extract_pathway`'s traced node/edge sequence | `test_permutation_invariance_extract_pathway` confirms the traced path relabels consistently **for the tested graph/permutation pair, which contains no exact tie in the greedy walk**. The walk's tie-break (lowest node index) is **not** permutation-invariant in general when two candidate next-hops tie exactly in current magnitude — that specific case is untested. | **PARTIAL** — common case verified, tie-break case **OPEN** |

## KNOB

- Which `H` variant is passed in (`H2_combinatorial_laplacian` vs
  `build_H_new` vs any other `hamiltoniansPy` operator) is an explicit
  modeling choice — different operators can and will rank edges
  differently (potential terms are diagonal-only so the conductance graph
  itself is unaffected, but the *node potentials* `phi` solved from `L`
  are unaffected by potentials too, since `_conductance_laplacian` derives
  `L` purely from `H`'s off-diagonal — so in fact the choice of Hamiltonian
  variant only matters insofar as different variants imply different
  *contact* structure, e.g. `H1`'s binary cutoff vs `H6`'s exponential
  decay weighting). Not yet characterized as a spread. **OPEN.**
- `cutoff` (inherited from whichever `hamiltonians.py` builder produced
  `H`) — not characterized. **OPEN.**

## SIGNAL

- Null control on a structureless graph (e.g. a uniform complete graph
  with no real bottleneck) — not yet run. **OPEN.** The existing
  `TestEdgePropensity`/`TestExtractPathway` bottleneck tests demonstrate
  the metric responds to real structure but are not a formal null control.

## Status

Mixed, same shape as INV-0001 at its own seeding: the two GAUGE rows that
were testable within this module's own scope (no dependency on `viz.py` or
any other not-yet-built consumer) are verified for real; the tie-break
edge case, KNOB grid, and SIGNAL null control are registered `OPEN`
rather than silently assumed.

## Provenance

Seeded 2026-07-11 by [[TASK-0057]], applying the Invariance Protocol
([[TASK-0051]]) retroactively to [[TASK-0012]] (`pathways.py`), which
closed to DONE one commit before the invariance gate existed. Both GAUGE
tests were verified empirically (numeric check run before the assertions
were written, not derived from proof alone) — per `INVARIANCE_PROTOCOL.md`'s
own rule of engagement, "multi-turn agreement is not verification."
