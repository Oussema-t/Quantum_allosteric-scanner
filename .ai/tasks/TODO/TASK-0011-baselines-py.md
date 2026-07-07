# TASK-0011 Implement `baselines.py` — classical + external baselines

## Context

- ID: TASK-0011
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/baselines.py`
- Status: TODO
- Owner: Implementer
- Source: **no notebook precedent — net-new.** `.ai/tasks/PLANS/PLAN.md`
  Phase 2 ("must beat the right baselines... random residues, non-functional
  surface pockets, AND degree/betweenness centrality") and Phase 4
  ("external predictors as a baseline column AND a diagnostic").
  `ALGORITHM_REGISTER.md` §F rates the external tools: fpocket (4),
  PocketMiner (4), ProteinLens (4), AlloPred/PASSer/DeepAllo (3).
- Scope: `__WORK_IN_PROGRESS__/src/allostery/baselines.py` (currently a
  5-line stub) + `__WORK_IN_PROGRESS__/tests/test_baselines.py` (new)

## Intent Contract

- Outcome: a ceiling number only means something if it beats these
  baselines — per `PLAN.md`, "a ceiling that node degree also reaches is
  structure, not your method." This module is the gate that makes Phase 2's
  ceiling claim legitimate.
- In Scope:
  - `random_baseline(n, k)`, `surface_baseline(coords, k)` (non-functional
    surface-pocket score — the challenge's own comparison bar per
    `PLAN.md`).
  - `degree_centrality`, `betweenness_centrality` baselines on the contact
    graph.
  - thin client wrappers for external tools rated ≥3 in
    `ALGORITHM_REGISTER.md`: fpocket (apo-computable cavity score — also
    the openness objective the holo-direction module, TASK-0015, needs),
    PocketMiner, ProteinLens, and optionally AlloPred/PASSer/DeepAllo.
- Out Of Scope: fpocket's use as the holo-direction module's optimization
  objective (TASK-0015 consumes this module's fpocket wrapper, doesn't
  reimplement it).
- Constraints And Invariants: external-server wrappers must degrade
  gracefully (skip + warn, not crash) when offline/rate-limited — this
  module will be exercised in CI environments without guaranteed network
  access. Mirror `rcsb_extract.py`'s existing convention in `backend/`
  ("errors never raise").
- Planned Validation: unit tests for the classical baselines (random,
  degree, betweenness) on synthetic graphs with known centrality structure;
  external-tool wrappers tested only for graceful-failure behavior
  (mock the network call), not for correctness of the external service.

## In Progress

None

## TODO

- [ ] Implement `random_baseline`, `surface_baseline`.
- [ ] Implement `degree_centrality`, `betweenness_centrality` (networkx is
      already a plausible dependency given `hamiltonians.py`'s use of BA
      graphs in tests — confirm it's already a project dependency before
      adding a new one).
- [ ] Implement fpocket wrapper (local binary or API — check availability
      before committing to one integration path).
- [ ] Implement PocketMiner / ProteinLens wrappers (server-based; confirm
      terms of use for programmatic access before building the client).
- [ ] Unit tests for classical baselines; graceful-failure tests for
      external wrappers.

## Dependency

- TASK-0004 (`labels.py`) — baselines are scored against the same pocket
  labels the main method is scored against.

## Open Questions

- fpocket: local binary dependency (adds a system-level install
  requirement) vs a hosted API — which fits this project's "no GPU,
  embarrassingly parallel, CPU-hours only" compute profile better
  (per `PLAN.md`'s compute note)? Recommend local binary if available in
  the target CI/dev environment, to avoid a network dependency for a
  baseline that should be cheap and always available.
- Which of AlloPred/PASSer/DeepAllo (all rated 3, "lower priority than the
  three above" per `ALGORITHM_REGISTER.md`) are worth building clients for
  at all vs. just fpocket + PocketMiner + ProteinLens (all rated 4)?
  Recommend deferring the rating-3 tools unless the submission specifically
  needs the extra breadth.

## Done

(not yet)
