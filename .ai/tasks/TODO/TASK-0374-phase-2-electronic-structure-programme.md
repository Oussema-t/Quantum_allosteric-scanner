# TASK-0374 — Phase-2 programme: π-connectivity, the DAHP natural experiment, PCET chains, and the one arm that needs quantum hardware

- Status: TODO — **E3 scoped 2026-09-12 (Architect), ready for Implementer pending the IBM-access question below**
- Owner: **Architect/Planner** to scope (done); Implementer for E3's build
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

## E3 — scoped (2026-09-12, Architect)

Picked up per direct instruction. E3's own paragraph named two candidate targets
and one method (EWF-TrimSQD) without checking either against source — the same
discipline this task's own Gating section just enforced on the reviewer's cohort
table applies here too.

### Target: P450 3A4, not nitrite reductase — verified, not assumed

| Check | P450 3A4 | Cu nitrite reductase |
|---|---|---|
| Apo structure | **`1W0E`**, confirmed via RCSB + the original paper (Williams et al. 2004, *Science* 305:683, PMID 15256616) | Not confirmed — `1ZDS` (Yamaguchi et al.) is an **M150G mutant**, not wild-type; a clean apo/wild-type pair was not found in this pass |
| Holo structure | `1W0F` (progesterone), `1W0G` (metyrapone) — same paper, same crystal series | `1ZDS` itself is holo (6 Cu, acetamide bound) |
| Allosteric site, independently published | **Yes, directly on point**: the paper reports "an unexpected peripheral binding site... located above a phenylalanine cluster, which may be involved in the initial recognition of substrates or allosteric effectors" — a site distinct from the heme catalytic pocket, in the exact structure already in our own cohort table | Abstract discusses external ligands as "allosteric effectors" for the Type-1 Cu site, but no inter-copper coupling literature found in this pass |
| Electronic question | Heme Fe spin state (high/low-spin gates catalysis) vs. peripheral-site occupancy — single well-defined metal centre | Type-1→Type-2 Cu electron transfer — two metal centres, but the wild-type/apo pairing gap above blocks a clean apo-vs-holo comparison as scoped |

**Recommendation: P450 3A4 (`1W0E` apo / `1W0F` holo).** Clean apo/holo pair,
independently published peripheral allosteric site, matches this programme's own
distal-effector framing directly. Nitrite reductase is not dropped, but its
current entry needs curation (find a real apo/wild-type structure) before it is
usable the same way — a blocker, not a disqualification.

### Method: do not attempt to replicate EWF-TrimSQD — scope down to the same method class on open tooling

Read the sponsor's own paper (Merz, Shajan, Kaliakin et al., arXiv:2605.01138,
IBM + Cleveland Clinic + RIKEN, T4-lysozyme/trypsin, up to 94 qubits / 9200
circuits / 1.3B shots across `ibm_cleveland`/`ibm_kobe`) before scoping this,
per this task's own standing discipline. Three findings change the plan:

1. **EWF-TrimSQD is not public.** The paper names its own fragment-construction
   and TrimSQD code as "in-house"; no repository is given for either (only a
   *different*, RIKEN-authored tool, SBD, has one:
   `github.com/r-ccs-cms/sbd`). It cannot be ported the way this register
   usually ports published methods — there is nothing to port.
2. **It has never been pointed at a two-fragment coupling question.** Every
   demonstration to date is whole-protein solvation/binding energetics
   (T4-lysozyme, trypsin). E3's own observable — `ΔH_AB` between two named
   fragments — is a materially different calculation, not a re-run of the
   published one at smaller scale.
3. **The generic method underneath it — sample-based quantum diagonalization
   (SQD) — is public.** `qiskit-addon-sqd` (Qiskit's own addon,
   `github.com/Qiskit/qiskit-addon-sqd`, on PyPI) implements the base
   algorithm TrimSQD extends. Using it directly, honestly described as the
   generic method rather than the sponsor's own trimmed variant, is buildable
   here; claiming EWF-TrimSQD itself is not.

**Revised plan**: a minimal two-fragment active-space model — heme Fe +
proximal ligand vs. the peripheral Phe-cluster pocket — built classically with
PySCF (open source, the same tool the sponsor's own paper uses for its
classical reference calculations), diagonalized with `qiskit-addon-sqd`. This
is a capability claim in the **same method class** as the sponsor's published
work, scoped to what is actually buildable with public tooling — not a
replication, and the write-up must say so plainly.

