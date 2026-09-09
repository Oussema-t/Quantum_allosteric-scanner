# Task Claim Locks

Per-task lock files backing `.ai/tools/claim.py` (TASK-0024).

Each `TASK-XXXX.lock` file is a small JSON record (`task_id`, `claimant`,
`claimed_at`, optional `note`/override fields) created with an atomic
`O_EXCL` open — the mechanism that replaced TASK-0017's hand-edited
`Claimed By` / `Claimed At` cells in `.ai/COMMON.md`'s Active Work Registry
after that soft convention was clobbered twice by concurrent whole-file
writes in the same session it was introduced.

`*.lock` files are gitignored — they are live coordination state for
whoever currently has the repo checked out, not reviewed history. The
registry table in `.ai/COMMON.md` stays the human-readable, git-tracked
view; run `python3 .ai/tools/claim.py sync` to regenerate its `Claimed By`
/ `Claimed At` columns from these lock files.

## Non-task resource locks (TASK-0028, TASK-0024.001)

`claim`/`release`/`status` accept two kinds of id that are **not** task
rows, with the same `O_EXCL` atomicity and `--force --reason` override:

- **`GIT-COMMIT`** (TASK-0028) — the git add → commit → push critical
  section. Backed by `GIT-COMMIT.lock`. Overriding a held one needs
  `--hitl-override` on top of `--force --reason` (see `claim.py --help`).
- **Arbitrary whole-file / resource ids** (TASK-0024.001) — any argument
  that is *not* a clean task-id shape (`24`, `TASK-0024`, `TASK-0026.001`,
  `26.1`) is taken as a literal resource id: sanitized, upper-cased, and
  namespaced under `RESOURCE-` (e.g. `claim COMMON.md` →
  `RESOURCE-COMMON.MD.lock`; `claim __WORK_IN_PROGRESS__/RESULTS.md` →
  `RESOURCE-__WORK_IN_PROGRESS___RESULTS.MD.lock`). Use this before a
  **working-tree-level** operation on a shared coordination file that a
  normal row edit wouldn't cover — `git checkout -- <path>`, a multi-step
  edit spanning several tool calls, a manual restore-from-backup — so a
  concurrent thread checking `status` sees "hands off" first. Three
  independent incidents on `.ai/COMMON.md` motivated this (a git-checkout/
  restore surgery, a stale-uncommitted-rows-in-the-working-tree stage, and
  a `sync`-recovery reset — the last two 2026-07-11 / 2026-09-09).

`is_task_id()` is false for both kinds, so `move`/`resolve` refuse them
(they only operate on real `TASK-XXXX` rows) and `sync` ignores them
entirely — a `RESOURCE-*` lock has no registry row and never produces a
"no task file on disk" warning.

**Claim with the real relative path** (`.ai/COMMON.md`, not bare
`COMMON.md`) if you also want `check-staleness` to work: it records a
content-hash snapshot only when the raw claim argument resolves to an
actual file on disk. A bare name still gives you the advisory lock, just
no staleness detection.

See `.ai/tasks/DONE/TASK-0024-claim-lock-tool.md` for the design rationale
and `.ai/tools/claim.py --help` (or `claim`/`release`/`status`/`sync -h`)
for usage.
