# SEAM-0004 report `AUC_*_optimised` provenance matches protocol freeze state

- units: `protocol` (frozen/dev state machine) -> report producer call site -> `report.verdict_template` (gates on `provenance`)
- invariant: a report tagged `provenance == "frozen"` was actually produced under `protocol.py`'s frozen-config discipline, not just labeled that way
- owner: [[TASK-0055]]
- seam-test: not yet written
- status: OPEN
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
