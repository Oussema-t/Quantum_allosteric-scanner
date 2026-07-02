# First Agent Bootstrap

## Purpose

Explain how to build the first useful agent from instructions and capabilities before any workflow automation, remote orchestration, or ticketing backend is allowed.

The default assumption here is the highest-intensity human-in-the-loop mode:

- no workflow automation
- no hidden external writes
- no automatic ticket creation
- no automatic agent spawning outside explicit human direction

## Target Outcome

The first agent should help the human in the loop:

- create and maintain task threads
- choose or refine role briefs
- decide when a new expert or overlay is warranted
- keep capabilities and backends explicit
- review current work for defects, drift, and missing validation
- teach the human how the scaffold grows without hiding the mechanics

## Default Agent Shape

Start with one composite bootstrap agent.

It should behave as a bounded combination of:

- Architect/Planner for sequencing, ownership boundaries, and source-of-truth control
- Toolsmith for capability choice, backend gating, and provider hygiene
- Teacher for high-HITL explanation, handoff clarity, and gradual scaffold adoption
- General Critic for evidence-first review and validation-gap detection

Do not start by creating many agents.

Create specialist overlays or separate threads only after repeated need is visible.

## Build Inputs

### Stable Instructions To Load

- `.github/copilot-instructions.md`
- `.github/instructions/core/evidence-first.instructions.md`
- `.github/instructions/workflows/operation-protocol.instructions.md`
- `.github/instructions/workflows/task-files.instructions.md`
- `.github/instructions/workflows/planning.instructions.md`
- `.github/instructions/tooling/capability-selection.instructions.md`
- `.github/instructions/memory/learning-loop.instructions.md`

### Mutable References To Load

- `.ai/COMMON.md`
- `.ai/reference/CAPABILITIES.md`
- `.ai/reference/BACKEND_SELECTION.md`
- `.ai/reference/FIRST_AGENT_BOOTSTRAP.md`
- `.ai/reference/INTENT_CONTRACT_TEMPLATE.md`
- `.ai/reference/LOCAL_AUTOMATION_MANUAL_ENVIRONMENTS.md`
- `.ai/reference/OPERATION_PROTOCOL.md`
- `.ai/reference/SECOND_EXPERT_THREAD_WALKTHROUGH.md`
- `.ai/reference/STARTER_TASK_EXAMPLE.md`
- `.ai/experts/README.md`

## Minimum Capability Set

| Capability | Why It Belongs In The First Agent | Safe Default |
|------------|-----------------------------------|--------------|
| `workflow.task.create` | create the next bounded thread in the active task backend | on-disk task files |
| `workflow.task.resolve` | close the loop on finished work with explicit resolution | on-disk task files |
| `workflow.agent.review` | critique intent, task state, docs, and code slices | prompt-led review |
| `workflow.agent.delegate` | suggest or route work to the next role or overlay | manual orchestration only |
| `workflow.codequality.review` | review duplication, weak abstraction, and repeatable quality gaps | prompt-led review |

Add more only after the project names the backend and the safety model.

## Manual-First Operating Mode

In no-automation environments, the first agent should:

- create or update `.ai/tasks/TASK-*.md` files instead of opening external work items
- recommend the next expert or thread instead of assuming runtime agent creation
- keep unresolved test-case, test-step, and ticket backends explicit
- treat slash commands as prompt surfaces over named capabilities, not as hidden scripts
- ask the human to approve risky scope changes, backend activation, or write-oriented expansion

## Local Automation Stance

When the environment is heavily manual, the next safe step is local automation rather than remote integration.

Prefer helpers that:

- produce local files, previews, or read-only output
- package evidence for the HITL
- wrap local validation commands reproducibly
- keep remote writes and destructive actions disabled by default

See [LOCAL_AUTOMATION_MANUAL_ENVIRONMENTS](./LOCAL_AUTOMATION_MANUAL_ENVIRONMENTS.md).

## First Live Slash Commands

Start with the safe read-only or low-risk surfaces:

- `/intent-contract`
- `/intent-review`
- `/task-create`
- `/task-resolve`
- `/delegate-critic`
- `/quality-review`
- `/dry-review`
- `/duplication-review`
- `/generalize-review`
- `/best-practice-review`
- `/refactor-plan`

Avoid live testcase, teststep, ticket, or remote-execution commands until their backends are explicit.

## Thread Creation Rule

Create a new task thread when:

- the outcome is coherent and needs multi-step execution
- a separate role or review cycle is needed
- evidence, blockers, or dependencies would otherwise bloat a broad overview doc

Create a new expert or overlay only when:

- the same task shape repeats
- the responsibility boundary is stable
- the capability or review behavior is reusable across tasks

## Suggested First Sequence

1. Copy the minimum scaffold bundle.
2. Set backend defaults in `.ai/reference/BACKEND_SELECTION.md`.
3. Use `/intent-contract` to draft the first bounded Intent Contract.
4. Use `/intent-review` to complete the early critic pass over that intent.
5. Create the first bootstrap task with the reviewed intent.
6. Expose only the safe slash commands listed above.
7. Let the first agent help the human create the next role brief, task thread, or review slice.
8. Use [SECOND_EXPERT_THREAD_WALKTHROUGH](./SECOND_EXPERT_THREAD_WALKTHROUGH.md) when the first reusable handoff boundary appears.
9. Promote new experts, prompts, or backend adapters only after repeated evidence.

## Exit Criteria

The first agent is good enough when it can help the human in the loop:

- start a new bounded task correctly
- choose the next review or implementation role
- explain which capability or instruction governs the action
- keep backend assumptions explicit
- grow the scaffold without requiring workflow automation first