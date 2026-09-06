#!/usr/bin/env python3
"""TASK-0327 -- the three reference arms PIPELINE_DESIGN.md's own S5 specifies
(chance, random-residue-order, PASSer-alone-no-walk), reported side by side
with the pipeline as already run (round 1 = pre-veto, round 2 = post-veto).

Pure scoring pass over the already-stored artifacts (s14_r{1,2}_k10_h2_*.json)
-- no walk is re-run, no pocket is re-selected, no fpocket/PocketMiner call is
made. See PIPELINE_DESIGN.md S3/S4/S5 for the definitions this implements.

KEY IDENTITY USED THROUGHOUT (proved once here, not per-arm):
S3's own rule is "pocket score = its best member's residue score" (README /
PIPELINE_DESIGN.md, NOT the mean-based `top_pocket()` defined-but-unused in
pocketsweep.py -- that function contradicts the design doc and is never
called in main(), so it does not describe what actually produced the
checked-in numbers either; flagged, not silently used).
Under a "best member wins" rule, the top-ranked POCKET is, for any set of
per-residue scores, exactly whichever pocket contains the single top-ranked
RESIDUE overall -- no other pocket's best member can exceed the global max.
So:
  - the real pipeline's per-cell prediction reduces to "look up which pocket
    owns the residue with ranks[cell][i]==1" (no re-aggregation needed), and
  - "random residue order through the same veto" reduces to a closed form:
    P(a uniformly random top residue falls in pocket P) = |P| / n_seeds_total.
Both are implemented as this reduction, and the random-order arm's closed
form is cross-checked against an actual Monte Carlo shuffle before being
trusted (see verify_random_closed_form()).

Usage: python3 reference_arms.py
Reads: s14_r1_k10_h2_0.json, s14_r1_k10_h2_1.json (round 1, pre-veto)
       s14_r2_k10_h2_0.json, s14_r2_k10_h2_1.json (round 2, post-veto)
Writes: reference_arms_result.json
"""
import json
import glob
import numpy as np

RNG = np.random.default_rng(20260906)
DRUG_FRAC_BAR = 0.25  # PIPELINE_DESIGN.md's own "argmax rule" acceptance bar


def load_round(pattern):
    merged = {}
    for f in sorted(glob.glob(pattern)):
        d = json.load(open(f))
        merged.update(d)
    return merged


def drug_pocket_of(pockets):
    """PIPELINE_DESIGN.md's own truth-pocket rule: argmax n_drug, accepted
    only if drug_frac >= 0.25. Returns (pocket_id_or_None, valid_bool)."""
    if not pockets:
        return None, False
    best = max(pockets, key=lambda p: (p["n_drug"], p["drug_frac"]))
    return best["id"], best["drug_frac"] >= DRUG_FRAC_BAR


def analyze_protein(rec):
    """Returns None if this protein can't be scored (no cells / <2 candidate
    pockets / no valid drug pocket), else a dict of everything needed for
    all four arms, at protein level."""
    if "cells" not in rec:
        return None
    pockets = rec["pockets"]
    if len(pockets) < 2:
        return None
    drug_id, valid = drug_pocket_of(pockets)
    if not valid:
        return None
    n_total = sum(p["n"] for p in pockets)
    n_drug_pocket = next(p["n"] for p in pockets if p["id"] == drug_id)
    n_pockets = len(pockets)

    # Arm 3: chance
    chance = 1.0 / n_pockets

    # Arm 2: random residue order through the same (already-applied) veto --
    # closed form, see module docstring.
    random_p = n_drug_pocket / n_total

    # Arm 1: PASSer alone, no walk -- predicted pocket = best (lowest) rk_pa
    # among the SAME candidate set this round already carries (i.e. "no
    # walk" but the SAME veto state as this file: round 1 = veto off,
    # round 2 = veto on).
    passer_pred = min(pockets, key=lambda p: (p["rk_pa"] if p["rk_pa"] is not None else 10**9))["id"]
    passer_hit = int(passer_pred == drug_id)

    # Arm 4: the pipeline as already run -- per cell, the pocket owning the
    # rank==1 seed (see module docstring for why this equals the "best
    # member wins" pocket rule).
    seed_pocket = rec["seed_pocket"]
    cell_hits = {}
    for cell, ranks in rec["ranks"].items():
        top_idx = int(np.argmin(ranks))  # rank 1 == minimum
        pred = seed_pocket[top_idx]
        cell_hits[cell] = int(pred == drug_id)

    return dict(
        cluster=rec["cluster"],
        source=rec.get("source"),
        n_pockets=n_pockets,
        n_total_seeds=n_total,
        chance=chance,
        random_p=random_p,
        passer_hit=passer_hit,
        cell_hits=cell_hits,
        cell_hit_rate=float(np.mean(list(cell_hits.values()))) if cell_hits else None,
    )


