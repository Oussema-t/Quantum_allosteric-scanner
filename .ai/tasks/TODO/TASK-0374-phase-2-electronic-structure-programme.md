# TASK-0374 — Phase-2 programme: π-connectivity, the DAHP natural experiment, PCET chains, and the one arm that needs quantum hardware

- Status: TODO
- Owner: **Architect/Planner** to scope; Implementers per arm
- Priority: **Phase-2 planning — reduced to E3 alone. The gate fired: [[TASK-0372]] returned a clean negative on 2026-09-12 and E1/E2/E4 are closed with it.**
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

*Read the Gating section below first: three of these four are closed.*

### E1 — π-stack connectivity, not residue counts — **CLOSED 2026-09-12**

Build a second graph on **aromatic ring centroids**, edges weighted by real
stacking geometry (centroid distance ≤ 7 Å, interplanar angle, offset). Ask
whether the allosteric and active sites are connected in *that* graph when they
are far apart in the Cα contact graph.

**The existing CTQW machinery runs on it unchanged** — but the graph now encodes
what the Cα graph threw away, which is the whole point of [[TASK-0373]]'s reframe.
Null: random aromatic subsets matched on count **and burial**.

### E2 — DAHP synthase as a built-in natural experiment — **CLOSED 2026-09-12**

`1KFL` (Phe-sensitive) and `1OF6` (Tyr-inhibited) bind effectors differing by
**one hydroxyl**, and the isoforms are effector-specific. If allostery here were
purely steric, that hydroxyl should not matter much. Compute the electronic
coupling of the bound effector ring to the nearest protein aromatics in both and
ask whether the difference tracks the specificity.

**Sharpest item in the list, and n = 2.** Treat as hypothesis generation; it
cannot carry a conclusion alone.

### E3 — the arm that genuinely needs quantum hardware — **the only surviving arm**

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

### E4 — PCET pathway search — **CLOSED 2026-09-12**

His sits at 3.5% at allosteric sites. Enumerate hydrogen-bond chains connecting
allosteric to active sites through titratable residues; test whether such chains
exist more often than in matched decoys. **Ribonucleotide reductase (`2R1R`/`3R1R`)
is the textbook radical-transfer case and is already in the cohort** — it is the
positive control that says whether the detector works at all, and no arm should
run without it.

## Gating — RESOLVED 2026-09-12: the gate fired, and E1/E2/E4 are closed

[[TASK-0372]] ran the E0 gate on the full 118-entry cohort and returned **a clean
negative**. Verified against `results/tasks/0372_aromatic_enrichment_gate/aromatic_enrichment_gate.json`:

| stratum | proteins | allosteric | active site | cluster-p |
|---|---|---|---|---|
| all residues | 79 | 15.6% | 12.8% | **0.856** |
| ligand-contacting | 49 | 16.5% | 14.0% | **0.515** |
| non-contacting | 20 | 11.7% | 11.9% | **0.406** |

Not significant in any stratum, burial-residualised and paired within protein. The
non-contacting stratum's point estimate reverses sign, at n=20 with exact
sign-flip enumeration — correctly reported there as not a finding.

**It also found a third confound neither the reviewer nor this filing named.**
The validation gate reproduced the reviewer's own raw figure (0.15625 against their
0.157), then measured the matched baseline: **active sites are themselves aromatic
enriched at 12.8%**, not the 10.2% bulk-protein background the 1.54× was computed
against. They bind small molecules too. **About half the headline was the wrong
baseline before burial or ligand contact were considered at all** — which is
exactly why the within-protein pairing was made mandatory rather than optional.

### Consequence

- **E1 (π-stack connectivity) — CLOSED.** Its premise was that aromatic content
  marks allosteric sites. It does not.
- **E2 (DAHP synthase) — CLOSED as scoped here.** It was an n=2 illustration of a
  general effect that does not exist. A separate, differently-motivated task could
  still ask why those isoforms are effector-specific, but it would not be this
  programme's arm and must not inherit its framing.
- **E4 (PCET chains) — CLOSED.** The His 3.5% figure that motivated it is part of
  the same composition signal that just failed.
- **E3 — SURVIVES, and is now the whole task.** Its question never depended on
  residue-level aromatic counts, which is why this filing scoped it separately in
  advance. That separation is the reason a negative gate cost us three arms
  instead of four.

**Do not resurrect E1/E2/E4 on the strength of the raw 15.6% figure.** It is real
and it is not allostery-specific, and [[HYP-P29]] records exactly that.

## Constraints

- **No claim of quantum advantage**, in any arm, under any framing.
- Every borrowed number and every cohort assignment is **unverified by us** until
  checked against its own source.
- Each arm needs its null and its positive control stated **before** it runs —
  this register's standing discipline, and the reason its negatives are credible.
- The honest ceiling is stated up front: **E0 may kill most of this**, and a 1.5×
  enrichment fully explained by burial and ligand contact is a clean negative that
  gets recorded like every other.


---

## Status, 2026-09-12 (Reviewer) — what this does and does not change

**The submission needs no edit.** [[TASK-0373]]'s reframe was written for this
outcome: it says the contact graph cannot represent a π system and states
explicitly that *we have not measured electronic coupling*. It never borrowed the
enrichment figure, so a negative gate leaves it standing exactly as shipped.

**[[TASK-0371]]'s open strategic gap is now E3 or nothing.** The recommendation
there — E3 over a token Braket/Classiq run of our own walk — is unchanged and, if
anything, sharper: E3 is the only arm left that computes something no classical
method can, and the alternative remains re-executing a null we already published.

**Worth sending back to the external reviewer**: the **12.8% active-site figure**.
They proposed the paired control themselves and were right to. The number shows
why a cross-protein background could never have answered the question, which is a
more useful reply than "it didn't survive" — and it is their idea that produced
the cleanest negative in the register this week.

**Honest note on where this leaves the route.** The reviewer's own caveat was that
E0 might kill it, and it did. That is the system working: a pre-registered gate,
run before the expensive arms, returning the outcome it predicted was most likely.
The reframe that made this worth exploring survives on its own argument, not on
this measurement.