# TASK-0366 — Sweep the `allosteric` branch for positives that never reached us, verified at source

- Status: TODO
- Owner: **Explorer or Reviewer** (read-only; no compute)
- Priority: **High — 5 days to 2026-09-15, and it is the cheapest remaining route to a positive result**
- Filed: 2026-09-10 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0365]], [[TASK-0360]], [[TASK-0327]], [[TASK-0336]], [[TASK-0348]]

## Why: we already caught one, by accident

[[TASK-0365]] read `origin/allosteric`'s own committed files instead of the
summary we had been given, and found the summary **understated their own work in
three places**. The important one:

> We were told *"AI recommender, exact-winner accuracy 0.107 vs 0.137 baseline —
> negative."* Their `allosteric/results/ml_model/README.md` labels that figure
> **"earlier tests"**. The current results are two models, and **Model 1 is a
> positive**: topology → MIN_HOP separates near from distal at **AUC 0.793**, and
> running the walk at its predicted distance beats a fixed choice across the
> cohort (**0.924** against 0.901). Only Model 2 is the negative.

**A positive result was sitting in that branch, reported to us as a negative, and
we found it only because we went to check a different number.** That is not a
criticism of anyone — summaries compress, and the compression happened to drop the
half that helps. It is a reason to look systematically rather than by accident.

Also found in the same pass: the ML cohort is **597 proteins / 380 families**, not
the 630/399 quoted elsewhere; and the funnel ablation's AUC half (0.576 → **0.626**
*rising* while strict hits fall 48 → 6) was never mentioned to us at all.

## Intent Contract

- **Outcome:** a classified inventory of every result on `origin/allosteric` —
  **positive / negative / neutral**, and **present / absent from our submission** —
  with each entry traced to the artifact that produces it.
- **In scope:**
  1. Read every write-up under `allosteric/results/`: `ALL_RESULTS_SUMMARY.md`,
     `BRANCH_COMPARISON.md`, and the per-directory `RESULTS.md` / `README.md` in
     `centrality_ablation`, `challenge_targets`, `classical_comparison`,
     `full_run_1022`, `ml_model`, `pocket_seeded_sweep`, `proximity_floor`,
     `seeded_classical`, `veto_pipeline`.
  2. **For anything that looks positive, verify it against the raw artifact in the
     same directory before recording it as positive.** A number quoted in a
     write-up is a claim, not a measurement — this is the whole lesson of the
     Model 1 case and of [[TASK-0348]]'s ρ≈0.95.
  3. Record for each: the cohort (proteins **and** families — they differ between
     their own results), the metric, whether a null or baseline was used, and the
     file that produces it.
  4. Flag anything **positive and absent from our submission** as a candidate for
     the remaining space, ranked by how cheaply it can be stated.
- **Out of scope:**
  - Re-running their pipelines. Read-only.
  - Judging their methodology. We are inventorying what exists and whether it is
    supported by its own artifact.
  - Editing the submission. This task produces the inventory; the Team Lead
    decides what goes in.
- **Constraints and invariants:**
  - **Every entry cites `file:line` or a path.** An unsourced entry is not an
    entry.
  - Where a write-up and its artifact disagree, **record both and say which is
    which** — do not silently prefer either.
  - Where a result is positive but rests on a selected cell, a single family, or
    an unmatched cohort, **say so in the same row**. [[TASK-0336]] and the CAS0002
    concentration are the standing examples of exactly that failure.

## Planned Validation

Re-derive [[TASK-0365]]'s own three findings from the branch as a calibration
check — Model 1's 0.793/0.924, the 597/380 cohort, and the 0.576 → 0.626 funnel
figure. If the procedure cannot recover those three, it will not find anything
else reliably, and the task stops there.

## Pre-registered expectation

Recorded before looking, and two-sided. **Most of that branch is negative** — that
is the whole shape of both registers, and finding little is the likely outcome and
a fine one. But we have a demonstrated instance of a positive lost in compression,
one page of body space and one of appendix space, and five days. **If a second
under-reported positive exists, this is the only systematic way we will find it;
if none does, we learn that the inventory is complete and can say so.**

## Budget

Capped at one working session. Read-only, no compute. If time runs out, report
the directories covered and the ones not reached — a partial inventory that names
its own gaps is useful; a complete-looking one that quietly skipped three
directories is not.

## Dependency

- [[TASK-0365]] (Done) — the three findings this task calibrates against, and the
  reason it exists.
- `origin/allosteric` — fetchable; the branch is on the same remote.

## Staged Files

- [2026-09-10 23:13] `.ai/COMMON.md` -- V4 fixes / 0366
- [2026-09-10 23:13] `.ai/tasks/TODO/TASK-0366-sweep-the-allosteric-branch-for-under-reported-positives.md` -- V4 fixes / 0366
- [2026-09-10 23:13] `__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V4.md` -- V4 fixes / 0366
- [2026-09-10 23:13] `__WORK_IN_PROGRESS__/documentation/SUBMISSION_VERSION_LEDGER.md` -- V4 fixes / 0366
