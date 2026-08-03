# TASK-0191 `RESULTS.md` synthesis repair — a lost section, a stale budget, a stale cross-reference

## Context

- ID: TASK-0191
- Title: recover [[TASK-0167.003]]'s never-committed `RESULTS.md` section,
  refresh [[TASK-0161]]'s multiplicity budget to the current cell count, and
  fix the stale forward-reference in [[TASK-0178]]'s section.
- Status: Done
- Resolution: done
- Resolution Note: Recovered TASK-0167.003's lost RESULTS.md section (F3); recounted TASK-0161's multiplicity budget, +140 cells across 10 tasks, new total 366, still zero confirmed positives (F5); fixed TASK-0178's stale still-TODO reference to TASK-0167.002 (F8); no scientific number re-derived
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

- [x] `git pull --rebase`; re-read `RESULTS.md`'s current section boundaries
  — branch was already up to date with `origin/bartosz` (nothing to pull);
  a concurrent thread's own staged TASK-0190 rename blocked rebase mode
  briefly, left untouched (not mine), re-read section boundaries directly.
- [x] Reconstruct the zero-plant/null-calibration section from the task file.
- [x] Recount scored cells since 2026-07-25; state the method + per-task increments.
- [x] Decide + record the diagnostic-cell counting rule.
- [x] Fix the TASK-0178 "still-TODO" reference.
- [x] Verify every cross-reference into the recovered section resolves.

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
  **Decided**: cells scored against a synthetically planted patch or a
  synthetic decoy (not the real drug-pocket answer key) do not count —
  matches the frozen table's own existing exclusion of dumbbell gates and
  negative controls. This excludes the entire TASK-0167.001/.002/.003
  positive-control program (they measure the apparatus's own operating
  characteristics, not a comparison against a real label that could itself
  be reported as a finding). Recorded in `RESULTS.md`'s new Recount
  addendum with the full exclusion table and reasons, not just this line.
- Is the recovered section's Part A worth publishing at all before
  [[TASK-0189]] lands, or does a `[PENDING]` marker read worse than the gap?
  **Moot**: [[TASK-0189]] landed same-day (2026-08-03), before this task
  picked up — the recovered section carries its corrected numbers directly,
  no `[PENDING]` marker needed.

## Done

**2026-08-03, Implementer B.** All three defects (F3/F5/F8) fixed in
`RESULTS.md`, additively — no scientific number re-derived, per the
Constraint.

**F3 (lost section) — recovered.** New `## Zero-plant specificity and
null-calibration (TASK-0167.003, 2026-07-31)` section, reconstructed
directly from `.ai/tasks/DONE/TASK-0167.003-*.md`'s own Done section (the
record survived there completely — Parts A/B/C, the concordance check, the
verdict, all present). Part A carries [[TASK-0189]]'s 2026-08-03 correction
applied directly (that task landed same day, before this one picked up, so
no `[PENDING]` marker was needed) — quoted [[TASK-0189]]'s own "quotable
as-is" verdict sentence verbatim rather than re-deriving it, per that task's
own explicit hand-off. Opens with a dated recovery-note banner explaining
the loss (commit `92aa669`'s own message, the concurrent TASK-0157 clash,
zero follow-up) — the same transparency convention this project already
uses for superseded tables, applied to a *recovered* section instead of a
*corrected* one. `grep -n "zero-plant\|null-calibration" RESULTS.md` now
returns real hits (was 0); every `TASK-0167.003` cross-reference in the
file resolves (checked directly, 5 hits, all consistent).

**F5 (stale budget) — recounted, not overwritten.** [[TASK-0161]]'s own
226-cell table is left untouched (frozen at 2026-07-25, per convention); a
new "Recount, 2026-08-03" addendum walks every task closed since then using
the *identical* method (same p-value/AUC-vs-floor/Bonferroni criterion,
same synthetic-exclusion rule), with a full per-task increment table:
+140 cells across 10 task families (TASK-0162 25, TASK-0163 6, TASK-0166 7,
TASK-0171 50, TASK-0177 14, TASK-0178 21 [self-stated], TASK-0181 3
[self-stated], TASK-0185 3, TASK-0187 1, TASK-0155 10) — new total **366**,
expected false positives **≈18.3** (was ≈11.3). Still **zero** confirmed
positives program-wide — stated plainly as a *stronger*, not weaker,
position, per the Constraint ("say that plainly rather than letting it read
as a quiet upward revision"). A parallel exclusion table names every
Done-since-2026-07-25 task that does *not* add cells, with a one-line reason
each (TASK-0160/0164/0165/0167.001-003/0169/0180/0182/0186/0188, plus
TASK-0190/0172/0176/0183/0184 excluded as not-yet-Done) — this is the
"second person can reproduce the number" requirement, checkable line by
line, not just an asserted total. Added a one-line pointer from
[[TASK-0161]]'s own open-questions row (the other place "226" appears) to
this addendum, so a reader who stops at that row isn't left with the stale
number — same top-to-bottom-consistency discipline [[TASK-0193]] applied to
`COMPETENCE_MAP.md` the same session.

**F8 (stale forward-reference) — fixed.** [[TASK-0178]]'s section no longer
calls [[TASK-0167.002]] "still-TODO"; reworded to state it was Done four
days before that section was written, and to clarify *why* TASK-0178's own
LOD probe is narrower rather than duplicative (different observable,
different scoring target — synthetic planted patches vs. this task's real
per-target specificity statistic).

**Coordination**: sequenced after [[TASK-0192]]/[[TASK-0193]] (same session,
same thread) rather than in parallel — no collision, `git status` showed
only this task's own files before staging. `git pull --rebase` found
nothing to pull (branch already up to date with `origin/bartosz`); a
concurrent thread's own staged TASK-0190 rename blocked rebase mode
momentarily and was left untouched, not stashed or discarded.

**Not attempted, explicitly out of scope**: re-deriving any scientific
number (Constraint); the open-questions-table protection convention
([[TASK-0195]]'s own territory, already filed separately); re-running
TASK-0190's own still-in-progress Rg-matched-null work.
