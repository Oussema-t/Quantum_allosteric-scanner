#!/usr/bin/env python3
"""TASK-0039 -- pre-implementation review: does any current benchmark
target actually exercise a non-'A'-majority alt-loc case today?

Fetches every apo_pdb/holo_pdb in targets.yaml, checks getAltlocs() for
any non-blank label, and where alt-locs exist, compares mean occupancy
per label to see whether 'A' is genuinely the highest-occupancy
conformer (the common case the code already handles correctly) or
whether a non-'A' label would actually win under a real occupancy
comparison (the latent bug this task's own docstring promise is about)."""
from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import numpy as np
import prody
import yaml

prody.confProDy(verbosity="none")

CONFIG = Path(__file__).resolve().parent.parent / "config" / "targets.yaml"


def survey_pdb(pdb_id: str) -> dict:
    try:
        struct = prody.parsePDB(pdb_id, altloc="all", compressed=False)
    except Exception as exc:  # noqa: BLE001
        return {"pdb_id": pdb_id, "error": repr(exc)}
    if struct is None:
        return {"pdb_id": pdb_id, "error": "parsePDB returned None"}

    alt_locs = struct.getAltlocs()
    if alt_locs is None:
        return {"pdb_id": pdb_id, "has_altloc": False}
    present = sorted(set(a for a in alt_locs if a not in ("", " ", "\x00")))
    if not present:
        return {"pdb_id": pdb_id, "has_altloc": False}

    occ = struct.getOccupancies()
    chids = struct.getChids()
    resnums = struct.getResnums()

    # For each (chain, resnum) with >1 altloc, find which label has the
    # highest mean occupancy -- does 'A' always win?
    non_a_wins = []
    by_res = {}
    for i in range(len(alt_locs)):
        a = alt_locs[i]
        if a in ("", " ", "\x00"):
            continue
        key = (str(chids[i]), int(resnums[i]))
        by_res.setdefault(key, {}).setdefault(a, []).append(occ[i])

    for key, label_occ in by_res.items():
        if len(label_occ) < 2:
            continue
        means = {lab: float(np.mean(vals)) for lab, vals in label_occ.items()}
        best_label = max(means, key=means.get)
        if best_label != "A" and means[best_label] > means.get("A", -1):
            non_a_wins.append({"residue": key, "means": means, "winner": best_label})

    return {
        "pdb_id": pdb_id, "has_altloc": True, "altloc_labels_present": present,
        "n_multi_altloc_residues": len(by_res),
        "non_a_wins": non_a_wins,
    }


def main() -> int:
    data = yaml.safe_load(CONFIG.read_text())
    pdbs = set()
    for name, cfg in data["targets"].items():
        for k in ("apo_pdb", "holo_pdb"):
            v = cfg.get(k)
            if v:
                pdbs.add(v)

    results = []
    for pdb_id in sorted(pdbs):
        r = survey_pdb(pdb_id)
        results.append(r)
        tag = "ERROR" if "error" in r else ("ALTLOC" if r.get("has_altloc") else "clean")
        extra = ""
        if r.get("has_altloc"):
            extra = f" labels={r['altloc_labels_present']} multi_res={r['n_multi_altloc_residues']} non_a_wins={len(r['non_a_wins'])}"
        print(f"{pdb_id}: {tag}{extra}")

    flagged = [r for r in results if r.get("non_a_wins")]
    print(f"\n{len(flagged)} of {len(results)} PDBs have a residue where a non-'A' label has higher mean occupancy than 'A'.")
    for r in flagged:
        print(f"  {r['pdb_id']}: {r['non_a_wins']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
