#!/usr/bin/env python3
"""TASK-0171 -- [[TASK-0162]]'s forward/reverse coupling test, re-run
HOLO-native end-to-end, as a diagnostic comparison. Confirmed directly
(not assumed) that TASK-0162's own script ran every propagation on APO
topology exclusively (`build_H_new(apo.coords, ...)`, `H2_combinatorial_
laplacian(apo.coords, ...)`) -- holo was used there only to derive
labels. This script builds both the operators AND the labels from HOLO,
matching [[TASK-0067]]'s own established precedent for exactly this
apo-vs-holo question on a different observable family
(`_holo_native_labels`, imported verbatim from `test_gnm_cutoff_weight_
benchmark.py`, not re-derived).

**Diagnostic only, never a submission prediction** ([[TASK-0067]]'s own
Context, reused verbatim): a holo-side AUC distinguishes (a) apo
genuinely lacks the information a real predictive setting could ever
have (never having holo in advance) from (b) the operator/propagator
itself is the bottleneck (holo wouldn't have helped either). A holo run
is never scored as if it were a real result.

Reuses [[TASK-0162]]'s own five scoring functions and forward/reverse
seed-swap logic completely unmodified (this task's own Out of Scope: no
new observable) -- only the coordinate/label source changes from apo to
holo. The apo-side numbers are cited from TASK-0162's own already-written
`results_task0162_reverse_direction/reverse_direction_coupling_test.json`
(that JSON covers all 5 targets, including the generalization pair, even
though the committed script's own `TARGETS` constant lists only the 3
mandatory ones -- confirmed by reading the JSON directly before trusting
it), never recomputed here.

Same asymmetry statistic as TASK-0162: Spearman rho between the forward
and reverse score vectors, restricted to the background set (residues in
neither the holo-native pocket nor holo-native active site) -- isolates
"do residues outside either labeled set respond similarly regardless of
which end is doing the perturbing" from the trivial self-occupancy effect
a seed role has on its own direction.
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
from scipy.stats import spearmanr

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
from allostery.hamiltonians import H2_combinatorial_laplacian, build_H_new  # noqa: E402
from allostery.lowmode_predictor import dcc_low, prs_low  # noqa: E402
from allostery.metrics import auc as auc_fn  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.transport import effective_resistance_from_source, transmission_from_source  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo, not re-derived
from test_gnm_cutoff_weight_benchmark import _holo_native_labels  # noqa: E402
import reverse_direction_coupling_test as apo_run  # noqa: E402 -- cite its numbers, not recompute

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "RESULTS" / "results_task0171_reverse_direction_holo"
TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "PTP1B", "CASPASE7"]
K_MODES = 20


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _floor(coords, source, label, cutoff) -> float:
    candidates = [
        degree_centrality(coords, cutoff=cutoff),
        euclid_from_seed_centroid(coords, source),
        hop_from_seed(coords, source, cutoff=cutoff),
    ]
    return float(max(auc_fn(c, label) for c in candidates))


def _score_all(coords, H_new, L, source, cutoff) -> dict:
    return {
        "ctqw_converged": time_averaged_ctqw_converged(H_new, source=source, coherent=False),
        "prs_low": prs_low(coords, source, cutoff=cutoff, k_modes=K_MODES),
        "dcc_low": dcc_low(coords, source, cutoff=cutoff, k_modes=K_MODES),
        "R_eff": effective_resistance_from_source(L, source),
        "T_E0_Hnew": transmission_from_source(H_new, source, E=0.0),
    }


def run_one(target_name: str) -> dict:
    cfg = load_target_config(target_name)
    cutoff = float(cfg.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(cfg.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))

    _apo, holo = run_challenge._load_apo_holo(target_name, cfg)
    holo_pocket, holo_active, _ = _holo_native_labels(holo, cfg, pocket_cutoff)
    assert not (holo_pocket & holo_active).any(), \
        f"{target_name}: holo-native active_site/pocket overlap -- _holo_native_labels's own disjointness broken"
    if not holo_pocket.any():
        raise RuntimeError(f"{target_name}: holo-native pocket label is empty")
    active_idx = np.sort(np.where(holo_active)[0])
    pocket_idx = np.sort(np.where(holo_pocket)[0])
    if len(active_idx) == 0:
        raise RuntimeError(f"{target_name}: holo-native active_site mask is empty")

    n = len(holo.resnums)
    active_label = holo_active.astype(int)
    pocket_label = holo_pocket.astype(int)
    background = ~(holo_active | holo_pocket)

    _log(f"{target_name}: N={n} active_site={len(active_idx)} pocket={len(pocket_idx)} "
         f"background={background.sum()} cutoff={cutoff}")

    coords, bfactors = holo.coords, holo.bfactors
    H_new = build_H_new(coords, bfactors, cutoff=cutoff)
    L = H2_combinatorial_laplacian(coords, cutoff=cutoff)

    fwd_scores = _score_all(coords, H_new, L, active_idx, cutoff)
    rev_scores = _score_all(coords, H_new, L, pocket_idx, cutoff)

    fwd_floor = _floor(coords, active_idx, pocket_label, cutoff)
    rev_floor = _floor(coords, pocket_idx, active_label, cutoff)

    per_observable = {}
    for name in fwd_scores:
        s_fwd = fwd_scores[name]
        s_rev = rev_scores[name]
        auc_fwd = float(auc_fn(s_fwd, pocket_label))
        auc_rev = float(auc_fn(s_rev, active_label))
        rho_bg, p_bg = spearmanr(s_fwd[background], s_rev[background])
        per_observable[name] = {
            "auc_forward": auc_fwd, "floor_forward": fwd_floor,
            "forward_clears_floor": bool(auc_fwd > fwd_floor),
            "auc_reverse": auc_rev, "floor_reverse": rev_floor,
            "reverse_clears_floor": bool(auc_rev > rev_floor),
            "background_spearman_rho": float(rho_bg), "background_spearman_p": float(p_bg),
        }
        _log(
            f"{target_name}/{name}: fwd_auc={auc_fwd:.4f} (floor {fwd_floor:.4f}, "
            f"cleared={auc_fwd > fwd_floor}) rev_auc={auc_rev:.4f} (floor {rev_floor:.4f}, "
            f"cleared={auc_rev > rev_floor}) bg_rho={rho_bg:.4f} (p={p_bg:.4f})"
        )

    return {
        "target": target_name, "N": n,
        "n_active_site": len(active_idx), "n_pocket": len(pocket_idx),
        "n_background": int(background.sum()), "cutoff": cutoff,
        "observables": per_observable,
    }


def _apo_reference(target_name: str) -> dict:
    """TASK-0162's own already-computed apo-side numbers, cited not
    recomputed (this task's own Out of Scope: "re-litigating TASK-0162's
    apo-side numbers")."""
    with open(apo_run.OUTPUT_DIR / "reverse_direction_coupling_test.json") as f:
        return json.load(f)[target_name]


def build_four_way_table(holo_results: dict) -> list:
    rows = []
    for target in TARGETS:
        apo = _apo_reference(target)
        holo = holo_results[target]
        if "error" in apo or "error" in holo:
            continue
        for name in apo["observables"]:
            a = apo["observables"][name]
            h = holo["observables"][name]
            fwd_gap = h["auc_forward"] - a["auc_forward"]
            rev_gap = h["auc_reverse"] - a["auc_reverse"]
            # TASK-0067's own precedent gap scale: "an order of magnitude
            # smaller than the cutoff/weight-scheme spread" was judged
            # small; here, compared directly against each cell's own
            # floor-vs-actual margin (the scale this cell's own decision
            # already turns on) rather than an externally borrowed number.
            fwd_margin = abs(a["auc_forward"] - a["floor_forward"])
            small_gap_fwd = abs(fwd_gap) < max(fwd_margin, 0.05)
            rev_margin = abs(a["auc_reverse"] - a["floor_reverse"])
            small_gap_rev = abs(rev_gap) < max(rev_margin, 0.05)
            rows.append({
                "target": target, "observable": name,
                "apo_forward": a["auc_forward"], "apo_reverse": a["auc_reverse"],
                "holo_forward": h["auc_forward"], "holo_reverse": h["auc_reverse"],
                "forward_gap": fwd_gap, "reverse_gap": rev_gap,
                "forward_gap_small": small_gap_fwd, "reverse_gap_small": small_gap_rev,
                "apo_forward_cleared": a["forward_clears_floor"], "holo_forward_cleared": h["forward_clears_floor"],
                "apo_reverse_cleared": a["reverse_clears_floor"], "holo_reverse_cleared": h["reverse_clears_floor"],
            })
    return rows


def main() -> int:
    holo_results = {}
    for target_name in TARGETS:
        try:
            holo_results[target_name] = run_one(target_name)
        except Exception as exc:
            holo_results[target_name] = {"target": target_name, "error": str(exc)}
            _log(f"{target_name}: FAILED -- {exc!r}")

    four_way = build_four_way_table(holo_results)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = {"holo": holo_results, "four_way_comparison": four_way}
    out_path = OUTPUT_DIR / "reverse_direction_coupling_test_holo.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    _log(f"wrote {out_path}")

    _log("\n=== apo vs holo, forward/reverse (four-way) ===")
    for row in four_way:
        _log(
            f"  {row['target']} / {row['observable']}: "
            f"apo_fwd={row['apo_forward']:.3f} holo_fwd={row['holo_forward']:.3f} "
            f"(gap={row['forward_gap']:+.3f}, small={row['forward_gap_small']}) | "
            f"apo_rev={row['apo_reverse']:.3f} holo_rev={row['holo_reverse']:.3f} "
            f"(gap={row['reverse_gap']:+.3f}, small={row['reverse_gap_small']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
