# TASK-0184 The Phase-1 submission — analysis freeze, narrative decision, and the six-page document

## Context

- ID: TASK-0184
- Title: freeze the analysis register, make the narrative decision explicitly,
  and write the Phase-1 ideation proposal plus the §5.3 methodological report.
- Status: TODO
- Owner: Bartosz (writing), Architect/Planner (section map, evidence pull)
- Claimed By: —
- Claimed At: —
- Source: challenge §5.3; Phase-1 assessment criteria; deadline 2026-09-15.
- **Revised 2026-07-29** (narrative framing (B) updated).
- Priority: **P0 — this is the submission. Everything else in the register is
  input to it.**

## Why this matters — the register has been treated as a results paper

Phase 1 is scored as **ideation**. The criteria ask what the team *would*
build, whether the framing is credible, and whether the plan is realistic.
The 226 scored cells, four retractions, and falsification apparatus are not
the deliverable — they are the evidence that this team's proposal is credible
and its competitors' are not. That distinction should shape every section.

**The schedule is the binding risk.** Deadline 2026-09-15; analysis freeze
2026-08-08; today is 2026-07-29. That is ~10 days of runway, and results are
still landing daily — [[TASK-0163]]'s fpocket result (a 2009 classical tool
beating every observable here on 2/3 targets) landed the same day as the
external review. **A register that never freezes produces no document.**

## ⚠️ STRUCTURE UPDATE 2026-08-19 — the Guidelines mandate a 7-item ToC, and it is not the 6 criteria

`documentation/2026-04-06-Phase-1-Submission-Guidelines-VF.md` was obtained
2026-08-19 ([[TASK-0221]]) and converted. It settles three things this task
had been assuming, and changes one.

**Confirmed:** deadline **15 Sep 2026**; concept proposal **max 6 pages**,
PDF, min 10pt, ≤20 MB; Phase 1 is the Ideation stage; the six assessment
weights are exactly as this task recorded them.

**New and material:** the proposal has its own required structure (§4.3),
**seven numbered items**, and it is *not* the six assessment criteria. Also
new: **up to 3 appendix pages** and **a link to a public code repository** are
permitted supplementary material (§4.4) — the register is this submission's
strongest asset and currently has no route into the document.

### Coverage audit — can each mandated item be argued from what we hold?

| §4.3 item | Draft section | Can we argue it? | Gap |
|---|---|---|---|
| **1. Problem Framing** — *"why quantum or quantum-AI methods offer a credible advantage **or novel insight**"* | §1 | **Yes, strongly** | The clause is disjunctive: our answer is the *insight*, not the advantage. §1 currently presents benchmark findings without explicitly answering the question as asked. Needs one paragraph stating plainly that we claim novel insight, not advantage, and why that is the honest reading of §4.1's own formulation. |
| **2. Technical Approach** — *"a clear description of the **proposed** method, algorithm, or workflow. Specify whether gate-based, variational, quantum-inspired, hybrid…"* | §2 | **Partially — largest gap** | §2 describes what was *falsified*, not what is *proposed*, and **nowhere states our paradigm**. [[TASK-0224]]'s `WORKFLOW.md` is the input; the paradigm sentence is currently missing entirely. |
| **3. Feasibility & Resource Requirements** | §3 | **Yes** | [[TASK-0183]] is Done (with its own stale-scope correction); [[TASK-0182]]'s resource table exists. Needs folding in, not producing. |
| **4. Expected Impact** — *"What would a successful PoC demonstrate?… Include any quantitative targets or benchmarks where possible."* | — | **Missing as a section** | Impact is currently folded into §1. §4.3 wants it separate, forward-looking, and **quantitative**. |
| **5. Validation Plan** | §4 | **Yes — strongest section** | Complete. §8's tips call this *"one of the strongest differentiators."* |
| **6. Hybrid / Cross-Domain** | §5 | Partially | Diagram still `[TBD]`. |
| **7. Team Capability** | §6 | **No** | `[TBD]` — needs Bartosz; cannot be written by an implementer. |

