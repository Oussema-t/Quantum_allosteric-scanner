# Expert Role Briefs

Last Updated: 2026-06-25
Status: Seeded with core briefs and specialist overlays

This directory holds mutable briefs for specialized agent roles.

Phase 1 does not create runtime agents yet.
It defines the role model and the brief shape.

## Core Roles

- Architect/Planner
  - owns coordination, structure, escalation, and source-of-truth rules
- Explorer
  - performs focused read-only discovery and evidence gathering
- Implementer
  - applies small validated changes inside a bounded slice
- General Critic
  - reviews for defects, risks, regressions, and missing validation across code, docs, and plans
- Toolsmith
  - owns capability wrappers, provider choice, and interface contracts
- Teacher
  - turns completed work into reusable guidance, asks agents what they learned, and teaches the human in the loop
- Knowledge Curator
  - owns memory promotion, deduplication, and invariant hygiene

## Specialist Overlays

- Code Reviewer
  - code-focused critic for bugs, regressions, and missing validation
- Commit Packager
  - packaging-focused overlay for branch planning and split recommendations
- Test Report Reviewer
  - report-focused overlay for drift, bug, and failure-cause triage across test executions
- Skills Crafter
  - overlay under Toolsmith for authoring repo-local scripts and `.claude/skills/` Skills — Toolsmith picks the provider, Skills Crafter writes it

## Seeded Briefs

- `architect-planner.md`
  - first concrete root brief for scaffold coordination, sequencing, and boundary control
- `implementer.md`
  - concrete brief for bounded execution, local validation, and handoff discipline
- `toolsmith.md`
  - concrete brief for capability contracts, wrapper boundaries, and provider choice
- `teacher.md`
  - concrete brief for retrospective prompting, explanation quality, and human-loop learning
- `knowledge-curator.md`
  - concrete brief for promotion decisions, deduplication, and durable knowledge hygiene
- `general-critic.md`
  - concrete brief for evidence-first critique across implementations, docs, and plans
- `code-reviewer.md`
  - candidate overlay brief for code-local risk review and validation gaps
- `commit-packager.md`
  - candidate overlay brief for packaging analysis and split recommendations
- `test-report-reviewer.md`
  - candidate overlay brief for reading execution reports and isolating broken system areas
- `skills-crafter.md`
  - overlay brief for script/Skill authoring under Toolsmith, inferred from TASK-0025/TASK-0026 work — ratified 2026-07-04

## Role Model Notes

- Core roles own stable responsibility boundaries across the scaffold.
- Specialist overlays focus on recurring task shapes without redefining the core role model.
- General intent is handled by the operation protocol and Intent Contract, not by a standalone expert.
- BDD belongs to the intent layer; TDD and exact local checks are derived later by the execution layer.
- Test-management artifacts and automation-code artifacts are distinct workflow families.

## First Agent Pattern

- The first agent should usually be a composite bootstrap agent, not a large runtime swarm.
- Default first-agent mix: Architect/Planner plus Toolsmith plus Teacher plus General Critic.
- In no-workflow-automation environments, that first agent should operate through task files, reference docs, and prompt-led reviews rather than hidden external systems.
- Create specialist overlays or separate threads only after repeated demand becomes visible.

## Brief Template

Each future role brief should contain:

- status
- scope
- allowed inputs
- required outputs
- escalation rules
- current priorities
- linked tasks
- reference files
- memory touchpoints

## Current Rules

- Keep role descriptions mutable here.
- Keep stable runtime behavior in `.github/`.
- Keep broad role briefs stable and move live execution into `.ai/tasks/`.
- Move durable reusable facts into `.ai/memory/` or `.ai/reference/`.