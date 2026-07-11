"""SEAM-0006 seam-test (`.ai/seams/SEAM-0006-pathways-viz-consumption.md`).

Invariant: `viz.py`'s rendering of the current-flow field/path assumes the
exact shapes `pathways.py` actually returns -- `edge_propensity` ->
`{(i, j): float}` for `i < j` only (undirected, half the (N, N) matrix,
non-negative), and `extract_pathway` -> `{"nodes": [...], "edges": [(i, j),
...], "reached_target": bool, "propensity": {(i, j): float}}`.

Cross-boundary test between `pathways.py` (producer) and `viz.py`
(consumer) -- neither module's own unit tests can catch a shape mismatch
between them: `test_pathways.py` never imports `viz.py`, and
`test_viz.py`'s smoke tests use hand-built dicts that already match what
the developer *assumed* `pathways.py` returns, not what it actually
returns. This test feeds `pathways.py`'s real, live output directly into
`viz.plot_pathway_overlay` -- exactly the "distinct from either unit's own
tests" bar `SEAM_PROTOCOL.md` sets for a seam-test.

Unlike SEAM-0005's seam-test (xfail -- its consumer side didn't exist yet),
this one is a real, passing assertion: TASK-0014 is the seam's own
registered owner and this task builds the consumer, so the seam closes
(OPEN -> VERIFIED) in the same commit as this test, per SEAM_PROTOCOL.md's
gate ("registering means a SEAM record exists with a named owner and a
named seam-test -- the test may be xfail at open, but must exist"; nothing
requires staying xfail once the consumer is real).
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.pathways import edge_propensity, extract_pathway  # noqa: E402
from allostery.viz import plot_pathway_overlay  # noqa: E402


def _two_cluster_laplacian() -> np.ndarray:
    """Same fixture as test_pathways.py::_two_cluster_laplacian -- two
    4-node cliques joined by a single bridge edge (3, 4)."""
    N = 8
    W = np.zeros((N, N))
    for cluster in ([0, 1, 2, 3], [4, 5, 6, 7]):
        for i in cluster:
            for j in cluster:
                if i < j:
                    W[i, j] = W[j, i] = 1.0
    W[3, 4] = W[4, 3] = 1.0
    D = np.diag(W.sum(axis=1))
    return D - W


class TestSeam0006PathwaysVizConsumption:
    def test_real_edge_propensity_output_renders_without_shape_mismatch(self):
        L = _two_cluster_laplacian()
        prop = edge_propensity(L, source=0)

        ax = plot_pathway_overlay(8, prop)
        assert ax is not None
        plt.close(ax.figure)

    def test_real_extract_pathway_output_renders_without_shape_mismatch(self):
        L = _two_cluster_laplacian()
        result = extract_pathway(L, source=0, target=7)

        ax = plot_pathway_overlay(8, result["propensity"], pathway=result)
        assert ax is not None
        assert result["reached_target"] is True  # sanity: this fixture's bridge is traversable
        plt.close(ax.figure)

    def test_real_output_from_unreachable_target_also_renders(self):
        """extract_pathway's contract holds (all 4 keys present, propensity
        well-shaped) even when reached_target is False -- viz.py must not
        assume a successful walk to render safely."""
        N = 4
        W = np.zeros((N, N))
        W[0, 1] = W[1, 0] = 1.0
        W[1, 2] = W[2, 1] = 1.0
        L = np.diag(W.sum(axis=1)) - W
        result = extract_pathway(L, source=0, target=3)

        assert result["reached_target"] is False
        ax = plot_pathway_overlay(N, result["propensity"], pathway=result)
        assert ax is not None
        plt.close(ax.figure)
