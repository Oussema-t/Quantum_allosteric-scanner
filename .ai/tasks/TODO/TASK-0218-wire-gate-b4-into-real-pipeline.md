# TASK-0218 Wire GATE-B4's permutation-leak detector into the real pipeline

## Context

- ID: TASK-0218
- Title: `diagnostics.detect_permutation_leak` (GATE-B4) is a real,
  tested, structurally-independent leak backstop — but as of
  [[TASK-0087]]'s check, it is exercised only by its own unit test
  (`test_diagnostics.py`), never called from `run_challenge.py`'s real
  end-to-end run. Wire it in.
- Status: TODO
- Owner: Implementer
- Source: [[TASK-0087]] (harden `protocol.py`'s firewall) — while
  deciding whether the cooperative gate needed hardening into a hard
  data-seal, checked directly (not assumed) whether GATE-B4 backstops the
  real pipeline as the module's own design intent implies. It doesn't,
  currently. Surfaced and filed per this project's own "an implementer
  surfaces, an orchestrating thread files" convention, not fixed inline
  (out of that task's own scope — it was deciding the gate's *design*,
  not deploying an unrelated detector).
- Priority: P2 — no live leak found (checked, [[TASK-0087]]'s Done
  section), so this closes a real gap between documented intent and
  operational reality, not an active bug.

## Why this matters

`allostery/diagnostics.py`'s own module comment names GATE-B4 as *the*
catch-all: "a leak is anything that keeps scoring above chance when the
labels are randomized. The permutation-null (GATE-B4) catches it
regardless of *where* the leak entered — labels.py, the objective, or a
frozen-param violation." [[TASK-0087]] leaned on this as part of its own
rationale for keeping `protocol.py`'s firewall cooperative rather than a
hard data-seal ("a structurally different backstop exists for exactly an
unforeseen leak vector"). That rationale is only as good as GATE-B4 being
real in the pipeline that actually ships results — checked, and it isn't
yet. Wiring it in converts a documented design intent into an operational
guarantee.

## Intent Contract

- Outcome: `run_challenge.py`'s real end-to-end run (or
  `protocol.run_frozen_verdict`, if that is the more appropriate layer —
  decide and record which) calls `diagnostics.detect_permutation_leak`
  against the winning candidate's own scorer, and a positive detection is
  a hard failure (raises or is surfaced as a first-class result field a
  caller cannot silently ignore), not a warning buried in logs.
- In Scope: the wiring decision (where in the real pipeline this runs —
  every target, every run, vs. a periodic/sampled check, given
  `n_perm=200` re-invocations of the full scorer is real added cost);
  updating `diagnostics.py`'s/`protocol.py`'s own docstrings once this is
  true, so [[TASK-0087]]'s "cited as available, not operational" caveat
  can be corrected to "operational" with a pointer to this task.
- Out Of Scope: changing GATE-B4's own `PERM_LEAK_THRESHOLD`/mechanism;
  redesigning `protocol.py`'s cooperative-gate decision ([[TASK-0087]]'s
  own scope, already decided).
- Constraints And Invariants: state the real compute-cost impact
  (`n_perm` full-scorer re-runs per call) before deciding the wiring
  granularity, per this project's own "measure before committing a
  number" convention — do not silently make every real run `n_perm`
  times more expensive without stating that trade explicitly.
- Planned Validation: a synthetic deliberately-leaky scorer wired through
  the same real call path this task adds, confirming detection actually
  fires end-to-end (not just in `test_diagnostics.py`'s own isolated
  unit test).

## Dependency

- [[TASK-0087]] (Done) — found and filed this gap.
- `allostery.diagnostics.detect_permutation_leak` (already exists, already
  tested — this task wires it in, does not build it).

## Done

—
