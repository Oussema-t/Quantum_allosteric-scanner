---
description: "Summarize the current staged packaging state for branch or commit planning."
name: "Packaging Snapshot"
argument-hint: "Optional constraints such as desired split, commit count, or focus area"
agent: "agent"
---

Use the Commit Packager workflow to summarize the current packaging state for this repository.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- slash-command catalog: [SLASH_COMMAND_CANDIDATES](../../.ai/reference/SLASH_COMMAND_CANDIDATES.md)
- current provider: [packaging-snapshot.sh](../../agents-tools/commit-packaging/packaging-snapshot.sh)
- optional follow-up provider: [list-branch-files.sh](../../agents-tools/commit-packaging/list-branch-files.sh)

Required behavior:

- Treat this as the `repo.packaging.snapshot` capability.
- Use the current provider script unless a narrower equivalent capability call is clearly better.
- If the user supplied additional constraints, apply them to the recommendation.
- If the snapshot suggests mixed concerns, inspect the `maintenance` and `cluster` file lists before recommending a split.
- If there are no staged changes, say so and stop.
- Do not modify git state, stage files, unstage files, or create commits.

Respond in this shape:

- `Answer:` one to three lines with the packaging summary.
- `Evidence:` branch, staged status summary, diff size, bucket counts, and relevant file groups.
- `Risk/Unknown:` classification uncertainty, shared files, or missing context.
- `Next:` smallest useful follow-up, if any.