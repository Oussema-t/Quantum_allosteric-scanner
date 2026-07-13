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
    """
    from .propagators import time_averaged_ctqw, ground_state_relaxation

    occ_ctqw = time_averaged_ctqw(H, t_max, source=source, n_steps=n_steps)
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
) -> dict:
    """Default-parameter (not optimized -- see TASK-0008's Open Question on
    notebook Sec.8's coordinate-descent optimizer, out of this module's
    scope) comparison of H_new against the H10_disorder_suppressed
    baseline, both propagated by time-averaged CTQW.

    Returns {"H_new_default": metric_pack, "H10_disorder_suppressed":
    metric_pack}.
    """
    from .hamiltonians import build_H_new, build_H10
    from .propagators import time_averaged_ctqw

    H_new = build_H_new(coords, bfactors, cutoff=cutoff)
    H10 = build_H10(coords, bfactors, cutoff=cutoff)

    occ_new = time_averaged_ctqw(H_new, t_max, source=source, n_steps=n_steps)
    occ_10 = time_averaged_ctqw(H10, t_max, source=source, n_steps=n_steps)

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
    """
    from .propagators import haken_strobl
    from .metrics import auc as _auc

    omega_range = np.asarray(omega_range, dtype=float)
    labels_int = np.asarray(labels).astype(int)
    aucs = np.array([
        _auc(haken_strobl(H, t_max, gamma=float(w), source=source, rtol=rtol, atol=atol), labels_int)
        for w in omega_range
    ])
    finite = aucs[np.isfinite(aucs)]
    auc_range = float(finite.max() - finite.min()) if len(finite) else float("nan")

    return {
        "omega": omega_range,
        "auc": aucs,
        "auc_range": auc_range,
        "is_flat": bool(auc_range < flat_threshold) if np.isfinite(auc_range) else None,
        "flat_threshold": flat_threshold,
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
