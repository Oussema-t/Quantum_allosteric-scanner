"""Visualisation helpers (presentation only -- not scored, TASK-0014).

Callable-function port of notebook `H_new_engineering (4) CLEAN.ipynb`
Sec.13 ("Visualisations") -- a single multi-panel figure over ablation,
propagator comparison, apo/holo consistency, and CTQW occupation profile.
Ported as parameterized functions taking plain arrays/dicts (the actual
shapes `analysis.py`'s functions return, TASK-0008), not notebook-global
DataFrames -- each panel is reusable on its own, `summary_figure` composes
them.

Also implements `plot_pathway_overlay`, which has no notebook Sec.13
precedent: `pathways.py` (TASK-0012) was built after Sec.13 was written,
and its own docstring names this module as the intended consumer of
`edge_propensity`/`extract_pathway`'s output. That consumption is a
registered seam (`.ai/seams/SEAM-0006-pathways-viz-consumption.md`) --
`_validate_edge_propensity`/`_validate_pathway` below assert against
`pathways.py`'s actual documented return shapes (checked by reading its
source directly, not re-derived) before this module ever plots them, per
the seam record's own instruction.

Every function here accepts an optional `ax` (a matplotlib Axes) and draws
onto it, creating a new figure/axes only if none is given -- so callers can
compose these into a larger figure (see `summary_figure`) or use them
standalone. `matplotlib` is a new dependency for this scaffold's venv (see
TASK-0014's Done section) -- imported lazily inside each function, mirroring
this codebase's existing convention for optional/heavy dependencies
(`prody` in `labels.py`/`clean.py`).
"""
from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Panel E -- CTQW occupation profile (notebook Sec.13 panel E)
# ---------------------------------------------------------------------------

def plot_occupation_profile(
    resnums: np.ndarray,
    occ: np.ndarray,
    pocket_mask: np.ndarray | None = None,
    source_idx=None,
    baseline_occ: np.ndarray | None = None,
    baseline_label: str = "baseline",
    title: str | None = None,
    ax=None,
):
    """Time-averaged occupation vs. residue number, with the pocket and
    seed(s) marked -- the primary "does the signal land on the pocket"
    read-out. `source_idx` may be a scalar or a sequence (mirrors
    `propagators.py`'s multi-index source convention).
    """
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 3.5))

    resnums = np.asarray(resnums)
    ax.plot(resnums, occ, label="occupation", lw=1.4, color="C0")
    if baseline_occ is not None:
        ax.plot(resnums, baseline_occ, label=baseline_label, lw=1.0, ls="--", color="grey")
    if pocket_mask is not None:
        pocket_mask = np.asarray(pocket_mask, dtype=bool)
        ax.scatter(resnums[pocket_mask], occ[pocket_mask], color="red", s=22, zorder=5, label="pocket")
    if source_idx is not None:
        src = np.atleast_1d(np.asarray(source_idx, dtype=int))
        ax.scatter(resnums[src], occ[src], color="black", s=18, zorder=6, marker="x", label="source")

    ax.set_xlabel("residue number")
    ax.set_ylabel("time-averaged occupation")
    if title:
        ax.set_title(title)
    ax.legend(fontsize=8, ncol=4)
    ax.grid(alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Panel C -- per-term ablation (notebook Sec.13 panel A/C)
# ---------------------------------------------------------------------------

def plot_ablation_bar(
    ablation_result: dict,
    metric: str = "AUC",
    title: str | None = None,
    ax=None,
):
    """Bar chart of `metric` per term, from `analysis.ablation`'s real
    return shape: `{"L_only": metric_pack, "B": ..., "T": ..., "R": ...,
    "C": ..., "M": ...}`, each `metric_pack` a dict with an `"AUC"` (and
    `"P@k"`/`"E@k"`) key.
    """
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(6, 3.5))

    terms = list(ablation_result.keys())
    values = [ablation_result[t][metric] for t in terms]

    ax.bar(terms, values, edgecolor="black")
    ax.axhline(0.5, color="k", lw=0.5, ls=":")
    ax.set_ylabel(metric)
    ax.set_title(title or f"Ablation: {metric} per term")
    return ax


def plot_ablation_heatmap(
    results_by_system: dict[str, dict],
    metric: str = "AUC",
    title: str | None = None,
    ax=None,
):
    """Multi-target ablation heatmap: rows are systems, columns are terms.

    `results_by_system` is `{system_name: ablation_result}`, i.e. a plain
    dict of real `analysis.ablation()` outputs the caller assembled by
    calling it once per target -- not a notebook-global DataFrame.
    """
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(7, 0.6 * max(len(results_by_system), 2) + 1))

    systems = list(results_by_system.keys())
    terms = list(next(iter(results_by_system.values())).keys()) if results_by_system else []
    grid = np.array([[results_by_system[s][t][metric] for t in terms] for s in systems])

    im = ax.imshow(grid, aspect="auto", cmap="RdBu_r")
    ax.set_xticks(range(len(terms)))
    ax.set_xticklabels(terms, rotation=30)
    ax.set_yticks(range(len(systems)))
    ax.set_yticklabels(systems)
    for (i, j), v in np.ndenumerate(grid):
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8)
    ax.set_title(title or f"Ablation: {metric} per term")
    plt.colorbar(im, ax=ax, fraction=0.04)
    return ax


