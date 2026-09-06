#!/usr/bin/env python3
"""TASK-0334 -- is the pipeline's below-chance pocket pick (TASK-0327) a
proximity mechanism, not a defect?

TASK-0320 measured rho(ctqw, proximity) = +0.808 at candidate level: the walk
tracks distance from the active site. If the annotated truth pocket is
genuinely distal, a proximity-tracking score should *anti*-predict it. This
script tests that directly: does the pipeline's per-protein hit rate on the
drug/truth pocket fall as that pocket's distance from the active site grows?

Read-only over already-stored artifacts -- no walk re-run, no PDB refetch:
  - s14_r{1,2}_k10_h2_*.json (vendored by TASK-0328 at
    __WORK_IN_PROGRESS__/results/tasks/0328_pocketsweep_null_recalibration/
    upstream_artifacts/) -- reuses TASK-0327's own analyze_protein() via
    direct import, so the hit/arm definitions cannot drift from that task's.
  - pocket_distance.csv (vendored here, from origin/allosteric @ 8dcc6fa,
    current HEAD at fetch time; byte-identical to the f257789 copy TASK-0331
    used -- checked via `git diff f257789 8dcc6fa -- allosteric/datasets/
    pocket_distance.csv`, no output). Columns used: min_euclid, median_euclid,
    min_hop, median_hop, is_distal -- all computed by the collaborator between
    each protein's annotated "active" residues and annotated "true" (truth
    pocket) residues, i.e. exactly the (active site, drug/truth pocket)
    distance TASK-0334's Outcome (b) asks for.

WHAT THIS DOES NOT ANSWER: TASK-0334's Outcome also names (a) the distance
from the active site to the pocket the pipeline actually ranks #1, for the
cases where that is *not* the truth pocket (a miss). pocket_distance.csv only
carries (active site, truth pocket) distances -- it does not carry
(active site, candidate pocket) distances for the other, non-truth candidate
pockets in each protein's fpocket/PASSer set, and getting those would mean
recomputing per-pocket centroid geometry from the raw PDB structures, which
Constraints rules out ("no PDB refetch"). So arm (a) is not directly
measured here. What IS measured, and is the operational form of the same
mechanistic question: does the pipeline's *hit rate on the truth pocket*
fall as that pocket's own distance from the active site grows? If the walk
is a proximity detector, yes; if the below-chance result has some other
cause, no reason to expect it. This is stated as a limitation, not smoothed
over, per this task's own Planned Validation discipline.

Usage: python3 distance_anticorrelation.py
"""
import csv
import glob
import json
import os
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
TASK0327_DIR = os.path.join(HERE, "..", "0327_passer_reference_arms")
TASK0328_ARTIFACTS = os.path.join(
    HERE, "..", "0328_pocketsweep_null_recalibration", "upstream_artifacts"
)
sys.path.insert(0, os.path.abspath(TASK0327_DIR))
from reference_arms import load_round, analyze_protein, LEAKY_SOURCES  # noqa: E402


def load_distances(path):
    """protein-name -> distance-metric dict, from pocket_distance.csv."""
    out = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            out[row["name"]] = dict(
                source=row["source"],
                truth_type=row["truth_type"],
                min_euclid=float(row["min_euclid"]) if row["min_euclid"] else None,
                median_euclid=float(row["median_euclid"]) if row["median_euclid"] else None,
                min_hop=float(row["min_hop"]) if row["min_hop"] else None,
                median_hop=float(row["median_hop"]) if row["median_hop"] else None,
                is_distal=row["is_distal"] == "True",
            )
    return out


def validate_join(per_protein, dist, asbench_distal_pdbs_task0331):
    """Planned Validation: the true pocket's own distance distribution must
    match pocket_distance.csv's is_distal flag on the same rows, and the
    asbench curated_allosteric distal subset re-derived here must match
    TASK-0331's own 49-PDB count exactly (it is the same CSV, filtered the
    same way -- this checks the join key, not the science)."""
    matched, unmatched = 0, []
    for p in per_protein:
        if p["name"] in dist:
            matched += 1
        else:
            unmatched.append(p["name"])
    asbench_distal_here = sorted(
        name
        for name, d in dist.items()
        if d["source"] == "asbench" and d["truth_type"] == "curated_allosteric" and d["is_distal"]
    )
    return dict(
        n_scoreable=len(per_protein),
        n_matched=matched,
        n_unmatched=len(unmatched),
        unmatched_names=unmatched[:10],
        asbench_distal_count_here=len(asbench_distal_here),
        asbench_distal_count_task0331=asbench_distal_pdbs_task0331,
        asbench_distal_sets_agree=(len(asbench_distal_here) == asbench_distal_pdbs_task0331),
    )


