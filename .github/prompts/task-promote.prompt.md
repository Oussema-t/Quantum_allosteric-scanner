---
description: "Promote reusable outcomes from a TASK file into review and contract artifacts."
name: "Task Promote"
argument-hint: "TASK path and optional selectors such as sections=ui-intent,best-practice"
agent: "agent"
---

Use the task-promotion workflow for this repository.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- backend selection: [BACKEND_SELECTION](../../.ai/reference/BACKEND_SELECTION.md)
- task file shape: [TASKS README](../../.ai/tasks/README.md)
- traceability model: [TRACEABILITY_MODEL](../../.ai/reference/TRACEABILITY_MODEL.md)

Required behavior:

- Treat this as the `workflow.task.promote` capability.
- Require a task file path matching `.ai/tasks/TASK-*.md`.
- Default extraction targets:
  - UI intent baseline content -> contract artifact under `.ai/tasks/contracts/`
  - architecture-relevant findings and simplification candidates -> review artifact under `.ai/reviews/`
- If optional `sections=<csv>` is provided, restrict promotion to the selected sections.
- If optional `dry-run` is provided, produce promotion plan only and do not write files.
- Promotion should be additive and non-destructive: do not delete task content.
- Prefer retrieval-first behavior:
  - if a matching contract/review artifact already exists, update it in place instead of creating duplicates.
- Include provenance links back to the source TASK path and section names.
- Keep review artifacts concise and evidence-first.
- Keep contract artifacts stable and reusable across follow-up tasks.

Default output targets:

- Contract file: `.ai/tasks/contracts/<task-id>-ui-intent-baseline.md`
- Review file: `.ai/reviews/REVIEW-<date>-<task-id>-promotion.md`

Respond in this shape:

- `Answer:` what was promoted and where.
- `Evidence:` source TASK path, promoted section names, target artifact paths.
- `Risk/Unknown:` missing source sections, weak confidence, or promotion collisions.
- `Next:` smallest useful follow-up.
