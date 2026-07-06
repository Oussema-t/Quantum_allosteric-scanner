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

    A = contact_matrix(coords, cutoff=9.0, weight="binary")
    degree = A.sum(axis=1)
    return np.argsort(-degree)[:5], "top-degree fallback"