def aggregate(per_protein):
    """Protein-level and family-level summaries for one round's data."""
    if not per_protein:
        return dict(n_proteins=0)
    n = len(per_protein)
    out = dict(n_proteins=n)
    out["coverage_valid_drug_pocket"] = n  # already filtered to valid==True

    out["chance_mean"] = float(np.mean([p["chance"] for p in per_protein]))
    out["random_mean"] = float(np.mean([p["random_p"] for p in per_protein]))
    out["passer_hit_rate"] = float(np.mean([p["passer_hit"] for p in per_protein]))

    # Arm 4, pooled-over-cells (design doc's "averaged over the cells")
    all_cell_hits = [h for p in per_protein for h in p["cell_hits"].values()]
    out["pipeline_pooled_cell_rate"] = float(np.mean(all_cell_hits)) if all_cell_hits else None

    # Arm 4, majority-of-cells-per-protein (design doc's criterion 3)
    protein_majority = [1 if p["cell_hit_rate"] > 0.5 else 0 for p in per_protein]
    out["pipeline_protein_majority_rate"] = float(np.mean(protein_majority))

    # Family-level: a family counts if the MAJORITY of its structures clear
    # the per-protein majority bar (mandatory per PIPELINE_DESIGN.md's own
    # "family pseudo-replication" caveat and this task's own Constraint).
    fams = {}
    for p, hit in zip(per_protein, protein_majority):
        fams.setdefault(p["cluster"], []).append(hit)
    fam_pass = [1 if np.mean(v) > 0.5 else 0 for v in fams.values()]
    out["n_families"] = len(fams)
    out["pipeline_family_majority_rate"] = float(np.mean(fam_pass)) if fam_pass else None

    # Same family-level rollup applied to PASSer-alone, for a fair
    # apples-to-apples comparison (not just protein-level for one arm and
    # family-level for another).
    passer_fam = {}
    for p in per_protein:
        passer_fam.setdefault(p["cluster"], []).append(p["passer_hit"])
    passer_fam_pass = [1 if np.mean(v) > 0.5 else 0 for v in passer_fam.values()]
    out["passer_family_majority_rate"] = float(np.mean(passer_fam_pass)) if passer_fam_pass else None

    return out


def verify_random_closed_form(per_protein, reps=2000):
    """Cross-check the closed form (pocket_size/n_total) against an actual
    Monte Carlo shuffle on a handful of real proteins, not assumed."""
    checked = []
    for p in per_protein[: min(15, len(per_protein))]:
        n_total = p["n_total_seeds"]
        n_drug = round(p["random_p"] * n_total)
        hits = 0
        for _ in range(reps):
            perm = RNG.permutation(n_total)
            hits += int(perm[0] < n_drug)  # drug-pocket seeds occupy indices [0, n_drug) WLOG
        mc = hits / reps
        checked.append((p["random_p"], mc, abs(p["random_p"] - mc)))
    max_err = max(c[2] for c in checked) if checked else 0.0
    return dict(n_checked=len(checked), max_abs_error=max_err, samples=checked[:5])


