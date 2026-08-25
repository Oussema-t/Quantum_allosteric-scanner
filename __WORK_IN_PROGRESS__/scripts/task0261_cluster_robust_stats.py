#!/usr/bin/env python3
"""TASK-0261 -- every p-value in the frozen-set analyses is over-counted:
20 scoreable rows, but only 13 distinct apo structures. Seven apo PDBs
each carry two rows (a second ligand bound to an apo structure already
counted); every apo-side quantity (geometry, CTQW, ENM validity, hop,
fpocket cavities) is therefore correlated within a pair, not independent,
yet every Wilcoxon/Mann-Whitney/Spearman test in [[TASK-0249]]/[[TASK-0254]]/
[[TASK-0257]]/[[TASK-0259]] treats all 20/16/9 rows as exchangeable.

**Method chosen, and why (this task's own Scope explicitly rules out plain
within-cluster averaging as "a first pass, not the right method")**:
cluster-level PERMUTATION, not a mixed model. With 13 clusters -- 6
singletons, 7 pairs -- there is nowhere near enough replication to fit a
random-intercept variance component reliably (a mixed model needs many
more clusters than 7 non-trivial ones to estimate between-cluster
variance without it being numerically degenerate). Permutation makes no
distributional assumption and is *exact* here: with only 13 clusters, the
full space of cluster-level sign patterns (2^13 = 8192) or cluster-block
label permutations is small enough to enumerate or densely Monte-Carlo
sample, so the null distribution is not an approximation the way a
mixed-model p-value would be. This generalises the classical tests being
corrected without discarding within-cluster information the way averaging
does: every row keeps its own value in the test statistic; only the
resampling *unit* moves from row to cluster.

**Verified, not assumed, before designing the test**: [[TASK-0261]]'s own
filing states "every apo-side score is identical within a pair." Checked
directly against `config/candidate_targets_task0243.yaml`: 5/7 pairs use
an IDENTICAL apo chain selection (bit-identical apo-side quantities);
2/7 (GAC_BPTES/GAC_CPD12, FBPASE_94D/FBPASE_95S) use a DIFFERENT chain
SUBSET of the same deposited apo entry (correlated, not bit-identical --
confirmed the underlying gnm_r values differ slightly, e.g. GAC_BPTES
0.697 vs GAC_CPD12 0.811). Does not change the clustering unit (same PDB
entry, overlapping chains, same crystallographic origin -- still clearly
non-independent) but is reported precisely rather than repeating the
filing's own slightly-overstated "identical" claim unchecked.

Reuses, does not re-derive, every underlying per-target statistic --
this script only changes how significance is computed, never recomputes
an AUC, Shapley value, or correlation input:
  - [[TASK-0249]]'s own `headline_per_residue.json` (composite vs. ctqw
    per-target AUC).
  - [[TASK-0254]]'s own `part_a_shapley_attribution.json` (Shapley shares
    + subset AUCs, degree-based H_new).
  - [[TASK-0257]]'s own `part_a_shapley_sasa.json` (same, SASA-based
    H_new) for the R2 paired comparison.
  - [[TASK-0259]]'s own `profile.json` (ENM validity join, apo-open
    fraction, unexplained share, and every correlate already measured).

Run: ../.venv/bin/python3 scripts/task0261_cluster_robust_stats.py
"""
from __future__ import annotations

import json
import sys
from itertools import combinations, product
from math import comb
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr, wilcoxon

_ROOT = Path(__file__).resolve().parent.parent
OUT = _ROOT / "results/tasks/0261_cluster_robust_stats"

# The 7 shared-apo pairs, from this task's own filing table, re-verified
# against `config/candidate_targets_task0243.yaml`'s own `apo_pdb` field
# (not re-typed from the table blind).
PAIRS = [
    ("GAC_BPTES", "GAC_CPD12"),
    ("KSHV_PROTEASE_24Q", "KSHV_PROTEASE_25G"),
    ("HCV_NS5B_VRX", "HCV_NS5B_VR1"),
    ("HCV_NS5B_POO", "HCV_NS5B_CMF"),
    ("FBPASE_94D", "FBPASE_95S"),
    ("TRP_SYNTHASE_F6F", "TRP_SYNTHASE_F19"),
    ("PKR_MITAPIVAT", "PKR_AG946"),
]
SINGLETONS = ["DHPS_GC7", "PF_ATCASE", "SUMO_E1_FHJ", "SMYD3_DIPERODON",
              "MKK7_IBRUTINIB", "NAMPT_NPA1R"]


