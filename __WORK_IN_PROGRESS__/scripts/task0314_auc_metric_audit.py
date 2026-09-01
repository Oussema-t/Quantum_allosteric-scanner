"""TASK-0314 Part A -- the register has two incompatible "AUC"s, and every
solo-feature `cv_auc` needs its raw directional counterpart reported
alongside it before it is quoted again.

`task0254_fpocket_variance_and_crypticity.cv_auc` fits OLS per CV fold and
scores the out-of-fold PREDICTION. For a single feature, OLS picks
whichever sign best separates the label, so `cv_auc` measures
|discriminative power| -- it cannot be below ~0.5 by construction (modulo
CV-fold noise) even when the feature is strongly ANTI-correlated with the
label. `allostery.metrics.auc` (aliased here as `auc_directional`, the
Scope's own requested name) scores the RAW feature directly and is
signed: an anti-correlated feature reports below 0.5.

Demonstrated mechanism, reproduced fresh below (not just re-asserted from
the task's own filing): a synthetic feature built to anti-correlate with
its label scores ~0.24 raw / ~0.76 cv_auc -- confirming `cv_auc` silently
flips the sign rather than reporting it.

Consequence audited here: every solo-feature `cv_auc` quoted in
RESULTS.md/the brief states |separability|, not "ranks the label class
higher" -- the two only coincide when the feature is positively
correlated with the label to begin with. This script reports both for
every candidate the task names plus the two headline single-column
figures in the brief's own "Holds" table (CTQW, V_C alone).

Reuses, does not re-derive:
  - `task0254_fpocket_variance_and_crypticity.cv_auc`/`z` -- unchanged.
  - `allostery.metrics.auc` -- the raw directional ROC-AUC this whole
    register already has; only newly ALIASED here, not reimplemented.
  - `task0249_composite_dumb_baseline.target_rows` -- for `x_ctqw`/`y`
    (CTQW solo), exact z-scored, seed-excluded arrays [[TASK-0263]] itself
    scores.
  - `task0263_potential_terms_direct_predictors.potential_term_vectors`
    -- for the `V_C` raw term vector.
  - `task0277_apo_holo_ceiling_sweep.common_apo_holo_rows`/
    `compute_features` -- for the 8-feature apo/holo battery
    (`prs_low`/`degree`/`SASA`/... ), exact same arrays that produced the
    already-published `per_feature_auc_apo_holo.json` cv_auc medians.

Run: ../.venv/bin/python3 scripts/task0314_auc_metric_audit.py
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import yaml

warnings.filterwarnings("ignore")

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402
prody.confProDy(verbosity="none")
_orig_parsePDB = prody.parsePDB


def _parsePDB_all_altloc(*a, **kw):
    kw.setdefault("altloc", "all")
    return _orig_parsePDB(*a, **kw)


prody.parsePDB = _parsePDB_all_altloc

from task0254_fpocket_variance_and_crypticity import cv_auc  # noqa: E402
from allostery.metrics import auc as auc_directional  # noqa: E402  -- Scope's own requested name
from task0261_cluster_robust_stats import CM  # noqa: E402
import task0242_two_stage_dryrun as t0242  # noqa: E402
import task0249_composite_dumb_baseline as t0249  # noqa: E402
from task0263_potential_terms_direct_predictors import potential_term_vectors  # noqa: E402
import task0277_apo_holo_ceiling_sweep as t0277  # noqa: E402

OUT = _ROOT / "results/tasks/0314_auc_metric_audit"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"


# ---------------------------------------------------------------------------
# Part 0 -- the mechanism, reproduced fresh
# ---------------------------------------------------------------------------

def demonstrate_mechanism():
    print("=" * 78)
    print("PART 0 -- cv_auc silently flips sign; auc_directional does not")
    print("=" * 78)
    rng = np.random.default_rng(0)
    n = 200
    y = np.zeros(n, int)
    y[rng.choice(n, 40, replace=False)] = 1
    # x built to ANTI-correlate with y: higher x -> lower P(y=1)
    x = rng.normal(0, 1, n) - 2.0 * y
    raw = auc_directional(x, y)
    fitted = cv_auc(x.reshape(-1, 1), y)
    print(f"  synthetic anti-correlated feature (n={n}, 40 positives):")
    print(f"    auc_directional(x, y) = {raw:.4f}   <- correctly < 0.5, anti-correlated")
    print(f"    cv_auc(x, y)          = {fitted:.4f}   <- OLS silently flips the sign")
    print(f"    1 - raw = {1 - raw:.4f}  (cv_auc for a single feature tracks max(raw, 1-raw))")
    return dict(raw=float(raw), fitted=float(fitted))


# ---------------------------------------------------------------------------
# Part 1 -- CTQW solo and V_C alone, the brief's own headline single columns
# ---------------------------------------------------------------------------

def audit_ctqw_and_vc(frozen_targets):
    print("\n" + "=" * 78)
    print("PART 1 -- CTQW solo and V_C alone: cv_auc vs auc_directional, frozen 20")
    print("=" * 78)
    rows = []
    for t in frozen_targets:
        try:
            d = t0249.target_rows(t)
        except Exception as exc:  # noqa: BLE001
            print(f"  {t}: SKIP (target_rows) {type(exc).__name__}: {exc}")
            continue
        if d is None:
            continue
        y = d["y"]
        x_ctqw = d["x_ctqw"]  # already z-scored, seed-excluded -- AUC invariant to the scaling
        cv_ctqw = float(cv_auc(x_ctqw.reshape(-1, 1), y))
        raw_ctqw = float(auc_directional(x_ctqw, y))

        try:
            terms = potential_term_vectors(d["coords"], d["bfactors"], d["cut"])
        except Exception as exc:  # noqa: BLE001
            print(f"  {t}: SKIP (V_C) {type(exc).__name__}: {exc}")
            continue
        m = np.ones(len(d["coords"]), dtype=bool)
        m[d["seed"]] = False
        vc = terms["V_C"][m]
        cv_vc = float(cv_auc(vc.reshape(-1, 1), y))
        raw_vc = float(auc_directional(vc, y))

        rows.append(dict(target=t, cv_ctqw=cv_ctqw, raw_ctqw=raw_ctqw,
                          cv_vc=cv_vc, raw_vc=raw_vc))
        print(f"  {t:<22} ctqw cv={cv_ctqw:.3f} raw={raw_ctqw:.3f}   "
              f"V_C cv={cv_vc:.3f} raw={raw_vc:.3f}")

    def _median(key):
        return float(np.median([r[key] for r in rows]))

    print(f"\n  medians (n={len(rows)}):")
    print(f"    CTQW   cv_auc={_median('cv_ctqw'):.4f}  auc_directional={_median('raw_ctqw'):.4f}")
    print(f"    V_C    cv_auc={_median('cv_vc'):.4f}  auc_directional={_median('raw_vc'):.4f}")
    return rows


# ---------------------------------------------------------------------------
# Part 2 -- task0277's 8-feature apo battery: prs_low/degree/SASA and the rest
# ---------------------------------------------------------------------------

def audit_task0277_features(frozen_targets):
    print("\n" + "=" * 78)
    print("PART 2 -- task0277's apo feature battery: cv_auc (already published) vs")
    print("auc_directional (recomputed here from the identical arrays)")
    print("=" * 78)
    stored = json.loads((OUT.parent / "0277_apo_holo_ceiling_sweep"
                          / "per_feature_auc_apo_holo.json").read_text())
    per_feature_raw = {f: [] for f in t0277.FEATURES}
    per_feature_cv = {f: [] for f in t0277.FEATURES}
    for t in frozen_targets:
        try:
            r = t0277.common_apo_holo_rows(t)
        except Exception as exc:  # noqa: BLE001
            print(f"  {t}: SKIP {type(exc).__name__}: {exc}")
            continue
        if r is None:
            continue
        apo_idx, m, seed_local, cut, y = r["apo_idx"], r["m"], r["seed_local"], r["cut"], r["y"]
        coords_apo, bfac_apo = r["apo"].coords[apo_idx], r["apo"].bfactors[apo_idx]
        resnames_apo = [r["apo"].resnames[i] for i in apo_idx]
        try:
            feats = t0277.compute_features(coords_apo, bfac_apo, resnames_apo, seed_local, cut)
        except Exception as exc:  # noqa: BLE001
            print(f"  {t}: SKIP (compute_features) {type(exc).__name__}: {exc}")
            continue
        # SASA: ligand-present, keyed by (chain, resnum) -- same convention
        # task0277's own main() uses; skip per-target on any fetch failure
        # rather than silently zero-filling.
        try:
            sasa_map = t0277.sasa_by_key(r["cfg"]["apo_pdb"])
            chids_apo = np.asarray(r["apo"].chain_ids)[apo_idx]
            resn_apo = np.asarray(r["apo"].resnums)[apo_idx]
            sasa = np.array([sasa_map.get((c, int(rn)), np.nan) for c, rn in zip(chids_apo, resn_apo)])
            feats["SASA"] = sasa
        except Exception:  # noqa: BLE001
            feats["SASA"] = None

        if t not in stored:
            continue
        for f in t0277.FEATURES:
            vec = feats.get(f)
            if vec is None:
                continue
            x = vec[m]
            valid = np.isfinite(x)
            if valid.sum() < 3 or y[valid].sum() < 1 or y[valid].sum() == valid.sum():
                continue
            raw = float(auc_directional(x[valid], y[valid]))
            per_feature_raw[f].append(raw)
            per_feature_cv[f].append(stored[t]["apo"][f])

    print(f"\n  {'feature':<24}{'n':>4}{'cv_auc median':>16}{'raw median':>14}{'raw min':>10}  flag")
    table = {}
    for f in t0277.FEATURES:
        n = len(per_feature_raw[f])
        if n == 0:
            print(f"  {f:<24}{'--':>4}  no usable rows")
            continue
        cvm = float(np.median(per_feature_cv[f]))
        rawm = float(np.median(per_feature_raw[f]))
        rawmin = float(np.min(per_feature_raw[f]))
        flag = "BELOW 0.5 (anti-correlated)" if rawm < 0.5 else ""
        table[f] = dict(n=n, cv_auc_median=cvm, raw_median=rawm, raw_min=rawmin,
                         raw_all=per_feature_raw[f])
        print(f"  {f:<24}{n:>4}{cvm:>16.4f}{rawm:>14.4f}{rawmin:>10.4f}  {flag}")
    return table


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    new_cand = yaml.safe_load(FROZEN_CONFIG.read_text())["targets"]
    t0242.CAND = new_cand
    frozen_targets = [t for t in new_cand.keys() if t in CM]
    assert len(frozen_targets) == 20, f"expected 20, got {len(frozen_targets)}"

    mechanism = demonstrate_mechanism()
    ctqw_vc = audit_ctqw_and_vc(frozen_targets)
    features_0277 = audit_task0277_features(frozen_targets)

    print("\n" + "=" * 78)
    print("SUMMARY -- every value below < 0.5 raw was previously quoted only as cv_auc")
    print("=" * 78)
    for f, d in features_0277.items():
        if d["raw_median"] < 0.5:
            print(f"  {f}: cv_auc={d['cv_auc_median']:.3f} (looked like weak-positive signal) "
                  f"-> raw_directional={d['raw_median']:.3f} (median target is ANTI-correlated)")

    out = {
        "mechanism_demo": mechanism,
        "ctqw_and_vc_per_target": ctqw_vc,
        "task0277_features": features_0277,
    }
    (OUT / "auc_metric_audit.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwritten: {OUT / 'auc_metric_audit.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
