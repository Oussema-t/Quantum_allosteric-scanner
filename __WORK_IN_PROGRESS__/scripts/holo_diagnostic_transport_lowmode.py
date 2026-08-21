#!/usr/bin/env python3
"""TASK-0153 -- extend the TASK-0067/TASK-0092 holo-diagnostic comparison
to the two newest observable families: quantum transport (`transport.
effective_resistance_from_source`/`transmission_from_source`, TASK-0145)
and low-mode PRS/DCC (`lowmode_predictor.prs_low`/`dcc_low`, TASK-0149).

**Diagnostic only, never a submission prediction** (TASK-0092's own
Context, reused verbatim): a holo-side AUC distinguishes (a) apo
genuinely lacks the information a real predictive setting could ever
have (never having holo in advance) from (b) the operator/propagator
itself is the bottleneck (holo wouldn't have helped either). A holo
run is never scored as if it were a real result.

**Simpler than TASK-0092's own two-pass design, by this task's own
Design note**: neither observable goes through `run_frozen_verdict`'s
multi-candidate blind-selection machinery at all (TASK-0145/TASK-0149
both score these directly, with every parameter fixed a priori) -- so
there is no winner-selection step to keep holo out of, and no
self-check pass is needed. Direct application: compute each observable
on holo coordinates + `_holo_native_labels` (TASK-0067's own
holo-frame-only label construction, imported verbatim, not re-derived)
and compare against the already-recorded apo AUC from TASK-0145's/
TASK-0149's own real-run JSON outputs.

Seed convention: the full active-site array (TASK-0118/INV-0006's
current GAUGE, already used by both apo-side scripts) on the HOLO side
too -- not TASK-0092's own single-scalar seed, which predates that
fix. Consistency with the apo-side numbers being compared against, not
a re-litigation of TASK-0092's own (older) choice.

Permutation-null convention: reuses each observable's own already-
established function directly (`transport_observable_real_run._score`/
`lowmode_predictor_real_run._score_cell`) against a holo-shaped `prep`
dict built the same way each script's own `_prepare_target` builds its
apo one -- not a new statistical method.
"""
from __future__ import annotations

import json
import os
import sys
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
_TESTS = Path(__file__).resolve().parent.parent / "tests"
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import H2_combinatorial_laplacian, build_H_new, contact_matrix, laplacian  # noqa: E402
from allostery.lowmode_predictor import dcc_low, prs_low  # noqa: E402
from allostery.metrics import auc as auc_fn, stratified_auc  # noqa: E402
from allostery.transport import effective_resistance_from_source, transmission_from_source  # noqa: E402

import run_challenge  # noqa: E402
import transport_observable_real_run as transport_run  # noqa: E402
import lowmode_predictor_real_run as lowmode_run  # noqa: E402
from test_gnm_cutoff_weight_benchmark import _holo_native_labels  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0153_holo_diagnostic"
TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _prepare_holo(target_name: str) -> dict:
    """Mirrors `transport_observable_real_run._prepare_target`'s and
    `lowmode_predictor_real_run._prepare_target`'s own construction, on
    HOLO coordinates + `_holo_native_labels` instead of apo + `build_labels`
    -- same shape, so each script's own `_score`/`_score_cell` can be
    reused unmodified against it."""
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    holo_pocket, holo_active, _ = _holo_native_labels(holo, target_config, pocket_cutoff)
    if not holo_pocket.any():
        raise RuntimeError(f"{target_name}: holo-native pocket label is empty")
    source = np.sort(np.where(holo_active)[0])
    if len(source) == 0:
        raise RuntimeError(f"{target_name}: holo-native active_site mask is empty")

    coords, bfactors = holo.coords, holo.bfactors
    pocket = holo_pocket.astype(int)
    n_residues = len(holo.resnums)

    L = H2_combinatorial_laplacian(coords, cutoff=cutoff)
    H_new = build_H_new(coords, bfactors, cutoff=cutoff)
    floor_scores = [
        degree_centrality(coords, cutoff=cutoff),
        euclid_from_seed_centroid(coords, source),
        hop_from_seed(coords, source, cutoff=cutoff),
    ]
    A = contact_matrix(coords, cutoff=cutoff, weight="binary")
    H_for_diagnosis = laplacian(A, normalised=False)
    shells = -hop_from_seed(coords, source, cutoff=cutoff)
    floor = float(max(auc_fn(f, pocket) for f in floor_scores))

    return {
        "target": target_name, "coords": coords, "bfactors": bfactors, "source": source,
        "pocket": pocket, "n_residues": n_residues, "cutoff": cutoff,
        "L": L, "H_new": H_new, "floor_scores": floor_scores, "H_for_diagnosis": H_for_diagnosis,
        "shells": shells, "floor": floor,
    }


def run_transport_holo(target_name: str) -> dict:
    prep = _prepare_holo(target_name)
    L, H_new, source = prep["L"], prep["H_new"], prep["source"]
    _log(f"[transport/holo] {target_name}: N={prep['n_residues']} pocket_size={int(prep['pocket'].sum())}")

    conductance = effective_resistance_from_source(L, source)
    reff_result = transport_run._score("effective_resistance", conductance, prep)

    transmission_L_E0 = transmission_from_source(L, source, E=0.0)
    trans_L_result = transport_run._score("transmission_on_L_E0", transmission_L_E0, prep)

    transmission_Hnew_E0 = transmission_from_source(H_new, source, E=0.0)
    trans_Hnew_result = transport_run._score("transmission_on_H_new_E0", transmission_Hnew_E0, prep)

    for r in (reff_result, trans_L_result, trans_Hnew_result):
        _log(f"[transport/holo] {target_name} {r['name']}: AUC={r['auc']:.4f} cat={r['category']} "
             f"p={r['permutation_null']['p_value']:.4f}")

    return {
        "target": target_name, "n_residues": prep["n_residues"], "pocket_size": int(prep["pocket"].sum()),
        "effective_resistance": reff_result,
        "transmission_on_L_E0": trans_L_result,
        "transmission_on_H_new_E0": trans_Hnew_result,
    }


