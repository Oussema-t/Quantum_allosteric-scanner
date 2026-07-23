"""TASK-0140 -- tests for `allostery.chiral` (HYP-P9 chiral circulation
observable). No reference implementation existed to test against
(confirmed directly, not assumed) -- these tests check the physics this
module's own docstring derives: Hermiticity, Hodge reconstruction,
divergence-freeness of the circulating part, the zero-flux sanity limit,
and the (initially surprising, now documented) bipartite/symmetry null
that ruled out a bare ring as this module's own test fixture.
"""
from __future__ import annotations

import numpy as np
import pytest

from allostery.chiral import (
    bond_current_converged,
    chiral_circulation_score,
    circulation_score_from_hamiltonians,
    hodge_decompose,
    peierls_hamiltonian,
)
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed
from allostery.diagnostics import NO_FAILURE_DETECTED, classify_failure
from allostery.hamiltonians import contact_matrix
from allostery.metrics import auc as _auc
from allostery.propagators import ground_state_relaxation, time_averaged_ctqw_converged


def _ring_coords(n: int, radius: float = 10.0) -> np.ndarray:
    """n points evenly spaced on a circle in the xy-plane. A uniform
    ring: circulant (fully rotationally symmetric) AND, for even n,
    bipartite -- deliberately used ONLY as a *null*-result fixture (see
    `TestBipartiteAndSymmetryNulls`), never as a "does chirality produce
    a signal" fixture, since both of its symmetries independently force
    zero converged circulation from a diagonal seed regardless of flux
    (confirmed directly; see `chiral.py`'s own docstring §4)."""
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    return np.column_stack([x, y, np.zeros(n)])


def _chain_coords(n: int, spacing: float = 3.8) -> np.ndarray:
    return np.column_stack([np.arange(n, dtype=float) * spacing, np.zeros(n), np.zeros(n)])


def _triangulated_asymmetric_coords(n: int = 10, seed: int = 0) -> np.ndarray:
    """An irregular (non-circulant) ring with a cutoff wide enough to
    also connect next-nearest neighbors -- the resulting graph has
    triangles (non-bipartite: an odd cycle exists) and no rotational
    symmetry (Bloch's theorem doesn't apply), so neither of the two null
    mechanisms in `chiral.py`'s own docstring §4 applies here. This is
    this module's actual minimal "chirality can produce a signal"
    fixture -- confirmed nonzero directly during development, not
    assumed. Use with `cutoff=12.0`."""
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rng = np.random.default_rng(seed)
    radius = 10.0 + 1.5 * np.sin(3 * theta) + 0.3 * rng.standard_normal(n)
    z = 0.2 * rng.standard_normal(n)
    return np.column_stack([radius * np.cos(theta), radius * np.sin(theta), z])




class TestPeierlsHamiltonian:
    def test_hermitian(self):
        coords = _ring_coords(8)
        H = peierls_hamiltonian(coords, cutoff=8.5, field_direction=(0, 0, 1), field_scale=0.1)
        np.testing.assert_allclose(H, np.conj(H).T, atol=1e-12)

    def test_zero_field_scale_gives_real_hamiltonian(self):
        """field_scale=0 means every phase theta_ij=0 regardless of
        direction/geometry -- H must reduce exactly to the real binary
        contact Hamiltonian (no residual complex part)."""
        coords = _ring_coords(8)
        H = peierls_hamiltonian(coords, cutoff=8.5, field_direction=(0, 0, 1), field_scale=0.0)
        np.testing.assert_allclose(np.imag(H), 0.0, atol=1e-12)
        W = contact_matrix(coords, cutoff=8.5, weight="binary")
        np.testing.assert_allclose(np.real(H), -W, atol=1e-12)

    def test_zero_direction_raises(self):
        coords = _chain_coords(4)
        with pytest.raises(ValueError, match="nonzero"):
            peierls_hamiltonian(coords, cutoff=5.0, field_direction=(0, 0, 0), field_scale=0.1)

    def test_phase_antisymmetric(self):
        """theta_ji = -theta_ij by cross-product antisymmetry -- checked
        directly via the off-diagonal phase angles, not just inferred
        from the Hermiticity test above (which would also pass for a
        trivially-zero H)."""
        coords = _ring_coords(6)
        H = peierls_hamiltonian(coords, cutoff=11.0, field_direction=(0, 1, 0), field_scale=0.2)
        nz = np.argwhere(np.abs(H) > 1e-12)
        assert len(nz) > 0
        for i, j in nz:
            if i < j:
                theta_ij = np.angle(H[i, j])
                theta_ji = np.angle(H[j, i])
                assert theta_ij == pytest.approx(-theta_ji, abs=1e-10)


