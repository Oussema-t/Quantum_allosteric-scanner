# TASK-0001 Agent Scaffold Bootstrap

## Context

- ID: TASK-0001
- Title: Bootstrap repo-local agent scaffold under `.github` + `.ai`
- Status: In Progress
- Owner: Architect/Planner
- Scope: Phase 2 through Phase 5 scaffold refinement, including intent-first workflow and capability pilot shaping

## Intent Contract

- Outcome:
  - establish a reusable repo-local scaffold with explicit intent-first workflow, role boundaries, capability contracts, and slash-command-ready surfaces
- In Scope:
  - root scaffold docs and instructions
  - expert and overlay role briefs
  - capability and slash-command taxonomy
  - task-file workflow rules
- Out Of Scope:
  - broad migration of existing module-local `.claude` guidance
  - full MCP implementation
  - live external ticketing or test-management backend integrations
- Acceptance Scenarios:
  - Given a non-trivial task, when it is documented in `.ai/tasks/`, then it includes an Intent Contract before exact implementation detail.
  - Given a candidate slash command, when it affects tasks, tests, or agent handoff, then it maps to a named capability rather than raw tool prose.
  - Given a report-reading problem, when triage is needed, then a specialist overlay exists to classify drift, bugs, automation defects, and unknowns.
- Constraints And Invariants:
  - keep `.github/` stable and `.ai/` mutable
  - keep capabilities backend-agnostic where possible
  - separate test-management objects from automation-code objects
- Planned Validation:
  - validate scaffold files for errors after each edit burst
  - inspect source-of-truth consistency after protocol or capability changes

## In Progress

- Root scaffold files exist.
- The current slice is documenting the local-automation path for heavily manual environments.

## TODO

### Phase 1: Structure Bootstrap
- Objective: Create the minimal root scaffold without rewriting existing domain docs.
- Actions:
  - create `.github/` runtime policy entry point
  - create `.ai/` hub, reference, task, tools, reviews, and memory folders
  - document additive coexistence with existing `.claude`
- Evidence:
  - `.github/copilot-instructions.md`
  - `.ai/README.md`
  - `.ai/COMMON.md`
  - `.ai/ARCHITECTURE_OVERVIEW.md`
- Exit Criteria:
  - root scaffold exists and has a clear source-of-truth map

### Phase 2: Stable Policy Seed
- Objective: Define the first repo-local stable rules for mutable docs, task files, memory promotion, and capability catalogs.
- Actions:
  - add `.github/instructions/**` policies
  - keep descriptions concrete for discovery
  - scope file instructions narrowly with `applyTo`
  - add an intent-first operation protocol rule for non-trivial task flow
- Evidence:
  - `.github/instructions/core/evidence-first.instructions.md`
  - `.github/instructions/workflows/planning.instructions.md`
  - `.github/instructions/workflows/operation-protocol.instructions.md`
  - `.github/instructions/workflows/stable-vs-mutable.instructions.md`
  - `.github/instructions/workflows/task-files.instructions.md`
  - `.github/instructions/memory/learning-loop.instructions.md`
  - `.github/instructions/tooling/capability-selection.instructions.md`
- Exit Criteria:
  - stable policy exists without active task state or temporary incidents

### Phase 3: Role Brief Templates
- Objective: Define the reusable expert-role model without creating all runtime agents yet.
- Actions:
  - seed `.ai/experts/README.md`
  - define role taxonomy and brief template
  - add the first concrete root brief for `Architect/Planner`
  - add concrete root briefs for `Implementer` and `Toolsmith`
  - define `Teacher` as the human-loop and agent-learning role, including retrospective prompting
  - add concrete root briefs for `Knowledge Curator` and `General Critic`
  - seed specialist overlays for `Code Reviewer`, `Commit Packager`, and `Test Report Reviewer`
- Evidence:
  - `.ai/experts/README.md`
  - `.ai/experts/architect-planner.md`
  - `.ai/experts/implementer.md`
  - `.ai/experts/toolsmith.md`
  - `.ai/experts/teacher.md`
  - `.ai/experts/knowledge-curator.md`
  - `.ai/experts/general-critic.md`
  - `.ai/experts/code-reviewer.md`
  - `.ai/experts/commit-packager.md`
  - `.ai/experts/test-report-reviewer.md`
- Exit Criteria:
  - specialist roles are documented as mutable briefs

