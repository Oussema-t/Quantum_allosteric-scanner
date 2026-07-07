# TASK-0007 Implement `select.py` — unsupervised operator selector

## Context

- ID: TASK-0007
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/select.py`
- Status: Done
- Owner: Implementer
- Source: **no notebook precedent — net-new.** `.ai/tasks/PLANS/PLAN.md`
  Phase 3 ("`select.unsupervised_score` (focusing, source-specificity,
  ballistic exponent) — label-free config selection, enforced by
  `protocol.FROZEN`")
- Scope: `__WORK_IN_PROGRESS__/src/allostery/select.py` (currently a 5-line
  stub, despite `PLAN.md`'s repo-structure table marking it `[have]` —
  that annotation is stale, see Open Questions) +
  `__WORK_IN_PROGRESS__/tests/test_select.py` (new)

## Intent Contract

- Outcome: a way to pick which Hamiltonian/operator variant and which
  propagation parameters to use on a FROZEN (held-out) target **without
  ever looking at its labels** — using only properties observable from the
  apo structure and the walk's own dynamics.
- In Scope:
  - `focusing(P)` — how concentrated the time-averaged walk distribution is
    (relates to `metrics.ipr`, already implemented — reuse, don't
    reimplement).
  - `source_specificity(...)` — does the walk from the seed distinguish
    itself from walks seeded elsewhere (label-free proxy for "is this
    operator informative").
  - `ballistic_exponent(...)` — spread-vs-time scaling exponent, a
    label-free coherence/transport-regime diagnostic.
  - `unsupervised_score(candidates)` — combine the above into one ranking
    over candidate operator/parameter configs, usable inside
    `protocol.leave_one_protein_out`'s FROZEN loop.
- Out Of Scope: the DEV/FROZEN enforcement itself (TASK-0006).
- Constraints And Invariants:
  - every function here must be computable from the apo structure and its
    own walk output alone — if a metric needs the holo pocket to compute,
    it belongs in `analysis.py` (TASK-0008), not here. This is the
    line that keeps FROZEN-path selection legitimate.
- Planned Validation: unit tests using `metrics.ipr`/`spectral_gap` outputs
  on synthetic graphs with known localization/delocalization behavior, to
  confirm `focusing`/`ballistic_exponent` move in the expected direction.

## In Progress

None — all TODO items complete, see Done section.

## TODO

- [x] Implement `focusing`, `source_specificity`, `ballistic_exponent` as
      label-free functions over `propagators.ctqw`/`time_averaged_ctqw`
      output. `focusing` reuses `metrics.ipr` directly (per the Intent
      Contract). `source_specificity` and `ballistic_exponent` are net-new
      formulas (no notebook/existing-code precedent existed to port) — see
      Done section for the exact design and empirical validation.
- [x] Implement `unsupervised_score` combining them (z-scored sum, same
      combination convention as `potentials.V_R`).
- [x] Unit tests on synthetic graphs (path vs star vs complete). Note: they
      do *not* give a uniform "path always wins" reading — see Done section
      for the real, three-way tradeoff this surfaced and why that's
      expected, not a bug.
- [x] `.ai/tasks/PLANS/PLAN.md`'s repo-structure table corrected directly in
      this task's commit (one-line tag fix: `select.py` from `NEW` to
      `[have]`) rather than filing a new task for it — TASK-0002 (which
      last touched that table) is itself already `Done`, so reopening it
      for a single annotation would have been more process than the fix
      warranted.

## Dependency

- TASK-0006 (`protocol.py`) — this module's output is only meaningful
  inside the FROZEN context that module defines.
- Existing `metrics.py`, `propagators.py` (both `[have]`) supply the raw
  walk/graph statistics this module scores.

## Open Questions

- `PLAN.md`'s repo-structure table lists this file as `[have]` alongside
  `protocol.py`, but both are 5-line stubs on disk. Was `[have]` written
  aspirationally (i.e., "will exist by the time Phase 3 starts") or is it
  simply wrong? Recommend treating every `[have]` tag in that document as
  unverified until spot-checked — TASK-0002 should do a full pass on this.
  **Resolved by TASK-0002 (2026-07-04):** simply wrong, not aspirational —
  full spot-check done, `PLAN.md`'s repo-structure table corrected (`select.py`
  and `protocol.py` now tagged `NEW`; `clean.py` and `potentials.py`, which had
  the opposite drift — tagged `NEW` while fully implemented — corrected to
  `[have]`). See `PLAN.md`'s repo-structure section for the note.

## Done

- All 4 functions implemented in `__WORK_IN_PROGRESS__/src/allostery/select.py`:
  `focusing`, `source_specificity`, `ballistic_exponent`,
  `unsupervised_score`, plus two private helpers (`_hellinger_distance`,
  `_hop_distances_from_source`).
- `tests/test_select.py`: 14 tests, all passing. Full WIP suite (`python3
  .ai/tools/pytest_local.py wip-all`): 252 passed, 1 xpassed (the
  pre-existing `test_superpose.py` order flake noted in TASK-0004, still
  unrelated to this task).
- Design notes (net-new, no notebook/existing-code precedent to port):
  - `focusing(P)` = `metrics.ipr(P)` directly. Valid reuse even though
    `ipr`'s docstring is written for an L2-normalised eigenvector: the
    formula (`Sum P_i^4 / (Sum P_i^2)^2`) is scale-invariant, so it works
    identically on an L1-normalised probability vector.
  - `_hop_distances_from_source` recovers hop distance straight from `H`'s
    off-diagonal sparsity pattern (BFS), with no separate coords/adjacency
    input needed: `hamiltonians.build_H_new`'s diagonal potentials (V_B,
    V_T, V_R, V_C, V_M) never touch off-diagonal entries, so any H built by
    this codebase's convention has the underlying contact graph's
    connectivity sitting directly in its off-diagonal nonzero pattern.
    Keeps `ballistic_exponent` computable from `H` and a seed alone, per
    the Intent Contract's FROZEN-legitimacy constraint.
  - `source_specificity` samples (default `n_alt=20`, fixed-seed `rng`,
    same convention as `metrics.block_bootstrap_ci`) rather than exhausts
    all N-1 alternative seeds — each alternative costs a full
    `time_averaged_ctqw` run, which would be expensive on a real
    few-hundred-residue Hamiltonian even though it's free on this task's
    small synthetic test graphs.
  - `ballistic_exponent` fits `spread(t) ~ t^alpha` via log-log linear
    regression of the walk's RMS graph-distance from the seed. Nodes
    unreachable from the seed (disconnected graph) are excluded from the
    spread sum, not treated as infinitely far.
- **Empirical validation (synthetic path/star/complete graphs, N=10,
  2026-07-07)**, checked before writing test assertions rather than
  guessed:
  - `focusing`: localized P -> 1.0, uniform P -> 1/N, exactly as expected.
  - `source_specificity`: path endpoint (0.127) > path midpoint (0.109) —
    an endpoint is a structurally distinguished position on a path. Both
    star (0.756) and complete (0.764) score far higher than path — CTQW on
    a highly symmetric graph stays persistently peaked at its own seed
    (very high `focusing`, 0.989 for both), and that persistent self-peak
    is exactly what a raw per-node Hellinger comparison against a
    *different* seed's (also self-peaked, but peaked *elsewhere*) vector
    picks up as "specific."
  - `ballistic_exponent`: path endpoint 0.643, path midpoint 0.309, star
    hub -0.115, complete -0.115 (star and complete came out numerically
    identical over this metric — plausible given both saturate to their
    full reachable spread almost immediately). Path clearly higher
    (genuine ballistic-like spreading) than star/complete (saturate
    immediately, near-zero-or-negative log-log slope over the sampled
    window).
  - **Real finding, not a bug — three-way tradeoff:** star/complete score
    high on `focusing` + `source_specificity` but low on
    `ballistic_exponent`; path is the reverse. `unsupervised_score`'s equal-
    weight z-scored sum therefore ranked star/complete *above* path
    (scores ~0.70-0.72 vs. -1.41) despite path being the more
    "interesting"/heterogeneous topology — because 2 of the 3 signals
    favor the symmetric graphs for this specific comparison. This is a
    coherent consequence of the equal-weight combination on a genuinely
    multi-dimensional tradeoff, not a defect: a real biological
    Hamiltonian isn't a pure star or pure complete graph, so this
    particular tension is expected to matter far less on realistic
    same-target operator comparisons (different `lambda` weightings of the
    same `H_new`, not different graph topologies). Documented here rather
    than silently shipped, and `TestUnsupervisedScore` in
    `tests/test_select.py` deliberately tests combination *mechanics*
    (shape, zero-mean, identical-input tie, differentiation) instead of
    asserting a "which topology wins" ordering, since that ordering isn't
    well-posed given the tradeoff above.
  - Flag for whoever picks up TASK-0006/`protocol.py`'s FROZEN loop: if
    `unsupervised_score` under-performs in practice, the equal-weight
    combination (vs. a weighted one, or reporting the three components
    separately for a human/downstream call) is the first thing to revisit
    — this task did not have real per-target candidate data to tune
    against.
- `PLAN.md`'s repo-structure table: `select.py`'s row corrected from `NEW`
  to `[have]` in this commit (see TODO).
- TASK-0006 (`protocol.py`) landed concurrently (Implementer A) during this
  task, which unblocked the exact trigger condition TASK-0008's own Open
  Questions had named ("surface as a follow-up TASK once TASK-0006/0007
  exist"): notebook §8's ceiling coordinate-descent search still has no
  home. Filed as **TASK-0046** (not TASK-0045 — that ID collided with a
  concurrent thread claiming it independently for something else; renamed
  before either landed on disk, per user instruction).
