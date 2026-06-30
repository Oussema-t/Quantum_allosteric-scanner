---
description: "Use when deciding whether work should use an MCP, a local repo tool, or a manual fallback."
---

# Capability Selection

- Start from the capability needed, not from a script path.
- Resolve providers in this order:
  1. MCP or tool server
  2. repo-local wrapper or script
  3. manual fallback
- Prefer providers with dry-run, structured output, and a documented environment contract.
- Prefer capability boundaries that can also surface as slash commands with explicit inputs and predictable outputs.
- If only a project-specific script exists, treat it as an overlay provider until it is wrapped behind a generic interface.
- Destructive capabilities must document scope, confirmation, and safety constraints.
- Record new or changed capabilities in `.ai/reference/CAPABILITIES.md`.