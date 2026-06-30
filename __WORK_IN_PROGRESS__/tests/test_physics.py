"""Phase 0a – analytical physics unit tests.

These tests verify the correctness of the quantum operators and propagators
on small graphs where exact analytical results are known. They are purely
numerical (no PDB data required) and should run in < 5 s total.

Tests
-----
1. cycle_eigenvalues       – Adjacency eigenvalues of C_n = 2cos(2πk/n)
2. dimer_rabi              – Two-node CTQW gives Rabi cos²/sin² oscillations
3. ctqw_unitarity          – U†U = I on a random graph; row-probabilities sum to 1
4. laplacian_nullspace     – dim(null(L)) = number of connected components
5. bessel_line             – CTQW on finite path graph matches J_x(2t)² (Bessel)
6. haken_strobl_steady     – Strong dephasing → uniform diagonal ρ = I/N
7. haken_strobl_trace      – Trace(ρ(t)) = 1 is conserved throughout evolution
8. heat_kernel_conservation– Heat kernel columns are non-negative and sum ≤ 1
9. eff_rank_spectrum       – eff_rank of flat spectrum = N; spiked spectrum ≈ 1
10. normalised_laplacian   – Eigenvalues in [0, 2]; zero mode exists
"""
import numpy as np
import pytest
import networkx as nx
from scipy.special import jv as bessel_j

from allostery.propagators import ctqw, heat, haken_strobl
from allostery.hamiltonians import laplacian
from allostery.metrics import eff_rank


# ---------------------------------------------------------------------------
# 1. Cycle C_n adjacency eigenvalues
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", [4, 6, 8, 12, 20])
def test_cycle_eigenvalues(n):
    """Adjacency eigenvalues of C_n are 2*cos(2*pi*k/n) for k=0,...,n-1."""
    A = nx.adjacency_matrix(nx.cycle_graph(n)).toarray().astype(float)
    computed = np.sort(np.linalg.eigvalsh(A))
    expected = np.sort([2 * np.cos(2 * np.pi * k / n) for k in range(n)])
    np.testing.assert_allclose(computed, expected, atol=1e-10,
                               err_msg=f"Cycle C_{n} eigenvalues wrong")


# ---------------------------------------------------------------------------
# 2. Dimer Rabi oscillations
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("t", list(np.round(np.linspace(0, 2 * np.pi, 16), 4)))
def test_dimer_rabi(t):
    """Two-node CTQW: P(0,t)=cos²(t), P(1,t)=sin²(t)."""
    H = np.array([[0.0, 1.0], [1.0, 0.0]])
    p = ctqw(H, t, source=0)
    assert abs(p[0] - np.cos(t) ** 2) < 1e-10, f"P(0,t={t:.3f}) = {p[0]}, expected {np.cos(t)**2}"
    assert abs(p[1] - np.sin(t) ** 2) < 1e-10, f"P(1,t={t:.3f}) = {p[1]}, expected {np.sin(t)**2}"
    assert abs(p.sum() - 1.0) < 1e-12


# ---------------------------------------------------------------------------
# 3. CTQW unitarity
# ---------------------------------------------------------------------------

def test_ctqw_unitarity():
    """ctqw output matches |U[:,source]|² and sums to 1 on a random graph."""
    n = 15
    G = nx.erdos_renyi_graph(n, 0.4, seed=42)
    A = nx.adjacency_matrix(G).toarray().astype(float)
    t = 1.73

    # Reference unitary built from the same eigen-decomposition as ctqw()
    w, v = np.linalg.eigh(A)
    U = (v * np.exp(-1j * w * t)) @ v.T

    # U†U = I (sanity check on numpy's eigh)
    np.testing.assert_allclose(U.conj().T @ U, np.eye(n), atol=1e-10,
                               err_msg="U†U ≠ I")

    for source in range(n):
        p = ctqw(A, t, source=source)
        # ctqw must agree with |U[:,source]|²
        np.testing.assert_allclose(p, np.abs(U[:, source]) ** 2, atol=1e-10,
                                   err_msg=f"ctqw ≠ |U|² for source={source}")
        assert abs(p.sum() - 1.0) < 1e-10, f"prob sum ≠ 1 for source={source}"
        assert (p >= -1e-12).all(), f"Negative prob for source={source}"


# ---------------------------------------------------------------------------
# 4. Laplacian nullspace = connected components
# ---------------------------------------------------------------------------

