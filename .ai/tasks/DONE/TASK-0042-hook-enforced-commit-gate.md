# TASK-0042 Hook-enforce the GIT-COMMIT gate via Claude Code PreToolUse hooks

## Context

- ID: TASK-0042
- Title: Upgrade the advisory `GIT-COMMIT` lock (TASK-0028) from "works if
  the agent remembers to run it" to hook-enforced — a Claude Code
  `PreToolUse` hook that blocks `git commit`/`git push` Bash calls unless
  the calling session currently holds the `GIT-COMMIT` claim
- Status: Done
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

- [x] Confirm the installed Claude Code version supports the `"if"`
      matcher field; if not, filter on the full command string inside the
      script instead. **Not relied on** — matched all `Bash` calls and did
      the git-subcommand filtering inside the script, per this file's own
      documented fallback, rather than spend time confirming an optional
      feature this task doesn't actually need.
- [x] Decide hook placement: `.claude/settings.json` (shared, ships with
      the repo, protects every thread) vs `.claude/settings.local.json`
      (per-machine). **Shared file used**, per this file's own recommendation.
- [x] Write the wrapper script; register it as a `PreToolUse` hook matched
      on `Bash`.
- [x] Implement the minimum-viable deny condition (deny git commit/push if
      `GIT-COMMIT` is unclaimed by the calling session).
- [x] Update `.ai/COMMON.md`'s Current Rules to state the gate is now
      enforced, not advisory-only, once landed.
- [x] Run Planned Validation (3 cases above) — extended to 6, see Done.

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
  claim-existence check? **Shipped as recommended** — claim-identity check
  only (see Done). Full `--expect` enforcement stays a real follow-up, not
  attempted here.
- **Resolved (Bartosz, 2026-08-03): both fields, different readers.**
  `claimant` stays the free-text label — answers "what role is this claim"
  for a human reading `.ai/COMMON.md`/`claim.py status`. `session_id`
  (read from `CLAUDE_CODE_SESSION_ID`, never a CLI argument) answers "which
  exact running session, precisely" — what the hook actually checks a
  commit attempt against, and what closes the spoofing gap this question
  originally named (a caller could type any `claimant` string; it cannot
  fabricate its own environment's session id). Implemented in
  `claim.py`'s `session_id()` helper, written on every lock (`claim`,
  `reserve-next`, `scq-enter`), surfaced in `status`'s output.
- `.claude/settings.json` vs `.claude/settings.local.json` precedence is
  not documented upstream (confirmed via doc lookup, not assumed) — moot
  for this task: the shared file was used and works (Planned Validation
  below), so this is left as a genuinely open question for whoever
  eventually needs `.local.json` specifically, not resolved here.

## Done

**2026-08-03, Architect.** Two parts, per the resolved Open Question above.

**Part 1 — `claim.py`: `session_id` alongside `claimant` on every lock.**
New `session_id()` helper reads `CLAUDE_CODE_SESSION_ID` from the
environment (confirmed present on every Bash call in this environment,
a 36-char value, present via direct `env` inspection before relying on
it — not assumed from the hook-input schema alone). Written into the lock
dict in `cmd_claim` (covers both the plain-claim and `--force`-override
branches, which share the same `data` dict), `cmd_reserve_next`, and both
branches of `cmd_scq_enter` (new ticket and re-entering-in-place). `status`
(both the single-id and full-listing forms) now prints
`claimed by 'X' [session xxxxxxxx...] at ...` via a new `_short_sid()`
helper — absent session_id (a lock written before this change, or claimed
outside a Claude Code session) prints `no-session-id` explicitly rather
than a blank, so it reads as "unverifiable", not "fine."

**Part 2 — the hook.** `.ai/tools/git_commit_guard_hook.py`, registered
under `hooks.PreToolUse` in `.claude/settings.json` (shared file, matcher
`"Bash"`, no reliance on the optional `"if"` command-filter — regex
filtering for `git commit`/`git push` done inside the script instead, per
this file's own documented fallback). Imports `claim.py` directly
(`read_lock`) rather than shelling out to `status` and parsing text —
one implementation of the lock format, not two.

**Fails closed, not open** — every ambiguous state denies rather than
allows: unclaimed lock, a lock with no recorded `session_id` (legacy or
non-Claude-Code claim), or a caller with no incoming `session_id`, all
deny with a specific, distinguishing reason rather than a generic message
or (worse) silent passage.

**Planned Validation, all 3 original cases plus 3 more found worth
checking while building:**
1. Unrelated `Bash` command (`ls -la`) → allowed, no hook output. Confirmed.
2. `git commit`, `GIT-COMMIT` unclaimed → denied, names the exact `claim`
   command to run. Confirmed.
3. `git commit`, `GIT-COMMIT` claimed by a different `session_id` → denied,
   names the current claimant and both (truncated) session ids, and the
   two legitimate ways to proceed (release, or a human-instructed
   `--force --reason --hitl-override`). Confirmed.
4. `git commit`, `GIT-COMMIT` claimed by *this* `session_id` → allowed,
   no hook output. Confirmed.
5. `git push`, held by this session → allowed (the same regex covers both
   verbs, per this task's own original scope). Confirmed.
6. `git commit-tree` (a plumbing look-alike) → allowed, not treated as a
   real commit — confirms the word-boundary regex doesn't over-match.
   Confirmed.
7. **Fail-closed check, added beyond the original 3**: a hand-crafted
   legacy-format lock with no `session_id` field → denied with a message
   naming exactly that ("identity cannot be verified"), not silently
   allowed. Confirmed — this is the case a less careful implementation
   would get wrong.

**`.ai/COMMON.md`'s Current Rules** updated: the `GIT-COMMIT` claim-before-
staging bullet now states the gate is hook-enforced for `git commit`/
`git push` specifically (denies at the tool-call level, not merely
advisory), while still noting the hook is an identity check on the lock,
not a substitute for `commit-guard --expect`'s file-list verification —
that half of the discipline remains manual.

**Not done, flagged not hidden**: automatic `commit-guard --expect`
enforcement inside the hook (this task's own Out Of Scope); hardening any
command beyond the `git commit`/`git push` family; the `.local.json`
precedence question above.
