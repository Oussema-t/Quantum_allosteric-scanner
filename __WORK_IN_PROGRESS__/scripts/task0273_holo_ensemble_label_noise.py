#!/usr/bin/env python3
"""TASK-0273 -- experimental holo ensembles: how reproducible is our pocket
label, and what does that ceiling imply?

Every AUC this register has ever published treats the pocket label as exact
("residues within 4.5 A of the drug in one crystal structure"). This script
measures the noise floor beneath that label directly, using real,
independently-deposited crystal structures (RCSB) -- no simulation, no
Constraint-3 question.

**Live re-verification, this task's own required discipline** ([[TASK-0270]]
found 8/10 of [[TASK-0155]]'s own "verified apo" pool were actually
drug-bound because its filter trusted the RCSB *summary* field, which only
lists metal-coordinated nonpolymer components and silently drops
non-coordinating small-molecule ligands): every candidate structure below is
checked against RCSB's per-nonpolymer-entity endpoint directly (not the
summary field), and for KRAS, against the entry's own deposited sequence at
the anchor-relative position-12 offset (same "TEYKLVVVG" motif check
[[TASK-0155]]/[[TASK-0270]] used). Genuine, real exclusions were found doing
this -- see EXCLUSIONS below and the module's own printed diagnostics.

**KRAS G12C same-drug replicate search** (RCSB Search API, chemical
component exact match + UniProt P01116): of the 10 independently-verified
G12C/GDP/X-ray holo depositions (8 from [[TASK-0270]]'s own audit + 8S8C +
6OIM), searching for every OTHER deposition of the SAME drug found:
  - OFU (BI-2865): 7 other hits, but ALL are off-genotype (8AZV/9OU2-4 =
    wild-type K-Ras; 8AZY = G12D; 8AZZ = G12V; 8B00 = G13D). Zero usable
    same-drug G12C replicates for this drug.
  - WYU: 1 other hit (9IAY), wild-type -- excluded, zero replicates.
  - MOV (sotorasib): 5 other hits, all cryo-EM (not crystallography) and 4
    of 5 are antibody/MHC-peptide complexes, not the intact KRAS-drug
    pocket at all -- excluded on method + construct grounds, zero usable
    replicates.
  - MKZ (GNE-1952, [[TASK-0270]]'s own "covalently alkylated" 7RP3): 2 other
    hits, BOTH genuine G12C X-ray depositions (6T5V, 7RP4). **This is the
    only KRAS drug in this pool with any genuine same-drug X-ray G12C
    replicate** -- n=3 structures, 3 same-drug pairs. Small, but real and
    reported as such, not padded with the excluded entries.

**GAC (glutaminase) same-drug (04A/BPTES) search**: 6 other hits, all human,
one (4JKT) is MOUSE glutaminase -- excluded on species grounds, 5 remain
alongside the frozen set's own 3UO9 = 6 total, 15 same-drug pairs. Caveat
disclosed, not chased further: the frozen set's own apo (7SBN) is a
stabilizing Y466W point mutant; none of the replicate depositions carry that
mutation. Cross-drug comparison reuses [[TASK-0261]]'s own GAC_CPD12 holo
(8BSL, ligand R90) against every 04A entry.

**TRP_SYNTHASE (F6F) same-drug search**: 12 other hits, all Salmonella
typhimurium, alongside the frozen set's own 2CLF = 13 total, 78 same-drug
pairs -- the richest replicate set found. Caveat disclosed: entries span
different catalytic states (internal/external aldimine) and the ligand
occupies one or two sites (alpha and/or beta) depending on the entry; a
structure's own contact set is the union of whichever copies it has. This
measures total same-ligand pocket-residue variability across every real
source of variation in the deposited ensemble, not a purified estimate of
pure crystallographic noise alone -- reported as an upper bound on the
latter, not conflated with it.

**Contact extraction** is self-contained per PDB entry -- no apo/holo
overlay, no geometric alignment across entries. This project's own
`labels.py::protein_heavy_atoms_by_residue` already establishes that a
structure's pocket label is a pure (chain, resnum) heavy-atom-distance
computation on ITS OWN deposited coordinates; the same convention is used
directly here (protein heavy atoms across every chain vs. the named ligand's
heavy atoms, 4.5 A, whichever chain(s) that ligand copy occupies in THAT
entry).

**Jaccard, both keyings** ([[TASK-0265]]'s own established fix, reused
verbatim): (chain, resnum)-exact AND resnum-only, since a homo-oligomer can
legitimately deposit the same physical site on a differently-lettered
symmetric chain across independent depositions -- reporting only the
chain-exact version would then read as "no overlap" for what is really the
same site.

**Consensus/union re-scoring** is done for KRAS_G12C (monomeric, chain
letters unambiguous across all 10+3 depositions) and TRP_SYNTHASE_F6F (alpha
and beta are different polypeptides/entities, not symmetric copies -- chain
identity is safe there too). GAC_BPTES is a genuine homo-oligomer with no
established chain-correspondence across independent depositions; re-scoring
it against a consensus mask built from possibly-mismatched chain letters
would silently launder that ambiguity into a number, so it is deliberately
NOT re-scored here -- Jaccard/consensus-definition only, flagged, not
attempted. K stated before any number is computed: majority, K = ceil(N/2).

Run: ../.venv/bin/python3 scripts/task0273_holo_ensemble_label_noise.py
"""
from __future__ import annotations

