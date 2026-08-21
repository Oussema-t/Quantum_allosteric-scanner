"""TASK-0204 (reopened, reformulated) -- is side-chain rotamer packing on
these windows actually a HARD instance?

## Why this replaces criterion #1 as the gating question

Phase B's own criterion #1 asks a *biological* question: does optimized
packing open a druggable cavity more often than greedy? The reopened
TASK-0204 showed that question was badly instrumented. But there is a
prior problem, raised by the orchestrating user (2026-08-06) and not
addressed anywhere in the register:

    **Even a clean PASS on criterion #1 would not have supported a quantum
    route, because the instance solves classically in seconds.**

The original run repacked a 12-residue window in ~2 s per trial on a
laptop. "Why use a quantum computer for something a laptop does in
seconds?" is not a rhetorical objection -- it is the same complexity
argument this register already used to close Grover/HHL/QML and
single-particle CTQW ("at N<=704 it is an `eigh` call, so no advantage
exists at any point"). Applied here it must be answered *before* any
biological proxy is worth running.

## The measurement

Side-chain packing with a fixed backbone and a discrete rotamer library is
exactly a pairwise Markov random field: one discrete variable per repacked
residue (which rotamer), self-energies, and pairwise terms between
residues whose side chains can reach each other. The naive search space is
`prod_i n_i ~ n^m`, which looks exponential and is what the Phase B
write-up's own qubit estimate is built on (`m*n` one-hot binary
variables, "180 logical qubits").

But exact minimization of a pairwise MRF is **not** `O(n^m)`. Via bucket
elimination / junction-tree (equivalently, what Dead-End Elimination plus
branch-and-bound exploits in practice) it is::

    O(m * n^(tw+1))

where `tw` is the **treewidth** of the residue interaction graph. Treewidth,
not variable count, is what decides whether this instance class is hard.
A spatially compact surface window has a sparse, near-planar interaction
graph; if `tw` stays bounded as `m` grows, exact optimization is polynomial
in `m` and the NP-hardness of *general* rotamer packing (Pierce & Winfree
2002) never bites on the instances this project would actually solve.

So this script measures, on real structures:

  1. real window residues (the project's own pocket labels, several sizes)
  2. the side-chain interaction graph (Cbeta-Cbeta, cutoff swept)
  3. `tw` upper bound (min-fill) and lower bound (minor-min-width)
  4. naive `n^m` vs. exact `m * n^(tw+1)` cost, at the write-up's own n=15
  5. how `tw` scales with window size `m`

**Falsification, stated before running** (per this project's standing
practice): if `tw` grows roughly linearly with `m` -- i.e. the interaction
graph is dense enough that exact inference stays exponential in the window
size -- then there is a genuine hard-instance regime and Phase B's route
survives this test. If `tw` saturates at a small constant while `m` grows,
exact classical optimization is polynomial and the route is closed on
complexity grounds, permanently, for every window size, regardless of any
biological result.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from allostery.clean import load_target_config  # noqa: E402

TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "PTP1B"]
WINDOW_SIZES = [8, 12, 16, 20, 30, 50, 80]
CB_CUTOFFS = [8.0, 10.0, 12.0]
N_ROTAMERS = 15  # PHASE_B_ROTAMER_QUBO.md's own "n ~= 10-20, coarse buckets" midpoint
OUT_DIR = _ROOT / "results/tasks/0204_packing_hardness"


def _cbeta_coords(pdb_id: str, chains):
    """One representative side-chain-base coordinate per residue: CB where
    it exists, CA for glycine. Side-chain reach is measured from CB, so a
    CB-CB cutoff is the right proximity test for "can these two residues'
    rotamers interact"."""
    import prody

    prody.confProDy(verbosity="none")
    st = prody.parsePDB(pdb_id, compressed=False)
    alt = st.getAltlocs()
    if alt is not None and any(a not in ("", " ", "\x00") for a in alt):
        st = st.select("altloc _ A") or st
    sel = " or ".join(f"chain {c}" for c in chains)
    st = st.select(f"protein and ({sel})")
    coords, keys = [], []
    for res in st.getHierView().iterResidues():
        atom = res.select("name CB") or res.select("name CA")
        if atom is None:
            continue
        coords.append(np.asarray(atom.getCoords())[0])
        keys.append((str(res.getChid()), int(res.getResnum())))
    return np.array(coords), keys


