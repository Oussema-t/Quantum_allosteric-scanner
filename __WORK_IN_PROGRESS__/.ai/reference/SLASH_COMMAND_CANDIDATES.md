# Slash Command Candidates

## Purpose

Track candidate slash commands that bind to protocol steps or named capabilities instead of raw scripts.

## Current Rule

- Slash commands should map to a capability or protocol step.
- Slash commands should expose small explicit inputs and predictable outputs.
- Tool-specific details stay behind the capability contract.

## Implemented Commands

| Slash Command | File | Primary Capability Or Protocol Step | Purpose |
|---------------|------|--------------------------------------|---------|
| `/packaging-snapshot` | `.github/prompts/packaging-snapshot.prompt.md` | `repo.packaging.snapshot` | summarize the current staged packaging state for branch or commit planning |
| `/intent-contract` | `.github/prompts/intent-contract.prompt.md` | `Intent Formulation` | draft or refresh the current Intent Contract for a bounded task thread |
| `/intent-review` | `.github/prompts/intent-review.prompt.md` | `Intent Critic Review` | run the early critic pass over the current intent before implementation |
| `/task-create` | `.github/prompts/task-create.prompt.md` | `workflow.task.create` | create a task in the active task backend |
| `/task-resolve` | `.github/prompts/task-resolve.prompt.md` | `workflow.task.resolve` | resolve a task with an explicit canonical resolution |
| `/delegate-critic` | `.github/prompts/delegate-critic.prompt.md` | `workflow.agent.review` | run the critic workflow over the current slice |
| `/quality-review` | `.github/prompts/quality-review.prompt.md` | `workflow.codequality.review` | run a findings-first code-quality review with an explicit focus |
| `/dry-review` | `.github/prompts/dry-review.prompt.md` | `workflow.codequality.review` | run a findings-first code-quality review focused on DRY failures |
| `/duplication-review` | `.github/prompts/duplication-review.prompt.md` | `workflow.codequality.review` | run a findings-first code-quality review focused on repeated logic or structures |
| `/generalize-review` | `.github/prompts/generalize-review.prompt.md` | `workflow.codequality.review` | run a findings-first code-quality review focused on shared-abstraction opportunities |
| `/best-practice-review` | `.github/prompts/best-practice-review.prompt.md` | `workflow.codequality.review` | run a findings-first code-quality review focused on recurring best-practice failures |
| `/refactor-plan` | `.github/prompts/refactor-plan.prompt.md` | `workflow.codequality.refactor-plan` | turn accepted code-quality findings into a bounded refactor plan |
| `/test-report-review` | `.github/prompts/test-report-review.prompt.md` | `workflow.testreport.review` | review reports and artifacts without writing tickets |
| `/test-report-triage` | `.github/prompts/test-report-triage.prompt.md` | `workflow.testreport.triage` | classify report findings and route the next likely action without writing tickets |
| `/test-execute` | `.github/prompts/test-execute.prompt.md` | `workflow.testexecution.run` | execute specified automated test code on the active backend |

## Candidate Commands

| Candidate Command | Primary Capability Or Protocol Step | Purpose |
|-------------------|--------------------------------------|---------|
| `/packaging-classify` | `repo.packaging.classify-staged-files` | show current packaging buckets for staged files |
| `/packaging-files <target>` | `repo.packaging.branch-file-list` | list files for a packaging target such as `maintenance` or `cluster` |
| `/learning-check` | Learning Loop | ask what was learned in recent work and whether it should affect guidance or memory |

## Task Operation Candidates

| Candidate Command | Primary Capability Or Protocol Step | Purpose |
|-------------------|--------------------------------------|---------|
| `/task-update <id>` | `workflow.task.update` | update task status, scope, notes, or metadata |
| `/task-assign <id> <assignee>` | `workflow.task.assign` | delegate or assign a task to a human, role, or agent |
| `/task-delete <id>` | `workflow.task.delete` | permanently remove a task from the active backend |

## Test-Case Management Candidates

| Candidate Command | Primary Capability Or Protocol Step | Purpose |
|-------------------|--------------------------------------|---------|
| `/testcase-create` | `workflow.testcase.create` | create a test case in the active test-case system |
| `/testcase-update <id>` | `workflow.testcase.update` | update test-case content, mapping, or lifecycle state |
| `/testcase-link <id>` | `workflow.testcase.link` | link a test case to intent, code, workflow, or execution artifacts |

## Test-Step Management Candidates

| Candidate Command | Primary Capability Or Protocol Step | Purpose |
|-------------------|--------------------------------------|---------|
| `/teststep-create <case-id>` | `workflow.teststep.create` | create a managed test step under a specific test case |
| `/teststep-update <step-id>` | `workflow.teststep.update` | update managed test-step content or ordering |
| `/teststep-delete <step-id>` | `workflow.teststep.delete` | permanently remove a managed test step |

## Test-Automation Candidates

| Candidate Command | Primary Capability Or Protocol Step | Purpose |
|-------------------|--------------------------------------|---------|
| `/testcode-plan` | `workflow.testcode.plan` | derive or refine automation design from intent, testcase, and teststep inputs |
| `/testcode-update` | `workflow.testcode.update` | create or modify automated test code in the repository |
| `/testcode-link` | `workflow.testcode.link` | connect automated test code to intent and test-management artifacts |

## Test-Execution Candidates

| Candidate Command | Primary Capability Or Protocol Step | Purpose |
|-------------------|--------------------------------------|---------|
| `/test-execute-remote <backend> <target>` | `workflow.testexecution.run` | run selected test code on a named remote execution backend such as Testkube |

## Test-Report Triage Candidates

| Candidate Command | Primary Capability Or Protocol Step | Purpose |
|-------------------|--------------------------------------|---------|
| `/test-report-ticket-draft` | `workflow.testreport.ticket-draft` | draft issue or ticket content from report-triage output when an issue backend is explicit |

## Agent Handoff Candidates

| Candidate Command | Primary Capability Or Protocol Step | Purpose |
|-------------------|--------------------------------------|---------|
| `/delegate-implementer` | `workflow.agent.delegate` | hand the current bounded slice to the Implementer role |
| `/delegate-teacher` | `workflow.agent.delegate` | ask Teacher to capture or teach reusable lessons |
| `/delegate-toolsmith` | `workflow.agent.delegate` | route capability or provider work to Toolsmith |

## Notes

- Both implemented and candidate command shapes live here.
- Commit Packager is the first strong pilot because it already has concrete provider scripts and bounded read-only behavior.
- `/intent-contract` is the manual-first bridge from user request to a bounded task thread and should stay implementation-agnostic.
- `/intent-review` completes the intent loop by forcing an early critic pass before broad implementation begins.
- Task, test-case, and agent-handoff commands should remain backend-agnostic at the command name level and resolve through capability contracts.
- Test-management commands and test-automation commands are intentionally separate families.
- `testcase` and `teststep` refer to management objects; `testcode` refers to automation implementation.
- `test-execute` is the execution-layer command and should not be confused with testcase or teststep management.
- Live command surfaces exist only where the backend or execution path is explicit enough to avoid accidental writes or opaque execution.
- The focused code-quality commands are thin wrappers over the same capability family; change the capability behavior once, then keep the prompt surfaces aligned.
- Issue-writing commands should stay candidate-only until the issue backend placeholder contract is filled.