import dataclasses
import json
import math
import sys
import time
import urllib.error
import urllib.request
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
from scipy.spatial.distance import cdist

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402
import yaml  # noqa: E402

prody.confProDy(verbosity="none")

# Importing task0255 for its own side effect only: it leaves prody.parsePDB
# correctly composed (altloc="all" wrapping allostery's own pdb_cache/
# folder default). Do NOT re-assign prody.parsePDB to a name pulled out of
# it -- that function object's closure was bound before allostery's own
# init-time patch ran, so re-assigning it clobbers the folder default and
# scatters every fetched structure into this process's cwd instead of
# pdb_cache/ (TASK-0258's own finding; this task's own first run hit the
# identical bug -- confirmed directly: 39 stray .pdb/.cif files landed in
# __WORK_IN_PROGRESS__/ instead of pdb_cache/, cleaned up in TASK-0273's
# own follow-up pass, same fix task0259 already applies).
import task0255_hop_angstrom_calibration  # noqa: E402,F401

from allostery.labels import Labels  # noqa: E402
from allostery.metrics import precision_at_k  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.protocol import run_frozen_verdict  # noqa: E402

import run_challenge  # noqa: E402
from task0242_two_stage_dryrun import prep, CAND  # noqa: E402
import task0249_composite_dumb_baseline as t0249  # noqa: E402
import task0254_fpocket_variance_and_crypticity as t0254  # noqa: E402

OUT = _ROOT / "results/tasks/0273_holo_ensemble_label_noise"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
CAND.update(yaml.safe_load(FROZEN_CONFIG.read_text())["targets"])

ANCHOR = "TEYKLVVVG"  # KRAS residues 2-10, canonical -- position-12 offset check
POCKET_CUTOFF = 4.5


# ---------------------------------------------------------------------------
# RCSB live verification
# ---------------------------------------------------------------------------

def _rcsb_get(url: str, retries: int = 5) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "qas-task0273/1.0"})
    last_exc = None
    for _ in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(1.2)
    raise RuntimeError(f"RCSB fetch failed after {retries} tries: {url}") from last_exc


def rcsb_entry_meta(pdb_id: str) -> dict:
    d = _rcsb_get(f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}")
    return dict(
        method=d.get("exptl", [{}])[0].get("method"),
        resolution=(d.get("rcsb_entry_info", {}).get("resolution_combined") or [None])[0],
        title=d.get("struct", {}).get("title"),
        polymer_entity_ids=d.get("rcsb_entry_container_identifiers", {}).get("polymer_entity_ids", []) or [],
        nonpolymer_entity_ids=d.get("rcsb_entry_container_identifiers", {}).get("non_polymer_entity_ids", []) or [],
    )


