"""TASK-0348 -- the mandatory centrality ablation.

Mohtashim, Sajjan & Kais, "Continuous-Time Quantum-Walk Centrality for
Protein Residue Interaction Networks", J. Am. Chem. Soc. 148(27):29206-29219
(2026), DOI 10.1021/jacs.6c08053 -- CTQW on a weighted residue contact
network, essentially our own construction -- report their quantum
centrality agrees with classical EIGENVECTOR centrality at Spearman rho
median ~0.95, Kendall tau ~0.87, Overlap@10 0.90-1.00, and claim no quantum
advantage. This project has never run that comparison: `baselines.py` had
degree and betweenness, but no eigenvector or closeness centrality, and no
script has ever put CTQW next to all four plus GNM-alone on one cohort.

COHORT, per this task's own Constraint ("use the existing cohort and
labels; do not construct a new one"): TASK-0318's own ASBench cohort and
per-residue truth labels, reused directly via `build_structures()` -- same
105 structures, same `elig` (non-seed, non-terminal-5%) residue population,
same y. Re-derived (not re-typed) from `task0318_input_space_ceiling.py`'s
own module-level code, imported directly.

SCORES compared, all on the SAME contact graph (Calpha < 8.0 A, this
project's standing cutoff):
  - CTQW: `time_averaged_ctqw_converged` on `build_H_new` (identical to
    every other task in this register) -- via `compute_features_one`'s
    own `ctqw` column, not re-derived.
  - degree, GNM-alone (`gnm_context`'s `msf` -- the classical Bahar-GNM
    flexibility predictor, a genuinely different "GNM alone" object from
    this project's own H_new potential terms) -- also pulled straight from
    `compute_features_one`'s existing columns.
  - betweenness (existing in `baselines.py`), eigenvector + closeness (NEW
    this task, added to `baselines.py` beside the existing two, same
    module/conventions -- not a parallel implementation).

Planned Validation, run first: re-derive `degree`/`gnm_msf`/`ctqw` for
every structure via this script's own graph-construction path and confirm
byte-exact match against `compute_features_one`'s own committed
`feature_cache/*.npz` columns, BEFORE trusting the three new centralities
computed on that same graph.

Two things reported, matching the JACS paper's own two questions:
  1. Spearman rank correlation between CTQW and each classical baseline,
     per structure -- the JACS-comparable number (their own is a single
     aggregate over ~150 proteins; this reports the same summary, median
     + IQR, over 105).
  2. AUC of every arm (including CTQW) against the SAME truth labels --
     answers "does CTQW's own high correlation with eigenvector centrality
     translate into a detection advantage", which correlation alone
     cannot.
Cluster-robust throughout ([[TASK-0337]]): protein is the resampling unit
(the same field TASK-0318's own LOPO fold already uses), cluster-permutation
p-values and cluster-bootstrap 95% CIs, not raw per-structure p-values.

PROGRESS/CHECKPOINTING (added after the first run of this script sat silent
for 2+ hours with no way to tell working-slowly from hung -- see the
project-wide requirement this cost added, `.ai/COMMON.md`'s "Long-running
scripts" rule under Current Rules, and don't repeat this on the next one):
  - stdout is put into line-buffering mode explicitly (`sys.stdout.
    reconfigure`) so `print()` is visible immediately even when redirected
    to a file, regardless of how the caller invokes this script.
  - Validation and scoring are ONE pass per structure now, not two separate
    full-cohort passes (the original design called `compute_features_one` --
    which computes all 19 features, including the expensive persistent-
    homology/entanglement/transport ones this task doesn't even use --
    twice per structure: once to validate, once to score. Fixed to call it
    once and reuse the result for both).
  - Every structure prints one progress line with elapsed/ETA the moment
    it finishes, and its full result is appended to a checkpoint JSONL file
    immediately (not held in memory until the end) -- a kill/crash loses at
    most one in-flight structure, and a rerun resumes from the checkpoint
    instead of starting over.

Run: ../.venv/bin/python3 -u scripts/task0348_centrality_ablation.py
     (the `-u` is redundant with the stdout.reconfigure() below, kept in
     the invocation as the standard belt-and-suspenders for any redirected
     long-running script -- see the COMMON.md rule)
"""
from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

sys.stdout.reconfigure(line_buffering=True)

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from allostery.baselines import (  # noqa: E402
    betweenness_centrality, closeness_centrality, eigenvector_centrality,
)
from task0318_input_space_ceiling import (  # noqa: E402
    build_structures, compute_features_one, FEATURE_NAMES, CUTOFF, load_cache,
)

OUT = Path("results/tasks/0348_centrality_ablation")
DEG_IDX = FEATURE_NAMES.index("degree")
GNM_IDX = FEATURE_NAMES.index("gnm_msf")
CTQW_IDX = FEATURE_NAMES.index("ctqw")

