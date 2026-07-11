# Addressed Questions

Use this folder for a question raised by one thread that needs an answer from a
*specific* expert role. If a question names who should answer it, it belongs here.

This is a companion registry to `.ai/tasks/`, same lifecycle-folder idea, applied to
questions instead of work items. It does **not** replace `.ai/tasks/` — a question that
resolves into real implementation work still gets its own `TASK-XXXX` file; this registry
tracks the *question and its answer*, and links to that task once one exists.

## Layout

- `<addressee>/` — one folder per expert role the question is addressed to (e.g.
  `toolsmith/`). Create a new addressee folder the first time a question needs one; don't
  pre-create folders for roles nobody has ever addressed.
  - `open/` — asked, not yet answered.
  - `answered/` — the addressee answered; the answer itself is the resolution, no further
    action follows from it.
  - `need-action/` — the addressee answered, and the answer implies someone must *do*
    something (file a task, change a tool, update a convention) beyond just reading the
    answer. Stays here until that action is taken, then moves to `answered/` with a note
    on what was done (or a link to the `TASK-XXXX` file that now owns the follow-through).

Moving state = moving the file (`git mv`), then updating its `Status` field to match —
same convention as `.ai/tasks/README.md`'s folder-is-state rule.

## Naming

`Q-0001-slug.md` — numbered per addressee folder tree (i.e. `toolsmith/`'s own Q-0001 is
independent of any other addressee's Q-0001, the same way `TASK-`/`SEAM-`/`INV-` are
separate ID spaces from each other despite all starting at `0001`). Not the same registry
or numbering as `shared/open-questions.md`'s `Q-XXXX` scheme — that file's numbers and
this folder's numbers are allowed to collide; they are different systems, disambiguated
by path, not by a shared counter.

## Required sections

- `Context` — `Status` (Open / Answered / Needs-Action), `Addressee`, `Raised By`,
  `Raised At`, and any `TASK-XXXX`/`SEAM-XXXX`/commit this question grew out of.
- `Question` — the actual question, stated so it can be answered directly.
- `Background` — what happened, why it matters, what's already been checked.
- `Answer` — filled in by the addressee; empty while `Status: Open`.
- `Action` — filled in only if the answer requires follow-up; names the `TASK-XXXX` that
  now owns it once one is filed.
