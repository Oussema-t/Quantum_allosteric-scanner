# TASK-0302 — Sibling-conformer pocket persistence as an independent selector signal

- Status: TODO
- Priority: **High — the strongest untried lever, and independent of everything already ruled out**
- Filed: 2026-08-30 by Reviewer thread
- Related: [[TASK-0301]], [[TASK-0300]], [[TASK-0288]], external handover §4

## Why

[[TASK-0301]] established that every rule in the 61-rule family is a
function of the same two inputs — distance-to-seed and fpocket
druggability — so ensembling, voting and confidence-weighting over them
provably cannot work. A meta-selector needs **genuinely independent**
evidence.

Whether a cavity **persists across independently solved structures** is
evidence of a completely different kind. Your agents' handover §4 already
established feasibility: **every target has siblings at >=95% sequence
identity — median 53 entries, minimum 10, none below 5** — scanned live
via `search.rcsb.org`. No MD, no Docker, fully unblocked.

## Scope

- [ ] For each target, retrieve sibling entries at >=95% identity
      (`siblings.json` in `.ai/reviews/2026-08-29 - distal pockets/`
      already holds a scan — reuse rather than re-query).
- [ ] **Apply the holo filter FIRST** (see Constraint). Report the sibling
      count surviving it per target, before any scoring.
- [ ] Align each sibling to the target apo, run fpocket, and score each
      apo candidate pocket by **fraction of siblings in which an
      overlapping cavity is detected**.
- [ ] Test persistence as (a) a standalone ranker and (b) a tie-breaker on
      top of `hop>=1 + drug_alone`, cluster-robust, against random.
- [ ] Report whether persistence is independent of pocket size and
      druggability (partial correlation) — if it is just size again
      ([[TASK-0287]]), say so and stop.

## Constraint — the circularity trap

**Most siblings are holo, and some contain the drug ligand itself.**
Scoring "pocket persistence" over structures solved *with the allosteric
drug bound* measures the ligand's own imprint, not intrinsic
persistence — the same self-fulfilling error flagged for the matched-holo
control. **Exclude at minimum the target's own `drug_ligand`, and report
results both with and without an apo-only restriction.**

## Note

[[TASK-0301]]'s dominating constraint applies: **13 clusters cannot
validate a selector.** Run this as a proof of concept and to check
independence — not as a claim. Validation belongs on the larger cohort
([[TASK-0304]]).
