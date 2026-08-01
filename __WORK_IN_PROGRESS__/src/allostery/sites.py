"""TASK-0180 -- spatial deduplication of the top-scoring residues into
ranked *sites*, plus site-level hit metrics with their own chance level
and proximity floor.

`report.assemble_hit_list` (`report.py:77`) returns the top-5 *residues*
by score with no spatial deduplication (checked directly) -- because every
observable in this project is spatially smooth, the top 5 are frequently
5 neighbours in one groove, i.e. one predicted site reported as five. This
module fixes that: cluster the top-scoring residues into spatially
contiguous candidate sites (single-linkage, or DBSCAN as an alternate
method -- both use the same distance cutoff, no new geometric constant
invented beyond TASK-0067's own retained contact scale, see
`cluster_sites`'s own docstring), aggregate each cluster's score by its
**mean**, never its max (a max-over-members statistic reintroduces the
winner's-curse structure TASK-0131/TASK-0123 both found inflates this
project's statistics), and rank clusters, not residues.

A site-level hit metric is only interpretable with its own chance level
and proximity floor alongside it -- `main`'s `pocket_pk(tol=6.0)` dilates
the label by 6 A (27.7% of a KRAS-sized protein, chance P@5=0.26, a pure
distance-to-seed predictor P@5=0.66, measured 2026-07-28 external review
Sec.8) and reports neither; this module does not repeat that defect.
`site_chance_level` reruns the identical pipeline on random scores;
`site_proximity_floor` reruns it on `baselines.euclid_from_seed_centroid`
(the same distance-to-seed ranker the review measured) -- without both,
a bare site-level hit-rate number is exactly as uninterpretable as the
defect being fixed.

`site_knob_sweep` follows `superpose.cumulative_overlap_gate`'s own
GO/NO_GO/UNSTABLE convention (TASK-0075): a full per-combination grid,
never a point estimate. Its `linkage_cutoffs` default is deliberately
wide (1.5-10 A), not just TASK-0067's retained 8.0 A -- TASK-0067's own
sweep only tested a *contact-graph* cutoff, a different geometric
question from *clustering already-selected top-scoring residues*; 8.0 A
is not an actually-derived value for this specific use, so the sweep
itself is this module's empirical check on that default, not just a
stability report (see this module's own reconciliation note,
`SITES_RECONCILIATION.md`).
"""
from __future__ import annotations

from typing import Sequence

import numpy as np

# TASK-0067's retained contact-graph cutoff (`.ai/tasks/DONE/TASK-0067-*`) --
# reused here as the *starting* default for spatial clustering pending the
# empirical check `site_knob_sweep`'s widened grid runs (see module
# docstring); not re-derived, since TASK-0067 already settled that no
# cutoff in {7.5, 8.0, 10.0} showed a significant win for the contact
# graph -- this module tests whether that finding transfers to clustering.
DEFAULT_LINKAGE_CUTOFF = 8.0


def _cluster_labels(coords: np.ndarray, linkage_cutoff: float, method: str) -> np.ndarray:
    """Cluster labels for `coords` at `linkage_cutoff` -- single-linkage
    (headline, per this task's own Open Questions: "pre-commit to
    single-linkage") or DBSCAN (the alternate method those same Open
    Questions ask to try and report). Both are `sklearn.cluster`, already
    a dependency of this package (`coarse.py::coarse_grain`'s own
    `SpectralClustering` import) -- no new library introduced.

    A single residue or an empty array short-circuits: `AgglomerativeClustering`
    raises on n_samples < 2, and there is nothing to cluster either way.
    """
    n = len(coords)
    if n == 0:
        return np.empty(0, dtype=int)
    if n == 1:
        return np.zeros(1, dtype=int)

    if method == "single_linkage":
        from sklearn.cluster import AgglomerativeClustering

        model = AgglomerativeClustering(
            linkage="single", distance_threshold=linkage_cutoff, n_clusters=None,
        )
        return model.fit_predict(coords)
    if method == "dbscan":
        from sklearn.cluster import DBSCAN

        # min_samples=1: DBSCAN's own "noise" concept (a point with too
        # few neighbours) would double-apply this module's already-
        # separate `min_cluster_size` filter -- every top-m residue
        # should land in some cluster, and cluster_sites' own size filter
        # is the single place a candidate is dropped for being too small.
        model = DBSCAN(eps=linkage_cutoff, min_samples=1)
        return model.fit_predict(coords)
    raise ValueError(f"unknown clustering method {method!r}, must be 'single_linkage' or 'dbscan'")


