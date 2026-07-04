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

See `.ai/tasks/DONE/TASK-0024-claim-lock-tool.md` for the design rationale
and `.ai/tools/claim.py --help` (or `claim`/`release`/`status`/`sync -h`)
for usage.