# ---------------------------------------------------------------------------
# Panel B -- named-group comparison (propagators, targets, ...)
# ---------------------------------------------------------------------------

def plot_group_comparison(
    results: dict[str, dict],
    metric: str = "AUC",
    title: str | None = None,
    ax=None,
):
    """Bar chart of `metric` across named groups.

    Deliberately generic (not propagator-specific): works directly on
    `analysis.quantum_vs_classical`'s real return shape (`{"ctqw":
    metric_pack, "heat": metric_pack}`) for a propagator comparison, or on
    any other `{name: metric_pack}` mapping a caller assembles (e.g. one
    entry per target for a cross-target comparison) -- notebook Sec.13's
    panel B was specifically a propagator-vs-target grid built from a
    DataFrame; this keeps the same visual but takes real per-call
    `analysis.py` output instead.
    """
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(5, 3.5))

    names = list(results.keys())
    values = [results[n][metric] for n in names]

    ax.bar(names, values, edgecolor="black")
    ax.axhline(0.5, color="k", lw=0.5, ls=":")
    ax.set_ylabel(metric)
    ax.set_title(title or metric)
    return ax


# ---------------------------------------------------------------------------
# Panel D -- apo<->holo consistency
# ---------------------------------------------------------------------------

def plot_apo_holo_consistency(
    results_by_system: dict[str, dict],
    title: str | None = None,
    ax=None,
):
    """Bar chart of apo<->holo consistency, from `analysis.
    apo_holo_consistency`'s real return shape (`"spearman_rho"`,
    `"top_k_jaccard"`, per call) assembled by the caller as
    `{system_name: apo_holo_consistency_result}`.
    """
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(6, 3.5))

    systems = list(results_by_system.keys())
    xs = np.arange(len(systems))
    jaccard = [results_by_system[s]["top_k_jaccard"] for s in systems]
    rho = [results_by_system[s]["spearman_rho"] for s in systems]

    ax.bar(xs - 0.15, jaccard, 0.3, label="top-k Jaccard")
    ax.bar(xs + 0.15, rho, 0.3, label="Spearman rho")
    ax.set_xticks(xs)
    ax.set_xticklabels(systems, rotation=30, fontsize=8)
    ax.axhline(0.0, color="k", lw=0.5)
    ax.legend(fontsize=8)
    ax.set_title(title or "Apo<->holo consistency")
    return ax


# ---------------------------------------------------------------------------
# Pathway overlay -- SEAM-0006 (pathways.py -> viz.py consumption)
# ---------------------------------------------------------------------------

def _validate_edge_propensity(edge_propensity: dict, n_nodes: int) -> None:
    """Assert `edge_propensity` matches `pathways.edge_propensity`'s actual
    documented return contract: `{(i, j): float}` for every edge, `i < j`
    (undirected, half the (N, N) matrix), non-negative values. Checked
    against `pathways.py`'s source directly (SEAM-0006), not assumed.
    """
    for key, value in edge_propensity.items():
        if not (isinstance(key, tuple) and len(key) == 2):
            raise TypeError(f"edge_propensity key {key!r} is not an (i, j) tuple")
        i, j = key
        if not (isinstance(i, (int, np.integer)) and isinstance(j, (int, np.integer))):
            raise TypeError(f"edge_propensity key {key!r} must be a pair of ints")
        if not (0 <= i < n_nodes and 0 <= j < n_nodes):
            raise ValueError(f"edge_propensity key {key!r} out of range for n_nodes={n_nodes}")
        if not i < j:
            raise ValueError(
                f"edge_propensity key {key!r} violates the i < j (undirected, "
                "half-matrix) convention pathways.py's docstring specifies"
            )
        if value < 0:
            raise ValueError(f"edge_propensity[{key!r}] = {value} is negative")


def _validate_pathway(pathway: dict, n_nodes: int) -> None:
    """Assert `pathway` matches `pathways.extract_pathway`'s actual
    documented return contract: exactly the keys "nodes"/"edges"/
    "reached_target"/"propensity", the last shaped like `edge_propensity`.
    """
    required = {"nodes", "edges", "reached_target", "propensity"}
    missing = required - set(pathway)
    if missing:
        raise KeyError(
            f"pathway dict missing key(s) {sorted(missing)} -- does not match "
            "pathways.extract_pathway's documented contract"
        )
    if not isinstance(pathway["reached_target"], (bool, np.bool_)):
        raise TypeError("pathway['reached_target'] must be a bool")
    _validate_edge_propensity(pathway["propensity"], n_nodes)


