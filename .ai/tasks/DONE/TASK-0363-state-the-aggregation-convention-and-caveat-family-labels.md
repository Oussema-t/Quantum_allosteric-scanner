# TASK-0363 — State the aggregation convention as audited, and caveat the inherited family labels

- Status: Done
- Owner: **Reviewer**
- Priority: High
- Filed and completed: 2026-09-10 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0361]], [[TASK-0359]], [[HYP-P28]], [[TASK-0336]], [[TASK-0338]], [[TASK-0362]]

## Why

Two follow-ons that only became possible once [[TASK-0361]]'s audit landed, plus
one exposure the external branch surfaced the same evening.

**1. The convention is now a checked fact, and the document still hedged it.**
[[TASK-0361]] classified every number in the submission with `file:line`
citations and found **no pooled AUC among its own claims** — each traces to a
per-structure `roc_auc_score` call, or is a count/rate the [[HYP-P28]] mechanism
does not apply to. [[TASK-0362]]'s floor bullet said per-structure metrics are
"immune by construction", which is an argument. We can now say we checked.

**2. Our 276-family count inherits a convention we did not know we had.** The
external branch reported that its 399 "families" are **not one clustering** —
they are labels inherited from five source datasets (CASBench `CAS####`, UniProt
accessions, and free-text names), with CASBench grouping far more aggressively
than the others. **[[TASK-0336]]'s 276 was derived from that same artifact**, so
the submission has been quoting an inherited five-way convention as though it
were a clustering rule.

The claim we actually lean on survives: **McNemar is a paired test over the same
families**, so it is insensitive to how families were drawn. What is
convention-dependent is the absolute "5 of 276". Stating that is cheap and
removes the first question a referee would ask.

## Changes made

- **Validation Plan, protein-identity floor bullet**: the immunity sentence now
  reports the audit rather than the argument — *"We audited every AUC in this
  document against that distinction rather than assuming it: each is computed per
  structure and averaged, none pooled across proteins."*
- **Technical Approach, ensemble result**: added — *"The family labels are
  inherited from the source datasets rather than imposed by a single clustering
  rule, so the absolute count depends on that convention; the comparison does
  not, because McNemar is a paired test over the same families."*

Placed at the fuller technical statement rather than duplicated at the Section 1
summary, which quotes the same count in passing — one honest clause, not two.

## Not done, deliberately

- **The external branch's 0.771 identity floor** (pooled, 630 proteins — higher
  than our 0.65 and higher than any method either branch has tested) is **not
  cited**. It is their number on their cohort and we have not verified it. It
  belongs in the document only if the merge happens.
- **No family recount.** Imposing one rule (UniProt accession or a
  sequence-identity threshold) is a cohort decision for both branches, not a
  Phase-1 edit, and the comparative claim does not depend on it.
- **CAS0002 not pursued.** Of the external pipeline's 69 winning proteins, 26 are
  CAS0002 (all distal) and 21 are CAS0061 (none distal) — two families supply 68%
  of the wins, and only one contributes distal wins. A real mechanism lead, and
  **n = 1 at the family level**, which is the unit this register insists on. Not
  our data and not our five remaining days.

## Validation

Build **PASS**: A4, body **5/6**, appendix 2/3, 10.5pt, 0 words past the
printable margin, glyph coverage clean, every citation resolving with none
orphaned. Net +56 words (+39 Technical Approach, +17 Validation Plan) — inside
the page budget, no section displaced.

The standing WARN (6 characters at 7.0/7.3pt) is the known pdfplumber
superscript-flattening residual, unchanged.

## Staged Files

- [2026-09-10 06:38] `.ai/COMMON.md` -- TASK-0363
- [2026-09-10 06:38] `.ai/tasks/DONE/TASK-0363-state-the-aggregation-convention-and-caveat-family-labels.md` -- TASK-0363
- [2026-09-10 06:38] `__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V3.md` -- TASK-0363
- [2026-09-10 06:38] `__WORK_IN_PROGRESS__/documentation/SUBMISSION_VERSION_LEDGER.md` -- TASK-0363
