# INV-0005 `t_max`/`n_steps`/`gamma` — `propagators.py`

## KNOB

| Parameter | Status | Characterization |
|---|---|---|
| `t_max` (`ground_state_relaxation`) | **KNOB-CHARACTERIZED** | `propagators.check_convergence(kind="ground_state_relaxation")` gives a closed-form adequacy criterion (`exp(-gap*t_max) <= tol`), grounded in the same exponential-convergence mechanism as classical power iteration / imaginary-time ground-state projection. `min_adequate_t_max` inverts it directly (`t* = -ln(tol)/gap`). Empirically verified on a synthetic size/gap battery (`scripts/propagator_convergence_battery.py`, [[TASK-0109]]): `empirical_t_max` vs `1/gap` fits a power law with exponent 1.092, R²=0.9943 — matches the analytic `O(1/gap)` prediction closely. **Not yet applied**: this project's real default `t_max=15.0` (`analysis.py`/`ceiling.py`/`run_challenge.py`) has never been checked against this criterion on real target data — [[TASK-0109]]'s own Out Of Scope explicitly defers "whether/how to change the default" to a follow-up. `REVIEW-panel-2026-07-16-v2.md` section 2.2 independently flags this as a live, load-bearing gap ("t_max=15 is hardcoded and applied to every operator regardless of its energy scale... a precondition for the physics, not hygiene"). |
| `t_max` (`time_averaged_ctqw`) | **KNOB-CHARACTERIZED, criterion fragile on near-degenerate spectra** | A *different* criterion from the row above (do not conflate — see `check_convergence`'s own docstring): the AAKV-style time-averaging-mixing bound (`2/(min_gap*t_max) <= tol`), derived from Aharonov-Ambainis-Kempe-Vazirani's Lemma 4.3 (quant-ph/0012090) and verified to genuinely upper-bound `time_averaged_ctqw`'s real numerical error on a small, non-degenerate synthetic case (`tests/test_propagator_convergence.py::TestLiteratureReproductionAAKV`). **Real, reported limitation** ([[TASK-0109]]'s own finding): this bound uses the smallest eigenvalue gap over *all* pairs, which is dominated by near-degenerate pairs the source barely couples to — on the ring-topology synthetic battery, `min_gap` shrinks ~1/N², making the bound's `t_max` prediction reach into the millions at N=500 and never empirically scannable within any practical battery run. The criterion is mathematically sound but practically unusable as stated on spectra with near-degenerate pairs; a source-overlap-weighted refinement is a real follow-up, not attempted here. |
| `n_steps` (`time_averaged_ctqw`) | **KNOB-CHARACTERIZED** | Nyquist-type bound (`check_convergence`'s `nyquist` check): sample spacing must resolve `H`'s full spectral bandwidth (`dt <= pi/bandwidth`). `min_adequate_n_steps` inverts it directly. Empirical battery finding ([[TASK-0109]]): `empirical_n_steps` vs bandwidth does **not** fit a clean power law (exponent -2.503, R²=0.786, **negative sign is counter to the naive Nyquist expectation** that more bandwidth needs more steps) — reported plainly per this project's own "state what's true, don't force a hypothesis" convention, not resolved. Worth a follow-up look, not explained by this task. |
| `gamma` (`haken_strobl`) | **OPEN** | Explicitly out of [[TASK-0109]]'s own scope: `gamma` interacts with `solve_ivp`'s `rtol`/`atol`, a different numerical-error source (ODE integration) than the eigendecomposition-based analytic propagators this task's criteria target. No characterization attempted. |

## GAUGE

Not assessed by this record — [[TASK-0109]]'s scope was KNOB-characterization
(does the *result* change adequately with these parameters, and how much is
"enough"), not a permutation/rotation gauge audit of `propagators.py`'s own
functions. `INV-0002`/`INV-0004` are the nearest existing gauge-audit precedent
for this codebase's propagation layer; neither covers `t_max`/`n_steps`
directly.

## SIGNAL

Not applicable — these are numerical-adequacy parameters (how long/how finely
to run a fixed physical computation), not a modeling choice that should or
shouldn't change a scored outcome. `INV-0004`'s own SIGNAL rows (for
`select.py`'s consumers of `time_averaged_ctqw`) are the relevant record for
that question.

## Status

**KNOB rows characterized, not yet applied to any real default.** Relates
directly to [[INV-0004]]'s own still-open KNOB row ("`t`/`t_max`/`n_steps`...
fed to `time_averaged_ctqw` inside `focusing`/`source_specificity`... not
characterized as a spread over a grid") — this record is `propagators.py`'s
own side of that same gap; `INV-0004`'s row can now point here rather than
stay a bare "OPEN," though `select.py`'s specific call sites are still
unaudited by either record.

## Provenance

Filed 2026-07-15 by [[TASK-0109]] (propagator convergence-validity check +
synthetic power-law characterization + literature grounding), per that task's
own TODO item ("Register in `.ai/invariants/` if this quantity fits that
registry's shape... flag as a candidate, decide at execution time"). Not a
completed GAUGE/SIGNAL audit — a KNOB-characterization record, the shape this
task's own findings actually produced.
