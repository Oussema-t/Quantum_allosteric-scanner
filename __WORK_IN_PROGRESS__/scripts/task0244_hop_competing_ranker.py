"""TASK-0244 -- does the two-stage operator (CTQW ranking fpocket candidates,
[[TASK-0242]]) do anything beyond proximity-to-seed?

TASK-0242's own table already reports hop as a covariate, and its finding 3
is that ctqw and a trivial "mean BFS hops from seed" ranker have IDENTICAL
mean rank (5.71, Wilcoxon p=0.297) on the n=7 untuned targets. A covariate
cannot settle that -- it has to be a competing ranker in the same table, and
three more controls are needed to tell "ctqw is a proximity detector" apart
from "ctqw does real work beyond proximity":

  1. hop_covariate promoted to a first-class ranker (TASK-0242's table
     already has it; this script just adds it to the head-to-head Wilcoxon
     comparison alongside ctqw, rather than reporting it only as a stat).
  2. Residual ranker: regress ctqw on hop_cov *within each target's own
     candidate list*, rank candidates by the residual (the part of ctqw not
     explained by proximity), and see whether the true pocket still ranks
     well. This is the two-stage analogue of TASK-0238's residual analysis.
  3. Seed-free operator control: re-score the SAME candidate list with ctqw
     run from a random seed set of matched size. If the true pocket still
     ranks well, proximity-to-the-real-seed is not what is driving the
     ranking; if it collapses to chance, proximity is confirmed as the
     mechanism.
  4. Hop-matched candidate null: restrict the ranking competition to
     candidates matched to the true pocket's own hop distance and size
     (within each target's own candidate list) -- the two-stage counterpart
     of this register's compact-patch null, removing "easy" candidates the
     operator could beat for reasons unrelated to genuine pocket detection.

Reuses task0242_two_stage_dryrun.run() (return_state=True, an additive
opt-in this task added to that script) for the expensive part (fpocket
candidate generation, the real-seed ctqw pass) -- no candidate list is
regenerated here, no fpocket subprocess is re-run.

n=7 (untuned, stage-1-surviving) throughout -- the same, already-small
sample TASK-0242 itself flagged as underpowered (TASK-0243 is the separate
task supplying a larger frozen set). Every result here is reported with
that caveat, not as a standalone finding -- built and validated now so
TASK-0243's future re-run has working apparatus to plug into, per this
task's own Acceptance ("folded into TASK-0243's frozen-set re-run, not
reported alone").
"""
from __future__ import annotations
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import numpy as np
from scipy import stats

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from task0242_two_stage_dryrun import MIN_HOP, UNTUNED, run  # noqa: E402

N_SEEDFREE_REPS = 20  # per target; averaged, not a single noisy draw
HOP_TOL = 1.0         # +/- hops, matched-null candidate eligibility
SIZE_TOL_FRAC = 0.5   # +/- fraction of true pocket's own n_res
SEEDFREE_SEED = 11
OUT = _ROOT / "results/tasks/0244_hop_competing_ranker"


def residual_rank(kept: list[dict], true_i: int):
    """Rank candidates by ctqw with this target's own hop_cov linearly
    regressed out. None if the fit is degenerate (< 3 candidates, or hop_cov
    constant across the candidate set -- nothing to partial out)."""
    hop = np.array([c["hop_cov"] for c in kept], float)
    ctqw = np.array([c["ctqw"] for c in kept], float)
    if len(kept) < 3 or np.std(hop) == 0:
        return None
    slope, intercept = np.polyfit(hop, ctqw, 1)
    resid = ctqw - (slope * hop + intercept)
    order = np.argsort(-resid)
    return int(np.where(order == true_i)[0][0]) + 1


def seedfree_ranks(state: dict, n_reps: int, rng: np.random.Generator):
    """Re-score the identical candidate list under n_reps random seeds of
    matched size (drawn from every residue except the real seed). Returns
    the list of per-rep ranks of the true pocket."""
    kept, true_i = state["kept"], state["true_i"]
    coords, bfactors, cut = state["coords"], state["bfactors"], state["cut"]
    n = len(state["resn"])
    seed_size = len(state["seed_idx"])
    excl = set(state["seed_idx"])
    pool = np.array([i for i in range(n) if i not in excl])
    H = build_H_new(coords, bfactors, cutoff=cut)  # seed-independent, built once
    ranks = []
    for _ in range(n_reps):
        rseed = rng.choice(pool, size=seed_size, replace=False)
        ctqw = time_averaged_ctqw_converged(H, source=rseed, coherent=False)
        vals = [float(np.mean(ctqw[c["res_idx"]])) for c in kept]
        order = np.argsort(-np.asarray(vals))
        ranks.append(int(np.where(order == true_i)[0][0]) + 1)
    return ranks


