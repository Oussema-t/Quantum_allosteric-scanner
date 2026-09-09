"""TASK-0350 -- ask the interference question properly: coherent vs
decoherent, matched operator, matched seed, matched cohort.

`time_averaged_ctqw_converged` is PROVABLY phase-free at convergence
(TASK-0130) -- `coherent=False` is this register's own established
default. Every existing "does interference help" test (chiral circulation
TASK-0140 FAIL, frequency-domain TASK-0146, HOM TASK-0157) changed the
OBSERVABLE as well as the coherence. This is the direct version that has
never been run: the SAME operator (`H_new`), SAME seed set, SAME cohort,
SAME scoring, one variable (`coherent`) flipped.

COHORT AND SCORING, reused verbatim, not re-derived -- copied (not
imported, per TASK-0310's own precedent, to avoid triggering another
module's own import-time side effects/network fetch) from
`task0310_family_residualised_on_proximity.py`: ASBench cohort (ANN +
TASK-0305's KEEP filter), `build_H_new(xyz, bf, cutoff=8.0)`,
`hop_from_seed` proximity, eligibility masking (seed + terminal 5%
excluded), `score_stats` (raw AUC / rho-vs-proximity / rank-residualised
AUC), and `cluster_sign_flip_test_generic` for cluster-robust
significance by protein. This task's own Constraint is "reuse the
existing cohort and labels; introduce no new benchmark" -- satisfied by
construction, not by re-deriving an equivalent pipeline.

THREE ARMS, one variable changing at a time between the decisive pair:
  1. classical diffusion: `ground_state_relaxation(L, t, source)` where
     `L = normalised_laplacian_alpha(xyz, cutoff, alpha)` -- this IS
     H_new's own graph term, before any potential is added
     (`hamiltonians.build_H_new`: `H_new = L_norm(alpha,r_c) + V_B+V_T+
     V_R+V_C+V_M`) -- so this is the exact same graph the two CTQW arms
     use, with zero potential, and it is genuinely positive-semidefinite
     (no `_warn_if_indefinite` trigger), so `ground_state_relaxation` on
     it really is classical diffusion, not a ground-state-density
     artifact (see that function's own docstring for why this
     distinction matters and why H_new itself would NOT qualify).
  2. decoherent CTQW: `time_averaged_ctqw_converged(H_new, seed,
     coherent=False)` -- reproduces TASK-0308's committed numbers
     (Planned Validation, checked before arm 3 is trusted).
  3. coherent CTQW: `time_averaged_ctqw_converged(H_new, seed,
     coherent=True)` -- the new arm; identical H, identical seed.

PRE-REGISTERED PREDICTION, stated before this script computed anything
from real data: the coherent-decoherent gap is small and
non-significant, consistent with TASK-0146's own finding that T=50000
and the converged limit agree to <=0.005 AUC on all 3 mandatory targets.

FINITE-T SENSITIVITY (this task's own Constraint -- must not be averaged
away): alongside the parameter-free converged limit, also score
`time_averaged_ctqw(H_new, t_max, seed, coherent=X)` at T=15.0 (this
project's established default, `ceiling_search_batched.py`'s own
T_MAX) and T=50000.0 (TASK-0146's own probe), for both coherent
settings, and report how many structures' residualised-AUC sign flips
between T=15 and the converged limit -- an instability, if present, is
reported as a property of the construction, not smoothed into a mean.

Run: ../.venv/bin/python3 scripts/task0350_coherent_vs_decoherent.py
"""
from __future__ import annotations

import itertools
import json
import os
import re
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
from scipy.stats import rankdata, spearmanr, wilcoxon
from sklearn.metrics import roc_auc_score

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
sys.path.insert(0, "..")

from backend.data_layer import fetch  # noqa: E402
from allostery.hamiltonians import build_H_new, normalised_laplacian_alpha  # noqa: E402
from allostery.baselines import hop_from_seed  # noqa: E402
from allostery.labels import terminal_mask  # noqa: E402
from allostery.propagators import (  # noqa: E402
    time_averaged_ctqw_converged, time_averaged_ctqw, ground_state_relaxation,
    _ctqw_from_eigh, _ctqw_mixture_from_eigh,
)

