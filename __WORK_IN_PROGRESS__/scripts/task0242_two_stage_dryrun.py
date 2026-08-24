"""TASK-0242 -- DRY RUN of the joint protocol proposed by the collaborating
thread, executed on our side before anyone signs anything.

Their design, faithfully: fpocket proposes CANDIDATE POCKETS on the apo
structure; an operator ranks *within* that candidate set. That is a genuinely
different experiment from this register's per-residue AUC, and they are
correct that our compact-patch null does not test it. So it is rebuilt here
rather than argued with.

Their spec, adopted verbatim:
  - candidate pockets from fpocket on apo
  - MIN_HOP = 2 (pockets closer than 2 contact-graph hops from the seed are
    excluded as non-distal)
  - ONE pre-registered operator (H_new / converged incoherent CTQW -- this
    register's GAUGE, fixed before any number below was seen)
  - hop reported as a COVARIATE, not a filter, in the ranking comparison
  - targets neither side tuned on

THE CONTROL THEIR ARGUMENT OMITS. "Across 14 Hamiltonians the modal pocket is
the true drug pocket (drug_frac=1.00)" is a statement about agreement among
operators, not about validity. Fourteen operators that share a confound agree
perfectly and are all wrong together -- this register measured exactly that
degeneracy (TASK-0199: ~28 observables collapse to effective rank 2.6-4.1).
The question consensus cannot answer is:

    does the operator rank the true pocket better than fpocket's OWN
    druggability score already ranks it, on the same candidate list?

If not, the two-stage pipeline's performance is fpocket's, and the operator
-- any of the 14 -- is decoration. So every ranker below is scored on the
identical candidate set: the operator, fpocket's own score, the hop covariate,
and a random control.
"""
from __future__ import annotations
import json, subprocess, sys, tempfile, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path: sys.path.insert(0, str(_p))
import yaml, prody; prody.confProDy(verbosity="none")
CAND = yaml.safe_load((_ROOT/"config"/"candidate_targets_task0216.yaml").read_text())["targets"]
from allostery import clean as _clean
_o = _clean.load_target_config
_clean.load_target_config = lambda n, p=None: CAND[n] if n in CAND else _o(n, p)
from allostery.clean import clean_from_config
from allostery.labels import (holo_pocket_mask, terminal_mask, build_labels,
                              ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue)
from allostery.baselines import hop_from_seed, _parse_fpocket_info
from allostery.hamiltonians import build_H_new
from allostery.propagators import time_averaged_ctqw_converged
from backend import active_site as backend_as

MIN_HOP = 2                      # their spec
PREREG_OPERATOR = "H_new/ctqw_converged_incoherent"   # their spec: ONE operator
FPOCKET_BIN = str(_ROOT / "tools" / "fpocket" / "bin" / "fpocket")
# targets neither side tuned on (this register scored them in TASK-0216 but
# tuned nothing on them -- disclosed, not hidden). Mandatory 3 appended as a
# TUNED-ON reference row, labelled as such.
UNTUNED = ["HIV1_RT", "TEM1_BLA_CBT", "TEM1_BLA_FTA", "GLUR2_TRU",
           "GLUR2_ANIRACETAM", "GLUK1_BPAM", "FPPS_YF0282",
           # every remaining targets.yaml entry with a real small-molecule
           # drug_ligand and a holo structure. Not tuned on: no parameter in
           # this pipeline was ever fitted to any of them. GLUCOKINASE carries
           # an open apo/holo chain-mismatch defect ([[TASK-0219]]) -- included
           # and flagged, not silently dropped.
           "PTP1B", "GLUCOKINASE", "CASPASE1", "CASPASE7"]
TUNED = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
OUT = _ROOT / "results/tasks/0242_two_stage_dryrun"


