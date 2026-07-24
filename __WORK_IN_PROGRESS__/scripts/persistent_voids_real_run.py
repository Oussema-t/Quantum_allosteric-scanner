#!/usr/bin/env python3
"""TASK-0142 (H2 half, HYP-P12) -- persistent-H2 void detection on real
targets. Ungated (2026-07-22 gating correction, see the task file's own
"Gating correction" section): a capped H2 void requires its lining
residues to be graph-*adjacent*, the opposite premise from what
TASK-0143's graph-openness gate tested (0/7) -- that FAIL does not bear
on this observable.

Delivered implementation (`.ai/reviews/2026-07-22/persistent_voids.py`,
ported unmodified into `allostery.persistent_voids`, 4 tests re-verified
passing independently before use here) computes a Vietoris-Rips complex
directly on apo Ca coordinates (not the contact-graph clique complex --
a real, stated choice, see the task file's own resolved Open Question).

`thresh` (Rips filtration radius cap) is NOT this task's own "8 A cutoff"
convention -- tested directly on real KRAS_G12C coordinates before
assuming the filing text's generic "same 8 A cutoff as every other
observable" transfers here: at thresh=8.0 only 2 truncated-looking H2
classes appear (birth values sitting right at the 8.0 boundary); the
diagram is fully stable (11 classes, identical birth/death) from
thresh=12.0 upward, matching the delivered code's own tested default
(16.0-18.0). Using thresh=16.0, the delivered `void_score` default,
flagged here as a tested divergence from the literal TODO text, not a
silent override.

Primary gate (this task's own module docstring: "the honest 'no void
detected' output -- do not fabricate a ranking from noise"): a target's
top H2 persistence must clear the synthetic-established noise floor
(`test_solid_ball_has_no_strong_void`'s own threshold, 2.5) before any
per-residue void_score ranking is trusted. Checked and reported per
target before any AUC is read as signal.

Matched-null convention: TASK-0133's own plain random-patch null
(`scripts/learnability_gate_patch_control.py`'s pattern -- same-size
uniform random draws from all residues, scored with the SAME
already-computed statistic), not TASK-0143's *spread-matched* null
(infeasible via rejection sampling on 4/7 real targets, a documented,
unrelated problem) -- this task's own filing text says "matched-spread
random-patch null ([[TASK-0133]] precedent)," but TASK-0133's actual
delivered implementation is plain random-patch, not spread-matched; the
literal citation (not the adjective) is treated as the precedent, stated
here explicitly rather than silently resolved.
"""
from __future__ import annotations

import argparse
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

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.diagnostics import NO_FAILURE_DETECTED, classify_failure  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.persistent_voids import persistence_h2, void_score  # noqa: E402

import run_challenge  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0142_topology"
TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
THRESH = 16.0  # see module docstring -- tested divergence from the literal "8A" TODO text
NOISE_FLOOR = 2.5  # test_solid_ball_has_no_strong_void's own established threshold
N_NULL_REPS = 1000
NULL_SEED = 133  # nods to TASK-0133, the precedent being reused


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _prepare_target(target_name: str):
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")
    source = np.sort(np.where(labels_obj.active_site)[0])
    if len(source) == 0:
        raise RuntimeError(f"{target_name}: empty active-site seed")

    return {
        "coords": apo.coords, "source": source,
        "pocket": labels_obj.pocket.astype(int), "cutoff": cutoff,
        "n_residues": len(apo.resnums),
    }


