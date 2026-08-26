#!/usr/bin/env python3
"""TASK-0271 -- repulsor-constrained SCMF retention test: once a pinned
constraint holding a cryptic pocket open is released, does side-chain
repacking alone (at TRUE native apo backbone geometry) still support a
druggable pocket?

Full pre-registration (citation check, method, retention criterion, fixed
BEFORE any structure was scored) is in this task's own file,
`.ai/tasks/IN_PROGRESS/TASK-0271-*.md` -- not duplicated here except where
needed to make the code self-explaining. Summary of what changed from a
literal spec reading, and why:

This project has no backbone minimiser and no torsion-space (NeRF)
machinery ([[TASK-0235]]'s own docstring). A literal alternating
repack-with-memory SCMF loop cannot be built without either transplanting
EvoEF2-chosen side-chain atoms across differing backbone frames (no
internal-coordinate representation to do that correctly -- risks
fabricating clash artifacts that would masquerade as real hysteresis) or
inventing a backbone force field this register does not have. Neither is
attempted.

What IS run: the pinned repulsor is operationalised as the pre-registered
FULL apo->holo Cα displacement ([[TASK-0230]]/[[TASK-0235]]'s own
`_common_set_and_projection`/`local_rigid_reconstruction`, reused
unchanged) -- the same "hold pocket open" mechanism TASK-0230/0235/0213
already used, extended here with the release arm they never ran. A release
trajectory t in [1.0, 0.75, 0.5, 0.25, 0.0] applies the ABSOLUTE transform
(native apo -> apo + t*disp) at each step -- never compounded -- then runs
EvoEF2 SideChainRepack fresh from native apo's own side chains at that
backbone. At t=0.0 the transform is the identity: this is EvoEF2 repacking
TRUE, unmodified native apo geometry, independently, with no memory of the
open state -- the honest "did we actually release everything" reference
point that this task's retention criterion is evaluated at.

Reuses, does not re-derive: `task0242_two_stage_dryrun.prep` (this
register's own frozen-set pocket/active-site definition, the SAME
definition TASK-0254's crypticity screen used to select these 11 targets
in the first place -- using a different pocket definition here would be
internally inconsistent); `task0230_ceiling_and_brittleness`'s
`_common_set_and_projection`/`_load_full_atom_apo`/
`_write_contiguous_window_chain`/`_run_evoef2`/`score_structure`;
`task0235_local_rigid_backbone`'s `local_rigid_reconstruction`/
`_target_ca_dicts`; `task0204_rotamer_repack_baseline`'s `_select_window`/
`_is_hit`; `task0241_reproducibility_and_jitter`'s `_perturb_disp` (trial
independence, verbatim); `task0261_cluster_robust_stats`'s
`cluster_sign_flip_test` (cluster map overridden to this task's own 11
targets / 8 clusters, algorithm unchanged).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np
import yaml

_SRC = Path(__file__).resolve().parent.parent / "src"
_SCRIPTS = Path(__file__).resolve().parent
for _p in (_SRC, _SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import tempfile  # noqa: E402

import prody  # noqa: E402

# TASK-0243's own real, verified fix, reused verbatim (task0249_composite_
# dumb_baseline.py's own docstring: "NAMPT_NPA1R's own real defect"):
# without altloc="all", NAMPT_NPA1R's holo ligand atoms fail to resolve and
# `t0242.prep`'s own `holo_pocket_mask` returns None, crashing downstream
# (confirmed directly: this task's own first run crashed on exactly this
# target with exactly this TypeError before this patch was added).
_orig_parsePDB = prody.parsePDB


def _parsePDB_all_altloc(*a, **kw):
    kw.setdefault("altloc", "all")
    return _orig_parsePDB(*a, **kw)


prody.parsePDB = _parsePDB_all_altloc

import task0242_two_stage_dryrun as t0242  # noqa: E402
from allostery.clean import clean_from_config  # noqa: E402

from task0230_ceiling_and_brittleness import (  # noqa: E402
    _common_set_and_projection,
    _load_full_atom_apo,
    _log,
    _run_evoef2,
    _write_contiguous_window_chain,
    score_structure,
)
from task0204_rotamer_repack_baseline import (  # noqa: E402
    DRUGGABILITY_BAR,
    POCKET_HIT_OVERLAP,
    WINDOW_MAX_SIZE,
    _is_hit,
    _select_window,
)
from task0235_local_rigid_backbone import (  # noqa: E402
    LOCAL_WINDOW,
    _target_ca_dicts,
    local_rigid_reconstruction,
)
from task0241_reproducibility_and_jitter import _perturb_disp  # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
t0242.CAND = yaml.safe_load(FROZEN_CONFIG.read_text())["targets"]

# The 11 "already_open: false" targets from TASK-0254 Part B's own
# pre-registered crypticity screen (results/tasks/0254_fpocket_variance_
# and_crypticity/part_b_crypticity.json) -- the genuinely cryptic-testing
# subset this task's own Scope names explicitly (already-open targets
# cannot test collapse; nothing to collapse).
TARGETS = [
    "DHPS_GC7", "KSHV_PROTEASE_24Q", "KSHV_PROTEASE_25G", "SUMO_E1_FHJ",
    "HCV_NS5B_POO", "HCV_NS5B_CMF", "FBPASE_94D", "FBPASE_95S",
    "TRP_SYNTHASE_F19", "MKK7_IBRUTINIB", "NAMPT_NPA1R",
]
# target -> cluster (shared apo PDB), verified directly against
# candidate_targets_task0243.yaml, not assumed -- 8 clusters over 11 targets.
CLUSTER_OF = {
    "DHPS_GC7": "single_DHPS_GC7",
    "KSHV_PROTEASE_24Q": "pair_2PBK", "KSHV_PROTEASE_25G": "pair_2PBK",
    "SUMO_E1_FHJ": "single_SUMO_E1_FHJ",
    "HCV_NS5B_POO": "pair_2HAI", "HCV_NS5B_CMF": "pair_2HAI",
    "FBPASE_94D": "pair_5LDZ", "FBPASE_95S": "pair_5LDZ",
    "TRP_SYNTHASE_F19": "single_TRP_SYNTHASE_F19",
    "MKK7_IBRUTINIB": "single_MKK7_IBRUTINIB",
    "NAMPT_NPA1R": "single_NAMPT_NPA1R",
}

RELEASE_STEPS = [1.0, 0.75, 0.5, 0.25, 0.0]  # 1.0 = held open, 0.0 = fully released
DECISIVE_STEPS = {1.0, 0.0}  # full N_TRIALS replication; others: 1 representative trial
N_TRIALS = 4  # this register's own established multi-trial convention (TASK-0230/0235)
PERTURB_SIGMA = 0.15  # Angstrom, TASK-0241's own established nuisance-perturbation magnitude


def _build_target(name: str):
    """cfg (with pocket_contact_cutoff etc.), apo (Cα, TASK-0243's own
    frozen-set pocket/active-site definition via t0242.prep), window
    (<=12 residues, pocket-centroid-nearest), full apo->holo Cα
    displacement on the common set."""
    cfg, apo, seed, pocket = t0242.prep(name)
    if pocket is None or not np.asarray(pocket).any():
        raise RuntimeError(f"{name}: no resolvable pocket label from t0242.prep")
    window = _select_window(apo, np.asarray(pocket), max_size=WINDOW_MAX_SIZE)
    holo = clean_from_config(name, role="holo")
    alignment, full_disp, _proj_disp, delta_r, _k_used = _common_set_and_projection(apo, holo, cfg)
    apo_chains = cfg.get("apo_chains") or cfg.get("chains")
    return cfg, apo, alignment, full_disp, window, apo_chains, float(np.linalg.norm(delta_r))


def _trial_hash(disp: dict) -> str:
    keys = sorted(disp.keys())
    blob = np.concatenate([np.asarray(disp[k]) for k in keys]).tobytes()
    return hashlib.md5(blob).hexdigest()[:12]


def _run_one_step(cfg, apo, alignment, full_disp, window, apo_chains, t: float, seed: int, tmp: Path, tag: str) -> dict:
    """Absolute (never-compounded) backbone transform at fraction t of the
    full apo->holo displacement, fresh from native apo's OWN side chains,
    then one independent EvoEF2 SideChainRepack. t=0.0 => identity
    transform => true native apo, repacked with no memory of any open
    state."""
    disp_t = _perturb_disp(full_disp, PERTURB_SIGMA, seed)
    disp_t = {k: v * t for k, v in disp_t.items()}
    trial_hash = _trial_hash(disp_t)

    struct = _load_full_atom_apo(cfg, apo_chains)
    apo_ca, target_ca = _target_ca_dicts(apo, alignment, disp_t)
    struct = local_rigid_reconstruction(struct, apo_ca, target_ca, window=LOCAL_WINDOW)
    pdb = tmp / f"{tag}.pdb"
    design_chain = _write_contiguous_window_chain(struct, window, pdb)
    time.sleep(1.05)  # EvoEF2 seeds via time(NULL); forces a distinct RNG seed per call
    repacked = _run_evoef2("SideChainRepack", pdb, design_chain)
    if isinstance(repacked, dict):
        return {"t": t, "trial_hash": trial_hash, "error": repacked["error"]}
    target_set = {(design_chain, r) for (_c, r) in window}
    score = score_structure(repacked, target_set, tmp)
    hit = _is_hit(score.get("overlap_frac", 0.0), score.get("druggability_score"))
    return {"t": t, "trial_hash": trial_hash, **score, "hit": bool(hit)}


def run_target(name: str) -> dict:
    _log(f"{name}: building target (pocket window, apo->holo displacement)...")
    cfg, apo, alignment, full_disp, window, apo_chains, disp_norm = _build_target(name)
    _log(f"{name}: window={len(window)} residues, |apo->holo full displacement|={disp_norm:.3f} A")

    result = {"target": name, "window": window, "disp_norm": disp_norm, "steps": {}}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for t in RELEASE_STEPS:
            n_trials = N_TRIALS if t in DECISIVE_STEPS else 1
            trials = []
            for i in range(n_trials):
                seed = hash((name, t, i)) % (2**32)
                # EvoEF2's own internal filename parsing splits on the FIRST
                # '.', not the last (confirmed directly: a tag containing a
                # literal decimal point, e.g. "_t1.0_", silently truncated its
                # own output filename and made `_run_evoef2` report a false
                # "exited 0, no output" error) -- tag must be dot-free.
                t_tag = f"{int(round(t * 100)):03d}pct"
                r = _run_one_step(cfg, apo, alignment, full_disp, window, apo_chains, t, seed, tmp, f"{name.lower()}_t{t_tag}_{i}")
                trials.append(r)
                _log(f"{name}: t={t} trial {i} (hash={r.get('trial_hash')}): {r}")
            result["steps"][str(t)] = trials

    t0_trials = [r for r in result["steps"]["0.0"] if "error" not in r]
    t1_trials = [r for r in result["steps"]["1.0"] if "error" not in r]
    n_hit_t0 = sum(1 for r in t0_trials if r["hit"])
    n_hit_t1 = sum(1 for r in t1_trials if r["hit"])
    verdict = None
    if t0_trials:
        # pre-registered rule: majority (>=3/4) of t=0.0 trials clear _is_hit
        verdict = "PERSISTS" if n_hit_t0 >= 3 else "COLLAPSES"
    result["summary"] = {
        "n_hit_t1.0_of": f"{n_hit_t1}/{len(t1_trials)}" if t1_trials else "0/0",
        "n_hit_t0.0_of": f"{n_hit_t0}/{len(t0_trials)}" if t0_trials else "0/0",
        "verdict_prereg_rule": verdict,
        "distinct_trial_hashes_t0": len(set(r["trial_hash"] for r in result["steps"]["0.0"])),
        "distinct_trial_hashes_t1": len(set(r["trial_hash"] for r in result["steps"]["1.0"])),
    }
    _log(f"{name}: SUMMARY {result['summary']}")
    return result


def main() -> int:
    out = {"targets": {}}
    for name in TARGETS:
        try:
            out["targets"][name] = run_target(name)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            out["targets"][name] = {"target": name, "error": f"{type(exc).__name__}: {exc}"}

    out_dir = _ROOT / "results/tasks/0271_repulsor_scmf_retention"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {out_dir / 'results.json'}")

    print("\n=== TASK-0271 per-target verdicts ===")
    for name in TARGETS:
        r = out["targets"].get(name, {})
        s = r.get("summary", {})
        print(f"{name} ({CLUSTER_OF[name]}): {s.get('verdict_prereg_rule')} "
              f"t=0.0 {s.get('n_hit_t0.0_of')}  t=1.0 {s.get('n_hit_t1.0_of')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
