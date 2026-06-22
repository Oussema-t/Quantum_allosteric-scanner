"""
Scoring, labels, and metrics (notebook §4).

Given a connectivity matrix C and the active-site source residues, a residue's
allosteric score is its mean connectivity to the source. The top-k scorers (excluding
the source itself) are the predicted allosteric/cryptic sites. When a validated pocket
is known (benchmark targets), AUC / precision@k quantify predictive accuracy.
"""
import numpy as np
from scipy.spatial.distance import cdist
from sklearn.metrics import roc_auc_score


def score_from_source(C, src_idx):
    """Mean connectivity of every residue to the source set; source masked to -inf."""
    s = C[src_idx].mean(0).astype(float)
    s[src_idx] = -np.inf
    return s


def spherical_labels(coords, pocket_idx, tol):
    """Binary label: residues within `tol` Angstrom of any validated pocket residue."""
    if len(pocket_idx) == 0:
        return np.zeros(len(coords), int)
    return (cdist(coords, coords[pocket_idx]).min(1) <= tol).astype(int)


def evaluate(scores, coords, pocket_idx, tol=6.0, k=5):
    """AUC + precision@k + enrichment of `scores` against a validated pocket."""
    lab = spherical_labels(coords, pocket_idx, tol)
    m = np.isfinite(scores)
    out = {}
    out["auc"] = (roc_auc_score(lab[m], scores[m])
                  if (m.sum() > 1 and len(np.unique(lab[m])) > 1) else 0.5)
    order = np.argsort(scores)[::-1]
    out["p@5"] = lab[order[:5]].sum() / 5.0
    out["p@10"] = lab[order[:10]].sum() / 10.0
    out["enrich@5"] = lab[order[:5]].mean() / (lab[m].mean() + 1e-9)
    out["top_hit_idx"] = int(order[0])
    return out, lab, order


def predict_residues(st, scores, k=5):
    """Top-k predicted allosteric residue numbers (and their array indices)."""
    order = np.argsort(scores)[::-1][:k]
    return [int(st["resnums"][i]) for i in order], order
