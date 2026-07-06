"""TASK-0004 coverage -- labels.py pocket/label derivation.

Synthetic apo/holo coordinate pairs only (no network fetch, no prody
dependency for these tests) -- the real KRAS_G12C integration check ran
separately (session-local scratch script, not committed) once TASK-0003's
targets.yaml landed: derived pocket matched backend/systems.py's
pocket_full[4.5] 21/21 residues using the heavy-atom contact path
(protein_heavy_atoms_by_residue), vs. 9/21 with the Calpha-only
approximation alone -- see TASK-0004's Done section for the full numbers.
"""
import numpy as np
import pytest

from allostery.labels import (
    LigandGroup,
    _contact_residue_indices,
    functional_indices,
    holo_pocket_mask,
    ligand_groups_from_atomgroup,
    pick_drug,
    protein_heavy_atoms_by_residue,
    residues_near,
    terminal_mask,
)


def _helix_coords(n: int) -> np.ndarray:
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


N = 12
COORDS = _helix_coords(N)
# a 3-letter sequence long enough to exercise alignment; arbitrary but valid.
_SEQ3 = ["ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE", "LEU", "LYS"]


class _Struct:
    """Minimal CleanResult-shaped stand-in for apo/holo in these tests."""

    def __init__(self, coords, resnums, resnames, ligand_groups=None):
        self.coords = coords
        self.resnums = np.asarray(resnums)
        self.resnames = list(resnames)
        self.ligand_groups = ligand_groups or []


class TestResiduesNear:
    def test_finds_contacts_within_cutoff(self):
        ligand = np.array([COORDS[5]])  # sits exactly on residue 5
        idx = residues_near(COORDS, ligand, cutoff=4.5)
        assert 5 in idx

    def test_excludes_far_residues(self):
        # displace the "ligand" far away from the whole helix
        ligand = COORDS[[5]] + np.array([100.0, 100.0, 100.0])
        idx = residues_near(COORDS, ligand, cutoff=4.5)
        assert len(idx) == 0

    def test_empty_ligand_returns_empty(self):
        idx = residues_near(COORDS, np.zeros((0, 3)), cutoff=4.5)
        assert len(idx) == 0

    def test_returns_indices_not_mask(self):
        ligand = np.array([COORDS[0]])
        idx = residues_near(COORDS, ligand, cutoff=4.5)
        assert idx.dtype.kind == "i"
        assert idx.max() < N


class TestTerminalMask:
    def test_matches_potentials_v_t_convention(self):
        from allostery.potentials import V_T

        mask = terminal_mask(N, terminal_fraction=0.2)
        diag = np.diag(V_T(N, terminal_fraction=0.2))
        np.testing.assert_array_equal(mask, diag.astype(bool))

    def test_boolean_dtype_and_shape(self):
        mask = terminal_mask(N, terminal_fraction=0.2)
        assert mask.dtype == bool
        assert mask.shape == (N,)


class TestPickDrug:
    def _groups(self):
        return [
            LigandGroup("NIL", 501, "A", np.zeros((30, 3)), 30),   # bigger
            LigandGroup("AY7", 502, "A", np.zeros((10, 3)), 10),   # smaller, true drug
        ]

    def test_explicit_allow_list_wins_over_size(self):
        drug = pick_drug(self._groups(), {"drug_ligand": "AY7"})
        assert drug is not None
        assert drug.resname == "AY7"

    def test_no_drug_ligand_configured_returns_none_not_a_guess(self):
        """Regression for the NIL-vs-asciminib bug: with no explicit config,
        never fall back to "pick the biggest ligand"."""
        drug = pick_drug(self._groups(), {})
        assert drug is None

    def test_configured_ligand_absent_returns_none(self):
        drug = pick_drug(self._groups(), {"drug_ligand": "ZZZ"})
        assert drug is None