def _window(coords: np.ndarray, pocket_idx: np.ndarray, size: int) -> np.ndarray:
    """Same selection rule the repack runs used: grow outward from the
    pocket centroid. Beyond the pocket's own size this necessarily pulls in
    non-pocket neighbours -- which is the point, since the scaling question
    is about window size, not about pocket identity."""
    centroid = coords[pocket_idx].mean(axis=0)
    order = np.argsort(np.linalg.norm(coords - centroid, axis=1))
    return order[:size]


def _treewidth_bounds(g: nx.Graph):
    """Upper bound: min-fill heuristic (networkx). Lower bound:
    minor-min-width (contract the min-degree vertex into its
    lowest-degree neighbour, track the max degree seen) -- a standard,
    cheap, valid lower bound. Reporting both means the conclusion does not
    rest on a heuristic being tight."""
    if g.number_of_nodes() == 0:
        return 0, 0
    upper, _ = nx.algorithms.approximation.treewidth_min_fill_in(g)

    h = g.copy()
    lower = 0
    while h.number_of_nodes() > 1:
        v = min(h.nodes, key=lambda x: h.degree(x))
        lower = max(lower, h.degree(v))
        nbrs = list(h.neighbors(v))
        if not nbrs:
            h.remove_node(v)
            continue
        u = min(nbrs, key=lambda x: h.degree(x))
        h = nx.contracted_nodes(h, u, v, self_loops=False)
    return int(lower), int(upper)


def run_target(name: str) -> dict:
    cfg = load_target_config(name)
    chains = cfg.get("apo_chains") or cfg.get("chains") or ["A"]
    coords, keys = _cbeta_coords(cfg["apo_pdb"], chains)
    key_index = {k: i for i, k in enumerate(keys)}

    label = cfg.get("pocket_label") or {}
    pocket_keys = [(c, int(r)) for c, r in (label.get("consensus") or label.get("incumbent_4_5A") or [])]
    pocket_idx = np.array([key_index[k] for k in pocket_keys if k in key_index], dtype=int)
    if len(pocket_idx) == 0:
        return {"target": name, "error": "no pocket residues resolvable on the apo structure"}

    out = {"target": name, "n_residues": len(keys), "n_pocket": int(len(pocket_idx)), "scaling": []}
    for size in WINDOW_SIZES:
        if size > len(keys):
            continue
        widx = _window(coords, pocket_idx, size)
        wc = coords[widx]
        d = np.linalg.norm(wc[:, None, :] - wc[None, :, :], axis=-1)
        row = {"m": int(size), "cutoffs": {}}
        for cut in CB_CUTOFFS:
            g = nx.Graph()
            g.add_nodes_from(range(size))
            iu = np.triu_indices(size, k=1)
            for a, b in zip(*iu):
                if d[a, b] <= cut:
                    g.add_edge(int(a), int(b))
            lo, up = _treewidth_bounds(g)
            naive_log10 = size * np.log10(N_ROTAMERS)
            exact_log10 = np.log10(size) + (up + 1) * np.log10(N_ROTAMERS)
            row["cutoffs"][str(cut)] = {
                "edges": g.number_of_edges(),
                "mean_degree": round(2 * g.number_of_edges() / size, 2),
                "tw_lower": lo, "tw_upper": up,
                "naive_log10_ops": round(float(naive_log10), 1),
                "exact_log10_ops": round(float(exact_log10), 1),
            }
        out["scaling"].append(row)
    return out


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    results = {}
    for name in TARGETS:
        try:
            results[name] = run_target(name)
        except Exception as exc:  # noqa: BLE001
            results[name] = {"target": name, "error": f"{type(exc).__name__}: {exc}"}
        print(f"[done] {name}", flush=True)
    (OUT_DIR / "packing_hardness.json").write_text(json.dumps(results, indent=1))

    print(f"\n=== Exact-solve cost of side-chain packing (n={N_ROTAMERS} rotamers/site) ===")
    for name, r in results.items():
        if "error" in r:
            print(f"\n{name}: ERROR {r['error']}")
            continue
        print(f"\n{name}  (N={r['n_residues']}, pocket={r['n_pocket']})")
        print(f"  {'m':>4} {'cut':>5} {'edges':>6} {'<deg>':>6} {'tw':>9} "
              f"{'naive n^m':>11} {'exact m*n^(tw+1)':>18}")
        for row in r["scaling"]:
            for cut, c in row["cutoffs"].items():
                print(f"  {row['m']:>4} {cut:>5} {c['edges']:>6} {c['mean_degree']:>6} "
                      f"{str(c['tw_lower'])+'-'+str(c['tw_upper']):>9} "
                      f"{'1e'+str(c['naive_log10_ops']):>11} {'1e'+str(c['exact_log10_ops']):>18}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
