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
