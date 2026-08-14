#!/usr/bin/env python3
"""TASK-0200 -- conditional-on-fpocket residual analysis: restricted to
the residue population fpocket ranks ambiguously (inside a detected
cavity, but not among its most confident hits), does any dynamics
observable add discriminative power fpocket's own score does not already
have? Symmetric reverse check: does fpocket add anything conditional on
dynamics?

Band definition, success criterion, representative-observable choice, and
the (already-known-underpowered) primary-band positive counts are all
pre-registered in `.ai/tasks/DONE/TASK-0200-*.md`'s own "Pre-Registered
Band Definition + Success Criterion" section, fixed before this script
existed -- not repeated in full here. Summary: band = fpocket score > 0
and in `[lo, hi)` percentile of the nonzero distribution (primary window
40-70, swept 20-80/30-70/50-90); 3 representative observables (`H_new`
occupancy, `dcc_low`, `R_eff`) per [[TASK-0199]]'s own measured effective-
rank-~3 finding; success = clears the within-band floor AND a
compact-patch permutation null at `alpha=0.05/18`.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.diagnostics import assert_gate_reachable  # noqa: E402
from allostery.hamiltonians import H2_combinatorial_laplacian, build_H_new, laplacian  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.lowmode_predictor import dcc_low  # noqa: E402
from allostery.metrics import auc as auc_fn  # noqa: E402
from allostery.nulls import compact_patch, compact_patch_from_pool  # noqa: E402
from allostery.plant import plant_channel  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.transport import effective_resistance_from_source  # noqa: E402

import run_challenge  # noqa: E402
from task0163_external_baseline_scoring import (  # noqa: E402
    _fpocket_per_residue_scores, _run_fpocket, _write_full_atom_apo_pdb,
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0200_fpocket_conditional"
# TASK-0203: PTP1B added (the target carrying TASK-0201's own surviving
# positive, never covered by this script before); CASPASE7 attempted per
# this task's own "if cheap" hedge. KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN
# unchanged -- re-running this script reproduces their own cells
# byte-identically (this task's own wiring check), since nothing about
# their own computation path changed.
TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "PTP1B", "CASPASE7"]
PUBLISHED_FPOCKET_AUC = {"KRAS_G12C": 0.8348, "BCR_ABL1": 0.8596, "CARDIAC_MYOSIN": 0.5345}
# PTP1B/CASPASE7 have no TASK-0163 published number (that task covered
# only the 3 mandatory targets) -- sanity check below is skipped, not
# silently treated as passing, when a target has no published value.
REPRESENTATIVE_OBSERVABLES = ["H_new_occ", "dcc_low", "R_eff"]
BAND_WINDOWS = [(20, 80), (30, 70), (40, 70), (50, 90)]  # (40, 70) is primary
PRIMARY_WINDOW = (40, 70)
MIN_POS_WELL_POWERED = 3
N_PERM_REPS = 1000
PERM_SEED = 123
# TASK-0203: family size now depends on how many targets actually run
# (CASPASE7 may fail/be skipped) -- computed from the declared TARGETS
# list, not hand-maintained, so it can never silently drift out of sync
# with the targets actually scored (TASK-0189's own defect class).
FAMILY_SIZE = 3 * len(TARGETS) * 2  # 3 observables x N targets x 2 directions
ALPHA = 0.05 / FAMILY_SIZE

# TASK-0203 Leg 1: TASK-0201's actual PTP1B survival is dcc_low at
# k_modes=10, not the k=20 "representative" TASK-0199 chose for
# cross-target consistency. Tested here as one additional, clearly
# separate, single-target replication check -- NOT part of
# REPRESENTATIVE_OBSERVABLES/FAMILY_SIZE (would silently change every
# other target's own already-published family-size context) -- compared
# against the same updated ALPHA for consistency, per this task's own
# "no exceptions for a conditional analysis" reading rule.
K10_REPLICATION_TARGET = "PTP1B"
K10_REPLICATION_K_MODES = 10


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _prepare_target(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))
    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")
    source = np.sort(np.where(labels_obj.active_site)[0])
    return {
        "target_config": target_config, "apo": apo, "coords": apo.coords, "bfactors": apo.bfactors,
        "source": source, "cutoff": cutoff, "pocket": labels_obj.pocket.astype(int),
        "n_residues": len(apo.resnums),
    }


def _fpocket_scores(prep: dict, target_name: str) -> np.ndarray:
    apo_chains = prep["target_config"].get("apo_chains") or prep["target_config"].get("chains")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        pdb_path = tmp / f"{target_name}_apo.pdb"
        _write_full_atom_apo_pdb(prep["target_config"], apo_chains, pdb_path)
        pockets = _run_fpocket(pdb_path, tmp)
        if isinstance(pockets, dict) and "error" in pockets:
            raise RuntimeError(f"fpocket failed: {pockets['error']}")
        return _fpocket_per_residue_scores(pockets, prep["apo"].resnums, prep["apo"].chain_ids)


def compute_representative_observables(prep: dict) -> dict:
    coords, bfactors, source, cutoff = prep["coords"], prep["bfactors"], prep["source"], prep["cutoff"]
    H_new = build_H_new(coords, bfactors, cutoff=cutoff)
    w, v = np.linalg.eigh(H_new)
    L = H2_combinatorial_laplacian(coords, cutoff=cutoff)
    return {
        "H_new_occ": time_averaged_ctqw_converged(source=source, coherent=False, w=w, v=v),
        "dcc_low": dcc_low(coords, source, cutoff=cutoff, k_modes=20),
        "R_eff": effective_resistance_from_source(L, source),
    }


def band_mask(scores: np.ndarray, lo_pct: float, hi_pct: float, *, nonzero_only: bool) -> np.ndarray:
    if nonzero_only:
        pool = scores[scores != 0]
        if len(pool) == 0:
            return np.zeros(len(scores), dtype=bool)
        lo, hi = np.percentile(pool, [lo_pct, hi_pct])
        return (scores != 0) & (scores >= lo) & (scores < hi)
    lo, hi = np.percentile(scores, [lo_pct, hi_pct])
    return (scores >= lo) & (scores < hi)


def within_band_floor(coords: np.ndarray, source, cutoff: float, pocket: np.ndarray, mask: np.ndarray) -> dict:
    """Floor recomputed strictly within `mask` -- never inherited from
    the whole-graph floor, per this task's own Constraint (restricting
    the population changes the confound structure)."""
    floors = {
        "degree_centrality": degree_centrality(coords, cutoff=cutoff),
        "euclid_from_seed_centroid": euclid_from_seed_centroid(coords, source),
        "hop_from_seed": hop_from_seed(coords, source, cutoff=cutoff),
    }
    band_aucs = {name: auc_fn(s[mask], pocket[mask]) for name, s in floors.items()}
    finite = {k: v for k, v in band_aucs.items() if np.isfinite(v)}
    return {"floor_aucs": band_aucs, "floor_max": max(finite.values()) if finite else float("nan")}


def compact_null_within_band(coords: np.ndarray, pocket_size: int, mask: np.ndarray, score: np.ndarray,
                              real_auc: float, *, n_reps: int = N_PERM_REPS, seed: int = PERM_SEED) -> dict:
    """Same null mechanism `compact_null_rerun.py::_lowmode_null` uses
    (`nulls.compact_patch`-drawn same-size synthetic pocket labels over
    the whole target) -- band-restricted scoring pipeline, same null."""
    rng = np.random.default_rng(seed)
    n = len(coords)
    null_aucs = []
    for _ in range(n_reps):
        idx = compact_patch(coords, pocket_size, rng)
        null_label = np.zeros(n, dtype=int)
        null_label[idx] = 1
        a = auc_fn(score[mask], null_label[mask])
        if np.isfinite(a):
            null_aucs.append(a)
    null_aucs = np.array(null_aucs) if null_aucs else np.array([np.nan])
    p_value = float((null_aucs >= real_auc).mean()) if np.isfinite(real_auc) else float("nan")
    return {"p_value": p_value, "n_reps_used": len(null_aucs), "null_median": float(np.median(null_aucs))}


def conditional_cell(coords, source, cutoff, pocket, conditioning_score, target_score, *,
                      lo_pct, hi_pct, nonzero_only) -> dict:
    mask = band_mask(conditioning_score, lo_pct, hi_pct, nonzero_only=nonzero_only)
    n_band = int(mask.sum())
    n_pos = int(pocket[mask].sum())
    result = {
        "band_size": n_band, "band_positives": n_pos,
        "well_powered": n_pos >= MIN_POS_WELL_POWERED,
    }
    if n_pos < MIN_POS_WELL_POWERED:
        result["auc"] = None
        return result

    real_auc = float(auc_fn(target_score[mask], pocket[mask]))
    floor = within_band_floor(coords, source, cutoff, pocket, mask)
    pocket_size = int(pocket.sum())
    null = compact_null_within_band(coords, pocket_size, mask, target_score, real_auc)
    result.update({
        "auc": real_auc, "floor_max": floor["floor_max"], "floor_aucs": floor["floor_aucs"],
        "beats_floor": bool(np.isfinite(floor["floor_max"]) and real_auc > floor["floor_max"]),
        "null_p_value": null["p_value"], "null_n_reps_used": null["n_reps_used"],
        "clears_null": bool(np.isfinite(null["p_value"]) and null["p_value"] < ALPHA),
    })
    result["adds_information"] = bool(result["beats_floor"] and result["clears_null"])
    return result


def run_target(target_name: str) -> dict:
    _log(f"{target_name}: preparing...")
    prep = _prepare_target(target_name)
    coords, source, cutoff, pocket = prep["coords"], prep["source"], prep["cutoff"], prep["pocket"]

    _log(f"{target_name}: running fpocket...")
    fp_scores = _fpocket_scores(prep, target_name)
    fp_auc = float(auc_fn(fp_scores, pocket))
    published = PUBLISHED_FPOCKET_AUC.get(target_name)
    sanity_ok = (abs(fp_auc - published) < 1e-3) if published is not None else None
    _log(f"{target_name}: fpocket AUC={fp_auc:.4f} (published {published}) sanity_ok={sanity_ok}")

    _log(f"{target_name}: computing representative observables...")
    observables = compute_representative_observables(prep)

    forward = {}
    for obs_name in REPRESENTATIVE_OBSERVABLES:
        forward[obs_name] = {}
        for lo, hi in BAND_WINDOWS:
            cell = conditional_cell(
                coords, source, cutoff, pocket, fp_scores, observables[obs_name],
                lo_pct=lo, hi_pct=hi, nonzero_only=True,
            )
            forward[obs_name][f"{lo}-{hi}"] = cell
        primary = forward[obs_name][f"{PRIMARY_WINDOW[0]}-{PRIMARY_WINDOW[1]}"]
        _log(f"{target_name}: forward {obs_name} primary band n={primary['band_size']} "
             f"pos={primary['band_positives']} well_powered={primary['well_powered']}")

    reverse = {}
    for obs_name in REPRESENTATIVE_OBSERVABLES:
        reverse[obs_name] = {}
        for lo, hi in BAND_WINDOWS:
            cell = conditional_cell(
                coords, source, cutoff, pocket, observables[obs_name], fp_scores,
                lo_pct=lo, hi_pct=hi, nonzero_only=False,
            )
            reverse[obs_name][f"{lo}-{hi}"] = cell

    result = {
        "target": target_name, "n_residues": prep["n_residues"],
        "fpocket_auc": fp_auc, "fpocket_auc_published": published, "sanity_ok": sanity_ok,
        "forward_conditional": forward, "reverse_conditional": reverse,
    }

    if target_name == K10_REPLICATION_TARGET:
        _log(f"{target_name}: computing k={K10_REPLICATION_K_MODES} TASK-0201 replication check...")
        dcc_low_k10 = dcc_low(coords, source, cutoff=cutoff, k_modes=K10_REPLICATION_K_MODES)
        k10_forward = {}
        k10_reverse = {}
        for lo, hi in BAND_WINDOWS:
            k10_forward[f"{lo}-{hi}"] = conditional_cell(
                coords, source, cutoff, pocket, fp_scores, dcc_low_k10,
                lo_pct=lo, hi_pct=hi, nonzero_only=True,
            )
            k10_reverse[f"{lo}-{hi}"] = conditional_cell(
                coords, source, cutoff, pocket, dcc_low_k10, fp_scores,
                lo_pct=lo, hi_pct=hi, nonzero_only=False,
            )
        primary_k10 = k10_forward[f"{PRIMARY_WINDOW[0]}-{PRIMARY_WINDOW[1]}"]
        _log(
            f"{target_name}: k=10 replication forward primary band n={primary_k10['band_size']} "
            f"pos={primary_k10['band_positives']} well_powered={primary_k10['well_powered']}"
        )
        result["k10_replication"] = {
            "k_modes": K10_REPLICATION_K_MODES,
            "note": "TASK-0203: the exact dcc_low k value TASK-0201's PTP1B survival used "
                    "(graph_walk_patch_matched null there; compact_patch null here -- not the same "
                    "test, see this task's own pre-registration for the null-mismatch caveat).",
            "forward_conditional": k10_forward, "reverse_conditional": k10_reverse,
        }

    return result


NEGATIVE_CONTROL_WINDOW = (20, 80)  # primary (40,70) is underpowered by construction (see pre-registration)


def run_negative_control(target_name: str = "KRAS_G12C") -> dict:
    """Run at the wide (20,80) window, not the primary (40,70) one --
    the primary band's own positive count (2, pre-registered as
    known-underpowered before any run) cannot produce a defined AUC at
    all, positive or negative, so it cannot exercise this control
    meaningfully. The wide window has real power (checked: KRAS_G12C
    n=39, pos=4, well_powered=True) and is one of this task's own
    pre-registered sweep points, not a new ad hoc choice."""
    prep = _prepare_target(target_name)
    fp_scores = _fpocket_scores(prep, target_name)
    rng = np.random.default_rng(999)
    random_score = rng.normal(size=prep["n_residues"])
    cell = conditional_cell(
        prep["coords"], prep["source"], prep["cutoff"], prep["pocket"], fp_scores, random_score,
        lo_pct=NEGATIVE_CONTROL_WINDOW[0], hi_pct=NEGATIVE_CONTROL_WINDOW[1], nonzero_only=True,
    )
    return cell


def run_positive_control(target_name: str = "KRAS_G12C") -> dict:
    """A planted, geometry-blind channel must be detectable by THIS
    analysis pipeline specifically -- not just by R_eff in isolation
    (already validated in TASK-0190). **Found and fixed while building
    this control, not assumed correct on the first attempt**: drawing
    the planted patch via `select_distal_patch` (any distal, floor-blind
    compact patch anywhere on the protein) gave zero overlap with the
    fpocket band on every trial -- a real control bug, since a planted
    signal outside the tested population cannot validate that population's
    own detection pipeline. Fixed by drawing the patch from *within* the
    band pool directly (`nulls.compact_patch_from_pool`), guaranteeing
    overlap by construction, then scoring the SAME within-band
    conditional-AUC statistic `conditional_cell` uses elsewhere in this
    script (patch membership as the synthetic label, restricted to the
    band) -- not a side statistic.

    fpocket's own score is exactly invariant to a weight-only plant by
    construction (it reads only raw atomic coordinates, never `W`) --
    stated directly, not re-verified by an expensive fpocket re-run that
    would just reproduce the same input. R_eff on the planted Laplacian
    is the plant-sensitive observable (TASK-0190's own established
    recipe: `effective_resistance_from_source` on `hamiltonians.
    laplacian(W_planted)`, never H_new-derived quantities, which are
    provably blind to a weight-only plant, TASK-0167.001)."""
    prep = _prepare_target(target_name)
    coords, source, cutoff = prep["coords"], prep["source"], prep["cutoff"]

    fp_scores = _fpocket_scores(prep, target_name)
    band = band_mask(fp_scores, NEGATIVE_CONTROL_WINDOW[0], NEGATIVE_CONTROL_WINDOW[1], nonzero_only=True)
    band_pool = np.where(band)[0]
    if len(band_pool) < 6:
        raise RuntimeError(f"{target_name}: band pool too small ({len(band_pool)}) for a positive-control patch")

    from allostery.hamiltonians import contact_matrix
    W0 = contact_matrix(coords, cutoff=cutoff, weight="invdist")
    rng = np.random.default_rng(42)
    patch = compact_patch_from_pool(coords, band_pool, min(6, len(band_pool)), rng)
    patch_label = np.zeros(len(coords), dtype=int)
    patch_label[patch] = 1
    overlap = int(band[patch].sum())  # by construction, must equal len(patch)

    results_by_strength = []
    for strength in (0.0, 5.0, 20.0, 100.0):
        W_planted, _ = plant_channel(W0, source, patch, strength, n_paths=20, rng=np.random.default_rng(43))
        L_planted = laplacian(W_planted)
        r_eff = effective_resistance_from_source(L_planted, source)
        within_band_auc = float(auc_fn(r_eff[band], patch_label[band]))
        results_by_strength.append({"strength": strength, "within_band_auc_vs_patch": within_band_auc})

    detected = results_by_strength[-1]["within_band_auc_vs_patch"] > results_by_strength[0]["within_band_auc_vs_patch"] + 0.05
    return {
        "target": target_name, "band_window": NEGATIVE_CONTROL_WINDOW, "band_size": int(band.sum()),
        "patch_size": len(patch), "band_patch_overlap": overlap,
        "fpocket_geometry_blind": True,
        "results_by_strength": results_by_strength, "plant_detected_within_band": detected,
    }


def main() -> int:
    # TASK-0217.002 -- FAMILY_SIZE already auto-scales with len(TARGETS)
    # (TASK-0189's own defect class, family drift, guarded above), but
    # nothing previously checked the OTHER half of that same lesson: as
    # TARGETS grows, ALPHA=0.05/FAMILY_SIZE shrinks, and a Bonferroni-
    # corrected permutation gate below `1/N_PERM_REPS` can only ever fire
    # at p==0 exactly (`allostery.diagnostics.assert_gate_reachable`'s own
    # docstring). Currently reachable (ALPHA=0.05/30=1.67e-3 vs.
    # 1/N_PERM_REPS=1e-3, confirmed by this call) but with only ~67%
    # headroom -- a single further TARGETS extension (this register has
    # done exactly that twice already, TASK-0203 then this audit) would
    # cross into the same unreachable-gate defect TASK-0189 found and
    # fixed elsewhere, silently. Fail-fast here rather than re-discover it
    # after a future run.
    assert_gate_reachable(ALPHA, family_size=1, n_reps=N_PERM_REPS)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = {"targets": {}}
    for target in TARGETS:
        try:
            results["targets"][target] = run_target(target)
        except Exception as exc:
            results["targets"][target] = {"target": target, "error": str(exc)}
            _log(f"{target}: FAILED -- {exc!r}")
        with open(OUTPUT_DIR / "fpocket_conditional_analysis.json", "w") as f:
            json.dump(results, f, indent=2)

    _log("running negative control...")
    results["negative_control"] = run_negative_control()
    _log("running positive control (plant)...")
    results["positive_control"] = run_positive_control()
    results["family_size"] = FAMILY_SIZE
    results["alpha"] = ALPHA

    with open(OUTPUT_DIR / "fpocket_conditional_analysis.json", "w") as f:
        json.dump(results, f, indent=2)
    _log(f"wrote {OUTPUT_DIR / 'fpocket_conditional_analysis.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
