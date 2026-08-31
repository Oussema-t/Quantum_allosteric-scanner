"""TASK-0302 -- Sibling-conformer pocket persistence as an independent
selector signal.

[[TASK-0301]] found every rule in the 61-rule family is a function of the
same two inputs (distance-to-seed, fpocket druggability), so no
ensembling over them can add real evidence. This task tests a genuinely
different kind of evidence: does a candidate cavity, detected on the
target's own apo structure, PERSIST as a cavity in independently solved
sibling structures of the same protein (>=95% sequence identity)? The
external review's own handover (.ai/reviews/2026-08-29 - distal
pockets/, section 4) already scanned feasibility live via
search.rcsb.org: every target has siblings (median 53, min 10, none
below 5) -- `siblings.json` there holds that scan, reused here, not
re-queried (its own apo/chain keys checked directly against this repo's
own `config/candidate_targets_task0243.yaml` before trusting it: exact
match, 20/20).

THE CIRCULARITY TRAP, this task's own Constraint, handled first, not as
an afterthought: most siblings are holo, and some carry the target's own
allosteric drug. Scoring "persistence" over structures solved WITH the
drug bound would just measure the drug's own imprint again -- the same
error already flagged for the matched-holo control. Two filters are
applied and reported separately, per the Constraint's own explicit
"report both" instruction:
  min_bar    -- exclude only siblings carrying the target's own
                `drug_ligand` code (the Constraint's own stated minimum).
  strict_apo -- exclude any sibling carrying ANY ligand `backend.rcsb.
                classify_ligand` categorises as "drug" or "ligand"
                (cofactors/solvent/ions allowed) -- reuses [[TASK-0278]]'s
                own already-validated classification, not a new
                heuristic.

METHOD: for each surviving sibling, fetch, run fpocket
(`t0242.fpocket_candidates`, the identical apparatus [[TASK-0282]]/
[[TASK-0303]] use), and map its own detected-pocket residues onto the
TARGET's own apo numbering via `allostery.labels._needleman_wunsch_map`
(sequence-only, register-consistent -- the same primitive
`holo_pocket_mask` already uses for apo/holo numbering offsets, reused
here across independently-deposited entries rather than same-entry
apo/holo). Best-matching sibling chain chosen by alignment identity, not
assumed to be chain A. Persistence(candidate) = fraction of scored
siblings whose own mapped pocket-residue set overlaps that candidate at
>= `OVERLAP_JACCARD` Jaccard.

PROOF-OF-CONCEPT BOUND, stated not hidden (this task's own Note: "run
this as a proof of concept... validation belongs on the larger cohort,
[[TASK-0304]]"): at most `MAX_SIBLINGS_SCORED` siblings are fpocket-
scored per target after the holo filter (RCSB list order, no ranking
applied) -- a real, disclosed cap keeping ~20 targets x <=N fpocket runs
each tractable in one background pass, not an attempt at exhaustive
coverage.

Reuses, does not re-derive: `task0242_two_stage_dryrun.prep`/
`fpocket_candidates` (candidate/truth apparatus, same call shape as
[[TASK-0282]]/[[TASK-0303]] -- a separate, duplicated implementation per
the lane-collision discipline those tasks established, not an import
from `task0282_pocket_selection_sweep`, which this task does not touch
either), `backend.rcsb.ligands_and_sites` ([[TASK-0278]]'s own ligand-
classification audit tool), `allostery.labels._needleman_wunsch_map`/
`_sequence`, `task0261_cluster_robust_stats.CM`/`cluster_sign_flip_test`,
`task0249_composite_dumb_baseline.z`.

Run: ../.venv/bin/python3 scripts/task0302_sibling_persistence.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402
import yaml  # noqa: E402

prody.confProDy(verbosity="none")

_orig_parsePDB = prody.parsePDB


def _parsePDB_all_altloc(*a, **kw):
    kw.setdefault("altloc", "all")
    return _orig_parsePDB(*a, **kw)


prody.parsePDB = _parsePDB_all_altloc

import task0242_two_stage_dryrun as t0242  # noqa: E402
from allostery.labels import _needleman_wunsch_map, _sequence  # noqa: E402
from backend.rcsb import ligands_and_sites  # noqa: E402
from task0261_cluster_robust_stats import CM, cluster_sign_flip_test  # noqa: E402
from task0249_composite_dumb_baseline import z as zscore  # noqa: E402

OUT = _ROOT / "results/tasks/0302_sibling_persistence"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
SIBLINGS_JSON = _ROOT.parent / ".ai/reviews/2026-08-29 - distal pockets/siblings.json"
DROPPED = ["HIV_INTEGRASE_MUT871", "HIV_INTEGRASE_MUT916"]  # TASK-0253 finding, matches CM's own 20

MAX_SIBLINGS_SCORED = 10   # proof-of-concept bound, see module docstring
MAX_SIBLINGS_CHECKED = 30  # cap applied BEFORE the holo filter itself -- checked directly, not
                            # assumed: unfiltered sibling counts run to 493 (SUMO_E1_FHJ, itself a
                            # pagination-cap artifact of siblings.py's own 500-row RCSB query) and
                            # 1999 total across the frozen 20 -- one live RCSB fetch per sibling for
                            # the holo check alone, which is not tractable at that scale in one pass.
                            # RCSB list order (siblings.json's own `entries95`), no ranking applied.
OVERLAP_JACCARD = 0.2      # a mapped sibling pocket "overlaps" a target candidate at this Jaccard or above


# ---------------------------------------------------------------------------
# Siblings, holo filter (applied FIRST, per this task's own Constraint)
# ---------------------------------------------------------------------------

def target_sibling_list(t: str, cfg: dict, sib: dict) -> list[str]:
    apo_pdb = cfg["apo_pdb"].upper()
    chains = cfg.get("apo_chains") or cfg.get("chains")
    ents: set = set()
    for ch in chains:
        k = f"{apo_pdb}_{ch}"
        if k in sib:
            ents |= set(sib[k]["entries95"])
    ents.discard(apo_pdb)
    return sorted(ents)


def holo_filter(pdb_id: str, drug_ligand: str) -> dict:
    """Both filters this task's own Constraint requires, reported
    separately. Returns {"survives_min_bar": bool, "survives_strict_apo":
    bool, "ligand_codes": [...]} or {"error": ...} on fetch failure --
    a real network/parse failure is excluded from the denominator, not
    silently treated as passing."""
    try:
        ligs = ligands_and_sites(pdb_id)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}
    codes = [g["code"] for g in ligs]
    survives_min = drug_ligand.upper() not in {c.upper() for c in codes}
    survives_strict = not any(g["category"] in ("drug", "ligand") for g in ligs)
    return {"survives_min_bar": survives_min, "survives_strict_apo": survives_strict, "ligand_codes": codes}


# ---------------------------------------------------------------------------
# Per-sibling: fetch, fpocket, map onto target numbering
# ---------------------------------------------------------------------------

def sibling_mapped_pockets(pdb_id: str, target_seq: str) -> list[set] | None:
    """Fetches `pdb_id`, picks whichever protein chain best aligns to
    `target_seq` (not assumed to be chain A -- siblings can be a
    different oligomeric state/construct), runs fpocket on the sibling's
    OWN full deposited protein content, and returns each detected
    pocket's own residues mapped onto TARGET sequence-index positions
    (via `_needleman_wunsch_map`, sequence-only, no 3D superposition --
    matching `holo_pocket_mask`'s own established precedent). Returns
    None on any real failure (fetch/parse/fpocket), not silently
    zero-filled."""
    try:
        full = prody.parsePDB(pdb_id, compressed=False)
    except Exception:  # noqa: BLE001
        return None
    if full is None:
        return None
    prot = full.select("protein and not hetero")
    if prot is None:
        return None
    chain_ids = sorted(set(prot.getChids()))

    best_chain, best_map, best_score = None, None, -1.0
    for ch in chain_ids:
        sub = prot.select(f"chain {ch}")
        if sub is None or sub.numResidues() < 30:
            continue
        resnames = [r.getResname() for r in sub.getHierView().iterResidues()]
        seq = _sequence(resnames)
        b_to_a = _needleman_wunsch_map(target_seq, seq)  # {sib_idx: target_idx}
        if len(b_to_a) > best_score:
            best_score = len(b_to_a)
            best_chain, best_map = ch, b_to_a
    if best_chain is None or best_score < 10:
        return None

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        pdb_path = tmp / f"{pdb_id.lower()}_full.pdb"
        prody.writePDB(str(pdb_path), prot)
        pockets = t0242.fpocket_candidates(pdb_path, tmp)
    if isinstance(pockets, dict):
        return None

    # per-residue sequence index within best_chain, in file order (matches
    # the order _sequence()/the alignment above were built from)
    sub = prot.select(f"chain {best_chain}")
    resn_best = [r.getResnum() for r in sub.getHierView().iterResidues()]
    seq_idx_of = {("_", int(rn)): i for i, rn in enumerate(resn_best)}
    # fpocket's own p["resnums"] is a (chain, resnum) tuple set (TASK-0298)
    mapped = []
    for p in pockets:
        target_idx = set()
        for (ch, rn) in p["resnums"]:
            if ch != best_chain:
                continue
            si = seq_idx_of.get(("_", int(rn)))
            if si is None:
                continue
            ti = best_map.get(si)
            if ti is not None:
                target_idx.add(ti)
        if target_idx:
            mapped.append(target_idx)
    return mapped


# ---------------------------------------------------------------------------
# Per-target: candidates, persistence, standalone + tie-break scoring
# ---------------------------------------------------------------------------

def build_target(t: str, sib: dict) -> dict:
    cfg2, apo, seed, pocket = t0242.prep(t)
    if len(seed) == 0:
        return {"error": "empty active-site seed"}
    resn = np.asarray(apo.resnums)
    chids = np.asarray(apo.chain_ids)
    idx_of = {(str(c), int(r)): i for i, (c, r) in enumerate(zip(chids, resn))}
    apo_ch = cfg2.get("apo_chains") or cfg2.get("chains")
    target_seq = _sequence(list(apo.resnames))

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        ag = prody.parsePDB(cfg2["apo_pdb"], compressed=False).select(
            "protein and (" + " or ".join(f"chain {c}" for c in apo_ch) + ")"
        )
        pdb = tmp / f"{t.lower()}_apo.pdb"
        prody.writePDB(str(pdb), ag)
        pockets = t0242.fpocket_candidates(pdb, tmp)
    if isinstance(pockets, dict):
        return {"error": pockets["error"]}

    cands = []
    for p in pockets:
        ii = [idx_of[r] for r in p["resnums"] if r in idx_of]
        if not ii:
            continue
        ii = np.asarray(ii, dtype=int)
        n_res = int(len(ii))
        overlap_count = int(pocket[ii].sum())
        cands.append({
            "id": p["id"], "n_res": n_res, "overlap_count": overlap_count,
            "EH": overlap_count / n_res, "fpocket_drug": float(p.get("druggability_score") or 0.0),
            "seq_idx": set(ii.tolist()),  # apo array index doubles as sequence position here (built in file order)
        })
    if not cands:
        return {"error": "fpocket found no residue-resolvable candidates"}

    # --- siblings: list, cap the candidate pool, THEN holo filter, THEN score ---
    all_sibs_uncapped = target_sibling_list(t, cfg2, sib)
    all_sibs = all_sibs_uncapped[:MAX_SIBLINGS_CHECKED]
    filt = {s: holo_filter(s, cfg2["drug_ligand"]) for s in all_sibs}
    ok_min = [s for s in all_sibs if not filt[s].get("error") and filt[s]["survives_min_bar"]]
    ok_strict = [s for s in all_sibs if not filt[s].get("error") and filt[s]["survives_strict_apo"]]

    # Shared cache across both variants -- `ok_strict` is always a subset of
    # `ok_min` by construction (the strict filter is a superset of
    # conditions), so scoring both from one cache avoids re-fetching/
    # re-fpocketing the same sibling twice.
    mapped_cache: dict = {}

    def get_mapped(s):
        if s not in mapped_cache:
            mapped_cache[s] = sibling_mapped_pockets(s, target_seq)
        return mapped_cache[s]

    def score_variant(candidate_list, cap):
        scored = candidate_list[:cap]
        n_scored, mapped_all = 0, []
        for s in scored:
            m = get_mapped(s)
            if m is None:
                continue
            n_scored += 1
            mapped_all.append(m)
        result = {}
        for c in cands:
            hits = 0
            for sib_pockets in mapped_all:
                best_jac = 0.0
                for sp in sib_pockets:
                    inter = len(c["seq_idx"] & sp)
                    union = len(c["seq_idx"] | sp)
                    jac = inter / union if union else 0.0
                    best_jac = max(best_jac, jac)
                if best_jac >= OVERLAP_JACCARD:
                    hits += 1
            result[c["id"]] = hits / n_scored if n_scored else float("nan")
        return n_scored, result

    n_scored_min, persist_min = score_variant(ok_min, MAX_SIBLINGS_SCORED)
    n_scored_strict, persist_strict = score_variant(ok_strict, MAX_SIBLINGS_SCORED)
    for c in cands:
        c["persistence"] = persist_min[c["id"]]
        c["persistence_strict_apo"] = persist_strict[c["id"]]

    return {
        "cands": [{k: v for k, v in c.items() if k != "seq_idx"} for c in cands],
        "n_pocket": int(pocket.sum()),
        "n_siblings_available": len(all_sibs_uncapped), "n_siblings_checked": len(all_sibs),
        "n_siblings_min_bar": len(ok_min),
        "n_siblings_strict_apo": len(ok_strict), "n_siblings_scored": n_scored_min,
        "n_siblings_scored_strict_apo": n_scored_strict,
    }


def ranker_eh(cands: list, key: str) -> float:
    survivors = [c for c in cands if not np.isnan(c[key])]
    if not survivors:
        return float("nan")
    top = max(survivors, key=lambda c: c[key])
    return float(top["EH"])


def random_eh(cands: list) -> float:
    return float(np.mean([c["EH"] for c in cands]))


def tiebreak_eh(cands: list) -> float:
    """hop>=1 + drug_alone (TASK-0282's own LOTO-selected rule) is not
    reusable here (distance-to-seed fields live in that module's own
    build_target, not this one) -- druggability alone, with persistence
    as the tie-break, is this task's own minimal, faithful reproduction
    of the same "rank by the LOTO-selected rule, persistence decides
    ties" design its own Scope names."""
    survivors = [c for c in cands if not np.isnan(c["persistence"])]
    if not survivors:
        return float("nan")
    top = max(survivors, key=lambda c: (c["fpocket_drug"], c["persistence"]))
    return float(top["EH"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    new_cand = yaml.safe_load(FROZEN_CONFIG.read_text())["targets"]
    t0242.CAND = new_cand
    targets = [t for t in new_cand if t not in DROPPED]
    assert set(targets) == set(CM.keys()), "target set must match task0261's own 20-target CM"
    sib = json.loads(SIBLINGS_JSON.read_text())

    per_target = {}
    print(f"{'target':<20}{'avail':>7}{'checked':>9}{'min_bar':>9}{'strict':>8}{'scored':>8}"
          f"{'EH_rand':>9}{'EH_pers':>9}{'EH_tie':>8}")
    for t in targets:
        r = build_target(t, sib)
        if "error" in r:
            print(f"{t:<20}  SKIP -- {r['error']}")
            continue
        cands = r["cands"]
        eh_rand = random_eh(cands)
        eh_pers = ranker_eh(cands, "persistence")
        eh_pers_strict = ranker_eh(cands, "persistence_strict_apo")
        eh_tie = tiebreak_eh(cands)
        per_target[t] = {
            "n_siblings_available": r["n_siblings_available"], "n_siblings_checked": r["n_siblings_checked"],
            "n_siblings_min_bar": r["n_siblings_min_bar"],
            "n_siblings_strict_apo": r["n_siblings_strict_apo"], "n_siblings_scored": r["n_siblings_scored"],
            "n_siblings_scored_strict_apo": r["n_siblings_scored_strict_apo"],
            "eh_random": eh_rand, "eh_persistence": eh_pers,
            "eh_persistence_strict_apo": eh_pers_strict, "eh_tiebreak": eh_tie,
            "cands": cands,
        }
        print(f"{t:<20}{r['n_siblings_available']:>7}{r['n_siblings_checked']:>9}{r['n_siblings_min_bar']:>9}"
              f"{r['n_siblings_strict_apo']:>8}{r['n_siblings_scored']:>8}"
              f"{eh_rand:>9.4f}{eh_pers:>9.4f}{eh_tie:>8.4f}")

    print("\n### Standalone: persistence-selected EH vs random, cluster-robust (TASK-0261's exact sign-flip test) ###")
    deltas = {t: d["eh_persistence"] - d["eh_random"] for t, d in per_target.items()
              if not np.isnan(d["eh_persistence"])}
    res = cluster_sign_flip_test(deltas)
    print(f"  n={len(deltas)}  n_clusters={res['n_clusters']}  "
          f"mean_delta={np.mean(list(deltas.values())):+.4f}  p={res['p_value']:.4f}")

    print("\n### Standalone, STRICT apo-only siblings (this task's own Constraint: report both ways) ###")
    deltas_strict = {t: d["eh_persistence_strict_apo"] - d["eh_random"] for t, d in per_target.items()
                      if not np.isnan(d["eh_persistence_strict_apo"])}
    n_zero_strict = sum(1 for t in per_target if per_target[t]["n_siblings_scored_strict_apo"] == 0)
    print(f"  {n_zero_strict}/{len(per_target)} targets have ZERO strict-apo-only siblings scored "
          f"(excluded from this test, not treated as a zero delta)")
    if deltas_strict:
        res_strict = cluster_sign_flip_test(deltas_strict)
        print(f"  n={len(deltas_strict)}  n_clusters={res_strict['n_clusters']}  "
              f"mean_delta={np.mean(list(deltas_strict.values())):+.4f}  p={res_strict['p_value']:.4f}")
    else:
        print("  no targets with a scored strict-apo-only sibling -- not computed")

    print("\n### Tie-break: (drug_alone, persistence) vs drug_alone alone, cluster-robust ###")
    drug_alone = {t: max((c for c in d["cands"]), key=lambda c: c["fpocket_drug"])["EH"]
                  for t, d in per_target.items()}
    deltas_tb = {t: d["eh_tiebreak"] - drug_alone[t] for t, d in per_target.items()
                 if not np.isnan(d["eh_tiebreak"])}
    res_tb = cluster_sign_flip_test(deltas_tb)
    print(f"  n={len(deltas_tb)}  n_clusters={res_tb['n_clusters']}  "
          f"mean_delta={np.mean(list(deltas_tb.values())):+.4f}  p={res_tb['p_value']:.4f}")

    print("\n### Independence: partial correlation of persistence with fpocket_drug, controlling pocket size ###")
    pers_all, drug_all, size_all = [], [], []
    for t, d in per_target.items():
        cs = [c for c in d["cands"] if not np.isnan(c["persistence"])]
        if len(cs) < 3 or len(set(c["persistence"] for c in cs)) < 2:
            continue
        pers_all.append(zscore([c["persistence"] for c in cs]))
        drug_all.append(zscore([c["fpocket_drug"] for c in cs]))
        size_all.append(zscore([c["n_res"] for c in cs]))
    if pers_all:
        from scipy.stats import spearmanr
        pers_all = np.concatenate(pers_all)
        drug_all = np.concatenate(drug_all)
        size_all = np.concatenate(size_all)

        def residualize(y, x):
            A = np.column_stack([x, np.ones_like(x)])
            coef, *_ = np.linalg.lstsq(A, y, rcond=None)
            return y - A @ coef

        rho_raw, p_raw = spearmanr(pers_all, drug_all)
        rho_partial, p_partial = spearmanr(residualize(pers_all, size_all), residualize(drug_all, size_all))
        rho_size, p_size = spearmanr(pers_all, size_all)
        print(f"  Spearman(persistence, fpocket_drug), pooled per-target-z, n={len(pers_all)}: "
              f"rho={rho_raw:.3f} (p={p_raw:.3g})")
        print(f"  Spearman(persistence, n_res [pocket size]): rho={rho_size:.3f} (p={p_size:.3g})")
        print(f"  Partial (persistence, fpocket_drug), controlling n_res: rho={rho_partial:.3f} (p={p_partial:.3g})")
    else:
        print("  insufficient variance in persistence across targets -- not computed")

    out = {"per_target": per_target, "max_siblings_scored": MAX_SIBLINGS_SCORED, "overlap_jaccard": OVERLAP_JACCARD}
    (OUT / "sibling_persistence.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"\nWrote {OUT / 'sibling_persistence.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
