"""Challenge submission report: verdict template, hit list, and stability
metric.

Callable-function port of notebook `H_new_engineering (4) CLEAN.ipynb`
Sec.15 "Synthesis & honest verdict" (cell 58), Sec.16 "Final recommendation
(decision-support template)" (cell 60), and Sec.17 "Challenge Submission:
The Hit List (Top 5)" (cell 62).

This module renders prose/lists from an already-assembled results dict; it
does not compute the underlying numbers (that's analysis.py's job) and it
does not write the competence-map narrative (a human/report-writing step
that cites these numbers, per this task's own Out-Of-Scope).

Notebook-oracle gap: Sec.17.1 "Stability Analysis: Jaccard Similarity (Top
5)" (cell 63, markdown-only) has no corresponding code cell in this
notebook -- the markdown promises a Jaccard-top-5 stability computation
that was never written. `jaccard_stability` below satisfies that section's
stated purpose using this package's own already-ported Jaccard convention
(`analysis.py::apo_holo_consistency`, itself Sec.12/cell 52's
`rank_overlap`), rather than inventing new math -- it is not a line-by-line
port of a cell that does not exist.
"""
from __future__ import annotations

from itertools import combinations
from typing import Sequence

import numpy as np

# DEV/FROZEN vocabulary matches protocol.py::ProtocolRoster (lowercase
# "dev"/"frozen" strings, config-driven, no hardcoded target lists here).
_DEV_BANNER = "[DEV/CEILING RESULT -- NOT THE FROZEN SUBMISSION VERDICT]\n\n"


# ---------------------------------------------------------------------------
# Sec.17 -- hit list (top-k residue selection)
# ---------------------------------------------------------------------------

def hit_list(
    scores: np.ndarray,
    k: int = 5,
    *,
    resnums: np.ndarray | None = None,
    exclude_idx: Sequence[int] | None = None,
) -> dict:
    """Top-k residues by score, descending (cell 62's hit-list selection).

    `exclude_idx` mirrors cell 62's masking-out of the source/functional
    residues before ranking, so a trivial self-hit never appears in the
    list. `resnums`, if given, maps local array indices to PDB residue
    numbers for the returned list (cell 62's `top5_resnums`); omit it to
    get local indices only.

    Returns {"indices": (k_eff,) int array (local), "resnums": array or
    None, "scores": (k_eff,) float array}. `k_eff = min(k, n_candidates)`
    if fewer candidates remain than `k` after exclusion.
    """
    scores = np.asarray(scores, float)
    mask = np.ones(len(scores), dtype=bool)
    if exclude_idx is not None:
        mask[np.asarray(exclude_idx, int)] = False
    candidates = np.where(mask)[0]
    k_eff = min(k, len(candidates))
    top_local = candidates[np.argsort(-scores[candidates])[:k_eff]]

    return {
        "indices": top_local,
        "resnums": np.asarray(resnums)[top_local] if resnums is not None else None,
        "scores": scores[top_local],
    }


# ---------------------------------------------------------------------------
# TASK-0079.002 -- per-target wiring: labels.Labels -> hit_list's raw args
# ---------------------------------------------------------------------------

def assemble_hit_list(scores: np.ndarray, labels, resnums: np.ndarray | None = None, k: int = 5) -> dict:
    """Thin per-target call site wiring a real `labels.Labels` object
    (`labels.py`, TASK-0004/TASK-0070) into `hit_list`'s raw-array
    interface -- derives `exclude_idx` from `labels.active_site` so the
    functional/source residues this task's Intent Contract names are
    excluded automatically, rather than every call site re-deriving that
    mask by hand.

    Lives here (not `labels.py`) despite `Labels` being the "source
    shape": unlike TASK-0079.001's `analysis.assemble_verdict_results`
    (a real nested-to-flat shape *transformation*, kept with the module
    owning the shapes being transformed), this is a thin wrapper whose
    entire body is "derive one mask, call `hit_list`" -- discoverability
    next to the function it wraps outweighs the source-module precedent
    for something this thin.

    `scores` is caller-supplied and unconstrained by design: which
    occupation/ranking array feeds a given target's hit list is the
    FROZEN-gated pipeline's decision (TASK-0079.003), not this function's
    -- see this task's own Out Of Scope.
    """
    exclude_idx = np.where(labels.active_site)[0]
    return hit_list(scores, k=k, resnums=resnums, exclude_idx=exclude_idx)


