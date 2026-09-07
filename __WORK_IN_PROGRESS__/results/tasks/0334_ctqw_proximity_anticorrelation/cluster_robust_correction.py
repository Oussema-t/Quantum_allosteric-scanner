#!/usr/bin/env python3
"""TASK-0337 -- cluster-robust correction to TASK-0334's proximity-
anticorrelation result.

Confirmed independently before this script was written (see the filing,
`.ai/reviews/2026-09-07/REVIEW-2026-09-07-adversarial-submission-audit.md`
S3.2): `distance_anticorrelation.py` computed Spearman rho over
STRUCTURES, never referencing the `cluster` column present in the very CSV
it reads. The is_distal cohort is concentrated -- CAS0002 alone contributes
20% of the full 138-row population -- so "n=44" was 44 correlated rows,
not 44 independent proteins, and the row-level p-values are inflated by an
unknown factor.

Fix, per this task's own Intent Contract: collapse to cluster MEDIANS
before the Spearman, then get a p-value from CLUSTER-level permutation
(shuffle which cluster's distance goes with which cluster's hit-rate,
recompute rho, repeat) and a 95% CI from a CLUSTER bootstrap (resample
clusters with replacement) -- both are named as acceptable in the Intent
Contract ("cluster bootstrap or cluster permutation"); both are reported
here since at n_clusters in the 20s-30s neither alone is fully convincing.
[[TASK-0328]]'s own `det_seed` is reused for deterministic seeding (the
same discipline, not its `draw_pocket_block_null` verbatim -- that
function's null is a within-protein RESIDUE permutation respecting pocket
blocks, a different object than this task's between-CLUSTER permutation of
a between-protein correlation; reusing it directly would not be the right
null for this statistic, stated here rather than forcing a fit).

Applied to all 4 columns TASK-0334 reports (pre/post-veto x held-out/full,
x 2 distance metrics = 8 numbers) and to both specificity controls
(PASSer hit, random arm).

Planned Validation (run first, in the conversation that filed this task,
confirmed again here): re-running `distance_anticorrelation.py` unmodified
reproduces its own stored result.json byte-for-byte -- the row-level
numbers this correction starts from are not in question, only how they are
counted.

Usage: python3 cluster_robust_correction.py
"""
import json
import os
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
TASK0327_DIR = os.path.join(HERE, "..", "0327_passer_reference_arms")
TASK0328_DIR = os.path.join(HERE, "..", "..", "..", "scripts")
sys.path.insert(0, os.path.abspath(TASK0327_DIR))
sys.path.insert(0, os.path.abspath(TASK0328_DIR))
from reference_arms import load_round, analyze_protein, LEAKY_SOURCES  # noqa: E402
from task0328_pocketsweep_null_recalibration import det_seed  # noqa: E402
from distance_anticorrelation import load_distances, TASK0328_ARTIFACTS  # noqa: E402

B_PERM = 10000
B_BOOT = 10000


def build_rows(per_protein, dist, metric, held_out_only):
    rows = []
    for p in per_protein:
        if held_out_only and p.get("source") in LEAKY_SOURCES:
            continue
        d = dist.get(p["name"])
        if d is None or d[metric] is None:
            continue
        if p.get("cell_hit_rate") is None:
            continue
        rows.append(dict(
            cluster=p["cluster"],
            dist=d[metric],
            pipeline_hit_rate=p["cell_hit_rate"],
            passer_hit=p["passer_hit"],
            random_p=p["random_p"],
        ))
    return rows


def cluster_collapse(rows, value_key):
    """Median distance and median value per cluster -- the fix itself."""
    by_cluster = {}
    for r in rows:
        by_cluster.setdefault(r["cluster"], []).append(r)
    clusters = sorted(by_cluster.keys())
    dists = np.array([np.median([r["dist"] for r in by_cluster[c]]) for c in clusters])
    vals = np.array([np.median([r[value_key] for r in by_cluster[c]]) for c in clusters])
    sizes = {c: len(by_cluster[c]) for c in clusters}
    return clusters, dists, vals, sizes


def cluster_permutation_p(dists, vals, seed_name, obs_rho):
    rng = np.random.default_rng(det_seed(seed_name + "|cluster_perm"))
    n = len(vals)
    perm_rhos = np.empty(B_PERM)
    for b in range(B_PERM):
        perm = rng.permutation(n)
        perm_rhos[b] = stats.spearmanr(dists, vals[perm])[0]
    # two-sided, add-one smoothing -- never report p=0 from a finite Monte Carlo
    p = (np.sum(np.abs(perm_rhos) >= abs(obs_rho)) + 1) / (B_PERM + 1)
    return float(p)


