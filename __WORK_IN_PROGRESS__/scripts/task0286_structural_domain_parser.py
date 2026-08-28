"""TASK-0286 -- user-directed follow-up to [[TASK-0284]] Part B's own
disclosed caveat: Pfam domains are sequence-family boundaries, coarser
than a real structural-domain parser (CARDIAC_MYOSIN's entire ~700-residue
motor head is ONE Pfam entry despite several real structural subdomains).
Does a geometry/graph-based structural domain parser change Part B's
FAILS verdict?

METHOD VALIDATION FIRST, per this task's own Constraint ("chosen and
sanity-checked before the real run, not swept for whichever gives the
desired answer"). Three standard, un-tuned candidate methods were built
and checked against THREE KNOWN CONTROLS on each target's own apo Cα
contact graph (`allostery.potentials.gnm_context`'s binary contact matrix,
same `enm_cutoff` used everywhere else in this register):

  KRAS_G12C (170 res)     -- textbook SINGLE domain (one Ras/G-domain fold).
                             A trustworthy parser must call this ~1 domain.
  CARDIAC_MYOSIN (704 res) -- real multiple structural subdomains within
                             one Pfam entry (upper/lower 50 kDa, converter,
                             N-terminal). A trustworthy parser should split
                             this into >=2-3.
  BCR_ABL1 (451 res)      -- textbook BILOBED kinase fold (N-lobe/C-lobe).
                             A trustworthy parser should find ~2.

1. **Modularity communities** (`networkx.greedy_modularity_communities` on
   the contact graph): at default resolution, over-splits EVERY target
   including the single-domain control (KRAS -> 5 communities of size
   12-49, no dominant single component). Swept resolution 0.3-1.0 for a
   value that behaves sanely on all three controls simultaneously: none
   does -- results are also non-monotonic in resolution (greedy heuristic,
   order-dependent), not a real signal to tune against. REJECTED.

2. **Spatial k-means + silhouette-selected k** (Cα xyz coordinates, same
   silhouette-selection idea [[TASK-0284]]'s own Finding A used for a
   very different, 1-D, genuinely bimodal quantity): KRAS's own best-k
   silhouette (k=4, 0.302) is NOT meaningfully lower than CARDIAC_MYOSIN's
   own (k=2, 0.371) or BCR_ABL1's (k=3, 0.352) -- any non-spherical single
   globular fold gets "split" with similar weak-to-moderate silhouette
   for the boring geometric reason that few real domains are perfect
   spheres. Cannot distinguish the single-domain control from the known
   multi-domain ones. REJECTED.

3. **Sequence-contiguous split-density scan** (find the single sequence
   position that maximizes mean intra-segment contact density minus
   inter-segment contact density -- the classical PUU/DomainParser
   principle, reimplemented at the simplest single-split level): dominated
   by a trivial edge effect -- the best split lands at or near the
   `minseg` boundary (cutting off a small terminal fragment) for 4 of 5
   targets tested, including BOTH the single-domain control (KRAS, split
   at residue 149/170) and the known-bilobed kinase (BCR_ABL1, split at
   430/451) -- because a small terminal fragment trivially has fewer
   contacts to the rest of the chain regardless of any real domain
   boundary. REJECTED without a materially more careful re-implementation
   (multi-split search, proper null-model normalisation, exclusion logic
   for edge artefacts) that is out of scope for a same-session ad hoc
   parser.

**None of the three passes its own control check.** This is reported as
the actual result of this task, not a stepping stone to a fourth attempt
-- per the Constraint, tuning a fourth method until one "looks right" on
the controls would itself be exactly the outcome-fishing this task was
built to avoid. A real structural-domain assignment needs a validated
tool (PUU, DomainParser2, or an ENM/hinge-detection method with a
published implementation) that is not available in this environment
(same class of gap as no DSSP/biotite, [[TASK-0284]]'s own Finding B).

CONCLUSION: [[TASK-0284]] Part B's Pfam-based result (FAILS, p=0.12,
n=32) is not overturned or confirmed by a finer structural parser --
none could be built and trusted here. Pfam remains the best available,
live-verified domain source for this register; its coarseness caveat is
now resolved as "attempted and found genuinely hard", not merely stated.
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import prody
prody.confProDy(verbosity="none")

from task0255_hop_angstrom_calibration import min_heavy_atom_dist_to_seed  # noqa: F401
from task0242_two_stage_dryrun import prep, CAND
from allostery.potentials import gnm_context

CONTROLS = {
    "KRAS_G12C": "single domain (Ras fold) -- a trustworthy parser calls this ~1",
    "CARDIAC_MYOSIN": "multiple real structural subdomains within one Pfam entry -- should split >=2-3",
    "BCR_ABL1": "textbook bilobed kinase fold -- should find ~2 (N-lobe/C-lobe)",
}


def _chain_contact_matrix(t: str):
    cfg, apo, seed, pocket = prep(t)
    coords = np.asarray(apo.coords)
    chain_ids = np.asarray(apo.chain_ids)
    ch = chain_ids[seed][0] if len(seed) else chain_ids[0]
    idx = np.where(chain_ids == ch)[0]
    sub = coords[idx]
    cut = float(cfg.get("enm_cutoff", 8.0))
    A = gnm_context(sub, cut)["A"]
    return A, sub, ch


def method_modularity(A: np.ndarray, resolution: float):
    import networkx as nx
    from networkx.algorithms.community import greedy_modularity_communities
    G = nx.from_numpy_array(A)
    comms = list(greedy_modularity_communities(G, resolution=resolution))
    return sorted((len(c) for c in comms), reverse=True)


def method_spatial_kmeans(coords: np.ndarray, k_max: int = 5):
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    best = (1, -1.0)
    for k in range(2, k_max + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(coords)
        sil = silhouette_score(coords, km.labels_)
        if sil > best[1]:
            best = (k, sil)
    return best


def method_split_density(A: np.ndarray, minseg: int = 20):
    n = A.shape[0]
    best = None
    for b in range(minseg, n - minseg):
        n1, n2 = b, n - b
        intra1 = A[:b, :b].sum() / 2
        intra2 = A[b:, b:].sum() / 2
        inter = A[:b, b:].sum()
        d1 = intra1 / (n1 * (n1 - 1) / 2)
        d2 = intra2 / (n2 * (n2 - 1) / 2)
        di = inter / (n1 * n2)
        score = (d1 + d2) / 2 - di
        if best is None or score > best[1]:
            best = (b, score)
    return best


def main():
    import yaml
    FROZEN = _ROOT / "config" / "candidate_targets_task0243.yaml"
    fz = yaml.safe_load(FROZEN.read_text()).get("targets") or {}
    CAND.update(fz)

    targets = ["KRAS_G12C", "CARDIAC_MYOSIN", "BCR_ABL1", "PTP1B", "CASPASE7"]

    print("### Method 1: modularity communities, resolution sweep ###")
    for res in (0.3, 0.5, 0.7, 1.0):
        print(f"  resolution={res}")
        for t in targets:
            A, sub, ch = _chain_contact_matrix(t)
            sizes = method_modularity(A, res)
            print(f"    {t:<16} n={len(sub):<5} -> {len(sizes)} communities  {sizes}")

    print("\n### Method 2: spatial k-means, silhouette-selected k (k=2..5) ###")
    for t in targets:
        A, sub, ch = _chain_contact_matrix(t)
        k, sil = method_spatial_kmeans(sub)
        print(f"  {t:<16} n={len(sub):<5} -> best k={k}  silhouette={sil:.3f}")

    print("\n### Method 3: sequence-contiguous split-density scan ###")
    for t in targets:
        A, sub, ch = _chain_contact_matrix(t)
        b, score = method_split_density(A)
        n = len(sub)
        edge = "AT/NEAR EDGE (artefact)" if min(b, n - b) <= 25 else "interior"
        print(f"  {t:<16} n={n:<5} -> split at {b:<5} score={score:.4f}  [{edge}]")

    print("\n### Verdict ###")
    print("  All three methods fail their own control check (see script docstring).")
    print("  No structural-parser result to compare against TASK-0284 Part B's Pfam-based Fisher exact.")
    print("  TASK-0284's FAILS verdict (p=0.12, n=32) stands, unmodified.")


if __name__ == "__main__":
    raise SystemExit(main())
