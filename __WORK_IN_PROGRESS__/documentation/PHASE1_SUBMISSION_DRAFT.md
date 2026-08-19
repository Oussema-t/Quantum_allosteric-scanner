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

**Finding 1 — only 2 of 7 standard targets exhibit the contrast the entire
premise assumes.** Applying a blind, pre-registered rule (apo pocket scores
closed, holo pocket scores open, ligand stripped, fpocket druggability) to
every target in our register with a genuine small-molecule drug ligand:

| Verdict | Targets |
|---|---|
| **VALID** (apo closed → holo open) | KRAS_G12C, PTP1B |
| INVALID | BCR_ABL1, CARDIAC_MYOSIN, GLUCOKINASE, CASPASE1, CASPASE7 |

**Two of the three mandatory targets are INVALID.** For any claim that depends
on a druggability contrast, the standard three-target gate has been operating
at **1/3 validated coverage**. *(TASK-0209)*

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

Detailed scope, milestones, resources and pre-registered success criteria:
**[[TASK-0183]]**, `documentation/POC_SPRINT_PLAN.md` — month-by-month
milestones each with a falsifiable exit criterion, resource requirements
traced to measured numbers (not estimated), a risk register built from
this program's own observed failure modes, and an explicit exclusion
list. **Holding assumption stated there, repeated here**: sized against
Feasibility = 20% and "Phase 1 scored as ideation," neither of which
appears in `documentation/Cleveland-Clinic-Challenge-Statement-vF-1.md`
— the only challenge document in this repo. The two-phase document that
would confirm them is requested via [[TASK-0221]]; cheap to re-check once
it lands, not silently assumed correct.

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
  *(TASK-0161, TASK-0199)*.
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
