"""TASK-0110 -- Optuna-based scan of CTQW's *numerical* parameters
(`t_max`, `n_steps`) on real mandatory targets: an apo-only scan
establishing a "floor" and a holo-informed scan establishing a
"ceiling," per explicit user request ("Apo scan => floor. Holo scan =>
ceiling.").

Distinct from `ceiling.py` (TASK-0046, `H_new`'s *physical* potential-
weight DOF) -- this module never touches `lam_B`/`lam_T`/.../`alpha`/
`cutoff`; `H` is fixed input here, built once per target outside any
Optuna trial. Kept as its own module for the same DEV/FROZEN module-
boundary reason `ceiling.py` is separate from `analysis.py`.

Interpretation of "floor"/"ceiling" (TASK-0110's own Intent Contract,
stated explicitly rather than silently assumed):

- **floor**: an apo-only scan, *no pocket-label ground truth read at
  all* -- objective = `propagators.check_convergence`'s (TASK-0109)
  convergence-quality criterion. Finds the cheapest `(t_max, n_steps)`
  that still numerically converges, i.e. the honest non-cheating
  parameter choice a real deployment (no answer key) could actually use.
- **ceiling**: a holo-informed scan, objective = real AUC against
  `labels.build_labels`'s pocket -- the same diagnostic-ceiling concept
  as `ceiling.py`, on the numerical-parameter axis instead of `H_new`'s
  physical one. Wrapped in `protocol.ceiling_context()` (TASK-0046's own
  precedent), Tier-1 diagnostic only (TASK-0100) -- never wired into
  `run_challenge.py`'s live defaults by this module.

**Search parameterization -- `t_max` + oversample margin, not independent
`(t_max, n_steps)`.** An earlier version of this module searched
`n_steps` independently of `t_max` over a wide log-uniform range; testing
against a real spectrum showed this rarely finds the jointly-valid region
by chance within a practical trial budget, because `check_convergence`'s
Nyquist bound on `n_steps` scales *linearly with t_max* (a larger `t_max`
needs proportionally more samples) -- independent sampling wastes most
trials on a `t_max` that would converge paired with the "wrong" `n_steps`
sampled alongside it. Since `propagators.min_adequate_n_steps` already
gives the *exact* minimum `n_steps` for any given `t_max` in closed form
(TASK-0109), there is nothing to search on that axis: this module derives
`n_steps = ceil(min_adequate_n_steps(t_max) * oversample)` and searches
only `t_max` (the physically meaningful free parameter, subject to the
gap-based criterion) and `oversample` (a small safety margin above the
Nyquist minimum, `>= 1.0`). This is not a simplification of the task's
scope (`t_max`/`n_steps` are still both varied, per the Intent Contract)
-- it is searching the same two-dimensional space through a
reparameterization that respects the known analytic relationship between
them, exactly the kind of thing an "informed range" (the task's own
phrase, re: TASK-0109) should also mean for the search *parameterization*,
not just its bounds.

Both scans hold `H` fixed and vary only propagation-time parameters --
`H`'s `eigh` decomposition is the dominant per-trial cost either way
(Optuna's TPE sampler evaluates the objective as a black box, so there is
no way to precompute it once and reuse it across trials without reaching
around `propagators.py`'s own "never called directly outside this
module" boundary on its cached-eigh internals; accepted here as the
real, measured per-trial cost rather than optimized around).
"""
from __future__ import annotations

from typing import Optional

import numpy as np

_UNCONVERGED_PENALTY_FACTOR = 1.0e3
_DEFAULT_OVERSAMPLE_RANGE = (1.0, 3.0)

# Fallback only -- used solely when an adaptive range can't be derived
# (e.g. a degenerate/zero-gap spectrum, see `_adaptive_t_max_range`). Not
# used for any real target in practice; real ranges are always anchored
# on that target's own `min_adequate_t_max`, per REVIEW-panel-2026-07-16-v2
# §2.2/§5 P0#2 ("t_max=15 is hardcoded... 100x too short... set t* per
# operator from its spectral gap") -- a fixed guessed range risks never
# bracketing the true converged region for a real, small-spectral-gap
# `H_new`, which would make the whole floor scan vacuous (every trial
# penalised, "best" cost meaningless).
_FALLBACK_T_MAX_RANGE = (1.0, 60.0)


def _quiet_optuna():
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    return optuna


