"""TASK-0311 -- on a continuum, predict the distance. Stop building
classifiers.

[[TASK-0309]] settled it on 171 proteins: there are no discrete near/far
populations (Silverman critical-bandwidth p=0.81/0.14/0.11 across the
three cohorts; k-means best-k wanders 3/4/2/5). Every discriminator
attempt in this register up to now ([[TASK-0300]] stratified rules,
[[TASK-0306]] meta-classifier, [[TASK-0288]] near/far probes) assumed
classes the data does not support. On a continuum the well-posed problem
is regression, never tried here before.

Response: `min_heavy_A` (log scale) and the scale-free `min_A / Rg`, one
row per protein, on [[TASK-0309]]'s own pooled 171-protein cohort
(results/tasks/0309_kmeans_extended_cohort/kmeans_extended_cohort.json).

Predictors -- all already computed elsewhere, none invented here (this
task's own Constraint: "No new descriptors"):
  - N, Rg, compactness (= Rg / N^(1/3)). "ours" reuses [[TASK-0284]]'s own
    `t0242.prep`-scoped N/Rg (results/tasks/0284_two_populations/
    bimodality_and_nulls.json) -- restricted to each target's configured
    functional chain(s). ASBench/CASBench reuse [[TASK-0306]]'s own
    `structure_descriptors()` -- the WHOLE deposited asymmetric unit, all
    chains (verified live: annotation chain letters for citrate synthase
    (1NXE) include symmetry-generated copies ('C','F') absent from the
    raw ASU file -- restricting to annotation chains would silently
    undercount for exactly the multimeric cases where site geometry
    matters most, so that path was abandoned in favour of each cohort's
    own already-established, already-validated convention). This is a
    real, disclosed cross-cohort scoping mismatch, not introduced here --
    inherited from how each quantity was already computed upstream. Both
    N and Rg use the SAME scoping convention within a given cohort, so
    `compactness` is more robust to it than N or Rg alone; per-cohort
    held-out performance is reported alongside the pooled fit for exactly
    this reason (Sec. "Per-cohort robustness check" below).
  - n_chains: `structure_descriptors()`, uniform across all three cohorts
    ([[TASK-0306]]'s own definition, reused verbatim -- no scoping issue,
    since it counts distinct chain IDs in the deposited file regardless
    of which chain a site sits on).
  - site_size: the anchor/active-site residue count each cohort already
    annotates -- "ours" `n_seed` ([[TASK-0284]]), ASBench
    `n_act_resolved` ([[TASK-0304]]), CASBench `n_cat` (median per
    `cas_id` across its own resolved structures, [[TASK-0304]]).
  - fold_class: ASBench-only sub-analysis (111/113 structures,
    [[TASK-0306]] addendum's own live CATH pull,
    results/tasks/0306_six_measure_meta_classifier/
    fold_class_annotations.json) -- Alpha-Beta vs Mainly-Alpha, the only
    two classes numerous enough to use, exactly as that addendum
    established.
  - landscape (fpocket-derived, 13 features): "ours"-only sub-analysis,
    reusing [[TASK-0288]]'s own already-computed values
    (results/tasks/0288_contact_spike/contact_spike.json, 26/28
    structures with a landscape join) -- univariate per-feature LOPO, not
    one multivariate fit, since 13 predictors over ~24 protein clusters
    is exactly the "free parameters on 13 clusters" failure mode
    [[TASK-0301]] named.

Two-part model, per this task's own Scope: a linear-probability-model +
AUC for "is it at the covalent floor" (min_A < 1.5 Angstrom, [[TASK-0309]]
's own threshold) -- this register's own established way to score a
binary LOPO target with plain OLS + `roc_auc_score` ([[TASK-0306]]'s own
`meta_classifier`, reused verbatim, not upgraded to a true logistic
model), plus OLS regression of log(min_A) on the non-floor remainder.
LOPO throughout -- leave-one-PROTEIN-out; every cohort table here is
already one row per protein (or per `cas_id`), so this is leave-one-out
at exactly that granularity, no further grouping needed. Metric:
out-of-sample Spearman + MAE against a permuted-target null (this task's
own Metric bullet -- not R^2 alone).

Run: ../.venv/bin/python3 scripts/task0311_regression_not_classification.py
"""
import sys, os, json, warnings, re
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
from pathlib import Path
from collections import defaultdict

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")

