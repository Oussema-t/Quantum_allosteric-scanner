# Commit Packager Brief

Status: Candidate overlay

## Scope

- summarize staged or changed work into packaging targets for branch or commit planning
- use capability outputs to group files, detect mixed concerns, and propose cleaner split points
- rely on `repo.vcs.*` and `repo.packaging.*` capabilities instead of owning raw git calls directly
- keep packaging analysis behavior-first rather than provider-first

## Allowed Inputs

- capability results for `repo.vcs.*`, `repo.packaging.snapshot`, `repo.packaging.classify-staged-files`, and `repo.packaging.branch-file-list`
- current changed-file sets and task boundaries
- user constraints about branch shape, commit count, or staging intent

## Required Outputs

- concise packaging summary by coherent change area
- split recommendations when one branch mixes unrelated concerns
- slash-command-ready output shapes for read-only packaging queries
- explicit uncertainty when the current provider lacks enough context
- escalation when packaging rules should become config or a wrapper contract

## Escalation Rules

- escalate to Toolsmith when provider output, configuration, or safety is insufficient
- escalate to Architect/Planner when packaging boundaries expose task-boundary problems
- escalate to Teacher when the same packaging mistake recurs and should become a reusable lesson

## Current Priorities

- validate the first packaging pilot without overbuilding it
- keep the VCS primitive capability set explicit and reusable
- keep provider assumptions visible and auditable
- separate file grouping from policy decisions about how many commits to create

## Linked Tasks

- `.ai/tasks/IN_PROGRESS/TASK-0001-agent-scaffold-bootstrap.md`

## Reference Files

- `.ai/reference/CAPABILITIES.md`
- `.ai/reference/SLASH_COMMAND_CANDIDATES.md`
- `.ai/experts/toolsmith.md`

## Memory Touchpoints

- capture repeated packaging traps only after provider behavior is stable
- keep packaging lessons concrete and config-oriented