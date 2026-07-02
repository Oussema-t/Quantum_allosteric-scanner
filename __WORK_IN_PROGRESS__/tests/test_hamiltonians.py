"""Group B coverage tests — hamiltonians, potentials, and propagator utilities.

Each section corresponds to a TASKS.md Group B item.  Only completed items are
implemented here; future tasks will be added in-place.

Sections implemented
--------------------
T-009  contact_matrix() – weight schemes, exact values on a 4-point line
T-010  contact_matrix() – cutoff boundary and distance geometry vs. cdist
T-011  Structural/spectral smoke tests for H1 – H13
T-012  build_H_new() – shape, symmetry, zero-lambda recovery
T-014  time_averaged_ctqw() – dimer long-time limit → 0.5
T-015  ipr, spectral_gap, check_degree_correlation – analytical values
T-016  ctqw + heat on synthetic helical backbone
"""
import numpy as np
import pytest
import networkx as nx
from scipy.spatial.distance import cdist

from allostery.propagators import ctqw, heat, time_averaged_ctqw
from allostery.hamiltonians import (
    contact_matrix,
    laplacian,
    normalised_laplacian_alpha,
    build_H_new,
    H1_unweighted_adjacency,
    H2_combinatorial_laplacian,
    H3_normalised_laplacian,
    H4_powered_normalised,
    H5_gaussian_elastic,
    H6_exponential_decay,
    H7_harmonic,
    H8_gnm,
    H9_bfactor_regularised,
    H10_disorder_suppressed,
    H11_anisotropic_mechanical,
    H12_anm_scalarised,
    H13_3N_anm_hessian,
)
from allostery.metrics import ipr, spectral_gap, check_degree_correlation


# ---------------------------------------------------------------------------
# T-009 · contact_matrix() — weight schemes, exact values on a 4-point line
# ---------------------------------------------------------------------------

class TestContactMatrixWeightSchemes:
    """4 colinear points at unit spacing; cutoff=2.5 keeps dist∈{1,2} and drops
    dist=3 (the (0,3) pair). Expected values are computed from the closed-form
    weight formulas, not by re-deriving contact_matrix's own code path."""

    coords = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0],
                        [2.0, 0.0, 0.0], [3.0, 0.0, 0.0]])
    cutoff = 2.5

    @staticmethod
    def _expected(v1: float, v2: float) -> np.ndarray:
        """Fill the (0,3)-excluded pattern with per-distance values v1 (dist=1)
        and v2 (dist=2)."""
        return np.array([
            [0.0, v1, v2, 0.0],
            [v1, 0.0, v1, v2],
            [v2, v1, 0.0, v1],
            [0.0, v2, v1, 0.0],
        ])

    def _assert_symmetric_zero_diagonal(self, W: np.ndarray):
        assert np.allclose(W, W.T)
        assert np.allclose(np.diag(W), 0.0)

    def test_binary(self):
        W = contact_matrix(self.coords, cutoff=self.cutoff, weight="binary")
        np.testing.assert_allclose(W, self._expected(1.0, 1.0))
        self._assert_symmetric_zero_diagonal(W)

    def test_gaussian(self):
        sigma = 2.0
        W = contact_matrix(self.coords, cutoff=self.cutoff, weight="gaussian", sigma=sigma)
        v1 = np.exp(-(1.0 ** 2) / (2 * sigma ** 2))
        v2 = np.exp(-(2.0 ** 2) / (2 * sigma ** 2))
        np.testing.assert_allclose(W, self._expected(v1, v2), atol=1e-12)
        self._assert_symmetric_zero_diagonal(W)

    def test_exponential(self):
        alpha = 0.5
        W = contact_matrix(self.coords, cutoff=self.cutoff, weight="exponential", alpha=alpha)
        v1 = np.exp(-alpha * 1.0)
        v2 = np.exp(-alpha * 2.0)
        np.testing.assert_allclose(W, self._expected(v1, v2), atol=1e-12)
        self._assert_symmetric_zero_diagonal(W)

    def test_harmonic(self):
        """1/(d+eps)**2 with eps=1e-6 (internal); the eps shift is <2e-6 relative
        so atol=1e-4 comfortably separates it from a wrong formula."""
        W = contact_matrix(self.coords, cutoff=self.cutoff, weight="harmonic")
        v1 = 1.0 / 1.0 ** 2
        v2 = 1.0 / 2.0 ** 2
        np.testing.assert_allclose(W, self._expected(v1, v2), atol=1e-4)
        self._assert_symmetric_zero_diagonal(W)

    def test_invdist(self):
        """1/(d+eps) with eps=1e-6 (internal); see test_harmonic for tolerance."""
        W = contact_matrix(self.coords, cutoff=self.cutoff, weight="invdist")
        v1 = 1.0 / 1.0
        v2 = 1.0 / 2.0
        np.testing.assert_allclose(W, self._expected(v1, v2), atol=1e-4)
        self._assert_symmetric_zero_diagonal(W)

    def test_unknown_weight_raises(self):
        with pytest.raises(ValueError):
            contact_matrix(self.coords, cutoff=self.cutoff, weight="not_a_scheme")


