#!/usr/bin/env python3
"""TASK-0276 -- Holo-only: is an allosteric site structurally distinguishable
*at all*, even with the answer in hand?

Every prior negative in this register (nine of them, see the task file) is
of the form "method X cannot predict the allosteric pocket from apo." Nobody
had asked the prior question: is it distinguishable in HOLO, where all the
information -- induced-fit conformation, the drug's own structural imprint --
is actually present? If not even that succeeds, the task is ill-posed from
structure alone, not merely hard.

**The leakage trap, and how this script avoids it** (task's own explicit
warning): "find the open cavity" trivially recovers any ligand-contact label,
allosteric or orthosteric, since a holo pocket is open BECAUSE something is
bound there. The sharp, non-circular comparison used throughout: BOTH
groups compared here (the allosteric drug's own contact residues, and the
orthosteric/catalytic site) are real, independently-defined ligand-adjacent
or catalytic sites in the SAME holo structure -- never "ligand-occupied vs.
empty." Every feature below is computed on the holo structure with every
non-protein atom (ligand, ion, water, cofactor) physically removed BEFORE
the calculation runs -- not merely excluded from the reported output (SASA
in particular: a feature computed on a structure that still contains the
ligand would show artificially low solvent exposure exactly where the drug
sits, which is the leakage trap in a different guise; the ligand-stripped
structure is a separate, explicitly-built temp file/AtomGroup for every
feature here, not a re-use of the ligand-containing one).

**Design: every holo structure is used self-referentially** -- its own
ligand-stripped coordinates supply the 5 features, and its own (unstripped)
raw structure supplies both ligand-contact groups (allosteric drug,
orthosteric ligand where one is co-bound). No apo structure is fetched or
used anywhere in this script; that is the entire point ("Holo structures
have only ever been used to generate the label" -- this task computes on
them instead).

**Orthosteric-site definition, matched to what's actually available per
family** (not forced into one shape): KRAS's own GDP is co-bound in every
one of the 10 structures, so orthosteric = GDP-contact residues (tier-1
`functional_indices` logic, called directly). HCV_NS5B's 4 structures never
carry a co-bound catalytic ligand (`func_ligand: []` in this register's own
config) -- orthosteric there = `backend.active_site.detect_active_site`'s
live UniProt-annotation call on that structure's own PDB ID, the same
machinery `task0242_two_stage_dryrun.prep()` already uses for every CAND-set
target in this register, confirmed by direct execution (HCV_NS5B_CMF's own
`prep()` seed = residues 220/318/319 -- the classic GDD/YGDD catalytic motif
of an RNA-dependent RNA polymerase, a real functional site, not a
topological proxy).

**Features** (5, chosen to be ligand-contact-independent): `V_C` (GNM
dynamic cross-correlation centrality -- [[TASK-0275]]'s own strongest single
term, un-negated from its Hamiltonian-potential sign convention back to a
plain "higher = more centrally coupled" score), `V_B` (raw deposited
B-factor, this HOLO structure's own -- not apo's), `degree` (binary contact
centrality, `allostery.baselines.degree_centrality`), `SASA` (BioPython
ShrakeRupley, [[TASK-0257]]'s own validated wrapper, run on a genuinely
ligand-stripped copy -- see leakage-trap note above), `fpocket` (per-residue
max druggability score, fpocket run on the SAME ligand-stripped copy --
[[TASK-0242]]/[[TASK-0249]]'s own established wrapper).

**Statistic**: per structure, `metrics.auc(feature, y)` restricted to ONLY
the union of the two labeled groups (`y=1` allosteric-pocket, `y=0`
orthosteric-site; every other residue excluded from this particular
computation) -- does the feature rank allosteric residues above orthosteric
ones, within the same structure? One AUC per (structure, feature). Aggregated
across structures with an exact cluster-level sign-flip test
([[TASK-0261]]'s own algorithm, reimplemented locally against an explicit
cluster map passed as an argument rather than that module's own hardcoded
frozen-set `CM` global, which does not cover these raw PDB IDs) on
`AUC - 0.5`.

**Stage 2 family, fixed BEFORE Stage 1 was run** (task's own requirement):
HCV_NS5B, chosen on coverage -- 4 distinct allosteric ligands already
verified in this register's own frozen config (CMF/POO/VR1/VRX across 2 apo
pairs), more chemotype diversity than any other candidate in the task's own
list (GAC/PKR/TRP_SYNTHASE/KSHV_PROTEASE each have only 2).

Run: ../.venv/bin/python3 scripts/task0276_holo_only_structural_signature.py
"""
from __future__ import annotations

