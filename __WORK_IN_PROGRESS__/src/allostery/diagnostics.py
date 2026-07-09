"""Operator diagnostics + failure-mode classifier.

Callable-function port of notebook `H_new_engineering (4) CLEAN.ipynb`
Sec.14 "Failure-mode analysis" (cell 56 "OPERATOR DIAGNOSTICS" /
"Failure-mode notes"), reorganized from that cell's inline per-target loop
into two reusable functions: `operator_diagnostics` (per-operator structural
properties) and `classify_failure` (a closed-set verdict for one scoring
result). This module reports; it does not repair.

`operator_diagnostics` also surfaces the T-012 finding (`.claude/TASKS.md`):
default `build_H_new` is not globally PSD by design (`V_R`/`V_C`/`V_M` are
reward terms with negative diagonal contributions, not constrained to
preserve positive-semidefiniteness) -- the same kind of property T-012 found
by hand, made diagnosable instead of a one-off manual observation.

Off-diagonal decomposition (`_connected_components`, the diag/offdiag
ratio) relies on the same invariant `select.py::_hop_distances_from_source`
already establishes: the diagonal potentials in `hamiltonians.build_H_new`
only ever touch the diagonal, so H's off-diagonal structure is exactly the
underlying contact graph regardless of which potential terms were added --
diagnostics can introspect H alone, with no separate coords/adjacency input.
"""
from __future__ import annotations

import numpy as np

from .metrics import auc as _auc, eff_rank as _eff_rank

# notebook cell 56 thresholds, ported verbatim
LARGE_N_THRESHOLD = 800
DIAG_DOMINANCE_THRESHOLD = 3.0


def _connected_components(H: np.ndarray, tol: float = 1e-12) -> int:
    """Count connected components of H's off-diagonal sparsity pattern."""
    N = H.shape[0]
    adjacency = np.abs(H - np.diag(np.diag(H))) > tol
    seen = np.zeros(N, dtype=bool)
    n_components = 0
    for start in range(N):
        if seen[start]:
            continue
        n_components += 1
        frontier = [start]
        seen[start] = True
        while frontier:
            node = frontier.pop()
            for nb in np.where(adjacency[node])[0]:
                if not seen[nb]:
                    seen[nb] = True
                    frontier.append(int(nb))
    return n_components


def operator_diagnostics(
    H: np.ndarray,
    *,
    bfactors: np.ndarray | None = None,
    n_large: int = LARGE_N_THRESHOLD,
    diag_dominance_threshold: float = DIAG_DOMINANCE_THRESHOLD,
    psd_tol: float = 1e-9,
) -> dict:
    """Structural/spectral diagnostics for one built Hamiltonian H.

    Returns a dict: N, spec_min, spec_max, eff_rank, diag_over_offdiag,
    n_components, is_psd, b_all_zero (None if `bfactors` not given), and
    `notes` -- human-readable flags mirroring notebook cell 56's printed
    "Failure-mode notes" for this operator.
    """
    Hs = 0.5 * (H + H.T)
    w = np.linalg.eigvalsh(Hs)
    N = H.shape[0]

    diag = np.diag(H)
    offdiag = H - np.diag(diag)
    offdiag_norm = float(np.linalg.norm(offdiag))
    diag_over_offdiag = float(np.linalg.norm(diag)) / (offdiag_norm + 1e-9)

    n_components = _connected_components(H)
    b_all_zero = bool(np.allclose(bfactors, 0)) if bfactors is not None else None

    notes = []
    if b_all_zero:
        notes.append("V_B disabled (B==0)")
    if N > n_large:
        notes.append(f"very large N ({N}>{n_large}) -- anisotropic ANM channel may dominate")
    if diag_over_offdiag > diag_dominance_threshold:
        notes.append("diagonal potential dominates; collapses to ~diagonal")
    if n_components > 1:
        notes.append(f"operator disconnected into {n_components} components")
    if w.min() < -psd_tol:
        notes.append(f"not globally PSD (min eigenvalue={w.min():.3g}) -- by design, see T-012")

    return {
        "N": N,
        "spec_min": float(w.min()),
        "spec_max": float(w.max()),
        "eff_rank": _eff_rank(w),
        "diag_over_offdiag": diag_over_offdiag,
        "n_components": n_components,
        "is_psd": bool(w.min() >= -psd_tol),
        "b_all_zero": b_all_zero,
        "notes": notes,
    }


