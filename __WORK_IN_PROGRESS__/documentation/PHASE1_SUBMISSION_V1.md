# Quantum Allosteric Scanner — Phase 1 Proposal

**Global Quantum + AI Challenge 2026 · Phase 1 Ideation · Team AuraQu**

> The benchmark cannot certify what the challenge asks. Here is the measurement
> that shows it, and the specification for one that could.

| | |
|---|---|
| **Draft** | v1 — for adversarial review |
| **Date** | 2026-09-02 |
| **Deadline** | 2026-09-15 · 13 days |
| **Format** | 6pp + 3pp appendix + repo link |
| **HTML twin** | `documentation/PHASE1_SUBMISSION_V1.html` — published at https://claude.ai/code/artifact/c603f27a-ce03-47d5-b236-97719048263a |

> **Content parity**: `documentation/PHASE1_SUBMISSION_V1.html` and `documentation/PHASE1_SUBMISSION_V1.md` carry the same
> content. Edit both, or regenerate one from the other — two drifting copies of
> a submission is the failure mode that produced TASK-0307. Verified by
> `.ai/tools/doc_parity.py`.

---

## What this document is

This is the first full draft, restructured onto the seven-item table of contents
mandated by Guidelines §4.3 — *not* the six assessment criteria the previous
draft was organised around. A reviewer following the Guidelines would have looked
for item 4 in that version and not found it.

It is circulated for **adversarial review**. Section 8 lists the seven places we
believe this document is weakest and asks you to attack them specifically. What
is still unfinished is marked as such — we would rather hand you a draft with
visible holes than a draft with plausible filler.

---

## 1. Problem Framing

*Guidelines §4.1 — "why quantum or quantum-AI methods offer a credible advantage
**or novel insight**"*

**We claim the novel insight, not the advantage.** §4.1's formulation is
disjunctive, and answering it honestly requires saying which disjunct we are
taking. We identified nine candidate quantum-advantage routes for this problem.
We closed all nine by measurement, and we report that as our principal finding
rather than working around it.

Cryptic allosteric pockets are the most valuable unexploited target class in
small-molecule drug discovery: absent from the apo structure by definition, which
is exactly why they are both underexploited and hard to validate. The challenge
asks for a method that finds them from apo structure. We implemented that method
in full — §4.1's own specification, a continuous-time quantum walk on the residue
contact network seeded at the active site — and then did something we believe no
competing submission will have done. **We audited whether the benchmark can
certify the answer.**

It cannot, for three diagnosable reasons.

### Finding 1 — two of the three mandated targets cannot express the contrast the challenge's own premise assumes

A blind, pre-registered validity rule (apo pocket scores closed, holo pocket
scores open, ligand stripped, fpocket druggability) applied to every target with
a genuine small-molecule drug ligand:

| Target set | Source | Valid |
|---|---|---|
| KRAS_G12C, BCR-ABL1, Cardiac Myosin | Table 1, mandated | **1 of 3** — KRAS_G12C only |
| PTP1B, glucokinase, caspase-1, caspase-7 | §6's own recommended database | **1 of 4** — PTP1B only |

We stress provenance because it determines what the result means: **we did not
select the failing targets.** Two of three came from Table 1; the extension
followed §6's own instruction and its named source. The mandated gate has been
operating at **1/3 validated coverage**, and the shortfall is systemic across two
independent target sources.

### Finding 2 — two of the failures are previously unreported

An unexplained ligand holds the "apo" pocket open. BCR-ABL1's `1OPL` carries
`MYR` with **75% overlap** of the scored pocket window; GLUCOKINASE's `1V4S`
carries `MRK` at **88%**; PKR's `7FS3` carries an allosteric modulator at
**92%**. These are depositions the field uses as apo. They are not apo at the
site of interest.

### Finding 3 — the quantum observable's apparent signal is geometry

