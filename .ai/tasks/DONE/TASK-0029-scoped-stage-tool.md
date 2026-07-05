# TASK-0029 Scoped `stage` subcommand for whitelistable, self-verifying git add

## Context

- ID: TASK-0029
- Title: A `claim.py stage --expect PATH [PATH ...]` subcommand that stages
  exactly the declared paths and self-verifies with `commit-guard`
  immediately after, restricted to `.ai/` and `.claude/` so the tool's
  existing blanket whitelist never comes to imply unconstrained `git add`
- Status: Done
- Owner: Toolsmith
- Claimed By: Toolsmith (this thread)
- Claimed At: 2026-07-05 10:52
- Source: direct request, this session, 2026-07-05 — grew out of a
  discussion between this thread and Intent-Inferrer about closing the
  loop on TASK-0028's commit workflow (`claim GIT-COMMIT` → stage → `commit-guard`
  → `git commit` → `release`). Intent-Inferrer had done `git add` → discover
  contamination → `git reset HEAD --` to undo; both threads agreed
  "check before you touch the index" (what `commit-guard --expect-empty`,
  landed alongside this task, now enables) is strictly better than
  "mutate then verify then undo." Intent-Inferrer proposed a `stage`
  subcommand as the next link in the chain and asked whether to build it
  directly or file it for the Toolsmith thread that owns `claim.py`.
- Why this needs its own task rather than a quick addition: `Bash(python3
  .ai/tools/claim.py *)` (and the bare/`python` variants) are already
  blanket-whitelisted. Every subcommand that whitelist currently covers
  has a narrow, fixed write scope — lock files under `.ai/tasks/.locks/`,
  specific cells in `.ai/COMMON.md`, task files under `.ai/tasks/`. A
  naive `stage` that shells out to `git add <caller-supplied-paths>` with
  no scope limit would make the *existing* wildcard silently start
  covering unconstrained `git add` of any path in the repo — exactly the
  unconstrained-risk case Intent-Inferrer themselves argued `git add`
  should keep prompting for, undone by one level of indirection. That's a
  security-relevant design decision (same category as TASK-0028's
  `--hitl-override` requirement), not a mechanical extension, so it gets
  an Intent Contract with explicit Decisions before code, same as
  TASK-0024/0027/0028.
- Scope: one more subcommand on the existing `.ai/tools/claim.py` (not a
  new tool), restricted to staging paths under `.ai/` and `.claude/` only.

## Intent Contract

- Outcome: staging the files for a scaffold-coordination commit is one
  whitelisted command that adds exactly the declared paths (nothing more,
  nothing less) and immediately self-verifies, closing the loop:
  `claim GIT-COMMIT` → `commit-guard --expect-empty` → `stage --expect
  <files>` → `commit-guard --expect <files>` → `git commit` → `release`.
