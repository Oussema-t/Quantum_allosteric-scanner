# TASK-0051 Adopt the Invariance Protocol into the scaffold

## Context

- ID: TASK-0051
- Title: Incorporate `INVARIANCE_PROTOCOL.md` (relocated from
  `__WORK_IN_PROGRESS__/` to `.ai/reference/`) as a running practice — an
  `.ai/invariants/` registry, seeded with a real finding from this repo's
  own `superpose.py`, and `SUGGESTION.md`'s content absorbed into
  `.ai/memory/shared/pitfalls.md` rather than kept as a freestanding file
- Status: Done
- Owner: Architect/Planner
- Claimed By: Architect/Planner (this thread)
- Claimed At: 2026-07-11 11:59
- Source: user request, 2026-07-11 session — see [[TASK-0050]]'s Source
  for full context; this is the Invariance-Protocol half of the same
  incorporation request.
- Crit Ref: the doc's two worked-example bugs (ANM cumulative-overlap
  rotation-dependence; a quantum-channel Clifford-subgroup bug) are framed
  as *this repo's own history*, not hypothetical. Verified below that the
  ANM one's root-cause fix is already live in shipped code — the missing
  piece is the regression test, not the fix itself.

## Intent Contract

- Outcome: the Invariance Protocol's GAUGE/KNOB/SIGNAL classification is a
  registry with at least one real, evidence-checked entry (not just the
  doc's abstract template), `SUGGESTION.md` no longer exists as a
  standalone file (its content is one `pitfalls.md` entry plus what
  `INVARIANCE_PROTOCOL.md` already restates in its own "Rule of
  engagement"), and the specific missing regression test this task's own
  investigation found is named as a concrete follow-up, not left implicit.
- In Scope:
  - relocate `INVARIANCE_PROTOCOL.md` -> `.ai/reference/
    INVARIANCE_PROTOCOL.md` — **done, this commit**.
  - absorb `SUGGESTION.md` into `.ai/memory/shared/pitfalls.md` as entry
    `P-0001` — **done, this commit** (see that file for the entry).
  - create `.ai/invariants/README.md` (mirrors `.ai/seams/README.md` from
    [[TASK-0050]] and `.ai/tasks/README.md`'s shape)
  - create `INV-0001` for `cumulative_overlap`/`anm_modes`
    (`__WORK_IN_PROGRESS__/src/allostery/superpose.py`), the exact
    quantity the doc's own ANM worked example is about, seeded from a
    real code check performed for this task (not copied from the doc's
    generic template):
    - **GAUGE — zero-mode integrity: VERIFIED.** `anm_modes` (superpose.py:258-283)
      counts near-zero eigenvalues (`n_zero = int((w < 1e-8).sum())`),
      asserts `n_zero == 6`, and **raises** if not — never slices by a
      hardcoded index. This is the exact fix the doc's ANM war story
      describes; it is already live, not a gap. Covered by
      `test_drops_at_least_six_rigid_body_modes` and
      `test_raises_on_disconnected_graph` in `test_superpose.py`.
    - **GAUGE — SE(3)-joint-rotation invariance: OPEN.** No test in
      `test_superpose.py` rotates+translates `coords` *and* `delta_r`
      together and asserts `cumulative_overlap`'s output is stable to
      ~1e-9. `test_recovers_synthetic_rotation_translation` tests Kabsch
      alignment recovery, a different claim. The existing zero-mode-count
      guard makes this *likely* to hold by construction (modes are
      computed from the same aligned frame `delta_r` is expressed in),
      but the doc's own rule of engagement says exactly this: "invariant
      on our test set is a trigger to widen the group, not a green
      light" — a design argument is not the executable test. Owner:
      [[TASK-0054]] (new, filed by this task).
    - **KNOB:** ANM `cutoff` (default 10.0 in `anm_modes`), `n_modes` —
      not yet characterized as a spread (Tier 2); out of scope for this
      task, name it as `OPEN` in the record rather than silently omit it.
    - **SIGNAL:** not yet null-controlled (random displacement vs. real
      apo->holo) for this specific quantity; `OPEN`.
  - update `.ai/COMMON.md`'s Quick Navigation / Source Of Truth the same
    way [[TASK-0050]] does for seams (parallel structure, same commit
    pattern, avoid two inconsistent conventions for two sibling
    registries).
- Out Of Scope:
  - writing `INV` records for every reported quantity in the pipeline —
    one real, evidence-checked seed is the goal here; a full sweep is
    its own future task once the registry pattern is proven (same
    "advisory first, harden after" precedent this scaffold already uses
    repeatedly).
  - implementing the missing SE(3) regression test itself — [[TASK-0054]].
  - the Tier 2/3 KNOB/SIGNAL characterization for `cumulative_overlap` —
    named as `OPEN` in the seed record, not solved here.
- Constraints And Invariants:
  - do not claim `GAUGE-VERIFIED` for anything without checking the
    actual code, per this task's own subject matter — asserting
    invariance without running/reading the check would be exactly the
    "confident prose, not verification" failure mode the source doc
    warns about. The zero-mode-integrity claim above was confirmed by
    reading `superpose.py:258-283` directly, not inferred.
- Acceptance Scenarios:
  - Given `INV-0001`, when a reader checks any of its four rows, then
    each has a status that reflects an actual code/test check performed
    for this task, not a placeholder.
  - Given `__WORK_IN_PROGRESS__/`, when listed, then `SUGGESTION.md` no
    longer exists as a file.
- Planned Validation: not code — validation is "does `INV-0001`'s
  GAUGE-VERIFIED row cite a real line range and a real passing test," and
  "does the OPEN row name a real follow-up task" — both satisfied above,
  not left as TBD.

## In Progress

None

## TODO

- [x] Relocate `INVARIANCE_PROTOCOL.md`.
- [x] Absorb `SUGGESTION.md` into `pitfalls.md`, remove the original file.
- [x] Verify the ANM zero-mode-integrity claim against real code
      (`superpose.py:258-283`) rather than trusting the doc's narrative.
- [x] Verify no existing SE(3)-joint-rotation regression test exists for
      `cumulative_overlap` (checked `test_superpose.py`'s full test list).
- [x] Write `.ai/invariants/README.md`.
- [x] Write `INV-0001` with the four classified rows above.
- [x] File [[TASK-0054]] as `INV-0001`'s named owner for the OPEN
      SE(3)-invariance row.
- [x] Update `.ai/COMMON.md` (Quick Navigation, Source Of Truth, register
      this task).

## Dependency

- [[TASK-0050]] — sibling task, same pattern, for `SEAM_PROTOCOL.md`; not
  blocking each other, but should land together for a consistent
  `.ai/seams/` + `.ai/invariants/` story.
- [[TASK-0005]] (Done) — `superpose.py`, the module `INV-0001` is about.
- [[TASK-0054]] — the follow-up this task files for the one real OPEN gap
  found.

## Open Questions

- Should `.ai/invariants/` and `.ai/seams/` be one combined registry
  (they're both "cross-cutting verification state," per the source docs'
  own framing of seams as the process-level twin of the invariance gate)
  or stay separate? Recommend separate for now — they have different
  record shapes (GAUGE/KNOB/SIGNAL vs. units/invariant/owner) and merging
  them speculatively before either has more than one seeded record would
  be premature structure.
- The Tier 2 KNOB characterization example in the source doc (an 18-combo
  grid flipping the go/no-go verdict in 15/18 cases) is a strong, concrete
  number — is that from a run already performed on this repo's code, or
  from the doc's general prior experience? Not verifiable from the doc
  text alone; flag to the user rather than assume it's this-repo-specific
  evidence.

## Done

- Relocated `INVARIANCE_PROTOCOL.md` to `.ai/reference/INVARIANCE_PROTOCOL.md`.
- Absorbed `SUGGESTION.md` into `.ai/memory/shared/pitfalls.md` as
  entry `P-0001`; removed the standalone file.
- Created `.ai/invariants/README.md` and `INV-0001`
  (`cumulative_overlap`/`anm_modes`, `superpose.py`), seeded from a real
  code check: zero-mode-integrity confirmed `GAUGE-VERIFIED` by reading
  `superpose.py:258-283` directly (the historical bug's root-cause fix is
  live — `n_zero != 6: raise`, never slice by index); SE(3)-joint-rotation
  invariance confirmed genuinely `OPEN` (no such test exists in
  `test_superpose.py`, checked the full test list, not assumed); KNOB/
  SIGNAL rows left `OPEN`, correctly unaddressed rather than silently
  omitted.
- Filed [[TASK-0054]] as `INV-0001`'s named owner for the one OPEN GAUGE
  row.
- Added Quick Navigation and Source-Of-Truth entries to `.ai/COMMON.md`;
  registered this task.
