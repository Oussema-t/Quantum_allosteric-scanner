"""TASK-0304 -- CASBench's own site definitions, live from the source.

[[TASK-0304]]'s own "Still to do": CASBench's site residue annotations are
NOT in the ASBench paper's own supplementary Tables S5/S6 (those are
per-structure statistical-measure RESULTS -- ●/○ per test -- not residue
lists; confirmed directly by opening mmc5.xlsx/mmc6.xlsx and reading their
columns before writing this script). CASBench is a separate benchmark,
its own citation: Zlobin, Suplatov, Kopylov & Svedas (2019), "CASBench: a
benchmarking set of proteins with annotated catalytic and allosteric
sites in their structures", Acta Naturae 11, 74-80 (PMCID PMC6475866,
verified live via Europe PMC before citing). That paper's own full text
names its live web database: https://biokinet.belozersky.msu.ru/casbench
-- confirmed live (HTTP 200), Drupal-hosted, with a PHP browse/search
sub-app at /casbenchbrowse serving plain server-rendered HTML (no JS
proof-of-work, unlike PMC's own supplementary-file gate that blocked the
ASBench route earlier in this task).

STRUCTURE, verified by reading `view.php?id=cas0001` directly before
scaling to all 91 entries: `all.php` lists every CAS ID (CAS0001..) with
its protein name and one representative PDB; `view.php?id=casXXXX` embeds
EVERY PDB structure deposited for that protein family as its own
`<div id="div{pdbid}">` block (shown/hidden by the page's own dropdown
JS -- the data for every structure is already server-rendered into the
page, not fetched separately per structure), each containing an
"Allosteric Site:" table and a "Catalytic Site:" table (chain / resnum /
resname rows), aggregated here across every SITE_<N> sub-index CASBench
itself distinguishes -- this script does not need that sub-site
distinction, only the union of residues per category, matching how
[[TASK-0304]]'s own ASBench parsing already treats "Allosteric Site
Residues" as one set.

Fetches all 91 CASBench proteins (not just the 33/314 the Wu et al. 2022
paper's own subset used) -- more of "their" annotation, same source,
costs nothing extra. Cross-referenced against `cohort_pdb_ids.json`'s
own `casbench` (314 PDB ID) list at the end, not assumed to match 1:1.

Run: ../.venv/bin/python3 scripts/task0304_casbench_annotations.py
"""
import json, re, time, warnings
from pathlib import Path
import requests
warnings.filterwarnings("ignore")

BASE = "https://biokinet.belozersky.msu.ru/casbenchbrowse"
OUT = Path("results/tasks/0304_asbench_casbench")

_DIV_RE = re.compile(r'<div id="div([0-9a-zA-Z]{4})"')
_SITE_HDR_RE = re.compile(r'<h5[^>]*><strong>(Allosteric Site|Catalytic Site):</strong></h5>')
_ROW_RE = re.compile(
    r'<td>(ALLOSTERIC|CATALYTIC)_SITE_<B>\d+</B></td>\s*'
    r'<td>(\w)</td>\s*<td>(-?\d+)</td>\s*<td>(\w+)</td>',
)


def fetch(url, **kw):
    r = requests.get(url, timeout=30, **kw)
    r.raise_for_status()
    return r.text


def list_all_entries():
    html = fetch(f"{BASE}/all.php")
    rows = re.findall(
        r'<td>(CAS\d+)</td><td>([^<]*)</td><td>([0-9A-Za-z]{4})</td>', html,
    )
    return [{"cas_id": c, "protein": p.strip(), "repr_pdb": pdb.upper()} for c, p, pdb in rows]


def parse_entry_page(html):
    """Split into per-PDB blocks by div boundary, then pull every
    ALLOSTERIC_SITE_*/CATALYTIC_SITE_* row inside each block."""
    starts = [(m.start(), m.group(1).upper()) for m in _DIV_RE.finditer(html)]
    out = {}
    for i, (pos, pdb) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(html)
        block = html[pos:end]
        allo, cat = set(), set()
        for kind, chain, resnum, resname in _ROW_RE.findall(block):
            key = f"{resname[:3].upper()}{resnum} {chain}"
            (allo if kind == "ALLOSTERIC" else cat).add(key)
        if allo or cat:
            out[pdb] = {"allosteric_residues": sorted(allo), "catalytic_residues": sorted(cat)}
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    entries = list_all_entries()
    print(f"CASBench: {len(entries)} protein entries listed in all.php")

    records = []
    errors = []
    for i, e in enumerate(entries):
        try:
            html = fetch(f"{BASE}/view.php", params={"id": e["cas_id"].lower()})
        except Exception as ex:
            errors.append((e["cas_id"], f"fetch: {type(ex).__name__}: {ex}"))
            continue
        per_pdb = parse_entry_page(html)
        if not per_pdb:
            errors.append((e["cas_id"], "no structure blocks parsed"))
            continue
        for pdb, sites in per_pdb.items():
            records.append(dict(cas_id=e["cas_id"], protein=e["protein"], pdb=pdb,
                                n_allo=len(sites["allosteric_residues"]),
                                n_cat=len(sites["catalytic_residues"]),
                                allosteric_residues=sites["allosteric_residues"],
                                catalytic_residues=sites["catalytic_residues"]))
        if (i + 1) % 15 == 0:
            print(f"  ... {i+1}/{len(entries)} proteins  ({len(records)} structures so far)")
        time.sleep(0.15)

    print(f"\nparsed {len(records)} (cas_id, pdb) structures across "
          f"{len(entries) - len(errors)}/{len(entries)} proteins ({len(errors)} errors)")
    both = sum(1 for r in records if r["n_allo"] > 0 and r["n_cat"] > 0)
    print(f"  structures with BOTH allosteric and catalytic residues: {both}/{len(records)}")

    # cross-check against the already-known 314-PDB CASBench subset
    cohort = json.loads((OUT / "cohort_pdb_ids.json").read_text())
    known = set(p.upper() for p in cohort.get("casbench", []))
    have = set(r["pdb"] for r in records if r["n_allo"] > 0 and r["n_cat"] > 0)
    overlap = known & have
    print(f"\n  cohort_pdb_ids.json's own 314-PDB CASBench subset: {len(known)}")
    print(f"  of those, resolvable here with BOTH site types annotated: {len(overlap)}/{len(known)}")

    if errors:
        print(f"\n  errors ({len(errors)}):")
        for cid, why in errors[:20]:
            print(f"    {cid}: {why}")

    (OUT / "casbench_annotations.json").write_text(json.dumps(dict(
        n_proteins_listed=len(entries), n_structures=len(records),
        n_structures_both_sites=both, records=records, errors=errors,
        cohort_314_overlap=sorted(overlap), cohort_314_missing=sorted(known - have),
    ), indent=1))
    print(f"\n  written -> {OUT}/casbench_annotations.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
