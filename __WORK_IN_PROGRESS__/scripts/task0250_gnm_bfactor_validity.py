#!/usr/bin/env python3
"""TASK-0250 (H16.1) -- does GNM actually reproduce experimental B-factors
on the targets this project actually scores?

The standard per-target ENM model-validity check: correlate GNM-predicted
mean-square fluctuation (diagonal of the Kirchhoff pseudo-inverse,
`potentials._gnm_msf`, this project's own existing implementation, not
re-derived) against deposited crystallographic Cα B-factors. Never run
before in this register despite GNM/ANM being used everywhere (`dcc_low`,
`prs_low`, mode energetics, two-state ANM, ANM reachability).

**Pre-registered pass bar** (per the task filing's own text, stated before
any correlation below was computed): Pearson >= 0.6 PASS, 0.4-0.6
MARGINAL, < 0.4 FAIL -- the literature convention for a GNM-B-factor fit.

**Cutoff**: every target's own real `enm_cutoff` from `targets.yaml`
(uniformly 8.0 A across all 15 real targets, confirmed by direct read, not
assumed) -- the model actually used, not a re-tuned one (this task's own
Constraint).

**Unusable-B-factor flag, checked directly via RCSB before scoring** (not
guessed): `exptl.method` + resolution for all 15 apo entries, batched
GraphQL query. One flagged case found: CARDIAC_MYOSIN_TABLE1's apo (5TBY)
is ELECTRON MICROSCOPY at nominal 20.0 A resolution -- exactly the
"cryo-EM without per-atom B" case this task's own filing names explicitly.
Reported, not scored into the pass/fail tally.

Run: ../.venv/bin/python3 scripts/task0250_gnm_bfactor_validity.py
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
from scipy.stats import pearsonr, spearmanr

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.potentials import _gnm_msf  # noqa: E402

TARGETS = [
    "KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "CARDIAC_MYOSIN_TABLE1",
    "MYC_MAX", "PTP1B", "GLUCOKINASE", "ATCase", "CASPASE1", "CASPASE7",
    "HEMOGLOBIN", "TAR_RECEPTOR", "GLYCOGEN_PHOSPHORYLASE", "PFK", "GROEL_SUBUNIT",
]

# Checked directly against RCSB (batched GraphQL, exptl.method +
# rcsb_entry_info.resolution_combined), 2026-08-24, before any correlation
# below was computed -- not asserted from memory.
UNUSABLE_BFACTORS = {
    "CARDIAC_MYOSIN_TABLE1": (
        "apo 5TBY is ELECTRON MICROSCOPY, nominal resolution 20.0 A "
        "(RCSB em_3d_reconstruction.resolution) -- no meaningful per-atom "
        "B-factor refinement at this resolution; excluded from the "
        "pass/fail tally per this task's own explicit instruction, "
        "reported for transparency only."
    ),
}
# All other 14 apo entries confirmed X-RAY DIFFRACTION, resolution
# 1.24-3.42 A (BCR_ABL1's 1OPL is the lowest-resolution X-ray entry in
# the set at 3.42 A -- not flagged as unusable per the task's own bar,
# but its correlation should be read with lower confidence than the
# sub-2.5-A entries; noted, not excluded).

PASS_BAR = 0.6
MARGINAL_BAR = 0.4


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def verdict(pearson: float) -> str:
    if pearson >= PASS_BAR:
        return "PASS"
    if pearson >= MARGINAL_BAR:
        return "MARGINAL"
    return "FAIL"


def compute_target(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    cutoff = float(target_config["enm_cutoff"])
    apo = clean_from_config(target_name, role="apo")
    coords = apo.coords.astype(float)
    bfactors = apo.bfactors

    msf = _gnm_msf(coords, cutoff)

    n_nan = int(np.isnan(bfactors).sum())
    valid = ~np.isnan(bfactors)
    pearson_r, pearson_p = pearsonr(msf[valid], bfactors[valid])
    spearman_r, spearman_p = spearmanr(msf[valid], bfactors[valid])

    result = dict(
        target=target_name, apo_pdb=target_config["apo_pdb"], N=len(coords),
        cutoff=cutoff, n_bfactor_nan=n_nan,
        pearson_r=float(pearson_r), pearson_p=float(pearson_p),
        spearman_r=float(spearman_r), spearman_p=float(spearman_p),
        verdict=verdict(float(pearson_r)),
        unusable_reason=UNUSABLE_BFACTORS.get(target_name),
    )
    flag = " [UNUSABLE B-FACTORS -- not counted]" if target_name in UNUSABLE_BFACTORS else ""
    _log(f"{target_name} ({target_config['apo_pdb']}, N={len(coords)}): "
         f"Pearson={pearson_r:.3f} Spearman={spearman_r:.3f} -> {result['verdict']}{flag}")
    return result


def main() -> int:
    results = []
    for name in TARGETS:
        results.append(compute_target(name))

    out_dir = Path(__file__).resolve().parent.parent / "results" / "tasks" / "0250_gnm_bfactor_validity"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "gnm_bfactor_validity.json"
    json.dump(dict(pass_bar=PASS_BAR, marginal_bar=MARGINAL_BAR, results=results), open(out_path, "w"), indent=1)
    _log(f"wrote {out_path}")

    scored = [r for r in results if r["unusable_reason"] is None]
    print(f"\n{'target':24s} {'apo':6s} {'N':>5s} {'Pearson':>9s} {'Spearman':>9s} {'verdict':>10s}")
    print("-" * 70)
    for r in results:
        flag = " *UNUSABLE*" if r["unusable_reason"] else ""
        print(f"{r['target']:24s} {r['apo_pdb']:6s} {r['N']:5d} {r['pearson_r']:9.3f} "
              f"{r['spearman_r']:9.3f} {r['verdict']:>10s}{flag}")
    n_pass = sum(1 for r in scored if r["verdict"] == "PASS")
    n_marginal = sum(1 for r in scored if r["verdict"] == "MARGINAL")
    n_fail = sum(1 for r in scored if r["verdict"] == "FAIL")
    print(f"\n{len(scored)} scored (excl. {len(results) - len(scored)} unusable): "
          f"{n_pass} PASS, {n_marginal} MARGINAL, {n_fail} FAIL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