import itertools
import json
import sys
import tempfile
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402
import Bio.PDB as PDB  # noqa: E402

prody.confProDy(verbosity="none")

# Side-effect-only import (TASK-0258's own fix, TASK-0273's cleanup pass
# re-applied it): leaves prody.parsePDB correctly composed (altloc="all"
# wrapping allostery's own pdb_cache/ folder default). Do NOT re-assign
# prody.parsePDB from a name pulled out of this module.
import task0255_hop_angstrom_calibration  # noqa: E402,F401

from allostery.clean import clean  # noqa: E402
from allostery.labels import (  # noqa: E402
    functional_indices, holo_pocket_mask, ligand_groups_from_atomgroup,
    protein_heavy_atoms_by_residue, terminal_mask,
)
from allostery.baselines import degree_centrality  # noqa: E402
from allostery.potentials import gnm_context, _normalized_dcc  # noqa: E402
from allostery.metrics import auc  # noqa: E402
from allostery.corex import per_atom_asa, per_residue_native_asa  # noqa: E402

from backend.active_site import detect_active_site  # noqa: E402

import task0242_two_stage_dryrun as t0242  # noqa: E402 -- fpocket_candidates
from task0249_composite_dumb_baseline import fpocket_druggability_per_residue  # noqa: E402

OUT = _ROOT / "results/tasks/0276_holo_only_structural_signature"
CUTOFF = 8.0  # this register's own default enm_cutoff (targets.yaml KRAS_G12C)
POCKET_CUTOFF = 4.5

FEATURE_NAMES = ["V_C", "V_B", "degree", "SASA", "fpocket"]

# (pdb_id, drug_ligand_code) -- the 10 verified KRAS G12C holo depositions,
# [[TASK-0270]]/[[TASK-0273]]'s own live-verified ensemble, reused unchanged.
KRAS_ENSEMBLE = [
    ("8AZX", "OFU"), ("7A1X", "QWB"), ("8QUG", "WYU"), ("9UOH", "A1L9E"),
    ("7YCE", "IQN"), ("7MDP", "Z07"), ("7RP3", "MKZ"), ("8AFC", "LXK"),
    ("8S8C", "A1H5U"), ("6OIM", "MOV"),
]

# (pdb_id, drug_ligand_code, cluster) -- HCV_NS5B's own 4 verified holo
# depositions (config/candidate_targets_task0243.yaml); cluster = shared apo
# pair, since CMF/POO and VR1/VRX are each two ligands on the same apo
# structure ([[TASK-0261]]'s own clustering unit).
HCV_ENSEMBLE = [
    ("2BRK", "CMF", "2HAI"), ("2BRL", "POO", "2HAI"),
    ("2O5D", "VR1", "2GIQ"), ("2HWI", "VRX", "2GIQ"),
]


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Features (all computed on ligand-stripped coordinates)
# ---------------------------------------------------------------------------

def dcc_centrality(coords: np.ndarray, cutoff: float) -> np.ndarray:
    """Raw (un-negated) V_C -- higher = more centrally DCC-coupled, the
    natural sign for a plain per-residue feature (V_C's own Hamiltonian
    convention negates it to a "reward", which would just flip every AUC
    below to 1-AUC; reported the natural way instead)."""
    ctx = gnm_context(coords, cutoff)
    nDCC = _normalized_dcc(ctx["U"], ctx["winv"])
    np.fill_diagonal(nDCC, 0.0)
    return np.abs(nDCC).sum(axis=1)


def _parse_any(pdb_id: str, **kwargs):
    """`prody.parsePDB` with an mmCIF fallback for entries whose 5-character
    extended chemical-component IDs (e.g. A1L9E, A1H5U) overflow the legacy
    PDB format's fixed-width HETATM columns -- the same fix now applied
    inside `allostery.clean.clean()` itself (TASK-0276), duplicated here
    only because this function's two call sites (`write_ligand_stripped_pdb`,
    `_raw_holo`) parse directly via prody, not through `clean()`."""
    try:
        return prody.parsePDB(pdb_id, compressed=False, **kwargs)
    except prody.proteins.pdbfile.PDBParseError:
        cif_path = prody.fetchPDB(pdb_id, format="cif", compressed=False)
        return prody.parseMMCIF(cif_path, **kwargs)


def write_ligand_stripped_pdb(pdb_id: str, chains: list, out_path: Path) -> None:
    ag = _parse_any(pdb_id)
    chain_sel = " or ".join(f"chain {c}" for c in chains)
    prot = ag.select(f"protein and ({chain_sel}) and not hetero")
    prody.writePDB(str(out_path), prot)