# ---------------------------------------------------------------------------
# T-010 · contact_matrix() — cutoff boundary and distance geometry
# ---------------------------------------------------------------------------

class TestContactMatrixCutoffAndGeometry:

    def test_dist_at_cutoff_boundary_is_excluded(self):
        """Pairs with dist >= cutoff (strict '<' mask) must get zero weight,
        even at the exact boundary value."""
        coords = np.array([[0.0, 0.0, 0.0], [5.0, 0.0, 0.0], [10.0, 0.0, 0.0]])
        W = contact_matrix(coords, cutoff=5.0, weight="binary")
        assert np.allclose(W, 0.0), "dist == cutoff must not be included"

    @pytest.mark.parametrize("weight,kwargs", [
        ("binary", {}), ("gaussian", {}), ("exponential", {}),
        ("harmonic", {}), ("invdist", {}),
    ])
    def test_self_loops_always_zero(self, weight, kwargs):
        coords = np.array([[0.0, 0.0, 0.0], [3.0, 1.0, 0.0], [-2.0, 4.0, 1.0],
                            [5.0, -3.0, 2.0]])
        W = contact_matrix(coords, cutoff=100.0, weight=weight, **kwargs)
        assert np.allclose(np.diag(W), 0.0), f"{weight}: diagonal not zero"

    coords_geo = np.array([
        [0.0, 0.0, 0.0], [3.0, 0.0, 0.0], [0.0, 4.0, 0.0], [6.0, 8.0, 0.0],
        [1.0, 1.0, 1.0], [-2.0, 3.0, 5.0], [4.0, -1.0, 2.0], [-3.0, -3.0, -3.0],
    ])

    def test_pairwise_distances_match_cdist(self):
        """contact_matrix's internal Euclidean distance must agree with
        scipy.spatial.distance.cdist, the independent reference."""
        D_ref = cdist(self.coords_geo, self.coords_geo)
        for cutoff in (5.0, 8.0, 12.0):
            expected = ((D_ref < cutoff) & (D_ref > 0)).astype(float)
            got = contact_matrix(self.coords_geo, cutoff=cutoff, weight="binary")
            np.testing.assert_allclose(got, expected)

    @pytest.mark.parametrize("cutoff", [5.0, 8.0, 12.0])
    def test_dist_ge_cutoff_produce_zero_weight(self, cutoff):
        D_ref = cdist(self.coords_geo, self.coords_geo)
        W = contact_matrix(self.coords_geo, cutoff=cutoff, weight="binary")
        assert np.all(W[D_ref >= cutoff] == 0.0)


# ---------------------------------------------------------------------------
# T-011 · Structural/spectral smoke tests for H1 – H13
# ---------------------------------------------------------------------------

_H11_BFACTORS = np.array([30.0, 25.0, 18.0, 22.0, 30.0, 15.0])

