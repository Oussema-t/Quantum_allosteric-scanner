"""TASK-0187 -- does undirected ENM ("wobbling") conformational sampling
create new contact-graph edges that shorten the active-site<->pocket
hop-distance below its static-apo value, *specifically* (not as generic
noise on the whole contact graph)?

Deliberately undirected and topology-focused -- see TASK-0187's own
"Why this matters, and how it differs from what's already filed" section
for the boundary against TASK-0015 (one directed apo->holo deformation)
and TASK-0185 (cavity/volume, not graph topology).

Reuses, does not re-derive:
  - `superpose.anm_modes` for the ANM Hessian eigendecomposition (already
    confirmed a proper 3N x 3N operator, TASK-0005's Open Question).
  - `baselines.hop_from_seed` for BFS hop-distance on the standard binary
    8.0 A contact-graph convention (TASK-0067).
  - `plant.select_distal_patch` for the matched-decoy draw (TASK-0167.001,
    already validated to be a fair, non-trivial, floor-blind decoy).
  - `hamiltonians.contact_matrix` for the weighted adjacency `select_distal_patch`
    itself requires as an interface argument.

Sampling method (Step 1): closed-form equipartition Gaussian draws in ANM
mode space -- amplitude_k ~ N(0, sqrt(kT/lambda_k)) -- no MD, no
integrator, same method as TASK-0185's reference prototype
(`.ai/reviews/2026-07-31-rev-8/conformational_search_prototype_REFERENCE.py`).
Unlike that prototype, this module's sampler is cross-checked against the
analytic per-residue MSF before any downstream use (TASK-0187's own
blocking constraint -- the prototype has no such check).
"""
from __future__ import annotations

from typing import NamedTuple, Optional

import numpy as np

from .baselines import hop_from_seed
from .hamiltonians import contact_matrix
from .plant import select_distal_patch
from .superpose import anm_modes


def analytic_msf(eigvals: np.ndarray, eigvecs: np.ndarray, kT: float = 1.0) -> np.ndarray:
    """Per-residue analytic ANM mean-square fluctuation, in the same
    unit-kappa convention as `superpose.calibrate_kappa`:

        MSF_i = kT * sum_k ||v_ik||^2 / lambda_k

    `eigvals`/`eigvecs` are `anm_modes`'s own output (rigid-body zero
    modes already dropped). Returns (N,).
    """
    n_modes = eigvecs.shape[1]
    n = eigvecs.shape[0] // 3
    v3 = eigvecs.reshape(n, 3, n_modes)
    per_mode_sq = (v3 ** 2).sum(axis=1)          # (N, n_modes)
    return kT * (per_mode_sq / eigvals).sum(axis=1)


def equipartition_ensemble(
    coords: np.ndarray,
    *,
    cutoff: float = 8.0,
    n_modes: int = 20,
    kT: float = 1.0,
    n_samples: int = 2000,
    rng: Optional[np.random.Generator] = None,
) -> "EnsembleResult":
    """Draw `n_samples` undirected equilibrium conformations from the ANM
    Gaussian ensemble about `coords` (closed-form, no trajectory).

    Returns an `EnsembleResult` carrying the raw per-sample displacements
    (N, 3) each, plus the mode data needed for `analytic_msf` -- the
    caller runs `msf_cross_check` before trusting anything downstream,
    this function does not gate itself (kept a pure sampler, single
    responsibility).
    """
    rng = rng or np.random.default_rng(0)
    n = len(coords)
    eigvals, eigvecs = anm_modes(coords, cutoff=cutoff, n_modes=n_modes)

    amps = rng.normal(size=(n_samples, len(eigvals))) * np.sqrt(kT / eigvals)
    disp_flat = amps @ eigvecs.T                    # (n_samples, 3N)
    displacements = disp_flat.reshape(n_samples, n, 3)

    return EnsembleResult(
        displacements=displacements, eigvals=eigvals, eigvecs=eigvecs, kT=kT,
    )


