"""TASK-0046 -- notebook §8 "interpretable parameter optimization" (blind
random search, not literal coordinate descent -- see below), ported to run
inside `protocol.ceiling_context()`.

Separate module, not a function on `analysis.py` (Open Question, resolved
here): `analysis.py` is already 8 functions / ~460 lines covering scoring
primitives (`benchmark`/`ablation`/`quantum_vs_classical`/...); this task
is a label-using *search driver* over that scoring surface, a different
concern -- the same DEV/FROZEN module-boundary reasoning that already
keeps `select.py` (label-free, FROZEN-eligible) and `protocol.py`
(enforcement) as separate files from `analysis.py` (label-using scoring).

Ported from notebook cell 43 (`consistency_score`, `map_holo_to_apo_occ`,
`sample_params`, the driver loop), read in full before implementing --
NOT re-derived from PLAN.md's summary. Two deliberate deviations from the
notebook, both because this module targets the actual ported codebase,
not the notebook's own from-scratch implementation:

1. **"Coordinate-descent" is a misnomer inherited from the notebook's own
   section title.** Cell 43's actual driver (`for _ in range(60): p =
   sample_params(rng); ...`) is blind random search over the full
   parameter space every trial -- no per-coordinate stepping, no use of
   the previous best as a starting point. Ported as random search, not
   invented into real coordinate descent; the notebook title over-claims,
   the notebook body is the actual spec (TASK-0046's own Open Question,
   resolved by reading the driver cell in full per that task's own
   instruction).
2. **No `kernel` parameter.** The notebook's `sample_params` includes
   `kernel = rng.choice(["exp","gauss"])`, but this repo's ported
   `hamiltonians.build_H_new` -> `normalised_laplacian_alpha` has no
   kernel-choice argument at all (always exponential-decay, tunable via
   `alpha`) -- the notebook's `L_norm` had a DOF the port never carried
   over. Adding a Gaussian-kernel option to `hamiltonians.py` is out of
   this task's scope (that module is `[have]`, owned elsewhere); this
   module searches exactly the DOF `build_H_new` actually exposes:
   `(lam_B, lam_T, lam_R, lam_C, lam_M, alpha, cutoff, n_low_modes)`.
"""
from __future__ import annotations

import numpy as np

_PARAM_RANGES = {
    "lam_B": (0.0, 2.0),
    "lam_T": (0.0, 2.0),
    "lam_R": (0.0, 2.0),
    "lam_C": (0.0, 2.0),
    "lam_M": (0.0, 2.0),
    "alpha": (0.1, 0.6),
    "cutoff": (8.0, 12.0),  # notebook's "r_c"
}
_N_LOW_CHOICES = (5, 8, 10, 12, 15)


def sample_params(rng: np.random.Generator) -> dict:
    """One random draw over `build_H_new`'s physical scalars -- notebook
    cell 43's `sample_params`, minus `kernel` (module docstring)."""
    params = {name: float(rng.uniform(lo, hi)) for name, (lo, hi) in _PARAM_RANGES.items()}
    params["n_low"] = int(rng.choice(_N_LOW_CHOICES))
    return params


def _map_holo_to_apo_occ(apo_resnames, holo_resnames, occ_holo: np.ndarray) -> np.ndarray:
    """notebook cell 43's `map_holo_to_apo_occ`, ported onto `labels.py`'s
    already-implemented, tested Needleman-Wunsch map (TASK-0004) instead
    of re-porting the notebook's own Biopython `PairwiseAligner` version --
    `labels.py` deliberately avoided a Biopython dependency for exactly
    this apo/holo residue-numbering problem (TASK-0004 Open Questions);
    this task should not reintroduce it. Returns an apo-length array,
    `NaN` where no aligned holo residue exists (matches the notebook's own
    NaN-then-filter convention downstream)."""
    from .labels import _needleman_wunsch_map, _sequence

    apo_seq = _sequence(apo_resnames)
    holo_seq = _sequence(holo_resnames)
    holo_to_apo = _needleman_wunsch_map(apo_seq, holo_seq)

    out = np.full(len(apo_resnames), np.nan)
    for h_idx, a_idx in holo_to_apo.items():
        if 0 <= h_idx < len(occ_holo):
            out[a_idx] = occ_holo[h_idx]
    return out