sys.path.insert(0, "..")
from backend.data_layer import fetch  # noqa: E402 -- this register's own cached PDB fetch

ROOT = Path(".")
R0304 = ROOT / "results/tasks/0304_asbench_casbench"
R0309 = ROOT / "results/tasks/0309_kmeans_extended_cohort"
R0288 = ROOT / "results/tasks/0288_contact_spike"
R0306 = ROOT / "results/tasks/0306_six_measure_meta_classifier"
R0284 = ROOT / "results/tasks/0284_two_populations"
OUT = ROOT / "results/tasks/0311_regression_not_classification"

FLOOR_A = 1.5  # [[TASK-0309]]'s own covalent-limit threshold
N_PERM_MAIN = 500
N_PERM_SMALL = 1000  # smaller cohorts -- cheap, more permutations for resolution
SEED = 0


# ------------------------------------------------------------ descriptors
def structure_descriptors(pdb_id):
    """N (resolved CA count, ALL chains) and chain count, from the
    deposited PDB file -- [[TASK-0306]]'s own `structure_descriptors`,
    duplicated verbatim (this register's own precedent: reuse the DESIGN,
    not a cross-script import, per the standing lane-collision
    convention)."""
    fp = fetch(pdb_id)
    if fp is None:
        return None
    chains = {}
    for line in Path(fp).read_text().splitlines():
        if not line.startswith("ATOM"):
            continue
        if line[12:16].strip() != "CA":
            continue
        ch = line[21]
        try:
            resnum = int(line[22:26])
        except ValueError:
            continue
        chains.setdefault(ch, set()).add(resnum)
    if not chains:
        return None
    return {"N": sum(len(v) for v in chains.values()), "n_chains": len(chains)}


# ------------------------------------------------------------- cohort load
def load_ours():
    bim = json.load(open(R0284 / "bimodality_and_nulls.json"))
    by_target = {r["target"]: r for r in bim["rows"]}
    k = json.load(open(R0309 / "kmeans_extended_cohort.json"))
    out, skipped = [], []
    for c in k["ours"]:
        apo = c["protein"]
        targets = c["targets"]
        rows = [by_target[t] for t in targets]
        Ns = [r["N"] for r in rows]
        seeds = [r["n_seed"] for r in rows if r.get("n_seed") is not None]
        desc = structure_descriptors(apo)
        if desc is None or not seeds:
            skipped.append(apo)
            continue
        out.append(dict(cohort="ours", protein=apo,
                         min_A=c["min_A"], Rg=c["Rg"],
                         N=float(np.median(Ns)), site_size=float(np.median(seeds)),
                         n_chains=float(desc["n_chains"])))
    return out, skipped


def load_asbench():
    k = json.load(open(R0309 / "kmeans_extended_cohort.json"))
    ff = json.load(open(R0304 / "asbench_finding_f.json"))
    by_code = defaultdict(list)
    for r in ff["rows"]:
        by_code[r["pdb"].split("_")[0]].append(r)
    out, skipped = [], []
    for c in k["asbench"]:
        code = c["protein"]
        members = by_code.get(code, [])
        if not members:
            skipped.append(code)
            continue
        desc = structure_descriptors(code)
        if desc is None:
            skipped.append(code)
            continue
        site = [m["n_act_resolved"] for m in members]
        out.append(dict(cohort="asbench", protein=code,
                         min_A=c["min_A"], Rg=c["Rg"],
                         N=float(desc["N"]), site_size=float(np.median(site)),
                         n_chains=float(desc["n_chains"]),
                         _pdbs=[m["pdb"] for m in members]))
    return out, skipped