def hop_matched_null(kept: list[dict], true_i: int, hop_tol: float, size_tol_frac: float):
    """Restrict the ranking competition to candidates matched to the true
    pocket's own hop distance and size, within this target's own candidate
    list. None (INFEASIBLE, this register's established convention for an
    unconstructible null, TASK-0143) if no candidate matches."""
    true_c = kept[true_i]
    lo_n, hi_n = true_c["n_res"] * (1 - size_tol_frac), true_c["n_res"] * (1 + size_tol_frac)
    matched = [
        i for i, c in enumerate(kept)
        if i != true_i and abs(c["hop_cov"] - true_c["hop_cov"]) <= hop_tol and lo_n <= c["n_res"] <= hi_n
    ]
    if not matched:
        return None
    pool = [true_i] + matched
    vals = [kept[i]["ctqw"] for i in pool]
    order = np.argsort(-np.asarray(vals))
    rank = int(np.where(order == 0)[0][0]) + 1  # true_i is pool[0]
    return {"rank": rank, "pool_size": len(pool), "n_matched": len(matched)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEEDFREE_SEED)
    rows = []
    print(f"protocol: MIN_HOP={MIN_HOP}, n_seedfree_reps={N_SEEDFREE_REPS}, "
          f"hop_tol={HOP_TOL}, size_tol_frac={SIZE_TOL_FRAC}\n")

    for t in UNTUNED:
        try:
            r = run(t, tuned=False, return_state=True)
        except Exception as e:
            r = {"target": t, "error": f"{type(e).__name__}: {e}"}
        if "error" in r:
            print(f"{t:<18} SKIP: {r['error'][:70]}")
            rows.append({"target": t, "error": r["error"]})
            continue

        kept, true_i = r["kept"], r["true_i"]
        rank_ctqw = r["ranks"]["ctqw"]
        rank_hop = r["ranks"]["hop_covariate"]
        rank_resid = residual_rank(kept, true_i)
        sf_ranks = seedfree_ranks(r, N_SEEDFREE_REPS, rng)
        null = hop_matched_null(kept, true_i, HOP_TOL, SIZE_TOL_FRAC)

        row = {
            "target": t, "K": r["n_kept"],
            "rank_ctqw": rank_ctqw, "rank_hop_covariate": rank_hop,
            "rank_ctqw_residual": rank_resid,
            "seedfree_ranks": sf_ranks,
            "seedfree_mean_rank": float(np.mean(sf_ranks)),
            "hop_matched_null": null,
        }
        rows.append(row)
        sf_str = f"{row['seedfree_mean_rank']:.1f}"
        null_str = f"{null['rank']}/{null['pool_size']}" if null else "INFEASIBLE"
        print(f"{t:<18} K={r['n_kept']:>3} ctqw={rank_ctqw:>3} hop={rank_hop:>3} "
              f"resid={rank_resid} seedfree_mean={sf_str} matched_null={null_str}")

    ok = [r for r in rows if "error" not in r]
    n = len(ok)
    print(f"\n--- untuned targets only, n={n} (same set TASK-0242 scored) ---")

    def _stats(ranks, ks):
        rr = np.asarray(ranks, float)
        mrr = float(np.mean(1.0 / rr))
        top1 = int(np.sum(rr == 1))
        chance = float(np.mean([1.0 / k for k in ks]))
        return {"mean_rank": float(np.mean(rr)), "mrr": mrr, "top1": top1, "chance_mrr": chance}

    def _wilcoxon_vs_ctqw(subset, ranks_key):
        """Paired Wilcoxon on (rank_ctqw - ranks_key) over the same subset of
        targets an arm was actually computed on -- never mixes subsets."""
        diffs = [r["rank_ctqw"] - (r[ranks_key] if ranks_key != "seedfree_mean_rank" else r["seedfree_mean_rank"])
                 for r in subset]
        try:
            _, p = stats.wilcoxon(diffs)
        except ValueError:
            p = float("nan")  # all-zero differences (e.g. identical to ctqw everywhere)
        return p

    resid_ok = [r for r in ok if r["rank_ctqw_residual"] is not None]

    summary = {}
    for name, subset, key in (
        ("ctqw (real seed)", ok, "rank_ctqw"),
        ("hop_covariate", ok, "rank_hop_covariate"),
        ("ctqw_residual (hop partialled out)", resid_ok, "rank_ctqw_residual"),
        ("ctqw_seedfree (mean over reps)", ok, "seedfree_mean_rank"),
    ):
        if not subset:
            continue
        ranks = [r[key] for r in subset]
        s = _stats(ranks, [r["K"] for r in subset])
        s["n"] = len(subset)
        s["wilcoxon_vs_ctqw_p"] = None if name == "ctqw (real seed)" else _wilcoxon_vs_ctqw(subset, key)
        summary[name] = s
        print(f"  {name:<38} n={s['n']:>2} mean rank {s['mean_rank']:>5.2f}  MRR {s['mrr']:.3f}  "
              f"top-1 {s['top1']}/{s['n']}  wilcoxon-vs-ctqw p={s['wilcoxon_vs_ctqw_p']}")

    matched_feasible = [r for r in ok if r["hop_matched_null"] is not None]
    print(f"\n  hop-matched null: feasible on {len(matched_feasible)}/{n} targets "
          f"(hop_tol={HOP_TOL}, size_tol={SIZE_TOL_FRAC:.0%})")
    for r in matched_feasible:
        hn = r["hop_matched_null"]
        print(f"    {r['target']:<18} rank {hn['rank']}/{hn['pool_size']} "
              f"({hn['n_matched']} matched decoys)")
    if matched_feasible:
        top1_null = sum(1 for r in matched_feasible if r["hop_matched_null"]["rank"] == 1)
        print(f"  true pocket ranked #1 within its own hop/size-matched pool: "
              f"{top1_null}/{len(matched_feasible)}")

    print(f"\n  seed-free collapse check: real-seed ctqw MRR "
          f"{summary['ctqw (real seed)']['mrr']:.3f} vs seed-free ctqw MRR "
          f"{summary['ctqw_seedfree (mean over reps)']['mrr']:.3f}")

    (OUT / "results.json").write_text(json.dumps(
        {"summary": summary, "rows": rows}, indent=1, default=str))
    print(f"\nwritten: {OUT / 'results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
