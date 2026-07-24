import numpy as np
import networkx as nx
from allostery import lowmode_predictor as LM
from allostery.hamiltonians import contact_matrix


def _hinge_system(cutoff=12.0):
    """Two dense domains joined by a thin hinge — a connected two-domain
    system whose lowest ANM mode is the hinge bend. Built on a jittered grid
    so the contact graph is reliably connected (real apo folds are; random
    sparse blobs need not be, which is what anm_modes' TASK-0005 guard trips)."""
    def domain(cx):
        g = np.array([(x, y, z)
                      for x in range(4) for y in range(4) for z in range(4)], float)
        g *= 4.5
        g[:, 0] += cx
        return g
    A = domain(-30.0); B = domain(12.0)
    hinge = np.array([[x, 7.5, 7.5] for x in np.arange(-8, 14, 3.5)], float)
    coords = np.vstack([A, hinge, B])
    coords += np.random.default_rng(1).normal(0, 0.3, coords.shape)
    seed = int(np.argmin(coords[:, 0]))  # far end of domain A
    A_adj = contact_matrix(coords, cutoff=cutoff, weight="binary")
    assert nx.is_connected(nx.from_numpy_array(A_adj)), "fixture must be connected"
    return coords, seed


def test_prs_low_is_proximity_orthogonal():
    from scipy.stats import spearmanr
    coords, seed = _hinge_system()
    A = contact_matrix(coords, cutoff=12.0, weight="binary")
    G = nx.from_numpy_array(A)
    hop = np.array([nx.shortest_path_length(G, seed).get(j, len(coords))
                    for j in range(len(coords))])
    ctqw_like = -hop  # the confounded observable is ~monotone in hop
    prs = LM.prs_low(coords, seed, cutoff=12.0, k_modes=20)
    rho_prs, _ = spearmanr(prs, -hop)
    rho_conf, _ = spearmanr(ctqw_like, -hop)
    # PRS-low must be markedly LESS distance-coupled than the proximity observable
    assert abs(rho_prs) < abs(rho_conf) - 0.3, (
        f"PRS-low rho={rho_prs} not sufficiently below confound rho={rho_conf}")


def test_prs_low_shapes_and_finite():
    coords, seed = _hinge_system()
    for k in (5, 20):
        sc = LM.prs_low(coords, seed, cutoff=12.0, k_modes=k)
        assert sc.shape == (len(coords),)
        assert np.all(np.isfinite(sc)) and np.all(sc >= 0)


def test_dcc_low_shapes_and_finite():
    coords, seed = _hinge_system()
    sc = LM.dcc_low(coords, seed, cutoff=12.0, k_modes=20)
    assert sc.shape == (len(coords),)
    assert np.all(np.isfinite(sc))
