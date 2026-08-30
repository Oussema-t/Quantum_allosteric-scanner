"""Regenerate the apo input PDBs and prove they are the same inputs the cached
fpocket runs used, by matching expA_fpocket.json's n_residues / n_atoms and then
hyd_cache.json's candidate counts.

The repo is not in this container, so expC_prep.py's exact prep is reconstructed
from matched.py's documented recipe: parse with altloc='all', select configured
chains, keep altloc '_ A', select protein.
"""
import json
import sys
from pathlib import Path

import prody

_o = prody.parsePDB


def _p(*a, **k):
    k.setdefault("altloc", "all")
    return _o(*a, **k)


prody.parsePDB = _p

UP = Path("/mnt/user-data/uploads")
EXPA = json.loads((UP / "expA_fpocket.json").read_text())
OUT = Path("/home/claude/apo")
OUT.mkdir(exist_ok=True)
CACHE = Path("/home/claude/pdb_cache")
CACHE.mkdir(exist_ok=True)


def main():
    prody.pathPDBFolder(str(CACHE))
    prody.confProDy(verbosity="none")
    ok = 0
    print(f"  {'target':<20}{'pdb':<6}{'nres':>6}{'want':>6}{'natom':>7}"
          f"{'want':>7}  match")
    for t, v in EXPA.items():
        st = prody.parsePDB(v["apo_pdb"], compressed=False)
        sel = st.select(" or ".join(f"chain {c}" for c in v["chains"]))
        al = sel.getAltlocs()
        if al is not None and any(x not in ("", " ", "\x00") for x in al):
            sel = sel.select("altloc _ A") or sel
        pro = sel.select("protein")
        nres = pro.numResidues()
        natom = pro.numAtoms()
        good = (nres == v["n_residues"] and natom == v["n_atoms"])
        ok += good
        prody.writePDB(str(OUT / f"{t}_apo.pdb"), pro)
        print(f"  {t:<20}{v['apo_pdb']:<6}{nres:>6}{v['n_residues']:>6}"
              f"{natom:>7}{v['n_atoms']:>7}  {'OK' if good else 'MISMATCH'}")
    print(f"\n  {ok}/{len(EXPA)} inputs reproduce recorded residue and atom counts")
    return 0 if ok == len(EXPA) else 1


if __name__ == "__main__":
    sys.exit(main())
