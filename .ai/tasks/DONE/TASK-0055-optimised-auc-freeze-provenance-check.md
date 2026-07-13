# TASK-0055 Verify `AUC_*_optimised` provenance is actually frozen, not just labeled so

## Context

- ID: TASK-0055
- Title: `report.py` (TASK-0010, Done) gates on a `provenance` string —
  prepends a `[DEV/CEILING RESULT]` banner unless `provenance == "frozen"`
  (`report.py:141-142`) — but nothing verified for this task confirms
  *who sets that string* actually only marks it `"frozen"` when the
  reported `AUC_apo_Hnew_optimised`/`AUC_holo_Hnew_optimised` values were
  genuinely produced under `protocol.py`'s frozen-config discipline, not
  just labeled that way by whatever caller assembled the report
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: filed by [[TASK-0050]] (Seam Protocol adoption) as `SEAM-0004`'s
  named owner, per that protocol's core rule that a seam with no owner is
  the defect condition it exists to prevent.
- Crit Ref: this is exactly the "§8 leak" `SEAM_PROTOCOL.md`'s own seed
  table warns about re-importing if the provenance check is honored in
  name only. `report.py`'s own module comment (line 30-31) confirms the
  DEV/FROZEN vocabulary is meant to match `protocol.py::ProtocolRoster`
  — this task checks that the two sides of that match actually hold,
  not just that both sides use the same words.

## Intent Contract

- Outcome: a confirmed answer to "can `AUC_*_optimised` ever be tagged
  `provenance='frozen'` while actually having been computed with
  label-tuned/DEV parameters" — either verified impossible (cite the
  mechanism that prevents it), or a real gap with a concrete repro.
- In Scope:
  - trace every call site that produces a `results` dict consumed by
    `report.py`'s `verdict_template` (or equivalent) — find where
    `provenance` is actually set, not just where it's read
  - cross-check against `protocol.py`'s `ProtocolContext`/`frozen_context`/
    `ProtocolRoster` (`protocol.py:44-175`) — does the frozen/dev state
    machine make it *structurally* impossible to set `provenance="frozen"`
    without having actually gone through `frozen_context`, or is
    `provenance` just a free-text string a caller could set to anything?
  - write a seam-test: attempt to construct a report claiming
    `provenance="frozen"` from a call path that never entered
    `frozen_context` — assert this either can't happen (raises / is
    structurally prevented) or currently *can* (a real finding)
- Out Of Scope:
  - redesigning the DEV/FROZEN mechanism — this task verifies the
    existing one, doesn't replace it, unless the seam-test proves it's
    broken, in which case report the finding and let a follow-up decide
    the fix.
  - the other seeded seams from [[TASK-0050]] — `SEAM-0003` is
    [[TASK-0052]]'s job, `SEAM-0005` is entangled with [[TASK-0011]].
- Constraints And Invariants:
  - per the Seam Protocol: this is a seam-test, meaning it must exercise
    the invariant *across* `report.py` and `protocol.py` — a unit test
    inside either module alone that could catch this on its own is not
    sufficient to close this seam.
- Planned Validation: the seam-test itself (see In Scope) is the
  validation — pass means the invariant is structurally enforced, fail
  means a real gap, both are a valid, useful outcome for this task to
  report.

## In Progress

None

## TODO

- [x] Trace `provenance` from every producer call site through to
      `report.py`'s consumption of it.
- [x] Determine whether `provenance="frozen"` is structurally gated by
      `protocol.py`'s state machine or is a free-text label.
- [x] Write the cross-module seam-test.
- [x] Update `SEAM-0004` (from [[TASK-0050]]) to `VERIFIED` (with the
      seam-test as evidence) or leave `OPEN` with the finding documented,
      whichever the test result actually shows.

## Dependency

- [[TASK-0010]] (Done) — `report.py`, the consumer side of this seam.
- [[TASK-0006]] (Done) — `protocol.py`, the producer side.
- [[TASK-0050]] — this task is `SEAM-0004`'s named owner; that record
  must exist first.

## Open Questions

- None yet — scope is bounded to tracing one field's provenance guarantee
  across two already-Done modules.

## Done

- Traced `provenance` end-to-end: `report.py::verdict_template(results,
  *, provenance: str = "dev")` (`report.py:115`) is a plain caller-supplied
  keyword. Confirmed zero calls to `protocol.current_context()` anywhere
  in `report.py`, and `protocol.frozen_context` returns a `ProtocolContext`
  that nothing in `report.py` ever consumes.
- **Finding: the invariant does NOT hold.** `provenance="frozen"` is a
  free-text label, not structurally gated by `protocol.py`'s state
  machine — confirmed empirically, not just by inspection: outside any
  `frozen_context` (`protocol.current_context().mode == "unguarded"`),
  `verdict_template({"AUC_apo_Hnew_optimised": 0.9}, provenance="frozen")`
  renders with no DEV banner. A DEV/ceiling number can currently be
  presented as the frozen submission verdict undetected — the exact
  "§8 leak" scenario `SEAM_PROTOCOL.md`'s seed table warns about.
- Cross-module seam-test written:
  `test_seam_0004_auc_freeze_provenance.py` —
  `test_provenance_frozen_claim_requires_having_been_inside_frozen_context`
  (`xfail(strict=True)`, encodes the desired invariant, fails today
  exactly as the finding above predicts) + a positive-control test
  documenting the same gap from the other side. Both pass/xfail as
  designed (`1 passed, 1 xfailed`).
- `SEAM-0004` updated with this evidence — **left `OPEN`** (not
  auto-flipped to `VERIFIED`; the seam is confirmed broken, not closed),
  per the Intent Contract's own "both are a valid, useful outcome"
  framing.
- Per Out Of Scope, the fix itself was **not** implemented here — filed
  as **TASK-0088** (structurally gate the provenance claim, e.g. a
  `protocol.stamp_provenance()` helper only callable from inside
  `frozen_context`), unclaimed, same precedent as TASK-0052 → TASK-0087.
- Full local run: `python3 .ai/tools/pytest_local.py wip-all --json` →
  399 passed, 1 xfailed (this task's own SEAM-0004 test, expected), 1
  xpassed (pre-existing, unrelated, not investigated — out of scope),
  0 failed.
- **Staging/commit deferred** — held per the user's manual
  Stage-Commit-Queue coordination (2nd in queue at completion time); code
  and tests are complete and locally green, not yet staged.

**Update 2026-07-13, closure confirmed:** the "left `OPEN`" line above
describes SEAM-0004's state *at this task's own completion* — do not read
it as current. **TASK-0088 (Done, commit `6c164d4`) closed SEAM-0004 to
`VERIFIED`**: `protocol.stamp_provenance`/`verify_frozen_stamp` now gate
`provenance == "frozen"` behind an unforgeable-in-practice token issued
only from inside a real `frozen_context`; `report.verdict_template`
requires both. Re-verified independently and live in this session (not
just re-reading task files): a naive `provenance="frozen"` claim with no
stamp still renders the DEV banner, a hand-forged `_frozen_stamp` value
is rejected, and a real stamp issued inside `frozen_context` and rendered
after context exit renders unbannered.
`tests/test_seam_0004_auc_freeze_provenance.py` now has 3 passing tests
(no `xfail`) — the seam-test this task wrote was extended, not replaced,
by TASK-0088. No further action against this task; the TASK-0055 →
TASK-0088 → SEAM-0004 chain is complete.
