# Q-0002 `claim.py move` staged stale file content (predating my own edits)

## Context

- ID: Q-0002 (toolsmith addressee folder)
- Status: Open
- Addressee: Toolsmith
- Raised By: Implementer A, 2026-07-11 session
- Raised At: 2026-07-11, discovered by the user reviewing commit `e60b13b`
  ("Escape RCSB-sourced strings before innerHTML injection (TASK-0032)"),
  fixed via `git commit --amend` in `b3e7ef4`
- Related: [[Q-0001]] (answered — the `GIT-COMMIT` lock/shared-file
  question this session already raised; related but distinct, see
  Background), `.ai/tasks/DONE/TASK-0032-frontend-html-escaping.md`,
  `.ai/tools/claim.py::cmd_move`

## Question

`claim.py move`'s `git mv` staged a version of
`TASK-0032-frontend-html-escaping.md` that predated three `Edit`-tool
writes made and confirmed-saved *before* `move` was called — the
committed content had `Status: TODO`, no `In Progress` section, and an
empty `Done` section, while the file on disk (and every edit I'd made)
already had `Status: Done` and both sections filled in. Reading
`cmd_move`'s source, the sequencing looks correct on paper (read content
→ rewrite the Status line in that same content → `git mv`, which stages
whatever is currently on disk). I can't explain the discrepancy from a
static code read alone. Is this a real bug in `move` itself, or a
concurrent-write race with another thread's operation on the same file
(this session had heavy parallel activity at the time)? Either way, should
`move` (and `stage`) verify what they actually staged against what was on
disk immediately before, the same way `commit-guard` verifies the index
against a caller's `--expect` list?

## Background

Sequence, as actually executed (not reconstructed after the fact):

1. Three `Edit` tool calls against
   `.ai/tasks/TODO/TASK-0032-frontend-html-escaping.md` — checked off the
   `TODO` list, inserted a new `## In Progress` section (call-site
   enumeration), filled in `## Done`. All three returned success; the
   tool would have errored on a failed `old_string` match (one attempt
   *did* fail earlier for exactly that reason and was corrected before
   proceeding — so silent no-ops were already ruled out for this file
   this session).
2. `python3 .ai/tools/claim.py move TASK-0032 DONE --as "Implementer A
   (this thread)"` → printed `moved TASK-0032 -> DONE (Status: Done),
   registry updated, claim released`.
3. `commit-guard --expect-empty` immediately after refused: `.ai/tasks/DONE/TASK-0032-frontend-html-escaping.md`
   already staged — confirming `move` had run `git mv` (the `tracked`
   branch in `cmd_move`, not the untracked `os.replace` fallback).
4. Staged `COMMON.md`/`frontend/app.js` (re-verified their diffs directly,
   clean), ran `commit-guard --expect <3 paths>` → `ok`, committed
   (`e60b13b`).
5. User's next message: "please amend the commit with whatever was
   leftover - I can see unstaged TASK-0032 residue." `git status` showed
   `.ai/tasks/DONE/TASK-0032-frontend-html-escaping.md` modified
   (unstaged) — i.e. the working-tree file (with all my edits) differed
   from what step 4 had committed. Diffed the committed blob against the
   working tree: the committed version was missing the entire `In
   Progress` section and `Done` write-up, and still said `Status: TODO`
   even though `move`'s own stdout in step 2 said `Status: Done` and the
   *current* working-tree file does say `Status: Done`.
6. Fixed by re-`git add`ing just that one file (current, correct content)
   and `git commit --amend --no-edit` → `b3e7ef4`. Confirmed via `git show
   HEAD:<path> | grep` that the amended blob now has `Status: Done`, `##
   In Progress`, `## Done`.

Investigated `cmd_move` directly (`.ai/tools/claim.py` lines ~535-662)
rather than guess:

- `content = f.read()` at function start reads the *current* file —
  should include my three prior edits.
- Status-line rewrite (`STATUS_LINE_RE.sub(...)`, written back to
  `src_path`) operates on that same `content` string, so the write-back
  should carry my edits plus the corrected Status line.
- `git mv src_rel dst_rel` runs *after* that write-back — `git mv` stages
  whatever is on disk at call time, which per the above should already be
  fully correct.
- `find_task_file` does a fresh directory scan each call (no caching);
  `REPO_ROOT` is derived from `claim.py`'s own file location (no
  cwd-mismatch risk).

None of that explains a stale-content result for a single, uncontested
thread. The one thing I can't rule out from the tool's own output: this
session had several other threads (Implementer B, Architect/Planner,
General Critic, Code Reviewer) actively running concurrently in this same
checkout the whole time (see [[Q-0001]] for two independent, confirmed
instances of concurrent writes landing in *my* git operations that same
session). If another thread's process also touched this exact file or ran
its own `git mv`/`git add` around the same moment, the working-tree
content `move`'s `git mv` actually captured could have been a
transiently-older version — a race window between my `Edit` writes
completing and `move`'s `git mv` subprocess reading disk, not a logic bug
in `cmd_move` itself. I did not reproduce this in isolation (no repeated
attempts, no controlled two-thread test) — flagging as the leading
hypothesis, not a confirmed cause.

## Answer

(not yet)

## Action

(not yet)
