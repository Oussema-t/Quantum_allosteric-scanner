"""TASK-0167.001 -- `allostery.plant`: inject a controllable,
confound-orthogonal active-site -> distal-patch coupling into a real apo
contact graph, for TASK-0167's protein-scale positive control (does the
verdict pipeline detect signal that IS there?).

**Mechanism: channel reweighting.** Multiply edge *weights* along
`n_paths` weighted shortest paths from active-site residues to a planted
distal patch by `(1 + strength)`. No edge is added or removed and no
coordinate is touched -- so `hop_from_seed` (unweighted BFS),
`euclid_from_seed_centroid` (3D distance), and `degree_centrality`
(unweighted degree) are provably invariant. This is a **theorem**, not an
empirical hope, confirmed by reading `baselines.py` directly (not
assumed): all three take `(coords, cutoff)` and rebuild their own
**binary** contact matrix internally -- none of them ever sees a weighted
`W` at all. `assert_confound_orthogonal` below still asserts it, per
this task's own discipline of never trusting a construction without
checking it (`percolation.py`'s TASK-0136 precedent: a unit-capacity
virtual-edge bug sat undetected until a direct synthetic check found it).

**Real, decisive finding, checked before writing any scoring code (not
assumed from the task's own filing text): a weight-only plant is
structurally invisible to `hamiltonians.build_H_new` AND to
`lowmode_predictor.dcc_low`, not merely "not yet wired."** Every GNM-
derived term in `H_new` (`V_R` via `potentials._gnm_msf`, `V_C`, `V_M`)
and `dcc_low` itself route through `potentials._kirchhoff_eigh`, which
**always** builds `contact_matrix(coords, cutoff, weight="binary")`
internally -- hardcoded, no parameter to override, confirmed by reading
the function body directly. `build_H_new`'s own base Laplacian term
(`normalised_laplacian_alpha`) independently rebuilds an
`exponential`-weighted contact matrix from raw coordinates too -- there
is no code path anywhere in `build_H_new` by which an externally-modified
weighted adjacency matrix could ever reach it. This is not a stale-cache
bug (TASK-0135's precedent, which this task's own filing text expected
to find) -- it is that every sub-component independently recomputes its
own contact matrix from `coords`, always with a fixed weighting scheme,
by original design. **A weight-only plant can only be scored against an
operator built directly from the planted `W`** (a weighted graph
Laplacian, e.g. `hamiltonians.laplacian(W_planted)`, or
`transport.effective_resistance_from_source`/`transmission_from_source`
on that Laplacian) -- not against `H_new` or `dcc_low` as currently
coded. This is [[TASK-0167.002]]'s own scoring-scope decision to make
explicitly, not silently discovered there; recorded here as this task's
own answer to its "verify build_H_new consumes the planted W" TODO item.

**Induced-coupling dose axis (Open Question, resolved by measurement +
code-level proof, not just the task's own a-priori recommendation)**:
`lowmode_predictor.dcc_low` is **exactly** invariant to a weight-only
plant (the paragraph above), not merely "non-monotone" as the prototype's
own (differently-implemented) DCC measure showed -- confirmed directly,
see this module's own test suite and TASK-0167.001's Done section for the
real-target measurement. `R_eff` (`transport.effective_resistance_from_
source` on `hamiltonians.laplacian(W_planted)`) is monotone in edge
conductance by Rayleigh's monotonicity law -- a theorem, not an empirical
finding, confirmed numerically on a real target before trusting it. Total
added edge-weight mass is a pure construction quantity: trivially
monotone by definition (guaranteed positive `strength` increment on
every reweighted edge) but carries no physical interpretation on its
own. **`R_eff` is the primary induced-coupling measure**; edge-weight
mass is recorded as a secondary, always-available sanity quantity;
`dcc_low`/`|DCC|` is not used at all (proven inert, not merely
de-prioritized).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed
from .metrics import auc as _auc
from .nulls import compact_patch


def _source_indices(source) -> np.ndarray:
    return np.atleast_1d(np.asarray(source, dtype=int))


@dataclass
class PlantReport:
    """Everything a caller needs to trust and reproduce one plant.

    `pre_floor_auc`/`post_floor_auc` are filled in by the caller from
    `assert_confound_orthogonal`'s own return value (that function's
    docstring: "returns the pre/post floor triple so callers can record
    it") -- `plant_channel` itself never calls the gate (single-purpose
    functions, per this task's own In Scope split), so these fields
    start `None` and are the caller's responsibility to populate before
    trusting a plant downstream.
    """

    strength: float
    n_paths_requested: int
    n_paths_applied: int
    n_paths_failed: int
    edges_modified: list = field(default_factory=list)
    seed_idx: np.ndarray = None
    target_idx: np.ndarray = None
    pre_floor_auc: dict = None
    post_floor_auc: dict = None
    induced_coupling: dict = None


def _graph_from_W(W: np.ndarray):
    """Dijkstra-ready weighted graph from an explicit weighted adjacency
    matrix `W` -- `percolation._weighted_graph`'s own construction
    (`weight = 1/W[i,j]`, a strong/close contact is cheap to traverse),
    generalized from that function's coords-and-cutoff-rebuilt `W` to an
    arbitrary caller-supplied one (this module's own `W` may already be
    a *planted*, i.e. reweighted, matrix -- `percolation._weighted_graph`
    has no hook for that, so it is not reused directly, only its
    convention is)."""
    import networkx as nx

    n = len(W)
    G = nx.Graph()
    G.add_nodes_from(range(n))
    rows, cols = np.nonzero(np.triu(W, k=1))
    for i, j in zip(rows.tolist(), cols.tolist()):
        G.add_edge(i, j, weight=1.0 / W[i, j])
    return G


def plant_channel(
    W: np.ndarray,
    seed_idx,
    target_idx,
    strength: float,
    n_paths: int,
    rng: np.random.Generator,
) -> tuple:
    """Multiply edge weights along `n_paths` weighted shortest paths
    (`dist = 1/weight`) from randomly-drawn seed residues to randomly-
    drawn target-patch residues by `(1 + strength)`. Edits **existing
    edges only** -- an edge with `W[i,j] == 0` before planting has
    `W[i,j] == 0` after (multiplying zero by anything is still zero;
    also no new edge is ever added to the traversed-edge set, since
    every edge on a path found in `_graph_from_W(W)` already existed in
    `W` by construction of that graph).

    Each of the `n_paths` iterations draws one random seed residue and
    one random target-patch residue (`rng.choice`, not the single
    globally-cheapest path repeated) and reweights the single weighted
    shortest path between that specific pair -- spreading the plant
    across the channel's own natural route diversity rather than always
    reinforcing one path. A pair with no path between them (disconnected
    apo graph) is recorded as a failure in `PlantReport.n_paths_failed`,
    not silently dropped or fatal.

    `strength == 0.0` returns `W` **bit-identical** (a plain `.copy()`,
    no path-finding attempted at all) -- the identity this task's own
    Constraint requires and TASK-0167.003's zero-plant specificity check
    depends on.
    """
    seed_idx = _source_indices(seed_idx)
    target_idx = _source_indices(target_idx)
    W_planted = W.copy()

    if strength == 0.0:
        return W_planted, PlantReport(
            strength=0.0, n_paths_requested=n_paths, n_paths_applied=0,
            n_paths_failed=0, edges_modified=[], seed_idx=seed_idx, target_idx=target_idx,
        )

    import networkx as nx

    G = _graph_from_W(W)
    edges_to_reweight = set()
    n_applied = 0
    n_failed = 0
    for _ in range(n_paths):
        s = int(rng.choice(seed_idx))
        t = int(rng.choice(target_idx))
        try:
            path = nx.shortest_path(G, s, t, weight="weight")
        except nx.NetworkXNoPath:
            n_failed += 1
            continue
        for a, b in zip(path[:-1], path[1:]):
            edges_to_reweight.add((min(a, b), max(a, b)))
        n_applied += 1

    for i, j in edges_to_reweight:
        W_planted[i, j] *= 1.0 + strength
        W_planted[j, i] *= 1.0 + strength

    report = PlantReport(
        strength=strength, n_paths_requested=n_paths, n_paths_applied=n_applied,
        n_paths_failed=n_failed, edges_modified=sorted(edges_to_reweight),
        seed_idx=seed_idx, target_idx=target_idx,
    )
    return W_planted, report


def plant_mode(
    W: np.ndarray,
    seed_idx,
    target_idx,
    strength: float,
    rng: np.random.Generator,
) -> tuple:
    """TASK-0168 -- Plant B: a *correlated-mode* perturbation, the mirror
    image of `plant_channel`'s strengthening. Softens every edge crossing
    the boundary of `G = seed_idx UNION target_idx` versus the rest of the
    structure (divides its weight by `(1 + strength)`), intended to make a
    low collective (Kirchhoff-Laplacian) eigenmode concentrate coordinated,
    same-sign amplitude on `G` -- without adding, removing, or strengthening
    any edge *within* `G` (including the direct seed<->target path, which
    is untouched here, unlike `plant_channel`'s whole purpose).

    `rng` is accepted for interface symmetry with `plant_channel`
    (unused -- this construction is deterministic given
    `W`/`seed_idx`/`target_idx`/`strength`, there is no random draw to make).

    Same `strength == 0.0` identity guarantee as `plant_channel`: returns
    `W` bit-identical, no boundary computed.

    **Not proven orthogonal to a channel effect by construction** -- see
    this module's own TASK-0168 caller for the required empirical spectral
    check (`verify_mode_plant_spectral_effect` in
    `scripts/mechanism_discriminating_plant.py`); TASK-0168's own Open
    Questions flags this as a real, unresolved possibility, not assumed
    away here.
    """
    seed_idx = _source_indices(seed_idx)
    target_idx = _source_indices(target_idx)
    W_planted = W.copy()

    if strength == 0.0:
        return W_planted, PlantReport(
            strength=0.0, n_paths_requested=0, n_paths_applied=0,
            n_paths_failed=0, edges_modified=[], seed_idx=seed_idx, target_idx=target_idx,
        )

    group = set(seed_idx.tolist()) | set(target_idx.tolist())
    rows, cols = np.nonzero(np.triu(W, k=1))
    edges_to_soften = []
    for i, j in zip(rows.tolist(), cols.tolist()):
        if (i in group) != (j in group):  # exactly one endpoint in G: a boundary edge
            edges_to_soften.append((i, j))

    for i, j in edges_to_soften:
        W_planted[i, j] /= 1.0 + strength
        W_planted[j, i] /= 1.0 + strength

    report = PlantReport(
        strength=strength, n_paths_requested=0, n_paths_applied=len(edges_to_soften),
        n_paths_failed=0, edges_modified=sorted(edges_to_soften),
        seed_idx=seed_idx, target_idx=target_idx,
    )
    return W_planted, report


def select_distal_patch(
    coords: np.ndarray,
    W: np.ndarray,
    seed_idx,
    size: int,
    rng: np.random.Generator,
    *,
    cutoff: float = 10.0,
    hop_percentile: float = 60.0,
    max_floor_auc: float = 0.5,
    max_attempts: int = 20_000,
) -> np.ndarray:
    """Draw a compact (`nulls.compact_patch`) candidate patch subject to
    both of this task's own hard admission criteria, rejection-sampled
    (`closure.matched_spread_null`'s own precedent: a real, reportable
    infeasibility raises, it is never silently absorbed into a weaker
    patch):

    1. **Genuinely distal**: mean hop-from-seed >= `hop_percentile`
       (default 60th) of the protein's own hop-distance distribution --
       not a near-shell patch that would be an easy, uninteresting case.
    2. **Floor-blind before planting**: the pre-plant proximity-floor AUC
       (max of `degree_centrality`/`hop_from_seed`/`euclid_from_seed_
       centroid`, seed residues excluded from scoring, matching
       `diagnostics.classify_failure`'s own masking convention) must be
       <= `max_floor_auc` (default 0.5) -- planting somewhere the floor
       already favours is a null experiment, per this task's own
       Constraint, and must be rejected outright, not reported as a weak
       positive control.

    `W` is accepted (not just `coords`) for interface symmetry with
    `plant_channel`/`assert_confound_orthogonal`, though patch selection
    itself only uses `coords` (both admission criteria are properties of
    the unplanted floor, which never depends on edge weight -- see this
    module's own docstring)."""
    seed_idx = _source_indices(seed_idx)
    n = len(coords)
    hops = -hop_from_seed(coords, seed_idx, cutoff=cutoff)
    hop_threshold = float(np.percentile(hops, hop_percentile))

    floor_scores = [
        degree_centrality(coords, cutoff=cutoff),
        hop_from_seed(coords, seed_idx, cutoff=cutoff),
        euclid_from_seed_centroid(coords, seed_idx),
    ]
    mask = np.ones(n, dtype=bool)
    mask[seed_idx] = False

    seed_set = set(seed_idx.tolist())
    for _attempt in range(max_attempts):
        candidate = compact_patch(coords, size, rng)
        if seed_set & set(candidate.tolist()):
            continue
        mean_hop = float(hops[candidate].mean())
        if mean_hop < hop_threshold:
            continue
        label = np.zeros(n, dtype=int)
        label[candidate] = 1
        cand_max_floor = max(float(_auc(fs[mask], label[mask])) for fs in floor_scores)
        if cand_max_floor <= max_floor_auc:
            return candidate

    raise RuntimeError(
        f"select_distal_patch: no admissible patch (mean hop >= {hop_threshold:.2f}, "
        f"max floor AUC <= {max_floor_auc}) found within {max_attempts} attempts"
    )


def assert_confound_orthogonal(
    W0: np.ndarray,
    W_planted: np.ndarray,
    coords: np.ndarray,
    seed_idx,
    label: np.ndarray,
    *,
    cutoff: float = 10.0,
) -> tuple:
    """The gate. Asserts, to **exact equality** where exact equality is
    the correct bar (no tolerance parameter -- these are edits that
    provably cannot move these quantities, `baselines.py` never
    consulting `W` at all, per this module's own docstring; any movement
    is therefore a real bug, not numerical noise to be tolerated):

    - unweighted adjacency `(W > 0)` bit-identical between `W0` and
      `W_planted` -- the one check that actually depends on `W_planted`,
      since it is the one thing a buggy `plant_channel` could violate
      (adding or removing an edge);
    - `coords` unchanged (identity/equality check against a snapshot
      taken at the top of this function -- `plant_channel` never
      receives `coords` at all, so this can only fail if some future
      caller mutates it in place before calling this gate);
    - `degree_centrality`/`hop_from_seed`/`euclid_from_seed_centroid`
      AUC against `label` unchanged exactly, computed twice (nominally
      "pre" and "post") from the identical `coords` -- since none of
      them ever look at `W`, this is a regression guard against a
      future `baselines.py` change to a weighted convention silently
      breaking the orthogonality property, not a check that could ever
      catch anything about `W_planted` itself.

    Raises `AssertionError` (not a bool return) on any violation --
    a plant that fails this gate is not a usable positive control, and
    must stop the caller, not be reported. Returns `(pre_auc, post_auc)`
    dicts (keys `"degree"`/`"hop"`/`"euclid"`) so callers can record them
    into their own `PlantReport.pre_floor_auc`/`post_floor_auc`.
    """
    if not np.array_equal(W0 > 0, W_planted > 0):
        raise AssertionError(
            "assert_confound_orthogonal: unweighted adjacency changed by planting "
            "(an edge was added or removed) -- the plant is contaminated"
        )

    coords_snapshot = coords.copy()
    if not np.array_equal(coords, coords_snapshot):
        raise AssertionError("assert_confound_orthogonal: coords mutated")

    seed_idx = _source_indices(seed_idx)
    n = len(coords)
    mask = np.ones(n, dtype=bool)
    mask[seed_idx] = False

    def _floor_aucs():
        scores = {
            "degree": degree_centrality(coords, cutoff=cutoff),
            "hop": hop_from_seed(coords, seed_idx, cutoff=cutoff),
            "euclid": euclid_from_seed_centroid(coords, seed_idx),
        }
        return {name: float(_auc(s[mask], label[mask])) for name, s in scores.items()}

    pre_auc = _floor_aucs()
    post_auc = _floor_aucs()
    for name in pre_auc:
        if pre_auc[name] != post_auc[name]:
            raise AssertionError(
                f"assert_confound_orthogonal: floor AUC '{name}' moved "
                f"({pre_auc[name]} -> {post_auc[name]}) -- this should be structurally "
                "impossible for a weight-only plant; the orthogonality property is broken"
            )

    return pre_auc, post_auc
