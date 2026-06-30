---
description: "Run a critic review over the current intent, task slice, or implementation evidence."
name: "Delegate Critic"
argument-hint: "Optional review focus such as intent, code, validation, or report triage"
agent: "agent"
---

Use the critic workflow for the current slice.

Sources:

- role model: [EXPERTS](../../.ai/experts/README.md)
- general critic brief: [GENERAL_CRITIC](../../.ai/experts/general-critic.md)
- code reviewer brief: [CODE_REVIEWER](../../.ai/experts/code-reviewer.md)
- operation protocol: [OPERATION_PROTOCOL](../../.ai/reference/OPERATION_PROTOCOL.md)

Required behavior:

- Treat this as the `workflow.agent.review` capability.
- Choose General Critic by default.
- If the current slice is primarily code or test implementation, apply Code Reviewer depth.
- Review the active intent, task, implementation, or evidence according to the user focus.
- Keep the review findings-first, severity-ordered, and evidence-first.
- Do not modify files unless the user separately asks for fixes.

Respond in this shape:

- `Findings:` ordered by severity with concrete evidence.
- `Open Questions:` only if the evidence is incomplete.
- `Risk/Unknown:` residual risk or validation gaps.
- `Next:` smallest useful corrective action.