Our walk occupation scores AUC 0.5921 on 108 annotated structures — until it is
conditioned on distance to the active site, which is what it is seeded on.
Residualised, it falls to **0.5184, not significantly above chance**. Roughly
four fifths of the signal was proximity the walk inherited from its own seeding.
We published the unconditioned number first and retracted it four days later; the
record is in Appendix B.

---

## 2. Technical Approach

*Guidelines §4.3 item 2 — the **proposed** method, and the paradigm, stated in terms*

### Paradigm

**Quantum-inspired, classically-simulable.** Single-particle continuous-time
quantum walks on a residue contact graph are efficiently simulable on classical
hardware; no asymptotic speedup is claimed or available. We used the quantum
formalism as a *modelling language* — a principled way to write down coherent,
interference-carrying transport on a protein graph — and then measured what that
language can and cannot express. Stating this plainly is not a hedge. It is the
finding.

We are **not** proposing to run QAOA on a protein. Our own evidence says the
instances are not hard: side-chain packing at pocket scale is a pairwise MRF with
treewidth 2–5, solved exactly in 0.001–0.159 s against a naive 10^14 search
space. A hard regime exists only at ~50–80 residues, which is most of a domain,
not a pocket.

### What we propose to build

**(a) A certifying cryptic-pocket benchmark.** Blind validity rule + endogenous-
ligand audit + positive control + measured limit of detection, applied at scale to
establish which apo/holo pairs can support a cryptic-pocket claim at all. Our
audit found 5 of 7 standard targets fail; the field is using them.

**(b) A screening criterion for the hard regime** — which targets sit where a
search-based, possibly quantum-amenable method could matter, decidable *from apo
alone*. Our own data motivates this: coupled search succeeds on 20% of restarts
for KRAS_G12C and 0/65 for PTP1B. The two valid targets disagree, and at n=2 we
cannot adjudicate.

**(c) The apo vs stripped-holo delta.** Published propensity methods report
89.8%/98.1% on ASBench/CASBench — but those benchmarks evaluate *ligand-removed
holo* conformations, not apo. Measuring the same observable on both isolates
precisely the quantity cryptic-pocket prediction depends on. To our knowledge
that delta has never been reported.

**(d) A combined-readout ranker.** Our newest result, and the one constructive
lead we have. Individually, none of seven implemented observables survives
conditioning on proximity. *Jointly*, under leave-one-protein-out cross-validation
on 105 structures, they reach residualised AUC **0.595** — and the ceiling barely
moves when both proximity features are removed from the model entirely (0.602).
The information is in the representation; no single observable exposes it.

> #### Both controls, stated
>
> (d) clears a positive control — proximity
> residualised on itself lands at **0.5000 exactly**, 105/105 — and a negative
> one: a permuted-label null centres on **0.4993 ± 0.0110** with **0 of 100**
> replicates reaching the observed value (z = 8.69). We ran the negative control
> because we had found the same omission invalidate one of our own headlines a
> day earlier.
>
> It remains an *upper bound* — a high-capacity model on one cohort — and the
> proximity-excluded variant (0.602) has not had its own separate null.

---

## 3. Feasibility & Resource Requirements

At full resolution — one qubit per residue, the convention every number in this
document uses — the register needs **169–704 qubits and 3.3M–124.9M two-qubit
gates**. Louvain coarse-graining to a NISQ-plausible 10–15 qubits destroys most of
the ranking signal (retention Jaccard 0.00–0.18) without reaching hardware-usable
fidelity.

Against a real IBM device calibration snapshot, every mandatory target verdicts
**`FAULT_TOLERANT_ONLY`**, at both resolutions. We checked both hardware routes
named in the challenge's own bibliography; neither changes this picture.

This is why the proposal in §2 is classical-plus-quantum-inspired rather than
hardware-targeted. The resource picture was measured before the framing was
chosen, not after.

---

## 4. Expected Impact

