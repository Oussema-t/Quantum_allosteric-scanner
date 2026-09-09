"""TASK-0357 -- replicate the finite-delay, phase-sensitive observable

    O(r) = 2 * Re<r| exp(-i H tau) |a>

(`a` = active site / seed, coherent equal-amplitude superposition over a
multi-residue seed -- the SAME convention `propagators._quantum_initial_
coeffs`/`_ctqw_from_eigh` already use for every other phase-carrying arm
in this register, not a new one invented here) under a PRINCIPLED clock
(`tau = min_adequate_t_max(kind="ground_state_relaxation")`, HYP-P6's own
alternative 2 -- no sweep, no per-fold tau) and a PRE-REGISTERED sign
(written into TASK-0357's own task file before this script existed; no
defensible physical argument survived at the operating tau scale, so
`|O(r)|` unsigned is primary, signed O(r) with the cohort's own observed
majority sign is secondary/exploratory only).

COHORT: TASK-0350's own ASBench cohort (108 structures / 76 protein
clusters), reused directly -- see TASK-0357's own "Cohort decision"
section for why (Planned Validation needs the SAME code path TASK-0350
used; the veto-pipeline 276-family comparison against the external claim
is a separate, out-of-scope reconciliation). Cohort-building, `ca()`
parser, `score_stats`, `cluster_sign_flip_test_generic` copied (not
imported) from `task0350_coherent_vs_decoherent.py`, matching that
script's own stated reason (avoid an unwanted import-time side effect
from pulling in a sibling task module) -- same convention, not a new one.

PLANNED VALIDATION, two independent checks, both must pass before the
finite-delay arm is trusted:
  1. Reproduce TASK-0308/0350's own committed converged decoherent-CTQW
     numbers (raw=0.5921, resid=0.5184) via this script's own cohort/H_new
     path -- proves the harness itself (not the new observable) is correct.
  2. TASK-0130 proves the converged/time-averaged limit of any coherent
     phase-carrying quantity built this way is phase-free -- so O(r),
     TIME-AVERAGED over a growing window, must converge to ~0. Checked
     directly on a handful of real structures (not assumed): average
     |O(r)| over an increasing tau_max window and confirm it shrinks
     toward the expected O(1/sqrt(T)) decay, not staying flat or growing
     -- a bug in the new formula would likely fail this even where the
     harness-reproduction check above passes.

SECONDARY ARM (the held +0.031, amplitudes vs probabilities): NOT run in
this script -- see TASK-0357's own Done section for why it is deferred,
not silently dropped.

Run: ../.venv/bin/python3 -u scripts/task0357_finite_delay_phase_observable.py
"""
from __future__ import annotations

import itertools
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import rankdata, spearmanr, wilcoxon
from sklearn.metrics import roc_auc_score

sys.stdout.reconfigure(line_buffering=True)

sys.path.insert(0, "src")
sys.path.insert(0, "..")

from backend.data_layer import fetch  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.baselines import hop_from_seed  # noqa: E402
from allostery.labels import terminal_mask  # noqa: E402
from allostery.propagators import (  # noqa: E402
    time_averaged_ctqw_converged, min_adequate_t_max, _quantum_initial_coeffs,
)

OUT = Path("results/tasks/0357_finite_delay_phase_observable")
CHECKPOINT_PATH = OUT / "checkpoint.jsonl"
ANN = json.load(open("results/tasks/0304_asbench_casbench/asbench_annotations.json"))
KEEP = {r["pdb"] for r in json.load(
    open("results/tasks/0305_asbench_detection/asbench_detection.json"))["rows"]}

CUTOFF = 8.0
ALPHA = 0.3
TOL = 1e-2  # min_adequate_t_max's own tolerance, per HYP-P6's alternative 2 as named in the task file

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


def residualise(y_ranks, x_ranks):
    A = np.column_stack([x_ranks, np.ones_like(x_ranks)])
    coef, *_ = np.linalg.lstsq(A, y_ranks, rcond=None)
    return y_ranks - A @ coef


