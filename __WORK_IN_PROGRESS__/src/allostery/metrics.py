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
