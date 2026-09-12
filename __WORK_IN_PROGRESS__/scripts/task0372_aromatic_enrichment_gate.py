"""TASK-0372 -- E0: is ASBench's aromatic (F/Y/W/H) enrichment at allosteric
sites real, or is it burial plus ligand contact?

External reviewer (2026-09-11/12): allosteric sites are 15.7% aromatic vs
~10.2% background across ASBench's 118 curated entries -- a real 1.54x, and
they pre-register the right first gate (burial). Not sufficient: ASBench
annotates allosteric sites as LIGAND-CONTACT residues, and this register's
own TASK-0329/TASK-0345 already measured 40/40 sampled ASBench structures
carry a bound ligand at the scored site. Aromatics dominate ligand binding
generically, so 15.7% may be "aromatics touch ligands", not allostery.

Design (this task's own Intent Contract):
  1. Resolve residue IDENTITIES from the deposited PDB. `allosteric_residues`
     already carries the resname in ASBench's own annotation string
     ("ASP14 A") -- no fetch needed for that half. `active_residues` does
     NOT ("A41" -- chain+resnum only), which is what makes this task
     non-trivial: the active-site control set's amino-acid identities have
     to be looked up from the actual structure.
  2. Relative burial per residue: BioPython ShrakeRupley SASA
     (`allostery.corex.per_atom_asa`/`per_residue_native_asa`, the SAME
     validated computation TASK-0257/TASK-0266 already used, not
     re-implemented) over Tien et al. 2013 MAX_ASA (`allostery.corex.
     MAX_ASA`, also reused).
  3. Ligand contact per residue: identical definition to TASK-0329's own
     `ligand_contact_resnums` / TASK-0359's `ligand_contacts_truth_site`
     (non-JUNK HETATM within 4.5 A of the residue's own heavy atoms) --
     same JUNK list, same cutoff, reshaped here to return a per-residue
     flag for an arbitrary residue set instead of one whole-structure bool
     (that shape doesn't fit this task's Intent Contract item 4, which
     needs the contacting/non-contacting split kept separate).
  4. Rank-residualise is_aromatic (0/1) on burial, pooled across the whole
     cohort -- the SAME `residualise()` construction TASK-0308/TASK-0310
     already established for a continuous score; used here on a binary
     variable exactly the way this register scores any y against a
     residualised covariate.
  5. Per-protein paired delta: mean residual (allosteric residues) - mean
     residual (active-site residues), in the SAME protein. Tested across
     proteins with a sign-flip permutation (TASK-0337's cluster-permutation
     convention) -- protein IS the cluster here (ASBench is already
     ~1 structure/protein, TASK-0359's own finding), so this is directly
     cluster-robust, not row-level.
  6. Repeat 4-5 separately for ligand-contacting and non-contacting strata
     (Intent Contract item 4) -- if the effect lives only in the
     contacting stratum, it is a ligand-binding result, not allostery.

Planned Validation (not named as a section in the filing, done anyway per
this register's own habit): reproduce the reviewer's own raw numbers
(15.7% vs ~10.2%, 1.54x) on this exact cohort before trusting anything
built on top of it.

Run: ../.venv/bin/python3 -u scripts/task0372_aromatic_enrichment_gate.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import os

import numpy as np
from scipy.stats import rankdata, wilcoxon

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
sys.path.insert(0, "..")

from backend.data_layer import PDB_CACHE  # noqa: E402
from allostery.corex import per_atom_asa, per_residue_native_asa, MAX_ASA  # noqa: E402

import requests

OUT = Path("results/tasks/0372_aromatic_enrichment_gate")
ANN = json.load(open("results/tasks/0304_asbench_casbench/asbench_annotations.json"))

AROMATIC = {"PHE", "TYR", "TRP", "HIS"}
AA3 = {"ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
       "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL", "MSE"}
# TASK-0329's own JUNK list, reused verbatim (also reused by TASK-0359).
JUNK = set("HOH SO4 PO4 GOL EDO PEG PGE MPD ACT CL NA K MG CA ZN MN FE NI CD CU TRS "
           "EPE IMD DMS FMT ACY BME NO3 CIT TLA MES BTB IOD BR CO SR CS NH4 AZI 1PE "
           "P6G PE4 PGO BOG LDA OCT SIN MLI SCN F UNX UNL".split())
CONTACT_CUTOFF = 4.5
MAX_FILE_MB = 30

_A = re.compile(r'^([A-Z]{2,3})\s*(-?\d+)([A-Za-z]?)\s+(\w)$')


def pa(t):
    """ASBench's "RESNAME NUM CHAIN" token -> ((chain, resnum), resname).
    Same regex TASK-0308/0310/0357 already use for allosteric_residues,
    extended here to also return the resname it already carries."""
    m = _A.match(t.strip())
    if m:
        return (m.group(4), int(m.group(2))), m.group(1)
    m = re.match(r'^([A-Z]{2,3})(-?\d+)\s+(\w)$', t.strip())
    return ((m.group(3), int(m.group(2))), m.group(1)) if m else (None, None)


def pact(t):
    """ASBench's bare "CHAIN NUM" active-site token -> (chain, resnum).
    No resname -- must be resolved from the deposited structure."""
    m = re.match(r'^(\w)(-?\d+)$', t.strip())
    return (m.group(1), int(m.group(2))) if m else None


def fetch_bounded(pdb, timeout=20):
    fp = os.path.join(PDB_CACHE, f"{pdb}.pdb")
    if os.path.exists(fp) and os.path.getsize(fp) > 0:
        return fp
    r = requests.get(f"https://files.rcsb.org/download/{pdb}.pdb", timeout=timeout)
    r.raise_for_status()
    if len(r.content) / 1e6 > MAX_FILE_MB:
        raise ValueError(f"{pdb}: {len(r.content)/1e6:.0f} MB > {MAX_FILE_MB} MB cap, skipped")
    with open(fp, "w") as fh:
        fh.write(r.text)
    return fp


def parse_structure(pdb_path):
    """One pass over the deposited file: resname per (chain,resnum), heavy
    atom coords per (chain,resnum) [protein residues only], and every
    non-JUNK HETATM heavy-atom coord (the ligand pool)."""
    resname_by_key = {}
    atoms_by_key = defaultdict(list)
    lig_xyz = []
    for L in Path(pdb_path).read_text(errors="replace").splitlines():
        if L.startswith("ENDMDL"):
            break
        if not (L.startswith("ATOM") or L.startswith("HETATM")):
            continue
        if len(L) < 54 or L[16] not in (" ", "A"):
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
            if resn3 in AA3:
                resname_by_key.setdefault(key, resn3)
            atoms_by_key[key].append((x, y, z))
        elif resn3 not in JUNK:
            lig_xyz.append((x, y, z))
    return resname_by_key, atoms_by_key, np.asarray(lig_xyz, float) if lig_xyz else np.zeros((0, 3))


def residue_burial(pdb_path):
    """Relative burial (1 - rSASA) per (chain,resnum), via the SAME
    ShrakeRupley computation TASK-0257/TASK-0266 already validated."""
    from Bio import PDB
    structure = PDB.PDBParser(QUIET=True).get_structure("x", pdb_path)
    model = structure[0]
    per_atom_asa(model)
    burial = {}
    for chain in model:
        for resnum, asa in per_residue_native_asa(chain).items():
            res = chain[(" ", resnum, " ")] if (" ", resnum, " ") in chain else None
            resn3 = res.get_resname() if res is not None else None
            max_asa = MAX_ASA.get(resn3)
            if max_asa:
                rel = min(asa / max_asa, 1.5)  # clip absurd outliers, not silently truncate to 1.0
                burial[(chain.id, resnum)] = max(0.0, 1.0 - rel)
    return burial


def ligand_contact_flags(atoms_by_key, lig_xyz, keys):
    """Per-residue: does ANY of its heavy atoms sit within CONTACT_CUTOFF of
    ANY non-JUNK HETATM heavy atom? Identical definition to TASK-0329's own
    `ligand_contact_resnums` (same cutoff, same JUNK list), reshaped to a
    per-residue dict instead of one whole-structure boolean."""
    out = {}
    if len(lig_xyz) == 0:
        return {k: False for k in keys}
    for k in keys:
        atoms = atoms_by_key.get(k)
        if not atoms:
            out[k] = False
            continue
        a = np.asarray(atoms, float)
        d = np.sqrt(((a[:, None, :] - lig_xyz[None, :, :]) ** 2).sum(-1))
        out[k] = bool((d < CONTACT_CUTOFF).any())
    return out


def residualise(y_ranks, x_ranks):
    A = np.column_stack([x_ranks, np.ones_like(x_ranks)])
    coef, *_ = np.linalg.lstsq(A, y_ranks, rcond=None)
    return y_ranks - A @ coef


def cluster_sign_flip_test(deltas: dict, n_mc: int = 100_000, seed: int = 0):
    """Sign-flip permutation on per-protein deltas -- protein IS the
    cluster here, so this is TASK-0337's cluster-permutation convention
    applied directly, not a row-level test standing in for it."""
    vals = np.array(list(deltas.values()))
    n = len(vals)
    obs = float(vals.sum())
    if n == 0:
        return dict(n=0, statistic=None, p_value=None)
    if n <= 20:
        import itertools
        null = np.array([sum(s * v for s, v in zip(signs, vals))
                          for signs in itertools.product([1, -1], repeat=n)])
        exact = True
    else:
        rng = np.random.default_rng(seed)
        signs = rng.choice([1, -1], size=(n_mc, n))
        null = signs @ vals
        exact = False
    p = float(np.mean(np.abs(null) >= abs(obs) - 1e-12))
    return dict(n=n, statistic=obs, mean_delta=float(vals.mean()),
                median_delta=float(np.median(vals)), p_value=p, exact=exact)


def build_rows(log):
    """One row per (protein, residue) across BOTH active and allosteric
    sets, with resname/is_aromatic/burial/ligand_contact -- pooled table
    the rest of the analysis reads from."""
    rows = []
    n_fetch_fail = 0
    t0 = time.monotonic()
    max_entries = int(os.environ.get("MAX_ENTRIES", "0")) or None  # smoke-test knob
    entries = ANN[:max_entries] if max_entries else ANN
    for i, rec in enumerate(entries):
        pdb = rec["pdb"].split("_")[0]
        try:
            fp = fetch_bounded(pdb)
        except Exception as e:
            n_fetch_fail += 1
            log(f"  [{i+1}/{len(entries)}] {pdb:<8} FETCH FAILED: {e}")
            continue
        try:
            resname_by_key, atoms_by_key, lig_xyz = parse_structure(fp)
            burial = residue_burial(fp)
        except Exception as e:
            n_fetch_fail += 1
            log(f"  [{i+1}/{len(entries)}] {pdb:<8} PARSE FAILED: {type(e).__name__}: {e}")
            continue

        allo_keys, allo_resn = [], {}
        for t in rec["allosteric_residues"]:
            k, resn = pa(t)
            if k is None:
                continue
            allo_keys.append(k)
            allo_resn[k] = resn

        act_keys = []
        act_resn = {}
        for t in rec["active_residues"]:
            k = pact(t)
            if k is None:
                continue
            act_keys.append(k)
            resolved = resname_by_key.get(k)
            if resolved:
                act_resn[k] = resolved

        all_keys = sorted(set(allo_keys) | set(act_keys))
        contact = ligand_contact_flags(atoms_by_key, lig_xyz, all_keys)

        n_allo_used = n_act_used = 0
        for k in allo_keys:
            resn = allo_resn.get(k)
            b = burial.get(k)
            if resn is None or b is None:
                continue
            rows.append(dict(pdb=pdb, protein=rec["protein"], site="allosteric",
                              key=f"{k[0]}{k[1]}", resname=resn,
                              is_aromatic=int(resn in AROMATIC),
                              burial=b, ligand_contact=contact.get(k, False)))
            n_allo_used += 1
        for k in act_keys:
            resn = act_resn.get(k)
            b = burial.get(k)
            if resn is None or b is None:
                continue
            rows.append(dict(pdb=pdb, protein=rec["protein"], site="active",
                              key=f"{k[0]}{k[1]}", resname=resn,
                              is_aromatic=int(resn in AROMATIC),
                              burial=b, ligand_contact=contact.get(k, False)))
            n_act_used += 1

        if (i + 1) % 15 == 0:
            log(f"  [{i+1}/{len(entries)}] {pdb:<8} allo={n_allo_used}/{len(allo_keys)} "
                f"act={n_act_used}/{len(act_keys)} ({time.monotonic()-t0:.0f}s)")

    log(f"done: {len(rows)} residue-rows, {n_fetch_fail} structures failed to fetch/parse "
        f"({time.monotonic()-t0:.0f}s total)")
    return rows


def raw_reproduction(rows):
    """Planned Validation: reproduce the reviewer's own 15.7% vs ~10.2%
    before trusting anything built on top of this cohort."""
    allo = [r for r in rows if r["site"] == "allosteric"]
    act = [r for r in rows if r["site"] == "active"]
    allo_frac = float(np.mean([r["is_aromatic"] for r in allo])) if allo else None
    act_frac = float(np.mean([r["is_aromatic"] for r in act])) if act else None
    return dict(n_allo=len(allo), n_act=len(act), allo_aromatic_frac=allo_frac,
                act_aromatic_frac=act_frac,
                ratio=(allo_frac / act_frac) if (allo_frac and act_frac) else None)


def run_stratum(rows, label, log):
    """Rank-residualise is_aromatic on burial (pooled), then the per-protein
    paired (allosteric - active) delta on the residual, cluster-tested."""
    if not rows:
        log(f"  [{label}] no rows")
        return None
    y = np.array([r["is_aromatic"] for r in rows], float)
    x = np.array([r["burial"] for r in rows], float)
    if np.ptp(x) == 0 or np.ptp(y) == 0:
        log(f"  [{label}] degenerate (n={len(rows)}), skipped")
        return dict(n=len(rows), degenerate=True)
    ry, rx = rankdata(y), rankdata(x)
    resid = residualise(ry, rx)
    for r, res in zip(rows, resid):
        r["_resid"] = float(res)

    by_protein_site = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by_protein_site[r["protein"]][r["site"]].append(r["_resid"])

    deltas = {}
    for prot, sites in by_protein_site.items():
        if "allosteric" in sites and "active" in sites:
            deltas[prot] = float(np.mean(sites["allosteric"]) - np.mean(sites["active"]))

    cl = cluster_sign_flip_test(deltas)
    raw_allo = np.mean([r["is_aromatic"] for r in rows if r["site"] == "allosteric"]) \
        if any(r["site"] == "allosteric" for r in rows) else None
    raw_act = np.mean([r["is_aromatic"] for r in rows if r["site"] == "active"]) \
        if any(r["site"] == "active" for r in rows) else None
    out = dict(n_rows=len(rows), n_proteins_paired=cl["n"],
               raw_allo_aromatic_frac=float(raw_allo) if raw_allo is not None else None,
               raw_act_aromatic_frac=float(raw_act) if raw_act is not None else None,
               **cl)
    log(f"  [{label}] n_rows={out['n_rows']} n_proteins={cl['n']} "
        f"raw_allo={out['raw_allo_aromatic_frac']} raw_act={out['raw_act_aromatic_frac']} "
        f"mean_resid_delta={cl.get('mean_delta')} p={cl.get('p_value')}"
        f"{' (exact)' if cl.get('exact') else ' (Monte Carlo)'}")
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    def log(msg):
        print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

    log(f"{len(ANN)} ASBench entries")
    rows = build_rows(log)

    log("\n### Planned Validation: reproduce the reviewer's own raw numbers ###")
    raw = raw_reproduction(rows)
    log(f"  allosteric aromatic frac = {raw['allo_aromatic_frac']:.4f} (reviewer: 0.157)")
    log(f"  active-site aromatic frac = {raw['act_aromatic_frac']:.4f} (reviewer background: ~0.102)")
    log(f"  ratio = {raw['ratio']:.3f} (reviewer: 1.54)")

    log("\n### Burial-residualised, paired within-protein, ALL residues ###")
    all_result = run_stratum(rows, "all", log)

    log("\n### Ligand-contact stratum ###")
    contact_rows = [r for r in rows if r["ligand_contact"]]
    contact_result = run_stratum(contact_rows, "ligand-contacting", log)

    log("\n### Non-contact stratum ###")
    noncontact_rows = [r for r in rows if not r["ligand_contact"]]
    noncontact_result = run_stratum(noncontact_rows, "non-contacting", log)

    out = dict(
        n_entries=len(ANN),
        planned_validation_raw_reproduction=raw,
        all_residues=all_result,
        ligand_contacting_stratum=contact_result,
        non_contacting_stratum=noncontact_result,
    )
    (OUT / "aromatic_enrichment_gate.json").write_text(json.dumps(out, indent=1, default=str))
    (OUT / "rows.json").write_text(json.dumps(rows, default=str))
    log(f"\nWrote {OUT}/aromatic_enrichment_gate.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
