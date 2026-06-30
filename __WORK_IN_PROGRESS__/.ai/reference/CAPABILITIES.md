# Capability Catalog

This file tracks reusable capabilities independently of the provider that implements them.

Capabilities should be slash-command-friendly when they are likely to become user-facing entry points.
That means small explicit inputs, bounded scope, predictable output, and no hidden script assumptions.

Provider order:

1. MCP or tool server
2. repo-local script or wrapper
3. manual fallback

## Commit Packager Capability Set

| Capability | Purpose | Current Provider | Scope | Safety | Notes |
|------------|---------|------------------|-------|--------|-------|
| `repo.vcs.current-branch` | Read the current branch name | `git rev-parse --abbrev-ref HEAD` | generic | read-only | Good primitive capability for packaging and future slash commands. |
| `repo.vcs.short-status` | Read short working-tree status | `git status --short` | generic | read-only | Current packaging snapshot uses this as context even though the commit-packaging decision is staged-focused. |
| `repo.vcs.staged-diff-stat` | Summarize staged diff size | `git diff --cached --stat` | generic | read-only | Useful bounded summary for branch and commit planning. |
| `repo.vcs.staged-files` | List staged file paths | `git diff --cached --name-only` | generic | read-only | Baseline input for classification and split logic. |
| `repo.packaging.classify-staged-files` | Bucket staged files into packaging groups | `agents-tools/commit-packaging/classify-staged-files.sh` | reusable with config extraction | read-only | Current rules are repo-specific and should become config before broader reuse. |
| `repo.packaging.snapshot` | Summarize staged change packaging state for branch planning | `agents-tools/commit-packaging/packaging-snapshot.sh` | reusable with wrapper | read-only | Composite capability over `repo.vcs.*` and packaging classification calls. |
| `repo.packaging.branch-file-list` | List staged files for a packaging target | `agents-tools/commit-packaging/list-branch-files.sh` | reusable with wrapper | read-only | Current targets are `maintenance` and `cluster`; these should become parameterized config. |

## Other Seeded Capabilities