# Laplacian-based operators: PSD, with exactly one zero mode on a connected
# 6-node graph. (Confirmed empirically: H2-H9, H11, H12 all have nullity==1
# on the fixture below; H1 is adjacency-based and H10/H13 are handled
# separately below because they break the plain nullity>=1 pattern.)
_LAPLACIAN_OPS = {
    "H2": lambda c: H2_combinatorial_laplacian(c, cutoff=10.0),
    "H3": lambda c: H3_normalised_laplacian(c, cutoff=10.0),
    "H4": lambda c: H4_powered_normalised(c, cutoff=10.0),
    "H5": lambda c: H5_gaussian_elastic(c, cutoff=10.0),
    "H6": lambda c: H6_exponential_decay(c, cutoff=10.0),
    "H7": lambda c: H7_harmonic(c, cutoff=10.0),
    "H8": lambda c: H8_gnm(c, cutoff=10.0),
    "H9": lambda c: H9_bfactor_regularised(c, _H11_BFACTORS, cutoff=10.0),
    "H11": lambda c: H11_anisotropic_mechanical(c, cutoff=10.0),
    "H12": lambda c: H12_anm_scalarised(c, cutoff=10.0),
}


class TestH1toH13Smoke:
    """Fixed 6-residue synthetic helix (non-colinear, avoids the ANM rotational
    degeneracy that a straight-line fixture would introduce for H13)."""

    @staticmethod
    @pytest.fixture(scope="class")
    def coords6():
        return _helix_coords(6)

    def test_h1_matches_binary_contact_matrix(self, coords6):
        A = contact_matrix(coords6, cutoff=10.0, weight="binary")
        H1 = H1_unweighted_adjacency(coords6, cutoff=10.0)
        assert H1.shape == (6, 6)
        assert np.allclose(H1, H1.T)
        np.testing.assert_allclose(H1, A)

    @pytest.mark.parametrize("name", sorted(_LAPLACIAN_OPS))
    def test_laplacian_ops_psd_with_nullity(self, coords6, name):
        M = _LAPLACIAN_OPS[name](coords6)
        assert M.shape == (6, 6)
        assert np.allclose(M, M.T), f"{name} is not symmetric"
        w = np.linalg.eigvalsh(M)
        assert (w >= -1e-10).all(), f"{name} has eigenvalue {w.min():.3e} < -1e-10"
        nullity = int((np.abs(w) < 1e-8).sum())
        assert nullity >= 1, f"{name} nullity={nullity}, expected >= 1 on a connected graph"

    def test_h10_disorder_suppressed_psd_no_zero_mode(self, coords6):
        """H10 adds strictly non-negative diagonal terms (V_B, V_F) on top of the
        combinatorial Laplacian; it stays PSD but the diagonal shift lifts the
        zero mode away from zero, so nullity is *not* asserted here."""
        M = H10_disorder_suppressed(coords6, _H11_BFACTORS, cutoff=10.0)
        assert M.shape == (6, 6)
        assert np.allclose(M, M.T)
        w = np.linalg.eigvalsh(M)
        assert (w >= -1e-10).all()

    def test_h13_shape_and_translational_nullspace(self, coords6):
        """H13 operates in 3N x 3N space; translational invariance guarantees
        (at least) 3 zero modes regardless of coordinate geometry."""
        M = H13_3N_anm_hessian(coords6, cutoff=10.0)
        N = coords6.shape[0]
        assert M.shape == (3 * N, 3 * N)
        assert np.allclose(M, M.T)
        w = np.linalg.eigvalsh(M)
        assert (w >= -1e-10).all()
        nullity = int((np.abs(w) < 1e-8).sum())
        assert nullity >= 3, f"H13 nullity={nullity}, expected >= 3 (translations)"


# ---------------------------------------------------------------------------
# T-012 · build_H_new()
# ---------------------------------------------------------------------------

