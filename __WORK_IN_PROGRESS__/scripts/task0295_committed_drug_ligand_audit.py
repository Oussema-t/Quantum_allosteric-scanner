"""TASK-0295 -- could `classify_ligand`'s degraded mode have already mis-set
a committed `drug_ligand`?

[[TASK-0294]]'s audit named `backend/rcsb.py`'s `classify_ligand` as the
highest-stakes silent-fallback in the scientific path: when
`_chem_comp_record` returns `None` (any RCSB chemcomp network/JSON
failure, swallowed by `_get_json`'s bare `except Exception`), the
function degrades to a heavy-atom-count-only heuristic with no formula,
no drug-DB cross-references, and no aliphatic/lipid check. The return
value is indistinguishable from a fully-informed classification.

`classify_ligand` drives which ligand becomes a target's committed
`drug_ligand:`. A degraded curation run could therefore have committed
the wrong ground-truth pocket, leaving no trace.

THE HISTORICAL QUESTION FIRST (this task's own Constraint): did that
already happen? Remediation comes after, and is NOT done here.

METHOD. The two code paths are read directly out of `classify_ligand`
and re-implemented side by side, so the comparison is exact rather than
inferred:

  INFORMED  solvent/ion if code in _NON_DRUG, cofactor if in _COFACTORS,
            solvent/ion if heavy<=2 or no carbon or _is_aliphatic_additive,
            drug if (_DRUG_DB_REFS & refs) or heavy >= _DRUG_HEAVY_MIN,
            else ligand.
  DEGRADED  solvent/ion if code in _NON_DRUG, cofactor if in _COFACTORS,
            solvent/ion if n_atoms<=2,
            drug if n_atoms >= _DRUG_HEAVY_MIN, else ligand.

Note both paths share the two curated blocklists, which are consulted
BEFORE the record lookup -- so cofactors and known additives cannot
diverge. Divergence is possible in exactly two directions:

  FALSE NEGATIVE  a drug-DB-referenced ligand with heavy < 30. Informed
                  says drug; degraded says ligand.
  FALSE POSITIVE  an aliphatic additive / lipid (or a carbon-free
                  species) with heavy >= 30. Informed says solvent/ion;
                  degraded says drug. THIS is the dangerous direction --
                  it can promote an additive to ground truth.

Every HET code present in every target's holo structure is classified
both ways, not just the committed `drug_ligand`, because the risk is
that a degraded run picked the WRONG ligand from among several.

Run: ../.venv/bin/python3 scripts/task0295_committed_drug_ligand_audit.py
"""
import sys, json, warnings
from pathlib import Path
from collections import defaultdict
warnings.filterwarnings("ignore")
sys.path.insert(0, 'src'); sys.path.insert(0, 'scripts'); sys.path.insert(0, '..')
import prody; prody.confProDy(verbosity="none")
import yaml
from backend import rcsb
from backend.rcsb import (classify_ligand, _chem_comp_record, _NON_DRUG,
                          _COFACTORS, _DRUG_DB_REFS, _DRUG_HEAVY_MIN,
                          _is_aliphatic_additive)
from backend.data_layer import fetch

OUT = Path("results/tasks/0295_drug_ligand_audit")
WATER = {"HOH", "DOD", "WAT"}


def degraded(code, n_atoms):
    """Exactly what classify_ligand returns when _chem_comp_record is None."""
    code = (code or "").strip().upper()
    if code in _NON_DRUG:
        return "solvent/ion", False
    if code in _COFACTORS:
        return "cofactor", False
    if n_atoms is not None and n_atoms <= 2:
        return "solvent/ion", False
    return ("drug", True) if (n_atoms or 0) >= _DRUG_HEAVY_MIN else ("ligand", False)


def het_codes(pdb_id):
    """HET codes in a deposited structure, with their heavy-atom counts."""
    fp = fetch(pdb_id)
    counts = defaultdict(set)
    for line in Path(fp).read_text().splitlines():
        if not line.startswith("HETATM"):
            continue
        resn = line[17:20].strip().upper()
        if resn in WATER:
            continue
        el = line[76:78].strip().upper()
        if el == "H" or (not el and line[12:16].strip().startswith("H")):
            continue
        counts[resn].add((line[21], line[22:27], line[12:16].strip()))
    return {k: len(v) for k, v in counts.items()}


