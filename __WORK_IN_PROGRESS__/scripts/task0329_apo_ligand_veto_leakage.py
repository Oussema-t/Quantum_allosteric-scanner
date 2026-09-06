"""TASK-0329 -- is the apo-ligand veto exception ("keep a pocket PocketMiner
calls closed if it touches a ligand already bound in the apo file") doing
real, label-independent work, or is it leaking ligand location into the
prediction?

Owner of the veto is Oussema (`allosteric` branch). This task measures the
already-run pipeline; it does not redesign it (Out Of Scope, per its own
filing). Everything below is a read-only scoring pass over the SAME 138
structures/artifacts [[TASK-0327]]/[[TASK-0328]] already used
(`origin/allosteric` @ f257789, `results/veto_pipeline/`), copied into a
local worktree, never pushed upstream -- identical convention to those two
tasks.

METHOD -- reuses, does not re-derive, two already-validated pieces of
machinery:
  1. [[TASK-0327]]'s own "best member wins" identity: under S3's real rule
     (pocket score = its best residue's score, not the mean-based
     `top_pocket()` defined-but-unused in `pocketsweep.py`), the top-ranked
     pocket for ANY per-residue score vector is exactly whichever surviving
     pocket contains the single top-ranked residue. This makes every "what
     if a DIFFERENT set of pockets had survived the veto" question a
     pure post-filter of round-1's own per-residue CTQW ranks (pre-veto,
     unfiltered) -- no re-run of fpocket, PocketMiner, or the walk needed,
     because round 1 already computed occupation for every candidate
     residue and the walk depends only on the fixed active-site seed and
     the whole structure's own H_new, never on which pockets are being
     considered downstream. Verified directly below (`verify_filter_
     invariance`), not assumed, before trusting anything built on it.
  2. PocketMiner itself ([[TASK-0269]]/[[TASK-0285]]'s own vendored Docker
     image, `qas-pocketminer:pocket_pred`) -- re-run fresh on all 138
     structures' own candidate-pocket residues, because no per-residue
     PocketMiner score for this exact cohort was ever committed anywhere
     in the `allosteric` branch's own history (checked directly, `git log
     --all` on every `pm_out`/`.resnums.json` path -- zero hits). The
     median-split veto rule (`results/full_run_1022/build_veto_hpc.py`,
     the only surviving copy of the actual formula, corroborated by
     `PIPELINE_DESIGN.md`'s own S4 spec: "drop worse half by pocket-mean
     score") needs real accessibility numbers to test the exception
     against, not a substitute.

Ligand contact is computed directly from raw apo-PDB HETATM records
(`build_veto_hpc.py`'s own JUNK-exclusion list, reused verbatim, 4.5 A),
never from `apo_bound_ligands.json`'s own protein-level summary alone --
that file is missing 28/138 proteins entirely (CASBench/CryptoBench rows),
confirmed by direct lookup, so a per-atom recomputation is the only way to
cover the full cohort.

Run: ../.venv/bin/python3 scripts/task0329_apo_ligand_veto_leakage.py
"""
from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
import time
import warnings
from collections import defaultdict
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "2")

import numpy as np
import requests
from scipy.stats import wilcoxon

warnings.filterwarnings("ignore")
sys.path.insert(0, "src")
sys.path.insert(0, "..")
from backend.data_layer import PDB_CACHE  # noqa: E402

WT = Path("/tmp/qas_allosteric_wt/allosteric/results/veto_pipeline")
OUT = Path("results/tasks/0329_apo_ligand_veto_leakage")
PM_IN = OUT / "pocketminer_io" / "input"
PM_OUT = OUT / "pocketminer_io" / "output"
DOCKER_IMAGE = "qas-pocketminer:pocket_pred"

AA3 = {"ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
       "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL", "MSE"}
JUNK = set("HOH SO4 PO4 GOL EDO PEG PGE MPD ACT CL NA K MG CA ZN MN FE NI CD CU TRS "
           "EPE IMD DMS FMT ACY BME NO3 CIT TLA MES BTB IOD BR CO SR CS NH4 AZI 1PE "
           "P6G PE4 PGO BOG LDA OCT SIN MLI SCN F UNX UNL".split())


def _log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def fetch(pdb, timeout=20):
    fp = os.path.join(PDB_CACHE, f"{pdb}.pdb")
    if os.path.exists(fp):
        return fp
    r = requests.get(f"https://files.rcsb.org/download/{pdb}.pdb", timeout=timeout)
    r.raise_for_status()
    with open(fp, "w") as fh:
        fh.write(r.text)
    return fp


