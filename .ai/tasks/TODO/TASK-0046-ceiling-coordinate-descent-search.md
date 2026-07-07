# TASK-0046 Notebook §8 ceiling coordinate-descent search — needs a home

## Context

- ID: TASK-0046
- Title: Give notebook §8's "interpretable parameter optimization"
  (coordinate-descent/random search over `H_new`'s physical scalars) a home
  in `__WORK_IN_PROGRESS__/src/allostery/`
- Status: TODO
- Owner: Implementer
- Source: notebook `notebooks/H_new_engineering (4) CLEAN.ipynb` §8
  ("Interpretable parameter optimization (coordinate-descent random
  search)"); raised as an Open Question in
  `.ai/tasks/TODO/TASK-0008-analysis-py.md` ("Recommend surfacing this as a
  follow-up TASK once TASK-0006/0007 (protocol/select) exist, since the
  ceiling search must run inside `protocol.ceiling_context()`") — both are
  now `Done` (TASK-0006 2026-07-07, TASK-0007 2026-07-07), which is the
  trigger condition TASK-0008 itself named for filing this.
- Scope: not yet decided which file — see Open Questions. Either a new
  `__WORK_IN_PROGRESS__/src/allostery/ceiling.py`, or a function added to
  `analysis.py` (`analysis.ceiling_search`, TASK-0008) once that task
  lands. This task's first job is making that call, not just implementing
  blind.

## Intent Contract

- Outcome: reproduce notebook §8's multi-objective random search over
  `H_new`'s physical scalars
  `(lambda_B, lambda_T, lambda_R, lambda_C, lambda_M, alpha, r_c, kernel)`
  as a callable function, running inside `protocol.ceiling_context()`
  (TASK-0006) so its label-using search is explicitly marked as the
  intentional Phase 2 "leakage is the goal" step, not accidentally reused
  on a FROZEN path.
- In Scope:
  - Port the objective function verbatim (notebook cell 43, `consistency_score`):
    `S(theta) = 0.5*(AUC_apo + AUC_holo) - 0.25*|AUC_apo - AUC_holo| +
    0.10*Spearman(occ_apo, occ_holo_mapped_to_apo)` — rewards pocket AUC on
    both apo and holo while penalizing an apo/holo split, per the notebook's
    own rationale ("a setting that overfits to apo but breaks holo is
    penalised").
  - The apo<->holo occupancy mapping this needs
    (`map_holo_to_apo_occ` in the notebook) should reuse `labels.py`'s
    already-implemented, tested sequence-alignment mapping (TASK-0004's
    Needleman-Wunsch `_needleman_wunsch_map` handles exactly this apo/holo
    residue-numbering problem, including the ABL1 +19 offset) rather than
    re-porting the notebook's own Biopython-based version — `labels.py`
    deliberately avoided a Biopython dependency (TASK-0004 Open Questions);
    this task should not reintroduce it for the same problem.
  - Random search driver (`N_trials` per target, notebook default 60) over
    the physical-scalar space, running inside `protocol.ceiling_context()`.
  - This is the piece that produces the "ceiling" number
    `.ai/tasks/PLANS/PLAN.md`'s Phase 2 gate needs ("ceiling-minus-baseline
    per target... If the ceiling sits at the floor, blind LOPO is not
    worth running").
- Out Of Scope:
  - The ceiling-vs-baseline gate comparison itself (needs `baselines.py`,
    TASK-0011, still TODO, for the random/surface/degree baseline numbers
    to compare the ceiling against) — this task produces the ceiling
    number; a later task (or a small addition to this one, once
    `baselines.py` exists) does the actual gate check.
  - `select.py`'s label-free operator/parameter selection (TASK-0007,
    Done) — that is the FROZEN-path analogue of this task's DEV-path
    search; they are deliberately separate (label-free vs. label-using),
    not two entry points into the same function.
- Constraints And Invariants:
  - Must run its label-using search wrapped in
    `protocol.ceiling_context()` (TASK-0006) — this is Phase 2's
    documented, sanctioned leakage, not a violation, but it must be
    explicit at the call site, not bare.
  - Reuse `metrics.auc`/`metrics.block_bootstrap_ci` (`[have]`) for the AUC
    terms, `scipy.stats.spearmanr` (already a project dependency via
    scipy) for the consistency term — don't reimplement either.
- Planned Validation: unit test on synthetic apo/holo coordinate pairs that
  the objective function's three terms move in the expected direction
  (higher apo+holo AUC -> higher score; larger apo/holo AUC gap -> lower
  score); one real-target run (KRAS_G12C) cross-checked against the
  notebook's own §8 output cell values, read directly rather than
  re-derived.

## In Progress

None

## TODO

- [ ] Decide `ceiling.py` (new file) vs. `analysis.ceiling_search`
      (TASK-0008) — see Open Questions. Whichever is chosen, update
      `.ai/tasks/PLANS/PLAN.md`'s repo-structure table in the same commit
      (same discipline as TASK-0007's `[have]` fix).
  - `.ai/tasks/PLANS/PLAN.md`'s repo-structure table.
- [ ] Read notebook cell 43 (`consistency_score`, `map_holo_to_apo_occ`)
      and the §8 driver cell(s) that call it; extract exact §8 output
      values as regression oracles (same discipline TASK-0008 uses for its
      own two oracle numbers).
- [ ] Implement the objective function, reusing `labels.py`'s alignment
      map (see Intent Contract) instead of a fresh Biopython port.
- [ ] Implement the random-search driver, explicitly wrapped in
      `protocol.ceiling_context()`.
- [ ] Unit tests (synthetic apo/holo pairs) + the KRAS_G12C real-target
      cross-check.

## Dependency

- TASK-0006 (`protocol.py`, Done) — `ceiling_context()` this search must
  run inside.
- TASK-0007 (`select.py`, Done) — not a code dependency, but establishes
  the DEV-path/FROZEN-path split this task is the DEV-path half of.
- TASK-0004 (`labels.py`, Done) — reuse its apo/holo alignment map, per
  Intent Contract.
- TASK-0008 (`analysis.py`, claimed by Implementer A as of 2026-07-07
  06:20, TODO) — if the "add a function to analysis.py" option is chosen
  over a new `ceiling.py`, this task is blocked on TASK-0008 landing
  first; check `analysis.py`'s state before deciding.
- TASK-0011 (`baselines.py`, TODO) — needed for the ceiling-vs-baseline
  gate comparison (Out Of Scope above), not for this task's own ceiling
  number.

## Open Questions

- `ceiling.py` (new file) vs. `analysis.ceiling_search` (function inside
  TASK-0008's module) — `.ai/tasks/TODO/TASK-0008-analysis-py.md`'s own
  Open Questions section raised this without deciding. Whoever picks up
  this task should check `analysis.py`'s actual shape once TASK-0008
  lands before deciding — if `analysis.py` ends up large/broad, a separate
  `ceiling.py` keeps the DEV/FROZEN module split legible (mirrors
  `select.py` vs `protocol.py` being separate files for a similar
  selection-vs-enforcement reason); if `analysis.py` stays focused, adding
  one function there is less overhead than a new file.
- Does the notebook's `N_trials=60` random search need to become something
  smarter (actual coordinate descent, not just random search, despite the
  section's title) for this port, or is blind random search over 60 trials
  the actual intended method despite the "coordinate-descent" name in the
  notebook heading? Re-read cell 43's full driver logic (only partially
  quoted in this task's Intent Contract) before assuming either.
- Filed as TASK-0046, not TASK-0045: an ID collision with a concurrent
  thread claiming TASK-0045 for something else independently (both threads
  computed "next free ID" at nearly the same time) — renumbered on the
  user's instruction before either landed on disk. Check TASK-0045's own
  file once it appears, in case it's a duplicate of this same gap rather
  than unrelated work.

## Done

(not yet)
