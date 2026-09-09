"""TASK-0358 -- retest the finite-delay phase observable across a tau
SCAN (phase-alive through converged), not a single point.

[[TASK-0357]] was executed correctly but tested the wrong tau: `min_
adequate_t_max(kind="ground_state_relaxation")` is a CONVERGENCE window
(the time by which transients have died), so evaluating O(r) there --
as TASK-0357 did -- lands precisely where its own phase content is
smallest (TASK-0130 proves the converged limit is phase-free; TASK-0357's
own check 2 measured the decay directly). TASK-0357's own tolerance sweep
compounded this: tau depends on the LOG of `tol`, so a 100x sweep in
`tol` (1e-3..1e-1) is only a ~3x sweep in tau -- nowhere near "an order of
magnitude either side" in the variable that actually matters.

FIX: scan tau directly, on a pre-registered PER-PROTEIN RELATIVE grid --
see TASK-0358's own "Tau grid" section for why relative (not a shared
absolute tau) is the right design. `tau(protein, f) = f *
min_adequate_t_max(protein, tol=1e-2)`, `f` the new scanned axis,
`f in {0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100}` (11
points). `f=1` reproduces TASK-0357's own exact numbers (Planned
Validation).

Reuses TASK-0357's own validated cohort-building, observable, scoring and
cluster-test functions by direct import (that module's own top-level code
is two cheap local JSON reads, safe to import -- same precedent
`task0350`'s own docstring establishes for when import IS safe vs. when
to copy instead). No cohort/label change, no new benchmark, per this
task's own Constraint.

SIGNED is the primary arm here (it is the external claim); unsigned
`|O(r)|` reported alongside as the distinct observable TASK-0357 already
found real proximity content in, not as a substitute for the signed one.

Run: ../.venv/bin/python3 -u scripts/task0358_tau_scan.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, "scripts")

from task0357_finite_delay_phase_observable import (  # noqa: E402
    build_cohort, finite_delay_phase_observable, min_adequate_t_max,
    score_stats, cluster_sign_flip_test_generic, agg, TOL,
)

OUT = Path("results/tasks/0358_tau_scan")
CHECKPOINT_PATH = OUT / "checkpoint.jsonl"

F_GRID = [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]

# TASK-0357's own committed numbers at f=1 (tau=min_adequate_t_max(tol=1e-2)) --
# this script's own Planned Validation target.
TASK0357_SIGNED = dict(raw=0.5031, rho=-0.0157, resid=0.5018)
TASK0357_UNSIGNED = dict(raw=0.5797, rho=0.3466, resid=0.5287)


def main() -> int:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    print("building ASBench cohort (same as TASK-0357, reused via import)...")
    structures = build_cohort()
    print(f"{len(structures)} structures ({time.time()-t0:.0f}s)")

    for s in structures:
        s["w"], s["v"] = np.linalg.eigh(s["H"])
        s["tau_base"] = min_adequate_t_max(w=s["w"], kind="ground_state_relaxation", tol=TOL)
    protein_of = {s["pdb"]: s["protein"] for s in structures}
    n_inf = sum(1 for s in structures if not np.isfinite(s["tau_base"]))
    print(f"eigh + tau_base done ({time.time()-t0:.0f}s); {n_inf} structures have non-finite tau_base (excluded)")

    checkpoint_f = open(CHECKPOINT_PATH, "w")
    results_by_f = {}
    for fi, f in enumerate(F_GRID, 1):
        signed_rows, unsigned_rows = {}, {}
        for s in structures:
            if not np.isfinite(s["tau_base"]):
                continue
            tau = f * s["tau_base"]
            O = finite_delay_phase_observable(s["w"], s["v"], tau, s["seed"])
            O_elig = O[s["elig"]]
            r_s = score_stats(O_elig, s["y"], s["prox"][s["elig"]])
            r_u = score_stats(np.abs(O_elig), s["y"], s["prox"][s["elig"]])
            if r_s:
                signed_rows[s["pdb"]] = r_s
            if r_u:
                unsigned_rows[s["pdb"]] = r_u

        s_raw, s_rho, s_resid, s_p5 = agg(signed_rows)
        u_raw, u_rho, u_resid, u_p5 = agg(unsigned_rows)
        delta_s = {pdb: r["resid_auc"] - 0.5 for pdb, r in signed_rows.items()}
        delta_u = {pdb: r["resid_auc"] - 0.5 for pdb, r in unsigned_rows.items()}
        cl_s = cluster_sign_flip_test_generic(delta_s, protein_of)
        cl_u = cluster_sign_flip_test_generic(delta_u, protein_of)

        row = dict(
            f=f,
            median_tau=float(np.median([f * s["tau_base"] for s in structures if np.isfinite(s["tau_base"])])),
            signed=dict(raw=s_raw, rho=s_rho, resid=s_resid, p5=s_p5, n=len(signed_rows),
                        mean_delta=float(np.mean(list(delta_s.values()))), cluster_p=cl_s["p_value"],
                        n_clusters=cl_s["n_clusters"], exact=cl_s["exact"]),
            unsigned=dict(raw=u_raw, rho=u_rho, resid=u_resid, p5=u_p5, n=len(unsigned_rows),
                          mean_delta=float(np.mean(list(delta_u.values()))), cluster_p=cl_u["p_value"],
                          n_clusters=cl_u["n_clusters"], exact=cl_u["exact"]),
        )
        results_by_f[f] = row
        checkpoint_f.write(json.dumps(row) + "\n")
        checkpoint_f.flush()
        print(f"  [{fi}/{len(F_GRID)}] f={f:<8g} median_tau={row['median_tau']:9.2f}  "
              f"SIGNED raw={s_raw:.4f} rho={s_rho:+.4f} resid={s_resid:.4f} cluster_p={cl_s['p_value']:.4f}  |  "
              f"UNSIGNED raw={u_raw:.4f} rho={u_rho:+.4f} resid={u_resid:.4f} cluster_p={cl_u['p_value']:.4f}  "
              f"({time.time()-t0:.0f}s)")
    checkpoint_f.close()

    # ---------------------------------------------------- Planned Validation
    anchor = results_by_f[1.0]
    val_signed = dict(
        raw_diff=abs(anchor["signed"]["raw"] - TASK0357_SIGNED["raw"]),
        rho_diff=abs(anchor["signed"]["rho"] - TASK0357_SIGNED["rho"]),
        resid_diff=abs(anchor["signed"]["resid"] - TASK0357_SIGNED["resid"]),
    )
    val_unsigned = dict(
        raw_diff=abs(anchor["unsigned"]["raw"] - TASK0357_UNSIGNED["raw"]),
        rho_diff=abs(anchor["unsigned"]["rho"] - TASK0357_UNSIGNED["rho"]),
        resid_diff=abs(anchor["unsigned"]["resid"] - TASK0357_UNSIGNED["resid"]),
    )
    check = all(v < 5e-4 for v in val_signed.values()) and all(v < 5e-4 for v in val_unsigned.values())
    print(f"\n### Planned Validation: f=1.0 (tau=min_adequate_t_max(tol=1e-2)) must reproduce TASK-0357 exactly ###")
    print(f"  signed   diffs: {val_signed}")
    print(f"  unsigned diffs: {val_unsigned}")
    print(f"  CHECK {'PASSES' if check else 'FAILS'}.")

    print("\n### Tau-scan summary: SIGNED (primary, the external claim) ###")
    print(f"  {'f':>8} {'median_tau':>11} {'raw':>7} {'rho':>7} {'resid':>7} {'cluster_p':>10}")
    for f in F_GRID:
        r = results_by_f[f]["signed"]
        print(f"  {f:>8g} {results_by_f[f]['median_tau']:>11.2f} {r['raw']:>7.4f} {r['rho']:>+7.4f} "
              f"{r['resid']:>7.4f} {r['cluster_p']:>10.4f}")

    print("\n### Tau-scan summary: UNSIGNED (secondary, distinct observable) ###")
    print(f"  {'f':>8} {'median_tau':>11} {'raw':>7} {'rho':>7} {'resid':>7} {'cluster_p':>10}")
    for f in F_GRID:
        r = results_by_f[f]["unsigned"]
        print(f"  {f:>8g} {results_by_f[f]['median_tau']:>11.2f} {r['raw']:>7.4f} {r['rho']:>+7.4f} "
              f"{r['resid']:>7.4f} {r['cluster_p']:>10.4f}")

    n_signed_sig = sum(1 for f in F_GRID if results_by_f[f]["signed"]["cluster_p"] < 0.05)
    n_unsigned_sig = sum(1 for f in F_GRID if results_by_f[f]["unsigned"]["cluster_p"] < 0.05)
    print(f"\nSIGNED:   {n_signed_sig}/{len(F_GRID)} grid points at cluster_p<0.05 "
          f"({'broad band -- signal' if n_signed_sig >= 3 else 'isolated/none -- selection artifact or null'})")
    print(f"UNSIGNED: {n_unsigned_sig}/{len(F_GRID)} grid points at cluster_p<0.05 "
          f"({'broad band -- signal' if n_unsigned_sig >= 3 else 'isolated/none -- selection artifact or null'})")

    out = dict(
        f_grid=F_GRID, tol=TOL, n_structures=len(structures), n_non_finite_tau_base=n_inf,
        planned_validation=dict(pass_=check, signed_diffs=val_signed, unsigned_diffs=val_unsigned),
        results_by_f={str(f): r for f, r in results_by_f.items()},
        n_signed_significant=n_signed_sig, n_unsigned_significant=n_unsigned_sig,
    )
    (OUT / "tau_scan_result.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"\nWrote {OUT}/tau_scan_result.json ({time.time()-t0:.0f}s total)")
    return 0 if check else 1


if __name__ == "__main__":
    sys.exit(main())