def rcsb_ligand_chains(pdb_id: str, npe_ids: list, ligand_code: str) -> list | None:
    for e in npe_ids:
        nd = _rcsb_get(f"https://data.rcsb.org/rest/v1/core/nonpolymer_entity/{pdb_id}/{e}")
        if nd.get("pdbx_entity_nonpoly", {}).get("comp_id") == ligand_code:
            return nd.get("rcsb_nonpolymer_entity_container_identifiers", {}).get("auth_asym_ids")
        time.sleep(0.05)
    return None


def rcsb_kras_res12(pdb_id: str, polymer_entity_ids: list) -> str | None:
    for e in polymer_entity_ids:
        pd = _rcsb_get(f"https://data.rcsb.org/rest/v1/core/polymer_entity/{pdb_id}/{e}")
        seq = pd.get("entity_poly", {}).get("pdbx_seq_one_letter_code_can", "") or ""
        i = seq.find(ANCHOR)
        if i == -1:
            continue
        return seq[i + len(ANCHOR) + 1]  # ANCHOR ends at res10(G); +1->res11(A); +1->res12
        time.sleep(0.05)
    return None


def rcsb_organism(pdb_id: str, polymer_entity_ids: list) -> set:
    orgs = set()
    for e in polymer_entity_ids:
        pd = _rcsb_get(f"https://data.rcsb.org/rest/v1/core/polymer_entity/{pdb_id}/{e}")
        for o in (pd.get("rcsb_entity_source_organism") or []):
            if o.get("scientific_name"):
                orgs.add(o["scientific_name"])
        time.sleep(0.05)
    return orgs


# ---------------------------------------------------------------------------
# Ensemble definitions (candidate lists assembled via RCSB Search API,
# chemical-component exact match; verification below is what actually
# decides membership, not this list)
# ---------------------------------------------------------------------------

KRAS_CANDIDATES = [
    # (pdb_id, ligand_code, is_base_10)
    ("8AZX", "OFU", True), ("7A1X", "QWB", True), ("8QUG", "WYU", True),
    ("9UOH", "A1L9E", True), ("7YCE", "IQN", True), ("7MDP", "Z07", True),
    ("7RP3", "MKZ", True), ("8AFC", "LXK", True), ("8S8C", "A1H5U", True),
    ("6OIM", "MOV", True),
    ("8AZV", "OFU", False), ("8AZY", "OFU", False), ("8AZZ", "OFU", False),
    ("8B00", "OFU", False), ("9OU2", "OFU", False), ("9OU3", "OFU", False),
    ("9OU4", "OFU", False), ("9IAY", "WYU", False),
    ("6T5V", "MKZ", False), ("7RP4", "MKZ", False),
    ("8G47", "MOV", False), ("8UDR", "MOV", False), ("8VR9", "MOV", False),
    ("8VRA", "MOV", False), ("8VRB", "MOV", False),
]

GAC_CANDIDATES = [
    ("3UO9", "04A", True),
    ("3VOZ", "04A", False), ("3VP1", "04A", False), ("4JKT", "04A", False),
    ("5UQE", "04A", False), ("7RGG", "04A", False), ("8BSK", "04A", False),
    ("8BSL", "R90", None),  # cross-drug reference, TASK-0243's own GAC_CPD12 holo
]

TRP_CANDIDATES = [
    ("2CLF", "F6F", True), ("2CLH", "F19", True),
    ("2CLE", "F6F", False), ("2CLM", "F6F", False), ("4KKX", "F6F", False),
    ("4WX2", "F6F", False), ("4Y6G", "F6F", False), ("4ZQC", "F6F", False),
    ("5BW6", "F6F", False), ("7KU9", "F6F", False), ("7LY8", "F6F", False),
    ("7M2L", "F6F", False), ("7M3S", "F6F", False), ("7ME8", "F6F", False),
    ("2CLO", "F19", False),
]


