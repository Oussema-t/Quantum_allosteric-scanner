"""Group B coverage tests — hamiltonians, potentials, and propagator utilities.

Each section corresponds to a TASKS.md Group B item.  Only completed items are
implemented here; future tasks will be added in-place.

Sections implemented
--------------------
T-014  time_averaged_ctqw() – dimer long-time limit → 0.5
T-015  ipr, spectral_gap, check_degree_correlation – analytical values
T-016  ctqw + heat on synthetic helical backbone
"""
import numpy as np
import pytest
import networkx as nx

from allostery.propagators import ctqw, heat, time_averaged_ctqw
from allostery.hamiltonians import contact_matrix, laplacian
from allostery.metrics import ipr, spectral_gap, check_degree_correlation


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
