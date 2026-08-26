#!/usr/bin/env python3
"""TASK-0277 -- apo<->holo ceiling sweep across every feature this register
has ever scored that [[TASK-0275]] does NOT already own.

[[TASK-0275]] covers the 5 `build_H_new` potential terms (V_B/V_T/V_R/V_C/
V_M), CTQW, and the combined 3-feature "geometry" Shapley block. Not
duplicated here (its own Scope: "do not duplicate", honored). This task's
own scope is everything else with a non-severe leakage grade: the 3
geometry features scored INDIVIDUALLY (not as one combined block),
`dcc_low`/`prs_low` (`lowmode_predictor.py`), ground-state relaxation on the
same `H_new` CTQW uses ([[TASK-0256]]'s own "classical diffusion" twin --
**not actually classical diffusion**, since `H_new` is indefinite on 100%
of this frozen set per [[TASK-0256]]'s own established finding; reported as
ground-state relaxation throughout, never re-labelled), and single-residue
mutational frustration ([[TASK-0268]]). SASA is run and explicitly flagged
moderate-leakage (natural, ligand-present holo burial -- this is the
question, not stripped, unlike [[TASK-0276]]'s deliberately-stripped
design for a different purpose). fpocket/P2Rank/PocketMiner are excluded
per this task's own table (severe leakage, cavity detectors on a
drug-shaped-open holo cavity). Conservation/chemistry have no holo flavour
at all -- stated, not computed.

**Method, identical to [[TASK-0275]]'s own established recipe, reproduced
here rather than imported** (that module's own `_common_rows` bundles its
own exclusive feature blocks inline; this reproduces only the shared
alignment/masking half, not the feature-building half): both flavours
scored on the MATCHED common apo/holo (chain, resnum) residue set
(`allostery.superpose.align_apo_holo`), never apo's own full residue set
vs. holo's own reduced one. **AUC = `task0254`'s own `cv_auc`** (5-fold
stratified CV, 20 repeats, OLS, out-of-fold), even for a single feature --
matching [[TASK-0275]]'s own choice, so every "AUC" in this register's
apo/holo tables is the same recipe, not two inconsistent ones for the same
word.

Reuses, does not re-derive:
  - `task0242_two_stage_dryrun.prep`/`CAND`, `allostery.clean.clean_from_config`,
    `allostery.superpose.align_apo_holo`/`chain_map_from_config` -- the
    exact apo/holo alignment TASK-0275 established.
  - `task0254_fpocket_variance_and_crypticity.cv_auc`/`z`, its own
    crypticity screen (`part_b_crypticity.json`).
  - `task0261_cluster_robust_stats.cluster_sign_flip_test`/
    `cluster_permutation_correlation`/`CM` -- 13 clusters.
  - `allostery.baselines.{degree_centrality,euclid_from_seed_centroid,
    hop_from_seed}`, `allostery.lowmode_predictor.{dcc_low,prs_low}`
    (function defaults: cutoff=10.0, k_modes=20 -- not swept, this task
    does not ask for a k-grid), `allostery.hamiltonians.build_H_new`,
    `allostery.propagators.ground_state_relaxation`,
    `allostery.frustration.single_residue_frustration` (CA coordinates,
    matching [[TASK-0268]]'s own already-published call convention exactly
    -- not `task0204_packing_hardness`'s CB variant, which would silently
    produce a second, different frustration number for the same apo
    target), `allostery.corex.{per_atom_asa,per_residue_native_asa}`
    ([[TASK-0257]]'s own validated SASA wrapper).

Pre-registered before any holo number was seen (matching [[TASK-0275]]'s
own prediction, inherited per this task's Scope): the apo-crypticity
correlation should be negative (larger gap on cryptic targets). [[TASK-0275]]
already found this does NOT hold at the potential-term level; this task
tests it again, independently, on a disjoint feature set.
"""
from __future__ import annotations

