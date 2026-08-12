"""TASK-0204 (reopened) -- validate the treewidth cost model by actually
solving a real packing instance exactly, and timing it.

`task0204_packing_hardness.py` argues from treewidth that exact
minimization of the side-chain packing MRF costs `O(m * n^(tw+1))`, not
the naive `O(n^m)`. That is a standard result, but this project's own
convention is to measure rather than cite. So: build the real interaction
graph for a real pocket window, put a real-shaped pairwise energy model on
it, minimize **exactly** by bucket elimination, and time it.

Correctness gate, run first: on instances small enough to enumerate, the
bucket-elimination optimum must equal the brute-force optimum exactly.
"""
from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path

import networkx as nx
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from task0204_packing_hardness import _cbeta_coords, _window, load_target_config  # noqa: E402

N_ROTAMERS = 15
# ~1e8 float64 entries = 800 MB. Above this the exact solve is genuinely
# expensive and gets reported as a projection rather than run -- the cost
# model doing its job, not a failure to measure.
MAX_FACTOR_ENTRIES = 1e8
OUT_DIR = _ROOT / "results_task0204_packing_hardness"


def build_instance(g: nx.Graph, n: int, rng: np.random.Generator):
    """Self-energies + pairwise tables on the real interaction graph.
    Magnitudes follow packing-energy convention (pairwise clash terms
    dominate self terms); the *values* do not matter for timing, only the
    graph and the table sizes do."""
    self_e = {v: rng.normal(0, 1, size=n) for v in g.nodes}
    pair_e = {(u, v): rng.normal(0, 3, size=(n, n)) for u, v in g.edges}
    return self_e, pair_e


def brute_force_min(g, self_e, pair_e, n):
    best = np.inf
    for assign in itertools.product(range(n), repeat=g.number_of_nodes()):
        e = sum(self_e[v][assign[v]] for v in g.nodes)
        e += sum(pair_e[(u, v)][assign[u], assign[v]] for u, v in g.edges)
        best = min(best, e)
    return float(best)


def bucket_elimination_min(g, self_e, pair_e, n):
    """Exact minimization by variable elimination in a min-fill order.
    Factors are min-plus combined; cost is dominated by the largest
    intermediate factor, i.e. `n^(tw+1)`."""
    h = g.copy()
    order = []
    while h.number_of_nodes():
        v = min(h.nodes, key=lambda x: _fill_in(h, x))
        order.append(v)
        nbrs = list(h.neighbors(v))
        for a, b in itertools.combinations(nbrs, 2):
            h.add_edge(a, b)
        h.remove_node(v)

    # factors: dict from tuple(vars) -> ndarray over those vars
    factors = [((v,), self_e[v].copy()) for v in g.nodes]
    factors += [((u, v), pair_e[(u, v)].copy()) for u, v in g.edges]
    max_factor = 0

    for v in order:
        touching = [f for f in factors if v in f[0]]
        factors = [f for f in factors if v not in f[0]]
        if not touching:
            continue
        scope = sorted({x for f in touching for x in f[0]})
        shape = tuple(n for _ in scope)
        max_factor = max(max_factor, int(np.prod(shape)))
        acc = np.zeros(shape)
        for vars_, tab in touching:
            acc = acc + _broadcast(tab, vars_, scope, n)
        axis = scope.index(v)
        reduced = acc.min(axis=axis)
        new_scope = tuple(x for x in scope if x != v)
        factors.append((new_scope, reduced) if new_scope else ((), reduced))

    total = 0.0
    for scope, tab in factors:
        total += float(tab) if scope == () else float(np.min(tab))
    return total, max_factor


def _broadcast(tab, vars_, scope, n):
    """Reshape a factor over `vars_` so it broadcasts against `scope`.

    `scope` is sorted. Transpose `tab` so its axes follow sorted(`vars_`)
    -- then those axes appear in `scope` in the same increasing order, so a
    reshape inserting singleton dims at the non-member positions is a valid
    (and correctly aligned) broadcast view."""
    perm = np.argsort(np.asarray(vars_))
    tab_sorted = np.transpose(tab, perm)
    member = set(vars_)
    return tab_sorted.reshape([n if s in member else 1 for s in scope])