*New section — absent from the previous draft, mandated by §4.3*

**What a successful PoC would demonstrate:** that cryptic-pocket method claims in
this field are currently uncertifiable, and that a validated instrument changes
which published results survive.

| Target | Quantitative goal | Baseline today |
|---|---|---|
| Certified apo/holo pairs | ≥ 40 pairs passing the blind validity rule | 7 audited, 2 pass |
| Apo vs stripped-holo delta | Reported for ≥ 100 structures | Never reported |
| Combined readout | Residual AUC ≥ 0.60, LOPO, with a null | 0.595, null passed |
| Re-audit of published claims | The 84% headline decomposed | Done: it is a six-way disjunction |

That last row is the shape of the impact. The field's leading reported figure —
84% recovery — is **99/118 structures detected by *at least one* of six
measures**. Requiring three of six drops it to 57.6%; requiring all six drops it
to 17.8%. The number is real and correctly computed. What it measures is not what
a reader assumes.

---

## 5. Validation Plan

*Guidelines §8 calls this "one of the strongest differentiators"*

Already built and in use, not proposed:

- **Proximity floor** — every score must beat the strongest trivial baseline
  (degree, hop, Euclidean distance from seed), not chance.
- **Spatially-correct nulls** — three generations, each fixing a measured defect
  in the last.
- **Positive control with a measured limit of detection** — a planted,
  confound-orthogonal coupling; under the corrected null no target reaches 80%
  power up to ~4× background conductance.
- **Cluster-robust inference by structure** — exact cluster-level permutation,
  after four selection procedures in our own register died of pseudo-replication.
- **Program-level multiplicity budget**, stated with its redundancy correction and
  its own limit.
- **Firewall / frozen-context provenance** — an unforgeable stamp preventing a
  claimed-frozen result from rendering unbannered.

**Added because we found we had been running it asymmetrically:** a mandatory
*negative* control alongside every positive one. We had consistently verified that
a test can detect signal and never that it refuses noise. That omission produced a
false headline in our own register within the last week. It is now applied — the
constructive result in §2(d) carries a permuted-label null, and running it is what
let us promote that result from a lead to a finding.

---

## 6. Hybrid / Cross-Domain Architecture

Classical ENM ensemble generation → quantum-inspired transport subroutine →
classical verification (fpocket druggability, proximity floor, null). One runner
emits all three artefacts, so the connectivity matrix, the site-level hit list and
this report cannot disagree.

> **OPEN — diagram not yet drawn.** The architecture figure is unbuilt. Also
> unresolved and more serious: the shipped demo reports P@5 with no floor, on an
> operator this register has since falsified. A judge who clicks the demo and then
> reads this document would find them in contradiction. This must be fixed before
> submission, not explained.

---

## 7. Team Capability

Three people, spanning the three disciplines this problem actually requires — and
one methodological commitment that explains the rest of this document.

| Member | Discipline | Role here |
|---|---|---|
| **Oussema Turki** | Quantum algorithms | Operator design, propagator formulation |
| **Berke Turkaydin** | Molecular biology | Target selection, structural validity, biological interpretation |
| **Bartosz Chmura** | PhD, molecular photophysics · 14 years software quality assurance | Scope and narrative decisions, verification methodology |

### Why this team produced a falsification record instead of a results paper

The appendices report five retractions in seven days, all self-found. That is not
an accident of temperament — it is **fourteen years of software quality assurance
applied to a scientific register**. QA practice supplies exactly the habits this
document is built on: separation of the party that builds from the party that
verifies; a negative control alongside every positive one; treating an
unreproduced result as unverified rather than probably fine; and the discipline
that finding your own defect before release is the cheap case.

Applied to computational science, that stance produced the audit in §1 — which is
the submission. A team without it would have shipped the +18.4% quantum figure. We
published it, tested the confound, and withdrew it the same day.

### Execution model — an explicit adversarial split

