# TASK-0012 Implement `pathways.py` — current-flow / edge-propensity pathway extraction

## Context

- ID: TASK-0012
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/pathways.py`
- Status: TODO
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

- [ ] Implement `edge_propensity` (current-flow betweenness adaptation on
      the CTQW/transport operator).
- [ ] Implement `extract_pathway`.
- [ ] Unit test on the bottleneck-graph synthetic case.
- [ ] Decide (with TASK-0002 or standalone) where the distance-bias
      quantile correction belongs; don't fold it in here silently.

## Dependency

- TASK-0008 (`analysis.py`) — reuses whatever operator/scoring conventions
  that module establishes so both modules read pathway/score output the
  same way.

## Open Questions

- Confirmed: no existing "green tube" code was found anywhere in this repo
  (`backend/`, `frontend/`, or `__WORK_IN_PROGRESS__`) — it's referenced
  only as prose in `PLAN.md`. Treat this as a from-scratch build, not a
  replacement of code that needs to be located first.

## Done

(not yet)