def _fill_in(h, v):
    nbrs = list(h.neighbors(v))
    return sum(1 for a, b in itertools.combinations(nbrs, 2) if not h.has_edge(a, b))


def real_graph(target: str, m: int, cutoff: float = 8.0) -> nx.Graph:
    cfg = load_target_config(target)
    chains = cfg.get("apo_chains") or cfg.get("chains") or ["A"]
    coords, keys = _cbeta_coords(cfg["apo_pdb"], chains)
    key_index = {k: i for i, k in enumerate(keys)}
    label = cfg.get("pocket_label") or {}
    pk = [(c, int(r)) for c, r in (label.get("consensus") or label.get("incumbent_4_5A") or [])]
    pocket_idx = np.array([key_index[k] for k in pk if k in key_index], dtype=int)
    widx = _window(coords, pocket_idx, m)
    wc = coords[widx]
    d = np.linalg.norm(wc[:, None, :] - wc[None, :, :], axis=-1)
    g = nx.Graph()
    g.add_nodes_from(range(m))
    for a, b in zip(*np.triu_indices(m, k=1)):
        if d[a, b] <= cutoff:
            g.add_edge(int(a), int(b))
    return g


def main() -> int:
    rng = np.random.default_rng(0)
    results = {"correctness_gate": [], "timing": []}

    print("=== Correctness gate: bucket elimination vs. brute force ===")
    for m, n in [(6, 4), (7, 3), (8, 4)]:
        g = real_graph("KRAS_G12C", m)
        se, pe = build_instance(g, n, rng)
        bf = brute_force_min(g, se, pe, n)
        be, _ = bucket_elimination_min(g, se, pe, n)
        ok = abs(bf - be) < 1e-9
        print(f"  m={m} n={n}: brute={bf:.6f} bucket={be:.6f}  match={ok}")
        results["correctness_gate"].append({"m": m, "n": n, "brute": bf, "bucket": be, "match": bool(ok)})
        assert ok, "bucket elimination disagrees with brute force -- solver is wrong"

    print(f"\n=== Exact solve of REAL pocket windows, n={N_ROTAMERS} rotamers/site, 8 A ===")
    print(f"  {'target':<16} {'m':>3} {'tw':>3} {'naive n^m':>11} {'wall (s)':>9} {'max factor':>11}")
    for target in ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "PTP1B"]:
        for m in (12, 16, 20):
            g = real_graph(target, m)
            tw = nx.algorithms.approximation.treewidth_min_fill_in(g)[0]
            projected = N_ROTAMERS ** (tw + 1)
            naive = f"1e{m * np.log10(N_ROTAMERS):.1f}"
            if projected > MAX_FACTOR_ENTRIES:
                # Honest handling: this is the cost model working, not a
                # failure. Report the projection rather than exhausting RAM
                # (15**9 float64 = 300 GB). An instance this project would
                # not actually solve should not be silently omitted either.
                print(f"  {target:<16} {m:>3} {tw:>3} {naive:>11} {'skipped':>9} "
                      f"{projected:>11.3g}  (projected > budget)")
                results["timing"].append({
                    "target": target, "m": m, "n": N_ROTAMERS, "tw_upper": int(tw),
                    "skipped_over_budget": True, "projected_factor_entries": float(projected),
                    "naive_log10": round(float(m * np.log10(N_ROTAMERS)), 1),
                })
                continue
            se, pe = build_instance(g, N_ROTAMERS, rng)
            t0 = time.monotonic()
            val, maxf = bucket_elimination_min(g, se, pe, N_ROTAMERS)
            dt = time.monotonic() - t0
            print(f"  {target:<16} {m:>3} {tw:>3} {naive:>11} {dt:>9.3f} {maxf:>11.3g}")
            results["timing"].append({
                "target": target, "m": m, "n": N_ROTAMERS, "tw_upper": int(tw),
                "wall_s": round(dt, 4), "max_factor_entries": int(maxf), "optimum": val,
                "naive_log10": round(float(m * np.log10(N_ROTAMERS)), 1),
            })

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "exact_solve_validation.json").write_text(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
