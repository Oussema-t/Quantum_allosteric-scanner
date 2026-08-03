# TASK-0191 `RESULTS.md` synthesis repair — a lost section, a stale budget, a stale cross-reference

## Context

- ID: TASK-0191
- Title: recover [[TASK-0167.003]]'s never-committed `RESULTS.md` section,
  refresh [[TASK-0161]]'s multiplicity budget to the current cell count, and
  fix the stale forward-reference in [[TASK-0178]]'s section.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: Reviewer thread, 2026-08-03, findings F3, F5, F8.
- Priority: **P1 — `RESULTS.md` is the synthesis a referee reads. All three
  defects are in it, and one is silent data loss already in committed
  history.**
- Dependency: [[TASK-0189]] (soft — its corrected Part A numbers should land
  in the recovered section rather than requiring a second edit).

## Why this matters

**F3 — a section that was written, deliberately not committed, and is now
gone.** Commit `92aa669`'s own message states it:

> *"RESULTS.md's own 'Zero-plant specificity and null-calibration' section is
> written but NOT included in this commit — a concurrent thread's own
> uncommitted TASK-0157 edit currently shares the same working-tree file;
> splitting them out is left to a follow-up rather than risking either
> thread's content."*

No follow-up landed. The working tree is clean and
`grep -n "zero-plant\|null-calibration" RESULTS.md` returns **zero hits**.
Both the task file's "Full detail" line and the commit message cite a section
that does not exist. Part B's calibration table — the most generally reusable
result in the whole [[TASK-0167]] series, and the evidence [[TASK-0190]]
depends on — lives only inside a task file.

This is the same failure class the Architect documented on 2026-08-03 for the
open-questions rows, and the same class as `Q-0001`/[[TASK-0107]] for
`COMMON.md`: an unprotected concurrent write to a shared synthesis file. The
underlying record survived in both cases. The synthesis did not.

**F5 — the multiplicity budget is stale, and one of the tasks that grew it
says so.** [[TASK-0161]]'s "226 scored cells" was frozen 2026-07-25. Landed
since: [[TASK-0162]] (25 reverse cells), [[TASK-0163]], [[TASK-0170]],
[[TASK-0171]] (50 holo cells), [[TASK-0177]], [[TASK-0178]], [[TASK-0185]],
[[TASK-0187]], [[TASK-0155]] (10 apo structures). `RESULTS.md`'s TASK-0178
section explicitly writes *"the ~21-cell family this task itself adds to
TASK-0161's multiplicity budget"* — and the budget table was never
incremented. The direction is safe (more cells makes "fewer positives than
chance predicts" **stronger**), but "226" is a headline figure in
[[TASK-0184]] and a referee can count.

**F8 — minor.** `RESULTS.md`'s TASK-0178 section calls [[TASK-0167.002]]'s
protocol "still-TODO." It was Done four days before that section was written.

## Intent Contract

- Outcome: `RESULTS.md` contains the recovered zero-plant/null-calibration
  section (with [[TASK-0189]]'s corrections applied), a refreshed budget table
  with a stated recount method, and no stale forward-reference.
- Why required, not assumed: each defect individually is small. Together they
  mean the document a referee reads disagrees with the task ledger it claims
  to synthesize — which is precisely the credibility this project's
  falsification apparatus was built to earn.
- In Scope:
  - Reconstruct the section from `.ai/tasks/DONE/TASK-0167.003-*.md`'s Done
    section (Parts A/B/C, the concordance check, the verdict) — the record is
    complete there. Apply [[TASK-0189]]'s corrected Part A if it has landed;
    if it has not, land the section with an explicit `[PENDING TASK-0189]`
    marker on Part A rather than publishing the known-wrong table.
  - Recount the scored-cell total by the **same enumeration method**
    [[TASK-0161]] used, applied to every task closed since 2026-07-25. State
    the method and show the per-task increments, so the next recount is
    mechanical.
  - Decide and state explicitly whether diagnostic-only cells
    ([[TASK-0171]]'s 50 holo cells, [[TASK-0067]]-style apo/holo comparisons)
    count toward the budget. [[TASK-0161]]'s original rule governs; if it is
    silent, make the call and record it.
  - Fix the "still-TODO" reference.
- Out Of Scope:
  - Re-deriving any scientific number. This is synthesis repair.
  - The open-questions-table protection convention — that is [[TASK-0195]].
- Constraints And Invariants:
  - Before editing `RESULTS.md`, `git pull --rebase` and re-read the section
    boundaries. This file has now lost content to a silent merge **twice**.
  - Use `claim.py scq-enter` to publish the intended file list before staging,
    per [[TASK-0065]] — this is exactly the visibility case SCQ exists for.
  - The budget number moves in the project's favour. Say that plainly rather
    than letting it read as a quiet upward revision.
- Planned Validation:
  - After the edit, `grep` for the recovered section heading and for every
    `[[TASK-0167.003]]` "Full detail" pointer — every cross-reference must
    resolve.
  - Recount must be reproducible: a second person following the stated method
    lands on the same number.

## In Progress

—

## TODO

- [ ] `git pull --rebase`; re-read `RESULTS.md`'s current section boundaries.
- [ ] Reconstruct the zero-plant/null-calibration section from the task file.
- [ ] Recount scored cells since 2026-07-25; state the method + per-task increments.
- [ ] Decide + record the diagnostic-cell counting rule.
- [ ] Fix the TASK-0178 "still-TODO" reference.
- [ ] Verify every cross-reference into the recovered section resolves.

## Dependency

- [[TASK-0189]] (soft) — corrected Part A numbers.
- [[TASK-0167.003]] (Done) — the source record for the lost section.
- [[TASK-0161]] (Done) — the budget being refreshed.
- [[TASK-0065]] (Done) — SCQ, the visibility mechanism to use here.

## Open Questions

- Do diagnostic-only cells belong in the multiplicity budget? Argument both
  ways: they were never used to claim a positive (exclude), but they were
  scored against real labels and could have produced one (include).
  [[TASK-0161]]'s own rule decides; if silent, this task decides and records.
- Is the recovered section's Part A worth publishing at all before
  [[TASK-0189]] lands, or does a `[PENDING]` marker read worse than the gap?

## Done

—
