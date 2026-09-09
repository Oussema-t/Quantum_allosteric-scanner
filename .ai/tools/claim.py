#!/usr/bin/env python3
"""Atomic claim/release/status/sync tool for .ai/tasks/ coordination.

Built for TASK-0024: replaces hand-edited "Claimed By" / "Claimed At"
cells in .ai/COMMON.md's Active Work Registry (a last-writer-wins prose
table) with per-task lock files under .ai/tasks/.locks/, created with an
O_EXCL atomic open. `sync` regenerates only the Claimed By / Claimed At
cells of that table from the lock files -- every other column (Description,
Assigned To, Priority, Last Active, Path) stays hand-maintained, per
TASK-0024's decision to scope this to the claim mechanism only.

Extended for TASK-0028: GIT-COMMIT is a fixed, non-task resource id
usable with claim/release/status like any TASK-XXXX id, meant to serialize
the git add -> git commit critical section across threads. Overriding a
held GIT-COMMIT claim requires --hitl-override in addition to
--force --reason -- do not pass --hitl-override without an explicit human
instruction, in the current conversation, to override a held commit lock.
`commit-guard` is a separate, read-only safety check: it compares the
actually-staged git index against an --expect list and refuses if they
don't match exactly, independent of whether GIT-COMMIT was claimed.
--expect-empty asserts nothing is staged yet -- run it before your first
git add, so a mismatch is caught before the index is ever touched, not
after (fail-fast beats add-then-check-then-git-reset-HEAD--).

Extended for TASK-0027: `move` relocates a task file between
TODO/IN_PROGRESS/DONE, rewrites its own "- Status:" line, and updates its
.ai/COMMON.md registry row's Status/Path cells, all as one command --
refusing on a claim mismatch the same way `claim` does. Moving to DONE
auto-releases the claim by default (--keep-claim to opt out).

Extended for TASK-0029: `stage` runs `git add` on exactly the --expect
paths and self-verifies with the same comparison commit-guard uses --
but ONLY for paths under .ai/ or .claude/ (path-traversal-safe: it
normalizes first). This is deliberate and load-bearing: claim.py's own
invocation is already blanket-whitelisted, so an unscoped stage wrapper
would silently make that whitelist imply unconstrained `git add` of any
repo path. Anything outside .ai/.claude still needs a plain `git add`,
which correctly prompts. Recommended workflow as of this task -- see the
TASK-0356 paragraph below for the current, revised form:
    claim GIT-COMMIT -> commit-guard --expect-empty -> stage --expect ... ->
    commit-guard --expect ... -> git commit -> release GIT-COMMIT

Extended for TASK-0154: `stage` now refuses outright unless GIT-COMMIT is
currently claimed (by anyone -- an existence check, not yet an identity
check against the caller). Real incident, 2026-07-24: a thread staged
files via `stage` before ever claiming GIT-COMMIT -- nothing previously
checked for that, `stage` would run regardless of lock state. This is
deliberately scoped to `stage` alone, not `move`/`resolve` (both also
call `git add`/`git mv` internally): those are routine task-file
housekeeping calls this whole scaffold already relies on working without
holding GIT-COMMIT first (e.g. marking a task Done mid-session, well
before deciding what to bundle into a commit) -- `stage` is the one
subcommand whose entire purpose is the deliberate, immediately-pre-commit
staging step, so it's the one that should never run lock-less.

Extended for TASK-0045: `reserve-next` atomically hands back a TASK-XXXX
id guaranteed not to collide with any other thread's concurrent
reservation. Plain `claim` requires the caller to already know which id
to ask for -- if two threads independently compute "the highest number"
from a snapshot (disk listing, CAPABILITIES.md read, etc.) and then each
file a new task at highest+1, that read-then-write gap is exactly where a
collision happens (the incident that motivated this: two threads both
filed TASK-0045). `reserve-next` closes the gap by taking the highest
number found across BOTH on-disk task files AND currently-held lock files
(a number can be "used" before its task file is ever written), then
claiming that candidate via the same O_EXCL primitive `claim` uses,
retrying upward on a lost race instead of racing again on the next
candidate.

Extended for TASK-0065: `scq-enter`/`scq-leave` implement a Stage-Commit-
Queue (SCQ) -- a gitignored, per-ticket-file FIFO queue for the
GIT-COMMIT resource. A thread proactively publishes its intended file
list and a prepared commit message any time it knows enough (not only
after being refused GIT-COMMIT); `status GIT-COMMIT` (and the
no-argument full listing) shows the whole ordered queue. Visibility
only -- nothing enforces queue order, `claim GIT-COMMIT` behaves exactly
as before. Entries are `SCQ-XXXX.lock` files reusing the existing
`.ai/tasks/.locks/*.lock` gitignore glob as-is. Re-entering as the same
claimant updates that claimant's ticket in place. An entry is
automatically removed once that same claimant successfully claims
GIT-COMMIT. Ticket ids reuse `reserve-next`'s generalized
allocate-with-retry logic (now parameterized by prefix, shared with
TASK-XXXX allocation) rather than a second allocator.

Extended for TASK-0042: every claim-producing subcommand (`claim`,
`reserve-next`, `scq-enter`) now records `session_id` (read from the
`CLAUDE_CODE_SESSION_ID` environment variable, never a caller-supplied
argument) alongside the existing free-text `claimant` label -- `claimant`
answers "what role holds this" (HITL-facing), `session_id` answers "which
exact running session, precisely" (what the `git_commit_guard_hook.py`
PreToolUse hook checks a commit/push attempt against). `status` surfaces
both.

Extended for TASK-0197: `stage --expect <path>` no longer refuses a path
that is absent from disk if that path is still tracked by git -- a real
deletion to stage, not a typo. `_is_tracked()` (a `git ls-files
--error-unmatch` check) distinguishes the two; a genuinely never-tracked
missing path still refuses with the original error.

Extended for TASK-0024.002: `_staged_paths()` (shared by `commit-guard`
and `stage`'s self-verification) now reads `git diff --cached --name-only
--no-renames`. Without `--no-renames`, whether a renamed path collapsed to
one entry or split into two (old removed, new added) depended on git's
own content-similarity threshold -- reproduced live: a trivial rename
reported one path, the identical rename plus a large-enough content edit
(e.g. `move`'s own Status-line rewrite plus a big `## Done` section)
reported two, with nothing in the `--expect` contract explaining which to
expect. The rule is now fixed and unconditional: a rename always counts
as two entries, list both.

Extended for TASK-0356: two independent defects in the documented
sequence, both reproduced live. (1) `--expect-empty` is unpassable
immediately after `move`/`resolve`, which legitimately leaves its own
rename staged -- and closing a task then committing it is the ordinary
order of work, not an edge case. `--expect-empty` remains correct for
what it actually asserts (nothing staged yet) and is now documented as
valid *only* for a true from-scratch commit; the revised recommended
sequence for the ordinary "I already ran `move`" case skips straight to
`stage --expect <paths, including that rename>`, whose own
self-verification (unchanged) gives the identical contamination check
one step later, never a weaker one. (2) The two-step
`commit-guard --expect ... -> git commit` boundary was routinely joined
with `| tail -1 && ...` to keep output short -- with `pipefail` off (this
shell's default), `&&` after a pipe tests the pipe's last command, not
the guard, so a *failing* guard's chain proceeded to commit anyway. Real
incident: this defect swept another thread's staged rename into an
unrelated commit, twice in one week, including once inside the commit
that filed this very task. `commit-guard --expect ... --commit
--message-file PATH` closes this by fusing check and action into one
process -- no shell step exists between them for that idiom to attach to.
Because that internal `git commit` call is a subprocess of claim.py's own
process, invisible to `git_commit_guard_hook.py`'s PreToolUse match (which
only inspects the one literal Bash command the harness matched, never a
child process it spawns), `--commit` independently re-verifies GIT-COMMIT
session identity in-process (`verify_git_commit_session()`) before
committing -- otherwise this path would have silently reopened exactly
the gap TASK-0042 closed, for itself alone. Old two-step usage
(`commit-guard --expect ...` with no `--commit`) is unchanged and still
supported for anything that wants the check without the action.

Extended for TASK-0061: `add <TASK-ID> <path> --purpose TEXT` (or
`--from-file <manifest.json>` for several files at once) stages a path
via plain `git add` and permanently appends one dated line -- `- [<ts>]
<path> -- <purpose>` -- to the claiming task's own `## Staged Files`
section (created just before `## Done` if absent), so a reviewer can
check what a task actually staged against what its own file says, without
trusting after-the-fact Done-section prose. Unscoped by directory,
deliberately unlike `stage` (TASK-0029): `stage`'s `.ai/`/`.claude/`
restriction exists because an unattributed bulk `git add` wrapper on
claim.py's own blanket whitelist would let any thread silently stage
anything; `add` can't be used unattributed at all (`--purpose` or a
manifest entry's `purpose` is mandatory), so the safety property here is
attribution, not a path prefix. Does not touch `stage`, `commit-guard`,
`move`, `sync`, or the `GIT-COMMIT` gate -- `add` only changes what gets
staged and annotated; a thread still runs the full claim -> stage/add ->
commit-guard --commit -> release sequence to actually commit.

No third-party dependencies -- stdlib only.

Usage:
    claim.py claim        TASK-0024 "Toolsmith (this thread)" [--reason TEXT] [--force] [--note TEXT]
    claim.py claim        GIT-COMMIT "Toolsmith (this thread)" [--force --reason TEXT --hitl-override]
    claim.py reserve-next --as "Toolsmith (this thread)" [--note TEXT] [--dry-run] [--quiet]
    claim.py release      TASK-0024 [--claimant TEXT] [--strict]
    claim.py status       [TASK-0024 | GIT-COMMIT | SCQ-0001]
    claim.py sync         [--dry-run] [--check]
    claim.py commit-guard --expect PATH [PATH ...]
    claim.py commit-guard --expect PATH [PATH ...] --commit --message-file PATH
    claim.py commit-guard --expect-empty
    claim.py move         TASK-0024 IN_PROGRESS --as "Toolsmith (this thread)" [--force --reason TEXT] [--keep-claim]
    claim.py resolve      TASK-0024 done --as "Toolsmith (this thread)" [--note TEXT] [--no-stage]
    claim.py stage        --expect PATH [PATH ...]
    claim.py add          TASK-0024 path/to/file --purpose "why this is staged"
    claim.py add          TASK-0024 --from-file manifest.json
    claim.py scq-enter    --as "Toolsmith (this thread)" --files PATH [PATH ...] --message TEXT [--message-file PATH]
    claim.py scq-leave    SCQ-0001 --as "Toolsmith (this thread)" [--strict]
"""

