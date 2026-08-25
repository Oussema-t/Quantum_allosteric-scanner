"""TASK-0266 -- is CTQW's cryptic lean (TASK-0259/TASK-0260: the only block
that leans toward cryptic targets rather than already-open ones) just burial
detection in disguise?

The confound: buried regions are closed, closed regions are cryptic. The
existing geometry block's own burial proxy is `degree_centrality`, but
TASK-0257 R2 established `degree` is a *poor* burial measure (real SASA beats
it against B-factors on 11/14 targets) -- and real SASA is in no block at
all. A score that simply prefers buried residues would produce CTQW's exact
cryptic-lean pattern with no dynamics involved, and nothing controls for it.

Reuses, does not re-derive:
  - `task0249_composite_dumb_baseline.target_rows` / `task0242_two_stage_
    dryrun.prep` for the frozen-set apo structures/seeds/labels (imported).
  - `task0254_fpocket_variance_and_crypticity`'s own `cv_auc`/`build_blocks`/
    `crypticity`/`z` (imported) -- the CV-AUC engine and the pre-registered
    crypticity definition, unchanged.
  - `task0257_r2_sasa_burial_vs_degree.per_residue_sasa` (imported) -- the
    same validated BioPython ShrakeRupley SASA computation R2 already used,
    not a second implementation. Used here as its OWN Shapley block (this
    task's own Scope), not substituted into H_new's own V_R term the way R2
    did -- a different, simpler construction: CTQW is scored exactly as
    TASK-0254's own baseline computed it (degree-based H_new, unchanged).
  - `task0261_cluster_robust_stats.cluster_sign_flip_test`/
    `cluster_permutation_two_group`/`CM` (imported) -- this task's own Scope
    explicitly specifies "TASK-0261's exact cluster-level permutation, not
    row-level Wilcoxon."
  - A generalised n-block exact Shapley routine, written here (not imported
    from `task0254`, whose own `shapley_attribution` hardcodes 3 blocks at
    module level) -- the same pattern already established in
    `task0260_cryptic_predictor_residual.py`'s own `shapley_attribution_4`,
    rewritten locally rather than imported cross-task, and extended here to
    also report added-last for *every* block, not just one (this task's own
    Acceptance: "added-last for every block").
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
import task0254_fpocket_variance_and_crypticity as t0254  # noqa: E402
from task0257_r2_sasa_burial_vs_degree import per_residue_sasa  # noqa: E402
from task0261_cluster_robust_stats import (  # noqa: E402
    CM, cluster_permutation_two_group, cluster_sign_flip_test,
)

OUT = _ROOT / "results/tasks/0266_sasa_burial_control"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
BLOCKS4 = ["geometry", "fpocket", "sasa", "ctqw"]
BASELINE_3BLOCK = _ROOT / "results/tasks/0254_fpocket_variance_and_crypticity/part_a_shapley_attribution.json"


def shapley_attribution_n(feat: dict, y: np.ndarray, blocks: list[str]) -> dict:
    """Exact Shapley over `blocks` (4! = 24 permutations here, cheap),
    reusing `t0254.cv_auc` unmodified. Returns the Shapley share AND the
    added-last (full model minus every-other-block) value for EVERY block,
    not just one -- this task's own Acceptance."""
    cache: dict = {}

    def value(subset: tuple) -> float:
        key = tuple(sorted(subset))
        if key in cache:
            return cache[key]
        if not key:
            v = 0.0
        else:
            X = np.column_stack([feat[b] for b in key])
            v = (t0254.cv_auc(X, y) - 0.5) / 0.5
        cache[key] = v
        return v

    shap = {b: [] for b in blocks}
    for perm in itertools.permutations(blocks):
        prefix: list = []
        for b in perm:
            before = value(tuple(prefix))
            prefix = prefix + [b]
            after = value(tuple(prefix))
            shap[b].append(after - before)
    shapley = {b: float(np.mean(shap[b])) for b in blocks}
    full_share = value(tuple(blocks))
    full_auc = 0.5 + 0.5 * full_share
    added_last = {b: full_share - value(tuple(x for x in blocks if x != b)) for b in blocks}
    return dict(shapley=shapley, added_last=added_last, full_auc=full_auc,
                full_share=full_share, unexplained=1.0 - full_share)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    new_cand = yaml.safe_load(FROZEN_CONFIG.read_text())["targets"]
    t0242.CAND = new_cand
    t0249.t0242.CAND = new_cand

    baseline3 = json.loads(BASELINE_3BLOCK.read_text())
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
    print(f"{len(data)}/{len(frozen_targets)} usable (matches TASK-0249's own n=20 filter)\n")

    print("### Computing real per-residue SASA + 4-block Shapley (geometry/fpocket/SASA/CTQW) ###")
    attribution = {}
    crypt = {}
    for t, d in data.items():
        cfg, apo, seed2, _pocket2 = t0242.prep(t)
        sasa = per_residue_sasa(cfg, apo)
        n_nan = int(np.isnan(sasa).sum())
        if n_nan:
            sasa = np.where(np.isnan(sasa), np.nanmedian(sasa), sasa)

        seed = d["seed"]
        m = np.ones(len(d["coords"]), dtype=bool)
        m[seed] = False

        blocks = t0254.build_blocks(t, d)
        blocks["sasa"] = t0254.z(sasa)[m].reshape(-1, 1)
        y = d["y"]
        result = shapley_attribution_n(blocks, y, BLOCKS4)
        attribution[t] = result
        crypt[t] = t0254.crypticity(d)
        sh, al = result["shapley"], result["added_last"]
        print(f"{t:24s} nan_sasa={n_nan:<3d} geom={100*sh['geometry']:+5.1f}%  fpocket={100*sh['fpocket']:+5.1f}%  "
              f"sasa={100*sh['sasa']:+5.1f}%  ctqw={100*sh['ctqw']:+5.1f}%  "
              f"ctqw_added_last={100*al['ctqw']:+5.1f}%  unexplained={100*result['unexplained']:5.1f}%  "
              f"crypticity={100*crypt[t]['fraction_open']:.0f}%")

    (OUT / "shapley_4block_sasa.json").write_text(json.dumps(attribution, indent=1))
    (OUT / "crypticity.json").write_text(json.dumps(crypt, indent=1))

    n = len(attribution)
    print(f"\n=== n={n} ===")
    for b in BLOCKS4:
        shares = [attribution[t]["shapley"][b] for t in attribution]
        al = [attribution[t]["added_last"][b] for t in attribution]
        print(f"  {b:<10} Shapley median {100*np.median(shares):+.1f}%  "
              f"added-last median {100*np.median(al):+.1f}%")

    unexs4 = [a["unexplained"] for a in attribution.values()]
    unexs3 = [baseline3[t]["unexplained"] for t in attribution if t in baseline3]
    print(f"\nunexplained: 3-block (geom/fpocket/ctqw) median {100*np.median(unexs3):.1f}% "
          f"-> 4-block (+SASA) median {100*np.median(unexs4):.1f}%")

    print("\n### Cluster-robust significance (TASK-0261's exact permutation, 13 clusters) ###")
    ctqw_added_last_4 = {t: attribution[t]["added_last"]["ctqw"] for t in attribution}
    sasa_added_last_4 = {t: attribution[t]["added_last"]["sasa"] for t in attribution}
    ctqw_added_last_3 = {t: baseline3[t]["seq_geom_first"]["ctqw"] for t in attribution if t in baseline3}

    r_ctqw4 = cluster_sign_flip_test(ctqw_added_last_4)
    r_sasa4 = cluster_sign_flip_test(sasa_added_last_4)
    r_ctqw3 = cluster_sign_flip_test(ctqw_added_last_3)
    print(f"CTQW added-last, 3-block (no SASA):  median={100*r_ctqw3['median']:+.2f}%  "
          f"n_clusters={r_ctqw3['n_clusters']}  cluster-p={r_ctqw3['p_value']:.4f}")
    print(f"CTQW added-last, 4-block (with SASA): median={100*r_ctqw4['median']:+.2f}%  "
          f"n_clusters={r_ctqw4['n_clusters']}  cluster-p={r_ctqw4['p_value']:.4f}")
    print(f"SASA added-last (its own marginal):   median={100*r_sasa4['median']:+.2f}%  "
          f"n_clusters={r_sasa4['n_clusters']}  cluster-p={r_sasa4['p_value']:.4f}")

    print("\n### Crypticity-stratified breakdown, with vs. without SASA ###")
    # Crypticity is per-ligand (holo-specific); clustering is per-apo-
    # structure (TASK-0261). These can genuinely conflict when a pair's two
    # ligands straddle the 80% bar on the same apo structure -- found here,
    # not assumed away: TRP_SYNTHASE_F6F (87% open) vs. TRP_SYNTHASE_F19
    # (78%, just under the bar). cluster_permutation_two_group's own
    # assertion correctly refuses to split one cluster across both groups.
    # Excluded from THIS stratified test specifically (both members, not
    # silently assigned to one side) -- kept in every other number above.
    straddling = {c for c in set(CM.values())
                  if len({crypt[t]["already_open"] for t in attribution if CM.get(t) == c}) > 1}
    excluded = [t for t in attribution if CM.get(t) in straddling]
    if excluded:
        print(f"Straddling cluster(s) excluded from crypticity stratification only: "
              f"{excluded} (same apo structure, opposite sides of the 80% bar)")
    open_t = [t for t in attribution if crypt[t]["already_open"] and CM.get(t) not in straddling]
    cryptic_t = [t for t in attribution if crypt[t]["already_open"] is False and CM.get(t) not in straddling]
    print(f"n_open={len(open_t)} n_cryptic={len(cryptic_t)}")

    def stratify(values: dict, label: str):
        open_v = {t: values[t] for t in open_t if t in values}
        cryptic_v = {t: values[t] for t in cryptic_t if t in values}
        r = cluster_permutation_two_group(cryptic_v, open_v, alternative="greater")
        print(f"{label:<32} cryptic median {100*np.median(list(cryptic_v.values())):+.2f}%  "
              f"open median {100*np.median(list(open_v.values())):+.2f}%  "
              f"cluster-perm p(cryptic>open)={r['p_value']:.4f} "
              f"(n_clusters_cryptic={r['n_clusters_a']}, n_clusters_open={r['n_clusters_b']})")
        return r

    ctqw_shapley_3 = {t: baseline3[t]["shapley"]["ctqw"] for t in attribution if t in baseline3}
    ctqw_shapley_4 = {t: attribution[t]["shapley"]["ctqw"] for t in attribution}
    sasa_shapley_4 = {t: attribution[t]["shapley"]["sasa"] for t in attribution}

    r1 = stratify(ctqw_shapley_3, "CTQW Shapley share, no SASA")
    r2 = stratify(ctqw_shapley_4, "CTQW Shapley share, with SASA")
    r3 = stratify(sasa_shapley_4, "SASA's OWN Shapley share")
    r4 = stratify(ctqw_added_last_3, "CTQW added-last, no SASA")
    r5 = stratify(ctqw_added_last_4, "CTQW added-last, with SASA")

    (OUT / "cluster_robust_results.json").write_text(json.dumps({
        "ctqw_added_last_3block": r_ctqw3, "ctqw_added_last_4block": r_ctqw4,
        "sasa_added_last": r_sasa4,
        "strat_ctqw_shapley_no_sasa": r1, "strat_ctqw_shapley_with_sasa": r2,
        "strat_sasa_shapley": r3, "strat_ctqw_added_last_no_sasa": r4,
        "strat_ctqw_added_last_with_sasa": r5,
    }, indent=1, default=str))

    print("\n### Verdict ###")
    print("Does SASA itself lean cryptic (the confound demonstrated directly)?",
          "YES" if np.median(list(sasa_shapley_4.values())) > 0 and
          np.median([sasa_shapley_4[t] for t in cryptic_t if t in sasa_shapley_4]) >
          np.median([sasa_shapley_4[t] for t in open_t if t in sasa_shapley_4]) else "NO")
    ctqw_lean_survives = (np.median([ctqw_added_last_4[t] for t in cryptic_t if t in ctqw_added_last_4]) >
                          np.median([ctqw_added_last_4[t] for t in open_t if t in ctqw_added_last_4]))
    print("Does CTQW's own cryptic lean survive with SASA in the model (added-last)?",
          "SURVIVES (direction held)" if ctqw_lean_survives else "VANISHES/REVERSES")

    print(f"\nWrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
