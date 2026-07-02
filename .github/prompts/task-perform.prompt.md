---
description: "Perform one selected TODO item from a task file and synchronize task state, with optional opt-in chain mode and optional quality-review chaining."
name: "Task Perform"
argument-hint: "Task path and optional selector (phase/item); optional chain mode with hops (default 3); optional quality chain: .ai/tasks/TASK-0002-*.md chain hops=3 chain-quality"
agent: "agent"
---

Use the task-perform workflow for this repository.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- backend selection: [BACKEND_SELECTION](../../.ai/reference/BACKEND_SELECTION.md)
- task file shape: [TASKS README](../../.ai/tasks/README.md)
- traceability model: [TRACEABILITY_MODEL](../../.ai/reference/TRACEABILITY_MODEL.md)

Required behavior:

- Treat this as the `workflow.task.perform` capability.
- Require a task file path matching `.ai/tasks/TASK-*.md`.
- If a selector is provided, perform that specific TODO item only.
- If no selector is provided, choose the next unchecked actionable TODO from the earliest incomplete phase and state which item was selected.
- Default mode is single-hop: keep work bounded to one coherent TODO outcome per run.
- Opt-in chain mode is allowed only when the user explicitly passes `chain`.
- In chain mode, default `hops=3`.
- In chain mode, `hops` is overridable via `hops=<n>`.
- In chain mode, if `hops` is missing, invalid, or less than 1, fall back to `hops=3`.
- In chain mode, perform one coherent TODO outcome per hop and persist task-file updates after each hop.
- In chain mode, stop early on first blocking failure, low-confidence result, explicit user stop condition, or when no actionable TODO remains.
- If a selector is provided, do not chain beyond that selected item unless the user explicitly requests both selector-first and chaining.
- Execute implementation and focused validation in the same run unless explicitly asked for `no-run`.
- Command-structure contract for local execution steps:
	- prefer one stable capability invocation per execution step, for example `agents-tools/capability-runner.sh repo.test.playwright-local ...`
	- do not use chained one-liners for execution (`&&`, `;`, or pipe-based orchestration) when running tests
	- do not embed log/snippet path construction and execution in the same shell command
	- prefer request-file mode for long or repeated Playwright invocations; use inline args only for short one-off runs
	- if artifact capture is needed, run capture as a separate explicit step after execution
- Optional quality chaining is enabled only when the user explicitly passes `chain-quality`.
- When `chain-quality` is enabled, run `workflow.codequality.review` with `best-practice` focus only if all hard gates pass and at least one risk gate is true.
- Hard gates for `chain-quality`:
	- task-perform changed repository code files (not only task/docs/prompt files)
	- focused validation was executed in the same run
	- confidence is high and boundary meaningfully improved or shifted after the change
	- user did not request read-only/no-chain behavior
- Risk gates for `chain-quality` (any one):
	- changed shared POM/action/helper logic used by multiple specs
	- changed waits/retries/polling/reload/synchronization logic
	- changed role/permission/visibility contract logic
	- changed at least two code files or at least 30 non-comment LOC in code files
	- introduced fallback/heuristic logic with regression risk
- Skip `chain-quality` when only non-code files changed, evidence confidence is below high, or best-practice review already ran for the same hop.
- Run `chain-quality` at most once per hop and persist outcome in the same TASK file under `## Best-Practice Review Outcome`.
- Update the same task file in the same run.
- For task-file updates, synchronize `## TODO`, `## Execution Evidence`, and `## Immediate Next Steps`.
- Mark completed TODO entries in place and append the next smallest follow-up action.
- Do not create tickets or write to external systems in this command.

Respond in this shape:

- `Answer:` selected TODO item and high-level outcome.
- `Evidence:` changed files, focused validation command, and result summary.
- `Chain:` include only when chain mode is used; report requested hops, completed hops, and stop reason.
- `Quality:` include only when chain-quality was requested; report whether gates passed, whether best-practice-review executed, and outcome summary.
- `Risk/Unknown:` residual ambiguity or unverified edges.
- `Next:` smallest useful follow-up.
