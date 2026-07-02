# Traceability Model

## Purpose

Make the link structure explicit across intent, test-management artifacts, automation code, execution, reports, and triage.

This keeps `testcase`, `teststep`, `testcode`, `test execution`, and `test report` from collapsing into one ambiguous layer.

## Core Chain

| Layer | Object | Primary Owner | Must Link To | Notes |
|-------|--------|---------------|--------------|-------|
| Intent | Intent Contract | Architect/Planner | none or parent task | Human-readable behavior and constraints start here. |
| Test Management | Test Case | test-management workflow | Intent Contract | A test case expresses managed verification coverage, not automation code. |
| Test Management | Test Step | test-management workflow | Test Case | Steps are managed substructure of a test case. |
| Automation | Test Code | Implementer or test-automation flow | Intent Contract, Test Case, Test Step when available | Automation code realizes managed or implied verification behavior. |
| Execution | Test Execution | test-execution workflow | Test Code | A run targets specific automated test code on a chosen backend. |
| Observation | Test Report | report review workflow | Test Execution, Test Code | Reports capture observed outcomes and artifacts from execution. |
| Triage | Report Triage | Test Report Reviewer or downstream ticketing flow | Test Report | Triage classifies failure causes and decides the next owner or ticket target. |
| Follow-up | Task or Ticket | task or ticketing backend | Report Triage, Intent, Test Code as needed | Follow-up work should preserve why the issue exists and where it surfaced. |

## Rules

- `testcase` and `teststep` are management objects.
- `testcode` is automation implementation.
- `test execution` is the runtime invocation layer.
- `test report` is observed evidence, not a test definition.
- `report triage` is the classification and ownership decision layer.
- Each downstream layer should preserve upstream references when the backend supports linking.

## Minimal Traceability Expectations

- Intent should map to at least one testcase or a directly justified testcode slice.
- Testcode should link back to intent and, when managed artifacts exist, to testcase and teststep.
- Test reports should identify the executed testcode and execution backend.
- Triage outcomes should identify whether the failure belongs to product, environment, data, infrastructure, automation, or unknown signal.