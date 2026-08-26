# TASK-0245 — Cross-validated variance attribution — geometry / CTQW / unexplained

- Status: DONE
- Assignee: Reviewer thread
- Filed & completed: 2026-08-24
- Related: [[TASK-0238]], [[TASK-0242]], [[TASK-0244]], [[TASK-0248]], [[TASK-0249]]

## Context

Filed retroactively. This analysis was run inline by the Reviewer thread on
2026-08-24 while answering a direct question, and its results were written to
`RESULTS.md` and cited there as `[[TASK-0245]]`. This file exists so that
citation resolves and the work is registered rather than living only in a
results section — per [[TASK-0195]]'s task-ID citation discipline.

## Done

Superseded [[TASK-0238]]'s in-sample estimate. 5-fold stratified CV, 20 repeats, 9 targets. Geometry 0-84% (median 30%), CTQW -4 to +15% (median +1%, negative on 3/9), unexplained 16-108% (median 67%). Every number moved in the direction TASK-0238 predicted cross-validation would move it.

**Script:** `scripts/task0245_cv_attribution.py`
**Data:** `results/tasks/0245_cv_attribution/`
**Write-up:** `RESULTS.md`, the dated [[TASK-0245]] section.

**2026-08-26 note ([[TASK-0272]]):** this task's own KRAS_G12C row (geometry
58%, CTQW 8%, unexplained 34%) was computed on `4OBE`, since found
misannotated (wild-type, not G12C — [[TASK-0270]]). Kept as a historical
artifact, not recomputed, per `RESULTS.md`'s own no-silent-overwrite
convention. **Checked, not assumed**: KRAS_G12C's own unexplained-share
value (34%) is the 2nd-lowest of the 9 rows, not the median (67%,
PTP1B) — the headline median statistic is not directly determined by this
row. Whether the *exact* median would shift under a recomputed KRAS row
was not tested (that requires an actual re-run, out of this task's own
scope) — stated as a real limit on this note's own confidence, not
papered over.
