# TASK-0150 Wire the learnability verdict into the real end-to-end run (`run_challenge.py`)

## Context

- ID: TASK-0150
- Title: [[TASK-0059]] gave `protocol.run_frozen_verdict` an optional
  `learnability` parameter — when a caller supplies a precomputed
  `superpose.learnability_verdict(...)` result, it lands in the same
  result dict `_diagnosis`/AUC already do. `scripts/run_challenge.py`
  (the actual end-to-end submission pipeline) does not supply it —
  its own `run_target`'s `run_frozen_verdict(...)` call has no
  `learnability=` kwarg, so real target runs still don't carry the
  learnability verdict inline in `verdict.json`/the connectivity
  output, only in the separate `scripts/learnability_gate.py`'s own
  JSON.
- Status: TODO
- Owner: Implementer
- Source: filed by [[TASK-0059]] itself, closing [[SEAM-0007]] —
  deliberately split from that task's own scope, mirroring
  [[TASK-0092]]'s own precedent (that task split "support the holo
  kwargs" from "wire them into the real run" the same way, filed as
  two separate tasks rather than one).
- Priority: P2 — the capability already exists and is tested
  ([[TASK-0059]]'s seam-test); this is about a real caller actually
  using it, not a missing mechanism.

## Intent Contract

- Outcome: `scripts/run_challenge.py::run_target` computes a real
  `superpose.learnability_verdict(...)` result (reusing the same
  composition `scripts/learnability_gate.py::run_one` already
  established — `align_apo_holo`, `cryptic_openness_gate`,
  `background_rmsd`, `anm_modes`+`cumulative_overlap` with
  [[TASK-0128]]'s own graceful-degradation handling for the
  `n_zero>6` case, `learnability_verdict`) and passes it to
  `run_frozen_verdict(..., learnability=...)`, so a real target run's
  own `verdict.json` carries `_learnability_verdict`/`_learnability`
  inline.
- In Scope:
  - `run_target`'s own call site in `run_challenge.py`.
  - Deciding where the shared "compute learnability from apo/holo"
    logic should live so it isn't duplicated between
    `run_challenge.py` and `learnability_gate.py` — a small shared
    helper (candidate home: `superpose.py` itself, since it's purely
    a composition of that module's own existing primitives) is one
    option; a local copy is another. Implementer's own call, stated
    with reasoning, given `learnability_gate.py` already imports
    `run_challenge` (`_load_apo_holo`) — a shared helper in
    `superpose.py` avoids a circular import either way, a local copy
    in `run_challenge.py` does not.
  - Re-running the 3 mandatory targets (`run_challenge.py --target
    KRAS_G12C BCR_ABL1 CARDIAC_MYOSIN`) once wired, confirming
    `verdict.json` carries the verdict and it matches
    `scripts/learnability_gate.py`'s own already-recorded numbers for
    the same targets (a cross-check, not a re-derivation — if they
    disagree, that is itself a real finding to report, not silently
    reconciled).
- Out Of Scope:
  - Any change to `learnability_verdict`/`cryptic_openness_gate`/
    `cumulative_overlap`'s own logic — reuse exactly as-is.
  - Any change to `protocol.run_frozen_verdict`'s own signature —
    already correct as of [[TASK-0059]].
- Constraints And Invariants: must not change any existing
  `test_run_challenge.py` test's expected output when `learnability`
  isn't exercised — additive only, same discipline [[TASK-0059]] held
  `run_frozen_verdict` to.
- Planned Validation: a new `test_run_challenge.py` test asserting
  `run_target`'s output includes the learnability verdict for a
  synthetic apo/holo pair; the real 3-target cross-check against
  `scripts/learnability_gate.py`'s own recorded numbers.

## Dependency

- [[TASK-0059]] (Done) — the `learnability` parameter this task
  actually calls.
- [[TASK-0128]] (Done) — the `anm_modes` graceful-degradation case
  this task's shared-logic decision must preserve, not silently drop.

## Open Questions

- None yet — scope is fully specified by [[TASK-0059]]'s own
  follow-up note.

## Done

(not yet)
