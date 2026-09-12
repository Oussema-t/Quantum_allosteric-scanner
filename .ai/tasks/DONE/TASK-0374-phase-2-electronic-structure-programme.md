# TASK-0374 — Phase-2 programme: π-connectivity, the DAHP natural experiment, PCET chains, and the one arm that needs quantum hardware

- Status: Done — **E3 scoped (Architect) then attempted (Implementer), 2026-09-12: a real capability gap found (SCF non-convergence + a venv/jaxlib blocker for SQD), `ΔH_AB` not computed. Concrete next steps recorded below, not a finished result.**
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

**Provenance, disclosed by its own author on 2026-09-12 and weaker than it looked**: the tiering is **keyword matching on the catalogue's `protein` name field plus the reviewer's own knowledge of which cofactors those enzymes carry**. **No PDB was fetched and it was never checked against HETATM records.** "Glycogen phosphorylase has PLP" is correct, but it is knowledge, not measurement — and several of these enzymes are deposited *without* their cofactor, so the tier can be right about the enzyme and wrong about the entry.

**Do not verify all 42.** With E0 negative the tiering's only remaining job is picking one or two E3 targets, and at n=2 it does not need to be right in aggregate. **Verify the entries E3 actually uses and skip the rest** — the reviewer's own recommendation, and it is the right one.

## The arms

*Read the Gating section below first: three of these four are closed.*

### E1 — π-stack connectivity, not residue counts — **prior lowered 2026-09-12, not closed on evidence**

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

- **E1 (π-stack connectivity) — prior substantially lowered, premise NOT
  falsified.** *Corrected 2026-09-12 after the external reviewer flagged the
  logical gap, which was real and ours.* E1 was scoped as **connectivity**, not
  composition: whether a π-stack graph connects the two sites when the Cα graph
  does not. **Those are separable** — a protein can have background-level
  aromatic content and still have a connected ring path between distant sites,
  because path existence depends on geometric arrangement rather than count. So
  [[HYP-P29]] lowers E1's prior substantially and does **not** refute it. Not
  reopened, and the reviewer does not argue to reopen it: with composition
  negative, matched-subset nulls get harder and E3 is the better use of Phase 2.
  **But the register must not claim more than it measured.**
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

**Do not resurrect E2/E4 on the strength of the raw 15.6% figure**, and do not describe E1 as refuted. It is real
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

---

## Reviewer's Q1 answer, and where our own check contradicts it (2026-09-12)

**The reviewer recommends nitrite reductase first, P450 as the stated stretch.**
Their reasoning is good and worth recording in full, because most of it survives:

> **Cu nitrite reductase (`1ZDS`), primary.** Donor–acceptor pair unambiguous —
> Type-1 Cu to Type-2 Cu, ~12.5 Å, bridged by the adjacent Cys–His pair. `H_AB`
> for that transfer has published experimental rate constants and decades of
> classical pathway calculations to check against. Cu(II) is d⁹ — one unpaired
> electron, the simplest open-shell case available. And ASBench's own allosteric
> annotation (His60, His95, Trp144, His145) sits in the bridge region, so the site
> you would fragment is the site the catalogue names.
>
> **P450 3A4 (`1W0F`), stretch.** Fe(III) heme is d⁵ with a dense low-lying spin
> manifold and strong static correlation — simultaneously the best advertisement
> for the method and the likeliest place to fail to converge with nothing to show.

**Their framing of the real trade is the part to keep**, and the Architect's
target table does not address it:

> Nitrite reductase has ground truth and no pharmacological relevance; P450 3A4
> has enormous pharmacological relevance and no ground truth. For a Cleveland
> Clinic panel that trade is not obviously in nitrite reductase's favour on
> Impact.

### But the Architect's verification blocks their primary choice

The Architect checked both entries against source rather than reasoning from
enzyme identity, and found two facts the reviewer's recommendation does not
survive unchanged:

- **`1ZDS` is an M150G mutant, not wild-type.**
- **`1ZDS` is itself holo** (6 Cu, acetamide bound), and no clean apo/wild-type
  pair was found in that pass.

E3's observable is `ΔH_AB` **apo vs holo**. Without an apo/wild-type partner,
nitrite reductase cannot carry the comparison as scoped — however good its ground
truth is. **That is a blocker, not a disqualification**: the entry needs curation,
not abandonment.

**This is the third time in a week that an unverified structure recommendation has
not survived contact with the deposition** — after `8S8C` (suggested as apo, is
holo) and `8QYR` (labelled apo by us, is the holo validation structure). The
pattern is now strong enough to state as a rule: **a PDB ID is a claim until
someone opens the entry.**

