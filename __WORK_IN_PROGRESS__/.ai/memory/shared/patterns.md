# Shared Patterns

Last Updated: 2026-06-25

## P-0001 Stable vs Mutable Split

- Stable rules live in `.github/`.
- Active status, tasks, and changing context live in `.ai/`.
- Do not mix temporary task state into stable instructions.

## P-0002 Capability-First Tooling

- Name the behavior first.
- Bind the behavior to a provider second.
- Prefer MCP when stable, local wrappers when practical, and manual fallback last.