def test_laplacian_nullspace_connected():
    """Single connected graph: null(L) has dimension 1."""
    G = nx.path_graph(10)
    A = nx.adjacency_matrix(G).toarray().astype(float)
    L = laplacian(A)
    w = np.linalg.eigvalsh(L)
    n_zero = int((w < 1e-8).sum())
    assert n_zero == 1, f"Expected 1 zero eigenvalue, got {n_zero}"


@pytest.mark.parametrize("sizes", [(3, 4), (5, 6, 7), (2, 2)])
def test_laplacian_nullspace_disconnected(sizes):
    """Disjoint union of k components: null(L) has dimension k."""
    G = nx.disjoint_union_all([nx.path_graph(s) for s in sizes])
    A = nx.adjacency_matrix(G).toarray().astype(float)
    L = laplacian(A)
    w = np.linalg.eigvalsh(L)
    n_zero = int((w < 1e-8).sum())
    k = len(sizes)
    assert n_zero == k, f"Expected {k} zero eigenvalues for {k} components, got {n_zero}"


# ---------------------------------------------------------------------------
# 5. Bessel function on finite path graph
# ---------------------------------------------------------------------------

def test_bessel_line():
    """CTQW on a long path: P(x, t|center) ≈ J_x(2t)² for small |x|, t."""
    N = 80
    center = N // 2
    t = 2.0

    G = nx.path_graph(N)
    A = nx.adjacency_matrix(G).toarray().astype(float)
    p = ctqw(A, t, source=center)

    # Check first 6 offsets from the centre.
    # Finite-chain boundary effects are ~exp(-N²/8t) ≈ 1e-11 at these params;
    # dominant error is floating-point; empirical tolerance is 1e-2.
    for x in range(6):
        expected = bessel_j(x, 2 * t) ** 2
        actual = p[center + x]
        assert abs(actual - expected) < 1e-2, (
            f"Bessel mismatch at offset x={x}: got {actual:.6f}, "
            f"expected J_{x}(2t={2*t:.1f})²={expected:.6f}"
        )


# ---------------------------------------------------------------------------
# 6. Haken–Strobl steady state (strong dephasing → uniform diagonal)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("gamma,t_run,label", [
    # Low dephasing: γ=0.5 < ||H||~2; D_eff~2, τ_eq~N²/D_eff~6; t=60>>τ_eq
    (0.5,  60.0,  "low"),
    # Mid dephasing: γ=2.0 ~ ||H||; D_eff~2, τ_eq~12.5; t=120>>τ_eq
    (2.0, 120.0, "mid"),
    # High dephasing (Zeno): γ=20>>||H||; D_eff=||H||²/2γ~0.1, τ_eq~125; t=1000>>τ_eq
    (20.0, 1000.0, "high"),
])
def test_haken_strobl_steady_state(gamma, t_run, label):
    """At long times with any γ > 0, diagonal of ρ approaches 1/N.

    Tests three regimes: low (γ < ||H||), mid (γ ~ ||H||), high/Zeno (γ >> ||H||).
    Each t_run is chosen to be > 8 equilibration times so atol=1e-3 is tight.
    """
    N = 5
    A = nx.adjacency_matrix(nx.path_graph(N)).toarray().astype(float)
    p = haken_strobl(A, t=t_run, gamma=gamma, source=0)
    expected = 1.0 / N
    np.testing.assert_allclose(
        p, expected, atol=1e-3,
        err_msg=f"Haken-Strobl steady state not uniform for γ={gamma} ({label})",
    )


# ---------------------------------------------------------------------------
# 7. Haken–Strobl trace conservation
# ---------------------------------------------------------------------------

def test_haken_strobl_trace():
    """Trace(ρ) = 1 and ρ_diag ≥ 0 at multiple time points and γ values."""
    N = 4
    A = nx.adjacency_matrix(nx.path_graph(N)).toarray().astype(float)

    for gamma in [0.0, 1.0, 10.0]:
        for t in [0.5, 2.0, 10.0]:
            p = haken_strobl(A, t=t, gamma=gamma, source=1)
            assert abs(p.sum() - 1.0) < 1e-6, (
                f"Trace not conserved for gamma={gamma}, t={t}: sum={p.sum()}"
            )
            assert (p >= -1e-8).all(), (
                f"Negative diagonal element for gamma={gamma}, t={t}"
            )


