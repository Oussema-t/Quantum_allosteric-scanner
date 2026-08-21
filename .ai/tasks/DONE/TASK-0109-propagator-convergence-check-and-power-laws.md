# TASK-0109 Propagator convergence-validity check + synthetic power-law characterization + literature grounding

## Context

- ID: TASK-0109
- Title: Build a reusable numerical-validity check for
  `time_averaged_ctqw`/`ground_state_relaxation`/`haken_strobl`'s
  `t_max`/`n_steps`/`gamma` parameters, characterize how the *minimum
  adequate* values scale with system size and spectral properties on
  synthetic systems (the user's explicit "so we know any power laws
  involved"), and ground the check in published CTQW/quantum-walk
  numerical-propagation literature rather than inventing a bespoke
  criterion from scratch.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-15 21:05
- Source: subtask of [[TASK-0108]], per explicit user request.
- Crit Ref: generalizes [[TASK-0102]]'s one-off manual check (BCR_ABL1's
  spectral gap = 0.430, `exp(-gap*t_max)=0.055` at `t_max=15`, done by
  hand for one target after the fact) into something applied
  automatically, before trusting any operator's output on any target.

## Intent Contract

- Outcome: (1) a function, e.g. `propagators.check_convergence(H, t_max,
  n_steps=None, gamma=None) -> ConvergenceReport`, following this
  module's existing `_warn_if_indefinite` pattern (warn by default,
  `strict=True` raises) rather than inventing a new error-handling
  convention; (2) a synthetic test suite that empirically finds the
  minimum adequate `t_max`/`n_steps` across a range of system sizes and
  spectral-gap/eigenvalue-spread conditions, and characterizes the
  scaling relationship (power law or otherwise — report whatever the
  data actually shows, do not assume a power law and force a fit to it);
  (3) at least one literature-sourced convergence criterion, reproduced
  on a case where it's known, as a sanity check on (1).
