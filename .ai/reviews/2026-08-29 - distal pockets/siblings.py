"""Feasibility scan for handover item 6: how many experimental sibling
conformers exist per target, via search.rcsb.org sequence identity?

Cheap de-risking: if a target has only its own entry at high identity, the
persistence-across-conformers idea cannot be tested for it. Counts only; no
downloads.
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

SM = json.loads(Path("/home/claude/struct_map.json").read_text())
EXPA = json.loads((Path("/mnt/user-data/uploads") / "expA_fpocket.json").read_text())
URL = "https://search.rcsb.org/rcsbsearch/v2/query?json="


def search(seq, ident):
    q = {
        "query": {"type": "terminal", "service": "sequence",
                  "parameters": {"evalue_cutoff": 1, "identity_cutoff": ident,
                                 "sequence_type": "protein", "value": seq}},
        "return_type": "polymer_entity",
        "request_options": {"paginate": {"start": 0, "rows": 500},
                            "results_content_type": ["experimental"]},
    }
    url = URL + urllib.parse.quote(json.dumps(q))
    for i in range(4):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                if r.status == 204:
                    return []
                d = json.loads(r.read())
            return [x["identifier"] for x in d.get("result_set", [])]
        except Exception:  # noqa: BLE001
            if i == 3:
                return None
            time.sleep(2 * (i + 1))
    return None


def main():
    print(f"  {'pdb':<6}{'chain':<6}{'len':>5}{'>=95%':>8}{'>=70%':>8}"
          f"{'distinct entries (95%)':>24}")
    out = {}
    for pdb in sorted(SM):
        for ch, cd in sorted(SM[pdb]["chains"].items()):
            seq = cd["seq"]
            if len(seq) < 30:
                continue
            hi = search(seq, 0.95)
            lo = search(seq, 0.70)
            if hi is None:
                print(f"  {pdb:<6}{ch:<6}{len(seq):>5}   search failed")
                continue
            ents = sorted({x.split("_")[0] for x in hi})
            out[f"{pdb}_{ch}"] = {"n95": len(hi), "n70": len(lo or []),
                                  "entries95": ents}
            print(f"  {pdb:<6}{ch:<6}{len(seq):>5}{len(hi):>8}"
                  f"{len(lo or []):>8}{len(ents):>24}")
    Path("/home/claude/siblings.json").write_text(json.dumps(out, indent=1))

    print("\n  Per target, sibling entries available at >=95% identity "
          "(excluding the apo entry itself):")
    print(f"  {'target':<20}{'apo':<6}{'siblings':>10}")
    counts = []
    for t, v in EXPA.items():
        pdb = v["apo_pdb"].upper()
        ents = set()
        for ch in v["chains"]:
            k = f"{pdb}_{ch}"
            if k in out:
                ents |= set(out[k]["entries95"])
        ents.discard(pdb)
        counts.append(len(ents))
        print(f"  {t:<20}{pdb:<6}{len(ents):>10}")
    print(f"\n  median siblings per target: {np.median(counts):.0f}; "
          f"min {min(counts)}; targets with <5: "
          f"{sum(1 for c in counts if c < 5)}/{len(counts)}")


if __name__ == "__main__":
    main()
