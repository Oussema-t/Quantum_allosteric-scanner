"""TASK-0359 -- extend the cohort along the axis that carries power:
distinct PROTEINS, not more structures of the 76 we already have.

Every quantum-arm null in this register (TASK-0350, TASK-0357, TASK-0358) is
computed on the SAME 108 ASBench structures / 76 protein clusters (1.42
structures/cluster -- already near one-structure-per-protein). This script
adds up to 56 more distinct proteins, sourced from CASBench
(`casbench_annotations.json`, already fetched by TASK-0304, reused here for
CTQW scoring for the first time -- disclosed, not implied pre-tested), dedup'd
against the existing 76 by hand-adjudicated name/gene identity (see TASK-0359's
own "Pre-registration" section, written before this script ran), then:

  1. runs the SAME contamination audit TASK-0329 established (non-JUNK
     HETATM within 4.5A of the TRUTH/allosteric residues) on the extension,
     reported separately from the original's own already-known 40/40;
  2. re-runs TASK-0350's decisive decoherent-vs-coherent delta test and
     TASK-0358's f=1 anchor (signed + unsigned) on the UNION cohort, with
     the original-108 subset checked against both tasks' own committed
     numbers before any pooled number is trusted (Planned Validation);
  3. computes `protein_baseline_auc` -- the one genuinely new measurement,
     defined in the pre-registration -- per protein-cluster mean score
     replacing all within-structure position information, pooled AUC against
     the true label, cluster-permutation significance. Run on the original
     108 alone, the extension alone, and the union, separately.

Cohort-building, scoring and cluster-test machinery reused BY IMPORT from
task0357 (that module's own top-level code is two cheap local JSON reads --
same "safe to import" precedent task0358 already established), not
re-derived. The CASBench-specific extension builder below is new (CASBench's
own residue-list format needs its own parser choice: BOTH its
`catalytic_residues` and `allosteric_residues` fields use the "RESNAME NUM
CHAIN" token ASBench's `pa()` already parses -- CASBench has no equivalent of
ASBench's bare "CHAIN NUM" active-site token `pact()` expects, so `pa()` is
used for both roles here, not `pact()`).

Run: ../.venv/bin/python3 -u scripts/task0359_cohort_extension_by_protein.py
"""
from __future__ import annotations

import itertools
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import requests
from sklearn.metrics import roc_auc_score

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, "scripts")
sys.path.insert(0, "src")
sys.path.insert(0, "..")

import task0357_finite_delay_phase_observable as T0357  # noqa: E402
from task0357_finite_delay_phase_observable import (  # noqa: E402
    build_H_new, hop_from_seed, terminal_mask, pa, ca, CUTOFF,
    build_cohort, score_stats, cluster_sign_flip_test_generic, agg,
    finite_delay_phase_observable, min_adequate_t_max, time_averaged_ctqw_converged, TOL,
)
from backend.data_layer import PDB_CACHE  # noqa: E402

# task0357's own `fetch` is `backend.data_layer.fetch` -- bare `urllib.request.
# urlretrieve`, NO timeout. Already diagnosed as a real hang risk on this exact
# codebase (task0304_casbench_finding_f.py's own docstring: "confirmed the hard
# way ... hung indefinitely"). This run hit it directly on a large CASBench
# multimer (GroEL) after being killed once for an unexplained multi-minute
# stall -- same landmine, not a new one. Fixed here with the SAME bounded-
# timeout local override task0304_casbench_finding_f.py/task0329 already
# established, monkeypatched into the imported module so `ca()`/`build_cohort()`
# (which call the module-level name `fetch`, resolved at call time) get it too
# -- not editing `backend/` itself, a shared, live-deployed module, per that
# same precedent's own reasoning.
MAX_FETCH_MB = 30


def fetch_bounded(pdb, timeout=20):
    import os
    fp = os.path.join(PDB_CACHE, f"{pdb}.pdb")
    if os.path.exists(fp):
        return fp
    r = requests.get(f"https://files.rcsb.org/download/{pdb}.pdb", timeout=timeout)
    r.raise_for_status()
    if len(r.content) / 1e6 > MAX_FETCH_MB:
        raise ValueError(f"{pdb}: {len(r.content)/1e6:.0f} MB > {MAX_FETCH_MB} MB cap, skipped")
    with open(fp, "w") as fh:
        fh.write(r.text)
    return fp


