#!/usr/bin/env python3
"""TASK-0257, rung R1 -- heavy-atom contact weighting, Cα nodes retained.

Replaces the binary Cα-cutoff contact matrix (`hamiltonians.contact_matrix`,
`weight="binary"`, used by every GNM/ANM quantity in this register) with an
edge weight equal to the COUNT of heavy-atom pairs between the two residues
within a contact distance -- same N (one node per residue), same downstream
shape, only the edge weights change. Scored against [[TASK-0250]]'s own
pre-registered, label-free objective: GNM MSF (diagonal of the Kirchhoff
pseudo-inverse) vs. real deposited B-factors, same 15 targets, same
PASS(>=0.6)/MARGINAL(0.4-0.6)/FAIL(<0.4) bars, so the comparison is
like-for-like.

Reuses, does not re-derive:
  - [[TASK-0250]]'s own target list, pass bars, unusable-B-factor flag
    (CARDIAC_MYOSIN_TABLE1's 5TBY, 20 A cryo-EM, no per-atom B).
  - `allostery.hamiltonians.laplacian` for the Laplacian -> eigh ->
    pseudo-inverse -> MSF pipeline (identical math to `potentials._gnm_msf`,
    only the input adjacency matrix `A` differs).
  - [[TASK-0255]]'s own fix for `allostery.labels.
    protein_heavy_atoms_by_residue`'s multi-chain resnum collision -- the
    (chain, resnum)-keyed heavy-atom loader, reused verbatim (not re-derived
    a third time) since R1 needs exactly the same per-residue heavy-atom
    coordinate set TASK-0255 needed for its own distance calibration.

Heavy-atom contact distance: 4.5 A, this project's own established
convention for heavy-atom contacts (`pocket_contact_cutoff: 4.5` used
uniformly across `targets.yaml` for every ligand-contact pocket-label
derivation) -- not a new number invented for this task.

Uses `scipy.spatial.cKDTree.query_pairs` for the heavy-atom neighbour
search rather than a dense atom-atom distance matrix: the largest target
here (GAC_BPTES-scale N~1200, ~8 heavy atoms/residue -> ~9600 atoms) would
need a dense atom-atom matrix of the same order [[TASK-0257]]'s own R4
feasibility note flags (~93M floats, ~744 MB) -- a KD-tree avoids paying
that cost for a rung that is supposed to be the cheapest on the ladder.
[[TASK-0204]]'s 300 GB memory incident is exactly the failure mode this
choice avoids, per this task's own R5 warning about doing the projected-
cost check before the first run, not after.

Run: ../.venv/bin/python3 scripts/task0257_r1_heavy_atom_contact_weighting.py
"""
from __future__ import annotations

import json
import resource
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
from scipy.spatial import cKDTree
from scipy.stats import pearsonr, spearmanr

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import prody  # noqa: E402

prody.confProDy(verbosity="none")

# TASK-0039/TASK-0243's own established fix, reused defensively (some of
# these 15 targets have not been checked for altloc issues before; this
# has zero regressions on targets that don't need it).
_orig_parsePDB = prody.parsePDB


def _parsePDB_all_altloc(*a, **kw):
    kw.setdefault("altloc", "all")
    return _orig_parsePDB(*a, **kw)


prody.parsePDB = _parsePDB_all_altloc

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.hamiltonians import laplacian  # noqa: E402
from allostery.potentials import _gnm_msf  # noqa: E402

# TASK-0250's own list, bars, and unusable-B-factor flag -- reused verbatim.
TARGETS = [
    "KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "CARDIAC_MYOSIN_TABLE1",
    "MYC_MAX", "PTP1B", "GLUCOKINASE", "ATCase", "CASPASE1", "CASPASE7",
    "HEMOGLOBIN", "TAR_RECEPTOR", "GLYCOGEN_PHOSPHORYLASE", "PFK", "GROEL_SUBUNIT",
]
UNUSABLE_BFACTORS = {
    "CARDIAC_MYOSIN_TABLE1": (
        "apo 5TBY is ELECTRON MICROSCOPY, nominal resolution 20.0 A -- "
        "no meaningful per-atom B-factor refinement; excluded from the "
        "pass/fail tally, reported for transparency only (same exclusion "
        "TASK-0250 applied)."
    ),
}
PASS_BAR = 0.6
MARGINAL_BAR = 0.4
HEAVY_ATOM_CONTACT_A = 4.5  # this project's own established pocket_contact_cutoff


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def verdict(pearson: float) -> str:
    if pearson >= PASS_BAR:
        return "PASS"
    if pearson >= MARGINAL_BAR:
        return "MARGINAL"
    return "FAIL"


