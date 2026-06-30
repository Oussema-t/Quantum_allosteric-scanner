---
description: "Turn accepted code-quality findings into a bounded refactor plan with validation steps."
name: "Refactor Plan"
argument-hint: "Optional focus or accepted finding set"
agent: "agent"
---

Use the code-quality refactor-planning workflow for the current slice.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- slash-command catalog: [SLASH_COMMAND_CANDIDATES](../../.ai/reference/SLASH_COMMAND_CANDIDATES.md)
- operation protocol: [OPERATION_PROTOCOL](../../.ai/reference/OPERATION_PROTOCOL.md)
- code reviewer brief: [CODE_REVIEWER](../../.ai/experts/code-reviewer.md)

Required behavior:

- Treat this as the `workflow.codequality.refactor-plan` capability.
- Prefer accepted findings from `quality-review` or one of the focused code-quality review commands when they exist.
- If accepted findings are not supplied, derive the plan only from direct evidence in the current slice and label assumptions clearly.
- Produce a bounded refactor plan, not a broad redesign.
- Sequence the work smallest-first.
- Include the first focused validation step that should run immediately after the first substantive edit.
- Do not modify files unless the user separately asks for changes.

Respond in this shape:

- `Refactor Goal:` concise intended outcome.
- `Plan:` numbered bounded steps.
- `Validation:` first focused validation and follow-up checks.
- `Risk/Unknown:` residual uncertainty or preconditions.
- `Next:` smallest useful action.