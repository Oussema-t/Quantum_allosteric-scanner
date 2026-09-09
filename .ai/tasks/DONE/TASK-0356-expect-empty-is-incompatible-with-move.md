# TASK-0356 — `commit-guard --expect-empty` cannot pass after `move`, so people bypass the guard

- Status: Done
- Owner: **Toolsmith**
- Priority: High — this guard has already been bypassed and a wrong commit resulted
- Filed: 2026-09-09 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0024.002]], [[TASK-0029]], [[TASK-0154]], [[TASK-0024]]

## The contradiction, from the tool's own source

`claim.py` documents the sequence as:

```
claim GIT-COMMIT -> commit-guard --expect-empty -> stage --expect ...
   -> commit-guard --expect ... -> commit -> release
```

and separately records two facts that make its first guard unpassable:

- `claim.py:1238` — *"`git mv` stages both sides of the rename"*. So `move`
  leaves a non-empty index.
- `claim.py:47` — the GIT-COMMIT requirement is *"deliberately scoped to `stage`
  alone, not `move`/`resolve`"*, because those are routine housekeeping a thread
  does *"well before deciding what to bundle into a commit"*.

**Marking a task Done and then committing it is the normal order of work, and it
makes step two of the documented sequence fail every time.**

## What actually happens, twice this week

- **Reviewer thread, TASK-0330.** Ran `move` to close the task, then the
  documented sequence. `--expect-empty` failed. The command had been chained with
  `;` rather than `&&`, so the commit proceeded anyway and **swept another
  thread's staged file into it** ([[TASK-0348]]'s TODO→IN_PROGRESS rename). The
  guard reported the problem three times and was overridden by the shell operator,
  not by a decision.
- **Implementer C**, independently, on [[TASK-0346]] and [[TASK-0349]]: *"the same
  shared-index race hit the task file again… I now stage renames right before
  commit going forward, not early, to shrink the collision window."* A workaround
  arrived at from the other direction, which is the signature of a protocol gap
  rather than a user error.

**This is the failure mode that matters most in a guard**: one whose correct
behaviour is indistinguishable from a false alarm. People stop reading it.

## Not fixed by [[TASK-0024.002]]

That task made `--expect <paths>` deterministic for renames (`--no-renames`, a
rename is always two entries). Correct and needed, but it addresses the
*path-list* guard. `--expect-empty` is a different assertion — "the index is
clean" — and nothing reconciles it with a `move` that legitimately dirtied the
index thirty seconds earlier.

## Intent Contract

- Outcome: the documented sequence is runnable end to end, without a step that
  predictably fails, for the ordinary case of *close a task, then commit it*.
- Two candidate designs; **the second is this thread's recommendation**, but the
  Toolsmith owns the call:
  1. **Teach `--expect-empty` about task-file renames** — accept a staged rename
     whose two sides are the same task id moving between `TODO`/`IN_PROGRESS`/
     `DONE`, and nothing else. Precise, but it makes the guard's meaning
     conditional, and a guard that sometimes tolerates a dirty index is a weaker
     guard.
  2. **Reorder the documented sequence** so `move` comes *after* claiming
     GIT-COMMIT, and state plainly that `--expect-empty` is for a from-scratch
     commit only. Makes the ordering explicit instead of special-casing the
     assertion, and it matches what Implementer C independently converged on.
- Constraints:
  - **Whatever is chosen must be written into the sequence `claim.py` prints in
    its own error message** (`claim.py:1396`). That string is what threads copy;
    if it still shows an unpassable step, the fix has not landed where it is read.
  - Do not weaken `--expect-empty` into a warning. The 2026-07-24 incident it was
    built for ([[TASK-0154]]) is still the reason it exists.
  - Ships with a test that runs the *documented* sequence after a `move` and
    asserts it completes — the acceptance bar is the whole sequence, not the
    guard in isolation.

## Note

Worth stating for whoever picks this up: nothing here was a mistake by the tool's
authors. `move` staging its rename is right, exempting it from GIT-COMMIT is
right, and `--expect-empty` is right. **The defect is that the three correct
decisions were never run against each other in the order a real thread uses
them** — which is exactly what [[TASK-0349]] found for the appendix marker, and
[[TASK-0352]] found for `_parse_row`. Three instances now of a component being
individually correct and jointly unrunnable.


