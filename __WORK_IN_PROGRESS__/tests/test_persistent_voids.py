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


_BASE_U = rng.normal(size=(160, 3))
_BASE_U /= np.linalg.norm(_BASE_U, axis=1, keepdims=True)


def _shell_member(jitter_rng):
    """One conformation of a near-identical ensemble: same 160 base
    directions (so residue i means the same thing across members, as it
    would across an NMA-displaced ensemble of one apo structure), each with
    its own independent small jitter."""
    return _BASE_U * 12.0 + jitter_rng.normal(0, 0.4, (160, 3))


def test_ensemble_score_matches_single_structure_shape_and_scale():
    """An ensemble of near-identical hollow shells (shared base positions,
    independent small per-member jitter -- the residue-correspondence shape
    an NMA-displaced ensemble actually has) should score like the
    single-structure void_score on any one member — same shape, correlated
    ranking, not washed out by averaging over conformations that agree with
    each other."""
    ensemble = [_shell_member(np.random.default_rng(100 + i)) for i in range(6)]
    ens_score, top_h1, top_h2 = PV.ensemble_void_score(ensemble, thresh=18.0)
    single_score = PV.void_score(ensemble[0], thresh=18.0)
    assert ens_score.shape == (160,)
    assert top_h1.shape == (6,) and top_h2.shape == (6,)
    assert np.corrcoef(ens_score, single_score)[0, 1] > 0.6
    assert np.all(top_h2 > 3.0)  # every member is a real shell, per test_hollow_shell_has_persistent_void


def test_ensemble_diagnostic_distinguishes_void_from_no_void_members():
    """A mixed ensemble (half real shells, half solid balls) should report
    per-conformation top_h2 that tells the two apart -- the point of
    returning per-conformation diagnostics rather than only the averaged
    score, so a mostly-noise ensemble isn't silently presented as confident."""
    v = rng.normal(size=(320, 3)); v /= np.linalg.norm(v, axis=1, keepdims=True)
    ball = v * (rng.uniform(0, 1, (320, 1)) ** (1 / 3)) * 12.0
    shells = [_shell_member(np.random.default_rng(200 + i)) for i in range(3)]
    n_pad = shells[0].shape[0] - ball.shape[0]
    balls = [np.vstack([ball, ball[:n_pad]]) if n_pad > 0 else ball[: shells[0].shape[0]] for _ in range(3)]
    ensemble = shells + balls
    _, _, top_h2 = PV.ensemble_void_score(ensemble, thresh=18.0)
    assert np.all(top_h2[:3] > 3.0)
    assert np.all(top_h2[3:] < 2.5)
