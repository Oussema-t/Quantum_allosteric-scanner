# TASK-0223 `claim.py stage` silently skips re-adding a path edited after an earlier stage call

## Context

- ID: TASK-0223
- Title: `cmd_stage`'s "already staged, skip `git add`" optimization
  (TASK-0197) doesn't check whether the staged content still matches the
  working tree — a path staged once (e.g. by `claim.py move`), then
  edited, then passed to `stage --expect` again, gets silently skipped:
  `stage` reports "self-verified clean" and `commit-guard` reports "ok:
  matches --expect", but the commit carries the *stale* pre-edit content.
- Status: Done
- Owner: Toolsmith (Implementer C implementing directly, same session —
  same shape as [[TASK-0197]]'s own "found + fixed inline")
- Claimed By: —
- Claimed At: —
- Source: found twice in one session, both times the same mechanism —
  [[TASK-0195]]'s Done section addendum was written after that file's
  first `stage --expect` call and silently dropped from the commit;
  [[TASK-0220]]'s Done section had a clarifying edit dropped the same
  way. Root-caused this time instead of worked around a third time.
- Priority: **P2** — not data loss (the edit stays on disk, uncommitted,
  and is caught by a plain `git status`/`git diff` after the fact — both
  prior incidents were caught and fixed with a small follow-up commit)
  but a real, silent gap in the exact tool this scaffold's whole
  commit-safety story (`claim -> commit-guard --expect-empty -> stage ->
  commit-guard --expect -> commit`) depends on. `commit-guard`'s own
  self-verification does not catch it either (checked directly, see
  Why below) — this isn't a "forgot to re-run stage" user error, it's
  that re-running `stage` doesn't help.

## Why this matters

`cmd_stage` (`.ai/tools/claim.py`), added by TASK-0029 and last touched
by TASK-0197:

```python
already_staged = _staged_paths()
to_add = [p for p in expect if p not in already_staged]
if to_add:
    subprocess.run(["git", "add", "--"] + to_add, ...)
```

`_staged_paths()` is `git diff --cached --name-only` — paths where the
INDEX differs from HEAD, not paths where the WORKING TREE matches the
INDEX. A path staged once (any content) stays in `_staged_paths()` for
as long as it differs from HEAD, regardless of any *later* edit to the
working tree. TASK-0197 added the `already_staged` filter specifically so
a legitimately-fully-staged **deletion** (gone from both index and
working tree) isn't re-passed to `git add`, which errors on that exact
case (`pathspec ... did not match any files`, real incident, TASK-0197's
own Done section). The filter is correct for that one case and wrong for
every other one: a path that's **present on disk**, already staged from
an earlier call, and has since been edited again is *also* "already
staged" by this check, so `to_add` drops it too — and `git add` on a
present, tracked, edited file is always safe and never errors, so
excluding it was never necessary.

`commit-guard`'s own self-verification (`_compare_staged`, shared with
`stage`) only diffs the **path set** (`staged - expected`, `expected -
staged`) against `--expect` — it has no way to notice that a staged
path's *content* is stale relative to the working tree, since it never
looks at content at all. So the whole verify chain (`stage`'s own
self-check, then a separate `commit-guard --expect` call right before
`git commit`) reports clean at every step, and the commit still carries
stale content. Both real incidents this session were caught only by a
human/agent noticing `git status` still showed the file as modified
*after* the commit — incidental, not load-bearing.

## Intent Contract

- Outcome: `stage --expect <path>` re-adds `<path>` whenever its working-
  tree content differs from HEAD (i.e., whenever `git add` on it would
  actually change the index) — except the one case TASK-0197 fixed
  (already-staged deletion, absent from both index and working tree),
  which must keep working exactly as before (regression guard).
- Why required, not assumed: reproduced twice this session with a clear,
  readable mechanism (above) — not a hypothetical.
