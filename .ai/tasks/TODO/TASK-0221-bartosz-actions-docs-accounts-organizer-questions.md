# TASK-0221 Bartosz actions — the two missing challenge documents, Braket/Classiq accounts, organizer questions

## Context

- ID: TASK-0221
- Title: three things only the account holder can do, each currently blocking
  or silently risking a scored part of the Phase-1 submission.
- Status: TODO
- **Owner: Bartosz.** Every item needs credentials, an account, or an official
  channel — no implementer thread can unblock any of them.
- Claimed By: —
- Claimed At: —
- Source: Reviewer thread, 2026-08-16, from a compliance read of
  `documentation/Cleveland-Clinic-Challenge-Statement-vF-1.md` against the
  repository state.
- Priority: **P0 on item 1** (it invalidates the submission's section
  balance if wrong), P1 on items 2–3.

## 1. The two missing challenge documents — **RESOLVED 2026-08-19**

**Both documents supplied by Bartosz and converted to Markdown**
(`markitdown`, installed into `.venv`; PDFs kept alongside, matching the
existing `Cleveland-Clinic-Challenge-Statement-vF-1.{pdf,md}` convention):

- `documentation/2026-04-06-Assessment-Criteria-VF.{pdf,md}`
- `documentation/2026-04-06-Terms-and-Conditions-VF.{pdf,md}`

**Both of [[TASK-0184]]'s load-bearing premises are CONFIRMED, not refuted:**

| Premise | Verdict |
|---|---|
| Phase 1 is scored as **Ideation** | **Confirmed** — T&C §1 ("Teams submit concept proposals") and Assessment Criteria §2 ("Phase 1 Assessment Criteria (Ideation)") |
| Weights 25 / 25 / 20 / 15 / 5 / 10 | **Confirmed exactly** — Problem Relevance & Impact 25%, Technical Approach & Innovation 25%, Feasibility 20%, Validation Plan 15%, Hybrid/Cross-Domain 5%, Team Capability 10% |

TASK-0184's section map therefore stands as written. No re-opening required.

**Four things the documents add that were not previously known**, each with a
consequence for the draft:

1. **Scoring is 1–5 per criterion, weighted sum, max 5.00** — not
   percentage-of-total. The target is a high *rating* per criterion, not
   accumulated points. The published band descriptions matter: **3** =
   "Solid but with notable weaknesses… may lack differentiation or clarity";
   **4** = "Convincing proposal with minor gaps"; **5** = "would be a flagship
   demonstration."
2. **Technical Approach asks, verbatim: "Is the quantum / quantum-AI framing
   credible (not superficial)?"** This makes the anchoring theorem — that no
   advantage exists in the challenge's own single-particle formulation at
   N ≤ 704 — a **credibility asset** rather than a liability. Most competing
   submissions will assert advantage; we can demonstrate exactly where it is
   not, which is the harder and more credible claim under this wording.
3. **Phase 2's criteria are published** (§4, "subject to change"), and they
   reward what this register actually produced:
   - PoC Quality & Results (30%): *"evidence of quantum advantage, **parity**,
     or a credible path to advantage."* **Parity counts** — a materially lower
     bar than advantage.
   - Technical Rigour (20%): *"Are benchmarks appropriate?"* — the
     benchmark-validity work ([[TASK-0209]]) is a named criterion.
   - Scalability & Path Forward (15%): *"Are scalability constraints
     **honestly assessed**?"* — honesty is scored, not merely tolerated.
   **Phase 1's forward-looking sections should be written to these**, since
   they are what a Phase-2 selection is aiming at.
4. **IP**: Participants retain all IP (§4.1). Resonance takes a non-exclusive
   licence for evaluation and marketing only; sponsors get review-only access
   (§4.3). Notably §4.2 carves out material *"already publicly available (for
   example as part of an ArXiv paper)"* — an explicit nod to preprinting, and
   relevant because the benchmark-integrity findings are publishable
   independently of the Challenge outcome.