def fpocket_candidates(pdb_path: Path, work: Path):
    r = subprocess.run([FPOCKET_BIN, "-f", str(pdb_path)], cwd=work,
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        return {"error": f"fpocket exited {r.returncode}"}
    od = work / f"{pdb_path.stem}_out"
    info = od / f"{pdb_path.stem}_info.txt"
    if not info.exists():
        return {"error": "no info file"}
    pockets = _parse_fpocket_info(info.read_text())
    for p in pockets:
        f = od / "pockets" / f"pocket{p['id']}_atm.pdb"
        res = set()
        if f.exists():
            for line in f.read_text().splitlines():
                if line.startswith(("ATOM", "HETATM")):
                    try: res.add(int(line[22:26]))
                    except ValueError: pass
        p["resnums"] = res
    return [p for p in pockets if p["resnums"]]


def prep(t):
    cfg = dict(CAND[t]) if t in CAND else dict(_o(t))
    apo = clean_from_config(t, role="apo"); holo = clean_from_config(t, role="holo")
    ch = cfg.get("holo_chains") or cfg.get("chains")
    st = prody.parsePDB(cfg["holo_pdb"], compressed=False).select(" or ".join(f"chain {c}" for c in ch))
    holo.ligand_groups = ligand_groups_from_atomgroup(st)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(st, ch, holo.resnums)
    if t in CAND:
        det = backend_as.detect_active_site(cfg["apo_pdb"], chain=(cfg.get("apo_chains") or ch)[0])
        rn = np.asarray(apo.resnums)
        sd = np.sort(np.where(np.isin(rn, list(det.get("active_site") or [])))[0])
        raw = holo_pocket_mask(apo, holo, cfg["drug_ligand"], cutoff=float(cfg["pocket_contact_cutoff"]))
        n = len(rn); a = np.zeros(n, bool); a[sd] = True
        pocket = raw & ~a & ~terminal_mask(n, 0.05)
    else:
        lab = build_labels(apo, holo, cfg, cutoff=float(cfg.get("pocket_contact_cutoff", 4.5)))
        sd = np.where(lab.active_site)[0]; pocket = lab.pocket
    return cfg, apo, sd, pocket


def run(t, tuned, return_state=False):
    cfg, apo, seed, pocket = prep(t)
    coords = apo.coords; cut = float(cfg.get("enm_cutoff", 8.0))
    resn = np.asarray(apo.resnums)
    idx_of = {int(r): i for i, r in enumerate(resn)}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        apo_ch = (cfg.get("apo_chains") or cfg.get("chains"))
        ag = prody.parsePDB(cfg["apo_pdb"], compressed=False).select(
            "protein and (" + " or ".join(f"chain {c}" for c in apo_ch) + ")")
        pdb = tmp / f"{t.lower()}_apo.pdb"; prody.writePDB(str(pdb), ag)
        pockets = fpocket_candidates(pdb, tmp)
    if isinstance(pockets, dict):
        return {"target": t, "error": pockets["error"]}

    # baselines.hop_from_seed returns NEGATED BFS distance (higher = closer to
    # seed), so flip it back to true hop counts for the MIN_HOP distality filter.
    hops = -hop_from_seed(coords, seed, cutoff=cut)
    ctqw = time_averaged_ctqw_converged(
        build_H_new(coords, apo.bfactors, cutoff=cut), source=seed, coherent=False)
    seedset = set(int(resn[i]) for i in seed)
    truth = set(int(resn[i]) for i in np.where(pocket)[0])

    cands = []
    for p in pockets:
        ii = [idx_of[r] for r in p["resnums"] if r in idx_of]
        if not ii:
            continue
        # MIN_HOP: their distality filter, applied to the CANDIDATE, on the
        # pocket's minimum hop distance from the seed
        min_hop = float(np.min(hops[ii]))
        cands.append({
            "id": p["id"], "n_res": len(ii), "min_hop": min_hop,
            "fpocket_drug": p.get("druggability_score") or 0.0,
            "fpocket_score": p.get("score") or 0.0,
            "ctqw": float(np.mean(ctqw[ii])),
            "hop_cov": float(np.mean(hops[ii])),   # mean BFS hops from seed
            "overlap": len(set(p["resnums"]) & truth) / max(1, len(truth)),
            "is_seed_pocket": bool(set(p["resnums"]) & seedset),
            "res_idx": ii,   # apo-array indices, TASK-0244: re-scoring candidates under alternate seeds/nulls without re-running fpocket
        })
    kept = [c for c in cands if c["min_hop"] >= MIN_HOP]
    if not kept:
        return {"target": t, "error": f"MIN_HOP={MIN_HOP} removed all {len(cands)} candidates"}
    true_i = max(range(len(kept)), key=lambda i: kept[i]["overlap"])
    if kept[true_i]["overlap"] == 0.0:
        return {"target": t, "error": "true drug pocket not among surviving fpocket candidates",
                "n_candidates": len(cands), "n_kept": len(kept)}

    K = len(kept)
    rng = np.random.default_rng(7)
    ranks = {}
    for key, vals in (("ctqw", [c["ctqw"] for c in kept]),
                      ("fpocket_drug", [c["fpocket_drug"] for c in kept]),
                      ("fpocket_score", [c["fpocket_score"] for c in kept]),
                      ("hop_covariate", [-c["hop_cov"] for c in kept]),
                      ("random", list(rng.random(K)))):
        order = np.argsort(-np.asarray(vals, float))
        ranks[key] = int(np.where(order == true_i)[0][0]) + 1
    out = {"target": t, "tuned_on": tuned, "n_candidates": len(cands), "n_kept": K,
           "true_pocket_overlap": kept[true_i]["overlap"], "ranks": ranks,
           "n_seed_pockets_removed": sum(1 for c in cands if c["min_hop"] < MIN_HOP)}
    if return_state:
        # TASK-0244: enough state to re-score the identical candidate list
        # under an alternate seed or matched-null selection, without
        # re-running fpocket (the expensive step) or re-deriving candidates.
        # Not JSON-serializable (numpy arrays) -- opt-in only, main()'s own
        # dryrun.json write path is unaffected (return_state defaults False).
        out.update(kept=kept, true_i=true_i, seed_idx=[int(i) for i in seed],
                    coords=coords, bfactors=apo.bfactors, cut=cut, resn=resn)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    print(f"protocol: MIN_HOP={MIN_HOP}, operator={PREREG_OPERATOR}, hop=covariate\n")
    print(f"{'target':<18}{'tuned':>6}{'K':>4} | {'ctqw':>6}{'fpock_d':>8}{'fpock_s':>8}{'hop':>6}{'rand':>6}")
    for t, tuned in [(x, False) for x in UNTUNED] + [(x, True) for x in TUNED]:
        try:
            r = run(t, tuned)
        except Exception as e:
            r = {"target": t, "error": f"{type(e).__name__}: {e}"}
        rows.append(r)
        if "error" in r:
            print(f"{t:<18}{'yes' if tuned else 'no':>6}{'--':>4} | SKIP: {r['error'][:60]}")
            continue
        q = r["ranks"]
        print(f"{t:<18}{'yes' if tuned else 'no':>6}{r['n_kept']:>4} | {q['ctqw']:>6}{q['fpocket_drug']:>8}"
              f"{q['fpocket_score']:>8}{q['hop_covariate']:>6}{q['random']:>6}")

    ok = [r for r in rows if "error" not in r and not r["tuned_on"]]
    print(f"\n--- untuned targets only, n={len(ok)} (rank of the TRUE pocket, 1=best) ---")
    if ok:
        for key in ("ctqw", "fpocket_drug", "fpocket_score", "hop_covariate", "random"):
            rr = [r["ranks"][key] for r in ok]
            mrr = float(np.mean([1.0/x for x in rr]))
            top1 = sum(1 for x in rr if x == 1)
            exp = float(np.mean([1.0/r["n_kept"] for r in ok]))
            print(f"  {key:<15} mean rank {np.mean(rr):>5.2f}  MRR {mrr:.3f}  "
                  f"top-1 {top1}/{len(ok)}  (chance MRR~{exp:.3f})")
        wins = sum(1 for r in ok if r["ranks"]["ctqw"] < r["ranks"]["fpocket_drug"])
        ties = sum(1 for r in ok if r["ranks"]["ctqw"] == r["ranks"]["fpocket_drug"])
        print(f"\n  KEY CONTROL -- ctqw vs fpocket's own druggability, same candidate list:")
        print(f"    ctqw ranks true pocket better: {wins}/{len(ok)}   ties: {ties}   "
              f"worse: {len(ok)-wins-ties}")
    (OUT/"dryrun.json").write_text(json.dumps(rows, indent=1))
    print(f"\nwritten: {OUT/'dryrun.json'}")

if __name__ == "__main__":
    raise SystemExit(main())
