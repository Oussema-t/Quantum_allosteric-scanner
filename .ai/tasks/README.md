# Task Files

Use this folder for multi-step implementation, investigation, migration, or validation work.

Naming:

- `TASK-0001-slug.md` — number is a permanent ID, never reused, never renumbered on move.
- `TASK-0001.001-slug.md` — a subtask of TASK-0001. Use dotted subtask IDs
  (`.001`, `.002`, …) when a task's work splits into independently
  claimable, independently stateful slices (e.g. one thread per slice)
  instead of writing one large task file with an internal checklist that
  spans multiple owners. The parent file stays a thin coordinator: it holds
  shared decisions/constraints and a subtask table linking to each
  `TASK-XXXX.NNN` file, but not the implementation detail itself. Each
  subtask file is a full task file in its own right — same required
  sections below, own `Status`/`Owner`/`Claimed By`, own folder placement —
  and links back to its parent in `Context`/`Dependency`. The parent is Done
  only once every subtask is Done.

## Folder = lifecycle state

A task file lives in exactly one of these subfolders. Moving state = moving the file
(`git mv`), then updating its `Context: Status` field to match. This is the on-disk
backlog — the folder a file sits in tells you its state without opening it.

- `TODO/` — not yet started.
- `IN_PROGRESS/` — actively being worked by the owner named in `Context`.
- `DONE/` — accepted; `Done` section filled in with what actually shipped.
- `PLANS/` — roadmap/program-level docs (multi-week plans, phase sequencing) that are
  *not* single-outcome task files and don't move through TODO/IN_PROGRESS/DONE. A plan
  spawns TASK-XXXX files; it isn't one itself.

Rejected/abandoned tasks stay in whichever folder they were in when dropped, with
`Context: Status: Rejected` and a one-line reason in `Open Questions` — don't delete,
don't invent a `REJECTED/` folder for a handful of files.

## Required sections (inside every TASK-XXXX file, regardless of folder)

- `Context` — includes `Status` (TODO / In Progress / Blocked / Done / Rejected),
  `Owner` (which expert thread: Architect/Planner, Implementer, General Critic, …),
  and `Crit Ref` / source-plan pointer if spawned from a `PLANS/` doc.
- `Intent Contract`
- `In Progress` — running notes on the current slice of work (not the folder name).
- `TODO` — remaining steps.
- `Dependency` — other TASK-XXXX files or artifacts this is blocked on.
- `Open Questions`
- `Done` — filled in only once the file moves to `DONE/`.

Keep one file per coherent outcome.

Use the Intent Contract section for the human-readable goal, BDD-style acceptance, constraints, and planned validation before exact implementation details.

Starter example: `.ai/reference/STARTER_TASK_EXAMPLE.md`