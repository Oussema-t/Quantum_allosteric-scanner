# Issue Backend Placeholder Contract

## Purpose

Define the minimum contract an issue or ticket backend must satisfy before live ticket-drafting or ticket-creation commands become safe.

This keeps report triage and issue escalation separate until the backend is explicit enough to avoid accidental writes or lossy field mapping.

## Status

- current state: unresolved placeholder
- safe live commands today: report review and report triage
- gated commands: ticket draft, issue create, issue update, issue link

## Required Adapter Fields

| Field | Purpose |
|-------|---------|
| backend name | identify the issue system unambiguously |
| project, space, or queue selection | decide where issues will be created |
| canonical issue identifier shape | support stable linking from tasks, reports, and code |
| issue type mapping | map scaffold concepts such as defect, task, or investigation to backend types |
| severity or priority mapping | preserve triage importance consistently |
| status and resolution mapping | translate scaffold lifecycle terms into backend-native values |
| auth model | declare how the backend is accessed safely |
| link model | define how issues can reference intent, testcase, teststep, testcode, reports, and tasks |
| artifact support | define whether logs, traces, screenshots, or report links can be attached or referenced |
| dry-run or preview mode | allow safe preview before write operations |

## Command Gating Rules

- `/test-report-ticket-draft` should stay candidate-only until this contract is filled.
- Any future `/issue-create`, `/issue-update`, or `/issue-link` command should stay candidate-only until this contract is filled.
- Backends that cannot preview or dry-run should require stricter confirmation before live write commands are added.

## Minimal Output Contract

Before a live ticketing command is enabled, the adapter should be able to produce:

- target backend name
- target project, space, or queue
- issue type
- title or summary
- body or description
- mapped severity or priority
- linked intent, task, test, or report references
- preview of what will be written

## Current Rule

- Keep issue escalation separate from report review and report triage until the backend is explicit.