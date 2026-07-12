# SEAM-0004 report `AUC_*_optimised` provenance matches protocol freeze state

- units: `protocol` (frozen/dev state machine) -> report producer call site -> `report.verdict_template` (gates on `provenance`)
- invariant: a report tagged `provenance == "frozen"` was actually produced under `protocol.py`'s frozen-config discipline, not just labeled that way
- owner: [[TASK-0055]] verified the gap; [[TASK-0088]] fixed it.
- seam-test: `__WORK_IN_PROGRESS__/tests/test_seam_0004_auc_freeze_provenance.py` —
  three tests, all passing: `test_provenance_frozen_claim_requires_having_been_inside_frozen_context`
  (unstamped `provenance="frozen"` still renders the banner),
  `test_provenance_frozen_from_inside_frozen_context_is_the_intended_clean_case`
  (a real `protocol.stamp_provenance` stamp, rendered after the context has
  already exited, is honored), `test_forged_stamp_string_is_rejected` (a
  hand-written `"_frozen_stamp"` value never issued by `stamp_provenance`
  is rejected, proving the check is a real token lookup, not key presence).
- status: VERIFIED
- provenance: seeded from `SEAM_PROTOCOL.md`'s own table at adoption ([[TASK-0050]],
  2026-07-11). Confirmed `report.py:141-142` does gate on `provenance != "frozen"` (prepends a
  DEV banner), and the module comment (line 30-31) states the vocabulary is meant to match
  `protocol.py::ProtocolRoster` — but whether that match is structurally enforced or just a
  naming convention both sides happen to follow is exactly what [[TASK-0055]] checks. Unchecked
  as of seeding; re-imports the doc's own referenced "§8 leak" if false.
  **Corroborated by [[TASK-0053]]'s sweep (2026-07-11):** `verdict_template(results, *,
  provenance="dev")` — `provenance` is a plain caller-supplied keyword with no read of
  `protocol.current_context().mode` anywhere in `report.py`, and no call site anywhere
  in `__WORK_IN_PROGRESS__/src/allostery` or its tests currently calls
  `verdict_template` from inside a real `frozen_context` — every exercised call
  (`test_report.py`) hand-passes the string. The gap is real, not hypothetical;
  still OPEN, [[TASK-0055]] remains the right owner.
  **Confirmed empirically by [[TASK-0055]] (2026-07-12), not just by code inspection:**
  outside any `frozen_context` (`protocol.current_context().mode == "unguarded"`),
  `verdict_template({"AUC_apo_Hnew_optimised": 0.9}, provenance="frozen")` renders with
  **no** DEV banner — a caller can label a DEV/ceiling number as the frozen submission
  verdict and nothing in `report.py` or `protocol.py` stops it. Per this task's own Out
  Of Scope, the fix (making `provenance="frozen"` structurally gated by
  `protocol.py`'s state machine, e.g. threading `ProtocolContext` through instead of a
  free string) is deliberately **not** implemented here — this task verifies and makes
  the gap executable, a follow-up task should decide and implement the fix.
  **Closed 2026-07-12 by [[TASK-0088]]**: `protocol.stamp_provenance(results) -> dict`
  raises unless `current_context().mode == "frozen"`, and issues a token (tracked in a
  module-level `_issued_frozen_stamps` set) recorded under `results["_frozen_stamp"]`.
  `protocol.verify_frozen_stamp(results)` checks the token was actually issued, not just
  present. `report.verdict_template` now requires both `provenance == "frozen"` **and**
  a valid stamp to render unbannered — plain `provenance="frozen"` (the leak) and a
  hand-forged `"_frozen_stamp"` value both still render with the banner. Chosen over
  threading `ProtocolContext` itself through to render time (this record's own
  originally-sketched alternative) because rendering happens almost always *after* the
  computing context has exited (`report.py`'s own docstring: "renders from an
  already-assembled results dict") — a stamp issued at computation time and verified
  later survives that gap; a context object captured at render time would not exist by
  then. `test_report.py`'s one test that asserted the old (leaky) behavior was updated to
  stamp its result, per this task's own Constraints ("only the frozen-claim path changes
  shape"); every other `test_report.py` DEV-path test is unchanged.
