---
description: "Run a findings-first code-quality review focused on repeated logic or repeated structures that should be consolidated."
name: "Duplication Review"
argument-hint: "Optional scope hint such as file, folder, or slice"
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
- Fix the focus to `duplication`.
- Review the current slice for repeated logic, parallel structures, duplicated configuration, and code paths that should converge.
- Prefer findings-first output with direct evidence over immediate refactor design.
- Do not modify files unless the user separately asks for changes.

Respond in this shape:

- `Findings:` ordered by severity with direct evidence.
- `Open Questions:` only when evidence is incomplete.
- `Risk/Unknown:` residual uncertainty or validation gaps.
- `Next:` smallest useful corrective action.