### Actions this creates

1. **Restructure the draft to §4.3's seven items.** The current six-section
   layout maps to the *criteria*, not the *required ToC*. A reviewer following
   the Guidelines will look for item 4 and not find it.
2. **Add "Expected Impact"** as its own section, with quantitative targets.
3. **State the paradigm explicitly** in item 2 (quantum-inspired / hybrid —
   decide and say it). §4.3 asks for this in terms; omitting it reads as
   evasion under a criterion that asks whether the framing is *"credible (not
   superficial)"*.
4. **Use the appendix allowance and the repo link** (§4.4). Three pages of
   figures/tables plus a public repository link converts the register from an
   unciteable asset into evidence. This is free score.
5. **Fold [[TASK-0224]]'s workflow into item 2** rather than writing the
   method description twice.

### Phase-2 criteria are now known and should shape items 3–5

`2026-04-06-Assessment-Criteria-VF.md` §4 publishes them (subject to change):
PoC Quality & Results 30% — *"evidence of quantum advantage, **parity**, or a
credible path to advantage"*; Enterprise Relevance 25%; Technical Rigour 20% —
*"Are benchmarks appropriate?"*; Scalability & Path Forward 15% — *"Are
scalability constraints **honestly assessed**?"*; Presentation 10%.

**Parity is an accepted Phase-2 outcome**, and honest constraint assessment is
explicitly scored. The register's actual position — no advantage available in
the specified formulation, a benchmark instrument, and honestly-bounded
constraints — maps onto three of those five criteria directly. Items 3–5
should be written to that, since Phase-2 selection is what they are aiming at.

## ⚠️ NARRATIVE UPDATE 2026-08-13 — framing (B) is no longer available. Read before the options below.

**Recorded by the Reviewer thread (Opus). The recommendation below (B, revised
2026-07-29) rests on two premises the register has since measured false. Its
own stated fallback now applies.**

Framing (B)'s forward half is: *"reformulate cryptic-pocket prediction as
conformational search... and place the quantum contribution at the side-chain
rotamer packing layer, which is discrete and NP-hard, rather than at the
backbone layer, which we measured is not."* Both halves are now closed:

| (B)'s premise | What was measured since | Task |
|---|---|---|
| Side-chain rotamer packing is NP-hard, so the quantum contribution belongs there | **NP-hard in general; trivial on these instances.** Packing is a pairwise MRF with treewidth 2-5 at pocket scale; the exact global optimum is found in **0.001-0.159 s** against a naive 1e14.1 search space. A hard regime exists only at m~50-80, i.e. most of a domain, not a pocket. | [[TASK-0204]] |
| Conformational search is the right reformulation | **Coupled backbone+rotamer search is not hard either**, on the one target where the objective is valid and succeeds: 13/65 restarts reach the holo basin on KRAS_G12C. TASK-0210's "tentatively OPEN" was an n=2 artifact. | [[TASK-0213]], [[TASK-0210]] |

(B) also assumed a benchmark that can express the premise. [[TASK-0209]] found
**only 2 of 7 targets show the apo-closed/holo-open contrast at all**, and 2
of the 3 mandatory targets are INVALID.

**(B)'s own sequencing-risk paragraph anticipated exactly this** — "if
[[TASK-0185]]'s prerequisite fails... the forward half weakens, and the
proposal falls back toward (A)." The prerequisite did not fail the way it
anticipated; the *layer beneath it* turned out tractable. Same consequence.

**There is now no OPEN quantum-advantage route in the register.** Nine
identified routes, all closed by measurement.

### Recommended framing (A′) — (A), sharpened by what (A) did not have when it was written

> **"The benchmark cannot certify what the challenge asks. Here is the
> measurement that shows it, and the specification for one that could."**

