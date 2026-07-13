"""Classical + external baseline scores (TASK-0011).

No notebook precedent -- net-new per this task's own Source note. Ports
`PLAN.md` Phase 2's baseline requirement ("must beat the right baselines...
random residues, non-functional surface pockets, AND degree/betweenness
centrality" -- "a ceiling that node degree also reaches is structure, not
your method") and Phase 4's external-predictor column
(`ALGORITHM_REGISTER.md` Sec.F).

Each classical baseline returns a per-residue score array with the same
shape/orientation as the main method's occupation scores, so it plugs into
the same `metrics.auc`/`report.hit_list` pipeline unmodified -- this module
produces scores, it does not itself compute AUC or fetch pocket labels
(that composition is the caller's job, per TASK-0004's dependency note).

External-tool wrappers never raise -- mirrors `backend/rcsb_extract.py`'s
`{"error": ...}` convention, since this module runs in CI/dev environments
without guaranteed network access or the fpocket binary installed.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from .hamiltonians import contact_matrix


# ---------------------------------------------------------------------------
# Classical baselines
# ---------------------------------------------------------------------------

def random_baseline(n: int, seed: int | None = None) -> np.ndarray:
    """Null-signal baseline: uniform random score per residue, (n,)."""
    rng = np.random.default_rng(seed)
    return rng.random(n)


def surface_baseline(coords: np.ndarray, cutoff: float = 10.0) -> np.ndarray:
    """Non-functional surface-pocket score: low-contact-degree residues
    (more solvent-exposed) score higher, independent of any pocket label.

    Deliberately naive/positionless -- stands in for "any surface patch,"
    per PLAN.md's "must beat...non-functional surface pockets" requirement.
    Shape mirrors `backend/analysis.py::V_terminal`'s exposure-proxy
    (`1 - degree/rsa_cut`, clipped) without the terminus term; simplified
    here to bare `-degree` since only rank order matters for this baseline,
    not a bounded [0,1] value.
    """
    A = contact_matrix(coords, cutoff=cutoff, weight="binary")
    degree = A.sum(axis=1)
    return -degree


def degree_centrality(coords: np.ndarray, cutoff: float = 10.0) -> np.ndarray:
    """Raw contact-graph degree per residue, (n,)."""
    A = contact_matrix(coords, cutoff=cutoff, weight="binary")
    return A.sum(axis=1)


def betweenness_centrality(coords: np.ndarray, cutoff: float = 10.0) -> np.ndarray:
    """Betweenness centrality on the unweighted contact graph, (n,).

    Disconnected residues (no path to most of the graph) get a low but
    well-defined betweenness from networkx -- not NaN/error -- so this is
    safe to call on any contact graph this package builds, including the
    disconnected synthetic cases `diagnostics.py`'s tests use.
    """
    import networkx as nx

    A = contact_matrix(coords, cutoff=cutoff, weight="binary")
    G = nx.from_numpy_array(A)
    bc = nx.betweenness_centrality(G)
    return np.array([bc[i] for i in range(len(coords))])


# ---------------------------------------------------------------------------
# Proximity-to-seed baselines (TASK-0094, REVIEW-2026-07-13 finding P1-A)
# ---------------------------------------------------------------------------
#
# The propagator is always seeded at the functional/active-site set
# (`analysis.py`'s `source` argument), and the pocket label is "residues
# near the allosteric ligand, minus the active site" -- so a score that
# does nothing but measure proximity-to-seed already reproduces most of
# the signal (REVIEW-2026-07-13, real numbers on a synthetic 170-residue
# globule, cutoff 8.0 A, 6-residue seed cluster):
#   Spearman(time_averaged_ctqw occupation, -Euclidean distance from seed)
#     = +0.853; Spearman(CTQW, -hop distance) = +0.880; on a pocket placed
#   *adjacent* to the seed, the pure distance baseline (AUC 0.966) beats
#   CTQW itself (0.914). Before this task, `baselines.py` had no proximity
#   baseline at all -- `classify_failure`'s only floor was
#   `degree_centrality`, which is not the confounding variable. These two
#   functions are that floor; see `diagnostics.classify_failure`'s
#   `floor_scores` and `scripts/run_challenge.py`'s floor computation for
#   where they are actually applied.

def euclid_from_seed_centroid(coords: np.ndarray, source) -> np.ndarray:
    """Negative Euclidean distance from the seed-residue centroid, (n,).

    `source` is a scalar index or a sequence of indices (this package's
    standard multi-index seed convention, `propagators.py`/`pathways.py`'s
    `_source_indices`) -- the centroid of all seed residues, not just the
    first. Negated so "closer to the seed = higher score", matching this
    module's existing convention (`surface_baseline`'s `-degree`).
    """
    idx = np.atleast_1d(np.asarray(source, dtype=int))
    centroid = coords[idx].mean(axis=0)
    dist = np.linalg.norm(coords - centroid, axis=1)
    return -dist


def hop_from_seed(coords: np.ndarray, source, cutoff: float = 10.0) -> np.ndarray:
    """Negative graph-hop (BFS) distance from the seed set, on the same
    binary contact-graph convention this module's other centrality
    baselines use (`degree_centrality`/`betweenness_centrality`), (n,).

    BFS logic ported from (not imported -- private helper, `select.py`'s
    own module boundary) `select.py::_hop_distances_from_source`, adapted
    to this module's `coords`+`cutoff` signature (matching its siblings)
    and to a multi-index seed (BFS from every seed residue at once, so
    hop distance is "nearest seed member", not "distance from one
    representative index"). Unreachable residues (a disconnected
    component) get a hop distance of `n_residues + 1` -- a finite,
    well-defined penalty rather than -1/inf/NaN, so this stays directly
    usable by `metrics.auc` without a caller-side NaN check, unlike
    `_hop_distances_from_source`'s `-1` convention (that function is
    consumed by `ballistic_exponent`, which explicitly excludes
    unreachable nodes itself; this one has no such caller, so it cannot
    rely on the same downstream handling).
    """
    import networkx as nx

    idx = np.atleast_1d(np.asarray(source, dtype=int))
    A = contact_matrix(coords, cutoff=cutoff, weight="binary")
    G = nx.from_numpy_array(A)
    n = len(coords)
    dist = np.full(n, float(n + 1))
    for i in idx.tolist():
        for node, d in nx.single_source_shortest_path_length(G, i).items():
            if d < dist[node]:
                dist[node] = float(d)
    return -dist


# ---------------------------------------------------------------------------
# External baselines -- fpocket (real wrapper; binary-based, apo-computable)
# ---------------------------------------------------------------------------

def fpocket_baseline(pdb_path: str, timeout: float = 120.0) -> dict:
    """Run fpocket (apo-computable cavity-openness score,
    `ALGORITHM_REGISTER.md` Sec.F, rated 4/4) on a PDB file.

    Returns {"pockets": [{"id": int, "score": float,
    "druggability_score": float}, ...]} on success, or {"error": "..."} if
    the binary isn't on PATH, the input file is missing, the subprocess
    fails/times out, or its output can't be parsed -- never raises. The
    binary is not installed in this repo's dev/CI environment, so the
    graceful-degradation path (not a live fpocket run) is what this
    module's own tests actually exercise; `_parse_fpocket_info` is tested
    separately against a synthetic info-file string so the parse logic
    itself has real coverage independent of binary availability.
    """
    if shutil.which("fpocket") is None:
        return {"error": "fpocket binary not found on PATH"}

    pdb_path = Path(pdb_path)
    if not pdb_path.exists():
        return {"error": f"pdb file not found: {pdb_path}"}

    try:
        with tempfile.TemporaryDirectory() as tmp:
            local_pdb = Path(tmp) / pdb_path.name
            local_pdb.write_bytes(pdb_path.read_bytes())
            result = subprocess.run(
                ["fpocket", "-f", str(local_pdb)],
                cwd=tmp, capture_output=True, text=True, timeout=timeout,
            )
            if result.returncode != 0:
                return {"error": f"fpocket exited {result.returncode}: {result.stderr.strip()[:500]}"}

            info_file = Path(tmp) / f"{local_pdb.stem}_out" / f"{local_pdb.stem}_info.txt"
            if not info_file.exists():
                return {"error": f"fpocket produced no info file at {info_file}"}

            return {"pockets": _parse_fpocket_info(info_file.read_text())}
    except subprocess.TimeoutExpired:
        return {"error": f"fpocket timed out after {timeout}s"}
    except Exception as e:
        return {"error": f"fpocket_baseline: {e}"}


def _parse_fpocket_info(text: str) -> list:
    """Best-effort parse of fpocket's `<name>_info.txt` format:

        Pocket 1 :
            Score :  0.523
            Druggability Score :  0.712
            ...

    Not verified against a live fpocket install (unavailable in this
    sandbox) -- a format change in a different fpocket version raises
    inside this function, which `fpocket_baseline`'s own try/except turns
    into a graceful `{"error": ...}` rather than a silently wrong result.
    """
    pockets = []
    blocks = re.split(r"^Pocket (\d+) :\s*$", text, flags=re.MULTILINE)[1:]
    for pocket_id, body in zip(blocks[0::2], blocks[1::2]):
        score_m = re.search(r"^\s*Score\s*:\s*([-\d.]+)", body, flags=re.MULTILINE)
        drug_m = re.search(r"^\s*Druggability Score\s*:\s*([-\d.]+)", body, flags=re.MULTILINE)
        pockets.append({
            "id": int(pocket_id),
            "score": float(score_m.group(1)) if score_m else None,
            "druggability_score": float(drug_m.group(1)) if drug_m else None,
        })
    return pockets


# ---------------------------------------------------------------------------
# External baselines -- not yet wired (see Open Questions)
# ---------------------------------------------------------------------------

_NOT_WIRED = (
    "{name} not yet wired to a verified endpoint -- ALGORITHM_REGISTER.md "
    "rates it but does not specify a concrete API/local-inference contract, "
    "and this is deliberately left unguessed rather than shipping an "
    "unverified integration (see TASK-0011 Open Questions)."
)


def pocketminer_baseline(coords: np.ndarray, **kwargs) -> dict:
    """PocketMiner (GNN cryptic-pocket predictor, `ALGORITHM_REGISTER.md`
    Sec.F, rated 4/4) cross-check baseline -- not yet wired, see
    `_NOT_WIRED`. Accepts the same `coords` shape the other baselines do
    so it's a drop-in once a provider is chosen; currently ignores its
    arguments and always returns the same error dict (deterministic,
    hence directly unit-testable without a network mock)."""
    return {"error": _NOT_WIRED.format(name="pocketminer_baseline")}


def proteinlens_baseline(coords: np.ndarray, **kwargs) -> dict:
    """ProteinLens (bond-to-bond propensity web server,
    `ALGORITHM_REGISTER.md` Sec.F, rated 4/4) cross-check baseline -- not
    yet wired, see `pocketminer_baseline`'s docstring (same status)."""
    return {"error": _NOT_WIRED.format(name="proteinlens_baseline")}