class TestBuildHNew:
    """Synthetic 10-residue helix with uniform B-factors."""

    BFACTORS_UNIFORM = np.full(10, 20.0)

    @staticmethod
    @pytest.fixture(scope="class")
    def coords10():
        return _helix_coords(10)

    def test_shape_and_symmetry(self, coords10):
        Hn = build_H_new(coords10, self.BFACTORS_UNIFORM, cutoff=10.0)
        assert Hn.shape == (10, 10)
        assert np.allclose(Hn, Hn.T)

    def test_zero_lambdas_recovers_base_laplacian(self, coords10):
        """lam_B=lam_T=lam_R=lam_C=lam_M=0 must recover normalised_laplacian_alpha
        exactly — build_H_new degenerates to its base term with no potentials."""
        Hn = build_H_new(
            coords10, self.BFACTORS_UNIFORM, cutoff=10.0,
            lam_B=0.0, lam_T=0.0, lam_R=0.0, lam_C=0.0, lam_M=0.0,
        )
        L = normalised_laplacian_alpha(coords10, cutoff=10.0)
        np.testing.assert_allclose(Hn, L, atol=1e-12)

    def test_base_laplacian_is_psd(self, coords10):
        """With all potential terms disabled, H_new is exactly a normalised
        graph Laplacian and must be positive semidefinite."""
        Hn = build_H_new(
            coords10, self.BFACTORS_UNIFORM, cutoff=10.0,
            lam_B=0.0, lam_T=0.0, lam_R=0.0, lam_C=0.0, lam_M=0.0,
        )
        w = np.linalg.eigvalsh(Hn)
        assert (w >= -1e-10).all()

    def test_default_h_new_is_not_globally_psd(self, coords10):
        """V_R, V_C, V_M (potentials.py) are *reward* terms — they contribute a
        negative diagonal for rigid/coupled/low-mode-participating residues by
        design (see CRIT-003 T-019/T-020) and are not constrained to preserve
        positive-semidefiniteness. Empirically, default build_H_new has at
        least one negative eigenvalue. This is a canary, not a hard physics
        requirement: if potentials.py semantics change and this starts failing,
        that's a signal to revisit this note and TASKS.md T-012, not to loosen
        the assertion."""
        Hn = build_H_new(coords10, self.BFACTORS_UNIFORM, cutoff=10.0)
        w = np.linalg.eigvalsh(Hn)
        assert w.min() < 0


# ---------------------------------------------------------------------------
# T-015 · ipr, spectral_gap, check_degree_correlation — analytical values
# ---------------------------------------------------------------------------

class TestIPR:
    """Inverse Participation Ratio: IPR(v) = Σv_i⁴ / (Σv_i²)²."""

    def test_uniform_vector(self):
        """Uniform v = (1/√N, …): IPR = 1/N (maximally delocalised)."""
        N = 12
        v = np.full(N, 1.0 / np.sqrt(N))
        assert abs(ipr(v) - 1.0 / N) < 1e-10, f"IPR={ipr(v):.6f}, expected {1/N:.6f}"

    def test_localised_vector(self):
        """Single-entry v = (1, 0, …, 0): IPR = 1 (maximally localised)."""
        N = 12
        v = np.zeros(N)
        v[3] = 1.0
        assert abs(ipr(v) - 1.0) < 1e-10

    def test_two_equal_entries(self):
        """v = (1/√2, 1/√2, 0, …): IPR = 1/2."""
        N = 10
        v = np.zeros(N)
        v[0] = v[1] = 1.0 / np.sqrt(2)
        assert abs(ipr(v) - 0.5) < 1e-10

    def test_scale_invariance(self):
        """IPR must be homogeneous of degree 0: ipr(c·v) = ipr(v)."""
        v = np.array([0.1, 0.4, 0.5, 0.0, 0.7])
        assert abs(ipr(v) - ipr(7.3 * v)) < 1e-12
        assert abs(ipr(v) - ipr(-3.0 * v)) < 1e-12

    @pytest.mark.parametrize("N", [4, 8, 20])
    def test_uniform_parameterised(self, N):
        """IPR = 1/N for any N with uniform eigenvector."""
        v = np.full(N, 1.0 / np.sqrt(N))
        assert abs(ipr(v) - 1.0 / N) < 1e-10


