# TASK-0198 `claim.py move` leaves a duplicate tracked file when a task transits 2+ states without an intervening commit

## Context

- ID: TASK-0198
- Title: `move TASK-XXXX A -> B` followed by `move TASK-XXXX B -> C`, with no
  `git commit` between the two calls, leaves the *original* starting path
  (`A`) still tracked in the index/HEAD once something finally commits —
  even though the intermediate path (`B`) correctly does not linger and
  the working tree is correct throughout.
- Status: TODO
- Owner: Toolsmith
- Claimed By: —
- Claimed At: —
- Source: Architect, 2026-08-03 — reproduced twice this session, not a
  one-off: `TASK-0189` (found and fixed via [[TASK-0197]]'s new deletion-
  staging support) and `TASK-0073` (found immediately after, same
  session, fixed the same way) both ended up duplicate-tracked
  (`TODO/`+`DONE/`) after a `TODO -> IN_PROGRESS -> DONE` sequence with no
  commit in between.
- Priority: **P2.** Not urgent — [[TASK-0197]] makes the symptom cheap to
  fix each time it recurs — but it's a real, reproducible tool defect, not
  environmental bad luck, and will keep recurring until fixed at the
  source.

## Why this matters

Both known instances share the same shape: `move` was called twice in a
row (`TODO -> IN_PROGRESS`, then later `IN_PROGRESS -> DONE`) with real
work (editing the task file's own content, editing *other* files) happening
in between, and no `git commit` landed for this specific task's move until
the very end. In both cases the final committed state had the task file
correctly present *only* in `DONE/` on disk, but `git ls-tree -r HEAD`
showed it tracked at **both** the DONE path and the original TODO path —
confirmed directly (`git ls-tree -r HEAD --name-only | grep TASK-XXXX`),
not inferred from `git status` alone (which can show a misleading `D`
against a path that was never really going to be committed that way).

**A plausible mechanism, not yet confirmed as the actual cause** — worth
stating so whoever picks this up doesn't have to re-derive it from
scratch, but flagged explicitly as unconfirmed: `_perform_transition`'s
`tracked` check (`git ls-files --error-unmatch <src_rel>`) asks whether
the *first* call's `git mv` already staged. If the task file's own content
is edited (a plain `Write`/`Edit`, not through `move`) *between* the two
`move` calls, the working tree and the index diverge for that path before
the second `move` runs — `git mv`'s own handling of a rename source whose
working-tree content differs from the index may be where the original
path's index entry survives instead of being cleanly replaced. This is a
hypothesis to verify by direct reproduction, not an established root
cause — do not fix blind.

## Intent Contract

- Outcome: either (a) `move`/`_perform_transition` is fixed so a chained
  `A -> B -> C` transition, uncommitted throughout, never leaves `A`
  tracked once something commits, or (b) if the real cause turns out to
  be inherent to calling `git mv` twice on an uncommitted rename chain,
  `move` gains a cheap self-check (e.g. `git ls-tree -r HEAD -- 'TASK-ID*'`
  after the move, refusing or warning loudly if more than one path for
  the same task id would be committed) so the defect is caught at the
  point it's introduced, not discovered later via a stray `git status`
  line.
- Why required, not assumed: reproduced twice, same shape, same session —
  a real defect, not a coincidence.

- In Scope:
  - Reproduce deliberately and minimally: a scratch task file, `move`
    TODO->IN_PROGRESS, edit its content directly (not via `move`), `move`
    IN_PROGRESS->DONE, no commit in between, then inspect the index
    (`git diff --cached --name-status`) at each step to find exactly
    where the stale `TODO` entry re-enters or fails to clear.
  - Fix at whichever step the reproduction identifies, or add the
    self-check from Intent Contract option (b) if the root cause turns
    out to be inherent to the two-`git-mv`-calls-with-no-commit-between
    shape rather than a fixable ordering bug.
  - Regression test: the exact reproduction sequence above, asserting
    only one path is tracked for the task id after the final `move`.

- Out Of Scope:
  - Auditing the rest of the task registry for other pre-existing
    duplicates beyond the two already found and fixed (TASK-0189,
    TASK-0073) — a real, cheap follow-up (`git ls-tree -r HEAD
    --name-only | grep -oE 'TASK-[0-9]+' | sort | uniq -c | sort -rn`
    would surface any others), but a separate, smaller task if wanted —
    don't fold an open-ended sweep into a root-cause fix.
  - `resolve`'s own transition logic — same underlying `_perform_transition`
    but worth confirming separately whether it's equally affected, not
    assumed identical without checking.

- Constraints And Invariants:
  - No behavior change to a *single* `move` call (the common case) — this
    is about the chained-uncommitted-transitions case specifically.
  - Stdlib only, matching the tool's existing constraint.

- Planned Validation:
  - The regression test above, run before and after the fix (must fail
    before, pass after — a fix that "fixes" a test that never actually
    reproduced the bug is worse than no fix).
  - Re-verify the two already-fixed instances (TASK-0189, TASK-0073) stay
    single-tracked — confirm the fix doesn't just move the bug elsewhere.

## Dependency

- [[TASK-0197]] (Done) — the `stage` capability used to fix both known
  instances by hand; this task fixes the tool that produced them, not a
  duplicate of that work.
- [[TASK-0202]] (In Progress) — cross-linked, not a dependency: adopts the
  general merge-conflict resolution protocol, which cites this task's own
  two known instances as one of its three motivating incidents. Related,
  distinct failure mode (this is an index/HEAD desync from `claim.py move`
  itself, not a merge/rebase conflict).

## Open Questions

- Is `resolve` (which shares `_perform_transition`) equally affected? Not
  checked — its own transition is always a single hop (`-> DONE` only,
  never chained), so it may not be reachable, but confirm rather than
  assume.
- Worth the one-time backlog sweep (Out Of Scope above) regardless of
  whether this task's own fix lands soon? Recommend yes, cheaply, as a
  follow-up — a stale duplicate is silent until someone happens to check
  `git ls-tree`, exactly how both known instances were found (by
  accident, not by a systematic check).

## Done

(not yet)
