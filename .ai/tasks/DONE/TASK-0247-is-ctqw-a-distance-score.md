# TASK-0247 — Is the CTQW score anything more than a re-encoded distance-from-seed

- Status: DONE
- Assignee: Reviewer thread
- Filed & completed: 2026-08-24
- Related: [[TASK-0238]], [[TASK-0242]], [[TASK-0244]], [[TASK-0248]], [[TASK-0249]]

## Context

Filed retroactively. This analysis was run inline by the Reviewer thread on
2026-08-24 while answering a direct question, and its results were written to
`RESULTS.md` and cited there as `[[TASK-0247]]`. This file exists so that
citation resolves and the work is registered rather than living only in a
results section — per [[TASK-0195]]'s task-ID citation discipline.

## Done

NO, it is not a distance score: within-shell AUC 0.6305 (median), above 0.5 on 8/9 targets, Wilcoxon p=0.0273; only ~39% of its variance is a function of hop shell. BUT its non-distance signal is indistinguishable from the best geometric baseline within-shell (0.6305 vs 0.6292, 4/9 wins, p=0.4961). Correct statement: adds nothing over the FULL GEOMETRY BLOCK, not 'adds nothing over proximity'.

**Script:** `scripts/task0247_is_ctqw_a_distance_score.py`
**Data:** `results/tasks/0247_ctqw_vs_distance/`
**Write-up:** `RESULTS.md`, the dated [[TASK-0247]] section.

**2026-08-26 note ([[TASK-0272]]):** this task's own KRAS_G12C row (both
tables) was computed on `4OBE`, since found misannotated (wild-type, not
G12C — [[TASK-0270]]). Kept as a historical artifact, not recomputed.
**Checked, not assumed**: KRAS_G12C's within-shell AUC (0.5595) is not the
median-determining row in either table (PTP1B, 0.6305, occupies that
position in both) — the headline median claims are not directly set by
this row. KRAS_G12C *is* the single most extreme value in the
"ctqw − best geometry" gap column (−0.2344, driven by an unusually high
`euclid` baseline on this target) — a reader should not treat that one
data point as representative of the register going forward, independent
of the genotype question.