The register's ~338 tasks were produced by a role-separated agent workflow, with
the reviewing role deliberately assigned to a *different model* from the
implementing one, so that a defect and its audit do not share a failure mode:

| Layer | Model | Roles |
|---|---|---|
| Repository | Claude Sonnet | Implementers, Toolsmith, Architect/Planner |
| Repository | Claude Opus | Code Reviewer |
| Project | Claude Opus | **Adversarial Reviewer / Critic** |
| Project | Google Gemini 2.6 Pro | Critic / Reviewer / Researcher / Brainstormer |

The separation is the point, and it is measurable: **four of the five retractions
in Appendix B were produced by the adversarial reviewer role attacking work the
implementing role had just completed and believed correct.** A cross-model critic
caught the proximity confound, the missing baseline comparison, the symmetry
category error, and the miscalibrated test. This is the same
independent-verification principle QA applies to software, transplanted onto a
research register — and it is why we are able to hand you a document whose weakest
points are listed in §8 rather than discovered by a referee.

### Why we disclose this, and open the register with it

We could have described the outcome and omitted the method. We are doing the
opposite, and publishing the working repository — including the `bartosz` branch,
where the scientific register actually lives: **338 task files** (310 done), 549
commits, every retraction with its dated commit message stating the error against
ourselves, and the internal disagreements and their resolutions left in rather
than tidied out.

Three reasons. **First**, this is a Quantum *and AI* challenge that permits AI
involvement; treating our own use of it as something to minimise would be
incoherent. **Second**, the register is too large for one person to review
unaided — reviewing it properly will itself likely require AI assistance, and we
would rather say so than pretend to a reading nobody performs. **Third**, the
traces that matter are visible in it: human-in-the-loop decisions, team
disagreement, and how conflicts were resolved. That record is the evidence for
every capability claim on this page.

Science is science, tools are tools, results are results — and the results here
are the same results however they were reached. What should be judged is whether
the verification was real. We have made that checkable rather than asked to be
believed.

| Artefact | What is in it |
|---|---|
| **Repository** `github.com/Oussema-t/Quantum_allosteric-scanner` | The scanner, the pipeline, the analysis scripts behind every number in this document. |
| **Branch `bartosz`** | 338 task files · 310 done · 549 commits · the full falsification record |

> **INCOMPLETE — awaiting detail.** Oussema and Berke's specific backgrounds and
> prior work are placeholders above pending their own text. They are named with
> disciplines only; nothing has been attributed to them that they have not
> supplied.

---

# Appendix A — Claims ledger

Every load-bearing claim, with its current verdict as of 2026-09-02. This is the
material the six-page limit cannot hold and the §4.4 appendix allowance exists
for.

**Verdict key:** HOLDS · QUALIFIED · RETRACTED · UNDETERMINED

