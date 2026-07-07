# TASK-0047 Bridge gaps found in the Foundation review (TASK-0003/0004/0005)

## Context

- ID: TASK-0047
- Title: Add the missing `labels.py` network-gated KRAS_G12C integration
  test (TASK-0004's own unmet Planned Validation item) and strengthen the
  numbering-offset regression test in `test_labels.py` to actually exercise
  a real sequence-alignment indel case.
- Status: TODO
- Owner: Implementer
- Source: Reviewer A's Foundation Review Record,
  [`.ai/reviews/REVIEW-2026-07-07-foundation-0003-0005.md`](../../reviews/REVIEW-2026-07-07-foundation-0003-0005.md),
  findings P2 and P3. No new defect in shipped behavior — both findings are
  test-coverage gaps against already-Done tasks' own stated validation
  plans.
- Scope: `__WORK_IN_PROGRESS__/tests/test_labels.py` only. No production
  code in `labels.py` is expected to change — if writing the network test
  surfaces an actual behavioral bug, that's a new finding, not this task's
  starting premise.

## Intent Contract

- Outcome: `test_labels.py`'s committed test suite actually covers what
  TASK-0004's own Intent Contract promised, closing the gap between "a
  check was run by hand once" and "a check runs every time CI runs."
- In Scope:
  1. **P2 (primary):** add a network/`prody`-gated integration test against
     real KRAS_G12C data (apo `4OBE`, holo `6OIM`), mirroring the pattern
     already established in `test_superpose.py`'s
     `test_kras_g12c_real_target_expects_low_cumulative_overlap`
     (`pytest.importorskip("prody")`, live `prody.parsePDB` fetch). This is
     exactly the test TASK-0004's Intent Contract asked for and never
     landed: "one integration test gated behind network access... against
     KRAS_G12C (4OBE/6OIM) once TASK-0003's config exists."
     - Assert `holo_pocket_mask`'s output is consistent with the
       previously-cited manual check referenced in `labels.py`'s
       docstrings (`labels.py:56-67`, `:96-104`) — the 9/21
       heavy-atom-vs-Cα-only recovery finding — so that narrated,
       one-time result becomes a pinned, re-run-every-time regression
       check instead of a docstring claim nobody re-verifies.
     - Load the real target config via `targets.yaml`
       (`load_target_config("KRAS_G12C")`, TASK-0003's own loader) rather
       than hand-constructing a config dict, so this test also exercises
       the TASK-0003→TASK-0004 config handoff end-to-end.
  2. **P3 (secondary, smaller):** either strengthen
     `test_numbering_offset_still_maps_correctly` or add a sibling test so
     that at least one case in `test_labels.py` exercises the
     Needleman-Wunsch aligner (`_needleman_wunsch_map`) on a genuine
     insertion/deletion (apo and holo sequences of *different* length, not
     just re-numbered), not only the "same sequence, shifted resnums" case
     that never actually depends on alignment recovering a gap. Document in
     the test itself why the existing offset test and the new indel test
     are checking two different things (numbering-independence vs.
     alignment-correctness-under-gaps) so a future reader doesn't collapse
     them back into one.
- Out Of Scope: any change to `labels.py`/`superpose.py`/`targets.yaml`
  production code; re-opening TASK-0003/0004/0005 themselves (this is a
  follow-up, per the Review Record's own recommendation to file one rather
  than reopen a Done task); Phase 3/4 test coverage (separate review
  track).
- Constraints And Invariants:
  - New network-gated test must follow the existing skip discipline
    exactly (`pytest.importorskip("prody")` or equivalent) — must not
    become a hard CI failure in environments without `prody`/network, same
    as `test_superpose.py`'s precedent.
  - Do not weaken or delete `test_numbering_offset_still_maps_correctly` —
    it still correctly documents that resnum values are ignored by design;
    add coverage alongside it, don't replace its intent.
- Planned Validation:
  - `pytest __WORK_IN_PROGRESS__/tests/test_labels.py` passes with `prody`
    absent (new test skips cleanly) and with `prody` installed + network
    available (new test runs and passes, matching the 9/21 recovery
    finding and a sequence-alignment-derived pocket mask consistent with
    `backend/systems.py`'s existing `pocket_full[4.5]` KRAS_G12C entries).
  - The new indel test fails if `_needleman_wunsch_map` is naively replaced
    with a positional (non-aligned) mapping — i.e. it must be a real
    discriminating test, not something that would pass under either
    implementation.

## In Progress

None

## TODO

- [ ] Write the network-gated KRAS_G12C integration test in
      `test_labels.py`, following `test_superpose.py`'s
      `pytest.importorskip("prody")` pattern.
- [ ] Confirm it passes locally with `prody` installed (this session's
      review already confirmed `prody` installs cleanly in `.venv` and the
      equivalent `superpose.py` test passes against live RCSB data — reuse
      that same environment state).
- [ ] Add/extend the indel-case test for `_needleman_wunsch_map` per P3
      above; add a one-line comment distinguishing it from the existing
      offset test's purpose.
- [ ] Run the full `test_labels.py` suite both with and without `prody`
      installed to confirm the skip path still works cleanly.

## Dependency

- TASK-0003 (`targets.yaml`, Done) — supplies `load_target_config` and the
  KRAS_G12C entry the new test loads.
- TASK-0004 (`labels.py`, Done) — the module under test; no code changes
  expected, per Scope above.
- Sourced from the Foundation Review Record (Reviewer A, 2026-07-07):
  [`.ai/reviews/REVIEW-2026-07-07-foundation-0003-0005.md`](../../reviews/REVIEW-2026-07-07-foundation-0003-0005.md).

## Open Questions

- None currently — both findings are well-scoped test-coverage gaps with a
  concrete existing pattern (`test_superpose.py`) to follow.

## Done

(not yet)
