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

## D-0004

- Decision: scaffold-only changes (`.ai/`, `.github/`, `.claude/` — anything that never touches `backend/`/`frontend/`) are authored on this `scaffold` branch going forward, merged to `main` via its own PR, kept separate from product-code branches.
- Rationale: demonstrated need, not speculative — the branch this replaced (`bartosz`) accumulated 41 commits mixing scaffold/coordination work with a single product-code commit (a Kabsch-helper dedup), requiring manual post-hoc separation (`git worktree` + cherry-pick, one conflict) before it could be merged responsibly. A dedicated branch lets scaffold and product code be reviewed, merged, and deployed on independent cadences without that untangling step recurring every time.
- Status: active
- See: the task documenting the split itself (filed on the `bartosz` branch, not reproduced here since it's specific to that branch's history), and `COLLABORATION.md`'s "Scaffold vs. product branches" section for the operational rule contributors actually follow.