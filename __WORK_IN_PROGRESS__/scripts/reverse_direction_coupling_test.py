#!/usr/bin/env python3
"""TASK-0162 -- reverse-direction coupling test: seed at the (holo-labeled)
pocket, score coupling into the active-site residues, and compare against
the forward direction (seed at the active site, score into the pocket)
already on record.

Every observable in this project's register seeds at the active site and
asks where signal goes. Real allosteric experiments measure the reverse
direction -- does binding at the candidate site perturb the active site --
and this project has never computed it. `labels.build_labels`'s own
`pocket`/`active_site` masks are guaranteed disjoint by construction
(`pocket = pocket_raw & ~active_site & ~terminal`, `labels.py`), so no
special handling is needed to swap which set is the seed and which is the
scored candidate/label.

Reuses every scoring function completely unmodified (this task's own
Out of Scope: no new observable) -- only the seed/label assignment swaps:

  FORWARD (already on record elsewhere in RESULTS.md, recomputed here
  fresh for a self-contained, apples-to-apples table): source=active_site,
  label=pocket.
  REVERSE (new): source=pocket, label=active_site.

Five observables, matching this task's own Intent Contract ("at
minimum"): `time_averaged_ctqw_converged` (TASK-0130), `prs_low`/`dcc_low`
(TASK-0149, k_modes=20 -- this project's own established default/headline
k, not a fresh k-sweep in each direction, a deliberate scope choice: this
task asks to re-run the existing best-performing observables, not
re-characterize their own k-sensitivity a second time), `R_eff` (on
`H2_combinatorial_laplacian`, TASK-0145's own Laplacian requirement) and
`T(E=0)` (on `H_new`, TASK-0145's own real-submission-operator choice).

Asymmetry statistic (this task's own explicit ask, Implementer's own
design choice, stated directly): Spearman rho between the forward and
reverse score vectors, restricted to the *background* set (residues in
neither pocket nor active_site) -- not the full N-residue vector. A
residue's own seed role trivially dominates its self-occupancy in that
direction (e.g. an active-site residue's forward occupation is large by
construction, its reverse occupation is not), so correlating the full
vectors would mostly measure "does each set have high self-occupancy in
its own seeded direction" (true by construction, not a real coupling
question) rather than "do residues *outside* either labeled set respond
similarly regardless of which end is doing the perturbing" -- the
background restriction isolates the actual reciprocity question.
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

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import H2_combinatorial_laplacian, build_H_new  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.lowmode_predictor import dcc_low, prs_low  # noqa: E402
from allostery.metrics import auc as auc_fn  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.transport import effective_resistance_from_source, transmission_from_source  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo, not re-derived

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "RESULTS" / "results_task0162_reverse_direction"
TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
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

    apo, holo = run_challenge._load_apo_holo(target_name, cfg)
    labels_obj = build_labels(apo, holo, cfg, cutoff=pocket_cutoff)
    active_idx = np.sort(np.where(labels_obj.active_site)[0])
    pocket_idx = np.sort(np.where(labels_obj.pocket)[0])
    assert len(set(active_idx.tolist()) & set(pocket_idx.tolist())) == 0, \
        f"{target_name}: active_site/pocket overlap -- labels.py's own disjointness guarantee violated"

    n = len(apo.resnums)
    active_label = labels_obj.active_site.astype(int)
    pocket_label = labels_obj.pocket.astype(int)
    background = ~(labels_obj.active_site | labels_obj.pocket)

    _log(f"{target_name}: N={n} active_site={len(active_idx)} pocket={len(pocket_idx)} "
         f"background={background.sum()} cutoff={cutoff}")

    H_new = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    L = H2_combinatorial_laplacian(apo.coords, cutoff=cutoff)

    fwd_scores = _score_all(apo.coords, H_new, L, active_idx, cutoff)
    rev_scores = _score_all(apo.coords, H_new, L, pocket_idx, cutoff)

    fwd_floor = _floor(apo.coords, active_idx, pocket_label, cutoff)
    rev_floor = _floor(apo.coords, pocket_idx, active_label, cutoff)

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


def main() -> int:
    results = {}
    for target_name in TARGETS:
        try:
            results[target_name] = run_one(target_name)
        except Exception as exc:
            results[target_name] = {"target": target_name, "error": str(exc)}
            _log(f"{target_name}: FAILED -- {exc!r}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "reverse_direction_coupling_test.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    _log(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