This is not merely a negative result, and that distinction is the whole
argument. The register produced a **validated instrument**: a blind VALID
rule with known-answer checks, an endogenous-HETATM audit, a positive control
with a measured limit of detection, proximity floors, corrected spatial nulls,
and a program-level multiplicity budget. Applied to the field's own standard
targets, that instrument finds **5 of 7 fail, for three distinct and
diagnosable reasons** — including two previously-unreported ligand confounds
(BCR_ABL1 `MYR`, GLUCOKINASE `MRK`) sitting in depositions the field uses as
"apo".

Why it scores better than (A) as originally framed:

- **Problem Relevance (25%)** — the problem is no longer "cryptic pockets are
  hard"; it is "the community cannot currently tell a working method from a
  broken one on these benchmarks," demonstrated with numbers.
- **Technical Approach (25%)** — the deliverable is the certifying instrument
  plus the screening criterion (which targets are even in a regime where a
  quantum approach could matter), not a fortieth observable. The nine closed
  routes become the *derivation* of that instrument rather than a list of
  failures.
- **Validation (15%)** — unchanged and still the strongest section.
- **Feasibility (20%)** — Phase 2 becomes "build the certifying benchmark and
  the screening criterion," which is concrete, cheap, and demonstrably within
  this team's competence because it is what the team already did once.

**What (A′) must not claim:** any quantum advantage, or that a certifying
benchmark implies one exists. The honest forward statement is that the
question is currently *unanswerable on available benchmarks*, and that fixing
that is a precondition for anyone — not just this team — to answer it.

**This remains Bartosz's call.** It is recorded here as evidence-forced rather
than preference: (B) is not a worse choice than (A′), it is a choice the
register's own measurements no longer support.

**Decided: (A′), 2026-08-13, Bartosz.** Confirmed after reading the existing
draft (`documentation/PHASE1_SUBMISSION_DRAFT.md`, already written under A′)
and this update. Recorded here in writing per this task's own TODO item —
see "The narrative decision" section below for the superseded A/B/C options,
kept for the record rather than deleted.

## The narrative decision — Bartosz's call, made once, in writing

Three coherent framings. They are mutually exclusive at the level of the
opening paragraph and cannot be blended:

**(A) "Rigorous negative + certifying-benchmark specification."**
Lead with what was falsified and the benchmark audit. Strongest on Validation
(15%) and Problem Relevance (25%); weakest on Technical Approach (25%) unless
paired with a concrete forward method.

**(B) "We were solving the wrong problem, and here is the right one."** ← *recommended, revised 2026-07-29*
Lead with the problem and the enterprise impact. Present the falsification
record as the *reason* for the proposed method rather than as the result.
The argument, which no competing team can make:

> A cryptic pocket is absent in the apo structure by definition. Static apo
> residue-scoring — the approach the challenge's §4.1 specifies, which we
> implemented in full — is therefore detecting a feature that is not in its
> input, and we measured it behaving exactly as that predicts: a proximity
> detector with no coherence dependence, beaten by a 2009 geometric tool on
> the two targets where the pocket is already open. We therefore reformulate
> cryptic-pocket prediction as **conformational search** — ENM ensembles,
> closed-form, no MD — and place the quantum contribution at the **side-chain
> rotamer packing** layer, which is discrete and NP-hard, rather than at the
> backbone layer, which we measured is not.

Strong on all four heavy criteria simultaneously: it is a problem insight
(criterion 1), a differentiated method with a measured justification
(criterion 2), it reuses machinery already built (criterion 3), and the
falsification record is the evidence (criterion 4). Requires [[TASK-0185]]'s
ensemble measurement, and is strengthened by [[TASK-0181]] Phase A.

**Sequencing risk to name honestly:** if [[TASK-0185]]'s prerequisite fails —
the known holo pocket never appears in an ENM ensemble — framing (B)'s first
half survives (the category-error diagnosis stands on [[TASK-0120]]/
[[TASK-0163]] alone) but its forward half weakens, and the proposal falls
back toward (A) with the response-coupling route as the method.