| Claim | Verdict | Evidence |
|---|---|---|
| No single observable survives conditioning on proximity — 7 of 7 tested | **HOLDS** | Best residual is `persistent_h2_void` at +12.0% — p = 0.107 uncorrected, on 45 of 108 structures. Nothing positive reaches even an *uncorrected* 0.05. The one cell that does is `dcc_low`, and it is **negative** (0.4445). Chiral circulation, orthogonal *by construction*, went 0.5560 → 0.4960. |
| Walk occupation is **80% proximity** — the single measurement behind the Appendix B retraction dated 2026-09-01, not independent corroboration of it | **HOLDS** | Share of ranking signal falls from **+18.4%** raw to **+3.7%** residualised: 1 − 3.7/18.4 = **80.0%**. Separately, ρ(occupation, proximity) = +0.735 — a *different* quantity (ρ² = 54%), reported here because the two do not agree and we no longer use ρ² to estimate shrinkage. Reproduced from scratch to 4 dp by an independent harness. |
| P@5 = 0.000 on all three mandatory targets | **HOLDS** | Deployed operator, re-run after a stale-artifact fix |
| On 108 annotated structures, nothing we have beats random at P@5 | **HOLDS** | Design has power: their own propensity beats random at p = 5×10⁻⁹ |
| The published 84% is a six-way disjunction | **HOLDS** | 99/118; ≥3 of 6 → 57.6%; all 6 → 17.8% |
| 5 of 7 standard targets fail a blind validity audit | **HOLDS** | Pre-registered rule: **1 of 3** mandated targets valid, **1 of 4** from the challenge's own recommended database. A *separate* audit of 29 apo depositions supplies two of the mechanisms, both previously unreported. |
| Instances are not computationally hard | **HOLDS** | Fixed backbone: treewidth 2–5, exact optimum in < 0.16 s. Coupled backbone + rotamer: median 5, max 7 at realistic window size — still far below the ~50–80-residue regime where a hard instance appears. |
| Hardware verdict is `FAULT_TOLERANT_ONLY` | **HOLDS** | Both resolutions, real device calibration |
| No structural descriptor predicts which method suits which protein | **HOLDS** | Size, chains, fold class, site separation all null against a working positive control |
| Combined readout reaches residual AUC 0.595 — our strongest constructive result, and the only one clearing both controls | **HOLDS** | 105 structures, 74 proteins, leave-one-protein-out; cluster-robust p = 1×10⁻⁵. *Positive control:* proximity residualised on itself → 0.5000 exactly, 105/105. *Negative control:* permuted-label null 0.4993 ± 0.0110, **0 of 100** reps reach the observed value, z = 8.69. Holds at 0.6017 with both proximity features removed. *Caveat: a high-capacity model, so this is an upper bound, on one cohort.* |
| Hamiltonian potential terms carry residual signal once geometry and proximity are controlled for — deliberately not worded as "beat geometry", because they do not | **QUALIFIED** | Two different questions, both answered. *Residualised:* retains signal, 0.740 → 0.660, p = 0.027. *Head-to-head:* **loses** to plain geometry, 0.751 vs 0.795, p = 0.29. And the published margin was a 5-column fitted model against a 1-column unfitted score — matched unfitted, it is 0.599 vs 0.575. |
| The quantum contribution is larger than the 5–10% Shapley estimate | **RETRACTED** | Withdrawn 2026-09-01. The unconditioned AUC inflated it; the more rigorous earlier method had it right |
| The site-distance distribution is a continuum with no discrete classes | **RETRACTED** | Rested on a test with too little power at the relevant separation (~40% at n = 26). A stronger "zero power" version of this was itself withdrawn — the original figure compared a separation in sample-SD units against a power curve in component-SD units. |
| Whether that distribution is multimodal | **UNDETERMINED** | Both available tests are miscalibrated, in opposite directions |

---

# Appendix B — What we retracted, and how fast

Offered as the team-capability evidence for §7. Each of these was found by our own
adversarial review thread, not by a referee, and each is committed with a dated
message stating the error against ourselves.

| Date | Retraction | Found by |
|---|---|---|
| 2026-08-26 | KRAS_G12C's "apo" structure was drug-bound; 8 of 10 candidates in the replacement pool were too. Headline re-run, and it got worse. | Live re-verification |
| 2026-09-01 | The quantum arm's +18.4% is 80% proximity (residualises to +3.7%, n.s.). Withdrawn the same day it was published. *Same measurement as the Appendix A row above.* | Confound test |
| 2026-09-01 | Our best constructive number was never compared against the strongest baseline. It loses to it. | Reviewer audit |
| 2026-09-01 | A directional "quantum" effect was a category error: the operator is symmetric to machine precision, so the effect was arithmetically impossible. | Reviewer audit |
| 2026-09-02 | A multimodality headline rested on a test that rejects unimodal data 52–68% of the time. Retracted the day after it landed. | Negative control |

---

# Appendix C — Known defects, disclosed

