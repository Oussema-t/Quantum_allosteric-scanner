#!/usr/bin/env python3
"""TASK-0275 -- V_C beats CTQW, and TASK-0263 lumped it. Two questions:

(1) Apo, per-term decomposition: re-run TASK-0254's Shapley with the five
    `build_H_new` potential terms as SEPARATE blocks (8 blocks total:
    geometry, fpocket, ctqw, V_B, V_T, V_R, V_C, V_M) instead of one lumped
    "terms" block. Headline: does CTQW retain any added-last contribution
    once V_C SPECIFICALLY (not the whole lumped block) is already in the
    model?
(2) Apo vs holo, per term: the same terms computed on the HOLO structure
    (ceiling -- "what could this term do with the bound conformation"),
    against the SAME apo-derived pocket label, on the matched common
    apo/holo (chain, resnum) residue set so the two flavours are scored on
    an identical node set. Report the per-term apo->holo gap and test it
    against crypticity (pre-registered: larger gap on cryptic targets).

Timing checked before launching (per this task's own Scope item 1): a
single `cv_auc` call measured at ~0.042s; the full 8-block Shapley for one
flavour needs 2^8=256 distinct subset evaluations/target x 20 targets =
5120 calls =~ 3.5 min, x2 flavours =~ 7 min total -- the reduction to
6 blocks this task's Scope allows for was not needed.

**Leakage discipline** (this task's own table, honoured exactly):
fpocket is EXCLUDED from the holo arm entirely -- a cavity detector run on
a drug-shaped-open holo cavity trivially recovers the label. Every
holo-flavour number is a ceiling, never reported as predictive
performance, and every table column below is labelled by flavour.

Reuses, does not re-derive:
  - `task0242_two_stage_dryrun.prep`/`CAND` (TASK-0243's own frozen-set
    pocket/active-site definition, unchanged).
  - `task0249_composite_dumb_baseline`'s `z`, `degree_centrality`,
    `euclid_from_seed_centroid`, `hop_from_seed`, `build_H_new`,
    `time_averaged_ctqw_converged` -- same primitives, same z-scoring
    convention as every block in this register.
  - `task0254_fpocket_variance_and_crypticity.cv_auc` (TASK-0245's own CV
    protocol, unchanged) and its own crypticity screen
    (`part_b_crypticity.json`, TASK-0254 Part B) for the pre-registered
    prediction test.
  - `task0260_cryptic_predictor_residual.shapley_attribution_4` -- the
    already-generalised n-block exact-Shapley routine this task's own
    Scope names explicitly ("use the n-block routine TASK-0260
    generalised rather than rewriting it"), unmodified.
  - `task0261_cluster_robust_stats.cluster_sign_flip_test`/
    `cluster_permutation_correlation`/`CM` -- 13 clusters, unchanged.
  - `task0263_potential_terms_direct_predictors.potential_term_vectors`
    (already flavour-agnostic: takes raw coords/bfactors/cut, not tied to
    apo) -- reused unchanged for BOTH flavours, not re-derived.
  - `allostery.superpose.align_apo_holo`/`chain_map_from_config` (TASK-0230's
    own apo/holo common-residue-set machinery) for the matched apo/holo
    node set the fair gap comparison needs.

Pre-registered before any holo number was seen (this task's own filing):
the apo->holo gap should correlate with apo crypticity (TASK-0259's own
rho=-0.771 finding) -- larger gap on cryptic targets, near-zero on
already-open ones. If the gap is uniform across crypticity, that
correlation is not made of what TASK-0259 read it as.
"""
from __future__ import annotations

import itertools
import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import yaml

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402

# TASK-0243's own real, verified fix (task0249_composite_dumb_baseline.py's
# own docstring: "NAMPT_NPA1R's own real defect"), reused verbatim -- must
# be applied globally BEFORE any `t0242.prep`/`clean_from_config` call, not
# just this module's own direct `parsePDB` use, since those internally call
# `prody.parsePDB` too (confirmed by TASK-0271's own first run crashing on
# exactly this target before this patch was added there).
_orig_parsePDB = prody.parsePDB


def _parsePDB_all_altloc(*a, **kw):
    kw.setdefault("altloc", "all")
    return _orig_parsePDB(*a, **kw)


prody.parsePDB = _parsePDB_all_altloc

