# TASK-0019 Package the accumulated AI-scaffold changes into shippable commits

## Context

- ID: TASK-0019
- Title: Split the working tree's accumulated `.ai/`/`.claude/` scaffold
  changes (bootstrap restructure, TASK-0002 hygiene review, TASK-0003–0016
  backlog spawn, TASK-0017 claim-lock) into a small number of coherent,
  reviewable commits on the current branch (`bartosz`)
- Status: Done — verified 2026-07-05 (Architect/Planner thread) and moved
  to `DONE/` + registry updated in this pass. Verification method: read
  every commit hash cited below (`git show --stat`) and diffed
  `.ai/COMMON.md` at `e70a644` against the tree at that commit
  (`git ls-tree`). Findings: commits `300b464`, `84a1d64`, `ec2cf4b` match
  their stated stories exactly. Commit `e70a644` is confirmed to have
  carried TASK-0003–0024 registry rows while only TASK-0001/0002/0017
  task files existed in that commit's tree — i.e. acceptance scenario 2
  ("registry never shown mid-corrupt") was genuinely violated at that one
  commit boundary, exactly as this task's own Done section already
  disclosed. Not a silent gap: the race is documented below, root-caused
  to a concurrent thread, and the missing files all landed in later
  commits (confirmed via `git ls-files` at current HEAD — TASK-0003
  through TASK-0027 are all tracked now). Closing as Done on that basis:
  the plan was sound and mostly executed clean, the one deviation was an
  external race outside this task's control and is transparently
  recorded rather than papered over.
- Owner: Commit Packager (overlay applied by the Implementer thread that
  also did TASK-0017, per user request in the same session)
- Claimed By: Architect/Planner (this thread)
- Claimed At: 2026-07-05 08:45
- Source: user request, 2026-07-04 session — "consider how we could ship
  the AI-scaffold related changes in best-sized chunks to the current
  branch," asked immediately after TASK-0017 landed
- Scope: everything currently modified/untracked under `.ai/` and
  `.claude/` on branch `bartosz`. Explicitly excludes the three untracked
  `__WORK_IN_PROGRESS__/*.md` research-content files (not scaffold) and
  excludes committing/pushing itself — this task produces the plan and
  (once approved) the staged/committed split, nothing beyond that.

## Intent Contract

- Outcome: the current single undifferentiated diff becomes a short,
  ordered sequence of commits, each with one coherent story, each
  independently reviewable, without rewriting history or squashing away
  the fact that this was multiple threads' work.
- In Scope:
  - classify every changed/untracked path under `.ai/`+`.claude/` into a
    commit group
  - for files whose diff spans more than one group (`.ai/COMMON.md`,
    `.ai/tasks/README.md`), identify the hunk-level split, not just a
    whole-file assignment
  - propose commit order and one-line commit messages per group
  - flag any file/group that isn't this thread's to commit unilaterally
    (i.e. belongs to a different, possibly still-active thread)
- Out Of Scope:
  - the three `__WORK_IN_PROGRESS__/*.md` research docs (ALGORITHM_REGISTER,
    HOLO_DIRECTION_MODULE, SYSTEMS_allosteric_corrected_v2) — not scaffold,
    a separate ship decision for the user
  - actually running `git commit` — user explicitly said "no committing
    yet"; this task stages/prepares only, up to a confirm-before-commit gate
  - pushing to remote
- Acceptance Scenarios:
  - Given the final plan, when each proposed commit's diff is read alone,
    then it tells one coherent story without unrelated hunks mixed in.
  - Given `.ai/COMMON.md`'s Active Work Registry, when the commits are
    applied in the proposed order, then the registry table is never shown
    mid-corrupt (e.g. a row referencing a task file that doesn't exist yet
    in that commit).