def cluster_sites(
    coords: np.ndarray,
    scores: np.ndarray,
    *,
    m: int | None = None,
    m_frac: float = 0.125,
    linkage_cutoff: float = DEFAULT_LINKAGE_CUTOFF,
    min_cluster_size: int = 2,
    method: str = "single_linkage",
    top_n: int = 5,
    resnums: np.ndarray | None = None,
) -> dict:
    """Cluster the top-`m` scoring residues into spatially contiguous
    candidate sites, rank clusters (not residues) by **mean** member
    score, and return the top `top_n`.

    `m` is `round(m_frac * N)` when not given directly -- `m_frac` in the
    task's own "10-15% of N" range, `0.125` its midpoint, a stated knob
    (swept by `site_knob_sweep`, never silently fixed as the only value
    tried).

    Clusters smaller than `min_cluster_size` are dropped before ranking
    (a druggable pocket is not one residue, per this task's own Design) --
    `n_dropped_small` in the returned dict counts how many were removed,
    so a caller can see this filter actually did something rather than
    guess.

    Each surviving cluster (dict): `member_indices` (local array indices,
    int list), `member_resnums` (or `None` if `resnums` wasn't given),
    `centroid` ((3,) float list, mean of member coords), `mean_score`
    (the ranking key), `max_score` (reported alongside, never the ranking
    key -- see module docstring), `size`, `rank` (1-indexed, after
    sorting by `mean_score` descending).

    Returns `{"top_sites": [...], "all_sites": [...], "m", "linkage_cutoff",
    "min_cluster_size", "method", "n_clusters_total", "n_dropped_small"}`
    -- `all_sites` (every surviving cluster, not just the top `top_n`) is
    kept alongside `top_sites` since `site_knob_sweep`/diagnostics may
    want the full set, not just the headline five.
    """
    coords = np.asarray(coords, dtype=float)
    scores = np.asarray(scores, dtype=float)
    n = len(scores)
    if len(coords) != n:
        raise ValueError(f"coords ({len(coords)}) and scores ({n}) length mismatch")

    m_eff = int(m) if m is not None else max(1, round(m_frac * n))
    m_eff = min(m_eff, n)

    top_idx = np.argsort(-scores)[:m_eff]
    top_coords = coords[top_idx]
    labels = _cluster_labels(top_coords, linkage_cutoff, method)

    unique_labels = [lab for lab in np.unique(labels) if lab != -1]  # -1: DBSCAN noise
    n_clusters_total = len(unique_labels)

    clusters = []
    for lab in unique_labels:
        member_local = top_idx[labels == lab]
        size = int(len(member_local))
        if size < min_cluster_size:
            continue
        member_scores = scores[member_local]
        clusters.append({
            "member_indices": member_local.tolist(),
            "member_resnums": (
                np.asarray(resnums)[member_local].tolist() if resnums is not None else None
            ),
            "centroid": coords[member_local].mean(axis=0).tolist(),
            "mean_score": float(member_scores.mean()),
            "max_score": float(member_scores.max()),
            "size": size,
        })

    clusters.sort(key=lambda c: -c["mean_score"])
    for rank, c in enumerate(clusters, start=1):
        c["rank"] = rank

    return {
        "top_sites": clusters[:top_n],
        "all_sites": clusters,
        "m": m_eff,
        "linkage_cutoff": linkage_cutoff,
        "min_cluster_size": min_cluster_size,
        "method": method,
        "n_clusters_total": n_clusters_total,
        "n_dropped_small": n_clusters_total - len(clusters),
    }


