#!/usr/bin/env python3
"""TASK-0120 -- learnability gate (HYP-P8): is the labeled pocket even
present in the apo topology?

`REVIEW-panel-2026-07-16-v2.md` Sec.6: "the highest information-per-hour
experiment available." For each mandatory target: Kabsch-superpose holo
onto apo (`superpose.align_apo_holo`), per-residue apo->holo Ca RMSD at
the labeled pocket vs. background (`superpose.cryptic_openness_gate` +
the new `superpose.background_rmsd`), and Tama-Sanejouand cumulative
overlap of the apo->holo displacement onto the apo ANM's low-frequency
modes (`superpose.anm_modes`/`cumulative_overlap`) -- classified via the
new `superpose.learnability_verdict`.

No new alignment/ANM machinery invented here -- this script is glue over
`superpose.py`'s existing primitives (`run_superpose`'s own building
blocks, called directly rather than through that one-call orchestrator,
since this task also needs `background_rmsd`, which `run_superpose`
does not compute).
"""
from __future__ import annotations

import json
import os
import sys
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

from allostery.clean import load_target_config  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.superpose import (  # noqa: E402
    align_apo_holo,
    anm_modes,
    background_rmsd,
    cryptic_openness_gate,
    cumulative_overlap,
    learnability_verdict,
)

import run_challenge  # noqa: E402 -- reuse _load_apo_holo, not re-derived

DEFAULT_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
DEFAULT_ANM_CUTOFF = 10.0
DEFAULT_N_MODES = 20
DEFAULT_POCKET_CUTOFF = 4.5
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0120"


def run_one(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    anm_cutoff = float(target_config.get("enm_cutoff", DEFAULT_ANM_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")

    alignment = align_apo_holo(apo, holo)
    gate = cryptic_openness_gate(apo, holo, alignment, labels_obj.pocket, rmsd_threshold=3.0)
    bg = background_rmsd(apo, holo, alignment, labels_obj.pocket)

    # TASK-0128 (still TODO, unclaimed as of this run): anm_modes' exactly-
    # 6-near-zero-mode assertion fails on multi-chain/floppy-linker targets
    # (BCR_ABL1 n_zero=7, CARDIAC_MYOSIN n_zero=10) -- that task's own scope
    # is determining *why* (floppiness vs. genuine disconnection) before
    # touching the assertion; not this task's call to preempt with an
    # inline widening. Degrade gracefully instead: pocket/background RMSD
    # (this task's own new contribution) does not depend on anm_modes at
    # all and is always reported; cumulative overlap is marked blocked,
    # not silently dropped, when it is.
    co_curve = None
    co_final = float("nan")
    co_blocked_reason = None
    try:
        eigvals, eigvecs = anm_modes(apo.coords, cutoff=anm_cutoff, n_modes=DEFAULT_N_MODES)
        delta_r = (
            alignment.aligned_holo_coords[alignment.holo_idx] - apo.coords[alignment.apo_idx]
        ).ravel()
        co_curve = cumulative_overlap(delta_r, eigvecs, alignment.apo_idx)
        co_final = float(co_curve[-1]) if len(co_curve) else float("nan")
    except ValueError as exc:
        co_blocked_reason = f"BLOCKED on TASK-0128 (anm_modes): {exc!r}"

    verdict = learnability_verdict(
        pocket_rmsd_mean=gate["pocket_rmsd_mean"],
        background_rmsd_mean=bg["background_rmsd_mean"],
        co_final=co_final,
    )
    if co_blocked_reason is not None:
        verdict["verdict"] = "PARTIAL_RMSD_ONLY_CO_BLOCKED"

    result = {
        "target": target_name,
        "n_residues": len(apo.resnums),
        "n_common_correspondence": len(alignment.apo_idx),
        "alignment_rmsd_overall": alignment.rmsd_overall,
        "n_pocket_residues": gate["n_pocket_residues"],
        "n_pocket_unmeasurable": gate["n_unmeasurable"],
        "n_background_residues": bg["n_background_residues"],
        "co_curve_at_n_modes": DEFAULT_N_MODES,
        "co_curve": co_curve.tolist() if co_curve is not None else None,
        "co_blocked_reason": co_blocked_reason,
        **verdict,
    }
    co_str = f"CO({DEFAULT_N_MODES})={co_final:.3f}" if co_blocked_reason is None else "CO=BLOCKED(TASK-0128)"
    print(
        f"{target_name}: N={result['n_residues']} pocket_rmsd={verdict['pocket_rmsd_mean']:.3f} "
        f"background_rmsd={verdict['background_rmsd_mean']:.3f} ratio={verdict['rmsd_ratio']:.2f} "
        f"{co_str} -> {verdict['verdict']}"
    )
    return result


def main() -> int:
    results = {}
    for target_name in DEFAULT_TARGETS:
        try:
            results[target_name] = run_one(target_name)
        except Exception as exc:
            print(f"{target_name}: FAILED -- {exc!r}")
            results[target_name] = {"target": target_name, "error": str(exc)}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "learnability_gate.json", "w") as f:
        json.dump(results, f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
