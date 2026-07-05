---
description: "Use before running any shell command with more than one step — chained (&&, ;), piped (|), or inline variable-setup-plus-execution — anywhere in this repo."
---

# Command Hygiene

- Prefer one stable, single-purpose command per tool call over composing a
  chain or pipe ad hoc at the point of use.
- Avoid chained shell orchestration (`&&`, `;`, mixed pipe workflows).
- Avoid inline shell-variable setup plus execution in the same command.
- Don't pipe or redirect a whitelisted command's output into a second,
  unwhitelisted program (`... | head`, `... | grep`, `2>&1 | tee ...`) —
  the whitelist only covers the first program; the whole command still
  prompts. If the output is long, that's a signal the underlying tool
  should support its own filtering/paging flag, not that a pipe is needed.
- If a multi-step sequence is genuinely required and likely to recur,
  expose it as a short, named, reusable script (`.ai/tools/` for
  scaffold-local scripts, `agents-tools/` for capability-runner-backed
  ones) instead of reinventing the pipeline inline each time:
  1. check `.ai/reference/CAPABILITIES.md` first — a capability may
     already cover it.
  2. if not, write the smallest script that performs the same effect as
     one entry point, stdlib/POSIX only, no new runtime dependency.
  3. register it in `.ai/reference/CAPABILITIES.md`.
  4. draft (do not apply) a `.claude/settings.json` allowlist line for it
     and get human approval before it lands.
- Prefer request-file mode for multi-argument or repeatable runs; reserve
  inline arguments for short one-off invocations.
- Run artifact extraction or follow-up snippet generation as a separate
  command after the main one, not chained onto it.

## Why

- **Token churn:** a named script call is cheaper context per turn than
  re-deriving or reasoning through a chained pipeline every time the same
  effect is needed.
- **Determinism:** a reviewed, named script's behavior is fixed and
  auditable; an ad hoc pipeline composed fresh each time can silently vary
  (flag order, quoting, intermediate state) between threads or sessions.
- **Whitelisting:** fewer distinct ad hoc command shapes means fewer
  `.claude/settings.json` allowlist patterns to reason about, and a real
  incentive to route through a named script or capability runner instead
  of composing shell inline.

## Evidence

Two reproduced incidents this session (see `.ai/reference/CAPABILITIES.md`,
the callouts after the `.ai/tools/claim.py`-backed capability rows, for the
full writeup): piping a whitelisted command's output to `head` still
prompted (the pipe hands off to a second, unwhitelisted program), and a
5-program `&&` chain prompted the same way. Splitting the chain into
separate calls would still leave up to three individual prompts — the fix
is a named script, not just fewer symbols per line.

## Origin

Generalizes `.github/prompts/test-execute.prompt.md`'s existing
"Command-structure contract for local execution" (originally scoped to
`workflow.testexecution.run` only) to every thread, per TASK-0025. That
prompt should point here rather than keep its own inline copy.