class TestSpectralGap:
    """spectral_gap(w) = second − first non-negative eigenvalue."""

    def test_path5_known_value(self):
        """Path graph P₅: gap = 2(1 − cos(π/5)) ≈ 0.38197."""
        G = nx.path_graph(5)
        w = np.linalg.eigvalsh(
            nx.laplacian_matrix(G).toarray().astype(float)
        )
        expected = 2.0 * (1.0 - np.cos(np.pi / 5))
        assert abs(spectral_gap(w) - expected) < 1e-10

    @pytest.mark.parametrize("N", [4, 6, 8])
    def test_complete_graph(self, N):
        """K_N Laplacian eigenvalues: 0 (×1) and N (×N−1) → gap = N."""
        w = np.linalg.eigvalsh(
            nx.laplacian_matrix(nx.complete_graph(N)).toarray().astype(float)
        )
        assert abs(spectral_gap(w) - N) < 1e-10

    def test_disconnected_zero_gap(self):
        """Two disjoint components → two zero eigenvalues → gap = 0."""
        G = nx.disjoint_union(nx.path_graph(4), nx.path_graph(4))
        w = np.linalg.eigvalsh(
            nx.laplacian_matrix(G).toarray().astype(float)
        )
        assert abs(spectral_gap(w)) < 1e-10

    def test_single_eigenvalue_nan(self):
        """Only one non-negative eigenvalue → gap is undefined (nan)."""
        assert np.isnan(spectral_gap(np.array([1.5])))

    def test_cycle_gap(self):
        """Cycle C₈: gap = 2(1 − cos(2π/8)) = 2 − √2 ≈ 0.5858."""
        N = 8
        w = np.linalg.eigvalsh(
            nx.laplacian_matrix(nx.cycle_graph(N)).toarray().astype(float)
        )
        expected = 2.0 * (1.0 - np.cos(2 * np.pi / N))
        assert abs(spectral_gap(w) - expected) < 1e-10


class TestDegreeCorrrelation:
    """check_degree_correlation returns Pearson r between scores and node degree."""

    # 10 nodes on a 1-D line at 5 Å spacing; cutoff=10 Å → path graph
    # degree = [1, 2, 2, 2, 2, 2, 2, 2, 2, 1]
    coords_1d = np.column_stack([
        np.arange(10, dtype=float) * 5.0,
        np.zeros(10),
        np.zeros(10),
    ])

    def _degree(self):
        A = contact_matrix(self.coords_1d, cutoff=10.0, weight="binary")
        return A.sum(axis=1)

    def test_scores_equal_degree_r1(self):
        """Scores proportional to degree → Pearson r = 1.0."""
        d = self._degree()
        r = check_degree_correlation(d, self.coords_1d, cutoff=10.0)
        assert abs(r - 1.0) < 1e-10, f"r={r:.6f}, expected 1.0"

    def test_scores_neg_degree_r_minus1(self):
        """Scores = −degree → Pearson r = −1.0."""
        d = self._degree()
        r = check_degree_correlation(-d, self.coords_1d, cutoff=10.0)
        assert abs(r + 1.0) < 1e-10, f"r={r:.6f}, expected −1.0"

    def test_returns_float(self):
        """Return type is a Python float (not an array)."""
        d = self._degree()
        r = check_degree_correlation(d, self.coords_1d, cutoff=10.0)
        assert isinstance(r, float)

    def test_uniform_scores_nan(self):
        """Uniform scores (zero variance) → Pearson r is undefined (nan)."""
        uniform = np.ones(10)
        r = check_degree_correlation(uniform, self.coords_1d, cutoff=10.0)
        assert np.isnan(r), f"Expected NaN for uniform scores, got {r}"


# ---------------------------------------------------------------------------
# T-014 · time_averaged_ctqw — dimer long-time average → 0.5
# ---------------------------------------------------------------------------

