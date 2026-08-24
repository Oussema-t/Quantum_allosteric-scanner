#!/usr/bin/env python3
"""TASK-0241 -- statistical analysis of task0241_reproducibility_and_jitter.py's
own results.json: jitter distributions, hit rates under strict `_is_hit`,
Mann-Whitney U (old vs new method, per target), and the vdwrep-vs-overlap_frac
mechanism check ((A)/(B) reconciliation)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats

RESULTS = Path(__file__).resolve().parent.parent / "results/tasks/0241_reproducibility_and_jitter/results.json"

# Published TASK-0235 full-displacement pre-repack vdwrep ratios to native apo (Done section table)
VDWREP_RATIO = {
    "KRAS_G12C": {"old": 12.07, "new": 6.46},
    "BCR_ABL1": {"old": 2.92, "new": 2.86},
    "CARDIAC_MYOSIN": {"old": 3.02, "new": 2.84},
}


def summarize(trials: list) -> dict:
    d = [t["druggability_score"] for t in trials if "error" not in t and t.get("druggability_score") is not None]
    o = [t["overlap_frac"] for t in trials if "error" not in t]
    hits = [t["hit"] for t in trials if "error" not in t]
    n = len(trials)
    n_err = sum(1 for t in trials if "error" in t)
    return {
        "n": n, "n_errors": n_err,
        "druggability_median": round(float(np.median(d)), 3) if d else None,
        "druggability_iqr": [round(float(np.percentile(d, 25)), 3), round(float(np.percentile(d, 75)), 3)] if d else None,
        "druggability_min_max": [round(float(min(d)), 3), round(float(max(d)), 3)] if d else None,
        "overlap_frac_mean": round(float(np.mean(o)), 3) if o else None,
        "hit_rate": round(sum(hits) / len(hits), 3) if hits else None,
        "hit_count": f"{sum(hits)}/{len(hits)}" if hits else None,
        "bare_bar_count": f"{sum(1 for x in d if x >= 0.5)}/{len(d)}" if d else None,
    }


def main() -> int:
    data = json.loads(RESULTS.read_text())

    print("=" * 70)
    print("EXPERIMENT A -- pure tool jitter, BCR_ABL1, byte-identical input")
    print("=" * 70)
    expA = data["experiment_a_pure_jitter"]["BCR_ABL1"]
    for method, trials in expA.items():
        s = summarize(trials)
        print(f"{method}: {json.dumps(s)}")

    print()
    print("=" * 70)
    print("EXPERIMENT B -- perturbed re-run, all targets, both methods")
    print("=" * 70)
    expB = data["experiment_b_perturbed_rerun"]
    summary_table = {}
    for target, methods in expB.items():
        summary_table[target] = {}
        print(f"\n--- {target} ---")
        for method, trials in methods.items():
            s = summarize(trials)
            summary_table[target][method] = s
            print(f"{method}: {json.dumps(s)}")

        d_old = [t["druggability_score"] for t in methods["old_rigid"] if "error" not in t]
        d_new = [t["druggability_score"] for t in methods["new_local_kabsch"] if "error" not in t]
        if d_old and d_new:
            u, p = stats.mannwhitneyu(d_new, d_old, alternative="two-sided")
            print(f"Mann-Whitney U (new vs old druggability): U={u:.1f} p={p:.4f}")
            summary_table[target]["mannwhitney_druggability_p"] = round(float(p), 4)

        hits_old = [t["hit"] for t in methods["old_rigid"] if "error" not in t]
        hits_new = [t["hit"] for t in methods["new_local_kabsch"] if "error" not in t]
        if hits_old and hits_new:
            table = [[sum(hits_old), len(hits_old) - sum(hits_old)], [sum(hits_new), len(hits_new) - sum(hits_new)]]
            odds, p_fisher = stats.fisher_exact(table)
            print(f"Fisher exact (hit rate, old vs new): table={table} p={p_fisher:.4f}")
            summary_table[target]["fisher_hit_rate_p"] = round(float(p_fisher), 4)

        vr = VDWREP_RATIO.get(target, {})
        old_overlap = summary_table[target]["old_rigid"]["overlap_frac_mean"]
        new_overlap = summary_table[target]["new_local_kabsch"]["overlap_frac_mean"]
        if vr and old_overlap is not None and new_overlap is not None:
            vdwrep_pct_change = (vr["new"] - vr["old"]) / vr["old"] * 100
            overlap_pct_change = (new_overlap - old_overlap) / old_overlap * 100 if old_overlap else float("nan")
            print(f"Mechanism check: vdwrep ratio change {vdwrep_pct_change:+.1f}%, "
                  f"overlap_frac change {overlap_pct_change:+.1f}% (old={old_overlap:.3f} new={new_overlap:.3f})")
            summary_table[target]["mechanism_check"] = {
                "vdwrep_ratio_pct_change": round(vdwrep_pct_change, 1),
                "overlap_frac_pct_change": round(overlap_pct_change, 1),
                "overlap_frac_old_mean": old_overlap, "overlap_frac_new_mean": new_overlap,
            }

    out_path = Path(__file__).resolve().parent.parent / "results/tasks/0241_reproducibility_and_jitter/summary.json"
    out_path.write_text(json.dumps(summary_table, indent=2))
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