def verify_kras(pdb_id: str, ligand_code: str) -> dict:
    meta = rcsb_entry_meta(pdb_id)
    if meta["method"] != "X-RAY DIFFRACTION":
        return dict(**meta, ligand=ligand_code, ok=False, reason=f"not X-ray ({meta['method']})")
    chains = rcsb_ligand_chains(pdb_id, meta["nonpolymer_entity_ids"], ligand_code)
    if not chains:
        return dict(**meta, ligand=ligand_code, ok=False, reason="ligand not found among nonpoly entities")
    res12 = rcsb_kras_res12(pdb_id, meta["polymer_entity_ids"])
    if res12 != "C":
        return dict(**meta, ligand=ligand_code, ok=False, reason=f"not G12C (residue 12 = {res12})",
                    ligand_chains=chains)
    return dict(**meta, ligand=ligand_code, ok=True, reason="verified G12C X-ray", ligand_chains=chains)


def verify_generic(pdb_id: str, ligand_code: str, require_organism: str | None = None) -> dict:
    """`require_organism` is matched as a case-insensitive keyword, not an
    exact string: RCSB's own `rcsb_entity_source_organism.scientific_name`
    is depositor-free-text and varies across entries for the identical
    organism -- confirmed directly, this task's own first run: real
    Salmonella typhimurium F6F replicates came back as 'Salmonella
    typhimurium', 'SALMONELLA TYPHIMURIUM', 'Salmonella enterica subsp.
    enterica serovar Typhimurium', and 'Salmonella typhimurium (strain LT2
    / SGSC1412 / ATCC 700720)' -- an exact match wrongly excluded 10 of 12
    genuine replicates on the first run. A keyword substring check is the
    correct fix, not a workaround."""
    meta = rcsb_entry_meta(pdb_id)
    if meta["method"] != "X-RAY DIFFRACTION":
        return dict(**meta, ligand=ligand_code, ok=False, reason=f"not X-ray ({meta['method']})")
    chains = rcsb_ligand_chains(pdb_id, meta["nonpolymer_entity_ids"], ligand_code)
    if not chains:
        return dict(**meta, ligand=ligand_code, ok=False, reason="ligand not found among nonpoly entities")
    if require_organism:
        orgs = rcsb_organism(pdb_id, meta["polymer_entity_ids"])
        kw = require_organism.lower()
        if not any(kw in o.lower() for o in orgs):
            return dict(**meta, ligand=ligand_code, ok=False,
                        reason=f"organism mismatch ({orgs} does not contain '{require_organism}')",
                        ligand_chains=chains)
    return dict(**meta, ligand=ligand_code, ok=True, reason="verified", ligand_chains=chains)


# ---------------------------------------------------------------------------
# Contact extraction (self-contained per entry, no apo/holo overlay)
# ---------------------------------------------------------------------------

