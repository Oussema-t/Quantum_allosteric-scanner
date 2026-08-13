"""TASK-0215 -- [[TASK-0214]]'s own Leg B: source NEW cryptic-pocket
candidates from RCSB (not just re-selected depositions of this register's
existing 14 targets), derive the pocket window from the holo structure's
own drug-ligand binding site (`rcsb.ligands_and_sites`), and score
apo/holo through [[TASK-0209]]'s VALID rule, unchanged.

Pipeline, per the task's own pre-registered protocol:

  1. RCSB full-text search, 3 query terms ("allosteric inhibitor" /
     "activator" / "modulator"), X-ray, resolution <=2.5, has a bound
     nonpolymer, capped at 100 hits/query, pooled + deduped.
  2. Exclude entries whose UniProt matches one of the 14 existing
     targets.yaml targets.
  3. Per surviving holo candidate: pick its highest-`n_atoms` `drug`-
     classified ligand (`classify_ligand`), take its `binding_site_full`
     as the window.
  4. Find apo candidates for the same UniProt; apply TASK-0214's own
     exclusion filter (chem_comp-driven, not `classify_ligand`'s
     top-level bucket alone -- see that filter's own docstring for why).
  5. Score holo_native (sanity: should hit, since the window is derived
     from its own ligand) and up to 3 apo candidates' native structure.
  6. VALID iff apo misses and holo hits -- verbatim from TASK-0209.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _ROOT.parent
_SRC = _ROOT / "src"
_SCRIPTS = _ROOT / "scripts"
_TESTS = _ROOT / "tests"
for _p in (_SRC, _SCRIPTS, _TESTS, _REPO_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from allostery.clean import load_target_config  # noqa: E402
from backend.discovery import (  # noqa: E402
    SEARCH_API, get_uniprot, same_protein_entries, _search_entries_by_uniprot,
)
from backend.rcsb import (  # noqa: E402
    _chem_comp_record, _is_aliphatic_additive, classify_ligand, entry_summary,
    ligands_and_sites,
)
from task0204_positive_control import score_structure  # noqa: E402
from task0214_apo_reselection import (  # noqa: E402
    _is_buffer_or_water, _write_native_protein_pdb,
)

import urllib.request  # noqa: E402

OUT_DIR = _ROOT / "results_task0215_leg_b_new_proteins"

QUERY_TERMS = ["allosteric inhibitor", "allosteric activator", "allosteric modulator"]
ROWS_PER_QUERY = 100
RESOLUTION_MAX = 2.5
MAX_APO_CANDIDATES_PER_HOLO = 3
WINDOW_MIN_RESIDUES = 6
WINDOW_MAX_RESIDUES = 20

EXISTING_TARGET_UNIPROTS = {
    "P01116", "P00519", "Q9BE39", "P01106", "P61244", "P18031", "P35557",
    "P0A786", "P0A7F3", "P29466", "P55210", "P69905", "P68871", "P02941",
    "P00489", "P0A796", "P0A6F5",
}


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _full_text_search(term: str, rows: int) -> list:
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
                             "paginate": {"start": 0, "rows": rows}},
    }
    try:
        req = urllib.request.Request(
            SEARCH_API, data=json.dumps(query).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        return [hit["identifier"] for hit in data.get("result_set", [])]
    except Exception as exc:  # noqa: BLE001
        _log(f"full-text search failed for {term!r}: {exc}")
        return []


def _seed_candidates() -> list:
    seen, pooled = set(), []
    for term in QUERY_TERMS:
        ids = _full_text_search(term, ROWS_PER_QUERY)
        _log(f"query {term!r}: {len(ids)} hits")
        for pid in ids:
            if pid not in seen:
                seen.add(pid)
                pooled.append(pid)
    return pooled


def _holo_window_from_ligands(pdb_id: str):
    """Best drug-classified ligand's own binding site as the window.
    Returns (window, chains, ligand_code) or (None, None, None)."""
    ligs = ligands_and_sites(pdb_id, contact_cutoff=4.5)
    drugs = [l for l in ligs if l["category"] == "drug"]
    if not drugs:
        return None, None, None
    best = max(drugs, key=lambda l: l["n_atoms"])
    site = best["binding_site_full"]
    if not site:
        return None, None, None
    window = [(d["chain"], d["resnum"]) for d in site]
    chains = sorted(set(c for c, _ in window))
    return window, chains, best["code"]


def _candidate_survives_filter(pdb_id: str, window: list, pocket_cutoff: float = 4.5) -> dict:
    """Same exclusion filter as [[TASK-0214]], reused for the apo side of
    a new-protein candidate."""
    import prody

    prody.confProDy(verbosity="none")
    raw = prody.parsePDB(pdb_id, compressed=False)
    if raw is None:
        return {"survives": False, "reason": "fetch_failed"}
    window_sel = " or ".join(f"(chain {c} and resnum {r})" for c, r in window)
    window_atoms = raw.select(f"protein and not hetero and ({window_sel})")
    if window_atoms is None:
        return {"survives": False, "reason": "window_not_found"}
    window_xyz = window_atoms.getCoords()

    from allostery.labels import ligand_groups_from_atomgroup
    groups = ligand_groups_from_atomgroup(raw)
    findings = []
    for g in groups:
        code = g.resname.strip().upper()
        if code in ("HOH", "DOD", "WAT"):
            continue
        d = np.linalg.norm(window_xyz[:, None, :] - g.coords[None, :, :], axis=-1)
        min_dist = float(d.min())
        if min_dist > pocket_cutoff:
            continue
        rec = _chem_comp_record(code)
        heavy = rec["heavy"] if rec else None
        elements = rec["elements"] if rec else None
        safe = _is_buffer_or_water(code, heavy, elements)
        findings.append({"resname": code, "min_dist_to_window": round(min_dist, 2),
                          "treated_as_buffer": safe})
    unsafe = [f for f in findings if not f["treated_as_buffer"]]
    return {"survives": not unsafe, "reason": None if not unsafe else "unsafe_hetatm_near_window",
            "near_pocket_hetatm": findings}


def evaluate_candidate(holo_pdb: str) -> dict:
    t0 = time.monotonic()
    result: dict = {"holo_pdb": holo_pdb}

    window, holo_chains, drug_code = _holo_window_from_ligands(holo_pdb)
    if window is None:
        return {**result, "error": "no drug-classified ligand with a resolvable binding site"}
    if not (WINDOW_MIN_RESIDUES <= len(window) <= WINDOW_MAX_RESIDUES):
        return {**result, "error": f"window size {len(window)} outside "
                f"[{WINDOW_MIN_RESIDUES},{WINDOW_MAX_RESIDUES}] sanity range",
                "window": window, "drug_ligand": drug_code}
    result["window"] = window
    result["drug_ligand"] = drug_code
    result["holo_chains"] = holo_chains

    unis = get_uniprot(holo_pdb)
    if not unis:
        return {**result, "error": "no UniProt resolved"}
    if unis[0] in EXISTING_TARGET_UNIPROTS:
        return {**result, "error": f"UniProt {unis[0]} already in targets.yaml"}
    result["uniprot"] = unis[0]

    target_set = set(window)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        try:
            holo_local = tmp / f"{holo_pdb.lower()}_native.pdb"
            _write_native_protein_pdb(holo_pdb, holo_chains, holo_local)
            result["holo_native"] = score_structure(holo_local, target_set, tmp)
        except Exception as exc:  # noqa: BLE001
            return {**result, "error": f"holo scoring {type(exc).__name__}: {exc}"}

        if result["holo_native"].get("hit") is not True:
            result["verdict"] = "holo_does_not_hit_own_window"
            result["elapsed_s"] = round(time.monotonic() - t0, 1)
            return result

        apo_ids = same_protein_entries(holo_pdb, max_n=40, with_ligand=False)
        apo_candidates = []
        for pid in apo_ids:
            summary = entry_summary(pid)
            method = (summary.get("method") or "").lower()
            res = summary.get("resolution")
            if "x-ray" not in method or res is None or res > RESOLUTION_MAX:
                continue
            apo_candidates.append({"pdb_id": pid, **summary})
        apo_candidates.sort(key=lambda c: c.get("resolution") or 99)
        result["n_apo_candidates"] = len(apo_candidates)

        scored, apo_results = 0, []
        for cand in apo_candidates:
            if scored >= MAX_APO_CANDIDATES_PER_HOLO:
                break
            pid = cand["pdb_id"]
            entry = {"pdb_id": pid, "resolution": cand.get("resolution")}
            try:
                audit = _candidate_survives_filter(pid, window)
            except Exception as exc:  # noqa: BLE001
                entry["error"] = f"audit {type(exc).__name__}: {exc}"
                apo_results.append(entry)
                continue
            entry["audit"] = audit
            if not audit["survives"]:
                apo_results.append(entry)
                continue
            try:
                apo_local = tmp / f"{pid.lower()}_native.pdb"
                _write_native_protein_pdb(pid, holo_chains, apo_local)
                entry["score"] = score_structure(apo_local, target_set, tmp)
            except Exception as exc:  # noqa: BLE001
                entry["error"] = f"score {type(exc).__name__}: {exc}"
                apo_results.append(entry)
                continue
            scored += 1
            entry["verdict"] = "apo_closed" if entry["score"].get("hit") is False else "apo_still_open"
            apo_results.append(entry)
        result["apo_candidates"] = apo_results

    valid_recoveries = [c["pdb_id"] for c in apo_results if c.get("verdict") == "apo_closed"]
    result["recovered"] = bool(valid_recoveries)
    result["best_recovery"] = valid_recoveries[0] if valid_recoveries else None
    result["verdict"] = "VALID_NEW_TARGET" if result["recovered"] else "holo_ok_no_closed_apo"
    result["elapsed_s"] = round(time.monotonic() - t0, 1)
    return result


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)

    _log("=== Seeding: RCSB full-text search ===")
    pooled = _seed_candidates()
    _log(f"{len(pooled)} unique entries pooled across {len(QUERY_TERMS)} queries")

    results: dict = {"_seed_count": len(pooled), "_query_terms": QUERY_TERMS, "candidates": {}}
    n_valid = 0
    seen_uniprots: set = set()
    for i, pdb_id in enumerate(pooled):
        _log(f"[{i+1}/{len(pooled)}] {pdb_id} ...")
        try:
            r = evaluate_candidate(pdb_id)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            r = {"holo_pdb": pdb_id, "error": f"{type(exc).__name__}: {exc}"}
        results["candidates"][pdb_id] = r
        uni = r.get("uniprot")
        if uni:
            if uni in seen_uniprots:
                r["note"] = "duplicate UniProt within this run, scored anyway for completeness"
            seen_uniprots.add(uni)
        if r.get("verdict") == "VALID_NEW_TARGET":
            n_valid += 1
            _log(f"  -> VALID_NEW_TARGET ({r['best_recovery']} apo / {pdb_id} holo, "
                 f"UniProt {uni})")
        (OUT_DIR / "leg_b_results.json").write_text(json.dumps(results, indent=1, default=str))

    print("\n=== TASK-0215 Leg B: new-protein sourcing ===")
    print(f"Seeded {len(pooled)} entries, {len(seen_uniprots)} distinct UniProts touched.")
    print(f"VALID new targets found: {n_valid}")
    for pid, r in results["candidates"].items():
        if r.get("verdict") == "VALID_NEW_TARGET":
            print(f"  {pid} (UniProt {r.get('uniprot')}): holo={pid} apo={r['best_recovery']} "
                  f"window={len(r['window'])} residues, ligand={r.get('drug_ligand')}")
    print(f"\nRevised total usable-instance count: {2 + n_valid}/{7 + n_valid} "
          f"(TASK-0209's 2/7 + {n_valid} new).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
