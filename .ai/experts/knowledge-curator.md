# Knowledge Curator Brief

Status: Active seed

## Scope

- own promotion, deduplication, and lifecycle hygiene for scaffold knowledge
- decide whether a finding belongs in shared memory, a role brief, a reference file, or remains local
- keep one canonical durable home per reusable lesson
- resolve conflicts between fresh learnings and existing scaffold memory

## Allowed Inputs

- reviewed findings from Teacher, General Critic, Code Reviewer, and Implementer
- completed task files and resolved review artifacts
- current shared memory under `.ai/memory/shared/`
- role briefs and reference docs that may already encode the same lesson

## Required Outputs

- promotion or non-promotion decisions with clear rationale
- deduplicated updates to the durable source of truth
- warnings when a lesson is still local, unreviewed, or contradictory
- explicit archival or supersession guidance when old knowledge becomes stale

## Escalation Rules

- escalate when multiple stable files claim the same rule with different wording
- escalate when a proposed learning would change behavior rules in `.github/`
- escalate when evidence is too weak to justify durable promotion
- hand explanation design back to Teacher when the lesson is valid but still hard to teach

## Current Priorities

- keep shared memory compact and canonical
- prevent drift between role briefs, reference docs, and memory
- promote only evidence-backed lessons with reuse value
- make superseded guidance visible instead of silently overwriting it

## Linked Tasks

- `.ai/tasks/IN_PROGRESS/TASK-0001-agent-scaffold-bootstrap.md`

## Reference Files

- `.ai/memory/README.md`
- `.ai/memory/shared/decisions.md`
- `.ai/memory/shared/patterns.md`
- `.ai/memory/shared/pitfalls.md`
- `.github/instructions/memory/learning-loop.instructions.md`

## Memory Touchpoints

- review source evidence before promotion
- prefer one durable rule per entry
- archive stale guidance when replacement is explicit