Phase-2 criteria explicitly score whether constraints are *"honestly assessed."*
These are findable by any referee reading our repository, so we name them first.

- **No family-wise multiplicity control** across roughly fifty analyses. No
  surviving claim sits below p = 0.019 — which is the signature of a large
  unrecorded family, not of a robust effect.
- **Two incompatible definitions of "AUC"** were in simultaneous use. One fits a
  model per fold and silently flips sign on anti-correlated features, so it
  measures magnitude of discrimination, not direction. Every solo figure computed
  that way needs its directional value reported beside it.
- **Negative controls were omitted systematically** until two days ago. We
  verified that tests detect signal and never that they refuse noise; this
  produced one false headline in the last week. Now applied to the §2(d) result,
  and being retrofitted to the rest — most existing verdicts in the register have
  still never faced one.
- **Modality is undetermined.** Two tests, miscalibrated in opposite directions,
  produced our two contradictory verdicts. Neither was earned.
- **One external comparator has no number attached.** ProteinLens was confirmed
  live but is browser-only with no API. Flagged, not skipped.

---

## 8. Attack these first

The seven places we think this document is weakest, with our current answers. An
adversarial review is more useful aimed than unaimed — if you break something not
on this list, that is more valuable still.

**01 — "What is actually quantum about this?"**
Our single weakest point. We propose a benchmark and a classical readout, and we
concede the formalism is classically simulable. Our defence is that §4.1 asks for
advantage *or insight* and we take the second disjunct explicitly. Press on
whether an ideation panel will accept that.

**02 — "Your one constructive result is a ceiling from a high-capacity model."**
It now clears both controls — the permuted-label null landed while this draft was
being written (0.4993, 0/100 reps, z = 8.69). What remains arguable is that a
gradient-boosted combination of features is an *upper bound*, on a single cohort,
and that we have not shown any deployable ranker achieving it. Press there.

**03 — "You flip-flopped on multimodality twice in three days."**
True. Both reversals were self-caught, and the second found that both available
tests are miscalibrated. Ask whether that reads as rigour or as instability — we
genuinely do not know how it lands on a referee.

**04 — "How much of this is independently reproduced?"**
Honestly: one result. An independent from-scratch harness reproduced the proximity
confound to four decimal places. Most of the rest is single-implementation.

**05 — "No multiplicity control across ~50 analyses."**
Conceded in Appendix C. No survivor below p = 0.019. Ask whether disclosing this
helps us or simply hands a referee the weapon.

**06 — "Is a certifying benchmark a Phase-2 deliverable, or a paper?"**
Unresolved, and the most consequential strategic question here. If the panel wants
a quantum PoC, our proposal may be well-argued and off-brief.

**07 — "Heavy AI involvement — won't a panel discount this as machine-generated?"**
**Decided: we disclose fully and open the register.** The counter-argument is that
in a Quantum-and-AI challenge that permits AI use, hiding it would be incoherent —
and that what should be judged is whether the verification was real, which we have
made checkable. Challenge the decision if you disagree; it is deliberate, not an
oversight. The narrower version worth pressing: does opening 338 task files help a
reviewer, or simply give them 338 places to find something we missed?

### What we specifically want from this round

- A ruling on **01** and **06** — both are positioning calls, not technical ones,
  and they determine whether the rest of the document is the right document. **07**
  is decided; argue us out of it if you can.
- Whether Appendix C should ship. It is unusual to volunteer this, and we may be
  wrong that honesty outscores exposure.
- Anything in Appendix A you think we have graded too generously. The QUALIFIED
  rows are where we are least confident of our own calibration.

---

*Team AuraQu · Cleveland Clinic Quantum Allosteric Scanner*
*Draft v1 · 2026-09-02 · restructured onto Guidelines §4.3's seven-item ToC*
*Open: §6 architecture diagram · two team biographies · demo/report consistency · multiplicity budget across the register*