def main():
    cfgs = {}
    for f in ["config/targets.yaml", "config/candidate_targets_task0243.yaml"]:
        try:
            d = yaml.safe_load(open(f)) or {}
        except FileNotFoundError:
            print(f"  [skip] {f} not found"); continue
        cfgs.update(d.get("targets", d) or {})
    print(f"  {len(cfgs)} targets in committed config\n")

    rows, flips, committed_bad = [], [], []
    seen = {}
    for t, cfg in sorted(cfgs.items()):
        holo = cfg.get("holo_pdb"); drug = (cfg.get("drug_ligand") or "").strip().upper()
        if not holo:
            continue
        try:
            hets = het_codes(holo)
        except Exception as ex:
            print(f"  [skip] {t}: {type(ex).__name__}: {ex}"); continue
        for code, n in sorted(hets.items()):
            key = (code, n)
            if key not in seen:
                rec = _chem_comp_record(code)
                inf = classify_ligand(code, n_atoms=n)
                deg = degraded(code, n)
                seen[key] = dict(code=code, n_heavy=n, record_available=rec is not None,
                                 informed=inf[0], informed_is_drug=inf[1],
                                 degraded=deg[0], degraded_is_drug=deg[1],
                                 agree=(inf[1] == deg[1]))
            s = dict(seen[key]); s.update(target=t, holo=holo, is_committed=(code == drug))
            rows.append(s)
            if not s["agree"]:
                flips.append(s)
            if s["is_committed"] and not s["informed_is_drug"]:
                committed_bad.append(s)

    print(f"  {len(rows)} (target, HET) pairs   {len(seen)} distinct ligands\n")
    print("=" * 74)
    print("Q1 -- does every COMMITTED drug_ligand classify as a drug on the")
    print("      fully-informed path?")
    print("=" * 74)
    if committed_bad:
        for s in committed_bad:
            print(f"  *** {s['target']:<22} {s['code']:<5} heavy={s['n_heavy']:<4} "
                  f"informed={s['informed']}  degraded={s['degraded']}")
    else:
        n_comm = sum(1 for r in rows if r['is_committed'])
        print(f"  YES -- all {n_comm} committed drug_ligands classify as 'drug' informed.")

    print("\n" + "=" * 74)
    print("Q2 -- which ligands would a DEGRADED run classify differently?")
    print("=" * 74)
    if not flips:
        print("  NONE. On every ligand present in every target's holo structure,")
        print("  the informed and degraded paths agree on is_drug.")
    else:
        print(f"  {'ligand':<7}{'heavy':>6}  {'informed':<13}{'degraded':<13}"
              f"direction        targets")
        byc = {}
        for s in flips:
            byc.setdefault((s['code'], s['n_heavy']), []).append(s)
        for (code, n), ss in sorted(byc.items()):
            s = ss[0]
            d = ("FALSE POSITIVE" if s['degraded_is_drug'] else "false negative")
            tg = ",".join(sorted({x['target'] for x in ss}))[:34]
            star = " ***" if any(x['is_committed'] for x in ss) else ""
            print(f"  {code:<7}{n:>6}  {s['informed']:<13}{s['degraded']:<13}"
                  f"{d:<17}{tg}{star}")
        print(f"\n  *** = this ligand is a COMMITTED drug_ligand for that target")

    unavail = [c for c, s in seen.items() if not s['record_available']]
    print(f"\n  chem_comp record unavailable right now for {len(unavail)} ligand(s): "
          f"{sorted(set(c for c, _ in unavail)) if unavail else 'none'}")

    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(dict(n_targets=len(cfgs), n_pairs=len(rows), n_distinct=len(seen),
                   committed_not_drug_informed=committed_bad,
                   divergent=flips, rows=rows,
                   drug_heavy_min=_DRUG_HEAVY_MIN),
              open(OUT / "drug_ligand_audit.json", "w"), indent=1)
    print(f"\n  written -> {OUT}/drug_ligand_audit.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
