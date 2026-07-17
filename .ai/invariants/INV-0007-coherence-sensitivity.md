# INV-0007 `coherence_sensitivity`'s `coherence_auc_range`/`coherence_classification` — `analysis.py`

**Renumbered 2026-07-16/17**: filed as `INV-0005` by TASK-0099, claimed the same
session by TASK-0109's own, unrelated `INV-0005-propagator-time-parameters.md` —
a genuine ID collision (two concurrent threads, same number). Found and fixed
by this Architect/Planner thread while reviewing `EXECUTION_PLAN.md`'s post-panel-review
state; renumbered to the next free slot (`INV-0006` already taken by TASK-0118's
seed-definition record) rather than the propagator-time-parameters file, since
`INV-0006` and other files already cross-reference the propagator one by its
full filename. No content changed, only the ID and this note.

## GAUGE

| Transformation | Test | Status |
|---|---|---|
| Residue relabeling (graph permutation of `H`, `source`/`labels`/`floor_scores` remapped consistently) | Not checked. `coherence_sensitivity` calls `ctqw`/`haken_strobl` on `H`'s eigenstructure and scores via `classify_failure` -- a consistent relabeling should leave `coherence_auc_range`/`classification` unchanged, but no test asserts it. Same open row as [[INV-0004]]'s equivalent for `select.py`. | **OPEN** |

## KNOB

- **`t_max`** -- **KNOB-CHARACTERIZED.** Spread reported: `auc_range` in
  `[0.0132, 0.0247]` on real KRAS_G12C data across `t_max ∈ {8, 25, 100}`
  (a 12x range); `classification` checked stable across the grid --
  `COHERENCE_NOT_SIGNIFICANT` at every point. The *absolute* per-gamma AUC's
  chance/floor diagnosis does shift with `t_max` (some points read
  `BEATS_CHANCE_NOT_FLOOR` at `t=8` vs. `NO_SIGNAL_IN_APO` at `t=25`/`100`)
  -- the classification is robust even though the underlying diagnosis
  category is not, on this one target. Not yet characterized on
  BCR_ABL1/CARDIAC_MYOSIN (blocked, see [[TASK-0128]]).
- **Source/seed cardinality** -- **KNOB-CHARACTERIZED (partial).** Two real
  conventions cross-checked on KRAS_G12C (active-site multi-index array vs.
  GDP-functional-site single/multi-index, different `gamma_scale`/`cutoff`
  too): `auc_range` 0.0132 vs. 0.0076, both `COHERENCE_NOT_SIGNIFICANT`.
  `REVIEW-panel-2026-07-16-v2` Sec.2.1 recommends a wider sweep
  (`{1, k-subset, full, incoherent mixture}`) than the 2 points checked here
  -- not exhaustive, flagged partial rather than claimed complete.
- **`multipliers`** (which γ points are sampled, default `{0, 0.5, 1, 2}`) --
  not characterized against a finer grid; a narrow interior spike between
  sampled points would be missed. **OPEN.**
- **`flat_threshold`** (0.05, reused from `dephasing_sweep`'s own default) --
  sensitivity of the `COHERENCE_NOT_SIGNIFICANT`/`COHERENCE_DEPENDENT_SIGNAL`
  boundary to this specific constant not characterized independently for
  this classification's use (KRAS's own measured range, ~0.013-0.025, sits
  well inside it, so the boundary isn't being tested by any real data point
  yet). **OPEN.**
- **`floor_scores` composition** (which baseline stack forms the floor) --
  inherited from [[TASK-0094]]/[[SEAM-0011]], not independently
  characterized here. **OPEN, deferred to SEAM-0011's own scope.**

## SIGNAL

- Does `classification` actually report `COHERENCE_DEPENDENT_SIGNAL` when
  the floor-cleared status genuinely flips across the sweep (not just
  default to `COHERENCE_NOT_SIGNIFICANT` regardless)? --
  **SIGNAL-VERIFIED** via `test_analysis.py::TestCoherenceSensitivity::
  test_floor_gate_promotes_to_dependent_signal_when_status_flips`
  (monkeypatched propagators forcing a controlled flip) and its sibling
  `test_floor_gate_stays_not_significant_when_status_never_flips` (the
  negative control -- a large raw AUC swing that never flips floor status
  must NOT trigger the dependent-signal classification). The metric is not
  inert to the transformation it exists to detect.
- Real-data case where TASK-0105 found a genuine interior-γ transport
  optimum (KRAS×`H2`, BCR_ABL1×`H_new`, BCR_ABL1×`H2` -- transport
  magnitude, not AUC) -- `coherence_sensitivity` has not yet been run on
  any of those specific (target, operator) cells to see whether it
  correctly flags them (if their AUC/floor response differs from the
  H_new-only cells checked so far). **OPEN**, real gap, not a synthetic
  substitute for a null control that already exists above.

## Status

Mixed: `t_max` and (partially) source-cardinality `KNOB-CHARACTERIZED` with
real data; the flip/no-flip `SIGNAL` row verified by a deliberate synthetic
null control; everything else `OPEN`. Not a completed audit.

## Provenance

Seeded 2026-07-16 by [[TASK-0099]], directly prompted by the user asking
whether `REVIEW-panel-2026-07-16-v2` (Sec.2.1 seed gauge, Sec.2.2 clock
gauge -- "none registered as invariants" per that review's own Weakness #1)
required redoing any part of the just-landed task. The `t_max`/seed rows
above are that audit's actual output, not a placeholder seed record.
Cross-reference: [[pitfalls#P-0003]].