import task0242_two_stage_dryrun as t0242  # noqa: E402
import task0249_composite_dumb_baseline as t0249  # noqa: E402
from task0254_fpocket_variance_and_crypticity import cv_auc, z  # noqa: E402
from task0260_cryptic_predictor_residual import shapley_attribution_4  # noqa: E402
from task0261_cluster_robust_stats import CM, cluster_permutation_correlation, cluster_sign_flip_test  # noqa: E402
from task0263_potential_terms_direct_predictors import TERM_NAMES, potential_term_vectors  # noqa: E402
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import clean_from_config  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.superpose import align_apo_holo, chain_map_from_config  # noqa: E402

OUT = _ROOT / "results/tasks/0275_term_decomposition_apo_holo"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
BLOCKS_APO = ["geometry", "fpocket", "ctqw"] + TERM_NAMES  # 8 blocks
BLOCKS_HOLO = ["geometry", "ctqw"] + TERM_NAMES  # 7 blocks -- fpocket excluded, leaky on holo


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _geometry_block(coords: np.ndarray, seed_local: np.ndarray, cut: float, m: np.ndarray) -> np.ndarray:
    """TASK-0254's own `build_blocks` geometry formula, verbatim -- just
    decoupled from that function's `target_rows`-shaped dict input, since
    this task needs it computed on TWO differently-indexed (apo, holo)
    common-set coordinate arrays that `target_rows` never produces."""
    return np.column_stack([
        z(degree_centrality(coords, cutoff=cut))[m],
        z(euclid_from_seed_centroid(coords, seed_local))[m],
        z(hop_from_seed(coords, seed_local, cutoff=cut))[m],
    ])


def _common_rows(t: str):
    """Both flavours' (coords, bfactors) restricted to the matched common
    apo/holo (chain, resnum) set (`align_apo_holo`, TASK-0230's own
    machinery) -- required for a FAIR apo-vs-holo gap comparison (same
    node set scored both ways, not apo's own full residue set vs holo's
    own reduced one). Returns None on any real failure, not silently
    zero-filled (same discipline as `target_rows`)."""
    cfg, apo, seed, pocket = t0242.prep(t)
    if pocket is None or not np.asarray(pocket).any():
        return None
    if len(seed) == 0:
        return None
    holo = clean_from_config(t, role="holo")
    chain_map = chain_map_from_config(cfg)
    alignment = align_apo_holo(apo, holo, chain_map=chain_map)
    apo_idx, holo_idx = alignment.apo_idx, alignment.holo_idx
    if len(apo_idx) < 10:
        return None

    seed_local = np.where(np.isin(apo_idx, seed))[0]
    if len(seed_local) == 0:
        return None
    pocket_local = np.asarray(pocket)[apo_idx]
    n_local = len(apo_idx)
    m = np.ones(n_local, dtype=bool)
    m[seed_local] = False
    y = pocket_local[m].astype(int)
    if y.sum() < 3:
        return None

    cut = float(cfg.get("enm_cutoff", 8.0))
    coords_apo = apo.coords[apo_idx]
    bfac_apo = apo.bfactors[apo_idx]
    coords_holo = holo.coords[holo_idx]
    bfac_holo = holo.bfactors[holo_idx]

    # fpocket (apo only -- real predictor; excluded on holo, see module docstring)
    apo_ch = cfg.get("apo_chains") or cfg.get("chains")
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        ag = prody.parsePDB(cfg["apo_pdb"], compressed=False).select(
            "protein and (" + " or ".join(f"chain {c}" for c in apo_ch) + ")"
        )
        pdb = tmp / f"{t.lower()}_apo.pdb"
        prody.writePDB(str(pdb), ag)
        pockets = t0242.fpocket_candidates(pdb, tmp)
    if isinstance(pockets, dict):
        return None
    resn_full = np.asarray(apo.resnums)
    fpocket_full = t0249.fpocket_druggability_per_residue(pockets, resn_full)
    fpocket_x = z(fpocket_full[apo_idx])[m].reshape(-1, 1)

    def flavour_blocks(coords, bfac):
        geometry = _geometry_block(coords, seed_local, cut, m)
        ctqw = z(time_averaged_ctqw_converged(build_H_new(coords, bfac, cutoff=cut), source=seed_local, coherent=False))[m]
        tv = potential_term_vectors(coords, bfac, cut)
        terms = {name: z(tv[name])[m] for name in TERM_NAMES}
        return geometry, ctqw.reshape(-1, 1), terms

    geom_apo, ctqw_apo, terms_apo = flavour_blocks(coords_apo, bfac_apo)
    geom_holo, ctqw_holo, terms_holo = flavour_blocks(coords_holo, bfac_holo)

    feat_apo = dict(geometry=geom_apo, fpocket=fpocket_x, ctqw=ctqw_apo, **{k: v.reshape(-1, 1) for k, v in terms_apo.items()})
    feat_holo = dict(geometry=geom_holo, ctqw=ctqw_holo, **{k: v.reshape(-1, 1) for k, v in terms_holo.items()})

    return dict(target=t, y=y, n_common=n_local, feat_apo=feat_apo, feat_holo=feat_holo)