def run_target(target_name: str) -> dict:
    _log(f"{target_name}: preparing (fetch + clean + labels)...")
    prep = _prepare_target(target_name)
    coords, source, cutoff = prep["coords"], prep["source"], prep["cutoff"]
    labels = prep["pocket"]
    n = prep["n_residues"]
    _log(f"{target_name}: N={n} n_seed={len(source)} pocket_size={int(labels.sum())}")

    t0 = time.time()
    dgm2, _res = persistence_h2(coords, thresh=THRESH)
    h2_time = time.time() - t0
    if len(dgm2) == 0:
        top_persistence = 0.0
    else:
        top_persistence = float((dgm2[:, 1] - dgm2[:, 0]).max())
    void_detected = top_persistence > NOISE_FLOOR
    _log(f"{target_name}: top_h2_persistence={top_persistence:.3f} (noise floor {NOISE_FLOOR}) "
         f"void_detected={void_detected} n_H2_classes={len(dgm2)} ({h2_time:.2f}s)")

    # Gated score: honest "no void" -> all-zeros, per this module's own design.
    score_gated = void_score(coords, thresh=THRESH, min_persistence=NOISE_FLOOR, top_k=1)
    # Ungated score: reported for completeness/diagnosis, not as trusted signal
    # when void_detected is False (this task's own module docstring warns
    # against fabricating a ranking from noise).
    score_ungated = void_score(coords, thresh=THRESH, min_persistence=0.0, top_k=1)

    mask = np.ones(n, dtype=bool)
    mask[source] = False

    floor_scores = np.stack([
        euclid_from_seed_centroid(coords, source)[mask],
        hop_from_seed(coords, source, cutoff=cutoff)[mask],
        degree_centrality(coords, cutoff=cutoff)[mask],
    ])
    floor_aucs = [_auc(c, labels[mask]) for c in floor_scores]
    max_floor_auc = float(np.nanmax(floor_aucs))

    auc_gated = _auc(score_gated[mask], labels[mask])
    auc_ungated = _auc(score_ungated[mask], labels[mask])
    category_gated = classify_failure(score_gated[mask], labels[mask], floor_scores=floor_scores)
    category_ungated = classify_failure(score_ungated[mask], labels[mask], floor_scores=floor_scores)

    # TASK-0133's own plain random-patch null, applied to the (cheap: no
    # re-diagonalization, no re-running ripser) already-computed ungated
    # score vector's mean over the pocket vs a same-size random patch.
    pocket_idx = np.where(labels == 1)[0]
    pool = np.where(mask)[0]
    real_mean = float(score_ungated[pocket_idx].mean())
    rng = np.random.default_rng(NULL_SEED)
    null_means = np.empty(N_NULL_REPS)
    for i in range(N_NULL_REPS):
        patch = rng.choice(pool, size=len(pocket_idx), replace=False)
        null_means[i] = score_ungated[patch].mean()
    percentile = float((null_means < real_mean).mean() * 100.0)
    p_value = float((null_means >= real_mean).mean())

    result = {
        "target": target_name, "n_residues": n, "pocket_size": int(labels.sum()),
        "top_h2_persistence": top_persistence, "noise_floor": NOISE_FLOOR,
        "void_detected": void_detected, "n_h2_classes": len(dgm2),
        "auc_gated": auc_gated, "category_gated": category_gated,
        "auc_ungated": auc_ungated, "category_ungated": category_ungated,
        "floor_aucs": {"euclid": floor_aucs[0], "hop": floor_aucs[1], "degree": floor_aucs[2]},
        "max_floor_auc": max_floor_auc,
        "random_patch_null": {
            "real_mean_score": real_mean, "null_mean": float(null_means.mean()),
            "null_sd": float(null_means.std()), "percentile": percentile,
            "p_value": p_value, "n_reps": N_NULL_REPS,
        },
    }
    _log(
        f"{target_name}: auc_gated={auc_gated:.3f} ({category_gated}) "
        f"auc_ungated={auc_ungated:.3f} ({category_ungated}) max_floor={max_floor_auc:.3f} "
        f"null_percentile={percentile:.1f} p={p_value:.4f}"
    )
    return result


def _load_existing(output_path: Path) -> dict:
    if output_path.exists():
        with open(output_path) as f:
            return json.load(f)
    return {}


def render_summary(all_results: dict) -> str:
    n_tests = sum(1 for r in all_results.values() if "error" not in r)
    bonferroni = 0.05 / n_tests if n_tests else float("nan")

    lines = ["# TASK-0142 (H2 half) -- persistent-void real-target run summary", ""]
    lines.append(f"Bonferroni threshold: 0.05 / {n_tests} = {bonferroni:.5f}")
    lines.append(f"Noise floor (synthetic solid-ball negative control): top H2 persistence > {NOISE_FLOOR}")
    lines.append("")
    lines.append("| Target | top H2 persist. | void detected | AUC (gated) | AUC (ungated) | "
                  "max floor AUC | patch-null pctile | patch-null p |")
    lines.append("|---|---|---|---|---|---|---|---|")
    passes = []
    for name in TARGETS:
        r = all_results.get(name)
        if r is None or "error" in r:
            lines.append(f"| {name} | ERROR | | | | | | |")
            continue
        lines.append(
            f"| {name} | {r['top_h2_persistence']:.3f} | {r['void_detected']} | "
            f"{r['auc_gated']:.3f} ({r['category_gated']}) | {r['auc_ungated']:.3f} | "
            f"{r['max_floor_auc']:.3f} | {r['random_patch_null']['percentile']:.1f} | "
            f"{r['random_patch_null']['p_value']:.4f} |"
        )
        cleared = (
            r["void_detected"]
            and r["category_gated"] == NO_FAILURE_DETECTED
            and r["random_patch_null"]["p_value"] < bonferroni
        )
        if cleared:
            passes.append(name)

    lines.append("")
    if passes:
        lines.append(f"**PASS**: {', '.join(passes)} clears the void-detected gate, beats the floor, "
                      f"and clears the Bonferroni-corrected random-patch null.")
    else:
        any_void = [n for n in TARGETS if all_results.get(n, {}).get("void_detected")]
        if any_void:
            lines.append(f"**FAIL** -- {', '.join(any_void)} shows a top H2 persistence above the noise "
                          f"floor, but does not clear the floor/null bar for a real PASS.")
        else:
            lines.append("**FAIL** -- no target's top H2 persistence clears the synthetic-established "
                          "noise floor; none of the 3 mandatory targets show evidence of a genuine "
                          "persistent void at Ca resolution. Reported per this task's own pre-registered "
                          "FAIL framing: \"the pocket is not a topological feature these operators see "
                          "at Ca resolution.\"")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=TARGETS)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "persistent_voids_real_run.json")
    args = parser.parse_args(argv)

    all_results = _load_existing(args.output)
    for name in args.target:
        if name in all_results and "error" not in all_results[name]:
            _log(f"{name}: already computed, skipping")
            continue
        try:
            all_results[name] = run_target(name)
        except Exception as exc:
            all_results[name] = {"error": str(exc)}
            _log(f"{name}: FAILED -- {exc!r}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(all_results, f, indent=2)
        _log(f"checkpointed {args.output}")

    summary = render_summary(all_results)
    with open(args.output.parent / "summary.md", "w") as f:
        f.write(summary)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
