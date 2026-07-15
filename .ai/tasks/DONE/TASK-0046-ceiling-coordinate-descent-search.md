# TASK-0046 Notebook §8 ceiling coordinate-descent search — needs a home

## Context

- ID: TASK-0046
- Title: Give notebook §8's "interpretable parameter optimization"
  (coordinate-descent/random search over `H_new`'s physical scalars) a home
  in `__WORK_IN_PROGRESS__/src/allostery/`
- Status: Done
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

None -- see Done below.

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

**Note on Phase 1B gating**: `EXECUTION_PLAN.md`'s Phase 5 row for this
task (5.6) marks it "gated pending Phase 1B" (the proximity-confound/
propagator-semantics correction). Proceeded 2026-07-14 on the reasoning
(confirmed with the orchestrating user) that this task's actual
dependencies are 1B.1-1B.3 (`TASK-0094`/`0095`/`0096`, all Done) -- the
foundational floor/propagator/operator-register fixes -- not the
still-in-flight causal-attribution threads (1B.4/1B.5/1B.14/1B.15). This
task's ceiling search uses `metrics.auc`/real labels the same way
everything else in the pipeline now does, post-1B.1-3; it does not
depend on how BCR_ABL1's `ground_state_relaxation` finding or KRAS's
proximity-floor finding are ultimately framed.

**`ceiling.py` vs `analysis.ceiling_search` (Open Question, resolved)**:
new file, `__WORK_IN_PROGRESS__/src/allostery/ceiling.py`. Checked
`analysis.py`'s actual shape first, per this task's own instruction:
457 lines / 8 functions (`benchmark`, `ablation`, `quantum_vs_classical`,
`assemble_verdict_results`, `apo_holo_consistency`, `spectral_enrichment`,
`dephasing_sweep`, `gnm_cutoff_weight_sweep`) -- already broad, covering
several distinct scoring concerns. A label-using *search driver* on top
of that scoring surface is a different concern, the same DEV/FROZEN
module-boundary reasoning that already keeps `select.py`/`protocol.py`
separate from `analysis.py`. `.ai/tasks/PLANS/PLAN.md`'s repo-structure
table was not updated in this commit -- flagged: that table already
predates several modules (`ceiling.py` included) and is documented
elsewhere (`.ai/COMMON.md`) as not the live source of truth; deferred to
whoever next does a docs-sync pass rather than hand-editing a table this
task doesn't own the accuracy of.

**"Coordinate-descent" naming (Open Question, resolved)**: read notebook
cell 43's full driver in the raw `.ipynb` JSON (not PLAN.md's summary,
per this task's own instruction). The driver is blind random search
(`for _ in range(60): p = sample_params(rng); ...`), no per-coordinate
stepping, no warm-starting from the previous best -- the "coordinate-
descent" section title over-claims; the cell body is the actual spec.
Ported as random search, not invented into real coordinate descent.

**No `kernel` DOF (new finding, not anticipated when this task was
filed)**: the notebook's `sample_params` includes
`kernel = rng.choice(["exp","gauss"])`, but this repo's ported
`hamiltonians.build_H_new` -> `normalised_laplacian_alpha` has no
kernel-choice parameter at all -- always exponential-decay, tunable only
via `alpha`. Confirmed by reading `hamiltonians.py` directly, not
assumed. Searches exactly `build_H_new`'s actual DOF: `(lam_B, lam_T,
lam_R, lam_C, lam_M, alpha, cutoff, n_low_modes)`, documented in
`ceiling.py`'s own module docstring rather than silently dropping the
parameter.

**`map_holo_to_apo_occ`**: ported onto `labels._needleman_wunsch_map`/
`labels._sequence` (both private, same-module-boundary reuse the task's
own Intent Contract calls for), not the notebook's Biopython
`PairwiseAligner` -- `labels.py` deliberately has no Biopython
dependency (TASK-0004).

**Objective function** (`consistency_score`): ported verbatim, `S =
0.5*(AUC_apo+AUC_holo) - 0.25*|AUC_apo-AUC_holo| + 0.10*rho`, including
the notebook's own edge-case conventions (holo AUC falls back to apo AUC
when holo is unlabelled or degenerate; rho falls back to 0.0 when fewer
than 10 residues have a common apo/holo alignment). The pure formula is
isolated as `_combine_score(auc_apo, auc_holo, rho)` so its three-term
direction is unit-testable deterministically (Planned Validation),
without needing synthetic coordinates engineered to produce a specific
AUC gap through real CTQW physics.

**One deliberate deviation from verbatim porting**: the notebook's own
`trials.sort(key=lambda x: -x[0])` does not guard against a `NaN` `S`
(Python's sort with `NaN` present is not reliably consistent -- a latent
bug, not a result to reproduce). `ceiling_search` excludes `NaN`-scored
trials from "best" selection while keeping them in the full `trials`
list for audit, and raises if every trial is `NaN` rather than silently
returning a `NaN` "best".

**`ceiling_context()` wiring**: verified directly (not just by reading
the source) that a trial actually executes with
`protocol.current_context().mode == "ceiling"` and that the context
exits cleanly afterward (`test_search_runs_with_ceiling_mode_active_and_
exits_cleanly`, via a monkeypatched spy on `consistency_score`).

**Tests**: `__WORK_IN_PROGRESS__/tests/test_ceiling.py`, 13 cases (12
synthetic/offline + 1 real-network). `.venv/bin/python3 -m pytest -q
tests/test_ceiling.py -k "not real_target"` — 12 passed, 1.6s.

**Real KRAS_G12C cross-check** (Planned Validation): `apo=4OBE`,
`source=labels.build_labels(...).active_site` (full multi-index array —
this module never calls `select.py`, so TASK-0090's single-index
workaround does not apply here, same reasoning `TASK-0105`'s Done
section already used), `pocket=labels.build_labels(...).pocket`, 60
trials, `seed=7` (matches the notebook's own `np.random.default_rng(7)`
— though, per the `kernel`-DOF removal above, the exact per-trial
parameter sequence diverges from the notebook's, so this reproduces the
notebook's *intent*, not a byte-identical trial sequence). Real result:

```
S=0.5250  AUC_apo=0.5250
params: lam_B=1.65, lam_T=1.84, lam_R=0.25, lam_C=0.18, lam_M=1.98,
        alpha=0.158, cutoff=8.71, n_low=12