def cluster_map() -> dict[str, str]:
    """target -> cluster id. 13 clusters (7 pairs + 6 singletons) over the
    20-row frozen set, matching this task's own filing exactly."""
    cm: dict[str, str] = {}
    for i, (a, b) in enumerate(PAIRS):
        cm[a] = cm[b] = f"pair{i}"
    for s in SINGLETONS:
        cm[s] = f"single_{s}"
    return cm


CM = cluster_map()
assert len(set(CM.values())) == 13, f"expected 13 clusters, got {len(set(CM.values()))}"
assert len(CM) == 20, f"expected 20 targets mapped, got {len(CM)}"


# ---------------------------------------------------------------------------
# Cluster-level exact sign-flip test (one-sample / paired: H0: median = 0)
# ---------------------------------------------------------------------------

def cluster_sign_flip_test(values: dict[str, float]) -> dict:
    """Exact test of H0: the values are symmetric about 0, respecting
    cluster structure -- generalises Wilcoxon's own exact enumeration
    (over 2^n row-level sign patterns) to 2^n_clusters CLUSTER-level sign
    patterns: every row in a cluster is flipped together, not
    independently. Statistic: sum of values (equivalent to n * mean;
    monotonic in the natural "how far from 0" summary, and the flip
    distribution is exactly symmetric under H0 regardless of which
    monotonic summary is used).
    """
    targets = [t for t in values if t in CM]
    clusters = sorted(set(CM[t] for t in targets))
    by_cluster: dict[str, list[float]] = {c: [] for c in clusters}
    for t in targets:
        by_cluster[CM[t]].append(values[t])

    obs = sum(values[t] for t in targets)
    n_clusters = len(clusters)
    null = []
    for signs in product([1, -1], repeat=n_clusters):
        s = 0.0
        for sign, c in zip(signs, clusters):
            s += sign * sum(by_cluster[c])
        null.append(s)
    null = np.asarray(null)
    p = float(np.mean(np.abs(null) >= abs(obs) - 1e-12))
    return dict(n_rows=len(targets), n_clusters=n_clusters, statistic=obs,
                p_value=p, median=float(np.median([values[t] for t in targets])))


# ---------------------------------------------------------------------------
# Cluster-block permutation: two-group (Mann-Whitney-style) comparison
# ---------------------------------------------------------------------------

def cluster_permutation_two_group(group_a: dict[str, float], group_b: dict[str, float],
                                   n_perm: int = 40000, seed: int = 0,
                                   alternative: str = "two-sided") -> dict:
    """H0: no location shift between the two groups, respecting cluster
    structure. Group membership here is itself cluster-consistent (every
    row of a given apo structure carries the same ENM verdict -- verified
    directly, not assumed, see module docstring), so this permutes whole
    CLUSTERS between the pooled group assignment, preserving each row's
    own value and each cluster's own row count. Statistic: difference of
    means (a - b); Monte Carlo since 2^13 cluster-to-group reassignments
    times the group-size constraint is not as cleanly enumerable as the
    sign-flip case, but 40000 draws gives Monte Carlo SE on p ~0.0025.

    `alternative`: 'two-sided' (default), 'greater' (H1: mean(a)>mean(b)),
    or 'less' -- pass the SAME alternative the classical test being
    compared against used, so a claimed "significance flip" is never an
    artifact of comparing a one-sided p to a two-sided one.

    **Exact when feasible**: the null space is "which n_a of the
    n_clusters_total clusters land in group a" -- C(n_total, n_a) distinct
    outcomes. When that is small (<=200000, true for every test in this
    task -- the largest is C(13,10)=286) every outcome is enumerated
    exactly, not Monte Carlo sampled; falls back to `n_perm` random draws
    only above that threshold.
    """
    clusters_a = sorted(set(CM[t] for t in group_a if t in CM))
    clusters_b = sorted(set(CM[t] for t in group_b if t in CM))
    assert not set(clusters_a) & set(clusters_b), "a cluster split across groups -- see module docstring"

    obs = float(np.mean(list(group_a.values())) - np.mean(list(group_b.values())))

    all_clusters = clusters_a + clusters_b
    n_a = len(clusters_a)
    n_total = len(all_clusters)
    rows_by_cluster = {}
    for t, v in {**group_a, **group_b}.items():
        rows_by_cluster.setdefault(CM[t], []).append(v)

    n_exact = comb(n_total, n_a)
    exact = n_exact <= 200000
    null = []
    if exact:
        for a_clusters in combinations(all_clusters, n_a):
            a_set = set(a_clusters)
            b_clusters = [c for c in all_clusters if c not in a_set]
            a_vals = [v for c in a_clusters for v in rows_by_cluster[c]]
            b_vals = [v for c in b_clusters for v in rows_by_cluster[c]]
            null.append(np.mean(a_vals) - np.mean(b_vals))
    else:
        rng = np.random.default_rng(seed)
        idx = np.arange(n_total)
        for _ in range(n_perm):
            rng.shuffle(idx)
            a_clusters = [all_clusters[i] for i in idx[:n_a]]
            b_clusters = [all_clusters[i] for i in idx[n_a:]]
            a_vals = [v for c in a_clusters for v in rows_by_cluster[c]]
            b_vals = [v for c in b_clusters for v in rows_by_cluster[c]]
            null.append(np.mean(a_vals) - np.mean(b_vals))
    null = np.asarray(null)
    if alternative == "two-sided":
        p = float(np.mean(np.abs(null) >= abs(obs) - 1e-12))
    elif alternative == "greater":
        p = float(np.mean(null >= obs - 1e-12))
    elif alternative == "less":
        p = float(np.mean(null <= obs + 1e-12))
    else:
        raise ValueError(alternative)
    return dict(n_clusters_a=len(clusters_a), n_clusters_b=len(clusters_b),
                n_rows_a=len(group_a), n_rows_b=len(group_b),
                statistic=obs, p_value=p, alternative=alternative,
                exact=exact, n_null_outcomes=len(null))