def score_stats(score: np.ndarray, y: np.ndarray, prox: np.ndarray) -> dict | None:
    """Identical to task0310/task0350's own function -- raw AUC, rho vs
    proximity, rank-residualised AUC -- plus P@5 (top-5 eligible residues
    by `score`, fraction true), the residue-level convention this task's
    own "Cohort decision" section adopts for ASBench."""
    if not np.isfinite(score).all() or np.ptp(score) == 0:
        return None
    raw_auc = float(roc_auc_score(y, score))
    rho, _ = spearmanr(score, prox)
    r_score = rankdata(score)
    r_prox = rankdata(prox)
    resid = residualise(r_score, r_prox)
    resid_auc = 0.5 if np.ptp(resid) < 1e-9 else float(roc_auc_score(y, resid))
    top5 = np.argsort(-score)[:5]
    p5 = float(y[top5].sum()) / min(5, len(y))
    return dict(raw_auc=raw_auc, rho=float(rho), resid_auc=resid_auc, p5=p5)


def cluster_sign_flip_test_generic(values: dict, cluster_map: dict,
                                    n_mc: int = 100_000, seed: int = 0) -> dict:
    """Identical to task0310/task0350's own function."""
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


def finite_delay_phase_observable(w: np.ndarray, v: np.ndarray, tau: float, source) -> np.ndarray:
    """O(r) = 2*Re<r|exp(-iH tau)|a>, TASK-0157's own cross-term (2026-08-02),
    computed from H's already-known spectrum -- reuses `_quantum_initial_
    coeffs` (propagators.py's own coherent multi-residue seed-state
    convention), not a parallel re-derivation."""
    coeffs = _quantum_initial_coeffs(v, source)
    amplitudes = v @ (np.exp(-1j * w * tau) * coeffs)
    return 2.0 * amplitudes.real


def agg(rows):
    return (np.mean([r["raw_auc"] for r in rows.values()]),
            np.mean([r["rho"] for r in rows.values()]),
            np.mean([r["resid_auc"] for r in rows.values()]),
            np.mean([r["p5"] for r in rows.values()]))


def build_cohort():
    structures = []
    for rec in ANN:
        if rec["pdb"] not in KEEP:
            continue
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
            prox = hop_from_seed(xyz, np.asarray(seed), cutoff=CUTOFF)
        except Exception:
            continue
        structures.append(dict(pdb=rec["pdb"], protein=rec.get("protein", rec["pdb"]),
                                xyz=xyz, bf=bf, seed=np.asarray(seed),
                                elig=elig, y=y, H=H, prox=prox, N=n))
    return structures


def validation_time_average_vanishes(structures, n_check=5, windows=(5.0, 50.0, 500.0, 5000.0, 50000.0)):
    """Check 2: TIME-AVERAGE O(r,t) itself (signed) over a growing window,
    then take |.| -- must shrink toward 0 (TASK-0130's own phase-free-at-
    convergence proof, applied here to THIS observable specifically, not
    assumed to carry over). Averaging |O(r,t)| directly (an earlier,
    wrong version of this check) does NOT test the right thing -- |x| is
    non-negative regardless of oscillation, so its own time-average
    approaches the oscillation's RMS-ish magnitude, not 0, even when the
    phase genuinely cancels; confirmed empirically on a real structure
    before trusting this fixed version (mean|<O(r,t)>_signed| shrinks
    0.038->0.016->0.004->0.0009->0.0006 over T=5..50000 on 11BG, while
    mean<|O(r,t)|>_t stayed flat/grew -- exactly the artifact this
    docstring warns about)."""
    out = {}
    for s in structures[:n_check]:
        w, v = np.linalg.eigh(s["H"])
        means = {}
        for T in windows:
            times = np.linspace(1e-6, T, 400)
            acc = np.zeros(len(w))
            for t in times:
                acc += finite_delay_phase_observable(w, v, t, s["seed"])
            signed_mean = acc / len(times)
            means[T] = float(np.mean(np.abs(signed_mean)))
        out[s["pdb"]] = means
    return out