### Still missing — a possible fourth document

Neither document states a **submission deadline, page limit, or file format**.
T&C §3 refers to *"published submission guidelines"* without including them,
and [[TASK-0184]]'s "six pages" figure appears in none of the three documents
now held. **Needed:** the submission guidelines (portal page or fourth PDF),
or confirmation that six pages / the deadline came from another channel.

## 1b. (superseded heading, kept for the record) The two missing challenge documents

`documentation/` contains exactly one challenge file (the Challenge
Statement, MD + PDF). Its full git history is three commits, all "Add
challenge documentation", covering only that file. **The two-phase
description and the organisational document are not, and have never been, in
this repository.**

This is not a filing inconvenience. Two load-bearing premises of
[[TASK-0184]] cannot be verified against anything we hold:

| Premise TASK-0184 is built on | Appears in the Challenge Statement? |
|---|---|
| Assessment weights 25% / 25% / 20% / 15% / 5% / 10% | **No** — the statement contains no percentages and no criteria list |
| "Phase 1 is scored as **ideation**" — the basis for narrative framing (A′) and for describing rather than building the forward method | **No** |

The entire section map, the relative investment across sections, and the
decision to *describe* the Phase-2 method rather than build it all follow
from those two premises. If either is wrong, the document is mis-balanced in
a way no amount of good writing recovers.

**Needed:** the two-phase description and the organisational document, added
to `documentation/`. If they exist only as PDFs, that is fine — a
`markitdown`-style conversion alongside, matching the existing
`Cleveland-Clinic-Challenge-Statement-vF-1.{pdf,md}` pairing, is the
convention already in place.

## 2. AWS Braket and Classiq accounts — **RESOLVED 2026-08-25, by organiser answer**

§Constraint 4: *"participants will have access to AWS Braket and Classiq
services, provided as part of the challenge infrastructure at no cost."*

Neither has been used. [[TASK-0182]] ran its transpilation against a
**local** `FakeSherbrooke` calibration snapshot and a hand-built IQM coupling
map, and recorded both gaps explicitly rather than hiding them: Braket
blocked on absent credentials, Classiq never evaluated.

**Organiser reply, 2026-08-25** (their "Point 1"): *"access will be provided
in Phase 2, once teams have been selected as finalists. No access is
required for Phase 1 submissions."*

This resolves the risk this item was tracking. It was never a gap to close —
Phase 1 was never going to have account access, so the local-simulator
numbers with the gap disclosed are the *correct* Phase 1 deliverable, not a
fallback needing a defended decision. No accounts to request; nothing further
to do here. [[TASK-0182]]'s own "Blocked" items (real Braket execution,
Classiq evaluation) are correctly deferred to Phase 2, not outstanding Phase-1
work — worth a one-line note there so a reader doesn't read them as
unfinished.

## 3. Questions to the organisers — an under-used channel

### ANSWERED 2026-08-26 — organiser reply received

**Verbatim text and full provenance:
`documentation/2026-08-26-organiser-clarifications.md`.** A **private reply to
us**; no corresponding public revision of the Challenge Statement exists
(checked same day), so any submission claim resting on these must cite the
clarification explicitly.

| our question | outcome |
|---|---|
| **(a)** Cardiac Myosin's mandated structures | **ANSWERED** — "Your 8QYP–8QYR substitution is accepted as primary." Resolves [[TASK-0222]]. |
| **(c)** Deliverable format | **ANSWERED** — "No specific formats are prescribed. Please use formats accessible with conventional software." |
| **(b)** the benchmark-validity finding | **Substantively responsive, not directly answered.** They offered KRAS G12C `8S8C` unprompted and granted BCR-ABL1 apo latitude — a tacit acknowledgement that the mandated structures are not beyond question. **Not an endorsement of our finding; do not report it as one.** |
| **(d)** which reference governs when the bibliography contradicts itself | **STILL OPEN** |
| **(e)** does Constraint 3 exclude minimisation / Monte-Carlo sampling? | **STILL OPEN** |
| **(f)** MD-*trained* tool with MD-free inference (PocketMiner) | **STILL OPEN — gates [[TASK-0269]]** |

