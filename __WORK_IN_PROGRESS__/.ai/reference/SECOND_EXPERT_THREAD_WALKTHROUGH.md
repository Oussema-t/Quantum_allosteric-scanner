# Second Expert Or Thread Walkthrough

## Purpose

Show exactly how the first composite bootstrap agent should help the human in the loop create a second expert or task thread without hidden automation.

This walkthrough is manual-first.

It uses explicit artifacts, explicit role boundaries, and explicit handoff points.

## Example Trigger

The first agent has already helped create a bounded task.

During review, the work shows a repeated need for packaging-specific analysis that should not stay mixed into the broad bootstrap thread.

The human wants a second expert or thread.

## Handoff Decision Rule

Create a second task thread when:

- the new outcome is coherent and multi-step
- evidence, blockers, or dependencies would clutter the current task
- a separate validation or review cycle is needed

Create a second expert or overlay when:

- the same work shape repeats
- the responsibility boundary is stable
- the review or execution behavior is reusable across tasks

## Exact Artifact Chain

1. `Intent Formulation`
   - prompt surface: `/intent-contract`
   - artifact: `Intent Contract`
   - location: current chat output or a new task draft

2. `Intent Critic Review`
   - prompt surface: `/intent-review`
   - artifact: `Intent Review`
   - location: current chat output, task notes, or review record

3. `Task Thread Creation`
   - prompt surface: `/task-create`
   - artifact: new task file
   - location: `.ai/tasks/TASK-xxxx-<slug>.md`

4. `Role Boundary Decision`
   - owner: first composite bootstrap agent acting as Architect/Planner
   - artifact: explicit decision recorded in the task `TODO` or `Open Questions`
   - question answered: is a new thread enough, or is a reusable expert overlay also warranted?

5. `Expert Brief Selection Or Creation`
   - if an existing overlay fits, reuse it
   - if no overlay fits and the pattern is recurring, create or refine a brief under `.ai/experts/`
   - artifact: expert brief or explicit reuse decision

6. `Capability Binding`
   - owner: first composite bootstrap agent acting as Toolsmith
   - artifact: capability choice and backend note
   - location: task evidence, prompt surface, or capability catalog if the behavior becomes durable

7. `Execution Handoff`
   - owner: first composite bootstrap agent acting as Architect/Planner or Teacher
   - artifact: bounded next slice for the new thread or expert
   - location: new task file `Intent Contract`, `TODO`, and `Dependency` sections

8. `Critic Check`
   - prompt surface: `/delegate-critic`
   - artifact: review record
   - purpose: confirm the new thread or expert boundary is justified and not premature

## Concrete Walkthrough

### Step 1: First Agent Detects Repeated Need

- current task: scaffold bootstrap
- observed pattern: packaging analysis needs a recurring specialist lens
- decision: reuse or refine `commit-packager.md` instead of keeping the concern implicit in the broad bootstrap task

### Step 2: First Agent Drafts The New Intent

Use `/intent-contract` to draft a bounded intent such as:

- Outcome:
  - define a packaging-focused review slice that can classify staged files and recommend safe commit splits
- In Scope:
  - packaging analysis behavior
  - prompt surface and capability references
- Out Of Scope:
  - unrelated scaffold redesign
  - write-oriented git automation

### Step 3: First Agent Creates The New Thread

Use `/task-create` to create a task such as:

- `.ai/tasks/TASK-0101-commit-packager-overlay.md`

That task should include:

- `Context`
- `Intent Contract`
- `In Progress`
- `TODO`
- `Dependency`
- `Open Questions`
- `Done`

### Step 4: First Agent Chooses The Expert Boundary

- if `commit-packager.md` already fits, link it from the task
- if the brief is too broad or missing, update or create the expert brief before broad execution starts

Artifact chain here:

- task file references the expert brief
- expert brief references the task when the work is active

### Step 5: First Agent Hands Off The Slice

The first agent should hand off a bounded slice such as:

- review current packaging scripts
- confirm capability names and provider boundaries
- expose one safe prompt surface
- validate with evidence-first output only

### Step 6: Critic Verifies The Split

Use `/delegate-critic` to ask:

- is this really a reusable expert shape?
- is the thread bounded enough?
- did the handoff preserve explicit capability and backend assumptions?

## Minimal File Chain Example

- first guidance: `.ai/reference/FIRST_AGENT_BOOTSTRAP.md`
- new intent draft: `/intent-contract` output
- new task file: `.ai/tasks/TASK-0101-commit-packager-overlay.md`
- expert brief: `.ai/experts/commit-packager.md`
- command or capability references if promoted:
  - `.github/prompts/packaging-snapshot.prompt.md`
  - `.ai/reference/CAPABILITIES.md`
  - `.ai/reference/SLASH_COMMAND_CANDIDATES.md`

## Current Rule

- The first agent should create the second thread from intent first, then intent review, then task file, then expert reuse or creation, then bounded handoff.
- Do not create a new expert only because a task is new.
- Do not hide the handoff inside raw prose when an artifact can hold it explicitly.