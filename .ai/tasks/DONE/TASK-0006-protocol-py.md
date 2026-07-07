# TASK-0006 Implement `protocol.py` — DEV/FROZEN firewall + LOPO

## Context

- ID: TASK-0006
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/protocol.py`
- Status: Done
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

## TODO (resolved 2026-07-07, Implementer A)

- [x] Design the DEV/FROZEN context-manager API (see Constraints above).
  - `ceiling_context()` / `frozen_context(blocked_targets)`, both stdlib
    `contextlib.contextmanager`s pushing onto a module-level stack (so
    nesting resolves to "innermost wins" — tested explicitly). No active
    context = `"unguarded"` (blocks nothing) — a deliberate, documented
    default: this is an opt-in firewall for future Phase-3 pipeline code
    (`select.py`/TASK-0007, `analysis.py`/TASK-0008), not a retroactive
    lock on every existing direct caller of `labels.py`/`superpose.py`
    (including their own test suites).
  - `ProtocolRoster` (DEV/FROZEN split of the *target set*, distinct from
    the ceiling/frozen *execution contexts* above) is built from an
    explicit `{target_name: "dev"|"frozen"}` mapping the caller supplies —
    no hardcoded target list in this module. Which targets graduate from
    DEV to FROZEN is a baseline-clearing decision that belongs to
    `select.py`/`analysis.py`, per this task's own Out Of Scope line; this
    module only provides the bookkeeping container.
- [x] Implement `leave_one_protein_out`.
  - Deliberately a **plain generator** — does not itself enter a
    `frozen_context`. Composability over magic: the caller wraps only
    their selection logic in `with frozen_context({held_out}): ...` inside
    the loop body, then reads the held-out target's true label *after*
    that block exits, to score it — baking context entry into the
    generator would make that release (the entire point of LOPO)
    inexpressible.
- [x] Implement the runtime leakage guard (likely: labels.py's accessor
      functions take a `context` argument, or protocol.py wraps them).
  - Went with wrapping (per this task's own Open Question, resolved below):
    `get_pocket_mask`/`get_functional_indices`/`get_superpose_report` gate
    exactly the three holo-derived outputs `labels.py`'s own module
    docstring names as its output surface (pocket mask, functional
    indices) plus `superpose.py`'s holo-informed Phase 1b report — not a
    speculative wrap of every conceivable future label-reading function.
    `assert_readable(target_name)` is also exposed directly for any future
    call site that reads a holo-derived label some other way.
- [x] Unit tests for the guard (both the "should raise" and "should permit"
      paths) and for LOPO coverage.
  - `tests/test_protocol.py`: 21 tests — context defaults/nesting/release,
    all three gated accessors' raise-and-permit paths (blocked, ceiling,
    unguarded, and "only the named target is blocked, not others"),
    `ProtocolRoster` splitting + validation, LOPO's exactly-once coverage
    + train-set-excludes-held-out + empty-input + "does not itself guard"
    + the full intended compose-then-release-for-scoring pattern.
- [x] Document the phase-conditional leakage rule prominently in the module
      docstring — this is the project's stated single biggest risk
      (per `PLAN-01.07.26.md` conclusion #2), so the code enforcing it
      should be impossible to misread.
  - Module docstring opens with the PLAN-01.07.26.md #2 quote verbatim and
    states the unguarded-by-default design decision explicitly (with the
    reasoning), rather than leaving it implicit.

## Dependency

- TASK-0004 (`labels.py`) — this module wraps/gates access to its outputs.
- TASK-0005 (`superpose.py`) — FROZEN path should only ever include targets
  that passed the Phase 1 cryptic-openness/overlap gate; needs that verdict.

## Open Questions

- Should the leakage guard be enforced by static wrapping (context manager
  that intercepts calls) or by a lint-style check (a test that scans which
  functions were called during a FROZEN run)? Context manager is more robust
  against agent-introduced regressions; recommend that over a lint check.
  - **Resolved in favor of the context-manager + wrapped-accessor
    combination**, as recommended: `frozen_context`/`ceiling_context`
    manage a module-level stack; `get_pocket_mask`/`get_functional_indices`/
    `get_superpose_report` are the only sanctioned entry points into the
    holo-derived outputs and check the active context before delegating.
    A lint-style scan was not built — it would only catch violations
    after the fact (a completed FROZEN run), where the context-manager
    approach raises at the exact moment of the violation.
- **New, raised by this task's implementation:** the gated accessors only
  cover `labels.holo_pocket_mask`/`labels.functional_indices`/
  `superpose.run_superpose` — the specific holo-derived outputs those two
  modules' own docstrings declare as their output surface. If `select.py`
  (TASK-0007) or `analysis.py` (TASK-0008) end up needing some other
  holo-touching call gated (e.g. a narrower superpose.py sub-step called
  directly instead of through `run_superpose`), that caller should use the
  exposed `assert_readable(target_name)` primitive directly rather than
  this task growing speculative wrappers for functions no real caller
  needs yet.
- **New, raised by this task's implementation:** `ProtocolRoster` is pure
  bookkeeping (an explicit `{target: "dev"|"frozen"}` mapping in, a
  queryable split out) — it does not itself decide which targets clear
  ceiling-vs-baseline and graduate to FROZEN. That decision logic (PLAN.md
  Phase 3: "only on targets whose ceiling clears the baselines") still
  needs a home in `select.py`/`analysis.py`; flagging so it isn't assumed
  to already exist.

## Done

- `__WORK_IN_PROGRESS__/src/allostery/protocol.py` implemented: `LeakageError`,
  `ceiling_context()`/`frozen_context()` (stack-based, innermost-wins
  nesting, unguarded-by-default), `assert_readable()`, the three gated
  accessors, `ProtocolRoster` (DEV/FROZEN target-set bookkeeping), and
  `leave_one_protein_out()` (a plain, unguarded generator by design).
- `__WORK_IN_PROGRESS__/tests/test_protocol.py`: 21 tests, all passing.
  Full suite (`python3 .ai/tools/pytest_local.py wip-all`): 238 passed, 1
  pre-existing unrelated xpass, no regressions.
- All three Planned Validation items met: a FROZEN-context read of a
  held-out target's pocket label raises (`TestGatedAccessors::
  test_get_pocket_mask_raises_when_target_blocked` and the `superpose`/
  `functional_indices` equivalents); the same read succeeds inside a
  ceiling context (and unguarded, and for non-blocked targets); the LOPO
  generator yields every target exactly once as held-out over a full pass,
  with the train set always excluding it.
