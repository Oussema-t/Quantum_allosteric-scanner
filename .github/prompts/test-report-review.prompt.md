---
description: "Review test reports and artifacts to classify likely failure causes without writing tickets."
name: "Test Report Review"
argument-hint: "Report path, artifact references, or the area you want triaged"
agent: "agent"
---

Use the Test Report Reviewer workflow for this repository.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- backend selection: [BACKEND_SELECTION](../../.ai/reference/BACKEND_SELECTION.md)
- traceability model: [TRACEABILITY_MODEL](../../.ai/reference/TRACEABILITY_MODEL.md)
- triage taxonomy: [TEST_REPORT_TRIAGE_TAXONOMY](../../.ai/reference/TEST_REPORT_TRIAGE_TAXONOMY.md)
- role brief: [TEST_REPORT_REVIEWER](../../.ai/experts/test-report-reviewer.md)

Required behavior:

- Treat this as the `workflow.testreport.review` capability.
- Review the provided execution reports, logs, and artifacts.
- Classify failures using the triage taxonomy.
- Preserve separation between test-management objects, automation code, and observed report evidence.
- If links to intent, testcase, teststep, or testcode are visible, include them.
- Do not create tickets or modify external systems in this review command.
- If the evidence is too weak, use `unclear-signal` and say what additional artifacts are needed.
- If the user argument includes a path matching `.ai/tasks/TASK-*.md`, update that task file in the same run.
- For task-file updates, write or refresh section `## Report Review Outcome`.
- Persist the current review class, affected area, strongest evidence signals, risk/unknown, and smallest next debugging step.
- Treat task-file persistence as required for this command when a TASK path is provided; only skip file writes if explicitly asked to run read-only.

Respond in this shape:

- `Answer:` one to three lines with what appears broken and the primary triage class.
- `Evidence:` report signals, linked artifacts, and affected system area.
- `Risk/Unknown:` ambiguity, missing artifacts, or mixed signals.
- `Next:` best debugging or escalation step.