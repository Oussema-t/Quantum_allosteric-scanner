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

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .metrics import auc as _auc, block_bootstrap_ci as _block_bootstrap_ci, eff_rank as _eff_rank

# notebook cell 56 thresholds, ported verbatim
#
# LARGE_N_THRESHOLD -- CORRECTED 2026-07-14 (user-identified finding, no
# task number assigned yet, see the follow-up constants-audit task filed
# the same day). The ported value was 800, with the comment "anisotropic
# ANM channel may dominate" -- checked directly against
# `notebooks/H_new_engineering (4) CLEAN.ipynb` cell 56, its only source:
# that comment is the *entire* justification given there too. No formula,
# no citation, no measurement of scalar-vs-anisotropic divergence as a
# function of N anywhere in the notebook or this codebase. It is an
# unfalsified physics claim, not a derived threshold -- and CARDIAC_MYOSIN
# (N=950), a mandatory challenge target, is disqualified by it with no
# argument for why 950 residues specifically breaks the model.
#
# Reframed as what it actually is: a **computational-scaling ceiling**,
# not a claim about model validity. `operator_diagnostics`/`classify_
# failure` are built on dense `np.linalg.eigh`/`eigvalsh` (O(N^3)); this
# is the largest N this pipeline has been run against and is known to
# complete in practical time (CARDIAC_MYOSIN's own real sweep, TASK-0101,
# ~50 min including several O(N^3)/O(N) operators) -- not a size beyond
# which the *science* is known to break down, which nothing in this repo
# or the notebook has ever measured. 1000 is chosen only to sit just
# above CARDIAC_MYOSIN's real N (950) with a little headroom, per
# explicit user direction -- it is exactly as arbitrary as 800 was, and
# is documented as such here rather than dressed up as principled. If a
# real anisotropy-divergence measurement is ever built (comparing this
# scalar operator's predictions against the real 3N ANM Hessian,
# `hamiltonians.H13_3N_anm_hessian`/`H14_anm_pinv_trace` already exist for
# exactly this), replace this with that, cited properly, per this
# project's own "don't invent formulas, cite the section" convention.
LARGE_N_THRESHOLD = 1000
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
        notes.append(
            f"N={N} exceeds {n_large}, the largest size this pipeline has been "
            "run against in practical time (O(N^3) eigendecomposition cost) -- "
            "a computational-scaling ceiling, not a claim that the model is "
            "invalid at this size (no such claim has been measured; see this "
            "module's own LARGE_N_THRESHOLD comment)"
        )
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