# ---------------------------------------------------------------------------
# Sec.17.1 -- stability across repeated/perturbed runs (notebook-oracle gap,
# see module docstring)
# ---------------------------------------------------------------------------

def jaccard_stability(hit_lists_across_runs: Sequence[Sequence[int]]) -> dict:
    """Pairwise Jaccard similarity of a residue-index set across >=1
    hit-lists (e.g. repeated/perturbed runs, or apo-vs-holo with holo
    already mapped to apo numbering by the caller -- matching Sec.17.1's
    own framing).

    Jaccard convention matches `analysis.py::apo_holo_consistency`:
    |intersection| / |union|, with an empty-union pair (both hit-lists
    empty) scored 1.0 -- this diverges from notebook cell 52's
    `rank_overlap` (which divides by `max(len(union), 1)`, scoring that
    same case 0.0); kept consistent with this package's existing
    convention rather than the notebook's, since both live in the same
    package.

    Returns {"pairwise": [{"i": int, "j": int, "jaccard": float}, ...],
    "mean": float, "min": float}. A single hit-list (nothing to compare
    against) returns a trivial similarity of 1.0 with an empty pairwise
    list.
    """
    sets = [set(int(x) for x in hl) for hl in hit_lists_across_runs]
    if len(sets) < 2:
        return {"pairwise": [], "mean": 1.0, "min": 1.0}

    pairwise = []
    for i, j in combinations(range(len(sets)), 2):
        union = sets[i] | sets[j]
        jaccard = len(sets[i] & sets[j]) / len(union) if union else 1.0
        pairwise.append({"i": i, "j": j, "jaccard": jaccard})

    values = [p["jaccard"] for p in pairwise]
    return {"pairwise": pairwise, "mean": float(np.mean(values)), "min": float(np.min(values))}


# ---------------------------------------------------------------------------
# Sec.15/16 -- honest verdict + decision-support recommendation
# ---------------------------------------------------------------------------

def _has_valid_frozen_stamp(results: dict) -> bool:
    """Local import: report.py otherwise has no dependency on protocol.py,
    and this keeps that the common case (most call sites never touch the
    frozen path at all)."""
    from .protocol import verify_frozen_stamp

    return verify_frozen_stamp(results)