class EnsembleResult(NamedTuple):
    displacements: np.ndarray   # (n_samples, N, 3)
    eigvals: np.ndarray         # (n_modes,)
    eigvecs: np.ndarray         # (3N, n_modes)
    kT: float


def msf_cross_check(
    ensemble: "EnsembleResult",
    *,
    min_pearson_r: float = 0.90,
    max_median_rel_error: float = 0.25,
) -> dict:
    """Blocking gate (TASK-0187 Constraints): empirical per-residue MSF
    over the sampled ensemble must match the analytic GNM/ANM MSF
    prediction, or the sampler is wrong and nothing downstream (Step 2+)
    is trustworthy.

    Two checks, both must pass for `ok=True`:
      - Pearson r between empirical and analytic per-residue MSF >=
        `min_pearson_r` (shape agreement -- flexible/rigid residues
        ranked consistently).
      - median relative error |empirical - analytic| / analytic <=
        `max_median_rel_error` (scale agreement -- not just correlated,
        actually the same magnitude).

    Does not raise; returns a dict so the caller (script) decides how to
    fail loudly, per this project's convention of an explicit, reported
    gate rather than a buried exception.
    """
    empirical = (ensemble.displacements ** 2).sum(axis=2).mean(axis=0)  # (N,)
    analytic = analytic_msf(ensemble.eigvals, ensemble.eigvecs, kT=ensemble.kT)

    r = float(np.corrcoef(empirical, analytic)[0, 1])
    rel_error = np.abs(empirical - analytic) / analytic
    median_rel_error = float(np.median(rel_error))

    ok = (r >= min_pearson_r) and (median_rel_error <= max_median_rel_error)
    return {
        "ok": ok,
        "pearson_r": r,
        "median_rel_error": median_rel_error,
        "min_pearson_r": min_pearson_r,
        "max_median_rel_error": max_median_rel_error,
        "n_samples": int(ensemble.displacements.shape[0]),
    }


def patch_hop_distance(coords: np.ndarray, seed_idx: np.ndarray, patch_idx: np.ndarray, cutoff: float = 8.0) -> float:
    """Min BFS hop-distance from the seed set to any residue in `patch_idx`
    -- the same scalar-per-pocket convention TASK-0186 reports (e.g.
    "PTP1B... min spatial-hop = 2"). `n + 1` if every patch residue is
    unreachable (same `hop_from_seed` convention)."""
    neg_hops = hop_from_seed(coords, source=seed_idx, cutoff=cutoff)
    return float((-neg_hops)[patch_idx].min())


def ensemble_hop_matrix(
    ensemble: "EnsembleResult", coords0: np.ndarray, seed_idx: np.ndarray, *, cutoff: float = 8.0,
) -> np.ndarray:
    """Per-residue hop-distance from `seed_idx`, one row per ensemble
    sample -- (n_samples, N). Computed **once per sample**, shared by
    every patch (real pocket + every decoy) `shortcut_rate` is asked
    about, rather than rebuilding the same displaced contact graph once
    per patch. At PTP1B's scale (N~300, n_samples=2000, n_decoy=30) that
    is a real cost: rebuilding per-patch would mean 31x redundant graph
    builds for identical displaced coordinates.
    """
    n_samples = ensemble.displacements.shape[0]
    n = len(coords0)
    hops = np.empty((n_samples, n))
    for i in range(n_samples):
        displaced = coords0 + ensemble.displacements[i]
        hops[i] = -hop_from_seed(displaced, source=seed_idx, cutoff=cutoff)
    return hops