ARMS = ["ctqw", "degree", "gnm_msf", "betweenness", "eigenvector", "closeness"]


# ---------------------------------------------------------------- validation
def validate_one(feats: dict, elig: np.ndarray, cached: dict | None) -> dict:
    """Re-derive degree/gnm_msf/ctqw for ONE structure from `feats` (this
    script's own `compute_features_one` output -- the exact call
    `task0318_input_space_ceiling.py`'s own Phase A used to build the
    committed cache) and confirm byte-exact match against that structure's
    committed `feature_cache/*.npz` columns -- before trusting the three
    genuinely new centralities computed on the same graph. Takes `feats`
    rather than recomputing it -- the caller has already paid for the one
    `compute_features_one` call this structure needs, for both validation
    and scoring (the original version of this script called it twice per
    structure, once per purpose; fixed, see module docstring)."""
    if cached is None:
        return dict(checked=False, exact_match=None, max_abs_diff=None)
    my = dict(degree=feats["X"][elig, DEG_IDX],
              gnm_msf=feats["X"][elig, GNM_IDX],
              ctqw=feats["X"][elig, CTQW_IDX])
    theirs = dict(degree=cached["X"][:, DEG_IDX],
                  gnm_msf=cached["X"][:, GNM_IDX],
                  ctqw=cached["X"][:, CTQW_IDX])
    diffs = {}
    ok = True
    for k in my:
        d = float(np.max(np.abs(my[k] - theirs[k]))) if len(my[k]) else 0.0
        diffs[k] = d
        ok = ok and d < 1e-9
    return dict(checked=True, exact_match=ok, max_abs_diff=diffs)


# --------------------------------------------------------- cluster-robust stats
# Generic sign-flip test over cluster-summed values, same construction
# TASK-0318's own `cluster_sign_flip_test_generic` uses (that copy is a
# nested function inside its `phase_b`, not importable -- reimplemented at
# module level here so it can be called on this task's own per-structure
# deltas without a parallel design).
def cluster_sign_flip_test(values: dict, cluster_map: dict, n_mc: int = 100_000, seed: int = 0) -> dict:
    keys = [k for k in values if k in cluster_map]
    clusters = sorted(set(cluster_map[k] for k in keys))
    by_cluster = {c: [] for c in clusters}
    for k in keys:
        by_cluster[cluster_map[k]].append(values[k])
    cluster_sums = {c: sum(v) for c, v in by_cluster.items()}
    obs = sum(cluster_sums.values())
    n_clusters = len(clusters)
    rng = np.random.default_rng(seed)
    if n_clusters <= 20:
        null = np.array([sum(sg * cluster_sums[c] for sg, c in zip(signs, clusters))
                          for signs in itertools.product([1, -1], repeat=n_clusters)])
        exact = True
    else:
        signs = rng.choice([1, -1], size=(n_mc, n_clusters))
        sums_arr = np.array([cluster_sums[c] for c in clusters])
        null = signs @ sums_arr
        exact = False
    p = float(np.mean(np.abs(null) >= abs(obs) - 1e-9))
    return dict(n_rows=len(keys), n_clusters=n_clusters, p_value=p, exact=exact,
                median=float(np.median([values[k] for k in keys])))


def cluster_bootstrap_ci(values: dict, cluster_map: dict, statistic=np.median,
                          n_boot: int = 10000, seed: int = 0, alpha: float = 0.05) -> dict:
    """Resample CLUSTERS (proteins) with replacement, recompute `statistic`
    over the resampled rows each time -- percentile CI on the summary
    statistic under between-protein resampling, not row resampling."""
    keys = [k for k in values if k in cluster_map]
    clusters = sorted(set(cluster_map[k] for k in keys))
    rows_by_cluster = {c: [] for c in clusters}
    for k in keys:
        rows_by_cluster[cluster_map[k]].append(values[k])
    rng = np.random.default_rng(seed)
    n_c = len(clusters)
    boots = np.empty(n_boot)
    for b in range(n_boot):
        picked = rng.choice(clusters, size=n_c, replace=True)
        rows = [v for c in picked for v in rows_by_cluster[c]]
        boots[b] = statistic(rows)
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return dict(point=float(statistic([values[k] for k in keys])),
                ci95=[round(float(lo), 4), round(float(hi), 4)], n_clusters=n_c)


CHECKPOINT_PATH = OUT / "checkpoint.jsonl"


def load_checkpoint() -> dict:
    """pdb -> result dict, from a prior (possibly killed/crashed) run --
    resumed instead of recomputed. Malformed trailing line (a kill mid-write)
    is dropped, not fatal -- everything before it is still good."""
    per_structure = {}
    if not CHECKPOINT_PATH.exists():
        return per_structure
    n_bad = 0
    for line in CHECKPOINT_PATH.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            n_bad += 1
            continue
        per_structure[rec["pdb"]] = rec
    if n_bad:
        print(f"checkpoint: dropped {n_bad} malformed trailing line(s)")
    if per_structure:
        print(f"checkpoint: resuming with {len(per_structure)} structures already done "
              f"({CHECKPOINT_PATH})")
    return per_structure


