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
# Sec.10 -- quantum-walk vs classical-heat head-to-head (same H)
# ---------------------------------------------------------------------------

def quantum_vs_classical(
    H: np.ndarray,
    source,
    labels: np.ndarray | None = None,
    t_max: float = 15.0,
    n_steps: int = 500,
) -> dict:
    """CTQW vs classical heat-kernel on the *same* Hamiltonian H.

    CTQW is coherent/oscillatory (no decay), so it is compared via its
    time-average over [0, t_max] (`propagators.time_averaged_ctqw`) -- a
    single-time snapshot would be an arbitrary phase pick. The heat kernel
    monotonically relaxes toward a stationary distribution, so a single
    evaluation at t_max (`propagators.heat`) is already representative and
    does not need the same averaging (there is no analogous
    time-averaged-heat helper in propagators.py by design, not by
    omission).

    Returns a dict with "ctqw" and "heat" sub-dicts (each a metric pack, or
    just the occupation vector if `labels` is None).
    """
    from .propagators import time_averaged_ctqw, heat

    occ_ctqw = time_averaged_ctqw(H, t_max, source=source, n_steps=n_steps)
    occ_heat = heat(H, t_max, source=source)

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