def shortcut_rate(
    hop_matrix: np.ndarray,
    coords0: np.ndarray,
    seed_idx: np.ndarray,
    patch_idx: np.ndarray,
    *,
    cutoff: float = 8.0,
) -> dict:
    """Fraction of the ensemble's samples (rows of `hop_matrix`, from
    `ensemble_hop_matrix`) where `patch_idx`'s hop-distance from
    `seed_idx` is strictly shorter than that patch's own static-apo
    (undisplaced) hop-distance -- the "shortcut" event, scored against
    the patch's *own* baseline so real-pocket and decoy patches starting
    at different static hop-distances remain a fair comparison (each is
    only asked "did dynamics beat your own static number").
    """
    static_hop = patch_hop_distance(coords0, seed_idx, patch_idx, cutoff=cutoff)
    sample_hops = hop_matrix[:, patch_idx].min(axis=1)

    events = sample_hops < static_hop
    return {
        "static_hop": static_hop,
        "rate": float(events.mean()),
        "min_sample_hop": float(sample_hops.min()),
        "sample_hops": sample_hops,
    }


def specificity_test(
    ensemble: "EnsembleResult",
    coords0: np.ndarray,
    seed_idx: np.ndarray,
    real_patch_idx: np.ndarray,
    *,
    cutoff: float = 8.0,
    n_decoy: int = 30,
    decoy_hop_percentile: float = 60.0,
    decoy_max_floor_auc: float = 0.5,
    effect_size_floor: float = 0.10,
    rng: Optional[np.random.Generator] = None,
    hop_matrix: Optional[np.ndarray] = None,
) -> dict:
    """TASK-0187's pre-registered specificity gate (see task file
    Constraints for the full derivation). Draws `n_decoy` matched decoys
    via `plant.select_distal_patch` (same size as `real_patch_idx`,
    genuinely distal + floor-blind, TASK-0167.001's own admission
    criteria -- not an exact same-static-hop match, `select_distal_patch`
    selects by hop *percentile* not exact hop value; `shortcut_rate`'s
    own-baseline scoring makes an exact match unnecessary for validity).

    `hop_matrix`: pass a matrix already computed by `ensemble_hop_matrix`
    (e.g. the caller's own Step 2 pass) to avoid rebuilding the same
    per-sample displaced contact graphs a second time; computed fresh if
    omitted.

    PASS requires BOTH:
      (a) real_pocket rate > 95th percentile of the `n_decoy` decoy rates
      (b) real_pocket rate - median(decoy rates) >= effect_size_floor
    """
    rng = rng or np.random.default_rng(0)
    size = len(real_patch_idx)
    W = contact_matrix(coords0, cutoff=cutoff, weight="invdist")
    if hop_matrix is None:
        hop_matrix = ensemble_hop_matrix(ensemble, coords0, seed_idx, cutoff=cutoff)

    real = shortcut_rate(hop_matrix, coords0, seed_idx, real_patch_idx, cutoff=cutoff)

    decoy_rates = []
    decoy_patches = []
    for _ in range(n_decoy):
        patch = select_distal_patch(
            coords0, W, seed_idx, size, rng,
            cutoff=cutoff, hop_percentile=decoy_hop_percentile, max_floor_auc=decoy_max_floor_auc,
        )
        decoy_patches.append(patch)
        decoy_rates.append(shortcut_rate(hop_matrix, coords0, seed_idx, patch, cutoff=cutoff)["rate"])

    decoy_rates = np.asarray(decoy_rates)
    p95 = float(np.percentile(decoy_rates, 95))
    median_decoy = float(np.median(decoy_rates))
    effect_size = real["rate"] - median_decoy

    significant = real["rate"] > p95
    material = effect_size >= effect_size_floor
    passed = bool(significant and material)

    return {
        "passed": passed,
        "significant": bool(significant),
        "material": bool(material),
        "real_rate": real["rate"],
        "real_static_hop": real["static_hop"],
        "decoy_rates": decoy_rates,
        "decoy_p95": p95,
        "decoy_median": median_decoy,
        "effect_size": effect_size,
        "effect_size_floor": effect_size_floor,
        "n_decoy": n_decoy,
        "decoy_patches": decoy_patches,
    }
