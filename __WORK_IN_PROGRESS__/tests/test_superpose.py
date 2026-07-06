"""TASK-0005 coverage -- Kabsch superposition, the cryptic-openness gate,
and ANM mode-projection / Tama-Sanejouand cumulative overlap.

Synthetic apo/holo coordinate pairs only (no network fetch, no prody
dependency) for everything except the real-target KRAS_G12C check at the
bottom, which is skipped when prody/network access is unavailable.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.labels import LigandGroup, holo_pocket_mask  # noqa: E402
from allostery.superpose import (  # noqa: E402
    Alignment,
    align_apo_holo,
    anm_modes,
    calibrate_kappa,
    common_residues_by_resnum,
    cryptic_openness_gate,
    cumulative_overlap,
    geometric_pocket_mask,
    kabsch_align,
    kabsch_apply,
    kabsch_fit,
    mode_energetics,
    pocket_cross_map,
    run_superpose,
)


def _helix_coords(n: int, radius: float = 2.3, rise: float = 1.5, turn_deg: float = 100.0) -> np.ndarray:
    theta = np.arange(n) * (turn_deg * np.pi / 180.0)
    return np.column_stack([
        radius * np.cos(theta),
        radius * np.sin(theta),
        rise * np.arange(n, dtype=float),
    ])


N = 12
COORDS = _helix_coords(N)
_SEQ3 = ["ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE", "LEU", "LYS"]


def _rotation_matrix(ax, ay, az):
    """Compose an XYZ Euler rotation -- small helper, test-only."""
    Rx = np.array([[1, 0, 0], [0, np.cos(ax), -np.sin(ax)], [0, np.sin(ax), np.cos(ax)]])
    Ry = np.array([[np.cos(ay), 0, np.sin(ay)], [0, 1, 0], [-np.sin(ay), 0, np.cos(ay)]])
    Rz = np.array([[np.cos(az), -np.sin(az), 0], [np.sin(az), np.cos(az), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


class _Struct:
    """Minimal CleanResult-shaped stand-in for apo/holo in these tests."""

    def __init__(self, coords, resnums, resnames, chain_ids=None, ligand_groups=None, b_mean=20.0, pdb_id="TEST"):
        self.pdb_id = pdb_id
        self.coords = coords
        self.resnums = np.asarray(resnums)
        self.resnames = list(resnames)
        self.chain_ids = list(chain_ids) if chain_ids is not None else ["A"] * len(resnums)
        self.ligand_groups = ligand_groups or []
        self.b_mean = b_mean


# ---------------------------------------------------------------------------
# Kabsch/SVD alignment
# ---------------------------------------------------------------------------

class TestKabsch:
    def test_recovers_synthetic_rotation_translation(self):
        rng = np.random.default_rng(0)
        ref = rng.normal(size=(20, 3))
        R0 = _rotation_matrix(0.3, -0.5, 1.1)
        t0 = np.array([5.0, -2.0, 3.0])
        mobile = ref @ R0.T + t0

        R, mc, rc = kabsch_fit(mobile, ref)
        recovered = kabsch_apply(mobile, R, mc, rc)
        np.testing.assert_allclose(recovered, ref, atol=1e-9)

    def test_reflection_case_det_sign_flip(self):
        """A planar (degenerate) point set exercises the det(Vt.T@U.T) branch."""
        rng = np.random.default_rng(1)
        ref = rng.normal(size=(10, 2))
        ref = np.column_stack([ref, np.zeros(10)])  # flat in z
        R0 = _rotation_matrix(0.0, 0.0, 0.7)
        mobile = ref @ R0.T

        aligned = kabsch_align(mobile, ref)
        np.testing.assert_allclose(aligned, ref, atol=1e-9)

    def test_apply_to_defaults_to_mobile(self):
        ref = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        mobile = ref + np.array([1.0, 2.0, 3.0])
        aligned = kabsch_align(mobile, ref)
        np.testing.assert_allclose(aligned, ref, atol=1e-9)


# ---------------------------------------------------------------------------
# Common-residue correspondence + full alignment
# ---------------------------------------------------------------------------

class TestCommonResiduesByResnum:
    def test_matches_on_chain_and_resnum_only(self):
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        # holo has a numbering offset for the last 2 residues (simulate a gap)
        holo_resnums = list(range(1, N - 1)) + [50, 51]
        holo = _Struct(COORDS, resnums=holo_resnums, resnames=_SEQ3)

        apo_idx, holo_idx = common_residues_by_resnum(apo, holo)
        assert len(apo_idx) == N - 2
        assert 50 not in apo.resnums.tolist()

    def test_no_overlap_returns_empty(self):
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        holo = _Struct(COORDS, resnums=list(range(100, 100 + N)), resnames=_SEQ3)
        apo_idx, holo_idx = common_residues_by_resnum(apo, holo)
        assert len(apo_idx) == 0
        assert len(holo_idx) == 0


class TestAlignApoHolo:
    def test_zero_rmsd_for_identical_structures(self):
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        holo = _Struct(COORDS.copy(), resnums=list(range(1, N + 1)), resnames=_SEQ3)

        alignment = align_apo_holo(apo, holo)
        assert isinstance(alignment, Alignment)
        assert alignment.rmsd_overall < 1e-9
        assert all(v < 1e-9 for v in alignment.rmsd_per_chain.values())

    def test_recovers_known_rigid_transform(self):
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        R0 = _rotation_matrix(0.2, 0.1, -0.4)
        t0 = np.array([10.0, -5.0, 2.0])
        holo_coords = COORDS @ R0.T + t0
        holo = _Struct(holo_coords, resnums=list(range(1, N + 1)), resnames=_SEQ3)

        alignment = align_apo_holo(apo, holo)
        assert alignment.rmsd_overall < 1e-9
        np.testing.assert_allclose(alignment.aligned_holo_coords, COORDS, atol=1e-8)

    def test_raises_on_too_few_common_residues(self):
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        holo = _Struct(COORDS[:1], resnums=[1], resnames=_SEQ3[:1])
        with pytest.raises(ValueError):
            align_apo_holo(apo, holo)

    def test_per_chain_rmsd_reports_each_chain(self):
        chains = ["A"] * (N // 2) + ["B"] * (N - N // 2)
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3, chain_ids=chains)
        holo = _Struct(COORDS.copy(), resnums=list(range(1, N + 1)), resnames=_SEQ3, chain_ids=chains)
        alignment = align_apo_holo(apo, holo)
        assert set(alignment.rmsd_per_chain) == {"A", "B"}


# ---------------------------------------------------------------------------
# 3D pocket cross-map
# ---------------------------------------------------------------------------

class TestPocketCrossMap:
    def _apo_holo_with_ligand(self):
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        ligand = LigandGroup("LIG", 501, "A", np.array([COORDS[5]]), 1)
        holo = _Struct(COORDS.copy(), resnums=list(range(1, N + 1)), resnames=_SEQ3, ligand_groups=[ligand])
        return apo, holo

    def test_geometric_mask_agrees_with_sequence_mask_when_structures_identical(self):
        apo, holo = self._apo_holo_with_ligand()
        seq_mask = holo_pocket_mask(apo, holo, "LIG", cutoff=4.5)
        alignment = align_apo_holo(apo, holo)
        geo_mask = geometric_pocket_mask(apo, holo, alignment, "LIG", cutoff=4.5)

        assert seq_mask is not None and geo_mask is not None
        np.testing.assert_array_equal(seq_mask, geo_mask)

        result = pocket_cross_map(seq_mask, geo_mask)
        assert result["agreement"] == 1.0
        assert len(result["only_in_sequence"]) == 0
        assert len(result["only_in_geometric"]) == 0

    def test_disagreement_is_reported_not_resolved(self):
        seq_mask = np.array([True, True, False, False, False])
        geo_mask = np.array([True, False, True, False, False])
        result = pocket_cross_map(seq_mask, geo_mask)
        assert 0.0 < result["agreement"] < 1.0
        np.testing.assert_array_equal(result["only_in_sequence"], [1])
        np.testing.assert_array_equal(result["only_in_geometric"], [2])

    def test_none_mask_propagates_as_none_agreement(self):
        result = pocket_cross_map(None, np.array([True, False]))
        assert result["agreement"] is None

    def test_geometric_mask_none_when_ligand_absent(self):
        apo, holo = self._apo_holo_with_ligand()
        alignment = align_apo_holo(apo, holo)
        assert geometric_pocket_mask(apo, holo, alignment, "ZZZ") is None


# ---------------------------------------------------------------------------
# Cryptic-openness gate
# ---------------------------------------------------------------------------

class TestCrypticOpennessGate:
    def test_small_displacement_reports_open_in_apo(self):
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        holo_coords = COORDS.copy()
        holo_coords[5] += np.array([0.1, 0.0, 0.0])  # tiny nudge
        holo = _Struct(holo_coords, resnums=list(range(1, N + 1)), resnames=_SEQ3)

        alignment = align_apo_holo(apo, holo)
        pocket_mask = np.zeros(N, dtype=bool)
        pocket_mask[5] = True

        gate = cryptic_openness_gate(apo, holo, alignment, pocket_mask, rmsd_threshold=3.0)
        assert gate["pocket_open_in_apo"] is True
        assert gate["pocket_rmsd_mean"] < 3.0
        assert gate["n_pocket_residues"] == 1

    def test_large_displacement_reports_closed_in_apo(self):
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        holo_coords = COORDS.copy()
        holo_coords[5] += np.array([10.0, 0.0, 0.0])  # large rearrangement
        holo = _Struct(holo_coords, resnums=list(range(1, N + 1)), resnames=_SEQ3)

        alignment = align_apo_holo(apo, holo)
        pocket_mask = np.zeros(N, dtype=bool)
        pocket_mask[5] = True

        gate = cryptic_openness_gate(apo, holo, alignment, pocket_mask, rmsd_threshold=3.0)
        assert gate["pocket_open_in_apo"] is False
        assert gate["pocket_rmsd_mean"] > 3.0

    def test_unmeasurable_pocket_residues_counted_not_dropped(self):
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        holo = _Struct(COORDS.copy(), resnums=list(range(1, N - 1)), resnames=_SEQ3[: N - 2])
        alignment = align_apo_holo(apo, holo)

        pocket_mask = np.zeros(N, dtype=bool)
        pocket_mask[[5, N - 1]] = True  # N-1 has no common-set correspondence

        gate = cryptic_openness_gate(apo, holo, alignment, pocket_mask, rmsd_threshold=3.0)
        assert gate["n_unmeasurable"] == 1
        assert gate["n_pocket_residues"] == 1

    def test_no_measurable_pocket_residues_returns_none_verdict(self):
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        holo = _Struct(COORDS[:3], resnums=[1, 2, 3], resnames=_SEQ3[:3])
        alignment = align_apo_holo(apo, holo)

        pocket_mask = np.zeros(N, dtype=bool)
        pocket_mask[N - 1] = True

        gate = cryptic_openness_gate(apo, holo, alignment, pocket_mask, rmsd_threshold=3.0)
        assert gate["pocket_open_in_apo"] is None
        assert np.isnan(gate["pocket_rmsd_mean"])


# ---------------------------------------------------------------------------
# ANM modes
# ---------------------------------------------------------------------------

class TestAnmModes:
    def test_shape_and_ascending_order(self):
        eigvals, eigvecs = anm_modes(COORDS, cutoff=10.0, n_modes=5)
        assert eigvals.shape == (5,)
        assert eigvecs.shape == (3 * N, 5)
        assert np.all(np.diff(eigvals) >= -1e-12)  # ascending

    def test_drops_at_least_six_rigid_body_modes(self):
        eigvals, _ = anm_modes(COORDS, cutoff=10.0, n_modes=100)
        assert eigvals.min() > 1e-8

    def test_requests_more_modes_than_available_clamps(self):
        eigvals, eigvecs = anm_modes(COORDS, cutoff=10.0, n_modes=10_000)
        assert eigvals.shape[0] == 3 * N - 6
        assert eigvecs.shape[1] == 3 * N - 6

    def test_raises_on_disconnected_graph(self):
        # two well-separated clusters -- no contacts between them at this cutoff
        cluster_a = _helix_coords(6)
        cluster_b = _helix_coords(6) + np.array([1000.0, 1000.0, 1000.0])
        coords = np.vstack([cluster_a, cluster_b])
        with pytest.raises(ValueError):
            anm_modes(coords, cutoff=10.0, n_modes=5)


# ---------------------------------------------------------------------------
# Cumulative overlap (Planned Validation's core numeric requirement)
# ---------------------------------------------------------------------------

class TestCumulativeOverlap:
    def test_delta_r_confined_to_first_two_modes_gives_co2_near_one(self):
        eigvals, eigvecs = anm_modes(COORDS, cutoff=10.0, n_modes=3 * N - 6)
        common_idx = np.arange(N)
        delta_r = 0.7 * eigvecs[:, 0] + 0.3 * eigvecs[:, 1]

        co = cumulative_overlap(delta_r, eigvecs, common_idx)
        assert co[1] == pytest.approx(1.0, abs=1e-8)
        assert co[0] < co[1]

    def test_monotonically_non_decreasing(self):
        eigvals, eigvecs = anm_modes(COORDS, cutoff=10.0, n_modes=3 * N - 6)
        common_idx = np.arange(N)
        rng = np.random.default_rng(2)
        delta_r = rng.normal(size=3 * N)

        co = cumulative_overlap(delta_r, eigvecs, common_idx)
        assert np.all(np.diff(co) >= -1e-9)
        assert co[-1] <= 1.0 + 1e-6

    def test_zero_delta_r_returns_zeros(self):
        _, eigvecs = anm_modes(COORDS, cutoff=10.0, n_modes=5)
        co = cumulative_overlap(np.zeros(3 * N), eigvecs, np.arange(N))
        np.testing.assert_array_equal(co, np.zeros(5))

    def test_wrong_length_delta_r_raises(self):
        _, eigvecs = anm_modes(COORDS, cutoff=10.0, n_modes=5)
        with pytest.raises(ValueError):
            cumulative_overlap(np.zeros(7), eigvecs, np.arange(N))


# ---------------------------------------------------------------------------
# kappa calibration + mode energetics
# ---------------------------------------------------------------------------

class TestKappaAndEnergetics:
    def test_kappa_is_positive_and_inversely_proportional_to_b_mean(self):
        k1 = calibrate_kappa(COORDS, b_mean=10.0, cutoff=10.0)
        k2 = calibrate_kappa(COORDS, b_mean=20.0, cutoff=10.0)
        assert k1 > 0 and k2 > 0
        assert k2 == pytest.approx(k1 / 2.0, rel=1e-9)

    def test_kappa_rejects_nonpositive_b_mean(self):
        with pytest.raises(ValueError):
            calibrate_kappa(COORDS, b_mean=0.0, cutoff=10.0)

    def test_mode_energetics_formulas(self):
        eigvals, eigvecs = anm_modes(COORDS, cutoff=10.0, n_modes=5)
        common_idx = np.arange(N)
        delta_r = 0.7 * eigvecs[:, 0] + 0.3 * eigvecs[:, 1]
        kappa = 2.0
        zeta = 1.5

        result = mode_energetics(delta_r, eigvals, eigvecs, common_idx, kappa, zeta=zeta)
        expected_energy = 0.5 * kappa * eigvals * result["coefficients"] ** 2
        expected_tau = zeta / (kappa * eigvals)

        np.testing.assert_allclose(result["elastic_energy"], expected_energy)
        np.testing.assert_allclose(result["relaxation_time"], expected_tau)
        # relaxation TIME, not an oscillation period -- must scale as 1/lambda, not 1/sqrt(lambda)
        assert np.all(result["relaxation_time"] > 0)


# ---------------------------------------------------------------------------
# One-call orchestrator
# ---------------------------------------------------------------------------

class TestRunSuperpose:
    def test_end_to_end_smoke(self):
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3, b_mean=25.0)
        ligand = LigandGroup("LIG", 501, "A", np.array([COORDS[5]]), 1)
        holo_coords = COORDS.copy()
        holo_coords[5] += np.array([0.2, 0.0, 0.0])
        holo = _Struct(holo_coords, resnums=list(range(1, N + 1)), resnames=_SEQ3, ligand_groups=[ligand])

        report = run_superpose(apo, holo, {"drug_ligand": "LIG"}, n_modes=5, cutoff=10.0)

        assert isinstance(report["alignment"], Alignment)
        assert report["pocket_cross_map"]["agreement"] == 1.0
        assert report["openness_gate"]["pocket_open_in_apo"] is True
        assert len(report["cumulative_overlap"]) == 5
        assert report["kappa"] > 0
        assert len(report["mode_energetics"]["elastic_energy"]) == 5

    def test_no_drug_ligand_configured_skips_pocket_steps_not_a_crash(self):
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3, b_mean=25.0)
        holo = _Struct(COORDS.copy(), resnums=list(range(1, N + 1)), resnames=_SEQ3)

        report = run_superpose(apo, holo, {}, n_modes=5, cutoff=10.0)
        assert report["pocket_cross_map"]["agreement"] is None
        assert report["openness_gate"] is None


# ---------------------------------------------------------------------------
# Real-target check (KRAS_G12C) -- skipped where prody/network is unavailable
# ---------------------------------------------------------------------------

def test_kras_g12c_real_target_expects_low_cumulative_overlap():
    """KRAS_G12C's Switch-II cryptic pocket (SII-P) is the literature case
    where the apo->holo direction is *not* spanned by the soft ANM modes --
    a low CO(m) here is the expected, correct result (ALGORITHM_REGISTER.md's
    Tama-Sanejouand entry), not a test failure.
    """
    pytest.importorskip("prody")
    from allostery.clean import clean

    try:
        apo = clean("4OBE", chains=["A"])
        holo = clean("6OIM", chains=["A"])
    except Exception as exc:  # network/RCSB fetch unavailable in this sandbox
        pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")

    from allostery.labels import ligand_groups_from_atomgroup
    import prody

    prody.confProDy(verbosity="none")
    holo_struct = prody.parsePDB("6OIM", compressed=False).select("chain A")
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)

    alignment = align_apo_holo(apo, holo)
    eigvals, eigvecs = anm_modes(apo.coords, cutoff=10.0, n_modes=20)
    delta_r = (
        alignment.aligned_holo_coords[alignment.holo_idx] - apo.coords[alignment.apo_idx]
    ).ravel()
    co = cumulative_overlap(delta_r, eigvecs, alignment.apo_idx)

    # expected-low overlap even at 20 modes -- SII-P is a cryptic/anharmonic
    # opening, not a harmonic-mode-reachable one.
    assert co[-1] < 0.9
