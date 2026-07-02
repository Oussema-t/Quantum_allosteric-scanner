# Shared Decisions

Last Updated: 2026-06-25

## D-0001

- Decision: use `.github/` for stable repo-local runtime policy and `.ai/` for mutable scaffold state.
- Rationale: VS Code and Copilot load `.github/` naturally, while mutable coordination and memory need a separate layer that can change often.
- Status: active

## D-0002

- Decision: keep existing FIX_HERE guidance under `FIX_HERE/.claude/` authoritative until migration is scoped explicitly, but do not actively reference it (we want it immediately decoupled).
- Rationale: additive bootstrap avoids duplicating or destabilizing the current domain docs.
- Status: active

## D-0003

- Decision: use `.ai/reference/CAPABILITIES.md` as the canonical capability catalog and reserve `.ai/tools/` for wrappers and provider implementations.
- Rationale: capability documentation and executable providers should not compete for the same path.
- Status: active