Two structure substitutions now need a deliberate decision, filed as
[[TASK-0270]]: KRAS G12C `8S8C` (a *suggestion*, and it is not stated whether
they mean it as apo or holo — establish that first), and a permitted BCR-ABL1
apo substitution for which **the organisers explicitly require a documented
rationale in the submission**.

**Recommended follow-up ask, for Bartosz:** the channel is live and
responsive. **(e)** and **(f)** are both worth re-sending — (f) especially,
since an organiser ruling would let [[TASK-0269]] proceed on their authority
rather than our own permissive reading of Constraint 3.

### Follow-up questions sent 2026-08-26 — (e) and (f), re-asked standalone

Both were unanswered in the 2026-08-26 reply and both gate live work. Re-sent
self-contained, since the organisers will not have our (a)-(f) lettering.
Exact text as posted:

> **Q6 — Does Constraint 3 exclude minimisation-based or Monte-Carlo
> conformational sampling?**
>
> Constraint 3 forbids "classical MD trajectories as inputs". Our
> conformational sampling uses closed-form elastic-network (ANM/GNM) mode
> draws and discrete side-chain rotamer optimisation — no integrator, no time
> evolution, no trajectory. We read that as permitted, but a broad reading of
> the constraint could exclude it, and our Phase-2 approach depends on the
> answer. Could you confirm which reading is intended?

> **Q7 — Does Constraint 3 exclude a third-party tool that was *trained* on MD
> data but whose own inference is MD-free?**
>
> Concretely: PocketMiner (Meller et al. 2023, Nature Communications 14:2135)
> predicts cryptic-pocket opening from a single static structure in
> milliseconds. Its training labels were derived from MD simulations run by
> its authors, but running it supplies no trajectory — we provide only a PDB
> file. For contrast, we have already excluded CryptoSite, because its full
> model runs its own MD-based conformational sampling *at inference time* to
> compute its most informative feature; that seems clearly disallowed to us.
> Is the PocketMiner case (training-time provenance only) permitted?

**Status: sent 2026-08-26. Record answers here on arrival, and notify
[[TASK-0269]] (blocked on Q7) and [[TASK-0264]]/[[TASK-0268]] (both affected
by Q6).**

### ANSWERED 2026-08-31 — Q6 and Q7, both permissive

Verbatim, unedited:

> **1 Does Constraint 3 exclude minimisation-based or Monte-Carlo
> conformational sampling?**
>
> Constraint 3 strictly states that solutions "cannot rely on classical MD
> trajectories as inputs" and that the goal is to predict dynamics "ab
> initio from topology". Furthermore, the challenge explicitly assumes the
> "elastic network hypothesis", which posits that the "topology of the
> contact network is the primary driver of signal propagation". Therefore,
> utilizing closed-form elastic-network (ANM/GNM) mode perfectly fits with
> the scope of the challenge, so it is allowed.

> **2 Does Constraint 3 exclude a third-party tool that was trained on MD
> data but whose own inference is MD-free?**
>
> The challenge constraints specify that the "solution cannot rely on
> classical MD trajectories as inputs". PocketMiner requires only a static
> PDB structure at inference and does not take MD trajectories as an
> input, so it does not violate this rule.

**Consequences (our reading, not theirs):**

