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
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
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

## Open Questions

- None yet — scope is fully specified; specifics (which literature
  source, exact tolerance values) are this task's own job to determine,
  not pre-decided here.

## Done

(not yet)
