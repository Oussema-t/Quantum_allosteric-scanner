---
name: command-hygiene
description: Use when you are about to run, or just ran, a chained (&&, ;) or piped (|) shell command anywhere in this repo — including piping a whitelisted command's output into a second, unwhitelisted program (e.g. `... | head`). Turns a repeated multi-step command into a single named, reusable, whitelisted script instead of reinventing the pipeline inline. Triggers on: "chain", "pipe", "&&", multi-step shell, "permission prompt", reusable script, command hygiene.
---

# Command Hygiene

Implements `.github/instructions/tooling/command-hygiene.instructions.md`
(TASK-0025, repo-wide). Read that file first for the full policy and
rationale — this skill is the concrete procedure for acting on it.

## When this fires

- You are about to compose a command with `&&`, `;`, or a pipe (`|`).
- You just ran one (including piping a whitelisted command's output to an
  unwhitelisted one, e.g. `python3 .ai/tools/claim.py status | head`) and
  it prompted for permission, or you notice you've run a similar chain
  more than once this session.
- A one-off chain that will genuinely never recur does **not** need this
  skill — extracting a script for something run exactly once is premature
  abstraction, not hygiene. Use judgment; the bar is "likely to recur,"
  not "any multi-step command."

## Procedure

1. **Decompose.** List the distinct programs/steps in the chain and what
   each one actually contributes to the final result.
2. **Check for an existing capability first.** Search
   `.ai/reference/CAPABILITIES.md` for a row that already covers this
   combination. If one exists, use it directly instead of the chain —
   stop here.
3. **If none exists and it's likely to recur, write the smallest script**
   that produces the same effect as one entry point:
   - location: `.ai/tools/` for scaffold-local scripts, `agents-tools/`
     for capability-runner-backed ones (see
     `.ai/reference/CAPABILITIES.md`'s provider-order rule).
   - stdlib/POSIX only — no new runtime dependency.
   - reuse existing code where it exists rather than re-deriving it (e.g.
     import a sibling module in the same directory instead of shelling out
     to it as a second process). See `.ai/tools/task_locate.py` for a
     worked example: it replaced a 5-program `&&` chain by importing
     `claim.py`'s own lock-reading and disk-scan functions directly.
   - deterministic, sorted output wherever the original chain's output
     needed to be.
4. **Register it** as a new row in `.ai/reference/CAPABILITIES.md`
   (capability name, purpose, provider command, scope, safety class, one
   line of notes — match the existing table's shape).
5. **Draft — do not apply — a `.claude/settings.json` allowlist line** for
   the new script's invocation. Present the exact line to the human and
   wait for explicit approval before adding it, per
   `.ai/reference/LOCAL_AUTOMATION_MANUAL_ENVIRONMENTS.md`'s
   approval-gated-helper rule. Never widen an allowlist entry beyond the
   read-only or narrowly-scoped invocation you just built.
6. **Prefer the new script going forward.** Once it exists and is
   registered, use it instead of reconstructing the original chain —
   that's the whole point.

## Worked example (this session)

- Incident: `python3 .ai/tools/claim.py status && echo ... && find
  .ai/tasks -iname "TASK-0024*" && echo ... && ls .ai/tasks/TODO
  .ai/tasks/IN_PROGRESS .ai/tasks/DONE` — a 5-program chain, reproduced
  and root-caused in `.ai/reference/CAPABILITIES.md`.
- Fix: `.ai/tools/task_locate.py <TASK-ID>` — one script, one whitelisted
  call, same effect (claim status + on-disk path + lifecycle-folder
  state), registered as `workflow.task.locate` in `CAPABILITIES.md`.
- The `.claude/settings.json` allowlist line for it is drafted, not yet
  applied — pending human approval (see TASK-0025's Done section once
  filled in).
