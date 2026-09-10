# TASK-0365 — V4: put the AI where the rubric looks for it, and add the funnel ablation

- Status: Done
- Owner: **Reviewer**
- Priority: High
- Filed and completed: 2026-09-10 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0363]], [[TASK-0353]], [[TASK-0348]]

## Why

Two findings from re-reading the challenge documents, and one from reading the
`allosteric` branch's own artifacts rather than a summary of them.

### 1. "AI workflows" is a rubric line about the *method*, not about how we wrote the document

`documentation/2026-04-06-Phase-1-Submission-Guidelines-VF.md`, item 6:

> **Hybrid / Cross-Domain Integration (if applicable):** Describe how your approach
> integrates quantum methods with **classical, HPC, or AI workflows**, and the
> rationale for the hybrid design.

Scored at **5%** in `2026-04-06-Assessment-Criteria-VF.md`'s Phase-1 table
(Problem Relevance 25 / Technical Approach 25 / Feasibility 20 / Validation 15 /
**Hybrid 5** / Team 10).

The submission already had a substantial AI paragraph — but in Section 7, about
the *authoring* workflow. **An external reviewer's claim that "there is no AI
anywhere in the document" was factually wrong** and was corrected in-meeting.
The narrower true statement is that Section 6's architecture ran
`ENM -> quantum transport -> classical verification` with **no AI stage**, which
answers the 5% criterion at partial credit and leaves an easy, wrong criticism
available to a rubric-driven reader.

**Note the Challenge Statement's own section 6 is "Data and Resources"** — the
"AI workflows" language is in the *Submission Guidelines*, a different document.
Getting that wrong is how the confusion started.

### 2. On generating results

`Cleveland-Clinic-Challenge-Statement-vF-1.md:91` only *encourages* open-source
frameworks "to ensure reproducibility". Reproducibility is scored explicitly in
the **Phase-2** table (30% PoC Quality "well-documented and reproducible"; 20%
Technical Rigour "workflow clearly documented and reproducible") — **not as a
separate Phase-1 criterion**, though Phase-1 Feasibility asks whether
"assumptions and constraints are clearly stated". Practical consequence carried
into this task: any number taken from the other branch must be **producible on
demand**, so each was traced to its own committed artifact before use.

## The numbers, checked against `origin/allosteric` directly

Read from the branch's own files, not from the summary we were given —
`allosteric/results/ml_model/README.md` and
`allosteric/results/classical_comparison/UNCONSTRAINED_AND_SITE_LEVEL.md`.

**Three discrepancies found, all in the direction of the summary understating
their own work:**

1. **The AI result is not purely negative, and we were told it was.** The
   summary reported only *"AI recommender, exact-winner accuracy 0.107 vs 0.137
   baseline — negative"*. The branch README labels that figure **"earlier
   tests"**. The current results are two models: **Model 1 (topology -> MIN_HOP)
   is a partial positive** — near-vs-distal AUC **0.793**, and running at its
   predicted distance gives best-cell AUC **0.924** against 0.901 for always
   using MIN_HOP=1 — while **Model 2 (topology -> operator x score) is the
   negative**, 0.625 against 0.630 for one fixed cell, 13 families against 15.
2. **Cohort differs from the headline one.** The ML models ran on **597 proteins
   / 380 families** (the round-2 testable set), not the 630/399 used elsewhere on
   that branch. Stated in the document as 597/380.
3. **The funnel ablation has a second half nobody quoted.** Unconstrained,
   closeness's strict hit count falls **48 proteins -> 6** — but its **AUC rises**,
   0.576 -> 0.626, because the base rate drops from 0.33 to 0.070. AUC is
   prevalence-insensitive and P@5 is not, so AUC *conceals* the collapse. That is
   a sharper methodological point than the hit-count drop alone.

## Changes made (V4, from V3)

- **Section 6, new paragraph** — the two learned models, with leave-one-family-out
  stated, the positive used, the negative reported as a negative, and the line
  drawn where the measurement puts it: topology carries coarse information about
  *where* to look and essentially none about *how* to look.
- **Section 6, split rationale extended** — the funnel ablation, including the
  AUC-rises-while-P@5-collapses observation and why.
- **Section 7 trimmed** — *"We report that as evidence the method of working is
  sound, not as a credential"* removed. It argued with an imagined objector; the
  facts (separated implement/verify roles on different models, a negative control
  beside every positive, cohort on every claim, five errors caught in seven days
  including our own headline, public history) carry it without the defence.

**V3 preserved on disk** per the version-history convention: `PHASE1_SUBMISSION_V4.md`
is a new file, not an edit in place.

## Validation

Build **PASS**: A4, body **5/6**, appendix 2/3, 10.5pt, 0 words past the
printable margin, glyph coverage clean, every citation resolving with none
orphaned. The additions fit inside the existing page budget — body page count
unchanged.

Every borrowed number traced to a committed file on `origin/allosteric` and
quoted at that file's own value, including where it contradicted the summary we
were given.

## Not done, disclosed

- The larger merge items the external review asked for — the two-round pipeline
  description, the MIN_HOP sweep, thirteen baselines at 630, interference at 630,
  the family-provenance audit — are **not** in V4. Several would require
  rewriting Section 6 rather than extending it, and the remaining space is one
  body page and one appendix page. **A changelist from the other branch was
  requested and has not yet arrived**; that decision is the Team Lead's.
- The identity floor is still quoted at our **0.65**, not their 0.771. Unchanged
  from [[TASK-0363]]'s reasoning: their cohort, unverified by us, merge-only.

## Staged Files

- [2026-09-10 22:59] `.ai/COMMON.md` -- V4
- [2026-09-10 22:59] `.ai/tasks/DONE/TASK-0365-v4-the-ai-stage-and-the-funnel-ablation.md` -- V4
- [2026-09-10 22:59] `__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V4.md` -- V4
- [2026-09-10 22:59] `__WORK_IN_PROGRESS__/documentation/SUBMISSION_VERSION_LEDGER.md` -- V4