OUT = Path("results/tasks/0350_coherent_vs_decoherent_matched_twin")
ANN = json.load(open("results/tasks/0304_asbench_casbench/asbench_annotations.json"))
KEEP = {r["pdb"] for r in json.load(
    open("results/tasks/0305_asbench_detection/asbench_detection.json"))["rows"]}

CUTOFF = 8.0            # matches TASK-0310/TASK-0320b's own build_H_new/hop_from_seed convention
ALPHA = 0.3              # build_H_new's own default exponential-decay constant
T_DEFAULT = 15.0         # ceiling_search_batched.py's own T_MAX ("analysis.operator_sweep's own established t_max default")
T_LONG = 50000.0         # TASK-0146's own probe

# --- parsers, copied (not imported) from task0308_attribution_scaling.py /
# task0310, for the same reason task0310 itself gives: avoid an unwanted
# import-time network fetch from pulling in that whole module. ---
_A = re.compile(r'^([A-Z]{2,3})\s*(-?\d+)([A-Za-z]?)\s+(\w)$')


def pa(t):
    m = _A.match(t.strip())
    if m:
        return (m.group(4), int(m.group(2)))
    m = re.match(r'^([A-Z]{2,3})(-?\d+)\s+(\w)$', t.strip())
    return (m.group(3), int(m.group(2))) if m else None


def pact(t):
    m = re.match(r'^(\w)(-?\d+)$', t.strip())
    return (m.group(1), int(m.group(2))) if m else None


def ca(pdb):
    keys, xyz, bf, seen = [], [], [], set()
    for L in Path(fetch(pdb)).read_text().splitlines():
        if not L.startswith("ATOM") or L[12:16].strip() != "CA":
            continue
        if L[16] not in (" ", "A"):
            continue
        try:
            k = (L[21], int(L[22:26]))
            if k in seen:
                continue
            seen.add(k); keys.append(k)
            xyz.append((float(L[30:38]), float(L[38:46]), float(L[46:54])))
            bf.append(float(L[60:66]) if L[60:66].strip() else 0.0)
        except ValueError:
            continue
    return keys, np.asarray(xyz, float), np.asarray(bf, float)


def residualise(y_ranks: np.ndarray, x_ranks: np.ndarray) -> np.ndarray:
    A = np.column_stack([x_ranks, np.ones_like(x_ranks)])
    coef, *_ = np.linalg.lstsq(A, y_ranks, rcond=None)
    return y_ranks - A @ coef


def score_stats(score: np.ndarray, y: np.ndarray, prox: np.ndarray) -> dict | None:
    """Identical to task0310's own function -- raw AUC, rho vs proximity,
    rank-residualised AUC, over already-eligibility-masked arrays."""
    if not np.isfinite(score).all() or np.ptp(score) == 0:
        return None
    raw_auc = float(roc_auc_score(y, score))
    rho, _ = spearmanr(score, prox)
    r_score = rankdata(score)
    r_prox = rankdata(prox)
    resid = residualise(r_score, r_prox)
    resid_auc = 0.5 if np.ptp(resid) < 1e-9 else float(roc_auc_score(y, resid))
    return dict(raw_auc=raw_auc, rho=float(rho), resid_auc=resid_auc)


def cluster_sign_flip_test_generic(values: dict, cluster_map: dict,
                                    n_mc: int = 100_000, seed: int = 0) -> dict:
    """Identical to task0310's own function (itself generalised from
    TASK-0261) -- sum-of-cluster-sums, sign-flip null under H0."""
    keys = [k for k in values if k in cluster_map]
    clusters = sorted(set(cluster_map[k] for k in keys))
    by_cluster: dict = {c: [] for c in clusters}
    for k in keys:
        by_cluster[cluster_map[k]].append(values[k])
    cluster_sums = {c: sum(v) for c, v in by_cluster.items()}
    obs = sum(cluster_sums.values())
    n_clusters = len(clusters)
    rng = np.random.default_rng(seed)
    if n_clusters <= 20:
        null = np.array([sum(s * cluster_sums[c] for s, c in zip(signs, clusters))
                          for signs in itertools.product([1, -1], repeat=n_clusters)])
        exact = True
    else:
        signs = rng.choice([1, -1], size=(n_mc, n_clusters))
        sums_arr = np.array([cluster_sums[c] for c in clusters])
        null = signs @ sums_arr
        exact = False
    p = float(np.mean(np.abs(null) >= abs(obs) - 1e-9))
    return dict(n_rows=len(keys), n_clusters=n_clusters, statistic=float(obs),
                p_value=p, exact=exact, median=float(np.median([values[k] for k in keys])))