def _adaptive_t_max_range(w: np.ndarray, *, kind: str, tol: float, span_lo: float = 0.5, span_hi: float = 20.0):
    """Derive a `t_max` search range from `H`'s own spectrum via
    TASK-0109's closed-form `min_adequate_t_max`, instead of a fixed
    guessed constant -- brackets `[span_lo, span_hi] x prescribed_value`
    around the actual analytically-adequate point for *this* `H`.
    `span_lo=0.5` (not lower) deliberately keeps most of the range at or
    above the prescribed minimum, since `t_max` below it can never
    converge regardless of `n_steps` -- the search should mostly explore
    "how close to the true minimum can Optuna get," not waste budget deep
    in the guaranteed-unconverged region.

    Falls back to a fixed wide range only if the prescription is
    infinite (degenerate/zero-gap spectrum, in which case no finite
    `t_max` converges by this criterion anyway -- the scan will
    correctly report every trial as unconverged)."""
    from .propagators import min_adequate_t_max

    t_star = min_adequate_t_max(w=w, kind=kind, tol=tol)
    if not np.isfinite(t_star):
        return _FALLBACK_T_MAX_RANGE
    return (max(t_star * span_lo, 1e-6), t_star * span_hi)


def apo_floor_scan(
    H: np.ndarray,
    *,
    kind: str = "time_averaged_ctqw",
    tol: float = 1e-2,
    t_max_range: Optional[tuple] = None,
    oversample_range: tuple = _DEFAULT_OVERSAMPLE_RANGE,
    n_trials: int = 50,
    seed: int = 7,
):
    """Apo-only ("floor") scan: minimize a compute-cost proxy
    (`t_max * n_steps`) subject to `propagators.check_convergence`'s
    criterion for `kind` -- no pocket label, no holo, read anywhere in
    this function. A trial that fails convergence is penalised (cost +
    a large constant), not rejected/pruned -- Optuna's TPE sampler
    still learns from *how much* it failed by, which converges faster
    than a hard reject that gives the sampler no gradient information.

    Searches `t_max` (log-uniform) and `oversample` (linear, `>= 1.0`);
    `n_steps` is derived as `ceil(min_adequate_n_steps(t_max) *
    oversample)`, guaranteeing the Nyquist criterion is satisfied by
    construction so the search only has to find where the *gap-based*
    criterion holds (module docstring explains why searching `n_steps`
    independently doesn't work in practice).

    `t_max_range` defaults to `None` -- derived from *this* `H`'s own
    spectrum via `_adaptive_t_max_range` (TASK-0109's closed-form
    prescription) when omitted. Pass an explicit range to override.

    `kind="time_averaged_ctqw"` (default) matches this pipeline's actual
    headline propagator (`analysis.benchmark`/`ceiling.consistency_score`
    /`run_challenge.py` all score via `time_averaged_ctqw`, never
    `ground_state_relaxation`, for the primary reported AUCs) --
    `kind="ground_state_relaxation"` is available for the BCR_ABL1-style
    secondary metric but is not this function's default.

    Returns the `optuna.Study` (direction="minimize") -- `study.best_
    trial`/`study.trials_dataframe()` give the best cost + full history,
    per this task's own Planned Validation ("not just a single best-value
    summary"). Each trial's `user_attrs` carries `"converged"` and the
    derived `"n_steps"` (not a search parameter, so not in `best_params`).
    """
    from .propagators import check_convergence, min_adequate_n_steps

    optuna = _quiet_optuna()
    w = np.linalg.eigvalsh(H)
    if t_max_range is None:
        t_max_range = _adaptive_t_max_range(w, kind=kind, tol=tol)

    # The penalty must exceed the *worst-case valid cost anywhere in the
    # search range*, not just some fixed constant -- a real target's own
    # converged cost (t_max * n_steps) can itself be in the millions (a
    # small spectral gap forces a large t_max, which forces a large
    # n_steps to match), so a fixed additive penalty like `+1e6` can be
    # smaller than a legitimately-converged trial's own cost, letting an
    # *unconverged* trial with a small base cost numerically outscore a
    # converged one (found by direct testing, not assumed). Anchoring the
    # penalty on this range's own worst-case valid cost keeps it correct
    # regardless of the target's absolute spectral scale.
    worst_case_n_steps = min_adequate_n_steps(w=w, t_max=t_max_range[1])
    worst_case_valid_cost = t_max_range[1] * worst_case_n_steps * oversample_range[1]
    penalty = worst_case_valid_cost * _UNCONVERGED_PENALTY_FACTOR

    def objective(trial):
        t_max = trial.suggest_float("t_max", *t_max_range, log=True)
        oversample = trial.suggest_float("oversample", *oversample_range)
        n_steps = max(int(np.ceil(min_adequate_n_steps(w=w, t_max=t_max) * oversample)), 2)
        report = check_convergence(w=w, t_max=t_max, n_steps=n_steps, kind=kind, tol=tol)
        cost = t_max * n_steps
        trial.set_user_attr("converged", bool(report.ok))
        trial.set_user_attr("n_steps", n_steps)
        return cost if report.ok else cost + penalty

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.set_user_attr("t_max_range", list(t_max_range))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return study


_DEFAULT_MAX_N_STEPS = 20_000


