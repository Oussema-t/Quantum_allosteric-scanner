# TASK-0068 NISQ noise-model simulation on `coarse.py`'s output

## Context

- ID: TASK-0068
- Title: Depolarizing + amplitude-damping Trotterized simulation on
  `coarse.py`'s coarse-grained graph, reporting top-5 ranking degradation
  vs. circuit depth and error rate
- Status: TODO
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

(not yet)