**(C) "Full quantum-advantage claim."** Not available. The register's own
evidence contradicts it and a reviewer checking the numbers would find that
out. Listed only so the decision is on the record as considered and rejected.

**Recommend (B).** It is the only framing where the falsification work becomes
an asset in the 25%-weighted Technical Approach criterion instead of a
liability, and it is honest. But it is a real choice with real trade-offs and
it belongs to Bartosz, not to an implementer or a reviewer.

**Superseded 2026-08-13 — see the NARRATIVE UPDATE section above. Decided:
(A′), not (B).** Kept below verbatim for the record of what changed and why,
per this register's own no-silent-overwrite convention.

## Section map to rubric weights

| Criterion | Wt | Section | Primary evidence |
|---|---|---|---|
| Problem Relevance & Impact | 25% | Problem + why current approaches fail | [[TASK-0169]] benchmark audit; [[TASK-0163]] fpocket; Eroom's-law framing from §3 |
| Technical Approach & Innovation | 25% | Method + what was ruled out and why | [[TASK-0185]] conformational search + the measured backbone-rarity negative; [[TASK-0181]] side-chain QUBO; [[TASK-0178]] response coupling; the anchoring theorem; the ruled-out ladder |
| Feasibility | 20% | PoC sprint plan | [[TASK-0183]]; [[TASK-0182]] resource table; measured runtimes |
| Validation Plan | 15% | Floors, nulls, LOD, positive control | [[TASK-0167]] LOD; [[TASK-0177]] consensus label; invariance protocol |
| Hybrid / Cross-Domain | 5% | Architecture diagram | classical ENM → quantum subroutine → classical verification |
| Team Capability | 10% | Roles | [[TASK-0183]]'s split |

Note the arithmetic: **Technical Approach and Problem Relevance together are
50%.** The falsification apparatus, which is this project's best work, sits
under Validation at 15%. Framing (B) is how that work gets counted twice —
once as validation rigor, once as the justification for the method choice.

## Intent Contract

- Outcome: the submitted Phase-1 proposal + §5.3 methodological report + the
  §5.1/§5.2 deliverables, all consistent with each other and with `RESULTS.md`.
- Why required, not assumed: no draft exists, the deadline is fixed, and the
  register is still moving.

- In Scope:
  - **Freeze the analysis register on 2026-08-07.** After that date, no new
    scored cell enters the proposal. Late results go to `RESULTS.md` for the
    record and, if material, to Phase 2.
  - The narrative decision, recorded in this file with reasoning.
  - Draft → adversarial panel review → revision. Reuse the existing
    `PANEL_REVIEW_*.md` convention on the *document*, not the code.
  - **Every number in the document traced to a `RESULTS.md` entry**, checked
    line by line. [[TASK-0169]] caught a stale floor (0.798, superseded by
    0.4818) inside its own filing. That will happen again in a 6-page
    compression; a numbers-audit pass is mandatory, not optional.
  - Reconcile the two branches' claims. `main` currently reports P@5 with no
    floor, on a `bartosz`-falsified operator; measured chance P@5 under its
    own `pocket_pk(tol=6.0)` metric is 0.26 on a KRAS-sized protein and a
    pure distance-to-seed predictor scores 0.66. **A judge who clicks the demo
    and then reads a paper arguing that number is an artifact will conclude
    the team does not read its own work.** Fix before submission.
  - §5.1 connectivity matrix, §5.2 hit list (site-level, [[TASK-0180]]), §5.3
    report — all emitted by one runner, all consistent.
  - The tonal constraint: Cleveland Clinic authored the premise partly being
    falsified. Frame as measurement of benchmark and method, never as
    correction of the sponsor. Lead the audit with the constructive half (the
    certifying-benchmark specification).

- Out Of Scope:
  - New experiments after the freeze.
  - Claiming quantum advantage.
  - Publishing anything not in `RESULTS.md`.