import argparse
import contextlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TASKS_DIR = os.path.join(REPO_ROOT, ".ai", "tasks")
LOCKS_DIR = os.path.join(TASKS_DIR, ".locks")
COMMON_MD = os.path.join(REPO_ROOT, ".ai", "COMMON.md")
TASK_STATE_DIRS = ["TODO", "IN_PROGRESS", "DONE"]

TASK_ID_RE = re.compile(r"(\d+)(?:\.(\d+))?")
TASK_ID_ONLY_RE = re.compile(r"^TASK-\d{4}(?:\.\d+)?$")
TABLE_ROW_RE = re.compile(r"^\|\s*TASK-\d{4}(?:\.\d+)?\s*\|")

# TASK-0028: fixed non-task resource ids usable with claim/release/status.
# Kept as a small explicit set, not folded into the general RESOURCE-*
# mechanism below (TASK-0024.001), because GIT-COMMIT carries an extra
# protection ordinary resources don't (--hitl-override gate on a forced
# override, cmd_claim above) -- SPECIAL_RESOURCE_IDS marks "this id needs
# the extra gate", not "this id is the only non-task id that exists."
SPECIAL_RESOURCE_IDS = frozenset(["GIT-COMMIT"])

# TASK-0024.001: general whole-file/arbitrary resource ids -- e.g.
# `claim.py claim RESULTS.md "..."` or `claim.py claim COMMON.md "..."`
# before a risky working-tree-level operation on a shared coordination
# file (the incident this task was filed from: a multi-step git-checkout/
# restore sequence on COMMON.md with no way to signal "hands off" to a
# concurrent thread). Namespaced with a `RESOURCE-` prefix (this task's
# own recommended Open Question resolution) so a resource id can never
# collide with, or be misread as, a real `TASK-XXXX` id -- `is_task_id`
# below stays false for every one of these, exactly like GIT-COMMIT.
RESOURCE_ID_PREFIX = "RESOURCE-"
_RESOURCE_SANITIZE_RE = re.compile(r"[^A-Za-z0-9_.\-]")


def normalize_task_id(raw):
    # type: (str) -> str
    """Accepts TASK-0024, 24, TASK-0026.001, 26.1, GIT-COMMIT, RESULTS.md,
    COMMON.md, or any other non-numeric string, etc.

    Dotted suffixes are the .ai/tasks/README.md subtask convention
    (TASK-XXXX.NNN) for independently claimable slices of a parent task.
    GIT-COMMIT (TASK-0028) is a fixed non-numeric resource id, checked
    before the numeric parsing below. Any other input with no digit in it
    (TASK-0024.001) is treated as a literal whole-file/arbitrary resource
    id instead of an error -- sanitized and namespaced under
    `RESOURCE-` so it can never collide with a real TASK-XXXX id. A
    string that DOES contain a digit (e.g. "26" or embedded in a longer
    non-task string) still resolves as a TASK id via the numeric path
    below, unchanged from before this task -- only genuinely digit-free
    input takes the new resource-id path.
    """
    upper = raw.strip().upper()
    if upper in SPECIAL_RESOURCE_IDS:
        return upper
    match = TASK_ID_RE.search(raw)
    if match:
        main = "TASK-%04d" % int(match.group(1))
        sub = match.group(2)
        return main if sub is None else "%s.%03d" % (main, int(sub))
    sanitized = _RESOURCE_SANITIZE_RE.sub("_", raw.strip())
    if not sanitized:
        raise SystemExit("error: could not find a task number or a usable resource id in %r" % raw)
    return RESOURCE_ID_PREFIX + sanitized.upper()


def is_task_id(resource_id):
    # type: (str) -> bool
    """True for TASK-XXXX[.NNN] ids, False for special/general resources
    like GIT-COMMIT or RESOURCE-COMMON.MD."""
    return bool(TASK_ID_ONLY_RE.match(resource_id))


def lock_path(task_id):
    # type: (str) -> str
    return os.path.join(LOCKS_DIR, task_id + ".lock")


def now_str():
    # type: () -> str
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def session_id():
    # type: () -> Optional[str]
    """The calling Claude Code session's own id, read from the environment
    -- never a CLI argument, so a caller cannot type an arbitrary value for
    "who is claiming this" (TASK-0042's own Open Question: labels are
    free-text and spoofable, this is not). `claimant` stays the free-text
    human/HITL-facing label ("what role is this" -- Implementer A,
    Architect, ...); `session_id` is the machine-facing identity ("which
    exact running session, precisely" -- what the PreToolUse hook checks
    a commit attempt against). None outside a Claude Code session (e.g. a
    human running claim.py by hand at a terminal) -- callers must treat
    that as "identity unverifiable", not as an identity of its own."""
    return os.environ.get("CLAUDE_CODE_SESSION_ID")


def _short_sid(lock):
    # type: (dict) -> str
    """Display form of a lock's recorded session_id: first 8 chars, or an
    explicit marker when absent -- absent means either a lock written
    before this field existed, or one claimed outside a Claude Code
    session (a human running claim.py by hand). Never fabricate a value;
    callers (including the PreToolUse hook) must treat "no-session-id" as
    unverifiable identity, not as a wildcard match."""
    sid = lock.get("session_id")
    return (sid[:8] + "...") if sid else "no-session-id"


def read_lock(task_id):
    # type: (str) -> Optional[dict]
    path = lock_path(task_id)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def verify_git_commit_session():
    # type: () -> Optional[str]
    """None if GIT-COMMIT is validly claimed by this exact running session;
    otherwise a human-readable reason it is not.

    TASK-0356: `commit-guard --commit` (below) runs `git commit` itself,
    as a subprocess of claim.py's own process -- invisible to
    `git_commit_guard_hook.py`'s PreToolUse check, which only ever sees
    the literal Bash tool_input.command text of the ONE call the harness
    matched against (`\\bgit\\s+(commit|push)`), never a child process an
    allowed call goes on to spawn. That hook cannot gate this path no
    matter how it's invoked -- so this path must independently re-verify
    the identical identity rule in-process, not rely on the hook to catch
    it externally. Deliberately mirrors the hook's own three checks
    (lock exists / session_id recorded on both sides / session_ids match)
    rather than being a looser approximation of them -- same fail-closed
    posture, on purpose: a same-invariant check that's weaker on this one
    call path would be exactly the kind of "looks enforced, isn't"
    regression this task exists to close. Not called *by* the hook itself
    (kept separate rather than refactored to share one function across
    both) -- the hook is a small, already-incident-tested, independently
    reviewable file; duplicating three straightforward comparisons here
    is a smaller risk than touching it."""
    lock = read_lock("GIT-COMMIT")
    if lock is None:
        return (
            "GIT-COMMIT is not currently claimed. Run `python3 "
            ".ai/tools/claim.py claim GIT-COMMIT \"<label>\"` first."
        )
    held_sid = lock.get("session_id")
    caller_sid = session_id()
    if not held_sid or not caller_sid:
        return (
            "GIT-COMMIT is claimed by %r, but its recorded session_id is "
            "missing (an old lock, or one claimed outside a Claude Code "
            "session) -- identity cannot be verified, so this is denied "
            "rather than assumed safe. Release and re-claim to refresh "
            "the lock's session_id, then retry." % lock.get("claimant")
        )
    if held_sid != caller_sid:
        return (
            "GIT-COMMIT is claimed by %r [session %s...], not this "
            "session [%s...]. If that other claim is stale, release it "
            "explicitly (`claim.py release GIT-COMMIT`) or override with "
            "`claim.py claim GIT-COMMIT ... --force --reason ... "
            "--hitl-override` -- only with an explicit human instruction "
            "in the current conversation to do so, never on an agent's "
            "own judgment."
            % (lock.get("claimant"), held_sid[:8], caller_sid[:8])
        )
    return None


def disk_task_ids():
    # type: () -> Dict[str, str]
    """Map TASK-XXXX -> relative path, scanned from TODO/IN_PROGRESS/DONE."""
    found = {}
    for state in TASK_STATE_DIRS:
        d = os.path.join(TASKS_DIR, state)
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if name.startswith("TASK-") and name.endswith(".md"):
                task_id = name.split("-", 2)
                task_id = "TASK-" + task_id[1]
                found[task_id] = os.path.join(".ai", "tasks", state, name)
    return found


def find_task_file(task_id):
    # type: (str) -> tuple
    """Locate task_id's file across TODO/IN_PROGRESS/DONE.

    Returns (state, filename). Raises SystemExit if zero or more than one
    match is found -- a duplicate is real on-disk drift, not something to
    silently pick one of.
    """
    matches = []
    for state in TASK_STATE_DIRS:
        d = os.path.join(TASKS_DIR, state)
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if name.startswith(task_id + "-") and name.endswith(".md"):
                matches.append((state, name))
    if not matches:
        raise SystemExit(
            "error: no task file found for %s under TODO/IN_PROGRESS/DONE" % task_id
        )
    if len(matches) > 1:
        raise SystemExit(
            "error: %s has more than one task file on disk (%s) -- resolve "
            "this drift manually before moving"
            % (task_id, ", ".join("%s/%s" % m for m in matches))
        )
    return matches[0]


# ---------------------------------------------------------------- claim ----