### Recommendation, taking both inputs

Adopt the reviewer's *structure* with the Architect's *ordering*:

1. **Pre-register both targets**, as they suggest.
2. **Run P450 3A4 (`1W0E` apo / `1W0F` holo) first** — not because it is the
   better science question, but because it is the one with a verified apo/holo
   pair and an independently published peripheral allosteric site in the exact
   structure already in our cohort.
3. **State in the text that the pipeline is target-agnostic**, with nitrite
   reductase named as the validatable case **pending curation of a wild-type apo
   partner** — which is an honest disclosure of exactly why the order is what it
   is, not a preference dressed as a decision.
4. Carry the reviewer's own caveat about 3A4 unchanged: d⁵ with strong static
   correlation is where classical DFT genuinely struggles **and** where a
   non-converged run leaves us with nothing to show. That risk is stated in
   advance, not discovered.

**Verify only these two entries' HETATM records**, per the tiering note above.

## Reusable asset from a negative result (2026-09-12)

The reviewer asks that one number survive the dead hypothesis, and they are right
to:

> **The 12.8% figure is worth keeping as infrastructure, separate from the dead
> hypothesis.** Any future composition test against pockets in this cohort should
> use it rather than bulk frequency. It is a small reusable asset produced by a
> negative result, and it is the kind of thing that gets re-derived expensively
> later if it isn't filed now.

**Recorded here and in [[HYP-P29]]: the matched baseline for aromatic content at
ligand-binding pockets in the ASBench cohort is 12.76% (F/Y/W/H, active sites,
n=2422 residues across 79 proteins), not the ~10.2% bulk-protein frequency.** Any
future composition test on this cohort uses the former. Source artifact:
`results/tasks/0372_aromatic_enrichment_gate/aromatic_enrichment_gate.json`,
key `planned_validation_raw_reproduction.act_aromatic_frac`.

## Done (2026-09-12, Implementer A) — E3 attempted, a real capability gap found, not the coupling number

Picked up after E3 was scoped (above). No blocker before pickup (claim
released cleanly by the prior Reviewer-thread session). Script:
`scripts/task0374_e3_electronic_coupling.py`.

### What was built and verified, not assumed

- **`pyscf`, `qiskit-addon-sqd` installed** (neither was present before
  this task).
- **Geometry, checked directly against the deposited structures, not
  the paper's own description alone**: both `1W0E` (apo) and `1W0F`
  (holo) are 5-coordinate at Fe — 4 porphyrin N (2.03-2.07 Å) + Cys442
  Sγ (2.41-2.47 Å per structure) — **no axial water within 3.2 Å in
  either structure.** This corrects the Architect's own scoping
  paragraph above, which carried over the field's general "apo =
  6-coordinate low-spin, substrate-bound = 5-coordinate high-spin"
  picture without checking it against this specific pair — checked
  here, and it does not hold for `1W0E`/`1W0F`: the apo/holo difference
  in this pair is not a coordination-number change at Fe.
- **Fragment A (heme site)**: the deposited `HEM` group (43 atoms,
  unmodified) + Cys442's own thiolate, capped at the Sγ-Cβ bond with a
  link H (1.34 Å) — the field's own standard minimal P450 model,
  Fe(porphine)(SH).
- **Fragment B (peripheral site)**: PHE213/PHE219/PHE220's aromatic
  rings — ASBench's own annotated `allosteric_residues` for `1W0F`,
  restricted to the aromatic subset (ASP214/ASP217/VAL240 excluded, not
  part of the π-system this observable is about) — each capped at
  Cγ-Cβ with a link H, a toluene-like model per residue.
- Both fragments taken from each structure's own real coordinates
  (apo from `1W0E`, holo from `1W0F` independently), not superposed or
  idealised.

### What was attempted, and where it stopped

