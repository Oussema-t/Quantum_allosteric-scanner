# TASK-0296 — 6 backend tests fail on stale KRAS_G12C golden values

- Status: TODO
- Priority: Medium — not a regression, but a red suite hides the next real one
- Filed: 2026-08-29 by Reviewer thread (promoting [[TASK-0290]]'s flagged-but-unfixed finding out of a DONE file)
- Related: [[TASK-0290]], [[TASK-0270]]

## What

`backend/test_analysis_characterization.py` has **6 failing tests**,
pinned to KRAS_G12C golden values that went stale when the 2026-08-26
genotype fix swapped the apo structure **4OBE → 4LDJ** ([[TASK-0270]])
and the fixtures were never regenerated.

[[TASK-0290]] confirmed these are **not** a regression from its own
changes — identical failures with that task's edits fully reverted via
`git stash` — and correctly left them alone as outside LANE 1's scope.

## Why it matters

A permanently-red suite is indistinguishable from a newly-red suite. The
next real regression in this file will look exactly like today's noise.
[[TASK-0290]] and [[TASK-0293]] both had to reason around it this window.

## Scope

- [ ] Regenerate the 6 golden values against `4LDJ`, the structure
      [[TASK-0270]] adopted.
- [ ] In the same commit, record **in the test file** which structure the
      goldens are pinned to and which task set them, so the next
      structure change makes the staleness obvious.
- [ ] Confirm the suite is green afterwards, and that no *other* test was
      silently relying on the 4OBE values.

## Constraint

Regenerate from the current code path — do **not** hand-edit the expected
numbers to match. If a regenerated value looks wrong, that is a finding,
not a fixture to overwrite.
