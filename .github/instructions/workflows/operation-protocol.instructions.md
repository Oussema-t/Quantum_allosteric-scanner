---
description: "Use when work needs an intent-first workflow from human-readable goal through implementation, verification, and learning."
applyTo: ".ai/tasks/**/*.md"
---

# Operation Protocol

- Treat intent as a protocol artifact, not as a standalone expert.
- Start non-trivial work with an Intent Contract before exact implementation details.
- For `.ai/tasks/**/*.md`, make the Intent Contract a mandatory section.
- Keep the intent human-readable and implementation-agnostic.
- Express desired behavior with BDD-style scenarios before deriving exact test or code structure.
- Run an intent review before broad implementation starts.
- Derive the execution slice, TDD checks, and local validation plan from the approved intent.
- If verification fails or becomes ambiguous, run a bounded debugging sub-loop before redefining intent or widening scope.
- Keep implementation, review, final verification, and learning capture explicit.
- Use the same artifacts for manual orchestration and agent workflows.
- Minimize HITL touchpoints to objective framing, risky-scope approval, and final acceptance.