def _content_sha256_if_file(raw_arg):
    # type: (str) -> Optional[str]
    """TASK-0195: snapshot the claimed file's content at claim time, so
    `check-staleness` can later detect drift. Only applies when the raw
    claim argument (before resource-id sanitizing) is itself a real,
    readable path -- e.g. `claim __WORK_IN_PROGRESS__/RESULTS.md "..."`,
    not the bare symbolic id `RESULTS.md`. Silent no-op (returns None)
    for TASK-XXXX ids, GIT-COMMIT, and any resource id that isn't also a
    literal path -- those simply get no staleness snapshot.
    """
    candidate = raw_arg if os.path.isabs(raw_arg) else os.path.join(REPO_ROOT, raw_arg)
    if not os.path.isfile(candidate):
        return None
    import hashlib
    with open(candidate, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def cmd_claim(args):
    task_id = normalize_task_id(args.task_id)
    os.makedirs(LOCKS_DIR, exist_ok=True)
    path = lock_path(task_id)
    data = {
        "task_id": task_id,
        "claimant": args.claimant,
        "claimed_at": now_str(),
        "note": args.note,
        "session_id": session_id(),
    }
    content_sha256 = _content_sha256_if_file(args.task_id)
    if content_sha256 is not None:
        data["content_sha256"] = content_sha256

    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        existing = read_lock(task_id)
        if not args.force:
            print(
                "error: %s already claimed by %r at %s (use --force --reason "
                "TEXT to override if you judge this stale)"
                % (task_id, existing["claimant"], existing["claimed_at"]),
                file=sys.stderr,
            )
            return 1
        if not args.reason:
            print(
                "error: --force requires --reason (a short note on why the "
                "existing claim is being overridden)",
                file=sys.stderr,
            )
            return 1
        if task_id in SPECIAL_RESOURCE_IDS and not args.hitl_override:
            print(
                "error: overriding %s requires --hitl-override in addition "
                "to --force --reason -- do not pass --hitl-override without "
                "an explicit human instruction, in the current conversation, "
                "to override a held commit lock" % task_id,
                file=sys.stderr,
            )
            return 1
        data["forced_from"] = existing
        data["override_reason"] = args.reason
        data["hitl_override"] = bool(args.hitl_override)
        tmp = path + ".tmp-%d" % os.getpid()
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
        redeemed = _redeem_scq_entry(args.claimant) if task_id == "GIT-COMMIT" else None
        print(
            "claimed %s for %r (overrode previous claim by %r, reason: %s)%s"
            % (
                task_id, args.claimant, existing["claimant"], args.reason,
                ", SCQ entry %s redeemed" % redeemed if redeemed else "",
            )
        )
        return 0
    else:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        redeemed = _redeem_scq_entry(args.claimant) if task_id == "GIT-COMMIT" else None
        print(
            "claimed %s for %r at %s%s"
            % (
                task_id, args.claimant, data["claimed_at"],
                ", SCQ entry %s redeemed" % redeemed if redeemed else "",
            )
        )
        return 0


# --------------------------------------------------------- reserve-next ----

RESERVE_NEXT_MAX_ATTEMPTS = 50


def _highest_numbered(prefix, ids):
    # type: (str, List[str]) -> int
    """Highest `<prefix>-NNNN` main number across an iterable of id-like
    strings (generalized from TASK-0045's TASK-XXXX-only version -- now
    shared by `reserve-next` (prefix "TASK") and `scq-enter` (prefix
    "SCQ"), TASK-0065).

    Dotted subtask ids (TASK-0026.004) contribute their main number (26),
    never their sub number -- a subtask never raises the ceiling a new
    top-level id must clear. SCQ tickets never have a dotted suffix, so
    the same pattern is a no-op restriction for them.
    """
    pat = re.compile(r"^%s-(\d+)(?:\.\d+)?$" % re.escape(prefix))
    highest = 0
    for raw in ids:
        match = pat.match(raw)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest


def _existing_lock_names():
    # type: () -> List[str]
    if not os.path.isdir(LOCKS_DIR):
        return []
    return [name[: -len(".lock")] for name in os.listdir(LOCKS_DIR) if name.endswith(".lock")]


def _allocate_numbered_lock(prefix, disk_highest, data_without_id, id_field):
    # type: (str, int, dict, str) -> Optional[str]
    """Atomically allocate the next unused `<prefix>-NNNN` id.

    Generalized TASK-0045 allocator (was TASK-XXXX-only): candidate is
    max(disk_highest, highest existing `<prefix>-NNNN.lock`) + 1, claimed
    via the same O_EXCL primitive `claim` uses, retrying upward on a lost
    race. Writes `data_without_id` plus `{id_field: allocated_id}` to the
    new lock file. Returns the allocated id, or None if
    RESERVE_NEXT_MAX_ATTEMPTS is exhausted (caller reports the error --
    this stays silent so both TASK and SCQ callers can word their own
    message).
    """
    candidate = max(disk_highest, _highest_numbered(prefix, _existing_lock_names())) + 1
    os.makedirs(LOCKS_DIR, exist_ok=True)
    for _ in range(RESERVE_NEXT_MAX_ATTEMPTS):
        new_id = "%s-%04d" % (prefix, candidate)
        path = lock_path(new_id)
        data = dict(data_without_id)
        data[id_field] = new_id
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            candidate += 1
            continue
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        return new_id
    return None


def cmd_reserve_next(args):
    """Atomically hand back a TASK-XXXX id no other thread also holds.

    Fixes the actual race TASK-0045 hit: reading "the highest number" and
    then writing a new task file at highest+1 is a read-then-write race
    with no lock in between -- two threads can read the same snapshot and
    file the same number. This considers both on-disk task files AND
    currently-held locks (a number can be reserved before its task file
    exists), then claims the candidate via the same O_EXCL primitive
    cmd_claim uses, retrying upward on a lost race instead of racing again.
    """
    on_disk_max = _highest_numbered("TASK", disk_task_ids().keys())

    if args.dry_run:
        lock_max = _highest_numbered("TASK", _existing_lock_names())
        candidate = max(on_disk_max, lock_max) + 1
        print(
            "TASK-%04d (preview only -- not reserved; this can go stale if "
            "another thread reserves first. Run without --dry-run to "
            "actually claim it.)" % candidate
        )
        return 0

    task_id = _allocate_numbered_lock(
        "TASK",
        on_disk_max,
        {
            "claimant": args.claimant,
            "claimed_at": now_str(),
            "note": args.note,
            "reserved": True,
            "session_id": session_id(),
        },
        "task_id",
    )
    if task_id is None:
        print(
            "error: could not find an available id after %d attempts -- "
            "something is wrong beyond normal contention" % RESERVE_NEXT_MAX_ATTEMPTS,
            file=sys.stderr,
        )
        return 1
    if args.quiet:
        print(task_id)
    else:
        lock = read_lock(task_id)
        print("reserved %s for %r at %s" % (task_id, args.claimant, lock["claimed_at"]))
    return 0


# -------------------------------------------------------------- release ----

def cmd_release(args):
    task_id = normalize_task_id(args.task_id)
    path = lock_path(task_id)
    if not os.path.exists(path):
        print("%s is already unclaimed" % task_id)
        return 0
    existing = read_lock(task_id)
    if args.claimant and existing.get("claimant") != args.claimant:
        msg = "%s is claimed by %r, not %r" % (task_id, existing["claimant"], args.claimant)
        if args.strict:
            print("error: refusing to release -- " + msg, file=sys.stderr)
            return 1
        print("warning: releasing a claim held by someone else -- " + msg, file=sys.stderr)
    os.remove(path)
    print("released %s (was claimed by %r)" % (task_id, existing["claimant"]))
    return 0


# ------------------------------------------------------- check-staleness ---

def cmd_check_staleness(args):
    # type: (...) -> int
    """TASK-0195. Detects drift on a *claimed* file since the snapshot
    `cmd_claim` recorded -- run it right after claiming (before you start
    editing) to confirm your starting point is clean, the same place in
    the workflow `commit-guard --expect-empty` occupies for GIT-COMMIT.

    Deliberately content-hash-based, not git-ancestry-based: TASK-0195's
    own investigation (replaying the incident that motivated this task,
    RESULTS.md rows 47-53, recovered in 61b8096) found the actual loss was
    a *working-tree* collision between concurrently-active, uncommitted
    edits from separate threads sharing one checkout -- every commit
    involved was, by construction, correctly based on its true immediate
    git parent (a linear rebase-only history can't be "behind" its own
    parent), so a check that compares committed-git ancestry would have
    reported "clean" the whole time and caught nothing. Only a snapshot of
    actual file *content* at claim time, compared against actual content
    right now, would have shown the drift.
    """
    task_id = normalize_task_id(args.path)
    lock = read_lock(task_id)
    if lock is None:
        print("error: %s is not currently claimed -- claim it first, "
              "check-staleness compares against the snapshot taken at "
              "claim time" % task_id, file=sys.stderr)
        return 1
    snapshot = lock.get("content_sha256")
    if snapshot is None:
        print("%s: claimed, but no content snapshot was recorded (the "
              "claim argument wasn't a real path at claim time) -- "
              "nothing to compare" % task_id)
        return 0
    current = _content_sha256_if_file(args.path)
    if current is None:
        print("error: %s no longer resolves to a readable file" % args.path, file=sys.stderr)
        return 1
    if current == snapshot:
        print("%s: no drift since claim (%s) -- safe to proceed"
              % (task_id, lock.get("claimed_at", "?")))
        return 0
    print(
        "STALE: %s has changed on disk since it was claimed at %s -- "
        "if you haven't made your own edit yet, someone/something else "
        "touched this file; diff it and reconcile before editing. If "
        "this is your own in-progress edit, this warning is expected and "
        "not a problem." % (task_id, lock.get("claimed_at", "?")),
        file=sys.stderr,
    )
    return 1


# --------------------------------------------------------------- status ----

def cmd_status(args):
    if args.task_id:
        raw = args.task_id.strip().upper()
        if raw.startswith("SCQ-"):
            # TASK-0065: direct single-ticket view (doubles as "scq-show" --
            # normalize_task_id would otherwise mis-parse "SCQ-0001" as
            # TASK-0001 via its bare-digit search, silently checking the
            # wrong resource, so this is handled before that call.
            data = read_lock(raw)
            if data is None:
                print("%s: no such SCQ entry" % raw)
                return 0
            print(
                "%s: %r entered %s -- files: %s"
                % (raw, data["claimant"], data.get("entered_at", "?"), ", ".join(data.get("files", [])))
            )
            print("message: %s" % data.get("message", ""))
            if data.get("message_body"):
                print("--- prepared message ---")
                print(data["message_body"])
            return 0

        task_id = normalize_task_id(args.task_id)
        lock = read_lock(task_id)
        if lock is None:
            print("%s: unclaimed" % task_id)
        else:
            print(
                "%s: claimed by %r [session %s] at %s"
                % (task_id, lock["claimant"], _short_sid(lock), lock["claimed_at"])
            )
        if task_id == "GIT-COMMIT":
            _print_scq_queue()
        return 0

    os.makedirs(LOCKS_DIR, exist_ok=True)
    lock_ids = sorted(
        name[: -len(".lock")]
        for name in os.listdir(LOCKS_DIR)
        if name.endswith(".lock") and not name.startswith("SCQ-")
    )
    on_disk = disk_task_ids()
    if not lock_ids:
        print("no active claims")
    for task_id in lock_ids:
        lock = read_lock(task_id)
        if is_task_id(task_id):
            dangling = "" if task_id in on_disk else "  [warning: no task file on disk]"
        else:
            dangling = ""  # special resource (e.g. GIT-COMMIT), not a task file
        print(
            "%s: claimed by %r [session %s] at %s%s"
            % (task_id, lock["claimant"], _short_sid(lock), lock["claimed_at"], dangling)
        )
    _print_scq_queue()
    return 0


# ----------------------------------------------------------------- sync ----

@contextlib.contextmanager
def _common_md_lock(timeout=2.0):
    lock_file = COMMON_MD + ".synclock"
    deadline = time.time() + timeout
    while True:
        try:
            fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.close(fd)
            break
        except FileExistsError:
            if time.time() > deadline:
                raise SystemExit(
                    "error: could not acquire COMMON.md sync lock (%s) -- "
                    "another sync is in progress or a stale lock was left "
                    "behind; remove it manually if you've confirmed no other "
                    "sync is running" % lock_file
                )
            time.sleep(0.05)
    try:
        yield
    finally:
        os.remove(lock_file)


def _parse_row(line):
    # type: (str) -> Optional[List[str]]
    if not TABLE_ROW_RE.match(line):
        return None
    parts = line.split("|")
    # leading/trailing '' from the outer pipes
    cols = [c.strip() for c in parts[1:-1]]
    if len(cols) != 9:
        return None
    return cols


def _apply_registry_row_update(lines, task_id, new_status, new_path):
    # type: (object, str, str, str) -> object
    """Pure per-row transform shared by `update_registry_row` (writes the
    live working-tree file) and `_stage_registry_row_only` (applies the
    same single-row edit to an arbitrary baseline, e.g. the index's
    current blob, for surgical staging). Returns (new_lines, changed)."""
    changed = False
    new_lines = []
    for line in lines:
        cols = _parse_row(line)
        if cols is not None and cols[0] == task_id:
            if cols[3] != new_status or cols[8] != new_path:
                cols[3] = new_status
                cols[8] = new_path
                line = "| " + " | ".join(cols) + " |\n"
                changed = True
        new_lines.append(line)
    return new_lines, changed


def update_registry_row(task_id, new_status, new_path):
    # type: (str, str, str) -> bool
    """Rewrite only the Status (index 3) and Path (index 8) cells for
    task_id's row in COMMON.md, via the same targeted per-row replacement
    and .synclock serialization `sync` uses for the claim columns.

    Returns True if a row was found and changed, False otherwise (no row
    for task_id, or the row already matched).
    """
    if not os.path.exists(COMMON_MD):
        return False

    with open(COMMON_MD, "r") as f:
        lines = f.readlines()

    new_lines, changed = _apply_registry_row_update(lines, task_id, new_status, new_path)

    if changed:
        with _common_md_lock():
            with open(COMMON_MD, "w") as f:
                f.writelines(new_lines)
    return changed


def _stage_registry_row_only(task_id, new_status, new_path):
    # type: (str, str, str) -> bool
    """Stage *only* task_id's row change in .ai/COMMON.md, never the whole
    file. A plain `git add .ai/COMMON.md` would sweep in any other
    thread's unrelated unstaged edits sitting in that same shared file --
    confirmed as a real failure mode during TASK-0107's own validation,
    exactly the whole-file collision this scaffold's COMMON.md tooling
    (TASK-0017/0024) exists to avoid. Builds a blob from the index's
    current COMMON.md content with only this one row's cells replaced,
    and stages that blob directly via `update-index --cacheinfo` --
    mirrors the manual surgical-staging technique already used by hand
    for shared-file commits this session. Returns True if a row was
    found and staged, False otherwise (no row for task_id, or unchanged)."""
    common_md_rel = os.path.relpath(COMMON_MD, REPO_ROOT)
    show = subprocess.run(
        ["git", "show", ":%s" % common_md_rel],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if show.returncode != 0:
        return False

    base_lines = show.stdout.splitlines(keepends=True)
    new_lines, changed = _apply_registry_row_update(base_lines, task_id, new_status, new_path)
    if not changed:
        return False

    blob_sha = subprocess.run(
        ["git", "hash-object", "-w", "--path=%s" % common_md_rel, "--stdin"],
        cwd=REPO_ROOT,
        input="".join(new_lines),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    subprocess.run(
        ["git", "update-index", "--cacheinfo", "100644,%s,%s" % (blob_sha, common_md_rel)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return True


def cmd_sync(args):
    if not os.path.exists(COMMON_MD):
        print("error: %s not found" % COMMON_MD, file=sys.stderr)
        return 1

    with open(COMMON_MD, "r") as f:
        lines = f.readlines()

    on_disk = disk_task_ids()
    changed = []
    new_lines = []
    seen_in_table = set()

    for line in lines:
        cols = _parse_row(line)
        if cols is None:
            new_lines.append(line)
            continue
        task_id = cols[0]
        seen_in_table.add(task_id)
        lock = read_lock(task_id)
        new_claimed_by = lock["claimant"] if lock else "—"
        new_claimed_at = lock["claimed_at"] if lock else "—"
        if cols[6] != new_claimed_by or cols[7] != new_claimed_at:
            changed.append((task_id, cols[6], cols[7], new_claimed_by, new_claimed_at))
            cols[6] = new_claimed_by
            cols[7] = new_claimed_at
        new_lines.append("| " + " | ".join(cols) + " |\n")

    missing_from_table = sorted(set(on_disk) - seen_in_table)
    missing_from_disk = sorted(seen_in_table - set(on_disk))

    for task_id, old_by, old_at, new_by, new_at in changed:
        print("%s: Claimed By %r -> %r, Claimed At %r -> %r" % (task_id, old_by, new_by, old_at, new_at))
    if missing_from_table:
        print(
            "warning: task files on disk with no registry row: %s"
            % ", ".join(missing_from_table),
            file=sys.stderr,
        )
    if missing_from_disk:
        print(
            "warning: registry rows with no task file on disk: %s"
            % ", ".join(missing_from_disk),
            file=sys.stderr,
        )

    dirty = bool(changed or missing_from_table or missing_from_disk)

    if args.check:
        return 1 if dirty else 0

    if not changed:
        print("no claim-column changes needed")
        return 0

    if args.dry_run:
        print("(dry run -- not writing %s)" % COMMON_MD)
        return 0

    with _common_md_lock():
        with open(COMMON_MD, "w") as f:
            f.writelines(new_lines)
    print("wrote %s (%d row(s) updated)" % (COMMON_MD, len(changed)))
    return 0


# ----------------------------------------------------------------- move ----

STATE_TO_STATUS = {"TODO": "TODO", "IN_PROGRESS": "In Progress", "DONE": "Done"}
STATUS_LINE_RE = re.compile(r"^- Status:.*$", re.MULTILINE)


def _claim_gate(task_id, claimant, force, reason, verb):
    # type: (str, str, bool, object, str) -> bool
    """Shared claim-mismatch check for move/resolve. Prints and returns
    False on refusal; True to proceed (after printing a warning, if any).
    `verb` ("moving"/"resolving") only affects message wording."""
    lock = read_lock(task_id)
    if lock is not None and lock["claimant"] != claimant:
        if not force:
            print(
                "error: %s already claimed by %r at %s (use --force --reason "
                "TEXT to override if you judge this stale)"
                % (task_id, lock["claimant"], lock["claimed_at"]),
                file=sys.stderr,
            )
            return False
        if not reason:
            print(
                "error: --force requires --reason (a short note on why the "
                "existing claim is being overridden)",
                file=sys.stderr,
            )
            return False
        print(
            "warning: %s %s despite a claim mismatch (held by %r), "
            "reason: %s" % (verb, task_id, lock["claimant"], reason),
            file=sys.stderr,
        )
    elif lock is None:
        print(
            "warning: %s is unclaimed -- proceeding without a claim check"
            % task_id,
            file=sys.stderr,
        )
    return True


def _assert_single_tracked_path(task_id):
    # type: (str) -> Optional[List[str]]
    """TASK-0198: after a `move`/`resolve` transition, verify the
    *currently staged index* would produce exactly one tracked path for
    `task_id` if committed right now -- catches the "duplicate tracked
    file" defect at the point it would be introduced, rather than relying
    on someone noticing a stray `git ls-tree -r HEAD` line later (how both
    known instances, TASK-0189 and TASK-0073, were actually found).

    Reproduction attempted directly before adding this (per this task's
    own "do not fix blind" Constraint): five real variations of a chained
    TODO->IN_PROGRESS->DONE transition (immediate, with a manual content
    edit between hops, with an intervening `git add`, via `move` then
    `resolve`, and a back-and-forth TODO->IN_PROGRESS->TODO->IN_PROGRESS
    ->DONE chain) were each run through this module's own real `move`/
    `resolve` commands and checked with this exact `write-tree`+`ls-tree`
    technique after a real commit -- every one produced a single, clean
    tracked path, no duplicate. This is itself a real finding, not a
    failure to reproduce something simple: it points away from a
    deterministic bug in `_perform_transition`'s own sequential logic and
    toward concurrent-thread index interference (this scaffold's actual
    operating mode -- multiple sessions issuing git commands against the
    same shared repo without a true cross-process index lock beyond
    git's own, which serializes individual commands, not multi-command
    sequences). A single-process script cannot reliably force that race,
    so per this task's own Intent Contract option (b), this check closes
    the gap regardless of the exact trigger, rather than chasing a root
    cause with no guaranteed reproduction.

    `git write-tree` is read-only plumbing -- it writes a tree *object*
    from the current index into the object database and returns its
    hash, touching neither HEAD nor any ref, so this is safe to run
    speculatively without side effects on the repo's actual history.

    Returns `None` if exactly one (or zero, e.g. a `--no-stage`-style
    caller) match is found -- the healthy case. Returns the list of
    matched paths (length >= 2) if the defect is present -- printing is
    the caller's job, so `move`/`resolve` can each phrase the warning in
    their own voice."""
    tree = subprocess.run(
        ["git", "write-tree"], cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if tree.returncode != 0:
        # An unmerged/conflicted index can't produce a tree -- not this
        # check's failure mode to diagnose; skip rather than crash the
        # move/resolve call that already succeeded on disk.
        return None
    out = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", tree.stdout.strip()],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if out.returncode != 0:
        return None
    tasks_prefix = os.path.relpath(TASKS_DIR, REPO_ROOT).replace(os.sep, "/") + "/"
    matches = [
        line for line in out.stdout.splitlines()
        if line.startswith(tasks_prefix)
        and os.path.basename(line).startswith(task_id + "-")
        and line.endswith(".md")
    ]
    return matches if len(matches) > 1 else None


def _perform_transition(task_id, target_state, keep_claim, content_transform):
    # type: (str, str, bool, object) -> object
    """Shared relocate + registry-sync + claim-release logic used by both
    `move` and `resolve`. `content_transform(content, src_path) -> (new_content,
    changed)` is applied to the task file's current content before any
    physical move -- `move` uses it for the Status-line rewrite alone;
    `resolve` folds in the Resolution/Resolution-Note lines too, as one
    read-modify-write. Returns None on a fatal find_task_file error (already
    printed), or a dict with `error` plus enough state for the caller to
    build its own report/staging behavior on top."""
    try:
        current_state, filename = find_task_file(task_id)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return None

    src_path = os.path.join(TASKS_DIR, current_state, filename)
    dst_path = os.path.join(TASKS_DIR, target_state, filename)
    src_rel = os.path.relpath(src_path, REPO_ROOT)
    dst_rel = os.path.relpath(dst_path, REPO_ROOT)

    with open(src_path, "r") as f:
        content = f.read()

    new_content, content_changed = content_transform(content, src_path)
    if content_changed:
        with open(src_path, "w") as f:
            f.write(new_content)

    need_file_move = current_state != target_state
    final_rel = src_rel

    if need_file_move:
        os.makedirs(os.path.join(TASKS_DIR, target_state), exist_ok=True)
        tracked = (
            subprocess.run(
                ["git", "ls-files", "--error-unmatch", src_rel],
                cwd=REPO_ROOT,
                capture_output=True,
            ).returncode
            == 0
        )
        try:
            if tracked:
                subprocess.run(
                    ["git", "mv", src_rel, dst_rel],
                    cwd=REPO_ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            else:
                os.replace(src_path, dst_path)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            print(
                "error: failed to move %s -> %s (%s) -- it may have already "
                "been moved by another thread; re-run status/find before "
                "retrying" % (src_rel, dst_rel, exc),
                file=sys.stderr,
            )
            return {"error": True}
        final_rel = dst_rel

    # `git mv`/a plain rename carries over the index's existing blob for the
    # path rather than re-reading the working tree -- so any content written
    # above or already sitting unstaged on disk before this call (e.g. prior
    # edits the caller made) would otherwise land in the index as stale.
    # Re-add the final path so the staged blob always matches what's
    # actually on disk post-move (mirrors commit-guard's disk-vs-expect
    # verification, per Q-0002).
    final_tracked = (
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", final_rel],
            cwd=REPO_ROOT,
            capture_output=True,
        ).returncode
        == 0
    )
    if final_tracked:
        subprocess.run(
            ["git", "add", final_rel],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    target_status_text = STATE_TO_STATUS[target_state]
    registry_path_cell = "`%s`" % dst_rel.replace(os.sep, "/")
    registry_changed = update_registry_row(task_id, target_status_text, registry_path_cell)

    lock = read_lock(task_id)
    released = False
    if target_state == "DONE" and lock is not None and not keep_claim:
        os.remove(lock_path(task_id))
        released = True

    # TASK-0198: only meaningful when a physical relocation happened --
    # a same-state call (need_file_move False) never touches the file's
    # tracked path at all, nothing to check.
    duplicate_paths = _assert_single_tracked_path(task_id) if need_file_move else None

    return {
        "error": False,
        "src_rel": src_rel,
        "final_rel": final_rel,
        "final_tracked": final_tracked,
        "need_file_move": need_file_move,
        "content_changed": content_changed,
        "registry_changed": registry_changed,
        "registry_path_cell": registry_path_cell,
        "released": released,
        "target_status_text": target_status_text,
        "duplicate_paths": duplicate_paths,
    }


def _warn_if_duplicate_tracked(task_id, duplicate_paths):
    # type: (str, Optional[List[str]]) -> None
    """TASK-0198: print `_assert_single_tracked_path`'s finding loudly --
    a no-op if `duplicate_paths` is `None` (the healthy case). Shared by
    `cmd_move`/`cmd_resolve` so the message and the remediation guidance
    stay in one place rather than drifting between the two callers."""
    if not duplicate_paths:
        return
    print(
        "warning: %s would be tracked at MORE THAN ONE path if committed "
        "right now -- %s. This is TASK-0198's own duplicate-tracking "
        "defect (chained TODO->IN_PROGRESS->DONE-style transitions with "
        "no commit in between); the file move itself succeeded and the "
        "working tree is correct, only the staged index has the extra "
        "entry. Before committing: inspect `git diff --cached "
        "--name-status`, then stage the stale path's deletion explicitly "
        "(`git rm --cached <stale path>` or `.ai/tools/claim.py stage "
        "--expect <stale path> ...` alongside the real change set) -- do "
        "not `git commit` as-is." % (task_id, ", ".join(duplicate_paths)),
        file=sys.stderr,
    )


def cmd_move(args):
    task_id = normalize_task_id(args.task_id)
    if not is_task_id(task_id):
        print(
            "error: move only operates on TASK-XXXX[.NNN] ids, not special "
            "resources like %s" % task_id,
            file=sys.stderr,
        )
        return 1

    target_state = args.target_state
    if not _claim_gate(task_id, args.as_, args.force, args.reason, "moving"):
        return 1

    def _status_only(content, src_path):
        target_status_text = STATE_TO_STATUS[target_state]
        status_match = STATUS_LINE_RE.search(content)
        current_status_text = (
            status_match.group(0)[len("- Status:") :].strip() if status_match else None
        )
        if current_status_text == target_status_text:
            return content, False
        if status_match is None:
            print(
                "warning: no '- Status:' line found in %s -- Status not rewritten"
                % src_path,
                file=sys.stderr,
            )
            return content, False
        return (
            STATUS_LINE_RE.sub("- Status: %s" % target_status_text, content, count=1),
            True,
        )

    result = _perform_transition(task_id, target_state, args.keep_claim, _status_only)
    if result is None or result["error"]:
        return 1

    _warn_if_duplicate_tracked(task_id, result["duplicate_paths"])

    if not result["need_file_move"] and not result["content_changed"] and not result["registry_changed"]:
        print(
            "%s already in %s with Status: %s -- no-op"
            % (task_id, target_state, result["target_status_text"])
        )
    else:
        print(
            "moved %s -> %s (Status: %s)%s%s"
            % (
                task_id,
                target_state,
                result["target_status_text"],
                ", registry updated" if result["registry_changed"] else "",
                ", claim released" if result["released"] else "",
            )
        )
    return 0


# -------------------------------------------------------------- resolve ----

# Mirrors .ai/reference/RESOLUTION_VOCABULARY.md's "Task Resolution Values"
# table exactly -- kept in sync by hand, not parsed from the markdown.
RESOLUTION_VALUES = (
    "done",
    "fixed",
    "wont-do",
    "duplicate",
    "obsolete",
    "not-reproducible",
    "moved",
)
RESOLUTION_LINE_RE = re.compile(r"^- Resolution:.*$", re.MULTILINE)
RESOLUTION_NOTE_LINE_RE = re.compile(r"^- Resolution Note:.*$", re.MULTILINE)


def cmd_resolve(args):
    task_id = normalize_task_id(args.task_id)
    if not is_task_id(task_id):
        print(
            "error: resolve only operates on TASK-XXXX[.NNN] ids, not "
            "special resources like %s" % task_id,
            file=sys.stderr,
        )
        return 1

    if args.resolution not in RESOLUTION_VALUES:
        print(
            "error: %r is not a canonical resolution value -- must be one "
            "of: %s (see .ai/reference/RESOLUTION_VOCABULARY.md)"
            % (args.resolution, ", ".join(RESOLUTION_VALUES)),
            file=sys.stderr,
        )
        return 1

    if not _claim_gate(task_id, args.as_, args.force, args.reason, "resolving"):
        return 1

    def _resolve_content(content, src_path):
        changed = False
        target_status_text = STATE_TO_STATUS["DONE"]
        status_match = STATUS_LINE_RE.search(content)
        current_status_text = (
            status_match.group(0)[len("- Status:") :].strip() if status_match else None
        )
        if current_status_text != target_status_text:
            if status_match is None:
                print(
                    "warning: no '- Status:' line found in %s -- Status not "
                    "rewritten" % src_path,
                    file=sys.stderr,
                )
            else:
                content = STATUS_LINE_RE.sub(
                    "- Status: %s" % target_status_text, content, count=1
                )
                changed = True

        resolution_line = "- Resolution: %s" % args.resolution
        res_match = RESOLUTION_LINE_RE.search(content)
        if res_match is None:
            status_match = STATUS_LINE_RE.search(content)
            if status_match is None:
                print(
                    "warning: no '- Status:' line found in %s -- Resolution "
                    "line not inserted, append it by hand" % src_path,
                    file=sys.stderr,
                )
            else:
                insert_at = status_match.end()
                content = content[:insert_at] + "\n" + resolution_line + content[insert_at:]
                changed = True
        elif res_match.group(0) != resolution_line:
            content = RESOLUTION_LINE_RE.sub(resolution_line, content, count=1)
            changed = True

        if args.note:
            note_line = "- Resolution Note: %s" % args.note
            note_match = RESOLUTION_NOTE_LINE_RE.search(content)
            if note_match is None:
                res_match = RESOLUTION_LINE_RE.search(content)
                if res_match is not None:
                    insert_at = res_match.end()
                    content = content[:insert_at] + "\n" + note_line + content[insert_at:]
                    changed = True
            elif note_match.group(0) != note_line:
                content = RESOLUTION_NOTE_LINE_RE.sub(note_line, content, count=1)
                changed = True

        return content, changed

    result = _perform_transition(task_id, "DONE", args.keep_claim, _resolve_content)
    if result is None or result["error"]:
        return 1

    if args.no_stage:
        # `git mv` stages both sides of the rename (removes src_rel, adds
        # final_rel) -- resetting only final_rel would leave src_rel's
        # deletion still staged. Reset both unconditionally; when no move
        # happened, src_rel == final_rel and this is a harmless no-op repeat.
        reset_paths = sorted(set([result["src_rel"], result["final_rel"]]))
        subprocess.run(
            ["git", "reset", "--"] + reset_paths,
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        stage_note = ", not staged (--no-stage)"
    else:
        if result["registry_changed"]:
            _stage_registry_row_only(
                task_id, result["target_status_text"], result["registry_path_cell"]
            )
        stage_note = ", staged"
        # TASK-0198: the --no-stage branch above already reset both sides
        # of any rename, so a duplicate this check would have caught is
        # moot there -- only meaningful once something is actually staged.
        _warn_if_duplicate_tracked(task_id, result["duplicate_paths"])

    print(
        "resolved %s -> DONE (Resolution: %s)%s%s%s"
        % (
            task_id,
            args.resolution,
            ", registry updated" if result["registry_changed"] else "",
            stage_note,
            ", claim released" if result["released"] else "",
        )
    )
    return 0


# --------------------------------------------------------- commit-guard ----

def _staged_paths():
    # type: () -> set
    """TASK-0024.002: `--no-renames` is load-bearing, not cosmetic. Without
    it, `git diff --cached --name-only` collapses a renamed path to just
    the new name ONLY when the old/new content stays above git's
    similarity threshold -- reproduced live (2026-07-09 incident, and
    again in this task's own scratch-repo validation): a trivial rename
    reports one path, the identical rename plus a large-enough content
    edit reports two, with nothing about the caller's `--expect` list
    explaining which to expect. `--no-renames` makes every rename report
    as a plain delete+add (old path removed, new path added) unconditionally,
    so "list both paths for a rename" becomes a fixed rule instead of a
    threshold a caller has to discover by having a call fail."""
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--no-renames"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return set(line for line in proc.stdout.splitlines() if line)


def _compare_staged(expected):
    # type: (set) -> tuple
    """Compare the actually-staged index against an expected path set.

    Returns (unexpected, missing) -- both sorted lists. Shared by
    commit-guard and stage's self-verification step so the two never
    drift out of sync with each other.
    """
    staged = _staged_paths()
    return sorted(staged - expected), sorted(expected - staged)


def cmd_commit_guard(args):
    expected = set() if args.expect_empty else set(args.expect)
    unexpected, missing = _compare_staged(expected)

    if unexpected:
        print(
            "error: staged index contains paths not in --expect%s: %s"
            % ("-empty" if args.expect_empty else "", ", ".join(unexpected)),
            file=sys.stderr,
        )
        return 1
    if missing:
        print(
            "error: --expect listed paths that are not actually staged: %s"
            % ", ".join(missing),
            file=sys.stderr,
        )
        return 1

    if not args.commit:
        if args.expect_empty:
            print("ok: staged index is empty")
        else:
            print("ok: staged index exactly matches --expect (%d path(s))" % len(expected))
        return 0

    # TASK-0356: `--commit` fuses this check with the actual `git commit`
    # into one atomic call. Real incident this closes: the documented
    # sequence's separate check-then-commit shell steps were chained as
    # `commit-guard --expect ... | tail -1 && git commit ...` -- with
    # `pipefail` off (this shell's default; verified `false | tail -1`
    # exits 0), `&&` tests `tail`'s exit status, not the guard's, so a
    # failing guard's own `&&` chain proceeded to commit anyway. Twice.
    # There is no shell step here for that idiom to attach to: this
    # process either calls `git commit` itself, having just verified the
    # check in the same call, or it doesn't call it at all.
    if args.expect_empty:
        print(
            "error: --commit cannot be combined with --expect-empty -- "
            "there is nothing to commit yet; stage first, then re-run "
            "with --expect --commit",
            file=sys.stderr,
        )
        return 1
    if not args.message_file:
        print("error: --commit requires --message-file PATH", file=sys.stderr)
        return 1
    if not os.path.exists(args.message_file):
        print(
            "error: --message-file %s does not exist" % args.message_file,
            file=sys.stderr,
        )
        return 1

    # Re-verify GIT-COMMIT identity in-process: the `git commit` call two
    # lines down is a subprocess of THIS process, invisible to
    # `git_commit_guard_hook.py`'s PreToolUse check (that hook only ever
    # sees the literal Bash command the harness matched -- this one,
    # `claim.py commit-guard ...`, not the child process it goes on to
    # spawn). Skipping this would silently reopen exactly the gap
    # TASK-0042 closed, for this one call path only.
    reason = verify_git_commit_session()
    if reason is not None:
        print("error: refusing to commit -- %s" % reason, file=sys.stderr)
        return 1

    proc = subprocess.run(["git", "commit", "-F", args.message_file], cwd=REPO_ROOT)
    if proc.returncode != 0:
        print(
            "error: git commit exited %d -- staged index is untouched, "
            "nothing was lost" % proc.returncode,
            file=sys.stderr,
        )
        return proc.returncode

    print(
        "ok: staged index exactly matched --expect (%d path(s)), committed"
        % len(expected)
    )
    return 0


# --------------------------------------------------------------- stage ----

STAGE_ALLOWED_PREFIXES = (".ai", ".claude")


def _in_scope(rel_path):
    # type: (str) -> bool
    """True if rel_path normalizes to somewhere under .ai/ or .claude/.

    TASK-0029: this is the load-bearing check that keeps `stage` from
    quietly becoming an unconstrained `git add` wrapper riding on
    claim.py's existing blanket allowlist. Normalizes first so a
    traversal like ".ai/../backend/x.py" (which collapses to
    "backend/x.py") is rejected, not silently allowed.
    """
    norm = os.path.normpath(rel_path)
    if os.path.isabs(norm) or norm == os.pardir or norm.startswith(os.pardir + os.sep):
        return False
    first = norm.split(os.sep, 1)[0]
    return first in STAGE_ALLOWED_PREFIXES


def _is_tracked(rel_path):
    # type: (str) -> bool
    """True if rel_path exists at HEAD, regardless of whether it currently
    exists on disk or is currently staged.

    Checks HEAD (`git cat-file -e HEAD:<path>`), not the index (`git
    ls-files`) -- found the difference matters in real use, same session:
    once a deletion is staged (e.g. a first `stage --expect` call in a
    multi-file commit-prep sequence), `git ls-files` no longer lists that
    path at all, so a second `--expect` call including the same path
    (needed because `stage`'s self-verification requires the *full*
    intended set every time) would wrongly read it as untracked/typo'd.
    HEAD does not move until the actual commit, so it stays correct
    across that whole staged-but-uncommitted window -- unlike
    `_perform_transition`'s own `git ls-files --error-unmatch` check
    (TASK-0027/TASK-0029), which intentionally asks "is this staged right
    now" for a different purpose (deciding `git mv` vs. a plain filesystem
    move on a file that, at that point in `move`'s flow, has not yet had
    anything staged for it this session)."""
    return (
        subprocess.run(
            ["git", "cat-file", "-e", "HEAD:%s" % rel_path],
            cwd=REPO_ROOT,
            capture_output=True,
        ).returncode
        == 0
    )


def cmd_stage(args):
    expect = list(args.expect)

    if read_lock("GIT-COMMIT") is None:
        print(
            "error: GIT-COMMIT is not currently claimed -- run `claim.py "
            "claim GIT-COMMIT <claimant>` before staging (stage is the "
            "deliberate pre-commit step: claim -> stage --expect <paths, "
            "incl. any pending move/resolve rename> -> commit-guard "
            "--expect <same paths> --commit --message-file PATH -> release "
            "-- only prefix with `commit-guard --expect-empty` if nothing "
            "has been staged yet this session, TASK-0356). Real incident, "
            "2026-07-24: a thread staged files via "
            "previously checked for that.",
            file=sys.stderr,
        )
        return 1

    out_of_scope = [p for p in expect if not _in_scope(p)]
    if out_of_scope:
        print(
            "error: stage only accepts paths under .ai/ or .claude/; "
            "out-of-scope: %s -- use a normal `git add` for these (it will "
            "correctly prompt)" % ", ".join(out_of_scope),
            file=sys.stderr,
        )
        return 1

    # TASK-0197: absent-from-disk splits into two different cases that
    # os.path.exists() alone cannot tell apart -- a typo (never tracked,
    # still an error) vs. a legitimate deletion of a previously-tracked
    # file (allowed through to `git add`, which stages removals for a
    # tracked-but-missing pathspec since Git 2.0 -- no `git rm` needed as
    # a separate call). Real incident, 2026-08-03: cleaning up a duplicate
    # task file (tracked in two locations after another thread's commit)
    # had no whitelisted path forward, forcing a bare `git add` outside
    # this tool entirely.
    missing_on_disk = [p for p in expect if not os.path.exists(os.path.join(REPO_ROOT, p))]
    untracked_missing = [p for p in missing_on_disk if not _is_tracked(p)]
    if untracked_missing:
        print(
            "error: --expect names paths that do not exist on disk and are "
            "not tracked by git (check for a typo): %s"
            % ", ".join(untracked_missing),
            file=sys.stderr,
        )
        return 1

    # TASK-0197: a path already fully staged as a DELETION (absent from
    # both the index and the working tree -- e.g. staged by an earlier
    # `stage` call in the same commit-prep sequence) has nothing left for
    # `git add` to do, and a bare `git add` on it errors ("pathspec ...
    # did not match any files", real incident). Skip only that exact
    # case. TASK-0223: a path that IS present on disk must always be
    # re-added, even if some earlier call (this one or `move`'s own
    # internal `git mv`) already staged an *older* version of it --
    # `git add` on a present, tracked file is always safe/idempotent, and
    # skipping it here silently left a later edit un-staged: `stage`'s own
    # self-verification below (and a separate `commit-guard --expect`
    # right before commit) both check only the *path set*, not staged
    # *content*, so neither ever caught the drop. Only exclude a path
    # when it is BOTH missing on disk AND already reflected in the index
    # (the TASK-0197 case) -- everything else always gets re-added.
    still_missing = set(missing_on_disk) & _staged_paths()
    to_add = [p for p in expect if p not in still_missing]
    if to_add:
        subprocess.run(["git", "add", "--"] + to_add, cwd=REPO_ROOT, check=True)

    unexpected, missing = _compare_staged(set(expect))
    if unexpected or missing:
        print(
            "error: staged index does not match --expect after staging -- "
            "unexpected: %s; missing: %s"
            % (", ".join(unexpected) or "none", ", ".join(missing) or "none"),
            file=sys.stderr,
        )
        return 1

    print("staged exactly %d path(s), self-verified clean" % len(expect))
    return 0


# -------------------------------------------------------------------- add --
# TASK-0061: attributed stage-and-annotate, any path -- complementary to
# `stage` (bulk, .ai/.claude-scoped, exact-match self-verify), not a
# replacement. `add` is incremental/per-file, used as work progresses, and
# is unscoped by directory because its safety property is *attribution*
# (every call ties a path to a real task and a required --purpose,
# permanently recorded in that task's own file), not a path prefix.

_STAGED_FILES_HEADING = "## Staged Files"
_STAGED_FILES_HEADING_RE = re.compile(r"^## Staged Files[ \t]*$", re.MULTILINE)
_ANY_H1_H2_RE = re.compile(r"^#{1,2} ", re.MULTILINE)


def _append_to_staged_files_section(content, entry_line):
    # type: (str, str) -> str
    """Targeted read-modify-write, same discipline `_perform_transition`'s
    Status-line rewrite uses -- never a whole-file rewrite. Creates the
    section (right before `## Done` if that heading exists, matching
    every task file's own convention of `## Done` as the final section;
    otherwise at end of file) if absent; appends one line to it either way."""
    m = _STAGED_FILES_HEADING_RE.search(content)
    if m is None:
        done_m = re.search(r"^## Done[ \t]*$", content, re.MULTILINE)
        section = _STAGED_FILES_HEADING + "\n\n" + entry_line + "\n\n"
        if done_m is None:
            return content.rstrip("\n") + "\n\n" + section
        return content[: done_m.start()] + section + content[done_m.start() :]

    # Section exists -- append at its end (just before the next `#`/`##`
    # heading, or EOF), not at its start, so entries stay in call order.
    next_h = _ANY_H1_H2_RE.search(content, m.end())
    section_end = next_h.start() if next_h else len(content)
    body = content[m.end() : section_end].rstrip("\n")  # keeps its own
    # leading blank line intact; only trailing newlines are trimmed here,
    # replaced below with an exact, known amount.
    new_body = body + "\n" + entry_line + "\n"
    if next_h is not None:
        new_body += "\n"
    return content[: m.end()] + new_body + content[section_end:]


def _parse_manifest_entries(data):
    # type: (object) -> List[tuple]
    """Both accepted manifest shapes -> a flat, ordered [(file, purpose)]
    list. Raises ValueError (never a raw traceback) naming the exact
    problem -- the caller must treat any error here as all-or-nothing,
    nothing staged yet at this point."""
    entries = []
    if isinstance(data, list):
        for i, item in enumerate(data):
            if not isinstance(item, dict) or "file" not in item or "purpose" not in item:
                raise ValueError(
                    "array-form manifest entry %d must be an object with "
                    "'file' and 'purpose' keys, got %r" % (i, item)
                )
            entries.append((item["file"], item["purpose"]))
    elif isinstance(data, dict):
        shared_purpose = data.get("purpose")
        files = data.get("files")
        if not isinstance(files, list):
            raise ValueError("object-form manifest must have a 'files' array")
        for i, item in enumerate(files):
            if isinstance(item, str):
                path, purpose = item, shared_purpose
            elif isinstance(item, dict):
                if "file" not in item:
                    raise ValueError("files[%d] object entry missing 'file'" % i)
                path, purpose = item["file"], item.get("purpose", shared_purpose)
            else:
                raise ValueError(
                    "files[%d] must be a path string or an object, got %r" % (i, item)
                )
            if purpose is None:
                raise ValueError(
                    "files[%d] (%r) has no purpose and the manifest has no "
                    "top-level 'purpose' to fall back to" % (i, path)
                )
            entries.append((path, purpose))
    else:
        raise ValueError("manifest JSON must be an array or an object, got %s" % type(data).__name__)
    if not entries:
        raise ValueError("manifest contains no file entries")
    return entries


def _resolve_add_entries(args):
    # type: (object) -> List[tuple]
    """CLI args -> a normalized, repo-relative [(path, purpose)] list.
    Raises ValueError for any usage/parse problem -- caller prints it and
    returns 1 before touching git or the task file at all."""
    if args.from_file:
        if args.path or args.purpose:
            raise ValueError("--from-file is mutually exclusive with a positional PATH/--purpose")
        if not os.path.exists(args.from_file):
            raise ValueError("--from-file %s does not exist" % args.from_file)
        with open(args.from_file, "r") as f:
            raw = f.read()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("malformed manifest JSON in %s: %s" % (args.from_file, exc))
        entries = _parse_manifest_entries(data)
    else:
        if not args.path or not args.purpose:
            raise ValueError("single-file form requires both PATH and --purpose (or use --from-file)")
        entries = [(args.path, args.purpose)]

    normalized = []
    for p, purpose in entries:
        abs_p = p if os.path.isabs(p) else os.path.join(REPO_ROOT, p)
        rel = os.path.relpath(abs_p, REPO_ROOT)
        if rel == os.pardir or rel.startswith(os.pardir + os.sep):
            raise ValueError("path %r resolves outside the repository" % p)
        normalized.append((rel.replace(os.sep, "/"), purpose))
    return normalized


def cmd_add(args):
    task_id = normalize_task_id(args.task_id)
    if not is_task_id(task_id):
        print("error: %r is not a TASK-XXXX id" % args.task_id, file=sys.stderr)
        return 1

    try:
        entries = _resolve_add_entries(args)
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1

    try:
        state, filename = find_task_file(task_id)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 1
    task_path = os.path.join(TASKS_DIR, state, filename)
    task_rel = os.path.relpath(task_path, REPO_ROOT).replace(os.sep, "/")

    # All-or-nothing (Planned Validation #4): every target must exist on
    # disk before `git add` touches any of them.
    missing = [p for p, _ in entries if not os.path.exists(os.path.join(REPO_ROOT, p))]
    if missing:
        print(
            "error: path(s) not found on disk, nothing staged: %s" % ", ".join(missing),
            file=sys.stderr,
        )
        return 1

    rel_paths = [p for p, _ in entries]
    subprocess.run(["git", "add", "--"] + rel_paths, cwd=REPO_ROOT, check=True)

    # Lighter self-check than `stage`'s exact-match assertion (this task's
    # own In Scope wording): confirm each just-added path now actually
    # appears staged -- catches a silent no-op (e.g. gitignored), never
    # asserts the whole index matches only these paths.
    staged = _staged_paths()
    not_staged = [p for p in rel_paths if p not in staged]
    if not_staged:
        print(
            "error: git add reported no error but these path(s) are not in "
            "the staged index: %s -- either gitignored, or the file is "
            "already identical to HEAD (nothing to stage; if you only "
            "want to attribute an already-correct file to this task, "
            "edit its own '## Staged Files' section by hand instead of "
            "running `add`)" % ", ".join(not_staged),
            file=sys.stderr,
        )
        return 1

    with open(task_path, "r") as f:
        content = f.read()
    ts = now_str()
    for p, purpose in entries:
        content = _append_to_staged_files_section(
            content, "- [%s] `%s` -- %s" % (ts, p, purpose)
        )
    with open(task_path, "w") as f:
        f.write(content)
    subprocess.run(["git", "add", "--", task_rel], cwd=REPO_ROOT, check=True)

    print(
        "staged %d file(s) under %s, annotated in %s"
        % (len(entries), task_id, task_rel)
    )
    return 0


# ------------------------------------------------------------------ scq ----
# TASK-0065: Stage-Commit-Queue. Entries are SCQ-XXXX.lock files under the
# same LOCKS_DIR as task/GIT-COMMIT locks, reusing the existing
# `.ai/tasks/.locks/*.lock` .gitignore glob as-is -- no new ignore rule.
# One file per entry (never a single shared queue file) so concurrent
# entrants can't race on the same write, the same reasoning this scaffold
# already applied to .ai/COMMON.md (see Q-0002, TASK-0107's own validation).

def _scq_lock_names():
    # type: () -> List[str]
    """Sorted `SCQ-XXXX.lock` filenames currently in LOCKS_DIR (ticket order)."""
    if not os.path.isdir(LOCKS_DIR):
        return []
    return sorted(name for name in os.listdir(LOCKS_DIR) if name.startswith("SCQ-") and name.endswith(".lock"))


def _scq_entries():
    # type: () -> List[dict]
    """All current SCQ entries, ordered by ticket number ascending (FIFO)."""
    entries = []
    for name in _scq_lock_names():
        data = read_lock(name[: -len(".lock")])
        if data is not None:
            entries.append(data)
    return entries


def _files_preview(files, limit=5):
    # type: (List[str], int) -> str
    if len(files) <= limit:
        return ", ".join(files)
    return ", ".join(files[:limit]) + " (+%d more)" % (len(files) - limit)


def _print_scq_queue():
    entries = _scq_entries()
    if not entries:
        return
    print("Stage-Commit-Queue (SCQ):")
    for e in entries:
        print(
            "  %s: %r entered %s -- files: %s -- %s"
            % (
                e.get("ticket", "?"),
                e.get("claimant", "?"),
                e.get("entered_at", "?"),
                _files_preview(e.get("files", [])),
                e.get("message", ""),
            )
        )


def _redeem_scq_entry(claimant):
    # type: (str) -> Optional[str]
    """Remove claimant's own SCQ entry, if any, after it successfully
    claims GIT-COMMIT. The entry's purpose (signal intent to commit soon)
    is fulfilled once the lock is actually held, whether or not the
    claimant was first in the queue -- this doesn't enforce turn order,
    it just clears a redeemed entry. Returns the removed ticket, or None.
    """
    for name in _scq_lock_names():
        ticket = name[: -len(".lock")]
        data = read_lock(ticket)
        if data is not None and data.get("claimant") == claimant:
            os.remove(lock_path(ticket))
            return ticket
    return None


def cmd_scq_enter(args):
    message_body = None
    if args.message_file:
        if not os.path.exists(args.message_file):
            print("error: --message-file %s does not exist" % args.message_file, file=sys.stderr)
            return 1
        with open(args.message_file, "r") as f:
            message_body = f.read()

    # Re-entering as the same claimant updates that claimant's existing
    # ticket in place rather than allocating a second one.
    for name in _scq_lock_names():
        ticket = name[: -len(".lock")]
        existing = read_lock(ticket)
        if existing is not None and existing.get("claimant") == args.as_:
            data = {
                "ticket": ticket,
                "claimant": args.as_,
                "entered_at": existing.get("entered_at", now_str()),
                "updated_at": now_str(),
                "files": args.files,
                "message": args.message,
                "message_body": message_body,
                "session_id": session_id(),
            }
            with open(lock_path(ticket), "w") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
            print("updated %s for %r (%d file(s))" % (ticket, args.as_, len(args.files)))
            return 0

    ticket = _allocate_numbered_lock(
        "SCQ",
        0,
        {
            "claimant": args.as_,
            "entered_at": now_str(),
            "files": args.files,
            "message": args.message,
            "message_body": message_body,
            "session_id": session_id(),
        },
        "ticket",
    )
    if ticket is None:
        print(
            "error: could not find an available SCQ ticket after %d attempts"
            % RESERVE_NEXT_MAX_ATTEMPTS,
            file=sys.stderr,
        )
        return 1
    print("entered %s for %r (%d file(s))" % (ticket, args.as_, len(args.files)))
    return 0


def cmd_scq_leave(args):
    ticket = args.ticket.strip().upper()
    if not ticket.startswith("SCQ-"):
        print("error: scq-leave only operates on SCQ-XXXX tickets, not %r" % ticket, file=sys.stderr)
        return 1
    path = lock_path(ticket)
    if not os.path.exists(path):
        print("%s is already gone" % ticket)
        return 0
    existing = read_lock(ticket)
    if existing.get("claimant") != args.as_:
        msg = "%s is claimed by %r, not %r" % (ticket, existing["claimant"], args.as_)
        if args.strict:
            print("error: refusing to remove -- " + msg, file=sys.stderr)
            return 1
        print("warning: removing an entry held by someone else -- " + msg, file=sys.stderr)
    os.remove(path)
    print("removed %s (was %r)" % (ticket, existing["claimant"]))
    return 0


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    p_claim = sub.add_parser("claim", help="atomically claim a task")
    p_claim.add_argument("task_id")
    p_claim.add_argument("claimant")
    p_claim.add_argument("--force", action="store_true", help="override an existing claim")
    p_claim.add_argument("--reason", help="required with --force: why the existing claim is being overridden")
    p_claim.add_argument("--note", help="optional free-text note stored in the lock file")
    p_claim.add_argument(
        "--hitl-override",
        action="store_true",
        help="required in addition to --force --reason when overriding GIT-COMMIT "
        "(or other special resources) specifically -- do NOT pass this without an "
        "explicit human instruction, in the current conversation, to override a "
        "held commit lock",
    )
    p_claim.set_defaults(func=cmd_claim)

    p_reserve_next = sub.add_parser(
        "reserve-next",
        help="atomically claim the next available TASK-XXXX id -- no read-then-write race",
    )
    p_reserve_next.add_argument("--as", dest="claimant", required=True, metavar="LABEL", help="claimant label, always required")
    p_reserve_next.add_argument("--note", help="optional free-text note stored in the lock file")
    p_reserve_next.add_argument(
        "--dry-run",
        action="store_true",
        help="preview the next candidate id without claiming it -- can go stale before you act on it",
    )
    p_reserve_next.add_argument(
        "--quiet",
        action="store_true",
        help="print only the bare reserved id (for command substitution), no human-readable line",
    )
    p_reserve_next.set_defaults(func=cmd_reserve_next)

    p_release = sub.add_parser("release", help="release a task's claim (idempotent)")
    p_release.add_argument("task_id")
    p_release.add_argument("--claimant", help="expected current claimant; mismatch warns unless --strict")
    p_release.add_argument("--strict", action="store_true", help="fail instead of warn on claimant mismatch")
    p_release.set_defaults(func=cmd_release)

    p_status = sub.add_parser("status", help="show current claim(s)")
    p_status.add_argument("task_id", nargs="?")
    p_status.set_defaults(func=cmd_status)

    p_check_staleness = sub.add_parser(
        "check-staleness",
        help="TASK-0195: has a claimed file changed on disk since its claim-time content snapshot?",
    )
    p_check_staleness.add_argument("path", help="the same path/id you passed to `claim`")
    p_check_staleness.set_defaults(func=cmd_check_staleness)

    p_sync = sub.add_parser("sync", help="regenerate Claimed By/At cells in .ai/COMMON.md from lock files")
    p_sync.add_argument("--dry-run", action="store_true", help="print what would change without writing")
    p_sync.add_argument("--check", action="store_true", help="exit 1 if the table is out of sync; do not write")
    p_sync.set_defaults(func=cmd_sync)

    p_move = sub.add_parser(
        "move",
        help="move a task file between TODO/IN_PROGRESS/DONE, syncing its Status line + registry row",
    )
    p_move.add_argument("task_id")
    p_move.add_argument("target_state", choices=["TODO", "IN_PROGRESS", "DONE"])
    p_move.add_argument("--as", dest="as_", required=True, metavar="LABEL", help="claimant label, always required")
    p_move.add_argument("--force", action="store_true", help="override a claim mismatch")
    p_move.add_argument("--reason", help="required with --force")
    p_move.add_argument(
        "--keep-claim",
        action="store_true",
        help="do not auto-release the claim when moving to DONE (default: release)",
    )
    p_move.set_defaults(func=cmd_move)

    p_resolve = sub.add_parser(
        "resolve",
        help="resolve a task to DONE with an explicit canonical resolution value, staged by default",
    )
    p_resolve.add_argument("task_id")
    p_resolve.add_argument(
        "resolution",
        help="canonical value from .ai/reference/RESOLUTION_VOCABULARY.md "
        "(done/fixed/wont-do/duplicate/obsolete/not-reproducible/moved)",
    )
    p_resolve.add_argument("--note", help="optional free-text resolution note")
    p_resolve.add_argument("--as", dest="as_", required=True, metavar="LABEL", help="claimant label, always required")
    p_resolve.add_argument("--force", action="store_true", help="override a claim mismatch")
    p_resolve.add_argument("--reason", help="required with --force")
    p_resolve.add_argument(
        "--keep-claim",
        action="store_true",
        help="do not auto-release the claim on resolve (default: release)",
    )
    p_resolve.add_argument(
        "--no-stage",
        action="store_true",
        help="leave the on-disk changes correct but unstage them (git reset "
        "the task file, skip staging .ai/COMMON.md) -- default is to stage both",
    )
    p_resolve.set_defaults(func=cmd_resolve)

    p_guard = sub.add_parser(
        "commit-guard",
        help="refuse unless the staged index exactly matches --expect(-empty); "
        "read-only by default, add --commit to also perform the commit atomically",
    )
    guard_group = p_guard.add_mutually_exclusive_group(required=True)
    guard_group.add_argument(
        "--expect",
        nargs="+",
        metavar="PATH",
        help="exact set of paths expected to be staged for the next commit "
        "-- a renamed path always counts as TWO entries (old path removed, "
        "new path added): list both, never just the new one (TASK-0024.002)",
    )
    guard_group.add_argument(
        "--expect-empty",
        action="store_true",
        help="assert nothing is currently staged -- valid only for a "
        "from-scratch commit, before your first `stage`/`git add` this "
        "session; a prior `move`/`resolve` already left its own rename "
        "staged and legitimately fails this (TASK-0356) -- skip straight "
        "to `stage --expect <paths incl. that rename>` instead, whose own "
        "self-verification gives the same contamination check one step "
        "later. Incompatible with --commit.",
    )
    p_guard.add_argument(
        "--commit",
        action="store_true",
        help="TASK-0356: if the --expect check passes, immediately run "
        "`git commit -F <--message-file>` in the same process -- no "
        "separate shell step between check and commit for a `|`/`;`/`&&` "
        "idiom to silently disconnect (the exact mechanism that let a "
        "failing guard's commit proceed anyway, twice). Re-verifies "
        "GIT-COMMIT session identity itself before committing (the "
        "PreToolUse hook cannot see this call's own `git commit` "
        "subprocess). Requires --expect (not --expect-empty) and "
        "--message-file.",
    )
    p_guard.add_argument(
        "--message-file",
        metavar="PATH",
        help="path to the full commit message, read verbatim via `git commit "
        "-F` -- required with --commit; write it with the Write tool first, "
        "never pass a message inline",
    )
    p_guard.set_defaults(func=cmd_commit_guard)

    p_stage = sub.add_parser(
        "stage",
        help="git add exactly the declared .ai/.claude paths, self-verifying after",
    )
    p_stage.add_argument(
        "--expect",
        nargs="+",
        required=True,
        metavar="PATH",
        help="exact paths to stage; every path must be under .ai/ or .claude/ "
        "-- if one of them is a rename (moved since the last commit), list "
        "BOTH the old and new path: self-verification compares against the "
        "actually-staged index, which always splits a rename into two "
        "entries (TASK-0024.002)",
    )
    p_stage.set_defaults(func=cmd_stage)

    p_add = sub.add_parser(
        "add",
        help="TASK-0061: attributed git add (any path) + a permanent "
        "'why' record appended to the claiming task's own file",
    )
    p_add.add_argument("task_id")
    p_add.add_argument(
        "path",
        nargs="?",
        help="single-file form: the path to stage. Omit and use --from-file "
        "for the batch form instead.",
    )
    p_add.add_argument(
        "--purpose",
        help="single-file form: short free-text reason, permanently recorded "
        "in the task's own '## Staged Files' section",
    )
    p_add.add_argument(
        "--from-file",
        metavar="PATH",
        help="batch form: path to a JSON manifest -- either an array of "
        "{'file','purpose'} objects, or an object {'purpose': '<shared>', "
        "'files': [...]} whose 'files' entries may be plain path strings "
        "(inherit the shared purpose) or {'file','purpose'} objects "
        "(override it). Mutually exclusive with the positional PATH/"
        "--purpose. Write it with the Write tool, never inline JSON on the "
        "command line.",
    )
    p_add.set_defaults(func=cmd_add)

    p_scq_enter = sub.add_parser(
        "scq-enter",
        help="publish/update a Stage-Commit-Queue entry: intended files + a prepared commit message",
    )
    p_scq_enter.add_argument("--as", dest="as_", required=True, metavar="LABEL", help="claimant label, always required")
    p_scq_enter.add_argument(
        "--files",
        nargs="+",
        required=True,
        metavar="PATH",
        help="intended files for the upcoming commit (informational only -- not staged)",
    )
    p_scq_enter.add_argument("--message", required=True, metavar="TEXT", help="short one-line summary shown in the queue listing")
    p_scq_enter.add_argument(
        "--message-file",
        metavar="PATH",
        help="path to the full prepared commit message, read verbatim (write it with the Write tool, never inline)",
    )
    p_scq_enter.set_defaults(func=cmd_scq_enter)

    p_scq_leave = sub.add_parser(
        "scq-leave",
        help="withdraw a Stage-Commit-Queue entry",
    )
    p_scq_leave.add_argument("ticket")
    p_scq_leave.add_argument("--as", dest="as_", required=True, metavar="LABEL", help="claimant label, always required")
    p_scq_leave.add_argument("--strict", action="store_true", help="refuse instead of warn on claimant mismatch")
    p_scq_leave.set_defaults(func=cmd_scq_leave)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