| Capability | Purpose | Current Provider | Scope | Safety | Notes |
|------------|---------|------------------|-------|--------|-------|
| `workflow.task.create` | Create a task in the active task backend | manual fallback | generic with backend adapter | write | Backend may be on-disk task files, JIRA, or another HITL-selected system. |
| `workflow.task.update` | Update task status, content, or metadata in the active task backend | manual fallback | generic with backend adapter | write | Requires a stable task identifier and backend contract. |
| `workflow.task.assign` | Delegate or assign a task to a person, role, or agent | manual fallback | generic with backend adapter | write | Backend may support human assignees, role tags, or agent overlays differently. |
| `workflow.task.resolve` | Resolve a task with an explicit backend-relevant resolution value | manual fallback | generic with backend adapter | write | Distinct from deletion; backend adapters should map the resolution field correctly. |
| `workflow.task.delete` | Permanently delete a task from the active task backend | manual fallback | generic with backend adapter | destructive | Do not overload with close, archive, or resolve semantics. |
| `workflow.testcase.create` | Create a test case in the active test-case system | manual fallback | generic with backend adapter | write | Backend may be markdown, TestRail, Jira/Xray, or another HITL-selected system. |
| `workflow.testcase.update` | Update test-case content, mapping, or status | manual fallback | generic with backend adapter | write | Exact fields depend on the selected test-case backend. |
| `workflow.testcase.link` | Link a test case to code, intent, workflow, or execution artifacts | manual fallback | generic with backend adapter | write | Important for intent-to-test traceability. |
| `workflow.teststep.create` | Create a managed test step under a test case in the active test-management system | manual fallback | generic with backend adapter | write | Test steps are management artifacts, not automation code. |
| `workflow.teststep.update` | Update managed test-step content or ordering | manual fallback | generic with backend adapter | write | Exact step fields depend on the selected backend. |
| `workflow.teststep.delete` | Permanently delete a managed test step from the active test-management system | manual fallback | generic with backend adapter | destructive | Keep step deletion distinct from testcase lifecycle changes. |
| `workflow.testcode.plan` | Derive or refine automated test implementation from intent and test-management artifacts | prompt or agent orchestration | scaffold-specific | control-plane | Test code belongs to the automation layer, not the test-management backend. |
| `workflow.testcode.update` | Create or modify automated test code in the repository | prompt or agent orchestration | scaffold-specific | write | Distinct from testcase and teststep operations. |
| `workflow.testcode.link` | Link automated test code to intent, testcase, teststep, or execution artifacts | manual fallback | generic with backend adapter | write | Supports traceability across management and automation layers. |
| `workflow.testexecution.run` | Execute selected automated test code locally or on an explicit project-specific backend | `runTests` for local execution | scaffold-specific with backend adapter | environment-dependent | Local repository execution is the current default; remote backends such as Testkube must be named explicitly. |
| `workflow.testreport.review` | Review test reports to classify failures, drift, and broken system areas | prompt or agent orchestration | scaffold-specific | read-only | Natural fit for a specialist report-review overlay. |
| `workflow.testreport.triage` | Apply the report triage taxonomy and route likely next actions | prompt or agent orchestration | scaffold-specific | read-only | Structured subset of report review focused on classification and routing. |
| `workflow.testreport.ticket-draft` | Draft follow-up ticket content from report triage results | manual fallback | generic with backend adapter | write | Keep candidate-only until the issue backend is explicit and satisfies the issue-backend placeholder contract. |
| `workflow.codequality.review` | Review code for duplication, DRY failures, weak abstraction, and best-practice issues | prompt or agent orchestration | scaffold-specific | read-only | Prefer one review capability with explicit focus such as `dry`, `duplication`, `generalization`, or `best-practice` over many unrelated command implementations. |
| `workflow.codequality.refactor-plan` | Turn accepted code-quality findings into bounded refactor steps | prompt or agent orchestration | scaffold-specific | control-plane | Use after review, not as a substitute for a findings-first pass. |
| `workflow.agent.delegate` | Hand a slice to another agent role or overlay | prompt or agent orchestration | scaffold-specific | control-plane | Should route by role contract, not by ad hoc prose only. |
| `workflow.agent.review` | Invoke a review or critic pass by the appropriate role | prompt or agent orchestration | scaffold-specific | control-plane | Maps naturally to General Critic, Code Reviewer, or future specialized critics. |
| `ui.snapshot.selector-extraction` | Extract candidate selectors and labels from saved UI snapshots | `agents-tools/portal-snapshots/extract-object-storage-selectors.sh` | overlay-specific | read-only | Useful pattern, but current default paths are Portal-specific. |
| `cluster.prm.resourceproject.delete` | Delete PRM `ResourceProject` objects with pre-delete annotation flow | `agents-tools/delete-resource-projects.mjs` | project-specific | destructive | Keep as overlay provider until it supports generic targeting, dry-run, and safer contracts. |

## Slash Command Fit

- Candidate command shapes live in `.ai/reference/SLASH_COMMAND_CANDIDATES.md`.
- Slash commands should bind to capabilities such as `repo.packaging.snapshot`, not to raw script paths.
- Primitive `repo.vcs.*` capabilities keep Commit Packager decoupled from direct git-specific reasoning.
- Implemented prompt surfaces currently include packaging, intent formulation and intent review, task creation and resolution, critic delegation, the code-quality review family, refactor planning, test report review and triage, and test execution.
- Task operations, test-case management, and agent handoff should also bind to named workflow capabilities before backend-specific implementations are chosen.
- Current backend resolution lives in `.ai/reference/BACKEND_SELECTION.md`.
- Issue escalation requirements live in `.ai/reference/ISSUE_BACKEND_PLACEHOLDER_CONTRACT.md`.
- End-to-end linking expectations live in `.ai/reference/TRACEABILITY_MODEL.md`.
- Canonical lifecycle and resolution meanings live in `.ai/reference/RESOLUTION_VOCABULARY.md`.
- Report triage classes live in `.ai/reference/TEST_REPORT_TRIAGE_TAXONOMY.md`.

## Provider Contract Template

For each new capability, document:

- capability name
- purpose
- provider order
- current provider
- environment contract
- output format
- safety constraints
- generalization status
- slash-command fit