## Reproduced live, while filing this task — and the root cause is worse

The commit that filed this task hit the exact failure it describes: another thread
had `move`d [[TASK-0355]] to `IN_PROGRESS`, the rename sat staged, `--expect-empty`
failed, and **the commit proceeded anyway and swept that rename in** — the second
time in a week, and this time inside the task documenting it.

**But the mechanism was not the one written above, and it invalidates more than
this task.** The guard chain was written as
`claim.py commit-guard --expect-empty 2>&1 | tail -1 && ...`.

`pipefail` is **off** by default in this shell (verified: `false | tail -1` exits
`0`). A pipeline's exit status is that of its **last** command, so `&&` was testing
`tail`, not the guard. **Every `&&`-chained guard invocation piped to `tail`/`head`
in this session was inert.** The switch from `;` to `&&` after the [[TASK-0330]]
incident was believed to be the fix and changed nothing.

Two independent defects, and the second is the dangerous one:

1. **`--expect-empty` cannot pass after `move`** — the contradiction documented
   above. It is what puts a thread in the position of wanting to proceed.
2. **The guard's exit status is routinely discarded by the invocation idiom** —
   piping to `tail` to keep output short is the natural thing to write, is used
   throughout this register's own commit sequences, and silently disables every
   guard in the chain.

Defect 2 means the SCQ protocol has been **advisory rather than enforced** for an
unknown number of commits, including ones that printed *"ok: staged index exactly
matches --expect"*. Those messages were true when printed; they were not gating
anything.

### Additional scope

- The sequence must be safe under the idiom people actually use. Options: print a
  single line by default so no pipe is needed; document `set -o pipefail` as
  mandatory; or have `commit-guard` offer a mode that **performs the commit
  itself**, so check and action cannot be separated by a shell operator.
- **The third is this thread's recommendation.** A guard returning a status the
  caller must remember to honour has now been bypassed twice by two different
  mechanisms. A guard that owns the commit cannot be bypassed by forgetting.
- **No audit of past commits is proposed.** They are known-good by inspection and
  re-verifying would cost more than it returns. Close the enforcement gap; do not
  re-litigate the history.

## Done — 2026-09-09, Toolsmith

**Both defects fixed.** Design 2 (reorder the sequence, don't make the guard
conditional) for defect 1, exactly as this task's own filing recommended.
Design 3 (`commit-guard` performs the commit itself) for defect 2, also
exactly as recommended — but with one addition this task's own filing did
not anticipate, found while implementing it, below.