class TestBipartiteAndSymmetryNulls:
    """Documents (as regression tests, not just prose) the ring-topology
    null mechanism found during development: a bare N-cycle (every node
    degree exactly 2, including a triangle at N=3) gives EXACTLY zero
    converged circulation from a diagonal seed, at ANY flux strength --
    confirmed here so a future change to `bond_current_converged` that
    accidentally breaks this documented invariant is caught, and so
    nobody re-derives this the hard way."""

    def test_uniform_ring_gives_zero_circulation_at_strong_flux(self):
        coords = _ring_coords(8)
        H = peierls_hamiltonian(coords, cutoff=8.5, field_direction=(0, 0, 1), field_scale=0.5)
        J = bond_current_converged(H, source=0)
        np.testing.assert_allclose(J, 0.0, atol=1e-9)

    def test_uniform_ring_gives_zero_circulation_for_incoherent_multi_seed(self):
        coords = _ring_coords(10)
        H = peierls_hamiltonian(coords, cutoff=8.0, field_direction=(1, 1, 1), field_scale=0.3)
        J = bond_current_converged(H, source=[0, 3, 7], coherent=False)
        np.testing.assert_allclose(J, 0.0, atol=1e-9)

    def test_ring_with_chord_stays_bipartite_and_null(self):
        """A chord across an even ring at an even hop-distance keeps the
        graph bipartite (both endpoints fall in the same bipartition
        class as any edge always crossing classes) -- still null."""
        coords = _ring_coords(6)
        # Add an explicit chord by moving two non-adjacent points closer
        # so the contact graph picks up edge (0, 3) alongside the ring.
        coords[3] = coords[0] + np.array([9.5, 0.5, 0.0])
        H = peierls_hamiltonian(coords, cutoff=10.0, field_direction=(0, 0, 1), field_scale=0.3)
        J = bond_current_converged(H, source=0)
        np.testing.assert_allclose(J, 0.0, atol=1e-8)

    def test_uniform_weight_triangle_is_also_null(self):
        """A single triangle (n=3, the minimal odd cycle) with uniform
        edge magnitude -- `contact_matrix`'s own "binary" weighting, this
        module's actual default -- gives exactly zero circulation from
        any diagonal seed, at any flux, confirmed directly across several
        flux values. Non-bipartiteness alone is *not* sufficient to break
        the ring null: a triangle is the degree-2-everywhere ring case at
        its smallest size (N=3), inheriting the same null as the
        mechanism above, not a separate exception to it."""
        coords = np.array([[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [2.0, 3.5, 0.0]])
        for field_scale in (0.1, 0.4, 0.9):
            H = peierls_hamiltonian(coords, cutoff=5.0, field_direction=(0, 0, 1), field_scale=field_scale)
            J = bond_current_converged(H, source=0)
            np.testing.assert_allclose(J, 0.0, atol=1e-9)

    def test_triangulated_asymmetric_graph_breaks_the_null(self):
        """Sanity check that the null is specific to ring-like topologies,
        not a blanket property of `bond_current_converged` -- confirms
        the fixture used for the "real signal" tests below actually
        produces one."""
        coords = _triangulated_asymmetric_coords()
        H = peierls_hamiltonian(coords, cutoff=12.0, field_direction=(0, 0, 1), field_scale=0.2)
        J = bond_current_converged(H, source=0)
        assert np.abs(J).max() > 1e-4


class TestBondCurrentConverged:
    def test_antisymmetric(self):
        coords = _triangulated_asymmetric_coords()
        H = peierls_hamiltonian(coords, cutoff=12.0, field_direction=(0, 0, 1), field_scale=0.2)
        J = bond_current_converged(H, source=0)
        np.testing.assert_allclose(J, -J.T, atol=1e-10)

    def test_zero_flux_gives_zero_current(self):
        """The physical guarantee this task's own Constraints require as
        a regression test: at zero flux (real H, since field_scale=0
        collapses every phase to zero), the converged current must
        vanish identically -- a real-symmetric H has real eigenvectors,
        so `rho_inf` is real and `J = 2*Im(H * rho_inf.T)` is exactly
        zero, not merely small. Uses the triangulated/asymmetric fixture
        so this is distinguished from the separate bipartite/symmetry
        null documented in `TestBipartiteAndSymmetryNulls`."""
        coords = _triangulated_asymmetric_coords()
        H = peierls_hamiltonian(coords, cutoff=12.0, field_direction=(0, 0, 1), field_scale=0.0)
        J = bond_current_converged(H, source=[0, 3], coherent=False)
        np.testing.assert_allclose(J, 0.0, atol=1e-10)

    def test_nonzero_flux_gives_nonzero_current(self):
        coords = _triangulated_asymmetric_coords()
        H = peierls_hamiltonian(coords, cutoff=12.0, field_direction=(0, 0, 1), field_scale=0.3)
        J = bond_current_converged(H, source=0)
        assert np.abs(J).max() > 1e-4

    def test_degenerate_spectrum_handled_without_error(self):
        """Two disconnected, identical triangulated-asymmetric fixtures
        share every eigenvalue (each copy's own spectrum repeats
        exactly) -- deliberately exactly degenerate. The projector-
        dephasing generalization must handle this without raising and
        without corrupting the (zero, by block-diagonal disconnection)
        cross terms between the two copies, and must reproduce the
        single-copy answer for the populated copy's own edges."""
        coords1 = _triangulated_asymmetric_coords(seed=0)
        coords2 = coords1 + np.array([1000.0, 0.0, 0.0])
        coords = np.vstack([coords1, coords2])
        H = peierls_hamiltonian(coords, cutoff=12.0, field_direction=(0, 0, 1), field_scale=0.2)

        n1 = len(coords1)
        J_double = bond_current_converged(H, source=0)

        H_single = peierls_hamiltonian(coords1, cutoff=12.0, field_direction=(0, 0, 1), field_scale=0.2)
        J_single = bond_current_converged(H_single, source=0)

        np.testing.assert_allclose(J_double[:n1, :n1], J_single, atol=1e-8)
        np.testing.assert_allclose(J_double[n1:, n1:], 0.0, atol=1e-10)
        np.testing.assert_allclose(J_double[:n1, n1:], 0.0, atol=1e-10)

    def test_coherent_vs_incoherent_differ_for_multi_index_source(self):
        coords = _triangulated_asymmetric_coords()
        H = peierls_hamiltonian(coords, cutoff=12.0, field_direction=(0, 0, 1), field_scale=0.25)
        j_coh = bond_current_converged(H, source=[0, 2, 5], coherent=True)
        j_incoh = bond_current_converged(H, source=[0, 2, 5], coherent=False)
        assert not np.allclose(j_coh, j_incoh)

    def test_coherent_and_incoherent_identical_for_scalar_source(self):
        coords = _triangulated_asymmetric_coords()
        H = peierls_hamiltonian(coords, cutoff=12.0, field_direction=(0, 0, 1), field_scale=0.25)
        j_coh = bond_current_converged(H, source=3, coherent=True)
        j_incoh = bond_current_converged(H, source=3, coherent=False)
        np.testing.assert_allclose(j_coh, j_incoh, atol=1e-10)


class TestHodgeDecompose:
    def test_reconstructs_J_exactly(self):
        """J_grad + J_circ == J -- the decomposition is a partition, not
        an approximation."""
        coords = _triangulated_asymmetric_coords()
        H = peierls_hamiltonian(coords, cutoff=12.0, field_direction=(0, 0, 1), field_scale=0.2)
        J = bond_current_converged(H, source=0)
        A = (contact_matrix(coords, cutoff=12.0, weight="binary") > 0).astype(float)
        J_grad, J_circ = hodge_decompose(J, A)
        np.testing.assert_allclose(J_grad + J_circ, J, atol=1e-10)

    def test_circulating_part_is_divergence_free(self):
        """div(J_circ) == 0 at every node -- the defining property of
        the circulating component, asserted numerically, not assumed
        from the construction alone."""
        coords = _triangulated_asymmetric_coords()
        H = peierls_hamiltonian(coords, cutoff=12.0, field_direction=(1, 1, 0), field_scale=0.25)
        J = bond_current_converged(H, source=[0, 1])
        A = (contact_matrix(coords, cutoff=12.0, weight="binary") > 0).astype(float)
        _, J_circ = hodge_decompose(J, A)
        div_circ = J_circ.sum(axis=1)
        np.testing.assert_allclose(div_circ, 0.0, atol=1e-8)

    def test_circulating_part_is_actually_nonzero(self):
        """The decomposition should not be a degenerate no-op on this
        fixture -- confirms J itself has genuine curl content here, not
        just that the (trivially true for J=0) divergence-free identity
        holds."""
        coords = _triangulated_asymmetric_coords()
        H = peierls_hamiltonian(coords, cutoff=12.0, field_direction=(0, 0, 1), field_scale=0.25)
        J = bond_current_converged(H, source=0)
        A = (contact_matrix(coords, cutoff=12.0, weight="binary") > 0).astype(float)
        _, J_circ = hodge_decompose(J, A)
        assert np.abs(J_circ).max() > 1e-4

    def test_gradient_part_matches_divergence_of_J(self):
        """div(J_grad) == div(J) exactly -- the Poisson-equation
        construction's own defining property."""
        coords = _triangulated_asymmetric_coords()
        H = peierls_hamiltonian(coords, cutoff=12.0, field_direction=(0, 0, 1), field_scale=0.18)
        J = bond_current_converged(H, source=0)
        A = (contact_matrix(coords, cutoff=12.0, weight="binary") > 0).astype(float)
        J_grad, _ = hodge_decompose(J, A)
        np.testing.assert_allclose(J_grad.sum(axis=1), J.sum(axis=1), atol=1e-8)

    def test_zero_current_decomposes_to_zero(self):
        coords = _ring_coords(6)
        A = (contact_matrix(coords, cutoff=11.0, weight="binary") > 0).astype(float)
        J = np.zeros((6, 6))
        J_grad, J_circ = hodge_decompose(J, A)
        np.testing.assert_allclose(J_grad, 0.0, atol=1e-10)
        np.testing.assert_allclose(J_circ, 0.0, atol=1e-10)


class TestChiralCirculationScore:
    def test_output_shape_and_finiteness(self):
        coords = _triangulated_asymmetric_coords()
        score = chiral_circulation_score(coords, source=0, cutoff=12.0)
        assert score.shape == (10,)
        assert np.isfinite(score).all()
        assert (score >= 0).all()

    def test_zero_field_scale_gives_zero_score(self):
        coords = _triangulated_asymmetric_coords()
        score = chiral_circulation_score(coords, source=0, cutoff=12.0, field_scale=0.0)
        np.testing.assert_allclose(score, 0.0, atol=1e-9)

    def test_uniform_ring_gives_zero_score_regardless_of_field_scale(self):
        """Reconfirms the bipartite/symmetry null at the
        `chiral_circulation_score` pipeline level, not just at
        `bond_current_converged`'s own level -- the two default field
        directions in the xy-plane are perpendicular to a ring lying in
        the xy-plane... it's the z-direction default that actually
        threads it; this checks the FULL default 3-direction average
        stays null on a ring regardless."""
        coords = _ring_coords(10)
        score = chiral_circulation_score(coords, source=0, cutoff=8.0, field_scale=0.3)
        np.testing.assert_allclose(score, 0.0, atol=1e-8)

    def test_nontrivial_topology_gives_nonzero_score(self):
        coords = _triangulated_asymmetric_coords()
        score = chiral_circulation_score(coords, source=0, cutoff=12.0, field_scale=0.2)
        assert score.max() > 1e-4


# ---------------------------------------------------------------------------
# GATE 1 -- dissociates coupling from well-depth (TASK-0140's own pre-
# registered regression gate, ported from TASK-0103's dumbbell negative-
# control apparatus, `tests/test_dumbbell_negative_control.py`). That
# fixture's own topology is a TREE (HUB -- one bridge -- lobe), and Peierls
# phases on a tree are always gaugeable to zero (no cycle to carry flux --
# see `chiral.py`'s own docstring), so it cannot be reused unmodified for a
# circulation-based observable. This loop-dumbbell keeps the same well-
# vs-coupling axis-separation logic (well = a diagonal trap on one lobe;
# coupling = the bridge edge weight) but connects HUB to each lobe via TWO
# disjoint bridge paths, so each lobe sits on its own genuine cycle for a
# single Peierls-substituted phase (placed on one representative edge per
# loop -- the WLOG single-edge gauge choice from `chiral.py`'s own §4) to
# circulate around.
# ---------------------------------------------------------------------------

_G1_HUB = [0]
_G1_DRUG = list(range(1, 5))
_G1_DECOY = list(range(5, 9))
_G1_BRIDGE_DRUG_A = [9, 10]
_G1_BRIDGE_DRUG_B = [11, 12]
_G1_BRIDGE_DECOY_A = [13, 14]
_G1_BRIDGE_DECOY_B = [15, 16]
_G1_N = 17
_G1_WELL_DEPTH = 5.0
_G1_STRONG = 1.0
_G1_WEAK = 0.15
_G1_PHASE = 0.6


def _build_loop_dumbbell(well_lobe, strong_lobe, *, seed: int = 0):
    """Returns `(W_real, H_complex, A_binary)`: `W_real` the real
    symmetric weight matrix with the diagonal well applied (no Peierls
    phase -- for a well-tracking comparison observable, `ground_state_
    relaxation`), `H_complex` the same network with a single, fixed-
    magnitude Peierls phase on one bridge edge of each lobe's loop (for
    the circulation score), and `A_binary` the shared binary adjacency
    for the Hodge split. Randomized per `seed` (intra-lobe clique weights,
    bridge anchor choice) matching TASK-0103's own reasoning: without
    this, "averaging over seeds" would silently repeat one number."""
    rng = np.random.default_rng(seed)
    W = np.zeros((_G1_N, _G1_N))

    def _clique(idxs):
        for i in idxs:
            for j in idxs:
                if i < j:
                    W[i, j] = W[j, i] = rng.uniform(0.7, 1.3)

    _clique(_G1_DRUG)
    _clique(_G1_DECOY)

    if strong_lobe is None:
        w_drug = w_decoy = 0.5
    else:
        w_drug = _G1_STRONG if strong_lobe == "DRUG" else _G1_WEAK
        w_decoy = _G1_STRONG if strong_lobe == "DECOY" else _G1_WEAK

    anchor_drug = int(rng.choice(_G1_DRUG))
    anchor_decoy = int(rng.choice(_G1_DECOY))

    for chain, w in (
        ([_G1_HUB[0]] + _G1_BRIDGE_DRUG_A + [anchor_drug], w_drug),
        ([_G1_HUB[0]] + _G1_BRIDGE_DRUG_B + [anchor_drug], w_drug),
        ([_G1_HUB[0]] + _G1_BRIDGE_DECOY_A + [anchor_decoy], w_decoy),
        ([_G1_HUB[0]] + _G1_BRIDGE_DECOY_B + [anchor_decoy], w_decoy),
    ):
        for a, b in zip(chain[:-1], chain[1:]):
            W[a, b] = W[b, a] = w

    diag = np.zeros(_G1_N)
    if well_lobe == "DRUG":
        diag[_G1_DRUG] -= _G1_WELL_DEPTH
    elif well_lobe == "DECOY":
        diag[_G1_DECOY] -= _G1_WELL_DEPTH

    W_real = -W.copy()
    np.fill_diagonal(W_real, diag)

    H = -W.astype(complex)
    for hub_node, bridge0, w in (
        (_G1_HUB[0], _G1_BRIDGE_DRUG_A[0], w_drug),
        (_G1_HUB[0], _G1_BRIDGE_DECOY_A[0], w_decoy),
    ):
        H[hub_node, bridge0] = -w * np.exp(1j * _G1_PHASE)
        H[bridge0, hub_node] = np.conj(H[hub_node, bridge0])
    np.fill_diagonal(H, diag)

    A_binary = (np.abs(W) > 1e-12).astype(float)
    return W_real, H, A_binary


def _g1_auc_to_drug(score: np.ndarray) -> float:
    scores = np.concatenate([score[_G1_DRUG], score[_G1_DECOY]])
    labels = np.concatenate([np.ones(len(_G1_DRUG)), np.zeros(len(_G1_DECOY))])
    return _auc(scores, labels)


def _g1_mean_circulation_auc(well_lobe, strong_lobe, n_seeds: int = 8) -> float:
    aucs = []
    for seed in range(n_seeds):
        _, H, A = _build_loop_dumbbell(well_lobe, strong_lobe, seed=seed)
        score = circulation_score_from_hamiltonians([H], _G1_HUB, A)
        aucs.append(_g1_auc_to_drug(score))
    return float(np.mean(aucs))


def _g1_mean_gsr_auc(well_lobe, strong_lobe, n_seeds: int = 8) -> float:
    aucs = []
    for seed in range(n_seeds):
        W_real, _, _ = _build_loop_dumbbell(well_lobe, strong_lobe, seed=seed)
        p = ground_state_relaxation(W_real, 20.0, source=_G1_HUB)
        aucs.append(_g1_auc_to_drug(p))
    return float(np.mean(aucs))


class TestGate1CouplingVsWellDissociation:
    """The decisive cells (well and coupling deliberately disagree): the
    chiral circulation score must follow the COUPLING (which lobe has the
    strong bridge), not the WELL (which lobe has the diagonal trap) --
    while `ground_state_relaxation` (an imaginary-time, well-chasing
    observable, TASK-0103's own established contrast) must do the
    opposite on the identical topology. Confirmed directly (not assumed
    from the original dumbbell's tree-topology result, which used a
    different, cycle-free construction that cannot carry Peierls flux at
    all)."""

    def test_circulation_follows_coupling_when_well_is_on_decoy(self):
        auc = _g1_mean_circulation_auc(well_lobe="DECOY", strong_lobe="DRUG")
        assert auc > 0.7, f"circulation did not follow coupling (AUC={auc:.3f})"

    def test_circulation_follows_coupling_when_well_is_on_drug(self):
        auc = _g1_mean_circulation_auc(well_lobe="DRUG", strong_lobe="DECOY")
        assert auc < 0.3, f"circulation did not follow coupling (AUC={auc:.3f})"

    def test_gsr_follows_well_not_coupling_contrast(self):
        """Contrast check on the identical topology: GSR must do the
        OPPOSITE of the two tests above, confirming this network's own
        well/coupling axes are genuinely independent, not confounded."""
        auc_well_decoy = _g1_mean_gsr_auc(well_lobe="DECOY", strong_lobe="DRUG")
        auc_well_drug = _g1_mean_gsr_auc(well_lobe="DRUG", strong_lobe="DECOY")
        assert auc_well_decoy < 0.3, f"GSR unexpectedly followed coupling (AUC={auc_well_decoy:.3f})"
        assert auc_well_drug > 0.7, f"GSR unexpectedly followed coupling (AUC={auc_well_drug:.3f})"


# ---------------------------------------------------------------------------
# GATE 2 -- beats the proximity floor on a synthetic distal loop pocket
# (TASK-0140's own pre-registered regression gate). HYP-P9's own
# (unrecoverable -- reference script confirmed missing) cited numbers were
# residual rho(score,-dist) ~ +0.33 for circulation vs +0.6..+0.97 for
# occupation; this reconstruction is not fit to reproduce those exact
# figures (impossible without the original script) but is built
# independently to test the same qualitative claim, and its own actual
# numbers are reported here and in this task's own Done section, not
# silently forced to match.
#
# Construction: a backbone (the natural, monotonically-receding
# background population) forks into two branches of matched length at
# its far end -- a POCKET branch (tight residue spacing, so a fixed
# global cutoff naturally picks up next-nearest-neighbor edges there,
# giving it genuine local loop/triangulated structure to circulate in --
# same mechanism as `_triangulated_asymmetric_coords`) and a DECOY branch
# (normal spacing, stays bare/ring-like, near-null by this module's own
# §4). Both branches are equidistant from the seed by construction (same
# node count, mirrored angle) -- exactly TASK-0103's own "same bridge
# length" design principle, so proximity alone cannot separate them.
# ---------------------------------------------------------------------------


def _gate2_coords(n_backbone: int = 16, branch_len: int = 8, seed: int = 0):
    """Returns `(coords, idx)`; `idx` maps "backbone"/"pocket"/"decoy"/
    "seed" to node-index lists. See module comment above for the design."""
    rng = np.random.default_rng(seed)
    backbone = np.zeros((n_backbone, 3))
    backbone[:, 0] = np.arange(n_backbone) * 6.0
    backbone[:, 1] = 0.4 * rng.standard_normal(n_backbone)
    backbone[:, 2] = 0.4 * rng.standard_normal(n_backbone)
    base = backbone[-1]

    pocket = np.zeros((branch_len, 3))
    ang = 0.6
    pocket[:, 0] = base[0] + np.cumsum(np.full(branch_len, 3.0)) * np.cos(ang)
    pocket[:, 1] = base[1] + np.cumsum(np.full(branch_len, 3.0)) * np.sin(ang) + 0.3 * rng.standard_normal(branch_len)
    pocket[:, 2] = base[2] + 0.3 * rng.standard_normal(branch_len)

    decoy = np.zeros((branch_len, 3))
    ang2 = -0.6
    decoy[:, 0] = base[0] + np.cumsum(np.full(branch_len, 6.0)) * np.cos(ang2)
    decoy[:, 1] = base[1] + np.cumsum(np.full(branch_len, 6.0)) * np.sin(ang2) + 0.3 * rng.standard_normal(branch_len)
    decoy[:, 2] = base[2] + 0.3 * rng.standard_normal(branch_len)

    coords = np.vstack([backbone, pocket, decoy])
    idx = {
        "backbone": list(range(n_backbone)),
        "pocket": list(range(n_backbone, n_backbone + branch_len)),
        "decoy": list(range(n_backbone + branch_len, n_backbone + 2 * branch_len)),
        "seed": [0, 1],
    }
    return coords, idx


_GATE2_CUTOFF = 7.0
_GATE2_FIELD_SCALE = 0.2


class TestGate2BeatsFloorOnSyntheticLoopPocket:
    def test_circulation_beats_the_proximity_floor(self):
        """`diagnostics.classify_failure` against the project's own
        established floor candidates (euclid-from-seed, hop-from-seed,
        degree-centrality, `baselines.py`) -- the same check every real
        operator in this program is held to, not a bespoke pass bar."""
        coords, idx = _gate2_coords()
        n = len(coords)
        source = idx["seed"]
        circ = chiral_circulation_score(coords, source=source, cutoff=_GATE2_CUTOFF, field_scale=_GATE2_FIELD_SCALE)

        labels = np.zeros(n, dtype=int)
        labels[idx["pocket"]] = 1
        mask = np.ones(n, dtype=bool)
        mask[source] = False

        floor_scores = np.stack([
            euclid_from_seed_centroid(coords, source)[mask],
            hop_from_seed(coords, source, cutoff=_GATE2_CUTOFF)[mask],
            degree_centrality(coords, cutoff=_GATE2_CUTOFF)[mask],
        ])
        category = classify_failure(circ[mask], labels[mask], floor_scores=floor_scores)
        assert category == NO_FAILURE_DETECTED, f"circulation did not beat the floor ({category})"

    def test_occupation_does_not_beat_the_floor_on_this_construction(self):
        """Contrast check: the converged occupation observable
        (`propagators.time_averaged_ctqw_converged`, this project's own
        established convention, TASK-0130) should NOT beat the floor
        here -- confirms the pocket's signal genuinely requires reading
        loop structure, not just "any observable finds it"."""
        coords, idx = _gate2_coords()
        n = len(coords)
        source = idx["seed"]
        W = contact_matrix(coords, cutoff=_GATE2_CUTOFF, weight="binary")
        occ = time_averaged_ctqw_converged(-W, source=source, coherent=False)

        labels = np.zeros(n, dtype=int)
        labels[idx["pocket"]] = 1
        mask = np.ones(n, dtype=bool)
        mask[source] = False

        floor_scores = np.stack([
            euclid_from_seed_centroid(coords, source)[mask],
            hop_from_seed(coords, source, cutoff=_GATE2_CUTOFF)[mask],
            degree_centrality(coords, cutoff=_GATE2_CUTOFF)[mask],
        ])
        category = classify_failure(occ[mask], labels[mask], floor_scores=floor_scores)
        assert category != NO_FAILURE_DETECTED, f"occupation unexpectedly beat the floor ({category})"

    def test_circulation_correlates_with_distance_much_less_than_occupation(self):
        """The residual-correlation-with-distance comparison HYP-P9's own
        text reports (circulation << occupation, not necessarily the
        exact +0.33 vs +0.6..+0.97 figures from the unrecoverable
        original script -- this reconstruction's own numbers, reported
        here and in this task's own Done section)."""
        from scipy.stats import spearmanr

        coords, idx = _gate2_coords()
        source = idx["seed"]
        W = contact_matrix(coords, cutoff=_GATE2_CUTOFF, weight="binary")
        occ = time_averaged_ctqw_converged(-W, source=source, coherent=False)
        circ = chiral_circulation_score(coords, source=source, cutoff=_GATE2_CUTOFF, field_scale=_GATE2_FIELD_SCALE)

        mask = np.ones(len(coords), dtype=bool)
        mask[source] = False
        dist = -euclid_from_seed_centroid(coords, source)

        rho_occ = spearmanr(occ[mask], dist[mask]).correlation
        rho_circ = spearmanr(circ[mask], dist[mask]).correlation
        assert abs(rho_occ) > 0.5, f"occupation's own proximity confound was weaker than expected (rho={rho_occ:.3f})"
        assert abs(rho_circ) < 0.25, f"circulation correlated with distance more than expected (rho={rho_circ:.3f})"


class TestHRealPath:
    """TASK-0140's own real-data call shape (`chiral_circulation_score(...,
    H_real=...)`, so `H_new`'s actual weighting -- not a fresh binary
    contact matrix -- drives the off-diagonal magnitudes, per the task
    file's explicit `chiral_circulation_score(H_real, coords, source)`
    instruction). Checked directly before trusting it on real targets."""

    def test_diagonal_preserved_exactly(self):
        coords = _triangulated_asymmetric_coords()
        rng = np.random.default_rng(1)
        H_real = -(contact_matrix(coords, cutoff=12.0, weight="binary"))
        diag = rng.uniform(-2.0, 2.0, size=len(coords))
        np.fill_diagonal(H_real, diag)
        H = peierls_hamiltonian(coords, cutoff=12.0, field_direction=(0, 0, 1), field_scale=0.2, H_real=H_real)
        np.testing.assert_allclose(np.diag(H).real, diag, atol=1e-10)
        np.testing.assert_allclose(np.diag(H).imag, 0.0, atol=1e-10)

    def test_off_diagonal_magnitude_preserved(self):
        """The phase is inserted multiplicatively -- `|H[i,j]|` must
        equal `|H_real[i,j]|` exactly, whatever weighting scheme
        `H_real` used (not rederived from a fresh contact matrix)."""
        coords = _triangulated_asymmetric_coords()
        H_real = -(contact_matrix(coords, cutoff=12.0, weight="invdist"))
        H = peierls_hamiltonian(coords, cutoff=12.0, field_direction=(0, 0, 1), field_scale=0.2, H_real=H_real)
        np.testing.assert_allclose(np.abs(H), np.abs(H_real), atol=1e-10)

    def test_hermitian(self):
        coords = _triangulated_asymmetric_coords()
        H_real = -(contact_matrix(coords, cutoff=12.0, weight="binary"))
        H = peierls_hamiltonian(coords, cutoff=12.0, field_direction=(0, 0, 1), field_scale=0.2, H_real=H_real)
        np.testing.assert_allclose(H, np.conj(H).T, atol=1e-12)

    def test_zero_field_scale_reduces_to_H_real(self):
        coords = _triangulated_asymmetric_coords()
        H_real = -(contact_matrix(coords, cutoff=12.0, weight="binary"))
        H = peierls_hamiltonian(coords, cutoff=12.0, field_direction=(0, 0, 1), field_scale=0.0, H_real=H_real)
        np.testing.assert_allclose(H.real, H_real, atol=1e-12)
        np.testing.assert_allclose(H.imag, 0.0, atol=1e-12)

    def test_chiral_circulation_score_h_real_path_runs_and_beats_gate2_still(self):
        """End-to-end: `chiral_circulation_score(..., H_real=...)` on the
        GATE-2 fixture with an explicit (here, identical-to-default)
        `H_real` reproduces the coords-only path's own result -- confirms
        the `H_real` plumbing (adjacency-from-H_real, diagonal handling)
        doesn't silently change behavior when `H_real` matches what the
        coords-only path would have built anyway."""
        coords, idx = _gate2_coords()
        source = idx["seed"]
        H_real = -(contact_matrix(coords, cutoff=_GATE2_CUTOFF, weight="binary"))
        score_default = chiral_circulation_score(coords, source=source, cutoff=_GATE2_CUTOFF, field_scale=_GATE2_FIELD_SCALE)
        score_h_real = chiral_circulation_score(
            coords, source=source, cutoff=_GATE2_CUTOFF, field_scale=_GATE2_FIELD_SCALE, H_real=H_real
        )
        np.testing.assert_allclose(score_default, score_h_real, atol=1e-10)
