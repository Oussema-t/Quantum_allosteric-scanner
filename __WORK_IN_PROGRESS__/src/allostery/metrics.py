"""Evaluation metrics: AUC, P@k, enrichment, block-bootstrap CI, spectral stats."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score


def auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """ROC-AUC. labels is a binary (0/1) array of the same length as scores."""
    if labels.sum() == 0 or labels.sum() == len(labels):
        return float("nan")
    return float(roc_auc_score(labels, scores))


def precision_at_k(scores: np.ndarray, labels: np.ndarray, k: int) -> float:
    """Fraction of ground-truth positives in the top-k ranked residues."""
    idx = np.argsort(scores)[::-1][:k]
    return float(labels[idx].sum() / k)


def enrichment_at_k(scores: np.ndarray, labels: np.ndarray, k: int) -> float:
    """Enrichment factor = (hits in top-k / k) / (total hits / N)."""
    N = len(labels)
    prevalence = labels.mean()
    if prevalence == 0:
        return float("nan")
    p_at_k = precision_at_k(scores, labels, k)
    return p_at_k / prevalence


def top_k_indices(scores: np.ndarray, k: int) -> np.ndarray:
    """Return indices of top-k scoring residues (descending order)."""
    return np.argsort(scores)[::-1][:k]


# ---------------------------------------------------------------------------
# TASK-0229.001 -- rank-of-known-site. Ref [9] (Gunasekaran, Ma & Nussinov
# 2004, Proteins 57:433 -- verified directly against the live article
# before this was written, not assumed from the citing task file) argues
# there is no clean class of "non-allosteric" surface sites, which attacks
# every AUC in this register: ROC-AUC is a statement about the FULL
# negative class (does the score separate positives from every negative,
# on average), so a contaminated negative class (a "negative" surface
# residue that is secretly a latent allosteric site for a different
# effector) directly corrupts the number. Rank-of-known-site and
# enrichment-at-k (above) both degrade more gracefully: they only ask
# where the KNOWN positives land relative to the rest of the ranking, not
# whether every single labelled negative is a genuine negative -- a
# contaminated negative class can still shift these somewhat (a secretly-
# allosteric "negative" that outscores the known site would still hurt
# rank-of-known-site), but nowhere near as badly as AUC, which is a sum
# over every positive/negative pair.
# ---------------------------------------------------------------------------

def rank_of_known_site(scores: np.ndarray, labels: np.ndarray) -> dict:
    """Rank (1 = best/highest score) of every labelled-positive residue in
    the full descending score ordering, plus summary stats.

    Ties are handled by average rank (`scipy`-style "fractional ranking"
    convention: tied scores share the mean of the ranks they would occupy)
    so a run of identical scores doesn't arbitrarily favor whichever index
    happens to sort first.

    A perfect predictor ranks every positive at 1..n_pos (min rank == 1,
    matching this task's own Planned Validation sanity check). Returns
    `{"ranks": [...], "min": ..., "median": ..., "n_positive": ...,
    "n_total": ...}`; `min`/`median`/`ranks` are `None` if there are no
    positives (mirrors `auc`'s own degenerate-label convention).
    """
    from scipy.stats import rankdata

    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels).astype(bool)
    n = len(scores)
    if not labels.any():
        return {"ranks": None, "min": None, "median": None, "n_positive": 0, "n_total": n}

    ranks = rankdata(-scores, method="average")  # rank 1 = highest score
    pos_ranks = ranks[labels]
    return {
        "ranks": [float(r) for r in pos_ranks],
        "min": float(pos_ranks.min()),
        "median": float(np.median(pos_ranks)),
        "n_positive": int(labels.sum()),
        "n_total": n,
    }


# ---------------------------------------------------------------------------
# TASK-0123 -- distance-stratified AUC (REVIEW-panel-2026-07-16-v2.md Sec.2.3,
# Sec.6): whole-graph AUC is mechanically dominated by "occupation of a walk
# seeded at a point is a monotonically-decreasing function of distance from
# that point, for any operator, at any time" -- it cannot distinguish "found
# the pocket" from "found distance." Scoring each pocket residue only against
# non-pocket residues at the *same* hop-shell removes the distance axis from
# the comparison entirely, letting a real signal inside the confound become
# visible if one exists.
# ---------------------------------------------------------------------------

def stratified_auc(scores: np.ndarray, labels: np.ndarray, shells: np.ndarray,
                    min_pos: int = 1, min_neg: int = 1) -> dict:
    """AUC computed independently within each unique value of `shells`
    (e.g. integer hop-distance-from-seed, `-baselines.hop_from_seed(...)`)
    -- residues are compared only against same-shell residues, never
    across shells, so a scorable shell's AUC cannot be driven by distance
    (every residue being compared is equidistant from the seed by
    construction).

    A shell needs at least `min_pos` positive and `min_neg` negative
    labels to be scorable (mirrors `auc`'s own degenerate-label NaN
    convention, but at the shell level: an all-pocket or all-non-pocket
    shell is silently excluded from the result, not scored as a
    degenerate NaN entry -- there is nothing to discriminate within it).

    Returns `{shell_value: {"auc", "n_pos", "n_neg"}, ...}` for every
    scorable shell -- empty if no shell has both labels present (the
    panel's own "observable dead" case reports as an empty result, not a
    crash or a silent 0.5).
    """
    scores = np.asarray(scores)
    labels = np.asarray(labels).astype(int)
    shells = np.asarray(shells)

    result: dict = {}
    for shell_value in np.unique(shells):
        mask = shells == shell_value
        shell_labels = labels[mask]
        n_pos = int(shell_labels.sum())
        n_neg = int(len(shell_labels) - n_pos)
        if n_pos < min_pos or n_neg < min_neg:
            continue
        result[float(shell_value)] = {
            "auc": auc(scores[mask], shell_labels),
            "n_pos": n_pos,
            "n_neg": n_neg,
        }
    return result


def stratified_auc_summary(stratified: dict) -> dict:
    """Collapse `stratified_auc`'s per-shell dict into the single
    summary this task's own Planned Validation reads: does *any* shell
    clear 0.5 (the panel's own pass criterion), or is stratified AUC
    approximately 0.5 everywhere (the panel's own "observable dead, per
    this task's own framing" kill criterion)."""
    if not stratified:
        return {"n_scorable_shells": 0, "mean_auc": float("nan"), "max_auc": float("nan"), "max_shell": None}
    aucs = [v["auc"] for v in stratified.values() if np.isfinite(v["auc"])]
    if not aucs:
        return {"n_scorable_shells": len(stratified), "mean_auc": float("nan"), "max_auc": float("nan"), "max_shell": None}
    max_shell = max((s for s in stratified if np.isfinite(stratified[s]["auc"])), key=lambda s: stratified[s]["auc"])
    return {
        "n_scorable_shells": len(stratified),
        "mean_auc": float(np.mean(aucs)),
        "max_auc": float(np.max(aucs)),
        "max_shell": max_shell,
    }


def block_bootstrap_ci(
    scores: np.ndarray,
    labels: np.ndarray,
    n_boot: int = 1000,
    confidence: float = 0.95,
    block_size: int = 10,
    rng: np.random.Generator | None = None,
) -> tuple[float, float, float]:
    """Block-bootstrap 95% CI for AUC.

    Block bootstrap preserves local spatial correlation in the residue ordering.

    Returns
    -------
    (auc_point, lower, upper) where lower/upper are the CI bounds.
    """
    if rng is None:
        rng = np.random.default_rng(42)
    N = len(scores)
    n_blocks = int(np.ceil(N / block_size))
    aucs: list[float] = []
    for _ in range(n_boot):
        block_starts = rng.integers(0, N, size=n_blocks)
        idx = np.concatenate(
            [np.arange(s, min(s + block_size, N)) for s in block_starts]
        )[:N]
        a = auc(scores[idx], labels[idx])
        if not np.isnan(a):
            aucs.append(a)
    if not aucs:
        return float("nan"), float("nan"), float("nan")
    alpha = 1 - confidence
    lo = float(np.percentile(aucs, 100 * alpha / 2))
    hi = float(np.percentile(aucs, 100 * (1 - alpha / 2)))
    return auc(scores, labels), lo, hi


# ---------------------------------------------------------------------------
# TASK-0165 -- spatial-block bootstrap CI (`PANEL_REVIEW_2026-07-25.md` W6/V4).
# `block_bootstrap_ci` above blocks on residue SEQUENCE index ("preserve local
# spatial correlation" -- but pockets are spatially compact while being
# sequence-*scattered*: two residues adjacent in 3D space are frequently far
# apart in sequence index (a beta-sheet's paired strands, a domain interface,
# a loop closure). The dependence structure a bootstrap needs to preserve is
# the one the SCORE actually varies smoothly over (3D Euclidean neighbourhood,
# same root mechanism TASK-0158 found for the permutation null, `nulls.
# compact_patch`'s own docstring) -- not sequence adjacency, which is close
# to irrelevant to it. Same defect, different statistical procedure.
# ---------------------------------------------------------------------------

def spatial_block_bootstrap_ci(
    coords: np.ndarray,
    scores: np.ndarray,
    labels: np.ndarray,
    n_boot: int = 1000,
    confidence: float = 0.95,
    block_size: int = 10,
    rng: np.random.Generator | None = None,
) -> tuple[float, float, float]:
    """Spatial-block-bootstrap 95% CI for AUC -- `block_bootstrap_ci`'s own
    drop-in companion (identical `n_boot`/`confidence`/`block_size`/`rng`
    parameters and `(auc_point, lower, upper)` return shape; only `coords`
    is new, since a spatial block needs 3D positions to be defined at all).

    **Block construction (Implementer's own call, stated here):** for each
    residue `i`, its own spatial block is the `block_size` nearest Euclidean
    neighbours (inclusive of itself) -- `N` overlapping, residue-centred
    blocks, one per residue, the direct 3D analogue of `block_bootstrap_ci`'s
    own `N` overlapping sequence-window starting positions (the classic
    moving-block-bootstrap construction, Kunsch 1989, applied to whichever
    axis actually carries the dependence). A grid-partition alternative was
    considered and rejected: a fixed grid creates hard block-boundary
    artefacts (two residues 0.1 A apart, on opposite sides of a cell wall,
    land in different blocks with zero shared resampling; a k-NN neighbourhood
    has no such boundary) and needs a cell-size parameter with no natural
    correspondence to `block_size`'s own existing "how many residues per
    block" meaning -- k-NN reuses `block_size` directly, unmodified.

    Resampling mirrors `block_bootstrap_ci` exactly, block SOURCE swapped
    from `range(s, s+block_size)` (sequence window) to `argsort(dist to
    coords[s])[:block_size]` (spatial neighbourhood): draw `n_blocks =
    ceil(N/block_size)` random block-centre residues per replicate,
    concatenate their neighbourhoods, truncate to length `N`.

    **Correction (TASK-0167.002, external review `PANEL_REVIEW_2026-07-25.md`
    §2.2): on a 1D-line control this block does NOT coincide exactly with
    `block_bootstrap_ci`'s own sequence window.** `block_bootstrap_ci`'s
    window (`range(s, s+block_size)`) is asymmetric/forward-only from `s`;
    this function's own k-NN block is symmetric/centred on its seed residue
    -- even when 3D position matches sequence order, these are different
    index sets (measured mean overlap ~55%, matching the review's own 54%
    finding almost exactly). The two methods' aggregate CI *widths* are
    close on that control (within the loose tolerance `tests/test_metrics.
    py` originally checked), which is not the same claim as "the same index
    sets" -- corrected here rather than left standing. See
    `.ai/tasks/DONE/TASK-0165-spatial-block-bootstrap.md`'s own 2026-07-28
    correction note for the full account and why no fix to either
    construction was attempted (both options change a much larger surface
    than this correction's own scope).
    """
    if rng is None:
        rng = np.random.default_rng(42)
    N = len(scores)
    n_blocks = int(np.ceil(N / block_size))

    # Precompute each residue's own k-NN block once (shared across all
    # n_boot replicates) -- the expensive part (an N x N distance matrix)
    # done a single time, not per replicate.
    dist = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=-1)
    neighbour_blocks = np.argsort(dist, axis=1)[:, :block_size]

    aucs: list[float] = []
    for _ in range(n_boot):
        centres = rng.integers(0, N, size=n_blocks)
        idx = np.concatenate([neighbour_blocks[c] for c in centres])[:N]
        a = auc(scores[idx], labels[idx])
        if not np.isnan(a):
            aucs.append(a)
    if not aucs:
        return float("nan"), float("nan"), float("nan")
    alpha = 1 - confidence
    lo = float(np.percentile(aucs, 100 * alpha / 2))
    hi = float(np.percentile(aucs, 100 * (1 - alpha / 2)))
    return auc(scores, labels), lo, hi


# ---------------------------------------------------------------------------
# Spectral / structural stats (used in eff_rank pinning test)
# ---------------------------------------------------------------------------

def eff_rank(eigenvalues: np.ndarray) -> float:
    """Effective rank of a spectrum (Roy & Vetterli 2007).

    eff_rank = exp(H) where H = -Σ p_k log(p_k) and p_k = |λ_k| / Σ|λ_j|.
    """
    ev = np.abs(eigenvalues)
    s = ev.sum()
    if s < 1e-300:
        return 1.0
    p = ev / s
    p = p[p > 0]
    return float(np.exp(-np.sum(p * np.log(p))))


# ---------------------------------------------------------------------------
# TASK-0199 -- participation-ratio effective rank of a correlation matrix
# (the register's own "did we test 40 things or one thing 40 times"
# statistic). A different definition from `eff_rank` above (Roy &
# Vetterli's entropy-based one) -- confirmed distinct, not a duplicate;
# TASK-0199 uses this one as primary and `eff_rank` as a sweep companion.
# ---------------------------------------------------------------------------

def participation_ratio_rank(eigenvalues: np.ndarray) -> float:
    """Participation ratio of a spectrum: `(sum(lambda))^2 / sum(lambda^2)`.

    For an `M x M` correlation matrix (unit diagonal, `sum(lambda) = M`),
    this ranges `[1, M]` -- `1` if the matrix has a single dominant
    component (every variable perfectly correlated, one underlying
    quantity), `M` if the matrix is the identity (every variable
    orthogonal, fully independent). Continuous, no arbitrary threshold --
    this task's own stated reason for preferring it over a fixed
    variance-explained cutoff, which is reported alongside as a sanity
    check, not a substitute.
    """
    ev = np.asarray(eigenvalues, dtype=float)
    s1 = ev.sum()
    s2 = float(np.sum(ev ** 2))
    if s2 < 1e-300:
        return 1.0
    return float((s1 ** 2) / s2)


def variance_explained_count(eigenvalues: np.ndarray, threshold: float = 0.90) -> int:
    """Smallest `k` such that the top-`k` eigenvalues (descending) sum to
    at least `threshold` fraction of the total -- the threshold-based
    sanity-check companion `participation_ratio_rank`'s own docstring
    promises, never a substitute for it."""
    ev = np.sort(np.asarray(eigenvalues, dtype=float))[::-1]
    total = ev.sum()
    if total < 1e-300:
        return 0
    cumulative = np.cumsum(ev) / total
    k = int(np.searchsorted(cumulative, threshold) + 1)
    return min(k, len(ev))


def ipr(v: np.ndarray) -> float:
    """Inverse Participation Ratio of an eigenvector: Σ v_i^4 / (Σ v_i^2)^2."""
    v2 = v ** 2
    return float((v2 ** 2).sum() / (v2.sum() ** 2 + 1e-300))


def spectral_gap(eigenvalues: np.ndarray) -> float:
    """Gap between the two smallest non-negative eigenvalues."""
    w = np.sort(eigenvalues)
    pos = w[w >= -1e-10]
    if len(pos) < 2:
        return float("nan")
    return float(pos[1] - pos[0])


# ---------------------------------------------------------------------------
# Guardrail checks
# ---------------------------------------------------------------------------

def check_degree_correlation(scores: np.ndarray, coords: np.ndarray, cutoff: float = 10.0) -> float:
    """Pearson r between scores and node degree. High r → scores are trivially
    degree-driven; flag if |r| > 0.8."""
    from .hamiltonians import contact_matrix
    W = contact_matrix(coords, cutoff=cutoff, weight="binary")
    degree = W.sum(axis=1)
    return float(np.corrcoef(scores, degree)[0, 1])
