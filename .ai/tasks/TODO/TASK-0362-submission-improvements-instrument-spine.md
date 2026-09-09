# TASK-0362 — Submission improvements: promote the delivered result, and reframe around the instrument

- Status: TODO
- Owner: **Reviewer or Implementer** (document work, not compute)
- Priority: **High**
- **Blocked until [[TASK-0360]] reports.** Do not start before it lands — item 3 folds its result in, and rebuilding the PDF twice wastes the page budget check.
- Filed: 2026-09-09 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0345]], [[TASK-0306]], [[TASK-0359]], [[TASK-0360]], [[TASK-0361]], [[HYP-P28]], [[TASK-0353]]

## Why

The submission currently reads as *"we tested quantum approaches and they did not
work."* Every number in it is true, but the framing undersells what was actually
built, and one section promises a measurement **we have already delivered**.

## Item 1 — Promote component (b) from a Phase-2 promise to a Phase-1 result

`PHASE1_SUBMISSION_V3.md` line ~96 currently says:

> *Component (b) is ~27 minutes of compute … We expect to report it before Phase 2
> begins rather than propose it.*

**It was run.** [[TASK-0345]] (Done, 2026-09-07/08):

> 63 pairs, 59 distinct proteins. Stripped-holo minus true apo:
> **mean +0.199, median +0.184.** Wilcoxon p=2.6e-4; sign-flip permutation
> p<1e-4 (B=10000); bootstrap 95% CI **[+0.102, +0.296]**, excluding zero by a
> wide margin. Same sign in both source cohorts (cryptosite +0.247,
> pocketminer +0.174).

This is a delivered, significant, and — as far as this register's survey found —
**unreported** measurement. Its "so what" is direct and must be stated: leading
methods report 89.8%/98.1% on ligand-removed holo, and ligand-removed holo is
measurably ~0.2 AUC easier than the apo case those numbers are read as solving.

- Move it into the body as a result, not a proposal.
- **Carry the caveat honestly: n=63 pairs, not the >=100 the Phase-2 success
  criterion names.** Do not quietly drop that criterion to make the result look
  complete; state the delivered n and keep the criterion as the Phase-2 bar.
- The Phase-2 table's (b) row becomes redundant once (b) is a result. Removing it
  roughly pays for the paragraph the promotion costs — see the page budget below.

## Item 2 — Reframe around the instrument, without softening a single negative

We now hold four independent demonstrations that the field's headline numbers do
not mean what a reader assumes:

| finding | number | source |
|---|---|---|
| "84% recovery" is at-least-one-of-six | 83.9% -> **17.8%** requiring all six | [[TASK-0306]] |
| stripped-holo is easier than apo | **+0.199** AUC, CI [+0.102, +0.296] | [[TASK-0345]] |
| protein-identity floor in pooled AUC | **0.65** with zero site information | [[TASK-0359]] / [[HYP-P28]] |
| detector disagreement | pending | [[TASK-0360]] |

Same evidence, better order: *we built the instrument the field lacks, and here
is what it caught.* **Every negative stays exactly as measured** — this is a
reordering and a framing change, not a softening, and any edit that weakens a
null is out of scope by definition.

## Item 3 — Fold in [[TASK-0360]]'s detector cascade

Whatever it reports. **Both outcomes are usable and the task is pre-registered
two-sided**: a shallow cascade deflates the detector-choice question and should be
reported as the deflationary result it is; a steep one becomes the fourth row
above. Do not wait for a preferred answer.

## Item 4 — The protein-identity floor as a named contribution

[[HYP-P28]] is novel, cheap to compute, and applies to every method in the field.
State it in the Phase-2 instrument section as a floor the benchmark enforces,
alongside the proximity floor.

**Precision that must not be lost** (getting this wrong would be the exact error
we have criticised elsewhere): the floor bites on **pooled AUC across proteins**.
It does **not** bite on P@5 or on any per-structure-then-averaged metric, which
are immune by construction. Do not overstate its reach.

## Item 5 — Housekeeping

- Update `SUBMISSION_VERSION_LEDGER.md` per [[TASK-0353]]'s format: what changed ·
  why · what must not regress.
- Re-run the LaTeX build; **every compliance check must PASS** before this task
  closes.

## Constraints And Invariants

- **Style rules already established for this document, non-negotiable**: no
  internal framing, no section-symbol cross-references, no task ids, no
  "collaborators" — "we" throughout. Every finding answers "so what?" explicitly.
- **Page budget: the body is at 5 of 6 pages.** Additions must be paid for. The
  redundant (b) row is the identified source of slack; if more is needed, tighten
  rather than delete a result.
- **No number changes.** This task edits framing, placement and emphasis. If a
  number looks wrong, stop and file separately rather than correcting it here.
- **[[TASK-0361]] may land mid-flight.** If its audit finds a pooled number in the
  submission, that supersedes item 4's wording and must be reflected, not deferred.

## Planned Validation

- The LaTeX build reports PASS on paper size, body pages, appendix pages, body
  font, horizontal overflow, glyph coverage and citations.
- Every number moved or requoted is checked against its own source artifact,
  not against the current draft's rendering of it — a transcription error
  introduced while promoting a result would be worse than leaving it in the
  Phase-2 table.

## Dependency

- [[TASK-0360]] (in progress) — **hard block**, item 3.
- [[TASK-0345]] (Done) — the delivered component (b) result and its numbers.
- [[TASK-0359]] (Done) / [[HYP-P28]] — the floor, and the immunity boundary.
- [[TASK-0361]] (TODO) — may supersede item 4's wording.

## Staged Files

- [2026-09-09 22:23] `.ai/COMMON.md` -- registry row
- [2026-09-09 22:23] `.ai/tasks/TODO/TASK-0362-submission-improvements-instrument-spine.md` -- the task file itself
