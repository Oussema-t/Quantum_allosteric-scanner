# TASK-0012 Implement `pathways.py` — current-flow / edge-propensity pathway extraction

## Context

- ID: TASK-0012
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/pathways.py`
- Status: Done
- Owner: Implementer
- Source: **no notebook precedent — net-new.** `.ai/tasks/PLANS/PLAN.md`
  feature backlog: "current-flow / edge-propensity pathway extraction
  (model-derived pathway, replaces the sequence-range 'green tube')".
  `ALGORITHM_REGISTER.md` §F rates ProteinLens (bond-to-bond current-flow
  propensity, 4) as the method to adopt the *readout* from, not the
  all-atom graph.
- Scope: `__WORK_IN_PROGRESS__/src/allostery/pathways.py` (currently a
  5-line stub) + `__WORK_IN_PROGRESS__/tests/test_pathways.py` (new)

## Intent Contract

- Outcome: replace whatever ad hoc "sequence-range" pathway visualization
  existed before (referenced only as "the green tube" in `PLAN.md`, not
  found elsewhere in this repo — likely a notebook/presentation artifact,
  not code) with a real model-derived pathway: which residues/edges
  actually carry the active-site→pocket signal, not just which residues sit
  between them by sequence number.
- In Scope:
  - `edge_propensity(H, source, ...)` — current-flow-style edge importance
    on the transport operator, adapting ProteinLens's bond-to-bond
    propensity readout (per `ALGORITHM_REGISTER.md`: "adopt the readout,
    not the all-atom graph" — this operates on the existing Cα contact
    graph, not a new all-atom one).
  - `extract_pathway(H, source, target, ...)` — the actual residue/edge
    sequence from active site to predicted pocket, for the 3D
    visualization layer (`viz.py`, TASK-0014) to render.
- Out Of Scope: the distance-bias quantile correction also mentioned in
  `PLAN.md`'s backlog under "From ProteinLens / external work" — that's a
  scoring correction, arguably belongs in `metrics.py` or `analysis.py`;
  flag as open question rather than absorbing it here without a decision.
- Constraints And Invariants: pathway extraction runs on the FROZEN-path
  operator output only when used for an actual prediction — using it purely
  as a characterization tool on known apo/holo pairs (DEV) is fine, per the
  same leakage discipline TASK-0004/0005 establish.
- Planned Validation: unit test on a small synthetic graph with one obvious
  bottleneck edge (e.g. two dense clusters joined by a single edge) —
  `edge_propensity` must rank that bridge edge highest.

## In Progress

None

## TODO

- [x] Implement `edge_propensity` (current-flow betweenness adaptation on
      the CTQW/transport operator).
- [x] Implement `extract_pathway`.
- [x] Unit test on the bottleneck-graph synthetic case.
- [ ] Decide (with TASK-0002 or standalone) where the distance-bias
      quantile correction belongs; don't fold it in here silently. **Still
      open** — deliberately not decided by this task (Out Of Scope above);
      left as a standing open question for whoever picks it up next, same
      pattern as TASK-0008's ceiling-search question that became TASK-0046.

## Dependency

- TASK-0008 (`analysis.py`) — reuses whatever operator/scoring conventions
  that module establishes so both modules read pathway/score output the
  same way.

## Open Questions

- Confirmed: no existing "green tube" code was found anywhere in this repo
  (`backend/`, `frontend/`, or `__WORK_IN_PROGRESS__`) — it's referenced
  only as prose in `PLAN.md`. Treat this as a from-scratch build, not a
  replacement of code that needs to be located first.
- Distance-bias quantile correction placement (`metrics.py` vs
  `analysis.py`) — still undecided, see TODO above.

## Done

- `edge_propensity(H, source)` and `extract_pathway(H, source, target,
  max_hops=None)` implemented in
  `__WORK_IN_PROGRESS__/src/allostery/pathways.py`. Both rebuild a
  resistor-network Laplacian from `H`'s off-diagonal magnitude
  (`abs(H_ij)`, robust to either sign convention `hamiltonians.py`
  documents) and solve node potentials via `np.linalg.pinv` — the standard
  current-flow-betweenness construction (Newman 2005). Confirmed by
  reading `potentials.py` that all five V_* terms are diagonal-only, so
  this conductance network is identical for any H a caller passes in
  (H2/H3/H_new/...), never distorted by the potential terms.
- `edge_propensity` uses a single linear solve (unit current at `source`,
  extracted uniformly over every other node) rather than one solve per
  candidate sink, matching its signature (no `target` argument) and
  keeping it O(N^3) once, not O(N^4).
- `extract_pathway` greedily walks the potential gradient from `source` to
  `target`, returning `reached_target=False` (not raising) when no route
  exists, and raises `ValueError` if `target` coincides with (or is inside
  a multi-index) `source`.
- Validated on `__WORK_IN_PROGRESS__/tests/test_pathways.py`: a two-clique
  synthetic graph joined by one bridge edge, confirming (a) the bridge
  scores highest in `edge_propensity`, including with a multi-index
  source, (b) `extract_pathway` traces straight through the bridge to a
  cross-cluster target, (c) an unreachable target reports
  `reached_target=False` instead of a partial/incorrect path, (d) the two
  `target`-coincides-with-`source` guard cases raise.
- Full local run: `python3 .ai/tools/pytest_local.py wip-all --json` →
  340 passed, 4 skipped (pre-existing network-gated skips, unrelated),
  0 failed.
