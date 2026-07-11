# TASK-0064 Wire `select.unsupervised_score` into a real FROZEN-loop consumer

## Context

- ID: TASK-0064
- Title: close [[SEAM-0009]] — `select.unsupervised_score` (TASK-0007,
  Done) has no call site anywhere in production code; `analysis.py`
  (TASK-0008, Done) never imports `select.py` at all
- Status: TODO
- Owner: Implementer
- Source: found during TASK-0048's Phase 3 review (2026-07-11) — see
  `.ai/seams/SEAM-0009-select-unsupervised-score-frozen-consumption.md`
  for full evidence and
  `.ai/reviews/REVIEW-2026-07-11-phase3-protocol-select.md` for the
  review record this was found in.
- Scope: a config-selection step that calls `select.unsupervised_score`
  inside `protocol.leave_one_protein_out`'s loop body, wrapped in
  `protocol.frozen_context({held_out})` — likely lives in `analysis.py`
  or a new thin orchestration function, mirroring TASK-0059's own
  "wrapper vs. in-place" design question for SEAM-0007.

## Intent Contract

- Outcome: a FROZEN (held-out) target's operator/parameter config is
  actually chosen by `select.unsupervised_score`'s label-free ranking, not
  by some other unreviewed path — the concrete mechanism TASK-0007 was
  built to be, wired into the loop TASK-0006 was built to guard.
- In Scope:
  - a function that, per held-out target from
    `protocol.leave_one_protein_out`, builds the candidate list
    (`unsupervised_score`'s expected `{"H", "source", "t", ...}` dicts),
    calls `unsupervised_score` **inside** `frozen_context({held_out})`,
    and picks the top-ranked candidate.
  - a seam-test for `SEAM-0009`: assert the selection step never reads the
    held-out target's true label (reuse `protocol.assert_readable`/a
    `frozen_context` + `pytest.raises` pattern, same shape as
    `test_protocol.py`'s existing gated-accessor tests) **and** that the
    picked config is actually derived from `unsupervised_score`'s output
    (not just "no leak occurred by accident because nothing was called") —
    per this seam's own note, absence-of-leak alone is necessary but not
    sufficient evidence the wiring is real.
- Out Of Scope: changing `select.py`'s scoring functions or `protocol.py`'s
  context managers themselves — this task only adds the missing connective
  layer, same discipline as TASK-0059's Out Of Scope for SEAM-0007.
- Constraints And Invariants:
  - must not change any existing test's expected output for
    `select.py`/`protocol.py` when called directly — additive only.
  - per the Invariance Protocol (`.ai/reference/INVARIANCE_PROTOCOL.md`,
    TASK-0051), `unsupervised_score` is a reported quantity with no
    GAUGE/KNOB/SIGNAL transformation table anywhere in `.ai/invariants/`
    yet (confirmed: zero hits for `select`/`unsupervised_score` in that
    directory as of this filing). This task is not required to build that
    table, but whoever does this wiring should be aware the ranking has
    not been checked for e.g. seed-order invariance or RNG-seed stability
    per that protocol's "Required tests (code / agent output)" section —
    flag as a candidate follow-up (mirroring TASK-0054/TASK-0055's pattern
    of owning one INV row each) rather than silently assuming it's fine.
- Planned Validation: the new `SEAM-0009` seam-test above; re-run existing
  `test_select.py`/`test_protocol.py` suites unchanged.

## TODO

- [ ] Decide wiring location (in `analysis.py` vs. a new thin function) —
      same design question TASK-0059 already faces for SEAM-0007;
      consider resolving both the same way for consistency if TASK-0059
      lands first.
- [ ] Implement the FROZEN-loop config-selection step.
- [ ] Add the `SEAM-0009` seam-test.
- [ ] Update `.ai/seams/SEAM-0009-select-unsupervised-score-frozen-consumption.md`
      to `VERIFIED` once the seam-test passes — do not flip it as part of
      a larger unrelated commit.
- [ ] File (or fold into this task, reviewer's judgment at implementation
      time) the missing `.ai/invariants/` table for `select.py`'s reported
      quantities, per the Constraints note above.

## Dependency

- [[TASK-0006]] (`protocol.py`, Done) — the FROZEN context this task calls
  into.
- [[TASK-0007]] (`select.py`, Done) — the scoring function this task
  wires in.
- [[TASK-0008]] (`analysis.py`, Done) — likely host module, or the
  sibling this task's new orchestration function sits alongside.
- [[TASK-0059]] — same shape of problem (producer/consumer both Done,
  wiring missing) for a different seam (SEAM-0007); not a hard blocker,
  but worth reading together for a consistent wiring-location decision.

## Open Questions

- Same wrapper-vs-in-place question as TASK-0059 — recommend deciding both
  consistently rather than independently, since both are "the missing
  connective layer between two Done modules" in the same package.
- Should this task also produce the INV table for `select.py`'s reported
  quantities, or should that be its own follow-up (`INV-000X` + a
  `TASK-005x`-style owning task, mirroring `TASK-0054`)? Recommend
  deciding at implementation time once the wiring's actual shape is known
  — the invariance classification is easier to get right once there's a
  real call site to reason about, not just the standalone functions.

## Done

(not yet)
