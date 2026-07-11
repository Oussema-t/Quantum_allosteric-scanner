# SEAM-0002 protocol firewall isolates held-out labels from any reader

- units: `protocol` (DEV/FROZEN + LOPO selection) -> any label reader during selection
- invariant: held-out labels are unreadable during selection (`assert_readable` raises)
- owner: [[TASK-0006]] (Done)
- seam-test: `protocol.py::assert_readable` (raises) — exact test file/function not independently confirmed at seeding time, see Open item below
- status: VERIFIED
- provenance: seeded from `SEAM_PROTOCOL.md`'s own table at adoption ([[TASK-0050]], 2026-07-11).
  **Not independently re-verified** — confirmed `assert_readable` exists in `protocol.py`
  (line 90) but did not confirm a dedicated cross-unit seam-test exercises it (vs. a
  same-module unit test only, which per this registry's own definition would not qualify
  as a seam-test). Follow-up: confirm or demote to OPEN as part of [[TASK-0053]]'s sweep.