def run_lowmode_holo(target_name: str) -> dict:
    prep = _prepare_holo(target_name)
    _log(f"[lowmode/holo] {target_name}: N={prep['n_residues']} pocket_size={int(prep['pocket'].sum())} "
         f"floor={prep['floor']:.4f}")

    cells = []
    for k in lowmode_run.K_MODES_GRID:
        prs = prs_low(prep["coords"], prep["source"], cutoff=prep["cutoff"], k_modes=k)
        dcc = dcc_low(prep["coords"], prep["source"], cutoff=prep["cutoff"], k_modes=k)
        row_prs = lowmode_run._score_cell("prs_low", prs, prep)
        row_dcc = lowmode_run._score_cell("dcc_low", dcc, prep)
        row_prs["k_modes"] = k
        row_dcc["k_modes"] = k
        cells.append(row_prs)
        cells.append(row_dcc)
        _log(
            f"[lowmode/holo] {target_name} k={k}: prs_low whole_auc={row_prs['whole_graph_auc']:.3f} "
            f"well_powered_max={row_prs['well_powered_max_auc']:.3f} "
            f"(p={row_prs['permutation_null']['p_value']:.4f}) | "
            f"dcc_low whole_auc={row_dcc['whole_graph_auc']:.3f} "
            f"well_powered_max={row_dcc['well_powered_max_auc']:.3f} "
            f"(p={row_dcc['permutation_null']['p_value']:.4f})"
        )

    return {
        "target": target_name, "n_residues": prep["n_residues"],
        "pocket_size": int(prep["pocket"].sum()), "floor": prep["floor"], "cells": cells,
    }


def _apo_transport(target_name: str) -> dict:
    with open(transport_run.OUTPUT_DIR / "transport_observable_real_run.json") as f:
        return json.load(f)[target_name]


def _apo_lowmode(target_name: str) -> dict:
    with open(lowmode_run.OUTPUT_DIR / "lowmode_predictor_real_run.json") as f:
        return json.load(f)[target_name]


def build_transport_comparison(holo_results: dict) -> list:
    rows = []
    for target in TARGETS:
        apo = _apo_transport(target)
        holo = holo_results[target]
        for name in ("effective_resistance", "transmission_on_L_E0", "transmission_on_H_new_E0"):
            apo_auc = apo[name]["auc"]
            holo_auc = holo[name]["auc"]
            gap = holo_auc - apo_auc
            rows.append({
                "target": target, "observable": name,
                "apo_auc": apo_auc, "holo_auc": holo_auc, "gap": gap,
                "holo_p": holo[name]["permutation_null"]["p_value"],
                "holo_category": holo[name]["category"],
            })
    return rows


def build_lowmode_comparison(holo_results: dict) -> list:
    rows = []
    for target in TARGETS:
        apo = _apo_lowmode(target)
        holo = holo_results[target]
        apo_by_key = {(c["observable"], c["k_modes"]): c for c in apo["cells"]}
        holo_by_key = {(c["observable"], c["k_modes"]): c for c in holo["cells"]}
        for key, holo_c in holo_by_key.items():
            apo_c = apo_by_key[key]
            gap = holo_c["well_powered_max_auc"] - apo_c["well_powered_max_auc"]
            rows.append({
                "target": target, "observable": key[0], "k_modes": key[1],
                "apo_well_powered_max": apo_c["well_powered_max_auc"],
                "holo_well_powered_max": holo_c["well_powered_max_auc"],
                "gap": gap, "holo_p": holo_c["permutation_null"]["p_value"],
            })
    return rows


def main() -> int:
    transport_holo = {}
    lowmode_holo = {}
    for target in TARGETS:
        try:
            transport_holo[target] = run_transport_holo(target)
        except Exception as exc:
            transport_holo[target] = {"target": target, "error": str(exc)}
            _log(f"[transport/holo] {target}: FAILED -- {exc!r}")
        try:
            lowmode_holo[target] = run_lowmode_holo(target)
        except Exception as exc:
            lowmode_holo[target] = {"target": target, "error": str(exc)}
            _log(f"[lowmode/holo] {target}: FAILED -- {exc!r}")

    transport_comparison = build_transport_comparison(transport_holo)
    lowmode_comparison = build_lowmode_comparison(lowmode_holo)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "transport_holo": transport_holo, "lowmode_holo": lowmode_holo,
        "transport_comparison": transport_comparison, "lowmode_comparison": lowmode_comparison,
    }
    with open(OUTPUT_DIR / "holo_diagnostic_transport_lowmode.json", "w") as f:
        json.dump(out, f, indent=2)
    _log(f"wrote {OUTPUT_DIR / 'holo_diagnostic_transport_lowmode.json'}")

    _log("\n=== Transport apo-vs-holo ===")
    for row in transport_comparison:
        _log(f"  {row['target']} / {row['observable']}: apo={row['apo_auc']:.3f} "
             f"holo={row['holo_auc']:.3f} gap={row['gap']:+.3f} holo_p={row['holo_p']:.4f}")

    _log("\n=== Lowmode apo-vs-holo (well-powered max AUC) ===")
    for row in lowmode_comparison:
        _log(f"  {row['target']} / {row['observable']} k={row['k_modes']}: "
             f"apo={row['apo_well_powered_max']:.3f} holo={row['holo_well_powered_max']:.3f} "
             f"gap={row['gap']:+.3f} holo_p={row['holo_p']:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
