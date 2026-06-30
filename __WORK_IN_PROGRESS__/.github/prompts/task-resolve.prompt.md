---
description: "Resolve a task in the active task backend with an explicit resolution value."
name: "Task Resolve"
argument-hint: "Task id/path, resolution value, and optional resolution note"
agent: "agent"
---

Use the task-resolution workflow for this repository.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- backend selection: [BACKEND_SELECTION](../../.ai/reference/BACKEND_SELECTION.md)
- resolution vocabulary: [RESOLUTION_VOCABULARY](../../.ai/reference/RESOLUTION_VOCABULARY.md)
- task file shape: [TASKS README](../../.ai/tasks/README.md)

Required behavior:

- Treat this as the `workflow.task.resolve` capability.
- Require an explicit canonical resolution value.
- Use the active task backend from the backend selection reference.
- For the current default backend, update the on-disk task file instead of deleting it.
- Preserve task history and reflect the resolution in the task state.
- If the requested resolution value is not canonical, stop and ask for clarification instead of guessing.
- Do not use deletion semantics when the intent is resolve or close.

Respond in this shape:

- `Answer:` what task was resolved and with which resolution.
- `Evidence:` backend used, updated task identifier or path, and the resolution value.
- `Risk/Unknown:` missing task identity, ambiguous resolution, or unresolved backend mismatch.
- `Next:` smallest useful follow-up.