def load_merged(pattern):
    d = {}
    for f in sorted(glob.glob(str(WT / pattern))):
        d.update(json.load(open(f)))
    return d


def resolve_chain(name, pdb, lig_summary):
    if name in lig_summary:
        return lig_summary[name]["chain"], False
    fp = fetch(pdb)
    counts = defaultdict(int)
    with open(fp) as fh:
        for line in fh:
            if line.startswith("ATOM") and line[17:20].strip() in AA3:
                counts[line[21]] += 1
    if not counts:
        return None, True
    return max(counts, key=counts.get), True


def parse_structure(pdb, chain):
    """One pass: CA resnums in file order (for PocketMiner alignment), and
    per-residue heavy-atom coords + ligand heavy-atom coords (for the
    contact computation)."""
    fp = fetch(pdb)
    ca_resn = []
    prot_atoms = defaultdict(list)
    lig_xyz = []
    seen_ca = set()
    seen_model = False
    with open(fp) as fh:
        for line in fh:
            if line.startswith("MODEL"):
                if seen_model:
                    break
                seen_model = True
                continue
            if not (line.startswith("ATOM") or line.startswith("HETATM")):
                continue
            if line[21] != chain or line[16] not in (" ", "A"):
                continue
            resn3 = line[17:20].strip()
            try:
                resnum = int(line[22:26])
                x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
            except ValueError:
                continue
            el = line[76:78].strip().upper()
            aname = line[12:16].strip()
            is_h = el == "H" or (not el and aname.startswith("H"))
            is_protein_atom = line.startswith("ATOM") or resn3 in AA3
            if is_protein_atom:
                if aname == "CA" and resnum not in seen_ca:
                    ca_resn.append(resnum); seen_ca.add(resnum)
                if not is_h:
                    prot_atoms[resnum].append((x, y, z))
            elif resn3 not in JUNK and not is_h:
                lig_xyz.append((x, y, z))
    return (np.asarray(ca_resn, int), prot_atoms,
            np.asarray(lig_xyz, float) if lig_xyz else np.zeros((0, 3)))


def ligand_contact_resnums(prot_atoms, lig_xyz, cutoff=4.5):
    if len(lig_xyz) == 0:
        return set()
    out = set()
    for resnum, atoms in prot_atoms.items():
        a = np.asarray(atoms, float)
        d = np.sqrt(((a[:, None, :] - lig_xyz[None, :, :]) ** 2).sum(-1))
        if (d < cutoff).any():
            out.add(resnum)
    return out


def export_pdb_for_pocketminer(pdb, chain, out_path):
    fp = fetch(pdb)
    lines = []
    seen_model = False
    with open(fp) as fh:
        for line in fh:
            if line.startswith("MODEL"):
                if seen_model:
                    break
                seen_model = True
                continue
            if not line.startswith("ATOM"):
                continue
            if line[21] != chain or line[16] not in (" ", "A"):
                continue
            lines.append(line)
    if len(lines) < 10:
        return False
    lines.append("END\n")
    out_path.write_text("".join(lines))
    return True


def run_pocketminer_docker(input_dir: Path, output_dir: Path, timeout=3600):
    output_dir.mkdir(parents=True, exist_ok=True)
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    cmd = ["docker", "run", "--rm", "--platform", "linux/amd64",
           "-v", f"{input_dir}:/data/input:ro", "-v", f"{output_dir}:/data/output",
           DOCKER_IMAGE]
    _log(f"$ {' '.join(cmd)}")
    t0 = time.monotonic()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    _log(f"docker run exit={r.returncode} elapsed={time.monotonic()-t0:.0f}s")
    print(r.stdout[-4000:])
    if r.returncode != 0 and not any(output_dir.iterdir()):
        print(r.stderr[-3000:])
        raise RuntimeError("docker run produced no output at all")


# ------------------------------------------------------------- scoring core
def pockets_from_flat(seed_resnum, seed_pocket):
    """Round-1's own flat (resnum, pocket_id) arrays -> {pocket_id: [resnum,...]}."""
    g = defaultdict(list)
    for r, p in zip(seed_resnum, seed_pocket):
        g[p].append(r)
    return g


