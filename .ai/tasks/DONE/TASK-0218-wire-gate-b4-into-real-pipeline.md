# TASK-0218 Wire GATE-B4's permutation-leak detector into the real pipeline

## Context

- ID: TASK-0218
- Title: `diagnostics.detect_permutation_leak` (GATE-B4) is a real,
  tested, structurally-independent leak backstop — but as of
  [[TASK-0087]]'s check, it is exercised only by its own unit test
  (`test_diagnostics.py`), never called from `run_challenge.py`'s real
  end-to-end run. Wire it in.
- Status: Done
- Resolution: done
- Resolution Note: GATE-B4 wired into protocol.run_frozen_verdict as opt-in leak_check_n_perm; run_challenge.py opts in with N-tiered n_perm and treats detection as fatal. Demonstrated with a real live run and a monkeypatched synthetic leak end-to-end.
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

**Verdict: wired in as an opt-in parameter (`run_frozen_verdict`'s own
`leak_check_n_perm`), layer decided as `protocol.run_frozen_verdict`
itself (not a separate `run_challenge.py`-only check) so any future
caller of the library function gets the same guarantee, not just this
one script. `run_challenge.py`'s real pipeline opts in with an N-tiered
`n_perm` and treats a positive detection as a hard per-target failure.
Demonstrated end-to-end with a real, live run and a monkeypatched
synthetic leak, not just described.**

**Where**: `run_frozen_verdict`, not `run_challenge.py` alone — the
function already owns the winning candidate's scoring step
(`quantum_vs_classical`) and already runs inside its own
`frozen_context`; adding the check there means every current and future
caller of this library function (not only this one script) gets it for
free, opt-in via `leak_check_n_perm: int | None = None` (default `None`
= byte-identical to pre-TASK-0218 behavior, zero risk to any existing
caller/test).

**Real cost, measured before choosing anything (this task's own
Constraint)**: one `quantum_vs_classical` call timed at **0.37s on
KRAS_G12C** (N=169). Cost is dominated by `time_averaged_ctqw`'s own
eigendecomposition, `O(N^3)` — scaling that measurement to
CARDIAC_MYOSIN-size (N~950) implies **~66s for a single permutation**,
so `n_perm=200` (GATE-B4's own test-suite default) would cost minutes on
the smallest mandatory target and multiple hours on the largest. No
single `n_perm` works across this project's real target-size range — a
coarse, explicitly-stated tier by N instead
(`run_challenge.py::_leak_check_n_perm_for`): 30 at N<=250, 10 at
N<=500, 3 above that. Stated as a coarse choice, not a validated cost
model derived from more than one real measurement.

**Why a cached-occupancy shortcut would have tested nothing (a real
design trap avoided, not just a cost optimization skipped)**: `labels`
only ever reaches `analysis._metric_pack`, strictly downstream of
occupancy computation (checked by reading `quantum_vs_classical`'s own
source before designing anything) — so a scorer that closed over an
already-computed occupancy array and ignored its own `labels` argument
would be *provably* leak-free by construction of the wrapper itself,
regardless of what the real pipeline does, and could never catch a
future regression. The wired scorer re-invokes the real
`quantum_vs_classical(winner["H"], ...)` call for real, once per
permutation, specifically so a future change that *does* introduce a
labels-dependency would be caught empirically rather than assumed absent
forever from one static reading of today's source.

**Surfaced, not silently absorbed (this task's own "hard failure, not a
buried warning")**: `results["_leak_check"]`
(`auc_true`/`perm_mean`/`perm_ci`/`n_perm`/`threshold`/`leak_detected`) —
a first-class field, not a log line. `run_frozen_verdict` itself does not
raise on detection (a false positive at a real run's necessarily-reduced
`n_perm` should not unilaterally abort a shared library call from inside
itself); `run_challenge.py`'s own real pipeline does — a positive
detection raises `RuntimeError`, caught by `run_target`'s existing
per-target `except Exception` handler, which writes `error.txt` and
returns `{"ok": False}` — the target is never reported as a clean
success, reusing existing, already-tested error-handling infrastructure
rather than building new.

**Demonstrated three ways, not just one**:
1. `test_protocol.py::TestRunFrozenVerdictLeakCheck` (4 new tests) —
   default omits the key (regression safety); opted-in populates the
   expected shape; the real, honest pipeline is correctly *not* flagged;
   and (Planned Validation's own explicit requirement) a monkeypatched
   `analysis.quantum_vs_classical` that reads `labels` directly, wired
   through the real, unmodified `run_frozen_verdict` end to end, *is*
   flagged (`leak_detected=True`) — not `detect_permutation_leak` called
   standalone (`test_diagnostics.py` already covers that in isolation).
2. A real, live `run_challenge.run_target("KRAS_G12C", ...)` call (not a
   test double) — `_leak_check` populated in the real `verdict.json`,
   `leak_detected=False`, `perm_mean=0.484` (centered on chance, as
   expected for the honest pipeline), total added cost small (the whole
   frozen-verdict step, bench+ablation+scoring+30-permutation leak check,
   completed in 5.4s).
3. Full local suite re-run clean after every change: 1196 passed, 1
   skipped, 3 xfailed, 0 failed.

**Docstrings updated, not left describing the pre-TASK-0218 state**:
`diagnostics.py`'s own GATE-B4 module comment now states it is
operational (not just self-tested) and points here;
`run_frozen_verdict`'s own docstring carries the full cost/design
rationale above so a future reader does not have to re-derive it from
this task file.

Full diff: `src/allostery/protocol.py`, `src/allostery/diagnostics.py`
(docstring only), `scripts/run_challenge.py`,
`tests/test_protocol.py::TestRunFrozenVerdictLeakCheck`.
