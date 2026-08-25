"""TASK-0263 -- was the physics right and the propagator wrong? Score
`build_H_new`'s five potential terms (V_B, V_T, V_R, V_C, V_M) directly as
per-residue predictors, on the same frozen set/protocol/cluster-robust
significance this line of work has already established, rather than only
ever seeing them mixed into a Hamiltonian a CTQW then propagates over.

Extraction route (stated per this task's own instruction: "say which route
you took"): `potentials.V_B/V_T/V_R/V_C/V_M` are already public, individually
callable functions -- each returns an (N,N) diagonal matrix (TASK-0121's own
per-term z-scoring), so `np.diag(V_X(...))` is the per-residue vector
directly, no re-derivation needed. Same route [[TASK-0257]]'s own
`task0257_r2_shapley_rerun.py` already used and validated (imports the same
five functions + `gnm_context` verbatim) -- confirmed by reading that
script before writing this one, not assumed.

Reuses, does not re-derive:
  - `task0249_composite_dumb_baseline.target_rows` for the frozen 22-target
    set's (n=20 usable) per-target coords/bfactors/seed/cutoff/CTQW/label
    rows.
  - `task0254_fpocket_variance_and_crypticity.z`/`cv_auc`/`build_blocks` for
    the geometry/fpocket/CTQW blocks and the exact CV protocol
    ([[TASK-0245]]'s own: 5-fold stratified, 20 repeats, OLS via `lstsq`,
    out-of-fold AUC, seed rows excluded) -- unchanged here, per this task's
    own Scope ("TASK-0254's protocol unchanged").
  - `task0261_cluster_robust_stats.cluster_sign_flip_test`/`CM` for the
    cluster-robust significance (13 clusters: 7 shared-apo pairs + 6
    singletons over the 20-row frozen set) -- not row-level Wilcoxon, per
    this task's own explicit instruction and [[TASK-0261]]'s own finding
    that row-level tests on this set are pseudo-replicated.

Pre-registered before the first number was seen (this task's own filing,
written before this script ran): potential-term block as a fourth Shapley
block alongside geometry/fpocket/CTQW; the decision statistic is the terms
block's own ADDED-LAST marginal (v(all 4) - v(geometry,fpocket,ctqw)), not
the averaged Shapley value alone (also reported, for symmetry with
[[TASK-0254]]'s own 3-block report) -- and the mirror question, CTQW's own
added-last marginal once the terms it was built from are already in the
model (v(all 4) - v(geometry,fpocket,terms)).
"""
from __future__ import annotations

import itertools
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import yaml

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import task0242_two_stage_dryrun as t0242  # noqa: E402
import task0249_composite_dumb_baseline as t0249  # noqa: E402
from task0254_fpocket_variance_and_crypticity import build_blocks, cv_auc, z  # noqa: E402
from task0261_cluster_robust_stats import CM, cluster_sign_flip_test  # noqa: E402
from allostery.potentials import V_B, V_T, V_R, V_C, V_M as _VM, gnm_context  # noqa: E402

OUT = _ROOT / "results/tasks/0263_potential_terms_direct_predictors"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
TERMINAL_FRACTION = 0.05
N_LOW_MODES = 10
TERM_NAMES = ["V_B", "V_T", "V_R", "V_C", "V_M"]
BLOCKS4 = ["geometry", "fpocket", "ctqw", "terms"]


def potential_term_vectors(coords: np.ndarray, bfactors: np.ndarray, cut: float) -> dict:
    """The five per-residue potential-term vectors, `build_H_new`'s own
    defaults (`terminal_fraction=0.05`, `n_low_modes=10`), same `gnm_context`
    threaded through V_R/V_C/V_M exactly as `build_H_new` itself does (not a
    freshly-tuned or re-derived construction)."""
    ctx = gnm_context(coords, cut)
    n = len(coords)
    return {
        "V_B": np.diag(V_B(bfactors)),
        "V_T": np.diag(V_T(n, TERMINAL_FRACTION)),
        "V_R": np.diag(V_R(coords, cutoff=cut, context=ctx)),
        "V_C": np.diag(V_C(coords, cutoff=cut, context=ctx)),
        "V_M": np.diag(_VM(coords, cutoff=cut, n_modes=N_LOW_MODES, context=ctx)),
    }