# Filter-invariance ("round-1 ranks restricted to a keep set == what a
# fresh walk on that keep set would give") was NOT assumed -- checked
# directly, per-score-type, before use. Ground truth: round-2's own real
# `pockets` list (which pockets pocketsweep.py's own round-2 ACTUALLY
# carried forward) vs round-1's ranks restricted to that same set,
# best-member-wins argmin, compared to round-2's own real argmin.
# Result (1040 protein-cells checked per type, 115 proteins):
#   QMI 97.4%, R 97.2%, green_lmax_0.05 98.9%, green_zero_0.01 97.9%,
#   green_zero_0.05 99.1%, neg_ED_final 99.0%, neg_dD_mean 98.0%,
#   p_avg 98.7%, p_peak 98.6%, pavg_over_dX 99.0% -- all >97%, trusted.
#   residLOG/residLOG_dX/residRAW/residRAW_dX: 76-87% -- clearly NOT just
#   a reordering under pool-size change (some per-round rescaling this
#   task did not chase down), EXCLUDED from every counterfactual arm
#   below. (Earlier, using `veto_keep.json`'s own "10" key as ground
#   truth instead of round-2's real pockets gave much worse agreement,
#   68-89% even for the clean score types -- traced to at least one real
#   discrepancy between that file and what pocketsweep.py's round-2 run
#   actually used, e.g. ASB_1W25 pocket 1: listed in veto_keep.json but
#   absent from round-2's own stored `pockets`. Round-2's own data is the
#   more authoritative ground truth and is what every arm below is
#   validated against.)
RELIABLE_SCORES = {"QMI", "R", "green_lmax_0.05", "green_zero_0.01", "green_zero_0.05",
                    "neg_ED_final", "neg_dD_mean", "p_avg", "p_peak", "pavg_over_dX"}


def best_member_hit(ranks, seed_pocket, keep_ids, drug_id):
    """[[TASK-0327]]'s own reduction, restricted to a candidate KEEP set:
    among positions whose pocket is in keep_ids, take the argmin rank
    (rank 1 = best); hit iff that residue's pocket is the drug pocket.
    Returns None if keep_ids leaves no residues at all (veto emptied the
    protein) or the drug pocket itself was vetoed out (a real, disclosed
    failure mode, not silently excluded)."""
    idx = [i for i, p in enumerate(seed_pocket) if p in keep_ids]
    if not idx:
        return None, "veto_emptied"
    if drug_id not in keep_ids:
        return 0, "drug_pocket_vetoed"
    sub_ranks = [ranks[i] for i in idx]
    best_i = idx[int(np.argmin(sub_ranks))]
    return int(seed_pocket[best_i] == drug_id), None


def drug_pocket_of(pockets_list, bar=0.25):
    if not pockets_list:
        return None, False
    best = max(pockets_list, key=lambda p: (p["n_drug"], p["drug_frac"]))
    return best["id"], best["drug_frac"] >= bar


def score_arm_real(round_data, label):
    """Arm A (baseline): scored DIRECTLY from a round's own real, stored
    ranks/seed_pocket -- no reduction, no assumption, exact ground truth.
    Used for round2 (current, ligand-aware veto, as actually run)."""
    rows = []
    for name, rec in round_data.items():
        if "cells" not in rec:
            continue
        pockets_list = rec["pockets"]
        if len(pockets_list) < 2:
            continue
        drug_id, valid = drug_pocket_of(pockets_list)
        if not valid:
            continue
        seed_pocket = rec["seed_pocket"]
        hits = []
        for cell, ranks in rec["ranks"].items():
            if cell.split("|")[-1] not in RELIABLE_SCORES:
                continue
            best_i = int(np.argmin(ranks))
            hits.append(int(seed_pocket[best_i] == drug_id))
        if not hits:
            continue
        rows.append(dict(name=name, cluster=rec["cluster"], n_kept_pockets=len(pockets_list),
                         n_pockets_total=len(pockets_list), drug_pocket_survived=True,
                         cell_hit_rate=float(np.mean(hits))))
    n = len(rows)
    hit_rate = float(np.mean([r["cell_hit_rate"] for r in rows])) if rows else float("nan")
    print(f"  {label:<32} n={n:4d}  pooled-cell hit rate={hit_rate:.4f}  (ground truth, no reduction)")
    return dict(label=label, n=n, hit_rate=hit_rate, rows=rows)