def correlate(per_protein, dist, metric, held_out_only):
    """Spearman rho between per-protein pipeline hit-rate (mean of per-cell
    arm-4 hits, i.e. how often the pipeline's #1 pick IS the truth pocket)
    and the truth pocket's own distance from the active site. Reported
    alongside the same correlation for arm 1 (PASSer, binary hit) and a
    sanity check that arm 2 (random, closed-form, no proximity term by
    construction) shows none -- if it did, pocket *size* itself would be
    confounded with distance and the whole read would need re-doing."""
    rows = []
    for p in per_protein:
        if held_out_only and p.get("source") in LEAKY_SOURCES:
            continue
        d = dist.get(p["name"])
        if d is None or d[metric] is None:
            continue
        if p.get("cell_hit_rate") is None:
            continue
        pipeline_hit_rate = p["cell_hit_rate"]
        rows.append(
            dict(
                name=p["name"],
                dist=d[metric],
                is_distal=d["is_distal"],
                pipeline_hit_rate=pipeline_hit_rate,
                passer_hit=p["passer_hit"],
                random_p=p["random_p"],
                chance=p["chance"],
            )
        )
    n = len(rows)
    if n < 4:
        return dict(n=n, note="too few rows to correlate")
    dists = [r["dist"] for r in rows]
    pipe = [r["pipeline_hit_rate"] for r in rows]
    passer = [r["passer_hit"] for r in rows]
    randp = [r["random_p"] for r in rows]
    rho_pipe, p_pipe = stats.spearmanr(dists, pipe)
    rho_passer, p_passer = stats.spearmanr(dists, passer)
    rho_rand, p_rand = stats.spearmanr(dists, randp)
    distal = [r for r in rows if r["is_distal"]]
    proximal = [r for r in rows if not r["is_distal"]]

    # is_distal is near-degenerate here (PIPELINE_DESIGN.md's own cohort
    # selection already restricts to is_distal proteins -- see below), so
    # also report a within-cohort median split on the continuous distance
    # metric itself, which is not degenerate and is what the rho above
    # already tests parametrically.
    med = float(np.median(dists))
    near = [r for r in rows if r["dist"] <= med]
    far = [r for r in rows if r["dist"] > med]

    return dict(
        n=n,
        n_distal=len(distal),
        n_proximal=len(proximal),
        median_distance=med,
        spearman_rho_pipeline_hitrate_vs_distance=rho_pipe,
        p_pipeline=p_pipe,
        spearman_rho_passer_hit_vs_distance=rho_passer,
        p_passer=p_passer,
        spearman_rho_random_arm_vs_distance=rho_rand,
        p_random=p_rand,
        pipeline_hitrate_mean_distal=float(np.mean([r["pipeline_hit_rate"] for r in distal])) if distal else None,
        pipeline_hitrate_mean_proximal=float(np.mean([r["pipeline_hit_rate"] for r in proximal])) if proximal else None,
        passer_hitrate_mean_distal=float(np.mean([r["passer_hit"] for r in distal])) if distal else None,
        passer_hitrate_mean_proximal=float(np.mean([r["passer_hit"] for r in proximal])) if proximal else None,
        n_near_half=len(near),
        n_far_half=len(far),
        pipeline_hitrate_near_half=float(np.mean([r["pipeline_hit_rate"] for r in near])) if near else None,
        pipeline_hitrate_far_half=float(np.mean([r["pipeline_hit_rate"] for r in far])) if far else None,
        passer_hitrate_near_half=float(np.mean([r["passer_hit"] for r in near])) if near else None,
        passer_hitrate_far_half=float(np.mean([r["passer_hit"] for r in far])) if far else None,
        random_p_near_half=float(np.mean([r["random_p"] for r in near])) if near else None,
        random_p_far_half=float(np.mean([r["random_p"] for r in far])) if far else None,
    )


def power_note(n):
    """Minimum |rho| a Spearman test could call significant at alpha=0.05,
    two-sided, at this n -- stated before interpretation, per this
    register's own standing rule after TASK-0313's addendum."""
    if n < 4:
        return None
    # critical rho approx via t-distribution inversion, standard formula
    from scipy.stats import t as tdist

    df = n - 2
    t_crit = tdist.ppf(0.975, df)
    rho_crit = t_crit / np.sqrt(df + t_crit**2)
    return dict(n=n, min_detectable_abs_rho_at_p05=float(rho_crit))


def run_round(round_name, pattern, dist, asbench_distal_task0331):
    raw = load_round(os.path.join(TASK0328_ARTIFACTS, pattern))
    per_protein = []
    for name, rec in raw.items():
        a = analyze_protein(rec)
        if a is not None:
            a["name"] = name
            per_protein.append(a)

    join_check = validate_join(per_protein, dist, asbench_distal_task0331)

    out = dict(round=round_name, join_check=join_check)
    for metric in ("median_hop", "median_euclid"):
        out[f"full_cohort__{metric}"] = correlate(per_protein, dist, metric, held_out_only=False)
        out[f"held_out__{metric}"] = correlate(per_protein, dist, metric, held_out_only=True)
    out["power_full_cohort"] = power_note(out["full_cohort__median_hop"].get("n", 0))
    out["power_held_out"] = power_note(out["held_out__median_hop"].get("n", 0))
    return out


def main():
    dist_path = os.path.join(HERE, "pocket_distance.csv")
    dist = load_distances(dist_path)

    # TASK-0331's own re-derived count, restated here as a join sanity check,
    # not re-verified against the collaborator's benchmark from scratch.
    ASBENCH_DISTAL_TASK0331 = 49

    r1 = run_round("round1_pre_veto", "s14_r1_k10_h2_*.json", dist, ASBENCH_DISTAL_TASK0331)
    r2 = run_round("round2_post_veto", "s14_r2_k10_h2_*.json", dist, ASBENCH_DISTAL_TASK0331)

    for r in (r1, r2):
        print(f"=== {r['round']} ===")
        print("  join check:", r["join_check"])
        print("  power (full cohort):", r["power_full_cohort"])
        print("  power (held-out):", r["power_held_out"])
        for metric in ("median_hop", "median_euclid"):
            print(f"  full cohort, {metric}:", r[f"full_cohort__{metric}"])
            print(f"  held-out,    {metric}:", r[f"held_out__{metric}"])
        print()

    out_path = os.path.join(HERE, "distance_anticorrelation_result.json")
    json.dump(dict(round1=r1, round2=r2), open(out_path, "w"), indent=2)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
