# Agent Scaffold Architecture Overview

## Goal

Provide a project-agnostic, repo-local operating model that can be reused by other repositories without inheriting Portal or Testkube-specific structure.

## Layers

### 1. Stable Runtime Layer

Stored in `.github/`.

Contains:

- runtime instructions
- future prompts
- future custom agents

Rules:

- no task state
- no timestamps unless part of a durable contract
- no temporary incidents or local-only status

### 2. Mutable Project Layer

Stored in `.ai/`.

Contains:

- coordination hub
- expert briefs
- task files
- review reports
- references
- memory

Rules:

- broad docs stay stable within the mutable layer
- live execution moves into dedicated task files

### 3. Capability Layer

Providers:

- MCP or tool server when available
- repo-local scripts under `agents-tools/`
- manual fallback only when automation is absent

This layer is cataloged in `reference/CAPABILITIES.md`.

### 4. Learning Retention Layer

Stored in `.ai/memory/`.

Promotion path:

- review note
- learning
- invariant

Canonical rule:

- reviewed shared memory is the team truth
- temporary working memory is not durable truth

## Bootstrap Boundary

- Root `.ai/` is a scaffold pilot.
- Existing module `.claude/` documentation remains in place until a dedicated migration is approved.