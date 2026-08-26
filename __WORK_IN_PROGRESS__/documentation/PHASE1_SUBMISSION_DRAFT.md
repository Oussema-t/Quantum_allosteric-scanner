# Quantum Allosteric Scanner — Phase 1 Proposal (DRAFT v0.1)

**Team AuraQu · Cleveland Clinic Global Quantum + AI Challenge 2026**

> **Status: first draft, 2026-08-13.** Narrative framing (A′), formally
> decided by Bartosz 2026-08-13 (see [[TASK-0184]]'s own record). **First
> numbers-audit pass complete, 2026-08-13** — every internal figure traced
> against `RESULTS.md`/its source task file; one critical undisclosed
> caveat found and fixed (Finding 4, KRAS_G12C's apo structure 4OBE is
> wild-type, not G12C), one factual error corrected (§2.4, TASK-0168 *was*
> run on PTP1B and contradicted, not "untested"), one provenance fix
> (§2.2's interacting-multi-particle row is an external-panel measurement,
> not this team's own), and one `[TBD]` filled (§1's fpocket pinned
> values). **Still outstanding, not yet auditable against `RESULTS.md`**:
> the Amor et al. 2016 / Wu et al. 2022 external literature percentages
> (§3c — needs a citation-accuracy check, not a RESULTS.md trace) and the
> §5 demo P@5/floor/baseline numbers (need a live re-run against `main`,
> not a document trace — [[TASK-0184]]'s own flagged fix). Remaining
> `[TBD]`s marked below.
>
> **2026-08-14 update ([[TASK-0217.003]])**: §2.4 rewritten — the register's
> one surviving positive (PTP1B `dcc_low`) was seeded via an undisclosed
> topological-proxy fallback, not the real active site; recomputed under
> the corrected (UniProt) seed, it does not survive at any tested k. The
> honest surviving-positive count is now zero, reported as a second
> instance of the same self-auditing pattern Finding 4 already established.
>
> **2026-08-19 update ([[TASK-0183]])**: the real Assessment Criteria
> document landed (`documentation/2026-04-06-Assessment-Criteria-VF.md`,
> requested via [[TASK-0221]]) — the 25/25/20/15/5/10 weighting and
> "Phase 1 = Ideation" premise this whole document is sized against are
> both **confirmed exactly**, not just assumed. §3's `[TBD]` filled with
> `documentation/POC_SPRINT_PLAN.md`; §6 filled with the team/role split.
> Phase 2's own criteria are now known too (previously unavailable) and
> folded into the sprint plan's own new "Phase 2, now known" section.
>
> **2026-08-21 update ([[TASK-0229.001]])**: new §2.5 — a bibliography
> audit surfaced a reference (Gunasekaran, Ma & Nussinov 2004) that
> attacks the negative class every AUC in this document assumes.
> Rank-of-known-site and enrichment-at-k, recomputed on the 3 mandatory
> targets' headline cells, do not rescue the result (enrichment@5 = 0.00
> on all three) but do change how "zero confirmed positives" must be
> phrased: evidence of no *robust* signal found, not proof no signal
> exists. §4's multiplicity-budget bullet cross-referenced accordingly.
>
> **2026-08-22 update ([[TASK-0229.002]])**: new §3(d) — surfaces
> [[TASK-0182]]'s own hardware-resource verdict for the first time in
> this document (`FAULT_TOLERANT_ONLY`, all mandatory targets, both
> resolutions — established weeks ago, never previously cited here), then
> checks the challenge's own two cited hardware routes against it.
> Circuit cutting ([10]): a real per-target boundary-cut count computed
> against each target's actual coupling graph, sampling overhead 10²²⁴-10⁴⁸⁷
> — reinforces the existing verdict, does not change it. SVD/dilation
> ([11], directly on-topic: FMO exciton transport): the one route in the
> whole document that clears the qubit-count bar, *if* paired with an
> amplitude-encoded register this project has not built or costed —
> stated as a real, honestly-caveated option, not a built result.
>
> **2026-08-22 update ([[TASK-0229.004]])**: new Finding 5 — implemented
> [1] Zheng 2023 (NMA-guided conformational sampling), the challenge's own
> reference #1, as a scored classical baseline for the first time. It
> beats this project's own quantum observable on KRAS_G12C by a wide
> point-estimate margin (AUC 0.728 vs. 0.557-0.590), reported per this
> project's own standing rule that a classical method outperforming the
> quantum arm is disclosed, not suppressed — while explicitly not counted
> as a significant result against the register's own multiplicity bar.
> **Correction, 2026-08-23**: this Finding was drafted and its numbers
> verified in the originating task, but a shared-file collision during
> that task's own commit silently dropped the actual document edit while
> absorbing a different, unrelated in-flight edit from another thread —
> the commit message claimed the insertion; the diff did not contain it.
> Caught and landed only now, alongside Finding 6 below. See
> [[TASK-0229.004]]'s own Done section for the added correction note.
>
> **2026-08-23 update ([[TASK-0229.005]])**: new Finding 6 — [1]+[2]
> stitched (NMA sampling feeding persistent homology, the register's own
> flagged "highest-value construction") fails at its own cheapest,
> first gate: the known pocket is not a persistent-homology H2 void even
> on the fully open, drug-bound structure, on either TASK-0209-VALID
> target. The ensemble question this construction was built to answer
> (does TDA over an ensemble beat TDA on one structure) is reported
> untested-and-untestable-as-scoped, not forced past a failed positive
> control.
>
> **2026-08-24 update ([[TASK-0229.006]])**: new Finding 7 — the Ensemble
> Allosteric Model (ref [4]), the largest previously-untested item in the
> challenge's own bibliography, tested via a real COREX-style
> implementation on both VALID targets. A genuine mixed result (real,
> significant, but partial agreement with propagation ranking, not
> redundancy) plus a type-correct quantum target this program had not
> previously connected to a formulation. **Added here, and to
> `POC_SPRINT_PLAN.md`, after [[TASK-0183]] had already shipped and
> closed** — see that document's own dated addendum for the honest
> record of the timing; nothing already committed there was revised.
>
> **2026-08-26 update ([[TASK-0270]]/[[TASK-0272]])**: `4OBE`, KRAS_G12C's
> apo structure named as misannotated in Finding 4, has now been swapped —
> organiser-sanctioned, `documentation/2026-08-26-organiser-clarifications.md`
> — for `4LDJ`, the best-resolution genuinely-G12C apo structure found by a
> live RCSB sweep ([[TASK-0270]]'s own Done section; the organisers'
> suggested `8S8C` turned out to be holo, not usable). Every KRAS_G12C
> number in Findings 5-6 that depends on the apo structure was computed on
> the misannotated wild-type protein. Re-run on the corrected structure:
> **quantum-observable AUC 0.557 → 0.514, diagnosis `NO_FAILURE_DETECTED` →
> `NO_SIGNAL_IN_APO`, ENM validity r=0.646 (PASS) → 0.496 (MARGINAL)**,
> pocket-to-active-site min heavy-atom distance materially unchanged (1.32
> Å → 1.31 Å). Findings 5 corrected in place below; Finding 6's own AUC
> 0.557 figure is a *holo*-structure measurement (6OIM, independently
> re-verified genuine G12C, unaffected by the apo swap) — checked
> directly, not assumed, and left as-is. Corrected the same way every
> other apo-genotype-sensitive number in this register was: reported
> plainly, including that it is a worse result than the one it replaces.

---

## 1. Problem and impact — the field cannot currently tell a working method from a broken one

Cryptic allosteric pockets are the most valuable unexploited target class in
small-molecule drug discovery: they are absent from the apo structure by
definition, which is precisely why they are both underexploited and hard to
validate. The challenge asks for a method that finds them from apo structure.

We implemented that method in full — the challenge's own §4.1 specification,
a continuous-time quantum walk on the residue contact network seeded at the
active site — and then did something we believe no competing submission will
have done: **we audited whether the benchmark can certify the answer.**

It cannot.

**Finding 1 — two of the three mandated targets cannot express the contrast
the challenge's own premise assumes.** We applied a blind, pre-registered rule
(apo pocket scores closed, holo pocket scores open, ligand stripped, fpocket
druggability) to every target with a genuine small-molecule drug ligand —
first the challenge's own set, then the extension §6 directs participants to
make:

| Target set | Source | Valid |
|---|---|---|
| Mandated, scoreable (KRAS_G12C, BCR-ABL1, Cardiac Myosin) | Table 1 | **1 of 3** — KRAS_G12C only |
| ASD extension (PTP1B, glucokinase, caspase-1, caspase-7) | §6's own recommended database | **1 of 4** — PTP1B only |

c-Myc, the fourth mandated target, has no drug-bound structure and therefore
cannot carry this contrast at all.

We stress the provenance because it determines what the result means: **we did
not select the failing targets.** Two of the three came from Table 1; the
extension followed §6's instruction (*"participants are highly encouraged to
test the robustness of their quantum approach on additional targets… may refer
to the Allosteric Database"*) and its named source. Extending into the
database the challenge itself recommends recovered exactly one more usable
instance.

For any claim depending on a druggability contrast, the mandated three-target
gate has therefore been operating at **1/3 validated coverage** — and the
shortfall is systemic across two independent target sources, not an artifact
of our choices. *(TASK-0209)*

**Finding 2 — the failures are diagnosable, and two are previously
unreported.** Three mechanistically distinct modes:

1. **An unexplained ligand holds the "apo" pocket open.** BCR_ABL1's `1OPL`
   contains **`MYR`** (myristic acid) 3.47 Å from the pocket — the
   autoinhibited form, where the kinase's own myristoylated N-terminus
   occupies its own allosteric site. GLUCOKINASE's apo contains **`MRK`** at
   2.45 Å, the same failure shape, **not previously reported**. In both cases
   the "apo" structure is not apo at the site of interest.
2. **An intrinsically open pocket with nothing to explain it** — CASPASE1
   scores 0.679 druggable in apo with no ligand nearby.
3. **No contrast at all: the holo positive control itself misses** —
   CARDIAC_MYOSIN (0.166), CASPASE7 (0.010). *(TASK-0209)*

**Finding 3 — a 2009 geometric tool beats the quantum observable.** fpocket,
with no propagator, no seed, and no dynamics, outscores our best quantum
observable on 2 of 3 mandatory targets: KRAS_G12C 0.7910 vs. 0.5901 (floor
0.4818), BCR_ABL1 0.8618 vs. 0.5266 (floor 0.5817); CARDIAC_MYOSIN 0.5303 vs.
0.5176, just above floor *(TASK-0163, pinned/reproducible build, TASK-0206)*.

**Finding 4 — the field's own reference structure for the flagship target is
misannotated.** `4OBE`, this project's (and the field's) apo structure for
KRAS_G12C, is confirmed **wild-type at residue 12, not the G12C mutant**
(RCSB deposition, independently re-verified twice). Swept 10 RCSB-verified
true-G12C apo structures through the identical pipeline: median AUC 0.482
(below chance), only 3/10 floor-clear, and **P@5 = 0.000 on all ten** — the
mislabeled 4OBE (P@5 0.200) is a lucky outlier, not a representative draw
*(TASK-0155, TASK-0192)*. Kept in the register rather than silently swapped
— every historical number here is conditioned on it, and changing it
retroactively would misrepresent what was actually measured — but it is
disclosed here because it must be: the field's flagship cryptic-pocket
target is validated against the wrong genotype, a benchmark-integrity defect
of exactly the kind Findings 1-2 already demonstrate this team can find and
the field has not.