# ---------------------------------------------------------------------------
# Cluster-block permutation: Spearman correlation
# ---------------------------------------------------------------------------

def cluster_permutation_correlation(x: dict[str, float], y: dict[str, float],
                                     n_perm: int = 40000, seed: int = 0) -> dict:
    """H0: no association between x and y, respecting cluster structure.
    Permutes y's CLUSTER BLOCKS relative to x (whole clusters of y-rows
    move together to a randomly chosen x-cluster's row positions),
    preserving within-cluster (x, y) co-variation structure under the
    null reassignment rather than shuffling individual rows."""
    targets = sorted(set(x) & set(y) & set(CM))
    rng = np.random.default_rng(seed)
    clusters = sorted(set(CM[t] for t in targets))
    x_by_cluster = {c: [] for c in clusters}
    y_by_cluster = {c: [] for c in clusters}
    for t in targets:
        x_by_cluster[CM[t]].append(x[t])
        y_by_cluster[CM[t]].append(y[t])

    xs = [x[t] for t in targets]
    ys = [y[t] for t in targets]
    obs = float(spearmanr(xs, ys).statistic)

    null = []
    idx = np.arange(len(clusters))
    for _ in range(n_perm):
        rng.shuffle(idx)
        perm_y = []
        perm_x = []
        for orig_c, new_c in zip(clusters, [clusters[i] for i in idx]):
            perm_x.extend(x_by_cluster[orig_c])
            perm_y.extend(y_by_cluster[new_c])
        null.append(spearmanr(perm_x, perm_y).statistic)
    null = np.asarray(null)
    p = float(np.mean(np.abs(null) >= abs(obs) - 1e-12))
    return dict(n_rows=len(targets), n_clusters=len(clusters), rho=obs, p_value=p)