class TestHoloPocketMask:
    def test_identical_numbering_direct_contact_maps_through(self):
        apo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3)
        ligand = LigandGroup("AY7", 900, "A", np.array([COORDS[6]]), 1)
        holo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3, [ligand])

        mask = holo_pocket_mask(apo, holo, "AY7", cutoff=4.5)
        assert mask is not None
        assert mask[6]
        assert mask.sum() >= 1

    def test_numbering_offset_still_maps_correctly(self):
        """Same sequence, holo resnums shifted by +19 (ABL1 1a/1b-style
        offset) -- alignment must still map the contact residue back onto
        the correct apo index, not the same array position."""
        apo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3)
        holo_resnums = np.arange(1, N + 1) + 19
        ligand = LigandGroup("AY7", 900, "A", np.array([COORDS[6]]), 1)
        holo = _Struct(COORDS, holo_resnums, _SEQ3, [ligand])

        mask = holo_pocket_mask(apo, holo, "AY7", cutoff=4.5)
        assert mask is not None
        # same sequence position (index 6) must still be flagged in apo space
        assert mask[6]

    def test_missing_ligand_code_returns_none(self):
        apo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3)
        holo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3, [])

        mask = holo_pocket_mask(apo, holo, "AY7", cutoff=4.5)
        assert mask is None

    def test_no_contacts_returns_all_false_mask(self):
        apo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3)
        far_ligand = LigandGroup(
            "AY7", 900, "A", np.array([COORDS[0] + 500.0]), 1
        )
        holo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3, [far_ligand])

        mask = holo_pocket_mask(apo, holo, "AY7", cutoff=4.5)
        assert mask is not None
        assert not mask.any()


class TestFunctionalIndices:
    def test_func_ligand_contact_from_target_config(self):
        """Real targets.yaml schema: func_ligand is a list of ligand codes
        (e.g. KRAS_G12C's ["GDP"]), not a resnum list -- functional_indices
        must resolve it via ligand contact, same geometry as pick_drug."""
        gdp = LigandGroup("GDP", 200, "A", np.array([COORDS[4]]), 1)
        idx, provenance = functional_indices(
            COORDS, [gdp], {"func_ligand": ["GDP"]}
        )
        assert provenance == "func_ligand-contact:GDP"
        assert 4 in idx

    def test_falls_back_to_top_degree_when_no_func_ligand(self):
        idx, provenance = functional_indices(COORDS, [], {})
        assert provenance == "top-degree fallback"
        assert len(idx) == 5

    def test_falls_back_when_func_ligand_is_descriptive_text_not_a_code(self):
        """PTP1B-style: func_ligand is free text ("pTyr / active-site
        Cys215 (descriptive marker, not a ligand code)"), never a resname
        present in ligand_groups -- must fall through gracefully, not error."""
        idx, provenance = functional_indices(
            COORDS, [], {"func_ligand": ["pTyr / active-site Cys215 (descriptive marker, not a ligand code)"]}
        )
        assert provenance == "top-degree fallback"

    def test_falls_back_when_configured_ligand_not_present_in_structure(self):
        idx, provenance = functional_indices(
            COORDS, [], {"func_ligand": ["DNA"]}
        )
        assert provenance == "top-degree fallback"


class _FakeAtom:
    def __init__(self, resname, resnum, chid, coords):
        self._resname = resname
        self._resnum = resnum
        self._chid = chid
        self._coords = np.array(coords, dtype=float)

    def getResname(self):
        return self._resname

    def getResnum(self):
        return self._resnum

    def getChid(self):
        return self._chid

    def getCoords(self):
        return self._coords


class _FakeAtomGroup:
    """Duck-typed prody AtomGroup stand-in exposing only what
    ligand_groups_from_atomgroup uses (select/iterAtoms)."""

    def __init__(self, hetero_atoms):
        self._hetero_atoms = hetero_atoms

    def select(self, sel_string):
        assert sel_string == "hetatm and not water"
        return self if self._hetero_atoms else None

    def iterAtoms(self):
        return iter(self._hetero_atoms)


class TestLigandGroupsFromAtomgroup:
    def test_groups_atoms_by_residue(self):
        atoms = [
            _FakeAtom("AY7", 502, "A", [1.0, 0.0, 0.0]),
            _FakeAtom("AY7", 502, "A", [2.0, 0.0, 0.0]),
            _FakeAtom("NIL", 501, "A", [5.0, 0.0, 0.0]),
        ]
        ag = _FakeAtomGroup(atoms)
        groups = ligand_groups_from_atomgroup(ag)

        by_resname = {g.resname: g for g in groups}
        assert set(by_resname) == {"AY7", "NIL"}
        assert by_resname["AY7"].n_atoms == 2
        assert by_resname["NIL"].n_atoms == 1
        assert by_resname["AY7"].coords.shape == (2, 3)

    def test_no_hetero_atoms_returns_empty(self):
        ag = _FakeAtomGroup([])
        assert ligand_groups_from_atomgroup(ag) == []


class _FakeSelection:
    def __init__(self, coords, resnums):
        self._coords = np.array(coords, dtype=float)
        self._resnums = np.array(resnums)

    def getCoords(self):
        return self._coords

    def getResnums(self):
        return self._resnums


