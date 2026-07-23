"""Persistent H2 (void) detection on the apo contact complex — the correct
topological home for a *capped* cryptic pocket.

Motivation (REVIEW-panel-2026-07-20 / EXECUTION_PLAN Phase 1D.4, HYP-P12):
a filled/capped cryptic cavity is an H2 *void*, not an H1 loop (which is why
Falsifier D's grooves were invisible to cycle counting). Critically, an H2
void does NOT require its bounding residues to be graph-hop-far from one
another — so the coordinated-closure *graph-openness* premise failing 0/7
(TASK-0143) does not falsify this observable; it falsifies a different
(graph-distance) signature. This module tests the H2 signature directly.

Real persistence tooling (ripser) is mandatory per the phase spec — no
homemade Betti number is admissible as evidence. `ripser` is an added
dependency (pyproject); if unavailable the functions raise a clear ImportError
rather than silently degrading.

Output is a per-residue score (proximity to the most persistent void's
enclosing surface), directly comparable via `metrics.auc` against the holo
pocket label, exactly like every other observable in this project.
"""
from __future__ import annotations

import numpy as np


def _ripser():
    try:
        from ripser import ripser
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "persistent_voids requires `ripser` (pip install ripser). "
            "It is listed in pyproject as an optional persistence dependency."
        ) from e
    return ripser


def persistence_h2(coords: np.ndarray, *, thresh: float | None = None):
    """Vietoris-Rips persistence up to H2 on Ca coordinates.

    Returns the H2 persistence diagram (array of [birth, death] rows) and the
    full ripser result dict (kept so a caller can inspect H0/H1 too). `thresh`
    caps the Rips filtration radius (A); None lets ripser choose. Capping is
    strongly recommended on large N for tractability — H2 on a full protein is
    the expensive dimension.
    """
    ripser = _ripser()
    res = ripser(np.asarray(coords, float), maxdim=2, thresh=(thresh if thresh else np.inf))
    dgm2 = res["dgms"][2]
    return dgm2, res


def void_score(
    coords: np.ndarray,
    *,
    thresh: float | None = 16.0,
    min_persistence: float = 0.0,
    top_k: int = 1,
) -> np.ndarray:
    """Per-residue void score, (N,): higher = closer to the enclosing surface
    of the most persistent H2 void(s).

    Method: compute the H2 diagram; take the `top_k` most persistent classes.
    For each, the void's characteristic scale is its birth radius `b` (the Rips
    radius at which the enclosing 2-cycle first closes). Residues lying on the
    void's shell are those whose local neighborhood radius is ~b and which sit
    near the void's centroid at distance ~ the class's geometric radius. Since
    ripser does not return cycle representatives for H2 by default, the void
    centroid is estimated as the mean of the coordinates that become mutually
    within `death` radius near the class's lifetime (a coordinate-space proxy),
    and each residue is scored by a shell-membership kernel peaked at the void
    radius. The score is intentionally a *geometric* lining score, not a binary
    membership, so it is rankable by AUC.

    If no H2 class survives `min_persistence`, returns all-zeros (the honest
    "no void detected" output — do not fabricate a ranking from noise).
    """
    dgm2, _res = persistence_h2(coords, thresh=thresh)
    if len(dgm2) == 0:
        return np.zeros(len(coords))
    lifetimes = dgm2[:, 1] - dgm2[:, 0]
    keep = lifetimes > min_persistence
    if not keep.any():
        return np.zeros(len(coords))
    dgm2 = dgm2[keep]
    lifetimes = lifetimes[keep]
    order = np.argsort(lifetimes)[::-1][:top_k]

    coords = np.asarray(coords, float)
    n = len(coords)
    score = np.zeros(n)
    for oi in order:
        birth, death = dgm2[oi]
        # Void radius ~ death (the scale at which the cavity is filled in).
        # Estimate the void centre robustly: the point maximising the number of
        # residues lying in a shell [0.6*death, 1.1*death] around it. Grid-free
        # estimate — use the residue whose shell membership is largest as centre
        # seed, then refine to that shell's centroid.
        r = float(death)
        best_c, best_cnt = coords.mean(0), -1
        for c in coords:
            d = np.linalg.norm(coords - c, axis=1)
            cnt = int(((d > 0.55 * r) & (d < 1.15 * r)).sum())
            if cnt > best_cnt:
                best_cnt, best_c = cnt, c
        d = np.linalg.norm(coords - best_c, axis=1)
        # shell kernel peaked at r: residues at distance ~r from centre line the void
        w = lifetimes[oi]
        score += w * np.exp(-((d - r) ** 2) / (2 * (0.25 * r) ** 2))
    return score


def top_h2_persistence(coords: np.ndarray, *, thresh: float | None = 16.0) -> float:
    """The single most persistent H2 lifetime (0.0 if none) — a scalar
    'is there a void at all' summary, useful as a positive/negative gate."""
    dgm2, _ = persistence_h2(coords, thresh=thresh)
    if len(dgm2) == 0:
        return 0.0
    return float((dgm2[:, 1] - dgm2[:, 0]).max())
