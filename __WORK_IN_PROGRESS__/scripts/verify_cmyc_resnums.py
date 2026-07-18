#!/usr/bin/env python3
"""TASK-0125 -- verify c-Myc/1NKP's hit-list residue numbers are real
protein residues, not DNA nucleotide indices leaking through under
`keep_nucleic: true`.

`REVIEW-panel-2026-07-16-v2.md` Sec.5 P2-11: "keep_nucleic: true means
the hit list may be reporting DNA nucleotides; a referee will spot
'residue 943' instantly." Traces every index in TASK-0080's real,
already-produced c-Myc hit list (`results_task0080/MYC_MAX/hit_list.json`)
back through the actual production pipeline (`clean.clean_from_config`)
and directly against 1NKP's raw PDB atom records -- two independent
checks, not just one, per this task's own verification-against-real-data
discipline.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.clean import clean_from_config  # noqa: E402

HIT_LIST_PATH = Path(__file__).resolve().parent.parent / "results_task0080" / "MYC_MAX" / "hit_list.json"
DNA_RESNAMES = {"DA", "DC", "DG", "DT"}
PROTEIN_ATOM_NAMES_SAMPLE = {"CA", "N", "C", "O"}  # any real amino acid has these


def main() -> int:
    import prody
    prody.confProDy(verbosity="none")

    with open(HIT_LIST_PATH) as f:
        hit_list = json.load(f)

    apo = clean_from_config("MYC_MAX", role="apo")
    struct = prody.parsePDB("1NKP", compressed=False)

    print(f"{'idx':>4} {'pipeline resnum':>16} {'pipeline chain':>14} {'pipeline resname':>16} "
          f"{'raw-PDB resname':>15} {'raw-PDB atoms':>30} verdict")

    all_ok = True
    for idx, expected_resnum in zip(hit_list["indices"], hit_list["resnums"]):
        pipeline_resnum = int(apo.resnums[idx])
        pipeline_chain = apo.chain_ids[idx]
        pipeline_resname = apo.resnames[idx]

        raw_sel = struct.select(f"chain {pipeline_chain} and resnum {pipeline_resnum}")
        raw_resnames = set(raw_sel.getResnames()) if raw_sel is not None else set()
        raw_atom_names = set(raw_sel.getNames()) if raw_sel is not None else set()

        is_dna = bool(raw_resnames & DNA_RESNAMES)
        has_protein_backbone = PROTEIN_ATOM_NAMES_SAMPLE.issubset(raw_atom_names)
        resnum_matches = pipeline_resnum == expected_resnum

        ok = resnum_matches and not is_dna and has_protein_backbone and len(raw_resnames) == 1
        all_ok = all_ok and ok
        verdict = "OK -- real protein residue" if ok else "MISMATCH/DNA -- INVESTIGATE"

        print(
            f"{idx:>4} {pipeline_resnum:>16} {pipeline_chain:>14} {pipeline_resname:>16} "
            f"{','.join(raw_resnames):>15} {','.join(sorted(raw_atom_names)):>30} {verdict}"
        )

    print()
    print("ALL HITS VERIFIED CORRECT (real protein residues, native 1NKP numbering)"
          if all_ok else "AT LEAST ONE HIT FAILED VERIFICATION -- see MISMATCH/DNA rows above")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