def consistency_score(
    apo_coords: np.ndarray,
    apo_bfactors: np.ndarray,
    apo_source,
    apo_pocket: np.ndarray,
    params: dict,
    *,
    apo_resnames=None,
    holo_coords: np.ndarray | None = None,
    holo_bfactors: np.ndarray | None = None,
    holo_source=None,
    holo_pocket: np.ndarray | None = None,
    holo_resnames=None,
    t_max: float = 15.0,
    n_steps: int = 500,
    coherent: bool = True,
) -> dict:
    """notebook cell 43's `consistency_score`, ported verbatim (Intent
    Contract): `S = 0.5*(AUC_apo+AUC_holo) - 0.25*|AUC_apo-AUC_holo| +
    0.10*Spearman(occ_apo, occ_holo_mapped_to_apo)` -- rewards pocket AUC
    on both apo and holo while penalising an apo/holo split ("a setting
    that overfits to apo but breaks holo is penalised", notebook's own
    rationale).

    `coherent` (TASK-0118): passed straight through to `time_averaged_ctqw`
    for both apo and holo occupations -- see that function's own docstring.

    Holo scoring is entirely optional (omit `holo_coords`/`holo_pocket`
    for an apo-only search) -- when omitted, or when holo's own pocket
    label is degenerate (<3 positives or <3 negatives), `auc_holo` falls
    back to `auc_apo` (notebook's own fallback: "when holo unlabelled"),
    which makes the split-penalty term exactly zero rather than undefined.
    `rho` defaults to `0.0` (notebook's own convention) when fewer than 10
    residues have a common apo/holo alignment.

    Returns `{"S", "auc_apo", "auc_holo", "rho", "params"}`. `S`/`auc_apo`
    are `NaN` if `apo_pocket` itself is degenerate (<3 positives) --
    propagated, not masked, so a caller sweeping many trials can see a
    real label problem rather than a silently-skipped one.
    """
    from scipy.stats import spearmanr

    from .hamiltonians import build_H_new
    from .metrics import auc as auc_fn
    from .propagators import time_averaged_ctqw

    def _build(coords, bfactors):
        return build_H_new(
            coords, bfactors,
            cutoff=params["cutoff"], alpha=params["alpha"],
            lam_B=params["lam_B"], lam_T=params["lam_T"], lam_R=params["lam_R"],
            lam_C=params["lam_C"], lam_M=params["lam_M"], n_low_modes=params["n_low"],
        )

    y_a = np.asarray(apo_pocket).astype(int)
    H_a = _build(apo_coords, apo_bfactors)
    occ_a = time_averaged_ctqw(H_a, t_max, source=apo_source, n_steps=n_steps, coherent=coherent)
    auc_a = auc_fn(occ_a, y_a) if y_a.sum() >= 3 else float("nan")

    auc_h = float("nan")
    rho = float("nan")
    if holo_coords is not None and holo_pocket is not None:
        y_h = np.asarray(holo_pocket).astype(int)
        H_h = _build(holo_coords, holo_bfactors)
        occ_h = time_averaged_ctqw(H_h, t_max, source=holo_source, n_steps=n_steps, coherent=coherent)
        if y_h.sum() >= 3 and (len(y_h) - y_h.sum()) >= 3:
            auc_h = auc_fn(occ_h, y_h)
        if apo_resnames is not None and holo_resnames is not None:
            occ_h_mapped = _map_holo_to_apo_occ(apo_resnames, holo_resnames, occ_h)
            ok = ~np.isnan(occ_h_mapped)
            if ok.sum() >= 10:
                r, _ = spearmanr(occ_a[ok], occ_h_mapped[ok])
                rho = float(r) if r is not None and np.isfinite(r) else float("nan")

    if np.isnan(auc_h):
        auc_h = auc_a
    if np.isnan(rho):
        rho = 0.0

    S = _combine_score(auc_a, auc_h, rho)
    return {"S": float(S), "auc_apo": float(auc_a), "auc_holo": float(auc_h),
            "rho": float(rho), "params": dict(params)}


