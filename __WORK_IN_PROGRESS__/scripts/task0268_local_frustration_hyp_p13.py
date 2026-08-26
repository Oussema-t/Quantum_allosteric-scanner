"""TASK-0268 -- local energetic frustration, the direct test of [[HYP-P13]].

**Citations verified live before implementing** (see `allostery.
frustration`'s own module docstring for the full record): Jenik et al.
2012, *Nucleic Acids Research* 40:W348-W351, doi:10.1093/nar/gks447
(Frustratometer formalism); Miyazawa & Jernigan 1996, *J Mol Biol*
256:623-644, doi:10.1006/jmbi.1996.0114 (pairwise contact potential,
matrix sourced from AAindex accession MIYS960101, not hand-recalled).

**Installability checked before committing effort**: the real PyPI
`frustratometer` package (Carlos Bueno, Rice, direct lineage of the
cited paper) resolves and its core deps install, but its own `numba`->
`llvmlite` dependency fails to build a wheel -- no system LLVM toolchain
present (`llvm-config` absent, no homebrew `llvm@*` keg; confirmed
directly, not assumed). Installing LLVM system-wide judged out of this
task's own scope (an environment change, not a Python fix). A from-
scratch port of the single-residue mutational-frustration formalism was
built instead (`allostery/frustration.py`), following this project's
own established precedent for exactly this situation
([[TASK-0229.006]]'s own COREX/EAM build).

**Pre-registered prediction, written before a single frustration number
was computed (this task's own Constraint):**

    HYP-P13 predicts frustration should be ELEVATED at true pocket
    residues relative to the rest of the structure, and MORE SO on the
    genuinely-cryptic targets ([[TASK-0254]] Part B) than on the
    already-open ones -- a site whose native packing is already close to
    optimal has nothing left to relieve by a conformational shift; a
    site that IS a locus of high native frustration has real strain a
    ligand-induced (or intrinsic) population shift could relieve.
    Operationalised exactly as [[TASK-0266]]'s own SASA-control template:
    frustration enters as a 5th Shapley/added-last block (geometry /
    fpocket / CTQW / SASA / frustration -- SASA already validated as a
    real, distinct block by TASK-0266, kept in the model rather than
    dropped, since it is this project's own established burial control);
    added-last value stratified by crypticity; TASK-0261's exact
    cluster-level permutation for significance, not a row-level test.

    Falsification, stated now: if frustration's own added-last value is
    NOT higher on cryptic targets than open ones, or is not distinguishable
    from zero either way, HYP-P13's own frustration prediction is not
    supported by this test -- reported with the same prominence as a
    positive would get, per this task's own Constraint.

Reuses, does not re-derive: `task0242_two_stage_dryrun.prep`/`CAND`,
`task0249_composite_dumb_baseline.target_rows`, `task0254_fpocket_
variance_and_crypticity`'s own `cv_auc`/`build_blocks`/`crypticity`/`z`,
`task0257_r2_sasa_burial_vs_degree.per_residue_sasa`, `task0261_cluster_
robust_stats`'s exact cluster-permutation machinery, and the generalised
n-block Shapley routine ([[TASK-0260]]/[[TASK-0266]]'s own established
pattern, rewritten locally per that pattern's own precedent rather than
imported cross-task).
"""
from __future__ import annotations

import itertools
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import prody
import yaml

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

prody.confProDy(verbosity="none")

import task0242_two_stage_dryrun as t0242  # noqa: E402
import task0249_composite_dumb_baseline as t0249  # noqa: E402
import task0254_fpocket_variance_and_crypticity as t0254  # noqa: E402
from allostery.frustration import single_residue_frustration  # noqa: E402
from task0257_r2_sasa_burial_vs_degree import per_residue_sasa  # noqa: E402
from task0261_cluster_robust_stats import (  # noqa: E402
    CM, cluster_permutation_two_group, cluster_sign_flip_test,
)

OUT = _ROOT / "results/tasks/0268_local_frustration_hyp_p13"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
BLOCKS5 = ["geometry", "fpocket", "sasa", "ctqw", "frustration"]
BASELINE_3BLOCK = _ROOT / "results/tasks/0254_fpocket_variance_and_crypticity/part_a_shapley_attribution.json"


