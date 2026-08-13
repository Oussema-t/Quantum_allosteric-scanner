"""TASK-0214 -- widen [[TASK-0209]]'s 2/7 valid-instance count by
re-selecting the *apo structure* for the 5 INVALID targets (Leg A only;
Leg B -- new proteins -- is out of scope here per the task's own
pre-registered protocol, only attempted if Leg A leaves the VALID count
below 5).

Per target's own existing curated pocket window (unchanged from
[[TASK-0209]]), search RCSB (via UniProt, `backend.discovery`) for
alternative apo depositions of the same protein, apply an exclusion
filter driven by chem_comp data (not a hand-written blocklist) to reject
any candidate with a substantive HETATM near the pocket window, score up
to 5 surviving candidates' *native* structure (no repacking -- this leg
asks only whether a different deposition is naturally closed) against
the target's own hit criterion, verbatim from TASK-0209
(`overlap_frac >= 0.5 AND druggability_score >= 0.5`).

KRAS_G12C is re-scored first as a known-answer check (harness integrity),
per the task's own Planned Validation.
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
from allostery.labels import build_labels, ligand_groups_from_atomgroup  # noqa: E402
from backend.discovery import get_uniprot, same_protein_entries  # noqa: E402
from backend.rcsb import (  # noqa: E402
    _chem_comp_record, _is_aliphatic_additive, classify_ligand, entry_summary,
)
from task0163_external_baseline_scoring import _run_fpocket  # noqa: E402
from task0204_positive_control import score_structure  # noqa: E402
from task0204_rotamer_repack_baseline import (  # noqa: E402
    _load_apo_holo, _select_window, _best_druggability_at_window, _is_hit,
)

OUT_DIR = _ROOT / "results_task0214_apo_reselection"
TASK0209_RESULTS = _ROOT / "results_task0209_instance_verification" / "instance_verification.json"


def _holo_native_hit(name: str) -> bool | None:
    """[[TASK-0209]]'s own `holo_native.hit` for `name`, loaded from its
    stored results rather than re-derived or assumed. Leg A only
    re-selects the apo structure -- the holo side, and its hit status, is
    unchanged by anything in this script. The VALID rule
    (`NOT apo_hit AND holo_hit`, verbatim from TASK-0209) needs both
    halves; scoring only the new apo candidate and treating a miss there
    as sufficient was a real bug caught before this task's write-up (see
    Done section) -- `holo_native_hit=False` on all 5 INVALID targets,
    without exception, per TASK-0209's own table, so no amount of apo
    re-selection alone can cross the bar for any of them."""
    data = json.loads(TASK0209_RESULTS.read_text())
    entry = data.get(name)
    if not entry or "error" in entry.get("ladder", {}):
        return None
    return entry["ladder"]["holo_native"].get("hit")

# The 5 INVALID targets from TASK-0209, in the same order the task file
# lists them. KRAS_G12C is scored first, separately, as the known-answer
# check (must reproduce ~0.001 -> 0.886 through THIS pipeline, not just
# cite TASK-0209's stored number, to confirm the harness itself).
KNOWN_ANSWER_TARGET = "KRAS_G12C"
INVALID_TARGETS = ["BCR_ABL1", "CARDIAC_MYOSIN", "GLUCOKINASE", "CASPASE1", "CASPASE7"]

MAX_CANDIDATES_SCORED = 5
RESOLUTION_MAX = 2.5


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _is_buffer_or_water(code: str, heavy, elements: dict) -> bool:
    """True iff `code` counts as harmless (water or a true small buffer/ion)
    for this filter's purposes.

    Deliberately does NOT just call `classify_ligand` and check for its
    "solvent/ion" category, even though that is what the task's own text
    describes ("Buffer/cryoprotectant status from rcsb.classify_ligand").
    Tested directly before writing this filter: `classify_ligand("MYR")`
    returns `("solvent/ion", False)` -- BCR_ABL1's own myristate, the
    exact ligand TASK-0209 found holding a pocket open, is bucketed by
    the register's own classifier as a harmless additive (its curated
    `_NON_DRUG` set lists MYR under "lipids / fatty acids / alkanes", a
    deliberate choice for OTHER purposes -- most fatty acids bound at a
    crystal surface really are inert). Naively reusing that category here
    would silently let a second MYR-shaped candidate straight through the
    filter this task exists to build. `_is_aliphatic_additive` (the same
    private helper `classify_ligand` itself calls internally) is used
    directly instead, so a long-chain lipid/fatty-acid/detergent is
    always treated as NOT safe regardless of `classify_ligand`'s own
    top-level bucket -- still chem_comp-data-driven, not a hand-written
    per-ligand list; only the *boundary* differs from `classify_ligand`'s
    own drug/non-drug split, not the data source.
    """
    code = (code or "").strip().upper()
    if code in ("HOH", "DOD", "WAT"):
        return True
    if heavy is not None and heavy <= 2:
        return True
    if elements and _is_aliphatic_additive(elements):
        return False
    cat, _ = classify_ligand(code, n_atoms=heavy)
    return cat == "solvent/ion"


def _target_window(name: str, cfg: dict):
    """The target's own existing curated pocket window, as (chain, resnum)
    pairs -- identical derivation to [[TASK-0209]]'s own
    `_select_window(apo, labels_obj.pocket)`, not re-derived differently."""
    apo, holo = _load_apo_holo(name, cfg)
    pocket_cutoff = float(cfg.get("pocket_contact_cutoff", 4.5))
    labels_obj = build_labels(apo, holo, cfg, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        return None, None, pocket_cutoff
    window = _select_window(apo, labels_obj.pocket)
    return window, apo, pocket_cutoff


def _candidate_survives_filter(pdb_id: str, window: list, pocket_cutoff: float) -> dict:
    """Fetch `pdb_id` raw, enumerate every non-water HETATM group, flag any
    within `pocket_cutoff` of the window's OWN coordinates in this
    candidate's own frame (same (chain, resnum) pairs as the incumbent --
    if this candidate is a genuinely different construct/numbering, the
    window residues simply will not be found, reported as
    `window_not_found`, not silently scored). Returns a dict with
    `survives` (bool) and supporting detail for the report."""
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
        findings.append({
            "resname": code, "resnum": g.resnum, "chain": g.chain,
            "min_dist_to_window": round(min_dist, 2), "treated_as_buffer": safe,
        })
    unsafe = [f for f in findings if not f["treated_as_buffer"]]
    return {"survives": not unsafe, "reason": None if not unsafe else "unsafe_hetatm_near_window",
            "near_pocket_hetatm": findings}


def _write_native_protein_pdb(pdb_id: str, chains, out_path: Path) -> None:
    import prody

    prody.confProDy(verbosity="none")
    struct = prody.parsePDB(pdb_id, compressed=False)
    alt_locs = struct.getAltlocs()
    if alt_locs is not None and any(a not in ("", " ", "\x00") for a in alt_locs):
        struct = struct.select("altloc _ A") or struct
    chain_part = " and (" + " or ".join(f"chain {c}" for c in chains) + ")"
    struct_clean = struct.select(f"protein{chain_part}")
    if struct_clean is None:
        raise ValueError(f"no protein atoms for chains {chains} in {pdb_id}")
    prody.writePDB(str(out_path), struct_clean.copy())


def _discover_candidates(name: str, cfg: dict, incumbent_apo: str) -> list:
    unis = get_uniprot(incumbent_apo)
    if not unis:
        return []
    ids = same_protein_entries(incumbent_apo, max_n=40, with_ligand=False)
    holo_pdb = (cfg.get("holo_pdb") or "").upper()
    out = []
    for pid in ids:
        if pid.upper() in (incumbent_apo.upper(), holo_pdb):
            continue
        summary = entry_summary(pid)
        method = (summary.get("method") or "").lower()
        res = summary.get("resolution")
        if "x-ray" not in method:
            continue
        if res is None or res > RESOLUTION_MAX:
            continue
        out.append({"pdb_id": pid, **summary})
    out.sort(key=lambda c: c.get("resolution") or 99)
    return out


def run_target(name: str) -> dict:
    t0 = time.monotonic()
    cfg = load_target_config(name)
    window, apo, pocket_cutoff = _target_window(name, cfg)
    if window is None:
        return {"target": name, "error": "no resolvable pocket window"}
    target_set = set(window)
    apo_chains = cfg.get("apo_chains") or cfg.get("chains")
    incumbent_apo = cfg["apo_pdb"]

    _log(f"{name}: window = {len(window)} residues, incumbent apo = {incumbent_apo}")
    candidates = _discover_candidates(name, cfg, incumbent_apo)
    _log(f"{name}: {len(candidates)} candidate depositions (X-ray, <={RESOLUTION_MAX} A)")

    result = {"target": name, "window": window, "incumbent_apo": incumbent_apo,
              "n_candidates_found": len(candidates), "candidates": []}

    scored = 0
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for cand in candidates:
            if scored >= MAX_CANDIDATES_SCORED:
                break
            pid = cand["pdb_id"]
            entry: dict = {"pdb_id": pid, "resolution": cand.get("resolution"),
                            "method": cand.get("method"), "title": cand.get("title")}
            try:
                audit = _candidate_survives_filter(pid, window, pocket_cutoff)
            except Exception as exc:  # noqa: BLE001
                entry["error"] = f"audit {type(exc).__name__}: {exc}"
                result["candidates"].append(entry)
                continue
            entry["audit"] = audit
            if not audit["survives"]:
                _log(f"{name}: {pid} excluded ({audit['reason']})")
                result["candidates"].append(entry)
                continue
            try:
                cand_pdb = tmp / f"{pid.lower()}_native.pdb"
                _write_native_protein_pdb(pid, apo_chains, cand_pdb)
                entry["score"] = score_structure(cand_pdb, target_set, tmp)
            except Exception as exc:  # noqa: BLE001
                entry["error"] = f"score {type(exc).__name__}: {exc}"
                result["candidates"].append(entry)
                continue
            scored += 1
            apo_hit = entry["score"].get("hit")
            # "apo_closed": this candidate's OWN native structure misses
            # the hit bar -- necessary but not sufficient. Full VALID
            # rule needs the (unchanged) holo side too, checked below,
            # not here -- see `_holo_native_hit`'s own docstring.
            entry["verdict"] = "apo_closed" if apo_hit is False else ("apo_still_open" if apo_hit is True else "ERROR")
            _log(f"{name}: {pid} scored -- {entry['score']} -> {entry['verdict']}")
            result["candidates"].append(entry)

    holo_hit = _holo_native_hit(name)
    result["holo_native_hit"] = holo_hit
    apo_closed_candidates = [c["pdb_id"] for c in result["candidates"] if c.get("verdict") == "apo_closed"]
    result["apo_closed_candidates"] = apo_closed_candidates
    # The actual, pre-registered VALID rule -- verbatim, both halves required.
    result["recovered"] = bool(holo_hit is True and apo_closed_candidates)
    result["best_recovery"] = apo_closed_candidates[0] if result["recovered"] else None
    result["blocked_by"] = (
        None if result["recovered"]
        else "holo_native_hit=False (unchanged by Leg A)" if holo_hit is not True
        else "no candidate apo scored closed"
    )
    result["elapsed_s"] = round(time.monotonic() - t0, 1)
    _log(f"{name}: recovered={result['recovered']} best={result['best_recovery']} "
         f"blocked_by={result['blocked_by']}")
    return result


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    results: dict = {}

    _log(f"=== KNOWN-ANSWER CHECK: {KNOWN_ANSWER_TARGET} ===")
    cfg = load_target_config(KNOWN_ANSWER_TARGET)
    window, apo, pocket_cutoff = _target_window(KNOWN_ANSWER_TARGET, cfg)
    target_set = set(window)
    apo_chains = cfg.get("apo_chains") or cfg.get("chains")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        incumbent_pdb = tmp / f"{cfg['apo_pdb'].lower()}_native.pdb"
        _write_native_protein_pdb(cfg["apo_pdb"], apo_chains, incumbent_pdb)
        known_answer_score = score_structure(incumbent_pdb, target_set, tmp)
    _log(f"{KNOWN_ANSWER_TARGET} incumbent apo re-scored through this pipeline: {known_answer_score}")
    results["_known_answer_check"] = {
        "target": KNOWN_ANSWER_TARGET, "apo_pdb": cfg["apo_pdb"], "score": known_answer_score,
        "passes": bool(known_answer_score.get("hit") is False),
    }
    if known_answer_score.get("hit") is not False:
        _log("KNOWN-ANSWER CHECK FAILED -- harness has drifted from TASK-0209's own "
             "result. Proceeding anyway so the failure is on record, but treat every "
             "number below as suspect until this is root-caused.")

    for name in INVALID_TARGETS:
        _log(f"=== {name} ===")
        try:
            results[name] = run_target(name)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            results[name] = {"target": name, "error": f"{type(exc).__name__}: {exc}"}
        (OUT_DIR / "apo_reselection.json").write_text(json.dumps(results, indent=1, default=str))

    print("\n=== TASK-0214 Leg A: apo re-selection ===")
    kac = results["_known_answer_check"]
    print(f"Known-answer check ({KNOWN_ANSWER_TARGET}): passes={kac['passes']} score={kac['score']}")
    n_recovered = 0
    for name in INVALID_TARGETS:
        r = results[name]
        if "error" in r:
            print(f"{name}: ERROR {r['error']}")
            continue
        print(f"{name}: candidates_found={r['n_candidates_found']} recovered={r['recovered']} "
              f"best={r['best_recovery']}")
        n_recovered += int(r["recovered"])
    print(f"\nLeg A recovered {n_recovered}/{len(INVALID_TARGETS)} of the INVALID targets.")
    print(f"Revised usable-instance count: {2 + n_recovered}/7 "
          f"(TASK-0209's 2 + Leg A's {n_recovered} recoveries).")
    print(f"Leg B needed (count < 5)? {'yes' if (2 + n_recovered) < 5 else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