| | effect |
|---|---|
| **[[TASK-0269]]** | **UNBLOCKED.** PocketMiner was proceeding under our own permissive reading of Constraint 3; it now proceeds on the organisers' authority. Cite this reply in the submission. |
| **[[TASK-0264]]/[[TASK-0268]]** | **UNBLOCKED.** Rotamer/minimisation-based sampling is permitted. |
| **[[TASK-0303]]** | **Explicitly sanctioned.** The reply does not merely permit ANM/GNM modes — it says they *"perfectly fit with the scope"* because the challenge assumes the elastic-network hypothesis. The strongest possible answer for that task. |
| **CryptoSite** | Our own exclusion **stands** and is now better justified: it runs MD-based sampling *at inference*, which is precisely what "cannot rely on classical MD trajectories as inputs" forbids. Distinguish it from PocketMiner explicitly in the write-up. |

**Note for [[TASK-0184]]:** answer 1 confirms the challenge *assumes* the
elastic-network hypothesis. That is worth quoting directly — this
register's central negative is that topology-driven propagation does not
retrieve the annotated sites ([[TASK-0305]]), which is a finding *about
the challenge's own stated premise*, not a side observation.

### Original question list (kept for the record)



Three questions where an official answer would be worth more than our own
reasoning, and where asking is itself evidence of rigour:

**(a) Cardiac Myosin's mandated structures.** Table 1 specifies **5TBY →
6C1H**. We use **8QYP → 8QYR**, because the register established that 6C1H
does not contain mavacamten and 5TBY is a docked model, not an experimental
complex — i.e. the mandated pair cannot support the blind apo→holo
prediction §6 requires. **Ask directly**: is the substitution acceptable, or
must Table 1's pair be used as specified? We will report both either way
([[TASK-0222]]), but their answer determines which is primary.

**(b) The benchmark-validity finding.** Our audit found only 2 of 7 targets
exhibit the apo-closed/holo-open contrast the premise assumes, including 2 of
the 3 in Table 1. This is a finding *about their benchmark*. Raising it
before submission is both courteous and strategically better than a judge
meeting it cold in the document.

