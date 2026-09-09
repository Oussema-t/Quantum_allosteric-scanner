# TASK-0361 — Audit which published numbers are pooled and which are per-structure-averaged

- Status: TODO
- Owner: **Implementer**
- Priority: **High — it decides whether a sentence in the shipping document is fact or expectation**
- Filed: 2026-09-09 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0359]], [[HYP-P28]], [[TASK-0094]], [[TASK-0310]], [[TASK-0350]], [[TASK-0358]]

## Why

[[TASK-0359]] established [[HYP-P28]]: a score carrying **zero within-structure
position information** — every residue replaced by its own protein's mean —
reaches **pooled AUC 0.6500** on the original 108, **0.5975** on 54 brand-new
proteins, **0.6549** on the union, all at p <= 0.0006. A pure protein-identity
channel, real and replicated.

[[TASK-0359]]'s own write-up draws the correct boundary, and this task exists to
verify it rather than trust it:

> This register's existing headline numbers (raw AUC computed per structure, then
> averaged and cluster-tested) are **immune by construction** — a
> per-structure-constant score is a tie within that one structure's own ROC
> curve, contributing exactly 0.5 regardless of the constant. The finding is
> about **pooling**.

**That immunity argument is sound. What has not been checked is whether it
actually applies to each number we publish.** [[TASK-0359]] itself lists this as
explicitly not resolved: *"auditing which of this register's own already-published
numbers are actually pooled vs. per-structure-averaged."*

The submission currently rests on the assumption that our convention is
per-structure everywhere. **Assumption is not audit**, and this register's own
standing rule is to check the register before assuming.

## Intent Contract

- **Outcome:** a table classifying each in-scope published number as
  **per-structure-averaged (immune)**, **pooled (needs a protein-identity
  floor)**, or **neither/unclear**, with the producing script and line cited for
  every row.
- **In scope, in this priority order** — the ordering is load-bearing, because the
  budget may not reach the end:
  1. **Every number quoted in `PHASE1_SUBMISSION_V3.md`.** This is what ships and
     it is the whole reason the task is High. Finish this before anything else.
  2. The arms feeding [[HYP-P6]], [[HYP-P7]], [[HYP-P13]] and [[HYP-P28]].
  3. Anything else in `RESULTS.md` only if time genuinely remains.
- **Method:** read the producing code, do not re-run the analyses. The
  distinguishing signature is mechanical — one `roc_auc_score` per structure
  followed by a mean, versus concatenating residues across structures into a
  single `roc_auc_score` call.
- **For any number found to be pooled:** compute [[TASK-0359]]'s
  `protein_baseline_auc` on that number's own cohort and report the number
  against that floor, exactly as this register already reports against the
  proximity floor ([[TASK-0094]]). Reuse
  `scripts/task0359_cohort_extension_by_protein.py`'s own function; do not
  reimplement it.
- **Out of scope:**
  - Re-running or re-deriving any analysis whose aggregation turns out to be
    fine.
  - Root-causing the protein-identity channel's mechanism (the protein-size
    hypothesis is [[HYP-P28]]'s open question, not this task's).
  - The external branch's numbers. We can ask them; we cannot audit their code
    for them.
  - Changing any published number. This task **classifies**; corrections are a
    separate decision once the classification exists.
- **Constraints and invariants:** cite `file:line` for every classification —
  a verdict without a citation is not a finding. Where a number's provenance
  cannot be established, record it as **unclear** rather than guessing; an
  honest gap is a result, a guess is a defect.

## Planned Validation — audit the auditor first

Before classifying anything else, the procedure must correctly classify two
numbers whose aggregation is already known from [[TASK-0359]]'s own run:

- [[TASK-0310]]'s converged decoherent `raw = 0.5921` — **per-structure-averaged**.
- [[TASK-0359]]'s `protein_baseline_auc = 0.6500` — **pooled**.

If the procedure cannot tell those two apart, it cannot be trusted on anything
else and the task stops there.

## Pre-registered prediction

Stated before looking. **The expected outcome is that the submission's numbers are
clean**, because the per-structure convention is used consistently in the scripts
this Reviewer has read. If that holds, the value delivered is the right to write
*"every AUC in this document is computed per structure and averaged, never pooled
across proteins"* as **a checked fact rather than an expectation** — which is
worth a line in a document whose entire argument is that the field does not check
things like this.

If it does not hold, we have found in our own work exactly the defect we are
proposing to build an instrument to catch, and it must be reported that way,
without softening.

## Budget

Capped. Item 1 (the submission's own numbers) is the deliverable; items 2 and 3
are bonus. If item 1 alone consumes the budget, report it complete and the rest as
not started — do not deliver a shallow pass over everything.

## Dependency

- [[TASK-0359]] (Done) — `protein_baseline_auc`, the finding, and the immunity
  argument this task verifies.
- [[HYP-P28]] — the hypothesis this audit's results attach to.
- [[TASK-0094]] (Done) — the proximity floor, the existing precedent for reporting
  a number against a floor rather than against chance.

## Staged Files

- [2026-09-09 21:34] `.ai/COMMON.md` -- registry row
- [2026-09-09 21:34] `.ai/tasks/TODO/TASK-0361-pooled-vs-per-structure-aggregation-audit.md` -- the task file itself
