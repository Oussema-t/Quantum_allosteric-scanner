---
description: "Classify test-report failures and route the next likely action without creating tickets."
name: "Test Report Triage"
argument-hint: "Report path, artifact references, or execution summary to classify"
agent: "agent"
---

Use the test-report triage workflow for this repository.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- backend selection: [BACKEND_SELECTION](../../.ai/reference/BACKEND_SELECTION.md)
- triage taxonomy: [TEST_REPORT_TRIAGE_TAXONOMY](../../.ai/reference/TEST_REPORT_TRIAGE_TAXONOMY.md)
- traceability model: [TRACEABILITY_MODEL](../../.ai/reference/TRACEABILITY_MODEL.md)
- role brief: [TEST_REPORT_REVIEWER](../../.ai/experts/test-report-reviewer.md)
- task file shape: [TASKS README](../../.ai/tasks/README.md)

Required behavior:

- Treat this as the `workflow.testreport.triage` capability.
- This workflow may be invoked directly by `/test-report-triage` or auto-invoked by `/test-execute` on high-confidence failed executions.
- Classify the provided report evidence using the triage taxonomy.
- Identify the most likely next owner and next debugging path.
- Preserve the distinction between report review, triage, and ticket drafting.
- If evidence is too weak, use `unclear-signal` and say what additional evidence is needed.
- Do not create tickets or write to external systems in this command.
- If the user wants a follow-up task or ticket draft, point to the next appropriate workflow instead of guessing backend behavior.
- If the user argument includes a path matching `.ai/tasks/TASK-*.md`, update that task file in the same run.
- For task-file updates, write or refresh two sections: `## Triage Outcome` and `## Immediate Next Steps`.
- Persist the current triage class, likely owner, affected area, rationale, and three smallest actionable next steps.
- For task-file updates, also synchronize relevant `## TODO` entries for the active phase.
- Mark completed discovery/triage actions as done in place and append newly required follow-up actions from triage under the same phase.
- Treat task-file persistence as required for this command when a TASK path is provided; only skip file writes if explicitly asked to run read-only.
- When this workflow is auto-invoked by `/test-execute` and classification is `automation-defect` with high confidence, you may continue with one task-execution hop.
- For this hop, create or refresh one bounded TODO in a TASK file and invoke `workflow.task.perform` for that TODO in the same run.
- Use the same confidence guardrails: no auto task-perform for unclear-signal, mixed ownership, read-only intent, or missing evidence.

Respond in this shape:

- `Answer:` one to three lines with the primary triage result.
- `Evidence:` strongest signals and affected area.
- `Triage:` primary class, likely owner, and likely next action.
- `Task:` include only when task chaining was executed; provide task path, selected TODO, and outcome.
- `Risk/Unknown:` ambiguity, conflicting signals, or missing artifacts.
- `Next:` smallest useful follow-up.