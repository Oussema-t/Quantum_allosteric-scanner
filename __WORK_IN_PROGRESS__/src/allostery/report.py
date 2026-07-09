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

def verdict_template(results: dict, *, provenance: str = "dev") -> str:
    """Render Sec.15's headline verdict + Sec.16's parameterized 5-point
    recommendation from an already-assembled `results` dict.

    `results` keys (verbatim from cell 58's `verdict` dict) --
    AUC_apo_Hnew_default, AUC_apo_H10_baseline, AUC_apo_Hnew_optimised,
    AUC_holo_Hnew_optimised, AUC_ctqw_mean, AUC_heat_mean,
    most_impactful_term, least_impactful_term, mean_rho_apo_holo,
    mean_jacc20 -- each optional; a missing key renders "N/A" in the
    headline block and skips its dependent recommendation line rather than
    raising, since a caller may not have every upstream analysis available
    for a given target.

    `provenance` must be exactly `"frozen"` (matches
    `protocol.py::ProtocolRoster`'s lowercase vocabulary) for this to be
    quoted as the actual submission verdict -- this task's own Constraints
    require a dev/ceiling number never be silently presented as a frozen
    result, so any other value prepends a loud banner making the
    distinction impossible to miss.

    Renders only the four data-driven recommendation lines from cell 60;
    that cell's fifth bullet ("Keep V_B and V_T as cheap priors...") is
    static prose independent of `results` -- competence-map narrative,
    out of this module's scope per this task's own Intent Contract.
    """
    lines = []
    if provenance != "frozen":
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
    for key in (
        "AUC_apo_Hnew_default", "AUC_apo_H10_baseline",
        "AUC_apo_Hnew_optimised", "AUC_holo_Hnew_optimised",
        "AUC_ctqw_mean", "AUC_heat_mean",
        "most_impactful_term", "least_impactful_term",
        "mean_rho_apo_holo", "mean_jacc20",
    ):
        lines.append(f"  {key:30s} : {fmt(key)}")

    lines.append("")
    lines.append("DECISION-SUPPORT RECOMMENDATION")
    lines.append("-" * 32)

    opt = results.get("AUC_apo_Hnew_optimised")
    base = results.get("AUC_apo_H10_baseline")
    if opt is not None and base is not None:
        diff = opt - base
        verdict = "meaningful" if diff > 0.05 else "marginal" if diff > 0.02 else "noise-level"
        lines.append(
            f"1) Operator gain over H10 baseline (apo): DAUC = {diff:+.3f}  ({verdict})."
        )

    ctqw = results.get("AUC_ctqw_mean")
    heat = results.get("AUC_heat_mean")
    if ctqw is not None and heat is not None:
        diff_qc = ctqw - heat
        verdict_qc = (
            "CTQW genuinely helps" if diff_qc > 0.05
            else "within graph-kernel noise -- CTQW does NOT add biological "
                 "information beyond the operator"
        )
        lines.append(
            f"2) CTQW vs classical heat on H_new (same operator): "
            f"DAUC = {diff_qc:+.3f}  ({verdict_qc})."
        )

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

    return "\n".join(lines)