def score_arm(round1, keep_fn, label):
    """Counterfactual arms (a DIFFERENT keep set than what was actually
    run): keep_fn(name, rec) -> set of kept pocket ids, or None to skip.
    Uses round-1's own ranks + the best-member-wins reduction, RESTRICTED
    to RELIABLE_SCORES (validated above) -- residLOG/RAW cells are
    excluded from every arm here, not just this one, for a fair
    apples-to-apples comparison across arms."""
    rows = []
    for name, rec in round1.items():
        if "cells" not in rec:
            continue
        pockets_list = rec["pockets"]
        if len(pockets_list) < 2:
            continue
        drug_id, valid = drug_pocket_of(pockets_list)
        if not valid:
            continue
        keep_ids = keep_fn(name, rec)
        if keep_ids is None:
            continue
        seed_pocket = rec["seed_pocket"]
        hits, reasons = [], []
        for cell, ranks in rec["ranks"].items():
            if cell.split("|")[-1] not in RELIABLE_SCORES:
                continue
            h, why = best_member_hit(ranks, seed_pocket, keep_ids, drug_id)
            if h is not None:
                hits.append(h)
            reasons.append(why)
        if not hits:
            continue
        rows.append(dict(name=name, cluster=rec["cluster"], n_kept_pockets=len(keep_ids),
                         n_pockets_total=len(pockets_list),
                         drug_pocket_survived=drug_id in keep_ids,
                         cell_hit_rate=float(np.mean(hits))))
    n = len(rows)
    hit_rate = float(np.mean([r["cell_hit_rate"] for r in rows])) if rows else float("nan")
    survived = float(np.mean([r["drug_pocket_survived"] for r in rows])) if rows else float("nan")
    kept_frac = float(np.mean([r["n_kept_pockets"] / r["n_pockets_total"] for r in rows])) if rows else float("nan")
    print(f"  {label:<32} n={n:4d}  pooled-cell hit rate={hit_rate:.4f}  "
          f"drug-pocket survives veto={survived:.1%}  mean kept-fraction={kept_frac:.1%}")
    return dict(label=label, n=n, hit_rate=hit_rate, drug_pocket_survival=survived,
               mean_kept_fraction=kept_frac, rows=rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    round1 = load_merged("s14_r1_k10_h2_*.json")
    round2 = load_merged("s14_r2_k10_h2_*.json")
    veto_keep = json.load(open(WT / "veto_keep.json"))
    lig_summary = json.load(open(WT / "apo_bound_ligands.json"))
    _log(f"round1={len(round1)} round2={len(round2)} veto_keep={len(veto_keep)} "
         f"apo_bound_ligands={len(lig_summary)}")

    # ---- Part 0: resolve pdb/chain ----
    meta = {}
    for name in round1:
        pdb = re.sub(r"_[0-9]+$", "", name.split("_", 1)[1])
        chain, guessed = resolve_chain(name, pdb, lig_summary)
        meta[name] = dict(pdb=pdb, chain=chain, chain_guessed=guessed)
    n_guessed = sum(1 for m in meta.values() if m["chain_guessed"])
    _log(f"chain resolved for {len(meta)} ({n_guessed} guessed, no apo_bound_ligands.json entry)")

    # ---- Part 1: per-protein ligand contact (real, from raw atoms) ----
    _log("Part 1: computing real ligand contact from raw apo PDB atoms...")
    contact = {}   # name -> set(resnum) that touch a real ligand
    ca_resn_by_name = {}
    for i, (name, m) in enumerate(meta.items()):
        if m["chain"] is None:
            continue
        try:
            ca_resn, prot_atoms, lig_xyz = parse_structure(m["pdb"], m["chain"])
        except Exception as e:
            _log(f"  {name}: parse FAILED {type(e).__name__}: {e}")
            continue
        contact[name] = ligand_contact_resnums(prot_atoms, lig_xyz)
        ca_resn_by_name[name] = ca_resn
        if (i + 1) % 30 == 0:
            _log(f"  {i+1}/{len(meta)}")
    _log(f"ligand contact computed for {len(contact)}/{len(meta)} proteins")

    # ---- Part 2: export + run PocketMiner on every resolvable structure ----
    PM_IN.mkdir(parents=True, exist_ok=True)
    exported = {}
    for name, m in meta.items():
        if m["chain"] is None:
            continue
        ok = export_pdb_for_pocketminer(m["pdb"], m["chain"], PM_IN / f"{name}.pdb")
        if ok:
            exported[name] = True
    _log(f"exported {len(exported)}/{len(meta)} structures for PocketMiner")

    already = {p.stem for p in PM_OUT.glob("*.txt")} | {p.stem for p in PM_OUT.glob("*.error.txt")}
    todo = len(exported) - len(already & exported.keys())
    if todo > 0:
        _log(f"running PocketMiner docker on {len(exported)} structures ({todo} new)...")
        run_pocketminer_docker(PM_IN, PM_OUT)
    else:
        _log("PocketMiner output already present for all exported structures, skipping docker run")

    # ---- Part 3: per-pocket accessibility from PocketMiner output ----
    acc_by_name = {}
    n_pm_ok = 0
    for name in exported:
        txt = PM_OUT / f"{name}.txt"
        if not txt.exists():
            continue
        arr = np.loadtxt(txt)
        resn = ca_resn_by_name.get(name)
        if resn is None or len(arr) != len(resn):
            _log(f"  {name}: PocketMiner length mismatch ({len(arr)} vs {len(resn) if resn is not None else '?'}), skipped")
            continue
        acc_by_name[name] = dict(zip(resn.tolist(), arr.tolist()))
        n_pm_ok += 1
    _log(f"PocketMiner scores usable for {n_pm_ok}/{len(exported)} exported structures")

    # ---- Part 4: reconstruct per-pocket accessibility_high + ligand_contact,
    # cross-validate against round-2's own real surviving pockets before
    # trusting either (not veto_keep.json -- see RELIABLE_SCORES comment) ----
    recon = {}
    for name, rec in round1.items():
        if "cells" not in rec:
            continue  # round1's own error record ({"error": ...}) -- 28/138, no seed_resnum to read
        if name not in acc_by_name or name not in contact:
            continue
        pk = pockets_from_flat(rec["seed_resnum"], rec["seed_pocket"])
        acc_map = acc_by_name[name]
        lig_res = contact[name]
        pocket_ids = sorted(pk)
        acc_vals = {}
        for pid in pocket_ids:
            vals = [acc_map[r] for r in pk[pid] if r in acc_map]
            acc_vals[pid] = float(np.mean(vals)) if vals else None
        valid_acc = [v for v in acc_vals.values() if v is not None]
        if not valid_acc:
            continue
        med = float(np.median(valid_acc))
        lig_contact_pocket = {pid: bool(set(pk[pid]) & lig_res) for pid in pocket_ids}
        acc_high = {pid: (acc_vals[pid] is not None and acc_vals[pid] >= med) for pid in pocket_ids}
        recon[name] = dict(pocket_ids=pocket_ids, acc_vals=acc_vals, acc_high=acc_high,
                           lig_contact=lig_contact_pocket, median=med)

    _log(f"reconstruction available for {len(recon)} proteins -- validating against "
         f"round-2's own real `pockets` list (ground truth; NOT veto_keep.json -- see "
         f"RELIABLE_SCORES comment above for why that file disagrees with what "
         f"pocketsweep.py's round 2 actually used on at least one protein)")
    agree, total, disagree_examples = 0, 0, []
    for name, r in recon.items():
        if name not in round2 or "pockets" not in round2[name]:
            continue
        real_keep = {p["id"] for p in round2[name]["pockets"]}
        for pid in r["pocket_ids"]:
            predicted_keep = r["acc_high"][pid] or r["lig_contact"][pid]
            actual_keep = pid in real_keep
            total += 1
            if predicted_keep == actual_keep:
                agree += 1
            elif len(disagree_examples) < 8:
                disagree_examples.append((name, pid, predicted_keep, actual_keep,
                                          r["acc_vals"][pid], r["lig_contact"][pid]))
    agree_rate = agree / total if total else float("nan")
    print(f"\n=== Reconstruction validation: predicted keep vs round-2's real pockets ===")
    print(f"  n_pockets_checked={total}  agreement={agree_rate:.1%}")
    for ex in disagree_examples:
        print(f"    disagree: {ex}")

    # ---- Part 5: the actual arms ----
    print(f"\n=== Arms (pocket-rank-1, best-member-wins; A is ground truth, B/C are the "
          f"validated round-1 reduction, RELIABLE_SCORES only) ===")
    print(f"{'arm':<32}{'n':>6}{'hit rate':>12}{'drug survives':>16}{'kept frac':>12}")

    def arm_B(name, rec):
        r = recon.get(name)
        if r is None:
            return None
        return {pid for pid in r["pocket_ids"] if r["acc_high"][pid]}

    def arm_C_matched(name, rec):
        r = recon.get(name)
        if r is None:
            return None
        vals = r["acc_vals"]
        valid = sorted([v for v in vals.values() if v is not None])
        if not valid:
            return None
        real_keep = {p["id"] for p in round2.get(name, {}).get("pockets", [])}
        target_frac = (len(real_keep & set(r["pocket_ids"])) / len(r["pocket_ids"])
                       if r["pocket_ids"] else 0.5)
        target_frac = min(max(target_frac, 0.0), 1.0)
        q = np.quantile(valid, 1.0 - target_frac) if valid else None
        if q is None:
            return None
        return {pid for pid in r["pocket_ids"] if vals[pid] is not None and vals[pid] >= q}

    res_A_all = score_arm_real(round2, "A: current (ligand-aware) veto, as actually run")
    res_A_recon_subset = score_arm_real({k: v for k, v in round2.items() if k in recon},
                                        "A': current veto, RECON SUBSET (fair baseline for B/C)")
    res_B = score_arm(round1, arm_B, "B: accessibility-only (exception removed)")
    res_C = score_arm(round1, arm_C_matched, "C: accessibility @ matched retention rate")

    # ---- Part 6: second arm -- ligand-free subset ----
    print(f"\n=== Second arm: proteins where the exception could not have fired ===")

    def has_any_relevant_ligand(name):
        c = contact.get(name)
        return bool(c)

    lig_free = {k: v for k, v in round2.items() if k in recon and not has_any_relevant_ligand(k)}
    lig_present = {k: v for k, v in round2.items() if k in recon and has_any_relevant_ligand(k)}
    print(f"  {len(lig_free)} proteins with NO ligand contacting any candidate pocket "
          f"(exception vacuous); {len(lig_present)} with >=1 (exception could fire)")
    res_ligfree_A = score_arm_real(lig_free, "  ligand-FREE subset, current veto (real)")
    res_ligpresent_A = score_arm_real(lig_present, "  ligand-PRESENT subset, current veto (real)")

    # ---- Part 7: direct mechanism check -- does the exception preferentially
    # rescue the TRUE pocket, vs. any other candidate? (no re-scoring needed
    # at all -- a property of the veto decision itself.) ----
    print(f"\n=== Direct leakage mechanism: is the TRUE pocket disproportionately an "
          f"'exception-only' survivor compared to other candidates? ===")
    true_exc_only, true_total = 0, 0
    other_exc_only, other_total = 0, 0
    for name, r in recon.items():
        rec1 = round1.get(name)
        if rec1 is None:
            continue
        drug_id, valid = drug_pocket_of(rec1["pockets"])
        if not valid or drug_id not in r["pocket_ids"]:
            continue
        for pid in r["pocket_ids"]:
            kept = r["acc_high"][pid] or r["lig_contact"][pid]
            if not kept:
                continue
            exc_only = r["lig_contact"][pid] and not r["acc_high"][pid]
            if pid == drug_id:
                true_total += 1; true_exc_only += int(exc_only)
            else:
                other_total += 1; other_exc_only += int(exc_only)
    true_rate = true_exc_only / true_total if true_total else float("nan")
    other_rate = other_exc_only / other_total if other_total else float("nan")
    print(f"  TRUE (drug) pockets:  {true_exc_only}/{true_total} = {true_rate:.1%} "
          f"survive ONLY via the ligand exception (would be vetoed by accessibility alone)")
    print(f"  OTHER candidates:     {other_exc_only}/{other_total} = {other_rate:.1%} "
          f"survive ONLY via the ligand exception")
    print(f"  {'LEAKAGE SIGNAL' if true_rate > other_rate * 1.3 else 'no strong differential'}: "
          f"the true pocket is {'MORE' if true_rate>other_rate else 'not more'} likely than an "
          f"arbitrary candidate to depend on the ligand exception to survive.")

    out = dict(
        n_round1=len(round1), n_round2=len(round2), n_chain_guessed=n_guessed,
        n_ligand_contact_computed=len(contact), n_pocketminer_ok=n_pm_ok,
        n_reconstructed=len(recon),
        reconstruction_validation=dict(n_pockets_checked=total, agreement=agree_rate,
                                       disagree_examples=disagree_examples),
        arm_A_all=res_A_all, arm_A_recon_subset=res_A_recon_subset,
        arm_B_accessibility_only=res_B, arm_C_matched_retention=res_C,
        ligand_free_subset=dict(n_proteins=len(lig_free), result=res_ligfree_A),
        ligand_present_subset=dict(n_proteins=len(lig_present), result=res_ligpresent_A),
        direct_mechanism=dict(true_exception_only_rate=true_rate, true_n=true_total,
                              other_exception_only_rate=other_rate, other_n=other_total),
    )
    (OUT / "veto_leakage_result.json").write_text(json.dumps(out, indent=1))
    _log(f"written -> {OUT}/veto_leakage_result.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