```

**This closely reproduces `PLAN.md`'s own qualitative §8 finding**
("optimized AUC_apo on KRAS ~= 0.53, near chance even with the answer
key") — measured 0.5250 vs. the plan's ~0.53, both squarely in the
near-chance band despite this port's several documented differences
from the notebook (label source, no `kernel` DOF, this repo's own
`build_H_new`/`time_averaged_ctqw`). **Even with 60 trials of the answer
key in hand, actively optimizing for pocket AUC, KRAS_G12C's ceiling
does not clear chance.** This is a genuinely different, and more
load-bearing, finding than `TASK-0093`'s: that task showed the *default*-
parameter AUC (0.779) is proximity-correlated, not a real signal. This
task shows the *ceiling* — the best a fully-informed, 60-trial random
search over `H_new`'s entire physical-scalar space can do — is itself
near chance. There is very little headroom in this operator family for
KRAS_G12C at all, floor-clearing or not; `TASK-0082`'s competence map
should read this ceiling number directly, not re-derive it.

**Real-run script**: not written as a separate orchestrator script (out
of scope, per Constraints — `ceiling_search` is a library function,
matching `run_challenge.py`'s own precedent of not letting `TASK-0046`'s
search live inside the submission orchestrator). The cross-check above
was run via `test_kras_g12c_real_target_ceiling_cross_check` directly.

**Ceiling-vs-baseline gate comparison**: out of scope (per Intent
Contract), deferred to whoever consumes this ceiling number alongside
`baselines.py`'s floor scores (`TASK-0082`).

**Addendum, 2026-07-15 (`REVIEW-2026-07-15b-ceiling-search-methodology.md`)**:
two follow-ups filed against this task's real KRAS_G12C finding
("S=0.5250... very little headroom in this operator family"), both
attaching here rather than reopening this task:

- `TASK-0116` — the 60-trial blind random search over `sample_params`'s
  ~8-dimensional space is sparse coverage for the *negative* claim drawn
  from it. A space-filling design or real optimizer may find headroom
  this run's 60 random draws missed.
- `TASK-0117` — `consistency_score`'s `t_max=15.0`/`n_steps=500`
  defaults (same values used across all 60 trials, N=169) are the exact
  unvalidated parameters `TASK-0108`/`TASK-0109`/`TASK-0110` (filed the
  same day) exist to check. Hard-blocked on `TASK-0109` landing.

Neither retracts the 0.5250 result — both ask whether it's strong enough
evidence for the "very little headroom" conclusion `TASK-0082` is
instructed to read directly.