def _combine_score(auc_apo: float, auc_holo: float, rho: float) -> float:
    """The pure notebook-cell-43 formula, isolated from the physics that
    produces its inputs -- `consistency_score` is this formula plus the
    wiring that computes `auc_apo`/`auc_holo`/`rho` from real occupation
    vectors; kept separate so the formula's own three-term direction
    (Planned Validation) is testable deterministically, without needing
    to engineer synthetic coordinates that happen to produce a desired
    AUC gap through `time_averaged_ctqw`."""
    return 0.5 * (auc_apo + auc_holo) - 0.25 * abs(auc_apo - auc_holo) + 0.10 * rho


def ceiling_search(
    target_name: str,
    apo_coords: np.ndarray,
    apo_bfactors: np.ndarray,
    apo_source,
    apo_pocket: np.ndarray,
    *,
    apo_resnames=None,
    holo_coords: np.ndarray | None = None,
    holo_bfactors: np.ndarray | None = None,
    holo_source=None,
    holo_pocket: np.ndarray | None = None,
    holo_resnames=None,
    n_trials: int = 60,
    seed: int = 7,
    t_max: float = 15.0,
    n_steps: int = 500,
    coherent: bool = True,
) -> dict:
    """Random search driver over `consistency_score` (notebook cell 43's
    `OPT[name] = ...` loop, `N_trials=60` default matching the notebook),
    run inside `protocol.ceiling_context()` -- Phase 2's explicit,
    sanctioned leakage (the search reads `apo_pocket`/`holo_pocket`, the
    answer key, by design; this call site marks that fact rather than
    leaving it implicit, per TASK-0006's Constraint).

    `coherent` (TASK-0118): passed straight through to every trial's
    `consistency_score` call -- see that function's own docstring.

    `seed=7` matches the notebook's own `np.random.default_rng(7)` --
    reproducing the notebook's exact trial sequence for the cross-check
    this task's Planned Validation calls for, not an arbitrary default.

    A trial whose `consistency_score` call raises (e.g. a degenerate
    contact graph at an extreme sampled `cutoff`) is skipped, not fatal --
    mirrors the notebook's own `try/except: continue`. A trial that
    returns a `NaN` `S` (degenerate `apo_pocket`) is kept in `trials` for
    audit but excluded from the "best" selection -- the notebook does not
    guard this (Python's `sort` with `NaN` present is not reliably
    consistent), a deliberate, documented improvement over verbatim
    porting where the notebook's own behaviour would be a latent bug, not
    a result to reproduce.

    Returns `{"target", "best", "trials", "n_trials_run", "n_trials_scored"}`.
    Raises if every trial's `S` came back `NaN` (nothing to rank).
    """
    from .protocol import ceiling_context

    rng = np.random.default_rng(seed)
    trials: list[dict] = []
    with ceiling_context():
        for _ in range(n_trials):
            params = sample_params(rng)
            try:
                result = consistency_score(
                    apo_coords, apo_bfactors, apo_source, apo_pocket, params,
                    apo_resnames=apo_resnames,
                    holo_coords=holo_coords, holo_bfactors=holo_bfactors,
                    holo_source=holo_source, holo_pocket=holo_pocket, holo_resnames=holo_resnames,
                    t_max=t_max, n_steps=n_steps, coherent=coherent,
                )
            except Exception:
                continue
            trials.append(result)

    scored = [t for t in trials if not np.isnan(t["S"])]
    if not scored:
        raise RuntimeError(
            f"ceiling_search({target_name!r}): every trial (of {len(trials)} run) "
            "produced a NaN score -- check apo_pocket has >=3 positive residues."
        )
    best = max(scored, key=lambda t: t["S"])
    return {
        "target": target_name,
        "best": best,
        "trials": trials,
        "n_trials_run": len(trials),
        "n_trials_scored": len(scored),
    }
