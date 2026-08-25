#!/usr/bin/env python3
"""TASK-0257 Acceptance item 3 -- R2 (SASA replacing `degree` as the burial
proxy inside `potentials.V_R`) improved the label-free objective on 11/14
targets ([[task0257_r2_sasa_burial_vs_degree.py]]), so per the task's own
Acceptance ("for any rung that improves the objective: re-run [[TASK-0254]]'s
Shapley attribution with fpocket in the stack, and report CTQW's marginal
when added last") this re-runs that check with a SASA-based H_new.

Reuses, does not re-derive:
  - [[TASK-0254]]'s own `build_blocks`/`shapley_attribution`/target set
    (`task0254_fpocket_variance_and_crypticity`, imported) -- only the
    "ctqw" block's own values are recomputed, geometry/fpocket unchanged.
  - `task0249_composite_dumb_baseline.target_rows` (imported, unchanged)
    for y/x_fpocket/coords/seed/cut/resn per target.
  - `task0242_two_stage_dryrun.prep` (imported, unchanged) to get the
    `apo`/`cfg` objects `target_rows` itself uses internally but does not
    return, needed here for the SASA fetch.
  - `task0257_r2_sasa_burial_vs_degree.per_residue_sasa` (imported,
    unchanged) -- the same BioPython `ShrakeRupley` SASA computation R2's
    own B-factor check used, reused verbatim, not a second implementation.
  - `allostery.potentials.V_B/V_T/V_R/V_C/V_M/gnm_context` and
    `allostery.hamiltonians.normalised_laplacian_alpha` -- `build_H_new`'s
    own five terms, called directly (not through `build_H_new` itself,
    which does not expose a burial-proxy override) with `V_R`'s own
    `context["degree"]` entry replaced by real SASA before the call. `V_R`
    z-scores whatever array it is given internally (`potentials._zscore`),
    so raw SASA values are valid input, matching how it already treats raw
    `degree`.

Baseline to compare against, reproduced directly from [[TASK-0254]]'s own
on-disk `part_a_shapley_attribution.json` (not re-typed from a citation):
CTQW's sequential marginal when added last (after geometry+fpocket, either
order -- identical by construction) has median -0.0006 (~-0.1%), Wilcoxon
signed-rank vs. 0 p=0.5016, n=20.

Run: ../.venv/bin/python3 scripts/task0257_r2_shapley_rerun.py
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import yaml
from scipy.stats import wilcoxon

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import task0242_two_stage_dryrun as t0242  # noqa: E402
import task0249_composite_dumb_baseline as t0249  # noqa: E402
import task0254_fpocket_variance_and_crypticity as t0254  # noqa: E402
from task0257_r2_sasa_burial_vs_degree import per_residue_sasa  # noqa: E402
from allostery.hamiltonians import normalised_laplacian_alpha  # noqa: E402
from allostery.potentials import V_B, V_T, V_R, V_C, V_M as _VM, gnm_context  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402

OUT = _ROOT / "results/tasks/0257_r2_shapley_rerun"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"

# build_H_new's own defaults (hamiltonians.py:293-299), reused unchanged --
# only the burial-proxy input to V_R differs in this script.
LAM_B, LAM_T, LAM_R, LAM_C, LAM_M = 0.08, 0.16, 0.08, 0.04, 0.04
ALPHA = 0.3
TERMINAL_FRACTION = 0.05
N_LOW_MODES = 10


def build_H_sasa(coords: np.ndarray, bfactors: np.ndarray, sasa: np.ndarray, cutoff: float) -> np.ndarray:
    """`hamiltonians.build_H_new`'s own body, reproduced term-for-term
    (same formula, same default lam_* weights), with `V_R`'s own
    `context["degree"]` entry replaced by real per-residue SASA before the
    call -- the only change from the original."""
    ctx = gnm_context(coords, cutoff)
    ctx_sasa = dict(ctx)
    ctx_sasa["degree"] = sasa  # V_R z-scores this internally; raw SASA is valid input

    L = normalised_laplacian_alpha(coords, cutoff=cutoff, alpha=ALPHA)
    H = (
        L
        + LAM_B * V_B(bfactors)
        + LAM_T * V_T(len(coords), TERMINAL_FRACTION)
        + LAM_R * V_R(coords, cutoff=cutoff, context=ctx_sasa)
        + LAM_C * V_C(coords, cutoff=cutoff, context=ctx)
        + LAM_M * _VM(coords, cutoff=cutoff, n_modes=N_LOW_MODES, context=ctx)
    )
    return H


def z(v):
    v = np.asarray(v, float)
    s = v.std()
    return (v - v.mean()) / (s if s > 1e-12 else 1.0)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    new_cand = yaml.safe_load(FROZEN_CONFIG.read_text())["targets"]
    t0242.CAND = new_cand
    t0249.t0242.CAND = new_cand  # t0249 imports t0242 itself; same module-global swap
    frozen_targets = list(new_cand.keys())

    attribution = {}
    for t in frozen_targets:
        try:
            d = t0249.target_rows(t)
        except Exception as exc:  # noqa: BLE001
            print(f"{t}: FAILED target_rows: {exc!r}")
            continue
        if d is None or d["n_pocket"] < 3:
            print(f"{t}: SKIP (fpocket failure, empty seed, or too few positives)")
            continue

        cfg, apo, seed2, _pocket2 = t0242.prep(t)
        sasa = per_residue_sasa(cfg, apo)
        if np.isnan(sasa).any():
            n_nan = int(np.isnan(sasa).sum())
            print(f"{t}: {n_nan}/{len(sasa)} residues unmapped for SASA -- filling with median")
            sasa = np.where(np.isnan(sasa), np.nanmedian(sasa), sasa)

        H_sasa = build_H_sasa(d["coords"], d["bfactors"], sasa, d["cut"])
        ctqw_sasa = time_averaged_ctqw_converged(H_sasa, source=d["seed"], coherent=False)

        n = len(d["coords"])
        m = np.ones(n, dtype=bool)
        m[d["seed"]] = False
        x_ctqw_sasa = z(ctqw_sasa)[m]

        feat = t0254.build_blocks(t, d)
        feat["ctqw"] = x_ctqw_sasa.reshape(-1, 1)
        y = d["y"]
        result = t0254.shapley_attribution(feat, y)
        attribution[t] = result
        sh = result["shapley"]
        print(f"{t:24s} geom={100*sh['geometry']:+5.1f}%  fpocket={100*sh['fpocket']:+5.1f}%  "
              f"ctqw(SASA)={100*sh['ctqw']:+5.1f}%  added-last={100*result['seq_geom_first']['ctqw']:+5.1f}%  "
              f"unexplained={100*result['unexplained']:5.1f}%  (full AUC={result['full_auc']:.3f})")

    (OUT / "part_a_shapley_sasa.json").write_text(json.dumps(attribution, indent=1))
    print(f"\nwrote {OUT / 'part_a_shapley_sasa.json'}")

    added_last_sasa = [a["seq_geom_first"]["ctqw"] for a in attribution.values()]
    ctqw_share_sasa = [a["shapley"]["ctqw"] for a in attribution.values()]

    baseline_path = _ROOT / "results/tasks/0254_fpocket_variance_and_crypticity/part_a_shapley_attribution.json"
    baseline = json.loads(baseline_path.read_text())
    added_last_base = [baseline[t]["seq_geom_first"]["ctqw"] for t in attribution if t in baseline]
    ctqw_share_base = [baseline[t]["shapley"]["ctqw"] for t in attribution if t in baseline]

    print(f"\n=== CTQW's marginal when added last (after geometry+fpocket), n={len(attribution)} ===")
    print(f"  baseline (degree-based H_new):  median={np.median(added_last_base):+.4f}  "
          f"mean={np.mean(added_last_base):+.4f}")
    w_base = wilcoxon(added_last_base)
    print(f"    Wilcoxon vs 0: statistic={w_base.statistic:.1f} p={w_base.pvalue:.4f}")
    print(f"  R2 (SASA-based H_new):          median={np.median(added_last_sasa):+.4f}  "
          f"mean={np.mean(added_last_sasa):+.4f}")
    w_sasa = wilcoxon(added_last_sasa)
    print(f"    Wilcoxon vs 0: statistic={w_sasa.statistic:.1f} p={w_sasa.pvalue:.4f}")
    w_paired = wilcoxon(added_last_sasa, added_last_base)
    print(f"  paired (SASA - degree) Wilcoxon: statistic={w_paired.statistic:.1f} p={w_paired.pvalue:.4f}")

    print(f"\n=== CTQW's own Shapley share (not just added-last) ===")
    print(f"  baseline: median={100*np.median(ctqw_share_base):+.1f}%  range=[{100*min(ctqw_share_base):+.0f}%,{100*max(ctqw_share_base):+.0f}%]")
    print(f"  R2:       median={100*np.median(ctqw_share_sasa):+.1f}%  range=[{100*min(ctqw_share_sasa):+.0f}%,{100*max(ctqw_share_sasa):+.0f}%]")

    n_improved = sum(1 for t in attribution if attribution[t]["seq_geom_first"]["ctqw"] > baseline[t]["seq_geom_first"]["ctqw"])
    print(f"\nCTQW's added-last marginal improves (SASA > degree) on {n_improved}/{len(attribution)} targets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
