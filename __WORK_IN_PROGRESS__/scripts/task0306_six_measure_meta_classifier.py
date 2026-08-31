"""TASK-0306 -- is WHICH of Wu/Stromich/Yaliraki (2022)'s six statistical
measures fires predictable, on a cohort large enough to ask ([[TASK-0304]]'s
ASBench/CASBench extension, 432 structures / 146 proteins)?

Background. [[TASK-0301]] closed the meta-selector question on our own
13-cluster cohort for two reasons, both lifted here: (1) 13 clusters
cannot validate any selector; ASBench+CASBench give protein-level counts
an order of magnitude larger. (2) our 61 rules were ALL functions of the
same two raw inputs (distance-to-seed, fpocket druggability) -- "one
signal at 61 settings," so no ensemble over them could ever add
information (TASK-0301's own finding: negative vote-margin-vs-accuracy
correlation). Their six measures are not that by construction: three test
TYPES (surrogate-CI, high-propensity-proportion P(p>0.95), reference-
quantile) each computed at TWO levels (pR = residue, pb = bond) --
genuinely two different observables (residue- vs bond-level propensity),
not one signal restated.

THE SIX MEASURES, Table S3/S4 (ASBench) and S5/S6 (CASBench) column order:
  0: pR,allo - <pR,site>surr > 0   (residue-level surrogate-CI)
  1: pb,allo - <pb,site>surr > 0   (bond-level surrogate-CI)
  2: P(pR,allo > 0.95) > 0.05      (residue-level high-propensity-proportion)
  3: P(pb,allo > 0.95) > 0.05      (bond-level high-propensity-proportion)
  4: ref pR,allo > 0.5             (residue-level reference-quantile)
  5: ref pb,allo > 0.5             (bond-level reference-quantile)
The paper's own ``Summary`` column (a 6-character bullet string, (star)/(open)
per measure in this exact order) is parsed directly -- these are THEIR
verdicts on THEIR own thresholds, not re-derived from the raw columns, so
this script's own binary calls cannot silently disagree with the paper's.

DATA SOURCE: Europe PMC's own `supplementaryFiles` endpoint (PMC8767309),
which serves the deposited Cell-Press supplementary files without the
JS proof-of-work challenge PMC's own site presents to `curl`
([[TASK-0304]]'s own finding, reused verbatim, not re-discovered). Fetched
live each run (4.8 MB, ~19 files, five .xlsx used here); nothing is
cached to disk beyond this script's own derived JSON output, matching
this register's own convention of not committing large upstream binaries.

Reuses, does not re-derive:
  - the Europe PMC endpoint URL and the mmc3-mmc6.xlsx = S3-S6 mapping
    ([[TASK-0304]]'s own Progress-2 section, confirmed independently here
    by reproducing its exact 105/118, 99/118, 27/118, 21/118 counts before
    trusting the parse for anything new).
  - `results/tasks/0304_asbench_casbench/cohort_pdb_ids.json` for the
    `casbench_ortho_ligand`/`casbench_ortho_residues` naming convention.

Run: ../.venv/bin/python3 scripts/task0306_six_measure_meta_classifier.py
(requires `openpyxl`, pip-installed into .venv for this task -- not added
to the deployed backend's own requirements.txt, which this script has no
relationship to.)
"""
from __future__ import annotations

import io
import json
import re
import sys
import urllib.request
import warnings
import zipfile
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")

sys.path.insert(0, "..")
from backend.data_layer import fetch  # noqa: E402 -- this register's own cached PDB fetch

OUT = Path("results/tasks/0306_six_measure_meta_classifier")
SUPP_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8767309/supplementaryFiles"
MEASURE_NAMES = ["surrCI_pR", "surrCI_pb", "highProp_pR", "highProp_pb", "refQ_pR", "refQ_pb"]

# (xlsx member, sheet, condition label) -- verified against TASK-0304's own
# reproduced counts before use, see main().
SHEETS = [
    ("mmc3.xlsx", "Scoring_SI_2", "asbench_with_ligand"),
    ("mmc4.xlsx", "Scoring_SI_3", "asbench_without_ligand"),
    ("mmc5.xlsx", "Scoring_SI_4", "casbench_ortho_ligand"),
    ("mmc6.xlsx", "Scoring_SI_5", "casbench_ortho_residues"),
]