- Constraints And Invariants:
  - do not squash away or attribute one thread's work to another — TASK-0018
    (Architect/Planner thread) and the TASK-0003–0016 backlog (a different
    parallel Implementer thread, per TASK-0002's Done notes) are not this
    thread's work product; package them as their own commit(s) but do not
    commit on their behalf without flagging it first.
  - keep `.ai/COMMON.md`'s registry internally consistent at every commit
    boundary (a row should never point at a path that doesn't exist yet in
    that commit's tree).
- Planned Validation: after staging each proposed group, run
  `git diff --cached` per group and confirm it matches exactly one story
  from the plan below; run `git status` after all staging to confirm
  nothing scaffold-related was left behind unaccounted-for.

## In Progress

None

## Packaging Analysis

Current diff shape (`git diff --stat` + untracked, `.ai`/`.claude` only):
19 tracked files modified/renamed, 17 new untracked task files, 2 new
`DONE/` files — all uncommitted on `bartosz`, spanning at least four
distinct units of work layered on top of each other.

### Proposed commits, in order

1. **"Move task/plan files into TODO/IN_PROGRESS/DONE/PLANS lifecycle
   folders; fix stale path references"** (mechanical, low-risk)
   - `.ai/tasks/IN_PROGRESS/TASK-0001-agent-scaffold-bootstrap.md` (rename
     from `.ai/tasks/TASK-0001-...`)
   - `.ai/experts/architect-planner.md`, `code-reviewer.md`,
     `commit-packager.md`, `general-critic.md`, `implementer.md`,
     `knowledge-curator.md`, `teacher.md`, `test-report-reviewer.md`,
     `toolsmith.md` (each: one stale `TASK-0001` path fixup, no other change)
   - `.ai/reviews/REVIEW-2026-06-25-scaffold-ripeness.md` (same path fixup)
   - `.ai/tasks/README.md` — **hunk split**: only the folder-lifecycle
     convention section (`## Folder = lifecycle state` and the
     `Required sections` rewrite), not the `Claimed By`/`Claimed At` line
     (that's commit 4).

2. **"TASK-0002 hygiene review: reconcile plans, document scaffold
   boundaries"**
   - `.ai/tasks/PLANS/PLAN.md` (rename + reconciliation header + `[have]`/
     `NEW` retagging content, kept together — splitting the rename from its
     same-task content edit is not worth the extra commit)
   - `.ai/tasks/PLANS/PLAN-01.07.26.md` (rename + reconciliation header)
   - `.ai/README.md` (`__WORK_IN_PROGRESS__` boundary doc)
   - `.ai/reference/SLASH_COMMAND_CANDIDATES.md` (`/learn` row)
   - `.claude/TASKS.md` (ledger-boundary mirror note)
   - `.claude/improvements/test_coverage.md` (TASK-0016 pointer fix)
   - `.ai/tasks/DONE/TASK-0002-ai-scaffold-hygiene-review.md` (new)
   - `.ai/COMMON.md` — **hunk split**: Quick Navigation additions for
     `PLANS/*`, the `Task Ledger Boundary` section, the Source-Of-Truth new
     row, the registry-sync rule bullet, and the TASK-0001/TASK-0002
     registry rows. Not the `Claimed By`/`Claimed At` columns or rules
     (commit 4), not the TASK-0003–0018 rows (commits 3/5).

3. **"Register the PLAN.md module backlog as TASK-0003–0016"**
   - `.ai/tasks/TODO/TASK-0003-targets-yaml-reconciliation.md` through
     `TASK-0016-heat-indefinite-hnew-test.md` (14 new files)
   - `.ai/COMMON.md` — **hunk split**: just the TASK-0003–0016 registry rows
   - Note: this is a different (parallel Implementer) thread's spawned
     work, per TASK-0002's own Done section. Packaging it is fine — it's
     already sitting in the working tree and self-registered — but flag to
     the user before committing on that thread's behalf.

4. **"TASK-0017: registry claim-lock convention"**
   - `.ai/COMMON.md` — **hunk split**: `Claimed By`/`Claimed At` columns,
     the claim-before-start + staleness-override rules, TASK-0017's own row
   - `.ai/tasks/README.md` — **hunk split**: the `Claimed By`/`Claimed At`
     Context-line mention
   - `.ai/reference/STARTER_TASK_EXAMPLE.md` (template addition)
   - `.ai/tasks/DONE/TASK-0017-registry-claim-lock.md` (new)

5. **"Register TASK-0018 (backend-vs-allostery architecture reconciliation)"**
   — **decision (2026-07-04): left for its owning thread, not committed
   here.** See "Decision: commits 3 and 5" below.
   - `.ai/tasks/TODO/TASK-0018-backend-vs-allostery-architecture-reconciliation.md`
   - `.ai/COMMON.md` — **hunk split**: just the TASK-0018 registry row

6. **"Register TASK-0019 (this scaffold commit-packaging task)"** (added
   after user go-ahead; this thread's own work, no ownership ambiguity)
   - `.ai/tasks/TODO/TASK-0019-scaffold-commit-packaging.md`
   - `.ai/COMMON.md` — **hunk split**: the TASK-0019 registry row, plus the
     new "Pending commit handoffs" note (see Decision below) flagging
     commits 3/5 to their owning threads

Held out entirely (not scaffold, separate decision — per user, 2026-07-04:
these move into the repo's main structure via a different, not-yet-
formulated task; not this task's concern):
- `__WORK_IN_PROGRESS__/ALGORITHM_REGISTER.md`
- `__WORK_IN_PROGRESS__/HOLO_DIRECTION_MODULE.md`
- `__WORK_IN_PROGRESS__/SYSTEMS_allosteric_corrected_v2.md`

### Decision: commits 3 and 5 (2026-07-04)

User: leave other threads' work in their own hands to commit; don't commit
on their behalf. Suggested owners, to be flagged via `.ai/COMMON.md` (a
"Pending commit handoffs" note added right after the Active Work Registry
table, per commit 6 above):
- **Commit 3** (TASK-0003–0016 module backlog) → the parallel **Implementer**
  thread that spawned them (per TASK-0002's Done section) — files are
  already written and self-registered; that thread just needs to run the
  `git add`/`git commit`.
- **Commit 5** (TASK-0018) → the **Architect/Planner** thread that owns it
  (registry `Assigned To` already says so) — same situation, file already
  written and registered, just needs its owning thread to commit it.

User also confirmed: no need to drive uncommitted scaffold changes to zero
in one pass — reducing the pile incrementally (commits 1/2/4/6 now, 3/5
later by their own threads) is the goal, not full cleanup this round.

## TODO

- [x] Confirm with user whether commits 3 and 5 (other threads' spawned
      task files) should be packaged now or left for those threads to
      commit themselves. — **left to owning threads**, flagged in
      `.ai/COMMON.md` (see Decision above).
- [x] Get explicit user go-ahead before running any `git commit`. — granted
      2026-07-04 for commits 1, 2, 4, 6; commits 3 and 5 explicitly withheld.
- [x] Ask user separately about the three `__WORK_IN_PROGRESS__/*.md`
      files. — deferred to a future, not-yet-formulated task; held out of
      this task's scope entirely.
- [x] Reconstruct intermediate snapshots of `.ai/COMMON.md` and
      `.ai/tasks/README.md` per commit boundary and commit 1, 2, 4 in order.
      Done cleanly for commits 1 and 2. Commit 4 (TASK-0017) hit a real
      `.git/index` race — see Done section.
- [x] Verify with `git status` that only the deferred items remain
      uncommitted. Confirmed — see Done section for the final list, which
      grew mid-task (TASK-0020–0024 appeared from another live thread).

## Dependency

- TASK-0002 (done) — source of most of commit 2's content.
- TASK-0017 (done) — source of commit 4's content and the claim-before-start
  rule this task itself is following (see Claimed By/At above).
- TASK-0018 (TODO, Architect/Planner) — commit 5 packages its file but does
  not do its work.

## Open Questions

- Noted 2026-07-04 (cross-reference added by a concurrent Skills Crafter
  thread, per user direction to flag this in every task that touches it):
  this task's packaging work was done by hand (raw `git`/manual analysis),
  not via the `repo.packaging.*` / `repo.vcs.*` capability set that
  `.ai/reference/CAPABILITIES.md` documents as backed by
  `agents-tools/capability-runner.sh` — that script does not exist on disk
  and is being rebuilt under TASK-0026 (parent) and its
  `TASK-0026.001`-`.004` subtasks. If this task or a successor packaging
  task is revisited after TASK-0026 lands, prefer the capability-runner
  path over manual git plumbing where it now covers the same ground.
- Resolved 2026-07-04: commits 3 and 5 are not committed by this thread —
  see "Decision: commits 3 and 5" above.
- Resolved 2026-07-04: `__WORK_IN_PROGRESS__/*.md` disposition — deferred to
  a separate, not-yet-formulated task that moves them into the repo's main
  structure; out of this task's scope.
- Superseded: the planned "Pending commit handoffs" note in `.ai/COMMON.md`
  was never landed as its own edit — see Done section, "the race," below.
  The registry now carries a different thread's own note about the same
  underlying risk (concurrent whole-file writes), plus TASK-0024, which
  proposes an actual mechanism. Treat that as the answer to this question
  rather than building a second, redundant note.

## Done

**Commits 1, 2 landed clean, exactly as planned:**
- `300b464` — mechanical lifecycle-folder restructure (TASK-0001 move, 9
  expert-file path fixups, ripeness-review fixup, README.md convention).
- `84a1d64` — TASK-0002 hygiene-review outcomes (plan reconciliation,
  scaffold-boundary docs, ledger-boundary note, `/learn` registration,
  TASK-0002's own DONE record).

**Commit 4 (TASK-0017) hit a real `.git/index` race with a concurrent
thread.** This working directory is shared by more than one live Claude
Code session at once (confirmed: TASK-0020–0024 appeared on disk,
unregistered, mid-task, authored by a thread calling itself
"Intent-Inferrer"). Sequence of events:
1. This thread wrote a clean intermediate snapshot of `.ai/COMMON.md`
   (claim-lock columns/rules + TASK-0001/0002/0017 rows only, no
   TASK-0003+ rows — by design, since those were meant to stay
   uncommitted for their owning threads) and `git add`ed it.
2. Between that `git add` and this thread's `git commit`, another
   process's `git add` on the same file won the race for what ended up
   in the index at commit time. The resulting commit (`e70a644`, still
   titled "TASK-0017: registry claim-lock convention") carries that other
   thread's full registry (TASK-0003 through TASK-0024, including a note
   from that thread about the table being "found reverted twice" — which
   was this thread's own snapshot-reconstruction technique, seen from the
   other side, being mistaken for data loss) and a rule about
   `.ai/COMMON.md` being unsafe under concurrent whole-file writes. None
   of that extra content was authored or reviewed by this thread; it is
   real, was already correct and self-registered, and reflects actual
   task files sitting on disk — it just landed inside the wrong commit,
   attributed to the wrong story.
3. **Decision: did not amend `e70a644`.** It's on a shared branch another
   live thread may already be building on top of; rewriting it risks a
   worse collision than the one that produced it. Left as-is per explicit
   user direction ("use COMMON.md as is") once this was discovered.
4. This thread's planned commit 6 (register TASK-0019 + add a "Pending
   commit handoffs" note) was reduced to just adding the TASK-0019 task
   file itself (`ec2cf4b`) — its registry row had already landed via the
   race in `e70a644`, so only the tree/registry inconsistency (a row
   pointing at a file that didn't exist yet) needed closing, not a new
   registry edit. The originally-planned handoff note was dropped rather
   than layered on top of an already-messy commit — see Open Questions.

**Commits 3 and 5 (TASK-0003–0016, TASK-0018) were never committed by
this thread**, per the user's explicit decision — left for the
Implementer and Architect/Planner threads that own them respectively.
Their registry rows are already present (via the race, in `e70a644`) even
though their task files are not yet committed; this is a known,
acknowledged inconsistency, not a silent one.

**Final state at task close:** four commits landed
(`300b464`, `84a1d64`, `e70a644`, `ec2cf4b`). Remaining uncommitted:
TASK-0003–0016, TASK-0018, TASK-0020–0024 (the last five appeared from
the concurrent "Intent-Inferrer" thread during this task and were never
this thread's to commit), and the three `__WORK_IN_PROGRESS__/*.md`
research docs (explicitly out of scope). Per the user: reducing the
uncommitted pile incrementally was the goal, not reaching zero this pass
— that goal was met (from 19 modified + 17 new + 2 DONE files uncommitted
at task start, to 4 commits landed and the remainder clearly attributed
to their owning threads).

**Field evidence for TASK-0024:** this task is now itself a second,
concrete instance of the exact `.ai/COMMON.md` concurrent-write collision
TASK-0024 (filed by the other thread) proposes to fix with an atomic
claim/free tool. Worth citing there directly if that task's thread wants
a second real example beyond its own.