- Constraints And Invariants:
  - **Freeze date is hard.** The single largest risk to this submission is not
    a weak result; it is no document.
  - Page limit respected; overflow goes to appendix or is cut.
  - The document must not contradict `COMPETENCE_MAP.md`. If it does, one of
    them is wrong and that is resolved before submission, not papered over.
  - Negative results stated as findings, not apologised for.

- Planned Validation:
  - Numbers audit: every figure traced to its source entry.
  - Adversarial read against all six criteria, scoring the draft 1–5 on each
    as a reviewer would, and rewriting whatever scores ≤3.
  - Consistency check across proposal / `RESULTS.md` / `COMPETENCE_MAP.md` /
    `main` branch outputs.
  - **Cross-model check** (the established practice) on the *narrative*, not
    just the numbers — specifically probing whether the framing overstates.

## In Progress

None

## TODO

- [x] **Bartosz: record the narrative decision (A/B/C) in this file.**
      **(A′), 2026-08-13 — see NARRATIVE UPDATE section.**
- [x] Announce the 2026-08-07 freeze to the team.
      **Missed by 5 days; superseded by a better natural point — see "Freeze,
      revised" below. Treated as done as of 2026-08-13.**
- [ ] Section map → assign evidence owners.
- [ ] Draft §5.3 methodological report first (shortest, most constrained,
      and it forces the metric-justification argument into the open).
      **A first draft already exists** (`documentation/PHASE1_SUBMISSION_
      DRAFT.md`, written under A′) — treat as v0.1, not a blank start.
- [ ] Full draft by 2026-08-22.
- [ ] Numbers audit. **First pass done, 2026-08-13** (internal figures vs.
      `RESULTS.md`/source task files): 1 critical undisclosed caveat found
      and fixed (KRAS_G12C's apo structure `4OBE` is wild-type, not G12C —
      P@5=0.000 on all 10 true-G12C structures — now disclosed as the
      draft's own Finding 4), 1 factual error corrected (§2.4 TASK-0168
      *was* run on PTP1B and contradicted, not "untested"), 1 provenance
      fix (§2.2 interacting-multi-particle is an external-panel number),
      1 `[TBD]` filled (§1 fpocket pinned values: 0.7910/0.8618/0.5303).
      **Not yet covered**: external literature citations (Amor 2016/Wu
      2022, §3c — needs a citation check, not a RESULTS.md trace) and the
      §5 demo P@5/floor/baseline numbers (need a live `main`-branch
      re-run, tracked by this task's own "Reconcile main branch outputs"
      item below, not a document trace).
- [ ] Adversarial panel review of the draft; revise anything scoring ≤3.
- [ ] Reconcile `main` branch outputs.
- [ ] Submit before 2026-09-15.

### Freeze, revised

Original freeze date (2026-08-07) passed without being executed — the
register was still actively closing routes through 2026-08-13
([[TASK-0213]], the last one). **2026-08-13 is treated as the effective
freeze instead**, and it is a *better* freeze point than the original, not
a worse one: it lands on the day the last open quantum-advantage route
closed, so nothing left moving is decision-relevant to the narrative. Any
result after this date goes to `RESULTS.md` only, per this task's own
Constraint, unless material enough to justify reopening the freeze
explicitly (not silently).

## Dependency

- [[TASK-0183]] — Feasibility section.
- [[TASK-0182]] — resource table for §4.2/§Constraint 2.
- [[TASK-0180]] — §5.2 site-level hit list.
- [[TASK-0177]] — the label everything is scored against.
- [[TASK-0181]] — Technical Approach's forward method (framing B needs at
  least its classical result).
- [[TASK-0167.002]] — LOD, the strongest single Validation-section number.

## Open Questions

- If [[TASK-0181]]'s classical gate closes, or [[TASK-0185]]'s ensemble
  prerequisite fails, does framing (B) survive? **Partly** — see the
  sequencing-risk note above. "We tested the selection reformulation and it
  did not beat greedy" is itself a credible Technical Approach sentence, and
  the category-error diagnosis does not depend on either. But (B) weakens and
  (A) becomes safer. Decide when they resolve, not before.