# PASSer's own published papers name ASD/ASBench as TRAINING data and
# CASBench as an EXTERNAL TEST set -- these are not interchangeable and
# an earlier pass of this script wrongly lumped them together (corrected
# 2026-09-06, see TASK-0327's own Done section for the full citation
# trail):
#   Xiao, Tian & Tao (2022), "PASSer2.0: Accurate Prediction of Protein
#     Allosteric Sites Through Automated Machine Learning," Front. Mol.
#     Biosci. 9:879251, doi:10.3389/fmolb.2022.879251 -- trained on ASD
#     (90 proteins) + ASBench's core-diversity set (138 proteins).
#   Tian, Xiao, Jiang & Tao (2023), "PASSer: fast and accurate
#     prediction of protein allosteric sites," Nucleic Acids Res.
#     51(W1):W427-W431, doi:10.1093/nar/gkad303 -- the "ensemble" model
#     this cache is keyed on (passer_cache.json's own "|ensemble" key
#     matches this paper's naming). Trained on ASD (207) + ASBench
#     core-diversity (138); CASBench (1049 after filtering) held out as
#     an EXTERNAL TEST set, not used to fit the model.
#   Tian, Xiao, Jiang & Tao (2023), "PASSerRank: Prediction of Allosteric
#     Sites with Learning to Rank," J. Comput. Chem.,
#     doi:10.1002/jcc.27193 (preprint: arXiv:2302.01117) -- trained on
#     ASD (207, 80/20 split); CASBench again an external test set (ASD
#     overlap explicitly removed by the authors); ASBench explicitly
#     NOT used for training in this specific paper.
# Net, across all three: ASBench is consistently training data for the
# PASSer lineage; CASBench is consistently the authors' OWN held-out
# test set, not training data. Scoring "PASSer alone" on asbench-sourced
# structures is therefore not a fair blind-baseline comparison; scoring
# it on casbench-sourced structures is -- CASBench is exactly the kind
# of external benchmark PASSer's own authors used to claim generalization,
# not memorization.
LEAKY_SOURCES = {"asbench"}


def run_round(label, files):
    raw = load_round(files)
    per_protein = []
    n_raw = len(raw)
    n_with_cells = sum(1 for v in raw.values() if "cells" in v)
    for name, rec in raw.items():
        a = analyze_protein(rec)
        if a is not None:
            a["name"] = name
            per_protein.append(a)
    agg = aggregate(per_protein)
    agg["n_raw_records"] = n_raw
    agg["n_with_cells"] = n_with_cells
    agg["n_valid_drug_pocket"] = len(per_protein)
    agg["coverage_frac"] = (len(per_protein) / n_with_cells) if n_with_cells else None
    verify = verify_random_closed_form(per_protein)

    held_out = [p for p in per_protein if p.get("source") not in LEAKY_SOURCES]
    agg_held_out = aggregate(held_out) if held_out else dict(n_proteins=0)
    src_counts = {}
    for p in per_protein:
        src_counts[p.get("source")] = src_counts.get(p.get("source"), 0) + 1

    return agg, verify, per_protein, agg_held_out, src_counts


def main():
    print("=== Round 1 (pre-veto, N_POCKETS=10, MIN_HOP=2) ===")
    r1_agg, r1_verify, r1_pp, r1_held, r1_src = run_round("round1", "s14_r1_k10_h2_*.json")
    for k, v in r1_agg.items():
        print(f"  {k}: {v}")
    print("  random-closed-form check:", r1_verify)
    print("  source counts:", r1_src)
    print("  HELD-OUT ONLY (excludes asbench/casbench -- PASSer's own reported training/validation sets):")
    for k, v in r1_held.items():
        print(f"    {k}: {v}")

    print("\n=== Round 2 (post-veto) ===")
    r2_agg, r2_verify, r2_pp, r2_held, r2_src = run_round("round2", "s14_r2_k10_h2_*.json")
    for k, v in r2_agg.items():
        print(f"  {k}: {v}")
    print("  random-closed-form check:", r2_verify)
    print("  source counts:", r2_src)
    print("  HELD-OUT ONLY (excludes asbench/casbench -- PASSer's own reported training/validation sets):")
    for k, v in r2_held.items():
        print(f"    {k}: {v}")

    out = dict(
        round1_pre_veto=r1_agg,
        round1_random_closed_form_check=r1_verify,
        round1_source_counts=r1_src,
        round1_held_out_only=r1_held,
        round2_post_veto=r2_agg,
        round2_random_closed_form_check=r2_verify,
        round2_source_counts=r2_src,
        round2_held_out_only=r2_held,
    )
    json.dump(out, open("reference_arms_result.json", "w"), indent=2)
    print("\nWrote reference_arms_result.json")


if __name__ == "__main__":
    main()