def shapley4(feat: dict, y: np.ndarray) -> dict:
    """Exact Shapley value over 4 blocks (4! = 24 permutations, still cheap
    to brute-force). Also returns every subset's own CV AUC (needed for the
    two added-last decision statistics) and the two added-last marginals
    this task's own filing pre-registers as the headline numbers."""
    cache: dict = {}

    def value(subset: tuple) -> float:
        key = tuple(sorted(subset))
        if key in cache:
            return cache[key]
        if not key:
            v = 0.0
        else:
            X = np.column_stack([feat[b] for b in key])
            v = (cv_auc(X, y) - 0.5) / 0.5
        cache[key] = v
        return v

    shap = {b: [] for b in BLOCKS4}
    for perm in itertools.permutations(BLOCKS4):
        prefix: list = []
        for b in perm:
            before = value(tuple(prefix))
            prefix = prefix + [b]
            after = value(tuple(prefix))
            shap[b].append(after - before)
    shapley = {b: float(np.mean(shap[b])) for b in BLOCKS4}

    full_share = value(tuple(BLOCKS4))
    terms_added_last = full_share - value(("ctqw", "fpocket", "geometry"))
    ctqw_added_last = full_share - value(("fpocket", "geometry", "terms"))
    return dict(
        shapley=shapley, full_share=full_share, full_auc=0.5 + 0.5 * full_share,
        terms_added_last=terms_added_last, ctqw_added_last=ctqw_added_last,
        subset_aucs={",".join(k) if k else "(none)": 0.5 + 0.5 * v for k, v in cache.items()},
    )


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
        print(f"{t}: n_pocket={d['n_pocket']} n_residues={len(d['y'])}")

    print(f"\n{len(data)}/{len(frozen_targets)} usable\n")

    # --- per-term CV AUC + terms-as-a-block, per target ---
    print("### Per-term CV AUC (n=20) ###")
    per_term = {}
    terms_block_auc = {}
    ctqw_auc = {}
    for t, d in data.items():
        n = len(d["coords"])
        seed = d["seed"]
        m = np.ones(n, dtype=bool)
        m[seed] = False
        tv = potential_term_vectors(d["coords"], d["bfactors"], d["cut"])
        y = d["y"]
        row = {}
        term_mat = []
        for name in TERM_NAMES:
            vec = z(tv[name][m])
            a = cv_auc(vec.reshape(-1, 1), y)
            row[name] = a
            term_mat.append(vec)
        per_term[t] = row
        terms_X = np.column_stack(term_mat)
        terms_block_auc[t] = cv_auc(terms_X, y)
        ctqw_auc[t] = cv_auc(d["x_ctqw"].reshape(-1, 1), y)
        print(f"{t:24s} " + " ".join(f"{k}={row[k]:.3f}" for k in TERM_NAMES) +
              f"  | terms_block={terms_block_auc[t]:.3f}  ctqw={ctqw_auc[t]:.3f}")

    (OUT / "per_term_auc.json").write_text(json.dumps(per_term, indent=1))
    (OUT / "terms_block_vs_ctqw_auc.json").write_text(json.dumps(
        {"terms_block": terms_block_auc, "ctqw": ctqw_auc}, indent=1))

    best_term_per_target = {t: max(row, key=row.get) for t, row in per_term.items()}
    print("\nBest single term per target:", {t: (v, per_term[t][v]) for t, v in best_term_per_target.items()})

    # --- headline: terms-block vs CTQW, cluster-robust ---
    print("\n### Headline: terms-block vs CTQW, cluster-robust (TASK-0261's method) ###")
    diffs = {t: terms_block_auc[t] - ctqw_auc[t] for t in data if t in CM}
    n_dropped = len(data) - len(diffs)
    if n_dropped:
        print(f"(note: {n_dropped} target(s) not in TASK-0261's own 20-row cluster map, excluded from this test)")
    cluster_result = cluster_sign_flip_test(diffs)
    print(f"terms_block - ctqw: median diff={cluster_result['median']:+.4f}, "
          f"n_rows={cluster_result['n_rows']}, n_clusters={cluster_result['n_clusters']}, "
          f"p={cluster_result['p_value']:.4f}")
    (OUT / "headline_cluster_robust.json").write_text(json.dumps(
        {"diffs": diffs, "cluster_test": cluster_result}, indent=1))

    # --- 4-block Shapley attribution, added-last decision statistics ---
    print("\n### Four-block Shapley (geometry/fpocket/ctqw/terms) ###")
    attribution = {}
    for t, d in data.items():
        feat3 = build_blocks(t, d)
        n = len(d["coords"])
        seed = d["seed"]
        m = np.ones(n, dtype=bool)
        m[seed] = False
        tv = potential_term_vectors(d["coords"], d["bfactors"], d["cut"])
        terms_X = np.column_stack([z(tv[name][m]) for name in TERM_NAMES])
        feat = dict(feat3, terms=terms_X)
        result = shapley4(feat, d["y"])
        attribution[t] = result
        sh = result["shapley"]
        print(f"{t:24s} geom={100*sh['geometry']:+5.1f}% fpocket={100*sh['fpocket']:+5.1f}% "
              f"ctqw={100*sh['ctqw']:+5.1f}% terms={100*sh['terms']:+5.1f}%  "
              f"| terms_added_last={100*result['terms_added_last']:+5.1f}% "
              f"ctqw_added_last={100*result['ctqw_added_last']:+5.1f}%  (full AUC={result['full_auc']:.3f})")

    (OUT / "four_block_shapley.json").write_text(json.dumps(attribution, indent=1))

    terms_al = [a["terms_added_last"] for a in attribution.values()]
    ctqw_al = [a["ctqw_added_last"] for a in attribution.values()]
    print(f"\nterms added-last:  {100*min(terms_al):+.0f} to {100*max(terms_al):+.0f}%  "
          f"(median {100*np.median(terms_al):+.0f}%)")
    print(f"ctqw added-last:   {100*min(ctqw_al):+.0f} to {100*max(ctqw_al):+.0f}%  "
          f"(median {100*np.median(ctqw_al):+.0f}%)")

    ctqw_al_map = {t: a["ctqw_added_last"] for t, a in attribution.items() if t in CM}
    ctqw_al_cluster = cluster_sign_flip_test(ctqw_al_map)
    print(f"\nCTQW added-last, cluster-robust: median={ctqw_al_cluster['median']:+.4f}, "
          f"p={ctqw_al_cluster['p_value']:.4f} (H0: no residual contribution once its own "
          f"potential terms are direct predictors)")
    (OUT / "ctqw_added_last_cluster_robust.json").write_text(json.dumps(ctqw_al_cluster, indent=1))

    print(f"\nWrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