- **Carry the honest negative on rare-event search into the document.** The
  1/√p amplitude-amplification argument is the first thing a quantum reviewer
  will reach for, and we measured that it fails at the backbone layer
  ([[TASK-0185]]). Stating that ourselves, with the numbers, is worth more
  than any claim we could make in its place.
- Does c-Myc get its own section? It is in the minimum set with a different
  evaluation basis (consensus + docking viability). Recommend a short
  dedicated subsection so it is visibly not forgotten.
- How much of the retraction history to include? **Recommend: a short
  paragraph, stated plainly, not hidden and not dwelt on.** Four documented
  self-retractions under a no-overwrite policy is unusual evidence of process
  quality, and a reviewer who spots it unmentioned will wonder what else is
  unmentioned.

## Done

(not yet)


---

## 2026-08-27 — Reviewer: the story is settled, and the deliverables question answered

**Written after TASK-0281 closed the last open experimental line.** Everything
below is measured and committed; nothing is pending.

### The Phase 1 deliverables — what §5 actually asks, and what we can produce

The Challenge Statement §5 requires three outputs:

1. **Connectivity Matrix** — N×N, entry (i,j) = quantum connectivity strength
2. **Hit List** — top-5 ranked predicted allosteric sites per target
3. **Methodological Report** — the quantum metric and why it proxies biology

**We can produce all three. `scripts/run_challenge.py` emits them today**
(`quantum_connectivity_matrix`, `assemble_hit_list`, `verdict_template`),
end-to-end, on live RCSB data. The artifacts are not the problem.

**The accuracy is.** Measured precision-at-5 against the true drug-contact
pocket, mandatory targets, current structures:

| target | top-5 predicted resnums | hits | P@5 |
|---|---|---|---|
| KRAS_G12C (`4LDJ`) | 31, 60, 33, 29, 27 | {60} | **0.2** |
| BCR_ABL1 (`1OPL`) | 402, 311, 310, 301, 338 | — | **0.0** |
| CARDIAC_MYOSIN (`8QYP`) | 682, 683, 681, 680, 133 | — | **0.0** |

**One hit in fifteen predictions.** Residue-level AUC 0.5565 / 0.5408 / 0.5485;
diagnosis `NO_SIGNAL_IN_APO` on two of three.

### Why this does not sink the submission — read §4.1 against the Assessment Criteria

§4.1 defines success as *"assign statistically significantly higher scores to
known distal regulatory residues compared to random background residues and
non-functional surface pockets."* **We have run exactly that measurement, and
we fail it.** Stating so is not optional.

But **Phase 1 is scored as Ideation** ([[TASK-0221]], confirmed against the
Assessment Criteria): Problem Relevance & Impact 25%, Technical Approach &
Innovation 25%, Feasibility 20%, Validation Plan 15%, Hybrid 5%, Team 10%.
**Predictive accuracy is not a Phase 1 scoring criterion.** §5's outputs
describe what the *proposed solution* generates — they are a specification of
the system, and we can demonstrate the system generates them.

The criteria we are actually scored on are the ones our work is strongest in.
Technical Approach asks, verbatim, *"Is the quantum/quantum-AI framing credible
(not superficial)?"* — and Phase 2's published criteria reward *"evidence of
quantum advantage, **parity**, or a credible path"*, *"are benchmarks
appropriate?"*, and *"are scalability constraints **honestly assessed**?"*

### The document to write

**Deliver all three artifacts. Report the accuracy failure plainly, with the
numbers above. Spend the document on why the benchmark cannot certify any
method — ours or anyone's.**

Load-bearing findings, all measured:

- **The label is geometric, not functional.** It is "residues within 4.5 Å of
  the drug in one crystal." The field establishes allostery through *coupling
  to the active site* (MD: cross-correlation, mutual information, Markov state
  populations). We predict binding geometry and call it allostery. And
  **Constraint 3 forbids MD — the challenge excludes the very method the field
  uses to establish the ground truth it asks us to predict.**
- **The benchmark is not distal.** 58% of pockets are in van der Waals contact
  with the active site (<4.5 Å heavy-atom), 27% proximal, 15% intermediate,
  **0% remote**. Only 4 of 20 targets meet a 15 Å separation bar; **none**
  meets 20 Å ([[TASK-0255]], [[TASK-0258]]).
- **Those distances are not one continuum — they are two populations, and
  nothing predicts which a protein has.** 1D k-means splits all 33 scoreable
  targets at ≈10 Å (silhouette 0.737, a 2.9 Å gap with nothing in it; Shapiro
  on log-distance p=0.0020 rejects one lognormal spread). Eight standard
  descriptors — size, shape, secondary structure, GNM stiffness, fold
  topology, packing density — are all silent under Bonferroni correction, and
  the one categorical, mechanistic candidate — does the allosteric site sit
  in a different Pfam domain from the active site — fails too (Fisher exact
  p=0.12, n=32). The split is real and currently unexplained by structure
  alone ([[TASK-0284]]).
- **The benchmark is two tasks bundled.** 9 of 20 targets are ≥80% open in apo;
  fpocket scores 0.854 on those and 0.515 — chance — on the rest
  ([[TASK-0254]]).
- **Three of six "apo" structures are not apo** ([[TASK-0278]]). BCR-ABL1's
  `1OPL` carries myristic acid **in the pocket we are asked to predict**.
- **KRAS's mandated apo was the wrong genotype** — `4OBE` is wild-type at
  residue 12. Found by us, reported, organiser-sanctioned replacement to
  `4LDJ`; the correction cost us our only clean floor-clear ([[TASK-0270]]).
- **The label is noisy.** Same-drug replicate structures agree at Jaccard
  0.42–0.88 ([[TASK-0273]]).
- **Proteins have several allosteric sites; the benchmark assigns one.** KRAS
  is 9:1 across two published sites (Switch-II, and the Switch-I/II "Tyr71"
  pocket — Mathieu et al. 2022, PMID 34558391); HCV NS5B is 2:2 fully disjoint
  ([[TASK-0280]]).

Constructive half, equally measured:

- **The physics encoding was right; the propagator was not.** `H_new`'s
  potential terms scored directly reach 0.751 against the CTQW built from them
  at 0.575, cluster-robust p=0.019 ([[TASK-0263]], [[TASK-0275]]).
- **A real signature exists and is classical.** `V_C` (GNM dynamic
  cross-correlation) separates allosteric from orthosteric sites in holo across
  two independent families, and **apo already carries it** — the apo→holo
  ceiling is a uniform null ([[TASK-0276]], [[TASK-0277]]).
- **We cannot yet say what it measures.** Three readings proposed, all three
  pre-registered and killed: efficacy ([[TASK-0279]]), coupling capacity
  ([[TASK-0281]]), stabilisation/frustration ([[TASK-0268]]). Two were ours.

### Phase 2, written to the published criteria

The named leads, each with a falsification test already specified:
[[TASK-0281]]'s docked/undocked design on a second multi-site protein;
[[TASK-0276]]'s signature tested for what it actually tracks; a
cryptic-enriched, genuinely-distal target set — which every finding above
independently argues for.

### Housekeeping before writing

- This file has ~167 uncommitted lines from an unidentified thread. **Reconcile
  before editing.**
- Q6/Q7 to the organisers are unanswered. **Do not wait.** Q7 gated PocketMiner,
  which already ran and returned a negative, so an adverse answer costs
  nothing. For Q6, state our reading of Constraint 3 and the alternative —
  naming the ambiguity scores better than an answer would have.
- Formats are unconstrained (organiser reply, 2026-08-26).
