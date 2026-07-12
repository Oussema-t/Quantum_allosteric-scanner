# TASK-0063 `protocol.get_functional_indices` drops heavy-atom params

## Context

- ID: TASK-0063
- Title: `protocol.get_functional_indices` doesn't forward
  `labels.functional_indices`'s `heavy_atom_coords`/`heavy_atom_seq_index`
  parameters — FROZEN-path callers are silently forced onto the coarser
  Cα-only contact approximation with no way to opt into the more accurate
  path without bypassing the firewall.
- Status: Done
- Owner: Implementer
- Source: TASK-0048 Phase 3 review, P2 finding —
  [`REVIEW-2026-07-11-phase3-protocol-select.md`](../../reviews/REVIEW-2026-07-11-phase3-protocol-select.md).
  No new defect in shipped behavior — no real caller of
  `get_functional_indices` exists yet (`select.py`/TASK-0007 never calls
  it; TASK-0008+ is the eventual caller), so this is an interface gap
  waiting to bite the first real FROZEN-path caller, not an active bug.
- Scope: `__WORK_IN_PROGRESS__/src/allostery/protocol.py`'s
  `get_functional_indices` only. No change to `labels.functional_indices`
  itself expected.

## Intent Contract

- Outcome: a FROZEN-path caller of `protocol.get_functional_indices` can
  supply everything `labels.functional_indices` accepts, exactly like the
  other two gated accessors already do — without ever needing to bypass
  the gate and call `labels.functional_indices` directly.
- In Scope:
  - Add `heavy_atom_coords: np.ndarray | None = None` and
    `heavy_atom_seq_index: np.ndarray | None = None` to
    `get_functional_indices`'s signature and forward both to
    `labels.functional_indices` (`protocol.py:117-122`).
  - Decide, and document the choice: match `get_pocket_mask`'s pattern
    (explicit, but now *complete*, parameter list) or `get_superpose_report`'s
    pattern (`**kwargs` pass-through, immune to future signature drift).
    Recommend `**kwargs` — `get_pocket_mask`'s wrapped function
    (`holo_pocket_mask`) has a small, stable 4-parameter signature, but
    `functional_indices` has already grown once (the heavy-atom params were
    presumably added after this gate was first written) and `**kwargs`
    would have prevented this exact gap from opening in the first place.
- Out Of Scope: `get_pocket_mask`/`get_superpose_report` — already forward
  their wrapped function's full signature (confirmed in the review), no
  change needed. Any change to `labels.functional_indices`'s own signature.
- Constraints And Invariants:
  - `assert_readable(target_name)` must still run before delegating,
    unchanged — this task only widens what's forwarded *after* the gate
    check passes.
  - Existing callers (`test_protocol.py`'s `test_get_functional_indices_gated`)
    must keep passing unchanged — this is an additive signature widening,
    not a breaking change.
- Planned Validation:
  - A new test in `test_protocol.py` that calls `get_functional_indices`
    with real `heavy_atom_coords`/`heavy_atom_seq_index` values (reuse
    `labels.py`'s own `protein_heavy_atoms_by_residue` test fixtures or
    synthesize equivalent small arrays) and asserts the result differs from
    the Cα-only default path on a case where the two approximations
    actually diverge — a test that would fail if the parameters were
    silently dropped again, not just a "doesn't raise" smoke test.
  - Existing `test_protocol.py`/`test_select.py` suites still pass
    unchanged (`pytest __WORK_IN_PROGRESS__/tests/test_protocol.py
    test_select.py -v`).

## In Progress

None

## TODO

- [x] Widen `get_functional_indices`'s signature per above (pick `**kwargs`
      or explicit-complete, document the choice inline).
- [x] Add the new heavy-atom-divergence regression test.
- [x] Run `test_protocol.py`/`test_select.py` to confirm no regression.

## Dependency

- TASK-0006 (`protocol.py`, Done) — the module this task modifies.
- TASK-0004 (`labels.py`, Done) — `functional_indices`'s real signature,
  unchanged by this task.
- Sourced from TASK-0048's Review Record:
  [`REVIEW-2026-07-11-phase3-protocol-select.md`](../../reviews/REVIEW-2026-07-11-phase3-protocol-select.md).

## Open Questions

- None currently — well-scoped signature-widening with a concrete existing
  pattern (`get_superpose_report`'s `**kwargs`) to follow.

## Done

- `protocol.get_functional_indices` now takes `**kwargs` and forwards them
  to `labels.functional_indices`, per the recommended pattern
  (`get_superpose_report`'s existing `**kwargs` shape) — chosen over an
  explicit-complete parameter list precisely because `functional_indices`
  had already grown once (the heavy-atom params) since this gate was
  first written, and an explicit list would just relocate the same class
  of gap to the next parameter addition.
- New regression test,
  `test_protocol.py::TestGatedAccessors::test_get_functional_indices_forwards_heavy_atom_params`:
  same synthetic construction as `test_labels.py::TestContactResidueIndicesHeavyAtomFix`
  (a Cα 6.0 Å from a ligand — outside the 4.5 Å default cutoff — vs. a
  heavy atom on the same residue sitting on top of it), but called
  through the gated `protocol.get_functional_indices` wrapper instead of
  `labels.functional_indices` directly, so it would fail if the gate ever
  drops the parameters again even though `labels.py`'s own tests would
  still pass. Confirmed the two paths genuinely diverge:
  `"top-degree fallback"` without the heavy-atom kwargs vs.
  `"func_ligand-contact:FUNC"` with them.
- `test_protocol.py` (24/24) and `test_select.py` (14/14) both pass
  unchanged — 38/38 combined, no regression.
- Installed `matplotlib` into the shared `.venv` (was missing, blocking
  whole-suite collection via `pytest_local.py all` on two unrelated files
  — `test_viz.py`/`test_seam_0006_pathways_viz.py`, TASK-0014's own gap,
  already filed as TASK-0069). Purely additive — unblocks the whitelisted
  test runner for every thread, doesn't touch any other package.
- No change to `labels.functional_indices` itself, `get_pocket_mask`, or
  `get_superpose_report` (already forward their full signature, confirmed
  by this task's Out Of Scope note).
