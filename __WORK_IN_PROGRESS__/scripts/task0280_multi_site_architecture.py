#!/usr/bin/env python3
"""TASK-0280 -- verification, not a new run: the Reviewer's own observation
(KRAS is a 9:1 two-site protein, from [[TASK-0276]]'s stored footprints)
needs (a) live confirmation that the outlier (`7A1X`/QWB) is a real,
published druggable site rather than a fragment-screening curiosity or a
numbering artefact, and (b) the same clustering repeated across every
frozen-set protein with >=2 holo structures, reusing already-computed data
rather than re-deriving it.

Reuses, does not re-derive:
  - `results/tasks/0276_holo_only_structural_signature/holo_only_structural_signature.json`
    (`allosteric_keys`) -- [[TASK-0276]]'s own per-structure KRAS/HCV_NS5B
    footprints, live-verified there.
  - `results/tasks/0265_pocket_label_overlap/pocket_label_overlap.json`
    (`frozen_set`) -- [[TASK-0265]]'s own same-apo pairwise Jaccard for
    every 2-ligand pair in [[TASK-0243]]'s frozen config.
  - `results/tasks/0273_holo_ensemble_label_noise/holo_ensemble_label_noise.json`
    (`GAC`, `TRP_SYNTHASE`) -- [[TASK-0273]]'s own richer same-drug-replicate
    ensembles for the two families with real replicate coverage, including
    the resnum-only Jaccard fix for homo-oligomer chain-letter ambiguity.

Live checks run here, not reused from anywhere (this task's own Scope):
  - RCSB primary-citation lookup for `7A1X` (its own deposited reference).
  - RCSB assembly oligomeric-state lookup for `8AZX` (representative of the
    single-chain-A KRAS G12C construct shared by all 10 ensemble members)
    -- rules out the chain-letter-ambiguity trap [[TASK-0273]] found in GAC
    for KRAS specifically: a monomeric construct has no symmetric copy to
    be mislabeled onto, so chain-exact and resnum-only Jaccard cannot
    diverge for it, unlike GAC/FBPASE.
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
OUT = _ROOT / "results/tasks/0280_multi_site_architecture"


def _rcsb_get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "qas-task0280/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def verify_7a1x_citation() -> dict:
    d = _rcsb_get("https://data.rcsb.org/rest/v1/core/entry/7A1X")
    c = d.get("rcsb_primary_citation", {})
    return dict(
        title=c.get("title"), journal=c.get("rcsb_journal_abbrev"), year=c.get("year"),
        volume=c.get("journal_volume"), pages=f"{c.get('page_first')}-{c.get('page_last')}",
        doi=c.get("pdbx_database_id_DOI"), pmid=c.get("pdbx_database_id_PubMed"),
        authors=c.get("rcsb_authors"),
    )


def verify_kras_monomeric() -> dict:
    d = _rcsb_get("https://data.rcsb.org/rest/v1/core/assembly/8AZX/1")
    return dict(
        pdb_id="8AZX", oligomeric_state=d.get("pdbx_struct_assembly", {}).get("oligomeric_details"),
    )


def kras_architecture() -> dict:
    d = json.loads((_ROOT / "results/tasks/0276_holo_only_structural_signature"
                     / "holo_only_structural_signature.json").read_text())
    keys = d["KRAS"]["allosteric_keys"]
    footprints = {pid: sorted(set(r for _c, r in ks)) for pid, ks in keys.items()}

    def jac(a, b):
        sa, sb = set(a), set(b)
        return len(sa & sb) / len(sa | sb) if (sa or sb) else float("nan")

    pids = sorted(footprints)
    outlier_vs_rest = {p: jac(footprints["7A1X"], footprints[p]) for p in pids if p != "7A1X"}
    rest_pairwise = []
    for i, a in enumerate(pids):
        for b in pids[i + 1:]:
            if "7A1X" in (a, b):
                continue
            rest_pairwise.append(jac(footprints[a], footprints[b]))
    return dict(footprints=footprints, outlier_vs_rest=outlier_vs_rest,
                rest_pairwise_range=(min(rest_pairwise), max(rest_pairwise)))


def hcv_architecture() -> dict:
    d = json.loads((_ROOT / "results/tasks/0276_holo_only_structural_signature"
                     / "holo_only_structural_signature.json").read_text())
    return dict(within_cluster=d["HCV_NS5B"]["jaccard_within_cluster"],
                across_cluster=d["HCV_NS5B"]["jaccard_across_cluster"])


def frozen_set_pairs() -> dict:
    d = json.loads((_ROOT / "results/tasks/0265_pocket_label_overlap"
                     / "pocket_label_overlap.json").read_text())
    return {r["apo"]: r for r in d["frozen_set"]}


def gac_trp_ensembles() -> dict:
    d = json.loads((_ROOT / "results/tasks/0273_holo_ensemble_label_noise"
                     / "holo_ensemble_label_noise.json").read_text())
    return dict(GAC=dict(same=d["GAC"]["same_drug_summary"], diff=d["GAC"]["diff_drug_summary"]),
                TRP_SYNTHASE=dict(same=d["TRP_SYNTHASE"]["same_drug_summary"],
                                   diff=d["TRP_SYNTHASE"]["diff_drug_summary"]))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    out = {}

    print("### 7A1X primary citation (live RCSB lookup) ###")
    cite = verify_7a1x_citation()
    for k, v in cite.items():
        print(f"  {k}: {v}")
    out["7a1x_citation"] = cite

    print("\n### KRAS G12C construct oligomeric state (live RCSB lookup) ###")
    mono = verify_kras_monomeric()
    print(f"  {mono}")
    out["kras_monomeric"] = mono

    print("\n### KRAS architecture (from TASK-0276's stored footprints) ###")
    kras = kras_architecture()
    print(f"  7A1X vs each of the other 9: {kras['outlier_vs_rest']}")
    print(f"  pairwise range among the other 9: {kras['rest_pairwise_range']}")
    out["kras_architecture"] = kras

    print("\n### HCV_NS5B architecture (from TASK-0276) ###")
    hcv = hcv_architecture()
    print(f"  {hcv}")
    out["hcv_architecture"] = hcv

    print("\n### Frozen-set same-apo pairs (from TASK-0265) ###")
    pairs = frozen_set_pairs()
    for apo, r in pairs.items():
        print(f"  {apo}: {r['a']} vs {r['b']}  jac={r['jaccard']:.3f}  "
              f"jac_resnum={r['jaccard_resnum_only']:.3f}  same_chain_sel={r['same_chain_selection']}")
    out["frozen_set_pairs"] = pairs

    print("\n### GAC / TRP_SYNTHASE richer ensembles (from TASK-0273) ###")
    ens = gac_trp_ensembles()
    print(f"  {ens}")
    out["gac_trp_ensembles"] = ens

    (OUT / "architecture_verification.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwritten: {OUT / 'architecture_verification.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
