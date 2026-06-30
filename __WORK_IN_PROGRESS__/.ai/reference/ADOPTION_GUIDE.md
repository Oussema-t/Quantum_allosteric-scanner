# Adoption Guide

## Purpose

Explain how another project should adopt this scaffold without inheriting repository-specific assumptions.

## Target Outcome

A new project should be able to:

- separate stable runtime policy from mutable project state
- document non-trivial work with an Intent Contract
- bootstrap a first manual-first agent that helps the HITL create later roles, prompts, and task threads
- define role boundaries before complex agent orchestration grows
- model capabilities before binding to tools or ticketing systems
- add live slash-command surfaces only where backends are explicit enough

## Recommended Adoption Sequence

1. Copy the minimum bundle from [MINIMUM_COPY_BUNDLE](./MINIMUM_COPY_BUNDLE.md).
2. Update project names, paths, and any repo-local assumptions.
3. Set the active backend defaults in [BACKEND_SELECTION](./BACKEND_SELECTION.md).
4. Keep unresolved backends explicit instead of guessing them.
5. Build the first manual-first agent using [FIRST_AGENT_BOOTSTRAP](./FIRST_AGENT_BOOTSTRAP.md).
6. Use `/intent-contract` or the intent template to draft the first bounded task intent.
7. Use `/intent-review` to run the early critic pass over that intent.
8. Create the first non-trivial task using [STARTER_TASK_EXAMPLE](./STARTER_TASK_EXAMPLE.md) as a model.
9. Use [SECOND_EXPERT_THREAD_WALKTHROUGH](./SECOND_EXPERT_THREAD_WALKTHROUGH.md) when the first reusable handoff boundary appears.
10. Add one live slash-command prompt only after its capability and backend are clear.

## Minimum Viable Setup

At minimum, the adopting project should have:

- stable `.github/instructions/**` workflow rules
- mutable `.ai/` hub, task, and reference surfaces
- a first-agent bootstrap guide or equivalent composite-agent contract
- an Intent Contract template
- a capability catalog
- a backend selection reference
- the core role briefs

## Manual-First Customer Mode

If the customer forbids workflow automation or limits external integrations:

- keep task flow on disk first
- keep review and delegation prompt-led
- keep write-oriented backend families unresolved until approved
- let the first agent teach the human how later experts or threads should be created
- let the first agent use explicit intent and task artifacts before creating a second expert or thread

## First Things To Customize

- backend defaults for task, test, execution, and ticket flows
- specialist overlays that are relevant to the project domain
- any live prompts that assume repository-specific tools
- project-specific capability providers and scripts

## Good Early Moves

- keep only one active backend per object family at first
- start with read-only or low-risk commands
- use the critic and quality-review prompts before adding more command surfaces
- add ticketing or remote execution only after the adapter contract is explicit

## Common Adoption Mistakes

- copying every prompt before choosing backends
- treating candidate commands as live behaviors
- mixing test-management objects with automation code concepts
- letting tasks skip the Intent Contract because the work feels familiar
- hiding unresolved backend choices inside prompts or scripts

## When The Scaffold Is Ready For More

Add more only after the project can already:

- create and resolve tasks consistently
- run critic or quality review against a bounded slice
- preserve traceability from intent to execution evidence
- explain what backend each live command actually uses