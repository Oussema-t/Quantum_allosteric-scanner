"""TASK-0318 addendum -- the missing negative control for the input-space
ceiling result, flagged in that task's own "Open item this task did not
cover" section (added by the Reviewer thread's correction pass) and named
again by [[TASK-0319]] as the same systemic omission (positive controls
run throughout this register, negative ones skipped).

The committed result: LOPO-by-protein `HistGradientBoostingClassifier`
over 19 reused features, residualised jointly on [hop, euclid] proximity,
gives residual AUC mean=0.5949 (Wilcoxon p=3.3e-6 vs 0.5, cluster-robust
p=1e-5, 74 protein clusters). No negative control existed for that number.

THIS SCRIPT: permute the truth labels **within each structure** (preserving
each structure's own positive count exactly -- a between-structure
permutation would additionally scramble class balance, a confound this
task's own open item did not ask for and this script does not introduce),
refit the IDENTICAL LOPO-by-protein pipeline (same features, same fold
structure, same `HistGradientBoostingClassifier(max_iter=150, max_depth=6,
random_state=0)`, same joint [hop, euclid] residualisation), and report the
resulting residual-AUC-mean's own null distribution.

Reuses [[TASK-0318]]'s own `task0318_input_space_ceiling.py` verbatim by
import (same task, not a cross-task lane-collision situation) --
`load_cache`, `resid_auc_joint`, `FEATURE_NAMES` -- and its own cached
Phase-A features (`results/tasks/0318_input_space_ceiling/feature_cache/`,
105 structures, unchanged, no re-fetch/re-derive of any structure).

COMPUTE BUDGET, disclosed not silently chosen: one real (unpermuted) LOPO
fit costs ~100-120s (this task's own committed Done section: "Phase B,
fast, ~118s"). [[TASK-0319]]'s own >=200-rep acceptance bar is scoped to
modality LRT false-positive rates specifically, not adopted here as a
blanket requirement -- at ~118s/rep, 200 reps is ~6.5 hours, judged not
worth the wall-clock for a check whose own expected answer (a null AUC
distribution centred near 0.50) needs only enough reps to establish the
null's own mean/spread precisely, not a razor-thin p-value on an effect
this large. N_REPS chosen below and reported plainly; the exact permuted
mean-AUCs are all written to the output JSON so anyone can recompute the
p-value at a different N or bootstrap it directly rather than trust a
summary number alone.

Run: ../.venv/bin/python3 scripts/task0318_negative_control.py [--n-reps N]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

sys.path.insert(0, ".")
from task0318_input_space_ceiling import load_cache, resid_auc_joint, FEATURE_NAMES  # noqa: E402

OUT = Path("results/tasks/0318_input_space_ceiling")
OBSERVED_MEAN = 0.5949  # this task's own committed ceiling_result.json residual_ceiling.mean
N_REPS_DEFAULT = 30


def one_permuted_rep(rows: list, rng: np.random.Generator) -> dict:
    """One full LOPO-by-protein refit on within-structure-permuted labels.
    Structure exactly mirrors `task0318_input_space_ceiling.phase_b`'s own
    pooling/fit/residualise/aggregate block, with y permuted per structure
    before pooling -- the only change."""
    X_all, y_all, prot_all, struct_all = [], [], [], []
    for si, r in enumerate(rows):
        yp = rng.permutation(r["y"])  # within THIS structure only, preserves its own positive count
        X_all.append(r["X"]); y_all.append(yp)
        prot_all.extend([r["protein"]] * len(yp))
        struct_all.extend([si] * len(yp))
    X_all = np.vstack(X_all); y_all = np.concatenate(y_all)
    prot_all = np.array(prot_all); struct_all = np.array(struct_all)
    proteins = sorted(set(prot_all))

    oof_score = np.full(len(y_all), np.nan)
    for prot in proteins:
        test_mask = prot_all == prot
        train_mask = ~test_mask
        if y_all[train_mask].sum() == 0 or y_all[train_mask].sum() == train_mask.sum():
            continue
        clf = HistGradientBoostingClassifier(max_iter=150, max_depth=6, random_state=0)
        clf.fit(X_all[train_mask], y_all[train_mask])
        oof_score[test_mask] = clf.predict_proba(X_all[test_mask])[:, 1]

    raw_aucs, resid_aucs = [], []
    for si, r in enumerate(rows):
        m = struct_all == si
        sc = oof_score[m]
        yp = y_all[m]
        if not np.isfinite(sc).all() or np.ptp(sc) == 0:
            continue
        if yp.sum() == 0 or yp.sum() == len(yp):
            continue  # AUC undefined for this structure under this permutation, skip (not epsilon-padded)
        raw_aucs.append(float(roc_auc_score(yp, sc)))
        ra = resid_auc_joint(sc, yp, r["hop"], r["euclid"])
        if ra is not None:
            resid_aucs.append(ra)
    raw_aucs = np.array(raw_aucs); resid_aucs = np.array(resid_aucs)
    return dict(n_structures_scored=len(resid_aucs),
                raw_mean=float(raw_aucs.mean()), raw_median=float(np.median(raw_aucs)),
                resid_mean=float(resid_aucs.mean()), resid_median=float(np.median(resid_aucs)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-reps", type=int, default=N_REPS_DEFAULT)
    args = ap.parse_args()

    rows = load_cache()
    print(f"Loaded {len(rows)} cached structures. Running {args.n_reps} within-structure "
          f"label-permutation reps (identical LOPO-by-protein pipeline, only y permuted)...\n")

    reps = []
    t0 = time.monotonic()
    for i in range(args.n_reps):
        rng = np.random.default_rng(1000 + i)
        r = one_permuted_rep(rows, rng)
        reps.append(r)
        elapsed = time.monotonic() - t0
        print(f"  rep {i+1}/{args.n_reps}: resid_mean={r['resid_mean']:.4f} "
              f"resid_median={r['resid_median']:.4f} raw_mean={r['raw_mean']:.4f} "
              f"n={r['n_structures_scored']}  ({elapsed:.0f}s elapsed, "
              f"{elapsed/(i+1):.0f}s/rep)")

    resid_means = np.array([r["resid_mean"] for r in reps])
    raw_means = np.array([r["raw_mean"] for r in reps])
    null_mean = float(resid_means.mean())
    null_std = float(resid_means.std(ddof=1))
    # one-sided permutation p: fraction of null reps at or above the real observed mean
    p_perm = float((np.sum(resid_means >= OBSERVED_MEAN) + 1) / (len(resid_means) + 1))
    z = (OBSERVED_MEAN - null_mean) / null_std if null_std > 0 else float("inf")

    print(f"\n=== Negative control summary ({args.n_reps} reps) ===")
    print(f"  null residual-AUC-mean: {null_mean:.4f} +/- {null_std:.4f} "
          f"(expect ~0.5000 under a true null)")
    print(f"  raw (non-residualised) null mean: {raw_means.mean():.4f} +/- {raw_means.std(ddof=1):.4f}")
    print(f"  OBSERVED (real labels, committed): {OBSERVED_MEAN}")
    print(f"  permutation p (one-sided, {args.n_reps} reps): {p_perm:.4g}")
    print(f"  z-score (parametric, using the null's own mean/std): {z:.2f}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "negative_control.json").write_text(json.dumps(dict(
        n_reps=args.n_reps, observed_mean=OBSERVED_MEAN,
        reps=reps, null_mean=null_mean, null_std=null_std,
        p_perm=p_perm, z_score=z,
    ), indent=1))
    print(f"\nWrote {OUT}/negative_control.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