T0357.fetch = fetch_bounded
fetch = fetch_bounded

OUT = Path("results/tasks/0359_cohort_extension_by_protein")
CHECKPOINT_PATH = OUT / "checkpoint.jsonl"
CASBENCH = json.load(open("results/tasks/0304_asbench_casbench/casbench_annotations.json"))

# ------------------------------------------------------------- Planned Validation targets
TASK0308_DECOHERENT = dict(raw=0.5921, resid=0.5184)
TASK0358_F1_SIGNED = dict(raw=0.5031, rho=-0.0157, resid=0.5018)
TASK0358_F1_UNSIGNED = dict(raw=0.5797, rho=0.3466, resid=0.5287)

# ------------------------------------------------------------- dedup (pre-registered, hand-adjudicated)
EXCLUDED_ALREADY_REPRESENTED = {
    "6-Phosphofructokinase Isozyme I", "Acetylglutamate Kinase", "Anthranilate synthase",
    "Bovine Seminal Ribonuclease", "Casein Kinase II", "Chorismate Mutase",
    "Copper-Containing Nitrite Reductase", "Cyclin-Dependent Kinase 2",
    "D-3-Phosphoglycerate Dehydrogenase", "Fructose-1,6-Bisphosphatase",
    "Glucosamine-6-Phosphate Synthase", "Glutamate Racemase", "Kinesin-like Protein KIF11",
    "L-Asparaginase", "Mitogen-Activated Protein Kinase 8", "Mitogen-activated protein kinase 14",
    "Myosin 2", "NAD-Dependent Malic Enzyme", "Parathion hydrolase",
    "Pyruvate Dehydrogenase Kinase", "Pyruvate Kinase", "Tyrosine-protein kinase ABL1",
    "Uracil Phosphoribosyltransferase", "Aspartate Transcarbamoylase",
    "Dihydrodipicolinate Synthase", "Phosphotyrosine Phosphatase 1B",
}

# ------------------------------------------------------------- contamination audit (TASK-0329's own convention, 4.5A, JUNK list)
JUNK = set("HOH SO4 PO4 GOL EDO PEG PGE MPD ACT CL NA K MG CA ZN MN FE NI CD CU TRS "
           "EPE IMD DMS FMT ACY BME NO3 CIT TLA MES BTB IOD BR CO SR CS NH4 AZI 1PE "
           "P6G PE4 PGO BOG LDA OCT SIN MLI SCN F UNX UNL".split())
AA3 = {"ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
       "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL", "MSE"}
MAX_FILE_MB = 30  # task0304_casbench_finding_f.py's own guard against the 4P3R-style
                   # SIGKILL this exact machine has shown on huge deposited files


def ligand_contacts_truth_site(pdb: str, truth_keys: set, cutoff: float = 4.5):
    """True if any non-JUNK HETATM sits within `cutoff` of ANY truth-site
    residue's heavy atoms, on the deposited (as-is) structure -- identical
    definition to TASK-0329's own `ligand_contact_resnums`, restricted here
    to just the truth/allosteric residue set (TASK-0359's own phrase: "a
    ligand at the scored site")."""
    prot_atoms, lig_xyz = {}, []
    try:
        fp = fetch(pdb)
        if Path(fp).stat().st_size / 1e6 > MAX_FILE_MB:
            return None
    except Exception:
        return None
    for L in Path(fp).read_text().splitlines():
        if not (L.startswith("ATOM") or L.startswith("HETATM")):
            continue
        if L[16] not in (" ", "A"):
            continue
        resn3 = L[17:20].strip()
        try:
            key = (L[21], int(L[22:26]))
            x, y, z = float(L[30:38]), float(L[38:46]), float(L[46:54])
        except ValueError:
            continue
        el = L[76:78].strip().upper()
        aname = L[12:16].strip()
        is_h = el == "H" or (not el and aname.startswith("H"))
        if is_h:
            continue
        is_protein_atom = L.startswith("ATOM") or resn3 in AA3
        if is_protein_atom:
            if key in truth_keys:
                prot_atoms.setdefault(key, []).append((x, y, z))
        elif resn3 not in JUNK:
            lig_xyz.append((x, y, z))
    if not prot_atoms or not lig_xyz:
        return False
    lig = np.asarray(lig_xyz, float)
    for atoms in prot_atoms.values():
        a = np.asarray(atoms, float)
        d = np.sqrt(((a[:, None, :] - lig[None, :, :]) ** 2).sum(-1))
        if (d < cutoff).any():
            return True
    return False