- In Scope:
  - **Decided: `stage` only accepts paths under `.ai/` or `.claude/`.**
    Any `--expect` path outside those two prefixes is refused (listing
    the offending paths), with a message pointing at a normal `git add`
    (which will correctly prompt) for anything outside scaffold
    territory. This is the load-bearing constraint that keeps
    `Bash(python3 .ai/tools/claim.py *)`'s blanket whitelist from ever
    implying unconstrained `git add` — checked this session's own commit
    history and every commit made through `claim.py`'s workflow so far
    only touched `.ai/`/`.claude/` paths, so this is not a real capability
    loss for the tool's actual use case.
  - `stage --expect PATH [PATH ...]`: runs `git add` on exactly the
    declared paths (no globs, no `-A`, no directory expansion beyond what
    the caller explicitly lists), then immediately runs the same check
    `commit-guard --expect <same paths>` performs internally (call the
    existing logic, don't re-derive it) and reports its result — if
    something unexpected ends up staged anyway (e.g. a stale partial
    stage from another thread that got merged in by git's own behavior),
    surface that clearly rather than silently declaring success.
  - refuses (before staging anything) if any `--expect` path resolves
    outside `.ai/` or `.claude/`, or doesn't exist on disk, or is already
    staged with unexpected content — fail fast, matching the
    `commit-guard --expect-empty` philosophy from the same discussion.
  - Companion to (not a replacement for) `commit-guard --expect-empty`
    (already shipped alongside this task) — `stage` doesn't itself check
    the index is empty first; callers still run `commit-guard
    --expect-empty` before `stage` per the documented workflow above.
- Out Of Scope:
  - staging anything outside `.ai/`/`.claude/` — always refused, not a
    configurable option in this task. Widening the scope later is a
    separate, deliberate decision if a real need shows up, not a default.
  - `git commit` itself, or `GIT-COMMIT` lock management — those stay
    `claim`/`release`/plain `git commit`, unchanged.
  - unstaging / `git reset` functionality — this task only adds, it
    doesn't remove; use plain `git restore --staged` for that, which
    doesn't carry the same unconstrained-write risk in the same way (it
    can only ever reduce what's staged, not add to it).
  - a distributed lock, CI gate, or anything beyond a script + local
    files — matches every prior claim.py task's scope ceiling.
- Constraints And Invariants:
  - Python stdlib only, no new dependency (matches every prior claim.py
    task).
  - reuse `cmd_commit_guard`'s comparison logic directly (call the
    function or extract a shared helper) for the self-verification step
    — do not re-implement the staged-vs-expected diff a second time.
  - the `.ai/`/`.claude/` scope check must reject path traversal tricks
    (e.g. `.ai/../backend/main.py`) — resolve paths (`os.path.normpath`
    or equivalent) before checking the prefix, not a naive string
    `startswith`.
- Planned Validation: (1) `stage --expect .ai/tasks/DONE/TASK-0029-*.md`
  (a real in-scope path) stages correctly and self-verifies clean; (2)
  `stage --expect backend/main.py` (or any real out-of-scope path) is
  refused before anything is staged, index left untouched; (3) a
  traversal attempt (`.ai/../backend/...`) is refused the same way, not
  silently normalized into an allowed path; (4) `stage --expect <path
  that does not exist on disk>` refuses with a clear message, nothing
  staged; (5) confirm the whole documented workflow end-to-end on this
  task's own files: `claim GIT-COMMIT` → `commit-guard --expect-empty` →
  `stage --expect <this task's files>` → `commit-guard --expect <same>` →
  `git commit` → `release GIT-COMMIT`.

## TODO

- [x] Implement the `.ai/`/`.claude/` scope check (normalized-path prefix
      match, reused as its own small function so Planned Validation case 3
      is easy to target directly).
- [x] Implement `cmd_stage`, reusing `cmd_commit_guard`'s comparison logic
      for the self-verify step rather than duplicating it.
- [x] Wire up the `stage` subcommand in argparse; update the module
      docstring/Usage block.
- [x] Run Planned Validation, all five cases.
- [x] Register `repo.commit.stage` in `.ai/reference/CAPABILITIES.md`
      (also updated `repo.commit.guard`'s row for `--expect-empty`).
- [x] Update `.ai/COMMON.md`'s "Current Rules" GIT-COMMIT bullet to
      mention the full `claim → commit-guard --expect-empty → stage →
      commit-guard --expect → commit → release` workflow.
- [x] **Revised per Reviewer note:** the prior finding ("no settings.json
      change needed, the blanket wildcard already covers it") is exactly
      the silent-future-subcommand-creep gap this task exists to close —
      the same blanket `Bash(python3 .ai/tools/claim.py *)` wildcard that
      would have covered an unscoped `stage` would just as silently cover
      *any* future subcommand nobody reviewed. Replace the three blanket
      wildcard entries with one enumerated entry per existing subcommand
      (`claim`/`release`/`status`/`sync`/`move`/`commit-guard`/`stage`) ×
      each invocation form (`python3`/bare/`python`) in
      `.claude/settings.json`, so a new subcommand added later requires an
      explicit settings.json update before it's frictionless, not an
      automatic grant. Also flag the heavier alternative (a structurally-
      validated capability-runner dispatch model) as an Open Question on
      TASK-0026 rather than deciding it here.

## Dependency

- [TASK-0028](../DONE/TASK-0028-commit-lock.md) (Done) — `GIT-COMMIT`,
  `commit-guard`, and `--expect-empty` (landed alongside this task) are
  all direct prerequisites/siblings.
- [TASK-0027](../DONE/TASK-0027-task-move-tool.md) (Done) — no functional
  dependency, but the third extension to `claim.py` in this session;
  implement with awareness of its argument conventions (`--as`,
  `--force --reason`) so the CLI surface stays consistent across all four
  extensions.

## Open Questions

- Should `stage` also accept an `--allow-outside-scope PATH [PATH ...]`
  escape hatch for the rare legitimate case (e.g. a commit that touches
  both `.ai/` docs and one backend file), or should that always fall back
  to plain manual `git add` for the whole commit? Recommend: always fall
  back to plain `git add` — an escape hatch here just re-creates the same
  unconstrained-risk surface this task exists to avoid, one flag away.
  Mixed-scope commits are not this tool's job.
- **Resolved 2026-07-05 (Reviewer + user decision):** the near-term
  settings.json enumeration (below) closes the immediate gap; the heavier
  "should claim.py register under a capability-runner dispatch model"
  question is deliberately deferred to TASK-0026 as its own Open Question
  rather than decided here.

## Done

- Extended `.ai/tools/claim.py`:
  - `_staged_paths()`/`_compare_staged()` extracted from `cmd_commit_guard`
    so `stage`'s self-verify step and `commit-guard` itself share one
    comparison implementation, never two independently-drifting ones.
  - `commit-guard` gained `--expect-empty` (mutually exclusive with
    `--expect` via `add_mutually_exclusive_group`) — asserts nothing is
    staged, for a fail-fast check *before* the index is ever touched.
  - `_in_scope()`: normalizes a path (`os.path.normpath`) and checks its
    first component is exactly `.ai` or `.claude` — rejects absolute
    paths and any `..`-leading result, so a traversal like
    `.ai/../backend/x.py` (which normalizes to `backend/x.py`) is caught,
    not silently allowed.
  - `cmd_stage`: refuses out-of-scope or nonexistent `--expect` paths
    before touching the index; otherwise `git add --` on exactly those
    paths, then self-verifies via `_compare_staged` and reports if
    anything unexpected ended up staged anyway.
- Planned Validation, all five cases exercised for real (no scratch
  files needed — case 5 doubled as actually shipping this task's own
  commit, see below): (1)/(5) the full `claim GIT-COMMIT` →
  `commit-guard --expect-empty` → `stage --expect ...` → `commit-guard
  --expect ...` → `git commit` → `release GIT-COMMIT` workflow, run
  end-to-end on this task's own files; (2) `stage --expect
  backend/main.py` refused before staging anything; (3) `stage --expect
  ".ai/../backend/main.py"` refused the same way — traversal doesn't
  bypass the scope check; (4) `stage --expect
  .ai/tasks/DOES-NOT-EXIST.md` refused with a clear message, nothing
  staged. `--expect-empty` itself separately verified: passes on a
  genuinely empty index, refuses (naming the path) once something is
  staged.
- **Reviewer-driven revision, landed before the rest of this task's own
  commit:** replaced `.claude/settings.json`'s three blanket
  `Bash(*.ai/tools/claim.py *)`-style wildcards with one enumerated entry
  per subcommand (`claim`/`release`/`status`/`sync`/`move`/
  `commit-guard`/`stage`) × invocation form (`python3`/bare/`python`) —
  21 entries replacing 3. This is the actual fix for the risk this task
  was created to address: an unscoped `stage` would have been one
  instance of "blanket wildcard silently covers a new write path nobody
  reviewed"; enumerating every subcommand closes that gap for *all*
  future subcommands, not just this one. Also added an Open Question to
  TASK-0026 (contributed evidence, that task remains claimed by Skills
  Crafter) about whether `claim.py` should eventually register under a
  structurally-validated capability-runner dispatch model instead of
  per-subcommand settings.json enumeration — deliberately deferred there
  rather than decided ad hoc in this task.
- Registered `repo.commit.stage` in `.ai/reference/CAPABILITIES.md` and
  updated `repo.commit.guard`'s row for `--expect-empty`. Updated
  `.ai/COMMON.md`'s Quick Navigation and "Current Rules" GIT-COMMIT
  bullet to document the full five-step workflow.
- Validation performed: `python3 -c "import ast; ast.parse(...)"` passes
  after every edit; `claim.py stage --help` / `commit-guard --help`
  render correctly with mutual exclusivity enforced by argparse itself
  (`--expect` and `--expect-empty` together is a parse error, not a
  runtime check).
