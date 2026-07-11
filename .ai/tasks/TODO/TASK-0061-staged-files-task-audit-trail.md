# TASK-0061 Reflect staged files into the claiming TASK file (audit trail)

## Context

- ID: TASK-0061
- Title: Extend `.ai/tools/claim.py stage` (or add a sibling subcommand)
  so that staging files under a claimed `TASK-XXXX` also appends a small,
  timestamped, machine-written record of exactly what was staged into
  that task's own file — closing the gap between "what a task file says
  happened" and "what was actually staged/committed," verifiable without
  re-deriving it from `git log`
- Status: TODO
- Owner: Toolsmith
- Claimed By: —
- Claimed At: —
- Source: direct request, this session, 2026-07-11, prompted by
  `.ai/memory/questions/toolsmith/need-action/Q-0001-*.md`'s incident —
  a concurrent thread's `git add` landed in another thread's staged
  index, caught by a *human/reviewer reading the proposed commit*, not by
  any tooling cross-referencing "what's staged" against "what the
  claiming task's own file says it's touching." `stage`/`commit-guard`
  already verify the staged set against a caller-supplied `--expect`
  list, but nothing today writes that list anywhere a *reviewer* can
  check it against the task's own record after the fact — today every
  task's Done section's "what I staged/committed" prose is entirely
  hand-written (this session's own `.ai/tasks/DONE/*.md` files are all
  free-text accounts of this, not a verifiable log).
- Scope: `.ai/tools/claim.py`'s `stage` subcommand (add an opt-in flag)
  or a small new sibling subcommand — implementer's call, see Open
  Questions. Does not change `commit-guard`, `move`, `sync`, or the
  `GIT-COMMIT` claim mechanics themselves.

## Intent Contract

- Outcome: after staging files for a commit under a specific claimed
  task, that task's own file carries a short, automatically-written
  record of exactly which paths were staged and when — so a later
  reviewer (human or agent) can check "does this task's own file agree
  with what actually got staged/committed under it" without trusting
  free-text prose alone or re-deriving it from `git log -p`.
- In Scope:
  - a `--reflect-into <TASK-ID>` flag on `stage` (or an equivalent
    sibling subcommand — see Open Questions on which shape is cleaner):
    after staging succeeds and self-verifies (reusing `stage`'s existing
    logic unchanged), append one small record to `<TASK-ID>`'s own file
    — format left to the implementer, but must include at minimum: a
    timestamp, the exact staged path list, and the claimant label
    currently holding `<TASK-ID>` (if any) for cross-reference. A
    plain, grep-able line format (matching this scaffold's existing
    "keep it plain markdown, grep-able" preference — see `.ai/COMMON.md`
    /`.ai/tasks/.locks/README.md` precedent) is preferred over inventing
    a structured sub-format inside the task file.
  - the record must be a **targeted append**, not a whole-file rewrite —
    same discipline `update_registry_row`/`move`'s Status-line rewrite
    already use for shared/task files; never risk clobbering the rest of
    a task file's content to add one audit line.
  - refuse (not silently skip) if `<TASK-ID>` doesn't resolve to exactly
    one file on disk — reuse `find_task_file`'s existing zero-or-multiple
    refusal discipline, don't re-derive it.
  - register the updated `repo.commit.stage` behavior (or the new
    sibling capability) in `.ai/reference/CAPABILITIES.md`.
- Out Of Scope:
  - recording the eventual **commit hash** as a second phase (i.e. a
    follow-up `claim.py record-commit <TASK-ID>` after `git commit`
    resolves the hash) — flagged as a natural extension in Open
    Questions, not required for this task to be Done. Ship the
    staged-at-a-point-in-time record first; revisit once that's proven
    useful in practice, matching this scaffold's incremental-hardening
    precedent (TASK-0017→TASK-0024, TASK-0028→TASK-0042).
  - making this mandatory / enforced — `--reflect-into` is opt-in; a
    thread that forgets to pass it gets today's behavior unchanged. Do
    not silently change `stage`'s default behavior for existing callers.
  - anything for plain `git add` (files outside `.ai/`/`.claude/`) — this
    only extends the already-scoped `stage` path, for the same load-
    bearing reason `stage` itself is scoped (TASK-0029): widening what
    `claim.py`'s blanket whitelist implicitly authorizes is exactly the
    risk this scaffold has already had to walk back once.
- Constraints And Invariants:
  - Python stdlib only, no new dependency.
  - must not change `stage`'s existing behavior when `--reflect-into` is
    omitted — purely additive.
  - the appended record must not break `.ai/tasks/README.md`'s required-
    sections structure (i.e. append inside an existing section such as
    `## In Progress` or `## Done`, or a new small dedicated section if
    that's cleaner — implementer's call, but must stay parseable by a
    human skimming the file, not a hidden machine-only blob).
- Planned Validation:
  1. Stage a real (or scratch) file set under a claimed scratch task with
     `--reflect-into`; confirm the task file gains exactly one new
     record line/section and nothing else changes.
  2. Confirm `stage` without `--reflect-into` behaves byte-identical to
     today (regression check against TASK-0029's own existing test
     cases).
  3. Confirm the refusal path when `<TASK-ID>` has zero or multiple
     on-disk matches — reuse, don't re-derive.

## Dependency

- [TASK-0029](../DONE/TASK-0029-scoped-stage-tool.md) (Done) — `stage`'s
  existing implementation this task extends.
- [TASK-0027](../DONE/TASK-0027-task-move-tool.md) (Done) — the
  `find_task_file` zero-or-multiple-match discipline this task reuses.
- `.ai/memory/questions/toolsmith/need-action/Q-0001-*.md` — the incident
  motivating this; read its Answer section (the two-layer advisory-lock-
  plus-guard design, and why the guard is the real backstop) before
  implementing, so this doesn't duplicate or contradict that reasoning.

## Open Questions

- `--reflect-into` flag on `stage` itself, vs. a separate sibling
  subcommand (e.g. `claim.py reflect-staged <TASK-ID>`, run right after a
  plain `stage` call)? Recommend the flag — one fewer subcommand to
  remember, and it guarantees the record can only ever describe a stage
  call that actually just happened and actually just self-verified,
  rather than trusting a second, separately-invoked command to
  accurately describe some earlier stage call's result.
- Worth the two-phase design (stage-time record now, commit-hash record
  later via a second call) from the start, or ship staged-only first?
  Recommend staged-only first — see Out Of Scope; adding the commit-hash
  phase later is additive, and building it before knowing whether the
  staged-only record is even useful in practice risks over-building.
- Exact record format/section placement inside a task file — left
  fully open for whoever implements this to decide against a real task
  file's actual shape, rather than guessed here in the abstract.

## Done

(not yet)
