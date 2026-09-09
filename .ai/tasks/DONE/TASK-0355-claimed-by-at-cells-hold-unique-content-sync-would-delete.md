# TASK-0355 — `claim.py sync` would silently delete unique content sitting in 19 registry rows

- Status: Done
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

## Done — 2026-09-09, Toolsmith

**Scope grew from 19 to 21 rows.** Re-ran `sync --check` at pickup (routine,
before touching anything) and it now flagged 22 rows, not 19: the original 19
plus `TASK-0352` and `TASK-0354` — both filed *after* this task, by the same
prior Toolsmith thread, and both committing the exact same mistake this task
exists to fix (`TASK-0352`'s own row even says so in its `Claimed At` cell).
The 22nd, `TASK-0355` itself, is not misuse — it's my own live claim on this
row, correctly reported by `--check` as a pending `—` -> real-value change in
the *helpful* direction sync exists for.

**The [[TASK-0341]] "ninth-column handoff-note convention" this task's own
filing cited does not exist as a working pattern — corrected here, not
silently.** Checked before reusing it: `TASK-0341`'s row is one of the ~26
`malformed_registry_row` rows [[TASK-0352]] found (11 pipe-delimited fields,
not 9 — `_parse_row()` returns `None` on it, confirmed directly against
`claim.py`'s own parser). `sync` can't see it at all, which is exactly why it
wasn't in the flagged 19/22: not a convention, an invisible row. There is no
9th column either — the table only has 9 *total* columns, and the 9th
(`Path`) is a file path in every real row. Every relocation below went into
`Description` instead, which the filing's own primary suggestion already
covered.

**Per-row disposition** (read every one of the 22 before touching anything,
per this task's own Constraint):

- **6 rows needed no edit** — `TASK-0035`, `TASK-0040`, `TASK-0172`,
  `TASK-0202`, `TASK-0224`, `TASK-0229`. Their `Claimed By`/`Claimed At`
  content is a verbatim duplicate already sitting in `Assigned To`/
  `Last Active`/`Description` in the same row (e.g. `TASK-0035`: `Claimed By`
  = `Implementer C` = `Assigned To`; `Claimed At` = `2026-08-14` =
  `Last Active`). `sync` alone loses nothing on these.
- **15 rows had genuinely unique content** — `TASK-0204`, `TASK-0323`,
  `TASK-0324`, `TASK-0334`, `TASK-0335`, `TASK-0337`, `TASK-0338`,
  `TASK-0339`, `TASK-0345`, `TASK-0346`, `TASK-0348`, `TASK-0349`,
  `TASK-0350`, `TASK-0352`, `TASK-0354`. Appended verbatim to `Description`
  under a `**[relocated by TASK-0355, 2026-09-09]:**` marker via a scripted,
  reviewable edit (`_parse_row`-based, touches only `Description`, never
  `Claimed By`/`Claimed At` — those two are left for `sync` to reset in a
  separate step) — 21 rows would be too many to hand-edit without a
  copy/paste mistake, and the script's own output (which rows it touched)
  is itself the verification that nothing was missed or duplicated.
  `TASK-0204` was the one exception worth flagging: its cells hold a real
  name + precise timestamp (`Reviewer-thread (Opus)`, `2026-08-06 20:38`),
  not prose — a genuine stale-but-accurate historical claim record, not
  hand-typed misuse. Relocated as a factual note rather than folded in as if
  it were a result summary. `TASK-0345`/`TASK-0350` also had a second,
  non-duplicate date sitting in `Claimed By` (differs from `Last Active`);
  preserved in the relocation note rather than silently dropped, per this
  task's own Constraint.
- Verified before writing: none of the 21 non-`TASK-0355` rows currently
  hold a live lock (`.ai/tasks/.locks/` has only `TASK-0258`, `TASK-0259`,
  `TASK-0355`) — `sync` resetting all 21 to `—` is the objectively correct
  target state, not a judgment call.

**Validation:**
- `git diff --stat .ai/COMMON.md` after the relocation script: exactly 15
  lines changed — matches the 15-row relocation set, confirms nothing else
  in the file moved.
- Re-parsed every row with `claim._parse_row` after the edit: still exactly
  26 unparseable (malformed) rows, same count as before — the relocation
  script didn't introduce or fix any malformed rows, confirming it's
  additive-only inside already-well-formed cells.
- Ran the real `claim.py sync` (not `--check`): 22 rows updated, matches
  the 21 target rows + `TASK-0355`'s own live claim. Output for all 21
  shows `-> '—'` with no residual free text.
- Re-ran `claim.py sync --check`: **0 rows report a `Claimed By`/`Claimed
  At` change** (the task's own stated Planned Validation, satisfied). Exit
  code is still 1, but only from the pre-existing `missing_from_table`
  warning (the ~108-row registry-abandonment backlog [[TASK-0352]] already
  found and left as its own out-of-scope finding) — unrelated to this task.
- `.ai/tools/task_reconcile.py`: re-ran, no new finding kind and no new
  instance of any existing kind attributable to this change.
- Full suite: `.venv/bin/python -m pytest .ai/tools/` → **126 passed**
  (unchanged from before this task — no code was touched, only `COMMON.md`
  content).
- Added the required `COMMON.md` "Current Rules" note (per this task's own
  Outcome bullet): states the actual rule (`Description`, append-only) and
  explicitly retracts the never-real "ninth column" convention so nobody
  else reuses it as I almost did.

**Noted, not fixed (genuinely out of scope):**
- The ~108-row `file_no_registry_row` backlog and the ~26 malformed rows
  are [[TASK-0352]]'s own findings, unrelated to claim-column misuse —
  touching them here would blur this task's diff with someone else's.
- `TASK-0355`'s own row briefly held a hand-written warning in `Claimed At`
  (`"Do not run a real sync until this resolves..."`) between claim and
  this write-up — the same pattern this task fixes, self-committed at
  filing time. `sync` overwrote it in the same run as the 21 others; no
  content lost, since the task file (this one) is the authoritative copy
  and the warning is moot once this task is Done. Left as an observation,
  not re-relocated.

**Open question, correctly left open:** whether new rows should ever be
allowed a free-text handoff cell at all (several `Description`s are already
dense) — out of this task's scope; if a future task wants that convention it
needs its own column, not another squat on `Claimed At`.
