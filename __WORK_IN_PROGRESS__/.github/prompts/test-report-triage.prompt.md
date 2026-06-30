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

Required behavior:

- Treat this as the `workflow.testreport.triage` capability.
- Classify the provided report evidence using the triage taxonomy.
- Identify the most likely next owner and next debugging path.
- Preserve the distinction between report review, triage, and ticket drafting.
- If evidence is too weak, use `unclear-signal` and say what additional evidence is needed.
- Do not create tickets or write to external systems in this command.
- If the user wants a follow-up task or ticket draft, point to the next appropriate workflow instead of guessing backend behavior.

Respond in this shape:

- `Answer:` one to three lines with the primary triage result.
- `Evidence:` strongest signals and affected area.
- `Triage:` primary class, likely owner, and likely next action.
- `Risk/Unknown:` ambiguity, conflicting signals, or missing artifacts.
- `Next:` smallest useful follow-up.