**Planned Validation (this task's own requirement): get the heme-alone
fragment to a converged mean-field reference before trusting an active
space built on it.** Tried, in order, each a standard, documented
remedy for exactly this failure mode, not an ad hoc guess:

1. **ROHF**, 3 spin states (doublet/quartet/sextet), `level_shift=0.2`,
   `max_cycle=150`: **none converged**, ~535-541s each (apo structure;
   holo not reached).
2. **UHF**, stronger aids (`level_shift=0.5`, `init_guess='atom'`,
   `diis_start_cycle=1`), sextet only: **did not converge** in 458s;
   spin contamination severe (`S²=20.5` vs. an ideal ≈9 for a clean
   sextet).
3. **UKS/B3LYP** (DFT in place of bare HF — standard practice for
   transition-metal active-space work, since HF's self-interaction
   error is a well-documented source of exactly this class of
   convergence failure for near-degenerate metal d-orbitals), sextet
   only: **still did not converge**, in 1479s (25 min) — slower, not
   faster, and still spin-contaminated (`S²=13.2` vs. ideal ≈7.3).

**Stopped here rather than keep iterating indefinitely.** Total
compute spent on convergence attempts alone: ~61 minutes, zero
converged results, escalating (not shrinking) cost per attempt. This
is reported as a capability finding, not smoothed into "in progress":
**a minimal-basis (STO-3G), single-determinant treatment of the
Fe-porphyrin-thiolate fragment does not converge on this hardware with
the standard remedies tried.** The general difficulty of describing
iron-heme electronic structure at the single-reference level — near-
degenerate d-orbitals, genuine multireference character — is
independently documented in the literature (Radoń, M.; Pierloot, K.
"Binding of CO, NO, and O2 to Heme by Density Functional and
Multireference ab Initio Calculations." *J. Phys. Chem. A* **2008**,
*112*, 11824-11832. DOI: [10.1021/jp806075b](https://doi.org/10.1021/jp806075b),
live-verified via Crossref) — cited as the source of the general
principle this task's own convergence failure is consistent with, not
as the source of any number here; this task's own failure was not
compared against that paper's specific results.

**A second, independent blocker, found and disclosed, not hidden:**
`qiskit_addon_sqd.fermion` imports `jax`; this repo's `.venv` is an
x86_64 (Rosetta) virtualenv on Apple Silicon (confirmed directly:
`.venv/bin/python3.13` is a Mach-O x86_64 executable), and the `jaxlib`
wheel pip installed into it was built with AVX instructions Rosetta
does not emulate — `qiskit_addon_sqd.fermion` cannot be imported at
all in this environment (`RuntimeError: ... built using AVX
instructions, which your CPU and/or operating system do not support`).
This is unrelated to the convergence problem above and would block a
real SQD run even if the classical reference converged. Fixing it
needs a native arm64 `.venv` (or a dedicated arm64 virtualenv for this
one dependency) — a shared-infrastructure change affecting every
concurrent thread's own `.venv`, out of this task's own scope to make
unilaterally.

**A separate, useful process finding from the same investigation**:
running `claim.py`'s `commit-guard`/`stage` subcommands with this same
x86_64 `.venv` activated breaks their internal `git diff --cached` call
for the identical reason (macOS's fat-binary architecture inheritance
execs `git`'s x86_64 slice from an x86_64 parent, which then needs the
same missing x86_64 `libxcrun.dylib`) — already worked around directly
in [[TASK-0372]]'s own commit and confirmed fixed by not having `.venv`
active for `claim.py` calls specifically.

### Consequence

- **`ΔH_AB` itself was not computed** — neither the Löwdin-Fock-matrix
  estimate (needs the same converged mean-field step) nor the
  SQD-based version (blocked twice over, independently).
- **This is not a null result about the electronic coupling** — no
  coupling was measured, positive or negative. It is a **capability/
  feasibility finding**: this exact minimal model, at this basis level,
  on this hardware, with these standard remedies, does not converge —
  which is itself the kind of thing this register states rather than
  silently retries forever.
- **Recommended next steps, concretely, for whoever picks this up**:
  (a) a native arm64 `.venv` (fixes the SQD import outright, and
  removes the Rosetta/AVX performance penalty that made each
  convergence attempt 8-25 minutes); (b) a larger basis (STO-3G is
  known to be a poor choice for transition-metal spin-state work) with
  a properly pre-converged initial guess (e.g. from a published
  heme-thiolate calculation, or PySCF's own `chkfile`-based restart
  from a smaller/simpler analog) rather than the default `minao` guess;
  (c) PySCF's `scf.newton()` second-order SCF solver, the standard
  remedy for exactly this failure mode, not yet tried here.

### Not done / explicitly out of scope

- Real hardware execution — moot until the simulator path itself works.
- Any claim of quantum advantage or capability beyond "attempted,
  documented where it stopped" (per this task's own Constraints).
- Nitrite reductase — already blocked on curation (a real apo/wild-type
  pair), unchanged by this pass.

**Files**: `__WORK_IN_PROGRESS__/scripts/task0374_e3_electronic_coupling.py`,
`__WORK_IN_PROGRESS__/results/tasks/0374_e3_electronic_coupling/run_log.txt`
(partial — the run was stopped once the convergence pattern was clear,
not once it finished, per the reasoning above).
