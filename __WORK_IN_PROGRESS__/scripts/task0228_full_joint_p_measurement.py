#!/usr/bin/env python3
"""TASK-0228 §6.2 -- full JOINT (backbone collective + rotamer) progress
probability `p`, now that a real rotamer packer and druggability scorer
are confirmed vendored and working (EvoEF2/fpocket -- `Q-0004`'s own
retraction: the earlier "both absent" finding was an inadequate search,
not a real environment gap; commit `fa94316`).

Extends the collective-only measurement (`task0228_progress_probability_
p.py`) with a real ablation: for the SAME admissible collective (ANM)
moves, does REPACKING side chains at the pocket window (EvoEF2
SideChainRepack, restricted to the window, matching TASK-0204's own
already-validated invocation) change how often the move makes progress?

Both conditions score the SAME objective for a fair ablation -- fpocket's
own druggability_score at the pocket window (TASK-0204's own
`score_structure`), NOT the backbone-only RMSD-to-holo objective the
collective-only script used (RMSD is Cα-only by construction, blind to
any rotamer change, so it cannot be reused to isolate rotamer's own
marginal effect). "Progress" = druggability increases relative to the
unmodified apo baseline (druggability is a higher-is-better quantity;
the document's own generic "reduces the objective" phrasing assumes a
minimization framing that does not fit this objective literally).

Coarse-to-all-atom reconstruction: `prody.extendVector` (an existing,
standard ProDy utility, not hand-rolled) broadcasts each residue's own
Cα-level ANM displacement rigidly to every atom in that residue --
verified directly (a synthetic per-residue check) before use here. This
is a real approximation (ignores local backbone/side-chain dihedral
relaxation a true flexible-fitting would capture) and is stated as such,
not hidden.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    import os
    os.environ.setdefault(_v, "4")

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
_SCRIPTS = Path(__file__).resolve().parent
for _p in (_SRC, _SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.holo_direction import build_deformation_family  # noqa: E402
from allostery.labels import build_labels  # noqa: E402

from task0204_rotamer_repack_baseline import (  # noqa: E402
    _run_evoef2, _select_window, score_structure,
)
from task0228_progress_probability_p import P_MEASUREMENT_PROTOCOL, _load_apo_holo  # noqa: E402

TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
DEFAULT_POCKET_CUTOFF = 4.5
MAX_CANDIDATES = 20  # subsample cap for tractability -- see Done section for the full-sample cross-check


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _load_full_atom_and_ca(target_config: dict, apo_chains):
    """Parses the apo PDB once; returns (struct_clean, ca) -- ca is a
    `name CA` sub-selection of struct_clean itself (not independently
    re-parsed), guaranteeing exact atom-index correspondence with
    `struct_clean` for `prody.extendVector`. Same altloc/protein/chain
    filtering as `task0204`'s own `_write_full_atom_apo_pdb`."""
    import prody

    prody.confProDy(verbosity="none")
    struct = prody.parsePDB(target_config["apo_pdb"], compressed=False)
    alt_locs = struct.getAltlocs()
    if alt_locs is not None and any(a not in ("", " ", "\x00") for a in alt_locs):
        struct = struct.select("altloc _ A") or struct
    chain_part = " and (" + " or ".join(f"chain {c}" for c in apo_chains) + ")"
    struct_clean = struct.select(f"protein{chain_part}").copy()
    ca = struct_clean.select("name CA and protein")
    return struct_clean, ca


def _write_displaced_window_pdb(struct_clean, ca, ca_displacement: np.ndarray,
                                 window: list, out_path: Path) -> str:
    """Applies `ca_displacement` (n_ca, 3), rigidly extended to all atoms
    per residue via `prody.extendVector`, then relabels `window` residues
    to chain 'B' and writes in contiguous per-chain blocks (TASK-0204's
    own interleaving-bug workaround, reused unchanged). `ca_displacement`
    of all zeros is a legal no-op (the apo/backbone-unmoved baseline)."""
    import prody

    atoms = struct_clean.copy()
    if np.any(ca_displacement):
        vec = prody.Vector(ca_displacement.astype(float).flatten(), "collective move", True)
        extended, _atommap = prody.extendVector(vec, ca, atoms)
        atoms.setCoords(atoms.getCoords() + extended.getArrayNx3())

    window_set = set(window)
    chids = atoms.getChids()
    resnums = atoms.getResnums()
    new_chids = chids.copy()
    for i in range(len(new_chids)):
        if (chids[i], int(resnums[i])) in window_set:
            new_chids[i] = "B"
    atoms.setChids(new_chids)

    is_window = new_chids == "B"
    other_idx = np.where(~is_window)[0]
    window_idx = np.where(is_window)[0]
    reordered = atoms[other_idx] + atoms[window_idx]
    prody.writePDB(str(out_path), reordered)
    return "B"


