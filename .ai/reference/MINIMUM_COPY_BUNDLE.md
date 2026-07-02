# Minimum Copy Bundle

## Purpose

Define the smallest credible scaffold subset another project can copy before adding project-specific roles, prompts, backends, or integrations.

## Copy This First

### Stable Runtime Layer

- `.github/copilot-instructions.md`
- `.github/instructions/core/evidence-first.instructions.md`
- `.github/instructions/workflows/planning.instructions.md`
- `.github/instructions/workflows/operation-protocol.instructions.md`
- `.github/instructions/workflows/task-files.instructions.md`
- `.github/instructions/workflows/stable-vs-mutable.instructions.md`
- `.github/instructions/tooling/capability-selection.instructions.md`
- `.github/instructions/memory/learning-loop.instructions.md`

### Mutable Project Layer

- `.ai/README.md`
- `.ai/COMMON.md`
- `.ai/tasks/README.md`
- `.ai/reference/OPERATION_PROTOCOL.md`
- `.ai/reference/INTENT_CONTRACT_TEMPLATE.md`
- `.ai/reference/FIRST_AGENT_BOOTSTRAP.md`
- `.ai/reference/CAPABILITIES.md`
- `.ai/reference/BACKEND_SELECTION.md`
- `.ai/reference/RESOLUTION_VOCABULARY.md`
- `.ai/reference/SECOND_EXPERT_THREAD_WALKTHROUGH.md`
- `.ai/reference/TRACEABILITY_MODEL.md`
- `.ai/reference/STARTER_TASK_EXAMPLE.md`

### Core Role Model

- `.ai/experts/README.md`
- `.ai/experts/architect-planner.md`
- `.ai/experts/implementer.md`
- `.ai/experts/general-critic.md`
- `.ai/experts/toolsmith.md`
- `.ai/experts/teacher.md`
- `.ai/experts/knowledge-curator.md`

## Add Next If Relevant

### Testing And Report Review

- `.ai/reference/TEST_REPORT_TRIAGE_TAXONOMY.md`
- `.ai/experts/test-report-reviewer.md`

### Manual-First Local Automation

- `.ai/reference/LOCAL_AUTOMATION_MANUAL_ENVIRONMENTS.md`

### Command Surfaces

- `.github/prompts/task-create.prompt.md`
- `.github/prompts/task-resolve.prompt.md`
- `.github/prompts/delegate-critic.prompt.md`
- `.github/prompts/intent-contract.prompt.md`
- `.github/prompts/intent-review.prompt.md`
- `.github/prompts/quality-review.prompt.md`
- `.github/prompts/dry-review.prompt.md`
- `.github/prompts/duplication-review.prompt.md`
- `.github/prompts/generalize-review.prompt.md`
- `.github/prompts/best-practice-review.prompt.md`
- `.github/prompts/refactor-plan.prompt.md`

### Packaging Example

- `.github/prompts/packaging-snapshot.prompt.md`
- `agents-tools/commit-packaging/`

## Do Not Copy Blindly

- project-specific scripts under `agents-tools/` unless the receiving project will use them
- prompts that assume a backend the target project has not selected
- any specialist overlay whose domain does not exist in the target project

## Success Criteria

- another project can create a task with an Intent Contract
- another project can bootstrap one manual-first agent before automating anything else
- another project can draft the first task intent and create a second expert or thread through explicit artifacts
- another project can reduce repetitive local work before enabling remote write integrations
- another project can run critic and quality review flows
- backend ambiguity is explicit, not hidden
- project-specific extensions can be added without rewriting the base scaffold