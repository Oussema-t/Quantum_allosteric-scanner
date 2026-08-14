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
    build_labels,
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
        """V_T is z-scored (TASK-0121), so its diagonal is nonzero
        everywhere -- the shared convention with `terminal_mask` is now the
        *sign*, not zero-ness: termini score strictly higher (positive)
        than the core (negative)."""
        from allostery.potentials import V_T

        mask = terminal_mask(N, terminal_fraction=0.2)
        diag = np.diag(V_T(N, terminal_fraction=0.2))
        np.testing.assert_array_equal(mask, diag > 0)

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

    def test_indel_case_needleman_wunsch_recovers_correct_apo_index(self):
        """TASK-0047 P3: a genuine insertion/deletion -- apo and holo
        sequences of DIFFERENT length, not just re-numbered -- so this
        actually exercises _needleman_wunsch_map's gap handling. Distinct
        from test_numbering_offset_still_maps_correctly above: that test
        checks numbering-INDEPENDENCE (same sequence, shifted resnums, a
        constant offset would also pass it); this one checks
        alignment-CORRECTNESS-UNDER-GAPS (a naive positional mapper, or a
        constant-offset mapper, both fail this one, since the correct
        apo<->holo offset changes before vs. after the deletion).

        apo (13 residues): ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS PHE
        holo (12 residues): apo with index 6 ("GLU") deleted, i.e.
                             ALA ARG ASN ASP CYS GLN GLY HIS ILE LEU LYS PHE

        The ligand sits at holo index 8; adjacent helix residues are only
        ~3.8 A apart (inside the 4.5 A contact cutoff), so holo indices
        7/8/9 all legitimately contact it -- this test does not assume a
        single hit. Under the correct gap-aware mapping those become apo
        indices 8/9/10; under a naive same-position (non-aligned) mapper
        they would instead become apo indices 7/8/9. The two hypotheses
        share indices 8-9 but disagree at the edges, so the discriminating
        assertions are: apo index 10 (only reachable via correct alignment)
        IS flagged, and apo index 7 (only produced by the wrong, naive
        mapping) is NOT.
        """
        apo_seq3 = ["ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU",
                    "GLY", "HIS", "ILE", "LEU", "LYS", "PHE"]
        holo_seq3 = apo_seq3[:6] + apo_seq3[7:]  # delete index 6 ("GLU")
        assert len(apo_seq3) == 13 and len(holo_seq3) == 12

        apo_coords = _helix_coords(13)
        holo_coords = _helix_coords(12)
        apo = _Struct(apo_coords, np.arange(1, 14), apo_seq3)
        ligand = LigandGroup("AY7", 900, "A", np.array([holo_coords[8]]), 1)
        holo = _Struct(holo_coords, np.arange(1, 13), holo_seq3, [ligand])

        mask = holo_pocket_mask(apo, holo, "AY7", cutoff=4.5)
        assert mask is not None
        assert mask[10], (
            "gap-aware alignment must map holo index 9 -> apo index 10 -- "
            "unreachable under a naive same-position mapper, which would "
            "cap out at apo index 9"
        )
        assert not mask[7], (
            "apo index 7 must NOT be flagged -- a naive same-position "
            "mapper would wrongly produce it (holo index 7 -> apo index 7), "
            "but the correct gap-aware mapping sends holo index 7 -> apo "
            "index 8 instead"
        )

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

    def test_cross_structure_heavy_atoms_translated_to_coords_space(self):
        """TASK-0217.001's retrospective-test defect #2, reconstructed
        synthetically: heavy_atom_coords/heavy_atom_seq_index belong to a
        *different* structure (holo) than `coords` (apo), and apo/holo
        differ by a 2-residue numbering offset (holo is missing apo's
        first two residues) -- the exact shape confirmed on real
        KRAS_G12C/BCR_ABL1 data. Without heavy_atom_resnames/
        coords_resnames, the pre-fix code would return holo-space index 0
        (out of range interpretation: apo residue 0, wrong) instead of the
        true apo-space index 2. With them supplied, the translation must
        land on the correct apo residue."""
        apo_resnames = _SEQ3  # 12 residues, apo's own numbering 0..11
        holo_resnames = _SEQ3[2:]  # holo is missing apo's first 2 residues
        # One holo heavy atom, on holo's own residue 0 (== apo residue 2),
        # sitting on top of the ligand.
        ligand = LigandGroup("LIG", 900, "A", np.array([[0.0, 0.0, 0.0]]), 1)
        heavy_atom_coords = np.array([[0.0, 0.0, 0.0]])
        heavy_atom_seq_index = np.array([0])

        idx, provenance = functional_indices(
            COORDS, [ligand], {"func_ligand": ["LIG"]},
            heavy_atom_coords=heavy_atom_coords,
            heavy_atom_seq_index=heavy_atom_seq_index,
            heavy_atom_resnames=holo_resnames,
            coords_resnames=apo_resnames,
        )
        assert provenance == "func_ligand-contact:LIG"
        assert list(idx) == [2], (
            f"expected translated apo-space index [2] (holo residue 0 -> "
            f"apo residue 2 under the 2-residue offset), got {list(idx)} "
            "-- the cross-structure translation is not landing correctly."
        )

    def test_cross_structure_heavy_atoms_without_resnames_raises(self):
        """The bug this guard exists to close: heavy_atom_coords/
        heavy_atom_seq_index provably belong to a different, longer
        structure than `coords` (indices exceed len(coords)) and no
        resname pair was supplied to translate -- must raise, not
        silently return the wrong-space indices (TASK-0217.001)."""
        ligand = LigandGroup("LIG", 900, "A", np.array([[0.0, 0.0, 0.0]]), 1)
        heavy_atom_coords = np.array([[0.0, 0.0, 0.0]])
        heavy_atom_seq_index = np.array([len(COORDS) + 5])  # provably out of range

        with pytest.raises(ValueError, match="different structure"):
            functional_indices(
                COORDS, [ligand], {"func_ligand": ["LIG"]},
                heavy_atom_coords=heavy_atom_coords,
                heavy_atom_seq_index=heavy_atom_seq_index,
            )

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


