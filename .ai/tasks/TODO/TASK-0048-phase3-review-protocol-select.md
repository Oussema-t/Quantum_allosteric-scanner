# TASK-0048 Phase 3 review (TASK-0006 `protocol.py` / TASK-0007 `select.py`)

## Context

- ID: TASK-0048
- Title: Code-Reviewer-overlay review of the Phase 3 cluster —
  `protocol.py` (DEV/FROZEN firewall + LOPO) and `select.py` (label-free
  unsupervised operator selection) — against their own Intent Contracts,
  mirroring the Foundation review's format.
- Status: TODO
- Owner: Code Reviewer
- Source: continuation of the review-plan thread established across this
  session's TASK-0044/TASK-0047 work. Both cluster members reached Done
  (TASK-0006, TASK-0007) during this session; user directed this review to
  run in the **next** session rather than now.
- Scope: `__WORK_IN_PROGRESS__/src/allostery/protocol.py` +
  `tests/test_protocol.py`; `__WORK_IN_PROGRESS__/src/allostery/select.py` +
  `tests/test_select.py`. Phase 4+ (TASK-0008 and later) stays out of scope
  — separate future review.

## Intent Contract

- Outcome: a Review Record (same shape as
  [`REVIEW-2026-07-07-foundation-0003-0005.md`](../../reviews/REVIEW-2026-07-07-foundation-0003-0005.md))
  covering TASK-0006 and TASK-0007 together, plus the cross-task leakage
  checks that only make sense once both are done.
- In Scope, per-task:
  - **TASK-0006 (`protocol.py`):** guard is a phase-switchable context
    manager (`ceiling_context()` permits, `frozen_context(X)` raises on a
    held-out target's holo/pocket read), not a lint-style check;
    `leave_one_protein_out` yields every target exactly once per pass;
    guard actually wraps `labels.py`'s real accessor functions
    (`holo_pocket_mask`, `functional_indices`, `pick_drug`), not a parallel
    reimplementation; unit tests cover both the "should raise" and "should
    permit" paths.
  - **TASK-0007 (`select.py`):** every function (`focusing`,
    `source_specificity`, `ballistic_exponent`, `unsupervised_score`) is
    computable from the apo structure and its own walk output alone — grep
    for any accidental holo/label access; `focusing` reuses `metrics.ipr`
    rather than reimplementing it; synthetic path/star/complete graphs
    give clearly distinct readings; `unsupervised_score` is a real
    combination, not a stub passthrough.
- In Scope, cross-task:
  - `select.py`'s `unsupervised_score` is actually meant to run inside
    `protocol.frozen_context()`/a LOPO loop — confirm the call-site
    contract is documented even if no caller exists yet (TASK-0008+ is the
    eventual caller).
  - `PLAN.md`'s stale `[have]` tag on `select.py`/`protocol.py` — TASK-0007's
    own TODO said this was already corrected by TASK-0002 (2026-07-04);
    spot-check `PLAN.md`'s repo-structure section still reflects that.
  - Leakage-boundary docstring language consistency across
    `labels.py`/`superpose.py`/`protocol.py`/`select.py` (labels.py↔protocol.py
    consistency already spot-checked during the Foundation review —
    confirm `select.py` fits the same story too).
- Out Of Scope: re-reviewing TASK-0003/0004/0005 (already done, see the
  Foundation Review Record); Phase 4 (TASK-0008+).
- Planned Validation: run
  `pytest __WORK_IN_PROGRESS__/tests/test_protocol.py test_select.py -v`
  and interpret results against each task's own Planned Validation section
  (TASK-0006: LOPO-raises / LOPO-permits / full-coverage tests; TASK-0007:
  synthetic path/star/complete graph tests), same evidence-first method
  used for the Foundation pass — don't just check green, check the tests
  assert what the Intent Contract actually asked for.

## In Progress

None

## TODO

- [ ] Read `protocol.py` + `test_protocol.py` in full; check against
      TASK-0006's Intent Contract and Constraints.
- [ ] Read `select.py` + `test_select.py` in full; check against
      TASK-0007's Intent Contract and Constraints.
- [ ] Run both test files; for any network/optional-dependency-gated test
      (if present), install the dependency and actually run it rather than
      trusting the skip, per the Foundation review's method.
- [ ] Cross-task checks per Intent Contract above.
- [ ] Write `REVIEW-<date>-phase3-protocol-select.md` under `.ai/reviews/`,
      same shape as the Foundation Record; file follow-up gap-bridging
      task(s) if findings warrant, same pattern as TASK-0047.

## Dependency

- TASK-0006 (`protocol.py`, Done) and TASK-0007 (`select.py`, Done) — both
  must stay Done; if either is reopened before this review starts, hold
  this task until it re-lands.
- Precedent/format: TASK-0047 and
  [`REVIEW-2026-07-07-foundation-0003-0005.md`](../../reviews/REVIEW-2026-07-07-foundation-0003-0005.md)
  (Foundation review, same reviewer, same method).

## Open Questions

- None yet — will surface during the review itself.

## Done

(not yet)
