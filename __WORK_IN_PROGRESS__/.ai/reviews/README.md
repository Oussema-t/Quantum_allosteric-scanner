# Review Artifacts

Last Updated: 2026-06-25
Status: Seeded

This directory stores critic outputs and review artifacts for scaffold work.

## Review Shape

- one review file per coherent slice
- findings ordered by severity
- evidence first
- recommended fixes tied to the owning task
- follow-up status when re-review is needed

## Severity

- `P0`: blocks use or creates incorrect source-of-truth behavior
- `P1`: high-value structural issue or validation gap
- `P2`: maintainability, clarity, or ergonomics issue
- `P3`: low-priority clarity or polish issue

## Current Rule

- Link each review back to its task file.
- Promote durable findings into `.ai/memory/shared/*` after resolution.