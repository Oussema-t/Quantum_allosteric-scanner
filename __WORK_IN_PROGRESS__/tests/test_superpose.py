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

from allostery.diagnostics import operator_diagnostics  # noqa: E402
from allostery.hamiltonians import H13_3N_anm_hessian  # noqa: E402
from allostery.labels import LigandGroup, holo_pocket_mask  # noqa: E402
from allostery.superpose import (  # noqa: E402
    Alignment,
    align_apo_holo,
    anm_modes,
    background_rmsd,
    calibrate_kappa,
    common_residues_by_resnum,
    cryptic_openness_gate,
    cumulative_overlap,
    cumulative_overlap_gate,
    geometric_pocket_mask,
    kabsch_align,
    kabsch_apply,
    kabsch_fit,
    learnability_verdict,
    mode_energetics,
    pocket_cross_map,
    restricted_cumulative_overlap,
    run_superpose,
    _check_anm_rigid_body_nullspace,
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


class TestBackgroundRmsd:
    """TASK-0120 -- the missing half of `cryptic_openness_gate`'s
    comparison: how much does the *rest* of the structure move, so pocket
    RMSD can be read relative to it, not in isolation."""

    def test_moving_only_the_pocket_leaves_background_still(self):
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        holo_coords = COORDS.copy()
        holo_coords[5] += np.array([10.0, 0.0, 0.0])  # only residue 5 (pocket) moves
        holo = _Struct(holo_coords, resnums=list(range(1, N + 1)), resnames=_SEQ3)

        alignment = align_apo_holo(apo, holo)
        pocket_mask = np.zeros(N, dtype=bool)
        pocket_mask[5] = True

        bg = background_rmsd(apo, holo, alignment, pocket_mask)
        assert bg["n_background_residues"] == N - 1
        assert bg["background_rmsd_mean"] < 1.0  # everything but residue 5 is unmoved

    def test_global_rearrangement_shows_up_in_background_too(self):
        """A globally flexible structure (every residue moves, not just the
        pocket) must show a large background RMSD too -- this is exactly
        the case `cryptic_openness_gate` alone cannot distinguish from a
        genuinely pocket-specific opening."""
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        rng = np.random.default_rng(0)
        holo_coords = COORDS + rng.normal(0, 5.0, COORDS.shape)  # everything moves
        holo = _Struct(holo_coords, resnums=list(range(1, N + 1)), resnames=_SEQ3)

        alignment = align_apo_holo(apo, holo)
        pocket_mask = np.zeros(N, dtype=bool)
        pocket_mask[5] = True

        bg = background_rmsd(apo, holo, alignment, pocket_mask)
        assert bg["background_rmsd_mean"] > 2.0

    def test_no_background_residues_returns_nan_not_crash(self):
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        holo = _Struct(COORDS.copy(), resnums=list(range(1, N + 1)), resnames=_SEQ3)
        alignment = align_apo_holo(apo, holo)
        pocket_mask = np.ones(N, dtype=bool)  # everything is "pocket" -- no background

        bg = background_rmsd(apo, holo, alignment, pocket_mask)
        assert bg["n_background_residues"] == 0
        assert np.isnan(bg["background_rmsd_mean"])


class TestLearnabilityVerdict:
    """TASK-0120 -- REVIEW-panel-2026-07-16-v2.md Sec.6's kill criterion:
    pocket RMSD >> background RMSD AND low cumulative overlap ->
    UNLEARNABLE_FROM_APO. Both conditions required, checked independently
    below so a passing test can't hide either half being unwired."""

    def test_large_relative_pocket_displacement_and_low_overlap_is_unlearnable(self):
        result = learnability_verdict(
            pocket_rmsd_mean=6.0, background_rmsd_mean=1.0, co_final=0.2,
        )
        assert result["verdict"] == "UNLEARNABLE_FROM_APO"
        assert result["rmsd_ratio"] == 6.0

    def test_large_relative_displacement_but_high_overlap_is_learnable(self):
        """The displacement is real and large relative to background, but
        it's *reachable* via the soft ANM modes (high CO) -- not the
        anharmonic/cryptic case, so LEARNABLE despite the large RMSD ratio."""
        result = learnability_verdict(
            pocket_rmsd_mean=6.0, background_rmsd_mean=1.0, co_final=0.8,
        )
        assert result["verdict"] == "LEARNABLE"

    def test_low_overlap_but_pocket_not_relatively_displaced_is_learnable(self):
        """Low CO alone, without the pocket actually standing out from
        background, must not trigger UNLEARNABLE -- could just be a
        globally floppy structure or measurement noise."""
        result = learnability_verdict(
            pocket_rmsd_mean=1.1, background_rmsd_mean=1.0, co_final=0.1,
        )
        assert result["verdict"] == "LEARNABLE"

    def test_zero_background_rmsd_does_not_crash(self):
        result = learnability_verdict(
            pocket_rmsd_mean=5.0, background_rmsd_mean=0.0, co_final=0.1,
        )
        assert result["verdict"] == "UNLEARNABLE_FROM_APO"
        assert result["rmsd_ratio"] == float("inf")

    def test_thresholds_are_reported_not_just_applied(self):
        """The verdict dict must carry the exact thresholds used, so a
        reader doesn't have to guess what '>>' meant for this particular
        call -- TASK-0120's own Planned Validation ('state the numbers,
        not just the label')."""
        result = learnability_verdict(
            pocket_rmsd_mean=3.0, background_rmsd_mean=1.0, co_final=0.3,
            rmsd_ratio_threshold=2.0, co_threshold=0.4,
        )
        assert result["rmsd_ratio_threshold"] == 2.0
        assert result["co_threshold"] == 0.4


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

    def test_raises_when_fewer_than_six_zero_modes(self):
        """TASK-0128's own unconditional case: n_zero<6 is always a bug
        (fewer than the mandatory 3 translation + 3 rotation modes cannot
        happen for a real ANM Hessian), independent of connectivity --
        must still raise even though this task widened the n_zero>6 case."""
        with pytest.raises(ValueError, match="at least 6"):
            _check_anm_rigid_body_nullspace(
                H=np.eye(30), w=np.concatenate([np.full(5, 1e-16), np.full(25, 1.0)]), n_zero=5,
            )

    def test_disconnected_graph_still_raises_even_with_many_zero_modes(self):
        """TASK-0005's original regression, re-verified directly against
        real numbers rather than just 'still raises': two disconnected
        6-residue clusters give n_zero=12 (2x6, confirmed via eigh) and
        n_components=2 (confirmed via operator_diagnostics) -- TASK-0128's
        widened `n_zero>6` acceptance must not silently swallow this case."""
        cluster_a = _helix_coords(6)
        cluster_b = _helix_coords(6) + np.array([1000.0, 1000.0, 1000.0])
        coords = np.vstack([cluster_a, cluster_b])
        H = H13_3N_anm_hessian(coords, cutoff=10.0)
        w = np.linalg.eigvalsh(H)
        n_zero = int((w < 1e-8).sum())
        assert n_zero == 12  # 2 independent rigid pieces, 6 trivial modes each
        assert operator_diagnostics(H)["n_components"] == 2
        with pytest.raises(ValueError, match="disconnected components"):
            anm_modes(coords, cutoff=10.0, n_modes=5)

    def test_connected_structure_with_more_than_six_zero_modes_does_not_raise(self):
        """TASK-0128's actual fix target: a *connected* structure (single
        component) can legitimately have more than 6 near-zero ANM modes --
        a locally under-constrained substructure (here: a small 3-residue
        cluster attached to the main body through only a thin bridge) has
        a genuine zero-energy internal rotational mode in a purely
        central-force ANM model, without the graph being disconnected.
        Reproduces the real BCR_ABL1/CARDIAC_MYOSIN pattern (n_zero>6,
        n_components==1) on a small synthetic case, not just described in
        prose."""
        main = _helix_coords(10)
        sub = _helix_coords(3) + np.array([9.5, 0.0, 5.0])  # thin bridge to main
        coords = np.vstack([main, sub])
        H = H13_3N_anm_hessian(coords, cutoff=10.0)
        w = np.linalg.eigvalsh(H)
        n_zero = int((w < 1e-8).sum())
        assert n_zero > 6  # the legitimately-floppy case this task targets
        assert operator_diagnostics(H)["n_components"] == 1  # genuinely connected

        eigvals, eigvecs = anm_modes(coords, cutoff=10.0, n_modes=5)  # must not raise
        assert eigvals.shape[0] <= 5
        assert eigvals.min() > 1e-8  # only real non-trivial modes returned

    def test_calibrate_kappa_also_accepts_the_connected_floppy_case(self):
        """calibrate_kappa had its own separate copy of the same check --
        confirm the shared helper actually reaches both call sites, not
        just anm_modes."""
        main = _helix_coords(10)
        sub = _helix_coords(3) + np.array([9.5, 0.0, 5.0])
        coords = np.vstack([main, sub])
        kappa = calibrate_kappa(coords, b_mean=20.0, cutoff=10.0)  # must not raise
        assert kappa > 0


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


class TestCumulativeOverlapSE3Invariance:
    """TASK-0054 -- `INVARIANCE_PROTOCOL.md` Tier 0 GAUGE regression test
    for `INV-0001`'s one `OPEN` row: rotating+translating `coords` *and*
    `delta_r` jointly by an arbitrary rigid motion must not change
    `cumulative_overlap`'s output at all. This is the exact class of bug
    the protocol names as this repo's own prior incident (cumulative
    overlap moved 0.34->0.90 under rotation before `anm_modes`'
    select-by-eigenvalue-not-index fix) -- that fix is already live
    (`anm_modes`'s own `n_zero = int((w < 1e-8).sum())` selection); this
    is the regression test that would have caught its absence, which
    never existed for this specific quantity until now.

    A genuinely arbitrary (non-axis-aligned) rotation matters: 90/180
    degree rotations can leave an axis-aligned bug undetected. Uses a
    fixed, off-axis Euler angle triple, not 0/90/180.
    """

    ROTATION = _rotation_matrix(0.4, -1.1, 2.3)  # arbitrary, off-axis, fixed
    TRANSLATION = np.array([5.0, -3.0, 12.0])    # arbitrary, nonzero

    def _rotate_flat(self, vec: np.ndarray, R: np.ndarray) -> np.ndarray:
        """Rotate a flat 3N-length vector (coords or a per-residue
        displacement) block-wise by R."""
        return (vec.reshape(-1, 3) @ R.T).ravel()

    def test_rotation_and_translation_leave_cumulative_overlap_unchanged(self):
        rng = np.random.default_rng(4)
        # Real, non-trivial displacement -- not the degenerate zero case
        # (already covered by test_zero_delta_r_returns_zeros above).
        delta_r = rng.normal(size=3 * N)

        eigvals_before, eigvecs_before = anm_modes(COORDS, cutoff=10.0, n_modes=3 * N - 6)
        common_idx = np.arange(N)
        co_before = cumulative_overlap(delta_r, eigvecs_before, common_idx)

        # Joint rigid motion: coords get rotation + translation; the
        # *displacement* vector gets rotation only (translation is gauge-
        # trivial for a difference of two translated point sets -- t
        # cancels: (R@holo+t) - (R@apo+t) = R@(holo-apo) -- asserted
        # below, not assumed).
        coords_transformed = (COORDS @ self.ROTATION.T) + self.TRANSLATION
        delta_r_transformed = self._rotate_flat(delta_r, self.ROTATION)

        eigvals_after, eigvecs_after = anm_modes(coords_transformed, cutoff=10.0, n_modes=3 * N - 6)
        co_after = cumulative_overlap(delta_r_transformed, eigvecs_after, common_idx)

        # Eigenvalues (the physical mode energies) are SE(3)-invariant by
        # construction -- a real ANM/GAUGE sanity check on the fixture
        # itself before trusting the CO comparison built on top of it.
        np.testing.assert_allclose(eigvals_after, eigvals_before, atol=1e-9)
        np.testing.assert_allclose(co_after, co_before, atol=1e-9)

    def test_translation_alone_is_gauge_trivial_for_the_displacement(self):
        """Isolates the translation half of the joint motion: translating
        `coords` (no rotation) while leaving `delta_r` untouched must also
        leave `cumulative_overlap` unchanged -- per this task's own Intent
        Contract ("translation should be gauge-trivial for a displacement
        vector, but assert it anyway -- cheap, and the protocol's own
        point is not to assume")."""
        rng = np.random.default_rng(5)
        delta_r = rng.normal(size=3 * N)
        common_idx = np.arange(N)

        _, eigvecs_before = anm_modes(COORDS, cutoff=10.0, n_modes=3 * N - 6)
        co_before = cumulative_overlap(delta_r, eigvecs_before, common_idx)

        coords_translated = COORDS + self.TRANSLATION
        _, eigvecs_after = anm_modes(coords_translated, cutoff=10.0, n_modes=3 * N - 6)
        co_after = cumulative_overlap(delta_r, eigvecs_after, common_idx)

        np.testing.assert_allclose(co_after, co_before, atol=1e-9)

    def test_residue_relabeling_leaves_cumulative_overlap_unchanged(self):
        """Sibling GAUGE check (INV-0001's second `OPEN` row, absorbed
        here since it's cheap alongside the rotation test, per this
        task's own Out Of Scope allowance): permuting residue indices
        consistently across coords/delta_r/common_idx must not change the
        result -- the modes and the displacement must permute together,
        not just the modes."""
        rng = np.random.default_rng(6)
        delta_r = rng.normal(size=3 * N)
        common_idx = np.arange(N)

        _, eigvecs = anm_modes(COORDS, cutoff=10.0, n_modes=3 * N - 6)
        co_before = cumulative_overlap(delta_r, eigvecs, common_idx)

        perm = rng.permutation(N)
        coords_perm = COORDS[perm]
        delta_r_perm = delta_r.reshape(N, 3)[perm].ravel()

        _, eigvecs_perm = anm_modes(coords_perm, cutoff=10.0, n_modes=3 * N - 6)
        co_after = cumulative_overlap(delta_r_perm, eigvecs_perm, common_idx)

        np.testing.assert_allclose(co_after, co_before, atol=1e-9)


class TestRestrictedCumulativeOverlap:
    """TASK-0133 -- CO(m) restricted to one residue subset's own
    displacement, distinct from `learnability_gate.py`'s whole-structure
    number (confirmed via `len(delta_r) == 3*len(alignment.apo_idx)` on
    real data, not the pocket size)."""

    def test_matches_cumulative_overlap_when_subset_is_the_full_common_set(self):
        """Sanity check: restricting to *every* common-set residue must
        reproduce the whole-structure `cumulative_overlap` exactly --
        the restriction logic is a strict generalization, not a
        different formula."""
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        rng = np.random.default_rng(1)
        holo_coords = COORDS + rng.normal(0, 1.0, COORDS.shape)
        holo = _Struct(holo_coords, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        alignment = align_apo_holo(apo, holo)
        _, eigvecs = anm_modes(COORDS, cutoff=10.0, n_modes=3 * N - 6)

        full_delta_r = (
            alignment.aligned_holo_coords[alignment.holo_idx] - apo.coords[alignment.apo_idx]
        ).ravel()
        expected = cumulative_overlap(full_delta_r, eigvecs, alignment.apo_idx)
        actual = restricted_cumulative_overlap(apo, alignment, eigvecs, alignment.apo_idx)
        np.testing.assert_allclose(actual, expected)

    def test_differs_from_whole_structure_when_only_one_residue_moves(self):
        """The whole-structure CO and a single-residue-restricted CO are
        genuinely different quantities: a small local displacement
        buried in a large whole-structure norm reads very differently
        once isolated -- this is the exact type mismatch TASK-0133's own
        Done section flags about `learnability_gate.py`'s reported
        number."""
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        rng = np.random.default_rng(2)
        holo_coords = COORDS + rng.normal(0, 3.0, COORDS.shape)  # everything moves
        holo = _Struct(holo_coords, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        alignment = align_apo_holo(apo, holo)
        _, eigvecs = anm_modes(COORDS, cutoff=10.0, n_modes=3 * N - 6)

        whole = restricted_cumulative_overlap(apo, alignment, eigvecs, alignment.apo_idx)
        one_residue = restricted_cumulative_overlap(apo, alignment, eigvecs, np.array([5]))
        assert not np.allclose(whole, one_residue)

    def test_residue_without_holo_correspondence_raises(self):
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        holo = _Struct(COORDS[: N - 2].copy(), resnums=list(range(1, N - 1)), resnames=_SEQ3[: N - 2])
        alignment = align_apo_holo(apo, holo)
        _, eigvecs = anm_modes(COORDS, cutoff=10.0, n_modes=5)

        with pytest.raises(ValueError, match="no holo correspondence"):
            restricted_cumulative_overlap(apo, alignment, eigvecs, np.array([N - 1]))

    def test_output_length_matches_n_modes(self):
        apo = _Struct(COORDS, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        rng = np.random.default_rng(3)
        holo_coords = COORDS + rng.normal(0, 1.0, COORDS.shape)
        holo = _Struct(holo_coords, resnums=list(range(1, N + 1)), resnames=_SEQ3)
        alignment = align_apo_holo(apo, holo)
        _, eigvecs = anm_modes(COORDS, cutoff=10.0, n_modes=7)

        co = restricted_cumulative_overlap(apo, alignment, eigvecs, np.array([2, 5, 8]))
        assert len(co) == 7

    def test_stays_bounded_by_one_for_a_small_subset_of_a_large_structure(self):
        """TASK-0133's own real, load-bearing finding: naively reusing
        `cumulative_overlap`'s renormalize-a-sliced-eigenvector approach
        for a small residue subset breaks `CO(m) <= 1` (confirmed on real
        pocket-sized data, up to 1.64) -- this function's zero-padding
        approach must not reproduce that bug. Large structure (N=50), tiny
        subset (3 residues), same shape as the real pocket-vs-full-
        structure ratio this task's real targets have (13-18 of
        166-709)."""
        big_coords = _helix_coords(50)
        apo = _Struct(big_coords, resnums=list(range(1, 51)), resnames=(_SEQ3 * 5)[:50])
        rng = np.random.default_rng(0)
        holo_coords = big_coords + rng.normal(0, 1.0, big_coords.shape)
        holo = _Struct(holo_coords, resnums=list(range(1, 51)), resnames=(_SEQ3 * 5)[:50])
        alignment = align_apo_holo(apo, holo)
        _, eigvecs = anm_modes(big_coords, cutoff=10.0, n_modes=20)

        co = restricted_cumulative_overlap(apo, alignment, eigvecs, np.array([10, 11, 12]))
        assert co.max() <= 1.0 + 1e-9
        assert np.all(np.diff(co) >= -1e-9)  # still monotonically non-decreasing


# ---------------------------------------------------------------------------
# TASK-0075 -- knob-spread go/no-go gate (Acceptance Scenarios)
# ---------------------------------------------------------------------------
#
# A larger synthetic helix than the module's own N=12 (below, GATE_N=20) --
# needed for a real, non-contrived knob-sensitivity: at N=12 the ANM mode
# spectrum is too coarse for cutoff/n_modes to meaningfully reorder which
# subspace delta_r projects onto. delta_r is constructed as a mix of the
# first two cutoff=10.0 modes plus fixed-seed noise (same recipe
# TestCumulativeOverlap's own tests already use for a controlled-overlap
# delta_r) -- real physics, not a rigged verdict: the resulting spread
# (CO ~= 0.31 to ~0.86 across the swept grid, verified by direct
# computation before writing these assertions) happens to flip a
# threshold near the middle of that range, which is what a real
# knob-sensitive case looks like. This is a fresh construction, not a
# byte-for-byte reproduction of the plan's originally-cited 0.067-0.860/
# 15-of-18 numbers -- those live in .ai/reference/INVARIANCE_PROTOCOL.md:76
# ("2-domain toy", rc x variant x k = 18 combos) as a summary statistic
# only, no coordinates or code checked in to rebuild the exact case. A
# literal 2-domain-hinge reconstruction was attempted first and did not
# reach that severity (stayed in a narrow 0.42-0.45 band); this simpler
# single-helix construction is the fallback that does exercise a real,
# if smaller (1/12 vs the documented 15/18), knob-driven flip -- see
# TASK-0075's own Done section for the full account of both attempts.

GATE_N = 20
GATE_COORDS = _helix_coords(GATE_N)
GATE_COMMON_IDX = np.arange(GATE_N)


def _gate_delta_r():
    _, eigvecs10 = anm_modes(GATE_COORDS, cutoff=10.0, n_modes=3 * GATE_N - 6)
    rng = np.random.default_rng(3)
    noise = rng.normal(size=3 * GATE_N)
    noise = noise / np.linalg.norm(noise)
    return 0.6 * eigvecs10[:, 0] + 0.3 * eigvecs10[:, 1] + 0.5 * noise


GATE_DELTA_R = _gate_delta_r()
GATE_CUTOFFS = (8.0, 10.0, 12.0)
GATE_N_MODES = (2, 5, 10, 20)


class TestCumulativeOverlapGate:
    def test_low_threshold_gives_decisive_go(self):
        out = cumulative_overlap_gate(
            GATE_DELTA_R, GATE_COMMON_IDX, {"apo": GATE_COORDS},
            cutoffs=GATE_CUTOFFS, n_modes_list=GATE_N_MODES, co_threshold=0.3,
        )
        assert out["verdict"] == "GO"
        assert out["n_go"] == out["n_combos"]

    def test_high_threshold_gives_decisive_no_go(self):
        out = cumulative_overlap_gate(
            GATE_DELTA_R, GATE_COMMON_IDX, {"apo": GATE_COORDS},
            cutoffs=GATE_CUTOFFS, n_modes_list=GATE_N_MODES, co_threshold=0.95,
        )
        assert out["verdict"] == "NO_GO"
        assert out["n_go"] == 0

    def test_mid_threshold_gives_unstable_not_a_point_estimate(self):
        """Acceptance Scenario: a knob-sensitive case must return UNSTABLE,
        never a single GO or NO-GO."""
        out = cumulative_overlap_gate(
            GATE_DELTA_R, GATE_COMMON_IDX, {"apo": GATE_COORDS},
            cutoffs=GATE_CUTOFFS, n_modes_list=GATE_N_MODES, co_threshold=0.5,
        )
        assert out["verdict"] == "UNSTABLE"
        assert 0 < out["n_go"] < out["n_combos"]
        assert out["spread"] > 0.3  # real, substantial knob sensitivity

    def test_all_agreeing_case_reports_narrow_spread_alongside_verdict(self):
        """Acceptance Scenario: when combinations agree, the gate returns a
        decisive verdict *plus* the (narrow) spread -- not a bare verdict
        with the evidence discarded."""
        out = cumulative_overlap_gate(
            GATE_DELTA_R, GATE_COMMON_IDX, {"apo": GATE_COORDS},
            cutoffs=GATE_CUTOFFS, n_modes_list=GATE_N_MODES, co_threshold=0.3,
        )
        assert out["verdict"] == "GO"
        assert "spread" in out and "co_min" in out and "co_max" in out
        assert out["spread"] == pytest.approx(out["co_max"] - out["co_min"])

    def test_reference_conformer_choice_is_a_real_swept_knob(self):
        """A second reference structure (a perturbed conformer) is
        actually used, not silently ignored -- part of this task's own
        named (cutoff x variant x k x reference) grid."""
        rng = np.random.default_rng(9)
        perturbed = GATE_COORDS + rng.normal(scale=0.3, size=GATE_COORDS.shape)
        out = cumulative_overlap_gate(
            GATE_DELTA_R, GATE_COMMON_IDX,
            {"apo": GATE_COORDS, "apo_alt_conformer": perturbed},
            cutoffs=GATE_CUTOFFS, n_modes_list=GATE_N_MODES, co_threshold=0.5,
        )
        assert out["n_combos"] == 2 * len(GATE_CUTOFFS) * len(GATE_N_MODES)
        refs_seen = {g["reference"] for g in out["grid"]}
        assert refs_seen == {"apo", "apo_alt_conformer"}

    def test_grid_is_the_full_evidence_not_just_the_summary(self):
        out = cumulative_overlap_gate(
            GATE_DELTA_R, GATE_COMMON_IDX, {"apo": GATE_COORDS},
            cutoffs=GATE_CUTOFFS, n_modes_list=GATE_N_MODES, co_threshold=0.5,
        )
        assert len(out["grid"]) == out["n_combos"]
        for combo in out["grid"]:
            assert set(combo) == {"reference", "cutoff", "n_modes", "co", "go"}

    def test_disconnected_reference_graph_recorded_not_crashed(self):
        cluster_a = _helix_coords(6)
        cluster_b = _helix_coords(6) + np.array([1000.0, 1000.0, 1000.0])
        disconnected = np.vstack([cluster_a, cluster_b])
        common_idx = np.arange(12)
        delta_r = np.zeros(3 * 12)
        delta_r[0] = 1.0
        out = cumulative_overlap_gate(
            delta_r, common_idx, {"disconnected": disconnected},
            cutoffs=(10.0,), n_modes_list=(5,), co_threshold=0.5,
        )
        assert out["grid"][0]["go"] is None
        assert np.isnan(out["grid"][0]["co"])
        # every combo degenerate -> nothing to call GO, per this function's
        # own "no finite combo => NO_GO" fallback (never silently UNSTABLE
        # or GO on zero evidence)
        assert out["verdict"] == "NO_GO"


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
