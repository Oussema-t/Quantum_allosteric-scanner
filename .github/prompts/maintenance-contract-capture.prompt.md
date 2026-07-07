---
description: "Capture a scoped UI behavior contract and probe matrix artifact for maintenance slices."
name: "Maintenance Contract Capture"
argument-hint: "Required: scope=<scope>; Optional: task-file=.ai/tasks/TASK-*.md output=.ai/tasks/contracts/behavior-contract-<scope>.md dry-run"
agent: "agent"
---

Use the maintenance contract-capture workflow to persist a behavior contract that agents should reuse during maintenance and implementation.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- slash-command catalog: [SLASH_COMMAND_CANDIDATES](../../.ai/reference/SLASH_COMMAND_CANDIDATES.md)
- provider entrypoint: [capability-runner.sh](../../agents-tools/capability-runner.sh)

Required behavior:

- Treat this as `repo.maintenance.behavior-contract-capture`.
- Write a ready-to-use artifact that contains:
  - Behavior Contract
  - Probe Matrix
  - Fast-Fail Budgets
- Default output should be scoped under `.ai/tasks/contracts/`.
- If `task-file` is provided, extract existing `Behavior Contract`, `Probe Matrix`, and `Fast-Fail Budgets` sections from that task when possible.
- If sections are missing, preserve placeholders instead of guessing.
- Do not stage files and do not create commits.

Execution hint:

- Apply: `agents-tools/capability-runner.sh repo.maintenance.behavior-contract-capture --task-file .ai/tasks/TASK-0002-006m-token-form-visibility-maintenance.md --scope 006-m-codebuild-token-form --json`
- Apply custom output: `agents-tools/capability-runner.sh repo.maintenance.behavior-contract-capture --task-file .ai/tasks/TASK-0002-006m-token-form-visibility-maintenance.md --scope 006-m-codebuild-token-form --output .ai/tasks/contracts/behavior-contract-006m.md --json`
- Dry-run: `agents-tools/capability-runner.sh repo.maintenance.behavior-contract-capture --task-file .ai/tasks/TASK-0002-006m-token-form-visibility-maintenance.md --scope 006-m-codebuild-token-form --dry-run --json`

Respond in this shape:

- `Answer:` output path and capture readiness.
- `Evidence:` scope, source task, behavior rule count, probe count, budget count.
- `Risk/Unknown:` missing sections, stale task context, or placeholder-only output.
- `Next:` smallest useful follow-up (for example `/Intent-Review` or `/Test-Execute`).
