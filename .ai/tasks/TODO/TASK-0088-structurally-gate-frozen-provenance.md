# TASK-0088 Structurally gate `provenance="frozen"` against `protocol.py`'s frozen-config state machine (fixes SEAM-0004)

## Context

- ID: TASK-0088
- Title: make `report.verdict_template`'s `provenance="frozen"` claim
  provably tied to having gone through `protocol.frozen_context`, not a
  free-text keyword any caller can set
- Status: TODO
- Owner: Implementer
- Source: [[TASK-0055]] (SEAM-0004 verification) confirmed the gap is
  real, not hypothetical, and is explicitly Out Of Scope for fixing there
  — same precedent as [[TASK-0052]] filing [[TASK-0087]] for its own
  discovered-but-out-of-scope gap. Full evidence:
  `.ai/seams/SEAM-0004-optimised-auc-freeze-provenance.md`,
  `__WORK_IN_PROGRESS__/tests/test_seam_0004_auc_freeze_provenance.py`
  (`xfail(strict=True)` — should start passing, unchanged, once this
  task lands).

## ⚠️ Before implementing

**This is a genuine design decision, not a mechanical fix.** `report.py`'s
own docstring says it "renders from an already-assembled results dict" —
i.e. rendering typically happens *after* the frozen computation has
finished and `frozen_context` has already exited. That rules out the
naive fix (`verdict_template` reading `protocol.current_context().mode`
at render time) — by the time you render, you're almost always already
outside the context, even for a genuinely honest frozen result. The fix
has to attach an unforgeable provenance marker *at computation time*
(inside the context) that survives into the persisted `results` dict for
later rendering.

## Intent Contract

- Outcome: `test_seam_0004_auc_freeze_provenance.py`'s `xfail(strict=True)`
  test passes for real (remove the marker, same convention TASK-0058 used
  for SEAM-0005) — a report cannot render as an unbannered frozen result
  unless the `provenance` claim was actually produced from inside
  `protocol.frozen_context`.
- In Scope (candidate designs — pick one, or propose a better one; both
  sketched at the level this task was filed, not fully specified):
  1. **Stamped provenance token.** Add `protocol.stamp_provenance(results:
     dict) -> dict` that raises unless called from inside an active
     `frozen_context`, and sets a marker in `results` that only it can
     produce (e.g. `results["_frozen_stamp"] = <opaque token>`, not just
     the string `"frozen"`). `verdict_template` requires that stamp to be
     present (and valid) to render unbannered — a plain `provenance="frozen"`
     string with no stamp renders with the banner regardless.
  2. **Context-object provenance.** `verdict_template` stops accepting a
     free-text `provenance: str` and instead accepts (optionally) the
     `ProtocolContext` object itself, captured by the caller *at
     computation time* (inside the `with frozen_context(...):` block) and
     threaded through to wherever the `results` dict is assembled and
     later passed to `verdict_template`. Simpler than (1) but pushes the
     "capture at the right time" discipline onto every call site instead
     of making it structurally enforced by a single stamping function.
  - Recommend (1) unless the review above finds a reason (2) is
    sufficient — a stamped, function-gated marker is harder to
    accidentally fake than "the caller remembered to capture the context
    object at the right time."
  - Whichever design: must not break `report.py`'s existing behavior for
    the DEV case (`provenance` omitted or anything other than a valid
    frozen claim still renders the `_DEV_BANNER`, unchanged).
- Out Of Scope: any other `provenance`-style gap elsewhere in the package
  (this task is scoped to the one seam it closes).
- Constraints And Invariants: `test_report.py`'s existing suite must keep
  passing unchanged for the DEV-path tests; only the frozen-claim path
  changes shape.
- Planned Validation: the SEAM-0004 seam-test's `xfail` removed and
  passing for real; add a positive-path test proving a genuinely
  stamped/context-captured frozen result renders unbannered, and a
  negative-path test proving a forged plain-string claim (no stamp / no
  captured context) still renders with the banner.

## Dependency

- [[TASK-0055]] (Done) — confirmed and seam-tested the gap this closes.
- [[TASK-0006]] (Done) — `protocol.py`, where the stamping function (if
  design 1 is chosen) would live.
- [[TASK-0010]] (Done) — `report.py`, the consumer side.

## Open Questions

- None yet beyond the design choice called out above.

## Done

(not yet)
