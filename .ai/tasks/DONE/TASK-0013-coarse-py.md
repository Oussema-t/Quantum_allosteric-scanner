# TASK-0013 Implement `coarse.py` — coarse-graining + Trotter/qubit cost

## Context

- ID: TASK-0013
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/coarse.py`
- Status: Done
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

## TODO (resolved 2026-07-12, Implementer A)

- [x] Implement `coarse_grain` (Louvain via networkx/python-louvain, or
      spectral clustering — confirm which dependency is already available
      before adding a new one; see TASK-0011's same open question re:
      networkx).
  - No new dependency needed: `networkx>=3.x` (already `[have]`) ships
    `algorithms.community.louvain_communities` built in, and `sklearn`
    (already used by `metrics.py::auc`) provides `SpectralClustering`.
  - `method="spectral"` honors `n_target` exactly (`n_clusters` param);
    `method="louvain"` has no direct node-count knob, so when Louvain's
    natural partition has more communities than `n_target`, the two
    most-strongly-coupled clusters are greedily merged (by total
    inter-cluster edge weight) until the budget is met — documented as
    best-effort for Louvain, exact for spectral, not silently uniform
    across both methods.
  - Graph weight extraction (`_graph_weights`) uses `abs(H_ij)`,
    `i != j`, the same convention `pathways.py::_conductance_laplacian`
    already established (TASK-0012) — ported locally rather than
    cross-importing that private helper (same "port, don't couple"
    convention TASK-0005 used for `backend/geometry.py`).
- [x] Implement `trotter_cost`.
  - First-order Trotter-Suzuki error-bound estimate (`r ~=
    ceil(t^2 * n_terms * energy_scale^2 / (2*error_budget))`), with
    `circuit_depth = r * (max_degree + 1)` (Vizing's-theorem parallel-
    scheduling bound). Documented explicitly as an *estimate* (the
    commutator-norm term is approximated by `energy_scale^2`, not
    computed exactly) rather than presented as a precise bound — see
    INV-0003's KNOB section.
- [x] Unit tests.
  - `tests/test_coarse.py`: 16 tests, all passing. Full suite
    (`python3 .ai/tools/pytest_local.py wip-all`): 362 passed, 1 xfailed
    (pre-existing, SEAM-0005/TASK-0058), 1 xpassed (pre-existing), no
    regressions.
- [x] **New, per TASK-0051 (Invariance Protocol, landed after this task
      was originally filed):** classify `coarse_grain`/`trotter_cost`'s
      transformations before reporting either as usable.
  - `.ai/invariants/INV-0003-coarse-grain-trotter-cost.md` — permutation
    (residue-relabeling) invariance of `coarse_grain`'s partition (as a
    *set of node sets*, not raw cluster-id values — ids are an arbitrary
    labeling artifact) and of `trotter_cost`'s scalar outputs, both
    **GAUGE-VERIFIED** empirically before being asserted (per the
    protocol's own rule of engagement — checked with a scratch script
    first, not assumed from the algorithm description). SE(3) invariance
    is by construction (neither function takes coordinates). Both of
    `trotter_cost`'s intended-to-move knobs (`error_budget`, `t`) are
    confirmed real **SIGNAL**, not accidentally inert, restating this
    task's own Planned Validation as a hard assert. `method` choice on an
    ambiguous (non-obvious) partition, and a structureless-graph null
    control for `coarse_grain`, are left **OPEN** rather than silently
    assumed covered.
- [x] **New, per TASK-0050 (Seam Protocol, landed after this task was
      originally filed):** `coarse_grain`'s Out Of Scope line names a real
      future consumer ("the noise-model simulation itself... consumes
      this module's output but is a separate deliverable") — that is a
      seam under the Definition-of-done addendum (output consumed by
      another unit), and a task cannot move to `DONE` while opening an
      unregistered one.
  - Filed [[TASK-0068]] (NISQ noise-model simulation) via
    `claim.py reserve-next`, resolving this task's own Open Question
    below rather than leaving it as a dangling recommendation, and
    registered `.ai/seams/SEAM-0010-coarse-noise-simulation-consumption.md`
    with TASK-0068 as owner. Seam-test not yet written — cannot be
    written for real until TASK-0068 exists to be the other side of the
    boundary (same precedent as SEAM-0004/SEAM-0005/SEAM-0006 pointing at
    not-yet-landed consumers).

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
  - **Resolved:** filed as [[TASK-0068]] (see TODO section above), which
    also owns the new SEAM-0010 this task's output opens.
- **New:** `coarse_grain`'s `method="louvain"` merge-to-target step is a
  real algorithmic choice (greedy strongest-inter-cluster-weight merge)
  not benchmarked against alternatives (e.g. always merging the two
  smallest clusters, or re-running Louvain at a different resolution
  parameter until the count matches). Works correctly on this task's
  Planned Validation fixture and a harder 24-node random-weight case
  (tested), but not characterized as a KNOB spread — flagged `OPEN` in
  INV-0003 rather than silently assumed equivalent to other merge
  strategies.

## Done

- `__WORK_IN_PROGRESS__/src/allostery/coarse.py` implemented:
  `coarse_grain` (Louvain with node-budget merging, or exact spectral
  clustering) and `trotter_cost` (first-order Trotter-Suzuki depth/gate-
  count estimate), both apo-computable by construction (take only `H`,
  never coordinates or holo data).
- `__WORK_IN_PROGRESS__/tests/test_coarse.py`: 16 tests, all passing.
  Full suite: 362 passed, 1 pre-existing xfail, 1 pre-existing xpass, no
  regressions.
- `.ai/invariants/INV-0003-coarse-grain-trotter-cost.md` seeded at initial
  landing (not retroactively) per TASK-0051.
- [[TASK-0068]] filed (NISQ noise-model simulation, this task's own
  recommended follow-up) and `.ai/seams/SEAM-0010-coarse-noise-simulation-
  consumption.md` registered with TASK-0068 as owner, per TASK-0050 — this
  task's Definition-of-done addendum obligation, satisfied rather than
  left as an unregistered seam.
- Both Planned Validation items met: `coarse_grain` recovers two obvious
  dense communities on the seed fixture (both methods); `trotter_cost`'s
  scaling direction (tighter error budget, longer time -> higher reported
  cost) is asserted directly, not eyeballed.
