"""Quantum-vs-classical comparison, ablation, spectral enrichment, apo/holo
consistency, and the dephasing-relevance sweep.

Callable-function port of notebook `H_new_engineering (4) CLEAN.ipynb`
Sec.7 (default-parameter benchmark), Sec.9 (ablation), Sec.10 (quantum vs
classical), Sec.11 (spectral/low-mode enrichment), Sec.12 (apo<->holo
consistency), plus the Phase 0a dephasing sweep (PLAN.md).

Notebook-oracle gap (read before trusting any "regression" number here):
the `.ipynb` in this repo has all cell outputs cleared -- there is no
"printed value to read directly" for any of Sec.7/9/10/11/12 to copy from,
the same pre-existing gap `.claude/TASKS.md` T-004/T-017 already documented
for `eff_rank`≈117.7 (marked `xfail(strict=False)` there rather than
faked). This module's own regression tests follow that same precedent:
numbers are computed fresh from this package's already-ported modules
against real RCSB structures, not copied from the notebook, and are
labelled as such.

Leakage boundary: every function here takes already-derived arrays
(occupation vectors, pocket-label masks) as input -- none of them touch a
holo structure directly. FROZEN-path callers must obtain those inputs via
protocol.py's gated accessors (TASK-0006), not by calling
labels.py/superpose.py directly; that boundary is enforced there, not here.
"""
from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Shared metric pack (mirrors notebook's metric_pack, built on metrics.py)
# ---------------------------------------------------------------------------

def _metric_pack(occ: np.ndarray, labels: np.ndarray, ks=(5, 10, 20)) -> dict:
    """AUC + precision/enrichment@k for one occupation vector vs one label
    mask. `occ` is dropped from the returned dict under key "occ" for
    callers that want the raw vector alongside the scalar metrics."""
    from .metrics import auc as _auc, precision_at_k, enrichment_at_k

    labels_int = np.asarray(labels).astype(int)
    out = {"AUC": _auc(occ, labels_int)}
    for k in ks:
        k_eff = min(k, len(occ))
        out[f"P@{k}"] = precision_at_k(occ, labels_int, k_eff)
        out[f"E@{k}"] = enrichment_at_k(occ, labels_int, k_eff)
    out["occ"] = occ
    return out


# ---------------------------------------------------------------------------
# Sec.10 -- CTQW vs ground-state relaxation head-to-head (same H)
# ---------------------------------------------------------------------------

def quantum_vs_classical(
    H: np.ndarray,
    source,
    labels: np.ndarray | None = None,
    t_max: float = 15.0,
    n_steps: int = 500,
    *,
    coherent: bool = True,
    use_converged_limit: bool = False,
) -> dict:
    """CTQW vs `propagators.ground_state_relaxation` on the *same* H.

    **Not a coherent-vs-diffusive comparison when `H` is indefinite** (e.g.
    `H_new` -- see TASK-0095 / REVIEW-2026-07-13 finding P1-B).
    `ground_state_relaxation` (formerly named after the diffusion process it
    is only sometimes computing) behaves as a diffusion kernel only when `H`
    is positive-semidefinite; on `H_new` it converges to the operator's
    ground-state density instead. This function still computes a real,
    useful comparison either way (does the coherent time-average differ
    from the operator's own ground-state-localized limit?) -- it was the
    *name* this module used to describe the second side that was wrong, not
    the computation. Callers must check `H`'s spectrum before describing the
    "heat" side of this dict as a diffusion process or as "quantum vs
    classical" (the renamed propagator warns by default when `H` is
    indefinite).

    CTQW is coherent/oscillatory (no decay), so it is compared via its
    time-average over [0, t_max] (`propagators.time_averaged_ctqw`) -- a
    single-time snapshot would be an arbitrary phase pick. A single
    evaluation of `ground_state_relaxation` at t_max is representative of
    its long-time behaviour either way (monotonic relaxation if `H` is PSD;
    convergence to the ground state otherwise), so it does not need the
    same averaging (there is no analogous time-averaged helper in
    propagators.py by design, not by omission).

    Returns a dict with "ctqw" and "heat" sub-dicts (each a metric pack, or
    just the occupation vector if `labels` is None) -- key names kept as
    short internal labels, not a physics claim; see the correction above
    for what "heat" actually means when `H` is indefinite.

    `coherent` (TASK-0118): passed straight through to `time_averaged_ctqw`
    -- `ground_state_relaxation`'s classical mixture is unaffected either
    way (it already treats a multi-index `source` as an incoherent
    probability split, by construction, not a choice this parameter
    changes).

    `use_converged_limit` (TASK-0130): `False` (default, byte-identical
    to every existing call site) uses `time_averaged_ctqw(H, t_max,
    ...)` as before. `True` uses `propagators.time_averaged_ctqw_
    converged` instead -- the exact infinite-time closed form, ignoring
    `t_max`/`n_steps` entirely for the "ctqw" side (`t_max` still governs
    `ground_state_relaxation`'s own, unaffected, unrelated convergence
    criterion -- see `check_convergence`'s two-independent-checks
    docstring). Exists because `t_max=15` is 145,000x-3,950,000x short of
    `time_averaged_ctqw`'s own AAKV convergence criterion on every real
    target checked (TASK-0110); the closed form sidesteps that gap
    entirely for a caller who wants the converged value.
    """
    from .propagators import ground_state_relaxation, time_averaged_ctqw, time_averaged_ctqw_converged

    if use_converged_limit:
        occ_ctqw = time_averaged_ctqw_converged(H, source=source, coherent=coherent)
    else:
        occ_ctqw = time_averaged_ctqw(H, t_max, source=source, n_steps=n_steps, coherent=coherent)
    occ_heat = ground_state_relaxation(H, t_max, source=source)

    if labels is None:
        return {"ctqw": occ_ctqw, "heat": occ_heat}
    return {
        "ctqw": _metric_pack(occ_ctqw, labels),
        "heat": _metric_pack(occ_heat, labels),
    }


# ---------------------------------------------------------------------------
# Sec.9 -- ablation: which potential term actually carries the signal?
# ---------------------------------------------------------------------------

def ablation(
    coords: np.ndarray,
    bfactors: np.ndarray,
    source,
    labels: np.ndarray,
    cutoff: float = 10.0,
    alpha: float = 0.3,
    terminal_fraction: float = 0.05,
    n_low_modes: int = 10,
    t_max: float = 15.0,
    n_steps: int = 500,
) -> dict:
    """Per-term contribution to pocket-ranking signal.

    Each of potentials.py's five terms (V_B/V_T/V_R/V_C/V_M) is added
    *individually* to the bare normalised Laplacian base (not H_new's full
    sum) and scored on its own -- this isolates which single term, if any,
    carries the signal, per this task's framing ("which term actually
    carries the signal", a single-term-attribution question, not a
    leave-one-out one). "L_only" (the bare base transport operator, no
    potential terms at all) is included as the reference every term is
    judged against.

    Returns {"L_only": metric_pack, "B": metric_pack, "T": ..., "R": ...,
    "C": ..., "M": ...}.
    """
    from .hamiltonians import normalised_laplacian_alpha
    from .potentials import V_B, V_T, V_R, V_C, V_M as _V_M
    from .propagators import time_averaged_ctqw

    L = normalised_laplacian_alpha(coords, cutoff=cutoff, alpha=alpha)
    terms = {
        "B": V_B(bfactors),
        "T": V_T(len(coords), terminal_fraction),
        "R": V_R(coords, cutoff=cutoff),
        "C": V_C(coords, cutoff=cutoff),
        "M": _V_M(coords, cutoff=cutoff, n_modes=n_low_modes),
    }

    results = {"L_only": _metric_pack(time_averaged_ctqw(L, t_max, source, n_steps), labels)}
    for name, V in terms.items():
        occ = time_averaged_ctqw(L + V, t_max, source, n_steps)
        results[name] = _metric_pack(occ, labels)
    return results


# ---------------------------------------------------------------------------
# Sec.7 -- default-parameter benchmark: H_new vs H10_disorder_suppressed
# ---------------------------------------------------------------------------

def benchmark(
    coords: np.ndarray,
    bfactors: np.ndarray,
    source,
    labels: np.ndarray,
    cutoff: float = 10.0,
    t_max: float = 15.0,
    n_steps: int = 500,
    *,
    coherent: bool = True,
    use_converged_limit: bool = False,
) -> dict:
    """Default-parameter (not optimized -- see TASK-0008's Open Question on
    notebook Sec.8's coordinate-descent optimizer, out of this module's
    scope) comparison of H_new against the H10_disorder_suppressed
    baseline, both propagated by time-averaged CTQW.

    `coherent` (TASK-0118): passed straight through to `time_averaged_ctqw`
    for both operators -- see that function's own docstring.

    `use_converged_limit` (TASK-0130): `False` (default, unchanged
    behavior) uses `time_averaged_ctqw(H, t_max, ...)`; `True` uses the
    exact infinite-time closed form (`time_averaged_ctqw_converged`)
    instead, ignoring `t_max`/`n_steps` -- see `quantum_vs_classical`'s
    own docstring for why this exists.

    Returns {"H_new_default": metric_pack, "H10_disorder_suppressed":
    metric_pack}.
    """
    from .hamiltonians import build_H_new, build_H10
    from .propagators import time_averaged_ctqw, time_averaged_ctqw_converged

    H_new = build_H_new(coords, bfactors, cutoff=cutoff)
    H10 = build_H10(coords, bfactors, cutoff=cutoff)

    if use_converged_limit:
        occ_new = time_averaged_ctqw_converged(H_new, source=source, coherent=coherent)
        occ_10 = time_averaged_ctqw_converged(H10, source=source, coherent=coherent)
    else:
        occ_new = time_averaged_ctqw(H_new, t_max, source=source, n_steps=n_steps, coherent=coherent)
        occ_10 = time_averaged_ctqw(H10, t_max, source=source, n_steps=n_steps, coherent=coherent)

    return {
        "H_new_default": _metric_pack(occ_new, labels),
        "H10_disorder_suppressed": _metric_pack(occ_10, labels),
    }


# ---------------------------------------------------------------------------
# TASK-0079.001 -- assemble this module's real (nested) output into
# report.verdict_template's expected flat schema (closes SEAM-0008)
# ---------------------------------------------------------------------------

def assemble_verdict_results(
    benchmark_out: dict | None = None,
    ablation_out: dict | None = None,
    qvc_out: dict | None = None,
    consistency_out: dict | None = None,
    coherence_out: dict | None = None,
    *,
    auc_apo_optimised: float | None = None,
    auc_holo_optimised: float | None = None,
) -> dict:
    """Translate this module's real return shapes into
    `report.verdict_template`'s expected flat `results` dict
    (`AUC_apo_Hnew_default`, `AUC_apo_H10_baseline`, ..., `mean_jacc20`).

    Every argument is optional and independently omittable, matching
    `verdict_template`'s own "a missing key renders N/A" philosophy for a
    caller who hasn't run every upstream analysis for a given target --
    this function degrades the same way, key-by-key, not all-or-nothing.

    `auc_apo_optimised`/`auc_holo_optimised` are **not** derived from
    `benchmark()` (which is explicitly the *default*-parameter comparison,
    per its own docstring) -- they must be supplied directly by the
    caller, from whatever produced the optimized-config run (TASK-0079.003's
    `select_frozen_config`-driven pipeline). Guessing them from `benchmark_out`
    would silently mislabel a default-parameter number as an optimized one.

    `most_impactful_term`/`least_impactful_term` are derived from
    `ablation_out`'s per-term *attribution* deltas against `"L_only"`
    (this module's `ablation()` adds each term individually to the bare
    base operator -- a single-term-attribution design, not a leave-one-out
    one, per that function's own docstring; "impact" here means the same
    thing cell 58's `abl_strength` meant, adapted to this module's actual
    computation rather than the notebook's). Formatted as `"V_B"`/`"V_T"`/
    etc., matching `potentials.py`'s canonical term names, not the bare
    single-letter dict keys `ablation()` returns.

    A `NaN` `"AUC"` (from `metrics.auc`'s own degenerate-labels convention,
    e.g. an all-positive or all-negative label mask) is treated as missing,
    not rendered as the literal string `"nan"` -- consistent with
    `verdict_template`'s `"N/A"` styling for every other absent value.

    `coherence_out` (TASK-0099) is `coherence_sensitivity`'s output --
    contributes `coherence_auc_range`, `coherence_auc_at_gamma0`, and
    `coherence_classification` (`COHERENCE_NOT_SIGNIFICANT` /
    `COHERENCE_DEPENDENT_SIGNAL`), the formal answer to "would the reported
    verdict change if quantum coherence were randomized away."
    """
    def _finite_or_none(value):
        return value if np.isfinite(value) else None

    results: dict = {}

    if benchmark_out is not None:
        v = _finite_or_none(benchmark_out["H_new_default"]["AUC"])
        if v is not None:
            results["AUC_apo_Hnew_default"] = v
        v = _finite_or_none(benchmark_out["H10_disorder_suppressed"]["AUC"])
        if v is not None:
            results["AUC_apo_H10_baseline"] = v

    if auc_apo_optimised is not None:
        results["AUC_apo_Hnew_optimised"] = auc_apo_optimised
    if auc_holo_optimised is not None:
        results["AUC_holo_Hnew_optimised"] = auc_holo_optimised

    if qvc_out is not None:
        v = _finite_or_none(qvc_out["ctqw"]["AUC"])
        if v is not None:
            results["AUC_ctqw_mean"] = v
        v = _finite_or_none(qvc_out["heat"]["AUC"])
        if v is not None:
            results["AUC_heat_mean"] = v

    if ablation_out is not None and "L_only" in ablation_out:
        baseline_auc = ablation_out["L_only"]["AUC"]
        impact = {
            name: pack["AUC"] - baseline_auc
            for name, pack in ablation_out.items()
            if name != "L_only" and np.isfinite(pack["AUC"]) and np.isfinite(baseline_auc)
        }
        if impact:
            most = max(impact, key=lambda k: abs(impact[k]))
            least = min(impact, key=lambda k: abs(impact[k]))
            results["most_impactful_term"] = f"V_{most}"
            results["least_impactful_term"] = f"V_{least}"

    if consistency_out is not None:
        v = consistency_out.get("spearman_rho")
        if v is not None and np.isfinite(v):
            results["mean_rho_apo_holo"] = v
        v = consistency_out.get("top_k_jaccard")
        if v is not None and np.isfinite(v):
            results["mean_jacc20"] = v

    if coherence_out is not None:
        v = coherence_out.get("auc_range")
        if v is not None and np.isfinite(v):
            results["coherence_auc_range"] = v
        v = coherence_out.get("auc_at_gamma0")
        if v is not None and np.isfinite(v):
            results["coherence_auc_at_gamma0"] = v
        v = coherence_out.get("classification")
        if v is not None:
            results["coherence_classification"] = v

    return results


# ---------------------------------------------------------------------------
# Sec.12 -- apo<->holo consistency in pocket ranking
# ---------------------------------------------------------------------------

def apo_holo_consistency(
    occ_apo: np.ndarray,
    occ_holo: np.ndarray,
    apo_idx: np.ndarray,
    holo_idx: np.ndarray,
    k: int = 5,
) -> dict:
    """Agreement between apo- and holo-computed rankings, restricted to a
    common residue correspondence (e.g. superpose.align_apo_holo's
    `apo_idx`/`holo_idx`, passed in by the caller -- this module stays
    decoupled from superpose.py's specific data types).

    Returns Spearman rank correlation over the common set plus top-k
    overlap/Jaccard of the highest-occupancy residues on each side.
    """
    from scipy.stats import spearmanr

    common_apo = occ_apo[apo_idx]
    common_holo = occ_holo[holo_idx]

    rho, pval = spearmanr(common_apo, common_holo)

    k_eff = min(k, len(common_apo))
    top_apo = set(np.argsort(-common_apo)[:k_eff].tolist())
    top_holo = set(np.argsort(-common_holo)[:k_eff].tolist())
    union = top_apo | top_holo
    jaccard = len(top_apo & top_holo) / len(union) if union else 1.0

    return {
        "spearman_rho": float(rho) if rho is not None else float("nan"),
        "spearman_p": float(pval) if pval is not None else float("nan"),
        "top_k_overlap": len(top_apo & top_holo),
        "top_k_jaccard": jaccard,
        "k": k_eff,
    }


# ---------------------------------------------------------------------------
# Sec.11 -- spectral & low-mode participation enrichment
# ---------------------------------------------------------------------------

def spectral_enrichment(H: np.ndarray, pocket_mask: np.ndarray, n_modes: int = 10) -> dict:
    """Does low-mode (slow, global) participation enrich for the pocket
    label? Reuses metrics.eff_rank/ipr/spectral_gap (this task's own
    Constraint) rather than recomputing spectral diagnostics from scratch.

    Skips the trivial zero mode the same way potentials.V_M does, for
    consistency with the rest of the package's low-mode convention.
    """
    from .metrics import eff_rank, ipr, spectral_gap, auc as _auc

    w, v = np.linalg.eigh((H + H.T) / 2)
    idx_start = max(1, int(np.searchsorted(w, 1e-8)))
    idx_end = min(idx_start + n_modes, len(w))
    low_modes = v[:, idx_start:idx_end]
    participation = (low_modes ** 2).mean(axis=1) if idx_end > idx_start else np.zeros(len(w))

    return {
        "auc": _auc(participation, np.asarray(pocket_mask).astype(int)),
        "eff_rank": eff_rank(w),
        "ipr_slowest_mode": ipr(v[:, idx_start]) if idx_end > idx_start else float("nan"),
        "spectral_gap": spectral_gap(w),
        "participation": participation,
    }


# ---------------------------------------------------------------------------
# Phase 0a -- dephasing sweep: is coherence scientifically relevant?
# ---------------------------------------------------------------------------

def dephasing_sweep(
    H: np.ndarray,
    omega_range: np.ndarray,
    labels: np.ndarray,
    source=0,
    t_max: float = 15.0,
    flat_threshold: float = 0.05,
    rtol: float = 1e-6,
    atol: float = 1e-8,
    return_occ: bool = False,
) -> dict:
    """AUC(omega) via Haken-Strobl dephasing (`propagators.haken_strobl`),
    scored with `metrics.auc` (this task's own Constraint: reuse, don't
    reimplement). Flat AUC across the sweep means coherence is not adding
    ranking power beyond what the topology/graph kernel already gives --
    PLAN.md's "coherence adds ~nothing" finding, restated as a runtime
    check rather than an eyeballed notebook plot.

    `flat_threshold` is the AUC range (max-min across the sweep) below
    which the sweep is called flat; 0.05 is a documented default, not a
    magic number -- override it if a target's own noise floor differs.

    `rtol`/`atol` pass straight through to `haken_strobl`'s `solve_ivp`
    call -- the defaults are tight (accurate) but slow at protein scale
    (~20s per gamma at N~170 residues); loosen them for a fast sanity
    sweep, tighten them for a number you intend to publish.

    `return_occ=True` additionally returns the raw per-gamma occupation
    vectors under key `"occ"` (list of `(N,)` arrays, aligned to
    `omega_range`) -- needed by callers that must run further per-point
    diagnostics beyond the scalar AUC this function already returns (e.g.
    `coherence_sensitivity`'s proximity-floor check, TASK-0099). Off by
    default -- existing callers keep the identical return shape.
    """
    from .propagators import haken_strobl
    from .metrics import auc as _auc

    omega_range = np.asarray(omega_range, dtype=float)
    labels_int = np.asarray(labels).astype(int)
    occs = [
        haken_strobl(H, t_max, gamma=float(w), source=source, rtol=rtol, atol=atol)
        for w in omega_range
    ]
    aucs = np.array([_auc(occ, labels_int) for occ in occs])
    finite = aucs[np.isfinite(aucs)]
    auc_range = float(finite.max() - finite.min()) if len(finite) else float("nan")

    result = {
        "omega": omega_range,
        "auc": aucs,
        "auc_range": auc_range,
        "is_flat": bool(auc_range < flat_threshold) if np.isfinite(auc_range) else None,
        "flat_threshold": flat_threshold,
    }
    if return_occ:
        result["occ"] = occs
    return result


# ---------------------------------------------------------------------------
# TASK-0099 -- wire dephasing_sweep into the reported verdict path
# ---------------------------------------------------------------------------

def coherence_sensitivity(
    H: np.ndarray,
    bfactors: np.ndarray,
    source,
    labels: np.ndarray,
    gamma_scale: float,
    *,
    floor_scores=None,
    t_max: float = 15.0,
    multipliers=(0.0, 0.5, 1.0, 2.0),
    flat_threshold: float = 0.05,
    rtol: float = 1e-6,
    atol: float = 1e-8,
) -> dict:
    """Formal coherence-sensitivity verdict: wires `dephasing_sweep`
    (already implemented, previously never called from `protocol.py` or
    `report.py` -- TASK-0099's own finding) into a proximity-floor-gated,
    classified quantity fit for `assemble_verdict_results`.

    `gamma_scale` is the caller-supplied *calibrated* dephasing rate --
    `1 / mean(mode_energetics(...)["relaxation_time"][:20])`, from
    `superpose.calibrate_kappa` + `superpose.anm_modes` +
    `superpose.mode_energetics`, exactly
    `test_kras_g12c_dephasing_flat_survives_kappa_calibration`'s
    already-validated recipe (this task's own Intent Contract). Computed by
    the caller, not here -- keeps this module decoupled from superpose.py,
    matching its existing convention of taking already-derived scalars/
    arrays as input, not raw structures.

    `multipliers` default `(0, 0.5, 1, 2)` -- the Intent Contract's stated
    minimum sweep. `gamma=0` is evaluated via the exact, cheap `ctqw` limit
    rather than paying for `haken_strobl`'s ODE solver at gamma=0 (reuses
    TASK-0105's own established optimization, `enaqt_gamma_sweep.
    sweep_gamma`, rather than re-deriving it).

    `flat_threshold` reuses `dephasing_sweep`'s own already-documented 0.05
    default as the significance bar -- this task's own Open Question ("what
    threshold separates COHERENCE_NOT_SIGNIFICANT from
    COHERENCE_DEPENDENT_SIGNAL") is resolved by reusing that existing,
    already-justified constant (KRAS's own empirical range is ~0.0035, well
    inside it) rather than inventing a second, undocumented magic number.

    `floor_scores` (TASK-0094): every swept gamma's occupation vector is run
    through `diagnostics.classify_failure` (H/bfactors passed through,
    matching `operator_sweep`'s own established call convention) -- a
    non-flat AUC range that never changes which side of the proximity floor
    the result lands on is `COHERENCE_NOT_SIGNIFICANT` (geometry-confounded,
    not oversold as a quantum finding, per this task's own Acceptance
    Scenario); one that does is `COHERENCE_DEPENDENT_SIGNAL`. `floor_scores
    =None` skips the floor gate and returns `classification=None` for a
    non-flat sweep (unresolved, not silently assumed insignificant) --
    real per-target verdict runs must always supply it.

    Returns `{"gammas", "auc", "auc_range", "is_flat", "flat_threshold",
    "auc_at_gamma0", "diagnoses", "floor_cleared", "classification"}`.
    """
    from .diagnostics import NO_FAILURE_DETECTED, classify_failure
    from .metrics import auc as _auc
    from .propagators import ctqw

    multipliers = np.asarray(sorted(multipliers), dtype=float)
    gammas = gamma_scale * multipliers
    labels_int = np.asarray(labels).astype(int)
    nonzero_mask = gammas > 0

    occs = [None] * len(gammas)
    zero_idx = np.where(~nonzero_mask)[0]
    if len(zero_idx):
        occ0 = ctqw(H, t_max, source=source)
        for i in zero_idx:
            occs[i] = occ0

    nz_idx = np.where(nonzero_mask)[0]
    if len(nz_idx):
        sweep = dephasing_sweep(
            H, gammas[nz_idx], labels, source=source, t_max=t_max,
            flat_threshold=flat_threshold, rtol=rtol, atol=atol, return_occ=True,
        )
        for i, occ in zip(nz_idx, sweep["occ"]):
            occs[i] = occ

    aucs = np.array([_auc(occ, labels_int) for occ in occs])
    finite = aucs[np.isfinite(aucs)]
    auc_range = float(finite.max() - finite.min()) if len(finite) else float("nan")
    is_flat = bool(auc_range < flat_threshold) if np.isfinite(auc_range) else None

    diagnoses = [
        classify_failure(occ, labels, H=H, bfactors=bfactors, floor_scores=floor_scores)
        for occ in occs
    ]
    floor_cleared = [d == NO_FAILURE_DETECTED for d in diagnoses]

    if is_flat is None:
        classification = None
    elif is_flat:
        classification = "COHERENCE_NOT_SIGNIFICANT"
    elif floor_scores is None:
        classification = None
    elif len(set(floor_cleared)) > 1:
        classification = "COHERENCE_DEPENDENT_SIGNAL"
    else:
        classification = "COHERENCE_NOT_SIGNIFICANT"

    return {
        "gammas": gammas.tolist(),
        "auc": aucs.tolist(),
        "auc_range": auc_range,
        "is_flat": is_flat,
        "flat_threshold": flat_threshold,
        "auc_at_gamma0": float(aucs[zero_idx[0]]) if len(zero_idx) else None,
        "diagnoses": diagnoses,
        "floor_cleared": floor_cleared,
        "classification": classification,
    }


# ---------------------------------------------------------------------------
# TASK-0067 -- GNM cutoff + contact-weight-scheme benchmark
#
# Resolves the three-way cutoff divergence TASK-0018's decision doc found:
# backend/analysis.py::gnm_context uses 8.0 A, hamiltonians.H8_gnm defaults
# to 7.5 A, potentials.py's GNM callers (_gnm_msf/V_R/V_C/V_M) pass 10.0 A --
# none benchmarked. H8_gnm itself is fixed to weight="binary" by convention
# (the classical GNM Kirchhoff definition); this sweep generalises that to
# every weighting scheme hamiltonians.contact_matrix already exposes
# (binary/gaussian/exponential/harmonic/invdist), building the same
# combinatorial-Laplacian family H8_gnm builds, parameterised by both knobs
# at once rather than hand-rolling a new operator.
# ---------------------------------------------------------------------------

def gnm_cutoff_weight_sweep(
    coords: np.ndarray,
    source,
    labels: np.ndarray,
    cutoffs=(7.5, 8.0, 10.0),
    weight_schemes=("binary", "gaussian", "exponential", "harmonic", "invdist"),
    t_max: float = 15.0,
) -> dict:
    """Score every (cutoff, weight_scheme) combination's GNM-Kirchhoff
    Laplacian against `labels`, scored from `source` via a genuine
    diffusion kernel (this call site's `L` is always PSD, see below).

    `ground_state_relaxation` (formerly `heat`, TASK-0095), not
    `time_averaged_ctqw`, is the deliberate choice here: propagators.py's
    own docstring states a single evaluation at `t_max` is "already
    representative" (no oscillation to average out, unlike CTQW) -- this
    sweep is comparing *operator construction* (cutoff x weight), not
    propagator choice, so the cheaper single-eval kernel is the right tool,
    not a shortcut that changes what's being measured. `laplacian(W,
    normalised=False)` is always PSD for any non-negative `W`, so this call
    site's diffusion-kernel framing is accurate (unlike `H_new`, there is no
    indefinite-operator concern here regardless of which weight scheme
    built `W` -- `ground_state_relaxation`'s guard will not fire).

    Returns `{(cutoff, weight_scheme): metric_pack, ...}` -- reuses this
    module's own `_metric_pack` (AUC + P@k + E@k), not a new score format.
    """
    from .hamiltonians import contact_matrix, laplacian
    from .propagators import ground_state_relaxation

    results = {}
    for cutoff in cutoffs:
        for scheme in weight_schemes:
            W = contact_matrix(coords, cutoff=cutoff, weight=scheme)
            L = laplacian(W, normalised=False)
            occ = ground_state_relaxation(L, t_max, source=source)
            results[(cutoff, scheme)] = _metric_pack(occ, labels)
    return results


# ---------------------------------------------------------------------------
# TASK-0080 -- consensus ranking (no-ground-truth targets, e.g. c-Myc/1NKP)
# ---------------------------------------------------------------------------

_CONSENSUS_DEFAULT_OPERATORS = (
    "H_new_default", "H10_disorder_suppressed", "H2_combinatorial_laplacian", "H14_anm_pinv_trace",
)


def consensus_ranking(
    coords: np.ndarray,
    bfactors: np.ndarray,
    source,
    *,
    cutoff: float = 10.0,
    t_max: float = 15.0,
    n_steps: int = 500,
    k: int = 10,
) -> dict:
    """Holo-free confidence signal for targets with no labeled pocket to
    score AUC against (`TASK-0080`'s c-Myc/1NKP case: `allosteric_pocket_
    exists: false`, `holo_pdb: null`). Adapts
    `HOLO_DIRECTION_MODULE.md` Step 5's "consensus across perturbations"
    idea (*"is the predicted pocket the same region across [an ensemble]?
    Stable region = real resolving power; smear across the surface =
    none. Computable with no holo at all."*) from an ensemble of
    admissible apo deformations (`TASK-0015`, not built) to an ensemble
    of already-built, already-tested operator families on the *same*
    fixed apo topology -- the same holo-free spirit (no AUC, no labeled
    pocket, anywhere in this function), a real and available substitute,
    not that task's own scope.

    Runs `time_averaged_ctqw` through each of `H_new_default`,
    `H10_disorder_suppressed`, `H2_combinatorial_laplacian`, and
    `H14_anm_pinv_trace` (Tier A/B mix per `TASK-0100`'s own operator
    tiering, not just the two candidates `benchmark()` compares) from the
    same `source` seed, and reports, per residue, how many of the 4
    operators' own top-`k` sets include it (`consensus_count`) plus the
    mean occupancy across operators (a tie-breaker within a consensus
    tier, not the primary signal -- agreement across independently-built
    operators is the actual claim here, not any single operator's score).

    Returns `{"operators", "occupancy", "top_k_per_operator",
    "consensus_count", "mean_occupancy", "consensus_ranked_indices",
    "n_operators", "k"}`. `consensus_ranked_indices` is the top-`k`
    residues ordered by `(consensus_count desc, mean_occupancy desc)`.
    """
    from .hamiltonians import H2_combinatorial_laplacian, H14_anm_pinv_trace, build_H10, build_H_new
    from .propagators import time_averaged_ctqw

    operators = {
        "H_new_default": build_H_new(coords, bfactors, cutoff=cutoff),
        "H10_disorder_suppressed": build_H10(coords, bfactors, cutoff=cutoff),
        "H2_combinatorial_laplacian": H2_combinatorial_laplacian(coords, cutoff=cutoff),
        "H14_anm_pinv_trace": H14_anm_pinv_trace(coords, cutoff=cutoff),
    }

    n = len(coords)
    k_eff = min(k, n)
    occupancy: dict = {}
    top_k_per_operator: dict = {}
    consensus_count = np.zeros(n, dtype=int)
    for name, H in operators.items():
        occ = time_averaged_ctqw(H, t_max, source=source, n_steps=n_steps)
        occupancy[name] = occ
        top_k = np.argsort(-occ)[:k_eff]
        top_k_per_operator[name] = sorted(int(i) for i in top_k)
        consensus_count[top_k] += 1

    mean_occupancy = np.mean(np.stack(list(occupancy.values())), axis=0)
    order = np.lexsort((-mean_occupancy, -consensus_count))
    consensus_ranked_indices = order[:k_eff]

    return {
        "operators": list(operators.keys()),
        "occupancy": occupancy,
        "top_k_per_operator": top_k_per_operator,
        "consensus_count": consensus_count,
        "mean_occupancy": mean_occupancy,
        "consensus_ranked_indices": consensus_ranked_indices,
        "n_operators": len(operators),
        "k": k_eff,
    }


# ---------------------------------------------------------------------------
# TASK-0101 -- Tier-1 operator sweep (TASK-0100's architecture decision)
#
# 16 named operators (H1-H14, H_new, build_H10) x 2 propagators (ctqw,
# ground_state) -- descriptive measurement only, no frozen gate (nothing
# is being selected, per TASK-0100 Sec.2's Tier-1/Tier-2 split). Tier
# labels (A: submission candidates; B: baseline/ablation family) per
# TASK-0100 Sec.3. `build_H10` is deliberately registered *alongside*
# `H10` (both resolve to `H10_disorder_suppressed`, `build_H10` via its
# own convenience-alias signature) -- redundant by design, per TASK-0101's
# own "H1-H14, build_H_new, build_H10" enumeration (16 operators, not 15);
# agreement between the two rows is itself a small, free consistency
# check on the alias.
# ---------------------------------------------------------------------------

_TIER_A_OPERATORS = frozenset({"H10", "H14", "H_new", "build_H10"})


def _operator_registry() -> dict:
    """name -> (tier, build_fn); build_fn(coords, bfactors, cutoff) -> H.

    One uniform three-argument call convention for every operator,
    regardless of which arguments the underlying `hamiltonians.py`
    function actually takes (`H1`-`H8`/`H11`-`H13` ignore `bfactors`;
    `H9`/`H10`/`H_new`/`build_H10` need it) -- each lambda is the explicit
    adapter, not a generic dispatch that would force one signature onto
    all fourteen (this task's own Constraint).
    """
    from .hamiltonians import (
        H1_unweighted_adjacency, H2_combinatorial_laplacian, H3_normalised_laplacian,
        H4_powered_normalised, H5_gaussian_elastic, H6_exponential_decay, H7_harmonic,
        H8_gnm, H9_bfactor_regularised, H10_disorder_suppressed, H11_anisotropic_mechanical,
        H12_anm_scalarised, H13_3N_anm_hessian, H14_anm_pinv_trace, build_H_new, build_H10,
    )

    return {
        "H1": ("B", lambda coords, bfactors, cutoff: H1_unweighted_adjacency(coords, cutoff=cutoff)),
        "H2": ("B", lambda coords, bfactors, cutoff: H2_combinatorial_laplacian(coords, cutoff=cutoff)),
        "H3": ("B", lambda coords, bfactors, cutoff: H3_normalised_laplacian(coords, cutoff=cutoff)),
        "H4": ("B", lambda coords, bfactors, cutoff: H4_powered_normalised(coords, cutoff=cutoff)),
        "H5": ("B", lambda coords, bfactors, cutoff: H5_gaussian_elastic(coords, cutoff=cutoff)),
        "H6": ("B", lambda coords, bfactors, cutoff: H6_exponential_decay(coords, cutoff=cutoff)),
        "H7": ("B", lambda coords, bfactors, cutoff: H7_harmonic(coords, cutoff=cutoff)),
        "H8": ("B", lambda coords, bfactors, cutoff: H8_gnm(coords, cutoff=cutoff)),
        "H9": ("B", lambda coords, bfactors, cutoff: H9_bfactor_regularised(coords, bfactors, cutoff=cutoff)),
        "H10": ("A", lambda coords, bfactors, cutoff: H10_disorder_suppressed(coords, bfactors, cutoff=cutoff)),
        "H11": ("B", lambda coords, bfactors, cutoff: H11_anisotropic_mechanical(coords, cutoff=cutoff)),
        "H12": ("B", lambda coords, bfactors, cutoff: H12_anm_scalarised(coords, cutoff=cutoff)),
        "H13": ("B", lambda coords, bfactors, cutoff: H13_3N_anm_hessian(coords, cutoff=cutoff)),
        "H14": ("A", lambda coords, bfactors, cutoff: H14_anm_pinv_trace(coords, cutoff=cutoff)),
        "H_new": ("A", lambda coords, bfactors, cutoff: build_H_new(coords, bfactors, cutoff=cutoff)),
        "build_H10": ("A", lambda coords, bfactors, cutoff: build_H10(coords, bfactors, cutoff=cutoff)),
    }


def _transport_participation_ratio(p) -> float:
    """PR/N of an occupation vector -- REVIEW-2026-07-13c's own transport
    diagnostic (Sec.1's disorder-sweep table), reused here rather than
    inventing a second one. 1.0 = fully delocalised (uniform over all N
    residues); ~1/N = fully localised (trapped at the seed)."""
    p = np.asarray(p, dtype=float)
    n = len(p)
    ssq = float(np.sum(p ** 2))
    return 1.0 / (n * ssq) if ssq > 0 else float("nan")


def operator_sweep(
    coords: np.ndarray,
    bfactors: np.ndarray,
    source,
    pocket_label: np.ndarray,
    floor_scores,
    cutoff: float = 10.0,
    operators=None,
    propagators=("ctqw", "ground_state"),
    t_max: float = 15.0,
    n_steps: int = 500,
    *,
    coherent: bool = True,
    use_converged_limit: bool = False,
) -> list:
    """Score every named operator, through every named propagator, against
    `pocket_label` and TASK-0094's proximity floor. Tier-1 (descriptive)
    only -- no `frozen_context`, nothing is being selected (TASK-0100
    Sec.2's own line: "pure measurement... `leave_one_protein_out` is not
    required").

    `operators`: iterable of registry names, or `None` for all 16.
    `propagators`: iterable of `{"ctqw", "ground_state"}`.

    `coherent` (TASK-0118/TASK-0129): passed straight through to the
    `"ctqw"` propagator's `time_averaged_ctqw` call -- see that function's
    own docstring. `"ground_state"` (`ground_state_relaxation`) is
    unaffected either way (already an incoherent classical mixture over a
    multi-index `source` by construction).

    An individual cell's failure (e.g. `H13`'s 3N x 3N shape, incompatible
    with residue-indexed scoring -- checked explicitly below, not left to
    silently mis-index) is caught and recorded as its own error row; it
    does not abort the rest of the sweep (this task's own Acceptance
    Scenario).

    `use_converged_limit` (TASK-0130): `False` (default, unchanged
    behavior) scores the `"ctqw"` propagator via `time_averaged_ctqw(H,
    t_max, ...)`; `True` scores it via the exact infinite-time closed
    form (`time_averaged_ctqw_converged`) instead, ignoring `t_max`/
    `n_steps` for that propagator only -- `"ground_state"` is unaffected
    either way (see `quantum_vs_classical`'s own docstring for why this
    exists: `t_max=15` is orders of magnitude short of this criterion on
    every real target checked).

    Returns a list of row-dicts: `operator`, `tier` ("A"/"B"), `propagator`,
    `auc`, `floor_cleared` (bool, via `diagnostics.classify_failure` --
    reuses the existing chance-then-floor precedence, not a new
    comparison), `diagnosis`, `transport_pr` (participation ratio / N,
    REVIEW-2026-07-13c's transport diagnostic), `apo_holo_consistency`
    (always `None`/N/A here -- TASK-0092 not yet landed, per this task's
    own Intent Contract), `error` (`None` on success).
    """
    from .diagnostics import NO_FAILURE_DETECTED, classify_failure
    from .metrics import auc as _auc_fn
    from .propagators import ground_state_relaxation as _gsr_fn
    from .propagators import time_averaged_ctqw as _ctqw_fn
    from .propagators import time_averaged_ctqw_converged as _ctqw_converged_fn

    if use_converged_limit:
        propagator_fns = {
            "ctqw": lambda H, source_: _ctqw_converged_fn(H, source=source_, coherent=coherent),
            "ground_state": lambda H, source_: _gsr_fn(H, t_max, source=source_),
        }
    else:
        propagator_fns = {
            "ctqw": lambda H, source_: _ctqw_fn(H, t_max, source=source_, n_steps=n_steps, coherent=coherent),
            "ground_state": lambda H, source_: _gsr_fn(H, t_max, source=source_),
        }

    registry = _operator_registry()
    op_names = list(operators) if operators is not None else list(registry)
    prop_names = list(propagators)
    n_residues = len(coords)

    rows = []
    for op_name in op_names:
        if op_name not in registry:
            for prop_name in prop_names:
                rows.append({
                    "operator": op_name, "tier": None, "propagator": prop_name,
                    "auc": None, "floor_cleared": None, "diagnosis": None,
                    "transport_pr": None, "apo_holo_consistency": None,
                    "error": f"unknown operator {op_name!r}",
                })
            continue

        tier, build_fn = registry[op_name]
        try:
            H = build_fn(coords, bfactors, cutoff)
            if H.shape[0] != n_residues or H.shape[1] != n_residues:
                raise ValueError(
                    f"{op_name} returned a {H.shape} operator, incompatible with "
                    f"{n_residues} residues -- likely a 3N-dimensional Hessian "
                    "(the H13 family): cannot be indexed by residue without a "
                    "reduction this task does not invent (out of scope, harness "
                    "not new physics)"
                )
        except Exception as exc:
            for prop_name in prop_names:
                rows.append({
                    "operator": op_name, "tier": tier, "propagator": prop_name,
                    "auc": None, "floor_cleared": None, "diagnosis": None,
                    "transport_pr": None, "apo_holo_consistency": None,
                    "error": f"{type(exc).__name__}: {exc}",
                })
            continue

        for prop_name in prop_names:
            try:
                if prop_name not in propagator_fns:
                    raise ValueError(f"unknown propagator {prop_name!r}")
                p = propagator_fns[prop_name](H, source)
                auc_val = float(_auc_fn(p, pocket_label))
                # H/bfactors must be passed through -- omitting them silently
                # disables classify_failure's OPERATOR_DEGENERATE and
                # INSUFFICIENT_RESOLUTION checks (both require H to run
                # operator_diagnostics at all). Caught by re-reading this
                # function's own real-data output before trusting it: the
                # first version of this line omitted them, and every
                # CARDIAC_MYOSIN cell (N=950 > LARGE_N_THRESHOLD=800) came
                # back NO_FAILURE_DETECTED/BEATS_CHANCE_NOT_FLOOR instead of
                # the INSUFFICIENT_RESOLUTION the real submission pipeline
                # (run_challenge.py, which does pass H/bfactors) correctly
                # assigns that same target.
                diagnosis = classify_failure(
                    p, pocket_label, H=H, bfactors=bfactors, floor_scores=floor_scores,
                )
                rows.append({
                    "operator": op_name, "tier": tier, "propagator": prop_name,
                    "auc": auc_val, "floor_cleared": diagnosis == NO_FAILURE_DETECTED,
                    "diagnosis": diagnosis,
                    "transport_pr": _transport_participation_ratio(p),
                    "apo_holo_consistency": None, "error": None,
                })
            except Exception as exc:
                rows.append({
                    "operator": op_name, "tier": tier, "propagator": prop_name,
                    "auc": None, "floor_cleared": None, "diagnosis": None,
                    "transport_pr": None, "apo_holo_consistency": None,
                    "error": f"{type(exc).__name__}: {exc}",
                })
    return rows
