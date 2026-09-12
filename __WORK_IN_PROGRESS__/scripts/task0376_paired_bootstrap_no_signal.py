"""TASK-0376 -- item 13: the paired score-minus-floor bootstrap NO_SIGNAL_IN_APO
needs, plus the detection limit it implies.

The external reviewer's own point (conceded, TASK-0369 item 13): `classify_
failure`'s `ci_overlap` diagnostic bootstraps `score` and `floor` SEPARATELY,
then checks whether the two independent CIs overlap. Score and floor are
computed on the SAME structure/residues and are correlated -- an independent-
CI overlap check throws that correlation away and is unfalsifiable in
practice for these targets (clearing `score_lo > floor_hi` would need
AUC ~0.80-0.89 here). The fix is a PAIRED bootstrap of the difference
`score_auc - floor_auc`: resample residue blocks once per iteration (the
identical scheme `metrics.block_bootstrap_ci` already uses -- same
`block_size`, same block-start convention), and evaluate BOTH AUCs on the
SAME resampled index set each time, so the correlation is preserved rather
than discarded.

Per-target arrays (`winner_occ`, `labels_obj.pocket`, the winning floor
array) are not persisted anywhere on disk (`hit_list.json`/`end_to_end.json`
keep only the summary AUC/CI) -- reconstructed here via the identical code
path `scripts/run_challenge.py::run_target` already uses (imported, not
reimplemented, for `_load_apo_holo`/`_make_candidates_builder`/
`run_frozen_verdict`/the floor-array recipe; the ~40-line per-target
orchestration glue between them is necessarily copied since `run_target`
itself only writes files and returns a status dict, never the arrays).

Planned Validation (this task's own): the recomputed `score_auc` must
reproduce the committed 0.514 / 0.541 / 0.548 (KRAS_G12C / BCR_ABL1 /
CARDIAC_MYOSIN) before the new paired CI is trusted.

Run: ../.venv/bin/python3 -u scripts/task0376_paired_bootstrap_no_signal.py
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

sys.stdout.reconfigure(line_buffering=True)
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_challenge as rc  # noqa: E402 -- module-level code is constants + function defs only, safe to import
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.protocol import run_frozen_verdict  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402

OUT = Path("results/tasks/0376_paired_bootstrap_no_signal")
CHECKPOINT_PATH = OUT / "checkpoint.jsonl"

# committed per-target AUCs this task's own Planned Validation must reproduce
COMMITTED_AUC = {"KRAS_G12C": 0.514, "BCR_ABL1": 0.541, "CARDIAC_MYOSIN": 0.548}
TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]

BLOCK_SIZE = 10  # matches metrics.block_bootstrap_ci's own default, for direct comparability
N_BOOT = 5000
CONFIDENCE = 0.95


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def build_target_arrays(target_name: str):
    """Reconstructs (winner_occ, labels, winning_floor, winning_floor_name)
    for one mandatory target -- the exact code path `run_challenge.py::
    run_target` uses through its own `winner_occ` computation, copied
    (not reimplemented) because that function itself only writes files."""
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", rc.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", rc.DEFAULT_POCKET_CUTOFF))

    apo, holo = rc._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None:
        raise RuntimeError(f"{target_name}: build_labels returned pocket=None")

    active_site_idx = np.where(labels_obj.active_site)[0]
    source = np.sort(active_site_idx)

    floor_names = ["degree_centrality", "euclid_from_seed_centroid", "hop_from_seed"]
    floor_scores = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]

    candidates_builder = rc._make_candidates_builder(apo, source, cutoff)
    leak_n_perm = rc._leak_check_n_perm_for(len(apo.resnums))
    result = run_frozen_verdict(
        target_name, candidates_builder,
        apo.coords, apo.bfactors, source, labels_obj.pocket,
        cutoff=cutoff, t_max=rc.SELECTION_GSR_ABLATION_T, n_steps=rc.SELECTION_GSR_ABLATION_N_STEPS,
        floor_scores=floor_scores, coherent=False,
        learnability=None, use_converged_limit=True,
        leak_check_n_perm=leak_n_perm,
    )
    leak_check = result.get("_leak_check")
    if leak_check is not None and leak_check.get("leak_detected"):
        raise RuntimeError(f"{target_name}: GATE-B4 leak check fired -- not trustworthy, matching run_challenge.py's own hard-stop")

    winner_H = candidates_builder()[result["_winner_index"]]["H"]
    w_winner, v_winner = np.linalg.eigh(winner_H)
    winner_occ = time_averaged_ctqw_converged(source=source, coherent=False, w=w_winner, v=v_winner)

    labels_arr = np.asarray(labels_obj.pocket).astype(int)
    floor_aucs = [_auc(np.asarray(f), labels_arr) for f in floor_scores]
    win_i = int(np.nanargmax(floor_aucs))
    return dict(winner_occ=winner_occ, labels=labels_arr,
                floor=np.asarray(floor_scores[win_i]), floor_name=floor_names[win_i],
                floor_auc=floor_aucs[win_i], N=len(apo.resnums))


def paired_block_bootstrap(scores, floor, labels, n_boot=N_BOOT, block_size=BLOCK_SIZE,
                            confidence=CONFIDENCE, rng=None):
    """Identical resampling scheme to `metrics.block_bootstrap_ci` (same
    block_size, same block-start draw), but evaluating BOTH arrays on the
    SAME resampled index set per iteration so the score/floor correlation
    (both measured on the same structure) is preserved in the difference's
    own distribution, rather than discarded by bootstrapping them apart."""
    if rng is None:
        rng = np.random.default_rng(42)  # matches block_bootstrap_ci's own default seed
    N = len(scores)
    n_blocks = int(np.ceil(N / block_size))
    diffs, score_boot, floor_boot = [], [], []
    for _ in range(n_boot):
        block_starts = rng.integers(0, N, size=n_blocks)
        idx = np.concatenate([np.arange(s, min(s + block_size, N)) for s in block_starts])[:N]
        s_auc = _auc(scores[idx], labels[idx])
        f_auc = _auc(floor[idx], labels[idx])
        if not (np.isnan(s_auc) or np.isnan(f_auc)):
            diffs.append(s_auc - f_auc)
            score_boot.append(s_auc)
            floor_boot.append(f_auc)
    diffs = np.asarray(diffs)
    alpha = 1 - confidence
    lo, hi = np.percentile(diffs, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    point_diff = _auc(scores, labels) - _auc(floor, labels)
    detection_limit = float((hi - lo) / 2.0)  # half-width of the paired 95% CI, stated explicitly as the definition used
    return dict(point_diff=float(point_diff), ci_lo=float(lo), ci_hi=float(hi),
                detection_limit=detection_limit, n_boot_used=len(diffs),
                excludes_zero=bool(lo > 0 or hi < 0))


def main() -> int:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    ckpt = open(CHECKPOINT_PATH, "w")
    results = {}
    for i, target in enumerate(TARGETS, 1):
        _log(f"[{i}/{len(TARGETS)}] {target}: building arrays (apo/holo fetch, labels, frozen verdict)...")
        arrs = build_target_arrays(target)
        score_auc = _auc(arrs["winner_occ"], arrs["labels"])
        _log(f"  {target}: N={arrs['N']} score_auc={score_auc:.4f} (committed {COMMITTED_AUC[target]}) "
             f"floor={arrs['floor_name']} floor_auc={arrs['floor_auc']:.4f}")
        matches = abs(score_auc - COMMITTED_AUC[target]) < 0.005
        _log(f"  Planned Validation: {'PASSES' if matches else 'FAILS'} "
             f"(|{score_auc:.4f} - {COMMITTED_AUC[target]}| = {abs(score_auc - COMMITTED_AUC[target]):.4f})")
        if not matches:
            _log(f"  STOPPING per this task's own Planned Validation -- harness does not reproduce the committed AUC.")
            ckpt.write(json.dumps({"target": target, "stopped": True, "score_auc": score_auc}) + "\n")
            ckpt.close()
            return 1

        boot = paired_block_bootstrap(arrs["winner_occ"], arrs["floor"], arrs["labels"])
        _log(f"  paired bootstrap (n_boot={boot['n_boot_used']}): diff={boot['point_diff']:+.4f} "
             f"95% CI=[{boot['ci_lo']:+.4f}, {boot['ci_hi']:+.4f}] detection_limit(halfwidth)={boot['detection_limit']:.4f} "
             f"excludes_zero={boot['excludes_zero']}")

        row = dict(N=arrs["N"], score_auc=float(score_auc), floor_name=arrs["floor_name"],
                   floor_auc=float(arrs["floor_auc"]), committed_auc=COMMITTED_AUC[target],
                   planned_validation_pass=matches, **boot)
        results[target] = row
        ckpt.write(json.dumps({"target": target, **row}) + "\n")
        ckpt.flush()

    (OUT / "paired_bootstrap_result.json").write_text(json.dumps(results, indent=1, default=str))
    ckpt.close()
    _log(f"\nWrote {OUT}/paired_bootstrap_result.json ({time.time()-t0:.0f}s total)")

    _log("\n### Summary: NO_SIGNAL_IN_APO (paired score-floor bootstrap; detection limit) ###")
    for target in TARGETS:
        r = results[target]
        _log(f"  {target}: score-floor = {r['point_diff']:+.3f}  95% CI [{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]  "
             f"detection limit dAUC = {r['detection_limit']:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