def shapley_attribution_n(feat: dict, y: np.ndarray, blocks: list[str]) -> dict:
    """Exact Shapley over `blocks`, reusing `t0254.cv_auc` unmodified --
    the same routine TASK-0260/TASK-0266 already established; rewritten
    locally per that pattern's own precedent. Returns Shapley share AND
    added-last for every block."""
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


def _resnames_for(cfg: dict, apo_chains) -> dict:
    """(chain, resnum) -> 3-letter resname, real structure, matching
    `apo.resnums`/`apo.chain_ids` ordering by key not position."""
    st = prody.parsePDB(cfg["apo_pdb"], compressed=False).select(
        "protein and (" + " or ".join(f"chain {c}" for c in apo_chains) + ")"
    )
    out = {}
    for res in st.getHierView().iterResidues():
        out[(str(res.getChid()), int(res.getResnum()))] = res.getResname()
    return out


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

    print("### Computing real per-residue frustration + SASA + 5-block Shapley ###")
    attribution = {}
    crypt = {}
    frustration_stats = {}
    for t, d in data.items():
        cfg, apo, seed2, _pocket2 = t0242.prep(t)
        apo_chains = cfg.get("apo_chains") or cfg.get("chains") or ["A"]

        sasa = per_residue_sasa(cfg, apo)
        if np.isnan(sasa).any():
            sasa = np.where(np.isnan(sasa), np.nanmedian(sasa), sasa)

        resname_by_key = _resnames_for(cfg, apo_chains)
        chain_ids = np.asarray(apo.chain_ids)
        resnames = [resname_by_key.get((str(chain_ids[i]), int(apo.resnums[i])), "XXX")
                    for i in range(len(apo.resnums))]
        frust, n_contacts = single_residue_frustration(apo.coords, resnames)
        n_nan_frust = int(np.isnan(frust).sum())
        if n_nan_frust:
            frust = np.where(np.isnan(frust), np.nanmedian(frust), frust)
        frustration_stats[t] = {
            "n_nan": n_nan_frust, "mean_n_contacts": float(np.mean(n_contacts)),
            "frac_highly_frustrated": float((frust > 0.78).mean()),
            "frac_minimally_frustrated": float((frust < -1.0).mean()),
        }

        seed = d["seed"]
        m = np.ones(len(d["coords"]), dtype=bool)
        m[seed] = False

        blocks = t0254.build_blocks(t, d)
        blocks["sasa"] = t0254.z(sasa)[m].reshape(-1, 1)
        blocks["frustration"] = t0254.z(frust)[m].reshape(-1, 1)
        y = d["y"]
        result = shapley_attribution_n(blocks, y, BLOCKS5)
        attribution[t] = result
        crypt[t] = t0254.crypticity(d)
        sh, al = result["shapley"], result["added_last"]
        print(f"{t:24s} frust_hi={100*frustration_stats[t]['frac_highly_frustrated']:4.0f}%  "
              f"frustration={100*sh['frustration']:+5.1f}%  frust_added_last={100*al['frustration']:+5.1f}%  "
              f"ctqw={100*sh['ctqw']:+5.1f}%  unexplained={100*result['unexplained']:5.1f}%  "
              f"crypticity={100*crypt[t]['fraction_open']:.0f}%")

    (OUT / "shapley_5block.json").write_text(json.dumps(attribution, indent=1))
    (OUT / "crypticity.json").write_text(json.dumps(crypt, indent=1))
    (OUT / "frustration_stats.json").write_text(json.dumps(frustration_stats, indent=1))

    n = len(attribution)
    print(f"\n=== n={n} ===")
    for b in BLOCKS5:
        shares = [attribution[t]["shapley"][b] for t in attribution]
        al = [attribution[t]["added_last"][b] for t in attribution]
        print(f"  {b:<12} Shapley median {100*np.median(shares):+.1f}%  "
              f"added-last median {100*np.median(al):+.1f}%")

    unexs5 = [a["unexplained"] for a in attribution.values()]
    unexs3 = [baseline3[t]["unexplained"] for t in attribution if t in baseline3]
    print(f"\nunexplained: 3-block (geom/fpocket/ctqw) median {100*np.median(unexs3):.1f}% "
          f"-> 5-block (+SASA+frustration) median {100*np.median(unexs5):.1f}%")

    print("\n### Cluster-robust significance (TASK-0261's exact permutation) ###")
    frust_added_last = {t: attribution[t]["added_last"]["frustration"] for t in attribution}
    frust_shapley = {t: attribution[t]["shapley"]["frustration"] for t in attribution}
    r_frust_al = cluster_sign_flip_test(frust_added_last)
    r_frust_sh = cluster_sign_flip_test(frust_shapley)
    print(f"frustration added-last (own marginal): median={100*r_frust_al['median']:+.2f}%  "
          f"n_clusters={r_frust_al['n_clusters']}  cluster-p={r_frust_al['p_value']:.4f}")
    print(f"frustration Shapley share:              median={100*r_frust_sh['median']:+.2f}%  "
          f"n_clusters={r_frust_sh['n_clusters']}  cluster-p={r_frust_sh['p_value']:.4f}")

    print("\n### Crypticity-stratified breakdown (TASK-0260/0266's own straddling-cluster handling) ###")
    straddling = {c for c in set(CM.values())
                  if len({crypt[t]["already_open"] for t in attribution if CM.get(t) == c}) > 1}
    excluded = [t for t in attribution if CM.get(t) in straddling]
    if excluded:
        print(f"Straddling cluster(s) excluded from crypticity stratification only: {excluded}")
    open_t = [t for t in attribution if crypt[t]["already_open"] and CM.get(t) not in straddling]
    cryptic_t = [t for t in attribution if crypt[t]["already_open"] is False and CM.get(t) not in straddling]
    print(f"n_open={len(open_t)} n_cryptic={len(cryptic_t)}")

    def stratify(values: dict, label: str):
        open_v = {t: values[t] for t in open_t if t in values}
        cryptic_v = {t: values[t] for t in cryptic_t if t in values}
        r = cluster_permutation_two_group(cryptic_v, open_v, alternative="greater")
        print(f"{label:<36} cryptic median {100*np.median(list(cryptic_v.values())):+.2f}%  "
              f"open median {100*np.median(list(open_v.values())):+.2f}%  "
              f"cluster-perm p(cryptic>open)={r['p_value']:.4f} "
              f"(n_clusters_cryptic={r['n_clusters_a']}, n_clusters_open={r['n_clusters_b']})")
        return r

    r1 = stratify(frust_shapley, "frustration Shapley share")
    r2 = stratify(frust_added_last, "frustration added-last")

    frac_hi_by_target = {t: frustration_stats[t]["frac_highly_frustrated"] for t in attribution}
    r3 = stratify(frac_hi_by_target, "frac. residues highly frustrated (z>0.78)")

    (OUT / "cluster_robust_results.json").write_text(json.dumps({
        "frust_added_last_overall": r_frust_al, "frust_shapley_overall": r_frust_sh,
        "strat_frust_shapley": r1, "strat_frust_added_last": r2, "strat_frac_highly_frustrated": r3,
    }, indent=1, default=str))

    print("\n### Verdict on HYP-P13's own pre-registered prediction ###")
    al_cryptic = np.median([frust_added_last[t] for t in cryptic_t if t in frust_added_last])
    al_open = np.median([frust_added_last[t] for t in open_t if t in frust_added_last])
    direction_holds = al_cryptic > al_open
    print(f"frustration added-last: cryptic median {100*al_cryptic:+.2f}%  vs  open median {100*al_open:+.2f}%")
    print("Direction predicted by HYP-P13 (cryptic > open):", "HOLDS" if direction_holds else "DOES NOT HOLD")
    print(f"Cluster-permutation p (cryptic>open, added-last): {r2['p_value']:.4f}")
    print(f"Overall frustration added-last distinguishable from zero: cluster-p={r_frust_al['p_value']:.4f}")

    print(f"\nWrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
