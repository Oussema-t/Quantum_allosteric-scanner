---
description: "Run a findings-first code-quality review with an explicit focus such as dry, duplication, generalization, or best-practice."
name: "Quality Review"
argument-hint: "Optional focus such as dry, duplication, generalization, best-practice, or all"
agent: "agent"
---

Use the code-quality review workflow for the current slice.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- slash-command catalog: [SLASH_COMMAND_CANDIDATES](../../.ai/reference/SLASH_COMMAND_CANDIDATES.md)
- general critic brief: [GENERAL_CRITIC](../../.ai/experts/general-critic.md)
- code reviewer brief: [CODE_REVIEWER](../../.ai/experts/code-reviewer.md)

Required behavior:

- Treat this as the `workflow.codequality.review` capability.
- Use the requested focus if one is supplied. Supported focuses include `dry`, `duplication`, `generalization`, `best-practice`, and `all`.
- Review the current slice for repeated logic, weak abstraction boundaries, avoidable copy-paste, and recurring best-practice failures.
- Prefer findings-first output with direct evidence over premature refactor design.
- If a refactor is clearly warranted, recommend a bounded follow-up rather than rewriting the slice during the review.
- Do not modify files unless the user separately asks for changes.

Respond in this shape:

- `Findings:` ordered by severity with direct evidence.
- `Open Questions:` only when evidence is incomplete.
- `Risk/Unknown:` residual uncertainty or validation gaps.
- `Next:` smallest useful corrective action.