# TASK-0045 atomic next-task-id reservation (`claim.py reserve-next`)

## Context

- ID: TASK-0045
- Title: Extend `claim.py` with an atomic "reserve the next `TASK-XXXX` id"
  operation, so threads filing a new task stop colliding on the same number
- Status: Done
- Owner: Toolsmith
- Claimed By: Toolsmith (this thread)
- Claimed At: 2026-07-07 06:37
- Source: user request, 2026-07-07 session — "Our threads have several
  times requested permission to find the highest numbered task. Please
  check if we have a tool for that and if it is whitelisted." Audit: no
  such tool exists (see below). While filing this very task, a second
  thread independently filed its own task as TASK-0045 at the same time
  (`TASK-0045-ceiling-coordinate-descent-search.md`) — a live collision
  on-disk, since finding "the next number" by reading the current state
  and then writing a new file is a read-then-write race with no lock
  in between. The user resolved the immediate collision (this task keeps
  0045, the other thread re-filed as TASK-0046) and asked for the tool to
  be extended to prevent this going forward, not just report a snapshot.
- Audit findings (why no whitelisted answer exists today):
  - `.ai/tools/task_locate.py` (TASK-0025) requires an already-known
    `TASK-ID` — it can't discover one.
  - `.claude/settings.json` whitelists exactly one `find` invocation
    (`Bash(find .ai/tasks -name '*.md')`, no wildcard args) that lists all
    task files unsorted; extracting the max still needs a second, piped,
    unwhitelisted command (`| sort -V | tail -1`), which also violates the
    command-hygiene skill's no-pipe rule.
  - `claim.py`'s internal `disk_task_ids()` (used by `move`/`status`)
    already scans every on-disk task id, but nothing surfaces "the highest
    one" as a standalone call — and even if it did, a read-only snapshot
    is exactly what raced this session: two threads can both read "highest
    = 44" and both decide to file "45".

## Intent Contract

- Outcome: a thread that wants to file a new task gets back a task id it
  is guaranteed not to collide with any other thread's concurrent
  reservation — via one atomic, whitelisted command, not a read-then-write
  race.
- In Scope:
  - `claim.py reserve-next --as "<label>" [--note TEXT]`: computes the
    next candidate id from `max(highest on-disk task number, highest
    currently-locked task number) + 1`, then attempts the same `O_EXCL`
    lock-file creation `cmd_claim` already uses for that candidate. On
    `FileExistsError` (lost the race to another concurrent
    `reserve-next`/`claim`), increments and retries, bounded (e.g. 50
    attempts) so a real bug can't spin forever. The lock file created on
    success *is* the claim — the caller does not need a separate `claim`
    call afterward, only to create the task file using the returned id
    and add its `.ai/COMMON.md` registry row (still a manual step, see Out
    Of Scope).
  - `--dry-run`: prints what the next candidate currently looks like
    without creating a lock — read-only preview for pure curiosity, with
    an explicit caveat in its own output that the answer can be stale by
    the time the caller acts on it (use the non-dry-run form to actually
    reserve).
  - considering both `disk_task_ids()` (real filed tasks) and the current
    contents of `.ai/tasks/.locks/` (in-flight reservations/claims not yet
    filed as task files) when computing the candidate — this is the actual
    fix; disk-only would have raced again the same way this session did.
  - whitelist `claim.py reserve-next *` in `.claude/settings.json` (same
    pattern as the tool's other subcommands).
  - one `CAPABILITIES.md` update describing the new subcommand alongside
    the existing `workflow.task.claim` row family.
- Out Of Scope:
  - automatically creating the task `.md` file or the `COMMON.md` registry
    row — `workflow.task.create` stays `manual fallback`, per
    `CAPABILITIES.md`; this only atomically hands back a safe id to use.
  - reclaiming numbers from abandoned reservations (a thread that reserves
    an id and never files or releases it "burns" that number permanently
    under this design). Acceptable: burning an integer is cheap, silently
    reusing one a moment later is what caused today's collision.
- Constraints And Invariants:
  - Python stdlib only, no third-party dependencies, no new dependency vs.
    `claim.py`'s existing `O_EXCL` primitive.
  - Never mutates or reads `.md` task file content — file scanning stays
    filename-based via the existing `disk_task_ids()`.
- Planned Validation: simulate the exact race that happened this session —
  two concurrent `reserve-next` calls (e.g. backgrounded in the same shell
  step) — and confirm they return two different ids, neither colliding
  with any id already on disk or already locked.

## In Progress

None

## TODO

None — see Done below.

## Done

- [x] Implemented `cmd_reserve_next` in `claim.py` (+ `_highest_top_level_number`
      helper) and wired `reserve-next` into the argparse subparsers, with
      `--as`, `--note`, `--dry-run`, `--quiet`.
- [x] Whitelisted `claim.py reserve-next *` in `.claude/settings.json` (3
      invocation forms, same pattern as the tool's other subcommands).
- [x] Added the `workflow.task.reserve-next` row to `CAPABILITIES.md`.
- [x] Ran Planned Validation: 5 concurrent `reserve-next --quiet` calls
      (`&` + `wait` in one shell step) returned 5 distinct ids
      (TASK-0049..0053 at the time), none colliding with each other or with
      any id already on disk/locked; `--dry-run` and a real reserve were
      also exercised individually first. All test reservations released
      afterward (`claim.py release`) so they don't burn real numbers.
- [x] This task itself moved TODO -> DONE.

(not yet)
