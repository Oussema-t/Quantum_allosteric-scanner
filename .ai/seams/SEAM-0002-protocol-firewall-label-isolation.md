# SEAM-0002 protocol firewall isolates held-out labels from any reader

- units: `protocol` (DEV/FROZEN + LOPO selection) -> any label reader during selection
- invariant: held-out labels are unreadable during selection (`assert_readable` raises)
- owner: [[TASK-0006]] (Done)
- seam-test: `test_protocol.py::test_get_pocket_mask_raises_when_target_blocked`,
  `::test_get_functional_indices_gated`, `::test_get_superpose_report_gated` —
  each calls a `protocol.py` gated accessor (`get_pocket_mask`/
  `get_functional_indices`/`get_superpose_report`) that internally invokes
  `labels.py`/`superpose.py` functions, inside a `frozen_context`, and
  asserts `LeakageError`. These genuinely cross the protocol.py <->
  labels.py/superpose.py boundary — distinct from the same-module
  `test_frozen_context_blocks_named_target`-style tests (lines 76-100 of the
  same file), which only exercise `assert_readable` in isolation and would
  not qualify as seam-tests on their own.
- status: VERIFIED
- provenance: seeded from `SEAM_PROTOCOL.md`'s own table at adoption ([[TASK-0050]], 2026-07-11).
  **Confirmed by [[TASK-0053]]'s sweep (2026-07-11):** read `protocol.py` and
  `test_protocol.py` directly; the three seam-tests named above exist, pass
  by construction (they assert the raise), and exercise the real cross-unit
  call path (accessor -> `assert_readable` -> underlying `labels`/
  `superpose` call), not just `protocol.py`'s internal state machine.
  Upgraded from "not independently re-verified" to confirmed.
  **Scope note added by [[TASK-0048]]'s Phase 3 review (2026-07-11):** this
  seam's invariant (held-out labels unreadable) still holds and this record
  stays `VERIFIED` for that invariant. But `::test_get_functional_indices_gated`
  only exercises the raise/permit boundary, not parameter-forwarding fidelity
  — `protocol.get_functional_indices` silently drops two of
  `labels.functional_indices`'s parameters (`heavy_atom_coords`,
  `heavy_atom_seq_index`), so an *unblocked* call through the gate gets
  different (coarser) behavior than calling `labels.functional_indices`
  directly. Filed separately as a plain implementation defect, not a new
  seam (it's entirely within `protocol.py`'s own TASK-0006 responsibility,
  not a boundary owned by nobody): [[TASK-0063]].
