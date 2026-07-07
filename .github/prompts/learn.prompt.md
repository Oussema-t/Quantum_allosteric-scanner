---
description: "Internalize and retrieve canonical learned facts with explicit retrieval-path metadata."
name: "Learn"
argument-hint: "mode=<internalize|retrieve|improve> plus query/source keys; e.g. mode=retrieve family=006"
agent: "agent"
---

Use the learn workflow for this repository.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- backend selection: [BACKEND_SELECTION](../../.ai/reference/BACKEND_SELECTION.md)
- traceability model: [TRACEABILITY_MODEL](../../.ai/reference/TRACEABILITY_MODEL.md)
- active learn schema: [LEARN_SCHEMA](../../.ai/tasks/contracts/learn-schema-index-v1.md)

Required behavior:

- Treat this as the `workflow.learn.manage` capability.
- Require explicit `mode=<internalize|retrieve|improve>`.
- Supported core arguments:
  - `query=<string>` for `retrieve` and `improve`
  - `source=<path-or-id>` for `internalize`
  - `family=<id>` optional scope key (example: `006`)
  - `case_id=<id>` optional narrow key 
  - `confidence=<high|medium|low>` required for `internalize`
- Retrieval mode must use schema-index as authoritative learned-fact lookup.
- Source grep may be used only for bootstrap or source discovery and must never be treated as authoritative learned-fact storage.
- Output must include `lookup_path` metadata with value `schema-index` or `source-grep`.
- Keep retrieval output separate from improve/proposal output.
- Do not write to external systems.

Respond in this shape:

- `Answer:` mode and high-level outcome.
- `Evidence:` source references, retrieval path, and key result summary.
- `Risk/Unknown:` stale, missing, or low-confidence factors.
- `Next:` smallest useful follow-up action.