def _shapley_with_cache(feat: dict, y: np.ndarray, blocks: list) -> dict:
    """`shapley_attribution_4`'s own official Shapley VALUES (TASK-0260's
    routine, unmodified, called for the attribution numbers) PLUS the two
    specific subset AUCs this task's own headline needs (v({V_C}) and
    v({V_C, ctqw})) -- two extra direct `cv_auc` calls, not a rewrite of
    the reused routine."""
    result = shapley_attribution_4(feat, y, blocks)

    def subset_auc(subset):
        X = np.column_stack([feat[b] for b in subset])
        return float(cv_auc(X, y))

    result["auc_V_C_alone"] = subset_auc(["V_C"])
    result["auc_V_C_plus_ctqw"] = subset_auc(["V_C", "ctqw"]) if "ctqw" in blocks else None
    result["auc_all_minus_ctqw"] = subset_auc([b for b in blocks if b != "ctqw"])
    result["auc_all"] = subset_auc(blocks)
    return result


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    new_cand = yaml.safe_load(FROZEN_CONFIG.read_text())["targets"]
    t0242.CAND = new_cand
    frozen_targets = list(new_cand.keys())

    rows = {}
    for t in frozen_targets:
        try:
            r = _common_rows(t)
        except Exception as exc:  # noqa: BLE001
            _log(f"{t}: FAILED {type(exc).__name__}: {exc}")
            continue
        if r is None:
            _log(f"{t}: SKIP (no pocket/seed/alignment, or too few common residues/positives)")
            continue
        rows[t] = r
        _log(f"{t}: n_common={r['n_common']} n_pocket={int(r['y'].sum())}")

    _log(f"\n{len(rows)}/{len(frozen_targets)} usable\n")

    # --- per-term AUC, both flavours ---
    _log("### Per-term AUC, apo vs holo ###")
    per_term = {}
    for t, r in rows.items():
        row = {"apo": {}, "holo": {}}
        for name in TERM_NAMES:
            row["apo"][name] = float(cv_auc(r["feat_apo"][name], r["y"]))
            row["holo"][name] = float(cv_auc(r["feat_holo"][name], r["y"]))
        row["apo"]["ctqw"] = float(cv_auc(r["feat_apo"]["ctqw"], r["y"]))
        row["holo"]["ctqw"] = float(cv_auc(r["feat_holo"]["ctqw"], r["y"]))
        per_term[t] = row
        _log(f"{t:24s} apo  " + " ".join(f"{k}={row['apo'][k]:.3f}" for k in TERM_NAMES + ['ctqw']))
        _log(f"{t:24s} holo " + " ".join(f"{k}={row['holo'][k]:.3f}" for k in TERM_NAMES + ['ctqw']))
    (OUT / "per_term_auc_apo_holo.json").write_text(json.dumps(per_term, indent=1))

    # --- 8-block (apo) / 7-block (holo) Shapley ---
    _log("\n### Shapley: apo (8 blocks) ###")
    shap_apo = {}
    for t, r in rows.items():
        shap_apo[t] = _shapley_with_cache(r["feat_apo"], r["y"], BLOCKS_APO)
        sh = shap_apo[t]["shapley"]
        _log(f"{t:24s} " + " ".join(f"{b}={100*sh[b]:+5.1f}%" for b in BLOCKS_APO) +
             f"  full_auc={shap_apo[t]['full_auc']:.3f}")
    (OUT / "shapley_apo_8block.json").write_text(json.dumps(shap_apo, indent=1))

    _log("\n### Shapley: holo (7 blocks, fpocket excluded -- ceiling) ###")
    shap_holo = {}
    for t, r in rows.items():
        shap_holo[t] = _shapley_with_cache(r["feat_holo"], r["y"], BLOCKS_HOLO)
        sh = shap_holo[t]["shapley"]
        _log(f"{t:24s} " + " ".join(f"{b}={100*sh[b]:+5.1f}%" for b in BLOCKS_HOLO) +
             f"  full_auc={shap_holo[t]['full_auc']:.3f}")
    (OUT / "shapley_holo_7block.json").write_text(json.dumps(shap_holo, indent=1))

    # --- headline: CTQW added-last vs V_C alone, both flavours ---
    _log("\n### Headline: does CTQW add anything once V_C alone is in the model? ###")
    ctqw_over_vc_apo = {t: shap_apo[t]["auc_V_C_plus_ctqw"] - shap_apo[t]["auc_V_C_alone"] for t in rows}
    ctqw_over_vc_holo = {t: shap_holo[t]["auc_V_C_plus_ctqw"] - shap_holo[t]["auc_V_C_alone"] for t in rows}
    ctqw_added_last_full_apo = {t: shap_apo[t]["full_auc"] - shap_apo[t]["auc_all_minus_ctqw"] for t in rows}
    ctqw_added_last_full_holo = {t: shap_holo[t]["full_auc"] - shap_holo[t]["auc_all_minus_ctqw"] for t in rows}

    def _cluster(vals, label):
        d = {t: v for t, v in vals.items() if t in CM}
        res = cluster_sign_flip_test(d)
        _log(f"{label}: median={res['median']:+.4f} n_rows={res['n_rows']} n_clusters={res['n_clusters']} p={res['p_value']:.4f}")
        return res

    headline = {
        "ctqw_minus_vc_alone_apo": _cluster(ctqw_over_vc_apo, "CTQW+V_C - V_C alone (apo)"),
        "ctqw_minus_vc_alone_holo": _cluster(ctqw_over_vc_holo, "CTQW+V_C - V_C alone (holo)"),
        "ctqw_added_last_full_apo": _cluster(ctqw_added_last_full_apo, "CTQW added-last, full 8-block (apo)"),
        "ctqw_added_last_full_holo": _cluster(ctqw_added_last_full_holo, "CTQW added-last, full 7-block (holo)"),
    }
    (OUT / "headline_ctqw_vs_vc.json").write_text(json.dumps(headline, indent=1))

    # --- per-term apo->holo gap, and the pre-registered crypticity test ---
    _log("\n### Per-term apo->holo gap ###")
    crypticity = json.loads((_ROOT / "results/tasks/0254_fpocket_variance_and_crypticity/part_b_crypticity.json").read_text())
    gap_by_term = {name: {} for name in TERM_NAMES + ["ctqw"]}
    for t in rows:
        for name in TERM_NAMES + ["ctqw"]:
            gap_by_term[name][t] = per_term[t]["holo"][name] - per_term[t]["apo"][name]

    crypticity_gap_tests = {}
    for name in TERM_NAMES + ["ctqw"]:
        gaps = gap_by_term[name]
        if name == "V_T":
            # V_T = potentials.V_T(n, TERMINAL_FRACTION) -- a function of
            # residue COUNT and sequence position only, no coordinate or
            # B-factor dependence at all. On the matched common apo/holo
            # set (same n both flavours, by construction) its gap is
            # IDENTICALLY zero for every target -- not noise, a real
            # structural fact about this term (conformation-invariant),
            # confirmed directly (all 20 gaps exactly 0.0). A Spearman
            # correlation against a zero-variance vector is undefined
            # (nan), and the permutation test's own nan-comparison
            # arithmetic silently returns a meaningless p=0.0 rather than
            # erroring -- excluded here rather than reported as a real
            # significance.
            _log("V_T: excluded -- gap is identically 0.0 for every target "
                 "by construction (V_T depends only on residue count, not "
                 "coordinates/B-factors, so it cannot distinguish apo from "
                 "holo on the matched common set)")
            continue
        frac_open = {t: crypticity[t]["fraction_open"] for t in gaps if t in crypticity}
        common = sorted(set(gaps) & set(frac_open))
        if len(common) < 4:
            continue
        gvec = {t: gaps[t] for t in common}
        fvec = {t: frac_open[t] for t in common}
        res = cluster_permutation_correlation(gvec, fvec)
        crypticity_gap_tests[name] = res
        _log(f"{name}: gap vs fraction_open, cluster-perm rho={res['rho']:+.3f} "
             f"p={res['p_value']:.4f} (pre-registered: negative -- larger gap where LESS already open)")
    (OUT / "term_apo_holo_gap.json").write_text(json.dumps(
        {"gap_by_term": gap_by_term, "crypticity_correlation_tests": crypticity_gap_tests}, indent=1))

    _log(f"\nWrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
