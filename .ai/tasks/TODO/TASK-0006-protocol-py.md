# TASK-0006 Implement `protocol.py` — DEV/FROZEN firewall + LOPO

## Context

- ID: TASK-0006
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/protocol.py`
- Status: TODO
- Owner: Implementer
- Source: **no notebook precedent — net-new.** `.ai/tasks/PLANS/PLAN.md`
  Phase 3; `HOLO_DIRECTION_MODULE.md` Step 0 ("freeze the protocol before
  looking at any holo") and its leakage-firewall section.
- Scope: `__WORK_IN_PROGRESS__/src/allostery/protocol.py` (currently a
  5-line stub) + `__WORK_IN_PROGRESS__/tests/test_protocol.py` (new)

## Intent Contract

- Outcome: a hard, mechanically-enforced boundary between "targets whose
  labels I'm allowed to look at while choosing a method" (DEV) and "targets
  that only ever run the one frozen, pre-registered method" (FROZEN) — the
  thing that makes the eventual ceiling−LOPO gap number honest.
- In Scope:
  - `DEV` / `FROZEN` split of the target set (config-driven, not ad hoc).
  - `leave_one_protein_out(targets)` — generator/iterator yielding
    (train_targets, held_out_target) with the held-out target's labels
    inaccessible to whatever selection logic runs inside the loop.
  - a runtime guard that raises if FROZEN-path code attempts to read a
    held-out target's holo/pocket label — not just a documentation
    convention. This is the "leakage is the *goal*" vs "leakage is the
    bug" line the whole plan hinges on (per `.ai/tasks/PLANS/PLAN-01.07.26.md`:
    "Leakage was the core flaw... any per-target knob touching holo =
    leakage").
- Out Of Scope: the selection heuristics themselves (that's `select.py`,
  TASK-0007 — this module only provides the firewall they must run behind).
- Constraints And Invariants:
  - Phase 2 (ceiling) is explicitly allowed to leak — "heavy optimizer,
    answer key in hand (leakage is the goal here)" per `PLAN.md`. This
    module's guard must be **switchable per phase**, not a blanket
    always-on restriction, or it will incorrectly block legitimate
    ceiling-measurement code. Design the API so the caller states which
    phase it's running as (e.g. `protocol.ceiling_context()` vs
    `protocol.frozen_context()`), not a single global flag.
- Planned Validation: unit test that a FROZEN-context read of a held-out
  target's pocket label raises; unit test that the same read succeeds
  inside a ceiling context; unit test LOPO generator yields every target
  exactly once as held-out over a full pass.

## In Progress

None

## TODO

- [ ] Design the DEV/FROZEN context-manager API (see Constraints above).
- [ ] Implement `leave_one_protein_out`.
- [ ] Implement the runtime leakage guard (likely: labels.py's accessor
      functions take a `context` argument, or protocol.py wraps them).
- [ ] Unit tests for the guard (both the "should raise" and "should permit"
      paths) and for LOPO coverage.
- [ ] Document the phase-conditional leakage rule prominently in the module
      docstring — this is the project's stated single biggest risk
      (per `PLAN-01.07.26.md` conclusion #2), so the code enforcing it
      should be impossible to misread.

## Dependency

- TASK-0004 (`labels.py`) — this module wraps/gates access to its outputs.
- TASK-0005 (`superpose.py`) — FROZEN path should only ever include targets
  that passed the Phase 1 cryptic-openness/overlap gate; needs that verdict.

## Open Questions

- Should the leakage guard be enforced by static wrapping (context manager
  that intercepts calls) or by a lint-style check (a test that scans which
  functions were called during a FROZEN run)? Context manager is more robust
  against agent-introduced regressions; recommend that over a lint check.

## Done

(not yet)
