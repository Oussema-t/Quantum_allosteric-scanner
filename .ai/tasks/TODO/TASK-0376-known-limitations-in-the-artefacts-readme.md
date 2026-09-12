# TASK-0376 — The six-page limit binds the body, not the package: put items 13, 11 and 12 in the artefacts README

- Status: TODO
- Owner: **Implementer** for the bootstrap; **Reviewer** for the wording
- Priority: **High — three corrections we conceded were right and shelved for space that we did not actually need**
- Filed: 2026-09-12 by Reviewer thread (id via `claim.py reserve-next`)
- Source: external reviewer response, 2026-09-12 (answer to our Q3)
- Related: [[TASK-0369]], [[TASK-0370]], [[TASK-0371]]

## Why this exists: we accepted a constraint that was not binding

[[TASK-0369]] closed with three of the external review's corrections **conceded as
correct and left undone for lack of page budget**: item 13 (`NO_SIGNAL_IN_APO`'s
near-unfalsifiability), item 11 (apo-draw sensitivity), item 12 (fpocket beating
the walk by ~0.3 AUC).

The reviewer's answer to our own question about which of the six pages item 13
should displace:

> **Item 13 shouldn't displace anything.** The measurement is the cost; the words
> are nearly free… **The six-page constraint binds the body, not the package.**

That is obviously right and we missed it. The `artefacts/` README has **no page
limit**, ships with the submission, and is where a reviewer who cares about
methodology will actually look.

## In scope

### 1. Item 13 — run the paired bootstrap, then report it as a clause

`NO_SIGNAL_IN_APO` currently fires on **CI overlap** between the score and the
best trivial baseline. Two problems, both ours:

- **CI overlap is not a test of difference.** Score and floor are computed on the
  same structure and are correlated, so a paired bootstrap of `score − floor`
  gives a narrower and correct interval.
- **As constructed the verdict is close to unfalsifiable**: clearing it requires
  `score_lo > floor_hi`, i.e. AUC ≈ 0.80–0.89 on these targets. A verdict that
  could not realistically have come out the other way is not evidence, and our own
  Validation Plan's positive-control bullet warns against exactly this.

**Do:** bootstrap `score − floor` **paired** per target, and derive a **detection
limit** — the smallest ΔAUC the design could have resolved.

**Then report it as a parenthetical on the existing verdict**, the reviewer's own
suggested form:

> `NO_SIGNAL_IN_APO (paired score−floor bootstrap; detection limit ΔAUC = X)`

A clause, not a paragraph. **The method, the resampling scheme and the full CI go
in the artefacts README.**

### 2. A "Known limitations, measured" section in `artefacts/README.md`

- **Item 11 — apo-draw sensitivity.** Ten true-G12C apo structures span AUC
  **0.408–0.595, median 0.482**; the cardiac substitution moved AUC by **0.27**.
  **Each shipped hit list is one draw.** A reader holding four matrices and four
  five-residue lists cannot otherwise know that.
- **Item 12 — fpocket beats the walk.** By ≈0.3 AUC on KRAS and BCR-ABL1
  (0.835/0.860 against 0.590/0.527). **fpocket is in our own pipeline.** The
  reviewer's framing is the right one: *"more credible sitting in your own
  artefacts than omitted and found by a reviewer"* — and it is evidence the
  benchmark is trivial, which is our own thesis.
- The item-13 method and CIs from above.

**Both numbers are the reviewer's and unverified by us.** Check each against its
own artifact before it ships — see the standing rule in `COMMON.md`; this register
has been caught twice repeating a number instead of checking it.

## Out of scope

- **Any change to the six-page body** beyond item 13's parenthetical clause. If
  the clause does not fit, the clause is what gets cut, not the README section.
- The shipped residues, matrices and AUCs. This task adds disclosure, not results.
- Hit-list biology — [[TASK-0368]], with Berke.

## Planned Validation

The paired bootstrap must reproduce the existing per-target raw AUCs
(0.514 / 0.541 / 0.548) from the same code path before its own new interval is
trusted. If it cannot recover the numbers already published, the harness is wrong
and the task stops.

## Why it is worth doing at three days out

It converts three conceded-but-unaddressed criticisms into disclosed, measured
limitations, at the cost of one bootstrap and a README section — **and a
limitation we state ourselves reads as rigour, while the same limitation found by
a reviewer reads as an omission.** That asymmetry is the whole argument of the
submission, applied to the submission.
