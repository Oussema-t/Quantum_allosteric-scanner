# SEAM-0007 cumulative-overlap go/no-go gate is not wired into which targets `analysis.py` scores

- units: `superpose.run_superpose` (produces `cumulative_overlap`/`openness_gate`) -> *no filtering step exists* -> `analysis.py`'s scoring entry points (`benchmark`, `ablation`, `quantum_vs_classical`, `apo_holo_consistency`, `spectral_enrichment`, `dephasing_sweep`)
- invariant: a target whose `cumulative_overlap`/`cryptic_openness_gate` verdict says the apo->holo direction is not spanned by the soft ANM modes (the documented Phase 1 / `HOLO_DIRECTION_MODULE.md` Step 2 go/no-go gate) does not silently proceed to full scoring as if it had cleared the gate
- owner: [[TASK-0059]] (new, filed by this sweep)
- seam-test: not yet written — `TASK-0059` should add one asserting that a synthetic
  low-`CO(m)` target either (a) is excluded from a scoring entry point by default, or
  (b) if scored anyway, the result is tagged/returned alongside the gate verdict so a
  caller cannot silently treat it as a cleared target — whichever design `TASK-0059`
  settles on (see that task's Open Questions)
- status: **VERIFIED** (2026-07-24, [[TASK-0059]])
- provenance: found by [[TASK-0053]]'s sweep (2026-07-11), one of the four flows its
  own Intent Contract named to check explicitly ("superpose.py -> analysis.py
  (cumulative-overlap gate into which targets proceed to scoring)"). Confirmed by
  direct read: none of `analysis.py`'s six public scoring functions take a gate
  verdict, a `CO(m)` value, or any parameter referencing `superpose.py`'s output at
  all — every one operates on raw `coords`/`H`/`labels`/`occ` arrays the caller must
  already have decided to score. `PLAN.md` Phase 1's own gate language ("only
  learnable targets proceed to ceiling/LOPO") and `HOLO_DIRECTION_MODULE.md` Step 2
  ("stop for that target and record it as a finding... do not proceed to Step 3-5")
  both describe this as a hard requirement; nothing in the landed code enforces it.
  This is not a hypothetical — every one of TASK-0003-0012's own unit tests scores
  synthetic/real targets directly, so the gate has never actually been exercised as a
  gate in this codebase yet.
- resolution ([[TASK-0059]], 2026-07-24): re-read `PLAN.md` Phase 1 ("report as
  'pocket absent from apo topology' — a finding, with a figure — rather than
  dropping the target silently") and `HOLO_DIRECTION_MODULE.md` Step 2 before
  choosing a shape, per this seam's own design-decision callout — both argue for
  tag-alongside, not hard exclusion, and the project's own established practice
  since ([[TASK-0120]]/[[TASK-0133]]/[[TASK-0139]]'s `learnability_verdict`, always
  reported alongside AUC, never used to exclude a target) independently confirms
  this reading. `protocol.run_frozen_verdict` gained an optional `learnability`
  parameter (a caller-precomputed `superpose.learnability_verdict(...)` result,
  same "caller assembles the holo-informed piece, this function only attaches it"
  boundary `holo_H`/`holo_labels` already establish, no new import from
  `superpose.py` inside `protocol.py`) — when supplied, `_learnability_verdict`/
  `_learnability` land in the same result dict `_diagnosis`/AUC already do;
  omitted entirely, not raised, when not supplied. Seam-test:
  `tests/test_protocol.py::TestLearnabilityWiring` (3 tests — omitted-by-default,
  a real `UNLEARNABLE_FROM_APO` verdict attached and visible alongside
  `_diagnosis`, a real `LEARNABLE` verdict attached symmetrically). Actually
  invoking this from the live end-to-end run (`run_challenge.py`) is filed as a
  separate follow-up ([[TASK-0150]]), matching this project's own established
  precedent ([[TASK-0092]] split "support the parameter" from "wire it into the
  real run" the same way) — this seam is about the wiring *existing and being
  exercised by a real test*, not about every caller having adopted it yet.
