# TASK-0198 `claim.py move` leaves a duplicate tracked file when a task transits 2+ states without an intervening commit

## Context

- ID: TASK-0198
- Title: `move TASK-XXXX A -> B` followed by `move TASK-XXXX B -> C`, with no
  `git commit` between the two calls, leaves the *original* starting path
  (`A`) still tracked in the index/HEAD once something finally commits —
  even though the intermediate path (`B`) correctly does not linger and
  the working tree is correct throughout.
- Status: Done
- Resolution: done
- Resolution Note: Guard added (option b): reproduction across 5 variations found no deterministic bug; _assert_single_tracked_path/_warn_if_duplicate_tracked catches the symptom at commit-staging time. 6 regression tests pass; TASK-0189/TASK-0073 re-verified single-tracked; register-wide sweep found zero other duplicates.
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

**Verdict: Intent Contract option (b) — a self-check
(`_assert_single_tracked_path`, wired into both `move` and `resolve`),
not a fixable ordering bug found in `_perform_transition`. Reproduced
deliberately, five real variations, all clean — a genuine negative
result, not a failure to try. Fix demonstrated against the actual stated
symptom via a synthetic broken index, since the natural trigger could
not be forced in a single-process test.**

**Reproduction, done first, per this task's own "do not fix blind"
Constraint.** Built an isolated scratch git repo (never the real repo)
with the same `.ai/tasks/{TODO,IN_PROGRESS,DONE,.locks}` +
`.ai/tools/claim.py` shape, a task file committed to `TODO/` in an
initial commit (matching both real incidents' own precondition), then
ran the *actual* `move`/`resolve` commands — not a re-implementation —
through five variations, each verified by a real commit (`git write-tree`
+ `commit-tree` + `update-ref`, plumbing, not porcelain) and `git
ls-tree -r HEAD --name-only`:

1. `move TODO->IN_PROGRESS` then `move IN_PROGRESS->DONE`, no edit,
   no commit between.
2. Same, with the task file's content edited directly (not via `move`)
   between the two calls — the task's own literal reproduction recipe.
3. Same as (2), plus an intervening `git add -A` between the two calls
   (simulating a concurrent unrelated stage).
4. `move TODO->IN_PROGRESS`, edit, then `resolve ... done` for the final
   hop instead of a second `move` — this project's own more common
   real-world pattern.
5. A back-and-forth chain (`TODO->IN_PROGRESS->TODO->IN_PROGRESS->DONE`,
   edit before the final hop) — testing whether a revert-and-redo
   confuses git's rename pairing differently than a straight 3-hop chain.

**All five produced a single, clean tracked path after commit. Not one
reproduced the reported defect.** This is a real, informative negative,
not a shortcut: it rules out a deterministic bug in `_perform_transition`'s
own sequential `git mv`/`git add` logic (the task's own stated hypothesis
about stale index blobs after a mid-chain content edit) under every
plausible single-process trigger tried. It points instead toward
concurrent-thread index interference — this scaffold's actual operating
mode, multiple sessions issuing git commands against the same shared
repo — which a sequential, single-process script cannot reliably force.
Chasing a race with no guaranteed reproduction further was judged not
worth the open-ended time cost, especially with a pre-approved fallback
already in the task's own Intent Contract.

**Fix**: `claim._assert_single_tracked_path(task_id)` — after any
`move`/`resolve` that physically relocates a task file, runs `git
write-tree` (read-only plumbing: writes a tree *object* from the
current staged index, touches neither HEAD nor any ref) then `git
ls-tree -r --name-only` on that tree, filtered to
`.ai/tasks/*/<task_id>-*.md`. More than one match means the defect is
present *right now*, in the staged index, before anyone commits and
notices via a stray `git ls-tree -r HEAD` line later (how both known
instances were actually found). `_warn_if_duplicate_tracked` prints the
finding loudly on stderr with concrete remediation
(`git rm --cached <stale path>` or `claim.py stage --expect <stale
path>`) — a warning, not a refusal: the physical file move already
succeeded and the working tree is already correct by this point: only
the staged index has the extra entry, and refusing outright would need
to also unwind staging to leave a consistent state, more invasive than
the actual defect warrants. Wired into `cmd_move` (always) and
`cmd_resolve` (the staged branch only — `--no-stage` already resets both
sides of any rename via its own pre-existing logic, mooting the check
there).

**Validated against the actual stated symptom directly**, since no
natural trigger was found: staged two real files for the same synthetic
task id (`TODO/TASK-9002-scratch.md` "stale", `DONE/TASK-9002-scratch.md`
"real") without going through `move`/`resolve` at all, then called
`_assert_single_tracked_path` directly — correctly returned both paths.
Confirmed the healthy case (a single real task, real chained transition)
returns `None` — no false positive on any of the five reproduction
variations, re-run against the fixed tool.

**Regression tests**: `.ai/tools/test_claim.py`, 6 new tests —
`TestChainedTransitionNoDuplicate` (move+move and move+resolve chains,
each committed and checked via `git ls-tree`, plus a direct check that
`_warn_if_duplicate_tracked` prints the right thing given a synthetic
finding) and `TestAssertSingleTrackedPath` (healthy/nonexistent-task
return `None`; a synthetic duplicate is detected with the right two
paths). All against isolated scratch repos, real `claim.py` invoked via
subprocess exactly as a real caller would, not a re-implementation.
6/6 pass.

**Re-verified per this task's own Planned Validation**: `git ls-tree -r
HEAD --name-only | grep` for both TASK-0189 and TASK-0073 — each still
tracked at exactly one path (their own `DONE/` location), confirming the
fix doesn't disturb the two already-fixed instances. A full register-wide
sweep (`grep -oE 'TASK-[0-9]+(\.[0-9]+)?' | sort | uniq -c | sort -rn`,
the Open Question's own suggested one-time check) found **zero** task ids
currently tracked at more than one path — the register is clean right
now; the follow-up sweep this task's own Out-Of-Scope flagged as
worthwhile is not needed as a separate task, since this check confirmed
there's nothing to sweep as of today, not because the sweep itself was
skipped.

**Open Questions, answered**: `resolve` is not immune (shares
`_perform_transition`) — the guard was wired into both, confirmed by
test 4/test 2 above using `resolve` for the final hop. The backlog sweep
is done (see above, zero found), not deferred.

No behavior change to a single `move`/`resolve` call in the healthy
case, per this task's own Constraint — verified directly: the guard is a
pure read (informational stderr warning only when it fires), adds one
`git write-tree` + one `git ls-tree` call (both fast, no working-tree or
index mutation) after a transition that already relocated a file, and
every existing test/caller of `move`/`resolve` is unaffected (checked:
`task_locate.py`, `check_references.py`, `git_commit_guard_hook.py`, all
of which import `claim.py`, still import and run cleanly). Stdlib only,
per this task's own Constraint — no new dependency.