@dataclass
class FailureClassification:
    """TASK-0112 -- `classify_failure`'s `return_ci=True` return shape: the
    same `category` a plain call would return, plus the uncertainty this
    project's headline verdicts previously reported none of.

    `score_ci`/`floor_ci` are `(auc, lower, upper)` from `metrics.
    block_bootstrap_ci`, or `None` when not computed (either `return_ci`
    was `False`, or `category` short-circuited before a real AUC existed
    to bootstrap -- `OPERATOR_DEGENERATE`/`LABEL_SUSPECT`/
    `INSUFFICIENT_RESOLUTION`, none of which have a well-formed
    scores-vs-labels comparison to attach a CI to). `floor_ci` is the CI
    of the single *winning* floor candidate (the one `category`'s own
    `BEATS_CHANCE_NOT_FLOOR` check already selects as `max(floor_aucs)`),
    not an average across every candidate.

    `ci_overlap`: `True` if `score_ci`'s and `floor_ci`'s `[lower, upper]`
    ranges intersect (the score is not statistically distinguishable from
    the floor at this confidence level), `False` if they don't, `None` if
    either CI is unavailable. This is reported *alongside* `category`, not
    used to change it -- `category` is still the deterministic point-
    estimate verdict this project's existing taxonomy already defines
    (TASK-0112's own Constraint: "do not change `classify_failure`'s
    category names or ordering... this task adds an uncertainty
    annotation to existing verdicts, it is not a re-design of the
    taxonomy").
    """
    category: str
    score_ci: tuple | None = None
    floor_ci: tuple | None = None
    ci_overlap: bool | None = None


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
    return_ci: bool = False,
    ci_n_boot: int = 1000,
    ci_confidence: float = 0.95,
    ci_block_size: int = 10,
    ci_rng: np.random.Generator | None = None,
) -> "str | FailureClassification":
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
    3. `INSUFFICIENT_RESOLUTION` -- notebook cell 56's data-quality notes,
       bundling two genuinely different concerns under one label (not
       renamed to keep this a documentation-only correction, see
       `LARGE_N_THRESHOLD`'s own comment for the full finding): (a) an
       all-zero B-factor column -- a real data-quality problem, `V_B` is
       silently inert; (b) N above `LARGE_N_THRESHOLD` -- a computational-
       scaling ceiling (this pipeline has not been run/validated past that
       size in practical time), corrected 2026-07-14 from the notebook's
       original, uncited claim that this size *itself* invalidates the
       model ("anisotropic ANM channel may dominate" -- checked directly
       against the notebook, that comment was never derived or measured
       anywhere). Checked ahead of the score itself: both invalidate
       trusting a result even if it happens to look fine, for different
       reasons.
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

    TASK-0112: `return_ci=True` returns a `FailureClassification` (category
    + `score_ci`/`floor_ci`/`ci_overlap`, see that dataclass's own
    docstring) instead of the bare category string -- `return_ci=False`
    (the default) is byte-identical to this function's pre-TASK-0112
    behavior, every existing call site untouched. CI is only computed once
    `scores`/`labels` are well-formed enough for `score_auc` to mean
    anything -- `OPERATOR_DEGENERATE`/`LABEL_SUSPECT`/
    `INSUFFICIENT_RESOLUTION` always return `score_ci=None`/`floor_ci=None`/
    `ci_overlap=None`, a technical failure has no AUC to bootstrap. Uses
    `metrics.block_bootstrap_ci`, documented to preserve local spatial
    correlation in the residue ordering -- not a naive i.i.d. resample,
    per this task's own Constraint.
    """
    def _result(category: str, score_auc_: float | None = None,
                floor_candidates: list | None = None, floor_aucs: list | None = None):
        if not return_ci:
            return category
        score_ci = floor_ci = ci_overlap = None
        if score_auc_ is not None:
            score_ci = _block_bootstrap_ci(
                np.asarray(scores), labels_arr, n_boot=ci_n_boot,
                confidence=ci_confidence, block_size=ci_block_size, rng=ci_rng,
            )
            if floor_candidates and floor_aucs:
                finite = [(a, c) for a, c in zip(floor_aucs, floor_candidates) if not np.isnan(a)]
                if finite:
                    _, winning = max(finite, key=lambda ac: ac[0])
                    floor_ci = _block_bootstrap_ci(
                        np.asarray(winning), labels_arr, n_boot=ci_n_boot,
                        confidence=ci_confidence, block_size=ci_block_size, rng=ci_rng,
                    )
            if score_ci is not None and floor_ci is not None:
                _, s_lo, s_hi = score_ci
                _, f_lo, f_hi = floor_ci
                if not (np.isnan(s_lo) or np.isnan(f_lo)):
                    ci_overlap = bool(s_lo <= f_hi and f_lo <= s_hi)
        return FailureClassification(category, score_ci, floor_ci, ci_overlap)

    diag = None
    if H is not None:
        diag = operator_diagnostics(
            H, bfactors=bfactors, n_large=n_large,
            diag_dominance_threshold=diag_dominance_threshold,
        )
        if diag["n_components"] > 1:
            return _result(OPERATOR_DEGENERATE)

    labels_arr = np.asarray(labels).astype(int)
    if labels_arr.sum() == 0 or labels_arr.sum() == len(labels_arr):
        return _result(LABEL_SUSPECT)

    if diag is not None and (diag["b_all_zero"] or diag["N"] > n_large):
        return _result(INSUFFICIENT_RESOLUTION)

    score_auc = _auc(np.asarray(scores), labels_arr)

    floor_candidates = None
    floor_aucs = None
    if floor_scores is not None:
        floor_stack = np.asarray(floor_scores)
        floor_candidates = [floor_stack] if floor_stack.ndim == 1 else list(floor_stack)
        floor_aucs = [_auc(np.asarray(c), labels_arr) for c in floor_candidates]

    if np.isnan(score_auc) or abs(score_auc - 0.5) < auc_chance_tol:
        return _result(NO_SIGNAL_IN_APO, score_auc, floor_candidates, floor_aucs)

    if floor_aucs is not None:
        finite_floor_aucs = [a for a in floor_aucs if not np.isnan(a)]
        if finite_floor_aucs and score_auc <= max(finite_floor_aucs):
            return _result(BEATS_CHANCE_NOT_FLOOR, score_auc, floor_candidates, floor_aucs)

    return _result(NO_FAILURE_DETECTED, score_auc, floor_candidates, floor_aucs)


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


# ---------------------------------------------------------------------------
# TASK-0189 -- certification-gate reachability guard
# ---------------------------------------------------------------------------
# A permutation-style p-value (`(null_stat >= real_stat).mean()` over
# `n_reps` replicates) can never be smaller than `1/n_reps` -- it is a
# fraction with that denominator. A Bonferroni-corrected certification gate
# with `alpha/family_size` below that floor can therefore only ever fire at
# `p_value == 0.0` exactly, silently truncating a real certification test
# into a much stricter (and differently-shaped) one than its own stated
# alpha implies. Found live in `scripts/zero_plant_specificity.py:154`
# (TASK-0189, Reviewer finding F1): `ALPHA / (len(STRENGTHS) * N_SEEDS)` =
# `3.125e-4`, below `1/N_PERM_REPS = 1e-3` -- the exact defect this guard
# exists to catch mechanically rather than by a reviewer re-deriving the
# arithmetic by hand.

def assert_gate_reachable(alpha: float, family_size: int, n_reps: int) -> bool:
    """Raise `ValueError` if a Bonferroni-corrected certification gate at
    `alpha/family_size` sits at or below the smallest non-zero p-value
    `n_reps` permutation replicates can produce (`1/n_reps`) -- the gate
    could then only ever fire at `p_value == 0.0`, not at the alpha it
    claims to test. Returns `True` if reachable (never `False` -- an
    unreachable gate is a construction error to fix, not a value to
    branch on silently, matching this task's own "a test failure, not a
    silent one" Intent Contract).

    `alpha`/`family_size` are the *corrected* deployment-level values
    (e.g. `0.05/3`, TASK-0145's own "correct across targets" convention),
    not a measurement device's own internal replicate-grid family size --
    computing the right family is the caller's job; this function only
    checks that whatever family was declared leaves the gate reachable
    given how many permutation replicates back it.
    """
    corrected_alpha = alpha / family_size
    reachable_floor = 1.0 / n_reps
    if reachable_floor >= corrected_alpha:
        raise ValueError(
            f"certification gate unreachable: alpha/family = {corrected_alpha:.6g} "
            f"<= 1/n_reps = {reachable_floor:.6g} (n_reps={n_reps}) -- this gate can "
            "only ever fire at p_value == 0.0, not at its own stated alpha. Raise "
            "n_reps, widen alpha, or shrink family_size before trusting this gate."
        )
    return True
