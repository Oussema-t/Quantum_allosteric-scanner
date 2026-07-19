# TASK-0041 `haken_strobl` doesn't check `solve_ivp`'s success flag

## Context

- ID: TASK-0041
- Title: `propagators.haken_strobl` reads `sol.y[:, -1]` without checking
  `sol.success` — a failed/non-converged integration would silently return
  a possibly-wrong probability vector
- Status: Done
- Resolution: done
- Owner: Implementer
- Claimed By: Implementer C (this thread)
- Claimed At: 2026-07-19 18:03
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

- [x] Try to reproduce a real `solve_ivp` failure at extreme parameters
      (see callout) — record whether one was found.
- [x] Add the `sol.success` check with a clear error message.
- [x] Re-run existing gamma-sweep tests to confirm no regression.

## Dependency

- None.

## Open Questions

- **Resolved**: raise, not flag. Surveyed `hamiltonians.py`/`clean.py`/
  `propagators.py` itself directly — `raise ValueError(...)` is the
  dominant pattern for hard/unrecoverable failures (bad weight scheme,
  unparseable PDB, empty structure, degenerate spectral gap, etc.);
  `warnings.warn` is reserved for known/expected soft conditions with a
  `strict` opt-in to escalate (e.g. `_warn_if_indefinite` — H_new being
  indefinite is a *designed* property, not a failure). A non-converged
  ODE integration has no valid physical fallback to warn-and-continue
  with — `sol.y[:, -1]` at that point is meaningless, not merely
  suboptimal — so it belongs with the hard-failure group. Used
  `RuntimeError` specifically (not `ValueError`, since the inputs
  themselves aren't invalid — the *numerical procedure* failed on
  otherwise-valid inputs, matching this module's own existing
  `RuntimeError` usage for a different but analogous case,
  `ceiling_search`'s "every trial produced NaN" failure).

## Done

**Before implementing (per this task's own callout): checked whether
RK45 genuinely fails anywhere in this project's real gamma/t range,
not just in theory.**

- Existing `T-002`/`T-005` gamma-sweep tests (`gamma ∈ {0.5, 2.0, 20.0}`,
  including the "Zeno regime" high-gamma case) re-ran clean, all pass.
- Tested well past that range with real, timed `solve_ivp` calls
  (5-residue path graph, same fixture the existing tests use):
  `gamma=100` (`analysis.dephasing_sweep`'s own `DEFAULT_GAMMAS =
  np.logspace(-4, 2, 8)` ceiling — the project's actual real-world
  maximum) succeeds in 0.27s. `gamma=1000` still succeeds but costs 13s
  (`nfev=105,764` — disproportionate slowdown vs. `gamma=100`, a classic
  stiffness signature under an explicit, non-stiff-aware method).
  `gamma=10,000` (t shortened to 10 to compensate) did not complete
  within a 20s timeout — genuinely impractically slow, not a clean
  `sol.success=False`. Confirmed via `ps`/CPU-time (not just wall-clock
  presence, this session's own established discipline per
  [[TASK-0135]]/P-0005) that the process was actively computing, not
  hung/stuck — RK45 is taking an enormous number of genuinely-executed
  tiny steps to resolve the stiffness, not stalled.
  Also tried a deliberately pathological `H` containing `np.inf` (to
  force NaN propagation into the RHS) — this also degrades to
  impractical slowness rather than a fast, clean `success=False`.
- **Checked whether the project's real call sites ever approach the
  range where this matters**: `analysis.dephasing_sweep`'s own
  `DEFAULT_GAMMAS` tops out at 100 (confirmed fast, above);
  `analysis.coherence_sensitivity`'s `gamma_scale * multipliers` caps
  at `multipliers=2.0` against a calibrated, physically-scaled
  `gamma_scale` — nowhere near the 1000+ range where RK45 starts to
  struggle. `scripts/enaqt_gamma_sweep.py`'s own per-target gamma grids
  (`np.logspace(-4, 2, ...)`) match the same ceiling.
- **Conclusion, stated directly per this task's own "either outcome is
  worth recording" framing**: RK45 does **not** fail (nor even get
  meaningfully slow) anywhere in this project's actual, real gamma
  range. It does become impractically slow — not incorrect, no
  `sol.success=False` observed even under extreme stress — starting
  somewhere between `gamma=1000` and `gamma=10,000`, roughly 10-100x
  beyond anything any real call site in this codebase requests. **The
  `sol.success` check is a genuinely defensive gap, not a live bug** —
  matches the task's own "confirm this is actually reachable in
  practice, not purely theoretical" framing exactly; it is not
  presently reachable, but costs nothing to guard against.

**Fix**: added `if not sol.success: raise RuntimeError(...)` immediately
after the `solve_ivp` call in `propagators.haken_strobl`, before
`sol.y[:, -1]` is read — the error message names `gamma`, `t`,
`sol.status`, and `sol.message` so a real failure (if one is ever hit
in a call this task's own review didn't anticipate) is immediately
diagnosable, not just "something went wrong." Docstring's `Returns`
section extended with a `Raises` note stating both the guarantee and
this task's own empirical finding about where it does/doesn't trigger,
so a future reader doesn't have to re-derive the same investigation.

**Out of scope, confirmed left alone**: did not change the default
integration method (`RK45` → `Radau`/`BDF`) — per this task's own
Constraints, and per the finding above, not motivated by anything this
project's real usage actually hits. Flagging for the record in case a
future gamma range expands: `Radau`/`BDF` (implicit, stiff-aware) would
likely help at the `gamma>=1000` range found here, but changing the
integrator changes numeric output and needs its own validation pass —
exactly the follow-up this task's own text anticipated, still not
bundled in.

**Test coverage**: `tests/test_physics.py` —
`test_haken_strobl_realistic_gamma_range_converges` (gamma=100 succeeds,
pins the real-range finding above as a regression test, not just a
one-off manual check) and
`test_haken_strobl_raises_on_failed_integration` (mocks `solve_ivp` to
return a `success=False` result, since a genuine failure proved
impractical to trigger with real physical parameters within any
reasonable wall-clock budget — confirms the new check actually fires
and raises `RuntimeError` with "did not converge" in the message).
Existing `test_haken_strobl_steady_state`/`test_haken_strobl_trace`
(`T-002`/`T-005`) re-ran unmodified and pass — the check only fires on
failure, which these don't hit, matching this task's own Constraint.
Full suite: 738 passed, 0 failed (`../.venv/bin/python -m pytest tests/
-q -k "not real_target and not real_run and not fetch and not
kras_g12c_real"`).
