---
description: "Infer UI intent from testcase exports and compare against current automation assertions."
name: "UI Intent Review"
argument-hint: "Task/case reference and optional testcase export source such as CSV path"
agent: "agent"
---

Use the UI-intent review workflow for this repository.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- traceability model: [TRACEABILITY_MODEL](../../.ai/reference/TRACEABILITY_MODEL.md)
- test report taxonomy: [TEST_REPORT_TRIAGE_TAXONOMY](../../.ai/reference/TEST_REPORT_TRIAGE_TAXONOMY.md)

Required behavior:

- Treat this as the `workflow.uiintent.review` capability.
- Infer UI intent from exported testcase artifacts such as CSV or structured testcase fields.
- Compare inferred intent against current automation assertions and role contracts.
- Keep this workflow read-only by default.
- If source evidence is weak or missing, report `unclear-signal` and list the minimum missing artifacts.
- Do not modify repository files unless user explicitly asks for persistence.
- If the user provides a task reference, include traceability mapping from testcase IDs to affected test-code locations.
- Always output the smallest safe contract adjustment before broader refactor suggestions.

Respond in this shape:

- `Answer:` one to three lines with primary alignment status.
- `Evidence:` testcase/export source, compared assertions, and strongest drift signal.
- `Intent Drift:` only mismatches with severity (`high|medium|low`).
- `Risk/Unknown:` ambiguity, conflicting source intent, or missing evidence.
- `Next:` smallest safe contract adjustment or follow-up check.
