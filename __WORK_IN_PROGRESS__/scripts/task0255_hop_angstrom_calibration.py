"""TASK-0255 -- Does MIN_HOP >= 2 mean anything in Angstroms?

[[TASK-0246]] measured pocket residues concentrate at graph-hop 2-4 from the
active site. `MIN_HOP = 2` is the two-stage design's operational definition
of "distal" ([[TASK-0242]]/[[TASK-0244]]/[[TASK-0249]]). Nobody had checked
what a graph hop actually costs in real 3D separation -- [[TASK-0169]] already
found one case (KRAS_G12C) where a nominally-distal pocket sits at van der
Waals contact range (3.75 A Ca-Ca). This task calibrates the hop<->Angstrom
relationship across the full frozen set, using the true metric this
register's own labelling code uses for contacts: minimum HEAVY-ATOM distance
(`allostery.labels.protein_heavy_atoms_by_residue`), not Ca-Ca -- side chains
reach several A closer than backbone, per that function's own docstring.

Reuses, does not re-derive:
  - `task0242_two_stage_dryrun`'s own `prep()` (seed/pocket resolution) and
    `fpocket_candidates()` (candidate pockets on apo) -- the collaborating
    thread's own apparatus, already validated by [[TASK-0243]]/[[TASK-0249]].
  - [[TASK-0243]]'s own altloc="all" monkeypatch for `prody.parsePDB`.
  - [[TASK-0249]]'s own "empty active-site seed -> attempted-target failure,
    not silently ranked" guard (the HIV_INTEGRASE_MUT871/916 defect
    [[TASK-0253]] is independently re-auditing at its source).
  - `allostery.baselines.hop_from_seed`'s sign convention (negated BFS
    distance; flipped back to true hop counts here, same as task0242).

`run()`'s own body (build candidates, apply MIN_HOP, rank) is NOT imported
whole, because this task needs the *pre-filter* candidate list (with a
second, Euclidean, filter applied) that `run()` does not expose even under
`return_state=True`. The candidate-construction loop is therefore mirrored
here against the same primitives `run()` itself calls
(`fpocket_candidates`/`hop_from_seed`/`build_H_new`/
`time_averaged_ctqw_converged`), not copied from its internals blind.
"""
from __future__ import annotations

import json
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

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
from allostery.baselines import hop_from_seed  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402

OUT = _ROOT / "results/tasks/0255_hop_angstrom_calibration"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
K_MAX_SHELL = 8
CONTACT_ADJACENT_A = 8.0        # Scope's own bar
SEPARATION_BARS_A = (15.0, 20.0)  # Scope's own "external suggestion", pre-registered here


def min_heavy_atom_dist_to_seed(cfg: dict, apo, seed: np.ndarray) -> np.ndarray:
    """Per-residue minimum heavy-atom distance from any seed (active-site)
    residue, on the apo structure. NaN for residues with no resolved heavy
    atoms (should not happen for real protein residues; guarded, not
    assumed away).

    Does NOT reuse `allostery.labels.protein_heavy_atoms_by_residue` as-is:
    that helper's `resnum_to_seq_idx` dict is keyed on bare residue number
    only (correct for its own single-chain callers), which silently
    collapses same-numbered residues across chains in a multi-chain target
    -- confirmed directly on GAC_BPTES (3 chains, 1223 residues but only
    411 unique resnums; the bare-resnum map left 812/1223 residues with no
    heavy atoms at all, corrupting exactly the statistic this task exists
    to report). Re-implemented here keyed on (chain, resnum), the only
    thing that changes; everything else (heavy-atom selection, distances)
    is the same computation.
    """
    resn = np.asarray(apo.resnums)
    chids = np.asarray(apo.chain_ids)
    n = len(resn)
    apo_ch = cfg.get("apo_chains") or cfg.get("chains")
    ag = prody.parsePDB(cfg["apo_pdb"], compressed=False).select(
        "protein and (" + " or ".join(f"chain {c}" for c in apo_ch) + ")"
    )
    if ag is None:
        return np.full(n, np.nan)
    key_to_seq = {(str(c), int(r)): i for i, (c, r) in enumerate(zip(chids, resn))}
    atom_resnums = ag.getResnums()
    atom_chids = ag.getChids()
    heavy_seq = np.array(
        [key_to_seq.get((str(c), int(r)), -1) for c, r in zip(atom_chids, atom_resnums)],
        dtype=int,
    )
    keep = heavy_seq >= 0
    heavy_coords = ag.getCoords()[keep]
    heavy_seq = heavy_seq[keep]
    if len(heavy_coords) == 0:
        return np.full(n, np.nan)
    seed_atoms = heavy_coords[np.isin(heavy_seq, seed)]
    if len(seed_atoms) == 0:
        return np.full(n, np.nan)
    d = np.sqrt(((heavy_coords[:, None, :] - seed_atoms[None, :, :]) ** 2).sum(-1))
    per_atom_min = d.min(axis=1)
    min_dist = np.full(n, np.inf)
    np.minimum.at(min_dist, heavy_seq, per_atom_min)
    min_dist[np.isinf(min_dist)] = np.nan
    return min_dist