# ------------------------------------------------------------- extension cohort builder (CASBench)
def build_extension_cohort(log):
    by_protein = {}
    for r in CASBENCH["records"]:
        if r["n_allo"] > 0 and r["n_cat"] > 0:
            by_protein.setdefault(r["protein"], []).append(r)
    candidates = sorted(p for p in by_protein if p not in EXCLUDED_ALREADY_REPRESENTED)
    log(f"{len(by_protein)} CASBench proteins with both site types; "
        f"{len(EXCLUDED_ALREADY_REPRESENTED)} excluded as already-represented; "
        f"{len(candidates)} candidates")

    structures, unresolved, t0 = [], [], time.time()
    for i, protein in enumerate(candidates, 1):
        recs = sorted(by_protein[protein], key=lambda r: r["pdb"])
        found = None
        for rec in recs:
            pdb = rec["pdb"]
            try:
                keys, xyz, bf = ca(pdb)
            except Exception:
                continue
            n = len(keys)
            if n == 0 or n > 3000:
                continue
            pos = {k: j for j, k in enumerate(keys)}
            seed = sorted({pos[k] for k in (pa(t) for t in rec["catalytic_residues"]) if k in pos})
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
            found = dict(pdb=pdb, protein=protein, xyz=xyz, bf=bf, seed=np.asarray(seed),
                         truth_keys={keys[j] for j in truth}, elig=elig, y=y, H=H, prox=prox, N=n,
                         n_pdbs_tried=recs.index(rec) + 1)
            break
        if found:
            structures.append(found)
        else:
            unresolved.append((protein, len(recs)))
        elapsed = time.time() - t0
        eta = elapsed / i * (len(candidates) - i)
        status = f"OK pdb={found['pdb']} N={found['N']} tried={found['n_pdbs_tried']}/{len(recs)}" if found \
            else f"UNRESOLVED (0/{len(recs)} usable)"
        log(f"  [{i}/{len(candidates)}] {protein:<45} {status:<40} elapsed={elapsed:.0f}s eta={eta:.0f}s")
    return structures, unresolved, candidates


def protein_baseline_auc(structures, protein_of, score_key="decoh_score", n_perm=20000, seed=0):
    """The pre-registered separation statistic: replace every eligible
    residue's score with its OWN PROTEIN CLUSTER's mean eligible score
    (pure protein-identity signal, zero within-structure position
    information), pool across the cohort, compute AUC against the true
    label. Permutation null: shuffle which cluster's baseline pairs with
    which cluster's (fixed) label array."""
    by_cluster: dict = {}
    for s in structures:
        c = protein_of[s["pdb"]]
        by_cluster.setdefault(c, []).append(s)
    clusters = sorted(by_cluster)
    y_by_c, base_by_c = {}, {}
    for c in clusters:
        ys = np.concatenate([s[score_key + "_y"] for s in by_cluster[c]])
        scores = np.concatenate([s[score_key] for s in by_cluster[c]])
        y_by_c[c] = ys
        base_by_c[c] = float(np.mean(scores))
    y_all = np.concatenate([y_by_c[c] for c in clusters])
    if y_all.sum() == 0 or y_all.sum() == len(y_all):
        return None

    def pooled_auc(order):
        base_all = np.concatenate([np.full(len(y_by_c[c]), base_by_c[order[i]])
                                    for i, c in enumerate(clusters)])
        return float(roc_auc_score(y_all, base_all))

    obs = pooled_auc(clusters)
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm)
    idx = np.arange(len(clusters))
    for k in range(n_perm):
        perm = rng.permutation(idx)
        null[k] = pooled_auc([clusters[j] for j in perm])
    p = float(np.mean(np.abs(null - 0.5) >= abs(obs - 0.5) - 1e-9))
    return dict(n_clusters=len(clusters), n_residues=len(y_all), auc=obs,
                null_mean=float(null.mean()), null_std=float(null.std()), p_value=p)


