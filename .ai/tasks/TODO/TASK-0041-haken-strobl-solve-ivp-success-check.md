# TASK-0041 `haken_strobl` doesn't check `solve_ivp`'s success flag

## Context

- ID: TASK-0041
- Title: `propagators.haken_strobl` reads `sol.y[:, -1]` without checking
  `sol.success` — a failed/non-converged integration would silently return
  a possibly-wrong probability vector
- Status: TODO
- Owner: Implementer
- Source: review of all `Bartosz`/`bchmura`-authored commits, 2026-07-05
  session — Medium-severity finding #5
- Scope: `__WORK_IN_PROGRESS__/src/allostery/propagators.py::haken_strobl`

## ⚠️ Before implementing

**Do a short review before adding the check** — confirm this is actually
reachable in practice, not purely theoretical. `.claude/TASKS.md` T-002/
T-005 already test this function at `gamma ∈ {0.5, 2.0, 20.0}` (including
an explicit "Zeno regime" high-gamma case) and reportedly pass — run those
existing tests and try an even larger gamma / longer `t` to see whether
RK45 actually fails to converge anywhere in a realistic parameter range,
or whether this is a defensive gap that never actually triggers for the
gamma/t ranges this project uses. Either outcome is worth recording.

## Intent Contract

- Outcome: a failed ODE integration is surfaced (raised or clearly
  flagged), not silently returned as if it succeeded.
- In Scope:
  - check `sol.success` after `solve_ivp` returns; raise a clear error
    (or return a flagged result, depending on how this project's other
    "never silently wrong" conventions are phrased elsewhere — check
    `metrics.py`/`hamiltonians.py` for the existing house style before
    picking raise-vs-flag) naming the `gamma`/`t` that failed.
  - if the review above finds RK45 genuinely struggles at extreme
    gamma/t combinations relevant to this project's actual use (e.g. the
    "gamma→∞ gives classical diffusion" limit mentioned in the
    docstring), consider whether `method="Radau"` or `"BDF"` (implicit,
    stiff-aware) would be a better default — but only as a follow-up, not
    bundled into this fix, since changing the integrator changes numeric
    output and needs its own validation pass.
- Out Of Scope: changing the default integration method (see above) —
  this task only adds the missing success check.
- Constraints And Invariants: must not change `haken_strobl`'s existing
  passing-test outputs (T-002/T-005) — the check only fires on failure,
  which the current tests presumably don't hit.
- Planned Validation: re-run the existing gamma-sweep tests, confirm they
  still pass; construct one deliberately extreme case (very large gamma
  and/or t) to try to trigger a real `sol.success == False`, confirm the
  new check catches it if reachable.

## TODO

- [ ] Try to reproduce a real `solve_ivp` failure at extreme parameters
      (see callout) — record whether one was found.
- [ ] Add the `sol.success` check with a clear error message.
- [ ] Re-run existing gamma-sweep tests to confirm no regression.

## Dependency

- None.

## Open Questions

- Raise vs. return-with-flag — which matches this codebase's existing
  convention better? (`hamiltonians.py`/`clean.py` mostly raise on hard
  failures and warn on soft ones; a non-converged integration reads more
  like a hard failure than a warning, but confirm against house style
  rather than assuming.)

## Done

(not yet)
