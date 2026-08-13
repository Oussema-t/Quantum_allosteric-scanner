"""Phase 1 - curated allosteric pocket labels.

Derives the allosteric pocket label (holo ligand-contact residues mapped onto
apo numbering) and the functional/active-site seed set used to run the CTQW,
per SYSTEMS_allosteric_corrected_v2.md's central rule: never hand-transcribe a
residue list -- if a target's ligand can't be resolved programmatically, the
label is None/empty and flagged, not guessed (see `pick_drug`/
`holo_pocket_mask`).

Leakage boundary: this module is the only place downstream code may look at
the holo structure. Everything after label derivation (transport operators,
scoring in protocol.py / TASK-0006) consumes only this module's *output*
(pocket mask, functional indices) and must not call back into holo directly.

Partial port of notebook `H_new_engineering (4) CLEAN.ipynb` Sec.1 ("Robust
functional-site detection") -- see TASK-0004's "why this is a partial port"
for which pieces are ported vs. net-new (pocket derivation + the
sequence-alignment residue mapping have no notebook precedent; `pick_drug`
deliberately drops the notebook's "largest ligand" fallback, see below).

Dependency note: sequence alignment here uses a minimal, local
Needleman-Wunsch implementation, not Biopython/prody -- neither is installed
in this scaffold's venv as of TASK-0004, so a stdlib/numpy-only aligner keeps
this module importable and testable without adding a new dependency
(resolves TASK-0004's Open Question in favor of the lighter option).
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np


# ---------------------------------------------------------------------------
# Ligand data contract
# ---------------------------------------------------------------------------

@dataclass
class LigandGroup:
    """One bound HETATM residue (drug, cofactor, ion, ...) in a holo structure."""

    resname: str
    resnum: int
    chain: str
    coords: np.ndarray  # (n_atoms, 3) heavy-atom coordinates
    n_atoms: int


def ligand_groups_from_atomgroup(ag) -> list[LigandGroup]:
    """Extract non-water HETATM residues from a prody AtomGroup.

    Adapter for real structures fetched via prody (see clean.py::clean, which
    parses with prody but discards hetero atoms when it builds CleanResult).
    Adapted from notebook Sec.1's `ligand_residues`, with one deliberate
    correction: selects on prody's raw `hetatm` record flag, not its derived
    `hetero` flag. Confirmed against a live fetch (TASK-0004 KRAS_G12C
    integration check, 2026-07-06): prody classifies bound-nucleotide
    ligands like GDP under its `nucleic` flag, which makes its `hetero` flag
    (defined as roughly "not protein/nucleic/water") False for GDP even
    though it is a real HETATM ligand -- the notebook's own selection string
    would have silently missed it too. `hetatm` is the raw per-atom record
    type instead, so it still correctly excludes real polymer nucleic-acid
    chains (verified against MYC_MAX's 1NKP DNA chain, which is proper ATOM
    records, not HETATM). No prody import here -- only prody's AtomGroup
    *methods* are used (select/iterAtoms/getResname/getResnum/getChid/
    getCoords), so pure-numpy callers (unit tests, synthetic data) never
    need prody installed to use the rest of this module.
    """
    het = ag.select("hetatm and not water")
    if het is None:
        return []
    groups: dict[tuple[str, int, str], list] = {}
    for atom in het.iterAtoms():
        key = (atom.getResname().strip(), int(atom.getResnum()), atom.getChid())
        groups.setdefault(key, []).append(atom.getCoords())
    return [
        LigandGroup(
            resname=key[0],
            resnum=key[1],
            chain=key[2],
            coords=np.array(atom_coords, dtype=float),
            n_atoms=len(atom_coords),
        )
        for key, atom_coords in groups.items()
    ]


def protein_heavy_atoms_by_residue(
    ag,
    chains: list[str],
    resnums: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """All protein heavy-atom coordinates for `chains`, each mapped to its
    position in `resnums` (this structure's own residue-sequence order).

    `holo_pocket_mask`/`functional_indices` are specified as a "heavy-atom
    distance contact set" (TASK-0004 Intent Contract) and the notebook's own
    precedent (`residues_near(model, ag, sel_string, cut)`, Sec.1) contacts
    against full protein heavy atoms, not just Calpha -- confirmed material
    in the TASK-0004 KRAS_G12C integration check (2026-07-06): a Calpha-only
    approximation recovered only 9/21 of `backend/systems.py`'s
    `pocket_full[4.5]` residues, because side-chain atoms reach several A
    closer to a bound ligand than Calpha does. This adapter supplies the
    real heavy-atom set so `holo_pocket_mask` can contact-test properly.

    Returns `(heavy_atom_coords, seq_index)`: `seq_index[k]` is the position
    in `resnums` that `heavy_atom_coords[k]` belongs to, so per-atom contact
    hits (from `residues_near`) can be aggregated back to whole-residue hits
    without assuming one row per residue. Atoms whose resnum isn't in
    `resnums` (e.g. a chain-selection mismatch) are dropped, not errored.
    """
    chain_sel = " or ".join(f"chain {c}" for c in chains)
    prot = ag.select(f"protein and ({chain_sel}) and not hetero")
    if prot is None:
        return np.zeros((0, 3)), np.zeros(0, dtype=int)
    resnum_to_seq_idx = {int(r): i for i, r in enumerate(resnums)}
    atom_resnums = prot.getResnums()
    seq_index = np.array(
        [resnum_to_seq_idx.get(int(r), -1) for r in atom_resnums], dtype=int
    )
    keep = seq_index >= 0
    return prot.getCoords()[keep], seq_index[keep]


# ---------------------------------------------------------------------------
# Contact geometry
# ---------------------------------------------------------------------------

def residues_near(
    coords: np.ndarray,
    ligand_coords: np.ndarray,
    cutoff: float = 4.5,
) -> np.ndarray:
    """Indices into `coords` within `cutoff` A of any atom in `ligand_coords`.

    Reuses hamiltonians.contact_matrix's pairwise-distance pattern. `coords`
    is one representative point per residue (Calpha, matching this codebase's
    GNM convention throughout); `ligand_coords` is one row per ligand heavy
    atom. Returns a sorted 1-D int array of residue indices (positions into
    `coords`), matching notebook Sec.1's `residues_near` contract (indices,
    not a boolean mask).
    """
    if len(ligand_coords) == 0:
        return np.array([], dtype=int)
    diff = coords[:, np.newaxis, :] - ligand_coords[np.newaxis, :, :]
    dist = np.sqrt((diff ** 2).sum(axis=2))
    min_dist = dist.min(axis=1)
    return np.where(min_dist < cutoff)[0]


def _contact_residue_indices(
    coords: np.ndarray,
    ligand_coords: np.ndarray,
    cutoff: float,
    heavy_atom_coords: np.ndarray | None = None,
    heavy_atom_seq_index: np.ndarray | None = None,
) -> np.ndarray:
    """Residue-sequence indices in contact with `ligand_coords`.

    Uses full protein heavy atoms (`heavy_atom_coords`/`heavy_atom_seq_index`
    from `protein_heavy_atoms_by_residue`, aggregated back to residue level)
    when available; falls back to the Calpha-only approximation via `coords`
    otherwise (e.g. synthetic unit tests with no heavy-atom data). See
    `protein_heavy_atoms_by_residue`'s docstring for why this distinction is
    material, not cosmetic, for real structures.
    """
    if heavy_atom_coords is not None and len(heavy_atom_coords):
        atom_hits = residues_near(heavy_atom_coords, ligand_coords, cutoff=cutoff)
        if len(atom_hits) == 0:
            return np.array([], dtype=int)
        return np.unique(heavy_atom_seq_index[atom_hits])
    return residues_near(coords, ligand_coords, cutoff=cutoff)


def terminal_mask(n_residues: int, terminal_fraction: float = 0.05) -> np.ndarray:
    """Boolean mask marking N-/C-terminal residues.

    Same eligibility rule as potentials.V_T (identical n_term formula and
    index ranges), so pocket-eligibility filtering here and V_T's disorder
    penalty in H_new agree on what counts as "terminal." Returns a boolean
    vector, not a diagonal matrix -- V_T builds its own diagonal from this
    same rule.
    """
    n_term = max(1, int(n_residues * terminal_fraction))
    mask = np.zeros(n_residues, dtype=bool)
    mask[:n_term] = True
    mask[-n_term:] = True
    return mask


# ---------------------------------------------------------------------------
# Drug selection
# ---------------------------------------------------------------------------

def pick_drug(
    ligand_groups: list[LigandGroup],
    target_config: dict,
) -> LigandGroup | None:
    """Select the allosteric drug ligand via target_config's explicit
    `drug_ligand` 3-letter code -- never a "largest/first ligand" heuristic.

    That heuristic is exactly what produced the original BCR_ABL1 bug: NIL
    (a co-crystallized orthosteric-site inhibitor) out-sizes the true
    allosteric ligand, so "pick the biggest HETATM group" silently picked the
    wrong drug. An explicit per-target allow-list can't make that mistake.

    Returns None (flagged, not guessed) when `target_config` has no
    `drug_ligand` set, or when the named ligand isn't present in this holo
    structure -- callers must treat both as "pocket undetermined."
    """
    drug_ligand = target_config.get("drug_ligand")
    if not drug_ligand:
        return None
    for group in ligand_groups:
        if group.resname == drug_ligand:
            return group
    return None


# ---------------------------------------------------------------------------
# Sequence alignment (apo <-> holo residue-numbering map)
# ---------------------------------------------------------------------------

_THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}


def _sequence(resnames: list[str]) -> str:
    """3-letter resnames -> 1-letter sequence; non-standard residues -> 'X'."""
    return "".join(_THREE_TO_ONE.get(r.strip().upper(), "X") for r in resnames)


def _needleman_wunsch_map(
    seq_a: str,
    seq_b: str,
    match: float = 2.0,
    mismatch: float = -1.0,
    gap: float = -2.0,
) -> dict[int, int]:
    """Global (Needleman-Wunsch) alignment of seq_a against seq_b.

    Returns {index_in_seq_b: index_in_seq_a} for aligned (non-gap) columns
    only. O(n*m) DP -- these are single protein chains (hundreds of
    residues), not genome-scale sequences, so the quadratic cost is not a
    concern.
    """
    n, m = len(seq_a), len(seq_b)
    score = np.zeros((n + 1, m + 1))
    score[:, 0] = np.arange(n + 1) * gap
    score[0, :] = np.arange(m + 1) * gap
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = match if seq_a[i - 1] == seq_b[j - 1] else mismatch
            score[i, j] = max(
                score[i - 1, j - 1] + s,
                score[i - 1, j] + gap,
                score[i, j - 1] + gap,
            )

    b_to_a: dict[int, int] = {}
    i, j = n, m
    while i > 0 and j > 0:
        s = match if seq_a[i - 1] == seq_b[j - 1] else mismatch
        if score[i, j] == score[i - 1, j - 1] + s:
            b_to_a[j - 1] = i - 1
            i, j = i - 1, j - 1
        elif score[i, j] == score[i - 1, j] + gap:
            i -= 1
        else:
            j -= 1
    return b_to_a


def holo_pocket_mask(
    apo,
    holo,
    ligand_code: str,
    cutoff: float = 4.5,
) -> np.ndarray | None:
    """Boolean pocket mask on *apo* numbering, derived from holo ligand contacts.

    Maps holo ligand-contact residues back onto the apo residue numbering via
    global sequence alignment (`_needleman_wunsch_map`) -- not residue-number
    equality, which breaks on numbering offsets between apo/holo constructs
    (e.g. the ABL1 1a/1b +19-residue offset,
    SYSTEMS_allosteric_corrected_v2.md).

    `apo`/`holo` are CleanResult-shaped (`.coords`, `.resnums`, `.resnames`);
    `holo` additionally exposes `.ligand_groups: list[LigandGroup]` -- this
    module's own contract, since clean.py's CleanResult is protein-only by
    design (see `ligand_groups_from_atomgroup` for the prody-side adapter
    that builds this field for a real fetched structure). `holo` may
    optionally also expose `.heavy_atom_coords`/`.heavy_atom_seq_index`
    (from `protein_heavy_atoms_by_residue`) for true heavy-atom contact
    distance, per this task's Intent Contract; without them this falls back
    to a Calpha-only approximation (see `_contact_residue_indices`).

    Returns None (flagged) if `ligand_code` isn't found among
    `holo.ligand_groups` -- mirrors `pick_drug`'s "never guess" contract.
    """
    ligand = next(
        (g for g in holo.ligand_groups if g.resname == ligand_code), None
    )
    if ligand is None:
        return None

    contact_idx = _contact_residue_indices(
        holo.coords,
        ligand.coords,
        cutoff,
        heavy_atom_coords=getattr(holo, "heavy_atom_coords", None),
        heavy_atom_seq_index=getattr(holo, "heavy_atom_seq_index", None),
    )
    if len(contact_idx) == 0:
        return np.zeros(len(apo.resnums), dtype=bool)

    apo_seq = _sequence(apo.resnames)
    holo_seq = _sequence(holo.resnames)
    holo_to_apo = _needleman_wunsch_map(apo_seq, holo_seq)

    mask = np.zeros(len(apo.resnums), dtype=bool)
    for h_idx in contact_idx:
        a_idx = holo_to_apo.get(int(h_idx))
        if a_idx is not None:
            mask[a_idx] = True
    return mask


# ---------------------------------------------------------------------------
# Functional / active-site seed
# ---------------------------------------------------------------------------

def functional_indices(
    coords: np.ndarray,
    ligand_groups: list[LigandGroup],
    target_config: dict,
    cutoff: float = 4.5,
    heavy_atom_coords: np.ndarray | None = None,
    heavy_atom_seq_index: np.ndarray | None = None,
) -> tuple[np.ndarray, str]:
    """Active/catalytic-site indices to seed the CTQW from (and exclude from
    the pocket label).

    Tiered, ported from notebook Sec.1's `functional_indices` -- but tier 1
    there (`target_config["active_site"]` resnums) does not exist in the
    schema TASK-0003 actually produced: `targets.yaml` has no `active_site`
    field, only `func_ligand` (ligand code(s)/marker(s) to exclude, e.g.
    KRAS_G12C's `["GDP"]`, BCR_ABL1's `["NIL"]`). This was corrected once
    `targets.yaml` landed (this session) -- the original resnum-anchor tier
    would have silently never matched real data. Tiers, against the real
    schema:

    1. `func_ligand` contact -- for each code in `target_config["func_ligand"]`
       that resolves to a real bound ligand in `ligand_groups`, the residues
       within `cutoff` of it (same contact geometry as `pick_drug`/
       `holo_pocket_mask`, applied to the orthosteric ligand instead of the
       allosteric one). Some `func_ligand` entries are descriptive text, not
       RCSB codes (e.g. PTP1B's "pTyr / active-site Cys215 (descriptive
       marker, not a ligand code)") or non-HETATM polymers (MYC_MAX's
       `"DNA"`) -- those never match a `ligand_groups` resname and fall
       through to tier 2, they are not treated as an error.
    2. last resort -- top-5 contact-degree residues (least informative;
       signals that no resolvable functional ligand was available for this
       target).

    Returns (indices, provenance_string).
    """
    for code in (target_config.get("func_ligand") or []):
        ligand = next((g for g in ligand_groups if g.resname == code), None)
        if ligand is None:
            continue
        idx = _contact_residue_indices(
            coords,
            ligand.coords,
            cutoff,
            heavy_atom_coords=heavy_atom_coords,
            heavy_atom_seq_index=heavy_atom_seq_index,
        )
        if len(idx):
            return idx, f"func_ligand-contact:{code}"

    from .hamiltonians import contact_matrix

    # TASK-0216: this fallback is a LAST RESORT and must never pass silently.
    # It returns the 5 highest-degree residues as a stand-in "active site" --
    # a topological proxy, not a functional site -- and that is actively
    # dangerous for two compounding reasons:
    #   1. Any active-site-seeded observable becomes a function of graph
    #      degree, so its mechanistic reading ("coupling from the catalytic
    #      site") is not what was measured.
    #   2. `baselines.degree_centrality` is one of the three proximity-floor
    #      baselines, so observable and floor then share a construction and
    #      the comparison is no longer independent.
    # Found firing silently on 9 of 13 register targets -- including PTP1B,
    # which carries the register's only surviving positive. Cause in every
    # case: `func_ligand` held a human-readable description ('Glucose',
    # 'substrate', 'O2', 'Asp') rather than a PDB chem-comp code, so no
    # ligand ever matched.
    declared = target_config.get("func_ligand") or []
    warnings.warn(
        "functional_indices: no func_ligand match"
        + (f" for declared {declared!r}" if declared else " (func_ligand empty)")
        + " -- falling back to the top-5 highest-degree residues. This is a "
        "TOPOLOGICAL PROXY, not a functional site: active-site-seeded "
        "observables computed on it do not measure active-site coupling, and "
        "are correlated with degree_centrality, itself a proximity-floor "
        "baseline. Supply real chem-comp codes in `func_ligand`, or a "
        "UniProt-derived active site (see backend/active_site.py).",
        RuntimeWarning,
        stacklevel=2,
    )
    A = contact_matrix(coords, cutoff=9.0, weight="binary")
    degree = A.sum(axis=1)
    return np.argsort(-degree)[:5], "top-degree fallback"


# ---------------------------------------------------------------------------
# Assembly -- the actual pocket label (TASK-0070, SEAM-0003)
# ---------------------------------------------------------------------------
#
# Oldest live defect this closes (EXECUTION_PLAN.md Phase 0, item 0.1):
# nothing assembled `pocket & ~functional & ~terminal` -- labels.py owned
# the three ingredients (holo_pocket_mask, functional_indices,
# terminal_mask), protocol.py gated access to them, and analysis.py scored
# whatever raw mask a caller handed it. Each piece was individually
# correct and tested; the composition was never assembled, so the
# exclusion invariant `pocket ∩ (functional ∪ terminal) == ∅` had no
# function anywhere that actually executed it (SEAM-0003, seeded directly
# from SEAM_PROTOCOL.md's own motivating example -- this exact gap).

@dataclass
class Labels:
    """The final, assembled pocket label plus every ingredient that went
    into it -- the single object downstream code (protocol.py's gate,
    analysis.py's scoring) should consume instead of a raw, unexcluded
    mask."""

    pocket: np.ndarray | None       # (N,) bool over apo residues, excludes active_site + terminal; None if undetermined (no resolvable drug ligand)
    pocket_raw: np.ndarray | None   # (N,) bool, the ligand-contact mask BEFORE exclusion (diagnostics only -- never score against this)
    active_site: np.ndarray         # (N,) bool -- the functional/catalytic seed set (functional_indices, as a mask)
    terminal: np.ndarray            # (N,) bool -- terminal_mask's output
    functional_provenance: str      # functional_indices' own provenance string (e.g. "func_ligand-contact:GDP")
    drug_ligand: str | None         # the allosteric ligand code used for pocket_raw, or None if unresolved


def build_labels(
    apo,
    holo,
    target_config: dict,
    cutoff: float = 4.5,
    terminal_fraction: float = 0.05,
) -> Labels:
    """Assemble the final pocket label: `pocket_raw & ~active_site & ~terminal`.

    This is the one function that actually executes SEAM-0003's invariant
    (`pocket ∩ (functional ∪ terminal) == ∅`) rather than leaving it as a
    docstring claim -- asserted below, not just documented, so a future
    regression here fails loudly instead of silently shipping an
    unexcluded label.

    `func_ligand` contacts (the active site) are excluded even when they
    also happen to be near the allosteric ligand -- this is what resolves
    TASK-0070's KRAS Cys12 decision: Cys12 is the covalent anchor for
    sotorasib (MOV), so it appears in `pocket_raw`, but it is *also* a
    GDP-contact residue (`targets.yaml`'s own literature note: "EXCLUDE
    Cys12/P-loop"), so it is excluded here by the same general rule that
    excludes every other active-site residue -- no special-casing needed,
    confirmed empirically against real KRAS_G12C data (4OBE/6OIM) in this
    task rather than assumed (`tests/test_labels.py::
    TestBuildLabels::test_kras_g12c_real_cys12_excluded`).

    Uses `holo.heavy_atom_coords`/`.heavy_atom_seq_index` for both the
    pocket and active-site contact geometry when present on `holo` (same
    optional attributes `holo_pocket_mask`/`functional_indices` already
    accept), falling back to the Calpha-only approximation otherwise.
    """
    n = len(apo.resnums)
    ligand_code = target_config.get("drug_ligand")
    heavy_atom_coords = getattr(holo, "heavy_atom_coords", None)
    heavy_atom_seq_index = getattr(holo, "heavy_atom_seq_index", None)

    pocket_raw = (
        holo_pocket_mask(apo, holo, ligand_code, cutoff=cutoff) if ligand_code else None
    )

    func_idx, provenance = functional_indices(
        apo.coords,
        holo.ligand_groups,
        target_config,
        cutoff=cutoff,
        heavy_atom_coords=heavy_atom_coords,
        heavy_atom_seq_index=heavy_atom_seq_index,
    )
    active_site = np.zeros(n, dtype=bool)
    active_site[func_idx] = True
    terminal = terminal_mask(n, terminal_fraction)

    if pocket_raw is None:
        pocket = None
    else:
        pocket = pocket_raw & ~active_site & ~terminal
        assert not (pocket & active_site).any(), (
            "SEAM-0003 invariant violated: assembled pocket intersects "
            "active_site -- this must never happen, the exclusion above "
            "is exactly what prevents it."
        )
        assert not (pocket & terminal).any(), (
            "SEAM-0003 invariant violated: assembled pocket intersects "
            "the terminal mask."
        )

    return Labels(
        pocket=pocket,
        pocket_raw=pocket_raw,
        active_site=active_site,
        terminal=terminal,
        functional_provenance=provenance,
        drug_ligand=ligand_code,
    )