### Hardware access — a real, unconfirmed gap, distinct from Braket/Classiq

The sponsor's own demonstration ran on `ibm_cleveland`/`ibm_kobe` (IBM Heron
r2, 156 qubits). **This project has never confirmed IBM Quantum access.**
[[TASK-0221]] resolved AWS Braket/Classiq as Phase-2-only, at no cost, per the
organisers — IBM Quantum is a third, separate platform that promise does not
cover. Given Cleveland Clinic's own direct collaboration with IBM on exactly
this method, access may be obtainable, but that is **unverified — a question
for Bartosz, not an assumption**, matching [[TASK-0221]]'s own pattern rather
than repeating the "assume access, get surprised at the end" mistake that
task was filed to prevent.

**Sequencing, so hardware access does not block starting**: run the two-fragment
SQD calculation on a local Qiskit Aer simulator first — feasibility and
correctness (does the fragment converge, is `ΔH_AB` even computable at this
active-space size) do not need real hardware to check. Real-hardware execution
is the stretch goal once (a) the simulator run works and (b) access is
confirmed one way or the other. This mirrors [[TASK-0182]]'s own
local-simulator-first precedent when Braket credentials were unavailable —
established practice here, not an improvisation.

### Intent Contract

- **Outcome**: a `ΔH_AB` (or equivalent electronic coupling observable) computed
  for CYP3A4's heme-Fe fragment vs. its peripheral Phe-cluster fragment, apo
  (`1W0E`) vs. holo (`1W0F`), on a local simulator at minimum; real-hardware
  execution contingent on the access question above.
- **In scope**: fragment/active-space definition and its own justification
  (orbital count, atoms included — stated up front, per this register's
  standing "state the null and the positive control before it runs"
  discipline); PySCF classical embedding; `qiskit-addon-sqd` diagonalization;
  apo-vs-holo comparison of the resulting coupling.
- **Out of scope**: any claim this replicates or matches EWF-TrimSQD's own
  published results; any advantage claim (per this task's own Constraints,
  unchanged); nitrite reductase (blocked on curation, not in this pass).
- **Positive control**: hemoglobin (`1B86`/`1IWH`/`2D60`, already in the
  cohort table) is a second, independent heme system with well-characterized
  allosteric behaviour (T-to-R spin/coordination coupling) — a natural
  second case if CYP3A4 alone is underpowered as n=1, not required to start.
- **Planned Validation**: the simulator run must reproduce a *known* quantity
  first (e.g. the heme Fe spin gap alone, without the second fragment, against
  a literature or PySCF-only reference) before the two-fragment coupling
  number is trusted — the same "does the detector work on a case with a known
  answer" discipline [[TASK-0374]]'s own E4 arm required of PCET chains.

### TODO

- [ ] Ask Bartosz: is IBM Quantum hardware access available via Cleveland
      Clinic's own collaboration, or is this platform genuinely out of reach
      for this submission? (File alongside/inside [[TASK-0221]] if that task
      is still the right home for organiser/account questions.)
- [ ] Define the heme-Fe and peripheral-Phe-cluster fragments concretely
      (residue lists, active-space orbital count) from `1W0E`/`1W0F`.
- [ ] Classical PySCF embedding for each fragment; validate the heme-alone
      spin gap against a known reference before adding the second fragment.
- [ ] `qiskit-addon-sqd` diagonalization on Aer simulator; compute `ΔH_AB`
      apo vs. holo.
- [ ] Write up as a capability claim in the sponsor's own method *class*, not
      as EWF-TrimSQD replication — state the difference explicitly.
- [ ] If simulator result is real and stable, and hardware access is
      confirmed: real-hardware run as the stretch goal, not the gate for
      reporting the simulator result.

### Dependency

- [[TASK-0372]] — the gate that closed E1/E2/E4 and left this arm standing.
- [[TASK-0221]] — organiser/account-access question pattern, reused here for
  the IBM hardware question.
- [[TASK-0182]] — local-simulator-first precedent when hardware access is
  unconfirmed.