- In Scope:
  - **Nyquist-type check for `n_steps`**: `dt = t_max / n_steps` must
    resolve `H`'s fastest relevant oscillation — check `dt` against
    `H`'s eigenvalue range (`w.max() - w.min()`, already computed by
    `np.linalg.eigh` inside every propagator, cheap to expose). A
    standard criterion from time-dependent Schrödinger numerical
    propagation (see Literature below) gives a concrete bound to check
    against, not an arbitrary safety factor invented here.
  - **Spectral-gap check for `t_max`** (generalizes TASK-0102's method):
    for `ground_state_relaxation`, check `exp(-gap * t_max)` against a
    stated tolerance (e.g. TASK-0102's own `0.055`, or a literature value
    if one is found) to flag "this hasn't converged to the ground state
    yet, the seed still matters more than this function's own semantics
    claim." For `time_averaged_ctqw`, the relevant criterion is
    different (time-averaging convergence, not ground-state relaxation)
    — do not conflate the two; state the distinct criterion for each
    function explicitly.
  - **Synthetic power-law characterization**: build a battery of
    synthetic graphs varying (a) system size `N` (e.g. 20/50/100/200/500
    residues) and (b) spectral gap / eigenvalue spread (via controlled
    potential strength, reusing `TASK-0103`'s dumbbell-construction
    precedent for a reusable synthetic-network helper rather than a
    second copy). For each, find the empirically minimum `n_steps`/
    `t_max` that agrees with a much finer reference (e.g. 10x steps) to
    within a stated tolerance. Fit and report the scaling relationship
    (log-log regression for a power-law candidate; state the fitted
    exponent and R², and say plainly if the data does *not* look like a
    clean power law rather than forcing one).
  - **Literature grounding**: find at least one published, citable
    numerical criterion for either (a) time-step/step-count adequacy for
    coherent time-dependent Schrödinger propagation (e.g. Trotter-Suzuki
    step-size bounds, spectral/Chebyshev propagator error bounds — both
    well-established in the quantum dynamics numerics literature), or
    (b) CTQW/quantum-walk mixing-time results relating convergence time
    to spectral gap (e.g. the quantum walk mixing-time literature
    following Aharonov et al., or the original Farhi & Gutmann CTQW
    paper's own treatment of propagation time). Attempt to reproduce the
    cited criterion's prediction on a case from this task's own synthetic
    battery, not just cite it in prose.
- Out Of Scope:
  - real PDB data or network access — synthetic only, by this task's own
    design (matches [[TASK-0103]]'s "no PDB, no network access" precedent
    for exactly this kind of ground-truth-by-construction test).
  - the Optuna real-target scan — [[TASK-0110]].
  - changing the default `t_max=15.0`/`n_steps=500` used throughout
    `analysis.py`/`ceiling.py`/`run_challenge.py` — this task builds the
    check and characterizes the scaling; whether/how to change the
    defaults (per-target adaptive values, or a fixed conservative bound)
    is a follow-up decision once this task's findings exist, not this
    task's own call to make unilaterally.
- Constraints And Invariants:
  - reuse `np.linalg.eigh`'s already-computed eigenvalues where a
    propagator already decomposes `H` — do not re-decompose for the
    convergence check if the caller already has `w` available.
  - follow this module's existing warn/strict convention
    (`_warn_if_indefinite`) rather than inventing a second one.
- Planned Validation: the synthetic test suite itself, plus the
  literature-reproduction case. Report the actual fitted scaling
  relationship (or its absence) — this task's job is to find out what's
  true, not to confirm a hypothesis.

## In Progress

None

## TODO

- [ ] Implement `check_convergence` (or equivalent), Nyquist check +
      spectral-gap check, warn/strict per this module's convention.
- [ ] Build the synthetic system battery (size x spectral-gap grid).
- [ ] Empirically find minimum adequate `t_max`/`n_steps` per synthetic
      system; fit and report the scaling relationship.
- [ ] Find and cite a literature criterion; reproduce it on a synthetic
      case.
- [ ] Register in `.ai/invariants/` if this quantity fits that registry's
      shape (a KNOB/GAUGE classification for `t_max`/`n_steps` themselves,
      per `INVARIANCE_PROTOCOL.md` — flag as a candidate, decide at
      execution time whether it warrants its own `INV-XXXX` record).

## Dependency

- [[TASK-0102]] — the one-off precedent this generalizes.
- [[TASK-0103]] — reuse its synthetic-network construction helper rather
  than writing a second one, if applicable to this task's battery.
- Feeds [[TASK-0110]] (informs what parameter range to search).
- Feeds [[TASK-0117]] (`REVIEW-2026-07-15b-ceiling-search-methodology.md`
  finding #2) — once `check_convergence` exists, TASK-0117 applies it
  to `ceiling.consistency_score`'s fixed `t_max=15`/`n_steps=500`
  defaults, the values TASK-0046's real KRAS_G12C ceiling run (60
  trials, N=169) already used with no validity check. TASK-0117 is
  hard-blocked on this task landing first; do not treat its convergence
  criterion as informal or start TASK-0117 early on an ad hoc check.

## Open Questions

- None yet — scope is fully specified; specifics (which literature
  source, exact tolerance values) are this task's own job to determine,
  not pre-decided here.

## Done

**Note on this task's own Context/Crit Ref line above** ("BCR_ABL1's
spectral gap = 0.430... exp(-gap*t_max)=0.055"): checked directly against
[[TASK-0102]]'s actual Done section, which states gap=**0.1933**, not
0.430 -- `exp(-0.1933*15)=0.055` reproduces exactly; `exp(-0.430*15)
=0.0016` does not. This task's own filing had a transcription error in
the gap value (the 0.055 result itself was carried over correctly). Left
uncorrected above as the historical record of how this task was filed;
noted here rather than silently edited.

**(1) `propagators.check_convergence`** (`ConvergenceReport` dataclass):
three independent checks, each only meaningful for the propagator it
names (do not conflate, per this task's own Constraint) --
- **Nyquist** (`n_steps`, either propagator): sample spacing must resolve
  `H`'s full spectral bandwidth (`dt <= pi/bandwidth`) -- `time_averaged_
  ctqw` evaluates the *exact* closed-form `p(t)` at `n_steps` sampled
  points and Riemann-sums them; this is a genuine sampling-theorem
  requirement on that discrete sum, not an ODE time-stepping error (there
  is none here -- evolution is exact via `eigh`).
- **`kind="ground_state_relaxation"`**: `exp(-gap*t_max) <= tol` --
  generalizes [[TASK-0102]]'s one-off manual check into a callable
  function. Reproduces TASK-0102's own number exactly (regression-pinned,
  `test_propagator_convergence.py::TestCheckConvergenceSpectralGap::
  test_reproduces_task_0102_bcr_abl1_number`).
- **`kind="time_averaged_ctqw"`**: a *different* criterion (time-
  averaging convergence to the decoherent/infinite-time limit, not
  ground-state relaxation) -- `2/(min_gap*t_max) <= tol`, derived
  directly (elementary oscillatory-integral calculus) and grounded in
  Aharonov-Ambainis-Kempe-Vazirani's Lemma 4.3 (quant-ph/0012090, STOC
  2001) for the discrete-time walk's identical `1/(gap*T)` mixing
  mechanism -- verified against the real paper via direct fetch (not
  taken on a search summary's word), see this section's own Literature
  Grounding subsection below.
- Follows this module's existing `_warn_if_indefinite` warn/strict
  convention exactly, per this task's own Constraint (no second
  error-handling convention invented).
- `gamma` accepted for signature symmetry with `haken_strobl` but has no
  dedicated check (interacts with `solve_ivp`'s own `rtol`/`atol`, a
  different numerical-error source than the eigendecomposition-based
  analytic propagators this task targets) -- explicit, not silent, scope
  cut.

**(2) `min_adequate_t_max`/`min_adequate_n_steps`** -- prescriptive
companions, not in this task's original Outcome spec but added after
reading `REVIEW-panel-2026-07-16-v2.md` section 2.2 mid-task: that review
independently names TASK-0108/0109/0110 "a precondition for the physics,
not hygiene" and recommends exactly `t* ~ 1/dlambda` (the graph mixing
time) as the fix for `t_max=15`'s hardcoded, energy-scale-blind default.
Both `min_adequate_*` functions are closed-form inversions of `check_
convergence`'s own criteria (`t* = -ln(tol)/gap`, `t* = 2/(min_gap*tol)`,
`n* = ceil(t_max*bandwidth/pi)+1`) -- a caller does not have to hand-
derive the inverse of this module's own formula. Does not change any
existing default (`t_max=15.0` untouched everywhere), per this task's own
Out Of Scope -- applying the prescription anywhere is a separate,
follow-up decision.

**(3) `build_gapped_synthetic_network(N, well_depth, seed)`** -- ring +
random-chord weighted graph with an optional single-node trap controlling
the spectral gap independent of `N`. Reuses [[TASK-0103]]'s own
randomization precedent (rng-seeded edge weights in `[0.7, 1.3]`, not a
bare unweighted graph -- that module's own regression guard against
silently-identical "different" seeds) rather than force-reusing its fixed
44-node two-lobe topology, which does not parametrize by `N`.

**(4) Empirical size/gap battery** (`scripts/propagator_convergence_
battery.py`, N in {20,50,100,200,500} x well_depth in {0,2,10,50} = 20
cells):

- Found and fixed a real performance bug in this script's own first
  version, before any real run: `time_averaged_ctqw` has no internal
  vectorized time axis (a Python loop per sample), so naively calling it
  once per scanned `(t_max, n_steps)` candidate re-runs that loop from
  scratch every time -- `O(candidates x n_steps_each)`. First run killed
  after 25+ minutes with N=500 not yet complete. Fixed by batching every
  needed time point for a whole scan into one `(M, N) @ (N, N)` matmul
  (`_vectorized_ctqw_batch`, exact reproduction of `time_averaged_ctqw`'s
  own `linspace` definition, not an approximation) -- full 20-cell battery
  now completes in ~7.5s.
- Found and fixed a real bug in this script's own ground-truth reference,
  caught because it produced an impossible-looking result (total-
  variation distance *plateauing* around 0.31 instead of decaying to 0 as
  `t` grew, for every `well_depth=2.0` row): `_true_ground_state_density`
  used `v[:,0]**2` (always non-negative) as `ground_state_relaxation`'s
  `t->infinity` limit -- wrong whenever `<v_0|p0>`'s sign is negative,
  since the real propagator clips its output to non-negative *before*
  renormalizing, which keeps a different half of the eigenvector than
  squaring would. Verified directly (`ground_state_relaxation(H, t=1000)`
  vs both candidate references: TV=0.31 against the wrong one, TV=7e-17
  against the corrected one) before trusting the fix.
- Found a real, structural blowup in the `time_averaged_ctqw` criterion
  itself, not a code bug: `min_gap` (smallest eigenvalue gap over *all*
  pairs) shrinks ~1/N^2 for this ring construction's near-degenerate
  pairs (measured 5.2e-2 at N=20 down to 1.3e-4 at N=500), making the
  naive AAKV-bound-derived `t_max` prediction reach into the hundreds of
  thousands to millions for N>=100 -- **every single one of the 20 cells'
  `empirical_t_max_ctqw` came back `None`** (analytic prediction exceeds
  any practical scan range, `T_MAX_SCAN_CAP=3000`). This is a real,
  reported finding about the naive form of this criterion's fragility on
  near-degenerate spectra (most of that minimum gap sits between
  eigenmode pairs the propagation source barely overlaps, which the naive
  min-over-all-pairs bound does not weight down) -- addressed separately,
  see (5) below, not swept under the rug.
- **Power-law fits** (log-log regression, this task's own Planned
  Validation: "find out what's true, not confirm a hypothesis"):
  - `empirical_t_max_gsr` vs `1/gap`: **exponent=1.092, R²=0.9943** --
    clean power law, closely matching the analytic `O(1/gap)` prediction
    (not exactly 1.0 since the empirical criterion, total-variation
    distance to the true ground state, differs slightly from the analytic
    one, relative first-excited-state weight).
  - `empirical_t_max_ctqw` vs `1/min_gap`: **could not be fit** -- every
    value is `None`, per the structural finding above.
  - `empirical_n_steps` vs bandwidth: **exponent=-2.503, R²=0.786 -- NOT
    a clean power law, and the sign is counter to the naive Nyquist
    expectation** (more bandwidth should need *more* steps, not fewer).
    Reported plainly, not explained -- a real follow-up question, not
    resolved by this task.
  Full table + fits: `results/tasks/0109/report.md`/`convergence_battery.json`.

**(5) Literature grounding + reproduction** -- since the battery's own
ring topology cannot practically exercise the `time_averaged_ctqw`/AAKV
criterion (finding above), built a dedicated small (N=10, N=8) generic
random-symmetric synthetic `H` (non-degenerate spectrum by construction)
specifically for this requirement
(`test_propagator_convergence.py::TestLiteratureReproductionAAKV`,
permanent regression test, not just an exploratory check):
- Verified via direct `WebFetch` against the actual paper (not a search
  summary) that Aharonov-Ambainis-Kempe-Vazirani, "Quantum Walks on
  Graphs" (STOC 2001, quant-ph/0012090), Lemma 4.3 states `||P_bar_T -
  pi|| <= 2 sum_{i,j: lambda_i!=lambda_j} |a_i|^2/(T|lambda_i-lambda_j|)`
  for the discrete-time walk's time-averaged distribution.
  `check_convergence`'s continuous-time analog (`2/(min_gap*T)`) is
  derived directly from the same oscillatory-cross-term mechanism
  (elementary calculus: `(1/T)*integral_0^T exp(-i*dw*t)dt`, magnitude
  `<=2/(|dw|*T)`), grounded in, not copied from, AAKV's result.
- **Reproduced on real (synthetic) data**: the bound genuinely upper-
  bounds `time_averaged_ctqw`'s actual numerical error against the true
  closed-form infinite-time limit at every `T` tested (1 to 100), and
  both the real error and the predicted ceiling decay with `T` as
  expected (not just "always an upper bound," which a trivially-loose
  bound could satisfy trivially).
- Second, standard grounding for the `ground_state_relaxation` criterion
  (exponential convergence set by the spectral gap): the same mechanism
  as classical power-iteration convergence (dominant/subdominant
  eigenvalue ratio) and imaginary-time ground-state projection in
  quantum chemistry -- confirmed via web search against multiple real
  sources (general mechanism corroborated, no single paper's exact
  formula independently pinned down the way AAKV's was via direct fetch,
  since the formula itself is elementary eigenbasis-expansion algebra,
  not a result requiring external derivation).

**(6) `INV-0005-propagator-time-parameters.md`** filed -- KNOB-
characterization record for `t_max`/`n_steps`/`gamma`, cross-linked from
[[INV-0004]]'s own previously-`OPEN` `t`/`t_max`/`n_steps` row (that row's
own call sites, `select.py`'s `focusing`/`source_specificity`, remain
unaudited by either record -- a tool now exists to answer it, the audit
itself is not this task's job).

**Full local test suite**: `tests/test_propagator_convergence.py` (25
tests, new) + `tests/test_propagators.py`/`test_analysis.py`/
`test_diagnostics.py`/`test_run_challenge.py`/
`test_dumbbell_negative_control.py` (133 total across all touched/
adjacent files) -- all green.

**Not attempted, explicitly out of this task's own scope**: changing
`analysis.py`/`ceiling.py`/`run_challenge.py`'s real `t_max=15.0`/
`n_steps=500` defaults anywhere. `REVIEW-panel-2026-07-16-v2.md` P0#2
recommends exactly this as the next step ("set `t*` per operator from
its spectral gap... re-run the operator comparison") -- this task
supplies the tool (`min_adequate_t_max`, closed-form, ready to call); a
follow-up task's job is to actually apply it to a real target and
re-run, a decision this task does not make unilaterally.
