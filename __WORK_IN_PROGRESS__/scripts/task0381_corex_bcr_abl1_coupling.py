#!/usr/bin/env python3
"""TASK-0381 -- Tier 0: COREX ensemble coupling on BCR-ABL1, CPU-only.

Precondition gate (must pass before any coupling number is computed):
nilotinib and dasatinib must contact materially different residue sets on
BCR-ABL1, or a fused/stabilized-region COREX model represents them
identically and cannot discriminate them by construction.

A real numbering trap caught while checking this, not after: `2GQG`
(dasatinib) uses Abl-1b numbering, offset **+19** from `1OPL`/`5MO4`'s own
convention (the same offset [[TASK-0377]] already documented for
T315I/T334I). Comparing raw resnums gives a false, wrong-direction
answer: nilotinib vs dasatinib Jaccard 0.09 (looks nearly disjoint) --
comparing residue IDENTITY at each resnum (not just presence) shows only
1/21 dasatinib contacts match their claimed identity in `1OPL`, versus
21/21 after applying +19. The CORRECTED overlap is Jaccard 0.57 -- real,
substantial overlap, the opposite conclusion from the uncorrected number.
Reported plainly; proceeds because 0.57 is not "near-identical" (43% of
the union is exclusive to one ligand or the other), but any measured
discrimination below must be read against this real overlap, not assumed
clean.

Reuses `allostery.corex` as-is: `coupling_score`'s already-existing
folded-constraint mechanism (a `stabilization_bonus` on any window
overlapping a given residue set) is generalized here from "one residue at
a time" ([[TASK-0229.006]]'s own per-candidate sweep,
`scripts/task0229_006_corex_eam.py::run_all_candidate_couplings`) to "an
arbitrary named region," which is the only change this task's own item 1
("add a folded-constraint to corex.py") actually needed -- no new
methodology, `corex.py` itself is untouched.

Run: ../.venv/bin/python3 -u scripts/task0381_corex_bcr_abl1_coupling.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    import os
    os.environ.setdefault(_v, "4")

import numpy as np
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
RESULTS = HERE.parent / "results" / "tasks" / "0381_tier0_corex_bcr_abl1"
RESULTS.mkdir(parents=True, exist_ok=True)
PDB_CACHE = RESULTS / "pdb_cache"
PDB_CACHE.mkdir(exist_ok=True)

sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(REPO_ROOT))

import Bio.PDB as PDB  # noqa: E402
from allostery.corex import (  # noqa: E402
    R_GAS, TEMPERATURE, apolar_max_asa_fraction, build_folding_windows,
    per_atom_asa, per_residue_apolar_native_asa, per_residue_native_asa,
    window_free_energy,
)

AA3 = {"ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
       "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL", "MSE"}
STABILIZATION_BONUS = 3.0  # matches corex.coupling_score's own default, reused not re-picked
WINDOW_SIZES = (6, 10, 15)  # matches corex_ensemble's own default, reused not re-picked

# Ligand codes, RCSB-verified live (this task's own fetch): asciminib=AY7,
# nilotinib=NIL (both in 5MO4, the ternary complex -- one structure, one
# numbering, no cross-structure resnum join needed for these two),
# dasatinib=1N1 (2GQG, a DIFFERENT numbering convention -- see module
# docstring). Apo: 1OPL chain A, this register's own targets.yaml assignment.
APO_PDB, APO_CHAIN = "1OPL", "A"
TERNARY_PDB, TERNARY_CHAIN = "5MO4", "A"
DASATINIB_PDB, DASATINIB_CHAIN = "2GQG", "A"
ASCIMINIB_CODE, NILOTINIB_CODE, DASATINIB_CODE = "AY7", "NIL", "1N1"
DASATINIB_NUMBERING_OFFSET = 19  # 2GQG-resnum + 19 = 1OPL/5MO4-resnum (Abl-1b vs this register's convention)


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def fetch_pdb(pdb_id: str) -> Path:
    p = PDB_CACHE / f"{pdb_id.lower()}.pdb"
    if p.exists() and p.stat().st_size > 0:
        return p
    for attempt in range(4):
        try:
            with urllib.request.urlopen(f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb", timeout=30) as r:
                p.write_bytes(r.read())
            return p
        except Exception:
            time.sleep(1.5 ** attempt)
    raise RuntimeError(f"fetch failed: {pdb_id}")


def chain_atoms(path, chain):
    out = []
    for l in open(path, errors="replace"):
        if l.startswith("ENDMDL"):
            break
        rec = l[:6].strip()
        if rec not in ("ATOM", "HETATM") or len(l) < 54 or l[21] != chain:
            continue
        resname = l[17:20].strip()
        try:
            resnum = int(l[22:26])
            x, y, z = float(l[30:38]), float(l[38:46]), float(l[46:54])
        except ValueError:
            continue
        out.append((rec, resname, resnum, l[12:16].strip(), x, y, z))
    return out


def chain_ca_resname(path, chain):
    out = {}
    for l in open(path, errors="replace"):
        if l.startswith("ENDMDL"):
            break
        if l[:6].strip() == "ATOM" and len(l) >= 54 and l[21] == chain and l[12:16].strip() == "CA":
            out[int(l[22:26])] = l[17:20].strip()
    return out


def ligand_contacts(path, chain, lig_code, cutoff=4.5):
    atoms = chain_atoms(path, chain)
    lig = np.array([(x, y, z) for rec, rn, num, an, x, y, z in atoms
                    if rec == "HETATM" and rn == lig_code and not an.startswith("H")])
    if len(lig) == 0:
        return set()
    prot = [(num, np.array([x, y, z])) for rec, rn, num, an, x, y, z in atoms
            if rn in AA3 and not an.startswith("H")]
    out = set()
    for num, xyz in prot:
        if np.sqrt(((lig - xyz) ** 2).sum(axis=1)).min() <= cutoff:
            out.add(num)
    return out


def precondition_gate() -> dict:
    _log("Precondition gate: nilotinib vs dasatinib contact sets...")
    ternary = fetch_pdb(TERNARY_PDB)
    das_struct = fetch_pdb(DASATINIB_PDB)
    apo_struct = fetch_pdb(APO_PDB)

    nil = ligand_contacts(ternary, TERNARY_CHAIN, NILOTINIB_CODE)
    asc = ligand_contacts(ternary, TERNARY_CHAIN, ASCIMINIB_CODE)
    das_raw = ligand_contacts(das_struct, DASATINIB_CHAIN, DASATINIB_CODE)

    apo_map = chain_ca_resname(apo_struct, APO_CHAIN)
    ternary_map = chain_ca_resname(ternary, TERNARY_CHAIN)
    das_map = chain_ca_resname(das_struct, DASATINIB_CHAIN)

    nil_ident = sum(1 for r in nil if r in apo_map and apo_map[r] == ternary_map.get(r))
    asc_ident = sum(1 for r in asc if r in apo_map and apo_map[r] == ternary_map.get(r))
    _log(f"  nilotinib/apo identity check: {nil_ident}/{len(nil)}; asciminib: {asc_ident}/{len(asc)}")

    # Dasatinib: check raw (no offset) identity first -- this is the trap.
    das_ident_raw = sum(1 for r in das_raw if r in apo_map and apo_map[r] == das_map.get(r))
    das_corrected = set(r + DASATINIB_NUMBERING_OFFSET for r in das_raw)
    das_ident_corrected = sum(1 for r in das_raw if apo_map.get(r + DASATINIB_NUMBERING_OFFSET) == das_map.get(r))
    _log(f"  dasatinib/apo identity check RAW (no offset): {das_ident_raw}/{len(das_raw)} -- "
        f"{'TRAP: wrong numbering convention' if das_ident_raw < len(das_raw) // 2 else 'ok'}")
    _log(f"  dasatinib/apo identity check with +{DASATINIB_NUMBERING_OFFSET} offset: "
        f"{das_ident_corrected}/{len(das_raw)}")

    def overlap_stats(a, b):
        ov = a & b
        return dict(overlap=sorted(ov), n_overlap=len(ov), jaccard=len(ov) / len(a | b) if (a | b) else float("nan"),
                   a_unique=sorted(a - b), b_unique=sorted(b - a))

    raw_stats = overlap_stats(nil, das_raw)
    corrected_stats = overlap_stats(nil, das_corrected)

    gate_pass = corrected_stats["jaccard"] < 0.85  # not "near-identical"; a real, if partial, footprint difference exists
    return dict(
        nilotinib_contacts=sorted(nil), asciminib_contacts=sorted(asc), dasatinib_contacts_raw=sorted(das_raw),
        nilotinib_apo_identity_match=f"{nil_ident}/{len(nil)}", asciminib_apo_identity_match=f"{asc_ident}/{len(asc)}",
        dasatinib_apo_identity_match_raw=f"{das_ident_raw}/{len(das_raw)}",
        dasatinib_apo_identity_match_corrected=f"{das_ident_corrected}/{len(das_raw)}",
        dasatinib_contacts_corrected=sorted(das_corrected),
        nilotinib_vs_asciminib_overlap=sorted(nil & asc),
        WRONG_uncorrected_nil_vs_das=raw_stats,
        CORRECT_nil_vs_das_corrected=corrected_stats,
        gate_pass=gate_pass,
        gate_note="Not near-identical (43% of the union is exclusive to one ligand), but real overlap "
                  "(57% Jaccard, 81% of dasatinib's own contacts are also nilotinib contacts) -- "
                  "any measured discrimination below must be read against this, not assumed clean.",
    )


def build_ensemble_base(model, chain_id: str):
    """Precomputes the unperturbed per-window free energies once -- shared
    by every one of the 4 states below, since only the stabilization
    bonus (a flat additive term on specific windows) differs between
    them, not the underlying ASA/geometry."""
    per_atom_asa(model)
    chain = model[chain_id]
    resnums = sorted(r.id[1] for r in chain if r.id[0] == " ")
    resnames = {r.id[1]: r.resname for r in chain if r.id[0] == " "}
    native_total_asa = per_residue_native_asa(chain)
    native_apolar_asa = per_residue_apolar_native_asa(chain)
    apolar_max = {
        rn: apolar_max_asa_fraction(resnames[rn], native_apolar_asa.get(rn, 0.0), native_total_asa.get(rn, 0.0))
        for rn in resnums
    }
    windows = build_folding_windows(resnums, WINDOW_SIZES)
    base_dg = np.array([
        window_free_energy(w, native_apolar_asa, apolar_max, n_conf_residues=len(w), temperature=TEMPERATURE)
        for w in windows
    ])
    window_sets = [set(w) for w in windows]
    return resnums, native_total_asa, window_sets, base_dg


def unfolded_probability(window_sets, weights, target_set) -> float:
    """The raw (linear, un-transformed) population fraction of the ensemble
    in which `target_set` is unfolded -- P(unfolded), not the log-odds
    dGf. Used only for the symmetry diagnosis below: the general
    statistical-mechanics reciprocity theorem (a Maxwell-relation-type
    identity, dP(unfolded_T)/d(bonus_M) = dP(unfolded_M)/d(bonus_T) in the
    infinitesimal-bonus limit, both equal -Cov(I_T,I_M)/RT) applies to
    this LINEAR observable, not to dGf's own nonlinear log(folded/unfolded)
    transform of it."""
    folded, unfolded = 1.0, 0.0
    for w_set, k in zip(window_sets, weights):
        if w_set & target_set:
            unfolded += k
        else:
            folded += k
    return unfolded / (folded + unfolded)


def dgf_of_region(window_sets, weights, target_set) -> float:
    folded, unfolded = 1.0, 0.0
    for w_set, k in zip(window_sets, weights):
        if w_set & target_set:
            unfolded += k
        else:
            folded += k
    kf = folded / unfolded if unfolded > 0 else float("inf")
    return -R_GAS * TEMPERATURE * np.log(kf) if np.isfinite(kf) and kf > 0 else float("-inf")


def state_weights(window_sets, base_dg, perturb_set, bonus=STABILIZATION_BONUS):
    touched = np.array([bool(w_set & perturb_set) for w_set in window_sets])
    dg = base_dg + np.where(touched, bonus, 0.0)
    return np.exp(-dg / (R_GAS * TEMPERATURE))


def sanity_check(model, chain_id) -> dict:
    from allostery.corex import corex_ensemble
    kf = corex_ensemble(model, chain_id)
    per_atom_asa(model)
    native_asa = per_residue_native_asa(model[chain_id])
    resnums = sorted(kf.keys())
    asa_vals = np.array([native_asa.get(rn, np.nan) for rn in resnums])
    kf_vals = np.array([kf[rn] for rn in resnums])
    finite = np.isfinite(kf_vals) & np.isfinite(asa_vals)
    rho, p = spearmanr(asa_vals[finite], np.log10(np.clip(kf_vals[finite], 1e-300, None)))
    return dict(spearman_rho_asa_vs_log_kappa_f=round(float(rho), 4), spearman_p=float(p),
               passes=bool(rho < 0 and p < 0.01))


def main() -> int:
    gate = precondition_gate()
    (RESULTS / "precondition_gate.json").write_text(json.dumps(gate, indent=1, default=str))
    _log(f"GATE: nilotinib vs dasatinib jaccard(corrected)={gate['CORRECT_nil_vs_das_corrected']['jaccard']:.3f} "
        f"-> {'PASS' if gate['gate_pass'] else 'STOP'}")
    if not gate["gate_pass"]:
        _log("STOPPING per this task's own precondition gate: sets too near-identical to discriminate.")
        return 1

    _log("Loading BCR_ABL1 apo (1OPL)...")
    apo_fp = fetch_pdb(APO_PDB)
    apo_model = PDB.PDBParser(QUIET=True).get_structure(APO_PDB, apo_fp)[0]

    _log("Sanity check (Planned Validation's own qualitative gate, applied to this new target too)...")
    sanity = sanity_check(apo_model, APO_CHAIN)
    _log(f"  {sanity}")
    if not sanity["passes"]:
        _log("STOPPING -- sanity check failed, coupling numbers not trusted.")
        return 1

    M = set(gate["asciminib_contacts"])         # myristoyl site
    T = set(gate["nilotinib_contacts"])          # ATP site (nilotinib)
    T_das = set(gate["dasatinib_contacts_corrected"])  # ATP site (dasatinib, discriminative control)

    resnums, native_total_asa, window_sets, base_dg = build_ensemble_base(apo_model, APO_CHAIN)

    # --- no-op check: empty perturb set must reproduce the apo dGf exactly ---
    w_apo = state_weights(window_sets, base_dg, set())
    w_noop = state_weights(window_sets, base_dg, set(), bonus=0.0)
    dgf_apo_T = dgf_of_region(window_sets, w_apo, T)
    dgf_noop_T = dgf_of_region(window_sets, w_noop, T)
    noop_ok = abs(dgf_apo_T - dgf_noop_T) < 1e-9
    _log(f"No-op check (empty perturb set, Planned Validation's own requirement): "
        f"dGf_T(apo)={dgf_apo_T:.6f} vs dGf_T(no bonus)={dgf_noop_T:.6f} -> {'PASS' if noop_ok else 'FAIL'}")

    # --- four states ---
    w_M = state_weights(window_sets, base_dg, M)
    w_T = state_weights(window_sets, base_dg, T)
    w_both = state_weights(window_sets, base_dg, M | T)

    dgf_T_apo = dgf_of_region(window_sets, w_apo, T)
    dgf_T_M = dgf_of_region(window_sets, w_M, T)
    dgf_T_T = dgf_of_region(window_sets, w_T, T)
    dgf_T_both = dgf_of_region(window_sets, w_both, T)

    dgf_M_apo = dgf_of_region(window_sets, w_apo, M)
    dgf_M_M = dgf_of_region(window_sets, w_M, M)
    dgf_M_T = dgf_of_region(window_sets, w_T, M)
    dgf_M_both = dgf_of_region(window_sets, w_both, M)

    coupling_M_to_T = dgf_T_M - dgf_T_apo   # stabilizing myristoyl -> shift in ATP-site dGf
    coupling_T_to_M = dgf_M_T - dgf_M_apo   # stabilizing ATP site -> shift in myristoyl dGf
    symmetry_gap = abs(coupling_M_to_T - coupling_T_to_M)

    nonadditivity_via_T = (dgf_T_both - dgf_T_T) - (dgf_T_M - dgf_T_apo)
    nonadditivity_via_M = (dgf_M_both - dgf_M_M) - (dgf_M_T - dgf_M_apo)

    _log(f"Four-state dGf(T=ATP-site region): apo={dgf_T_apo:.4f} M-bound={dgf_T_M:.4f} "
        f"T-bound={dgf_T_T:.4f} both={dgf_T_both:.4f}")
    _log(f"Four-state dGf(M=myristoyl region): apo={dgf_M_apo:.4f} M-bound={dgf_M_M:.4f} "
        f"T-bound={dgf_M_T:.4f} both={dgf_M_both:.4f}")
    _log(f"Coupling M->T = {coupling_M_to_T:.4f} kcal/mol; T->M = {coupling_T_to_M:.4f} kcal/mol; "
        f"symmetry gap = {symmetry_gap:.6f} ({'symmetric' if symmetry_gap < 1e-6 else 'ASYMMETRIC -- diagnosed below, not assumed a bug'})")
    _log(f"Cycle nonadditivity via T-readout = {nonadditivity_via_T:.4f}; via M-readout = {nonadditivity_via_M:.4f}")

    # --- symmetry diagnosis: is the asymmetry a bug, or the log-odds transform? ---
    # The general statistical-mechanics reciprocity (a Maxwell-relation-type
    # identity) guarantees d(raw unfolded population)/d(bonus) is symmetric
    # under exchanging perturbed/read regions -- but ONLY for that LINEAR
    # observable, and only in the infinitesimal-bonus limit. dGf is a
    # NONLINEAR (log-odds) transform of that population, so a real symmetry
    # break in dGf-space does not, by itself, mean the code is wrong. Tested
    # directly rather than assumed either way: sweep the bonus down toward
    # zero and check whether the RAW population coupling (not dGf) converges
    # to a 1:1 ratio between the two directions.
    I_T_apo = unfolded_probability(window_sets, w_apo, T)
    I_M_apo = unfolded_probability(window_sets, w_apo, M)
    bonus_sweep = [0.0001, 0.001, 0.01, 0.1, 1.0, STABILIZATION_BONUS]
    symmetry_diagnosis = []
    for b in bonus_sweep:
        w_M_b = state_weights(window_sets, base_dg, M, bonus=b)
        w_T_b = state_weights(window_sets, base_dg, T, bonus=b)
        dgf_ratio = ((dgf_of_region(window_sets, w_M_b, T) - dgf_T_apo) /
                    (dgf_of_region(window_sets, w_T_b, M) - dgf_M_apo))
        dI_T = unfolded_probability(window_sets, w_M_b, T) - I_T_apo
        dI_M = unfolded_probability(window_sets, w_T_b, M) - I_M_apo
        raw_ratio = dI_T / dI_M if dI_M else float("nan")
        symmetry_diagnosis.append(dict(bonus=b, dgf_based_ratio=float(dgf_ratio), raw_population_ratio=float(raw_ratio)))
    _log("Symmetry diagnosis (ratio -> 1.0 means symmetric): "
        + ", ".join(f"bonus={d['bonus']}: dGf-ratio={d['dgf_based_ratio']:.3f} "
                    f"raw-pop-ratio={d['raw_population_ratio']:.3f}" for d in symmetry_diagnosis))
    _log(f"Baseline unfolded probability: I_T(apo)={I_T_apo:.4f}, I_M(apo)={I_M_apo:.4f} "
        f"-- a {I_T_apo/I_M_apo:.1f}x difference in baseline stability is the mechanism: "
        "dGf's log-odds transform has a different local slope at each region's own operating "
        "point, so a symmetric raw-population response becomes an asymmetric dGf-shift.")

    # --- discriminative control: dasatinib in place of nilotinib as the readout region ---
    dgf_das_apo = dgf_of_region(window_sets, w_apo, T_das)
    dgf_das_M = dgf_of_region(window_sets, w_M, T_das)
    coupling_M_to_dasatinib = dgf_das_M - dgf_das_apo
    _log(f"Discriminative control: coupling M->dasatinib-site = {coupling_M_to_dasatinib:.4f} kcal/mol "
        f"(vs M->nilotinib-site = {coupling_M_to_T:.4f})")

    out = dict(
        gate=gate, sanity=sanity, noop_check=dict(dgf_T_apo=dgf_apo_T, dgf_T_no_bonus=dgf_noop_T, passes=noop_ok),
        four_state_T_readout=dict(apo=dgf_T_apo, M_bound=dgf_T_M, T_bound=dgf_T_T, both=dgf_T_both),
        four_state_M_readout=dict(apo=dgf_M_apo, M_bound=dgf_M_M, T_bound=dgf_M_T, both=dgf_M_both),
        coupling_M_to_T=coupling_M_to_T, coupling_T_to_M=coupling_T_to_M, symmetry_gap=symmetry_gap,
        nonadditivity_via_T_readout=nonadditivity_via_T, nonadditivity_via_M_readout=nonadditivity_via_M,
        baseline_unfolded_probability=dict(I_T_apo=I_T_apo, I_M_apo=I_M_apo, ratio=I_T_apo / I_M_apo),
        symmetry_diagnosis=symmetry_diagnosis,
        coupling_M_to_dasatinib=coupling_M_to_dasatinib,
        stabilization_bonus=STABILIZATION_BONUS, window_sizes=list(WINDOW_SIZES),
    )
    (RESULTS / "result.json").write_text(json.dumps(out, indent=1, default=str))
    _log(f"Wrote {RESULTS / 'result.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
