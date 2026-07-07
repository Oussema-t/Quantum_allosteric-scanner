---
description: "Execute specified automated test code using the active execution backend, with optional auto-triage and optional quality chaining."
name: "Test Execute"
argument-hint: "Test path/name and optional backend such as local; optional quality chain: chain-quality"
agent: "agent"
---

Use the test-execution workflow for this repository.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- backend selection: [BACKEND_SELECTION](../../.ai/reference/BACKEND_SELECTION.md)
- traceability model: [TRACEABILITY_MODEL](../../.ai/reference/TRACEABILITY_MODEL.md)
- triage taxonomy: [TEST_REPORT_TRIAGE_TAXONOMY](../../.ai/reference/TEST_REPORT_TRIAGE_TAXONOMY.md)
- task file shape: [TASKS README](../../.ai/tasks/README.md)

Required behavior:

- Treat this as the `workflow.testexecution.run` capability.
- Determine the requested test target and desired backend from the user input.
- Use the active execution backend from the backend selection reference.
- Prefer local execution when no backend is specified.
- For local repository execution, prefer the repo-aware test execution tooling over ad hoc shell behavior.
- Command-structure contract for local execution: follow
  [command-hygiene](../instructions/tooling/command-hygiene.instructions.md)
  (repo-wide, TASK-0025) — one stable capability command per run (e.g.
  `agents-tools/capability-runner.sh repo.test.playwright-local ...`), no
  chained/piped shell orchestration, no inline variable-setup-plus-execution,
  request-file mode for multi-argument or repeatable runs, artifact
  extraction as a separate command after execution.
- If the user asks for a remote or project-specific backend and that adapter is unresolved, say so explicitly instead of guessing.
- Do not reinterpret testcase or teststep identifiers as executable test code without a clear traceability link.
- After execution, decide whether report triage is the most likely immediate next step.
- If execution fails and triage confidence is high, automatically continue in the same run using the `workflow.testreport.triage` behavior (do not wait for a second slash command).
- For auto-triage, classify using the taxonomy, identify likely owner, and provide the smallest next debugging step.
- If confidence is not high, do not auto-chain triage; explicitly say what missing evidence is needed.
- If a TASK file path is provided in arguments or present in active context, persist triage outcome and immediate next steps in that TASK file using the same write contract as `/test-report-triage`.
- If auto-triage returns `automation-defect` with high confidence and intent remains valid, continue in the same run with task orchestration.
- For this task orchestration chain, create or update one bounded TODO in a TASK file and immediately invoke `workflow.task.perform` for that single item.
- Prefer TASK selection in this order: explicit TASK path in arguments, active TASK context, existing matching active TASK, then create a new TASK file.
- The auto-created TODO must be small and implementation-ready, for example locator or synchronization maintenance plus focused rerun.
- Skip auto task-perform when confidence is below high, requested mode is read-only/triage-only/no-code, or required evidence is missing.
- Optional quality chaining is enabled only when user explicitly passes `chain-quality`.
- When `chain-quality` is enabled and auto task-perform executed a code change with focused validation and high-confidence outcome, continue in the same run with `workflow.codequality.review` using `best-practice` focus.
- Skip quality chaining when task-perform changed only non-code files, confidence is below high, or evidence is incomplete.

Respond in this shape:

- `Answer:` what was executed, on which backend, and the high-level outcome.
- `Evidence:` targeted test identifiers or files, backend used, and result summary.
- `Triage:` include only when auto-triage was executed; provide class, likely owner, and likely next action.
- `Task:` include only when auto task orchestration was executed; provide task path, created/selected TODO, and task-perform outcome.
- `Quality:` include only when chain-quality was requested; provide gate decision and best-practice-review outcome.
- `Risk/Unknown:` backend limitations, traceability gaps, or unresolved runner support.
- `Next:` smallest useful follow-up.