def build_candidates(t: str, cfg: dict, apo, seed: np.ndarray, pocket: np.ndarray):
    """Mirrors task0242.run()'s own candidate-construction loop (same
    primitives, same MIN_HOP field computed for compatibility/reporting)
    but returns the FULL pre-filter candidate list so a second criterion
    can be applied without re-running fpocket."""
    coords = apo.coords
    cut = float(cfg.get("enm_cutoff", 8.0))
    resn = np.asarray(apo.resnums)
    chids = np.asarray(apo.chain_ids)
    # TASK-0298: (chain, resnum) compound key, matching fpocket_candidates'
    # own now-corrected `p["resnums"]` shape -- same class of defect this
    # file's own `min_heavy_atom_dist_to_seed` was already fixed for above.
    idx_of = {(str(c), int(r)): i for i, (c, r) in enumerate(zip(chids, resn))}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        apo_ch = cfg.get("apo_chains") or cfg.get("chains")
        ag = prody.parsePDB(cfg["apo_pdb"], compressed=False).select(
            "protein and (" + " or ".join(f"chain {c}" for c in apo_ch) + ")"
        )
        pdb = tmp / f"{t.lower()}_apo.pdb"
        prody.writePDB(str(pdb), ag)
        pockets = t0242.fpocket_candidates(pdb, tmp)
    if isinstance(pockets, dict):
        return {"error": pockets["error"]}

    hops = -hop_from_seed(coords, seed, cutoff=cut)
    ctqw = time_averaged_ctqw_converged(
        build_H_new(coords, apo.bfactors, cutoff=cut), source=seed, coherent=False
    )
    truth = set((str(chids[i]), int(resn[i])) for i in np.where(pocket)[0])

    cands = []
    for p in pockets:
        ii = [idx_of[r] for r in p["resnums"] if r in idx_of]
        if not ii:
            continue
        cands.append({
            "id": p["id"], "n_res": len(ii), "res_idx": ii,
            "min_hop": float(np.min(hops[ii])),
            "fpocket_drug": p.get("druggability_score") or 0.0,
            "fpocket_score": p.get("score") or 0.0,
            "ctqw": float(np.mean(ctqw[ii])),
            "hop_cov": float(np.mean(hops[ii])),
            "overlap": len(set(p["resnums"]) & truth) / max(1, len(truth)),
        })
    return {"cands": cands}


def rank_under_filter(cands: list, keep_mask: np.ndarray):
    kept = [c for c, k in zip(cands, keep_mask) if k]
    if not kept:
        return {"error": "filter removed all candidates", "n_kept": 0}
    true_i = max(range(len(kept)), key=lambda i: kept[i]["overlap"])
    if kept[true_i]["overlap"] == 0.0:
        return {"error": "true pocket not among survivors", "n_kept": len(kept)}
    K = len(kept)
    rng = np.random.default_rng(7)
    ranks = {}
    for key, vals in (
        ("ctqw", [c["ctqw"] for c in kept]),
        ("fpocket_drug", [c["fpocket_drug"] for c in kept]),
        ("hop_covariate", [-c["hop_cov"] for c in kept]),
        ("random", list(rng.random(K))),
    ):
        order = np.argsort(-np.asarray(vals, float))
        ranks[key] = int(np.where(order == true_i)[0][0]) + 1
    return {"n_kept": K, "ranks": ranks}