def main() -> int:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    cached_by_pdb = {r["pdb"]: r for r in load_cache()}
    print(f"loaded {len(cached_by_pdb)} cached structures from feature_cache")

    structures = build_structures()
    print(f"{len(structures)} structures from build_structures() ({time.time()-t0:.0f}s)")

    per_structure = load_checkpoint()
    todo = [s for s in structures if s["pdb"] not in per_structure]
    print(f"{len(todo)}/{len(structures)} structures left to process")

    n_val_checked = sum(1 for r in per_structure.values()
                        if not r.get("failed") and r["validation"]["checked"])
    n_val_exact = sum(1 for r in per_structure.values()
                       if not r.get("failed") and r["validation"]["exact_match"])
    checkpoint_f = open(CHECKPOINT_PATH, "a")
    t_loop = time.time()
    n_failed = 0
    for i, s in enumerate(todo, 1):
        t_s = time.time()
        try:
            # `compute_features_one` (`task0318_input_space_ceiling.py`'s own
            # Phase A) can raise -- e.g. a disconnected contact graph hits
            # `superpose.py`'s own `_check_anm_rigid_body_nullspace` guard
            # (TASK-0005's original disconnected-graph regression, an
            # intentional refusal, not a bug). Phase A itself wraps this
            # exact call in a skip-and-continue try/except; this script had
            # not, and crashed the whole run on one bad structure -- fixed
            # to match Phase A's own established handling.
            feats = compute_features_one(s)
        except Exception as exc:  # noqa: BLE001 -- matches Phase A's own convention
            print(f"  [{i}/{len(todo)}] {s['pdb']:<14} FAILED: {exc!r}")
            rec = dict(pdb=s["pdb"], protein=s["protein"], n_residues=int(s["N"]),
                       failed=True, error=repr(exc))
            per_structure[s["pdb"]] = rec
            checkpoint_f.write(json.dumps(rec) + "\n")
            checkpoint_f.flush()
            n_failed += 1
            continue
        elig = s["elig"]
        xyz = s["xyz"]
        y = s["y"]

        validation = validate_one(feats, elig, cached_by_pdb.get(s["pdb"]))
        n_val_checked += int(validation["checked"])
        n_val_exact += int(bool(validation["exact_match"]))
        if validation["checked"] and not validation["exact_match"]:
            print(f"  !! VALIDATION MISMATCH on {s['pdb']}: {validation['max_abs_diff']} "
                  f"-- this structure's new centralities are still computed and recorded, "
                  f"but flagged, not silently trusted.")

        scores = dict(
            ctqw=feats["X"][elig, CTQW_IDX],
            degree=feats["X"][elig, DEG_IDX],
            gnm_msf=feats["X"][elig, GNM_IDX],
            betweenness=betweenness_centrality(xyz, cutoff=CUTOFF)[elig],
            eigenvector=eigenvector_centrality(xyz, cutoff=CUTOFF)[elig],
            closeness=closeness_centrality(xyz, cutoff=CUTOFF)[elig],
        )
        rho = {}
        auc = {}
        for arm in ARMS:
            v = scores[arm]
            if arm != "ctqw" and np.ptp(v) > 0 and np.ptp(scores["ctqw"]) > 0:
                rho[arm] = float(spearmanr(scores["ctqw"], v).statistic)
            if np.ptp(v) > 0 and y.sum() not in (0, len(y)):
                auc[arm] = float(roc_auc_score(y, v))

        rec = dict(pdb=s["pdb"], protein=s["protein"], n_residues=int(s["N"]),
                   n_elig=int(elig.sum()), rho_vs_ctqw=rho, auc=auc, validation=validation)
        per_structure[s["pdb"]] = rec
        checkpoint_f.write(json.dumps(rec) + "\n")
        checkpoint_f.flush()

        elapsed = time.time() - t_loop
        rate = elapsed / i
        eta = rate * (len(todo) - i)
        print(f"  [{i}/{len(todo)}] {s['pdb']:<14} N={s['N']:5d} elig={elig.sum():4d} "
              f"this={time.time()-t_s:5.1f}s elapsed={elapsed:6.0f}s eta={eta:6.0f}s")

    checkpoint_f.close()

    print(f"\nPlanned Validation: {n_val_exact}/{n_val_checked} structures exact-match "
          f"against feature_cache (degree/gnm_msf/ctqw)")
    if n_val_checked == 0 or n_val_exact != n_val_checked:
        print("VALIDATION DID NOT FULLY PASS -- see per-structure mismatch lines above. "
              "Results are still written (nothing is silently discarded), but treat any "
              "arm involving a flagged structure's new centralities as unverified until "
              "the mismatch is explained.")

    n_failed = sum(1 for r in per_structure.values() if r.get("failed"))
    print(f"scored {len(per_structure) - n_failed} structures, {n_failed} failed "
          f"({time.time()-t0:.0f}s total)")

    ok_structures = {pdb: rec for pdb, rec in per_structure.items() if not rec.get("failed")}
    cluster_map = {pdb: rec["protein"] for pdb, rec in ok_structures.items()}

    # -------- 1. rank correlation with CTQW, per classical arm --------
    rho_summary = {}
    for arm in ARMS:
        if arm == "ctqw":
            continue
        vals = {pdb: rec["rho_vs_ctqw"][arm] for pdb, rec in ok_structures.items()
                if arm in rec["rho_vs_ctqw"]}
        if not vals:
            continue
        ci = cluster_bootstrap_ci(vals, cluster_map)
        rho_summary[arm] = dict(
            n=len(vals), median=round(float(np.median(list(vals.values()))), 4),
            iqr=[round(float(np.percentile(list(vals.values()), 25)), 4),
                 round(float(np.percentile(list(vals.values()), 75)), 4)],
            cluster_bootstrap_median_ci95=ci["ci95"], n_clusters=ci["n_clusters"],
        )

    # -------- 2. AUC of every arm vs the same truth labels --------
    auc_summary = {}
    auc_deltas_vs_ctqw = {}
    for arm in ARMS:
        vals = {pdb: rec["auc"][arm] for pdb, rec in ok_structures.items() if arm in rec["auc"]}
        if not vals:
            continue
        ci = cluster_bootstrap_ci(vals, cluster_map)
        auc_summary[arm] = dict(
            n=len(vals), mean=round(float(np.mean(list(vals.values()))), 4),
            median=round(float(np.median(list(vals.values()))), 4),
            cluster_bootstrap_median_ci95=ci["ci95"], n_clusters=ci["n_clusters"],
        )
        if arm != "ctqw":
            common = set(vals) & {pdb for pdb, rec in ok_structures.items() if "ctqw" in rec["auc"]}
            deltas = {pdb: ok_structures[pdb]["auc"]["ctqw"] - vals[pdb] for pdb in common}
            if deltas:
                test = cluster_sign_flip_test(deltas, cluster_map)
                auc_deltas_vs_ctqw[arm] = dict(
                    n=len(deltas), median_delta=round(test["median"], 4),
                    cluster_permutation_p=round(test["p_value"], 4),
                    n_clusters=test["n_clusters"], exact=test["exact"],
                )

    print("\n=== Spearman rho(CTQW, classical arm), cluster-bootstrap 95% CI on the median ===")
    for arm, r in rho_summary.items():
        print(f"  {arm:<12} n={r['n']:3d} median={r['median']:+.4f} iqr={r['iqr']} "
              f"cluster-CI={r['cluster_bootstrap_median_ci95']}")

    print("\n=== AUC per arm vs truth labels ===")
    for arm, r in auc_summary.items():
        print(f"  {arm:<12} n={r['n']:3d} mean={r['mean']:.4f} median={r['median']:.4f} "
              f"cluster-CI={r['cluster_bootstrap_median_ci95']}")

    print("\n=== AUC(ctqw) - AUC(arm), cluster-permutation p (H0: median delta = 0) ===")
    for arm, r in auc_deltas_vs_ctqw.items():
        print(f"  ctqw - {arm:<12} n={r['n']:3d} median_delta={r['median_delta']:+.4f} "
              f"p={r['cluster_permutation_p']} n_clusters={r['n_clusters']} exact={r['exact']}")

    out = dict(
        jacs_reference=dict(
            citation="Mohtashim, Sajjan & Kais, JACS 148(27):29206-29219 (2026), "
                     "DOI 10.1021/jacs.6c08053",
            reported_rho_median_vs_eigenvector=0.95,
            reported_kendall_tau_vs_eigenvector=0.87,
            reported_overlap_at_10=[0.90, 1.00],
        ),
        planned_validation=dict(n_checked=n_val_checked, n_exact_match=n_val_exact),
        n_structures=len(ok_structures),
        n_failed=n_failed,
        n_proteins=len(set(cluster_map.values())),
        cutoff=CUTOFF,
        rank_correlation_vs_ctqw=rho_summary,
        auc_per_arm=auc_summary,
        auc_delta_ctqw_minus_arm=auc_deltas_vs_ctqw,
        per_structure=per_structure,
    )
    out_path = OUT / "centrality_ablation_result.json"
    out_path.write_text(json.dumps(out, indent=1))
    print(f"\nWrote {out_path} ({time.time()-t0:.0f}s total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
