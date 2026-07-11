"""TASK-0014 coverage -- viz.py plotting helpers (presentation only).

Smoke tests only, per this task's own Planned Validation: functions run
without error on synthetic data and return a figure/axes object -- no
pixel-level or numerical assertions on a presentation-only module. The
`_validate_edge_propensity`/`_validate_pathway` error-path tests are the
exception (real assertions), since those functions ARE the executable form
of SEAM-0006's invariant, not presentation.

matplotlib uses the non-interactive "Agg" backend (set once, module level)
so this suite runs headlessly.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.viz import (  # noqa: E402
    plot_ablation_bar,
    plot_ablation_heatmap,
    plot_apo_holo_consistency,
    plot_group_comparison,
    plot_occupation_profile,
    plot_pathway_overlay,
    summary_figure,
)


def _metric_pack(auc: float) -> dict:
    """Same shape as analysis.py's private _metric_pack (AUC + occ)."""
    return {"AUC": auc, "P@5": 0.4, "E@5": 1.2, "occ": np.random.default_rng(0).random(10)}


N = 10
RESNUMS = np.arange(1, N + 1)
OCC = np.abs(np.random.default_rng(1).random(N))


class TestPlotOccupationProfile:
    def test_minimal_call_returns_axes(self):
        ax = plot_occupation_profile(RESNUMS, OCC)
        assert ax is not None
        plt.close(ax.figure)

    def test_with_pocket_and_source_and_baseline(self):
        pocket_mask = np.zeros(N, dtype=bool)
        pocket_mask[[2, 3]] = True
        ax = plot_occupation_profile(
            RESNUMS, OCC,
            pocket_mask=pocket_mask,
            source_idx=[0, 1],
            baseline_occ=OCC * 0.5,
            title="test",
        )
        assert ax.get_title() == "test"
        plt.close(ax.figure)


class TestPlotAblation:
    def _result(self):
        return {
            "L_only": _metric_pack(0.55),
            "B": _metric_pack(0.60),
            "T": _metric_pack(0.52),
            "R": _metric_pack(0.70),
            "C": _metric_pack(0.65),
            "M": _metric_pack(0.58),
        }

    def test_bar_runs(self):
        ax = plot_ablation_bar(self._result())
        assert ax is not None
        plt.close(ax.figure)

    def test_heatmap_runs_multi_system(self):
        results = {"SYS_A": self._result(), "SYS_B": self._result()}
        ax = plot_ablation_heatmap(results)
        assert ax is not None
        plt.close(ax.figure)


class TestPlotGroupComparison:
    def test_quantum_vs_classical_shape_runs(self):
        results = {"ctqw": _metric_pack(0.62), "heat": _metric_pack(0.58)}
        ax = plot_group_comparison(results)
        assert ax is not None
        plt.close(ax.figure)


class TestPlotApoHoloConsistency:
    def test_runs(self):
        results = {
            "SYS_A": {"spearman_rho": 0.4, "top_k_jaccard": 0.3, "top_k_overlap": 3, "k": 5},
            "SYS_B": {"spearman_rho": 0.1, "top_k_jaccard": 0.1, "top_k_overlap": 1, "k": 5},
        }
        ax = plot_apo_holo_consistency(results)
        assert ax is not None
        plt.close(ax.figure)


class TestPlotPathwayOverlay:
    def _edge_propensity(self):
        return {(0, 1): 0.5, (1, 2): 1.0, (2, 3): 0.2}

    def test_runs_without_pathway_or_coords(self):
        ax = plot_pathway_overlay(4, self._edge_propensity())
        assert ax is not None
        plt.close(ax.figure)

    def test_runs_with_pathway_and_coords(self):
        pathway = {
            "nodes": [0, 1, 2],
            "edges": [(0, 1), (1, 2)],
            "reached_target": True,
            "propensity": self._edge_propensity(),
        }
        coords = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [3.0, 0.0]])
        ax = plot_pathway_overlay(4, self._edge_propensity(), pathway=pathway, coords=coords)
        assert ax is not None
        plt.close(ax.figure)

    def test_runs_with_unreached_pathway(self):
        pathway = {
            "nodes": [0, 1],
            "edges": [(0, 1)],
            "reached_target": False,
            "propensity": self._edge_propensity(),
        }
        ax = plot_pathway_overlay(4, self._edge_propensity(), pathway=pathway)
        assert ax is not None
        plt.close(ax.figure)

    def test_empty_edge_propensity_does_not_crash(self):
        ax = plot_pathway_overlay(3, {})
        assert ax is not None
        plt.close(ax.figure)

    # -- validator error paths: these ARE real assertions, not smoke tests,
    # since they encode SEAM-0006's invariant directly.

    def test_rejects_directed_key_i_ge_j(self):
        with pytest.raises(ValueError):
            plot_pathway_overlay(4, {(1, 0): 0.5})

    def test_rejects_negative_value(self):
        with pytest.raises(ValueError):
            plot_pathway_overlay(4, {(0, 1): -0.1})

    def test_rejects_out_of_range_index(self):
        with pytest.raises(ValueError):
            plot_pathway_overlay(2, {(0, 5): 0.5})

    def test_rejects_non_tuple_key(self):
        with pytest.raises(TypeError):
            plot_pathway_overlay(4, {"01": 0.5})

    def test_rejects_pathway_missing_keys(self):
        with pytest.raises(KeyError):
            plot_pathway_overlay(4, self._edge_propensity(), pathway={"nodes": [0, 1]})


class TestSummaryFigure:
    def test_runs_without_consistency(self):
        ablation_result = {
            "L_only": _metric_pack(0.5),
            "B": _metric_pack(0.6),
        }
        propagator_result = {"ctqw": _metric_pack(0.6), "heat": _metric_pack(0.55)}
        occupation = {"resnums": RESNUMS, "occ": OCC}
        fig = summary_figure(ablation_result, propagator_result, occupation)
        assert fig is not None
        plt.close(fig)

    def test_runs_with_consistency(self):
        ablation_result = {"L_only": _metric_pack(0.5), "B": _metric_pack(0.6)}
        propagator_result = {"ctqw": _metric_pack(0.6), "heat": _metric_pack(0.55)}
        occupation = {"resnums": RESNUMS, "occ": OCC, "pocket_mask": np.zeros(N, dtype=bool)}
        consistency = {"SYS_A": {"spearman_rho": 0.3, "top_k_jaccard": 0.2}}
        fig = summary_figure(
            ablation_result, propagator_result, occupation,
            consistency_results=consistency, suptitle="test",
        )
        assert fig is not None
        plt.close(fig)