def contact_residue_keys(pdb_id: str, ligand_code: str, lig_chains: list, cutoff: float = POCKET_CUTOFF):
    """(chain, resnum) heavy-atom contact set of the protein against every
    copy of `ligand_code` deposited in chains `lig_chains` of `pdb_id`.
    Self-contained: parses `pdb_id` once, no reference to any other entry.

    Legacy PDB text format cannot represent a 5-character extended chemical
    component ID (e.g. A1L9E, A1H5U -- RCSB's newer convention once the
    classic 3-character alphabet was exhausted): the fixed-width HETATM
    columns overflow and corrupt the coordinate fields, which prody's PDB
    parser correctly refuses to read (confirmed directly: `PDBParseError`
    on 9UOH/8S8C, both real hits during this task's own run). Falls back to
    mmCIF for exactly that case. prody's mmCIF parser assigns its OWN chain
    letters to HETATM groups, unrelated to RCSB's `auth_asym_id` (confirmed:
    9UOH's A1L9E is `lig_chains=['A']` per the REST API but chain 'D' in
    prody's mmCIF AtomGroup) -- so the mmCIF fallback selects by resname
    alone, not `lig_chains`; both real-world cases it's needed for (9UOH,
    8S8C) have exactly one ligand copy, so this is safe, not a silent
    approximation for a case that would actually need the chain filter.

    `prody.parseMMCIF(pdb_id)` given a bare ID does its own internal fetch
    via a `fetchPDB` reference `ciffile.py` captured at PRODY'S OWN import
    time -- before `allostery`'s init-time monkeypatch of the top-level
    `prody.fetchPDB` name could ever reach it, since it's a separate,
    already-bound module-level reference inside prody's own source, not the
    attribute being patched. Confirmed directly: it writes an mmCIF-content
    file named `<id>.pdb` into cwd regardless of `pdb_cache/`. Worked around
    by fetching through the correctly-wrapped `prody.fetchPDB` ourselves
    first and handing `parseMMCIF` the resulting path -- it skips its own
    internal fetch whenever `os.path.isfile(pdb)` is already true."""
    try:
        ag = prody.parsePDB(pdb_id, compressed=False)
        chain_sel = " or ".join(f"chain {c}" for c in lig_chains)
        lig = ag.select(f"hetatm and (resname {ligand_code}) and ({chain_sel})")
    except prody.proteins.pdbfile.PDBParseError:
        print(f"    {pdb_id}: legacy PDB parse failed (extended chemical-component ID?) "
              f"-- falling back to mmCIF, resname-only ligand selection")
        cif_path = prody.fetchPDB(pdb_id, format="cif", compressed=False)
        ag = prody.parseMMCIF(cif_path)
        lig = ag.select(f"hetatm and (resname {ligand_code})")
    if ag is None:
        return None
    prot = ag.select("protein and not hetero")
    if lig is None or prot is None:
        return None
    d = cdist(prot.getCoords(), lig.getCoords())
    hit = d.min(axis=1) <= cutoff
    chids = prot.getChids()[hit]
    resn = prot.getResnums()[hit]
    return set(zip((str(c) for c in chids), (int(r) for r in resn)))


def jaccard_pair(a: set, b: set) -> tuple[float, float]:
    """(chain,resnum)-exact Jaccard, resnum-only Jaccard ([[TASK-0265]]'s
    own dual-keying fix for homo-oligomer symmetric-copy ambiguity)."""
    inter, uni = len(a & b), len(a | b)
    jac = inter / uni if uni else float("nan")
    ra, rb = set(r for _, r in a), set(r for _, r in b)
    ri, ru = len(ra & rb), len(ra | rb)
    jac_r = ri / ru if ru else float("nan")
    return jac, jac_r


# ---------------------------------------------------------------------------
# Consensus / union labels + re-scoring
# ---------------------------------------------------------------------------

def mask_from_keys(apo, keys: set) -> np.ndarray:
    chids = np.asarray(apo.chain_ids)
    resn = np.asarray(apo.resnums)
    return np.array([(str(c), int(r)) in keys for c, r in zip(chids, resn)], dtype=bool)


def consensus_union_keys(entries: dict[str, set], k: int) -> tuple[set, set]:
    """`entries`: pdb_id -> (chain,resnum) key set. Returns (consensus,
    union) key sets. K stated by the caller before any number is computed."""
    from collections import Counter
    counts = Counter()
    for keys in entries.values():
        counts.update(keys)
    consensus = {key for key, n in counts.items() if n >= k}
    union = set(counts.keys())
    return consensus, union


