"""TASK-0256 -- classical-diffusion parity as a standing, named arm in the
two-stage apparatus, not an ad-hoc side check.

The collaborating thread has already reported `heat_kernel` matching `p_avg`
on their side; TASK-0210 tested the Markovian random walk (ref [8]) as this
register's own classical analogue. This task institutionalises the same
question for the two-stage protocol specifically: does CTQW rank candidates
any differently than classical diffusion *on the identical Hamiltonian*?

**Which classical propagator, and why**: `propagators.ground_state_
relaxation` (`exp(-Ht)`), on the SAME `H_new` the ctqw arm already scores --
not a separately-built graph Laplacian, per this task's own Scope. This is
classical diffusion **only when H is positive-semidefinite** (TASK-0095 /
REVIEW-2026-07-13 finding P1-B); `H_new`'s V_R/V_C/V_M potential terms
contribute negative diagonals, so it is expected to be indefinite on most or
all real targets. Per this task's own Scope ("do not label the output
classical diffusion where it is not"), PSD status is checked and reported
per target, and the arm is honestly relabelled "ground-state relaxation"
wherever H is not PSD -- it is still a real, well-defined comparison (does
CTQW's ranking differ from H's own relaxation-toward-ground-state limit),
just not the specific "quantum vs. classical diffusion" claim this task set
out to test on those targets.

**Pre-registered tolerance, stated before any number below was seen** (this
task's own Scope: "a numerical-tolerance statement: what difference would
count as the walk doing something other than diffusive graph filtering"):
Spearman rho >= 0.95 between the ctqw and classical per-candidate score
vectors, on the same kept candidate list, counts as "no meaningful
separation" -- an Implementer's-call threshold, not derived from any prior
measurement in this register, stated explicitly as a judgment call.

Reuses task0242_two_stage_dryrun.py's own `run(..., include_classical=True,
return_state=True)` (this task's own additive extension to that shared
script) -- no candidate generation, seed resolution, or propagator logic
re-derived. Runs on TASK-0243's frozen 22-target set, the same set
TASK-0253 already audited and partially fixed (its own empty-seed guard is
inherited automatically, not re-implemented).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _ROOT.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _REPO_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np  # noqa: E402
import prody  # noqa: E402
import yaml  # noqa: E402
from scipy import stats  # noqa: E402

prody.confProDy(verbosity="none")
# Same TASK-0039 altloc fix TASK-0243/TASK-0253's own wrapper scripts
# already apply locally to task0242's own script -- reused verbatim.
_orig_parsePDB = prody.parsePDB


def _parsePDB_all_altloc(*a, **kw):
    kw.setdefault("altloc", "all")
    return _orig_parsePDB(*a, **kw)


prody.parsePDB = _parsePDB_all_altloc

import task0242_two_stage_dryrun as t0242  # noqa: E402
from allostery.metrics import auc  # noqa: E402

OUT = _ROOT / "results/tasks/0256_classical_diffusion_parity"
CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
RHO_TOLERANCE = 0.95  # pre-registered, see module docstring


def per_residue_auc(state: dict) -> dict:
    """The per-residue-AUC design (TASK-0249's own convention, "both
    designs") alongside the two-stage candidate design above -- ctqw and
    classical scored whole-graph against the same pocket label, not
    restricted to fpocket's own candidate set."""
    pocket = state["pocket"].astype(int)
    return {
        "auc_ctqw": auc(state["ctqw_full"], pocket),
        "auc_classical": auc(state["classical_full"], pocket),
    }


def candidate_parity(state: dict) -> dict:
    """Spearman rho + rank-difference between the ctqw and classical
    per-candidate score vectors on the identical kept candidate list."""
    kept, true_i = state["kept"], state["true_i"]
    ctqw_vals = np.array([c["ctqw"] for c in kept])
    classical_vals = np.array([c["classical"] for c in kept])
    if len(kept) < 3 or np.std(ctqw_vals) == 0 or np.std(classical_vals) == 0:
        rho, p = float("nan"), float("nan")
    else:
        rho, p = stats.spearmanr(ctqw_vals, classical_vals)
    return {
        "spearman_rho": float(rho), "spearman_p": float(p),
        "no_meaningful_separation": bool(np.isfinite(rho) and rho >= RHO_TOLERANCE),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cand = yaml.safe_load(CONFIG.read_text())["targets"]
    t0242.CAND = cand
    targets = list(cand.keys())

    print(f"protocol: T_CLASSICAL={t0242.T_CLASSICAL}, rho_tolerance={RHO_TOLERANCE} "
          f"(pre-registered, see module docstring), n_targets={len(targets)}\n")

    rows = []
    for name in targets:
        t0 = time.monotonic()
        try:
            r = t0242.run(name, tuned=False, include_classical=True, return_state=True)
        except Exception as exc:  # noqa: BLE001
            r = {"target": name, "error": f"{type(exc).__name__}: {exc}"}
        elapsed = time.monotonic() - t0
        if "error" in r:
            print(f"{name:<24} SKIP ({elapsed:.1f}s): {r['error'][:70]}")
            rows.append({"target": name, "error": r["error"]})
            continue
        parity = candidate_parity(r)
        resid = per_residue_auc(r)
        row = {
            "target": name, "K": r["n_kept"], "is_psd": r["is_psd"], "min_eig": r["min_eig"],
            "rank_ctqw": r["ranks"]["ctqw"], "rank_classical": r["ranks"]["classical"],
            "rank_fpocket_drug": r["ranks"]["fpocket_drug"], "rank_hop_covariate": r["ranks"]["hop_covariate"],
            "rank_random": r["ranks"]["random"], **parity, **resid,
        }
        rows.append(row)
        psd_tag = "PSD" if r["is_psd"] else "indefinite"
        print(f"{name:<24} ({elapsed:.1f}s) K={r['n_kept']:<3} H={psd_tag:<10} "
              f"ctqw_rank={r['ranks']['ctqw']:<3} classical_rank={r['ranks']['classical']:<3} "
              f"rho={parity['spearman_rho']:.3f} auc_ctqw={resid['auc_ctqw']:.3f} auc_classical={resid['auc_classical']:.3f}")

    ok = [r for r in rows if "error" not in r]
    n = len(ok)
    n_psd = sum(1 for r in ok if r["is_psd"])
    print(f"\n=== {n}/{len(targets)} targets scoreable; H_new is PSD on {n_psd}/{n} of them ===\n")
    if n_psd < n:
        print(f"On the other {n - n_psd}, `ground_state_relaxation` is NOT classical "
              "diffusion (TASK-0095/P1-B) -- reported honestly as ground-state "
              "relaxation, not relabelled to look like a diffusion comparison.\n")

    def _stats(key):
        ranks = [r[key] for r in ok]
        ks = [r["K"] for r in ok]
        mrr = float(np.mean([1.0 / x for x in ranks]))
        chance = float(np.mean([1.0 / k for k in ks]))
        return np.mean(ranks), mrr, chance

    for key, label in (
        ("rank_ctqw", "ctqw"), ("rank_classical", "classical (ground-state relax. where indefinite)"),
        ("rank_fpocket_drug", "fpocket_drug"), ("rank_hop_covariate", "hop_covariate"), ("rank_random", "random"),
    ):
        mean_rank, mrr, chance = _stats(key)
        print(f"  {label:<45} mean rank {mean_rank:>5.2f}  MRR {mrr:.3f}  (chance MRR~{chance:.3f})")

    ctqw_ranks = np.array([r["rank_ctqw"] for r in ok])
    classical_ranks = np.array([r["rank_classical"] for r in ok])
    diff = ctqw_ranks - classical_ranks
    wins = int((diff < 0).sum()); losses = int((diff > 0).sum()); ties = int((diff == 0).sum())
    try:
        w = stats.wilcoxon(ctqw_ranks, classical_ranks)
        wp = float(w.pvalue)
    except Exception:
        wp = float("nan")
    print(f"\n  KEY COMPARISON (two-stage design) -- ctqw vs classical, same candidate list:")
    print(f"    ctqw ranks true pocket better: {wins}/{n}   ties: {ties}   worse: {losses}   wilcoxon p={wp:.4f}")

    auc_ctqw = np.array([r["auc_ctqw"] for r in ok])
    auc_classical = np.array([r["auc_classical"] for r in ok])
    print(f"\n  KEY COMPARISON (per-residue AUC design) -- ctqw vs classical, whole-graph:")
    print(f"    median AUC ctqw={np.median(auc_ctqw):.3f}  median AUC classical={np.median(auc_classical):.3f}")
    try:
        wp_auc = float(stats.wilcoxon(auc_ctqw, auc_classical).pvalue)
    except Exception:
        wp_auc = float("nan")
    auc_wins = int((auc_ctqw > auc_classical).sum())
    print(f"    ctqw beats classical AUC on {auc_wins}/{n} targets, wilcoxon p={wp_auc:.4f}")

    rhos = [r["spearman_rho"] for r in ok if np.isfinite(r["spearman_rho"])]
    n_separated = sum(1 for r in ok if not r["no_meaningful_separation"] and np.isfinite(r["spearman_rho"]))
    print(f"\n  Candidate-score parity (rho >= {RHO_TOLERANCE} = no meaningful separation): "
          f"median rho={np.median(rhos):.3f}, {n_separated}/{len(rhos)} targets separate beyond tolerance")
    if n_separated:
        print("  Targets separating beyond tolerance (per this task's own Constraint, "
              "reported with full prominence, not buried):")
        for r in ok:
            if np.isfinite(r["spearman_rho"]) and not r["no_meaningful_separation"]:
                print(f"    {r['target']:<24} rho={r['spearman_rho']:.3f} "
                      f"ctqw_rank={r['rank_ctqw']} classical_rank={r['rank_classical']} "
                      f"H={'PSD' if r['is_psd'] else 'indefinite'}")

    (OUT / "results.json").write_text(json.dumps(rows, indent=1, default=str))
    print(f"\nwritten: {OUT / 'results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