def site_hit_metrics(
    sites: Sequence[dict],
    pocket_mask: np.ndarray,
    coords: np.ndarray,
    *,
    overlap_thresholds: Sequence[int] = (1, 3),
) -> dict:
    """Site-level hit metrics against `pocket_mask` -- a genuine,
    defensible metric per this task's own Design: a predicted site counts
    as a hit if it overlaps the label by >= a threshold (both >=1 and >=3
    reported, never just one), plus centroid-to-nearest-pocket-residue
    distance. Deliberately does **not** dilate `pocket_mask` the way
    `main`'s `pocket_pk(tol=6.0)` does (see module docstring).

    `sites` is `cluster_sites(...)["top_sites"]` (or any list of dicts
    with `member_indices`/`centroid`/`rank`) -- this function does not
    call `cluster_sites` itself, so `site_chance_level`/`site_proximity_
    floor` can pass a differently-scored `sites` list through the exact
    same metric without duplicating this logic.

    Returns `{"per_site": [...], "n_hit_at_<t>": int, ..., "n_sites",
    "mean_centroid_distance"}` for each `t` in `overlap_thresholds`.
    `mean_centroid_distance`/per-site `centroid_distance` is `nan` when
    `pocket_mask` has no positives (nothing to measure distance to).
    """
    pocket_mask = np.asarray(pocket_mask, dtype=bool)
    coords = np.asarray(coords, dtype=float)
    pocket_idx = np.where(pocket_mask)[0]
    pocket_coords = coords[pocket_idx]

    per_site = []
    for site in sites:
        member_idx = np.asarray(site["member_indices"], dtype=int)
        overlap = int(pocket_mask[member_idx].sum()) if len(member_idx) else 0
        if len(pocket_coords):
            centroid = np.asarray(site["centroid"], dtype=float)
            centroid_distance = float(np.linalg.norm(pocket_coords - centroid, axis=1).min())
        else:
            centroid_distance = float("nan")
        entry = {
            "rank": site.get("rank"),
            "overlap": overlap,
            "centroid_distance": centroid_distance,
        }
        for t in overlap_thresholds:
            entry[f"hit_at_{t}"] = bool(overlap >= t)
        per_site.append(entry)

    out: dict = {"per_site": per_site, "n_sites": len(per_site)}
    for t in overlap_thresholds:
        out[f"n_hit_at_{t}"] = sum(1 for s in per_site if s[f"hit_at_{t}"])
    finite_dists = [s["centroid_distance"] for s in per_site if np.isfinite(s["centroid_distance"])]
    out["mean_centroid_distance"] = float(np.mean(finite_dists)) if finite_dists else float("nan")
    return out


def site_chance_level(
    coords: np.ndarray,
    n_residues: int,
    pocket_mask: np.ndarray,
    *,
    n_null: int = 200,
    overlap_thresholds: Sequence[int] = (1, 3),
    rng: np.random.Generator | None = None,
    cluster_kwargs: dict | None = None,
) -> dict:
    """Null distribution of the site-hit rate: `n_null` independent random
    score fields, each pushed through the *identical* `cluster_sites` +
    `site_hit_metrics` pipeline the real scores use (`cluster_kwargs`
    forwarded verbatim to `cluster_sites`) -- re-invoking the whole
    pipeline per replicate, not scoring once and reusing, mirrors
    `diagnostics.permutation_null`'s own "a leak baked into the scorer
    itself... is caught too" reasoning applied to clustering instead of a
    scorer.

    Returns `{"n_null", "hit_rate_at_<t>", "hit_rate_at_<t>_ci", ...}` for
    each `t` in `overlap_thresholds` -- `hit_rate_at_<t>` is the fraction
    of null runs where at least one of the top-5 sites hits at that
    threshold; `_ci` is the 2.5/97.5 percentile band (matches `metrics.
    block_bootstrap_ci`'s reporting convention).
    """
    coords = np.asarray(coords, dtype=float)
    cluster_kwargs = dict(cluster_kwargs or {})
    rng = rng if rng is not None else np.random.default_rng(42)

    hit_flags = {t: np.empty(n_null, dtype=bool) for t in overlap_thresholds}
    for i in range(n_null):
        null_scores = rng.random(n_residues)
        sites = cluster_sites(coords, null_scores, **cluster_kwargs)["top_sites"]
        metrics = site_hit_metrics(sites, pocket_mask, coords, overlap_thresholds=overlap_thresholds)
        for t in overlap_thresholds:
            hit_flags[t][i] = metrics[f"n_hit_at_{t}"] > 0

    out: dict = {"n_null": n_null}
    for t in overlap_thresholds:
        arr = hit_flags[t].astype(float)
        out[f"hit_rate_at_{t}"] = float(arr.mean())
        lo, hi = np.percentile(arr, [2.5, 97.5])
        out[f"hit_rate_at_{t}_ci"] = (float(lo), float(hi))
    return out


