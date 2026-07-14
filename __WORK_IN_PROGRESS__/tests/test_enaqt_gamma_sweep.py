"""TASK-0105 coverage -- enaqt_gamma_sweep.py's pure sweep/transport logic,
against synthetic networks (no network fetch). The real-target sweep
itself is this task's own Planned Validation (run directly, findings
written up separately), not re-asserted here as a golden value -- these
tests cover the *mechanism* (does sweep_gamma correctly find an interior
optimum when the review's own construction says one exists), matching
REVIEW-2026-07-13b Sec.4's own disordered-bridge setup.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
for _p in (_SRC, _SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from allostery.hamiltonians import laplacian  # noqa: E402
from allostery.propagators import ctqw  # noqa: E402

import enaqt_gamma_sweep as sweep_mod  # noqa: E402


def _disordered_bridge_laplacian(n_lobe: int = 10, n_bridge: int = 6, disorder: float = 3.0, seed: int = 0):
    """Two lobes connected by a bridge with per-edge energy disorder on the
    bridge -- REVIEW-2026-07-13b Sec.4's own construction (a coherent walk
    Anderson-localizes on the disordered bridge; dephasing should reopen
    it, producing an interior-gamma optimum). Returns (H, source_idx,
    pocket_mask) with source = lobe A, pocket = lobe B.
    """
    rng = np.random.default_rng(seed)
    n = 2 * n_lobe + n_bridge
    A = np.zeros((n, n))

    def _connect_clique(offset, size):
        for i in range(size):
            for j in range(i + 1, size):
                A[offset + i, offset + j] = A[offset + j, offset + i] = 1.0

    _connect_clique(0, n_lobe)
    _connect_clique(n_lobe + n_bridge, n_lobe)

    bridge_start = n_lobe
    chain = [n_lobe - 1] + list(range(bridge_start, bridge_start + n_bridge)) + [n_lobe + n_bridge]
    for a, b in zip(chain[:-1], chain[1:]):
        w = 1.0
        A[a, b] = A[b, a] = w

    W = A.copy()
    H = laplacian(W, normalised=False)
    # per-node energy disorder on the bridge only (diagonal potential)
    for node in range(bridge_start, bridge_start + n_bridge):
        H[node, node] += disorder * rng.normal()

    source_idx = np.arange(0, n_lobe)
    pocket_mask = np.zeros(n, dtype=bool)
    pocket_mask[n_lobe + n_bridge:] = True
    return H, source_idx, pocket_mask


class TestTransportToPocket:
    def test_all_mass_on_pocket_gives_one(self):
        occ = np.array([0.0, 0.0, 1.0, 0.0])
        pocket = np.array([False, False, True, False])
        assert sweep_mod.transport_to_pocket(occ, pocket) == pytest.approx(1.0)

    def test_no_mass_on_pocket_gives_zero(self):
        occ = np.array([0.5, 0.5, 0.0, 0.0])
        pocket = np.array([False, False, True, True])
        assert sweep_mod.transport_to_pocket(occ, pocket) == pytest.approx(0.0)

    def test_sums_multiple_pocket_residues(self):
        occ = np.array([0.1, 0.2, 0.3, 0.4])
        pocket = np.array([False, True, True, False])
        assert sweep_mod.transport_to_pocket(occ, pocket) == pytest.approx(0.5)


class TestSweepGamma:
    def test_gamma0_matches_direct_ctqw(self):
        """The gamma=0 anchor is computed via ctqw directly (cheap, exact),
        not the ODE solver at gamma=0 -- must match a direct ctqw call."""
        H, source, pocket = _disordered_bridge_laplacian()
        result = sweep_mod.sweep_gamma(H, source, pocket, gammas=np.array([1.0]), t=10.0)
        expected = sweep_mod.transport_to_pocket(ctqw(H, 10.0, source=source), pocket)
        assert result["gamma0_transport"] == pytest.approx(expected)

    def test_empty_gamma_grid_returns_gamma0_only(self):
        H, source, pocket = _disordered_bridge_laplacian()
        result = sweep_mod.sweep_gamma(H, source, pocket, gammas=np.array([]), t=10.0)
        assert result["gammas"] == []
        assert result["gamma_star"] is None
        assert result["interior_optimum"] is None
        assert result["gamma0_transport"] >= 0.0

    def test_finds_an_interior_optimum_on_a_disordered_bridge(self):
        """REVIEW-2026-07-13b Sec.4's own falsifiable signature: a coherent
        walk Anderson-localizes on bridge disorder; dephasing at some
        intermediate gamma should transport more probability to the distal
        lobe than either the coherent (gamma->0) or fully-dephased
        (gamma->inf) limit."""
        H, source, pocket = _disordered_bridge_laplacian(disorder=4.0, seed=3)
        gammas = np.array([0.05, 0.2, 0.5, 1.0, 3.0, 10.0])
        result = sweep_mod.sweep_gamma(H, source, pocket, gammas=gammas, t=30.0)

        assert result["gamma_star"] is not None
        assert result["transport_star"] >= result["gamma0_transport"]
        assert result["transport_star"] >= result["gamma_inf_transport"]
        assert result["enhancement_ratio"] >= 1.0

    def test_transport_curve_values_are_probabilities(self):
        H, source, pocket = _disordered_bridge_laplacian()
        gammas = np.array([0.1, 1.0, 5.0])
        result = sweep_mod.sweep_gamma(H, source, pocket, gammas=gammas, t=15.0)
        for v in result["transport"]:
            assert 0.0 <= v <= 1.0 + 1e-9


class TestBuildOperator:
    def test_unknown_operator_raises(self):
        with pytest.raises(ValueError):
            sweep_mod._build_operator("H99", None, 10.0)