# closed set of failure categories returned by classify_failure()
NO_SIGNAL_IN_APO = "NO_SIGNAL_IN_APO"
LABEL_SUSPECT = "LABEL_SUSPECT"
OPERATOR_DEGENERATE = "OPERATOR_DEGENERATE"
INSUFFICIENT_RESOLUTION = "INSUFFICIENT_RESOLUTION"
NO_FAILURE_DETECTED = "NO_FAILURE_DETECTED"

FAILURE_CATEGORIES = (
    NO_SIGNAL_IN_APO,
    LABEL_SUSPECT,
    OPERATOR_DEGENERATE,
    INSUFFICIENT_RESOLUTION,
    NO_FAILURE_DETECTED,
)


def classify_failure(
    scores: np.ndarray,
    labels: np.ndarray,
    H: np.ndarray | None = None,
    bfactors: np.ndarray | None = None,
    *,
    auc_chance_tol: float = 0.05,
    n_large: int = LARGE_N_THRESHOLD,
    diag_dominance_threshold: float = DIAG_DOMINANCE_THRESHOLD,
) -> str:
    """Classify why a scoring result looks poor.

    Checked in this order -- rule out a diagnosable technical failure
    before accepting a scoring result as a legitimate negative, per the
    Intent Contract's "answer isn't in the apo topology" (legitimate) vs.
    "operator misconfigured" (bug) vs. "label is wrong" (upstream problem)
    distinction:

    1. `OPERATOR_DEGENERATE` -- H's off-diagonal graph is disconnected
       (`operator_diagnostics`'s `n_components > 1`). Independent of any
       label; a structural bug in operator construction.
    2. `LABEL_SUSPECT` -- `labels` has no positives or no negatives, so AUC
       is undefined (mirrors `metrics.auc`'s own NaN-return convention and
       notebook cell 56's "no pocket label -- cannot score" note).
    3. `INSUFFICIENT_RESOLUTION` -- notebook cell 56's data-quality notes:
       an all-zero B-factor column, or N above the large-protein threshold
       where the anisotropic ANM channel is expected to dominate a scalar
       operator. Checked ahead of the score itself: these invalidate a
       result even if it happens to look fine.
    4. `NO_SIGNAL_IN_APO` -- everything above checks out, but the score is
       statistically indistinguishable from chance: a legitimate,
       reportable negative result (`PLAN.md`'s "gates before build"
       framing).
    5. `NO_FAILURE_DETECTED` -- none of the above; not a notebook category,
       added so this function is total over well-scoring inputs too.
    """
    diag = None
    if H is not None:
        diag = operator_diagnostics(
            H, bfactors=bfactors, n_large=n_large,
            diag_dominance_threshold=diag_dominance_threshold,
        )
        if diag["n_components"] > 1:
            return OPERATOR_DEGENERATE

    labels_arr = np.asarray(labels).astype(int)
    if labels_arr.sum() == 0 or labels_arr.sum() == len(labels_arr):
        return LABEL_SUSPECT

    if diag is not None and (diag["b_all_zero"] or diag["N"] > n_large):
        return INSUFFICIENT_RESOLUTION

    score_auc = _auc(np.asarray(scores), labels_arr)
    if np.isnan(score_auc) or abs(score_auc - 0.5) < auc_chance_tol:
        return NO_SIGNAL_IN_APO

    return NO_FAILURE_DETECTED
