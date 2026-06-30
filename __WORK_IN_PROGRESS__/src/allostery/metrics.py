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