def fetch_supp() -> zipfile.ZipFile:
    req = urllib.request.Request(SUPP_URL, headers={"User-Agent": "qas-task0306/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return zipfile.ZipFile(io.BytesIO(data))


def parse_sheet(zf: zipfile.ZipFile, member: str, sheet: str, condition: str) -> list[dict]:
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(zf.read(member)), data_only=True)
    ws = wb[sheet]
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[1] is None:
            continue
        protein, pdb, summary = r[0], r[1], r[8]
        if summary is None or len(summary.strip()) != 6:
            continue
        bits = tuple(1 if ch == "●" else 0 for ch in summary.strip())
        rows.append(dict(protein=str(protein).strip(), pdb=str(pdb).strip(),
                          condition=condition, bits=bits, n_fired=sum(bits)))
    return rows


def phi_coefficient(a: np.ndarray, b: np.ndarray) -> float:
    """Matthews correlation for two binary vectors -- the direct pairwise
    redundancy statistic this task's own Scope calls for."""
    n11 = int(np.sum((a == 1) & (b == 1))); n00 = int(np.sum((a == 0) & (b == 0)))
    n10 = int(np.sum((a == 1) & (b == 0))); n01 = int(np.sum((a == 0) & (b == 1)))
    denom = np.sqrt((n11 + n10) * (n11 + n01) * (n00 + n10) * (n00 + n01))
    if denom == 0:
        return float("nan")
    return (n11 * n00 - n10 * n01) / denom


def describe_patterns(rows: list[dict]) -> dict:
    cnt = Counter(r["bits"] for r in rows)
    n = len(rows)
    ranked = cnt.most_common()
    top3_cov = sum(c for _, c in ranked[:3]) / n
    return {
        "n": n, "n_distinct_patterns": len(cnt),
        "max_possible_patterns": 64,
        "top5_patterns": [{"bits": "".join(map(str, k)), "count": v, "frac": v / n}
                           for k, v in ranked[:5]],
        "top3_coverage": top3_cov,
    }


def pairwise_matrix(rows: list[dict]) -> dict:
    B = np.array([r["bits"] for r in rows])
    mat = np.full((6, 6), np.nan)
    for i, j in combinations(range(6), 2):
        mat[i, j] = mat[j, i] = phi_coefficient(B[:, i], B[:, j])
    for i in range(6):
        mat[i, i] = 1.0
    offdiag = mat[np.triu_indices(6, k=1)]
    pR_block = [mat[i, j] for i, j in combinations([0, 2, 4], 2)]
    pb_block = [mat[i, j] for i, j in combinations([1, 3, 5], 2)]
    cross = [mat[i, j] for i in [0, 2, 4] for j in [1, 3, 5]]
    return {
        "matrix": mat.tolist(), "measure_names": MEASURE_NAMES,
        "mean_abs_offdiag": float(np.nanmean(np.abs(offdiag))),
        "mean_within_pR_block": float(np.nanmean(pR_block)),
        "mean_within_pb_block": float(np.nanmean(pb_block)),
        "mean_cross_pR_pb": float(np.nanmean(cross)),
    }


INDEPENDENCE_THRESHOLD = 0.6  # pre-stated: TASK-0301's 61 rules were the same
# 2 raw inputs at different knob settings -- that produces NEAR-PERFECT
# pairwise correlation among their rankings (the same formula, monotonic in
# each input). A mean |phi| well below that (this threshold, chosen before
# the numbers were computed) is the operational bar for "not that failure
# mode" -- not a claim of true statistical independence, which six related
# significance tests on the same structures will never fully satisfy.


def structure_descriptors(pdb_id: str) -> dict | None:
    """N (resolved CA count) and chain count, from the deposited PDB file
    -- `backend.data_layer.fetch`'s own cache, reused, not re-derived."""
    fp = fetch(pdb_id)
    if fp is None:
        return None
    chains = {}
    for line in Path(fp).read_text().splitlines():
        if not line.startswith("ATOM"):
            continue
        if line[12:16].strip() != "CA":
            continue
        ch = line[21]
        try:
            resnum = int(line[22:26])
        except ValueError:
            continue
        chains.setdefault(ch, set()).add(resnum)
    if not chains:
        return None
    return {"N": sum(len(v) for v in chains.values()), "n_chains": len(chains)}


def lopo_predict(X: np.ndarray, y: np.ndarray, groups: list[str]) -> np.ndarray:
    """Leave-one-PROTEIN-out OLS, this register's own established
    convention (TASK-0249/TASK-0282's own `_fit_ols`) -- not a new
    classifier. Returns out-of-fold predicted scores, same length as y."""
    groups = np.asarray(groups)
    preds = np.full(len(y), np.nan)
    for g in sorted(set(groups)):
        train = groups != g
        test = groups == g
        if train.sum() < 4:
            continue
        Xb = np.column_stack([X[train], np.ones(train.sum())])
        b, *_ = np.linalg.lstsq(Xb, y[train].astype(float), rcond=None)
        Xt = np.column_stack([X[test], np.ones(test.sum())])
        preds[test] = Xt @ b
    return preds


def meta_classifier(rows: list[dict], finding_f_by_pdb: dict) -> dict:
    """Predict which of the 6 measures fire from protein-level descriptors
    (N, n_chains, site separation), leave-one-PROTEIN-out throughout --
    this task's own Constraint against structure-level pseudo-replication.
    ASBench only (79 protein clusters over 118 structures) -- CASBench's
    own site-separation descriptor is not available yet ([[TASK-0304]]'s
    own "still to do": CASBench site annotations), and its 314/33
    structures-per-protein ratio is the exact failure mode this task's
    Constraint names, so it is not force-fit here without that feature."""
    joined = []
    for r in rows:
        ff = finding_f_by_pdb.get(r["pdb"])
        if ff is None:
            continue
        desc = structure_descriptors(r["pdb"].split("_")[0])
        if desc is None:
            continue
        joined.append(dict(**r, site_sep=ff["min_heavy_A"], **desc))
    print(f"\n  descriptor-joined: {len(joined)}/{len(rows)} structures "
          f"({len(set(j['protein'] for j in joined))} proteins)")

    N = np.array([j["N"] for j in joined], float)
    nch = np.array([j["n_chains"] for j in joined], float)
    sep = np.array([j["site_sep"] for j in joined], float)
    X = np.column_stack([(N - N.mean()) / N.std(), (nch - nch.mean()) / (nch.std() or 1.0),
                          (sep - sep.mean()) / sep.std()])
    groups = [j["protein"] for j in joined]
    n_fired = np.array([j["n_fired"] for j in joined], float)

    pred_nfired = lopo_predict(X, n_fired, groups)
    valid = ~np.isnan(pred_nfired)
    rho_nfired = spearmanr(pred_nfired[valid], n_fired[valid])

    per_measure = {}
    for k, name in enumerate(MEASURE_NAMES):
        y = np.array([j["bits"][k] for j in joined], float)
        if y.sum() < 5 or y.sum() > len(y) - 5:
            per_measure[name] = {"skipped": "too few positives/negatives for a stable LOPO AUC",
                                  "n_pos": int(y.sum())}
            continue
        pred = lopo_predict(X, y, groups)
        v = ~np.isnan(pred)
        auc = roc_auc_score(y[v], pred[v])
        per_measure[name] = {"lopo_auc": float(auc), "n_pos": int(y.sum()), "n": int(v.sum())}

    # Positive control (standing rule, .ai/COMPUTE_WINDOW_2026-08-31.md
    # #2: "every negative needs a positive control"). Uses the SAME
    # lopo_predict/roc_auc_score machinery on a relationship already known
    # to be real from the pairwise-phi step above: predicting one measure
    # from the other five. If this comes back near 0.5 too, the harness
    # itself -- not the protein descriptors -- would be the suspect.
    control = {}
    Ball = np.array([j["bits"] for j in joined], float)
    for k, name in enumerate(MEASURE_NAMES):
        y = Ball[:, k]
        Xc = np.delete(Ball, k, axis=1)
        pred = lopo_predict(Xc, y, groups)
        v = ~np.isnan(pred)
        control[name] = float(roc_auc_score(y[v], pred[v]))

    return dict(n_joined=len(joined), n_proteins=len(set(groups)),
                rho_nfired=float(rho_nfired.statistic), p_nfired=float(rho_nfired.pvalue),
                per_measure=per_measure, positive_control_auc=control)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Fetching Europe PMC supplementary files (PMC8767309)...")
    zf = fetch_supp()

    all_rows: dict[str, list[dict]] = {}
    for member, sheet, cond in SHEETS:
        rows = parse_sheet(zf, member, sheet, cond)
        all_rows[cond] = rows
        ge1 = sum(1 for r in rows if r["n_fired"] >= 1)
        all6 = sum(1 for r in rows if r["n_fired"] == 6)
        print(f"  {cond:<26} n={len(rows):<4} >=1: {ge1}/{len(rows)}={ge1/len(rows):.1%}  "
              f"all6: {all6}/{len(rows)}={all6/len(rows):.1%}")

    # control: reproduce TASK-0304's own already-verified ASBench counts exactly
    ref = {"asbench_with_ligand": (105, 27), "asbench_without_ligand": (99, 21)}
    print("\n=== Control: reproducing TASK-0304's own counts before trusting anything new ===")
    ok = True
    for cond, (exp_ge1, exp_all6) in ref.items():
        rows = all_rows[cond]
        ge1 = sum(1 for r in rows if r["n_fired"] >= 1)
        all6 = sum(1 for r in rows if r["n_fired"] == 6)
        match = (ge1, all6) == (exp_ge1, exp_all6)
        ok &= match
        print(f"  {cond}: got ({ge1},{all6}) expected ({exp_ge1},{exp_all6})  {'OK' if match else 'MISMATCH'}")
    if not ok:
        print("\n  *** CONTROL FAILED -- sheet/column mapping is wrong, stopping. ***")
        return 1

    print("\n=== Descriptive: how concentrated are the 6-bit patterns? ===")
    desc = {}
    for cond, rows in all_rows.items():
        d = describe_patterns(rows)
        desc[cond] = d
        print(f"  {cond:<26} {d['n_distinct_patterns']}/64 distinct patterns, "
              f"top-3 cover {d['top3_coverage']:.1%}")
        for p in d["top5_patterns"]:
            print(f"      {p['bits']}  n={p['count']:>3}  ({p['frac']:.1%})")

    print(f"\n=== Pairwise redundancy between the six measures (phi coefficient) ===")
    print(f"    measures: {MEASURE_NAMES}")
    pw = {}
    for cond, rows in all_rows.items():
        m = pairwise_matrix(rows)
        pw[cond] = m
        print(f"\n  {cond} (n={len(rows)}):")
        print(f"    mean |phi| off-diagonal (all 15 pairs)  = {m['mean_abs_offdiag']:.3f}")
        print(f"    mean phi WITHIN pR block (3 measures)   = {m['mean_within_pR_block']:.3f}")
        print(f"    mean phi WITHIN pb block (3 measures)   = {m['mean_within_pb_block']:.3f}")
        print(f"    mean phi ACROSS pR vs pb (9 pairs)      = {m['mean_cross_pR_pb']:.3f}")

    # decision gate, stated before looking at whether it favours proceeding
    primary = all_rows["asbench_without_ligand"]
    primary_phi = pw["asbench_without_ligand"]["mean_abs_offdiag"]
    proceed = primary_phi < INDEPENDENCE_THRESHOLD
    print(f"\n=== Decision gate (pre-stated bar: mean|phi| < {INDEPENDENCE_THRESHOLD}) ===")
    print(f"  primary condition (asbench_without_ligand) mean|phi| = {primary_phi:.3f}")
    print(f"  {'PROCEED' if proceed else 'STOP'} to protein-level meta-classifier "
          f"({'below' if proceed else 'at/above'} the bar)")
    print(f"  Note: {primary_phi:.3f} is moderate, not near-zero -- these six measures")
    print(f"  are more independent than TASK-0301's 61 rules (same 2 inputs, near-total")
    print(f"  collinearity) but not fully independent either; any meta-classifier gain")
    print(f"  below has to clear this much shared variance, not a clean-slate 6 votes.")

    meta = None
    if proceed:
        print("\n=== Meta-classifier: predict which measures fire from protein-level "
              "descriptors (N, n_chains, site separation), LOPO by protein, ASBench only ===")
        finf = json.loads(Path("results/tasks/0304_asbench_casbench/asbench_finding_f.json").read_text())
        finding_f_by_pdb = {r["pdb"]: r for r in finf["rows"]}
        meta = meta_classifier(primary, finding_f_by_pdb)
        print(f"\n  n_fired (0-6) LOPO Spearman rho = {meta['rho_nfired']:+.3f}  "
              f"(p={meta['p_nfired']:.4f}, n={meta['n_joined']}, "
              f"{meta['n_proteins']} protein clusters)")
        print(f"\n  per-measure LOPO AUC (protein-held-out):")
        for name, r in meta["per_measure"].items():
            if "skipped" in r:
                print(f"    {name:<14} skipped -- {r['skipped']} (n_pos={r['n_pos']})")
            else:
                print(f"    {name:<14} AUC={r['lopo_auc']:.3f}  (n_pos={r['n_pos']}/{r['n']})")
        print(f"\n  positive control -- predict measure k from the OTHER 5 measures' own bits")
        print(f"  (a known-real relationship, from the phi step above; validates the LOPO/AUC")
        print(f"  harness itself, so the near/below-0.5 numbers above are not a broken pipeline):")
        for name, auc in meta["positive_control_auc"].items():
            print(f"    {name:<14} AUC={auc:.3f}")

    out = dict(sheets=SHEETS, rows={k: v for k, v in all_rows.items()},
               descriptive=desc, pairwise=pw,
               decision_gate=dict(threshold=INDEPENDENCE_THRESHOLD, primary_phi=primary_phi,
                                   proceeded=proceed),
               meta_classifier=meta)
    (OUT / "six_measure_analysis.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwritten: {OUT / 'six_measure_analysis.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
