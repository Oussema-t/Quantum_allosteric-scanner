# Scaffold Memory

Last Updated: 2026-06-25
Status: Seeded

This directory stores reviewed memory for the repo-local agent scaffold.

## Layout

- `shared/`
  - reviewed team truth for scaffold decisions, patterns, pitfalls, questions, and glossary
- `experts/`
  - per-role session and long memory stubs
- `archive/`
  - superseded or expired memory retained for audit only

## Source Of Truth Rules

- `shared/*` is canonical for scaffold-wide decisions and patterns.
- expert long memory is durable local recall, not team truth.
- session memory is temporary and must not be treated as durable truth.
- if expert memory conflicts with `shared/*`, shared memory wins until reviewed.

## Promotion Ladder

1. review note
2. learning
3. invariant candidate

Promote only when the item is evidence-backed and reusable.

## Rules

- store structure, not narrative
- one entry should capture one decision, lesson, warning, or open question
- use links to source docs instead of copying large context
- add expert-specific files only after a role starts producing reusable knowledge