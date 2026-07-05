# TASK-0038 `clean.py` warns instead of raising on disconnected graphs, contradicting its own docstring

## Context

- ID: TASK-0038
- Title: module docstring states "disconnected graphs are an error";
  `_assert_connected` only appends a warning string and returns — never
  raises
- Status: TODO
- Owner: Implementer
- Source: review of all `Bartosz`/`bchmura`-authored commits, 2026-07-05
  session — High-severity finding #2
- Scope: `__WORK_IN_PROGRESS__/src/allostery/clean.py::_assert_connected`,
  its docstring, and `.ai/tasks/PLANS/PLAN.md`'s Phase 0 gate language

## ⚠️ Before implementing

**Do a short review before picking a side.** This could resolve either
way: (a) the module docstring is right and the code needs to actually
raise (matching `PLAN.md`'s Phase 0 gate: "no disconnected graphs"), or
(b) warn-not-raise was a deliberate softening (e.g. so a single bad chain
break doesn't kill an entire clean-up run before quality metadata can be
inspected) and the docstring is what's wrong. Check whether any caller of
`clean()` currently depends on getting a `CleanResult` back even for a
disconnected structure (e.g. to report/quarantine it) before deciding —
changing warn-to-raise could break a caller that expects a graceful
degrade.

## Intent Contract

- Outcome: the module docstring's stated guarantee and the actual
  behavior agree — whichever one is correct, not left contradicting each
  other.
- In Scope:
  - if raising is correct: change `_assert_connected` to raise (e.g. a
    dedicated `DisconnectedGraphError` or `ValueError`) when
    `n_comp != 1`, update `clean()`'s docstring/callers accordingly, and
    make sure `clean_from_config`'s quarantine-warning path (which
    already handles a *different* kind of "bad target" via
    `cfg.get("quarantine")`) isn't the only place disconnected structures
    should be caught — this is a structural property of the cleaned
    coordinates, not a per-target curation flag.
  - if warn-only is correct: fix the module docstring (line 13) to say
    so plainly, and remove any language elsewhere (`PLAN.md`'s Phase 0
    gate) implying disconnection is a hard reject, or clarify that the
    *gate* (a separate, later check) is what enforces it, not `clean()`
    itself.
- Out Of Scope: changing the actual connectivity *test* (nullspace/
  connected-components logic) — this task is about the contract
  (warn vs. raise), not the detection method.
- Constraints And Invariants: whichever direction is chosen, add a test
  exercising it directly — a synthetic disconnected coordinate set (two
  separated clusters) fed through `clean()`'s connectivity check path.
- Planned Validation: construct a synthetic disconnected input, confirm
  the chosen behavior (raise, or warn-and-continue) actually happens, and
  that `warn_list`/exception message clearly names the problem.

## TODO

- [ ] Determine intended behavior (see callout above — check callers,
      check `PLAN.md`'s Phase 0 gate intent).
- [ ] Align docstring and implementation to match.
- [ ] Add the disconnected-input regression test.

## Dependency

- None.

## Open Questions

- Is disconnection meant to be caught inside `clean()` at all, or is that
  properly Phase 0a's job (`hamiltonians.py`'s nullspace test, per
  `.claude/TASKS.md` T-011's framing: "nullspace test doubles as the
  disconnection detector")? If the *real* gate lives downstream in the
  physics tests, `clean()`'s warning may be redundant-but-harmless early
  signal, and the module docstring should say so rather than claim
  ownership of the hard gate.

## Done

(not yet)
