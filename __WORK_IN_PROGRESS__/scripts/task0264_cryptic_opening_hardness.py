#!/usr/bin/env python3
"""TASK-0264 -- is a genuine CRYPTIC-OPENING instance (backbone move choice
COUPLED to side-chain rotamer packing) actually hard, before any QUBO is
built for it? [[TASK-0204]] already answered this for pure rotamer packing
on a FIXED backbone (treewidth 2-5 at m=12, exact solve in milliseconds) --
this task asks the harder, physically correct question cryptic-pocket
opening actually poses: what happens once the backbone is also allowed to
move.

## Instance definition (written down before measurement, per this task's
## own Scope -- not adjusted after seeing a result)

**Variables.**
  - One ROTAMER-choice variable per repackable residue in the window
    (pocket-lining + a shell, grown outward from the pocket centroid by
    CB-CB distance -- [[TASK-0204]]'s own `_window` convention, reused
    unchanged). Domain size n=15 (TASK-0204's own established rotamer-
    library granularity, `PHASE_B_ROTAMER_QUBO.md`'s own "n~10-20, coarse
    buckets" midpoint) -- unchanged, for direct comparability.
  - ONE shared BACKBONE-CHOICE variable for the whole window. Domain size
    K=11: apo's own static conformation, plus apo stepped +-6A along each
    of its own first 5 ANM modes -- [[TASK-0228]]'s own already-validated
    `adaptive_anm_modes` convention (mode count, amplitude, sign
    convention all reused unchanged, not re-tuned here). Each of the 11
    displacement fields is turned into a real full-atom structure via
    [[TASK-0235]]'s own `local_rigid_reconstruction` (local-Kabsch,
    window=1) -- the SAME validated backbone-placement machinery that
    task built and tested, reused, not re-derived.

**Why one shared variable, not one per residue.** TASK-0235's own backbone
move is driven by a COLLECTIVE displacement field (a whole-structure ANM
mode step), not an independent per-residue choice. Encoding it as m
independent per-residue backbone variables would invent degrees of
freedom this project's own move-generating machinery does not have --
the physically honest encoding is one variable selecting WHICH of the K
collective conformations the window is in.

**Coupling / interaction graph.** The backbone-choice variable is
connected to every rotamer variable in the window (a "hub" node) --
choosing a backbone conformation changes every residue's own coordinate
context, hence its self-energy and every pairwise energy it enters.
Rotamer-rotamer edges are CB-CB proximity (cutoff swept, [[TASK-0204]]'s
own 8/10/12 A), UNIONED across all K backbone conformations -- exact
joint optimization over both variable types must account for any residue
pair that could interact under ANY conformation being jointly searched,
so the union graph, not any single conformation's own graph, is the one
whose treewidth answers the real question.

**Objective** (stated for completeness, per this task's own Scope --
NOT needed for a treewidth/timing measurement; [[TASK-0204]]'s own
precedent: "the *values* do not matter for timing, only the graph and
the table sizes do"): self+pairwise rotamer energy at the chosen backbone
conformation (EvoEF2-style) + that conformation's own harmonic strain
cost ([[TASK-0233]]/[[TASK-0235]]'s own DG(residual) machinery) minus a
cavity-opening/druggability reward (fpocket-style, `PHASE_B_ROTAMER_
QUBO.md`'s own `CavityOpening(x)` term). Not built as real numbers here,
matching TASK-0204's own exact-solve validation, which timed bucket
elimination on realistically-shaped RANDOM energies -- wall-clock cost
is graph-structure-determined (m, treewidth, domain sizes), not
value-determined.

**Pre-registered verdict rule, stated before running (this task's own
Scope requirement, its own suggested numbers adopted as stated):**
median treewidth >= 12 on the 11 genuinely-cryptic targets ([[TASK-0254]]
Part B) at realistic instance size (m=12-20, pocket+shell) => a real
quantum target, worth building the QUBO properly. Median treewidth <= 6
=> formulation exercise only, the same verdict TASK-0204 already reached
for pure rotamer packing.
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
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402

prody.confProDy(verbosity="none")
from task0255_hop_angstrom_calibration import _parsePDB_all_altloc  # noqa: E402

prody.parsePDB = _parsePDB_all_altloc

import yaml  # noqa: E402

from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import H13_3N_anm_hessian  # noqa: E402
from task0204_packing_hardness import _treewidth_bounds, _window  # noqa: E402
from task0230_ceiling_and_brittleness import _load_full_atom_apo  # noqa: E402
from task0235_local_rigid_backbone import LOCAL_WINDOW, local_rigid_reconstruction  # noqa: E402
import task0242_two_stage_dryrun as t0242  # noqa: E402

# task0242's own module-level CAND is bound to TASK-0216's small candidate
# file at import time -- swap it to TASK-0243's frozen 22-target set, same
# technique task0243_stage1_and_rerun.py/task0258 already used and verified
# propagates through prep()'s own closures (module-attribute access, not a
# `from module import CAND` snapshot, which would NOT see this update).
t0242.CAND = yaml.safe_load((_ROOT / "config" / "candidate_targets_task0243.yaml").read_text())["targets"]
CAND = t0242.CAND
prep = t0242.prep

N_ROTAMERS = 15
N_MODES_STEPPED = 5
STEP_AMP = 6.0  # Angstrom -- TASK-0228's own adaptive_anm_modes default, reused
K_BACKBONE = 1 + 2 * N_MODES_STEPPED  # 11
WINDOW_SIZES = [8, 12, 16, 20]
EXACT_SOLVE_SIZES = [4, 6, 8, 12, 16, 20]  # extends below WINDOW_SIZES' own min to find the feasible/infeasible boundary
CB_CUTOFFS = [8.0, 10.0, 12.0]
MAX_FACTOR_ENTRIES = 1e8  # TASK-0204's own guard, reused verbatim, not raised
OUT_DIR = _ROOT / "results/tasks/0264_cryptic_opening_hardness"

CRYPTIC_TARGETS = [  # TASK-0254 Part B, already_open == False
    "DHPS_GC7", "KSHV_PROTEASE_24Q", "KSHV_PROTEASE_25G", "SUMO_E1_FHJ",
    "HCV_NS5B_POO", "HCV_NS5B_CMF", "FBPASE_94D", "FBPASE_95S",
    "TRP_SYNTHASE_F19", "MKK7_IBRUTINIB", "NAMPT_NPA1R",
]
MANDATORY_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "PTP1B"]  # TASK-0204's own 4, for comparability


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _cb_coords_by_key(struct) -> dict:
    """(chain, resnum) -> CB coord (CA for glycine) over a real prody
    AtomGroup, same convention as task0204_packing_hardness._cbeta_coords."""
    out = {}
    for res in struct.getHierView().iterResidues():
        atom = res.select("name CB") or res.select("name CA")
        if atom is None:
            continue
        out[(str(res.getChid()), int(res.getResnum()))] = np.asarray(atom.getCoords())[0]
    return out


def build_instance(target: str) -> dict:
    """One target's own real cryptic-opening instance: the window, the K
    backbone conformations' own CB coordinates for that window, and the
    resulting per-cutoff union interaction graphs."""
    target_config = CAND[target] if target in CAND else load_target_config(target)
    apo_chains = target_config.get("apo_chains") or target_config.get("chains") or ["A"]

    cfg, apo, seed, pocket = prep(target)
    if pocket is None or not pocket.any():
        return {"target": target, "error": "no resolvable pocket"}
    pocket_idx = np.where(pocket)[0]

    native_struct = _load_full_atom_apo(target_config, apo_chains)
    native_cb = _cb_coords_by_key(native_struct)
    chain_ids = np.asarray(apo.chain_ids)
    apo_keys_all = [(str(chain_ids[i]), int(apo.resnums[i])) for i in range(len(apo.resnums))]
    cb_coords = np.array([native_cb.get(k, apo.coords[i]) for i, k in enumerate(apo_keys_all)])

    max_size = max(WINDOW_SIZES)
    if max_size > len(apo_keys_all):
        max_size = len(apo_keys_all)
    order = _window(cb_coords, pocket_idx, max_size)
    window_keys_full = [apo_keys_all[i] for i in order]

    # --- K backbone conformations: apo static + apo stepped +-STEP_AMP
    # along each of its own first N_MODES_STEPPED ANM modes -- TASK-0228's
    # own adaptive_anm_modes convention, re-derived here only because that
    # function returns a mode SUBSPACE, not the K stepped coordinate sets
    # this task needs; the underlying eigensolve (H13_3N_anm_hessian) is
    # reused unchanged, not re-implemented.
    enm_cutoff = float(target_config.get("enm_cutoff", 10.0))
    N = len(apo.coords)
    H = H13_3N_anm_hessian(apo.coords, cutoff=enm_cutoff)
    w, v = np.linalg.eigh(H)
    nz = np.flatnonzero(w > 1e-8)
    mode_vecs = v[:, nz[:N_MODES_STEPPED]]

    disp_fields = [np.zeros((N, 3))]  # apo static
    for m in range(min(N_MODES_STEPPED, mode_vecs.shape[1])):
        mode = mode_vecs[:, m].reshape(N, 3)
        mode = mode / np.linalg.norm(mode)
        for sign in (+1, -1):
            disp_fields.append(sign * mode * np.sqrt(N) * STEP_AMP)

    apo_ca_by_res = {apo_keys_all[i]: apo.coords[i] for i in range(N)}
    window_key_set = set(window_keys_full)

    cb_per_state = []  # list over K, each a dict window_key -> CB coord
    for disp in disp_fields:
        target_ca_by_res = {apo_keys_all[i]: apo.coords[i] + disp[i] for i in range(N)}
        struct = _load_full_atom_apo(target_config, apo_chains)
        struct = local_rigid_reconstruction(struct, apo_ca_by_res, target_ca_by_res, window=LOCAL_WINDOW)
        cb_this = _cb_coords_by_key(struct)
        cb_per_state.append({k: cb_this.get(k, target_ca_by_res[k]) for k in window_key_set})

    return {
        "target": target, "window_keys_full": window_keys_full,
        "cb_per_state": cb_per_state, "n_states": len(cb_per_state),
    }


def union_graph(window_keys: list, cb_per_state: list, cutoff: float) -> nx.Graph:
    m = len(window_keys)
    g = nx.Graph()
    g.add_nodes_from(range(m))
    for state_cb in cb_per_state:
        wc = np.array([state_cb[k] for k in window_keys])
        d = np.linalg.norm(wc[:, None, :] - wc[None, :, :], axis=-1)
        for a, b in zip(*np.triu_indices(m, k=1)):
            if d[a, b] <= cutoff:
                g.add_edge(int(a), int(b))
    return g


def _fill_in(h, v):
    nbrs = list(h.neighbors(v))
    return sum(1 for a, b in itertools.combinations(nbrs, 2) if not h.has_edge(a, b))


def bucket_elimination_min_mixed(g: nx.Graph, self_e: dict, pair_e: dict, domain: dict):
    """Same algorithm as task0204_exact_solve_validation.bucket_elimination_min,
    generalised to PER-NODE domain sizes (that script assumes one uniform
    `n` for every variable; here the backbone-choice node has domain
    K_BACKBONE while every rotamer node has domain N_ROTAMERS) -- the
    elimination/broadcast logic is unchanged, only the shape bookkeeping."""
    h = g.copy()
    order = []
    while h.number_of_nodes():
        v = min(h.nodes, key=lambda x: _fill_in(h, x))
        order.append(v)
        nbrs = list(h.neighbors(v))
        for a, b in itertools.combinations(nbrs, 2):
            h.add_edge(a, b)
        h.remove_node(v)

    factors = [((v,), self_e[v].copy()) for v in g.nodes]
    factors += [((u, v), pair_e[(u, v)].copy()) for u, v in g.edges]
    max_factor = 0

    for v in order:
        touching = [f for f in factors if v in f[0]]
        factors = [f for f in factors if v not in f[0]]
        if not touching:
            continue
        scope = sorted({x for f in touching for x in f[0]})
        shape = tuple(domain[s] for s in scope)
        max_factor = max(max_factor, int(np.prod(shape)))
        acc = np.zeros(shape)
        for vars_, tab in touching:
            perm = np.argsort(np.asarray(vars_))
            tab_sorted = np.transpose(tab, perm)
            member = set(vars_)
            bshape = [domain[s] if s in member else 1 for s in scope]
            acc = acc + np.broadcast_to(tab_sorted.reshape(bshape), shape)
        axis = scope.index(v)
        reduced = acc.min(axis=axis)
        new_scope = tuple(x for x in scope if x != v)
        factors.append((new_scope, reduced) if new_scope else ((), reduced))

    total = 0.0
    for scope, tab in factors:
        total += float(tab) if scope == () else float(np.min(tab))
    return total, max_factor


def _random_instance(g: nx.Graph, domain: dict, rng: np.random.Generator):
    self_e = {v: rng.normal(0, 1, size=domain[v]) for v in g.nodes}
    pair_e = {(u, v): rng.normal(0, 3, size=(domain[u], domain[v])) for u, v in g.edges}
    return self_e, pair_e


def _brute_force_min_mixed(g, self_e, pair_e, domain):
    ranges = [range(domain[v]) for v in g.nodes]
    nodes = list(g.nodes)
    best = np.inf
    for assign in itertools.product(*ranges):
        a = dict(zip(nodes, assign))
        e = sum(self_e[v][a[v]] for v in g.nodes)
        e += sum(pair_e[(u, v)][a[u], a[v]] for u, v in g.edges)
        best = min(best, e)
    return float(best)


def correctness_gate() -> list:
    """Same discipline as TASK-0204's own exact-solve validation: bucket
    elimination must match brute force exactly, on small enumerable
    instances, BEFORE any real-target number is trusted -- now re-checked
    for the mixed-domain generalisation specifically (the part that
    differs from TASK-0204's own already-validated uniform-domain code)."""
    rng = np.random.default_rng(0)
    results = []
    for m in (4, 5, 6):
        g = nx.gnp_random_graph(m, 0.5, seed=1)
        g.add_node(m)  # the "backbone" hub node
        for i in range(m):
            g.add_edge(i, m)
        domain = {i: 3 for i in range(m)}
        domain[m] = 4
        se, pe = _random_instance(g, domain, rng)
        bf = _brute_force_min_mixed(g, se, pe, domain)
        be, _ = bucket_elimination_min_mixed(g, se, pe, domain)
        ok = abs(bf - be) < 1e-9
        results.append({"m": m, "brute": bf, "bucket": be, "match": bool(ok)})
        _log(f"correctness gate m={m}: brute={bf:.6f} bucket={be:.6f} match={ok}")
        assert ok, "mixed-domain bucket elimination disagrees with brute force"
    return results


def run_target(target: str) -> dict:
    t0 = time.monotonic()
    inst = build_instance(target)
    if "error" in inst:
        return inst
    window_keys_full = inst["window_keys_full"]
    cb_per_state = inst["cb_per_state"]

    out = {"target": target, "n_states": inst["n_states"], "scaling": []}
    for size in WINDOW_SIZES:
        if size > len(window_keys_full):
            continue
        wk = window_keys_full[:size]
        row = {"m": size, "cutoffs": {}}
        for cut in CB_CUTOFFS:
            g = union_graph(wk, cb_per_state, cut)
            lo, up = _treewidth_bounds(g)
            # single-static-backbone graph, for direct within-target comparison
            g_static = union_graph(wk, [cb_per_state[0]], cut)
            lo_s, up_s = _treewidth_bounds(g_static)
            row["cutoffs"][str(cut)] = {
                "edges_union": g.number_of_edges(), "tw_union_lower": lo, "tw_union_upper": up,
                "edges_static": g_static.number_of_edges(), "tw_static_lower": lo_s, "tw_static_upper": up_s,
            }
        out["scaling"].append(row)
        _log(f"{target}: m={size} " + " | ".join(
            f"cut={c}: union tw={row['cutoffs'][c]['tw_union_lower']}-{row['cutoffs'][c]['tw_union_upper']} "
            f"static tw={row['cutoffs'][c]['tw_static_lower']}-{row['cutoffs'][c]['tw_static_upper']}"
            for c in row["cutoffs"]))

    # exact-solve timing at cutoff=8A, joint (backbone-hub + rotamer) MRF
    rng = np.random.default_rng(hash(target) % (2**32))
    out["exact_solve"] = []
    for size in EXACT_SOLVE_SIZES:
        if size > len(window_keys_full):
            continue
        wk = window_keys_full[:size]
        g = union_graph(wk, cb_per_state, 8.0)
        g_hub = g.copy()
        hub = size
        g_hub.add_node(hub)
        for i in range(size):
            g_hub.add_edge(i, hub)
        domain = {i: N_ROTAMERS for i in range(size)}
        domain[hub] = K_BACKBONE
        up = _treewidth_bounds(g_hub)[1]
        projected = float(np.prod([domain[s] for s in range(size + 1)][:1]))  # placeholder, real below
        # projected max-factor size at this treewidth: (tw+1) variables in
        # the worst bucket, dominated by rotamer-domain entries (backbone
        # domain is smaller) -- conservative upper bound N_ROTAMERS**(up+1)
        projected = float(N_ROTAMERS) ** (up + 1)
        entry = {"m": size, "tw_upper_with_hub": int(up), "projected_max_factor": projected}
        if projected > MAX_FACTOR_ENTRIES:
            entry["skipped_over_budget"] = True
            _log(f"{target}: exact-solve m={size} SKIPPED, projected {projected:.3g} > budget")
        else:
            se, pe = _random_instance(g_hub, domain, rng)
            t1 = time.monotonic()
            _val, maxf = bucket_elimination_min_mixed(g_hub, se, pe, domain)
            dt = time.monotonic() - t1
            entry["wall_s"] = round(dt, 4)
            entry["max_factor_entries"] = int(maxf)
            _log(f"{target}: exact-solve m={size} tw={up} wall={dt:.3f}s max_factor={maxf}")
        out["exact_solve"].append(entry)

    out["elapsed_s"] = round(time.monotonic() - t0, 1)
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _log("=== correctness gate ===")
    gate = correctness_gate()

    results = {"_correctness_gate": gate, "targets": {}}
    for target in MANDATORY_TARGETS + CRYPTIC_TARGETS:
        _log(f"=== {target} ===")
        try:
            r = run_target(target)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            r = {"target": target, "error": f"{type(exc).__name__}: {exc}"}
        results["targets"][target] = r
        (OUT_DIR / "hardness.json").write_text(json.dumps(results, indent=1, default=str))

    _log("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