def main() -> int:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    print("building ASBench cohort (fetch + build_H_new + hop_from_seed)...")
    structures = build_cohort()
    print(f"{len(structures)}/{len(ANN)} structures usable (matches TASK-0308/0310/0350's own n=108 filter) "
          f"({time.time()-t0:.0f}s)")

    # ---------------------------------------------- Planned Validation 1
    print("\n### Planned Validation 1: reproduce TASK-0308/0350's committed converged decoherent-CTQW numbers ###")
    decoh_rows = {}
    for i, s in enumerate(structures):
        s["w"], s["v"] = np.linalg.eigh(s["H"])
        occ = np.nan_to_num(time_averaged_ctqw_converged(w=s["w"], v=s["v"], source=s["seed"], coherent=False))
        r = score_stats(occ[s["elig"]], s["y"], s["prox"][s["elig"]])
        if r:
            decoh_rows[s["pdb"]] = r
        if (i + 1) % 20 == 0:
            print(f"  [{i+1}/{len(structures)}] ({time.time()-t0:.0f}s)")
    d_raw, d_rho, d_resid, d_p5 = agg(decoh_rows)
    print(f"  decoherent (coherent=False) raw={d_raw:.4f} (committed: 0.5921) "
          f"rho={d_rho:.4f} (committed: 0.7347) resid={d_resid:.4f} (committed: 0.5184) p5={d_p5:.4f}")
    check1 = abs(d_raw - 0.5921) < 0.01 and abs(d_resid - 0.5184) < 0.02
    print(f"  CHECK 1 {'PASSES' if check1 else 'FAILS'}.")

    # ---------------------------------------------- Planned Validation 2
    print("\n### Planned Validation 2: time-averaged |O(r)| shrinks toward 0 as the window grows ###")
    ta = validation_time_average_vanishes(structures)
    check2 = True
    for pdb, means in ta.items():
        vals = list(means.values())
        # Overall shrinkage (last window << first window), not strict
        # step-to-step monotonicity -- at these tiny magnitudes, grid/MC
        # noise between adjacent windows is real and expected (checked
        # directly: 1A3W/1B86 both have a step-to-step non-monotonic wiggle
        # while still shrinking by >10x overall) and a strict per-step
        # check would flag a healthy result as failed.
        shrinking = vals[-1] < vals[0] / 10.0 or vals[-1] < 1e-3
        check2 = check2 and shrinking
        print(f"  {pdb}: mean|O(r)| at T={list(means.keys())} -> {[round(v, 5) for v in vals]} "
              f"{'OK (shrinking)' if shrinking else 'FAIL (not shrinking)'}")
    print(f"  CHECK 2 {'PASSES' if check2 else 'FAILS'}.")

    if not (check1 and check2):
        print("\nVALIDATION DID NOT FULLY PASS -- stopping, not trusting the finite-delay arm.")
        return 1

    # -------------------------------------------------------- main arm
    print(f"\n### Main arm: O(r) at tau = min_adequate_t_max(ground_state_relaxation, tol={TOL}) ###")
    o_rows = {}
    signed_rows = {}
    taus = []
    checkpoint_f = open(CHECKPOINT_PATH, "w")
    for i, s in enumerate(structures):
        tau = min_adequate_t_max(w=s["w"], kind="ground_state_relaxation", tol=TOL)
        if not np.isfinite(tau):
            continue
        taus.append(tau)
        O = finite_delay_phase_observable(s["w"], s["v"], tau, s["seed"])
        O_elig = O[s["elig"]]
        r_unsigned = score_stats(np.abs(O_elig), s["y"], s["prox"][s["elig"]])
        r_signed = score_stats(O_elig, s["y"], s["prox"][s["elig"]])
        if r_unsigned:
            o_rows[s["pdb"]] = r_unsigned
        if r_signed:
            signed_rows[s["pdb"]] = r_signed
        checkpoint_f.write(json.dumps(dict(pdb=s["pdb"], protein=s["protein"], tau=float(tau),
                                            unsigned=r_unsigned, signed=r_signed)) + "\n")
        checkpoint_f.flush()
        if (i + 1) % 20 == 0:
            print(f"  [{i+1}/{len(structures)}] tau={tau:.2f} ({time.time()-t0:.0f}s)")
    checkpoint_f.close()

    o_raw, o_rho, o_resid, o_p5 = agg(o_rows)
    s_raw, s_rho, s_resid, s_p5 = agg(signed_rows)
    print(f"\n  |O(r)| unsigned (PRIMARY): raw={o_raw:.4f} rho={o_rho:.4f} resid={o_resid:.4f} p5={o_p5:.4f}  (n={len(o_rows)})")
    print(f"  O(r) signed (secondary):   raw={s_raw:.4f} rho={s_rho:.4f} resid={s_resid:.4f} p5={s_p5:.4f}  (n={len(signed_rows)})")
    print(f"  tau range: min={min(taus):.2f} max={max(taus):.2f} median={float(np.median(taus)):.2f} (n={len(taus)})")

    # ------------------------------------------------------- decisive test
    print("\n### Decisive test: per-structure resid-AUC delta vs 0.5, cluster-robust ###")
    protein_of = {s["pdb"]: s["protein"] for s in structures}

    delta_unsigned = {pdb: r["resid_auc"] - 0.5 for pdb, r in o_rows.items()}
    dv_u = np.array(list(delta_unsigned.values()))
    w_u, wp_u = wilcoxon(dv_u) if not np.allclose(dv_u, 0) else (0.0, 1.0)
    cl_u = cluster_sign_flip_test_generic(delta_unsigned, protein_of)
    print(f"  UNSIGNED  n={len(dv_u)} mean_delta={dv_u.mean():+.5f} median_delta={np.median(dv_u):+.5f} "
          f"Wilcoxon p={wp_u:.4g} cluster-p={cl_u['p_value']:.4g} n_clusters={cl_u['n_clusters']}"
          f"{' (exact)' if cl_u['exact'] else ' (MC)'}")

    delta_signed = {pdb: r["resid_auc"] - 0.5 for pdb, r in signed_rows.items()}
    dv_s = np.array(list(delta_signed.values()))
    w_s, wp_s = wilcoxon(dv_s) if not np.allclose(dv_s, 0) else (0.0, 1.0)
    cl_s = cluster_sign_flip_test_generic(delta_signed, protein_of)
    print(f"  SIGNED    n={len(dv_s)} mean_delta={dv_s.mean():+.5f} median_delta={np.median(dv_s):+.5f} "
          f"Wilcoxon p={wp_s:.4g} cluster-p={cl_s['p_value']:.4g} n_clusters={cl_s['n_clusters']}"
          f"{' (exact)' if cl_s['exact'] else ' (MC)'}")

    out = dict(
        n_structures=len(structures),
        check1_reproduces_task0308_0350=dict(pass_=check1, raw=d_raw, rho=d_rho, resid=d_resid, p5=d_p5),
        check2_time_average_vanishes=ta,
        tau=dict(min=float(min(taus)), max=float(max(taus)), median=float(np.median(taus)), n=len(taus), tol=TOL),
        unsigned_primary=dict(raw=o_raw, rho=o_rho, resid=o_resid, p5=o_p5, n=len(o_rows),
                               decisive_test=dict(mean_delta=float(dv_u.mean()), median_delta=float(np.median(dv_u)),
                                                   wilcoxon_p=float(wp_u), cluster_test=cl_u)),
        signed_secondary=dict(raw=s_raw, rho=s_rho, resid=s_resid, p5=s_p5, n=len(signed_rows),
                               decisive_test=dict(mean_delta=float(dv_s.mean()), median_delta=float(np.median(dv_s)),
                                                   wilcoxon_p=float(wp_s), cluster_test=cl_s)),
        rows=dict(unsigned=o_rows, signed=signed_rows, decoherent_converged=decoh_rows),
    )
    (OUT / "finite_delay_phase_observable.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"\nWrote {OUT}/finite_delay_phase_observable.json ({time.time()-t0:.0f}s total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