class _FakeAtomGroupWithProtein:
    """Duck-typed prody AtomGroup stand-in for protein_heavy_atoms_by_residue."""

    def __init__(self, protein_selection):
        self._protein_selection = protein_selection

    def select(self, sel_string):
        assert sel_string == "protein and (chain A) and not hetero"
        return self._protein_selection


class TestProteinHeavyAtomsByResidue:
    def test_maps_atoms_to_sequence_position(self):
        # 2 heavy atoms on residue 10, 1 on residue 12; resnums defines the
        # structure's own sequence order [10, 11, 12].
        sel = _FakeSelection(
            coords=[[0.0, 0.0, 0.0], [0.1, 0.0, 0.0], [5.0, 0.0, 0.0]],
            resnums=[10, 10, 12],
        )
        ag = _FakeAtomGroupWithProtein(sel)
        coords, seq_idx = protein_heavy_atoms_by_residue(ag, ["A"], np.array([10, 11, 12]))

        assert coords.shape == (3, 3)
        np.testing.assert_array_equal(seq_idx, [0, 0, 2])

    def test_drops_atoms_whose_resnum_is_not_in_resnums(self):
        sel = _FakeSelection(coords=[[0.0, 0.0, 0.0]], resnums=[999])
        ag = _FakeAtomGroupWithProtein(sel)
        coords, seq_idx = protein_heavy_atoms_by_residue(ag, ["A"], np.array([10, 11, 12]))

        assert coords.shape == (0, 3)
        assert seq_idx.shape == (0,)

    def test_no_protein_selection_returns_empty(self):
        ag = _FakeAtomGroupWithProtein(None)
        coords, seq_idx = protein_heavy_atoms_by_residue(ag, ["A"], np.array([10, 11, 12]))
        assert coords.shape == (0, 3)
        assert seq_idx.shape == (0,)


class TestContactResidueIndicesHeavyAtomFix:
    """Regression coverage for the Calpha-vs-heavy-atom gap found in the
    TASK-0004 KRAS_G12C integration check (9/21 pocket residues recovered
    with Calpha only, 21/21 with real heavy atoms)."""

    def test_heavy_atom_path_catches_a_contact_calpha_alone_misses(self):
        # Residue 0's Calpha sits 6.0 A from the ligand (outside a 4.5 A
        # cutoff), but one of its heavy atoms (a "side chain" point) sits
        # right on top of the ligand.
        ca_coords = np.array([[6.0, 0.0, 0.0], [50.0, 0.0, 0.0]])
        ligand_coords = np.array([[0.0, 0.0, 0.0]])
        heavy_coords = np.array([[6.0, 0.0, 0.0], [0.2, 0.0, 0.0], [50.0, 0.0, 0.0]])
        heavy_seq_idx = np.array([0, 0, 1])  # first two atoms both belong to residue 0

        without_heavy = _contact_residue_indices(ca_coords, ligand_coords, cutoff=4.5)
        assert list(without_heavy) == []  # Calpha-only misses it entirely

        with_heavy = _contact_residue_indices(
            ca_coords, ligand_coords, cutoff=4.5,
            heavy_atom_coords=heavy_coords, heavy_atom_seq_index=heavy_seq_idx,
        )
        assert list(with_heavy) == [0]

    def test_empty_heavy_atom_coords_falls_back_to_calpha(self):
        ca_coords = np.array([[0.0, 0.0, 0.0]])
        ligand_coords = np.array([[0.1, 0.0, 0.0]])
        idx = _contact_residue_indices(
            ca_coords, ligand_coords, cutoff=4.5,
            heavy_atom_coords=np.zeros((0, 3)), heavy_atom_seq_index=np.zeros(0, dtype=int),
        )
        assert list(idx) == [0]


class TestHoloPocketMaskHeavyAtomPath:
    def test_uses_heavy_atoms_when_provided(self):
        apo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3)
        # Calpha of residue 6 is far from the ligand; a heavy atom on that
        # same residue is right on top of it.
        far_point = COORDS[6] + np.array([100.0, 0.0, 0.0])
        ligand = LigandGroup("AY7", 900, "A", np.array([far_point]), 1)
        holo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3, [ligand])
        holo.heavy_atom_coords = np.array([far_point])
        holo.heavy_atom_seq_index = np.array([6])

        mask = holo_pocket_mask(apo, holo, "AY7", cutoff=4.5)
        assert mask is not None
        assert mask[6]
        # residue 6's own Calpha (in COORDS) is nowhere near far_point --
        # confirms the hit came from the heavy-atom path, not Calpha.
        assert np.linalg.norm(COORDS[6] - far_point) > 4.5
