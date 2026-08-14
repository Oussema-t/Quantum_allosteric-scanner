# TASK-0038 `clean.py` warns instead of raising on disconnected graphs, contradicting its own docstring

## Context

- ID: TASK-0038
- Title: module docstring states "disconnected graphs are an error";
  `_assert_connected` only appends a warning string and returns — never
  raises
- Status: Done
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

- [x] Determine intended behavior (see callout above — check callers,
      check `PLAN.md`'s Phase 0 gate intent). **Warn-only is correct** —
      see Done section.
- [x] Align docstring and implementation to match. Fixed the module
      docstring (implementation was already correct/intentional).
- [x] Add the disconnected-input regression test.
      `tests/test_clean.py::TestAssertConnectedIsWarnOnly` (3 cases).

## Dependency

- None.

## Open Questions

- Is disconnection meant to be caught inside `clean()` at all, or is that
  properly Phase 0a's job (`hamiltonians.py`'s nullspace test, per
  `.claude/TASKS.md` T-011's framing: "nullspace test doubles as the
  disconnection detector")? If the *real* gate lives downstream in the
  physics tests, `clean()`'s warning may be redundant-but-harmless early
  signal, and the module docstring should say so rather than claim
  ownership of the hard gate. **Resolved**: not `hamiltonians.py`
  specifically, but the same idea — the real hard gate is `superpose.py`'s
  ANM rigid-body-nullspace check (`anm_modes`'s helper), which raises
  `ValueError` on a disconnected contact graph, citing TASK-0005's
  original regression, independently of anything `clean()` does.
  `clean()`'s own warning is exactly the "redundant-but-harmless early
  signal" this question anticipated — now documented as such rather than
  as a hard guarantee `clean()` doesn't actually provide.

## Done

**2026-08-14, Implementer D.** Resolved as **(b): the module docstring
was wrong, the warn-only implementation was already the deliberate,
correct behavior** — not a bug to fix by making it raise.

Evidence gathered before picking a side, per this task's own "before
implementing" callout:
- `_assert_connected`'s own docstring already stated the real behavior
  plainly: "Warns rather than raises so callers can decide how to handle
  it" — an existing, explicit design statement, not an accidental gap.
- A real, hard-enforced gate for disconnected structures already exists
  **downstream, independently of `clean()`**: `superpose.py`'s ANM
  rigid-body-nullspace check (used by `anm_modes`) raises `ValueError`
  when `operator_diagnostics` finds the contact graph has more than one
  component, explicitly citing "TASK-0005's original disconnected-graph
  regression." Disconnection *is* a hard error in this pipeline — just
  not inside `clean()` itself.
- No current caller of `clean()`/`clean_from_config()` (searched
  `scripts/`, `src/allostery/`, `tests/`) reads `CleanResult.warnings`
  for the connectivity message specifically, or otherwise depends on
  `clean()` raising on disconnection. Changing warn-to-raise now would be
  a new, currently-unrequested breaking behavior change with no
  identified caller need — exactly the risk this task's own callout
  warned about checking first.
- `.ai/tasks/PLANS/PLAN.md` (cited in this task's own Context/Scope as
  the place needing reconciled "Phase 0 gate" language) **no longer
  exists in the repository** — confirmed via direct `ls`, not assumed.
  Nothing to reconcile there; that scope item is moot, superseded by this
  project's current `.ai/tasks/`+`RESULTS.md` workflow.

**Fix**: corrected `clean.py`'s module docstring (was: "The resulting Cα
graph must be connected; disconnected graphs are an error") to state the
actual, intentional behavior — warns via `CleanResult.warnings`, never
raises, and names exactly where the real hard gate lives
(`superpose.py`). Added a matching note to `_assert_connected`'s own
docstring cross-referencing this task and the module docstring. No
production code path changed — this was a documentation-matches-
behavior fix, not a behavior change, per the resolved direction.

**Regression test** (Constraint: synthetic disconnected coordinate set
fed through `clean()`'s connectivity check path):
`tests/test_clean.py::TestAssertConnectedIsWarnOnly` — two spatially
separated 4-point clusters (>1000 Å apart, unambiguously 2 components at
the default 10 Å cutoff): (1) does not raise, (2) appends exactly one
warning naming the PDB id and component count, (3) a connected control
input (sanity check on the fixture itself) appends no warning. 3/3 new
tests pass; full suite re-run before closing: 1185 passed, 1 skipped, 3
xfailed, 0 failed.

Artifacts: `src/allostery/clean.py` (module docstring +
`_assert_connected` docstring), `tests/test_clean.py`.
