---
description: "Execute specified automated test code using the active execution backend."
name: "Test Execute"
argument-hint: "Test path/name and optional backend such as local or testkube"
agent: "agent"
---

Use the test-execution workflow for this repository.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- backend selection: [BACKEND_SELECTION](../../.ai/reference/BACKEND_SELECTION.md)
- traceability model: [TRACEABILITY_MODEL](../../.ai/reference/TRACEABILITY_MODEL.md)

Required behavior:

- Treat this as the `workflow.testexecution.run` capability.
- Determine the requested test target and desired backend from the user input.
- Use the active execution backend from the backend selection reference.
- Prefer local execution when no backend is specified.
- For local repository execution, prefer the repo-aware test execution tooling over ad hoc shell behavior.
- If the user asks for a remote or project-specific backend such as Testkube and that adapter is unresolved, say so explicitly instead of guessing.
- Do not reinterpret testcase or teststep identifiers as executable test code without a clear traceability link.

Respond in this shape:

- `Answer:` what was executed, on which backend, and the high-level outcome.
- `Evidence:` targeted test identifiers or files, backend used, and result summary.
- `Risk/Unknown:` backend limitations, traceability gaps, or unresolved runner support.
- `Next:` smallest useful follow-up.