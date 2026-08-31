"""TASK-0304 -- does [[TASK-0288]] Finding F generalise beyond our 13 clusters?

Finding F: ~29% of the Cleveland Clinic benchmark's annotated "allosteric"
pockets sit at the **peptide-bond distance** from the active site -- i.e.
they are covalently adjacent, not distal at all. Measured on 28 structures
/ 13 independent apo clusters. The obvious objection is that 13 clusters
is too few to know whether that is a property of allosteric annotation in
general or a quirk of this particular target list.

ASBench answers it. Wu, Strömich & Yaliraki (2022) supply, in their own
Supplementary Table S2, **118 structures with BOTH the allosteric site
residues AND the active site residues explicitly annotated** -- the exact
two sets Finding F measures the distance between. 113 distinct PDB codes,
and only 4 overlap with our register.

This script recomputes Finding F's statistic on their cohort, using their
annotations rather than ours, so the comparison tests the finding and not
our own labelling pipeline.

METHOD, deliberately minimal: for each structure, fetch the deposited
coordinates, resolve the two annotated residue sets, and compute the
**minimum heavy-atom distance** between them -- the same quantity
`min_heavy_atom_dist_to_seed` computes in our own pipeline. No fpocket, no
active-site detection, no CTQW. Nothing from our pipeline is involved
except the distance definition itself, which is what is under test.

NOTE ON THE TWO ANNOTATION FORMATS (they differ, and silently mixing them
would corrupt everything):
  Allosteric Site Residues : "ASP14 A"  -> resname + resnum, space, chain
  Active Site Residues     : "A41"      -> chain, resnum

Run: ../.venv/bin/python3 scripts/task0304_asbench_finding_f.py
"""
import sys, json, re, warnings
from pathlib import Path
from collections import defaultdict
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, 'src'); sys.path.insert(0, '..')
from backend.data_layer import fetch

OUT = Path("results/tasks/0304_asbench_casbench")
ANN = json.load(open(OUT / "asbench_annotations.json"))

_ALLO = re.compile(r'^([A-Z]{2,3})\s*(-?\d+)([A-Za-z]?)\s+(\w)$')
_ACT = re.compile(r'^(\w)(-?\d+)$')


def parse_allo(tok):
    m = _ALLO.match(tok.strip())
    if m:
        return (m.group(4), int(m.group(2)))
    m = re.match(r'^([A-Z]{2,3})(-?\d+)\s+(\w)$', tok.strip())
    return (m.group(3), int(m.group(2))) if m else None


def parse_act(tok):
    m = _ACT.match(tok.strip())
    return (m.group(1), int(m.group(2))) if m else None


def heavy_atoms(pdb_id):
    """(chain, resnum) -> Nx3 heavy-atom coords, from the deposited model."""
    out = defaultdict(list)
    for line in Path(fetch(pdb_id)).read_text().splitlines():
        if not line.startswith(("ATOM", "HETATM")):
            continue
        el = line[76:78].strip().upper()
        name = line[12:16].strip()
        if el == "H" or (not el and name.startswith("H")):
            continue
        try:
            key = (line[21], int(line[22:26]))
            out[key].append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
        except ValueError:
            continue
    return {k: np.asarray(v, float) for k, v in out.items()}


def main():
    rows, skipped = [], []
    for i, rec in enumerate(ANN):
        pdb = rec["pdb"].split("_")[0]
        try:
            ha = heavy_atoms(pdb)
        except Exception as ex:
            skipped.append((rec["pdb"], f"fetch: {type(ex).__name__}")); continue
        allo = [parse_allo(t) for t in rec["allosteric_residues"]]
        act = [parse_act(t) for t in rec["active_residues"]]
        allo = [k for k in allo if k and k in ha]
        act = [k for k in act if k and k in ha]
        if not allo or not act:
            skipped.append((rec["pdb"],
                            f"unresolved allo={len(allo)}/{rec['n_allo']} "
                            f"act={len(act)}/{rec['n_act']}")); continue
        A = np.vstack([ha[k] for k in allo]); B = np.vstack([ha[k] for k in act])
        dmin = float(np.min(np.linalg.norm(A[:, None, :] - B[None, :, :], axis=-1)))
        rows.append(dict(pdb=rec["pdb"], protein=rec["protein"],
                         n_allo_resolved=len(allo), n_act_resolved=len(act),
                         min_heavy_A=dmin))
        if (i + 1) % 20 == 0:
            print(f"  ... {i+1}/{len(ANN)}")

    d = np.array([r["min_heavy_A"] for r in rows])
    print("\n" + "=" * 70)
    print(f"ASBench: min heavy-atom distance, annotated allosteric site -> active site")
    print("=" * 70)
    print(f"  resolved {len(rows)} of {len(ANN)} structures   ({len(skipped)} skipped)")
    print(f"  median {np.median(d):.2f} A   min {d.min():.2f}   max {d.max():.2f}")
    for lo, hi, lab in [(0, 1.5, "< 1.5 A  (COVALENT / peptide bond)"),
                        (1.5, 4.0, "1.5-4.0 A (van der Waals contact)"),
                        (4.0, 8.0, "4.0-8.0 A"),
                        (8.0, 1e9, "> 8.0 A  (genuinely distal)")]:
        c = int(((d >= lo) & (d < hi)).sum())
        print(f"    {lab:<38} {c:>4}/{len(d)} = {c/len(d):>6.1%}")
    print(f"\n  OUR register (TASK-0288/0297, 28 structures): 8/28 = 28.6% below 1.5 A")
    if skipped:
        print(f"\n  skipped ({len(skipped)}):")
        for p, why in skipped[:15]:
            print(f"    {p:<10} {why}")
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(dict(rows=rows, skipped=skipped, n_annotated=len(ANN),
                   median=float(np.median(d)),
                   frac_below_1p5=float((d < 1.5).mean()),
                   frac_below_4=float((d < 4.0).mean()),
                   frac_above_8=float((d >= 8.0).mean())),
              open(OUT / "asbench_finding_f.json", "w"), indent=1)
    print(f"\n  written -> {OUT}/asbench_finding_f.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
