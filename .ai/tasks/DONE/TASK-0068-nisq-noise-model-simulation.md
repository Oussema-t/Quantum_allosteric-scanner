# TASK-0068 NISQ noise-model simulation on `coarse.py`'s output

## Context

- ID: TASK-0068
- Title: Depolarizing + amplitude-damping Trotterized simulation on
  `coarse.py`'s coarse-grained graph, reporting top-5 ranking degradation
  vs. circuit depth and error rate
- Status: Done
- Owner: Implementer
- Source: `ALGORITHM_REGISTER.md` §H ("Trotterized Hamiltonian simulation
  under noise — rating 5, the actual scoreable NISQ result"); flagged as
  a follow-up by TASK-0013's own Open Question ("Is a full NISQ
  noise-model simulation in scope for any currently-planned task, or does
  it need its own TASK once this module exists?"), filed now that
  `coarse.py` (TASK-0013) has landed and needs a real consumer to close
  the seam it opens (see SEAM-0010).
- Scope: a new module or function (not yet decided — see Open Questions)
  that consumes `coarse.CoarseGrainResult`/`TrotterCostResult` and runs
  the actual noisy-circuit simulation `coarse.py` deliberately left out
  of scope.

## Intent Contract

- Outcome: the noise-resilience NISQ demo `HOLO_DIRECTION_MODULE.md`
  names as the project's actual scoreable hardware story — "is the
  ENAQT/QSW variant *more* noise-robust than coherent CTQW" — run for
  real on a coarse-grained (`N <= ~12-16` qubit) graph, under a
  depolarizing + amplitude-damping model with realistic 2-qubit error
  rates, reporting top-5 ranking degradation vs. circuit depth and error
  rate.
- In Scope:
  - consume `coarse.coarse_grain(...)`'s `H_coarse` directly — do not
    re-derive a coarse graph independently.
  - use `coarse.trotter_cost(...)`'s depth/gate-count estimates to choose
    the depth sweep range, rather than picking one ad hoc.
  - apply a depolarizing + amplitude-damping noise channel per gate
    (Qiskit/Braket/Classiq — provider choice deferred to Toolsmith, per
    `PLAN.md`'s "Braket/Classiq only for a small real-circuit demo").
  - report top-5 ranking degradation vs. depth and error rate, and
    specifically whether ENAQT/dephasing-assisted transport
    (`propagators.haken_strobl`, TASK-0008) is *more* noise-robust than
    coherent CTQW on the same coarse-grained graph under this noise
    model — the key result `HOLO_DIRECTION_MODULE.md` calls out.
- Out Of Scope: building a new coarse-graining method (that's
  `coarse.py`, done); anything above the `N <= ~12-16` qubit budget this
  module exists to fit under.
- Constraints And Invariants:
  - closes SEAM-0010 (`coarse.py` -> this task) — the seam-test there
    must be un-xfailed once this task's real consumer code exists and
    exercises `coarse_grain`'s actual output shape, not a synthetic
    stand-in.
  - per this task's own Invariance Protocol obligation: classify every
    transformation (noise-model seed, qubit-to-node mapping / relabeling,
    provider backend choice) as GAUGE/KNOB/SIGNAL before any degradation
    number is reported — do not skip straight to a headline "X% more
    robust" claim without that table (see `.ai/reference/
    INVARIANCE_PROTOCOL.md`).
- Planned Validation: not yet detailed — to be written when this task is
  picked up (deliberately left light here since the provider/library
  choice, deferred to Open Questions below, shapes what's testable).

## In Progress

None

## TODO

- [ ] Decide simulation provider (Qiskit Aer noise model vs. Braket
      local simulator vs. Classiq) — Toolsmith capability-contract
      question, not an Implementer call to make alone.
- [ ] Wire `coarse.trotter_cost`'s depth estimate into the depth sweep
      range.
- [ ] Implement the noisy Trotterized simulation + top-5 degradation
      metric.
- [ ] CTQW vs. Haken-Strobl (ENAQT) noise-robustness comparison — the
      headline question this task exists to answer.
- [ ] GAUGE/KNOB/SIGNAL transformation table (Invariance Protocol) before
      reporting any degradation number.
- [ ] Un-xfail SEAM-0010's seam-test once real consumer code exists.

## Dependency

- TASK-0013 (`coarse.py`, Done) — `coarse_grain`/`trotter_cost` are this
  task's direct inputs.
- TASK-0008 (`analysis.py`, Done) — `dephasing_sweep`/`haken_strobl` for
  the ENAQT-vs-CTQW comparison.

## Open Questions

- Module home: a new `noise.py`, or a function inside `coarse.py` itself
  (`coarse.simulate_noisy`)? `coarse.py`'s own Intent Contract explicitly
  scoped the noise simulation out ("that consumes this module's output
  but is a separate deliverable"), which reads as "new module" — but not
  decided here; flag for whoever picks this up, ideally cross-checked
  with Architect/Planner given it also touches `PLAN.md`'s repo-structure
  table (currently silent on this piece).
- Provider choice (Qiskit/Braket/Classiq) — Toolsmith capability-contract
  question per `CLAUDE.md`'s general provider-order convention; not
  decided here.

## Done

- 2026-07-14, Implementer A. **Provider decision**: this task's own Open
  Question flagged provider choice as "a Toolsmith capability-contract
  question, not an Implementer call to make alone." Surfaced explicitly
  before starting (`AskUserQuestion`); user's direction was to pick one
  and proceed. Chose **Qiskit + Qiskit Aer** (`AerSimulator`,
  `qiskit_aer.noise`) — the standard local-simulator choice, matching
  `PLAN.md`'s "Braket/Classiq only for a small real-circuit demo" (this
  is a local noise-model study, not that demo). Installed into `.venv`
  only (`backend/requirements.txt`, Render-deployment-scoped, untouched
  per TASK-0018's boundary).
- **Dependency-conflict finding, checked immediately, not assumed
  benign**: `qiskit-aer` pulled `numpy` 1.26.4->2.5.1 and `scipy`
  1.13.1->1.18.0, and pip flagged `biotite==0.41.0` as incompatible with
  numpy>2.0. Verified before proceeding: `import biotite` still works,
  and the **entire pre-existing test suite (`pytest_local.py wip-all`)
  passes unchanged** after the upgrade (531 passed, 0 regressions) —
  confirmed empirically, not assumed. Flagged here for visibility (a
  numpy major-version bump is a real, repo-wide dependency change) even
  though nothing broke.
- Added `src/allostery/noise.py`: `build_xy_walk_circuit` (Trotterized
  single-excitation-subspace XY-model circuit, one qubit per
  coarse-grained node, exact per-edge `RXX`+`RYY` since `[XX,YY]=0` — a
  real gate-model reproduction of `propagators.ctqw` restricted to
  `H_coarse`, documented as such in the module docstring, not an
  unrelated toy walk), `build_noise_model` (depolarizing on 2-qubit
  gates + amplitude damping per Trotter layer, `dephasing_prob` as the
  additional ENAQT channel), `simulate_occupation`, `top_k_overlap`,
  `run_noise_sweep`.
- **Real bug found and fixed while testing**: `qc.save_density_matrix()`
  only exists once `qiskit_aer` has been imported (it monkey-patches
  `QuantumCircuit`) — `build_xy_walk_circuit` tried to call it before
  that import happened. Fixed by moving the call into
  `simulate_occupation` (which owns the `qiskit_aer` import), not by
  reordering imports at the module top (keeps `build_xy_walk_circuit`
  usable without `qiskit_aer` installed at all, e.g. for depth/gate-count
  inspection only).
- **Computational-feasibility finding (found empirically, not
  anticipated)**: `coarse.trotter_cost`'s own step-count estimate
  (`error_budget=0.01`) is **3133 Trotter steps** for a 10-qubit
  coarse-grained real target — calibrated for high-fidelity simulation
  accuracy, not a NISQ-realistic circuit. A first attempt sweeping
  half/at/double that estimate produced a ~188,000-gate circuit that did
  not finish in 6m45s/69 CPU-minutes and was killed (reported here as a
  finding, not silently abandoned) — real NISQ hardware cannot run that
  depth either, so this gap is itself informative, not just an
  implementation nuisance. Redesigned to sweep a small, NISQ-plausible
  grid (2/5/10 Trotter steps) with `trotter_cost`'s real estimate
  reported alongside as context.
- SEAM-0010 (`coarse.py` -> this task's consumption of its real return
  shapes) closed to **VERIFIED**, with one documented, deliberate
  deviation from its own recommendation: the depth sweep varies
  `trotter_steps`, not `trotter_cost`'s `circuit_depth` estimate, since
  `build_xy_walk_circuit` does not implement the parallel-layer gate
  scheduling `circuit_depth` assumes — flagged as a real, visible gap
  (both quantities reported side by side in every output), not glossed
  over. Full reasoning in the seam file itself.
- **Real run (KRAS_G12C, `H_new`, Louvain-coarse-grained to 10 qubits;
  full detail + table in `RESULTS.md`, dated 2026-07-14)**: swept
  depth ∈ {2,5,10} Trotter steps × error_rate ∈ {0.0, 0.01, 0.05}, both
  coherent (`dephasing_gamma=0`) and ENAQT (`dephasing_gamma=0.3`), at
  two total-evolution times (t=1.0 and a t=25.0 spot-check matching
  TASK-0105's own timescale). **Result: coherent ties or beats ENAQT at
  every single point tested, never loses** — a real, honest negative
  answer to this task's own headline question ("is ENAQT more
  noise-robust than coherent CTQW"), not the hoped-for NISQ story from
  `HOLO_DIRECTION_MODULE.md`. Reported as such, per this project's
  established "an honest NO is a publishable result" convention — not
  softened, not re-run with different parameters to try to manufacture a
  different answer.
- GAUGE/KNOB/SIGNAL transformation table (this task's own Constraint,
  required before any degradation number) written into
  `nisq_noise_simulation.py`'s own module docstring and reproduced in
  `RESULTS.md`: coarse-graining seed (KNOB), qubit-to-cluster labeling
  (GAUGE), `AerSimulator` method choice (KNOB), depolarizing/
  amplitude-damping probabilities and `dephasing_gamma` (SIGNAL, the two
  swept/compared axes).
- Scope actually run: one real target (KRAS_G12C, cheapest of the
  three), one operator (`H_new`), one coarse-graining method (Louvain).
  BCR_ABL1/CARDIAC_MYOSIN, `H10`/`H2` comparisons, and a spectral
  coarse-graining cross-check were not run — the noise-simulation
  mechanism itself (tested on synthetic graphs) is this task's real
  deliverable; one real run demonstrates it end to end and answers the
  headline question with real data.
- Tests: `test_noise.py` (17 cases) — circuit qubit-count/depth-scaling
  sanity; noiseless occupation conserves probability (sums to 1) and
  correctly stays at the seed on a disconnected graph or at t=0; noise
  measurably breaks that conservation at a real error rate but not at
  zero error rate; `top_k_overlap`'s three cases (identical, disjoint,
  partial Jaccard); `run_noise_sweep`'s row count/dephasing-gamma
  bookkeeping; **the SEAM-0010 consumption tests** (4 cases, see above).
- Validation: `.venv/bin/python3 -m pytest -q __WORK_IN_PROGRESS__/tests/
  test_noise.py` — 17 passed. `python3 .ai/tools/pytest_local.py
  wip-all --json` (full suite, post-`qiskit-aer`-install) — confirmed
  green before and after this task's own additions.