def ligand_stripped_sasa(stripped_pdb_path: Path, resnums: np.ndarray, chain: str) -> np.ndarray:
    """SASA computed on an ALREADY ligand-stripped structure -- the leakage
    trap this whole task is built around avoiding for this specific feature
    (Shrake-Rupley considers every atom present when judging occlusion, so
    a ligand-containing model would show artificially low SASA exactly
    where the drug sits)."""
    structure = PDB.PDBParser(QUIET=True).get_structure("x", str(stripped_pdb_path))
    model = structure[0]
    per_atom_asa(model)
    asa_by_resnum: dict = {}
    for c in model:
        for resnum, asa in per_residue_native_asa(c).items():
            asa_by_resnum[int(resnum)] = asa
    return np.array([asa_by_resnum.get(int(r), np.nan) for r in resnums], dtype=float)


def fpocket_druggability(stripped_pdb_path: Path, work: Path, resnums: np.ndarray,
                         chain_ids: np.ndarray) -> np.ndarray:
    pockets = t0242.fpocket_candidates(stripped_pdb_path, work)
    if isinstance(pockets, dict):
        return np.zeros(len(resnums), dtype=float)
    return fpocket_druggability_per_residue(pockets, resnums, chain_ids)


def compute_features(pdb_id: str, chains: list) -> dict:
    """All 5 features, ligand-stripped, keyed by resnum (single-chain
    convention throughout this task, matching every ensemble member)."""
    apo_like = clean(pdb_id, chains=chains, keep_nucleic=False)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        stripped = tmp / f"{pdb_id.lower()}_stripped.pdb"
        write_ligand_stripped_pdb(pdb_id, chains, stripped)
        sasa = ligand_stripped_sasa(stripped, apo_like.resnums, chains[0])
        fpock = fpocket_druggability(stripped, tmp, apo_like.resnums, apo_like.chain_ids)

    feat = dict(
        V_C=dcc_centrality(apo_like.coords, CUTOFF),
        V_B=np.asarray(apo_like.bfactors, dtype=float),
        degree=degree_centrality(apo_like.coords, cutoff=CUTOFF),
        SASA=sasa,
        fpocket=fpock,
    )
    return apo_like, feat


# ---------------------------------------------------------------------------
# Labels: allosteric (drug contact) vs orthosteric (GDP contact / UniProt)
# ---------------------------------------------------------------------------

def _raw_holo(pdb_id: str, chains: list, resnums: np.ndarray):
    """Ligand-bearing raw structure, wrapped with the `.ligand_groups`/
    `.heavy_atom_coords`/`.heavy_atom_seq_index` attributes `labels.py`'s
    own contract expects -- same adapter every existing caller in this
    register uses (`apo_structure_sensitivity_sweep._load_holo`,
    `task0242_two_stage_dryrun.prep`), applied to this task's own
    self-referential apo=holo structure.

    `ligand_groups` is extracted from the UNRESTRICTED parse, never the
    chain-selected one -- confirmed directly (9UOH's own mmCIF fallback,
    this task's first real run against it): prody's legacy PDB parser keeps
    a HETATM record on the SAME chain letter as its neighboring protein
    chain, but its mmCIF parser assigns each hetero group its OWN distinct
    chain letter (9UOH's A1L9E: `lig_chains=['A']` per the RCSB REST API,
    but chain 'D' in prody's own mmCIF AtomGroup). Restricting to `chain A`
    before extracting ligand groups silently dropped every ligand for the
    2 entries needing the mmCIF fallback -- both GDP and the drug -- which
    collapsed active_site to the tier-3 topological-proxy fallback (n=5)
    and pocket to empty. Protein coordinates/heavy-atom mapping still use
    the chain-restricted `struct`, unaffected by this."""
    full = _parse_any(pdb_id)
    chain_sel = " or ".join(f"chain {c}" for c in chains)
    struct = full.select(chain_sel)

    class _Holo:
        pass

    h = _Holo()
    h.coords = struct.select("protein and not hetero").getCoords()
    h.ligand_groups = ligand_groups_from_atomgroup(full)
    h.heavy_atom_coords, h.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        struct, chains, resnums
    )
    return h