def site_proximity_floor(
    coords: np.ndarray,
    source,
    pocket_mask: np.ndarray,
    *,
    overlap_thresholds: Sequence[int] = (1, 3),
    cluster_kwargs: dict | None = None,
) -> dict:
    """The site-level proximity floor: `baselines.euclid_from_seed_
    centroid` (the same distance-to-seed ranker `run_target`'s own
    residue-level `floor_scores` list already uses, and the one measured
    in the 2026-07-28 external review, Sec.8, to reach P@5=0.66 under a
    6 A-dilated label) pushed through the *identical* clustering + hit-
    metric pipeline the real scores use. Without this, a site-level hit
    rate is exactly as uninterpretable as the defect this module fixes
    (see module docstring).

    This is also the direct input for this task's own degenerate-case
    regression test: since `euclid_from_seed_centroid` is a smooth,
    monotonically-decreasing function of distance from one point,
    clustering its own top-m residues must yield exactly one contiguous
    site near the seed, never five (`cluster_sites`'s own single-linkage
    chaining is expected to do this on a spatially smooth field -- if it
    doesn't, that is the exact regression TASK-0180 exists to catch).

    Returns `{"sites": cluster_sites(...), "hit_metrics": site_hit_metrics(...)}`.
    """
    from .baselines import euclid_from_seed_centroid

    coords = np.asarray(coords, dtype=float)
    cluster_kwargs = dict(cluster_kwargs or {})
    floor_scores = euclid_from_seed_centroid(coords, source)
    sites = cluster_sites(coords, floor_scores, **cluster_kwargs)
    metrics = site_hit_metrics(sites["top_sites"], pocket_mask, coords, overlap_thresholds=overlap_thresholds)
    return {"sites": sites, "hit_metrics": metrics}


def site_knob_sweep(
    coords: np.ndarray,
    scores: np.ndarray,
    pocket_mask: np.ndarray,
    *,
    m_fracs=(0.10, 0.125, 0.15),
    linkage_cutoffs=(1.5, 2.0, 3.0, 5.0, 7.5, 8.0, 10.0),
    min_cluster_sizes=(2, 3),
    methods=("single_linkage",),
    stability_threshold: float = 0.5,
    top_n: int = 5,
) -> dict:
    """Knob-spread verdict for the top-5 site set, mirroring `superpose.
    cumulative_overlap_gate`'s own GO/NO_GO/UNSTABLE convention (TASK-0075):
    a full per-combination grid is always returned, never collapsed to a
    point estimate.

    `linkage_cutoffs`' default deliberately spans 1.5-10 A, not just
    TASK-0067's retained 8.0 A -- see module docstring: this sweep is
    also this module's empirical check on whether 8.0 A is actually the
    right scale for clustering already-selected top-scoring residues (a
    different question from TASK-0067's contact-graph sweep), not merely
    a stability report around an assumed default.

    Stability is `report.jaccard_stability` (this package's existing
    Jaccard convention, not reinvented) applied to each combination's set
    of residue indices covered by its own top-`top_n` sites. Verdict is
    `STABLE` if the minimum pairwise Jaccard across the whole grid clears
    `stability_threshold`, `UNSTABLE` otherwise -- per TASK-0075's own
    "emit UNSTABLE when the knobs decide the top-5 rather than the
    scores" requirement.

    Returns `{"verdict", "jaccard_min", "jaccard_mean", "n_combos",
    "stability_threshold", "grid"}` -- `grid` entries carry the knobs used
    plus `n_sites`/`member_indices`, the actual evidence behind the
    verdict.
    """
    from .report import jaccard_stability

    grid = []
    membership_sets = []
    for method in methods:
        for m_frac in m_fracs:
            for linkage_cutoff in linkage_cutoffs:
                for min_cluster_size in min_cluster_sizes:
                    result = cluster_sites(
                        coords, scores, m_frac=m_frac, linkage_cutoff=linkage_cutoff,
                        min_cluster_size=min_cluster_size, method=method, top_n=top_n,
                    )
                    members = sorted({idx for site in result["top_sites"] for idx in site["member_indices"]})
                    grid.append({
                        "method": method, "m_frac": m_frac, "linkage_cutoff": linkage_cutoff,
                        "min_cluster_size": min_cluster_size,
                        "n_sites": len(result["top_sites"]), "member_indices": members,
                    })
                    membership_sets.append(members)

    stability = jaccard_stability(membership_sets)
    verdict = "STABLE" if stability["min"] >= stability_threshold else "UNSTABLE"

    return {
        "verdict": verdict,
        "jaccard_min": stability["min"],
        "jaccard_mean": stability["mean"],
        "n_combos": len(grid),
        "stability_threshold": stability_threshold,
        "grid": grid,
    }


