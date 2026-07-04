# TASK-0014 Implement `viz.py` — structure/pathway visualization (presentation only)

## Context

- ID: TASK-0014
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/viz.py`
- Status: TODO
- Owner: Implementer
- Source: notebook `notebooks/H_new_engineering (4) CLEAN.ipynb` §13
  "Visualisations" — direct port, lowest priority of all module tasks
  (explicitly "presentation only – not scored" per the existing stub
  docstring).
- Scope: `__WORK_IN_PROGRESS__/src/allostery/viz.py` (currently a 5-line
  stub) + `__WORK_IN_PROGRESS__/tests/test_viz.py` (new, minimal)

## Intent Contract

- Outcome: reusable plotting functions for the submission report, replacing
  ad hoc notebook plotting cells. Not on the critical path for any
  scientific gate — do this last, after TASK-0008/0009/0010 give it real
  data shapes to plot.
- In Scope: port §13's plot functions (structure rendering, pathway overlay,
  score-vs-label scatter, whatever else §13 contains) as callable functions
  taking data arrays, not notebook-global variables.
- Out Of Scope: the frontend's existing 3Dmol.js/Plotly viewer in
  `frontend/` — that's the production app's visualization layer and is
  unrelated to this research-scaffold module; do not conflate the two or
  attempt to unify them without a separate, explicit decision.
- Constraints And Invariants: since this module isn't scored, don't let it
  block or gate any other task — if TASK-0008/0009/0010 land without this,
  that's fine; this can trail behind.
- Planned Validation: smoke tests only (function runs without error on
  synthetic data, returns a figure/axes object) — no need for pixel-level
  or numerical assertions on a presentation-only module.

## In Progress

None

## TODO

- [ ] Read notebook §13; extract plot functions.
- [ ] Port as parameterized functions.
- [ ] Smoke tests.

## Dependency

- Soft dependency on TASK-0008/0009/0010 for realistic data shapes to
  visualize; not a hard blocker — can be stubbed against synthetic data
  first.

## Open Questions

- None — lowest-stakes task in this set.

## Done

(not yet)
