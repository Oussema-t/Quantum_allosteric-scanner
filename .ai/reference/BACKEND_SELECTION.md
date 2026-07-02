# Workflow Backend Selection

## Purpose

Define which backend currently owns each workflow object family.

This prevents slash commands and capability contracts from silently guessing whether they should operate on disk, in a ticketing system, or through another integration.

## Current Backend Map

| Object Family | Current Backend | Status | Notes |
|---------------|-----------------|--------|-------|
| Task | on-disk task files under `.ai/tasks/` | active default | External ticket systems such as JIRA remain future backend adapters, not the current default. |
| Test Case | unresolved | candidate only | Choose explicit backend before implementing live `/testcase-*` commands. |
| Test Step | unresolved | candidate only | Treat steps as test-management objects, not automation code. |
| Test Code | repository files plus agent orchestration | active by implication | This is the automation layer and must stay distinct from test-management records. |
| Test Execution | local repository execution via repo-aware tools | active default | Project-specific runners such as Playwright are future backend adapters until the execution capability names them explicitly. |
| Test Report Review | report artifacts plus agent orchestration | active default | This is read-only analysis over observed evidence. |
| Test Report Triage | prompt or agent orchestration over report artifacts | active default | This is read-only classification and routing over observed evidence. |
| Ticket or Issue Escalation | unresolved | candidate only | Choose explicit backend before implementing live ticket-drafting or ticket-creation commands. |
| Agent Delegation | prompt or agent orchestration | active default | Delegation should route by role contract, not raw prose. |

## Backend Adapter Contract

Each backend adapter should define:

- object family it serves
- canonical identifier shape
- allowed read and write operations
- lifecycle or resolution mapping rules
- required auth, environment, or project context
- safety model including destructive operations and dry-run expectations
- traceability fields it can preserve

## Backend Activation Requirements

| Family | Required Before Live Slash Commands |
|--------|------------------------------------|
| Test Case | backend name, auth model, ID shape, and lifecycle field mapping |
| Test Step | parent-case relation model, ordering model, and lifecycle field mapping |
| Ticket or Issue Escalation | backend name, project or space selection, issue type mapping, and auth model |

See [ISSUE_BACKEND_PLACEHOLDER_CONTRACT](./ISSUE_BACKEND_PLACEHOLDER_CONTRACT.md) for the minimum escalation-backend contract.

## Current Rules

- Every workflow capability family should name its active backend or explicitly say it is unresolved.
- Slash commands should not become live until their backend is explicit enough to avoid accidental writes to the wrong system.
- In heavily manual environments, local wrappers that emit local artifacts or read-only output are preferred before backend-integrated automation.
- Backend adapters may change later, but the capability name should stay stable.
- Task deletion means permanent removal.
- Task resolution means updating lifecycle state with an explicit backend-relevant resolution value.
- Testcase and teststep commands should stay candidate-only until their backend adapter is explicit.
- Remote execution backends should not be treated as active defaults until the execution capability supports them directly.
- Non-local test execution must name the execution backend explicitly.
- Report review may be live without ticketing integration, but ticket drafting must wait for an explicit issue backend.
- Report triage may be live as read-only classification and routing, even when ticket or issue escalation is still unresolved.