def _self_holo(pdb_id: str, apo_like):
    """`apo_like` (already `clean()`-ed, ligand-free) augmented in place
    with the `.ligand_groups`/`.heavy_atom_coords`/`.heavy_atom_seq_index`
    attributes `labels.py`'s contract expects on a `holo` object -- built
    from the SAME structure's own raw (ligand-bearing) coordinates, so no
    second fetch/clean is needed. Self-referential apo=holo throughout this
    task; `holo_pocket_mask`'s sequence alignment degenerates to the
    identity map since `apo_seq == holo_seq` exactly."""
    raw = _raw_holo(pdb_id, ["A"], apo_like.resnums)
    apo_like.ligand_groups = raw.ligand_groups
    apo_like.heavy_atom_coords = raw.heavy_atom_coords
    apo_like.heavy_atom_seq_index = raw.heavy_atom_seq_index
    return apo_like


def kras_labels(pdb_id: str, drug_code: str, apo_like) -> tuple[np.ndarray, np.ndarray]:
    holo = _self_holo(pdb_id, apo_like)
    n = len(apo_like.resnums)

    func_idx, _provenance = functional_indices(
        apo_like.coords, holo.ligand_groups, {"func_ligand": ["GDP"]},
        cutoff=POCKET_CUTOFF, heavy_atom_coords=holo.heavy_atom_coords,
        heavy_atom_seq_index=holo.heavy_atom_seq_index,
        heavy_atom_resnames=None, coords_resnames=None, coords_resnums=apo_like.resnums,
    )
    active_site = np.zeros(n, dtype=bool)
    active_site[func_idx] = True

    pocket_raw = holo_pocket_mask(apo_like, holo, drug_code, cutoff=POCKET_CUTOFF)
    if pocket_raw is None:
        pocket_raw = np.zeros(n, dtype=bool)
    terminal = terminal_mask(n, 0.05)
    pocket = pocket_raw & ~active_site & ~terminal
    return active_site, pocket


def hcv_labels(pdb_id: str, drug_code: str, apo_like) -> tuple[np.ndarray, np.ndarray]:
    holo = _self_holo(pdb_id, apo_like)
    n = len(apo_like.resnums)

    det = detect_active_site(pdb_id, chain="A")
    resn = np.asarray(apo_like.resnums)
    active_site = np.isin(resn, list(det.get("active_site") or []))

    pocket_raw = holo_pocket_mask(apo_like, holo, drug_code, cutoff=POCKET_CUTOFF)
    if pocket_raw is None:
        pocket_raw = np.zeros(n, dtype=bool)
    terminal = terminal_mask(n, 0.05)
    pocket = pocket_raw & ~active_site & ~terminal
    return active_site, pocket


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def cluster_sign_flip(values: dict, cluster_of: dict) -> dict:
    """[[TASK-0261]]'s own exact cluster-level sign-flip test, reimplemented
    against an explicit `cluster_of: {key: cluster_id}` map rather than that
    module's hardcoded frozen-set `CM` global (which has no entries for raw
    PDB IDs)."""
    keys = [k for k in values if k in cluster_of]
    clusters = sorted(set(cluster_of[k] for k in keys))
    by_cluster: dict = {c: [] for c in clusters}
    for k in keys:
        by_cluster[cluster_of[k]].append(values[k])
    obs = sum(values[k] for k in keys)
    n_clusters = len(clusters)
    null = []
    for signs in itertools.product([1, -1], repeat=n_clusters):
        s = sum(sign * sum(by_cluster[c]) for sign, c in zip(signs, clusters))
        null.append(s)
    null = np.asarray(null)
    p = float(np.mean(np.abs(null) >= abs(obs) - 1e-12))
    vals = list(values.values())
    return dict(median=float(np.median(vals)), n=len(vals), n_clusters=n_clusters, p_value=p)


def consensus_union(entry_keys: dict, k: int) -> tuple[set, set]:
    from collections import Counter
    counts = Counter()
    for keys in entry_keys.values():
        counts.update(keys)
    consensus = {key for key, n in counts.items() if n >= k}
    return consensus, set(counts.keys())


# ---------------------------------------------------------------------------
# Family pipeline
# ---------------------------------------------------------------------------

