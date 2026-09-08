#!/usr/bin/env python3
"""TASK-0345 -- analyze apo_holo_delta_result.json: positive control,
the (2)-(1) headline delta, (3) as ceiling, cluster-robust (by apo PDB,
this cohort is 62/63 already-unique proteins -- checked, not assumed).
"""
import json
from collections import Counter

import numpy as np
from scipy import stats

R = json.load(open("apo_holo_delta_result.json"))
B = 10000
rng_seed = 20260908


def rows():
    for x in R:
        s1, s2, s3 = x["state1_apo"], x["state2_holo_stripped"], x["state3_holo_deposited"]
        yield dict(
            apo=x["pair"]["apo"], holo=x["pair"]["holo"], source=x["pair"]["source"],
            d1=s1["best_druggability"], d2=s2["best_druggability"], d3=s3["best_druggability"],
            det1=s1["detected"], det2=s2["detected"], det3=s3["detected"],
            r1=s1["best_rank"], r2=s2["best_rank"], r3=s3["best_rank"],
            n1=s1["n_pockets"], n2=s2["n_pockets"], n3=s3["n_pockets"],
        )


rows = list(rows())
print(f"n pairs = {len(rows)}")
print(f"n distinct apo PDBs = {len(set(r['apo'] for r in rows))} (cluster key)")
print(f"source counts: {Counter(r['source'] for r in rows)}")

# ---- positive control ----
pos_ctrl_ok = sum(1 for r in rows if r["d3"] >= r["d2"] and r["d3"] >= r["d1"])
print(f"\nPositive control (state3 >= state2 and state3 >= state1): {pos_ctrl_ok}/{len(rows)}")
viol = [r for r in rows if not (r["d3"] >= r["d2"] and r["d3"] >= r["d1"])]
for r in viol:
    print(f"  VIOLATION {r['apo']}/{r['holo']}: d1={r['d1']:.3f} d2={r['d2']:.3f} d3={r['d3']:.3f}")

det1 = np.mean([r["det1"] for r in rows])
det2 = np.mean([r["det2"] for r in rows])
det3 = np.mean([r["det3"] for r in rows])
print(f"\nDetection rate (site found at all): apo={det1:.3f} stripped={det2:.3f} deposited={det3:.3f}")

d1 = np.array([r["d1"] for r in rows])
d2 = np.array([r["d2"] for r in rows])
d3 = np.array([r["d3"] for r in rows])
delta = d2 - d1
print(f"\nDruggability: apo mean={d1.mean():.3f} median={np.median(d1):.3f}")
print(f"              stripped-holo mean={d2.mean():.3f} median={np.median(d2):.3f}")
print(f"              deposited-holo mean={d3.mean():.3f} median={np.median(d3):.3f}")
print(f"\nHEADLINE delta (stripped - apo): mean={delta.mean():.4f} median={np.median(delta):.4f}")
print(f"  n positive (stripped easier): {np.sum(delta>0)}  n negative: {np.sum(delta<0)}  n zero: {np.sum(delta==0)}")

w_stat, w_p = stats.wilcoxon(d2, d1)
print(f"  Wilcoxon signed-rank (paired, row-level): stat={w_stat:.1f} p={w_p:.3g}")

# ---- rank delta (lower rank = better; None -> n_pockets+1 sentinel = worse than any detected rank) ----
def rank_or_sentinel(r_key, n_key, row):
    return row[r_key] if row[r_key] is not None else row[n_key] + 1


rk1 = np.array([rank_or_sentinel("r1", "n1", r) for r in rows], dtype=float)
rk2 = np.array([rank_or_sentinel("r2", "n2", r) for r in rows], dtype=float)
print(f"\nRank (1=best; not-detected -> n_pockets+1 sentinel): apo mean={rk1.mean():.2f} stripped mean={rk2.mean():.2f}")

# ---- cluster-robust: cluster key = apo PDB id (checked: 62/63 already unique) ----
rng = np.random.default_rng(rng_seed)
n = len(delta)
boot = np.empty(B)
for b in range(B):
    idx = rng.integers(0, n, size=n)
    boot[b] = np.mean(delta[idx])
ci_lo, ci_hi = np.percentile(boot, [2.5, 97.5])
print(f"\nCluster(=pair)-bootstrap 95% CI on mean delta: [{ci_lo:.4f}, {ci_hi:.4f}]  (B={B})")

# sign-flip permutation test (paired, exact-in-spirit): under H0 the sign of
# each pair's delta is a coin flip -- permute signs, not values, to preserve
# each pair's own magnitude
rng2 = np.random.default_rng(rng_seed + 1)
obs_mean = delta.mean()
perm = np.empty(B)
absdelta = np.abs(delta)
for b in range(B):
    signs = rng2.choice([-1, 1], size=n)
    perm[b] = np.mean(signs * absdelta)
perm_p = (np.sum(np.abs(perm) >= abs(obs_mean)) + 1) / (B + 1)
print(f"Sign-flip permutation p (two-sided, B={B}): {perm_p:.4g}")

by_source = {}
for src in ("cryptosite", "pocketminer"):
    sub = [r["d2"] - r["d1"] for r in rows if r["source"] == src]
    if sub:
        by_source[src] = dict(n=len(sub), mean=float(np.mean(sub)), median=float(np.median(sub)))
print(f"\nBy source: {by_source}")

out = dict(
    n_pairs=len(rows),
    n_distinct_apo=len(set(r["apo"] for r in rows)),
    positive_control_pass=pos_ctrl_ok,
    positive_control_violations=[dict(apo=r["apo"], holo=r["holo"], d1=r["d1"], d2=r["d2"], d3=r["d3"]) for r in viol],
    detection_rate=dict(apo=float(det1), stripped=float(det2), deposited=float(det3)),
    druggability_mean=dict(apo=float(d1.mean()), stripped=float(d2.mean()), deposited=float(d3.mean())),
    druggability_median=dict(apo=float(np.median(d1)), stripped=float(np.median(d2)), deposited=float(np.median(d3))),
    headline_delta_stripped_minus_apo=dict(
        mean=float(delta.mean()), median=float(np.median(delta)),
        n_positive=int(np.sum(delta > 0)), n_negative=int(np.sum(delta < 0)), n_zero=int(np.sum(delta == 0)),
        wilcoxon_stat=float(w_stat), wilcoxon_p=float(w_p),
        bootstrap_95ci=[float(ci_lo), float(ci_hi)],
        signflip_permutation_p=float(perm_p),
    ),
    rank_mean=dict(apo=float(rk1.mean()), stripped=float(rk2.mean())),
    by_source=by_source,
)
json.dump(out, open("analysis_result.json", "w"), indent=2)
print("\nWrote analysis_result.json")
