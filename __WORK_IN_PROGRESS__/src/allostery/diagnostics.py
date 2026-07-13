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

from typing import Callable

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
BEATS_CHANCE_NOT_FLOOR = "BEATS_CHANCE_NOT_FLOOR"
NO_FAILURE_DETECTED = "NO_FAILURE_DETECTED"

FAILURE_CATEGORIES = (
    NO_SIGNAL_IN_APO,
    LABEL_SUSPECT,
    OPERATOR_DEGENERATE,
    INSUFFICIENT_RESOLUTION,
    BEATS_CHANCE_NOT_FLOOR,
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
    floor_scores=None,
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
    5. `BEATS_CHANCE_NOT_FLOOR` (SEAM-0005, widened by TASK-0094) -- the
       score clears the chance bar above but does not beat `floor_scores`.
       `floor_scores` accepts either a single `(N,)` array (original
       SEAM-0005 shape, unchanged) or several stacked as `(k, N)`/a
       sequence of `(N,)` arrays (TASK-0094, REVIEW-2026-07-13 P1-A) --
       when several are given, the floor is the *maximum* AUC among them,
       i.e. "beats the single strongest trivial baseline available", not
       an average or the first one. This is the fix for `degree_centrality`
       alone being an insufficient floor: it does not measure proximity to
       the propagation seed, the confound the review found dominates the
       actual scores (`baselines.euclid_from_seed_centroid`/
       `hop_from_seed`). Only checked once chance is already cleared -- a
       result that doesn't even beat chance is `NO_SIGNAL_IN_APO`
       regardless of the floor. Skipped entirely when `floor_scores` is
       `None` (the default), which keeps every existing call site
       byte-identical to pre-SEAM-0005 behavior. Matches `PLAN.md`'s "a
       ceiling that node degree also reaches is structure, not your
       method" bar.
    6. `NO_FAILURE_DETECTED` -- none of the above; not a notebook category,
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

    if floor_scores is not None:
        floor_stack = np.asarray(floor_scores)
        candidates = [floor_stack] if floor_stack.ndim == 1 else list(floor_stack)
        floor_aucs = [_auc(np.asarray(c), labels_arr) for c in candidates]
        finite_floor_aucs = [a for a in floor_aucs if not np.isnan(a)]
        if finite_floor_aucs and score_auc <= max(finite_floor_aucs):
            return BEATS_CHANCE_NOT_FLOOR

    return NO_FAILURE_DETECTED


# ---------------------------------------------------------------------------
# Permutation-null leak detector (TASK-0071)
#
# Port of `__WORK_IN_PROGRESS__/tests/test_leakage_gate.py`'s GATE-B4 --
# that file's own docstring names it "the load-bearing detector" and its
# module docstring states the design axiom this ports verbatim: "a leak
# is anything that keeps scoring above chance when the labels are
# randomized... regardless of *where* the leak entered." Until this task,
# that reference implementation existed only as a self-validating
# meta-test fixture ("GATE-B4's permutation_null... [is] this file's own
# reference implementation... not a claim that protocol.py has [it]",
# test_leakage_gate.py:79-83) -- never wired into the production package.
# `PERM_LEAK_THRESHOLD` is ported at the same value (0.60), not re-derived,
# since it is validated in that file by `test_meta_permutation_detector_
# discriminates` against both a real honest scorer and a deliberately
# leaky one.
#
# The firewall (protocol.py) *prevents* known leak vectors structurally;
# this detector *catches* an unforeseen one empirically, by actually
# re-running the scorer on shuffled labels rather than trusting that every
# leak path was anticipated -- the two are complementary, not redundant
# (EXECUTION_PLAN.md Phase 1.4).
# ---------------------------------------------------------------------------

PERM_LEAK_THRESHOLD = 0.60  # ported verbatim from GATE-B4


def permutation_null(
    scorer: Callable[[np.ndarray, np.ndarray], np.ndarray],
    coords: np.ndarray,
    labels: np.ndarray,
    n_perm: int = 200,
    seed: int = 1,
) -> dict:
    """Re-run `scorer` on `n_perm` shuffles of `labels`, breaking any real
    label-structure relationship while leaving `coords` untouched.

    `scorer` takes `(coords, labels)` and returns a `(N,)` score array --
    deliberately re-invoked per permutation (not scored once and reused)
    so a leak baked into the scorer itself (e.g. one that reads labels
    directly, not just an upstream mislabeling) is caught too; this is
    why the reference implementation and this port both take a callable,
    not a precomputed score array like `classify_failure`'s `scores`.

    Returns `{"auc_true": float, "perm_mean": float, "perm_ci": (lo, hi),
    "n_perm": int}`. `perm_ci` is the 2.5/97.5 percentile band over the
    permutation AUCs (matches GATE-B4's own reporting, not just the mean).
    Non-finite (`NaN`) permutation AUCs -- possible in principle though not
    from permutation alone, since shuffling preserves the positive/negative
    label counts -- are excluded from `perm_mean`/`perm_ci`; if every
    permutation is non-finite both are `NaN`.
    """
    rng = np.random.default_rng(seed)
    labels = np.asarray(labels)

    auc_true = _auc(np.asarray(scorer(coords, labels)), labels)

    perm_aucs = np.empty(n_perm)
    for i in range(n_perm):
        y = rng.permutation(labels)
        perm_aucs[i] = _auc(np.asarray(scorer(coords, y)), y)

    finite = perm_aucs[np.isfinite(perm_aucs)]
    if len(finite) == 0:
        perm_mean = float("nan")
        perm_ci = (float("nan"), float("nan"))
    else:
        perm_mean = float(finite.mean())
        lo, hi = np.percentile(finite, [2.5, 97.5])
        perm_ci = (float(lo), float(hi))

    return {
        "auc_true": float(auc_true),
        "perm_mean": perm_mean,
        "perm_ci": perm_ci,
        "n_perm": n_perm,
    }


def detect_permutation_leak(
    scorer: Callable[[np.ndarray, np.ndarray], np.ndarray],
    coords: np.ndarray,
    labels: np.ndarray,
    n_perm: int = 200,
    seed: int = 1,
    threshold: float = PERM_LEAK_THRESHOLD,
) -> dict:
    """`permutation_null`, plus the flagging decision (GATE-B4's own
    `PERM_LEAK_THRESHOLD` gate: `perm_mean > threshold` => "label
    side-channel", a leak the firewall did not anticipate).

    Callable alongside `classify_failure`/`operator_diagnostics` as this
    module's third diagnostic entry point -- a catch-all *detector*
    backstopping `protocol.py`'s *preventive* DEV/FROZEN firewall, not a
    replacement for it (this task's own Intent Contract).

    Returns `permutation_null`'s dict plus `"threshold": float` and
    `"leak_detected": bool | None` (`None` only if every permutation AUC
    was non-finite, i.e. `perm_mean` itself is `NaN` -- undetermined, not
    a clean pass).
    """
    result = permutation_null(scorer, coords, labels, n_perm=n_perm, seed=seed)
    result["threshold"] = threshold
    result["leak_detected"] = (
        None if np.isnan(result["perm_mean"]) else bool(result["perm_mean"] > threshold)
    )
    return result