def holo_ceiling_scan(
    H: np.ndarray,
    source,
    pocket_labels: np.ndarray,
    *,
    kind: str = "time_averaged_ctqw",
    tol: float = 1e-2,
    t_max_range: Optional[tuple] = None,
    oversample_range: tuple = _DEFAULT_OVERSAMPLE_RANGE,
    max_n_steps: int = _DEFAULT_MAX_N_STEPS,
    n_trials: int = 50,
    seed: int = 7,
):
    """Holo-informed ("ceiling") scan: maximize real AUC against
    `pocket_labels`, over `(t_max, n_steps)`, `H` fixed -- the same
    diagnostic-ceiling concept as `ceiling.ceiling_search` (TASK-0046),
    applied to CTQW's numerical parameters instead of `H_new`'s physical
    potential-weight DOF. Wrapped in `protocol.ceiling_context()`, since
    this reads real ground truth on every trial (TASK-0046's own
    precedent for exactly this kind of label-using diagnostic search).

    Same `t_max` + `oversample` -> derived-`n_steps` parameterization as
    `apo_floor_scan` (module docstring) -- here the derived `n_steps`
    only guarantees Nyquist-adequate *sampling*, it does not force AUC-
    relevant convergence (that's an empirical question this scan answers
    by searching `t_max` against real labels, not assumed).

    **`max_n_steps` (new, found necessary by direct measurement, not
    assumed in advance):** `time_averaged_ctqw` evaluates its time grid
    in an explicit Python loop, O(n_steps) wall-clock cost with no way to
    vectorize across `t` without changing that function itself (out of
    this task's scope). For a real target's small `time_averaged_ctqw`
    spectral gap, the Nyquist-adequate `n_steps` at the gap-prescribed
    `t_max` can be in the *millions* (measured directly on real
    KRAS_G12C: closed-form `t_max~4.8e6`, `n_steps~1.3e7` -- a single
    `time_averaged_ctqw` call at that point did not return in 2+ hours,
    confirmed by direct measurement before this cap was added, not
    assumed). `n_steps` is therefore clamped to `max_n_steps` -- a trial
    whose *un-clamped* derived `n_steps` would exceed it is marked
    `"n_steps_capped": True` and scored on the clamped (necessarily
    under-sampled, per Nyquist) value; this is reported explicitly as a
    computational-feasibility finding in its own right (module docstring
    of the driver script), not silently substituted for a "real" answer.

    `t_max_range` defaults to the same spectrum-derived range
    `apo_floor_scan` uses -- the ceiling scan should search the region
    where convergence is at least *possible*, not an arbitrary fixed
    window that might sit entirely in the unconverged regime for this
    target's real spectral gap.

    Returns the `optuna.Study` (direction="maximize"). Each trial's
    `user_attrs` carries the derived `"n_steps"` and `"n_steps_capped"`.
    """
    from .metrics import auc as auc_fn
    from .propagators import min_adequate_n_steps, time_averaged_ctqw
    from .protocol import ceiling_context

    optuna = _quiet_optuna()
    y = np.asarray(pocket_labels).astype(int)
    w = np.linalg.eigvalsh(H)
    if t_max_range is None:
        t_max_range = _adaptive_t_max_range(w, kind=kind, tol=tol)

    def objective(trial):
        t_max = trial.suggest_float("t_max", *t_max_range, log=True)
        oversample = trial.suggest_float("oversample", *oversample_range)
        n_steps_needed = max(int(np.ceil(min_adequate_n_steps(w=w, t_max=t_max) * oversample)), 2)
        capped = n_steps_needed > max_n_steps
        n_steps = min(n_steps_needed, max_n_steps)
        trial.set_user_attr("n_steps", n_steps)
        trial.set_user_attr("n_steps_capped", capped)
        occ = time_averaged_ctqw(H, t_max, source=source, n_steps=n_steps)
        return float(auc_fn(occ, y))

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.set_user_attr("t_max_range", list(t_max_range))
    study.set_user_attr("max_n_steps", max_n_steps)
    with ceiling_context():
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return study


def closed_form_prescription(H: np.ndarray, *, kind: str = "time_averaged_ctqw", tol: float = 1e-2) -> dict:
    """Cross-check reference for `apo_floor_scan`: TASK-0109's own
    closed-form `min_adequate_t_max`/`min_adequate_n_steps` compose to
    the analytically cheapest valid `(t_max, n_steps)` pair directly, no
    search needed. `apo_floor_scan`'s Optuna result should converge
    toward this (up to the search budget and its `oversample >= 1.0`
    floor, which means the search can match but never beat this
    prescription's own cost) -- reported alongside the search result so
    agreement or disagreement is explicit, not silently assumed.
    """
    from .propagators import min_adequate_n_steps, min_adequate_t_max

    w = np.linalg.eigvalsh(H)
    t_max = min_adequate_t_max(w=w, kind=kind, tol=tol)
    n_steps = min_adequate_n_steps(w=w, t_max=t_max) if np.isfinite(t_max) else None
    return {
        "t_max": t_max,
        "n_steps": n_steps,
        "cost": (t_max * n_steps) if (n_steps is not None and np.isfinite(t_max)) else float("inf"),
    }