# ---------------------------------------------------------------------------
# end_to_end.json -- the per-target TASK-0176 statement (apo -> predicted
# pocket -> verified in holo), every clause filled or explicitly marked
# unavailable, per this task's own Intent Contract.
# ---------------------------------------------------------------------------

def end_to_end_statement(
    target_name: str,
    apo_pdb: str | None,
    holo_pdb: str | None,
    top_sites: Sequence[dict],
    site_hit: dict,
    label_source: str,
) -> str:
    """Render the TASK-0176 sentence ("from `apo_pdb` alone we predict
    pocket P, and P is/is not the pocket `holo_pdb` shows") for one
    target -- every clause filled or explicitly marked unavailable, never
    silently dropped, matching this package's existing missing-key-safe
    convention (`report.verdict_template`'s own "a missing key renders
    N/A" design)."""
    apo_desc = apo_pdb or "an unspecified apo structure"
    holo_desc = holo_pdb or "an unspecified holo structure"

    if not top_sites:
        return (
            f"From {apo_desc} alone, no candidate site survived clustering for "
            f"{target_name} -- no pocket prediction to state."
        )

    top = top_sites[0]
    resnums = top.get("member_resnums")
    site_desc = f"residues {resnums}" if resnums else f"local indices {top['member_indices']}"

    per_site = site_hit.get("per_site") if site_hit else None
    hit_entry = per_site[0] if per_site else None
    if hit_entry is None:
        overlap_desc = "overlap with the labeled pocket is unavailable"
    elif hit_entry["hit_at_1"]:
        overlap_desc = (
            f"overlaps the {label_source} pocket derived from {holo_desc} "
            f"({hit_entry['overlap']} shared residue(s))"
        )
    else:
        dist = hit_entry["centroid_distance"]
        dist_desc = f"{dist:.1f} A away" if np.isfinite(dist) else "distance unavailable"
        overlap_desc = f"does not overlap the {label_source} pocket derived from {holo_desc} (centroid {dist_desc})"

    return f"From {apo_desc} alone we predict pocket {site_desc} for {target_name}, which {overlap_desc}."


def end_to_end_record(
    *,
    target_name: str,
    apo_pdb: str | None,
    holo_pdb: str | None,
    label_source: str,
    cluster_result: dict,
    site_hit: dict,
    chance: dict,
    floor: dict,
    knob_spread: dict,
    residue_level: dict,
) -> dict:
    """Assemble one target's full `end_to_end.json` record -- carries the
    already-computed residue-level AUC/floor/CI/diagnosis through
    (`residue_level`, the caller's own `verdict.json` numbers, not
    recomputed here) alongside every site-level deliverable this task
    adds, plus the rendered `end_to_end_statement`."""
    top_sites = cluster_result["top_sites"]
    return {
        "target": target_name,
        "apo_pdb": apo_pdb,
        "holo_pdb": holo_pdb,
        "label_source": label_source,
        "predicted_sites": [
            {
                "rank": s["rank"],
                "resnums": s["member_resnums"],
                "member_indices": s["member_indices"],
                "mean_score": s["mean_score"],
                "max_score": s["max_score"],
                "size": s["size"],
            }
            for s in top_sites
        ],
        "site_hit": site_hit,
        "site_chance_level": chance,
        "site_proximity_floor": floor,
        "knob_spread": knob_spread,
        "residue_level": residue_level,
        "statement": end_to_end_statement(target_name, apo_pdb, holo_pdb, top_sites, site_hit, label_source),
    }
