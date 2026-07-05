"""Kabsch rigid-body alignment, shared by discovery.py's apo/holo superposition
and analysis.py's GNM morph/RMSF alignment (TASK-0030). Both were independent,
near-identical NumPy SVD implementations before this unification; origin:
backend/discovery.py::_kabsch + backend/analysis.py::_kabsch_rotate.
"""
import numpy as np


def kabsch_fit(mobile, ref):
    """Least-squares rotation aligning `mobile` (N,3) onto `ref` (N,3).
    Returns (R, mobile_centroid, ref_centroid) such that
    aligned = (X - mobile_centroid) @ R.T + ref_centroid."""
    mc, rc = mobile.mean(0), ref.mean(0)
    H = (mobile - mc).T @ (ref - rc)
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    return R, mc, rc


def kabsch_apply(coords, R, mobile_centroid, ref_centroid):
    """Apply a fit from `kabsch_fit` to any (M,3) coordinate array."""
    return (coords - mobile_centroid) @ R.T + ref_centroid


def kabsch_align(mobile, ref, apply_to=None):
    """Fit mobile->ref and return the aligned copy of `apply_to`
    (defaults to `mobile` itself)."""
    R, mc, rc = kabsch_fit(mobile, ref)
    return kabsch_apply(mobile if apply_to is None else apply_to, R, mc, rc)
