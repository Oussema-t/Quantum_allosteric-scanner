# TASK-0107 `claim.py resolve` — explicit resolution value, default-stage with `--no-stage` opt-out

## Context

- ID: TASK-0107
- Title: Implement the on-disk backend adapter for the already-catalogued
  `workflow.task.resolve` capability (`.ai/reference/CAPABILITIES.md` line
  56, currently "manual fallback") as a new `.ai/tools/claim.py resolve`
  subcommand — moves a task to `DONE`, records an explicit canonical
  resolution value, and by default stages the result (task file +
  `.ai/COMMON.md` registry row), with `--no-stage` to leave everything
  correct on disk but nothing staged.
- Status: Done
- Resolution: done
- Owner: Toolsmith
- Claimed By: Toolsmith (this thread)
- Claimed At: 2026-07-14 19:32
- Source: direct request, this session, 2026-07-14 — "Update our tooling
  to allow a resolve task call, but with a --no-stage opt-out."
- Scope: a new `.ai/tools/claim.py` subcommand, `resolve`. Reuses
  `cmd_move`'s file-relocation/registry-update machinery rather than
  duplicating it. Does not change `move`, `stage`, `commit-guard`, `add`
  (TASK-0061, unimplemented), or `sync`.

## Intent Contract

- Outcome: resolving a task is one whitelisted command that (a) requires
  an explicit, canonical resolution value instead of a bare "move to
  DONE", (b) records that value permanently in the task's own file, and
  (c) by default leaves the change already staged for the next commit —
  matching this session's own repeated manual pattern of `move TASK-XXXX
  DONE` immediately followed by staging the task file plus the
  `COMMON.md` row it touched. `--no-stage` opts out for a caller who wants
  to review or batch differently before staging.
- In Scope:
  - **Decided: resolution values are exactly `RESOLUTION_VOCABULARY.md`'s
    canonical `Task Resolution Values` table** — `done`, `fixed`,
    `wont-do`, `duplicate`, `obsolete`, `not-reproducible`, `moved`. Not a
    free string. Matches `.github/prompts/task-resolve.prompt.md`'s
    explicit requirement ("stop and ask for clarification instead of
    guessing" on a non-canonical value) — refuse with the canonical list
    printed, don't guess or normalize a near-miss.
  - `claim.py resolve <TASK-ID> <resolution> [--note TEXT] --as LABEL
    [--force --reason TEXT] [--keep-claim] [--no-stage]`. `--as` required,
    same as `move`.
  - Always moves the file to `DONE` (this backend has only
    `TODO`/`IN_PROGRESS`/`DONE` folders — there is no separate
    `resolved`-but-not-`closed` folder in `BACKEND_SELECTION.md`'s sense
    for this concrete adapter; every canonical resolution value is
    terminal here). Reuses `find_task_file`, the claim-mismatch check, and
    the Status-line rewrite exactly as `cmd_move` already does — refactor
    the claim-mismatch `if`/`elif` block in `cmd_move` into a small shared
    helper both subcommands call, rather than copy-pasting it.
  - Records the resolution as a new `- Resolution: <value>` line (a new
    `RESOLUTION_LINE_RE`, same targeted-rewrite discipline as
    `STATUS_LINE_RE` — insert right after the `- Status:` line if absent,
    replace in place if a task is re-resolved). `--note TEXT` additionally
    records/replaces a `- Resolution Note: <text>` line the same way.
    Both are single-line, plain markdown, grep-able — no new structured
    format.
  - **Default (no `--no-stage`)**: after the move/rewrite/registry-update,
    stage the result for the next commit:
    - the task file itself is already staged as a side effect of
      `git mv` + the Q-0002 fix's re-`git add` (see
      `.ai/memory/questions/toolsmith/answered/Q-0002-*.md` — `move`
      already re-`git add`s the tracked destination path to avoid staging
      a stale blob; `resolve` inherits this for free by reusing that
      code path).
    - **new**: also explicitly `git add .ai/COMMON.md` — `move` never did
      this (its registry-row edit is left unstaged today, a known gap
      nobody had filed), but `resolve`'s whole point is to remove the
      "now go stage COMMON.md too" manual step.
  - **`--no-stage`**: after performing the exact same on-disk
    move/rewrite/registry-update as the default path (nothing about *what
    changes* differs), unstage anything the git-mv path put in the index:
    `git reset -- <dst_rel>` and skip the `COMMON.md` `git add` entirely.
    End state: task file physically at the `DONE` path with fully correct
    content, `COMMON.md`'s row updated on disk, *nothing* staged in git's
    index for either — verified by `git diff --cached --stat` being empty
    for both paths. Do not implement this via a parallel `os.replace`
    code path for tracked files (an earlier idea considered and
    rejected) — reusing `git reset` after the same `git mv` is simpler,
    reuses git's own semantics instead of reinventing them, and can't
    reintroduce a Q-0002-shaped bug since the working-tree content is
    never in question, only what ends up in the index.
  - claim-release-on-`DONE` behavior unchanged from `move` (`--keep-claim`
    to opt out); this happens regardless of `--no-stage` — releasing a
    lock file is not a git-staging operation.
  - Register `resolve` in `.ai/reference/CAPABILITIES.md`, replacing the
    `workflow.task.resolve` row's "manual fallback" /
    "generic with backend adapter" cells with the concrete tool
    invocation, matching how TASK-0027 updated the `workflow.task.move`
    row. Whitelist `Bash(python3 .ai/tools/claim.py resolve *)` (+
    bare/`python` forms), matching every other subcommand's three-form
    enumeration in `.claude/settings.json`.
- Out Of Scope:
  - the abstract multi-backend `workflow.task.resolve` capability in
    general (JIRA or other future backends) — this task only implements
    the on-disk adapter, per `BACKEND_SELECTION.md`'s current backend map.
  - auto-chaining into `workflow.task.promote` (the prompt file's
    "extract UI intent baselines / architecture findings" auto-chain
    step) — that is prompt/agent-orchestration behavior layered on top of
    this capability, not something `claim.py resolve` itself should
    attempt from inside a stdlib script with no model access.
  - a `closed` lifecycle state distinct from `resolved`/`DONE` — this
    backend doesn't have that folder; not adding one speculatively.
  - changing `move`'s own behavior (still no default staging, still
    doesn't touch `COMMON.md`'s staging) — `resolve` is a distinct,
    additive command for the terminal-resolution case specifically.
- Constraints And Invariants:
  - Python stdlib only, no new dependency.
  - resolution values validated against a literal tuple mirroring
    `RESOLUTION_VOCABULARY.md` exactly — if that file's canonical list
    ever changes, this tuple must be kept in sync by hand (no runtime
    parsing of the markdown table; flag this coupling in a comment).
  - reuse `find_task_file`, `update_registry_row`, and the claim-mismatch
    check — do not duplicate any of the three.
  - `--no-stage`'s end state must be independently verified (not just
    trusted from reading the diff): `git diff --cached --stat` empty for
    both the task file's destination path and `COMMON.md` after a
    `--no-stage` call.
- Planned Validation:
  1. Scratch task, `resolve <ID> done --as ... `: confirm file moved to
     `DONE`, `- Status: Done` and `- Resolution: done` both present,
     `COMMON.md` row updated, and `git diff --cached --name-only` includes
     both the task file's destination path and `COMMON.md`.
  2. Same, with `--note "explanation"`: confirm `- Resolution Note:` line
     present with the given text.
  3. Reject path: `resolve <ID> not-a-real-value` — confirm refusal lists
     the canonical values, no file/registry mutation occurs at all.
  4. `--no-stage` run: confirm on-disk content is identical to the
     default-path case, but `git diff --cached --stat` is empty for both
     the task file and `COMMON.md`.
  5. Re-resolve an already-`DONE` task with a different resolution value:
     confirm the `- Resolution:` line is replaced in place (single line),
     not duplicated.
  6. Confirm `move` and `stage` are byte-identical in behavior to before
     this task — this task must not change their behavior at all, only
     add a new subcommand and extract a shared helper `cmd_move` and
     `cmd_resolve` both call.

## Dependency

- [TASK-0027](../DONE/TASK-0027-task-move-tool.md) (Done) — `cmd_move`'s
  file-relocation/registry-update logic, reused rather than duplicated.
- `.ai/memory/questions/toolsmith/answered/Q-0002-*.md` — the `git mv`
  stale-blob fix `resolve` depends on for its default-stage path to be
  safe; also the reasoning behind rejecting a parallel `os.replace`
  code path for `--no-stage`.
- `.ai/reference/RESOLUTION_VOCABULARY.md` — the canonical resolution
  value list this task hard-codes (see Constraints on keeping it in sync
  by hand).
- `.github/prompts/task-resolve.prompt.md` and
  `.ai/reference/BACKEND_SELECTION.md` — the existing capability spec
  this task provides the concrete on-disk-backend implementation for.
- `.ai/reference/CAPABILITIES.md` line 56 (`workflow.task.resolve` row)
  — updated by this task from "manual fallback" to the concrete tool.

## Open Questions

- Should `resolve` refuse (rather than warn-and-proceed) when the task is
  unclaimed, given resolving is a more terminal action than an
  in-progress `move`? Recommend keeping `move`'s existing warn-and-proceed
  advisory behavior for consistency — no incident yet motivating a
  stricter rule here specifically.
- Should a future `promote` auto-chain (per the prompt file) hook off of
  `resolve` specifically, now that a single command marks a task
  terminally resolved? Recommend leaving this as a follow-up task if/when
  `workflow.task.promote` gets its own concrete on-disk implementation —
  out of scope here per the prompt-orchestration boundary above.

## Done

- Implemented `.ai/tools/claim.py resolve <TASK-ID> <resolution> --as
  LABEL [--note TEXT] [--force --reason TEXT] [--keep-claim] [--no-stage]`.
  Refactored `cmd_move`'s claim-mismatch check into a shared `_claim_gate`
  helper (both `move`/`resolve` call it, `move`'s message wording
  unchanged) and its relocate/registry/release logic into a shared
  `_perform_transition(task_id, target_state, keep_claim,
  content_transform)` (both subcommands call it; `move` passes a
  Status-only transform, `resolve` passes a Status+Resolution+Note
  transform, in one read-modify-write).
- `RESOLUTION_VALUES` hard-codes `RESOLUTION_VOCABULARY.md`'s canonical
  list; a non-canonical value refuses with the list printed, no mutation.
- **Real bug found and fixed during this task's own validation, not
  anticipated in the Intent Contract**: the first implementation staged
  `.ai/COMMON.md` by default via a blanket `git add`, which swept a
  concurrent thread's unrelated unstaged edits into this thread's index
  (reproduced live, twice, against real concurrent activity in this
  session — not a synthetic test). Fixed by extracting
  `_apply_registry_row_update` (the per-row transform, shared with
  `update_registry_row`) and adding `_stage_registry_row_only`, which
  builds a blob from the *index's* current `.ai/COMMON.md` with only the
  caller's own row changed and stages that via `hash-object`/
  `update-index --cacheinfo` — never a whole-file `git add`. This is now
  the load-bearing safety property for `resolve`'s default staging.
- **Second bug found during `--no-stage` validation**: `git mv` stages
  both sides of a rename (removes the old path, adds the new); the first
  `--no-stage` implementation only `git reset`'d the destination path,
  leaving the source-side deletion still staged. Fixed by resetting both
  `src_rel` and `final_rel` (added `src_rel` to `_perform_transition`'s
  return dict).
- Validated (isolated scratch repo, `/tmp/.../resolve_test2`, to avoid
  further collisions with this session's very active concurrent
  threads): default staging (task file + surgical registry row, correct
  content picked up from unstaged prior edits, matching Q-0002's fix);
  `--note` (Resolution Note line inserted); reject path (non-canonical
  value, no mutation); `--no-stage` (both rename sides unstaged, content
  still correct on disk, registry row unstaged); re-resolve with a
  different resolution value (single-line replace, not duplicated);
  `move` regression (byte-identical output shape, Q-0002 fix intact
  through the shared helper).
- Updated `.ai/reference/CAPABILITIES.md`'s `workflow.task.resolve` row
  (was "manual fallback") and `.claude/settings.json` (three-form
  `resolve` whitelist entries, matching every other subcommand).
- Also caught, live, during validation: two *other* threads staged their
  own unrelated file moves (`TASK-0046`, `TASK-0075`) into this shared
  index while `GIT-COMMIT` was held by this thread — re-confirms Q-0001's
  finding that the lock is advisory-only, not enforced. Unstaged both
  (their working-tree content untouched) before this task's own commit.
  Not a `resolve` bug; flagged as further live evidence for TASK-0065's
  commit-queue visibility work.
