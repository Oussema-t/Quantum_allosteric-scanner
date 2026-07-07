---
description: "Cleanup stale commit split artifacts from previous packaging plans."
name: "Packaging Plan Cleanup"
argument-hint: "Optional scope/action overrides"
agent: "agent"
---

Use the Commit Packager cleanup workflow to remove or archive stale split-plan artifacts.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- slash-command catalog: [SLASH_COMMAND_CANDIDATES](../../.ai/reference/SLASH_COMMAND_CANDIDATES.md)
- provider entrypoint: [capability-runner.sh](../../agents-tools/capability-runner.sh)

Required behavior:

- Treat this as the `repo.packaging.cleanup-plan` capability.
- Default to dry-run unless the user explicitly asks to apply cleanup.
- Default action is archive; use delete only when explicitly requested.
- Scope cleanup to requested artifacts (`plan`, `state`, `source`, `drafts`, or `all`).
- Do not delete artifacts outside the packaging task files.

Execution hints:

- Dry-run all: `agents-tools/capability-runner.sh repo.packaging.cleanup-plan --json`
- Apply archive all: `agents-tools/capability-runner.sh repo.packaging.cleanup-plan --apply --action archive --scope all --json`
- Apply delete drafts only: `agents-tools/capability-runner.sh repo.packaging.cleanup-plan --apply --action delete --scope drafts --json`

Respond in this shape:

- `Answer:` what was cleaned or what would be cleaned.
- `Evidence:` action, scope, affected file count, and key artifact paths.
- `Risk/Unknown:` destructive mode use, missing files, or skipped scopes.
- `Next:` smallest useful follow-up command (for example `/Packaging-Plan`).
