---
description: "Refine an existing commit split plan by moving one path area into a dedicated group."
name: "Packaging Plan Refine"
argument-hint: "Required: path-prefix=<prefix> to-group=<name>; Optional: subject=... rationale=... status=pending|deferred target-branch=<name> dry-run"
agent: "agent"
---

Use this command to correct a generated plan when an area should be isolated into a dedicated group.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- slash-command catalog: [SLASH_COMMAND_CANDIDATES](../../.ai/reference/SLASH_COMMAND_CANDIDATES.md)
- provider entrypoint: [capability-runner.sh](../../agents-tools/capability-runner.sh)

Required behavior:

- Treat this as `repo.packaging.refine-plan`.
- Use `.ai/tasks/commit-split-plan.json` by default.
- Move all files under `path-prefix` into `to-group`.
- Keep exact plan coverage; do not drop files.
- After refinement, run one validation call:
  - `agents-tools/capability-runner.sh repo.packaging.validate-plan-coverage --json`
- Do not stage files and do not create commits.

Execution hint:

- `agents-tools/capability-runner.sh repo.packaging.refine-plan --path-prefix <prefix> --to-group <name> --json`
- `agents-tools/capability-runner.sh repo.packaging.refine-plan --path-prefix <prefix> --to-group <name> --status deferred --target-branch <branch> --json`

Respond in this shape:

- `Answer:` what area was moved and into which group.
- `Evidence:` moved file count, touched source groups, destination group, validation output.
- `Risk/Unknown:` empty match, over-broad prefix, or stale plan/source.
- `Next:` smallest follow-up (for example `/Packaging-Plan-Review` or `/Packaging-Next-Commit dry-run`).
