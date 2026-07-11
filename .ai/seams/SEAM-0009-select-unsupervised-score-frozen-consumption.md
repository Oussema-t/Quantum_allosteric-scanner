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
- owner: [[TASK-0064]] (new, filed by TASK-0048's Phase 3 review)
- seam-test: not yet written — cannot be written for real until a real
  call site exists (same precedent as SEAM-0006 pointing at not-yet-landed
  `viz.py`); when TASK-0064 starts, it should assert that a FROZEN-loop
  config-selection step actually calls `unsupervised_score` (or an
  equivalent label-free ranking) rather than merely not calling any gated
  `protocol.get_*` accessor (the latter is necessary but not sufficient —
  a selection step could still pick a config by some other unreviewed,
  possibly-leaky heuristic and this seam would stay silent).
- status: OPEN
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
