#!/usr/bin/env python3
"""TASK-0229.004 -- Zheng (2023, J. Chem. Phys. 158:124127, DOI
10.1063/5.0141630 -- verified directly, see the task file's own Done
section) as a real, scored classical baseline: "Predicting allosteric
sites using fast conformational sampling as guided by coarse-grained
normal modes."

**Zheng's own method, implemented faithfully, not approximated**: for
each of the lowest N_MODES ANM normal modes, displace the structure
along *that single mode* (both signs, at several amplitudes) --
deterministic per-mode scanning, not a joint Boltzmann-ensemble draw
over all modes at once (which is what [[TASK-0185]]'s own
`equipartition_ensemble` does, and is a different, already-answered
question -- reused here only for the parts that are generic
infrastructure, not "the method": `anm_modes`, full-atom reconstruction,
and the already-vendored/tested fpocket invocation).

Reuses, does not re-derive:
  - `allostery.superpose.anm_modes` for the ANM eigendecomposition.
  - `conformational_search_measurement._apply_ca_displacement`/
    `_load_full_atom_template`/`_pockets_overlap_frac` (TASK-0185) for
    the Ca-displacement-to-full-atom-PDB reconstruction and pocket
    scoring, ported by import, not copied.
  - `task0163_external_baseline_scoring._run_fpocket`/`_write_full_atom_
    apo_pdb`/`FPOCKET_BIN` (TASK-0163) for the one already-tested real
    fpocket invocation recipe in this repo.
  - `allostery.plant.select_distal_patch` (TASK-0167.001) for the
    negative-control decoy patch.
  - `allostery.nulls.graph_walk_patch_matched` (TASK-0201's corrected
    compact-patch null) for the null this task's own Constraints name.
  - `allostery.baselines.degree_centrality`/`euclid_from_seed_centroid`/
    `hop_from_seed` for the proximity floor (TASK-0094).

Run only on [[TASK-0209]]'s VALID targets (KRAS_G12C, PTP1B) for the
real scored result, per this task's own Constraint ("a result on an
invalid instance is uninterpretable") -- BCR_ABL1 is run first, and only
as this task's own required Planned-Validation qualitative check (a
known ENM-mode-driven pocket-opening case, [[TASK-0185]]'s own positive
control), not as a second scored VALID-target result.
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
from allostery.plant import select_distal_patch  # noqa: E402
from allostery.runlog import RunLogger  # noqa: E402
from allostery.superpose import anm_modes  # noqa: E402

from conformational_search_measurement import (  # noqa: E402
    DEFAULT_POCKET_CUTOFF,
    HOP_CUTOFF,
    POCKET_HIT_OVERLAP,
    _apply_ca_displacement,
    _load_apo_holo,
    _load_full_atom_template,
    _pockets_overlap_frac,
)
from task0163_external_baseline_scoring import FPOCKET_BIN, _run_fpocket, _write_full_atom_apo_pdb  # noqa: E402

N_MODES = 20  # matches TASK-0185's own primary choice; Zheng's own paper scans "the lowest 30" -- N_MODES=20 stated here as an Implementer's-call budget compromise (fpocket-call count), not a literal match to the paper's own 30
AMPLITUDES = (1.0, -1.0, 2.0, -2.0, 3.0, -3.0)  # multiples of each mode's own thermal scale sqrt(kT/eigval); Implementer's call, not asserted as the paper's own literal protocol -- stated explicitly, per this project's citation-use discipline
KT = 20.0  # matches TASK-0185/TASK-0187's own kT choice, for direct comparability
N_NULL_DRAWS = 1000

VALIDATION_TARGET = "BCR_ABL1"  # TASK-0185's own known positive control -- qualitative validation only, not a scored VALID-target result
SCORED_TARGETS = ["KRAS_G12C", "PTP1B"]  # TASK-0209's VALID targets


def per_mode_displacements(coords: np.ndarray, cutoff: float, n_modes: int, kT: float, amplitudes):
    """Zheng's own sampling scheme: for each of the lowest `n_modes` ANM
    modes, one displacement per (mode, amplitude) pair -- `amplitude *
    sqrt(kT/eigval_m) * eigvec_m`, not a joint random draw across modes.
    Returns `(displacements, mode_index, amplitude_used)`, displacements
    shape `(n_modes*len(amplitudes), N, 3)`."""
    eigvals, eigvecs = anm_modes(coords, cutoff=cutoff, n_modes=n_modes)
    n = coords.shape[0]
    disps, mode_idx, amp_used = [], [], []
    for m in range(n_modes):
        scale = float(np.sqrt(kT / eigvals[m]))
        mode_vec = eigvecs[:, m].reshape(n, 3)
        for a in amplitudes:
            disps.append((a * scale) * mode_vec)
            mode_idx.append(m)
            amp_used.append(a)
    return np.array(disps), np.array(mode_idx), np.array(amp_used), eigvals


def run_mode_scan_fpocket(template, chain_ids, resnums, displacements, real_pocket_set, decoy_set, log, label):
    """Single pass over the per-mode displacement samples: for each,
    reconstruct full-atom, run the already-vendored/tested fpocket, and
    record both (a) pocket-level real/decoy overlap fractions (Zheng's
    own hit-rate statistic, TASK-0185's own convention) and (b) which
    residues fell inside *any* detected cavity (this task's own
    residue-level score, one fpocket call per sample either way -- not
    duplicated across two passes)."""
    import prody

    n = len(chain_ids)
    n_samples = displacements.shape[0]
    real_fracs = np.zeros(n_samples)
    decoy_fracs = np.zeros(n_samples)
    hit_counts = np.zeros(n)
    errors = 0
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for i in range(n_samples):
            displaced, _n_unmatched = _apply_ca_displacement(template, chain_ids, resnums, displacements[i])
            pdb_path = tmp / f"sample_{i}.pdb"
            prody.writePDB(str(pdb_path), displaced)
            pockets = _run_fpocket(pdb_path, tmp)
            if isinstance(pockets, dict) and "error" in pockets:
                errors += 1
                continue
            real_fracs[i] = _pockets_overlap_frac(pockets, real_pocket_set)
            decoy_fracs[i] = _pockets_overlap_frac(pockets, decoy_set)
            hit_res: set = set()
            for p in pockets:
                hit_res |= p["residues"]
            for j in range(n):
                if (chain_ids[j], int(resnums[j])) in hit_res:
                    hit_counts[j] += 1
        log.step(
            f"{label}:mode_scan_fpocket_done", n_samples=n_samples, errors=errors,
            real_hit_rate=float((real_fracs >= POCKET_HIT_OVERLAP).mean()),
            decoy_hit_rate=float((decoy_fracs >= POCKET_HIT_OVERLAP).mean()),
        )
    return {
        "n_samples": n_samples, "errors": errors,
        "real_fracs": real_fracs, "decoy_fracs": decoy_fracs,
        "real_hit_rate": float((real_fracs >= POCKET_HIT_OVERLAP).mean()),
        "decoy_hit_rate": float((decoy_fracs >= POCKET_HIT_OVERLAP).mean()),
        "real_mean_overlap": float(real_fracs.mean()),
        "decoy_mean_overlap": float(decoy_fracs.mean()),
        "residue_score": hit_counts / max(n_samples, 1),
    }


def run_target(name: str, log: RunLogger, *, validation_only: bool = False) -> dict:
    t0 = time.monotonic()
    target_config = load_target_config(name)
    apo, holo = _load_apo_holo(name, target_config)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)

    if labels_obj.pocket is None or not labels_obj.pocket.any():
        return {"target": name, "ok": False, "reason": "no resolvable pocket label"}
    if not labels_obj.active_site.any():
        return {"target": name, "ok": False, "reason": "no resolvable active site"}

    pocket_idx = np.where(labels_obj.pocket)[0]
    active_idx = np.where(labels_obj.active_site)[0]
    real_pocket_set = {(apo.chain_ids[i], int(apo.resnums[i])) for i in pocket_idx}
    log.step(f"{name}:labels", n_residues=len(apo.resnums), n_active=len(active_idx), n_pocket=len(pocket_idx))

    W = contact_matrix(apo.coords, cutoff=HOP_CUTOFF, weight="invdist")
    decoy_idx = select_distal_patch(
        apo.coords, W, active_idx, len(pocket_idx), np.random.default_rng(0), cutoff=HOP_CUTOFF,
    )
    decoy_set = {(apo.chain_ids[i], int(apo.resnums[i])) for i in decoy_idx}

    apo_chains = target_config.get("apo_chains") or target_config.get("chains")
    template = _load_full_atom_template(target_config, apo_chains)

    displacements, mode_idx, amp_used, eigvals = per_mode_displacements(
        apo.coords, HOP_CUTOFF, N_MODES, KT, AMPLITUDES,
    )
    log.step(f"{name}:mode_scan_built", n_modes=N_MODES, n_amplitudes=len(AMPLITUDES), n_samples=len(displacements))

    main = run_mode_scan_fpocket(template, apo.chain_ids, apo.resnums, displacements, real_pocket_set, decoy_set, log, name)

    result = {
        "target": name, "ok": True,
        "n_residues": int(len(apo.resnums)), "n_pocket": int(len(pocket_idx)), "n_active": int(len(active_idx)),
        "n_modes": N_MODES, "amplitudes": list(AMPLITUDES), "kT": KT,
        "real_hit_rate": main["real_hit_rate"], "decoy_hit_rate": main["decoy_hit_rate"],
        "real_mean_overlap": main["real_mean_overlap"], "decoy_mean_overlap": main["decoy_mean_overlap"],
        "n_errors": main["errors"],
        "elapsed_s": round(time.monotonic() - t0, 1),
    }

    if validation_only:
        return result

    # ---- Residue-level Zheng score, floor, and corrected compact-patch null ----
    # Per-residue score: fraction of (mode, amplitude) samples in which
    # that residue's own position falls inside a detected fpocket cavity
    # -- a direct residue-level readout of "how often does sampling along
    # a low mode place this residue in an opened pocket," the natural
    # per-residue generalization of Zheng's own pocket-level hit-rate
    # statistic above. Computed in the same fpocket pass as `main`
    # (`run_mode_scan_fpocket`'s own `residue_score`), not a second,
    # duplicate sweep.
    n = len(apo.resnums)
    zheng_score = main["residue_score"]
    log.step(f"{name}:residue_score_done", mean_score=float(zheng_score.mean()), max_score=float(zheng_score.max()))

    pocket_label = labels_obj.pocket.astype(int)
    zheng_auc = auc(zheng_score, pocket_label)

    floor_scores = {
        "degree": degree_centrality(apo.coords, cutoff=pocket_cutoff),
        "euclid": euclid_from_seed_centroid(apo.coords, active_idx),
        "hop": hop_from_seed(apo.coords, active_idx, cutoff=HOP_CUTOFF),
    }
    floor_aucs = {k: auc(v, pocket_label) for k, v in floor_scores.items()}
    floor_max = max(v for v in floor_aucs.values() if np.isfinite(v))

    # TASK-0201's own corrected compact-patch null: graph_walk_patch_matched,
    # reused unchanged, not re-derived.
    adjacency = build_adjacency(apo.coords, cutoff=HOP_CUTOFF)
    real_rg = radius_of_gyration(apo.coords, pocket_idx)
    rng = np.random.default_rng(1)
    null_aucs = np.empty(N_NULL_DRAWS)
    for i in range(N_NULL_DRAWS):
        null_idx = graph_walk_patch_matched(apo.coords, adjacency, len(pocket_idx), rng, target_rg=real_rg)
        null_label = np.zeros(n, dtype=int)
        null_label[null_idx] = 1
        null_aucs[i] = auc(zheng_score, null_label)
    valid_null = null_aucs[np.isfinite(null_aucs)]
    perm_p = float((np.sum(valid_null >= zheng_auc) + 1) / (len(valid_null) + 1)) if len(valid_null) else float("nan")

    result.update({
        "zheng_score_whole_graph_auc": zheng_auc,
        "proximity_floor_aucs": floor_aucs,
        "proximity_floor_max": floor_max,
        "beats_floor": bool(np.isfinite(zheng_auc) and zheng_auc > floor_max),
        "compact_patch_null_p": perm_p,
        "compact_patch_null_mean": float(np.nanmean(null_aucs)),
        "n_null_draws": N_NULL_DRAWS,
    })
    return result


def main() -> int:
    out_dir = Path(__file__).resolve().parent.parent / "results/tasks/0229_004_zheng_nma_baseline"
    out_dir.mkdir(parents=True, exist_ok=True)
    log = RunLogger(out_dir / "run.jsonl", run_name="task0229_004_zheng_nma_baseline")

    out = []
    print(f"{VALIDATION_TARGET}: qualitative validation (Planned Validation, not scored)...", file=sys.stderr)
    v = run_target(VALIDATION_TARGET, log, validation_only=True)
    print(f"{VALIDATION_TARGET}: {v}", file=sys.stderr)
    out.append({"role": "validation", **v})

    if not v.get("ok") or v.get("real_hit_rate", 0.0) <= v.get("decoy_hit_rate", 1.0):
        print(
            f"VALIDATION FAILED: real_hit_rate={v.get('real_hit_rate')} decoy_hit_rate={v.get('decoy_hit_rate')} "
            "-- per-mode sampler does not reproduce the qualitative claim (specific pocket opening beats a matched "
            "decoy) on the known positive control. Stopping before scoring VALID targets, per this task's own "
            "Planned Validation ('reproduce a qualitative claim... before trusting our implementation').",
            file=sys.stderr,
        )
        out_path = out_dir / "results.json"
        out_path.write_text(json.dumps(out, indent=2, default=str))
        log.finish(validation_passed=False)
        return 1

    print("VALIDATION PASSED -- proceeding to scored VALID targets.", file=sys.stderr)
    for name in SCORED_TARGETS:
        print(f"{name}: running (scored)...", file=sys.stderr)
        r = run_target(name, log, validation_only=False)
        print(f"{name}: ok={r.get('ok')} auc={r.get('zheng_score_whole_graph_auc')} elapsed={r.get('elapsed_s')}", file=sys.stderr)
        out.append({"role": "scored", **r})

    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {out_path}")
    log.finish(validation_passed=True, n_scored=len(SCORED_TARGETS))

    print("\n=== summary ===")
    for r in out:
        if not r.get("ok"):
            print(f"[{r['role']}] {r['target']:16s} FAILED: {r.get('reason')}")
            continue
        if r["role"] == "validation":
            print(f"[validation] {r['target']:16s} real_hit_rate={r['real_hit_rate']:.3f} decoy_hit_rate={r['decoy_hit_rate']:.3f}")
        else:
            print(
                f"[scored]     {r['target']:16s} AUC={r['zheng_score_whole_graph_auc']:.3f} "
                f"floor_max={r['proximity_floor_max']:.3f} beats_floor={r['beats_floor']} "
                f"null_p={r['compact_patch_null_p']:.4f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
