---
description: "Review an existing commit split plan against deterministic packaging rules before execution."
name: "Packaging Plan Review"
argument-hint: "Optional: min-area-group-size=<n> min-commit-size=<n>"
agent: "agent"
---

Use this command to validate packaging quality gates before running next-commit steps.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- slash-command catalog: [SLASH_COMMAND_CANDIDATES](../../.ai/reference/SLASH_COMMAND_CANDIDATES.md)
- provider entrypoint: [capability-runner.sh](../../agents-tools/capability-runner.sh)

Required behavior:

- Treat this as `repo.packaging.review-plan-rules`.
- Use `.ai/tasks/commit-split-plan.json` and `.ai/tasks/changed-files.source.json` by default.
- Evaluate and report at least:
  - coverage (missing/extra)
  - area cohesion (area split across multiple pending groups over threshold)
  - commit-size floor (pending groups under threshold)
  - ambiguous files
- Do not mutate plan, stage files, or create commits.

Execution hint:

- `agents-tools/capability-runner.sh repo.packaging.review-plan-rules --json`
- `agents-tools/capability-runner.sh repo.packaging.review-plan-rules --min-area-group-size 3 --min-commit-size 3 --json`

Respond in this shape:

- `Answer:` pass/fail and brief reason.
- `Evidence:` pending/deferred counts and each rule result.
- `Risk/Unknown:` stale source snapshot or unresolved policy ambiguity.
- `Next:` exact command to refine (`/Packaging-Plan-Refine`) or proceed (`/Packaging-Next-Commit`).