import itertools
import json
import sys
import tempfile
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import yaml
from scipy.stats import spearmanr

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402
import Bio.PDB as PDB  # noqa: E402

_orig_parsePDB = prody.parsePDB


def _parsePDB_all_altloc(*a, **kw):
    kw.setdefault("altloc", "all")
    return _orig_parsePDB(*a, **kw)


prody.parsePDB = _parsePDB_all_altloc

import task0242_two_stage_dryrun as t0242  # noqa: E402
from task0254_fpocket_variance_and_crypticity import cv_auc, z  # noqa: E402
from task0261_cluster_robust_stats import cluster_sign_flip_test  # noqa: E402
from allostery.clean import clean_from_config  # noqa: E402
from allostery.superpose import align_apo_holo, chain_map_from_config  # noqa: E402
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.lowmode_predictor import dcc_low, prs_low  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.propagators import ground_state_relaxation  # noqa: E402
from allostery.frustration import single_residue_frustration  # noqa: E402
from allostery.corex import per_atom_asa, per_residue_native_asa  # noqa: E402
from backend.data_layer import fetch  # noqa: E402

OUT = _ROOT / "results/tasks/0277_apo_holo_ceiling_sweep"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
T_CLASSICAL = 15.0  # [[TASK-0256]]'s own established constant

FEATURES = ["degree", "euclid", "hop", "dcc_low", "prs_low", "ground_state_relaxation", "frustration", "SASA"]
STATIC_FEATURES = {"degree", "euclid", "hop", "SASA"}  # no dynamics/mode participation at all
DYNAMICAL_FEATURES = {"dcc_low", "prs_low", "ground_state_relaxation"}
# frustration is neither -- a sequence x contact-geometry quantity, no seed/mode dependence


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def common_apo_holo_rows(t: str):
    """Reproduces [[TASK-0275]]'s own `_common_rows` alignment/masking half
    -- see module docstring for why this isn't a direct import."""
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
    return dict(
        cfg=cfg, apo=apo, holo=holo, apo_idx=apo_idx, holo_idx=holo_idx,
        seed_local=seed_local, m=m, y=y, cut=cut, n_local=n_local,
    )


def sasa_by_key(pdb_id: str) -> dict:
    """Ligand PRESENT, full deposited model -- [[TASK-0257]]'s own
    convention, unmodified, deliberately not ligand-stripped here (this
    task's own leakage table flags SASA moderate/natural-burial, unlike
    [[TASK-0276]]'s deliberately-stripped design for a different
    question). Returns {(chain, resnum): asa}."""
    fp = fetch(pdb_id)
    structure = PDB.PDBParser(QUIET=True).get_structure(pdb_id, fp)
    model = structure[0]
    per_atom_asa(model)
    out = {}
    for chain in model:
        for resnum, asa in per_residue_native_asa(chain).items():
            out[(chain.id, int(resnum))] = asa
    return out