# ---------------------------------------------------------------------------
# TASK-0070 / SEAM-0003 -- build_labels' assembly + exclusion invariant
# ---------------------------------------------------------------------------

class TestBuildLabels:
    def test_excludes_functional_overlap_from_pocket(self):
        """The exact SEAM-0003 case: the drug ligand's raw contact set
        overlaps the functional (orthosteric) ligand's -- the assembled
        pocket must exclude the overlap, not just the non-overlapping
        functional residues."""
        apo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3)
        # drug ligand near residues 4,5,6; functional ligand near residue 5
        # (deliberately overlapping with the drug contact, like KRAS Cys12
        # sitting in both the MOV covalent-contact set and the GDP-contact
        # functional set).
        drug = LigandGroup("LIG", 501, "A", np.array([COORDS[5]]), 1)
        func = LigandGroup("FUNC", 502, "A", np.array([COORDS[5]]), 1)
        holo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3, [drug, func])

        labels = build_labels(apo, holo, {"drug_ligand": "LIG", "func_ligand": ["FUNC"]}, cutoff=4.5)

        assert labels.pocket_raw[5]     # raw contact hit, before exclusion
        assert labels.active_site[5]    # also a functional-contact hit
        assert not labels.pocket[5]     # excluded from the final label
        assert not (labels.pocket & labels.active_site).any()
        assert not (labels.pocket & labels.terminal).any()

    def test_disjoint_functional_and_drug_leaves_pocket_populated(self):
        apo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3)
        drug = LigandGroup("LIG", 501, "A", np.array([COORDS[5]]), 1)
        func = LigandGroup("FUNC", 502, "A", np.array([COORDS[10]]), 1)
        holo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3, [drug, func])

        labels = build_labels(apo, holo, {"drug_ligand": "LIG", "func_ligand": ["FUNC"]}, cutoff=4.5)

        assert labels.pocket is not None and labels.pocket.any()
        assert not (labels.pocket & labels.active_site).any()

    def test_no_drug_ligand_gives_none_pocket_not_a_crash(self):
        apo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3)
        func = LigandGroup("FUNC", 502, "A", np.array([COORDS[10]]), 1)
        holo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3, [func])

        labels = build_labels(apo, holo, {"func_ligand": ["FUNC"]}, cutoff=4.5)

        assert labels.pocket is None
        assert labels.pocket_raw is None
        assert labels.active_site.any()  # functional side still resolves

    def test_provenance_and_drug_ligand_recorded(self):
        apo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3)
        drug = LigandGroup("LIG", 501, "A", np.array([COORDS[5]]), 1)
        func = LigandGroup("FUNC", 502, "A", np.array([COORDS[10]]), 1)
        holo = _Struct(COORDS, np.arange(1, N + 1), _SEQ3, [drug, func])

        labels = build_labels(apo, holo, {"drug_ligand": "LIG", "func_ligand": ["FUNC"]}, cutoff=4.5)

        assert labels.drug_ligand == "LIG"
        assert labels.functional_provenance == "func_ligand-contact:FUNC"


# ---------------------------------------------------------------------------
# Real-target checks (KRAS_G12C, BCR_ABL1) -- skipped where prody/network is
# unavailable. TASK-0070's own Acceptance Scenario: assert the exclusion
# invariant holds on real benchmark targets, and record the KRAS Cys12
# in/out decision explicitly rather than by omission.
# ---------------------------------------------------------------------------

