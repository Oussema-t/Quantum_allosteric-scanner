# TASK-0356 — `commit-guard --expect-empty` cannot pass after `move`, so people bypass the guard

- Status: TODO
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