def heavy_atoms_keyed_by_chain_resnum(cfg: dict, apo):
    """TASK-0255's own fix, reused verbatim: `allostery.labels.
    protein_heavy_atoms_by_residue`'s bare-resnum dict silently collapses
    same-numbered residues across chains in a multi-chain target. Keyed on
    (chain, resnum) instead -- the only thing that differs from that
    helper; same heavy-atom selection, same coordinates.
    """
    resn = np.asarray(apo.resnums)
    chids = np.asarray(apo.chain_ids)
    # `allostery.clean.clean_from_config` (`clean()`'s own documented
    # contract, clean.py:94-95): chains=None means "all protein chains",
    # not an error -- ATCase/HEMOGLOBIN/TAR_RECEPTOR/GLYCOGEN_PHOSPHORYLASE/
    # PFK/GROEL_SUBUNIT all set `chains: null` deliberately (unresolved
    # assembly, per targets.yaml's own "VERIFY" comments), and
    # `clean_from_config` already succeeded loading `apo` under that same
    # convention -- matched here rather than treated as a missing value.
    apo_ch = cfg.get("apo_chains") or cfg.get("chains")
    sel = "protein" if not apo_ch else "protein and (" + " or ".join(f"chain {c}" for c in apo_ch) + ")"
    ag = prody.parsePDB(cfg["apo_pdb"], compressed=False).select(sel)
    if ag is None:
        return np.zeros((0, 3)), np.zeros(0, dtype=int)
    key_to_seq = {(str(c), int(r)): i for i, (c, r) in enumerate(zip(chids, resn))}
    atom_resnums = ag.getResnums()
    atom_chids = ag.getChids()
    heavy_seq = np.array(
        [key_to_seq.get((str(c), int(r)), -1) for c, r in zip(atom_chids, atom_resnums)],
        dtype=int,
    )
    keep = heavy_seq >= 0
    return ag.getCoords()[keep], heavy_seq[keep]


def heavy_atom_contact_count_matrix(
    heavy_coords: np.ndarray, heavy_seq: np.ndarray, n_residues: int,
    contact_dist: float = HEAVY_ATOM_CONTACT_A,
) -> np.ndarray:
    """(N, N) matrix: A[i, j] = count of heavy-atom pairs (one atom in
    residue i, one in residue j) within `contact_dist` -- replaces the
    binary Cα-cutoff adjacency. Symmetric, zero diagonal (self-contacts
    excluded, matching `contact_matrix`'s own `dist > 0` convention).
    """
    A = np.zeros((n_residues, n_residues))
    if len(heavy_coords) == 0:
        return A
    tree = cKDTree(heavy_coords)
    pairs = tree.query_pairs(r=contact_dist, output_type="ndarray")
    if len(pairs) == 0:
        return A
    ri = heavy_seq[pairs[:, 0]]
    rj = heavy_seq[pairs[:, 1]]
    inter = ri != rj
    ri, rj = ri[inter], rj[inter]
    np.add.at(A, (ri, rj), 1.0)
    np.add.at(A, (rj, ri), 1.0)
    return A


def msf_from_adjacency(A: np.ndarray) -> np.ndarray:
    """Same Laplacian -> eigh -> pseudo-inverse -> MSF pipeline
    `potentials._kirchhoff_eigh`/`_gnm_msf` use, generalised to an
    arbitrary weighted adjacency matrix instead of only the binary one."""
    K = laplacian(A)
    w, U = np.linalg.eigh(K)
    nz = w > 1e-9
    winv = np.where(nz, 1.0 / np.where(nz, w, 1.0), 0.0)
    return np.diag((U * winv) @ U.T)


