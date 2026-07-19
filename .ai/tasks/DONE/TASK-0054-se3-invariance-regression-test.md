# TASK-0054 Add the missing SE(3)-joint-rotation regression test for `cumulative_overlap`

## Context

- ID: TASK-0054
- Title: `__WORK_IN_PROGRESS__/src/allostery/superpose.py`'s
  `cumulative_overlap`/`anm_modes` have no test asserting the output is
  invariant under an arbitrary rigid rotation+translation applied jointly
  to the coordinates and the displacement — the exact class of bug
  `INVARIANCE_PROTOCOL.md` names as this repo's own prior incident
  (cumulative overlap moved 0.34→0.90 under rotation before the fix)
- Status: Done
- Resolution: done
- Owner: Implementer
- Claimed By: Implementer C (this thread)
- Claimed At: 2026-07-19 22:01
- Source: filed by [[TASK-0051]] (Invariance Protocol adoption) as
  `INV-0001`'s named owner for its one `OPEN` GAUGE row, per that
  protocol's own rule: "A seam/invariant with no owner is the defect
  condition this protocol exists to prevent."
- Crit Ref: the root-cause fix for the *historical* version of this bug
  (mode selection by eigenvalue tolerance, not index; raise on
  rank-deficient graph) is confirmed already live in `anm_modes`
  (`superpose.py:258-283`, verified by reading the code directly for
  [[TASK-0051]]). This task is not "fix a live bug" — it's "add the
  regression test that would have caught it," since none currently
  exists for this specific quantity.

## Intent Contract

- Outcome: one new test in `test_superpose.py` that rotates+translates
  both `coords` and the displacement vector jointly by an arbitrary
  `SO(3)` element (not just axis-aligned/identity — the historical bug
  was rotation-dependent specifically), recomputes `anm_modes` +
  `cumulative_overlap` on the transformed input, and asserts the output
  matches the untransformed result to `atol≈1e-9` — per
  `INVARIANCE_PROTOCOL.md`'s Tier 0 GAUGE standard (hard assert, not a
  tolerance to widen on failure).
