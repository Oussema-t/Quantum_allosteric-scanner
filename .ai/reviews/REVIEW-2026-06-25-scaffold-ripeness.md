# Scaffold Ripeness Review

## Linked Task

- `.ai/tasks/IN_PROGRESS/TASK-0001-agent-scaffold-bootstrap.md`

## Scope

- repo-local agent scaffold under `.github/` and `.ai/`
- manual-first adoption path
- live prompt surfaces, capability catalog, backend gating, and handoff artifacts

## Ripeness Score

- `88/100`

## Rating Rationale

- The scaffold now has a full manual-first intent loop with live `/intent-contract` and `/intent-review` surfaces before implementation starts.
- The first agent bootstrap path is explicit and can help a human create subsequent tasks, reviews, and expert handoffs without hidden automation.
- Task creation and resolution, critic review, the code-quality review family, report review, report triage, and local test execution all have named prompt surfaces.
- Capability contracts, backend-selection rules, traceability, resolution vocabulary, and issue-backend gating are explicit rather than hidden in scripts.
- The score stops short of production-complete maturity because several write-oriented or multi-system families remain intentionally unresolved.

## Findings

### P1

- Testcase, teststep, and issue-escalation backends remain unresolved by design.
- Evidence:
  - `.ai/reference/BACKEND_SELECTION.md`
  - `.ai/reference/ISSUE_BACKEND_PLACEHOLDER_CONTRACT.md`
- Impact:
  - The scaffold is strong for manual-first adoption, but not yet complete for backend-integrated task, test-management, or ticket-write workflows.

### P1

- Agent delegation beyond critic remains more documented than operational.
- Evidence:
  - `.ai/reference/SLASH_COMMAND_CANDIDATES.md`
  - `.ai/reference/SECOND_EXPERT_THREAD_WALKTHROUGH.md`
- Impact:
  - The handoff model is clear, but some delegate surfaces such as implementer or toolsmith are not live prompt commands yet.

### P2

- Remote execution backends are still gated behind explicit naming and are not first-class live defaults.
- Evidence:
  - `.ai/reference/BACKEND_SELECTION.md`
  - `.ai/reference/CAPABILITIES.md`
  - `.github/prompts/test-execute.prompt.md`
- Impact:
  - The execution model is safe and explicit, but not yet broad enough for projects that need immediate remote orchestration.

### P2

- The scaffold is now coherent enough for reuse, but its strongest mode is still manual-first rather than automation-first.
- Evidence:
  - `.ai/reference/FIRST_AGENT_BOOTSTRAP.md`
  - `.ai/reference/ADOPTION_GUIDE.md`
  - `.ai/reference/MINIMUM_COPY_BUNDLE.md`
- Impact:
  - This is a high-confidence reusable scaffold for guided adoption, but not yet a turnkey automation framework.

## Open Questions

- Which delegate surface should become live first after critic: implementer or toolsmith?
- Which backend family should be the first post-bootstrap write integration: task, testcase, or issue escalation?

## Recommended Next

- Promote `/delegate-implementer` or `/delegate-toolsmith` next so the documented second-thread handoff has one more live operational surface.
- Keep issue, testcase, and teststep families gated until the backend contracts are explicit enough to avoid accidental writes.