- In Scope:
  - Fix `to_add`'s computation in `cmd_stage` so a present-on-disk path
    is always included, regardless of `already_staged` — only a
    missing-on-disk path already reflected in the index (the TASK-0197
    case) is still excluded.
  - Regression test: stage a path, edit it again, stage the same
    `--expect` set a second time, assert the second commit's content
    (not just its path list) matches the post-edit working tree.
  - Regression test: TASK-0197's own already-staged-deletion case still
    works (no `git add` pathspec error), unchanged.
- Out Of Scope:
  - Making `commit-guard` itself content-aware (diffing staged blobs
    against a caller-declared intent, not just path lists) — named as a
    real gap by [[TASK-0195]]'s own Done section Addendum, a larger
    change than this task's narrow fix, left for that thread's own
    recommendation to pick up if it recurs.
- Constraints And Invariants: `stage` stays scoped to `.ai/`/`.claude/`
  only (unchanged); no change to `commit-guard`'s own interface/output
  shape.
- Planned Validation: reproduce the exact failure first (a test that
  fails against the current code), then fix, then confirm it passes —
  same failing-first discipline this session's other tooling work used.

## TODO

- [x] Reproduce failing-first (a test against current `claim.py` that
      demonstrates the stale-restage).
- [x] Fix `cmd_stage`'s `to_add` computation.
- [x] Confirm the new test passes; confirm TASK-0197's own deletion case
      still passes (existing coverage, if any, or a new explicit test).
- [x] Full `test_claim.py` run, no regressions.

## Dependency

- [[TASK-0197]] — the `already_staged` filter this task narrows, not
  reverts.
- [[TASK-0195]] — where this was first (silently) hit; recorded, not
  fixed, in that task's own Done section Addendum.
- [[TASK-0220]] — second occurrence, same session.

## Open Questions

- None.

## Done

**2026-08-19.** Root-caused and fixed the exact mechanism both prior
incidents shared.

**Fix**: `cmd_stage`'s `to_add` computation in `.ai/tools/claim.py`
narrowed from "skip anything already differing from HEAD" to "skip only
a path that is both missing on disk right now AND already reflected in
the staged index" (the one case TASK-0197's own fix needs to keep
working — a fully-staged deletion, where a repeat `git add` errors). Every
present-on-disk path is now always re-added, regardless of whether an
earlier call in the same commit-prep sequence already staged an older
version of it.

```python
still_missing = set(missing_on_disk) & _staged_paths()
to_add = [p for p in expect if p not in still_missing]
```

**Failing-first, per this task's own Planned Validation**: wrote
`TestStageRestagesEditedContent::test_stage_picks_up_an_edit_made_after_
an_earlier_stage` first, confirmed it FAILED against the pre-fix code
(staged blob still held the pre-edit content, `move`'s own `git mv`
snapshot, despite `stage --expect` reporting success) — then applied the
fix, confirmed it passes. A second test,
`test_task0197_deletion_case_still_works`, pins TASK-0197's own case
(stage a deletion, then stage the *same* `--expect` set again — must not
error) and passes both before and after this fix, confirming the
narrowing didn't regress the case it was built for.

**Why `commit-guard` didn't catch either real incident**: confirmed by
reading, not assumed — `_compare_staged` (shared by `stage`'s own
self-verification and `commit-guard --expect`) diffs the *path set*
against `--expect` only; it never inspects staged *content*. A path
present in both sets reports "ok, matches" regardless of whether the
staged blob is current. Left as-is here (named as its own, larger,
Out-Of-Scope item — see Intent Contract) rather than folded into this
narrower fix.

**Validated**: `.ai/tools/test_claim.py` — 17 passed (was 15 before this
task's 2 new tests), no regressions on the other 15. `.ai/tools/
test_check_references.py` + `backend/` — 44 passed, unaffected
(unrelated code, run for full-repo regression coverage per this
session's own convention).

**Retroactive fix, same session**: [[TASK-0195]]'s and [[TASK-0220]]'s
own Done-section edits, both dropped by this exact bug, were each
recovered with a small standalone follow-up commit at the time (see
their own Done sections) rather than left stale — this task documents
the mechanism those two commits were reacting to, it doesn't introduce
new data-loss risk of its own.