def load_casbench():
    k = json.load(open(R0309 / "kmeans_extended_cohort.json"))
    ann = json.load(open(R0304 / "casbench_annotations.json"))
    by_cas_ncat = defaultdict(list)
    by_cas_pdb = defaultdict(set)
    for r in ann["records"]:
        by_cas_ncat[r["cas_id"]].append(r["n_cat"])
        by_cas_pdb[r["cas_id"]].add(r["pdb"])
    out, skipped = [], []
    for c in k["casbench"]:
        cas = c["protein"]
        pdbs = sorted(by_cas_pdb.get(cas, []))
        rep = None
        desc = None
        for p in pdbs:
            desc = structure_descriptors(p)
            if desc is not None:
                rep = p
                break
        ncat = by_cas_ncat.get(cas, [])
        if desc is None or not ncat:
            skipped.append(cas)
            continue
        out.append(dict(cohort="casbench", protein=cas,
                         min_A=c["min_A"], Rg=c["Rg"],
                         N=float(desc["N"]), site_size=float(np.median(ncat)),
                         n_chains=float(desc["n_chains"]), _rep_pdb=rep))
    return out, skipped


# ------------------------------------------------------------------- LOPO
def lopo_predict(X, y, groups):
    """Leave-one-PROTEIN-out OLS -- this register's own established
    convention ([[TASK-0249]]/[[TASK-0282]]'s own `_fit_ols`,
    [[TASK-0306]]'s own `lopo_predict`, duplicated verbatim). Also used
    for the binary floor indicator (linear-probability-model + AUC,
    [[TASK-0306]]'s own precedent for a LOPO binary target -- not a true
    logistic fit). Returns out-of-fold predictions, NaN where the fold
    could not be fit."""
    groups = np.asarray(groups)
    preds = np.full(len(y), np.nan)
    for g in sorted(set(groups)):
        train = groups != g
        test = groups == g
        if train.sum() < max(4, X.shape[1] + 2):
            continue
        Xb = np.column_stack([X[train], np.ones(train.sum())])
        b, *_ = np.linalg.lstsq(Xb, y[train].astype(float), rcond=None)
        Xt = np.column_stack([X[test], np.ones(test.sum())])
        preds[test] = Xt @ b
    return preds


def zscore(x):
    x = np.asarray(x, float)
    s = x.std()
    return (x - x.mean()) / s if s > 0 else x - x.mean()


def continuum_fit(X, y, groups, n_perm, rng):
    """OOS Spearman + MAE via LOPO, plus a permuted-target null (shuffle y
    across proteins, refit the full LOPO pipeline, recompute the same
    metric against the shuffled target -- tests whether X carries any
    real information about y at all, not whether this particular fit
    overfit)."""
    pred = lopo_predict(X, y, groups)
    v = ~np.isnan(pred)
    obs_rho = float(spearmanr(pred[v], y[v]).statistic)
    obs_mae = float(np.mean(np.abs(pred[v] - y[v])))
    null_rho = []
    for _ in range(n_perm):
        yp = rng.permutation(y)
        predp = lopo_predict(X, yp, groups)
        vp = ~np.isnan(predp)
        r = spearmanr(predp[vp], yp[vp]).statistic
        null_rho.append(0.0 if np.isnan(r) else r)
    null_rho = np.array(null_rho)
    p = _perm_p(obs_rho, null_rho, n_perm)
    return dict(n=int(v.sum()), obs_rho=obs_rho, obs_mae=obs_mae, p_perm=p,
                null_rho_mean=float(null_rho.mean()), null_rho_sd=float(null_rho.std()))


def _perm_p(obs, null, n_perm):
    """Two-sided permutation p-value against the EMPIRICAL null
    distribution (not symmetric-around-zero) -- LOO regression's own null
    is not symmetric about 0 (confirmed empirically, null_rho_mean runs
    as low as -0.5 on several small-n arms below), and no per-feature
    direction is pre-registered for the univariate landscape scan
    (Part 5), so a fixed-sign one-sided test would be wrong there."""
    upper = (np.sum(null >= obs) + 1) / (n_perm + 1)
    lower = (np.sum(null <= obs) + 1) / (n_perm + 1)
    return float(min(1.0, 2 * min(upper, lower)))


