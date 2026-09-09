# TASK-0362 — Submission improvements: promote the delivered result, and reframe around the instrument

- Status: Done
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
- [2026-09-09 23:07] `__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V3.md` -- promote component (b); add the protein-identity floor
- [2026-09-09 23:07] `__WORK_IN_PROGRESS__/documentation/SUBMISSION_VERSION_LEDGER.md` -- V3 revisions block
- [2026-09-09 23:07] `.ai/COMMON.md` -- registry row status/path
- [2026-09-09 23:07] `.ai/tasks/DONE/TASK-0362-submission-improvements-instrument-spine.md` -- task file, moved to DONE

## Done, 2026-09-09 (Reviewer)

**Unblocked correctly**: [[TASK-0360]] reported Done before this was started, so
item 3's input existed rather than being guessed at.

### Item 1 — component (b) promoted, with its caveat intact

Moved into Section 1 as a fifth measurement (the count in the lead sentence
updated from "Four" to "Five"), beside the contamination audit it belongs with
rather than in the Phase-2 table. Every figure re-checked **against
[[TASK-0345]]'s own file, not against the draft's rendering of it**, per Planned
Validation: `63 pairs, 59 distinct proteins`, `+0.199`, `+0.184`, `2.6e-4`,
`[+0.102, +0.296]`, `cryptosite +0.247`, `pocketminer +0.174` — all matched
verbatim.

The "so what" is stated in-sentence as the Constraints require: those 89.8%/98.1%
headline figures describe a task ~0.2 AUC easier than the one they are read as
solving, and that gap is **larger than the margin separating most published
methods from each other**. The `n = 63, not >= 100` caveat is carried explicitly
and the >=100 remains a Phase-2 target — not dropped to make the result look
finished.

### Items 2-3 — spine, and the cascade

The detector cascade had already been folded into Section 4 by another thread
before this task started (94.8% by >=1 of four, 24.0% by all four, with
PocketMiner's different-question mechanism stated rather than treated as noise).
**Checked rather than assumed, and left alone** — re-writing a correct passage to
put this task's fingerprints on it would have been churn.

### Item 4 — the protein-identity floor, with its reach kept exact

Added to the Validation Plan as a second floor immediately after the proximity
floor, which is where floors live in this document. **The immunity sentence is
load-bearing and is stated in the same bullet**: the floor bites on *pooled* AUC
across proteins; per-structure metrics, including every number in this document,
are immune by construction. Overstating its reach would have been precisely the
error this register has criticised elsewhere.

### Item 5 — housekeeping

`SUBMISSION_VERSION_LEDGER.md` updated per [[TASK-0353]]'s format with a **V3
revisions** block: seven rows, each with what changed, why, and what must not
regress. The two entries most likely to be undone by a later editor are stated as
prohibitions: never demote (b) back to a proposal, and never drop the floor's
immunity sentence.

Also removed a `§1` cross-reference from Section 2 — house style for this
document forbids them, and it had survived earlier passes.

### Page budget — paid for, not exceeded

Net +243 words (+160 Problem Framing, +120 Validation Plan, -37 Technical
Approach). Removing the now-stale Phase-2 table row (b) and its trailing sentence
funded the promotion, as the filing predicted. **Body remains 5/6**; appendix
moved 1/3 -> 2/3.

### Planned Validation — both gates passed

Build: **RESULT: PASS**. Paper size A4, body pages 5/6, appendix 2/3, body font
10.5pt, **0 words past the printable margin**, glyph coverage clean, every `[n]`
citation resolving with none orphaned. The single standing WARN (6 characters at
7.0/7.3pt) is the known pdfplumber superscript-flattening residual, unchanged by
this task.

Every number moved or requoted was verified against its own source artifact
(`TASK-0345`'s task file; `0359_cohort_extension_by_protein/cohort_extension_result.json`
for `0.65` / `p<5e-5` / the 54-protein replication), not against the current
draft.

### Not done, disclosed

No number was changed anywhere — this task edited framing, placement and emphasis
only, per its own Constraint. [[TASK-0361]]'s aggregation audit was still running
(claimed by Implementer A at 22:56) when this closed; if it finds a pooled number
in the submission, item 4's wording must be revisited, exactly as this task's
filing anticipated.