def rescore_with_pocket(target_name: str, custom_pocket: np.ndarray | None, label: str) -> dict:
    """Re-run the exact frozen-verdict pipeline (`run_challenge`'s own
    candidates_builder + `run_frozen_verdict`, unmodified) against either
    the target's own shipped single-structure label (`custom_pocket=None`)
    or a supplied consensus/union mask -- same active_site/terminal
    exclusion `build_labels` itself applies, reused via `dataclasses.replace`
    rather than re-derived."""
    cfg, apo, seed, pocket = prep(target_name)
    if custom_pocket is not None:
        # prep() doesn't expose active_site/terminal separately; both are
        # already baked out of `pocket`, but active_site is exactly `seed`
        # (as a mask) and terminal only trims the sequence ends -- reapply
        # the same exclusion `build_labels` applies so a custom label is
        # scored under the identical rule, not a laxer one.
        n = len(apo.resnums)
        active_site = np.zeros(n, dtype=bool)
        active_site[seed] = True
        from allostery.labels import terminal_mask
        terminal = terminal_mask(n, 0.05)
        pocket = custom_pocket & ~active_site & ~terminal
    if pocket is None or not pocket.any():
        return dict(label=label, error="empty pocket after exclusion")

    cutoff = float(cfg.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    floor_scores = [
        run_challenge.degree_centrality(apo.coords, cutoff=cutoff),
        run_challenge.euclid_from_seed_centroid(apo.coords, seed),
        run_challenge.hop_from_seed(apo.coords, seed, cutoff=cutoff),
    ]
    candidates_builder = run_challenge._make_candidates_builder(apo, seed, cutoff)
    result = run_frozen_verdict(
        target_name, candidates_builder,
        apo.coords, apo.bfactors, seed, pocket,
        cutoff=cutoff, t_max=run_challenge.SELECTION_GSR_ABLATION_T,
        n_steps=run_challenge.SELECTION_GSR_ABLATION_N_STEPS,
        floor_scores=floor_scores, coherent=False, use_converged_limit=True,
    )
    winner_H = candidates_builder()[result["_winner_index"]]["H"]
    w, v = np.linalg.eigh(winner_H)
    winner_occ = time_averaged_ctqw_converged(source=seed, coherent=False, w=w, v=v)
    p_at_5 = float(precision_at_k(winner_occ, pocket, k=5))
    return dict(label=label, pocket_size=int(pocket.sum()), auc=result.get("AUC_apo_Hnew_optimised"),
                p_at_5=p_at_5, diagnosis=result.get("_diagnosis"))


def rescore_cv_composite(target_name: str, consensus: set, union: set) -> dict:
    """The metric that actually underlies this register's "X% unexplained"
    headline ([[TASK-0254]]/[[TASK-0261]]/[[TASK-0263]]/[[TASK-0274]]'s own
    shared machinery, reused unmodified) is NOT `run_frozen_verdict`'s raw
    single-operator AUC (`rescore_with_pocket`, above) -- it's the
    cross-validated AUC of the full geometry+fpocket+CTQW composite,
    holding features fixed and scoring against the pocket label as `y`.
    Only meaningful for a target already in [[TASK-0243]]'s frozen 22-target
    set (KRAS_G12C is not; GAC_BPTES is, but deliberately not re-scored
    here at all -- see module docstring); used for TRP_SYNTHASE_F6F only,
    the one case where doing so is both low-risk (chain-safe, see
    docstring) and directly comparable to an already-published number
    (TASK-0254's own table: TRP_SYNTHASE_F6F full AUC = 0.864 against the
    single-structure label)."""
    d = t0249.target_rows(target_name)
    if d is None:
        return dict(error="target_rows failed")
    cfg, apo, seed, _ = prep(target_name)
    n = len(apo.resnums)
    m = np.ones(n, dtype=bool)
    m[seed] = False
    chids_m = np.asarray(apo.chain_ids)[m]
    resn_m = np.asarray(apo.resnums)[m]

    feat = t0254.build_blocks(target_name, d)
    X_full = np.column_stack([feat["geometry"], feat["fpocket"], feat["ctqw"]])

    def y_from_keys(keys: set) -> np.ndarray:
        return np.array([(str(c), int(r)) in keys for c, r in zip(chids_m, resn_m)], dtype=int)

    y_single = d["y"]
    y_consensus = y_from_keys(consensus)
    y_union = y_from_keys(union)

    out = {}
    for label, y in (("single (shipped)", y_single), ("consensus", y_consensus), ("union", y_union)):
        if y.sum() == 0 or y.sum() == len(y):
            out[label] = dict(error=f"degenerate y (n_pos={int(y.sum())}/{len(y)})")
            continue
        cv = t0254.cv_auc(X_full, y)
        out[label] = dict(cv_auc=cv, n_pos=int(y.sum()), n=len(y))
        print(f"    CV-composite {label:<18}: AUC={cv:.4f}  n_pos={int(y.sum())}/{len(y)}")
    return out


# ---------------------------------------------------------------------------
# Per-protein pipeline
# ---------------------------------------------------------------------------

def run_protein(name: str, candidates: list, verify_fn, target_name: str,
                 k_consensus: int | None = None, do_rescore: bool = False) -> dict:
    print(f"\n{'='*70}\n{name}\n{'='*70}")
    verified = {}
    for pdb_id, ligand, is_base in candidates:
        v = verify_fn(pdb_id, ligand)
        v["is_base"] = is_base
        verified[pdb_id] = v
        flag = "OK " if v["ok"] else "SKIP"
        print(f"  {flag} {pdb_id:<8} lig={ligand:<8} {v['reason']}")
        time.sleep(0.1)

    usable = {pid: v for pid, v in verified.items() if v["ok"]}
    print(f"\n  {len(usable)}/{len(candidates)} usable after verification")

    contacts = {}
    for pid, v in usable.items():
        keys = contact_residue_keys(pid, v["ligand"], v["ligand_chains"])
        if keys:
            contacts[pid] = dict(keys=keys, ligand=v["ligand"])
        else:
            print(f"  {pid}: contact extraction failed, dropped")

    by_ligand: dict[str, list[str]] = {}
    for pid, c in contacts.items():
        by_ligand.setdefault(c["ligand"], []).append(pid)

    same_drug_rows, diff_drug_rows = [], []
    pids = sorted(contacts)
    for i in range(len(pids)):
        for j in range(i + 1, len(pids)):
            a, b = pids[i], pids[j]
            jac, jac_r = jaccard_pair(contacts[a]["keys"], contacts[b]["keys"])
            row = dict(a=a, b=b, ligand_a=contacts[a]["ligand"], ligand_b=contacts[b]["ligand"],
                       jaccard=jac, jaccard_resnum_only=jac_r,
                       n_a=len(contacts[a]["keys"]), n_b=len(contacts[b]["keys"]))
            (same_drug_rows if contacts[a]["ligand"] == contacts[b]["ligand"] else diff_drug_rows).append(row)

    def summarize(rows, tag):
        if not rows:
            print(f"  {tag}: n=0")
            return {}
        js = [r["jaccard"] for r in rows]
        jrs = [r["jaccard_resnum_only"] for r in rows]
        print(f"  {tag}: n={len(rows)}  Jaccard(chain,resnum) median={np.median(js):.3f} "
              f"[{min(js):.3f},{max(js):.3f}]  Jaccard(resnum-only) median={np.median(jrs):.3f} "
              f"[{min(jrs):.3f},{max(jrs):.3f}]")
        return dict(n=len(rows), jaccard_median=float(np.median(js)), jaccard_min=float(min(js)),
                    jaccard_max=float(max(js)), jaccard_resnum_only_median=float(np.median(jrs)))

    print()
    same_summary = summarize(same_drug_rows, "same-drug pairs")
    diff_summary = summarize(diff_drug_rows, "different-drug pairs")

    out = dict(verified={k: {kk: vv for kk, vv in v.items() if kk != "polymer_entity_ids"}
                          for k, v in verified.items()},
               same_drug_pairs=same_drug_rows, diff_drug_pairs=diff_drug_rows,
               same_drug_summary=same_summary, diff_drug_summary=diff_summary,
               by_ligand={k: v for k, v in by_ligand.items()})

    if k_consensus is not None and contacts:
        entry_keys = {pid: c["keys"] for pid, c in contacts.items()}
        n_entries = len(entry_keys)
        k = k_consensus if k_consensus > 0 else math.ceil(n_entries / 2)
        consensus, union = consensus_union_keys(entry_keys, k)
        print(f"\n  consensus (K={k} of {n_entries}): {len(consensus)} residues")
        print(f"  union: {len(union)} residues")
        out["consensus_union"] = dict(k=k, n_entries=n_entries,
                                       consensus_size=len(consensus), union_size=len(union),
                                       consensus_keys=sorted(list(consensus)),
                                       union_keys=sorted(list(union)))

        if do_rescore:
            print(f"\n  Re-scoring {target_name} against single / consensus / union labels...")
            r_single = rescore_with_pocket(target_name, None, "single (shipped)")
            print(f"    single    : AUC={r_single.get('auc')}  P@5={r_single.get('p_at_5')}  "
                  f"pocket={r_single.get('pocket_size')}")
            cfg, apo, seed, _ = prep(target_name)
            consensus_mask = mask_from_keys(apo, consensus)
            union_mask = mask_from_keys(apo, union)
            r_consensus = rescore_with_pocket(target_name, consensus_mask, "consensus")
            print(f"    consensus : AUC={r_consensus.get('auc')}  P@5={r_consensus.get('p_at_5')}  "
                  f"pocket={r_consensus.get('pocket_size')}")
            r_union = rescore_with_pocket(target_name, union_mask, "union")
            print(f"    union     : AUC={r_union.get('auc')}  P@5={r_union.get('p_at_5')}  "
                  f"pocket={r_union.get('pocket_size')}")
            out["rescore"] = dict(single=r_single, consensus=r_consensus, union=r_union)

    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}

    results["KRAS"] = run_protein("KRAS_G12C ensemble", KRAS_CANDIDATES, verify_kras,
                                   target_name="KRAS_G12C", k_consensus=0, do_rescore=True)

    def verify_gac(pid, lig):
        return verify_generic(pid, lig, require_organism="Homo sapiens")

    results["GAC"] = run_protein("GAC_BPTES ensemble", GAC_CANDIDATES, verify_gac,
                                  target_name="GAC_BPTES", k_consensus=0, do_rescore=False)
    print("\n  NOTE: GAC_BPTES is a genuine homo-oligomer with no established "
          "chain-correspondence across independently-solved depositions -- "
          "consensus/union DEFINED above (resnum-only-safe) but deliberately "
          "NOT used to re-score, to avoid silently laundering that ambiguity "
          "into a number. See module docstring.")

    def verify_trp(pid, lig):
        return verify_generic(pid, lig, require_organism="typhimurium")

    results["TRP_SYNTHASE"] = run_protein("TRP_SYNTHASE_F6F ensemble", TRP_CANDIDATES, verify_trp,
                                           target_name="TRP_SYNTHASE_F6F", k_consensus=0, do_rescore=True)
    cu = results["TRP_SYNTHASE"].get("consensus_union")
    if cu:
        print("\n  Re-scoring TRP_SYNTHASE_F6F in the CV-composite (geometry+fpocket+ctqw) "
              "framework that TASK-0254's own '67%->29% unexplained' headline actually uses...")
        consensus_set = {tuple(k) for k in cu["consensus_keys"]}
        union_set = {tuple(k) for k in cu["union_keys"]}
        results["TRP_SYNTHASE"]["rescore_cv_composite"] = rescore_cv_composite(
            "TRP_SYNTHASE_F6F", consensus_set, union_set)

    (OUT / "holo_ensemble_label_noise.json").write_text(json.dumps(results, indent=1, default=str))
    print(f"\nwritten: {OUT / 'holo_ensemble_label_noise.json'}")

    print("\n" + "=" * 70)
    print("SUMMARY -- implied AUC ceiling")
    print("=" * 70)
    for name in ("KRAS", "GAC", "TRP_SYNTHASE"):
        r = results[name]
        s, d = r.get("same_drug_summary", {}), r.get("diff_drug_summary", {})
        print(f"{name:<14} same-drug Jaccard median={s.get('jaccard_median')}  "
              f"(n={s.get('n', 0)})   different-drug Jaccard median={d.get('jaccard_median')}  "
              f"(n={d.get('n', 0)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
