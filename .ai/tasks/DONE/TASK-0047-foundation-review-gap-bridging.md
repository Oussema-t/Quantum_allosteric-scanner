# TASK-0047 Bridge gaps found in the Foundation review (TASK-0003/0004/0005)

## Context

- ID: TASK-0047
- Title: Add the missing `labels.py` network-gated KRAS_G12C integration
  test (TASK-0004's own unmet Planned Validation item) and strengthen the
  numbering-offset regression test in `test_labels.py` to actually exercise
  a real sequence-alignment indel case.
- Status: Done
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

- [x] Write the network-gated KRAS_G12C integration test in
      `test_labels.py`, following `test_superpose.py`'s
      `pytest.importorskip("prody")` pattern.
- [x] Confirm it passes locally with `prody` installed (`prody` was
      *not* already installed in `.venv` despite this note's claim —
      installed it fresh this session; ran against live RCSB data).
- [x] Add/extend the indel-case test for `_needleman_wunsch_map` per P3
      above; add a one-line comment distinguishing it from the existing
      offset test's purpose.
- [x] Run the full `test_labels.py` suite both with and without `prody`
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

**Scope note found at pickup (2026-07-12):** TASK-0070 (pocket label
exclusion assembly) landed since this task was filed and already added
`build_labels` plus two real-target network-gated tests
(`test_kras_g12c_real_cys12_excluded`, `test_bcr_abl1_real_exclusion_invariant_holds`).
Those cover the Cys12/exclusion-invariant question, but neither uses
`load_target_config` (both hand-build the config dict) nor asserts
`holo_pocket_mask`'s raw recovery against `backend/systems.py`'s
`pocket_full[4.5]` — so P2 was only partially subsumed, not fully closed.
Wrote the remaining piece rather than duplicating TASK-0070's coverage.

- **P2:** added `test_kras_g12c_real_holo_pocket_mask_matches_systems_py_pocket_full`
  — loads KRAS_G12C via `load_target_config` (exercises the
  TASK-0003→TASK-0004 config handoff end-to-end, not a hand-built dict),
  calls `holo_pocket_mask` directly (the raw contact mask, matching what
  `backend/systems.py`'s `pocket_full` itself represents — pre-exclusion,
  distinct from `build_labels`'s assembled `.pocket`), and asserts the
  recovered residue set matches `pocket_full[4.5]` **exactly**: `{9, 10,
  11, 12, 13, 16, 34, 58, 59, 60, 61, 62, 63, 68, 69, 72, 95, 96, 99, 100,
  103}` (21 residues). Ran against live 4OBE/6OIM data — passes, pinning
  the "21/21 heavy-atom recovery" docstring claim as a real regression
  check for the first time.
- **P3:** added `test_indel_case_needleman_wunsch_recovers_correct_apo_index`
  to `TestHoloPocketMask` — a genuine insertion/deletion (apo 13 residues,
  holo 12, one residue deleted mid-sequence), not just re-numbering.
  First attempt asserted a single flagged residue and failed: adjacent
  synthetic-helix residues sit ~3.8 Å apart, inside the 4.5 Å contact
  cutoff, so a ligand placed at one residue also contacts its immediate
  neighbors — not a bug, a wrong test assumption. Redesigned around two
  discriminating residues instead of one (apo index 10, reachable only
  under correct gap-aware alignment; apo index 7, produced only by a
  naive same-position mapper) so the test is robust to the multi-residue
  contact radius and still fails under a naively-reverted
  `_needleman_wunsch_map`.
- **Validation:** `pytest __WORK_IN_PROGRESS__/tests/test_labels.py`:
  30 passed / 3 skipped with `prody` absent (clean skip path, confirmed
  by reading skip reasons — all three are `No module named 'prody'`, not
  a masked failure); installed `prody` fresh in `.venv` (was *not*
  already present, despite this task's own TODO note claiming otherwise)
  and re-ran against live RCSB data: **33 passed, 0 skipped, 0 failed**
  — includes TASK-0070's two real-target tests and both new ones.
- No production code changed, per this task's own Scope — confirmed via
  `git diff` touching only `__WORK_IN_PROGRESS__/tests/test_labels.py`.
- **Not yet staged or committed** — holding per explicit instruction
  (second in the stage-commit queue at time of writing); this Done
  section and the DONE-folder move are filesystem-only, no `git add`.

**Addendum, 2026-07-15 (`REVIEW-2026-07-15-execution-plan-gap-audit.md`
finding #3, `TASK-0114`)**: the pinned `{9, 10, 11, ..., 100, 103}`
recovery this task locked in above uses `holo_pocket_mask`'s default
4.5 Å ligand-contact cutoff and has never been checked for sensitivity
to that choice — i.e. whether 4.0 Å or 5.0 Å would recover a
meaningfully different residue set, which would mean this pinned
fixture sits near a threshold cliff rather than a stable regression
anchor. Filed separately as `TASK-0114` (real per-target sensitivity
sweep, cross-checked directly against this test's own KRAS_G12C
fixture) rather than reopening this task.
