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

`ensemble_void_score` (TASK-0229.005) extends this from one structure to an
ensemble — CrypToth's own H2.2 claim (Koseki et al. 2025, DOI
10.1021/acs.jcim.4c02111) that TDA over an ensemble outperforms TDA on a
single structure. It reuses `void_score`'s own shell-kernel scoring
(factored into `_score_from_dgm2` so both paths share one implementation)
and, since a single `ripser` call already returns every homology dimension
up to `maxdim`, also surfaces the top H1 lifetime per conformation as a
free diagnostic — H1 is *not* this module's primary observable (see the
module docstring above: a capped cavity is an H2 void, not an H1 loop), so
it is reported as a secondary check, not scored into a residue ranking.
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
    dgm2 = _censor_deaths(dgm2, thresh)
    return _score_from_dgm2(coords, dgm2, min_persistence=min_persistence, top_k=top_k)


def _censor_deaths(dgm: np.ndarray, cap: float | None) -> np.ndarray:
    """Right-censor a persistence diagram at the Rips filtration cap.

    Bug found and fixed here (surfaced by the ensemble path, which runs many
    more conformations than any single-structure caller ever had, but latent
    in the original single-structure code too): a class still alive at
    `thresh` gets `death=inf` from ripser, so its raw "lifetime" is `inf` and
    always wins top-k selection over any real, finite void — propagating NaN
    into `_score_from_dgm2`'s shell kernel (`(d - r)**2 / r**2` with `r=inf`).

    A class still open at `thresh` is not *un*-persistent — if anything it is
    at least as persistent as one that closes within the window, since its
    true lifetime is >= `thresh - birth`. Treating it as zero/excluded (the
    first fix attempted) silently discards that signal and flips some
    existing synthetic-fixture tests from pass to fail for the wrong reason
    (their constructed void's true death lies beyond `thresh=18`, so their
    old ">3.0" checks were, in fact, passing on `inf > 3.0`, not on a
    measured finite lifetime). Right-censoring — substituting `cap` for an
    unbounded death, the standard treatment for censored lifetime data — is
    the correct fix: it keeps these classes as strong (finite, cap-bounded)
    evidence of a void instead of erasing them.

    If `cap` is None/inf (no filtration cap given), there is no substitute
    value to censor to, and a genuinely-unbounded class is excluded instead.
    """
    if len(dgm) == 0:
        return dgm
    dgm = dgm.copy()
    if cap is not None and np.isfinite(cap):
        dgm[:, 1] = np.minimum(dgm[:, 1], cap)
    return dgm[np.isfinite(dgm[:, 1])]


def _score_from_dgm2(
    coords: np.ndarray, dgm2: np.ndarray, *, min_persistence: float, top_k: int,
) -> np.ndarray:
    """`void_score`'s own shell-kernel geometry, factored out so
    `ensemble_void_score` can reuse it against a precomputed (already
    `_censor_deaths`-ed) `dgm2` without a second `ripser` call per
    conformation."""
    coords = np.asarray(coords, float)
    n = len(coords)
    if len(dgm2) == 0:
        return np.zeros(n)
    lifetimes = dgm2[:, 1] - dgm2[:, 0]
    keep = lifetimes > min_persistence
    if not keep.any():
        return np.zeros(n)
    dgm2 = dgm2[keep]
    lifetimes = lifetimes[keep]
    order = np.argsort(lifetimes)[::-1][:top_k]

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
    'is there a void at all' summary, useful as a positive/negative gate.

    Classes still alive at `thresh` are right-censored to `thresh` before
    taking the max, not treated as infinitely persistent — see
    `_censor_deaths`'s docstring."""
    dgm2, _ = persistence_h2(coords, thresh=thresh)
    dgm2 = _censor_deaths(dgm2, thresh)
    if len(dgm2) == 0:
        return 0.0
    return float((dgm2[:, 1] - dgm2[:, 0]).max())


def ensemble_void_score(
    coords_list,
    *,
    thresh: float | None = 16.0,
    min_persistence: float = 0.0,
    top_k: int = 1,
):
    """Average `void_score` across an ensemble of conformations sharing the
    same residue order/correspondence — the ensemble extension of this
    module's own single-structure H2 signature (CrypToth's H2.2 claim,
    TASK-0229.005).

    One `ripser` call per conformation (not two): each call already returns
    every homology dimension up to `maxdim=2`, so the per-conformation top H1
    lifetime is read from the same result used for the H2 void score, at no
    extra persistence-computation cost.

    Returns `(ensemble_score, top_h1_per_conf, top_h2_per_conf)`:
      - `ensemble_score` (N,): mean of `void_score` over the ensemble.
      - `top_h1_per_conf`, `top_h2_per_conf` (n_conf,): per-conformation top
        lifetimes — an ensemble-level "was a real void/loop ever present"
        diagnostic, so a shorter-than-noise-floor ensemble can be gated
        honestly rather than presented as a confident ranking.
    """
    ripser = _ripser()
    n_conf = len(coords_list)
    n = len(coords_list[0])
    score_sum = np.zeros(n)
    top_h1 = np.zeros(n_conf)
    top_h2 = np.zeros(n_conf)
    for i, coords in enumerate(coords_list):
        coords = np.asarray(coords, float)
        res = ripser(coords, maxdim=2, thresh=(thresh if thresh else np.inf))
        dgm1, dgm2 = res["dgms"][1], res["dgms"][2]
        # Same right-censoring as top_h2_persistence/void_score: see
        # _censor_deaths's docstring.
        dgm1_c, dgm2_c = _censor_deaths(dgm1, thresh), _censor_deaths(dgm2, thresh)
        top_h1[i] = float((dgm1_c[:, 1] - dgm1_c[:, 0]).max()) if len(dgm1_c) else 0.0
        top_h2[i] = float((dgm2_c[:, 1] - dgm2_c[:, 0]).max()) if len(dgm2_c) else 0.0
        score_sum += _score_from_dgm2(coords, dgm2_c, min_persistence=min_persistence, top_k=top_k)
    return score_sum / n_conf, top_h1, top_h2