def plot_pathway_overlay(
    n_nodes: int,
    edge_propensity: dict,
    pathway: dict | None = None,
    coords: np.ndarray | None = None,
    title: str | None = None,
    ax=None,
):
    """Render `pathways.edge_propensity`'s full current-flow field, with an
    optional `pathways.extract_pathway` result overlaid as a highlighted
    route (SEAM-0006).

    `coords` (N, 2) or (N, 3) positions nodes spatially if given (only the
    first two columns are used for a 3-D array -- this is a 2-D schematic,
    not a structure renderer, see TASK-0014's Out Of Scope); otherwise
    nodes are laid out with a networkx spring layout, matching
    `pathways.py`'s own coordinate-free design (it never takes coordinates,
    only `H` and node indices).
    """
    import matplotlib.pyplot as plt
    import networkx as nx

    _validate_edge_propensity(edge_propensity, n_nodes)
    if pathway is not None:
        _validate_pathway(pathway, n_nodes)

    if ax is None:
        _, ax = plt.subplots(figsize=(6, 6))

    G = nx.Graph()
    G.add_nodes_from(range(n_nodes))
    G.add_edges_from(edge_propensity.keys())

    if coords is not None:
        coords = np.asarray(coords)
        pos = {i: (coords[i, 0], coords[i, 1]) for i in range(n_nodes)}
    else:
        pos = nx.spring_layout(G, seed=0)

    max_prop = max(edge_propensity.values(), default=0.0)
    scale = 1.0 / max_prop if max_prop > 0 else 1.0
    edge_widths = [0.5 + 4.0 * edge_propensity[e] * scale for e in G.edges()]
    nx.draw_networkx_edges(G, pos, ax=ax, width=edge_widths, edge_color="C0", alpha=0.5)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=60, node_color="lightgrey", edgecolors="black")

    if pathway is not None and pathway["edges"]:
        nx.draw_networkx_edges(
            G, pos, ax=ax, edgelist=pathway["edges"], width=3.0, edge_color="red"
        )
        nx.draw_networkx_nodes(
            G, pos, ax=ax, nodelist=[pathway["nodes"][0]], node_color="black", node_size=90
        )
        end_color = "green" if pathway["reached_target"] else "orange"
        nx.draw_networkx_nodes(
            G, pos, ax=ax, nodelist=[pathway["nodes"][-1]], node_color=end_color, node_size=90
        )

    ax.set_title(title or "Current-flow edge propensity")
    ax.set_axis_off()
    return ax


# ---------------------------------------------------------------------------
# Summary figure -- composes the panels above (notebook Sec.13)
# ---------------------------------------------------------------------------

def summary_figure(
    ablation_result: dict,
    propagator_result: dict,
    occupation: dict,
    consistency_results: dict[str, dict] | None = None,
    suptitle: str | None = None,
):
    """One multi-panel figure over ablation, propagator comparison, apo/holo
    consistency (if given), and the occupation profile -- the reusable
    replacement for notebook Sec.13's monolithic plotting cell.

    `occupation` is `{"resnums": ..., "occ": ..., "pocket_mask": ...
    (optional), "source_idx": ... (optional), "baseline_occ": ...
    (optional), "baseline_label": ... (optional)}`.

    Returns the created `Figure`.
    """
    import matplotlib.pyplot as plt

    n_rows = 3 if consistency_results is not None else 2
    fig = plt.figure(figsize=(12, 3.2 * n_rows))
    gs = fig.add_gridspec(n_rows, 2, hspace=0.55, wspace=0.35)

    plot_ablation_bar(ablation_result, ax=fig.add_subplot(gs[0, 0]))
    plot_group_comparison(propagator_result, ax=fig.add_subplot(gs[0, 1]), title="Propagator comparison")

    row = 1
    if consistency_results is not None:
        plot_apo_holo_consistency(consistency_results, ax=fig.add_subplot(gs[1, :]))
        row = 2

    ax_occ = fig.add_subplot(gs[row, :])
    plot_occupation_profile(
        occupation["resnums"],
        occupation["occ"],
        pocket_mask=occupation.get("pocket_mask"),
        source_idx=occupation.get("source_idx"),
        baseline_occ=occupation.get("baseline_occ"),
        baseline_label=occupation.get("baseline_label", "baseline"),
        ax=ax_occ,
    )

    if suptitle:
        fig.suptitle(suptitle, y=1.02, fontsize=12, fontweight="bold")
    return fig
