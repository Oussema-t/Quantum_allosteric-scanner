# TASK-0013 Implement `coarse.py` — coarse-graining + Trotter/qubit cost

## Context

- ID: TASK-0013
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/coarse.py`
- Status: TODO
- Owner: Implementer
- Source: **no notebook precedent — net-new.** `.ai/tasks/PLANS/PLAN.md`
  feature backlog: "coarse-graining + QSW non-reciprocity demo +
  Trotter/qubit estimate"; `ALGORITHM_REGISTER.md` §H (Trotterized
  Hamiltonian simulation under noise — rating 5, "the actual scoreable NISQ
  result") and §D's non-reciprocal/chiral-phase walk (rating 3).
- Scope: `__WORK_IN_PROGRESS__/src/allostery/coarse.py` (currently a 5-line
  stub) + `__WORK_IN_PROGRESS__/tests/test_coarse.py` (new)

## Intent Contract

- Outcome: shrink a ~150-300 residue contact graph down to the N ≤ ~12-16
  node budget the NISQ noise study (`ALGORITHM_REGISTER.md` §H) needs,
  while preserving the transport-relevant structure — and report the
  Trotter-depth/qubit-count cost of simulating the result, which is the
  actual scoreable secondary objective per the challenge rubric mentioned
  in `PLAN-01.07.26.md` ("Feasibility 20" of the rubric).
- In Scope:
  - `coarse_grain(H, method="louvain"|"spectral", n_target)` — community
    detection or spectral clustering down to the target node count.
  - `trotter_cost(H, error_budget)` — estimated circuit depth / 2-qubit gate
    count for simulating `e^{-iHt}` at a given error tolerance, feeding
    directly into the NISQ noise study this coarse-grained graph is built
    for.
- Out Of Scope: the noise-model simulation itself (depolarizing/
  amplitude-damping under Trotterization) — that consumes this module's
  output but is a separate deliverable per `ALGORITHM_REGISTER.md` §H;
  track it as a follow-up task once this module exists rather than folding
  it in here.
- Constraints And Invariants: coarse-graining must be apo-computable
  (topology-only) — it cannot use holo information to decide the
  clustering, or every downstream NISQ result inherits a leakage problem
  nobody will think to check for.
- Planned Validation: unit test that `coarse_grain` on a graph with two
  obvious dense communities recovers them; unit test `trotter_cost`'s
  scaling direction (tighter error budget → higher reported cost) on a
  fixed small Hamiltonian.

## In Progress

None

## TODO

- [ ] Implement `coarse_grain` (Louvain via networkx/python-louvain, or
      spectral clustering — confirm which dependency is already available
      before adding a new one; see TASK-0011's same open question re:
      networkx).
- [ ] Implement `trotter_cost`.
- [ ] Unit tests.

## Dependency

- Existing `hamiltonians.py` (`[have]`) supplies the operators to
  coarse-grain; no blocking dependency on other stub modules.

## Open Questions

- Is a full NISQ noise-model simulation (the actual depolarizing/amplitude-
  damping study) in scope for *any* currently-planned task, or does it need
  its own TASK once this module exists? Recommend opening that as a
  follow-up once `coarse.py` lands, scoped explicitly to
  `ALGORITHM_REGISTER.md` §H's "Trotterized Hamiltonian simulation... report
  top-5 ranking degradation vs depth and error."

## Done

(not yet)