- In Scope:
  - a synthetic toy system (reuse `test_superpose.py`'s existing fixture
    patterns — check `test_delta_r_confined_to_first_two_modes_gives_co2_near_one`'s
    setup rather than inventing a new one) with a real, non-trivial
    displacement (not the degenerate zero-displacement case, which is
    already covered by `test_zero_delta_r_returns_zeros`)
  - apply a genuinely arbitrary rotation (e.g. sampled from a fixed seed,
    not just 90°/180° axis-aligned rotations, which can hide bugs that
    only show up off-axis) to both `coords` and the raw displacement
    before computing `delta_r`, translation applied too (translation
    should be gauge-trivial for a *displacement* vector, but assert it
    anyway — cheap, and the protocol's own point is not to assume)
  - assert `cumulative_overlap`'s full output array matches pre- and
    post-transform to `atol≈1e-9`, per every `m`, not just the final
    value
  - if this test **fails**, that is a real finding to report immediately,
    not a tolerance to loosen — per `INVARIANCE_PROTOCOL.md`'s explicit
    rule of engagement ("Any drift is a bug, never a tolerance to
    widen"). Given the zero-mode-integrity fix is already in place, the
    expectation is this test passes, but that expectation must be
    checked, not assumed (the whole reason this task exists).
- Out Of Scope:
  - the Tier 2 KNOB characterization (cutoff/`n_modes`/reference-conformer
    spread) or Tier 3 SIGNAL null controls for this quantity — separate,
    not-yet-filed follow-ups if `INV-0001`'s sweep continues.
  - permutation invariance (residue relabeling) — a related but distinct
    GAUGE check `INVARIANCE_PROTOCOL.md` also names; could be a sibling
    test in the same task if cheap, but don't let scope creep block
    landing the rotation test specifically.
- Constraints And Invariants:
  - stdlib/existing-dependency only (`numpy`, whatever `test_superpose.py`
    already imports) — no new test dependency for one regression test.
  - do not modify `anm_modes`/`cumulative_overlap` themselves unless this
    test actually fails and reveals a real bug — this task is test-first,
    not a refactor.
- Planned Validation: the test itself is the validation. Run
  `pytest_local.py wip-superpose` (or equivalent preset) before and after
  adding it to confirm it's collected and passes.

## In Progress

None

## TODO

- [x] Write the SE(3)-joint-rotation test in `test_superpose.py`.
- [x] Run it; if it fails, stop and report the failure as a finding
      (do not adjust tolerance to force green).
- [x] Update `INV-0001` (from [[TASK-0051]]) — flip the SE(3)-invariance
      row from `OPEN` to `GAUGE-VERIFIED` only if the test passes.

## Dependency

- [[TASK-0051]] — `INV-0001`'s record must exist for this task's status
  update to land somewhere.
- [[TASK-0005]] (Done) — `superpose.py`, the module under test.

## Open Questions

- None yet — this is a bounded, single-file test addition with a clear
  pass/fail outcome.

## Done

**Test written per this task's own Intent Contract, not a weaker version**:
`test_superpose.py::TestCumulativeOverlapSE3Invariance.
test_rotation_and_translation_leave_cumulative_overlap_unchanged` — reuses
the existing `_rotation_matrix(ax, ay, az)` helper already in the file with
a fixed, genuinely off-axis Euler triple (`0.4, -1.1, 2.3` radians, not
0/90/180°, which the task's own text flags as able to hide bugs that only
show up off-axis), a real non-degenerate displacement (`rng.normal`, not
the zero-displacement case already covered elsewhere), applied jointly to
`coords` (rotation + a nonzero translation) and `delta_r` (rotation only —
translation is gauge-trivial for a displacement, asserted not assumed, see
below). Recomputes `anm_modes` + `cumulative_overlap` on the transformed
input; asserts the **full output array** (every `m`, not just the final
value) matches pre-transform to `atol=1e-9`, per `INVARIANCE_PROTOCOL.md`'s
own Tier 0 GAUGE standard. Also asserts the eigenvalues themselves (mode
energies) are SE(3)-invariant as a fixture sanity check before trusting the
CO comparison built on top of them.

**Result: passes.** The historical bug's root-cause fix (`anm_modes`
selecting modes by eigenvalue tolerance, never by index) generalizes
correctly to cumulative overlap's full downstream computation — confirmed
directly by running the test, not assumed from the fix already being in
place (this task's own stated reason for existing). Per this task's own
explicit instruction, a failure here would have been reported immediately
as a finding, not absorbed by loosening the tolerance; no such finding
arose.

**Translation isolated as its own test**, per this task's own Intent
Contract ("translation should be gauge-trivial for a displacement vector,
but assert it anyway — cheap, and the protocol's own point is not to
assume"): `test_translation_alone_is_gauge_trivial_for_the_displacement`
translates `coords` alone (no rotation), leaves `delta_r` untouched,
confirms `cumulative_overlap` is unaffected. Passes.

**Permutation invariance absorbed as a sibling test** (this task's own Out
Of Scope explicitly allowed this "if cheap, don't let scope creep block
landing the rotation test specifically" — written after the rotation test,
not instead of it):
`test_residue_relabeling_leaves_cumulative_overlap_unchanged` — `coords`
and `delta_r` permuted together by the same random permutation (both must
move together; permuting only one would be a different, meaningless
comparison), `cumulative_overlap` unaffected to `atol=1e-9`. This closes
`INV-0001`'s second, previously-unowned `OPEN` GAUGE row in the same pass.
Passes.

**`INV-0001` updated**: all 3 GAUGE rows now `GAUGE-VERIFIED` (were: 1
`GAUGE-VERIFIED` by code-inspection-only, 2 `OPEN`). **Found and fixed a
real staleness while reading the record this task needed to update
anyway**: the zero-mode-count row still described `anm_modes`' selection as
asserting exactly `== 6` near-zero modes — [[TASK-0128]] (2026-07-18)
widened this to `>= 6` (plus a connectivity check) for genuinely-floppy
connected structures like BCR_ABL1/CARDIAC_MYOSIN, but `INV-0001` was never
updated to reflect it. Corrected additively (the row's own claim, test
references, and status all updated to match the current, real code and
test names) — not this task's own primary scope, but directly adjacent and
cheap to fix while already editing this exact file and section.

**`EXECUTION_PLAN.md` had two references to this task, in two different
phases (1C.13, 4.3) — both updated.** The older 4.3 entry's own framing
("applied to **both** trees") predates the task as actually filed and
turned out to be moot, not silently dropped: checked directly (grepped
`backend/` for `cumulative_overlap`/`anm_modes`), `backend/` has no such
function at all — there was only ever one tree with this quantity to test.
TASK-0051's own later, more specific scoping (`allostery/superpose.py`
only) is what this task actually implemented against, correctly.

**Test coverage**: 3 new tests in `test_superpose.py`
(`TestCumulativeOverlapSE3Invariance`), all passing. Full suite re-ran
clean, no regressions (see this session's own full-suite log). Per this
task's own Constraints: did not modify `anm_modes`/`cumulative_overlap`
themselves (the test passed on first try — no bug to fix), no new test
dependency added (reused the file's existing `_rotation_matrix` helper and
`numpy`/`pytest` only).
