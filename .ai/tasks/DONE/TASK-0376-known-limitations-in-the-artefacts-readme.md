# TASK-0376 — The six-page limit binds the body, not the package: put items 13, 11 and 12 in the artefacts README

- Status: Done
- Owner: **Implementer** for the bootstrap; **Reviewer** for the wording
- Done: 2026-09-12, Implementer B
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

## Planned Validation

Reproduced exactly, before the new CI was trusted: the paired-bootstrap harness's
own `score_auc` per target matches the committed 0.514/0.541/0.548 to <0.001 —
KRAS_G12C is bit-identical to `end_to_end.json`'s own stored value
(0.5136485966935793) to every printed digit. **PASSES.**

## Done (2026-09-12, Implementer B)

**All three items landed. Item 12 needed a real correction, not just a citation
— caught before it shipped, not after.**

### Item 13 — paired bootstrap, done

New script `scripts/task0376_paired_bootstrap_no_signal.py` reconstructs the
per-target arrays (`winner_occ`, `labels_obj.pocket`, the winning floor array)
via the identical code path `scripts/run_challenge.py::run_target` uses
(`_load_apo_holo`/`_make_candidates_builder`/`run_frozen_verdict`, imported;
the ~40-line orchestration glue between them copied, since `run_target` itself
only writes files and returns a status dict, never the arrays) — not
reimplemented. Paired block bootstrap (5000 replicates, same `block_size=10`/
`rng=default_rng(42)` scheme `metrics.block_bootstrap_ci` already uses, but one
resampled index set per replicate scoring BOTH arrays, preserving the
correlation an independent-CI check discards):

| target | score − floor | 95% CI | detection limit ΔAUC |
|---|---|---|---|
| KRAS_G12C | −0.015 | [−0.100, +0.087] | 0.093 |
| BCR_ABL1 | +0.038 | [−0.057, +0.130] | 0.094 |
| CARDIAC_MYOSIN | +0.095 | [−0.008, +0.201] | 0.104 |

Every CI includes zero — verdict unchanged, now on a falsifiable statistic
with a stated resolution (~0.09–0.10 AUC) instead of a near-unfalsifiable one.

**Body clause landed, budget-checked, not assumed to fit**: `PHASE1_SUBMISSION_
V4.md`'s two `NO_SIGNAL_IN_APO` sentences edited (one replaced with the
detection-limit clause, one de-specified to drop the now-superseded
independent-CI-overlap mechanism claim, net length within a few words of the
original). Rebuilt via `submission_build_latex.py --appendix-heading
"Appendix"`: **body 6/6 PASS** (first attempt at a fuller version of the
clause pushed to 7/6 FAIL — trimmed per this task's own Out of Scope, "the
clause is what gets cut, not the README section," rather than shipping
untested). Full method, per-target table and script/data pointers in
`artefacts/README.md` §4 ("Known limitations, measured").

### Item 11 — apo-draw sensitivity, verified as already-committed, not re-run

Traced to source rather than re-measured: [[TASK-0155]]'s own ten-true-genotype
KRAS sweep (AUC 0.408–0.595, median 0.482) and [[TASK-0124]]'s own CARDIAC_MYOSIN
apo-substitution swing (0.27) are **already-committed, Done findings in this
register** — the reviewer's number matches our own source exactly, nothing to
correct. Written into `artefacts/README.md` §4 with both citations.

### Item 12 — fpocket vs the walk: one confirmed, one reversed

Re-ran `scripts/task0163_external_baseline_scoring.py`'s own `score_target()`
fresh (not modified) against the **currently-shipped** apo structures, fpocket
provenance re-checked first (`docker run ... sha256sum qas-fpocket:4.2.3
/usr/local/bin/fpocket` → matches `PROVENANCE.json`'s
`containerized_build_TASK_0285` pin exactly — not drifted):

| target | fpocket (fresh) | our walk | direction |
|---|---|---|---|
| BCR_ABL1 | 0.860 | 0.541 | fpocket wins by 0.32 — **confirms** the reviewer's claim |
| CARDIAC_MYOSIN | 0.535 | 0.548 | fpocket does not win (already known) |
| KRAS_G12C | **0.420** | 0.514 | **the walk wins — reverses** the reviewer's claim |

**The KRAS number the reviewer quoted (fpocket ≈0.835) is stale, and the
staleness is ours, not theirs.** It traces to this register's own [[TASK-0169]],
computed against KRAS's *old* apo structure (`4OBE`, wild-type). [[TASK-0270]]
swapped the shipped apo to `4LDJ` (the genuine G12C structure) after that
number was recorded, and **fpocket was never re-run against the new structure
until this task** — `tools/fpocket/PROVENANCE.json`'s own
`containerized_build_TASK_0285` entry says exactly this ("KRAS_G12C: not
comparable... apo structure changed"), and nobody had closed that gap. Caught
here by checking the reviewer's own "unverified by us" instruction literally,
rather than transcribing the number from our own prior report. Written into
`artefacts/README.md` §4 with the correction stated plainly, not the stale
number repeated.

### Constraints honored

No change to the shipped residues, matrices, or headline AUCs (this task adds
disclosure, not results). No body change beyond item 13's clause, and that
clause was measured against the real page budget, not assumed to fit. Both
"unverified by us" numbers checked against their own artifact before shipping,
per this task's own instruction — one confirmed, one corrected.

### Not done / explicitly out of scope

- Did not re-run PocketMiner (unavailable in this environment, per TASK-0163's
  own original scope note) — item 12's table is fpocket-only, as the reviewer's
  own claim was.
- Did not investigate why the "small text" WARN (6 characters at 7.0/7.3pt,
  pre-existing, unrelated to this task's own edits) appears in the LaTeX build
  — flagged for whoever next touches that document, not chased here.
- Did not update `TASK-0169`'s own Done section to flag its KRAS number as
  apo-swap-stale — a citation-sweep task of its own, out of this task's scope
  (matches [[TASK-0206]]'s own "kept on record, not deleted" convention: the
  old number stays in TASK-0169's history, the correction lives here and in
  the artefacts README).

**Files**: `scripts/task0376_paired_bootstrap_no_signal.py` (new).
**Data**: `results/tasks/0376_paired_bootstrap_no_signal/
{checkpoint.jsonl,stdout.log,paired_bootstrap_result.json}`. **Docs**:
`documentation/PHASE1_SUBMISSION_V4.md` (item 13 clause),
`documentation/SUBMISSION_PACKAGE/artefacts/README.md` (§4, new).
