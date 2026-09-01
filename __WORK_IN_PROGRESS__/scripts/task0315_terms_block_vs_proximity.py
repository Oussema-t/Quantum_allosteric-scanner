"""TASK-0315 (filed as TASK-0313, renumbered -- see that task file's own
note) -- the terms-block result (0.751 vs CTQW 0.575, cluster-robust
p=0.019, [[TASK-0263]]'s headline) was never compared to the dominant
confound this register conditions every other apparent signal on:
proximity to the seed. [[TASK-0308]] found CTQW's own +18.4% AUC share
is "almost entirely proximity" (residual AUC 0.518, not significant).
This script runs the same style of test on the terms block and on V_C
alone, plus the comparison [[TASK-0277]] already computed but that was
never placed next to [[TASK-0263]]'s own headline.

Reuses, does not re-derive:
  - `task0249_composite_dumb_baseline.target_rows` -- frozen-20 per-target
    coords/bfactors/seed/cutoff/CTQW/label rows ([[TASK-0263]]'s own route).
  - `task0254_fpocket_variance_and_crypticity.build_blocks`/`z` -- the
    geometry(degree,euclid,hop)/fpocket blocks and z-scoring convention.
  - `task0263_potential_terms_direct_predictors.potential_term_vectors`,
    `TERM_NAMES` -- the five V_B/V_T/V_R/V_C/V_M per-residue vectors,
    `build_H_new`'s own defaults, unchanged.
  - `task0261_cluster_robust_stats.CM`/`cluster_sign_flip_test` -- the
    13-cluster-robust significance test, not row-level Wilcoxon.
  - `allostery.metrics.auc`, `allostery.baselines.hop_from_seed` /
    `euclid_from_seed_centroid` (both already "closer = higher score" by
    this module's own convention, no extra sign flip needed).

New in this script (all built FROM the above, no re-tuning, no new
sweeps):
  - `cv_score`: TASK-0245's own 5-fold/20-rep/OLS-via-lstsq protocol
    (`task0254.cv_auc`, reused verbatim for the fold/rep/seed machinery),
    but returning the mean out-of-fold fitted score array alongside the
    AUC, not just the AUC -- self-checked to reproduce `cv_auc`'s own AUC
    exactly on the same input before being trusted for anything else.
  - `rank_residualize`: [[TASK-0308]]'s own method ("residualising X on
    proximity, rank-wise, per structure") made explicit and reusable --
    per-target rank-transform of both the score and proximity, OLS the
    score-rank on the proximity-rank, return the residual. Sign-agnostic
    by construction (OLS residuals are unchanged by negating a
    predictor), so it does not matter which sign convention "proximity"
    is passed in.

Positive control (this task's own Constraint): `euclid_from_seed_centroid`
residualised on `hop_from_seed`-proximity was expected to land at ~0.5.
It does not (residual mean AUC ~0.61, drop from raw significant at
p=0.013 but not fully to chance, p=0.121 vs 0.5) -- root-caused with a
synthetic redundant/independent self-check run inside this script before
trusting anything further: `rank_residualize` itself is correct (collapses
a truly redundant predictor to ~0.5, preserves an independent one), so
this is a genuine cohort finding, not a harness bug -- on this register's
own 20 targets (more heterogeneous, several genuinely distal-labelled,
than ASBench's more proximal-skewed population) hop-distance and
Euclidean seed-distance are correlated but not fully redundant. Fixed by
residualising the terms-block/V_C/CTQW numbers on BOTH jointly, a more
complete "closeness to seed" control than either alone.

Run: ../.venv/bin/python3 scripts/task0315_terms_block_vs_proximity.py
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
from scipy.stats import rankdata
import yaml

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import task0242_two_stage_dryrun as t0242  # noqa: E402
import task0249_composite_dumb_baseline as t0249  # noqa: E402
from task0254_fpocket_variance_and_crypticity import (  # noqa: E402
    build_blocks, cv_auc, z, N_FOLD, N_REP,
)
from task0261_cluster_robust_stats import CM, cluster_sign_flip_test  # noqa: E402
from task0263_potential_terms_direct_predictors import (  # noqa: E402
    potential_term_vectors, TERM_NAMES,
)
from allostery.baselines import hop_from_seed, euclid_from_seed_centroid  # noqa: E402
from allostery.metrics import auc  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402

OUT = _ROOT / "results/tasks/0315_terms_block_vs_proximity"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"


# --------------------------------------------------------------- cv_score
def cv_score(X: np.ndarray, y: np.ndarray, n_rep: int = N_REP):
    """`task0254.cv_auc`'s exact protocol (5-fold stratified, N_REP
    repeats, OLS via lstsq, same `random_state=rep` sequence), but also
    returning the mean out-of-fold fitted score array so it can be
    rank-residualised downstream. Returns (auc, mean_oof_score)."""
    X = np.atleast_2d(X.T).T if X.ndim == 1 else X
    aucs, oofs = [], []
    for rep in range(n_rep):
        skf = StratifiedKFold(n_splits=N_FOLD, shuffle=True, random_state=rep)
        oof = np.zeros(len(y))
        for tr, te in skf.split(X, y):
            Xb_tr = np.column_stack([X[tr], np.ones(len(tr))])
            b, *_ = np.linalg.lstsq(Xb_tr, y[tr].astype(float), rcond=None)
            oof[te] = np.column_stack([X[te], np.ones(len(te))]) @ b
        oofs.append(oof)
        aucs.append(auc(oof, y))
    return float(np.mean(aucs)), np.mean(oofs, axis=0)


def rank_residualize(score: np.ndarray, *proximity: np.ndarray) -> np.ndarray:
    """[[TASK-0308]]'s own method made explicit: rank-transform both
    within this one structure, OLS the score-rank on the proximity-rank(s)
    (+intercept), return the residual. Sign-agnostic (OLS residuals are
    invariant to negating a predictor column). Accepts one or more
    proximity measures -- passing both hop and euclid jointly removes
    more of the "distance to seed" construct than either alone (see this
    task's own positive-control finding: on this cohort the two are
    correlated but not fully redundant, so hop alone under-controls)."""
    rs = rankdata(score).astype(float)
    rp_cols = [rankdata(p).astype(float) for p in proximity]
    Xb = np.column_stack(rp_cols + [np.ones(len(rs))])
    b, *_ = np.linalg.lstsq(Xb, rs, rcond=None)
    return rs - Xb @ b


def cluster_robust(per_target: dict, label: str):
    d = {t: v for t, v in per_target.items() if t in CM}
    n_dropped = len(per_target) - len(d)
    r = cluster_sign_flip_test(d)
    print(f"  [{label}] median={r['median']:+.4f} n_rows={r['n_rows']} "
          f"n_clusters={r['n_clusters']} p={r['p_value']:.4f}"
          + (f"  ({n_dropped} target(s) outside TASK-0261's cluster map, excluded)" if n_dropped else ""))
    return r


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    new_cand = yaml.safe_load(FROZEN_CONFIG.read_text())["targets"]
    t0242.CAND = new_cand
    frozen_targets = list(new_cand.keys())

    data = {}
    for t in frozen_targets:
        try:
            d = t0249.target_rows(t)
        except Exception as exc:  # noqa: BLE001
            print(f"{t}: FAILED {exc!r}")
            continue
        if d is None or d["n_pocket"] < 3:
            print(f"{t}: SKIP (fpocket failure, empty seed, or too few positives)")
            continue
        data[t] = d
    print(f"\n{len(data)}/{len(frozen_targets)} usable\n")

    results = {}

    # ---------------------------------------------------- Part 0: self-check
    print("### Part 0 -- cv_score self-check (must reproduce cv_auc exactly) ###")
    t0 = next(iter(data))
    d0 = data[t0]
    n0 = len(d0["coords"]); m0 = np.ones(n0, dtype=bool); m0[d0["seed"]] = False
    x0 = z(hop_from_seed(d0["coords"], d0["seed"], cutoff=d0["cut"]))[m0]
    a_direct = cv_auc(x0.reshape(-1, 1), d0["y"])
    a_via_score, _ = cv_score(x0.reshape(-1, 1), d0["y"])
    print(f"  cv_auc={a_direct:.6f}  cv_score's own auc={a_via_score:.6f}  "
          f"(diff={abs(a_direct - a_via_score):.2e})")
    assert abs(a_direct - a_via_score) < 1e-9, "cv_score does not reproduce cv_auc -- do not trust anything below"
    results["self_check_ok"] = True

    # ------------------------------------------- Part 1: the base AUC table
    print("\n### Part 1 -- base AUC table, frozen 20, fresh (not re-read from TASK-0263's old json) ###")
    per_target = {}
    for t, d in data.items():
        n = len(d["coords"]); seed = d["seed"]
        m = np.ones(n, dtype=bool); m[seed] = False
        y = d["y"]

        tv = potential_term_vectors(d["coords"], d["bfactors"], d["cut"])
        per_term_row = {}
        term_mat = []
        for name in TERM_NAMES:
            vec = z(tv[name][m])
            per_term_row[name] = cv_auc(vec.reshape(-1, 1), y)
            term_mat.append(vec)
        terms_X = np.column_stack(term_mat)
        terms_auc, terms_oof = cv_score(terms_X, y)

        feat3 = build_blocks(t, d)
        geometry_auc = cv_auc(feat3["geometry"], y)
        euclid_col = z(euclid_from_seed_centroid(d["coords"], seed))[m]
        hop_col = z(hop_from_seed(d["coords"], seed, cutoff=d["cut"]))[m]
        euclid_auc, euclid_oof = cv_score(euclid_col.reshape(-1, 1), y)
        hop_auc = cv_auc(hop_col.reshape(-1, 1), y)
        ctqw_auc, ctqw_oof = cv_score(d["x_ctqw"].reshape(-1, 1), y)
        vc_auc, vc_oof = cv_score(z(tv["V_C"][m]).reshape(-1, 1), y)
        terms_sum_auc, terms_sum_oof = cv_score(
            np.mean(term_mat, axis=0).reshape(-1, 1), y)  # unfitted equal-weight combination

        per_target[t] = dict(
            per_term=per_term_row, terms_block=terms_auc, geometry=geometry_auc,
            euclid=euclid_auc, hop=hop_auc, ctqw=ctqw_auc, V_C=vc_auc, terms_sum=terms_sum_auc,
            _terms_oof=terms_oof.tolist(), _ctqw_oof=ctqw_oof.tolist(), _vc_oof=vc_oof.tolist(),
            _terms_sum_oof=terms_sum_oof.tolist(), _euclid_oof=euclid_oof.tolist(),
            _hop_col=hop_col.tolist(), _y=y.tolist(),
        )
        print(f"{t:24s} terms_block={terms_auc:.3f} geometry={geometry_auc:.3f} "
              f"euclid={euclid_auc:.3f} hop={hop_auc:.3f} ctqw={ctqw_auc:.3f} "
              f"V_C={vc_auc:.3f} terms_sum(unfitted)={terms_sum_auc:.3f}")

    def median_of(key):
        return float(np.median([per_target[t][key] for t in per_target]))

    print(f"\n  median: terms_block={median_of('terms_block'):.4f} geometry={median_of('geometry'):.4f} "
          f"euclid={median_of('euclid'):.4f} hop={median_of('hop'):.4f} ctqw={median_of('ctqw'):.4f} "
          f"V_C={median_of('V_C'):.4f} terms_sum={median_of('terms_sum'):.4f}")
    results["medians"] = {k: median_of(k) for k in
                           ("terms_block", "geometry", "euclid", "hop", "ctqw", "V_C", "terms_sum")}

    # --- per-term cell distribution (Scope: restate the "0.81-0.93" claim honestly) ---
    all_cells = [per_target[t]["per_term"][name] for t in per_target for name in TERM_NAMES]
    print(f"\n  per-term x per-target cells (n={len(all_cells)}): "
          f"median={np.median(all_cells):.3f} mean={np.mean(all_cells):.3f} "
          f"max={np.max(all_cells):.3f} (previously cited range 0.81-0.93 is near this max, "
          f"not a typical cell)")
    results["per_term_cell_distribution"] = dict(
        n=len(all_cells), median=float(np.median(all_cells)), mean=float(np.mean(all_cells)),
        max=float(np.max(all_cells)), min=float(np.min(all_cells)))

    # ------------------------------- Part 2: headline, cluster-robust, reproduced
    print("\n### Part 2 -- terms_block vs geometry, cluster-robust (reproducing the Reviewer thread's own finding) ###")
    diffs_tg = {t: per_target[t]["terms_block"] - per_target[t]["geometry"] for t in per_target}
    r_tg = cluster_robust(diffs_tg, "terms_block - geometry")
    print("\n  (for reference) terms_block vs ctqw, cluster-robust:")
    diffs_tc = {t: per_target[t]["terms_block"] - per_target[t]["ctqw"] for t in per_target}
    r_tc = cluster_robust(diffs_tc, "terms_block - ctqw")
    results["headline_vs_geometry"] = dict(diffs=diffs_tg, test=r_tg)
    results["headline_vs_ctqw"] = dict(diffs=diffs_tc, test=r_tc)

    # ---------------------------------- Part 3: per-term rho(term, proximity)
    print("\n### Part 3 -- per-term Spearman(term, proximity=hop_from_seed), frozen 20 (not targets.yaml's 14) ###")
    from scipy.stats import spearmanr
    term_rho = {name: [] for name in TERM_NAMES}
    for t, d in data.items():
        n = len(d["coords"]); seed = d["seed"]
        m = np.ones(n, dtype=bool); m[seed] = False
        prox = hop_from_seed(d["coords"], seed, cutoff=d["cut"])[m]
        tv = potential_term_vectors(d["coords"], d["bfactors"], d["cut"])
        for name in TERM_NAMES:
            rho = spearmanr(tv[name][m], prox).statistic
            term_rho[name].append(float(rho) if np.isfinite(rho) else None)
    for name in TERM_NAMES:
        vals = [v for v in term_rho[name] if v is not None]
        print(f"  {name}: median rho={np.median(vals):+.3f}  "
              f"range [{min(vals):+.3f}, {max(vals):+.3f}]  n={len(vals)}")
    results["term_proximity_rho"] = {name: term_rho[name] for name in TERM_NAMES}

    # ------------------------------------- Part 4: rank-wise residualization
    print("\n### Part 4 -- rank-wise-per-structure residualization on proximity ###")

    print("  Synthetic self-check of rank_residualize (n=200, seed=0) -- "
          "must collapse a redundant predictor near 0.5 and preserve an independent one:")
    _rng = np.random.default_rng(0)
    _hop = _rng.normal(size=200)
    _redundant = _hop + 0.05 * _rng.normal(size=200)
    _y_a = (_hop + 0.5 * _rng.normal(size=200) > 0).astype(int)
    _indep = _rng.normal(size=200)
    _y_b = ((_hop + _indep) > 0).astype(int)
    _redundant_resid_auc = float(auc(rank_residualize(_redundant, _hop), _y_a))
    _indep_raw_auc = float(auc(_indep, _y_b))
    _indep_resid_auc = float(auc(rank_residualize(_indep, _hop), _y_b))
    print(f"    redundant case: residual AUC={_redundant_resid_auc:.3f} (expect ~0.5)")
    print(f"    independent case: raw AUC={_indep_raw_auc:.3f} residual AUC={_indep_resid_auc:.3f} (expect ~preserved)")
    assert abs(_redundant_resid_auc - 0.5) < 0.05, "rank_residualize does not collapse a redundant predictor -- BUG, stop"
    assert abs(_indep_resid_auc - _indep_raw_auc) < 0.05, "rank_residualize destroys independent signal -- BUG, stop"
    results["synthetic_selfcheck"] = dict(redundant_resid_auc=_redundant_resid_auc,
                                           indep_raw_auc=_indep_raw_auc, indep_resid_auc=_indep_resid_auc)

    print("\n  Cross-check: are hop and euclid themselves redundant on THIS cohort? "
          "(single-predictor each way, not the harness -- rank_residualize verified correct above)")
    hop_on_euclid, euclid_on_hop = {}, {}
    hop_raw_auc, euclid_raw_auc = {}, {}
    for t in per_target:
        r = per_target[t]
        hop_col = np.array(r["_hop_col"]); euclid_oof = np.array(r["_euclid_oof"]); y = np.array(r["_y"])
        hop_raw_auc[t] = float(auc(hop_col, y))
        euclid_raw_auc[t] = float(auc(euclid_oof, y))
        hop_on_euclid[t] = float(auc(rank_residualize(hop_col, euclid_oof), y))
        euclid_on_hop[t] = float(auc(rank_residualize(euclid_oof, hop_col), y))
    print(f"    hop:    raw mean={np.mean(list(hop_raw_auc.values())):.4f}  "
          f"residual-on-euclid mean={np.mean(list(hop_on_euclid.values())):.4f}")
    print(f"    euclid: raw mean={np.mean(list(euclid_raw_auc.values())):.4f}  "
          f"residual-on-hop mean={np.mean(list(euclid_on_hop.values())):.4f}")
    r_cross_e = cluster_robust({t: euclid_on_hop[t] - 0.5 for t in euclid_on_hop}, "euclid-on-hop residual vs chance")
    r_cross_h = cluster_robust({t: hop_on_euclid[t] - 0.5 for t in hop_on_euclid}, "hop-on-euclid residual vs chance")
    print("  NOT a clean ~0.5 either direction -- on this cohort (heterogeneous, several genuinely "
          "distal-labelled targets, unlike ASBench's more proximal-skewed population) hop-distance and "
          "Euclidean seed-distance are correlated but NOT fully redundant. Not a harness bug (synthetic "
          "check above passes); the honest fix is to residualise on BOTH jointly, not hop alone, below.")
    results["hop_euclid_cross_check"] = dict(
        hop_raw_mean=float(np.mean(list(hop_raw_auc.values()))),
        hop_on_euclid_mean=float(np.mean(list(hop_on_euclid.values()))), hop_on_euclid_test=r_cross_h,
        euclid_raw_mean=float(np.mean(list(euclid_raw_auc.values()))),
        euclid_on_hop_mean=float(np.mean(list(euclid_on_hop.values()))), euclid_on_hop_test=r_cross_e)

    print("\n  Main test: residualising each arm on BOTH hop and euclid jointly (the more complete "
          "'closeness to seed' control):")
    resid_auc = {"terms_block": {}, "V_C": {}, "ctqw": {}, "terms_sum": {}}
    raw_auc_for_resid = {"terms_block": {}, "V_C": {}, "ctqw": {}, "terms_sum": {}}
    for t in per_target:
        r = per_target[t]
        hop_col = np.array(r["_hop_col"]); euclid_oof = np.array(r["_euclid_oof"])
        y = np.array(r["_y"])
        for key, score in (
            ("terms_block", np.array(r["_terms_oof"])),
            ("V_C", np.array(r["_vc_oof"])),
            ("ctqw", np.array(r["_ctqw_oof"])),
            ("terms_sum", np.array(r["_terms_sum_oof"])),
        ):
            resid = rank_residualize(score, hop_col, euclid_oof)
            resid_auc[key][t] = float(auc(resid, y))
            raw_auc_for_resid[key][t] = float(auc(score, y))

    for key in ("terms_block", "V_C", "ctqw", "terms_sum"):
        raw_mean = float(np.mean(list(raw_auc_for_resid[key].values())))
        res_mean = float(np.mean(list(resid_auc[key].values())))
        print(f"\n  -- {key} --  raw mean AUC={raw_mean:.4f}  residual mean AUC={res_mean:.4f}")
        r_chance = cluster_robust({t: v - 0.5 for t, v in resid_auc[key].items()},
                                   f"{key} residual vs chance (0.5)")
        r_drop = cluster_robust({t: raw_auc_for_resid[key][t] - resid_auc[key][t] for t in resid_auc[key]},
                                 f"{key} raw - residual (the drop)")
        results.setdefault("residualization", {})[key] = dict(
            raw_auc=raw_auc_for_resid[key], residual_auc=resid_auc[key],
            raw_mean=raw_mean, residual_mean=res_mean,
            vs_chance_test=r_chance, drop_test=r_drop)

    with open(OUT / "terms_block_vs_proximity.json", "w") as fh:
        json.dump(results, fh, indent=1)
    print(f"\nWrote {OUT / 'terms_block_vs_proximity.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
