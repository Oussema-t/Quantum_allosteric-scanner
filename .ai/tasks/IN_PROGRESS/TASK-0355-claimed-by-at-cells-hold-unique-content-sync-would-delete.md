# TASK-0355 — `claim.py sync` would silently delete unique content sitting in 19 registry rows

- Status: In Progress
- Owner: **Toolsmith** (or whoever next needs to run a real, non-`--check` `sync`)
- Priority: Medium — no active corruption yet, but the next plain `sync` run destroys it
- Filed: 2026-09-09 by Toolsmith thread, found while cross-checking [[TASK-0352]]'s
  own findings against `claim.py sync --check`
- Related: [[TASK-0352]] (Part B; this is an adjacent finding, not a Part B output),
  [[TASK-0024]] (`sync`'s own design)

## The finding

`.ai/COMMON.md`'s "Current Rules" section states plainly: *"This table's claim
columns are no longer edited by hand (TASK-0024). `.ai/tools/claim.py sync` is
the only writer of `Claimed By`/`Claimed At`."* Ran `claim.py sync --check`
(read-only, per its own contract) while validating [[TASK-0352]]'s numbers
against it, and it reports **19 rows** where those two cells would change from
real content to `—`:

```
TASK-0035  TASK-0040  TASK-0172  TASK-0202  TASK-0204  TASK-0224  TASK-0229
TASK-0323  TASK-0324  TASK-0334  TASK-0335  TASK-0337  TASK-0338  TASK-0339
TASK-0345  TASK-0346  TASK-0348  TASK-0349  TASK-0350
```

**This is not a claim-tracking artefact — someone has been hand-editing these
two cells as extra free-text description fields**, contrary to the stated
rule. Checked `TASK-0323` directly, the content is real and **not duplicated
anywhere else in the row**:

- `Claimed By` cell: `2026-09-03` (a date, not a claimant — already a sign
  something is wrong)
- `Claimed At` cell: `14 findings (9 ready to apply, 4 NEVER TESTED, 1
  confounded) -- applied by [[TASK-0324]]`
- The row's actual `Description` cell is a separate, complete sentence about
  scope and does **not** contain that findings summary anywhere.

**`sync` would overwrite both cells to `—` on its next real (non-`--check`)
run**, since no lock file backs either value — that outcome summary would be
gone, not moved, unless something reads it out first.

## Why this is filed, not fixed here

Fixing it means deciding, per row, where 19 pieces of unique content actually
belong (most look like result summaries that belong in `Description`, or in
the free-form ninth column some later rows use for a handoff note — see
[[TASK-0341]]'s row for that convention) — a judgement call per row, not a
mechanical fix, and outside [[TASK-0352]]'s own read-only Part B scope. Filing
it plainly so **nobody runs a real `sync` before this is resolved**, and so
the fix is a deliberate, reviewed edit rather than an accidental one.

## Outcome

- For each of the 19 rows: read the current `Claimed By`/`Claimed At` cell
  content, decide where it belongs (fold into `Description`, or the free
  handoff-note convention already used elsewhere in the table), move it, then
  let `sync` reset the two cells to their real claim-derived values (`—` for
  all of these, since none currently has a live lock).
- Re-run `claim.py sync --check` afterward — 0 rows should report a change.
- Add a one-line note to `COMMON.md`'s own "Current Rules" bullet on this,
  since the existing rule statement alone evidently wasn't enough to stop it
  happening 19 times: name the two intended homes for post-hoc notes
  (`Description`, or the ninth-column handoff-note convention) so there's an
  obvious place that isn't the sync-owned cells.

## Constraints

- Read the row before editing it — some of these dates in the `Claimed By`
  cell may still be meaningful as a "when this was actually claimed"
  historical record even though the format is wrong; do not discard
  information while relocating it.
- Do not run a real `sync` on any of these 19 rows until its content has been
  moved somewhere durable.