### Phase 4: Capability Wrapping Plan
- Objective: Catalog current local tool providers and generalization gaps.
- Actions:
  - seed `.ai/reference/CAPABILITIES.md`
  - reserve `.ai/tools/` for wrappers and future implementations
  - map existing `agents-tools` assets to capability names
  - flag dry-run, output, and config gaps
  - add explicit `repo.vcs.*` primitives for Commit Packager
  - align capability shapes with future slash commands
  - implement the first real Commit Packager prompt surface
  - separate `testcase`, `teststep`, `testcode`, and `testreport` capability families
  - split task resolution from permanent task deletion
  - add explicit traceability, resolution vocabulary, and backend adapter references
  - implement safe prompt surfaces for task create, task resolve, critic delegation, test report review, and test execution
  - implement safe prompt surface for test report triage
  - seed the DRY or generalization code-quality review command family
  - promote `/quality-review` to a live prompt surface
  - add adoption guide and minimum-copy bundle
  - add an explicit issue-backend placeholder contract
  - add a starter task example that shows intent through learning
  - add a first-agent bootstrap guide for manual-first adoption
  - promote the focused code-quality commands and refactor plan to live prompt surfaces
  - promote `/intent-contract` to a live prompt surface
  - add a walkthrough for creating a second expert or thread from the first agent
  - promote `/intent-review` to a live prompt surface
  - document safe local-automation patterns for heavily manual environments
- Evidence:
  - `.ai/reference/CAPABILITIES.md`
  - `.ai/reference/SLASH_COMMAND_CANDIDATES.md`
  - `.ai/reference/BACKEND_SELECTION.md`
  - `.ai/reference/TRACEABILITY_MODEL.md`
  - `.ai/reference/RESOLUTION_VOCABULARY.md`
  - `.ai/reference/TEST_REPORT_TRIAGE_TAXONOMY.md`
  - `.ai/reference/ADOPTION_GUIDE.md`
  - `.ai/reference/FIRST_AGENT_BOOTSTRAP.md`
  - `.ai/reference/LOCAL_AUTOMATION_MANUAL_ENVIRONMENTS.md`
  - `.ai/reference/SECOND_EXPERT_THREAD_WALKTHROUGH.md`
  - `.ai/reference/MINIMUM_COPY_BUNDLE.md`
  - `.ai/reference/ISSUE_BACKEND_PLACEHOLDER_CONTRACT.md`
  - `.ai/reference/STARTER_TASK_EXAMPLE.md`
  - `.github/prompts/packaging-snapshot.prompt.md`
  - `.github/prompts/intent-contract.prompt.md`
  - `.github/prompts/intent-review.prompt.md`
  - `.github/prompts/task-create.prompt.md`
  - `.github/prompts/task-resolve.prompt.md`
  - `.github/prompts/delegate-critic.prompt.md`
  - `.github/prompts/quality-review.prompt.md`
  - `.github/prompts/dry-review.prompt.md`
  - `.github/prompts/duplication-review.prompt.md`
  - `.github/prompts/generalize-review.prompt.md`
  - `.github/prompts/best-practice-review.prompt.md`
  - `.github/prompts/refactor-plan.prompt.md`
  - `.github/prompts/test-report-review.prompt.md`
  - `.github/prompts/test-report-triage.prompt.md`
  - `.github/prompts/test-execute.prompt.md`
  - `.ai/tools/README.md`
- Exit Criteria:
  - each current provider has a named capability entry

### Phase 5: Pilot Planning
- Objective: Choose the first validation slice for the scaffold.
- Actions:
  - keep `commit-packaging` as the default first pilot
  - defer UI-domain pilot until after scaffold basics are stable
  - define the intent-first workflow as the default path for non-trivial work
  - add a verification debugging sub-loop inside the protocol
  - make Intent Contract mandatory in task files
  - rate current scaffold ripeness and record the rationale in a review artifact
- Evidence:
  - `.ai/reference/OPERATION_PROTOCOL.md`
  - `.ai/reference/INTENT_CONTRACT_TEMPLATE.md`
  - `.github/prompts/packaging-snapshot.prompt.md`
  - `.ai/reviews/REVIEW-2026-06-25-scaffold-ripeness.md`
  - task updates in this file
- Exit Criteria:
  - next implementation slice is unambiguous

## Dependency

- Existing domain documentation in `FIX_HERE/.claude/` remains authoritative until migration work is scoped explicitly.
- Future MCP adoption depends on a stable capability catalog first.

## Open Questions

- Should `.ai` remain the final mutable-layer name, or should it be renamed after the first pilot?
- When Phase 3 starts, should runtime agents live under `.github/agents/` or remain documentation-first until wrappers exist?

## Done

- Repo-local scope selected instead of user-level customization.
- Deliverable shape selected as reusable scaffold/template, not full migration.
- Root scaffold model chosen: `.github` for stable runtime policy, `.ai` for mutable project state.
- Initial root scaffold files created.
- Earlier overlapping scaffold duplication was cleaned into one canonical layout.
- Ripeness assessed at `88/100` for manual-first adoption on 2026-06-25; rationale recorded in `.ai/reviews/REVIEW-2026-06-25-scaffold-ripeness.md`.