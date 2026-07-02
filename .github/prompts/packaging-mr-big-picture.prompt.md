---
description: "Generate a big-picture merge-request summary from current split plan/state."
name: "Packaging MR Big Picture"
argument-hint: "Optional: output=.ai/tasks/mr-big-picture.md dry-run"
agent: "agent"
---

Use the Commit Packager MR-summary workflow to create a reusable big-picture message for a merge request.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- slash-command catalog: [SLASH_COMMAND_CANDIDATES](../../.ai/reference/SLASH_COMMAND_CANDIDATES.md)
- provider entrypoint: [capability-runner.sh](../../agents-tools/capability-runner.sh)

Required behavior:

- Treat this as the `repo.packaging.mr-big-picture` capability.
- Use `.ai/tasks/commit-split-plan.json` and `.ai/tasks/commit-split-state.json` by default.
- Generate a markdown big-picture summary file for MR description.
- Default output path: `.ai/tasks/mr-big-picture.md`.
- Default to apply (write output file) unless the user explicitly asks for dry-run.
- Do not stage files and do not create commits.

Execution hint:

- Apply: `agents-tools/capability-runner.sh repo.packaging.mr-big-picture --json`
- Apply custom output: `agents-tools/capability-runner.sh repo.packaging.mr-big-picture --output .ai/tasks/mr-big-picture.md --json`
- Dry-run: `agents-tools/capability-runner.sh repo.packaging.mr-big-picture --dry-run --json`

Respond in this shape:

- `Answer:` output path and summary readiness.
- `Evidence:` branch, changed count, done group count, deferred group count.
- `Risk/Unknown:` stale plan/state or missing grouping context.
- `Next:` smallest useful follow-up.
