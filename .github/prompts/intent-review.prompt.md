---
description: "Run the early critic pass over the current Intent Contract before implementation begins."
name: "Intent Review"
argument-hint: "Optional intent focus and flags such as ui-intent, no-ui-intent, or testcase-export source"
agent: "agent"
---

Use the intent critic-review workflow for the current slice.

Sources:

- operation protocol: [OPERATION_PROTOCOL](../../.ai/reference/OPERATION_PROTOCOL.md)
- intent template: [INTENT_CONTRACT_TEMPLATE](../../.ai/reference/INTENT_CONTRACT_TEMPLATE.md)
- intent contract prompt: [INTENT_CONTRACT](../../.github/prompts/intent-contract.prompt.md)
- ui intent capability: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- first agent bootstrap: [FIRST_AGENT_BOOTSTRAP](../../.ai/reference/FIRST_AGENT_BOOTSTRAP.md)
- general critic brief: [GENERAL_CRITIC](../../.ai/experts/general-critic.md)

Required behavior:

- Treat this as the `Intent Critic Review` protocol step.
- Review the current Intent Contract before broad implementation begins.
- Focus on ambiguity, contradictory scope, missing acceptance criteria, weak planned validation, unclear ownership boundaries, and hidden assumptions.
- Keep the review intent-layer only; do not jump ahead to exact implementation design unless a flaw in the intent requires it.
- Optional auto-chain: after the critic pass, run `workflow.uiintent.review` only when one of these is true and `no-ui-intent` is not requested:
	- user explicitly requests `ui-intent`
	- user provides testcase-export evidence (for example a CSV path or testcase artifact reference)
- For optional auto-chain, keep output bounded to intent-vs-assertion alignment and smallest safe contract adjustment.
- If the intent is not yet explicit enough, say so and identify the smallest missing fields.
- Do not modify files unless the user separately asks for an update.

Respond in this shape:

- `Findings:` ordered by severity with concrete evidence from the current intent.
- `UI Intent:` include only when optional auto-chain executed; summarize inferred intent and top mismatch.
- `Open Questions:` only if the current intent still lacks required facts.
- `Risk/Unknown:` residual ambiguity or validation risk.
- `Next:` smallest useful corrective action such as refine intent, run discovery, or derive execution.