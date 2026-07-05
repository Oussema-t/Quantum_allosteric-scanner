# TASK-0042 Hook-enforce the GIT-COMMIT gate via Claude Code PreToolUse hooks

## Context

- ID: TASK-0042
- Title: Upgrade the advisory `GIT-COMMIT` lock (TASK-0028) from "works if
  the agent remembers to run it" to hook-enforced — a Claude Code
  `PreToolUse` hook that blocks `git commit`/`git push` Bash calls unless
  the calling session currently holds the `GIT-COMMIT` claim
- Status: TODO
- Owner: Toolsmith
- Claimed By: —
- Claimed At: —
- Source: user request, 2026-07-05 session — this is exactly the question
  TASK-0028 itself deferred ("a real git hook enforcing the guard
  automatically — worth a future task if the advisory version proves
  insufficient"). That threshold looks crossed: this session alone had two
  `.ai/COMMON.md` whole-file-rewrite collisions, one real `.git/index` race
  (`e70a644`), and one misattributed commit (TASK-0025's evidence riding
  into an unrelated commit) — all before TASK-0028/0029 landed. Filed as a
  handoff (not claimed) per the user's request to formulate this for the
  Toolsmith thread specifically.
- Crit Ref: matches the scaffold's existing "advisory first, harden only
  after a real failure" precedent (TASK-0017 → TASK-0024, TASK-0025's own
  explicit deferral) — this is that harden step, not a new philosophy.
- Scope: `.claude/settings.json` (or `.local.json` — see Open Questions)
  hooks config + one small wrapper script that shells out to the existing
  `.ai/tools/claim.py`. No changes to `claim.py`'s own logic beyond what's
  needed to call it from a hook context.

## Intent Contract

- Outcome: `git commit`/`git push` Bash calls are blocked, not just
  advised against, unless the calling session currently holds the
  `GIT-COMMIT` claim.
- Verified mechanics to build against (confirmed against current Claude
  Code docs before writing this, not assumed):
  - **Event:** `PreToolUse` — fires before the tool call executes and can
    block it (`PostToolUse` fires after and cannot undo; not what we want
    here).
  - **Config location:** `hooks.PreToolUse` in `.claude/settings.json`
    (project-shared, committable) or `.claude/settings.local.json`
    (per-machine, gitignored). Precedence between the two `.claude/*`
    scopes is **not explicitly documented upstream** — don't assume, test
    empirically in this environment if it matters for placement (see Open
    Questions).
  - **Matcher:** match on tool name `"Bash"`. To avoid spawning the hook
    process on every unrelated Bash call, the optional `"if"` field
    supports permission-rule-syntax command filtering, e.g.
    `"if": "Bash(git commit *)"` — confirm the installed Claude Code
    version supports `if` before relying on it; if not, match all `Bash`
    calls and do the git-subcommand filtering inside the script instead.
  - **Hook input:** JSON on stdin, including `session_id`, `cwd`,
    `tool_name`, and `tool_input.command` (the literal command string) —
    parse `tool_input.command` to detect `git commit`/`git push`.
  - **Blocking mechanism — two options, pick one, be consistent:**
    (a) exit code `2` blocks the call and surfaces stderr as the reason;
    (b) exit `0` and print
    `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "..."}}`
    to stdout. Recommend (b) — clearer, structured reason surfaced to the
    agent instead of a bare stderr blob.
  - Hooks run with the user's own credentials, no sandboxing, and can only
    **tighten** permissions, never loosen them — design the script as
    read-only (status checks only), matching `commit-guard`'s existing
    read-only invariant.
- In Scope:
  - one hook script (placement is Toolsmith's call — keep it a thin
    wrapper that shells out to `claim.py status GIT-COMMIT` /
    `commit-guard`, not a reimplementation of lock-file reading)
  - the hook registration in `.claude/settings.json` (or `.local.json`)
  - the minimum-viable deny condition: **deny `git commit`/`git push` if
    `GIT-COMMIT` is not currently claimed by this session**
  - a note added to `.ai/COMMON.md`'s Current Rules once this lands,
    upgrading the existing advisory bullet to "enforced, not just
    advisory"
- Out Of Scope:
  - automatic `commit-guard --expect <paths>` enforcement inside the hook
    — the hook has no way to know an agent's *intended* file list unless
    that's persisted somewhere readable at hook time; that's this task's
    central Open Question, not assumed solvable in one pass
  - any hook that loosens permissions — not how the mechanism works
  - hardening any tool/command beyond the git add/commit/push family
- Constraints And Invariants:
  - Python stdlib only (matches TASK-0024/0027/0028/0029) — shell out to
    the existing `claim.py` subcommands, don't fork its logic
  - the hook script itself must never pass `--force`/`--hitl-override` to
    `claim.py` — a gate that can silently override itself defeats the
    purpose
- Planned Validation:
  1. claim `GIT-COMMIT` in one session; attempt `git commit` from a
     second session/context; confirm denial with a clear reason naming
     the holder.
  2. release the claim; confirm `git commit` proceeds normally.
  3. confirm an unrelated Bash command (e.g. `ls`, `pytest`) triggers no
     hook overhead or spurious denial.

## In Progress

None

## TODO

- [ ] Confirm the installed Claude Code version supports the `"if"`
      matcher field; if not, filter on the full command string inside the
      script instead.
- [ ] Decide hook placement: `.claude/settings.json` (shared, ships with
      the repo, protects every thread) vs `.claude/settings.local.json`
      (per-machine). Recommend the shared file — this is meant to protect
      every thread working this repo, not one operator's preference.
- [ ] Write the wrapper script; register it as a `PreToolUse` hook matched
      on `Bash`.
- [ ] Implement the minimum-viable deny condition (deny git commit/push if
      `GIT-COMMIT` is unclaimed by the calling session).
- [ ] Update `.ai/COMMON.md`'s Current Rules to state the gate is now
      enforced, not advisory-only, once landed.
- [ ] Run Planned Validation (3 cases above).

## Dependency

- [TASK-0028](../DONE/TASK-0028-commit-lock.md) (Done) — the `GIT-COMMIT`
  lock and `commit-guard` this hook wraps; do not reimplement.
- [TASK-0029](../DONE/TASK-0029-scoped-stage-tool.md) (Done) — scoped
  stage tooling; check whether its `commit-guard --expect-empty` addition
  changes what "minimum viable deny" should check here.
- [TASK-0025](../DONE/TASK-0025-command-hygiene-skill.md) (Done) —
  precedent for this scaffold's "advisory first, harden only after a real
  failure" philosophy; this task is that harden step.

## Open Questions

- Can the hook read an agent's *intended* commit-bound file list (to
  automatically enforce `commit-guard`), or does that require the agent
  to persist its `--expect` list somewhere the hook can read (e.g.
  alongside the `GIT-COMMIT` lock file) before this becomes more than a
  claim-existence check? Recommend shipping the claim-check-only version
  first and revisiting once it's proven in practice, rather than solving
  both at once.
- Should the lock file start storing `session_id` (available on every
  hook invocation) alongside — or instead of — the free-text `claimant`
  label, so the hook can verify "this exact session holds the claim"
  rather than trusting a string an agent could type for any session? This
  closes a real, if minor, gap: nothing today stops a thread from
  claiming under a label that doesn't match its actual session identity.
- `.claude/settings.json` vs `.claude/settings.local.json` precedence is
  not documented upstream (confirmed via doc lookup, not assumed) — worth
  an empirical test logged here if it turns out to matter for where this
  hook must live to apply repo-wide rather than per-machine.

## Done

(not yet)