def load(path: str) -> dict:
    return json.loads((_ROOT / path).read_text())


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    out: dict = {}

    print("=" * 100)
    print(f"Cluster map: {len(CM)} rows -> {len(set(CM.values()))} clusters "
          f"({len(PAIRS)} pairs + {len(SINGLETONS)} singletons)")
    print("=" * 100)

    # --- TASK-0249: composite vs ctqw, paired --------------------------
    d249 = load("results/tasks/0249_composite_dumb_baseline/headline_per_residue.json")
    comp, ctqw = d249["composite"], d249["ctqw"]
    diffs = {t: comp[t] - ctqw[t] for t in comp if t in ctqw}
    w20 = wilcoxon(list(diffs.values()))
    r261 = cluster_sign_flip_test(diffs)
    print(f"\n[TASK-0249] composite - ctqw (paired, per-target AUC)")
    print(f"  n=20 rows, plain Wilcoxon:        p={w20.pvalue:.4f}")
    print(f"  n=13 clusters, cluster sign-flip: p={r261['p_value']:.4f}  (median diff {r261['median']:+.4f})")
    out["task0249_composite_vs_ctqw"] = dict(n20_p=float(w20.pvalue), cluster=r261)

    # --- TASK-0254: Shapley shares + added-last per block ---------------
    d254 = load("results/tasks/0254_fpocket_variance_and_crypticity/part_a_shapley_attribution.json")

    def added_last(subset_aucs: dict, block: str) -> float:
        full = subset_aucs["ctqw,fpocket,geometry"]
        without = {"ctqw": "fpocket,geometry", "fpocket": "ctqw,geometry", "geometry": "ctqw,fpocket"}[block]
        return (full - subset_aucs[without]) / 0.5

    print(f"\n[TASK-0254] Shapley shares & added-last, per block")
    for block in ("geometry", "fpocket", "ctqw"):
        shap = {t: d254[t]["shapley"][block] for t in d254}
        al = {t: added_last(d254[t]["subset_aucs"], block) for t in d254}
        w_shap = wilcoxon(list(shap.values()))
        w_al = wilcoxon(list(al.values()))
        c_shap = cluster_sign_flip_test(shap)
        c_al = cluster_sign_flip_test(al)
        print(f"  {block:<10} Shapley:    n=20 p={w_shap.pvalue:.4f}  ->  n=13 cluster p={c_shap['p_value']:.4f}")
        print(f"  {block:<10} added-last: n=20 p={w_al.pvalue:.4f}  ->  n=13 cluster p={c_al['p_value']:.4f}")
        out[f"task0254_{block}_shapley"] = dict(n20_p=float(w_shap.pvalue), cluster=c_shap)
        out[f"task0254_{block}_added_last"] = dict(n20_p=float(w_al.pvalue), cluster=c_al)

    # --- TASK-0257 R2: SASA vs degree added-last, paired ----------------
    d257 = load("results/tasks/0257_r2_shapley_rerun/part_a_shapley_sasa.json")
    al_base = {t: added_last(d254[t]["subset_aucs"], "ctqw") for t in d254 if t in d257}
    al_sasa = {t: added_last(d257[t]["subset_aucs"], "ctqw") for t in d257 if t in d254}
    diffs257 = {t: al_sasa[t] - al_base[t] for t in al_sasa}
    w257 = wilcoxon(list(diffs257.values()))
    c257 = cluster_sign_flip_test(diffs257)
    print(f"\n[TASK-0257] R2 paired: SASA-based added-last - degree-based added-last")
    print(f"  n=20 rows, plain Wilcoxon:        p={w257.pvalue:.4f}")
    print(f"  n=13 clusters, cluster sign-flip: p={c257['p_value']:.4f}  (median diff {c257['median']:+.4f})")
    out["task0257_r2_sasa_vs_degree"] = dict(n20_p=float(w257.pvalue), cluster=c257)

    # --- TASK-0259: subgroup tests --------------------------------------
    rows259 = load("results/tasks/0259_ctqw_devils_advocate/profile.json")
    by_t = {r["target"]: r for r in rows259 if r.get("gnm_r") is not None}

    print(f"\n[TASK-0259A] ENM valid vs invalid, CTQW added-last (Mann-Whitney)")
    valid = {t: r["ctqw_added_last"] for t, r in by_t.items() if r["enm_verdict"] in ("PASS", "MARGINAL")}
    invalid = {t: r["ctqw_added_last"] for t, r in by_t.items() if r["enm_verdict"] == "FAIL"}
    from scipy.stats import mannwhitneyu
    # Pre-registered direction (the brief's own hypothesis, TASK-0259's own
    # test): H1 = valid > invalid. Reported first, matching the original
    # exactly (same alternative on both sides) so a "significance flip"
    # claim is never an artifact of comparing a one-sided p to a two-sided
    # one. Two-sided is also reported underneath for the full picture.
    mw_greater = mannwhitneyu(list(valid.values()), list(invalid.values()), alternative="greater")
    mw_two = mannwhitneyu(list(valid.values()), list(invalid.values()), alternative="two-sided")
    cmw_greater = cluster_permutation_two_group(valid, invalid, alternative="greater")
    cmw_two = cluster_permutation_two_group(valid, invalid, alternative="two-sided")
    print(f"  n=20 rows ({len(valid)} valid / {len(invalid)} invalid)")
    print(f"    pre-registered (valid > invalid): Mann-Whitney p={mw_greater.pvalue:.4f}  "
          f"->  cluster-block permutation p={cmw_greater['p_value']:.4f}  "
          f"({cmw_greater['n_clusters_a']} vs {cmw_greater['n_clusters_b']} clusters)")
    print(f"    two-sided (either direction):     Mann-Whitney p={mw_two.pvalue:.4f}  "
          f"->  cluster-block permutation p={cmw_two['p_value']:.4f}")
    print(f"    NOTE: the data run the OPPOSITE way from the pre-registered direction "
          f"(mean(invalid)-mean(valid)={-cmw_greater['statistic']:+.4f}) -- both the row-level and "
          f"cluster-level pre-registered test correctly report non-significance for 'valid>invalid' "
          f"because that is not the direction the data show, not because the effect is absent; "
          f"the two-sided/reverse-direction numbers are where the real (and, under clustering, "
          f"only borderline) signal is.")
    out["task0259_enm_valid_vs_invalid_preregistered"] = dict(n20_p=float(mw_greater.pvalue), cluster=cmw_greater)
    out["task0259_enm_valid_vs_invalid_twosided"] = dict(n20_p=float(mw_two.pvalue), cluster=cmw_two)

    print(f"\n[TASK-0259A] Spearman(ENM validity r, CTQW added-last)")
    gr = {t: r["gnm_r"] for t, r in by_t.items()}
    al = {t: r["ctqw_added_last"] for t, r in by_t.items()}
    s20 = spearmanr(list(gr.values()), list(al.values()))
    c20 = cluster_permutation_correlation(gr, al)
    print(f"  n=20 rows: rho={s20.statistic:+.3f} p={s20.pvalue:.4f}")
    print(f"  n=13 clusters, cluster-block permutation: rho={c20['rho']:+.3f} p={c20['p_value']:.4f}")
    out["task0259_spearman_enm_ctqw"] = dict(n20_rho=float(s20.statistic), n20_p=float(s20.pvalue), cluster=c20)

    print(f"\n[TASK-0259A] CTQW added-last on ENM-valid targets alone, vs 0")
    w_valid = wilcoxon(list(valid.values()))
    c_valid = cluster_sign_flip_test(valid)
    print(f"  n={len(valid)} rows, Wilcoxon vs 0: p={w_valid.pvalue:.4f}")
    print(f"  n={c_valid['n_clusters']} clusters, cluster sign-flip: p={c_valid['p_value']:.4f}")
    out["task0259_ctqw_added_last_enm_valid_only"] = dict(n20_p=float(w_valid.pvalue), cluster=c_valid)

    print(f"\n[TASK-0259B] Spearman(apo crypticity, unexplained share)")
    ao = {t: r["apo_open_frac"] for t, r in by_t.items() if r.get("apo_open_frac") is not None}
    unex = {t: r["unexplained"] for t, r in by_t.items() if t in ao}
    s_c = spearmanr([ao[t] for t in ao], [unex[t] for t in ao])
    c_c = cluster_permutation_correlation(ao, unex)
    print(f"  n=20 rows: rho={s_c.statistic:+.3f} p={s_c.pvalue:.4f}")
    print(f"  n=13 clusters, cluster-block permutation: rho={c_c['rho']:+.3f} p={c_c['p_value']:.4f}")
    out["task0259_spearman_crypticity_unexplained"] = dict(n20_rho=float(s_c.statistic), n20_p=float(s_c.pvalue), cluster=c_c)

    (OUT / "cluster_robust_results.json").write_text(json.dumps(out, indent=1))
    print(f"\nwritten: {OUT / 'cluster_robust_results.json'}")

    print("\n" + "=" * 100)
    print("SUMMARY -- old (n=20 or subgroup) vs cluster-robust (n=13 clusters)")
    print("=" * 100)
    for k, v in out.items():
        cp = v["cluster"]["p_value"] if "cluster" in v else v.get("cluster", {}).get("p_value")
        old_p = v.get("n20_p")
        flag = ""
        old_sig, new_sig = old_p < 0.05, cp < 0.05
        if old_sig != new_sig:
            flag = "  *** SIGNIFICANCE FLIPS ***"
        print(f"  {k:<45} n=20 p={old_p:.4f}  ->  cluster p={cp:.4f}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
