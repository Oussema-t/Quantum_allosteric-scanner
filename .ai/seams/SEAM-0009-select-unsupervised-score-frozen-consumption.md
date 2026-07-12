# SEAM-0009 `select.unsupervised_score` has no wired consumer

- units: `select.unsupervised_score` (TASK-0007, Done) -> *no assembly/call
  site exists* -> `protocol.leave_one_protein_out`'s FROZEN loop / a
  config-selection step in `analysis.py` (TASK-0008, Done)
- invariant: candidate operator/parameter configs selected on a FROZEN
  (held-out) target are actually ranked by `select.unsupervised_score`
  inside `protocol.frozen_context()`, not chosen by some other (possibly
  label-touching) path — the whole reason TASK-0007 exists is to be *the*
  legitimate FROZEN-path selection mechanism, per its own Intent Contract
  ("what keeps selection legitimate inside `protocol.py`'s FROZEN loop")
- owner: [[TASK-0064]] (Done)
- seam-test: `test_protocol.py::TestSelectFrozenConfig` — two tests, not one,
  per this record's own "necessary but not sufficient" warning:
  `test_picks_the_real_unsupervised_score_winner` (the selected config
  traces to `unsupervised_score`'s actual ranking, cross-checked against a
  direct ungated call — a known-discriminating path-vs-star case, computed
  empirically, not guessed) and
  `test_blocks_a_candidate_builder_that_reads_the_held_out_target` (a
  poisoned candidate-*builder* that reads the held-out target's pocket via
  a gated accessor raises `LeakageError` — proves the gate wraps
  construction, not just the scoring call, which alone could never catch
  this since `unsupervised_score` never touches labels).
- status: VERIFIED
- provenance: found during TASK-0048's Phase 3 review (2026-07-11) while
  checking the Intent Contract's cross-task item "`select.py`'s
  `unsupervised_score` is actually meant to run inside
  `protocol.frozen_context()`/a LOPO loop — confirm the call-site contract
  is documented even if no caller exists yet." The docstring contract is
  present and correct (`select.py:168-169`), but the review additionally
  confirmed, via direct grep (`grep -rn "unsupervised_score|from .select"
  __WORK_IN_PROGRESS__/src/allostery/*.py`), that **zero** production
  modules import `select.py` at all — including `analysis.py` (TASK-0008),
  which landed Done after `select.py` and was this seam's presumed
  consumer. This is the same shape as SEAM-0006
  (`pathways.py` -> `viz.py`) and SEAM-0007 (`superpose.py`'s gate ->
  `analysis.py`'s scoring entry points): a producer task reached Done, its
  intended consumer task also reached Done, and the wiring between them
  never actually landed — each side's own tests only exercise it in
  isolation. Not found by TASK-0053's sweep (2026-07-11, same day) — that
  sweep's own scope was TASK-0003-0012 but its four named cross-unit flows
  did not include this one; this record closes that gap.
- **Closed 2026-07-12 by [[TASK-0064]]**: `protocol.select_frozen_config`
  added — a `build_candidates` callable (not a pre-built list) is invoked
  *inside* `frozen_context({held_out_target})`, then scored via
  `unsupervised_score`, so a leaky candidate-construction routine is
  caught, not just a leaky scoring call. Wiring lives in `protocol.py`
  itself (not `analysis.py` or a new module) — consistent with `protocol.py`
  already owning every other FROZEN-gated composition (`get_pocket_mask`,
  `get_functional_indices`, `get_superpose_report`), and with
  `leave_one_protein_out`'s own docstring already describing exactly this
  call shape. Full suite: 405 passed (was 402), 1 pre-existing xfail, 1
  pre-existing xpass (unrelated, not investigated here). Missing
  `.ai/invariants/` GAUGE/KNOB/SIGNAL table for `select.py`'s reported
  quantities (flagged in TASK-0064's own Constraints) filed separately as
  [[TASK-0089]], not built as part of this seam closure.
