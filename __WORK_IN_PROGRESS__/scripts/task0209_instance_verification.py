"""TASK-0209 -- verify the apo(closed)->holo(open) contrast every
cryptic-pocket experiment in this register has assumed, per target, and
flag any endogenous HETATM sitting in the pocket window that would explain
a failure the way BCR_ABL1's bound MYR did ([[TASK-0204]] reopened).

Two legs, both required:

  1. Endogenous-HETATM-near-pocket audit -- enumerate every non-water
     HETATM in the RAW (pre-`select("protein")`) apo structure and flag any
     within `pocket_contact_cutoff` of the target's own pocket window. A
     grep-level check that would have caught BCR_ABL1's MYR before any
     downstream number was ever computed on it.
  2. The positive-control ladder ([[TASK-0204]] reopened,
     `task0204_positive_control.run_target`, reused verbatim, not
     reimplemented) -- `holo_native`/`holo_greedy`/`holo_optimized`/
     `apo_native`, run on every target with a usable apo/holo pair
     (`targets.yaml` entries with both `apo_pdb` and `holo_pdb` set --
     MYC_MAX has no holo and is excluded, not silently skipped).

VALID/INVALID verdict per the threshold pre-registered in this task's own
file (`.ai/tasks/DONE/TASK-0209-*.md` or `.ai/tasks/IN_PROGRESS/` if still
open -- check `.ai/COMMON.md`), BEFORE this script was run against the 11
targets beyond the two already-known KRAS_G12C/BCR_ABL1 answers:

    VALID iff NOT apo_native_hit AND holo_native_hit

reusing `task0204_rotamer_repack_baseline._is_hit`'s own criterion
(overlap_frac >= 0.5 AND druggability_score >= 0.5), not a new bar.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
_SCRIPTS = _ROOT / "scripts"
_TESTS = _ROOT / "tests"
for _p in (_SRC, _SCRIPTS, _TESTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import task0204_positive_control as _t0204pc  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.labels import build_labels, ligand_groups_from_atomgroup  # noqa: E402
from task0204_positive_control import run_target as run_positive_control_ladder  # noqa: E402
from task0204_rotamer_repack_baseline import _load_apo_holo  # noqa: E402

OUT_DIR = _ROOT / "results/tasks/0209_instance_verification"

# "Usable apo/holo pair" narrowed to targets.yaml entries with a genuine
# small-molecule `drug_ligand` code -- checked directly against every one of
# the 13 apo_pdb/holo_pdb-complete entries, not assumed. Excludes 6: ATCase,
# HEMOGLOBIN, TAR_RECEPTOR, GLYCOGEN_PHOSPHORYLASE, PFK have no `drug_ligand`
# field at all (they are classical-allostery targets used elsewhere in the
# register for a different purpose, not cryptic-druggable-pocket
# benchmarks); GROEL_SUBUNIT's `drug_ligand` is GroES, a protein, with its
# own config comment stating the drug-contact pocket definition does not
# apply. None of the six have a derivable "druggable pocket to be
# open/closed" in the first place, so the apo-closed/holo-open contrast
# this task verifies is not a meaningful question for them -- out of scope,
# not an error, and reported as excluded below rather than silently dropped.
TARGETS = [
    "KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "PTP1B", "GLUCOKINASE",
    "CASPASE1", "CASPASE7",
]
EXCLUDED_NO_DRUG_LIGAND = {
    "ATCase": "no drug_ligand set",
    "HEMOGLOBIN": "no drug_ligand set",
    "TAR_RECEPTOR": "no drug_ligand set",
    "GLYCOGEN_PHOSPHORYLASE": "no drug_ligand set",
    "PFK": "no drug_ligand set",
    "GROEL_SUBUNIT": "drug_ligand is GroES, a protein -- config's own comment: "
                      "drug-contact pocket definition does not apply cleanly",
    "MYC_MAX": "no holo_pdb set -- no apo/holo pair to contrast at all",
}


def _pick_unused_chain_letter(existing_chids) -> str:
    """A letter not already present among `existing_chids`, preferring 'B'
    when it is actually free (matches the original convention for the
    common case). Real bug found and fixed here, not in
    `task0204_positive_control.py`/`task0204_rotamer_repack_baseline.py`
    themselves (both currently under another thread's active claim,
    TASK-0204 reopened -- flagged for that thread in this task's own Done
    section instead of edited out from under it): both scripts hardcode
    'B' as the window's relabeled chain letter, silently assuming no
    existing chain in the selected structure is already called 'B'. That
    assumption holds for KRAS_G12C/BCR_ABL1 (`chains: ["A"]`) but breaks
    for CARDIAC_MYOSIN, whose holo structure is `holo_chains: ["B"]` --
    relabeling the window to 'B' is then a no-op collision, `is_window`
    matches every atom in the structure (not just the window), and
    `struct[~is_window]` is empty, confirmed directly via the resulting
    IndexError (`index 0 is out of bounds for axis 0 with size 0`) before
    this fix.
    """
    existing = set(existing_chids)
    for candidate in "BCDEFGHIJKLMNOPQRSTUVWXYZ":
        if candidate not in existing:
            return candidate
    raise RuntimeError("no unused chain letter available (structure uses all of B-Z)")


def _write_full_atom_with_window_chain_fixed(pdb_id: str, keep_chains, window: list, out_path: Path) -> str:
    """`task0204_positive_control._write_full_atom_with_window_chain` with
    the chain-letter-collision bug (above) fixed: the window's relabel
    letter is chosen to be genuinely unused in the selected structure,
    not hardcoded to 'B'. Every other behaviour, including the
    contiguous-per-chain-block write order, is preserved verbatim.
    """
    import prody

    prody.confProDy(verbosity="none")
    struct = prody.parsePDB(pdb_id, compressed=False)
    alt_locs = struct.getAltlocs()
    if alt_locs is not None and any(a not in ("", " ", "\x00") for a in alt_locs):
        struct = struct.select("altloc _ A") or struct
    chain_part = " and (" + " or ".join(f"chain {c}" for c in keep_chains) + ")"
    struct_clean = struct.select(f"protein{chain_part}").copy()

    chids = struct_clean.getChids()
    window_letter = _pick_unused_chain_letter(chids)
    window_set = set(window)
    resnums = struct_clean.getResnums()
    new_chids = chids.copy()
    for i in range(len(new_chids)):
        if (chids[i], int(resnums[i])) in window_set:
            new_chids[i] = window_letter
    struct_clean.setChids(new_chids)

    is_window = new_chids == window_letter
    reordered = struct_clean[np.where(~is_window)[0]] + struct_clean[np.where(is_window)[0]]
    prody.writePDB(str(out_path), reordered)
    return window_letter


_t0204pc._write_full_atom_with_window_chain = _write_full_atom_with_window_chain_fixed


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def audit_hetatm_near_pocket(name: str, cfg: dict) -> dict:
    """Every non-water HETATM group in the RAW apo deposition, with its
    minimum distance to the target's own apo-frame pocket window (protein
    heavy atoms only) -- flagged if within `pocket_contact_cutoff`.

    `drug_ligand`/`func_ligand` matches are labelled `expected` (the
    audit's job is to catch an UNEXPECTED occupant like MYR, not to
    re-flag ligands the config already knows about and excludes via
    `build_labels`'s own active-site exclusion).
    """
    import prody

    prody.confProDy(verbosity="none")
    apo, holo = _load_apo_holo(name, cfg)
    pocket_cutoff = float(cfg.get("pocket_contact_cutoff", 4.5))
    labels_obj = build_labels(apo, holo, cfg, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        return {"error": "no resolvable apo-frame pocket label"}
    window_idx = np.where(labels_obj.pocket)[0]
    window_resnums = set(int(r) for r in np.asarray(apo.resnums)[window_idx])

    apo_chains = cfg.get("apo_chains") or cfg.get("chains")
    chain_sel = " or ".join(f"chain {c}" for c in apo_chains)
    raw = prody.parsePDB(cfg["apo_pdb"], compressed=False).select(chain_sel)
    if raw is None:
        return {"error": "no atoms after chain selection on raw apo deposition"}

    window_coords = raw.select(
        "protein and not hetero and (" + " or ".join(f"resnum {r}" for r in window_resnums) + ")"
    )
    if window_coords is None:
        return {"error": "pocket window residues not found in raw apo deposition (numbering mismatch?)"}
    window_xyz = window_coords.getCoords()

    known = {cfg.get("drug_ligand"), *((cfg.get("func_ligand") or []) if isinstance(cfg.get("func_ligand"), list) else [cfg.get("func_ligand")])}
    known.discard(None)

    groups = ligand_groups_from_atomgroup(raw)
    # A group within ionic/covalent coordination range (~2-2.6 A for a
    # metal-oxygen bond, e.g. Mg-GDP measured directly at 2.05 A on
    # KRAS_G12C's own apo deposition) of a KNOWN ligand is that ligand's
    # own cofactor (Mg2+ coordinating GDP's phosphates), not an
    # independent, unexplained occupant -- flagging it as "unexpected"
    # alongside a real finding like BCR_ABL1's MYR would bury the signal
    # in noise on every metal-dependent target. 3.0 A gives headroom above
    # the measured bond length without reaching typical VdW-contact range
    # (~3.5-4.5 A), so a genuinely separate binder near a known ligand
    # still gets flagged.
    known_groups = [g for g in groups if g.resname in known]
    findings = []
    for g in groups:
        d = np.linalg.norm(window_xyz[:, None, :] - g.coords[None, :, :], axis=-1)
        min_dist = float(d.min())
        is_known = g.resname in known
        cofactor_of = None
        if not is_known:
            for kg in known_groups:
                dk = np.linalg.norm(g.coords[:, None, :] - kg.coords[None, :, :], axis=-1)
                if float(dk.min()) <= 3.0:
                    cofactor_of = kg.resname
                    break
        findings.append({
            "resname": g.resname, "resnum": g.resnum, "chain": g.chain,
            "min_dist_to_pocket_window": round(min_dist, 2),
            "near_pocket": min_dist <= pocket_cutoff,
            "expected": is_known,
            "cofactor_of_known_ligand": cofactor_of,
        })
    findings.sort(key=lambda f: f["min_dist_to_pocket_window"])
    flagged = [f for f in findings if f["near_pocket"] and not f["expected"] and not f["cofactor_of_known_ligand"]]
    return {
        "pocket_contact_cutoff": pocket_cutoff,
        "all_hetatm_groups": findings,
        "unexpected_near_pocket": flagged,
    }


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    results: dict = {"_excluded": EXCLUDED_NO_DRUG_LIGAND}
    for name in TARGETS:
        _log(f"=== {name} ===")
        cfg = load_target_config(name)
        entry: dict = {"target": name}

        _log(f"{name}: HETATM audit...")
        try:
            entry["hetatm_audit"] = audit_hetatm_near_pocket(name, cfg)
        except Exception as exc:  # noqa: BLE001
            entry["hetatm_audit"] = {"error": f"{type(exc).__name__}: {exc}"}
        _log(f"{name}: audit unexpected-near-pocket = "
             f"{entry['hetatm_audit'].get('unexpected_near_pocket', entry['hetatm_audit'].get('error'))}")

        _log(f"{name}: positive-control ladder...")
        try:
            entry["ladder"] = run_positive_control_ladder(name)
        except Exception as exc:  # noqa: BLE001
            entry["ladder"] = {"target": name, "error": f"{type(exc).__name__}: {exc}"}

        ladder = entry["ladder"]
        if "error" not in ladder:
            s = ladder["summary"]
            apo_hit = s["apo_native_hit"]
            holo_hit = s["holo_native_hit"]
            valid = bool((apo_hit is False) and (holo_hit is True))
            entry["verdict"] = "VALID" if valid else "INVALID"
        else:
            entry["verdict"] = "ERROR"
        _log(f"{name}: verdict = {entry['verdict']}")

        results[name] = entry
        (OUT_DIR / "instance_verification.json").write_text(json.dumps(results, indent=1, default=str))

    print("\n=== TASK-0209 instance verification ===")
    print("Excluded (no usable drug_ligand):")
    for name, reason in EXCLUDED_NO_DRUG_LIGAND.items():
        print(f"  {name}: {reason}")
    for name, r in results.items():
        if name == "_excluded":
            continue
        ladder = r.get("ladder", {})
        s = ladder.get("summary", {}) if "error" not in ladder else {}
        audit = r.get("hetatm_audit", {})
        flagged = audit.get("unexpected_near_pocket", []) if "error" not in audit else "AUDIT-ERROR"
        print(f"{name:24s} verdict={r['verdict']:8s} "
              f"apo_native_hit={s.get('apo_native_hit')} holo_native_hit={s.get('holo_native_hit')} "
              f"unexpected_hetatm={[f['resname'] for f in flagged] if isinstance(flagged, list) else flagged}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
