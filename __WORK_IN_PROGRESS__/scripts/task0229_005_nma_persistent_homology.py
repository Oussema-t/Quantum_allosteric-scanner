#!/usr/bin/env python3
"""TASK-0229.005 -- refs [1]+[2] stitched: NMA-guided conformational
sampling (Zheng 2023, J. Chem. Phys. 158:124127, DOI 10.1063/5.0141630,
reused from [[TASK-0229.004]]'s own sampler) feeding persistent homology
(Koseki et al. 2025, CrypToth, J. Chem. Inf. Model. 65:5567, DOI
10.1021/acs.jcim.4c02111 -- verified directly before use, DOI resolves)
-- the register's own "highest-value construction": zero MD, both halves
drawn from the challenge's own bibliography.

Revives the H2 persistent-void arm (`allostery.persistent_voids`,
[[TASK-0142]]): TASK-0143's 0/7 graph-openness result tested a different
(graph-distance) signature and does not bear on this one -- see
`persistent_voids.py`'s own module docstring, which already states this.
CrypToth's own H2.2 claim -- TDA over an **ensemble** outperforms TDA on
a single structure -- is UNTESTED until this task; TASK-0142's own real-
target run was single-structure only (apo, NO_SIGNAL_IN_APO on
KRAS_G12C/BCR_ABL1).

Reuses, does not re-derive:
  - `task0229_004_zheng_nma_baseline.per_mode_displacements` for the
    NMA-sampled ensemble -- same N_MODES/AMPLITUDES/kT, so this arm's
    ensemble is the *same* displacement set .004's fpocket arm scored;
    the only thing that changes is the pocket-detection layer (fpocket
    -> persistent homology).
  - `allostery.persistent_voids.ensemble_void_score` (new this task,
    factored out of the existing `void_score` so both share one
    shell-kernel implementation -- see that module for a real bug found
    and fixed while building this: an H2/H1 class still alive at the
    Rips filtration cap `thresh` was previously treated as having
    infinite lifetime, corrupting the shell-kernel score with NaN;
    fixed via right-censoring at `thresh`, not exclusion, since an
    unbounded class is *at least* as persistent as a bounded one, not
    "no signal").
  - `allostery.baselines`/`allostery.nulls`/`allostery.plant` exactly as
    .004, for the proximity floor and TASK-0201's corrected compact-patch
    null.
  - `conformational_search_measurement._load_apo_holo` for apo/holo
    loading.

Positive control (this task's own Planned Validation): `void_score` on
the HOLO structure itself (not an ensemble -- holo is already the open
state) should show a persistent void near the known pocket -- the
positive control this H2 arm has never had. Run per-VALID-target (not a
single stand-in target, since both TASK-0209-VALID targets are cheap to
check directly here -- no fpocket subprocess cost, this is pure numpy +
ripser). Scoring a target's apo ensemble is gated on that SAME target's
own holo positive control passing, not a shared global gate.
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
_SCRIPTS = Path(__file__).resolve().parent
for _p in (_SRC, _SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import contact_matrix  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc  # noqa: E402
from allostery.nulls import build_adjacency, graph_walk_patch_matched, radius_of_gyration  # noqa: E402
from allostery.persistent_voids import ensemble_void_score, top_h2_persistence, void_score  # noqa: E402
from allostery.plant import select_distal_patch  # noqa: E402
from allostery.runlog import RunLogger  # noqa: E402

from conformational_search_measurement import DEFAULT_POCKET_CUTOFF, HOP_CUTOFF, _load_apo_holo  # noqa: E402
from task0229_004_zheng_nma_baseline import AMPLITUDES, KT, N_MODES, per_mode_displacements  # noqa: E402

THRESH = 16.0  # persistent_voids_real_run.py's own tested convention (TASK-0142)
NOISE_FLOOR = 2.5  # test_solid_ball_has_no_strong_void's own established threshold
N_NULL_DRAWS = 1000

VALID_TARGETS = ["KRAS_G12C", "PTP1B"]  # TASK-0209's VALID targets


def _load_labels(name: str, target_config: dict):
    apo, holo = _load_apo_holo(name, target_config)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    return apo, holo, labels_obj


def holo_positive_control(name: str, log: RunLogger) -> dict:
    """This task's own Planned Validation: does the known pocket show a
    persistent H2 void on the already-open HOLO structure -- the positive
    control this arm has never had (TASK-0142 only ever ran apo)."""
    target_config = load_target_config(name)
    apo, holo, labels_obj = _load_labels(name, target_config)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        return {"target": name, "ok": False, "reason": "no resolvable pocket label"}

    pocket_idx = np.where(labels_obj.pocket)[0]
    real_pocket_set = {(apo.chain_ids[i], int(apo.resnums[i])) for i in pocket_idx}
    holo_label = np.array(
        [1 if (c, int(r)) in real_pocket_set else 0 for c, r in zip(holo.chain_ids, holo.resnums)]
    )
    if holo_label.sum() == 0:
        return {"target": name, "ok": False, "reason": "apo pocket residues not resolvable on holo numbering"}

    top_h2 = top_h2_persistence(holo.coords, thresh=THRESH)
    void_detected = top_h2 > NOISE_FLOOR
    score_ungated = void_score(holo.coords, thresh=THRESH, min_persistence=0.0, top_k=1)
    a = auc(score_ungated, holo_label)
    result = {
        "target": name, "ok": True,
        "n_holo_residues": int(len(holo.resnums)), "n_pocket_matched": int(holo_label.sum()),
        "top_h2_persistence": top_h2, "void_detected": bool(void_detected), "auc": a,
    }
    log.step(f"{name}:holo_positive_control", **{k: v for k, v in result.items() if k != "target"})
    return result


def run_target(name: str, log: RunLogger) -> dict:
    t0 = time.monotonic()
    target_config = load_target_config(name)
    apo, holo, labels_obj = _load_labels(name, target_config)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))

    if labels_obj.pocket is None or not labels_obj.pocket.any():
        return {"target": name, "ok": False, "reason": "no resolvable pocket label"}
    if not labels_obj.active_site.any():
        return {"target": name, "ok": False, "reason": "no resolvable active site"}

    n = len(apo.resnums)
    pocket_idx = np.where(labels_obj.pocket)[0]
    active_idx = np.where(labels_obj.active_site)[0]
    log.step(f"{name}:labels", n_residues=n, n_active=len(active_idx), n_pocket=len(pocket_idx))

    # ---- Ensemble from .004's own sampler (same N_MODES/AMPLITUDES/kT) ----
    displacements, mode_idx, amp_used, eigvals = per_mode_displacements(
        apo.coords, HOP_CUTOFF, N_MODES, KT, AMPLITUDES,
    )
    conformations = [apo.coords + displacements[i] for i in range(len(displacements))]
    log.step(f"{name}:ensemble_built", n_conformations=len(conformations))

    ens_score, top_h1, top_h2 = ensemble_void_score(conformations, thresh=THRESH, min_persistence=0.0, top_k=1)
    frac_void_detected = float((top_h2 > NOISE_FLOOR).mean())
    log.step(
        f"{name}:ensemble_persistence_done",
        mean_top_h2=float(top_h2.mean()), mean_top_h1=float(top_h1.mean()),
        frac_conf_void_detected=frac_void_detected,
    )

    pocket_label = labels_obj.pocket.astype(int)
    ens_auc = auc(ens_score, pocket_label)

    floor_scores = {
        "degree": degree_centrality(apo.coords, cutoff=pocket_cutoff),
        "euclid": euclid_from_seed_centroid(apo.coords, active_idx),
        "hop": hop_from_seed(apo.coords, active_idx, cutoff=HOP_CUTOFF),
    }
    floor_aucs = {k: auc(v, pocket_label) for k, v in floor_scores.items()}
    floor_max = max(v for v in floor_aucs.values() if np.isfinite(v))

    # TASK-0201's own corrected compact-patch null, reused unchanged.
    W = contact_matrix(apo.coords, cutoff=HOP_CUTOFF, weight="invdist")
    adjacency = build_adjacency(apo.coords, cutoff=HOP_CUTOFF)
    real_rg = radius_of_gyration(apo.coords, pocket_idx)
    rng = np.random.default_rng(1)
    null_aucs = np.empty(N_NULL_DRAWS)
    for i in range(N_NULL_DRAWS):
        null_idx = graph_walk_patch_matched(apo.coords, adjacency, len(pocket_idx), rng, target_rg=real_rg)
        null_label = np.zeros(n, dtype=int)
        null_label[null_idx] = 1
        null_aucs[i] = auc(ens_score, null_label)
    valid_null = null_aucs[np.isfinite(null_aucs)]
    perm_p = float((np.sum(valid_null >= ens_auc) + 1) / (len(valid_null) + 1)) if len(valid_null) else float("nan")

    return {
        "target": name, "ok": True,
        "n_residues": n, "n_pocket": len(pocket_idx), "n_active": len(active_idx),
        "n_conformations": len(conformations),
        "mean_top_h2": float(top_h2.mean()), "mean_top_h1": float(top_h1.mean()),
        "frac_conf_void_detected": frac_void_detected,
        "ensemble_void_score_auc": ens_auc,
        "proximity_floor_aucs": floor_aucs, "proximity_floor_max": floor_max,
        "beats_floor": bool(np.isfinite(ens_auc) and ens_auc > floor_max),
        "compact_patch_null_p": perm_p, "compact_patch_null_mean": float(np.nanmean(null_aucs)),
        "n_null_draws": N_NULL_DRAWS,
        "elapsed_s": round(time.monotonic() - t0, 1),
        # TASK-0142's own single-structure (apo) comparator, computed fresh here
        # for a direct within-task ensemble-vs-single-structure comparison
        # (CrypToth's own H2.2 claim), not pulled from that task's stale JSON.
        "single_structure_apo_auc": auc(void_score(apo.coords, thresh=THRESH, min_persistence=0.0, top_k=1), pocket_label),
        "single_structure_apo_top_h2": top_h2_persistence(apo.coords, thresh=THRESH),
    }


def main() -> int:
    out_dir = Path(__file__).resolve().parent.parent / "results/tasks/0229_005_nma_persistent_homology"
    out_dir.mkdir(parents=True, exist_ok=True)
    log = RunLogger(out_dir / "run.jsonl", run_name="task0229_005_nma_persistent_homology")

    out = []
    for name in VALID_TARGETS:
        print(f"{name}: holo positive control (Planned Validation)...", file=sys.stderr)
        v = holo_positive_control(name, log)
        print(f"{name}: {v}", file=sys.stderr)
        out.append({"role": "holo_positive_control", **v})

    passed = {r["target"] for r in out if r.get("ok") and r.get("void_detected") and r.get("auc", 0.0) > 0.5}
    print(f"Holo positive control passed for: {sorted(passed) or 'NONE'}", file=sys.stderr)

    for name in VALID_TARGETS:
        role = "scored" if name in passed else "ungated_diagnostic"
        if name not in passed:
            print(
                f"{name}: own holo positive control did not pass -- running anyway as an UNGATED "
                "diagnostic (reported for completeness/transparency, not trusted as signal, same "
                "convention as persistent_voids_real_run.py's own gated/ungated split).",
                file=sys.stderr,
            )
        else:
            print(f"{name}: running (scored, ensemble)...", file=sys.stderr)
        r = run_target(name, log)
        print(f"{name}: role={role} ok={r.get('ok')} auc={r.get('ensemble_void_score_auc')} elapsed={r.get('elapsed_s')}", file=sys.stderr)
        out.append({"role": role, **r})

    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {out_path}")
    log.finish(n_holo_controls=len(VALID_TARGETS), n_passed=len(passed))

    print("\n=== summary ===")
    for r in out:
        if r["role"] == "holo_positive_control":
            if not r.get("ok"):
                print(f"[holo_control] {r['target']:12s} FAILED: {r.get('reason')}")
            else:
                print(f"[holo_control] {r['target']:12s} top_h2={r['top_h2_persistence']:.3f} void_detected={r['void_detected']} AUC={r['auc']:.3f}")
        else:
            tag = "[scored]      " if r["role"] == "scored" else "[UNGATED]     "
            if not r.get("ok"):
                print(f"{tag} {r['target']:12s} FAILED: {r.get('reason')}")
            else:
                print(
                    f"{tag} {r['target']:12s} ens_AUC={r['ensemble_void_score_auc']:.3f} "
                    f"single_AUC={r['single_structure_apo_auc']:.3f} floor_max={r['proximity_floor_max']:.3f} "
                    f"beats_floor={r['beats_floor']} null_p={r['compact_patch_null_p']:.4f} "
                    f"frac_void_detected={r['frac_conf_void_detected']:.2f}"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