# ---------------------------------------------------------------------------
# 8. Heat kernel – non-negativity and sum ≤ 1
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("t", [0.1, 1.0, 5.0, 20.0])
def test_heat_kernel_conservation(t):
    """Heat kernel: p ≥ 0 and sum ≈ 1 (Laplacian convention)."""
    N = 12
    G = nx.barabasi_albert_graph(N, 2, seed=7)
    A = nx.adjacency_matrix(G).toarray().astype(float)
    L = laplacian(A)

    for source in range(N):
        p = heat(L, t, source=source)
        assert (p >= -1e-10).all(), f"Negative heat kernel entry at t={t}, source={source}"
        assert abs(p.sum() - 1.0) < 1e-8, f"Heat sum ≠ 1 at t={t}, source={source}"


# ---------------------------------------------------------------------------
# 9. Effective rank
# ---------------------------------------------------------------------------

def test_eff_rank_flat_spectrum():
    """Flat spectrum (all eigenvalues equal) → eff_rank = N."""
    N = 20
    ev = np.ones(N)
    assert abs(eff_rank(ev) - N) < 1e-6, "Flat spectrum should give eff_rank = N"


def test_eff_rank_spiked_spectrum():
    """Spiked spectrum (one dominant eigenvalue) → eff_rank ≈ 1."""
    ev = np.zeros(10)
    ev[0] = 1000.0
    er = eff_rank(ev)
    assert er < 1.1, f"Spiked spectrum should give eff_rank ≈ 1, got {er:.3f}"


@pytest.mark.xfail(
    strict=False,
    reason="Oracle value (≈117.7) not yet confirmed from notebook; "
           "tighten to abs(er - ORACLE) < 5 once confirmed.",
)
def test_eff_rank_kras_regression():
    """Regression oracle: H_new(KRAS_apo 4OBE) eff_rank ≈ 117.7.

    Uses real Cα coordinates and real B-factors from the PDB so the result
    matches the notebook calculation. Marked xfail until the notebook oracle
    is read off and the tolerance tightened.
    Skipped automatically when the PDB is unreachable (offline CI).
    """
    pytest.importorskip("prody")
    import prody

    prody.confProDy(verbosity="none")
    try:
        raw = prody.parsePDB("4OBE", compressed=False)
    except Exception as e:
        pytest.skip(f"Could not fetch 4OBE from PDB: {e}")

    if not isinstance(raw, prody.AtomGroup):
        pytest.skip(f"parsePDB returned unexpected type {type(raw)} for 4OBE")

    ca = raw.select("protein and name CA and chain A")
    if ca is None:
        pytest.skip("No Cα atoms found in 4OBE chain A")

    coords = ca.getCoords().astype(float)
    bfactors = ca.getBetas().astype(float)

    from allostery.hamiltonians import build_H_new
    H = build_H_new(coords, bfactors)
    w = np.linalg.eigvalsh(H)
    er = eff_rank(w)

    # TODO: replace 117.7 with confirmed value and narrow atol to 5
    assert abs(er - 117.7) < 30, (
        f"H_new(KRAS_apo 4OBE) eff_rank={er:.1f}; expected ≈117.7 ± 30"
    )


# ---------------------------------------------------------------------------
# 10. Normalised Laplacian eigenvalue bounds
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("graph,label", [
    (nx.path_graph(15),              "path"),       # sparse, linear topology
    (nx.cycle_graph(12),             "cycle"),      # regular degree-2
    (nx.barabasi_albert_graph(20, 2, seed=7), "scale_free"),  # heterogeneous degree
    (nx.complete_graph(8),           "complete"),   # dense; max eigenvalue hits 2
])
def test_normalised_laplacian_bounds(graph, label):
    """Normalised Laplacian eigenvalues lie in [0, 2]; zero mode exists.

    Uses deterministic connected graphs (no random fallback) covering sparse,
    regular, scale-free, and dense topologies.
    """
    A = nx.adjacency_matrix(graph).toarray().astype(float)
    L_norm = laplacian(A, normalised=True)
    w = np.linalg.eigvalsh(L_norm)
    assert w.min() >= -1e-10, f"[{label}] Negative eigenvalue {w.min():.2e}"
    assert w.max() <= 2.0 + 1e-10, f"[{label}] Eigenvalue {w.max():.4f} > 2"
    assert w[0] < 1e-8, f"[{label}] Zero mode missing from normalised Laplacian"