def compute_target(target_name: str) -> dict:
    t0 = time.monotonic()
    cfg = load_target_config(target_name)
    apo = clean_from_config(target_name, role="apo")
    coords = apo.coords.astype(float)
    bfactors = apo.bfactors
    n = len(coords)

    heavy_coords, heavy_seq = heavy_atoms_keyed_by_chain_resnum(cfg, apo)
    n_heavy_mapped = int(np.isin(np.arange(n), np.unique(heavy_seq)).sum())
    A_r1 = heavy_atom_contact_count_matrix(heavy_coords, heavy_seq, n)
    msf_r1 = msf_from_adjacency(A_r1)

    cutoff = float(cfg["enm_cutoff"])
    msf_baseline = _gnm_msf(coords, cutoff)

    valid = ~np.isnan(bfactors)
    pear_r1, p_r1 = pearsonr(msf_r1[valid], bfactors[valid])
    sp_r1, _ = spearmanr(msf_r1[valid], bfactors[valid])
    pear_base, p_base = pearsonr(msf_baseline[valid], bfactors[valid])
    sp_base, _ = spearmanr(msf_baseline[valid], bfactors[valid])

    peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024.0 if sys.platform == "darwin" else 1.0) / 1024.0
    elapsed = time.monotonic() - t0

    result = dict(
        target=target_name, apo_pdb=cfg["apo_pdb"], N=n,
        n_residues_with_heavy_atoms=n_heavy_mapped,
        mean_degree_r1=float(A_r1.sum(axis=1).mean()),
        pearson_r1=float(pear_r1), pearson_p_r1=float(p_r1),
        spearman_r1=float(sp_r1),
        verdict_r1=verdict(float(pear_r1)),
        pearson_baseline=float(pear_base), spearman_baseline=float(sp_base),
        verdict_baseline=verdict(float(pear_base)),
        delta_pearson=float(pear_r1 - pear_base),
        unusable_reason=UNUSABLE_BFACTORS.get(target_name),
        elapsed_s=round(elapsed, 2), peak_rss_mb=round(peak_mb, 1),
    )
    flag = " [UNUSABLE B-FACTORS]" if target_name in UNUSABLE_BFACTORS else ""
    _log(f"{target_name} ({cfg['apo_pdb']}, N={n}, heavy-mapped={n_heavy_mapped}): "
         f"R1 Pearson={pear_r1:.3f} ({result['verdict_r1']})  "
         f"baseline={pear_base:.3f} ({result['verdict_baseline']})  "
         f"delta={result['delta_pearson']:+.3f}  [{elapsed:.1f}s]{flag}")
    return result


def main() -> int:
    results = []
    for name in TARGETS:
        results.append(compute_target(name))

    out_dir = _ROOT / "results" / "tasks" / "0257_r1_heavy_atom_contact_weighting"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "r1_results.json"
    json.dump(
        dict(pass_bar=PASS_BAR, marginal_bar=MARGINAL_BAR,
             heavy_atom_contact_A=HEAVY_ATOM_CONTACT_A, results=results),
        open(out_path, "w"), indent=1,
    )
    _log(f"wrote {out_path}")

    scored = [r for r in results if r["unusable_reason"] is None]
    print(f"\n{'target':24s} {'N':>5s} {'R1 Pearson':>11s} {'R1':>10s} "
          f"{'base Pearson':>13s} {'base':>10s} {'delta':>8s}")
    print("-" * 90)
    for r in results:
        flag = " *UNUSABLE*" if r["unusable_reason"] else ""
        print(f"{r['target']:24s} {r['N']:5d} {r['pearson_r1']:11.3f} {r['verdict_r1']:>10s} "
              f"{r['pearson_baseline']:13.3f} {r['verdict_baseline']:>10s} "
              f"{r['delta_pearson']:+8.3f}{flag}")

    n_pass_r1 = sum(1 for r in scored if r["verdict_r1"] == "PASS")
    n_marg_r1 = sum(1 for r in scored if r["verdict_r1"] == "MARGINAL")
    n_fail_r1 = sum(1 for r in scored if r["verdict_r1"] == "FAIL")
    n_pass_b = sum(1 for r in scored if r["verdict_baseline"] == "PASS")
    n_marg_b = sum(1 for r in scored if r["verdict_baseline"] == "MARGINAL")
    n_fail_b = sum(1 for r in scored if r["verdict_baseline"] == "FAIL")
    print(f"\nR1 (heavy-atom contact weighting):  {n_pass_r1} PASS, {n_marg_r1} MARGINAL, {n_fail_r1} FAIL "
          f"(of {len(scored)} scored)")
    print(f"baseline (binary Cα cutoff):        {n_pass_b} PASS, {n_marg_b} MARGINAL, {n_fail_b} FAIL "
          f"(of {len(scored)} scored)")

    prev_fail = {r["target"] for r in scored if r["verdict_baseline"] == "FAIL"}
    now_pass_or_marg = {r["target"] for r in scored
                         if r["target"] in prev_fail and r["verdict_r1"] != "FAIL"}
    print(f"\nPreviously-FAIL targets that R1 fixes (PASS or MARGINAL now): "
          f"{sorted(now_pass_or_marg)} ({len(now_pass_or_marg)}/{len(prev_fail)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
