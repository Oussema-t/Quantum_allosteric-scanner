#!/usr/bin/env python3
"""TASK-0331 -- re-run [[TASK-0320]]'s reverse-seeded arms and [[TASK-0325]]'s
gate ablation on the DISTAL subset only: this register's own scope defect.

[[TASK-0320]] and [[TASK-0325]] ran on the unfiltered ASBench cohort (105
structures). The collaborator's unified benchmark measured that most of that
cohort is not distal at all: only 23% of curated_allosteric sites and 7% of
drug_contact pockets have hop>=2 AND >12A separation from the active site
(`allosteric/README.md`, `origin/allosteric` branch). A propagation method
evaluated where there is nothing to propagate across is being tested
off-target -- this task reopens the question on the subset where it is not.

THE WALK IS FILTER-INVARIANT (per [[TASK-0320]]'s own symmetry identity),
so this is a POST-FILTER of the per-structure/per-candidate dumps
`task0320b_reverse_seeded_asbench.py` and [[TASK-0325]] already wrote, not a
re-run of fpocket or the CTQW propagator. Same pattern as [[TASK-0325]]
itself, ADD-only against [[TASK-0320]]'s dumps.

DISTAL DEFINITION AND SOURCE, vendored not re-derived: `origin/allosteric`
branch, `allosteric/datasets/pocket_distance.csv` (commit f257789), column
`is_distal` = (min_hop >= 2 AND min_euclid > 12.0 A), computed by the
collaborator on the SAME structures via their own hop/Angstrom pipeline.
Filtered here to source=='asbench' & truth_type=='curated_allosteric' (this
register's own ASBench truth is exclusively curated_allosteric -- the
drug_contact truth type is a different collaborator cohort this register has
never scored against, so the Constraint's "keep truth types separate" is
already satisfied by construction, not by an added filter). That gives 49
distinct ASBench PDBs; 45/49 have per-structure rows in the existing
[[TASK-0320]]b dump (the other 4 were already excluded there for the same
reasons -- fpocket failure, MAXN, <3 candidates -- as everything else in that
105/118 run; not re-derived here).

LIGAND-CONTAMINATION CAVEAT ([[TASK-0329]]): `task0320b` runs fpocket on the
DEPOSITED structure, ligand included, for every row in this subset too --
this task does not fix that; the true-pocket recall/rank numbers below
inherit whatever advantage ligand occupancy gives fpocket, on top of whatever
distality contributes. Both subset and full-cohort numbers share the defect,
so the COMPARISON between them is not confounded by it, but neither is a
clean measurement of distality's effect in isolation.

Run: ../.venv/bin/python3 scripts/task0331_distal_subset_rerun.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import rankdata, spearmanr, wilcoxon

_ROOT = Path(__file__).resolve().parents[1]
SRC = _ROOT / "results/tasks/0320b_reverse_seeded_asbench/reverse_seeded_asbench.json"
OUT = _ROOT / "results/tasks/0331_distal_subset_rerun"

# origin/allosteric @ f257789, allosteric/datasets/pocket_distance.csv,
# rows with source=='asbench', truth_type=='curated_allosteric', is_distal==True.
# 49 distinct PDBs (of 109 curated_allosteric ASBench rows, 44.95% distal --
# matches the filing's own "ASBench-led at 45% distal").
DISTAL_ASBENCH_PDBS = {
    "1A3W", "1EM6", "1FRP", "1GZ3", "1H78", "1M8P", "1NE7", "1NH8",
    "1PFK", "1QW7", "1T49", "1UXV", "1W25", "1W96", "1Z8D", "2BU8",
    "2BXA", "2IEG", "2J0X", "2NW8", "2PA3", "2Q8M", "2QPY", "2R1R",
    "2VD3", "2VGI", "2Y0P", "2YLO", "3CEH", "3DC2", "3E3N", "3ETE",
    "3ETG", "3FUD", "3H6O", "3HQP", "3IFA", "3LSX", "3LU6", "3O2M",
    "3PG9", "3R1R", "4E6C", "4G1N", "4GRS", "4HYW", "4LRL", "4MRA",
    "4PFK",
}
ARMS_0320B = ["ctqw_mean", "ctqw_sum", "prox_min", "fpocket_drug", "n_res"]
ARMS_0325 = ["ctqw", "resid", "prox", "drug", "nres"]


def rank_resid(x, z):
    """Rank-residualise x on z (TASK-0308/0310/0320b's own definition)."""
    rx, rz = rankdata(x), rankdata(z)
    rz2 = rz - rz.mean()
    d = float(rz2 @ rz2)
    if d < 1e-12:
        return rx.astype(float)
    b = float((rx - rx.mean()) @ rz2) / d
    return (rx - rx.mean()) - b * rz2


def by_protein(rows, key):
    g = defaultdict(list)
    for r in rows:
        g[r["protein"]].append(r[key])
    return np.array([np.median(v) for v in g.values()])


def cluster_wilcoxon(v):
    v = v[np.isfinite(v)]
    if len(v) < 3 or np.allclose(v, 0):
        return float("nan"), float("nan"), 0, 0
    return (float(np.median(v)), float(wilcoxon(v).pvalue),
            int(np.sum(v > 0)), int(len(v)))


def summarise_0320b(rows, label):
    n = len(rows)
    nprot = len({r["protein"] for r in rows})
    print(f"\n{'='*80}\n{label} -- n={n} structures / {nprot} proteins\n{'='*80}")
    print(f"{'arm':<16}{'top-1 hit':>11}{'med rank':>10}{'recall@top':>12}{'med rho':>10}")
    for k in ARMS_0320B:
        hit = np.mean([r[f"{k}__top_is_best"] for r in rows])
        rk = np.median([r[f"{k}__rank_of_best"] for r in rows])
        rc = np.mean([r[f"{k}__recall_top"] for r in rows])
        rho = np.median([r[f"{k}__rho"] for r in rows])
        print(f"{k:<16}{hit:>10.1%}{rk:>10.1f}{rc:>12.4f}{rho:>+10.3f}")

    print("\n--- POWER FIRST: proximity's own detectability, before interpreting anything ---")
    prox_v = by_protein(rows, "prox_min__rho")
    pm, pp, ppos, pn = cluster_wilcoxon(prox_v)
    print(f"  proximity (power check)   median={pm:+.4f}  n={pn:3d}  "
          f"positive {ppos}/{pn}  Wilcoxon p={pp:.4g}")
    powered = np.isfinite(pp) and pp < 0.05
    print(f"  POWERED to detect proximity on this subset: {'YES' if powered else 'NO'}")

    print("\n--- decisive test, clustered by protein ---")
    results = {}
    for nm, key in (("ctqw raw", "ctqw_mean__rho"),
                    ("ctqw | proximity", "ctqw_resid__rho"),
                    ("proximity (power check)", "prox_min__rho"),
                    ("fpocket druggability", "fpocket_drug__rho")):
        v = by_protein(rows, key)
        m, p, pos, nn = cluster_wilcoxon(v)
        results[nm] = dict(median=m, p=p, positive=pos, n=nn)
        print(f"  {nm:<26} median={m:+.4f}  n={nn:3d}  positive {pos}/{nn}  Wilcoxon p={p:.4g}")
    if not powered:
        print("  ** NOT ADEQUATELY POWERED: the CTQW numbers above cannot be "
              "interpreted as a negative or a positive on this subset. **")

    print(f"\n  median rho(ctqw, proximity) = "
          f"{np.median([r['rho_ctqw_prox'] for r in rows]):+.3f}")

    print("\n--- negative control: permuted-label null, 200 reps ---")
    rng = np.random.default_rng(0)
    obs = {"ctqw raw": float(np.median(by_protein(rows, "ctqw_mean__rho"))),
           "ctqw | proximity": float(np.median(by_protein(rows, "ctqw_resid__rho")))}
    keyed = {"ctqw raw": "_ctqw", "ctqw | proximity": "_resid"}
    null = {k: [] for k in obs}
    have_dumps = all(k in rows[0] for k in ("_recall", "_ctqw", "_resid"))
    control_result = {}
    if have_dumps:
        for _ in range(200):
            for k, src in keyed.items():
                g = defaultdict(list)
                for r in rows:
                    rc = np.asarray(r["_recall"], float)
                    rng.shuffle(rc)
                    g[r["protein"]].append(
                        float(spearmanr(np.asarray(r[src], float), rc).statistic))
                null[k].append(float(np.median([np.median(v) for v in g.values()])))
        for k in obs:
            nz = np.asarray(null[k])
            p_emp = (int((nz >= obs[k]).sum()) + 1) / (len(nz) + 1)
            centred = "YES" if abs(float(nz.mean())) < 0.02 else "NO"
            control_result[k] = dict(observed=obs[k], null_mean=float(nz.mean()),
                                      null_sd=float(nz.std(ddof=1)), p=p_emp, centred=centred)
            print(f"  {k:<18} observed={obs[k]:+.4f}  null={nz.mean():+.4f} +/- {nz.std(ddof=1):.4f}"
                  f"  reps>=obs {int((nz >= obs[k]).sum())}/200  p={p_emp:.4f}  "
                  f"null centres on zero: {centred}")
    else:
        print("  per-candidate dumps missing on this row set -- skipped")

    return dict(n=n, n_proteins=nprot, powered=bool(powered),
                decisive=results, negative_control=control_result)


def gate_ablation(rows, label):
    print(f"\n{'='*78}\nGATE ABLATION ({label}) -- n={len(rows)} structures / "
          f"{len({r['protein'] for r in rows})} proteins\n{'='*78}")
    out = {}
    for k in (3, 5, "half", "none"):
        hits = defaultdict(list)
        retained, sizes, rand = [], [], []
        rho_by_prot = {a: defaultdict(list) for a in ARMS_0325}
        for r in rows:
            rec = np.asarray(r["_recall"], float)
            sc = {"ctqw": np.asarray(r["_ctqw"], float),
                  "prox": np.asarray(r["_prox"], float),
                  "drug": np.asarray(r["_drug"], float),
                  "nres": np.asarray(r["_nres"], float)}
            sc["resid"] = rank_resid(sc["ctqw"], sc["prox"])
            best = int(np.argmax(rec))
            if rec[best] <= 0:
                continue
            if k == "none":
                S = np.arange(len(rec))
            else:
                n = len(sc["drug"]); keep = max(1, n // 2) if k == "half" else min(int(k), n)
                S = np.argsort(-sc["drug"])[:keep]
            kept = best in set(S.tolist())
            retained.append(kept); sizes.append(len(S))
            rand.append((1.0 / len(S)) if kept else 0.0)
            for a in ARMS_0325:
                s = sc[a][S]
                hits[a].append(bool(kept and S[int(np.argmax(s))] == best))
                if len(S) >= 4:
                    rr = spearmanr(s, rec[S]).statistic
                    if np.isfinite(rr):
                        rho_by_prot[a][r["protein"]].append(float(rr))
        n = len(retained)
        tag = "NO FILTER" if k == "none" else f"top-{k} by druggability"
        print(f"\n--- {tag} ---")
        if n == 0:
            print("  (no eligible rows)")
            continue
        print(f"  candidates kept      : median {np.median(sizes):.0f} of median "
              f"{np.median([len(r['_recall']) for r in rows]):.0f}")
        print(f"  true pocket retained : {100*np.mean(retained):.1f}% of {n} structures")
        print(f"  {'arm':<22}{'top-1 hit':>10}{'med rho':>10}{'pos':>8}{'cluster p':>12}")
        print(f"  {'random (same gate)':<22}{100*np.mean(rand):>9.1f}%{0.0:>+10.3f}{'--':>8}{'--':>12}")
        row_out = {"retained_pct": 100 * float(np.mean(retained)), "n": n, "arms": {}}
        for a in ARMS_0325:
            v = np.array([np.median(x) for x in rho_by_prot[a].values()], float)
            m, p, pos, nn = cluster_wilcoxon(v)
            print(f"  {a:<22}{100*np.mean(hits[a]):>9.1f}%{m:>+10.3f}{f'{pos}/{nn}':>8}{p:>12.4g}")
            row_out["arms"][a] = dict(top1=100 * float(np.mean(hits[a])), median_rho=m, p=p)
        out[str(k)] = row_out
    return out


def main() -> int:
    all_rows = json.load(open(SRC))["rows"]
    for r in all_rows:
        r["is_distal"] = r["pdb"].split("_")[0] in DISTAL_ASBENCH_PDBS
    distal_rows = [r for r in all_rows if r["is_distal"]]
    distal_pdbs_present = {r["pdb"].split("_")[0] for r in distal_rows}
    missing_pdbs = sorted(DISTAL_ASBENCH_PDBS - distal_pdbs_present)
    print(f"Full cohort: {len(all_rows)} structures. "
          f"Distal (curated_allosteric, ASBench, origin/allosteric is_distal): "
          f"{len(distal_rows)} rows / {len(distal_pdbs_present)} distinct PDBs present "
          f"of {len(DISTAL_ASBENCH_PDBS)} distal PDBs (some PDBs carry >1 annotated "
          f"allosteric site, same one-row-per-site convention as the full cohort). "
          f"{len(missing_pdbs)} PDBs absent from TASK-0320b's own run entirely "
          f"(not in KEEP, N>MAXN, or excluded there for the same reasons as the rest "
          f"of that 105/118 run, not re-derived here): {missing_pdbs}.")

    full = summarise_0320b(all_rows, "FULL COHORT (TASK-0320b, unfiltered -- for reference)")
    distal = summarise_0320b(distal_rows, "DISTAL SUBSET (this task)")

    full_gate = gate_ablation(all_rows, "full cohort, for reference")
    distal_gate = gate_ablation(distal_rows, "distal subset")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "distal_subset_rerun.json").write_text(json.dumps(dict(
        distal_pdbs=sorted(DISTAL_ASBENCH_PDBS),
        n_distal_present=len(distal_rows),
        full_cohort=full, distal_subset=distal,
        gate_ablation_full=full_gate, gate_ablation_distal=distal_gate,
        rows_with_distal_flag=[{"pdb": r["pdb"], "protein": r["protein"],
                                 "is_distal": r["is_distal"]} for r in all_rows],
    ), indent=1))
    print(f"\nwritten -> {OUT}/distal_subset_rerun.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
