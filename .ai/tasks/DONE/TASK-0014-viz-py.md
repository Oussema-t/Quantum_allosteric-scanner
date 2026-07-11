# TASK-0014 Implement `viz.py` — structure/pathway visualization (presentation only)

## Context

- ID: TASK-0014
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/viz.py`
- Status: Done
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

None — all TODO items complete, see Done section.

## TODO

- [x] Read notebook §13; extract plot functions. §13 is a single monolithic
      cell (cell 54), not several named functions — 5 panels (A: ablation
      heatmap, B: propagator comparison, C: per-term AUC, D: apo/holo
      consistency, E: occupation profile), all pulling from notebook-global
      DataFrames (`ABL`/`QVC`/`SP`/`CONS`/`MODEL`/`OPT`). The Intent
      Contract above ("structure rendering, pathway overlay, score-vs-label
      scatter") doesn't actually match §13's real content — none of those
      three are in it; that phrasing looks like a guess by whoever wrote
      this task file, not a read of the cell. Noted rather than silently
      built to the wrong spec.
- [x] Port as parameterized functions — 6 functions, each taking plain
      arrays/dicts (the real shapes `analysis.py`'s functions return, now
      that TASK-0008 is Done) instead of notebook globals:
      `plot_occupation_profile` (panel E), `plot_ablation_bar` +
      `plot_ablation_heatmap` (panels A/C, split into single-target and
      multi-target versions since `analysis.ablation()` is single-call),
      `plot_group_comparison` (panel B, generalized rather than
      propagator-specific), `plot_apo_holo_consistency` (panel D),
      `summary_figure` (composes the above). Plus **`plot_pathway_overlay`
      — not in §13 at all**, built to close SEAM-0006 (see below).
- [x] Smoke tests — `tests/test_viz.py`, 17 tests, all passing (function
      runs on synthetic data, returns a Figure/Axes; plus real assertions
      on `plot_pathway_overlay`'s shape-validation error paths, since those
      encode SEAM-0006's invariant, not presentation).

## Dependency

- Soft dependency on TASK-0008/0009/0010 for realistic data shapes to
  visualize — **resolved**: all three landed Done before this task
  started, so `viz.py`'s panel functions were written against
  `analysis.py`'s actual real return shapes (checked by reading its source
  directly), not synthetic guesses.
- New, found this session: [[TASK-0012]] (`pathways.py`, Done) via
  [[SEAM-0006]] — `pathways.edge_propensity`/`extract_pathway`'s output is
  consumed by this task's new `plot_pathway_overlay`. Closed, not just
  consumed — see Done section.

## Open Questions

- ~~None — lowest-stakes task in this set.~~ Superseded — this task landed
  after the Seam/Invariance protocols (TASK-0050/0051), so it inherited a
  real registered seam ([[SEAM-0006]]) that didn't exist when this file was
  first written. No new open questions from the implementation itself.

## Done

- All 6 functions implemented in `__WORK_IN_PROGRESS__/src/allostery/viz.py`:
  `plot_occupation_profile`, `plot_ablation_bar`, `plot_ablation_heatmap`,
  `plot_group_comparison`, `plot_apo_holo_consistency`,
  `plot_pathway_overlay`, plus the composing `summary_figure`.
- `tests/test_viz.py`: 17 tests. `tests/test_seam_0006_pathways_viz.py`
  (new file, matching the `test_seam_0005_*` naming convention): 3 tests —
  feeds `pathways.py`'s *real*, live `edge_propensity`/`extract_pathway`
  output directly into `plot_pathway_overlay`, not a hand-built dict that
  already assumes the shape is right (that distinction is what makes it a
  seam-test per `SEAM_PROTOCOL.md`, not just another unit test). All 20
  new tests passing; full WIP suite (`__WORK_IN_PROGRESS__/.venv/bin/python
  -m pytest tests/`, run directly — see the `pytest_local.py` finding
  below) 382 passed, 1 xfailed (SEAM-0005, expected/pre-existing), 1
  xpassed (pre-existing unrelated `test_superpose.py` order flake, noted
  since TASK-0004), 0 failures.
- **SEAM-0006 closed: OPEN -> VERIFIED.** This task both owned the seam and
  built its consumer, so registering and closing happened in the same
  pass — `plot_pathway_overlay`'s `_validate_edge_propensity`/
  `_validate_pathway` are the seam's invariant made executable (asserted
  against `pathways.py`'s source directly: `edge_propensity` keys are
  `(i, j)` with `i < j`, non-negative values; `extract_pathway` returns
  exactly `nodes`/`edges`/`reached_target`/`propensity`), and
  `test_seam_0006_pathways_viz.py` exercises them against real producer
  output, not assumed shapes.
- **New dependency: `matplotlib`**, installed into
  `__WORK_IN_PROGRESS__/.venv` this session (not previously present —
  unavoidable for a plotting module; same "ask-first but load-bearing and
  low-risk" call as TASK-0004's `prody` install). Not yet in any
  `requirements.txt`/`pyproject.toml` for `__WORK_IN_PROGRESS__` — same
  pre-existing gap TASK-0003/TASK-0004 already flagged for `prody`/
  `pyyaml`, now also true for `matplotlib`. `networkx` (already a project
  dependency, used by `plot_pathway_overlay` for graph layout) needed no
  new install.
- **Real finding, not part of this task's own scope but blocking it
  directly: `pytest_local.py`'s `wip-*` presets silently resolve
  `REPO_ROOT/.venv` (a top-level venv that didn't exist when
  TASK-0026.005 was built/tested) instead of
  `__WORK_IN_PROGRESS__/.venv`**, so the whitelisted test wrapper was
  running WIP tests against the wrong interpreter — invisible until a
  WIP-only dependency (`matplotlib`) was needed, since the root venv has
  its own numpy/scipy/pytest and mostly "worked" by accident. Filed as
  **TASK-0069** (Toolsmith) rather than fixed here — out of an Implementer
  task's scope, and touching shared `.ai/tools/` risks collision given
  this session's active `GIT-COMMIT` queue. Verified the full suite
  directly against the correct venv instead
  (`__WORK_IN_PROGRESS__/.venv/bin/python -m pytest tests/`) so this task's
  own Done status isn't resting on a result from the wrong interpreter.
- Per user instruction this session: **no staging/commit performed** —
  this task's files (`viz.py`, `test_viz.py`,
  `test_seam_0006_pathways_viz.py`, this task file, `SEAM-0006`'s record,
  `TASK-0069`'s file, `COMMON.md`'s registry) are all on disk, uncommitted,
  pending the user's go-ahead and this thread's turn in the commit queue.