class TestTimeAveragedCTQW:
    """Tests for time_averaged_ctqw().

    Analytical reference: dimer H = [[0,1],[1,0]], eigenvalues ±1.
    P(0,t|source=0) = cos²(t).
    Time average over [0, T]: ½ + sin(2T)/(4T) → ½ as T→∞.
    At T=200 the correction is |sin(400)|/800 < 1.25e-3, so atol=0.02 is conservative.
    """

    H_dimer = np.array([[0.0, 1.0], [1.0, 0.0]])

    def test_dimer_long_time_source0(self):
        """P_avg(source=0) → 0.5 for dimer at large t_max."""
        p = time_averaged_ctqw(self.H_dimer, t_max=200.0, source=0, n_steps=2000)
        assert abs(p[0] - 0.5) < 0.02, f"P_avg(0) = {p[0]:.4f}, expected 0.5"
        assert abs(p[1] - 0.5) < 0.02, f"P_avg(1) = {p[1]:.4f}, expected 0.5"

    def test_dimer_long_time_source1(self):
        """P_avg(source=1) → 0.5 for dimer at large t_max (symmetry)."""
        p = time_averaged_ctqw(self.H_dimer, t_max=200.0, source=1, n_steps=2000)
        assert abs(p[0] - 0.5) < 0.02
        assert abs(p[1] - 0.5) < 0.02

    def test_normalization(self):
        """Time-averaged occupation must sum to 1 for any connected graph."""
        graphs = [
            nx.path_graph(6),
            nx.cycle_graph(8),
            nx.complete_graph(5),
            nx.barabasi_albert_graph(12, 2, seed=3),
        ]
        for G in graphs:
            A = nx.adjacency_matrix(G).toarray().astype(float)
            p = time_averaged_ctqw(A, t_max=50.0, source=0, n_steps=300)
            assert abs(p.sum() - 1.0) < 1e-10, (
                f"Sum = {p.sum():.6f} ≠ 1 on {G.__class__.__name__}(n={G.number_of_nodes()})"
            )

    def test_non_negative(self):
        """Time-averaged occupation entries must be ≥ 0."""
        A = nx.adjacency_matrix(nx.cycle_graph(10)).toarray().astype(float)
        p = time_averaged_ctqw(A, t_max=30.0, source=0, n_steps=300)
        assert (p >= -1e-12).all(), f"Negative entry: {p.min():.3e}"

    def test_initial_condition(self):
        """At t_max→0 (n_steps=1, t_grid=[0]), all weight is on the source."""
        p = time_averaged_ctqw(self.H_dimer, t_max=0.0, source=0, n_steps=1)
        np.testing.assert_allclose(p, [1.0, 0.0], atol=1e-10,
                                   err_msg="t_max=0 should concentrate on source")

    @pytest.mark.parametrize("n", [4, 6, 8])
    def test_cycle_symmetry(self, n):
        """On C_n with source=0, P_avg must be symmetric: P_avg(k) = P_avg(n-k)."""
        A = nx.adjacency_matrix(nx.cycle_graph(n)).toarray().astype(float)
        p = time_averaged_ctqw(A, t_max=100.0, source=0, n_steps=1000)
        for k in range(1, n // 2 + 1):
            assert abs(p[k] - p[n - k]) < 1e-8, (
                f"C_{n}: P_avg({k})={p[k]:.6f} ≠ P_avg({n-k})={p[n-k]:.6f}"
            )


# ---------------------------------------------------------------------------
# T-016 · ctqw and heat on a synthetic protein-like (helical) graph
# ---------------------------------------------------------------------------

def _helix_coords(n: int = 50) -> np.ndarray:
    """Alpha-helix Cα coordinates: r=2.3 Å, rise=1.5 Å/residue, 100°/residue.

    Adjacent-residue distance ≈ 3.83 Å; residues up to ±6 positions apart fall
    within the 10 Å GNM cutoff, giving a degree-~12 contact graph.
    """
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


@pytest.fixture(scope="module")
def helix_graph():
    """Return (coords, A, L, G) for a 50-residue helix at cutoff=10 Å."""
    coords = _helix_coords(50)
    A = contact_matrix(coords, cutoff=10.0, weight="binary")
    L = laplacian(A)
    G = nx.from_numpy_array(A)
    return coords, A, L, G


class TestHelixPropagators:
    """CTQW and heat kernel on a 50-residue synthetic alpha-helix.

    Tests verify spatial structure, not just summary statistics, making them
    immune to the normalization-masking issue noted in CRIT-002 GAP-5.
    """

    SOURCE = 25  # central residue — avoids boundary effects

    # --- initial condition -----------------------------------------------

    def test_ctqw_t0_delta(self, helix_graph):
        """CTQW at t=0 must be a delta function on the source."""
        _, A, _, _ = helix_graph
        p = ctqw(A, t=0.0, source=self.SOURCE)
        assert abs(p[self.SOURCE] - 1.0) < 1e-10, f"p[source] = {p[self.SOURCE]}"
        assert p[self.SOURCE - 1] < 1e-10
        assert p[self.SOURCE + 1] < 1e-10

    def test_heat_t0_delta(self, helix_graph):
        """Heat kernel at t=0 must be a delta function on the source."""
        _, _, L, _ = helix_graph
        p = heat(L, t=0.0, source=self.SOURCE)
        assert abs(p[self.SOURCE] - 1.0) < 1e-10, f"p[source] = {p[self.SOURCE]}"
        assert p[self.SOURCE - 1] < 1e-10
        assert p[self.SOURCE + 1] < 1e-10

    # --- short-time locality ---------------------------------------------

    def test_ctqw_short_time_locality(self, helix_graph):
        """CTQW at t=0.05: mean P at graph-distance 1 > mean P at distance 2.

        At short t, second-order perturbation gives P(dist-1) ~ t²|H|²
        and P(dist-2) ~ t⁴, so the ordering is guaranteed for small t.
        """
        _, A, _, G = helix_graph
        p = ctqw(A, t=0.05, source=self.SOURCE)
        lengths = nx.single_source_shortest_path_length(G, self.SOURCE)
        dist1 = [v for v, d in lengths.items() if d == 1]
        dist2 = [v for v, d in lengths.items() if d == 2]
        mean1 = p[dist1].mean()
        mean2 = p[dist2].mean()
        assert mean1 > mean2, (
            f"CTQW short-time locality violated: mean P(dist=1)={mean1:.2e} "
            f"≤ mean P(dist=2)={mean2:.2e}"
        )

    def test_heat_short_time_locality(self, helix_graph):
        """Heat kernel at t=0.1: mean P at graph-distance 1 > mean P at distance 2."""
        _, _, L, G = helix_graph
        p = heat(L, t=0.1, source=self.SOURCE)
        lengths = nx.single_source_shortest_path_length(G, self.SOURCE)
        dist1 = [v for v, d in lengths.items() if d == 1]
        dist2 = [v for v, d in lengths.items() if d == 2]
        mean1 = p[dist1].mean()
        mean2 = p[dist2].mean()
        assert mean1 > mean2, (
            f"Heat short-time locality violated: mean P(dist=1)={mean1:.2e} "
            f"≤ mean P(dist=2)={mean2:.2e}"
        )

    # --- large-t convergence (heat only) ---------------------------------

    def test_heat_large_t_uniform(self, helix_graph):
        """Heat kernel at t=1000 converges to uniform 1/N.

        All non-zero Laplacian eigenvalues satisfy exp(−λ × 1000) < 1e-4,
        leaving only the zero-mode projection = constant vector.
        """
        _, _, L, _ = helix_graph
        N = L.shape[0]
        p = heat(L, t=1000.0, source=self.SOURCE)
        np.testing.assert_allclose(p, np.full(N, 1.0 / N), atol=1e-3,
                                   err_msg="Heat kernel did not converge to 1/N")

    # --- source independence of large-t limit ----------------------------

    @pytest.mark.parametrize("source", [0, 10, 25, 40, 49])
    def test_heat_large_t_source_independent(self, helix_graph, source):
        """Heat convergence to 1/N holds regardless of starting residue."""
        _, _, L, _ = helix_graph
        N = L.shape[0]
        p = heat(L, t=1000.0, source=source)
        np.testing.assert_allclose(p, np.full(N, 1.0 / N), atol=1e-3,
                                   err_msg=f"Heat did not reach 1/N from source={source}")
