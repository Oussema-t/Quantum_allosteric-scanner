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

## 2. AWS Braket and Classiq accounts

§Constraint 4: *"participants will have access to AWS Braket and Classiq
services, provided as part of the challenge infrastructure at no cost."*

Neither has been used. [[TASK-0182]] ran its transpilation against a
**local** `FakeSherbrooke` calibration snapshot and a hand-built IQM coupling
map, and recorded both gaps explicitly rather than hiding them: Braket
blocked on absent credentials, Classiq never evaluated.

A reviewer will notice that infrastructure provided at no cost went unused —
and the resource/feasibility numbers are exactly the section where using it
would have carried weight.

**Needed:** accounts/credentials for both, or a decision (recorded here) that
we ship the local-simulator numbers with the gap disclosed. The second is
defensible; leaving it unstated is not.

## 3. Questions to the organisers — an under-used channel

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

**(c) Deliverable format.** §5 specifies a connectivity matrix, a top-5 hit
list, and a methodological report, without stating file formats, whether the
matrix must be dense, or whether c-Myc requires all three given it has no
ground truth. A one-line answer removes a compliance guess.

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

- [ ] Add the two-phase description document to `documentation/`.
- [ ] Add the organisational document to `documentation/`.
- [ ] Braket + Classiq accounts, or a recorded decision to ship without.
- [ ] Send organiser questions (a), (b), (c); record answers here.
- [ ] Re-verify TASK-0184's weights + ideation premise once (1) lands.

## Dependency

- Blocks full verification of [[TASK-0184]] and [[TASK-0183]].
- [[TASK-0222]] runs the Cardiac Myosin dual pair regardless of 3(a)'s answer.

## Done

—