def run_one(target_name: str, rng: np.random.Generator) -> dict:
    target_config = load_target_config(target_name)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))

    apo, holo = _load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")

    window = _select_window(apo, labels_obj.pocket)
    apo_chains = target_config.get("apo_chains") or target_config.get("chains")
    struct_clean, ca = _load_full_atom_and_ca(target_config, apo_chains)
    if ca.numAtoms() != len(apo.resnums) or list(zip(ca.getChids(), ca.getResnums())) != list(zip(apo.chain_ids, apo.resnums)):
        raise RuntimeError(
            f"{target_name}: Cα correspondence mismatch between clean_from_config "
            f"({len(apo.resnums)} residues) and the independently-parsed full-atom "
            f"structure ({ca.numAtoms()} CA atoms) -- not safe to extend a "
            "coarse-grained displacement onto this structure"
        )

    family = build_deformation_family(apo.coords, apo.b_mean, protocol=P_MEASUREMENT_PROTOCOL)
    admissible = family["admissible"]
    if len(admissible) == 0:
        raise RuntimeError(f"{target_name}: zero admissible collective moves")
    if len(admissible) > MAX_CANDIDATES:
        idx = rng.choice(len(admissible), size=MAX_CANDIDATES, replace=False)
        sampled = [admissible[i] for i in sorted(idx)]
    else:
        sampled = admissible

    target_set = {("B", r) for (_c, r) in window}

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        baseline_pdb = tmp / "baseline.pdb"
        _write_displaced_window_pdb(struct_clean, ca, np.zeros_like(apo.coords), window, baseline_pdb)
        baseline_score = score_structure(baseline_pdb, target_set, tmp)
        if "error" in baseline_score:
            raise RuntimeError(f"{target_name}: baseline fpocket scoring failed: {baseline_score['error']}")
        baseline_drug = baseline_score["druggability_score"] or 0.0
        _log(f"{target_name}: baseline druggability={baseline_drug:.4f} "
             f"({len(sampled)}/{len(admissible)} admissible moves sampled)")

        rows = []
        for k, entry in enumerate(sampled):
            disp = entry["coords"] - apo.coords
            backbone_pdb = tmp / f"cand{k}_backbone.pdb"
            _write_displaced_window_pdb(struct_clean, ca, disp, window, backbone_pdb)
            backbone_score = score_structure(backbone_pdb, target_set, tmp)
            backbone_drug = (backbone_score.get("druggability_score") or 0.0) if "error" not in backbone_score else None

            repack_out = _run_evoef2("SideChainRepack", backbone_pdb, "B")
            if isinstance(repack_out, dict):
                repack_drug = None
                repack_err = repack_out["error"]
            else:
                repack_score = score_structure(repack_out, target_set, tmp)
                repack_drug = (repack_score.get("druggability_score") or 0.0) if "error" not in repack_score else None
                repack_err = repack_score.get("error")

            rows.append(dict(
                mode=entry["mode"], sign=entry["sign"], scale=entry["scale"],
                backbone_druggability=backbone_drug, repack_druggability=repack_drug,
                repack_error=repack_err,
            ))
            _log(f"{target_name}: cand {k+1}/{len(sampled)} mode={entry['mode']} "
                 f"sign={entry['sign']:+.0f} scale={entry['scale']} "
                 f"backbone_drug={backbone_drug} repack_drug={repack_drug}")

        backbone_vals = [r["backbone_druggability"] for r in rows if r["backbone_druggability"] is not None]
        repack_vals = [r["repack_druggability"] for r in rows if r["repack_druggability"] is not None]
        p_backbone_only = float(np.mean([v > baseline_drug for v in backbone_vals])) if backbone_vals else float("nan")
        p_backbone_plus_repack = float(np.mean([v > baseline_drug for v in repack_vals])) if repack_vals else float("nan")

        result = {
            "target": target_name, "n_residues": len(apo.resnums), "window_size": len(window),
            "n_admissible_total": len(admissible), "n_sampled": len(sampled),
            "baseline_druggability": round(baseline_drug, 4),
            "n_backbone_scored": len(backbone_vals), "n_repack_scored": len(repack_vals),
            "p_backbone_only": round(p_backbone_only, 4) if backbone_vals else None,
            "p_backbone_plus_repack": round(p_backbone_plus_repack, 4) if repack_vals else None,
            "rows": rows,
        }
        _log(f"{target_name}: SUMMARY p_backbone_only={result['p_backbone_only']} "
             f"p_backbone_plus_repack={result['p_backbone_plus_repack']}")
        return result


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=TARGETS)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--output", type=Path,
        default=Path(__file__).resolve().parent.parent / "results/tasks/0228/full_joint_p_measurement.json",
    )
    args = parser.parse_args(argv)
    rng = np.random.default_rng(args.seed)

    results = {}
    for target_name in args.target:
        try:
            results[target_name] = run_one(target_name, rng)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            print(f"{target_name}: FAILED -- {exc!r}")
            results[target_name] = {"target": target_name, "error": str(exc)}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    print("\n=== TASK-0228 full joint p measurement ===")
    for t, r in results.items():
        if "error" in r:
            print(f"{t}: ERROR {r['error']}")
            continue
        print(f"{t}: p_backbone_only={r['p_backbone_only']} "
              f"p_backbone_plus_repack={r['p_backbone_plus_repack']} "
              f"(n={r['n_sampled']}/{r['n_admissible_total']} admissible)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
