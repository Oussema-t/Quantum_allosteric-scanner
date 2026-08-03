#!/usr/bin/env python3
"""PreToolUse hook: deny `git commit`/`git push` Bash calls unless the
calling session currently holds the `GIT-COMMIT` claim (TASK-0042).

Upgrades TASK-0028's advisory lock (works only if the agent remembers to
run `claim.py claim GIT-COMMIT ...` first) to an actually-enforced one.
Registered under `hooks.PreToolUse` in `.claude/settings.json`, matched on
the `Bash` tool -- Claude Code invokes this script with the proposed tool
call as JSON on stdin, before the call executes, and this script can deny
it. See `.ai/tasks/DONE/TASK-0042-hook-enforced-commit-gate.md` for the
full design record and the mechanics this was built against.

Deliberately minimum-viable, per that task's own Out Of Scope: this is a
claim-*identity* check only (is `GIT-COMMIT` held, and by this exact
session), not full automatic `commit-guard --expect <paths>` enforcement
-- the hook has no way to know an agent's *intended* file list unless
that were separately persisted somewhere readable at hook time, which
that task's own Open Questions left unsolved on purpose rather than
overreach in one pass.

Identity check, not just existence: TASK-0042's own Open Questions named
a real gap in the plain "is GIT-COMMIT claimed by anyone" check -- nothing
stopped a thread from claiming under a free-text label that doesn't match
its actual session. Closed here by recording `session_id` (read from the
`CLAUDE_CODE_SESSION_ID` environment variable at claim time, never a
caller-supplied argument) alongside the human-facing `claimant` label in
every lock file, and comparing it against the `session_id` this hook
receives on stdin for the *current* call. Label answers "what role is
this claim" (HITL-facing); session_id answers "which exact running
session, unambiguously" (agent-facing) -- both fields serve different
readers and neither substitutes for the other.

Fails closed, not open: any state this script cannot positively verify
(no lock, no recorded session_id, no incoming session_id, an unreadable
lock file) is treated as "deny", never as "allow by default". A gate that
silently degrades to permissive on its own error modes is worse than no
gate at all -- it would look enforced while enforcing nothing.

Reuses `claim.py`'s own `read_lock` directly (imported as a module, same
directory) rather than shelling out and parsing `status`'s human-readable
text output -- avoids a second, driftable parser for the same lock-file
format; this is not a reimplementation of the locking logic, it's the
one real implementation, called in-process.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import claim  # noqa: E402  (path insert must precede this import)

# Matches `git commit`/`git push` as a whole subcommand -- `(\s|$)` after
# the subcommand name excludes plumbing look-alikes like `git commit-tree`
# or `git push-something` (none exist upstream today, but the boundary is
# cheap and correct either way). `re.search`, not `match`: the real
# command is often a compound shell line (`cd X && git commit -F msg`),
# and the git invocation can appear anywhere in it.
_COMMIT_OR_PUSH_RE = re.compile(r"\bgit\s+(commit|push)(\s|$)")


def _deny(reason):
    # type: (str) -> None
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def main():
    # type: () -> int
    try:
        payload = json.load(sys.stdin)
    except (ValueError, json.JSONDecodeError):
        # Malformed input from the harness itself is not this hook's
        # failure mode to diagnose -- fail closed rather than guess.
        _deny(
            "git-commit-guard hook: could not parse hook input JSON; "
            "denying git commit/push out of caution rather than guessing "
            "intent."
        )
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = (payload.get("tool_input") or {}).get("command", "") or ""
    if not _COMMIT_OR_PUSH_RE.search(command):
        return 0

    lock = claim.read_lock("GIT-COMMIT")
    if lock is None:
        _deny(
            "GIT-COMMIT is not currently claimed. Run `python3 "
            ".ai/tools/claim.py claim GIT-COMMIT \"<label>\"` before "
            "staging/committing -- see .ai/COMMON.md's Current Rules for "
            "the full claim -> commit-guard -> stage -> commit-guard -> "
            "commit -> release sequence."
        )
        return 0

    held_sid = lock.get("session_id")
    caller_sid = payload.get("session_id")
    if not held_sid or not caller_sid:
        _deny(
            "GIT-COMMIT is claimed by %r, but its recorded session_id is "
            "missing (an old lock, or one claimed outside a Claude Code "
            "session) -- identity cannot be verified, so this is denied "
            "rather than assumed safe. Release and re-claim to refresh "
            "the lock's session_id, then retry." % lock.get("claimant")
        )
        return 0

    if held_sid != caller_sid:
        _deny(
            "GIT-COMMIT is claimed by %r [session %s...], not this "
            "session [%s...]. If that other claim is stale, release it "
            "explicitly (`claim.py release GIT-COMMIT`) or override with "
            "`claim.py claim GIT-COMMIT ... --force --reason ... "
            "--hitl-override` -- only with an explicit human instruction "
            "in the current conversation to do so, never on an agent's "
            "own judgment."
            % (lock.get("claimant"), held_sid[:8], caller_sid[:8])
        )
        return 0

    # Held, and held by this exact session -- allow, no output needed.
    return 0


if __name__ == "__main__":
    sys.exit(main())