def run_family(name: str, ensemble: list, label_fn, cluster_of: dict) -> dict:
    print(f"\n{'='*70}\n{name}\n{'='*70}")
    per_structure = {}
    allosteric_keys: dict = {}
    for entry in ensemble:
        pdb_id, drug_code = entry[0], entry[1]
        try:
            apo_like, feat = compute_features(pdb_id, ["A"])
            active_site, pocket = label_fn(pdb_id, drug_code, apo_like)
        except Exception as exc:  # noqa: BLE001
            print(f"  {pdb_id}: SKIP -- {type(exc).__name__}: {exc}")
            continue
        n_as, n_pk = int(active_site.sum()), int(pocket.sum())
        if n_as == 0 or n_pk == 0:
            print(f"  {pdb_id}: SKIP -- empty active_site({n_as}) or pocket({n_pk})")
            continue
        mask = active_site | pocket
        y = pocket.astype(int)[mask]
        row = {}
        for fname in FEATURE_NAMES:
            vals = feat[fname][mask]
            ok = np.isfinite(vals)
            if ok.sum() < len(vals) or not ok.all():
                vals = np.where(np.isfinite(vals), vals, np.nanmedian(vals[ok]) if ok.any() else 0.0)
            a = auc(vals, y)
            row[fname] = a
        per_structure[pdb_id] = row
        chids = np.asarray(apo_like.chain_ids)
        resn = np.asarray(apo_like.resnums)
        allosteric_keys[pdb_id] = set(
            (str(c), int(r)) for c, r in zip(chids[pocket], resn[pocket])
        )
        print(f"  {pdb_id:<8} drug={drug_code:<8} n_orthosteric={n_as:<4} n_allosteric={n_pk:<4}  "
              + "  ".join(f"{f}={row[f]:.3f}" for f in FEATURE_NAMES))

    print(f"\n  {len(per_structure)}/{len(ensemble)} usable")

    feature_stats = {}
    for fname in FEATURE_NAMES:
        vals = {pid: per_structure[pid][fname] - 0.5 for pid in per_structure
                if not np.isnan(per_structure[pid][fname])}
        if not vals:
            feature_stats[fname] = dict(error="all-nan")
            continue
        r = cluster_sign_flip(vals, cluster_of)
        feature_stats[fname] = r
        print(f"  {fname:<10} AUC median={0.5+r['median']:.3f}  n={r['n']}  "
              f"n_clusters={r['n_clusters']}  cluster-p={r['p_value']:.4f}")

    n_entries = len(allosteric_keys)
    k = (n_entries // 2) + 1
    consensus, union = ([], [])
    if allosteric_keys:
        consensus, union = consensus_union(allosteric_keys, k)
        print(f"\n  Commonality: consensus (K={k}/{n_entries}) = {len(consensus)} residues, "
              f"union = {len(union)} residues")
        print(f"  consensus residues: {sorted(consensus)}")

    # Within-cluster vs across-cluster Jaccard of the allosteric residue
    # set itself -- distinguishes "genuinely no common allosteric site"
    # from "these clusters sit at two different sites entirely" (a real
    # possibility whenever cluster_of has >1 distinct cluster, e.g.
    # HCV_NS5B's CMF/POO vs VR1/VRX pairs).
    pids = sorted(allosteric_keys)
    within, across = [], []
    for a, b in itertools.combinations(pids, 2):
        ka, kb = allosteric_keys[a], allosteric_keys[b]
        jac = len(ka & kb) / len(ka | kb) if (ka or kb) else float("nan")
        (within if cluster_of.get(a) == cluster_of.get(b) else across).append(jac)
    if within or across:
        print(f"  Allosteric-site Jaccard -- within-cluster: "
              f"{np.median(within) if within else float('nan'):.3f} (n={len(within)})  "
              f"across-cluster: {np.median(across) if across else float('nan'):.3f} (n={len(across)})")

    return dict(
        per_structure=per_structure, feature_stats=feature_stats,
        n_usable=len(per_structure), n_total=len(ensemble),
        consensus=dict(k=k, n_entries=n_entries, size=len(consensus),
                        keys=sorted(list(consensus))),
        union=dict(size=len(union), keys=sorted(list(union))),
        allosteric_keys={pid: sorted(allosteric_keys[pid]) for pid in allosteric_keys},
        jaccard_within_cluster=within, jaccard_across_cluster=across,
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}

    kras_cluster_of = {pid: pid for pid, _ in KRAS_ENSEMBLE}  # no shared apo -- singleton clusters
    results["KRAS"] = run_family("Stage 1 -- KRAS_G12C (10 drugs, GDP orthosteric)",
                                  KRAS_ENSEMBLE, kras_labels, kras_cluster_of)

    hcv_cluster_of = {pid: apo for pid, _, apo in HCV_ENSEMBLE}
    hcv_entries = [(pid, drug) for pid, drug, _ in HCV_ENSEMBLE]
    results["HCV_NS5B"] = run_family(
        "Stage 2 -- HCV_NS5B (4 drugs, UniProt-catalytic orthosteric; "
        "family fixed before Stage 1 was run, on coverage grounds)",
        hcv_entries, hcv_labels, hcv_cluster_of)

    (OUT / "holo_only_structural_signature.json").write_text(
        json.dumps(results, indent=1, default=str))
    print(f"\nwritten: {OUT / 'holo_only_structural_signature.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
