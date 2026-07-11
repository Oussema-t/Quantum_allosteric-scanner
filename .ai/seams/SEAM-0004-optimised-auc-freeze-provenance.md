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
