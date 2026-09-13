# TASK-0387 — Internal contradictions a reviewer will hit in the scored documents

- Status: TODO
- Owner: Implementer
- Priority: Medium-high. Items 1–2 are near-free; 3–5 cost page budget.
- Filed: 2026-09-13 by Reviewer thread
- Source: [[REVIEW-2026-09-13-adversarial-submission-package]] §E1–E6, F4
- Related: [[TASK-0369]], [[TASK-0385]]

All five verified directly against HEAD by the Reviewer.

## 1. "We followed it in each case" is contradicted by the table underneath it

`PHASE1_SUBMISSION_V4.md:21` — *"Their reply of 2026-08-26 answered three points,
and we followed it in each case:"* The KRAS row immediately below says the
organisers suggested `8S8C` and **we rejected it**. We were right to (8S8C is
holo, MK-1084-bound — confirmed by the external reviewer and consistent with our
own check). **Being right and describing ourselves as compliant when we were not
is the worst available combination.**

Rewrite to: *"answered three points; we adopted two and, on the third, checked
the suggested structure, found it holo, and substituted a verified apo instead."*

Near-free — replaces a clause with a clause.

## 2. The deviation count disagrees across three places

| where | says |
|---|---|
| `03_Problem_Statement_Selection.md:24` | "**Four** structure choices deviate from Table 1" |
| `PHASE1_SUBMISSION_V4.md:30` footnote | "**Two** rows above are deviations, one a retention" |
| actual deviating structures | **three**: `4LDJ`, `8QYP`, `8QYR` |

Both statements are defensible about different things (rows vs structures) and
together they read as carelessness. Pick one unit, state it, make all three
agree. Doc 03's other claim — that the reasons are "in Section 1 of the Concept
Proposal" — **is now true**, so only the number needs fixing.

## 3. Our own inputs are not ligand-free, and §1 does not say so

§1's fourth finding is *"'Apo' does not mean ligand-free"* — and the proposal then
labels `4LDJ` "(apo)" (GDP + Mg) and `8QYP` "(apo)" (**ADP + VO₄ + Mg**, a
transition-state mimic), disclosing only 1OPL's myristate and omitting 1OPL's
second ligand (P16) entirely. [[TASK-0278]] already found all of this.

**We are under-reporting our own strongest evidence in the one section where a
reviewer is primed to check.** Suggested sentence, from the review and verified
against the cached structures:

> Our own three inputs are no exception: 4LDJ carries GDP·Mg, 8QYP carries
> ADP·VO₄·Mg, and 1OPL carries both myristate and an ATP-site inhibitor. All
> three are apo only with respect to the scored pocket — which is the strongest
> form of the point.

## 4. Cardiac myosin is bovine and the Concept Proposal never says so

8QYP/8QYR are *Bos taurus* Myosin-7. The artefacts README discloses it; the
**scored** document does not. This matters because our stated objection to Table
1's `6C1H` is partly a species objection (rat myosin-Ib on rabbit actin). The
defence is easy and strong — bovine β-cardiac myosin is a near-identical
orthologue of the human target, whereas myosin-Ib is a **different class** — but
we have to make it, or the asymmetry reads as convenient.

## 5. The cardiac PDB code is missing from the five-guess table

`PHASE1_SUBMISSION_V4.md:44` — KRAS, BCR-ABL1 and c-Myc rows all carry their code
in the Target column; cardiac myosin does not. Flagged on 2026-09-11, still open.
Verified still missing. Near-free.

## 6. MYC_MAX: our own config says the pocket does not exist

`targets.yaml:437` — `allosteric_pocket_exists: false`. We ship a top-5 for a
target our own configuration asserts has no folded-state pocket, and the fpocket
druggability we report (max 0.161) sits well under our own 0.5 bar. "Unverified"
is honest but incomplete. Say the harder thing:

> Our own configuration records that this target has no folded-state allosteric
> pocket; we supply the five because the challenge requires them, and we report
> that our best candidate site scores 0.161 druggability against our own 0.5
> threshold.

That is a better answer to §6's "theoretical docking viability" than the current
one.

## Done when

All six reconciled, PDFs rebuilt, body still 6/6 PASS. If page budget forces a
choice, reviewer's order is **1, 2, 5 (near-free) → 3 → 6 → 4**.
