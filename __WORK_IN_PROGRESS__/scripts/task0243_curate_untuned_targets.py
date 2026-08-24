#!/usr/bin/env python3
"""TASK-0243 -- curate >=12 (target ~19, see below) NEW untuned apo/holo
pairs for the joint two-stage experiment with the collaborating thread.

Reuses [[TASK-0215]]'s own already-validated, live-RCSB, VALID-rule-scored
sourcing pipeline UNCHANGED (`evaluate_candidate`, `_full_text_search`,
`_seed_candidates`'s own logic re-implemented here only to add pagination
and extra query terms -- not to change the verification itself). This
project's own explicit precedent ([[TASK-0169]]'s CARDIAC_MYOSIN_TABLE1
finding: a literature table claimed 6C1H contained mavacamten; it does
not) is exactly why every candidate here is verified live, not proposed
from memory.

Two additions over TASK-0215's own run, both because that run already
exhausted its own stated scope (100 rows/query, 3 query terms, found 6
valid targets / 188 screened =~ 3.2% yield -- getting to ~19 new valid
targets at that yield needs ~600 screened, which is why both levers below
are pulled, not just one):

1. **Deeper pagination** on the SAME 3 original query terms (rows
   100-400, not just 0-100) -- TASK-0215's own cap was a stated scope
   bound, not a signal the pool was exhausted.
2. **More query terms**, targeting protein CLASSES with well-established
   allosteric small-molecule pharmacology (kinases, phosphatases,
   proteases) rather than only the generic "allosteric X" phrasing --
   still a full-text RCSB search over real depositions, not a hand-picked
   PDB ID list from memory.

**Exclusion set expanded** to also cover TASK-0215's own 6 already-found
UniProts (P62593 TEM-1, P14324 FPPS, P19491 GluR2, P22756 GluK1) and
TASK-0238's own HIV1_RT (P03366, verified live via `get_uniprot('1DLO')`
before adding here) -- this task sources NEW proteins beyond every one
already in `targets.yaml` OR `candidate_targets_task0216.yaml`, not a
third pass over either.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _ROOT.parent
_SRC = _ROOT / "src"
_SCRIPTS = _ROOT / "scripts"
_TESTS = _ROOT / "tests"
for _p in (_SRC, _SCRIPTS, _TESTS, _REPO_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import urllib.request  # noqa: E402

from task0215_leg_b_new_proteins import (  # noqa: E402
    EXISTING_TARGET_UNIPROTS as _TASK0215_EXISTING,
    RESOLUTION_MAX,
    evaluate_candidate,
)

OUT_DIR = _ROOT / "results/tasks/0243_curate_untuned_targets"
SEARCH_API = "https://search.rcsb.org/rcsbsearch/v2/query"

# TASK-0215's own 3 original terms (re-paginated deeper) + new, class-
# targeted terms (kinases/phosphatases/proteases are the largest classes
# with well-characterized allosteric small-molecule pharmacology this
# register does not yet cover at all).
QUERY_TERMS = [
    "allosteric inhibitor", "allosteric activator", "allosteric modulator",
    "allosteric kinase inhibitor", "allosteric phosphatase inhibitor",
    "allosteric protease inhibitor", "type III kinase inhibitor",
    "cryptic allosteric pocket",
]
ROWS_PER_QUERY = 400  # vs TASK-0215's own 100 -- explicit, stated widening

# TASK-0215's own 4 already-found UniProts (2 holo entries each for
# TEM-1/GluR2) + HIV1_RT (TASK-0238, verified live via get_uniprot('1DLO')
# before this script was written -- P03366, not assumed from memory).
NEWLY_EXCLUDED_UNIPROTS = {"P62593", "P14324", "P19491", "P22756", "P03366"}
EXISTING_TARGET_UNIPROTS = _TASK0215_EXISTING | NEWLY_EXCLUDED_UNIPROTS


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _full_text_search(term: str, rows: int, start: int) -> list:
    query = {
        "query": {
            "type": "group", "logical_operator": "and",
            "nodes": [
                {"type": "terminal", "service": "full_text", "parameters": {"value": term}},
                {"type": "terminal", "service": "text", "parameters": {
                    "attribute": "rcsb_entry_info.nonpolymer_entity_count",
                    "operator": "greater", "value": 0}},
                {"type": "terminal", "service": "text", "parameters": {
                    "attribute": "rcsb_entry_info.resolution_combined",
                    "operator": "less_or_equal", "value": RESOLUTION_MAX}},
                {"type": "terminal", "service": "text", "parameters": {
                    "attribute": "exptl.method", "operator": "exact_match",
                    "value": "X-RAY DIFFRACTION"}},
            ],
        },
        "return_type": "entry",
        "request_options": {"results_content_type": ["experimental"],
                             "paginate": {"start": start, "rows": rows}},
    }
    try:
        req = urllib.request.Request(
            SEARCH_API, data=json.dumps(query).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        return [hit["identifier"] for hit in data.get("result_set", [])]
    except Exception as exc:  # noqa: BLE001
        _log(f"full-text search failed for {term!r} start={start}: {exc}")
        return []


def _seed_candidates(already_screened: set) -> list:
    """Pooled, deduped candidate PDB IDs -- excludes anything TASK-0215
    already screened (`already_screened`, its own leg_b_results.json keys)
    so this run's own effort goes entirely toward genuinely new territory."""
    seen, pooled = set(already_screened), []
    for term in QUERY_TERMS:
        for start in range(0, ROWS_PER_QUERY, 100):
            ids = _full_text_search(term, 100, start)
            _log(f"query {term!r} start={start}: {len(ids)} hits")
            new_here = 0
            for pid in ids:
                if pid not in seen:
                    seen.add(pid)
                    pooled.append(pid)
                    new_here += 1
            if not ids:
                break  # exhausted this term's own result pages
    return pooled


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    already = json.loads((_ROOT / "results/tasks/0215_leg_b_new_proteins/leg_b_results.json").read_text())
    already_screened = set(already["candidates"].keys())
    prior_run_path = OUT_DIR / "curate_results.json"
    n_prior_valid = 0
    if prior_run_path.exists():
        prior = json.loads(prior_run_path.read_text())
        already_screened |= set(prior["candidates"].keys())
        n_prior_valid = sum(1 for r in prior["candidates"].values() if r.get("verdict") == "VALID_NEW_TARGET")
        _log(f"resuming: {len(prior['candidates'])} already screened this run, {n_prior_valid} already valid")
    _log(f"excluding {len(already_screened)} already-screened entries total")

    _log("=== Seeding: expanded RCSB full-text search ===")
    pooled = _seed_candidates(already_screened)
    _log(f"{len(pooled)} unique NEW entries pooled across {len(QUERY_TERMS)} terms")

    results: dict = {
        "_seed_count": len(pooled), "_query_terms": QUERY_TERMS,
        "_excluded_uniprots": sorted(EXISTING_TARGET_UNIPROTS),
        "_curation_order": [],  # frozen append-only log, per this task's own Scope
        "candidates": {},
    }
    if prior_run_path.exists():
        results["candidates"].update(prior["candidates"])
        results["_curation_order"] = prior.get("_curation_order", [])
    n_valid = n_prior_valid
    seen_uniprots: set = set(r.get("uniprot") for r in results["candidates"].values() if r.get("uniprot"))
    valid_targets: list = [pid for pid, r in results["candidates"].items() if r.get("verdict") == "VALID_NEW_TARGET"]
    for i, pdb_id in enumerate(pooled):
        _log(f"[{i+1}/{len(pooled)}] {pdb_id} ...")
        try:
            r = evaluate_candidate(pdb_id)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            r = {"holo_pdb": pdb_id, "error": f"{type(exc).__name__}: {exc}"}
        # this run's own exclusion set is wider than task0215's own -- an
        # entry whose UniProt matches TASK-0215's/TASK-0238's own finds
        # must be dropped even though evaluate_candidate() only checks
        # ITS OWN (narrower) EXISTING_TARGET_UNIPROTS constant internally.
        if r.get("uniprot") in NEWLY_EXCLUDED_UNIPROTS:
            r["verdict"] = "already_found_by_task0215_or_task0238"
        results["candidates"][pdb_id] = r
        results["_curation_order"].append({"i": i, "pdb_id": pdb_id, "verdict": r.get("verdict", r.get("error"))})
        uni = r.get("uniprot")
        if uni:
            if uni in seen_uniprots:
                r["note"] = "duplicate UniProt within this run"
            seen_uniprots.add(uni)
        if r.get("verdict") == "VALID_NEW_TARGET":
            n_valid += 1
            valid_targets.append(pdb_id)
            _log(f"  -> VALID_NEW_TARGET #{n_valid} ({r['best_recovery']} apo / {pdb_id} holo, "
                 f"UniProt {uni})")
        (OUT_DIR / "curate_results.json").write_text(json.dumps(results, indent=1, default=str))
        if n_valid >= 28:
            _log("reached 28 valid targets -- stopping early (margin above ~19 for expected post-hoc quality exclusions)")
            break

    print("\n=== TASK-0243: curated untuned target sourcing ===")
    print(f"Screened {len(results['candidates'])} of {len(pooled)} pooled entries, "
          f"{len(seen_uniprots)} distinct UniProts touched.")
    print(f"VALID new targets found: {n_valid}")
    for pid in valid_targets:
        r = results["candidates"][pid]
        print(f"  {pid} (UniProt {r.get('uniprot')}): holo={pid} apo={r['best_recovery']} "
              f"window={len(r['window'])} residues, ligand={r.get('drug_ligand')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
