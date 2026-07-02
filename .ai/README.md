# .ai Agent Scaffold

Last Updated: 2026-06-25
Status: Bootstrap in progress

`.ai/` is the mutable project layer for the repo-local agent scaffold.

This layer is additive.

- `.github/` stores stable runtime policy and repo-local instructions.
- `.ai/` stores mutable coordination, references, tasks, reviews, tools, and memory.
- Existing domain-specific guidance under `FIX_HERE/.claude/` remains authoritative until migration is planned explicitly.

## Start Here

1. Read `.ai/COMMON.md`.
2. Read `.ai/ARCHITECTURE_OVERVIEW.md`.
3. Open the active task file in `.ai/tasks/`.
4. Use `.ai/reference/CAPABILITIES.md` for named tool behaviors.
5. Use `.ai/memory/README.md` for learning retention and promotion.

## Directory Map

- `.ai/COMMON.md`
  - coordination hub and source-of-truth map for the scaffold
- `.ai/reference/`
  - canonical reference docs such as capability catalogs
- `.ai/tasks/`
  - live execution state for non-trivial scaffold work
- `.ai/tools/`
  - future wrappers, scripts, and provider implementations
- `.ai/experts/`
  - mutable expert-role briefs and ownership notes
- `.ai/reviews/`
  - critic outputs and review artifacts
- `.ai/memory/`
  - reviewed memory, promotion rules, and expert memory stubs

## Current Scope

Phase 1 and Phase 2 only:

- bootstrap folder structure
- add stable repo-local policies
- seed coordination, capability, and memory documents

Not included yet:

- runtime custom agents under `.github/agents/`
- MCP server implementation
- broad migration of existing `.claude` content
- wrappers for all current `agents-tools` providers