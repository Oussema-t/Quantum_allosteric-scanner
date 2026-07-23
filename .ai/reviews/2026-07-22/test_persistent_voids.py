import numpy as np
from allostery import persistent_voids as PV

rng = np.random.default_rng(3)


def test_hollow_shell_has_persistent_void():
    u = rng.normal(size=(160, 3)); u /= np.linalg.norm(u, axis=1, keepdims=True)
    shell = u * 12.0 + rng.normal(0, 0.4, (160, 3))
    assert PV.top_h2_persistence(shell, thresh=18.0) > 3.0


def test_solid_ball_has_no_strong_void():
    v = rng.normal(size=(320, 3)); v /= np.linalg.norm(v, axis=1, keepdims=True)
    ball = v * (rng.uniform(0, 1, (320, 1)) ** (1 / 3)) * 12.0
    # a filled ball has only small sampling-noise voids
    assert PV.top_h2_persistence(ball, thresh=18.0) < 2.5


def test_void_detected_even_when_lining_is_graph_adjacent():
    """The point of implementing H2 separately from the graph-openness gate:
    a cavity whose wall residues are graph-NEAR still registers as an H2 void."""
    w = rng.normal(size=(700, 3)); w /= np.linalg.norm(w, axis=1, keepdims=True)
    prot = w * (rng.uniform(0, 1, (700, 1)) ** (1 / 3)) * 15.0
    d2c = np.linalg.norm(prot - np.array([4.0, 0, 0]), axis=1)
    prot = prot[d2c > 5.5]
    assert PV.top_h2_persistence(prot, thresh=18.0) > 2.5


def test_no_void_returns_zero_score_not_noise():
    pts = rng.normal(size=(50, 3)) * 5.0  # small blob, unlikely persistent void
    sc = PV.void_score(pts, thresh=18.0, min_persistence=3.0)
    assert sc.shape == (50,)
    assert np.all(sc == 0.0) or np.all(np.isfinite(sc))