def summarize_two_stage(rows: list, n_attempted: int, label: str):
    assert len(rows) == n_attempted, f"{label}: denominator mismatch {len(rows)} != {n_attempted}"
    print(f"\n=== Two-stage ranking under {label}, denominator=targets attempted ({n_attempted}) ===")
    ok = [r for r in rows if "error" not in r]
    print(f"  survivors: {len(ok)}/{n_attempted}")
    for key in ("ctqw", "fpocket_drug", "hop_covariate", "random"):
        rr_sum = sum(1.0 / r["ranks"][key] for r in ok)
        top1 = sum(1 for r in ok if r["ranks"][key] == 1)
        mean_rank = np.mean([r["ranks"][key] for r in ok]) if ok else float("nan")
        print(f"  {key:<15} MRR={rr_sum / n_attempted:.4f}  top-1={top1}/{n_attempted}  "
              f"(mean_rank among survivors={mean_rank:.2f})")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    new_cand = yaml.safe_load(FROZEN_CONFIG.read_text())["targets"]
    t0242.CAND = new_cand
    targets = list(new_cand.keys())

    per_target = {}
    skipped = {}
    print(f"=== Loading {len(targets)} frozen-set targets, computing heavy-atom min-dist ===")
    for t in targets:
        try:
            cfg, apo, seed, pocket = t0242.prep(t)
        except Exception as e:  # noqa: BLE001
            skipped[t] = f"prep failed: {type(e).__name__}: {e}"
            print(f"  {t}: SKIP ({skipped[t]})")
            continue
        if len(seed) == 0:
            skipped[t] = "empty active-site seed"
            print(f"  {t}: SKIP (empty active-site seed)")
            continue
        coords = apo.coords
        cut = float(cfg.get("enm_cutoff", 8.0))
        hop_true = -hop_from_seed(coords, seed, cutoff=cut)
        min_dist = min_heavy_atom_dist_to_seed(cfg, apo, seed)
        resn = np.asarray(apo.resnums)
        n_pocket = int(pocket.sum())
        true_min = float(np.nanmin(min_dist[pocket])) if n_pocket else float("nan")
        per_target[t] = {
            "cfg": cfg, "apo": apo, "seed": seed, "pocket": pocket,
            "resn": resn, "hop": hop_true, "min_dist": min_dist,
        }
        print(f"  {t:<24} n_res={len(resn):5d} n_pocket={n_pocket:3d} "
              f"true_pocket_min_dist={true_min:6.2f} A")

    n_attempted = len(targets)

    # --- 1+2: pooled hop -> Angstrom calibration table -------------------
    pooled_hop = np.concatenate([d["hop"] for d in per_target.values()])
    pooled_dist = np.concatenate([d["min_dist"] for d in per_target.values()])
    valid = ~np.isnan(pooled_dist)
    pooled_hop, pooled_dist = pooled_hop[valid], pooled_dist[valid]
    print("\n=== Hop -> Angstrom calibration (pooled, all residues, all targets) ===")
    calib_rows = []
    for k in range(1, K_MAX_SHELL + 1):
        sel = (pooled_hop == k) if k < K_MAX_SHELL else (pooled_hop >= K_MAX_SHELL)
        vals = pooled_dist[sel]
        if len(vals) == 0:
            continue
        med = float(np.median(vals))
        q1, q3 = (float(x) for x in np.percentile(vals, [25, 75]))
        mn = float(vals.min())
        label = f"{k}+" if k == K_MAX_SHELL else str(k)
        calib_rows.append({"hop": label, "n": int(len(vals)), "median_A": med,
                            "iqr_A": [q1, q3], "min_A": mn})
        print(f"  hop {label:<3} n={len(vals):6d}  median={med:6.2f} A  "
              f"IQR=[{q1:5.2f},{q3:5.2f}]  MIN={mn:5.2f} A")

    # --- 3: true-pocket separation vs pre-registered bars -----------------
    print("\n=== True-pocket minimum distance to active site, per target ===")
    meet = {b: 0 for b in SEPARATION_BARS_A}
    n_scoreable = 0
    per_target_true_min = {}
    for t, d in per_target.items():
        if not d["pocket"].any():
            continue
        m = float(np.nanmin(d["min_dist"][d["pocket"]]))
        per_target_true_min[t] = m
        n_scoreable += 1
        flags = "  ".join(f"{'PASS' if m >= b else 'fail'}{int(b)}" for b in SEPARATION_BARS_A)
        for b in SEPARATION_BARS_A:
            meet[b] += m >= b
        print(f"  {t:<24} min_dist={m:6.2f} A   {flags}")
    for b in SEPARATION_BARS_A:
        print(f"\n  meet >= {b:.0f} A: {meet[b]}/{n_scoreable} "
              f"({100 * meet[b] / max(1, n_scoreable):.1f}%)")

    # --- 4+5+6: candidate-level filters ------------------------------------
    print("\n=== Candidate-level: building fpocket candidates once per target ===")
    all_cands = {}
    rows_min_hop_only = []
    rows_by_bar = {b: [] for b in SEPARATION_BARS_A}
    n_cand_total = 0
    n_cand_contact_adjacent = 0
    for t in targets:
        if t not in per_target:
            rows_min_hop_only.append({"target": t, "error": skipped.get(t, "unresolved")})
            for b in SEPARATION_BARS_A:
                rows_by_bar[b].append({"target": t, "error": skipped.get(t, "unresolved")})
            continue
        d = per_target[t]
        try:
            res = build_candidates(t, d["cfg"], d["apo"], d["seed"], d["pocket"])
        except Exception as e:  # noqa: BLE001
            res = {"error": f"{type(e).__name__}: {e}"}
        if "error" in res:
            rows_min_hop_only.append({"target": t, "error": res["error"]})
            for b in SEPARATION_BARS_A:
                rows_by_bar[b].append({"target": t, "error": res["error"]})
            continue
        cands = res["cands"]
        all_cands[t] = cands
        min_dist = d["min_dist"]
        for c in cands:
            c["min_euclid"] = float(np.nanmin(min_dist[c["res_idx"]]))

        min_hop_mask = np.array([c["min_hop"] >= t0242.MIN_HOP for c in cands])
        n_survivors = int(min_hop_mask.sum())
        n_cand_total += n_survivors
        n_cand_contact_adjacent += sum(
            1 for c, k in zip(cands, min_hop_mask) if k and c["min_euclid"] < CONTACT_ADJACENT_A
        )
        r = rank_under_filter(cands, min_hop_mask)
        r["target"] = t
        rows_min_hop_only.append(r)

        for b in SEPARATION_BARS_A:
            mask = np.array([c["min_hop"] >= t0242.MIN_HOP and c["min_euclid"] >= b for c in cands])
            r2 = rank_under_filter(cands, mask)
            r2["target"] = t
            rows_by_bar[b].append(r2)
        print(f"  {t:<24} n_cands={len(cands):3d} MIN_HOP-survivors={n_survivors:3d}")

    print(f"\n=== Contact-adjacency: MIN_HOP>=2 survivors within {CONTACT_ADJACENT_A:.0f} A "
          f"of active site despite passing the filter ===")
    print(f"  {n_cand_contact_adjacent}/{n_cand_total} candidates "
          f"({100 * n_cand_contact_adjacent / max(1, n_cand_total):.1f}%)")

    summarize_two_stage(rows_min_hop_only, n_attempted, "MIN_HOP>=2 only (current criterion)")
    for b in SEPARATION_BARS_A:
        summarize_two_stage(rows_by_bar[b], n_attempted, f"MIN_HOP>=2 AND min_euclid>={b:.0f}A")

    # --- cost of adopting each supplementary bar --------------------------
    print("\n=== Cost of adopting a supplementary Euclidean floor ===")
    for b in SEPARATION_BARS_A:
        n_ok_before = sum(1 for r in rows_min_hop_only if "error" not in r)
        n_ok_after = sum(1 for r in rows_by_bar[b] if "error" not in r)
        cand_before = sum(r.get("n_kept", 0) for r in rows_min_hop_only if "error" not in r)
        cand_after = sum(r.get("n_kept", 0) for r in rows_by_bar[b] if "error" not in r)
        print(f"  >= {b:.0f} A: targets scoreable {n_ok_before} -> {n_ok_after} "
              f"({n_ok_before - n_ok_after} lost); total surviving candidates "
              f"{cand_before} -> {cand_after} ({cand_before - cand_after} removed)")

    out = {
        "calibration_table": calib_rows,
        "true_pocket_min_dist": per_target_true_min,
        "meet_bar": {str(b): meet[b] for b in SEPARATION_BARS_A},
        "n_scoreable_targets": n_scoreable,
        "contact_adjacent_fraction": {"n": n_cand_contact_adjacent, "of": n_cand_total},
        "skipped": skipped,
        "rows_min_hop_only": rows_min_hop_only,
        "rows_by_bar": {str(b): rows_by_bar[b] for b in SEPARATION_BARS_A},
    }
    (OUT / "calibration.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwritten: {OUT / 'calibration.json'}")


if __name__ == "__main__":
    raise SystemExit(main())
