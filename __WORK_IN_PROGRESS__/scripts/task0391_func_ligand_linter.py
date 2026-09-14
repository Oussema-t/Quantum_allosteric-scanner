#!/usr/bin/env python3
"""TASK-0391 (diagnostics only, per this task's own explicit Phase-2/
post-deadline scoping for the actual data fix -- option 3 in the task
filing) -- a config-time linter for `func_ligand` vs. what each target's
own deposited structures actually carry.

Scope, decided at pickup time (the task's own filing left this open):
implement options 1+2 only (diagnostics, change no shipped numbers), not
option 3 (correcting `func_ligand` and re-running/re-shipping affected
hit lists/AUCs/matrices) -- that stays explicitly deferred to after the
Phase-1 deadline, matching [[TASK-0386]]'s own decision not to touch
shipped numbers this close to submission.

WHAT THIS CATCHES, precisely -- and a correction to [[TASK-0386]]'s own
root-cause framing, found while building this (see the module-level
finding below): [[TASK-0386]]'s `targets.yaml` note says BCR_ABL1's
`func_ligand: ["NIL"]` "finds no match on this target and falls through
silently." **Verified directly against the real pipeline
(`allostery.labels.build_labels`) before trusting that claim, and it is
not quite right**: `functional_indices` resolves BCR_ABL1 via
`func_ligand-contact:NIL`, not a fallback -- NIL IS present in the HOLO
structure (`5MO4`), and TASK-0217.001's own cross-structure translation
(Needleman-Wunsch-mapped heavy atoms) lets a holo-only ligand exclude
residues in `coords`' (apo's) own index space. Tier 1 does not fall
through for BCR_ABL1; it succeeds, just on the wrong (translated,
holo-native) geometry. `apo.ligand_groups` is empty for every target in
this pipeline (apo cleaning does not extract ligands at all), so
`functional_indices` can never check contacts against `1OPL`'s own,
apo-native second inhibitor (`P16`) directly -- P16 is not in
`func_ligand` at all, so it is never considered by any tier, holo or
apo. Confirmed the practical consequence directly: of the 26 residues
NIL-contact excludes, 337 and 340 are in, but **338 -- the actual
shipped #5 hit, TASK-0385's "gatekeeper" finding -- is not**, sitting
just outside the translated-NIL cutoff though it is real-space close to
apo's own P16. The outcome TASK-0385/TASK-0386 measured (338 not
excluded) is real and independently verified by direct distance
measurement in `Solution_Outputs.md` Sec.2 (unaffected by this
correction); the MECHANISM is "func_ligand's declared code list is
incomplete for this target, not that tier 1 fails to match at all."
That is exactly the same shape as CARDIAC_MYOSIN's already-diagnosed
case (`VO4` simply absent from `func_ligand: ["ADP","ATP"]`) -- both are
"the declared list omits a real ligand actually present," not "declared
codes fail to resolve." This linter is built to catch THAT shape
directly and generally, not the narrower "did tier 1 return nothing"
question TASK-0391's own option 1 was originally framed around (which
would have silently missed BCR_ABL1, since tier 1 does return
something).

FOR EACH TARGET WITH A NON-EMPTY, CODE-LOOKING `func_ligand`:
  1. Fetch `apo_pdb` and `holo_pdb` (if present) directly from the local
     PDB cache / RCSB (`backend.data_layer.fetch`, the same route every
     other script in this register uses -- not re-implemented).
  2. Parse each structure's own distinct HETATM chem-comp codes (minus
     the 20 standard amino acids + selenomethionine + water), by raw
     ATOM/HETATM line parsing -- deliberately NOT via the pipeline's own
     `ligand_groups` (which, per the finding above, is empty for apo),
     so this linter reads the ground truth directly rather than through
     the same lossy path it is auditing.
  3. Report, per declared code: found in apo / found in holo only /
     found nowhere (a real typo or wrong-code case, worse than either of
     the two known instances).
  4. Report apo's own HETATM codes NOT covered by any declared
     `func_ligand` code, after excluding a short, explicit denylist of
     inert crystallisation/cryoprotectant additives (listed below, not
     silently assumed) -- this is what would have caught BOTH known
     instances (`P16` for BCR_ABL1, `VO4` for CARDIAC_MYOSIN) before
     they shipped, and is run here across every target in the register,
     not just the two TASK-0386 happened to check by hand.

Descriptive-text `func_ligand` entries (e.g. PTP1B's "pTyr / active-site
Cys215 (descriptive marker, not a ligand code)", MYC_MAX's "DNA") are
detected by a simple code-shape heuristic (1-4 uppercase alphanumeric
characters, PDB chem-comp convention) and reported as N/A -- descriptive
marker, not scored as a miss, matching `functional_indices`'s own
documented convention that these are not treated as an error.

Read-only: makes no change to `targets.yaml`, `func_ligand`, or any
shipped result. Per this task's own Constraint.

Run: ../.venv/bin/python3 -u scripts/task0391_func_ligand_linter.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
RESULTS = HERE.parent / "results" / "tasks" / "0391_func_ligand_linter"
RESULTS.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(REPO_ROOT))
from backend.data_layer import fetch  # noqa: E402

AA3 = {"ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
       "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
       "MSE"}
WATER = {"HOH", "WAT", "DOD"}

# Explicit, conservative denylist of common crystallisation/cryoprotectant
# additives with no plausible functional-site role -- NOT metals or
# nucleotide-family codes, which can be genuinely catalytic and must be
# judged, not silently dropped. Extend deliberately, never by guessing.
INERT_ADDITIVES = {
    "GOL",   # glycerol, cryoprotectant
    "EDO",   # ethylene glycol, cryoprotectant
    "PEG", "PG4", "1PE", "P6G",  # polyethylene glycol variants
    "DMS",   # DMSO
    "MPD",   # 2-methyl-2,4-pentanediol, cryoprotectant
    "BME",   # beta-mercaptoethanol, reducing agent
    "ACT",   # acetate ion, buffer
    "TRS",   # Tris buffer
    "SO4", "PO4",  # buffer ions
    "IPA",   # isopropanol
    "FMT",   # formate
    "CIT",   # citrate buffer
    "UNK", "UNX",  # unknown / unmodelled density
}

CODE_RE = re.compile(r"^[A-Z0-9]{1,4}$")


def chain_hetatm_codes(pdb_path: Path) -> set[str]:
    codes: set[str] = set()
    for line in pdb_path.read_text(errors="replace").splitlines():
        if line.startswith("ENDMDL"):
            break
        rec = line[:6].strip()
        if rec not in ("ATOM", "HETATM") or len(line) < 20:
            continue
        resname = line[17:20].strip()
        if rec == "HETATM" and resname not in WATER and resname not in AA3:
            codes.add(resname)
    return codes


def lint_target(name: str, cfg: dict) -> dict:
    func_ligand = cfg.get("func_ligand") or []
    apo_pdb = cfg.get("apo_pdb")
    holo_pdb = cfg.get("holo_pdb")

    out = dict(target=name, apo_pdb=apo_pdb, holo_pdb=holo_pdb,
               func_ligand=func_ligand, code_status={}, apo_undeclared=[],
               notes=[])

    if not func_ligand:
        out["notes"].append("func_ligand empty -- not scored, deliberate per TASK-0216")
        return out

    real_codes = [c for c in func_ligand if CODE_RE.match(c)]
    descriptive = [c for c in func_ligand if not CODE_RE.match(c)]
    for c in descriptive:
        out["code_status"][c] = "N/A -- descriptive marker, not a chem-comp code"

    if not apo_pdb:
        out["notes"].append("no apo_pdb declared -- cannot check")
        return out

    apo_path = fetch(apo_pdb, raise_on_error=False)
    if not apo_path:
        out["notes"].append(f"could not fetch apo_pdb {apo_pdb!r}")
        return out
    apo_codes = chain_hetatm_codes(Path(apo_path))

    holo_codes: set[str] = set()
    if holo_pdb:
        holo_path = fetch(holo_pdb, raise_on_error=False)
        if holo_path:
            holo_codes = chain_hetatm_codes(Path(holo_path))
        else:
            out["notes"].append(f"could not fetch holo_pdb {holo_pdb!r}")

    for c in real_codes:
        in_apo = c in apo_codes
        in_holo = c in holo_codes
        if in_apo:
            out["code_status"][c] = "OK -- present in apo directly"
        elif in_holo:
            out["code_status"][c] = (
                "WARN -- found only in holo, not apo; functional_indices "
                "resolves this via cross-structure (Needleman-Wunsch) "
                "translation, not apo-native contact geometry -- a weaker "
                "geometric argument than a direct apo match, and the exact "
                "mechanism behind BCR_ABL1's NIL/338 near-miss"
            )
        else:
            out["code_status"][c] = "FAIL -- found in neither apo nor holo (check the code)"

    declared_set = set(real_codes)
    undeclared = sorted(apo_codes - declared_set - INERT_ADDITIVES)
    out["apo_undeclared"] = undeclared
    if undeclared:
        out["notes"].append(
            f"apo carries {len(undeclared)} HETATM code(s) not covered by any "
            f"declared func_ligand entry and not on the inert-additive "
            f"denylist: {undeclared} -- each needs a human judgement call "
            f"(genuinely irrelevant crystallisation artefact vs. a second "
            f"functional ligand like BCR_ABL1's P16 or CARDIAC_MYOSIN's VO4)"
        )
    return out


def main() -> int:
    cfg_path = HERE.parent / "config" / "targets.yaml"
    all_cfg = yaml.safe_load(cfg_path.read_text())
    targets = all_cfg.get("targets", all_cfg)

    results = {}
    for name, cfg in targets.items():
        if not isinstance(cfg, dict) or "apo_pdb" not in cfg:
            continue
        print(f"=== {name} ===")
        r = lint_target(name, cfg)
        results[name] = r
        if r["code_status"]:
            for code, status in r["code_status"].items():
                print(f"  {code}: {status}")
        for note in r["notes"]:
            print(f"  NOTE: {note}")

    out_path = RESULTS / "result.json"
    out_path.write_text(json.dumps(results, indent=1))
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