**Finding 5 — a second, independent classical method also beats the quantum
observable, and it is the challenge's own reference #1.** We implemented
Zheng (2023) — NMA-guided conformational sampling, the challenge's own
bibliography entry [1], never previously run as a scored baseline despite
being the canonical published version of the same conformational-search
reframing this program independently arrived at. On KRAS_G12C, the one
mandated target with a validated apo-closed/holo-open contrast (Finding 1):
**AUC 0.728, vs. our own quantum-observable AUC of 0.514** (floor 0.530;
**below floor**, diagnosis `NO_SIGNAL_IN_APO` — corrected 2026-08-26,
[[TASK-0270]]/[[TASK-0272]], after the apo genotype fix in Finding 4's own
update above; the pre-fix figure was 0.557 on `4OBE`, the misannotated
wild-type structure) — a wide point-estimate margin, from a dynamics-based
classical method this time, not a static geometric one like fpocket
(Finding 3).
Checked against a permutation null (1000 draws, the same corrected
compact-patch construction used elsewhere in this register): p=0.024 —
clears a naive two-test local bar by a hair, but is roughly three orders of
magnitude short of this program's own register-wide multiplicity bar
(≈0.00022 across 226+ scored cells). **We do not count this as a
significant result** — the register's own standing bar is the one that
governs, and this does not clear it — but the point-estimate margin itself
is real and, per this report's own stated method, reported rather than
omitted. On PTP1B (the register's other validated target), the method
beats the floor (0.610 vs. 0.451) but its own preferred statistic (pocket-
level hit rate) does not show the same specificity the residue-level AUC
does — a genuine internal disagreement, disclosed rather than resolved in
whichever direction looks better. *(TASK-0229.004)*

**Finding 6 — the register's own "highest-value construction" fails at its
first, cheapest gate.** [2] Koseki et al. 2025 (CrypToth) argues cryptic
pockets carry a persistent-homology (topological-cavity) signature, and
specifically that computing it over a conformational **ensemble** should
outperform any single structure. [1]+[2] stitched — Zheng's NMA sampling
feeding CrypToth's persistent-homology layer — was this register's own
explicitly flagged highest-value forward proposal: zero MD, both halves
drawn from the challenge's own bibliography. Before running the ensemble at
all, we required the observable to clear its own cheapest possible check
first: on the already-open, drug-bound structure (no sampling needed — the
best case for detecting a void), does the known pocket sit inside a
persistent H2 cavity at all? On both TASK-0209-VALID targets, no: KRAS_G12C's
top H2 lifetime is 0.81 (this project's own established noise floor is 2.5)
and the void-proximity score is barely above chance against the known pocket
(AUC 0.557); PTP1B's top lifetime is 1.54 (also sub-floor) and its void
score is *anti-correlated* with the known pocket (AUC 0.116) — confirmed not
a filtration-cap artifact (identical values from thresh=16 through
thresh=30). Per this task's own Planned Validation, ensemble scoring on the
apo structure was gated on this positive control passing; it did not, on
either target, so **the ensemble question (does TDA-over-an-ensemble beat
TDA-on-one-structure) is reported untested-and-untestable-as-scoped, not
forced past a failed gate.** Run anyway as an explicit, ungated diagnostic
for transparency: the 120-conformation NMA-sampled apo ensemble scores AUC
0.521 (KRAS_G12C) / 0.487 (PTP1B) — both within noise of chance, neither
beating its own proximity floor consistently. This directly explains, rather
than merely repeats, an earlier single-structure apo-only finding on this
same H2 observable: the missing signal is not an apo-vs-holo timing
artifact — these specific real binding sites are not the "capped cavity"
shape H2 requires, in either conformational state. *(TASK-0229.005)*

**Finding 7 — the largest previously-untested item in the bibliography
gives a genuine mixed result, and a quantum target of a different kind
than anything above.** [4] Motlagh, Wrabl, Li & Hilser (2014) — the
Ensemble Allosteric Model — holds that allosteric coupling is a
partition-function quantity over 2^N folded/unfolded microstates, not a
pathway on a contact graph, and can occur with zero mean structural
change. A **harmonic proxy** of this idea was already tested and landed
in the same confounded room as every other observable here (\|partial
ρ\|=0.773 on non-target structures, [[TASK-0226]]) — the ensemble route
is not an exit this program walked past. The **genuine, nonlinear EAM**
was not tested until now: a real COREX-style implementation (sliding-
window folding units, ASA-parameterised free energy, per-residue
stability constants) on both TASK-0209-VALID targets. Sanity check
passes on both (buried residues significantly more stable than exposed,
ρ=−0.365/−0.298, p<2×10⁻⁶). The decisive test — does EAM's own coupling
ranking agree with, or diverge from, this register's propagation-based
ranking — gives neither of the two clean answers pre-registered for it:
**Spearman ρ=0.542 (KRAS_G12C) / 0.493 (PTP1B)** against hop-distance —
real and highly significant, substantially more agreement than chance,
but far short of the ~0.85-0.95 this register's other observables show
when they turn out to be distance detectors wearing a different name.
Roughly 70-75% of EAM's own ranking variance is not explained by
proximity alone — reported as a genuinely mixed result, not forced into
either bin. Independent of that empirical result, the EAM's true object
— the partition function COREX's own tractable approximation exists to
avoid computing directly — is a **type-correct quantum target** (Gibbs-
state preparation / partition-function estimation), a structurally
different kind of route than the propagation-observable hardware stories
in §3(d) below, and the only one in this register's current hypothesis
set with any path to c-Myc/Max, via ref [4]'s own disorder-amplifies-
coupling claim (though c-Myc has no holo structure and stays
unvalidatable). **Not an advantage claim**: quantum speedups for
classical partition-function estimation are at best quadratic and
conditional, and the classical ensemble this task actually enumerated is
itself trivial to compute — stated with the same discipline this
proposal applies to every other candidate route. *(TASK-0229.006 —
added, honestly dated, after `POC_SPRINT_PLAN.md` had already shipped;
see that document's own addendum.)*

The impact claim is therefore not "we can find cryptic pockets." It is:
**the community currently has no instrument capable of certifying that
anyone can**, and we built and validated one that shows why.

---

## 2. Technical approach — what we falsified, and the instrument that came out of it

### 2.1 The anchoring result

Every observable in the challenge's specified family lives in a
single-particle Hilbert space of dimension *N*. At *N* ≤ 704 every one of them
is an `eigh` call. **No quantum advantage is available in that formulation at
any point, for any operator** — a statement about the formulation, not about
our implementation of it.

We nonetheless implemented and scored the family, because the interesting
question was *why* it fails.

### 2.2 What was ruled out, and by what measurement

| Route | Closed by | Measurement |
|---|---|---|
| Seeded-occupation observables | proximity confound | ρ(score, −hop) substantial on every target; a bare Laplacian correlates ρ=+0.83 with distance-from-seed |
| Coherence / interference | inert | flat γ-sweeps; converged limit provably phase-free, exact to 1e-6; coherent ≥ ENAQT under NISQ noise |
| Non-locality | absent by construction | single-particle entanglement reduces to Shannon entropy of regional occupation *(TASK-0148)* |
| Interacting multi-particle | measured (external panel, not this team) | 2-boson observable correlates ρ≈0.88–0.90 with the 1-particle one at U=12; the confound **worsens** (0.73→0.82) |
| Backbone-only conformational search | not a rare event | pocket recovery in **1–8 draws** *(TASK-0185)* |
| Residue-selection QUBO | 0/3 targets | *(TASK-0181 Phase A)* |
| Optimal control (GRAPE) | chance on 3/3 | AUC 0.501/0.404/0.474, p=0.48/0.99/0.71 *(TASK-0156)* |
| **Fixed-backbone rotamer packing** | **complexity** | pairwise MRF, treewidth 2–5; exact global optimum in **0.001–0.159 s** vs naive 1e14.1 *(TASK-0204)* |
| **Coupled backbone+rotamer search** | **not hard** | **13 of 65 restarts** reach the holo basin on KRAS_G12C *(TASK-0213)* |

**Nine routes, all closed by measurement.** We report this as the derivation of
the instrument, not as a list of failures.

### 2.3 The redundancy finding — why "we tested 28 observables" would be dishonest

The register's ~28 per-residue observables collapse to a **participation-ratio
effective rank of 2.6–4.1**, stable across 5 targets spanning N=169–704, with
`−hop_from_seed` loading at or above the median of all 28 on the dominant
component. We tested approximately **three** things thoroughly — proximity,
directed transport, and ensemble/mode structure — not twenty-eight.
*(TASK-0199, refined by TASK-0207: PC1/PC2 stable, PC3 is not.)*

We state this because it moves our own multiplicity arithmetic **against** us:
rescaled by the measured ~9× redundancy, the expected-false-positive baseline
falls from ~18.3 to ~2. A referee would find this; we would rather state it.

### 2.3b Variance attribution — geometry, CTQW, and the majority neither explains

**Added 2026-08-24, revised the same day (TASK-0238 → TASK-0245).** The
redundancy finding above says our observables are fewer than they look. This
says what the surviving ones explain — and the largest term is neither of them.
**These are cross-validated numbers.** The first version of this section was an
in-sample fit; we flagged it as an optimistic ceiling and then ran the check.
It moved against us, as predicted, and the revised numbers are the ones below.

Method, per target, on apo coordinates with seed rows excluded: 5-fold
stratified CV (20 repeats) over residues; fit OLS(geometry) and
OLS(geometry + CTQW) on train, score out-of-fold; attribute shares of
discrimination *above chance* as (AUC − 0.5) / 0.5. Geometry = the three
baselines `degree_centrality`, `euclid_from_seed_centroid`, `hop_from_seed`.
Operator = converged incoherent CTQW on `H_new`. n = 9 targets.

| target | geometry | CTQW | **unexplained** |
|---|---|---|---|
| KRAS_G12C | 58% | 8% | **34%** |
| BCR_ABL1 | 5% | −1% | **96%** |
| CARDIAC_MYOSIN | 0% | 15% | **93%** |
| HIV-1 RT | 54% | 0% | **45%** |
| PTP1B | 28% | −1% | **73%** |
| GLUCOKINASE | 30% | 3% | **67%** |
| CASPASE7 | 0% | −4% | **108%** |
| GLUR2_TRU | 46% | 2% | **51%** |
| GLUK1_BPAM | 84% | 1% | **16%** |
| **range (median)** | **0–84% (30%)** | **−4 to +15% (+1%)** | **16–108% (67%)** |

**We estimate that a major and highly variable share of allosteric-pocket
discrimination — 16–108%, median 67% — is explained by neither static geometry
nor quantum-walk transport. Geometry contributes 0–84% (median 30%). CTQW
contributes −4% to +15%, median +1%, and its out-of-fold increment is negative
on 3 of 9 targets.**

Reading the table honestly:

- A share above 100% (CASPASE7) means the stacked model scored *below chance*
  out-of-fold — no model we have generalises on that target at all.
- CTQW's contribution is not distinguishable from zero on most targets. The two
  where it is largest (CARDIAC_MYOSIN +15%, GLUK1_BPAM) are also the two where
  the geometry block is weakest, so it is partly filling a vacuum rather than
  adding orthogonal information.
- A separate two-stage experiment (fpocket proposes candidate pockets, the
  operator ranks within them) reached the same place by a different route,
  and **updated 2026-08-24** once pushed to proper power against an honest
  classical competitor. The original n=7 read (CTQW and a plain hop-distance
  ranker tying at mean rank 5.71) did not survive scale-up: on TASK-0243's
  frozen, untuned 22-target set (20/22 usable — a seed-resolution defect on
  two HIV integrase entries left `detect_active_site` with an empty seed,
  counted as an attempted failure, not excluded), an honest classical
  composite — fpocket druggability + banded hop-shell one-hot + degree +
  Euclidean distance, weights fit LOTO across targets, no access CTQW
  doesn't also have — reaches per-residue AUC 0.710 against CTQW's 0.592,
  and `fpocket_drug` alone, a single unfitted feature, reaches 0.756. The
  same ordering holds under the two-stage candidate-ranking design itself:
  composite MRR 0.304, `fpocket_drug` alone 0.344, CTQW 0.161 (denominator
  = 22 targets attempted; 14/22 survived stage-1 fpocket + seed resolution).
  CTQW's own increment over the full composite is real but small and
  insufficient to lead: +0.020 AUC, +0.016 MRR *(TASK-0249)*.

We report this because it disciplines our own Phase-2 proposal. The majority
term is not addressable by a better Hamiltonian or a better baseline — both are
already booked. That fpocket, a 2009 purely geometric tool with no dynamics and
no seed, reaches 0.8348/0.8596 on KRAS_G12C/BCR_ABL1 indicates a substantial
part of the residue is static pocket structure that no dynamics-based
observable in our register examines at all.

**Updated 2026-08-24 ([[TASK-0254]]) — the 67% figure above moved materially
and is superseded as the estimate of record.** The table above never included
`fpocket` as its own block — [[TASK-0249]] had already shown `fpocket_drug`
alone beats the full geometry+CTQW stack. TASK-0254 re-ran the attribution
with fpocket as a third block, **order-independent** (geometry and fpocket
are correlated; a fixed entry order misassigns their shared variance — exact
Shapley value over 3 blocks, not a sequential fit), on the frozen, untuned
22-target set (n=20 usable) rather than the 9-target set above.

**Corrected estimate of record: unexplained 2–62%, median 29%** (was 16–108%,
median 67%). Geometry 6–83% (median 42%), fpocket −9% to +65% (median +8%,
wide and target-dependent — dominant on some targets, negative on others),
CTQW −15% to +49% (median +11%, up from median +1% — a real change from
Shapley properly crediting CTQW's own share instead of it being absorbed by
whichever block entered first in a sequential fit). **Most of what the
original table called "unexplained" was static pocket geometry the three
simple baselines don't measure and fpocket does** — confirming this section's
own hypothesis, not merely revising a number downward for its own sake.

The same task ran a systematic apo-crypticity screen (no such screen existed
before it — the register had one target's worth of evidence, BCR_ABL1) and
found **9/20 (45%) of the frozen set already has ≥80% of its true pocket open
in apo** — cross-tabulated against `fpocket_drug`'s own per-target AUC, those
already-open targets score a median 0.854 versus 0.515 (near chance) on the
genuinely cryptic-testing remainder. **This benchmark's apparent difficulty is
substantially a mixture of two different tasks** — static retrieval and
genuine cryptic-site discovery — bundled into every number reported above and
in §2.3 generally. Full tables, method, and both screens: `RESULTS.md`'s
dated TASK-0254 section; `.ai/tasks/DONE/
TASK-0254-fpocket-in-the-variance-stack-and-apo-crypticity-screen.md`.

### 2.3c A theoretical reason this pattern was the expected one, not a defect

**Added 2026-08-24 (TASK-0252).** §2.3/§2.3b establish, empirically, that every
graph/pathway-based observable we have built — CTQW included — is redundant
with simple geometry and explains only a small, often negative, share of
discrimination beyond it. The literature this challenge itself cites predicts
exactly this outcome, not merely tolerates it. The Ensemble Allosteric Model
(ref [4], Motlagh, Wrabl, Li & Hilser 2014, *Nature* 508:331) states allosteric
coupling free energy as a partition-function quantity over an exponential space
of folded/unfolded microstates, explicitly **not** a pathway on a contact
graph. That is not an incidental phrasing choice: partition-function-derived
quantities are a nonlinear (log-sum-exp) transform of the underlying microstate
energies, and a coupling free energy computed through one is generically
non-separable into a sum of independent pairwise (graph-edge) terms — separable
only in the degenerate case where the two sites are statistically independent,
i.e. not actually coupled. **A graph-edge decomposition of allosteric coupling
free energy is not merely difficult to find; the ensemble formalism this
challenge cites says none should be expected to exist.** Every graph-shaped
observable we have built — contact-graph propagation, hop distance, and CTQW,
which our own within-shell audit shows duplicates two much simpler geometric
baselines rather than adding orthogonal signal (§2.3b, [[TASK-0247]]) — sits
entirely inside the representational class this argument says is structurally
insufficient.

This reframing is corroborated, not merely asserted: our own genuine
(COREX-style) ensemble-coupling measurement ([[TASK-0229.006]]) correlates
with graph-propagation ranking at ρ≈0.5 on both validated targets — real and
significant, but far short of the ~0.85–0.95 agreement this register's other
observables show when they turn out to be simple distance detectors in
disguise. Partial overlap, not identity, is exactly what "pathways are a
high-flux *subset* of population redistribution, not the whole causal story"
(ref [6], Tsai & Nussinov 2014) predicts. We read our own repeated negative
result — graph-based dynamics observables underperform static geometry, and
what little they add duplicates simpler baselines — as **consistent with,
not merely undefeated by,** the field's own leading account of how allosteric
coupling is actually structured. Full citation-level analysis, including a
diagnosed confound in this project's own COREX coupling metric found while
testing a related claim (disorder-amplified coupling, ref [4]'s H4.3):
[[TASK-0252]].

### 2.4 The one positive we had did not survive our own audit either

**Updated 2026-08-14 — this section's own headline changed.** The prior
draft reported PTP1B `dcc_low` (k=10) as the register's one surviving
positive: p=0.0027 against a pre-registered bar of 0.003125, AUC 1.000,
20,000 replicates, published *(TASK-0201)*. It no longer survives, and the
reason is itself a finding worth reporting.

**The seed was wrong.** A construct-validity sweep of the labelling
pipeline *(TASK-0216, TASK-0217.001, TASK-0217.003)* found that `PTP1B`'s
holo structure contains no functional/substrate ligand at all — only the
allosteric drug — so the code path that derives the active site silently
fell through to a topological placeholder (the 5 highest-degree residues in
the contact graph), not the real catalytic site. This was never flagged:
the fallback returned a plausible-looking index set with no warning. The
real catalytic site (Cys215 + the P-loop, 9 residues, UniProt-annotated) is
known and unambiguous.

**Recomputing TASK-0201's exact statistic under the real seed — same null,
same 20,000 replicates, same pre-registered bar, independently re-derived
twice from separate code paths — the result does not survive at any tested
k**: AUC drops from 1.000 to 0.598, p from 0.0027 to 0.567, against the same
0.05/16 bar. The permutation-null machinery was never at fault (it shuffles
pocket labels, not seeds); what changed is what was being scored.

**The register's honest count of surviving positives, updated: zero.** We
report this as a second, independent instance of the same finding pattern
Section 1 already documents at the benchmark level (Findings 1, 2 and 4):
this team's own audit apparatus catches errors — including its own — that a
less adversarial process would have shipped. The fallback is now fixed at
the source (a curated, UniProt-derived active site is consulted before the
topological placeholder, closing the failure mode for every future run, not
just this one cell), and the correction is reported here rather than left
for a reviewer to find independently.

*(TASK-0158 → TASK-0190 → TASK-0201 for the null-construction history that
produced the original p=0.0027; TASK-0168/TASK-0203 for the separate,
already-known mechanism caveat, which is now moot — there is no surviving
score to explain a mechanism for.)*

### 2.5 Does the negative class itself hold up?

A late-stage audit of the challenge's own bibliography found a reference
that attacks a premise every AUC above assumes. [9] (Gunasekaran, Ma &
Nussinov 2004, *Proteins* 57:433 — verified directly against the live
article, not relayed) argues allostery may be an intrinsic capability of
nearly every dynamic protein: there is no clean class of genuinely
non-allosteric surface sites. This corrupts the negative class every
ROC-AUC above presupposes, and it cuts both ways — it can inflate
apparent false positives, but it can equally mean a chance-level AUC is
**not** evidence of no signal: a contaminated negative class adds noise
that can mask a real, weaker effect.

[9] is a claim about protein biology in general, not a measurable
per-target quantity, so we cannot test it directly. What we can do is
check whether it changes how "zero confirmed positives" (§2.3-2.4) should
be read, using two metrics that degrade more gracefully than AUC under a
contaminated negative class: **rank-of-known-site** (where the true
pocket lands in the full ranking) and **enrichment-at-k** (how much
better than chance the reported top-k list is). Recomputed on the same
3 mandatory targets' headline cells, live pipeline, same H_new operator
*(TASK-0229.001)*:

| Target | AUC | Best pocket-residue rank (of N) | Median pocket rank | Enrichment@5 |
|---|---|---|---|---|
| KRAS_G12C | 0.557 | 7 / 169 | 82 | **0.00** |
| BCR_ABL1 | 0.541 | 125 / 451 | 176 | **0.00** |
| CARDIAC_MYOSIN | 0.549 | 107 / 704 | 279 | **0.00** |

*(AUC point estimates here differ slightly from §2.2's cited 0.5901/
0.5266/0.5176 — expected drift from intervening pocket-label refinements
[[TASK-0177]], not a new measurement disagreeing with an old one; both are
real numbers from the same live pipeline at different points in time.)*

*(Found while auditing this document for KRAS_G12C's own apo-genotype fix,
2026-08-26, [[TASK-0270]]/[[TASK-0272]] — flagged, not silently fixed: this
row's own N=169 and AUC 0.557 are `4OBE`-era (the misannotated wild-type
apo). The rank-of-known-site and enrichment-at-k statistics here were not
among the figures [[TASK-0270]] re-ran on the corrected `4LDJ` structure —
they need their own re-run before being cited as current, a real,
disclosed gap rather than an inherited stale number presented as live.)*

They do not tell a different story — they tell the same one more
concretely. **Zero of the top-5 residues in our own headline hit list are
real pocket residues, on every mandatory target.** The alternative
metrics do not rescue the result, and per this task's own constraint we
report that as plainly as we would report a rescue.

**What changes is the interpretation, not the count.** §2.3/[[TASK-0161]]/
[[TASK-0199]] found 226 real-target scored cells across the program,
~2 expected false positives at α=0.05 after the measured ~9× observable-
redundancy correction, zero confirmed. That arithmetic — how many cells
clear a significance bar, against how many chance alone predicts — does
not depend on negative-class quality; it is a count. What [9] puts in
question is whether "zero confirmed positives" may be read as "we have
shown there is no signal." It may not, without qualification: a
contaminated negative class is an equally consistent explanation for the
same zero — reduced statistical power from noisy negatives, not an
absence of real coupling, and our methodology as built cannot distinguish
the two. We therefore state the result as **no method tested here found
a statistically robust signal**, not as proof of absence — the
distinction [9] specifically forces, and one a referee who knows this
reference would otherwise draw for us.

---

## 3. Proposed Phase-2 work — build the certifying instrument

**We are not proposing to run QAOA on a protein.** The register's own evidence
says the instances are not hard, and we will not claim otherwise.

We propose to build what is actually missing and what our audit shows the
field needs:

**(a) A certifying cryptic-pocket benchmark.** Blind VALID rule + endogenous-
ligand audit + positive control + measured limit of detection, applied at
scale to identify which apo/holo pairs can support a cryptic-pocket claim at
all. Our audit found 5 of 7 standard targets fail; the field is using them.

**(b) A screening criterion for the hard regime.** Which targets sit in a
regime where a search-based (and therefore possibly quantum-amenable) method
could matter, decidable *from apo alone*. Our own data motivates this
directly: coupled search succeeds 20% of the time on KRAS_G12C and 0/65 on
PTP1B — the two valid targets **disagree**, and with n=2 we cannot adjudicate.

**(c) The apo vs. stripped-holo delta.** Published propensity-based methods
(Amor et al. 2016; Wu et al. 2022) report 89.8%/98.1% on ASBench/CASBench —
but those benchmarks evaluate *ligand-removed holo conformations*, not apo.
Measuring the same observable on apo and on stripped-holo for the same target
isolates exactly the quantity cryptic-pocket prediction depends on. To our
knowledge that delta has not been reported.

**(d) Hardware realization — two routes from the challenge's own
bibliography, costed honestly, against a resource picture this document
had not yet stated.** [[TASK-0182]] already measured, months ago, that our
full-resolution register (one qubit per residue, the convention every
number in this document uses) needs 169-704 qubits and 3.3M-124.9M
two-qubit gates, and that Louvain coarse-graining to a NISQ-plausible
~10-15 qubits destroys most of the ranking signal (retention Jaccard
0.00-0.18) without even reaching hardware-usable fidelity — every
mandatory target verdicts `FAULT_TOLERANT_ONLY`, at both resolutions,
against a real IBM device calibration snapshot. **That result was never
surfaced in this document until now** — corrected here, not left for a
referee to notice its absence.

We checked whether either of the challenge's own two cited hardware
routes changes that picture.

*Circuit cutting ([10] Mitarai & Fujii 2021, Quantum 5:388 — verified
directly).* Simulating *n* non-local two-qubit gates via local operations
and classical post-processing costs a sampling overhead of O(9ⁿ)
(O(4ⁿ) with classical communication between sub-circuits) — this is the
established scaling this line of work derives, not a number we invented.
We computed the real partition, not an assumed one: each mandatory
target's actual `H_new` coupling graph, split into NISQ-sized islands via
the same Louvain machinery [[TASK-0182]] already uses, counting genuine
boundary-crossing coupling edges as the required cut count *n*:

| Target | Islands | Max island (qubits) | Cut edges (*n*) | log₁₀ overhead, O(9ⁿ) | log₁₀ overhead, O(4ⁿ) |
|---|---|---|---|---|---|
| KRAS_G12C | 10 | 23 | 235 | 224 | 142 |
| BCR_ABL1 | 14 | 56 | 344 | 328 | 207 |
| CARDIAC_MYOSIN | 15 | 98 | 510 | 487 | 307 |

For scale: the observable universe holds an estimated ~10⁸⁰ atoms. Every
cell above exceeds that by 15-400 orders of magnitude, in the *cheaper*
of the two overhead regimes. **Circuit cutting does not change the
verdict** — it reinforces [[TASK-0182]]'s own `FAULT_TOLERANT_ONLY`
finding from an independent direction, and the honest, cited answer to
"how would you fit a 704-residue protein on near-term hardware" is: not
by cutting it into pieces small enough to run and stitching the results
back together classically, at this graph's real connectivity.

*SVD/dilation for open-system dynamics ([11] Oh, Krogmeier, Schlimgen &
Head-Marsden 2024, ACS Phys Chem Au 4:393 — verified directly, and
directly on-topic: exciton transport through the FMO complex, the same
physics as our own ENAQT measurements).* This route is more promising,
and worth stating precisely rather than dismissed alongside the first.
Their method needs only **one ancilla qubit, independent of system
size**, to implement non-unitary (dephasing) dynamics as a unitary
circuit — a real advantage over Stinespring dilation, whose ancilla count
scales with the channel's Kraus rank. Gate count is O(4^d), *d* the
*system* qubit count — their own worked example needs 8 qubits total for
a 7-site excitonic system, because *d* there is an amplitude-encoded
(log₂-scale) register over site basis states, not one qubit per site.

That is the catch, stated plainly: [[TASK-0182]]'s entire resource table,
including the numbers in this section, uses one qubit per residue —
matching this document's own CTQW convention throughout, and how every
existing observable in our register is actually built. Ref [11]'s small
qubit counts come from a *different* base encoding (amplitude/log-scale
over the single-excitation subspace) that this project has not built or
costed anywhere. Projected honestly under that alternative encoding —
d ≈ ⌈log₂ N⌉ system qubits (9-10 for N up to 704) plus 1 ancilla, giving
O(4^d) ≈ 10⁵-10⁶ gates — the *qubit count* becomes genuinely NISQ-
plausible for the first time in this register, at a gate count large but
no longer astronomical. **We have not built this circuit or verified the
projection against our own coupling structure — it is ref [11]'s own
complexity formula applied to our own N, nothing more** — but it is the
one route in this document, across both hardware-story references and
[[TASK-0182]]'s own full resource sweep, that does not fail on qubit
count alone. Reconciled with [[TASK-0182]]: that task never costed this
encoding, so there is no contradiction to resolve, only an unbuilt option
now on record rather than left unstated.

*A fourth route, of a different kind — Gibbs-state preparation over the
Ensemble Allosteric Model's own partition function (Finding 7, §1).*
Where the three routes above all target this register's existing
propagation observable, this one targets a structurally different
quantity: the 2^N folded/unfolded microstate space ref [4]'s own model
poses and COREX's tractable approximation exists to avoid enumerating
directly. Type-correct, not advantage-claiming, and not scoped into any
sprint milestone — see `POC_SPRINT_PLAN.md`'s own dated addendum for why
it is recorded here rather than built into the plan.

Detailed scope, milestones, resources and pre-registered success criteria:
**[[TASK-0183]]**, `documentation/POC_SPRINT_PLAN.md` — month-by-month
milestones each with a falsifiable exit criterion, resource requirements
traced to measured numbers (not estimated), a risk register built from
this program's own observed failure modes, and an explicit exclusion
list. **Sizing confirmed 2026-08-19**: `documentation/2026-04-06-
Assessment-Criteria-VF.md` (the two-phase document [[TASK-0221]]
requested) landed and matches this proposal's own weighting exactly —
Feasibility 20% within the full 25/25/20/15/5/10 spread, Phase 1 titled
"(Ideation)" in its own heading. Previously flagged as an unverified
holding assumption; no correction was needed.

---

## 4. Validation plan

Already built and in use, not proposed:

- **Proximity floor** — every score must beat the strongest trivial baseline
  (degree / hop / Euclidean distance from seed), not chance *(TASK-0094)*.
- **Spatially-correct nulls** — three generations, each fixing a measured
  defect in the last *(TASK-0158/0190/0201)*.
- **Positive control with a measured LOD** — a planted, confound-orthogonal
  coupling; under the corrected null, no target reaches 80% power up to ~4×
  background conductance *(TASK-0167.002)*.
- **Program-level multiplicity budget**, stated with its redundancy correction
  *(TASK-0161, TASK-0199)* — and its own limit: a contaminated negative
  class (§2.5) means the resulting zero-confirmed-positives count is
  evidence of "no robust signal found," not proof of "no signal exists"
  *(TASK-0229.001)*.
- **Firewall / frozen-context provenance** — an unforgeable stamp preventing a
  claimed-frozen result from rendering unbannered *(TASK-0088)*.

**Known gap, stated:** ProteinLens — the one remaining external 4/4 comparator
in our register — has **no number attached**. It was confirmed live but
browser-only with no API and was flagged rather than skipped *(TASK-0163)*.
`[TBD: check whether BagPype (Zenodo 10.5281/zenodo.6326081) makes this
scriptable; if not, run manually on KRAS_G12C and PTP1B — the two VALID
targets — before submission.]`

---

## 5. Hybrid architecture

`[TBD — diagram]` Classical ENM ensemble generation → quantum subroutine →
classical verification (fpocket druggability + floor + null). Emitted by one
runner so §5.1 (connectivity matrix), §5.2 (site-level hit list) and §5.3
(this report) are mutually consistent.

**Consistency action required before submission:** the shipped demo currently
reports P@5 with no floor, on an operator this register falsified, under a
6 Å-dilated metric whose chance rate is 0.26 on a KRAS-sized protein and
whose pure-distance baseline scores 0.66. A judge who clicks the demo and
then reads this document would find them in contradiction. `[TBD: fix]`

---

## 6. Team and roles

Not aspirational — the split that already produced this register's own
~200 tasks, including the construct-validity sweep ([[TASK-0217]]) that
found and fixed the seed-provenance and array-correspondence defects
Section 2.4 reports: an Architect/Planner role (coordination, scope
decisions, cross-task synthesis), an Implementer role (bounded execution,
local validation, retrospective tests before trusting a new check), and a
Reviewer role (adversarial audit — the thread that found the criteria
[[TASK-0204]] D1/D2/D3 and set the construct-validity sweep in motion).
Physics/science judgment calls sit with whoever holds Implementer or
Architect/Planner on that task; final scope and narrative decisions —
like this document's own (A′) framing — sit with Bartosz. Full detail:
`documentation/POC_SPRINT_PLAN.md` ([[TASK-0183]]).

---

## Appendix — what would change our conclusion

Stated so the claim is falsifiable rather than defensive:

1. A benchmark of ≥10 targets that pass the VALID rule, on which the
   quantum observable family still fails — that would make the negative
   general rather than benchmark-limited.
2. A demonstration that coupled search is hard on a *valid* target under an
   apo-only objective — PTP1B's 0/65 is suggestive and unexplained.
3. An observable outside the measured ~3-dimensional span that carries signal.
   Ensemble contact covariance was the best candidate and landed **inside** the
   span *(TASK-0211)*.