def time_averaged_from_eigh(w, v, t_max, source, coherent, n_steps=500):
    """`time_averaged_ctqw`'s own internal loop (`_ctqw_from_eigh`/
    `_ctqw_mixture_from_eigh` averaged over a `t_max` linspace), reusing an
    ALREADY-COMPUTED (w, v) instead of that public function's own internal
    `np.linalg.eigh(H)` -- real, not cosmetic, at this cohort's max N~3000:
    the first version of this script called `time_averaged_ctqw` directly
    for every (coherent, T) combination, redoing a full O(N^3)
    decomposition each time (4 redundant decompositions per structure on
    top of the one already computed for the converged-limit arms) and
    ran for 10+ hours without finishing -- killed and fixed here rather
    than left running. Numerically identical to `time_averaged_ctqw(H,
    t_max, source, n_steps, coherent)` for the same H -- same formula,
    same eigh, just not recomputed."""
    fn = _ctqw_from_eigh if coherent else _ctqw_mixture_from_eigh
    times = np.linspace(0.0, t_max, n_steps)
    acc = np.zeros(len(w))
    for t in times:
        acc += fn(w, v, t, source)
    return acc / n_steps


def agg(rows):
    raw = np.mean([r["raw_auc"] for r in rows.values()])
    rho = np.mean([r["rho"] for r in rows.values()])
    resid = np.mean([r["resid_auc"] for r in rows.values()])
    return raw, rho, resid


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    t_start = time.monotonic()

    max_structures = int(os.environ.get("MAX_STRUCTURES", "0")) or None  # smoke-test knob, unset in the real run

    _log("building cohort: fetch + build_H_new + hop_from_seed per structure "
         "(the O(N^3) eigh itself happens later, per arm)")
    structures = []
    n_scanned = 0
    for rec in ANN:
        if max_structures and len(structures) >= max_structures:
            break
        if rec["pdb"] not in KEEP:
            continue
        n_scanned += 1
        pdb = rec["pdb"].split("_")[0]
        try:
            keys, xyz, bf = ca(pdb)
        except Exception:
            continue
        n = len(keys)
        if n == 0 or n > 3000:
            continue
        pos = {k: j for j, k in enumerate(keys)}
        seed = sorted({pos[k] for k in (pact(t) for t in rec["active_residues"]) if k in pos})
        truth = sorted({pos[k] for k in (pa(t) for t in rec["allosteric_residues"]) if k in pos})
        if not seed or not truth:
            continue
        sm = np.zeros(n, bool); sm[seed] = True
        tm = np.zeros(n, bool); tm[truth] = True
        elig = (~terminal_mask(n, 0.05)) & ~sm
        y = tm[elig]
        if y.sum() == 0 or y.sum() == len(y):
            continue
        try:
            H = build_H_new(xyz, bf, cutoff=CUTOFF)
            L = normalised_laplacian_alpha(xyz, cutoff=CUTOFF, alpha=ALPHA)
            prox = hop_from_seed(xyz, np.asarray(seed), cutoff=CUTOFF)
        except Exception:
            continue
        structures.append(dict(pdb=rec["pdb"], protein=rec.get("protein", rec["pdb"]),
                                xyz=xyz, bf=bf, seed=np.asarray(seed),
                                truth=truth, elig=elig, y=y, H=H, L=L, prox=prox, N=n))
        if len(structures) % 15 == 0:
            _log(f"  cohort build: {n_scanned} scanned, {len(structures)} usable so far "
                 f"(latest {rec['pdb']}, N={n})")

    print(f"{len(structures)}/{len(ANN)} structures usable (matches TASK-0308/0310's own n=108 filter)\n")

    # ------------------------------------------------ Planned Validation
    print("### Planned Validation: coherent=False must reproduce TASK-0308's committed numbers ###")
    decoh_rows = {}
    for i, s in enumerate(structures):
        # eigh(H) shared across the coherent=True/False converged calls AND
        # the finite-T sensitivity check below (all accept/reuse a
        # precomputed (w, v) pair) -- avoids repeated O(N^3) decompositions
        # per structure, real at this cohort's max N~3000 (a first version
        # of this script redid eigh(H) 5 separate times per structure and
        # ran for 10+ hours without finishing on the full cohort).
        s["w"], s["v"] = np.linalg.eigh(s["H"])
        occ = np.nan_to_num(time_averaged_ctqw_converged(w=s["w"], v=s["v"], source=s["seed"], coherent=False))
        r = score_stats(occ[s["elig"]], s["y"], s["prox"][s["elig"]])
        if r:
            decoh_rows[s["pdb"]] = r
        if (i + 1) % 15 == 0:
            _log(f"  decoherent pass: {i+1}/{len(structures)}")
    d_raw, d_rho, d_resid = agg(decoh_rows)
    print(f"  decoherent (coherent=False) raw={d_raw:.4f} (committed: 0.5921) "
          f"rho={d_rho:.4f} (committed: 0.7347) resid={d_resid:.4f} (committed: 0.5184)")
    reproduces = abs(d_raw - 0.5921) < 0.01 and abs(d_resid - 0.5184) < 0.02
    print(f"  HARNESS {'REPRODUCES' if reproduces else 'DOES NOT REPRODUCE'} TASK-0308's own committed numbers.\n")
    if not reproduces:
        print("  Proceeding anyway, flagged prominently -- do not trust the coherent arm without checking why.\n")

    # ------------------------------------------------------- 3 arms
    print("### Three arms: classical diffusion (T=15) -> decoherent CTQW (converged) -> coherent CTQW (converged) ###")
    coh_rows = {}
    classical_rows = {}
    for i, s in enumerate(structures):
        occ = np.nan_to_num(time_averaged_ctqw_converged(w=s["w"], v=s["v"], source=s["seed"], coherent=True))
        r = score_stats(occ[s["elig"]], s["y"], s["prox"][s["elig"]])
        if r:
            coh_rows[s["pdb"]] = r
        cl = np.nan_to_num(ground_state_relaxation(s["L"], T_DEFAULT, source=s["seed"]))
        r2 = score_stats(cl[s["elig"]], s["y"], s["prox"][s["elig"]])
        if r2:
            classical_rows[s["pdb"]] = r2
        if (i + 1) % 15 == 0:
            _log(f"  coherent+classical pass: {i+1}/{len(structures)}")

    c_raw, c_rho, c_resid = agg(coh_rows)
    cl_raw, cl_rho, cl_resid = agg(classical_rows)
    print(f"  classical diffusion (T={T_DEFAULT:.0f}) raw={cl_raw:.4f} rho={cl_rho:.4f} resid={cl_resid:.4f}  (n={len(classical_rows)})")
    print(f"  decoherent CTQW (converged)   raw={d_raw:.4f} rho={d_rho:.4f} resid={d_resid:.4f}  (n={len(decoh_rows)})")
    print(f"  coherent CTQW (converged)     raw={c_raw:.4f} rho={c_rho:.4f} resid={c_resid:.4f}  (n={len(coh_rows)})")

    # ---------------------------------------- decisive test: coherent - decoherent
    print("\n### Decisive test: per-structure (coherent - decoherent) resid-AUC delta ###")
    common = sorted(set(coh_rows) & set(decoh_rows))
    delta = {pdb: coh_rows[pdb]["resid_auc"] - decoh_rows[pdb]["resid_auc"] for pdb in common}
    dv = np.array(list(delta.values()))
    w_stat, w_p = wilcoxon(dv) if not np.allclose(dv, 0) else (0.0, 1.0)
    print(f"  n={len(dv)}  mean delta={dv.mean():+.5f}  median delta={np.median(dv):+.5f}  "
          f"Wilcoxon p={w_p:.4g}")
    protein_of = {s["pdb"]: s["protein"] for s in structures}
    n_clusters_total = len(set(protein_of[p] for p in common))
    cl_test = cluster_sign_flip_test_generic(delta, protein_of)
    print(f"  cluster-robust by protein: n_clusters={cl_test['n_clusters']}/{n_clusters_total} total  "
          f"median={cl_test['median']:+.5f}  cluster-p={cl_test['p_value']:.4g}"
          f"{'  (exact)' if cl_test['exact'] else '  (Monte Carlo, 100000 draws)'}")
    small_and_ns = abs(np.median(dv)) < 0.005 and w_p > 0.05
    print(f"\n  PRE-REGISTERED PREDICTION ('gap is small and non-significant, <=0.005 AUC'): "
          f"{'HOLDS' if small_and_ns else 'DOES NOT HOLD'} -- reported whichever way it lands.")

    # ------------------------------------------ finite-T sensitivity (Constraint)
    print("\n### Finite-T sensitivity: T=15 / T=50000 / converged, both coherent settings ###")
    finite_t_rows = {True: {T_DEFAULT: {}, T_LONG: {}}, False: {T_DEFAULT: {}, T_LONG: {}}}
    for i, s in enumerate(structures):
        for coherent in (True, False):
            for T in (T_DEFAULT, T_LONG):
                occ = np.nan_to_num(time_averaged_from_eigh(s["w"], s["v"], T, s["seed"],
                                                             coherent, n_steps=500))
                r = score_stats(occ[s["elig"]], s["y"], s["prox"][s["elig"]])
                if r:
                    finite_t_rows[coherent][T][s["pdb"]] = r
        if (i + 1) % 15 == 0:
            _log(f"  finite-T sensitivity pass: {i+1}/{len(structures)}")

    converged_by_coh = {True: coh_rows, False: decoh_rows}
    flip_summary = {}
    for coherent in (True, False):
        label = "coherent" if coherent else "decoherent"
        for T in (T_DEFAULT, T_LONG):
            rows = finite_t_rows[coherent][T]
            if rows:
                raw_m, rho_m, resid_m = agg(rows)
                print(f"  {label:<11} T={T:<9.0f} raw={raw_m:.4f} rho={rho_m:.4f} resid={resid_m:.4f}  (n={len(rows)})")
        conv = converged_by_coh[coherent]
        common_pdbs = sorted(set(finite_t_rows[coherent][T_DEFAULT]) & set(conv))
        n_flip = sum(1 for pdb in common_pdbs
                     if (finite_t_rows[coherent][T_DEFAULT][pdb]["resid_auc"] - 0.5) *
                        (conv[pdb]["resid_auc"] - 0.5) < 0)
        flip_summary[label] = dict(n_common=len(common_pdbs), n_sign_flips_T15_vs_converged=n_flip)
        print(f"    {label}: {n_flip}/{len(common_pdbs)} structures flip resid-AUC sign between T={T_DEFAULT:.0f} and the converged limit")

    OUT_JSON = dict(
        n_structures=len(structures),
        harness_reproduces_task0308=reproduces,
        classical_diffusion=dict(T=T_DEFAULT, raw=cl_raw, rho=cl_rho, resid=cl_resid, n=len(classical_rows)),
        decoherent_ctqw_converged=dict(raw=d_raw, rho=d_rho, resid=d_resid, n=len(decoh_rows)),
        coherent_ctqw_converged=dict(raw=c_raw, rho=c_rho, resid=c_resid, n=len(coh_rows)),
        decisive_delta=dict(n=len(dv), mean=float(dv.mean()), median=float(np.median(dv)),
                             wilcoxon_p=float(w_p), cluster_test=cl_test,
                             pre_registered_prediction_holds=bool(small_and_ns)),
        finite_t_sensitivity=flip_summary,
        rows=dict(classical=classical_rows, decoherent=decoh_rows, coherent=coh_rows,
                  delta=delta),
    )
    (OUT / "coherent_vs_decoherent.json").write_text(json.dumps(OUT_JSON, indent=1, default=str))
    print(f"\nTotal wall time: {time.monotonic() - t_start:.0f}s. Wrote {OUT}/coherent_vs_decoherent.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