def verdict_template(
    results: dict, *, provenance: str = "dev",
    target_name: str | None = None, structure: str | None = None,
) -> str:
    """Render Sec.15's headline verdict + Sec.16's parameterized 5-point
    recommendation from an already-assembled `results` dict.

    `target_name`/`structure` (TASK-0370, external adversarial review item
    25 -- "three of four files have no target or PDB header"): optional,
    rendered as one header line before HEADLINE VERDICT when given. Kept
    optional rather than required so every existing call site (and this
    module's own tests) keeps working unchanged with no header at all --
    additive, matching `no_ground_truth_report`'s own header convention,
    not a new requirement on every caller.

    `results` keys (verbatim from cell 58's `verdict` dict) --
    AUC_apo_Hnew_default, AUC_apo_H10_baseline, AUC_apo_Hnew_optimised,
    AUC_holo_Hnew_optimised, AUC_ctqw_mean, AUC_heat_mean,
    most_impactful_term, least_impactful_term, mean_rho_apo_holo,
    mean_jacc20, coherence_auc_range, coherence_auc_at_gamma0,
    coherence_classification -- each optional; a missing key renders "N/A"
    in the headline block and skips its dependent recommendation line
    rather than raising, since a caller may not have every upstream
    analysis available for a given target.

    `provenance` must be exactly `"frozen"` **and** `results` must carry a
    valid stamp from `protocol.stamp_provenance` (TASK-0088, closes
    SEAM-0004) for this to render as the clean submission verdict --
    `provenance="frozen"` alone is not trusted, since it is a plain
    caller-supplied string a DEV/ceiling result could claim just as
    easily. The stamp is issued at computation time, inside the
    `frozen_context` that produced the numbers, and verified here at
    render time (almost always outside that context by then) -- see
    `protocol.stamp_provenance`'s own docstring for why a naive
    "check `current_context()` at render time" design does not work.
    Any other case (provenance not `"frozen"`, no stamp, or a forged
    `results["_frozen_stamp"]` value never actually issued by
    `stamp_provenance`) prepends a loud banner making the distinction
    impossible to miss.

    Renders only the four data-driven recommendation lines from cell 60;
    that cell's fifth bullet ("Keep V_B and V_T as cheap priors...") is
    static prose independent of `results` -- competence-map narrative,
    out of this module's scope per this task's own Intent Contract.
    """
    lines = []
    if target_name is not None or structure is not None:
        header = f"Target: {target_name or 'N/A'}"
        if structure is not None:
            header += f"  |  Structure: {structure}"
        lines.append(header)
    if not (provenance == "frozen" and _has_valid_frozen_stamp(results)):
        lines.append(_DEV_BANNER.rstrip("\n"))

    def fmt(key):
        v = results.get(key)
        if v is None:
            return "N/A"
        return f"{v:.3f}" if isinstance(v, float) else str(v)

    lines += [
        "=" * 72,
        "HEADLINE VERDICT",
        "=" * 72,
    ]
    # TASK-0097 / REVIEW-2026-07-13 (P2-B): every AUC below is computed
    # from propagators.time_averaged_ctqw -- the decoherent/infinite-time
    # average of the walk (Sum_k |v_k(j)|^2 |v_k(source)|^2, a spectral
    # overlap between eigenvector components at the source and each
    # residue), not a coherent quantum-walk snapshot. All phase/coherence
    # information is averaged out by construction -- consistent with this
    # repo's own flat-dephasing-sweep finding, not an inconsistency to
    # explain away, but a claim a judge should be told, not left to find.
    lines.append(
        "[NOTE] AUC values below use the decoherent/time-averaged CTQW "
        "limit (a spectral overlap between source and residue eigenvector "
        "components), not a coherent quantum-walk snapshot -- all phase "
        "information is averaged out by construction. See TASK-0097 / "
        "REVIEW-2026-07-13 finding P2-B."
    )
    lines.append("")
    for key in (
        "AUC_apo_Hnew_default", "AUC_apo_H10_baseline",
        "AUC_apo_Hnew_optimised", "AUC_holo_Hnew_optimised",
        "AUC_ctqw_mean", "AUC_heat_mean",
        "most_impactful_term", "least_impactful_term",
        "mean_rho_apo_holo", "mean_jacc20",
        "coherence_auc_range", "coherence_auc_at_gamma0", "coherence_classification",
    ):
        lines.append(f"  {key:30s} : {fmt(key)}")

    # TASK-0112: _diagnosis was computed (protocol.run_frozen_verdict, via
    # diagnostics.classify_failure) but never rendered here at all before
    # this task -- the category plus its block-bootstrap CI (both the
    # scored operator's and the winning floor candidate's), and whether
    # the two intervals overlap (statistically indistinguishable from the
    # floor, not just a smaller point estimate). Missing keys (a `results`
    # dict from before this task, or `return_ci` not used) render "N/A"/
    # omit the overlap line, same missing-key convention as the headline
    # block above -- not a crash.
    diagnosis = results.get("_diagnosis")
    if diagnosis is not None:
        lines.append("")
        lines.append(f"  {'_diagnosis':30s} : {diagnosis}")

        def _fmt_ci(ci):
            if ci is None:
                return "N/A"
            point, lo, hi = ci
            return f"{point:.3f}  [{lo:.3f}, {hi:.3f}] (95% block-bootstrap CI)"

        score_ci = results.get("_diagnosis_score_ci")
        floor_ci = results.get("_diagnosis_floor_ci")
        if score_ci is not None or floor_ci is not None:
            lines.append(f"  {'score 95% CI':30s} : {_fmt_ci(score_ci)}")
            lines.append(f"  {'floor 95% CI':30s} : {_fmt_ci(floor_ci)}")
            overlap = results.get("_diagnosis_ci_overlap")
            if overlap is not None:
                lines.append(
                    f"  {'CIs overlap?':30s} : "
                    + ("YES -- statistically indistinguishable from the floor at this confidence level"
                       if overlap else
                       "NO -- score is statistically distinguishable from the floor")
                )

    lines.append("")
    lines.append("DECISION-SUPPORT RECOMMENDATION")
    lines.append("-" * 32)

    # TASK-0370 (external adversarial review, item 6): the two DAUC lines
    # below classify by a raw point-estimate threshold, independent of the
    # _diagnosis/CI-overlap block rendered just above -- so a target the
    # headline already calls NO_SIGNAL_IN_APO (score statistically
    # indistinguishable from the trivial floor) could still get "(meaningful)"
    # or "CTQW genuinely helps" a few lines down, in the same file. That
    # shipped as the KRAS report contradicting the Concept Proposal's own
    # §1 finding. Fixed at the generator, not the file: append the CI-overlap
    # caveat inline whenever it applies, so the two sections can no longer
    # disagree with each other. Existing tests (no `_diagnosis_ci_overlap`
    # key) are unaffected -- `ci_overlap` is None/falsy there.
    ci_overlap = results.get("_diagnosis_ci_overlap")
    overlap_note = (
        " -- but not statistically distinguishable from the trivial floor "
        "at 95% CI (see _diagnosis above); read this point estimate as a "
        "lead, not an established gain"
    )

    opt = results.get("AUC_apo_Hnew_optimised")
    base = results.get("AUC_apo_H10_baseline")
    if opt is not None and base is not None:
        diff = opt - base
        verdict = "meaningful" if diff > 0.05 else "marginal" if diff > 0.02 else "noise-level"
        line1 = f"1) Operator gain over H10 baseline (apo): DAUC = {diff:+.3f}  ({verdict})."
        if ci_overlap and verdict != "noise-level":
            line1 += overlap_note
        lines.append(line1)

    ctqw = results.get("AUC_ctqw_mean")
    heat = results.get("AUC_heat_mean")
    if ctqw is not None and heat is not None:
        diff_qc = ctqw - heat
        helps = diff_qc > 0.05
        verdict_qc = (
            "CTQW genuinely helps" if helps
            else "within graph-kernel noise -- CTQW does NOT add biological "
                 "information beyond the operator"
        )
        # TASK-0095 / REVIEW-2026-07-13 (P1-B): "AUC_heat_mean" is
        # propagators.ground_state_relaxation's score on H_new, an
        # indefinite operator -- NOT a diffusion process. Keep this line's
        # wording accurate; the old framing here was a false physical claim
        # on every H_new run.
        line2 = (
            f"2) CTQW vs ground-state relaxation on H_new (same operator, "
            f"not a classical-diffusion comparison -- see TASK-0095): "
            f"DAUC = {diff_qc:+.3f}  ({verdict_qc})."
        )
        if helps and ci_overlap:
            line2 += overlap_note
        lines.append(line2)

    most_term = results.get("most_impactful_term")
    least_term = results.get("least_impactful_term")
    if most_term is not None and least_term is not None:
        lines.append(f"3) Most/least impactful potential terms: most = {most_term}, least = {least_term}.")

    rho = results.get("mean_rho_apo_holo")
    jacc20 = results.get("mean_jacc20")
    if rho is not None and jacc20 is not None:
        transfer = "Operator transfers cleanly" if rho > 0.5 else "Transferability is partial -- apo and holo may need separate operators"
        lines.append(
            f"4) Apo<->holo Spearman rho on occupation (mean over labelled "
            f"systems) = {rho:+.2f} ; top-20 Jaccard = {jacc20:.2f}.  {transfer}."
        )

    # TASK-0099: does the reported verdict change if quantum coherence is
    # randomized away? See analysis.coherence_sensitivity.
    coherence_range = results.get("coherence_auc_range")
    coherence_class = results.get("coherence_classification")
    if coherence_range is not None and coherence_class is not None:
        verdict_coh = (
            "coherence changes the score AND crosses the proximity floor "
            "-- a genuine ENAQT-relevant signal"
            if coherence_class == "COHERENCE_DEPENDENT_SIGNAL"
            else "AUC is insensitive to coherence (calibrated dephasing-rate "
                 "sweep) -- ranking power comes from graph topology, not "
                 "quantum phase"
        )
        lines.append(
            f"5) Coherence sensitivity (calibrated Haken-Strobl gamma-sweep): "
            f"AUC range = {coherence_range:.4f}  ({coherence_class}) -- "
            f"{verdict_coh}."
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# TASK-0080 -- no-ground-truth report (c-Myc/1NKP: allosteric_pocket_exists=false)
# ---------------------------------------------------------------------------

def _consensus_confidence_statement(consensus: dict) -> str:
    """Honest, qualitative confidence read of a `analysis.consensus_ranking`
    result -- no AUC exists here to attach a number to, so the statement is
    about *operator agreement*, the only holo-free signal this report has.

    TASK-0370 (external adversarial review, item 6): this used to read
    "high" whenever every operator agreed, which the Concept Proposal
    itself contradicts (§1 calls this target's prediction "unverified").
    Operator agreement is not validated confidence -- the CP's own §2
    measures the walk as "a distance measure with extra steps" (its hit
    rate anti-correlates with true-pocket distance) rather than an
    independent detector, so agreement across operators can mean "the
    same distance confound, seen four times," not independent
    corroboration. Fixed at the generator so every future render says
    this, not just the shipped snapshot. (Corrected again, same task: the
    CP has no numbered "Finding N" statements -- the prior wording here
    cited a "Finding 3" that does not exist in the document.)"""
    counts = consensus["consensus_count"]
    n_ops = consensus["n_operators"]
    max_agree = int(counts.max()) if len(counts) else 0
    if max_agree == n_ops:
        return (
            f"unverified -- at least one residue appears in all {n_ops} "
            f"operators' own top-{consensus['k']}, but operator agreement is "
            "not validated confidence: no ground truth exists for this "
            "target to check against, and the Concept Proposal's own §2 "
            "measures these operators as correlated distance detectors, "
            "not independent evidence"
        )
    if max_agree >= max(2, n_ops - 1):
        return (
            f"unverified -- best cross-operator agreement is {max_agree}/{n_ops}, "
            "and (as above) agreement is not itself validation"
        )
    return (
        f"unverified -- no residue clears {max_agree}/{n_ops} operator agreement; "
        "the prediction is operator-dependent, not convergent, and should be "
        "read as exploratory, not a confident hit list"
    )


def no_ground_truth_report(
    target_name: str,
    consensus: dict,
    docking: dict,
    *,
    resnums: np.ndarray | None = None,
    reason: str = "no holo/bound structure exists for this allosteric question",
) -> str:
    """Render TASK-0080's no-AUC/no-ceiling report for a target with no
    labeled holo pocket (`config/targets.yaml`'s `allosteric_pocket_exists:
    false`, `holo_pdb: null` -- c-Myc/1NKP is the only such mandatory
    target). Never attempts to compute or render `AUC`/ceiling/floor keys
    -- `verdict_template` is the wrong renderer for this target and is not
    reused with missing keys silently blank; this is a distinct report
    shape stating explicitly *why* those numbers are absent, per this
    task's own Constraint ("the absence of ground truth is itself
    information to surface").

    `consensus` is `analysis.consensus_ranking`'s output (cross-operator
    agreement, this target's only holo-free confidence signal).
    `docking` is `baselines.fpocket_baseline`'s output -- rendered
    whichever way it comes back, including its graceful `{"error": ...}`
    degradation (fpocket is not installed in this repo's dev/CI
    environment; that absence is reported honestly, not masked as "no
    pockets found").
    """
    lines = [
        f"=== {target_name} -- NO GROUND TRUTH ===",
        "",
        f"No AUC, no ceiling, and no proximity-floor check are computed or",
        f"reported for this target: {reason}. This is this target's own",
        "documented status (config/targets.yaml), not a scoring failure or",
        "an omission -- per this project's own convention, an honest NO is",
        "reported explicitly, not silently dropped.",
        "",
        f"Consensus prediction across {consensus['n_operators']} independent "
        f"operators ({', '.join(consensus['operators'])}), top-{consensus['k']}:",
    ]
    for rank, idx in enumerate(consensus["consensus_ranked_indices"], start=1):
        label = int(resnums[idx]) if resnums is not None else int(idx)
        agree = int(consensus["consensus_count"][idx])
        occ = float(consensus["mean_occupancy"][idx])
        lines.append(
            f"  {rank}. residue {label} -- {agree}/{consensus['n_operators']} "
            f"operators agree (top-{consensus['k']}), mean occupancy={occ:.4f}"
        )
    lines += [
        "",
        f"Confidence: {_consensus_confidence_statement(consensus)}",
        "",
        "Theoretical docking viability (fpocket):",
    ]
    if "error" in docking:
        lines.append(f"  unavailable -- {docking['error']}")
    else:
        pockets = docking.get("pockets", [])
        if not pockets:
            lines.append("  fpocket ran but found no druggable cavities.")
        else:
            for p in pockets[:5]:
                lines.append(
                    f"  pocket {p.get('id')}: score={p.get('score')}, "
                    f"druggability_score={p.get('druggability_score')}"
                )
    return "\n".join(lines)