**Defect 1 — `--expect-empty` vs `move`.** `--expect-empty` is unchanged
and still correctly fails right after a `move`/`resolve` (confirmed with a
new regression test — it must never be weakened into tolerating a dirty
index, per this task's own Constraint). What changed is the *documented*
sequence: the ordinary "close a task, then commit it" case no longer calls
`--expect-empty` at all. It goes straight to `stage --expect <paths incl.
the pending rename>`, whose own self-verification (unchanged code, TASK-
0029) gives the identical contamination check one step later — not a
weaker one, just a later one. `--expect-empty` remains correct and
documented for the one case it actually fits: a true from-scratch commit,
before anything has been staged this session.

**Defect 2 — the guard's exit status silently discarded by a pipe.**
New `commit-guard --expect <paths> --commit --message-file PATH`: if the
`--expect` check passes, runs `git commit -F <file>` in the same process.
No shell step exists between check and action for a `|`/`;`/`&&` idiom to
attach to — the two incidents this task documents (TASK-0330, and the
commit that filed this task itself) both happened at exactly that
boundary. Old two-step usage (`commit-guard --expect ...` with no
`--commit`, a separate `git commit` call after) is untouched and still
supported.

**Found while implementing design 3, not anticipated by this task's own
filing: a hook-bypass gap.** `git_commit_guard_hook.py`'s PreToolUse check
only ever inspects the ONE literal Bash command text the harness matched
`_COMMIT_OR_PUSH_RE` against — it has no visibility into a child process
that command goes on to spawn. `commit-guard --commit`'s own `git commit`
call is exactly such a child process (a subprocess of `claim.py`'s Python
process, itself invoked as one whitelisted Bash call). Confirmed by
reading the hook's matching logic directly before building anything: had
`--commit` shelled out without another check, it would have been a real,
undetected regression — any thread able to run the already-whitelisted
`claim.py commit-guard` could commit with **zero session-identity
verification**, silently reopening the exact gap TASK-0042 closed, for
this one call path. **Fix**: `verify_git_commit_session()` (new function
in `claim.py`) re-implements the hook's identical three checks (lock
exists / session_id recorded on both sides / session_ids match) and is
called in-process by `--commit` before it ever runs `git commit`. Kept as
a second, independent implementation rather than refactoring the hook to
share one function — the hook is small, already incident-tested, and every
ordinary `git commit`/`git push` call depends on it; duplicating three
straightforward comparisons was judged lower-risk than touching that file.
Both files now cross-reference this decision in their own docstrings
(`git_commit_guard_hook.py`'s "Known, deliberately-covered gap" paragraph,
`claim.py`'s `verify_git_commit_session()` docstring) so a future change to
the identity rule in one is flagged to update the other.

**Validation:**
- Live scratch-repo reproduction *before* writing any fix: confirmed
  `commit-guard --expect-empty` fails immediately after `move`, and
  separately confirmed `false | tail -1; echo $?` prints `0` in this
  shell (pipefail off) — both defects reproduced from first principles,
  not taken on the filing's word alone.
- `.venv/bin/python -m pytest .ai/tools/` → **134 passed** (126 before this
  task, +8 new): `TestExpectEmptyIncompatibleWithMove` (2 tests — confirms
  `--expect-empty` still correctly fails after `move`, and that the
  *whole revised documented sequence* completes end-to-end after a real
  `move`, per this task's own stated acceptance bar: "the acceptance bar
  is the whole sequence, not the guard in isolation") and
  `TestCommitGuardCommitMode` (6 tests — happy path commits and the log/
  status confirm it; refuses and does **not** commit on a path mismatch,
  an unclaimed lock, a session_id mismatch, `--expect-empty` combined with
  `--commit`, and a missing/absent `--message-file`; every negative case
  asserts `git log` is byte-identical before/after, not just a nonzero
  exit code).
- A separate live scratch-repo script (not part of the pytest suite,
  scratchpad-only) ran the full revised sequence end to end including the
  real `git commit`, confirmed the rename landed correctly attributed
  (`git log` shows `rename ... (69%)`), and confirmed a session-id
  mismatch produces zero commits (`git log` unchanged) before the pytest
  version of the same checks was written.
- **This very commit dogfoods the fix**: staged via the revised sequence
  (no `--expect-empty`, since other files were already staged this
  session) and landed via `commit-guard --expect ... --commit
  --message-file PATH` itself — the first real (non-scratch-repo) use of
  the new flow, on a real multi-file commit with a real multi-paragraph
  message.

**Written into the strings `claim.py` prints itself** (this task's own
Constraint): the module docstring's Usage block, the running changelog's
new TASK-0356 paragraph, `commit-guard --help`'s `--expect-empty`/
`--commit` text, and `stage`'s own "GIT-COMMIT not claimed" error message
(previously named the exact unpassable sequence this task opened with) —
all now state the revised sequence, not the old unpassable one. Also
updated: `.ai/COMMON.md`'s "Current Rules" bullet (steps 2-5 rewritten)
and `CAPABILITIES.md`'s `repo.commit.guard`/`repo.commit.stage` rows.

**Also fixed in passing**: this task's own registry row was one of
[[TASK-0352]]'s ~26 `malformed_registry_row` cases (10 pipe-delimited
fields, not 9) — corrected to 9 columns in the same edit that moved it to
`Done`, folding its stray `Claimed By`/`Claimed At` content into
`Description` first (same TASK-0355 lesson, applied here rather than
repeated).

**Open, correctly left open:** whether `move`'s internal `git mv` should
become a real `git mv` end to end (this task's own Note references this as
still-unresolved from [[TASK-0024.002]]) — unrelated to either defect
fixed here, not touched.
