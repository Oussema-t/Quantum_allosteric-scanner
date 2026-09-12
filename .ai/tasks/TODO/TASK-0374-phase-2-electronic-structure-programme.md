# TASK-0374 — Phase-2 programme: π-connectivity, the DAHP natural experiment, PCET chains, and the one arm that needs quantum hardware

- Status: TODO
- Owner: **Architect/Planner** to scope; Implementers per arm
- Priority: **Phase-2 planning. Gated on [[TASK-0372]]; do not start before 2026-09-15.**
- Filed: 2026-09-12 by Reviewer thread (id via `claim.py reserve-next`)
- Source: external reviewer discussion, 2026-09-11/12
- Related: [[TASK-0372]], [[TASK-0373]], [[TASK-0371]], [[TASK-0157]]

## The cohort already exists in our own repository

The reviewer screened ASBench's 118 curated entries and found **42 (36%) carrying
a cofactor or effector where electronic structure is plausibly load-bearing**:

| Tier | n | Examples |
|---|---|---|
| Metal/redox centre | 9 | P450 3A4 (`1W0F`), Cu nitrite reductase (`1ZDS`), hemoglobin (`1B86`/`1IWH`/`2D60`), ribonucleotide reductase (`2R1R`/`3R1R`), Trp 2,3-dioxygenase (`2NW8`) |
| PLP/ThDP cofactor | 9 | Glycogen phosphorylase ×6, ornithine decarboxylase, indole-3-pyruvate decarboxylase |
| NAD(P)/nicotinamide | 10 | IDH1 (`4JA8`), glutamate dehydrogenase ×4, GAPDH, malic enzyme |
| **Aromatic *effector*** | 13 | DAHP synthase Phe-sensitive (`1KFL`) and Tyr-inhibited (`1OF6`); prephenate dehydratase; anthranilate synthase |
| Heme peroxidase | 1 | COX-2 (`3QH0`) |

**Not verified by this thread.** The tier assignment is the reviewer's reading of
the catalogue; confirm entry-by-entry before any of it is quoted. This register
has twice been caught repeating a number instead of checking it ([[TASK-0348]],
[[TASK-0366]]).

## The arms

### E1 — π-stack connectivity, not residue counts

Build a second graph on **aromatic ring centroids**, edges weighted by real
stacking geometry (centroid distance ≤ 7 Å, interplanar angle, offset). Ask
whether the allosteric and active sites are connected in *that* graph when they
are far apart in the Cα contact graph.

**The existing CTQW machinery runs on it unchanged** — but the graph now encodes
what the Cα graph threw away, which is the whole point of [[TASK-0373]]'s reframe.
Null: random aromatic subsets matched on count **and burial**.

### E2 — DAHP synthase as a built-in natural experiment

`1KFL` (Phe-sensitive) and `1OF6` (Tyr-inhibited) bind effectors differing by
**one hydroxyl**, and the isoforms are effector-specific. If allostery here were
purely steric, that hydroxyl should not matter much. Compute the electronic
coupling of the bound effector ring to the nearest protein aromatics in both and
ask whether the difference tracks the specificity.

**Sharpest item in the list, and n = 2.** Treat as hypothesis generation; it
cannot carry a conclusion alone.

### E3 — the arm that genuinely needs quantum hardware

One target with a small, well-defined electronic question — P450 3A4 spin-state
gating, or the Cu–Cu coupling in nitrite reductase — fragmented the way
EWF-TrimSQD does. **Observable: the electronic coupling matrix element `ΔH_AB`
between the allosteric-site fragment and the active-site fragment, apo vs holo.**

This is a genuine many-body electronic-structure calculation at a size fragment
based quantum methods now handle, **and it cannot be done by any force field.**

**This is the answer to [[TASK-0371]]'s open strategic gap** — "Phase 2 contains
zero quantum execution" — and it is a far better answer than a token hardware run,
because the quantum step is doing work no classical alternative does, rather than
re-running something we already showed adds nothing. **Still not an advantage
claim**: it is a capability claim, and the distinction must survive into any text.

### E4 — PCET pathway search

His sits at 3.5% at allosteric sites. Enumerate hydrogen-bond chains connecting
allosteric to active sites through titratable residues; test whether such chains
exist more often than in matched decoys. **Ribonucleotide reductase (`2R1R`/`3R1R`)
is the textbook radical-transfer case and is already in the cohort** — it is the
positive control that says whether the detector works at all, and no arm should
run without it.

## Gating

**[[TASK-0372]] (E0) is a hard gate on E1, E2 and E4.** If aromatic enrichment is
burial plus ligand contact, the premise behind the π-connectivity arms is gone and
they should not run.

**E3 is only partly gated.** Its question — does ligand binding change the
electronic coupling between two distant fragments — stands whether or not
residue-level aromatic counts are enriched. Scope it separately if E0 fails.

## Constraints

- **No claim of quantum advantage**, in any arm, under any framing.
- Every borrowed number and every cohort assignment is **unverified by us** until
  checked against its own source.
- Each arm needs its null and its positive control stated **before** it runs —
  this register's standing discipline, and the reason its negatives are credible.
- The honest ceiling is stated up front: **E0 may kill most of this**, and a 1.5×
  enrichment fully explained by burial and ligand contact is a clean negative that
  gets recorded like every other.
