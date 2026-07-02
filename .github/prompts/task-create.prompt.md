---
description: "Create a task in the active task backend using the scaffold task format."
name: "Task Create"
argument-hint: "Task outcome, scope, owner, and any intent constraints"
agent: "agent"
---

Use the task-creation workflow for this repository.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- backend selection: [BACKEND_SELECTION](../../.ai/reference/BACKEND_SELECTION.md)
- task file shape: [TASKS README](../../.ai/tasks/README.md)
- intent template: [INTENT_CONTRACT_TEMPLATE](../../.ai/reference/INTENT_CONTRACT_TEMPLATE.md)

Required behavior:

- Treat this as the `workflow.task.create` capability.
- Use the active task backend from the backend selection reference.
- For the current default backend, create a new task file under `.ai/tasks/`.
- Include the mandatory `Intent Contract` section and all required task sections.
- Keep the task bounded to one coherent outcome.
- If an equivalent active task already exists, do not create a duplicate; report the existing task instead.
- Do not write to external ticketing systems unless the backend selection changes explicitly.

Respond in this shape:

- `Answer:` what task was created or which existing task matched.
- `Evidence:` backend used, task path or identifier, and key intent fields.
- `Risk/Unknown:` missing scope, unclear owner, or unresolved intent details.
- `Next:` smallest useful follow-up.