def cluster_bootstrap_ci(dists, vals, seed_name):
    rng = np.random.default_rng(det_seed(seed_name + "|cluster_boot"))
    n = len(vals)
    boot_rhos = np.empty(B_BOOT)
    for b in range(B_BOOT):
        idx = rng.integers(0, n, size=n)
        # spearmanr on a resample with ties/duplicates is well-defined
        r = stats.spearmanr(dists[idx], vals[idx])[0]
        boot_rhos[b] = r if np.isfinite(r) else 0.0
    lo, hi = np.percentile(boot_rhos, [2.5, 97.5])
    return float(lo), float(hi)


def analyze(rows, value_key, seed_name):
    clusters, dists, vals, sizes = cluster_collapse(rows, value_key)
    n_clusters = len(clusters)
    if n_clusters < 4:
        return dict(n_clusters=n_clusters, note="too few clusters")
    obs_rho, asymptotic_p = stats.spearmanr(dists, vals)
    perm_p = cluster_permutation_p(dists, vals, seed_name, obs_rho)
    ci_lo, ci_hi = cluster_bootstrap_ci(dists, vals, seed_name)
    top_clusters = sorted(sizes.items(), key=lambda kv: -kv[1])[:3]
    return dict(
        n_clusters=n_clusters,
        n_rows=sum(sizes.values()),
        cluster_rho=float(obs_rho),
        cluster_rho_asymptotic_p=float(asymptotic_p),
        cluster_permutation_p=perm_p,
        cluster_bootstrap_95ci=[ci_lo, ci_hi],
        top3_cluster_sizes=top_clusters,
    )


def main():
    dist_path = os.path.join(HERE, "pocket_distance.csv")
    dist = load_distances(dist_path)

    results = {}
    for round_name, pattern in (("round1_pre_veto", "s14_r1_k10_h2_*.json"),
                                 ("round2_post_veto", "s14_r2_k10_h2_*.json")):
        raw = load_round(os.path.join(TASK0328_ARTIFACTS, pattern))
        per_protein = []
        for name, rec in raw.items():
            a = analyze_protein(rec)
            if a is not None:
                a["name"] = name
                per_protein.append(a)

        round_out = {}
        for metric in ("median_hop", "median_euclid"):
            for cohort_name, held_out in (("full_cohort", False), ("held_out", True)):
                rows = build_rows(per_protein, dist, metric, held_out)
                seed_name = f"{round_name}|{metric}|{cohort_name}"
                key = f"{cohort_name}__{metric}"
                round_out[key] = dict(
                    pipeline_hit_rate=analyze(rows, "pipeline_hit_rate", seed_name),
                    passer_hit=analyze(rows, "passer_hit", seed_name),
                    random_p=analyze(rows, "random_p", seed_name),
                )
        results[round_name] = round_out

    print("=== Cluster-robust correction ===\n")
    for round_name, round_out in results.items():
        print(f"--- {round_name} ---")
        for key, arms in round_out.items():
            pipe = arms["pipeline_hit_rate"]
            passer = arms["passer_hit"]
            rand = arms["random_p"]
            print(f"  {key}:")
            print(f"    pipeline: n_clusters={pipe['n_clusters']} rho={pipe['cluster_rho']:.3f} "
                  f"perm_p={pipe['cluster_permutation_p']:.4g} "
                  f"95%CI=[{pipe['cluster_bootstrap_95ci'][0]:.3f},{pipe['cluster_bootstrap_95ci'][1]:.3f}] "
                  f"top3_cluster_sizes={pipe['top3_cluster_sizes']}")
            print(f"    passer:   n_clusters={passer['n_clusters']} rho={passer['cluster_rho']:.3f} "
                  f"perm_p={passer['cluster_permutation_p']:.4g}")
            print(f"    random:   n_clusters={rand['n_clusters']} rho={rand['cluster_rho']:.3f} "
                  f"perm_p={rand['cluster_permutation_p']:.4g}")
        print()

    out_path = os.path.join(HERE, "cluster_robust_correction_result.json")
    json.dump(results, open(out_path, "w"), indent=2)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