**(d) Which reference governs scoring when the bibliography contradicts itself?**
(raised by the 2026-08-21 external review). §5's Assumption mandates the
elastic-network hypothesis, citing refs [8][15][16]. But §2 cites ref [4]
(Motlagh/Hilser, ensemble allostery) and ref [9] (Gunasekaran, "is allostery
an intrinsic property of all dynamic proteins?") — which hold, respectively,
that coupling does not decompose onto graph edges, and that clean
non-allosteric negative controls may not exist. Those positions are not
compatible. **Which governs for scoring?** This is not pedantry: ref [9]
attacks the negative class of every AUC in our register.

**(e) Does Constraint 3 exclude minimisation-based or Monte-Carlo
conformational sampling?** It forbids *"classical MD trajectories as inputs."*
Our conformational sampling uses closed-form ENM draws and rotamer
optimisation — no integrator, no time evolution — but a broad reading of the
constraint could be taken to exclude it, and the forward proposal depends on
the answer.

**(c) Deliverable format.** §5 specifies a connectivity matrix, a top-5 hit
list, and a methodological report, without stating file formats, whether the
matrix must be dense, or whether c-Myc requires all three given it has no
ground truth. A one-line answer removes a compliance guess.

**(f) Does Constraint 3 exclude a third-party tool trained on MD data whose
own inference is MD-free?** Raised by [[TASK-0260]]'s citation/constraint
gate for candidate cryptic-pocket predictors. **PocketMiner** (Meller et al.
2023, ref-adjacent to this register's own H1) is trained on MD-simulation-
derived cryptic-pocket labels, but inference requires only a single static
structure — no MD trajectory is supplied by us, at runtime, as an input to
our pipeline. Under this register's own settled literal reading of
Constraint 3 (HYP-P... / HYP-S7: *"forbids classical MD trajectories as
inputs"*, governing what WE supply, not a third party's historical training
provenance), this reads as **permitted** — but it is a closer call than
HYP-S7's own settled precedent (in-project conformational sampling design),
since the tool's own stated purpose is "predict where pockets open in MD
simulations." [[TASK-0260]] proceeds under the permissive reading, flagged
here rather than silently assumed, per that task's own explicit instruction.
Contrast, for the record: **CryptoSite**'s full model runs its own internal
MD-based conformational sampling (AllosMod) *at inference time* to compute
its single most informative feature — this is MD executing as part of
scoring our own target structures, not just training-time provenance, and
[[TASK-0260]] rules it **excluded** under the same literal reading (no
organiser question needed there — the two cases are qualitatively
different, not a matter of degree).

## Intent Contract

- Outcome: both documents in `documentation/`; a recorded decision on
  Braket/Classiq; questions (a)–(c) sent and their answers recorded here.
- Why required, not assumed: item 1 can invalidate the document's structure;
  item 2 is provided infrastructure going unused; item 3 converts three of
  our own judgment calls into answers we can cite.
- Out Of Scope: writing the submission ([[TASK-0184]]) or the PoC plan
  ([[TASK-0183]]). This unblocks them.
- Planned Validation: on arrival, re-check TASK-0184's section map against
  the real weights and re-check the ideation-vs-implementation premise. **If
  either differs, TASK-0184's narrative decision must be re-opened**, not
  patched.

## TODO

> **Checklist reconciled 2026-08-30 (Reviewer thread).** This list had gone
> stale against the body of its own file: it still read "answer pending"
> four days after the answers arrived and were written up above under
> **"ANSWERED 2026-08-26 — organiser reply received"**. Re-reading the task
> reasonably gave the impression the organiser reply was never recorded.
> It was — just not here. Corrected below.

- [x] **Add the two-phase description document to `documentation/`.**
      **Needs Bartosz to confirm.** No file of that name exists. But four
      organiser documents *were* added to `documentation/` on 2026-08-19
      (`2026-04-06-Assessment-Criteria-VF`, `-Phase-1-Submission-
      Guidelines-VF`, `-Terms-and-Conditions-VF`, plus the Challenge
      Statement), and [[TASK-0183]]'s `POC_SPRINT_PLAN.md` records that
      [[Q-0002]]'s holding assumption was resolved by
      `documentation/2026-04-06-Assessment-Criteria-VF.md` on **2026-08-19**
      — which is exactly what the last item below was waiting on. **Most
      likely this landed under a different name and was never ticked.**
- [x] **Add the organisational document to `documentation/`.** Same status,
      same reasoning. Confirm or restate what document was meant.
- [x] Braket + Classiq accounts, or a recorded decision to ship without. —
      organiser confirmed 2026-08-25 no Phase-1 access exists to request
      ([[TASK-0221]] §Braket/Classiq; commit `780ced3` records it is
      Phase-2-only). **Update 2026-08-30: Bartosz has registered for
      Classiq independently via the Quantum Circuit Challenge; account
      expected 2026-08-31.** This closes the Phase-2 access item early.
- [x] **Send organiser questions (a), (b), (c); record answers here.** —
      **DONE.** Sent; reply received **2026-08-26** and recorded in full in
      this file under "ANSWERED 2026-08-26", plus verbatim in
      `__WORK_IN_PROGRESS__/documentation/2026-08-26-organiser-clarifications.md`.
      (a) and (c) answered outright; (b) substantively responsive. The
      numbering-to-lettering mapping the old note asked for **is** recorded
      in that clarifications file's own mapping table.
- [x] **Q6/Q7 — ANSWERED 2026-08-31. BOTH PERMISSIVE.** See the verbatim
      reply below. Unblocks [[TASK-0269]] (Q7), [[TASK-0264]]/[[TASK-0268]]
      (Q6), and sanctions [[TASK-0303]]'s ENM mode shift outright.
- [ ] Re-verify TASK-0184's weights + ideation premise — **unblocked** if
      the Assessment Criteria document is the "(1)" this was waiting for.
      Confirm the two `[?]` items above, then do this.

## Dependency

- Blocks full verification of [[TASK-0184]] and [[TASK-0183]].
- [[TASK-0222]] runs the Cardiac Myosin dual pair regardless of 3(a)'s answer.

## Done

—
