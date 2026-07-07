---
description: "Use when deciding whether information belongs in stable repo instructions or mutable project knowledge."
applyTo: ".ai/**/*.md"
---

# Stable Versus Mutable Split

- Put long-lived operating rules in `.github/`.
- Put active project state in `.ai/`.
- Stable files should contain behavior rules, trigger phrases, boundaries, and durable contracts.
- Mutable files should contain status, blockers, task state, environment notes, and current priorities.
- If a fact explains how the agent should always behave, keep it stable.
- If a fact describes the current state of work, keep it mutable.