---
description: "Prepare the next commit from persisted split plan (stage files, draft message, advance state)."
name: "Packaging Next Commit"
argument-hint: "Optional plan/state path override"
agent: "agent"
---

Use the Commit Packager execution workflow to prepare the next commit step from the persisted split plan.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- slash-command catalog: [SLASH_COMMAND_CANDIDATES](../../.ai/reference/SLASH_COMMAND_CANDIDATES.md)
- provider entrypoint: [capability-runner.sh](../../agents-tools/capability-runner.sh)

Required behavior:

- Treat this as the `repo.packaging.plan-next-commit` capability.
- Use `.ai/tasks/commit-split-plan.json` and `.ai/tasks/commit-split-state.json` by default.
- Apply changes unless the user explicitly asks for dry-run.
- Support explicit target selection via `--group <group-name-or-index>`.
- Support amend-aware staging via `--mode amend` (or `--amend`) to select a related done group.
- Generate commit message draft file and return its path.
- Do not run `git commit` automatically.

Execution hint:

- Apply: `agents-tools/capability-runner.sh repo.packaging.plan-next-commit --apply --json`
- Apply amend candidate: `agents-tools/capability-runner.sh repo.packaging.plan-next-commit --apply --mode amend --json`
- Apply explicit group: `agents-tools/capability-runner.sh repo.packaging.plan-next-commit --apply --group <name-or-index> --json`
- Dry-run: `agents-tools/capability-runner.sh repo.packaging.plan-next-commit --dry-run --json`

Respond in this shape:

- `Answer:` prepared group name and readiness for commit.
- `Evidence:` staged file count, commit subject, message draft path, mode, and selection source.
- `Risk/Unknown:` missing files, empty group, or stale plan.
- `Next:` exact commit command:
	- `git commit -F <message-file>` when mode is `next`
	- `git commit --amend -F <message-file>` when mode is `amend` or selected group status is `done`