def compute_features(coords: np.ndarray, bfac: np.ndarray, resnames: list,
                      seed_local: np.ndarray, cut: float) -> dict:
    H = build_H_new(coords, bfac, cutoff=cut)
    classical = ground_state_relaxation(H, T_CLASSICAL, source=seed_local)
    frust, _n_contacts = single_residue_frustration(coords, resnames)
    frust = np.where(np.isfinite(frust), frust, np.nanmedian(frust[np.isfinite(frust)]) if np.isfinite(frust).any() else 0.0)
    return dict(
        degree=degree_centrality(coords, cutoff=cut),
        euclid=euclid_from_seed_centroid(coords, seed_local),
        hop=hop_from_seed(coords, seed_local, cutoff=cut),
        dcc_low=dcc_low(coords, seed_local, cutoff=10.0, k_modes=20),
        prs_low=prs_low(coords, seed_local, cutoff=10.0, k_modes=20),
        ground_state_relaxation=classical,
        frustration=frust,
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    new_cand = yaml.safe_load(FROZEN_CONFIG.read_text())["targets"]
    t0242.CAND = new_cand
    frozen_targets = list(new_cand.keys())

    crypticity = json.loads((_ROOT / "results/tasks/0254_fpocket_variance_and_crypticity"
                              / "part_b_crypticity.json").read_text())

    rows = {}
    for t in frozen_targets:
        try:
            r = common_apo_holo_rows(t)
        except Exception as exc:  # noqa: BLE001
            _log(f"{t}: FAILED {type(exc).__name__}: {exc}")
            continue
        if r is None:
            _log(f"{t}: SKIP (no pocket/seed/alignment, or too few common residues/positives)")
            continue
        rows[t] = r
        _log(f"{t}: n_common={r['n_local']} n_pocket={int(r['y'].sum())}")

    _log(f"\n{len(rows)}/{len(frozen_targets)} usable\n")

    per_feature_auc: dict = {t: {"apo": {}, "holo": {}} for t in rows}
    for t, r in rows.items():
        apo, holo = r["apo"], r["holo"]
        apo_idx, holo_idx = r["apo_idx"], r["holo_idx"]
        m, seed_local, cut, y = r["m"], r["seed_local"], r["cut"], r["y"]

        coords_apo, bfac_apo = apo.coords[apo_idx], apo.bfactors[apo_idx]
        coords_holo, bfac_holo = holo.coords[holo_idx], holo.bfactors[holo_idx]
        resnames_apo = [apo.resnames[i] for i in apo_idx]
        resnames_holo = [holo.resnames[i] for i in holo_idx]

        feat_apo = compute_features(coords_apo, bfac_apo, resnames_apo, seed_local, cut)
        feat_holo = compute_features(coords_holo, bfac_holo, resnames_holo, seed_local, cut)

        # SASA: separate path (needs a fresh full-model fetch per flavour,
        # keyed by (chain, resnum), not index-positional).
        chids = np.asarray(apo.chain_ids)[apo_idx]
        resn = np.asarray(apo.resnums)[apo_idx]
        try:
            sasa_apo_by_key = sasa_by_key(r["cfg"]["apo_pdb"])
            sasa_holo_by_key = sasa_by_key(r["cfg"]["holo_pdb"])
            feat_apo["SASA"] = np.array([sasa_apo_by_key.get((str(c), int(rn)), np.nan)
                                          for c, rn in zip(chids, resn)])
            feat_holo["SASA"] = np.array([sasa_holo_by_key.get((str(c), int(rn)), np.nan)
                                           for c, rn in zip(chids, resn)])
        except Exception as exc:  # noqa: BLE001
            _log(f"  {t}: SASA failed ({type(exc).__name__}: {exc}), NaN both flavours")
            feat_apo["SASA"] = np.full(r["n_local"], np.nan)
            feat_holo["SASA"] = np.full(r["n_local"], np.nan)

        row_line = f"{t:24s} "
        for fname in FEATURES:
            xa = z(feat_apo[fname])[m].reshape(-1, 1)
            xh = z(feat_holo[fname])[m].reshape(-1, 1)
            ok_a = np.isfinite(xa).all()
            ok_h = np.isfinite(xh).all()
            auc_a = float(cv_auc(xa, y)) if ok_a else float("nan")
            auc_h = float(cv_auc(xh, y)) if ok_h else float("nan")
            per_feature_auc[t]["apo"][fname] = auc_a
            per_feature_auc[t]["holo"][fname] = auc_h
            row_line += f"{fname}={auc_a:.3f}/{auc_h:.3f}  "
        _log(row_line)

    (OUT / "per_feature_auc_apo_holo.json").write_text(json.dumps(per_feature_auc, indent=1))

    # --- consolidated table: median apo, median holo, median gap, cluster-p ---
    _log("\n### Consolidated table: feature | apo AUC | holo AUC | gap | cluster-p ###")
    summary = {}
    for fname in FEATURES:
        gaps = {t: per_feature_auc[t]["holo"][fname] - per_feature_auc[t]["apo"][fname]
                for t in per_feature_auc
                if np.isfinite(per_feature_auc[t]["holo"][fname]) and np.isfinite(per_feature_auc[t]["apo"][fname])}
        apo_vals = [per_feature_auc[t]["apo"][fname] for t in gaps]
        holo_vals = [per_feature_auc[t]["holo"][fname] for t in gaps]
        r = cluster_sign_flip_test(gaps) if gaps else dict(median=float("nan"), p_value=float("nan"), n_clusters=0)
        summary[fname] = dict(
            n=len(gaps), apo_median=float(np.median(apo_vals)) if apo_vals else float("nan"),
            holo_median=float(np.median(holo_vals)) if holo_vals else float("nan"),
            gap_median=r["median"], gap_p=r["p_value"], n_clusters=r.get("n_clusters", 0),
        )
        _log(f"{fname:<26} apo={summary[fname]['apo_median']:.3f}  holo={summary[fname]['holo_median']:.3f}  "
             f"gap={summary[fname]['gap_median']:+.4f}  p={summary[fname]['gap_p']:.4f}  n={summary[fname]['n']}")

    # --- central question: dynamical vs static gap distribution ---
    _log("\n### Central question: gap concentrated in dynamical features, or uniform? ###")
    dyn_gaps, static_gaps = [], []
    for fname in FEATURES:
        gaps = [per_feature_auc[t]["holo"][fname] - per_feature_auc[t]["apo"][fname]
                for t in per_feature_auc
                if np.isfinite(per_feature_auc[t]["holo"][fname]) and np.isfinite(per_feature_auc[t]["apo"][fname])]
        if fname in DYNAMICAL_FEATURES:
            dyn_gaps.extend(gaps)
        elif fname in STATIC_FEATURES:
            static_gaps.extend(gaps)
    from scipy.stats import mannwhitneyu
    if dyn_gaps and static_gaps:
        u_stat, u_p = mannwhitneyu(dyn_gaps, static_gaps, alternative="two-sided")
        _log(f"dynamical gaps: n={len(dyn_gaps)} median={np.median(dyn_gaps):+.4f}")
        _log(f"static gaps:    n={len(static_gaps)} median={np.median(static_gaps):+.4f}")
        _log(f"Mann-Whitney U p={u_p:.4f}")
    else:
        u_p = None

    # --- crypticity stratification ---
    _log("\n### Crypticity stratification (>=80% open in apo = 'open') ###")
    crypt_rows = {}
    for fname in FEATURES:
        gaps_open, gaps_cryptic = {}, {}
        for t in per_feature_auc:
            if t not in crypticity:
                continue
            a, h = per_feature_auc[t]["apo"][fname], per_feature_auc[t]["holo"][fname]
            if not (np.isfinite(a) and np.isfinite(h)):
                continue
            gap = h - a
            c = crypticity[t].get("fraction_open")
            if c is None:
                continue
            (gaps_open if c >= 0.80 else gaps_cryptic)[t] = gap
        med_open = float(np.median(list(gaps_open.values()))) if gaps_open else float("nan")
        med_cryptic = float(np.median(list(gaps_cryptic.values()))) if gaps_cryptic else float("nan")
        crypt_rows[fname] = dict(median_open=med_open, n_open=len(gaps_open),
                                  median_cryptic=med_cryptic, n_cryptic=len(gaps_cryptic))
        _log(f"{fname:<26} open(n={len(gaps_open)})={med_open:+.4f}  "
             f"cryptic(n={len(gaps_cryptic)})={med_cryptic:+.4f}")

    (OUT / "summary.json").write_text(json.dumps(
        dict(per_feature=summary, dynamical_vs_static_p=u_p, crypticity=crypt_rows), indent=1, default=str))
    _log(f"\nwritten: {OUT / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