def floor_fit(X, y, groups, n_perm, rng):
    """Same LOPO machinery, binary target, AUC instead of Spearman."""
    pred = lopo_predict(X, y, groups)
    v = ~np.isnan(pred)
    if y[v].sum() < 3 or y[v].sum() > v.sum() - 3:
        return dict(skipped="too few positives/negatives", n_pos=int(y[v].sum()), n=int(v.sum()))
    obs_auc = float(roc_auc_score(y[v], pred[v]))
    null_auc = []
    for _ in range(n_perm):
        yp = rng.permutation(y)
        predp = lopo_predict(X, yp, groups)
        vp = ~np.isnan(predp)
        if yp[vp].sum() < 3 or yp[vp].sum() > vp.sum() - 3:
            continue
        null_auc.append(roc_auc_score(yp[vp], predp[vp]))
    null_auc = np.array(null_auc)
    p = _perm_p(obs_auc, null_auc, len(null_auc))
    return dict(n=int(v.sum()), n_pos=int(y[v].sum()), obs_auc=obs_auc, p_perm=p,
                n_null=int(len(null_auc)))


# --------------------------------------------------------------------- main
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    print("Loading cohorts (cached PDBs only, no network expected)...")
    ours, sk_o = load_ours()
    asb, sk_a = load_asbench()
    cas, sk_c = load_casbench()
    print(f"  ours: {len(ours)} (skipped {len(sk_o)}: {sk_o})")
    print(f"  asbench: {len(asb)} (skipped {len(sk_a)}: {sk_a})")
    print(f"  casbench: {len(cas)} (skipped {len(sk_c)}: {sk_c})")

    pooled = ours + asb + cas
    for r in pooled:
        r["log_min_A"] = float(np.log(r["min_A"])) if r["min_A"] > 0 else None
        r["compactness"] = r["Rg"] / (r["N"] ** (1.0 / 3.0))
        r["min_A_over_Rg"] = r["min_A"] / r["Rg"]
        r["at_floor"] = 1.0 if r["min_A"] < FLOOR_A else 0.0

    n_floor = sum(r["at_floor"] for r in pooled)
    # [[TASK-0309]]'s own literal-overlap finding: min_A == 0.0 exactly for
    # 15/171 (12 ASBench, 3 CASBench, 0 ours) -- undefined on the log
    # scale every parametric test below uses. Excluded from THOSE tests
    # only (never epsilon-padded), same convention TASK-0309 established;
    # they ARE included in the floor logistic (Part 1a), which needs no
    # log and for which literal overlap is trivially "at the floor".
    n_zero = sum(1 for r in pooled if r["min_A"] <= 0)
    print(f"\nPooled n={len(pooled)}, at floor (<{FLOOR_A}A): {int(n_floor)} "
          f"({100*n_floor/len(pooled):.1f}%); literal site overlap (min_A=0, "
          f"excluded from log-scale tests): {n_zero}")

    results = {"n_pooled": len(pooled), "n_floor": int(n_floor), "n_zero_overlap": n_zero,
               "skipped": {"ours": sk_o, "asbench": sk_a, "casbench": sk_c}}

    # ---------------------------------------------------- Part 1: pooled
    proteins = np.array([r["protein"] for r in pooled])
    N = zscore([r["N"] for r in pooled])
    Rg = zscore([r["Rg"] for r in pooled])
    comp = zscore([r["compactness"] for r in pooled])
    nch = zscore([r["n_chains"] for r in pooled])
    site = zscore([r["site_size"] for r in pooled])
    y_floor = np.array([r["at_floor"] for r in pooled])
    valid_log = np.array([r["min_A"] > 0 for r in pooled])

    X_full = np.column_stack([N, Rg, comp, nch, site])
    print("\nPart 1a -- floor logistic (linear-probability + AUC), pooled, N/Rg/compactness/n_chains/site_size...")
    floor_res = floor_fit(X_full, y_floor, list(proteins), N_PERM_MAIN, rng)
    print(" ", floor_res)
    results["floor_pooled"] = floor_res

    y_log_valid = np.array([r["log_min_A"] for r in pooled if r["log_min_A"] is not None])
    X_log = X_full[valid_log]
    proteins_log = proteins[valid_log]
    floor_log = y_floor[valid_log]

    print("\nPart 1b -- continuum regression, log(min_A), pooled, non-floor subset (log-defined only)...")
    nf_log = floor_log == 0
    cont_res = continuum_fit(X_log[nf_log], y_log_valid[nf_log], list(proteins_log[nf_log]), N_PERM_MAIN, rng)
    print(" ", cont_res)
    results["continuum_pooled_nonfloor"] = cont_res

    print("\nPart 1c -- continuum regression, log(min_A), pooled, ALL log-defined rows (no floor split)...")
    cont_all = continuum_fit(X_log, y_log_valid, list(proteins_log), N_PERM_MAIN, rng)
    print(" ", cont_all)
    results["continuum_pooled_all"] = cont_all

    # ------------------------------------------------- Part 2: scale-free
    print("\nPart 2 -- scale-free target min_A/Rg, predictors N/compactness/n_chains/site_size (Rg dropped, avoids denominator circularity)...")
    y_ratio = np.array([r["min_A_over_Rg"] for r in pooled])
    X_sf = np.column_stack([N, comp, nch, site])
    ratio_res = continuum_fit(X_sf, y_ratio, list(proteins), N_PERM_MAIN, rng)
    print(" ", ratio_res)
    results["scale_free_pooled_all"] = ratio_res
    nf_full = y_floor == 0  # ratio is finite even at min_A=0, only the log-scale tests need valid_log
    ratio_nf = continuum_fit(X_sf[nf_full], y_ratio[nf_full], list(proteins[nf_full]), N_PERM_MAIN, rng)
    print(" ", ratio_nf)
    results["scale_free_pooled_nonfloor"] = ratio_nf

    # -------------------------------------- Part 3: per-cohort robustness
    print("\nPart 3 -- per-cohort-only continuum regression (robustness check against the N/Rg scoping mismatch)...")
    percohort = {}
    for name, rows0 in (("ours", ours), ("asbench", asb), ("casbench", cas)):
        rows = [r for r in rows0 if r["min_A"] > 0]  # log-defined only, TASK-0309's own convention
        n_excl = len(rows0) - len(rows)
        if len(rows) < 15:
            percohort[name] = {"skipped": "too few rows for a stable LOPO", "n_zero_excluded": n_excl}
            continue
        Nn = zscore([r["N"] for r in rows])
        Rgn = zscore([r["Rg"] for r in rows])
        compn = zscore([r["Rg"] / (r["N"] ** (1/3)) for r in rows])
        nchn = zscore([r["n_chains"] for r in rows])
        siten = zscore([r["site_size"] for r in rows])
        Xn = np.column_stack([Nn, Rgn, compn, nchn, siten])
        yn = np.array([np.log(r["min_A"]) for r in rows])
        pr = [r["protein"] for r in rows]
        res = continuum_fit(Xn, yn, pr, N_PERM_SMALL, rng)
        res["n_zero_excluded"] = n_excl
        print(f"  {name}: {res}")
        percohort[name] = res
    results["per_cohort_continuum"] = percohort

    # ------------------------------------------------- Part 4: fold class
    print("\nPart 4 -- ASBench-only, fold class added (Alpha-Beta vs Mainly-Alpha, [[TASK-0306]] addendum)...")
    fold = json.load(open(R0306 / "fold_class_annotations.json"))
    asb_by_code = {r["protein"]: r for r in asb}
    fold_rows = []
    for code, r in asb_by_code.items():
        fc = None
        for pdb, entry in fold.items():
            if pdb.split("_")[0] == code:
                fc = entry
                break
        if fc is None:
            continue
        cls = fc[2] if len(fc) > 2 else None
        if cls not in ("Alpha Beta", "Mainly Alpha"):
            continue
        fold_rows.append(dict(r, fold_class=cls))
    n_fc_zero = sum(1 for r in fold_rows if r["min_A"] <= 0)
    fold_rows = [r for r in fold_rows if r["min_A"] > 0]  # log-defined only
    print(f"  joined: {len(fold_rows)}/{len(asb_by_code)} ASBench proteins with a usable fold class "
          f"({n_fc_zero} literal-overlap excluded)")
    if len(fold_rows) >= 20:
        Nn = zscore([r["N"] for r in fold_rows])
        Rgn = zscore([r["Rg"] for r in fold_rows])
        compn = zscore([r["Rg"] / (r["N"] ** (1/3)) for r in fold_rows])
        nchn = zscore([r["n_chains"] for r in fold_rows])
        siten = zscore([r["site_size"] for r in fold_rows])
        fcbin = np.array([1.0 if r["fold_class"] == "Mainly Alpha" else 0.0 for r in fold_rows])
        yn = np.array([np.log(r["min_A"]) for r in fold_rows])
        pr = [r["protein"] for r in fold_rows]
        base = continuum_fit(np.column_stack([Nn, Rgn, compn, nchn, siten]), yn, pr, N_PERM_SMALL, rng)
        withfc = continuum_fit(np.column_stack([Nn, Rgn, compn, nchn, siten, fcbin]), yn, pr, N_PERM_SMALL, rng)
        print("  without fold class:", base)
        print("  with fold class   :", withfc)
        results["fold_class"] = {"n_joined": len(fold_rows), "without": base, "with": withfc}
    else:
        results["fold_class"] = {"skipped": "too few joined rows"}

    # ---------------------------------------------- Part 5: landscape ("ours")
    print("\nPart 5 -- 'ours'-only landscape features ([[TASK-0288]]'s own 13, univariate LOPO)...")
    land = json.load(open(R0288 / "contact_spike.json"))
    land_rows = land["rows"]
    # cluster landscape rows by apo_pdb the same way [[TASK-0309]]'s load_ours() does
    k = json.load(open(R0309 / "kmeans_extended_cohort.json"))
    target_to_apo = {t: c["protein"] for c in k["ours"] for t in c["targets"]}
    LAND_FEATS = ["n_cand", "d_best_drug", "d_best_drug_top3", "d_biggest", "max_drug_near",
                  "max_drug_far", "drug_gap_far_minus_near", "frac_cand_far", "n_cand_far",
                  "median_d", "max_d", "drug_wtd_d", "size_wtd_d", "max_drug_all"]
    by_apo = defaultdict(list)
    for r in land_rows:
        apo = target_to_apo.get(r["target"])
        if apo is None:
            continue
        by_apo[apo].append(r)
    land_clustered = []
    for apo, members in by_apo.items():
        row = {"protein": apo, "min_A": float(np.median([m["min_A"] for m in members]))}
        for f in LAND_FEATS:
            vals = [m[f] for m in members if f in m and m[f] is not None]
            row[f] = float(np.median(vals)) if vals else None
        land_clustered.append(row)
    print(f"  {len(land_clustered)} protein clusters with a landscape join (of 26 in the 'ours' cohort)")
    land_res = {}
    if len(land_clustered) >= 10:
        yn = np.array([np.log(r["min_A"]) for r in land_clustered])
        pr = [r["protein"] for r in land_clustered]
        for f in LAND_FEATS:
            vals = np.array([r[f] for r in land_clustered])
            if any(v is None for v in vals) or np.std(vals) == 0:
                land_res[f] = {"skipped": "missing or constant"}
                continue
            Xf = zscore(vals).reshape(-1, 1)
            res = continuum_fit(Xf, yn, pr, N_PERM_SMALL, rng)
            land_res[f] = res
        print("  per-feature results:")
        for f, r in land_res.items():
            print(f"    {f}: {r}")
    results["landscape_ours"] = {"n_clustered": len(land_clustered), "per_feature": land_res}

    with open(OUT / "regression_not_classification.json", "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nWrote {OUT / 'regression_not_classification.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
