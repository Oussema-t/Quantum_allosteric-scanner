# Local Automation In Heavily Manual Environments

## Purpose

Define safe ways to introduce local automation when a customer restricts workflow automation, remote orchestration, or external write integrations.

The goal is to reduce repetitive manual work without hiding control flow, approvals, or side effects from the human in the loop.

## Safe Default

In heavily manual environments, prefer automation that:

- runs locally
- emits local artifacts or previews
- keeps external writes disabled by default
- requires explicit human approval before destructive or remote actions
- stays understandable from capabilities, prompts, and local files

## What Local Automation Should Optimize First

### 1. Artifact Scaffolding

Automate the creation of:

- Intent Contract drafts
- task file skeletons
- review artifact skeletons
- expert-brief skeletons

These reduce repeated formatting work while preserving human control over meaning.

### 2. Evidence Packaging

Automate bounded local collection of:

- diff summaries
- staged file lists
- focused validation outputs
- report excerpts
- task-linked evidence bundles

These help the HITL review the current slice without opening many unrelated surfaces.

### 3. Dry-Run Drafting

Automate draft generation for:

- ticket or issue markdown
- testcase drafts
- step drafts
- handoff notes for a second expert or thread

In manual-first mode, these should stay local artifacts until the backend contract is explicit.

### 4. Local Validation Wrappers

Automate safe local checks such as:

- targeted tests
- narrow lint or type checks
- preflight environment checks
- reproducible local execution commands

These should produce deterministic local output and avoid remote mutation.

### 5. Approval-Gated Local Helpers

Automate repetitive but sensitive local steps only when:

- inputs are explicit
- outputs are reviewable
- the human approves the final action

Examples:

- generating a final task-resolution block before applying it
- assembling a remote-execution command without running it yet
- building a candidate issue payload without sending it

## Good First Local-Automation Targets

| Target | Why It Fits Manual-First Mode | Safe Output |
|--------|-------------------------------|-------------|
| intent and task scaffolding | repetitive structure, low risk | markdown sections or files |
| code-quality evidence bundling | read-only and bounded | findings summary or review artifact |
| report triage packaging | read-only classification | local review note or draft route |
| local validation runners | explicit and reproducible | command output or reviewable logs |
| handoff packet generation | helps the next expert or thread | local markdown or checklist |

## Poor Early Targets

Avoid early automation for:

- external ticket creation
- automatic testcase or teststep writes to remote systems
- hidden remote execution
- automatic agent spawning without explicit human intent
- destructive infrastructure or cluster mutations

## Activation Ladder

Use this escalation ladder:

1. prompt-only guidance
2. prompt plus local artifact output
3. repo-local wrapper that produces local artifacts or read-only output
4. repo-local wrapper with explicit human approval before a sensitive local action
5. backend adapter only after the backend contract is explicit and safe

Do not jump from prompt-only guidance to remote writes unless the backend, safety model, and approval gate are already defined.

## Relationship To Capability Design

For heavily manual environments:

- keep capability names stable
- prefer repo-local wrappers before backend adapters
- make local outputs explicit in the capability contract
- keep write-oriented families gated until the target backend is explicit

## Current Rule

- Local automation is the preferred intermediate step between fully manual work and backend-integrated automation.
- If the customer is highly restrictive, optimize for local artifacts, local validation, and approval-gated helpers before adding any remote write path.