---
description: "Draft or refresh the current Intent Contract so the first agent can bootstrap a bounded task thread from the intent layer."
name: "Intent Contract"
argument-hint: "Outcome, scope, constraints, scenarios, or current task context"
agent: "agent"
---

Use the intent-formulation workflow for the current slice.

Sources:

- operation protocol: [OPERATION_PROTOCOL](../../.ai/reference/OPERATION_PROTOCOL.md)
- intent template: [INTENT_CONTRACT_TEMPLATE](../../.ai/reference/INTENT_CONTRACT_TEMPLATE.md)
- first agent bootstrap: [FIRST_AGENT_BOOTSTRAP](../../.ai/reference/FIRST_AGENT_BOOTSTRAP.md)
- starter task example: [STARTER_TASK_EXAMPLE](../../.ai/reference/STARTER_TASK_EXAMPLE.md)

Required behavior:

- Treat this as the `Intent Formulation` protocol step.
- Draft or refresh a bounded Intent Contract before exact implementation details.
- If no task exists yet, shape the output so it can be inserted directly into a new `.ai/tasks/TASK-*.md` file. Create one if `apply` is requested.
- If a task already exists, refine the existing intent instead of creating a conflicting second one.
- Keep the intent human-readable and implementation-agnostic.
- Use BDD-style acceptance scenarios.
- Make scope, non-goals, constraints, discovery needs, and planned validation explicit.
- Surface missing facts as `Discovery Needs` instead of guessing them.
- Do not modify files unless the user separately asks for a task or file update.
- Ask follow-up questions if the intent is unclear or missing critical context.

Respond in this shape:

- `Intent Contract:` ready-to-paste section content.
- `Discovery Needs:` only the facts that still block a safe bounded slice.
- `Risk/Unknown:` ambiguity, ownership gaps, or missing acceptance criteria.
- `Next:` smallest useful follow-up such as create task, run intent review, or start discovery.