def main() -> int:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    log_f = open(OUT / "run_log.txt", "a")

    def log(msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        log_f.write(line + "\n"); log_f.flush()

    log("building original 108-structure ASBench cohort (reused via import, unchanged)...")
    original = build_cohort()
    log(f"{len(original)} original structures ({time.time()-t0:.0f}s)")

    log("building CASBench extension cohort...")
    extension, unresolved, candidates = build_extension_cohort(log)
    log(f"extension: {len(extension)}/{len(candidates)} candidate proteins resolved to a usable structure "
        f"({len(unresolved)} unresolved)")

    ckpt = open(CHECKPOINT_PATH, "w")
    ckpt.write(json.dumps(dict(kind="resolution_summary", n_candidates=len(candidates),
                                n_resolved=len(extension), unresolved=unresolved)) + "\n")
    ckpt.flush()

    # ------------------------------------------------------------- contamination audit
    log("\n### contamination audit: non-JUNK HETATM within 4.5A of the TRUTH site ###")
    audit = {}
    for s in extension:
        hit = ligand_contacts_truth_site(s["pdb"], s["truth_keys"])
        if hit is None:
            continue
        audit.setdefault("extension", []).append(hit)
    n_ext_checked = len(audit.get("extension", []))
    n_ext_contam = sum(audit.get("extension", []))
    if n_ext_checked:
        log(f"  extension: {n_ext_contam}/{n_ext_checked} carry a ligand at the truth site "
            f"({n_ext_contam/n_ext_checked:.1%})")
    else:
        log("  extension: audit skipped (nothing resolved)")

    # original-108 audit needs the truth (chain, resnum) keys, which
    # task0357's own build_cohort doesn't carry -- recover them the same way
    # via ASBench's own ANN/KEEP, reusing task0357's own parsers.
    from task0357_finite_delay_phase_observable import ANN as ASB_ANN, KEEP as ASB_KEEP
    n_orig_contam, n_orig_checked = 0, 0
    for rec in ASB_ANN:
        if rec["pdb"] not in ASB_KEEP:
            continue
        pdb = rec["pdb"].split("_")[0]
        try:
            keys, xyz, bf = ca(pdb)
        except Exception:
            continue
        pos = {k: j for j, k in enumerate(keys)}
        truth_idx = sorted({pos[k] for k in (pa(t) for t in rec["allosteric_residues"]) if k in pos})
        if not truth_idx:
            continue
        truth_keys = {keys[j] for j in truth_idx}
        hit = ligand_contacts_truth_site(pdb, truth_keys)
        if hit is None:
            continue
        n_orig_checked += 1
        n_orig_contam += int(hit)
    log(f"  original-108 (recomputed here): {n_orig_contam}/{n_orig_checked} carry a ligand at the truth site "
        f"({n_orig_contam/n_orig_checked:.1%})  -- cf. TASK-0329's own reported 40/40")
    contamination = dict(original_recomputed=dict(n=n_orig_checked, n_contam=n_orig_contam),
                          extension=dict(n=n_ext_checked, n_contam=n_ext_contam))

    # ------------------------------------------------------------- eigh, once per structure, reused across both re-run arms
    log("\n### eigendecomposition: once per structure, reused for both re-run arms ###")
    union = original + extension
    for i, s in enumerate(union):
        s["w"], s["v"] = np.linalg.eigh(s["H"])
        if (i + 1) % 20 == 0:
            log(f"  eigh: {i+1}/{len(union)} ({time.time()-t0:.0f}s)")
    protein_of = {s["pdb"]: s["protein"] for s in union}

    # ------------------------------------------------------------- Arm A: TASK-0350's decisive decoherent-vs-coherent delta
    log("\n### Arm A: TASK-0350's decisive test (decoherent vs coherent, converged), union cohort ###")
    decoh_rows, coh_rows = {}, {}
    for i, s in enumerate(union):
        occ_d = np.nan_to_num(time_averaged_ctqw_converged(w=s["w"], v=s["v"], source=s["seed"], coherent=False))
        occ_c = np.nan_to_num(time_averaged_ctqw_converged(w=s["w"], v=s["v"], source=s["seed"], coherent=True))
        s["decoh_score"] = occ_d[s["elig"]]
        s["decoh_score_y"] = s["y"]
        rd = score_stats(occ_d[s["elig"]], s["y"], s["prox"][s["elig"]])
        rc = score_stats(occ_c[s["elig"]], s["y"], s["prox"][s["elig"]])
        if rd:
            decoh_rows[s["pdb"]] = rd
        if rc:
            coh_rows[s["pdb"]] = rc
        if (i + 1) % 20 == 0:
            log(f"  arm A: {i+1}/{len(union)} ({time.time()-t0:.0f}s)")

    d_raw, d_rho, d_resid, _ = agg(decoh_rows)
    c_raw, c_rho, c_resid, _ = agg(coh_rows)
    orig_pdbs = {s["pdb"] for s in original}
    decoh_orig = {k: v for k, v in decoh_rows.items() if k in orig_pdbs}
    do_raw, do_rho, do_resid, _ = agg(decoh_orig)
    val_a = dict(raw_diff=abs(do_raw - TASK0308_DECOHERENT["raw"]), resid_diff=abs(do_resid - TASK0308_DECOHERENT["resid"]))
    check_a = val_a["raw_diff"] < 0.005 and val_a["resid_diff"] < 0.005
    log(f"  Planned Validation (original-108 subset of union vs TASK-0308/0350 committed): "
        f"raw={do_raw:.4f} (committed 0.5921) resid={do_resid:.4f} (committed 0.5184)  "
        f"{'PASSES' if check_a else 'FAILS'}")

    common = sorted(set(coh_rows) & set(decoh_rows))
    delta = {pdb: coh_rows[pdb]["resid_auc"] - decoh_rows[pdb]["resid_auc"] for pdb in common}
    cl_a = cluster_sign_flip_test_generic(delta, protein_of)
    log(f"  UNION (n={len(union)}, {cl_a['n_clusters']} clusters): decoherent raw={d_raw:.4f} resid={d_resid:.4f}  "
        f"coherent raw={c_raw:.4f} resid={c_resid:.4f}  delta median={cl_a['median']:+.5f} cluster-p={cl_a['p_value']:.4g}")

    # ------------------------------------------------------------- Arm B: TASK-0358's f=1 anchor
    log("\n### Arm B: TASK-0358's f=1 anchor (finite-delay observable), union cohort ###")
    signed_rows, unsigned_rows = {}, {}
    for i, s in enumerate(union):
        tau = min_adequate_t_max(w=s["w"], kind="ground_state_relaxation", tol=TOL)
        if not np.isfinite(tau):
            continue
        Oe = finite_delay_phase_observable(s["w"], s["v"], tau, s["seed"])[s["elig"]]
        rs = score_stats(Oe, s["y"], s["prox"][s["elig"]])
        ru = score_stats(np.abs(Oe), s["y"], s["prox"][s["elig"]])
        if rs:
            signed_rows[s["pdb"]] = rs
        if ru:
            unsigned_rows[s["pdb"]] = ru
        if (i + 1) % 20 == 0:
            log(f"  arm B: {i+1}/{len(union)} ({time.time()-t0:.0f}s)")

    signed_orig = {k: v for k, v in signed_rows.items() if k in orig_pdbs}
    unsigned_orig = {k: v for k, v in unsigned_rows.items() if k in orig_pdbs}
    so_raw, so_rho, so_resid, _ = agg(signed_orig)
    uo_raw, uo_rho, uo_resid, _ = agg(unsigned_orig)
    val_b_signed = dict(raw_diff=abs(so_raw - TASK0358_F1_SIGNED["raw"]), rho_diff=abs(so_rho - TASK0358_F1_SIGNED["rho"]),
                         resid_diff=abs(so_resid - TASK0358_F1_SIGNED["resid"]))
    val_b_unsigned = dict(raw_diff=abs(uo_raw - TASK0358_F1_UNSIGNED["raw"]), rho_diff=abs(uo_rho - TASK0358_F1_UNSIGNED["rho"]),
                           resid_diff=abs(uo_resid - TASK0358_F1_UNSIGNED["resid"]))
    check_b = all(v < 5e-4 for v in val_b_signed.values()) and all(v < 5e-4 for v in val_b_unsigned.values())
    log(f"  Planned Validation (original-108 subset vs TASK-0358 f=1 committed): "
        f"signed diffs={val_b_signed}  unsigned diffs={val_b_unsigned}  {'PASSES' if check_b else 'FAILS'}")

    s_raw, s_rho, s_resid, _ = agg(signed_rows)
    u_raw, u_rho, u_resid, _ = agg(unsigned_rows)
    delta_s = {pdb: r["resid_auc"] - 0.5 for pdb, r in signed_rows.items()}
    delta_u = {pdb: r["resid_auc"] - 0.5 for pdb, r in unsigned_rows.items()}
    cl_s = cluster_sign_flip_test_generic(delta_s, protein_of)
    cl_u = cluster_sign_flip_test_generic(delta_u, protein_of)
    log(f"  UNION SIGNED:   raw={s_raw:.4f} rho={s_rho:+.4f} resid={s_resid:.4f} cluster-p={cl_s['p_value']:.4g}")
    log(f"  UNION UNSIGNED: raw={u_raw:.4f} rho={u_rho:+.4f} resid={u_resid:.4f} cluster-p={cl_u['p_value']:.4g}")

    # ------------------------------------------------------------- Arm C: protein_baseline_auc, the new measurement
    log("\n### Arm C: protein_baseline_auc -- does the score separate proteins better than sites? ###")
    pb = {}
    for label, cohort in (("original_108", original), ("extension", extension), ("union", union)):
        r = protein_baseline_auc(cohort, protein_of)
        pb[label] = r
        if r:
            log(f"  {label:<14} n_clusters={r['n_clusters']:>3} n_residues={r['n_residues']:>5}  "
                f"protein_baseline_auc={r['auc']:.4f}  null={r['null_mean']:.4f}+-{r['null_std']:.4f}  p={r['p_value']:.4g}")
        else:
            log(f"  {label:<14} degenerate (all-same label), skipped")

    out = dict(
        n_candidates=len(candidates), n_extension_resolved=len(extension),
        unresolved=unresolved,
        contamination=contamination,
        arm_a_decoherent_vs_coherent=dict(
            planned_validation=dict(pass_=check_a, **val_a),
            union=dict(n=len(union), decoherent=dict(raw=d_raw, rho=d_rho, resid=d_resid),
                       coherent=dict(raw=c_raw, rho=c_rho, resid=c_resid),
                       delta_median=cl_a["median"], cluster_p=cl_a["p_value"], n_clusters=cl_a["n_clusters"]),
        ),
        arm_b_f1_anchor=dict(
            planned_validation=dict(pass_=check_b, signed=val_b_signed, unsigned=val_b_unsigned),
            union_signed=dict(raw=s_raw, rho=s_rho, resid=s_resid, cluster_p=cl_s["p_value"], n_clusters=cl_s["n_clusters"]),
            union_unsigned=dict(raw=u_raw, rho=u_rho, resid=u_resid, cluster_p=cl_u["p_value"], n_clusters=cl_u["n_clusters"]),
        ),
        arm_c_protein_baseline_auc=pb,
    )
    (OUT / "cohort_extension_result.json").write_text(json.dumps(out, indent=1, default=str))
    ckpt.write(json.dumps(dict(kind="final", **out), default=str) + "\n"); ckpt.close()
    log(f"\nWrote {OUT}/cohort_extension_result.json ({time.time()-t0:.0f}s total)")
    log_f.close()
    return 0 if (check_a and check_b) else 1


if __name__ == "__main__":
    sys.exit(main())