def _load_real_target(apo_id, holo_id, chains):
    from allostery.clean import clean
    import prody

    prody.confProDy(verbosity="none")
    apo = clean(apo_id, chains=chains)
    holo = clean(holo_id, chains=chains)
    holo_struct = prody.parsePDB(holo_id, compressed=False).select(
        " or ".join(f"chain {c}" for c in chains)
    )
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, chains, holo.resnums
    )
    return apo, holo


def test_kras_g12c_real_cys12_excluded():
    """TASK-0070's recorded Cys12 decision: sotorasib (MOV) is covalently
    anchored at Cys12, so Cys12 lands in `pocket_raw` -- but Cys12 is also
    a GDP-contact (functional/active-site) residue, so it is excluded by
    the *general* `~active_site` rule, not a KRAS-specific special case.
    `targets.yaml`'s own literature note ("EXCLUDE Cys12/P-loop") is
    satisfied automatically. Verified here against real 4OBE apo / 6OIM
    holo data (2026-07-12), not assumed."""
    pytest.importorskip("prody")
    try:
        apo, holo = _load_real_target("4OBE", "6OIM", ["A"])
    except Exception as exc:
        pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")

    labels = build_labels(apo, holo, {"drug_ligand": "MOV", "func_ligand": ["GDP"]}, cutoff=4.5)

    cys12_idx = np.where(apo.resnums == 12)[0]
    assert len(cys12_idx) == 1
    i = cys12_idx[0]

    assert labels.pocket_raw[i], "expected Cys12 in the raw MOV-contact set (it's the covalent anchor)"
    assert labels.active_site[i], "expected Cys12 in the GDP-contact functional set"
    assert not labels.pocket[i], "Cys12 must be excluded from the final assembled pocket"
    assert not (labels.pocket & labels.active_site).any()
    assert not (labels.pocket & labels.terminal).any()
    assert labels.pocket.sum() > 0, "exclusion should not have emptied the whole pocket"


def test_bcr_abl1_real_exclusion_invariant_holds():
    """Second independent real target (not just KRAS) for the exclusion
    invariant, per this task's own review -- confirms the fix generalizes
    rather than being tuned to one benchmark."""
    pytest.importorskip("prody")
    try:
        apo, holo = _load_real_target("1OPL", "5MO4", ["A"])
    except Exception as exc:
        pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")

    labels = build_labels(apo, holo, {"drug_ligand": "AY7", "func_ligand": ["NIL"]}, cutoff=4.5)

    assert labels.pocket is not None and labels.pocket.any()
    assert not (labels.pocket & labels.active_site).any()
    assert not (labels.pocket & labels.terminal).any()
    # the exclusion must have actually removed something on this target too
    # (not a no-op that happens to pass because nothing overlapped).
    assert labels.pocket.sum() < labels.pocket_raw.sum()


def test_kras_g12c_real_holo_pocket_mask_matches_systems_py_pocket_full():
    """TASK-0047 P2 (the piece TASK-0070's Cys12 test doesn't cover): load
    KRAS_G12C via `load_target_config` (TASK-0003's loader) rather than a
    hand-built dict, exercising the TASK-0003->TASK-0004 config handoff
    end-to-end -- then assert `holo_pocket_mask`'s heavy-atom-path output on
    real 4OBE/6OIM data matches `backend/systems.py`'s `pocket_full[4.5]`
    KRAS_G12C entry exactly, pinning the 21/21 heavy-atom recovery finding
    cited in `labels.py`'s own docstrings (`labels.py:56-67`, `:96-104`) as
    a real regression check instead of a docstring claim nobody re-runs.

    Deliberately checks the *raw* contact mask (`holo_pocket_mask`), not
    `build_labels`'s exclusion-applied `.pocket` -- `backend/systems.py`'s
    `pocket_full` is itself the raw ligand-contact list (pre-exclusion), so
    that is the correct thing to pin against, not the assembled/excluded
    label TASK-0070's tests already cover.
    """
    pytest.importorskip("prody")
    from allostery.clean import load_target_config

    cfg = load_target_config("KRAS_G12C")
    try:
        apo, holo = _load_real_target(cfg["apo_pdb"], cfg["holo_pdb"], cfg["chains"])
    except Exception as exc:
        pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")

    mask = holo_pocket_mask(
        apo, holo, cfg["drug_ligand"], cutoff=cfg["pocket_contact_cutoff"]
    )
    assert mask is not None

    recovered = set(int(r) for r in apo.resnums[mask])
    # backend/systems.py SYSTEMS["KRAS_G12C"]["pocket_full"][4.5], verbatim.
    expected = {9, 10, 11, 12, 13, 16, 34, 58, 59, 60, 61, 62, 63,
                68, 69, 72, 95, 96, 99, 100, 103}
    assert recovered == expected, (
        "heavy-atom-path pocket recovery diverged from backend/systems.py's "
        f"pocket_full[4.5] -- missing {sorted(expected - recovered)}, "
        f"extra {sorted(recovered - expected)}"
    )
