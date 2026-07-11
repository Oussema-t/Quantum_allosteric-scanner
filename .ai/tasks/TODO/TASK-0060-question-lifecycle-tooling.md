# TASK-0060 Tooling for the `.ai/memory/questions/` lifecycle

## Context

- ID: TASK-0060
- Title: A `claim.py question` subcommand family covering the
  `.ai/memory/questions/<addressee>/{open,answered,need-action}/`
  lifecycle move (mirroring `move`'s folder-is-state convention for
  `.ai/tasks/`) plus a helper to derive a new `TASK-XXXX` file from a
  Question's `## Action` section without re-deriving `reserve-next`'s
  race-safe id allocation
- Status: TODO
- Owner: Toolsmith
- Claimed By: —
- Claimed At: —
- Source: direct request, this session, 2026-07-11 — right after
  `.ai/memory/questions/` (the addressed-question registry) and its first
  real entry, `toolsmith/open/Q-0001-...md`, landed. The registry's own
  README explicitly models itself on `.ai/tasks/README.md`'s
  folder-lifecycle convention ("same lifecycle-folder idea, applied to
  questions instead of work items"), which is exactly what `claim.py
  move` (TASK-0027) already automated for tasks — this task is that same
  automation, applied to the new registry, not a new design.
- Scope: extend `.ai/tools/claim.py` (no new tool — same reasoning as
  every prior extension this session) with a `question` subcommand
  family. Does not touch `.ai/memory/shared/open-questions.md` (a
  different system per the questions README, out of scope).

## Intent Contract

- Outcome: relocating a question between `open/`/`answered/`/
  `need-action/`, and bootstrapping a `TASK-XXXX` skeleton from a
  question's `## Action` section, are both single whitelisted commands —
  not the manual `git mv` + hand-edit-the-Status-line + hand-write-a-new-
  task-file-then-remember-to-link-it-back sequence this thread just did
  by hand answering Q-0001.
- In Scope:
  - **Decided: extend `.ai/tools/claim.py`, not a new tool** — same
    rationale as every other extension this session (TASK-0027/0028/0029):
    the folder-move logic already exists (`find_task_file`-style scan +
    tracked-check + `git mv`/`os.replace` fallback + targeted
    `- Status:` line rewrite), and `question move` needs the same shape
    against a different directory tree and a different status vocabulary
    (`Open`/`Answered`/`Needs-Action` instead of
    `TODO`/`In Progress`/`Done`). Reuse the underlying helpers, don't
    duplicate them; refactor `move`'s current TASK-specific pieces into a
    shared parametrized core only if reuse turns out cleaner that way —
    don't force a shared abstraction if the two lifecycles diverge enough
    that forcing one creates more indirection than it saves (judgment
    call for whoever implements this, not decided in advance here).
  - `claim.py question move <addressee> <Q-ID> <open|answered|need-action>`
    — locates the file under `.ai/memory/questions/<addressee>/*/`
    (searching all three state folders, same "refuse on zero or >1
    match" discipline as `find_task_file`), relocates it, and rewrites
    its own `- Status:` line to the matching vocabulary word. **No claim
    check, no lock file** — unlike `.ai/tasks/`'s registry, a question has
    exactly one fixed addressee and no shared registry table a second
    thread could race on; the contention `move`'s claim-check protects
    against doesn't have an equivalent here yet. Revisit only if a real
    collision shows up (matches this scaffold's "advisory/harden-after-
    a-real-failure" precedent — don't build contention-handling for a
    contention case that hasn't happened).
  - `claim.py question derive-task <addressee> <Q-ID> --title "..."` [--as
    <label>] — calls `reserve-next`'s existing race-safe id-allocation
    directly (import/call the function, do not re-implement the
    highest-plus-one-with-retry loop a second time) to get a fresh
    `TASK-XXXX`, writes a minimal skeleton file to `.ai/tasks/TODO/`
    (`Context` section only: `ID`, `Title` from `--title`, `Status: TODO`,
    a `Source:` line pointing back at the originating question's path —
    everything past `Context` left as template placeholders for a human/
    agent to actually fill in, matching TASK-0027's "writing the actual
    Done section content is not mechanizable" precedent applied here to
    the whole Intent Contract, not just Done), and appends one line to
    the originating question's own `## Action` section linking the new
    task (targeted text append, not a whole-file rewrite — same
    discipline `update_registry_row` uses for `COMMON.md`).
  - register both in `.ai/reference/CAPABILITIES.md`.
- Out Of Scope:
  - any claim/lock mechanism for questions (see above — no contention
    case exists yet).
  - auto-answering a question, or auto-filling a derived task's Intent
    Contract from the question's own Answer/Action prose — real judgment
    work, not mechanizable; this tool bootstraps the skeleton and the
    cross-link, nothing past that.
  - touching `.ai/memory/shared/open-questions.md` or migrating anything
    between that system and this one.
  - a distributed lock, CI gate, or anything beyond a script + local
    files — matches every prior `claim.py` extension's scope ceiling.
- Constraints And Invariants:
  - Python stdlib only, no new dependency.
  - reuse `reserve-next`'s existing candidate-selection/retry logic
    directly for `derive-task` — do not re-derive a second "highest
    number so far" computation; that exact mistake (two independent
    "highest number" computations racing) is what TASK-0045 was filed to
    fix, and duplicating the logic here would eventually re-open the same
    class of bug in a second code path.
  - the question-file scan (locating `<Q-ID>` under an addressee's three
    state folders) must refuse, not silently pick one, if zero or more
    than one match is found — same discipline as `find_task_file`.
- Planned Validation:
  1. `question move` on a real question (or a scratch one under a
     scratch addressee folder) through all three states; confirm folder
     + `- Status:` line agree after each move, and a repeat move to the
     same state is a no-op (mirrors `move`'s own idempotency check).
  2. `question derive-task` against Q-0001 itself (already answered, safe
     to test against without disturbing its real Action content — use a
     `--dry-run` if one gets added, or a scratch question otherwise);
     confirm the new task file's `Source:` line points back correctly and
     the question's `Action` section gains exactly one new line, nothing
     else disturbed.
  3. Confirm `derive-task` never allocates a `TASK-XXXX` id that
     collides with a concurrently-running `reserve-next`/`claim` call —
     since it reuses the same underlying primitive, this should follow
     for free from TASK-0045's own validation, but re-confirm rather than
     assume.

## Dependency

- [TASK-0027](../DONE/TASK-0027-task-move-tool.md) (Done) — the
  folder-move + Status-line-rewrite pattern this task adapts.
- [TASK-0045](../DONE/TASK-0045-highest-task-lookup-tool.md) (Done) —
  `reserve-next`, reused directly by `derive-task`.
- `.ai/memory/questions/README.md` — the lifecycle convention this task
  automates; read it before implementing, it's short.

## Open Questions

- Should `question move`/`derive-task` share literal code with `cmd_move`
  via a parametrized helper, or just parallel its shape with separate,
  smaller functions? Recommend deciding once the second lifecycle's edge
  cases are in front of you (e.g. whether "addressee" needs the same kind
  of zero-or-multiple-match refusal `find_task_file` has) rather than
  guessing at the right abstraction boundary now.
- Should a derived task's `Context` skeleton include a `Claimed By`/
  `Claimed At` pair pre-filled to `--as`'s label (a soft pre-claim), or
  stay fully unclaimed until someone explicitly runs `claim`? Recommend
  unclaimed — filing a task and claiming it are already two distinct,
  deliberate steps everywhere else in this scaffold (see this very task's
  own Context: filed, not claimed, pending the next thread's decision to
  pick it up).

## Done

(not yet)
