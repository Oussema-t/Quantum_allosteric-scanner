# TASK-0246 — How much of the geometric contribution is hop distance, and how does it contribute

- Status: DONE
- Assignee: Reviewer thread
- Filed & completed: 2026-08-24
- Related: [[TASK-0238]], [[TASK-0242]], [[TASK-0244]], [[TASK-0248]], [[TASK-0249]]

## Context

Filed retroactively. This analysis was run inline by the Reviewer thread on
2026-08-24 while answering a direct question, and its results were written to
`RESULTS.md` and cited there as `[[TASK-0246]]`. This file exists so that
citation resolves and the work is registered rather than living only in a
results section — per [[TASK-0195]]'s task-ID citation discipline.

## Done

hop is the strongest single baseline on 5/9 targets; accounts for 46-492% of the geometry block's above-chance AUC (>100% = without it the block falls below chance). The shell profile is BANDED not monotonic: 0.93x at hop 1, 1.63x at hop 2, 1.38x at 3, 1.15x at 4, 0.69x at 5, ~0 past 6. 78% of pocket residues sit at hops 2-4, 12% beyond hop 5, none beyond hop 7. Tested whether a banded re-encoding beats the linear floor: it does not uniformly (one-hot wins 3/9, band 6/9 but lower median), so the floor stands as-is.

**Script:** `scripts/task0246_hop_contribution_anatomy.py`
**Data:** `results/tasks/0246_hop_anatomy/`
**Write-up:** `RESULTS.md`, the dated [[TASK-0246]] section.
