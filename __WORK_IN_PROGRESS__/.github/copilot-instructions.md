# Repo Agent Scaffold

This repository uses a two-layer agent scaffold.

- `.github/` stores stable runtime instructions and future agent artifacts.
- `.ai/` stores mutable coordination, references, task files, reviews, tools, and memory.

Rules:

1. Read `.ai/COMMON.md` before non-trivial scaffold work.
2. Keep live execution in `.ai/tasks/TASK-*.md`, not in `.github/`.
3. Treat `.ai/memory/shared/*` as reviewed team truth for scaffold learnings.
4. Use `.ai/reference/CAPABILITIES.md` as the canonical capability catalog.
5. Keep `.github/` short, durable, and free of active task state.

Bootstrap boundary:

- `.ai/` is the root-level project-agnostic scaffold pilot.
- Existing module-local `.claude/` documentation remains authoritative for the current Playwright/Testkube slice until a dedicated migration is approved.