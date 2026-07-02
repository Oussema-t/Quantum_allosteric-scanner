---
description: "Run a findings-first code-quality review focused on recurring best-practice failures and weak validation."
name: "Best Practice Review"
argument-hint: "Optional scope hint such as file, folder, or slice"
agent: "agent"
---

Use the code-quality review workflow for the current slice.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- slash-command catalog: [SLASH_COMMAND_CANDIDATES](../../.ai/reference/SLASH_COMMAND_CANDIDATES.md)
- general critic brief: [GENERAL_CRITIC](../../.ai/experts/general-critic.md)
- code reviewer brief: [CODE_REVIEWER](../../.ai/experts/code-reviewer.md)
- task file shape: [TASKS README](../../.ai/tasks/README.md)

Required behavior:

- Treat this as the `workflow.codequality.review` capability.
- Fix the focus to `best-practice`.
- Review the current slice for recurring implementation mistakes, weak validation, brittle structure, and local best-practice failures that are likely to recur.
- Prefer findings-first output with direct evidence over immediate refactor design.
- If the user argument includes a path matching `.ai/tasks/TASK-*.md`, update that task file in the same run.
- For task-file updates, write or refresh section `## Best-Practice Review Outcome`.
- Persist focus area, strongest findings, refactor-triage classification, high-confidence simplification candidate (if present), and confidence.
- If findings are high-confidence and a bounded refactor candidate is present, continue in the same run with `workflow.codequality.refactor-plan`.
- For this chain hop, pass the same TASK path and accepted finding set to refactor-plan.
- Skip auto refactor-plan when confidence is below high, requested mode is read-only/no-chain, or evidence is incomplete.
- Do not modify files unless the user separately asks for changes.

Respond in this shape:

- `Findings:` ordered by severity with direct evidence.
- `Open Questions:` only when evidence is incomplete.
- `Task:` include only when task persistence or chaining to refactor-plan was executed; provide task path and outcome.
- `Risk/Unknown:` residual uncertainty or validation gaps.
- `Next:` smallest useful corrective action.