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

Extended for TASK-0027: `move` relocates a task file between
TODO/IN_PROGRESS/DONE, rewrites its own "- Status:" line, and updates its
.ai/COMMON.md registry row's Status/Path cells, all as one command --
refusing on a claim mismatch the same way `claim` does. Moving to DONE
auto-releases the claim by default (--keep-claim to opt out).

No third-party dependencies -- stdlib only.

Usage:
    claim.py claim   TASK-0024 "Toolsmith (this thread)" [--reason TEXT] [--force] [--note TEXT]
    claim.py claim   GIT-COMMIT "Toolsmith (this thread)" [--force --reason TEXT --hitl-override]
    claim.py release TASK-0024 [--claimant TEXT] [--strict]
    claim.py status  [TASK-0024]
    claim.py sync    [--dry-run] [--check]
    claim.py commit-guard --expect PATH [PATH ...]
    claim.py move    TASK-0024 IN_PROGRESS --as "Toolsmith (this thread)" [--force --reason TEXT] [--keep-claim]
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
# Kept as a small explicit set (not general arbitrary-resource support --
# that's TASK-0024.001) so this doesn't collide with or duplicate that
# broader mechanism if/when it lands; same lock-file format either way.
SPECIAL_RESOURCE_IDS = frozenset(["GIT-COMMIT"])


def normalize_task_id(raw):
    # type: (str) -> str
    """Accepts TASK-0024, 24, TASK-0026.001, 26.1, GIT-COMMIT, etc.

    Dotted suffixes are the .ai/tasks/README.md subtask convention
    (TASK-XXXX.NNN) for independently claimable slices of a parent task.
    GIT-COMMIT (TASK-0028) is a fixed non-numeric resource id, checked
    before the numeric parsing below.
    """
    upper = raw.strip().upper()
    if upper in SPECIAL_RESOURCE_IDS:
        return upper
    match = TASK_ID_RE.search(raw)
    if not match:
        raise SystemExit("error: could not find a task number in %r" % raw)
    main = "TASK-%04d" % int(match.group(1))
    sub = match.group(2)
    return main if sub is None else "%s.%03d" % (main, int(sub))


def is_task_id(resource_id):
    # type: (str) -> bool
    """True for TASK-XXXX[.NNN] ids, False for special resources like GIT-COMMIT."""
    return bool(TASK_ID_ONLY_RE.match(resource_id))


def lock_path(task_id):
    # type: (str) -> str
    return os.path.join(LOCKS_DIR, task_id + ".lock")


def now_str():
    # type: () -> str
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def read_lock(task_id):
    # type: (str) -> Optional[dict]
    path = lock_path(task_id)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


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

def cmd_claim(args):
    task_id = normalize_task_id(args.task_id)
    os.makedirs(LOCKS_DIR, exist_ok=True)
    path = lock_path(task_id)
    data = {
        "task_id": task_id,
        "claimant": args.claimant,
        "claimed_at": now_str(),
        "note": args.note,
    }

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
        print(
            "claimed %s for %r (overrode previous claim by %r, reason: %s)"
            % (task_id, args.claimant, existing["claimant"], args.reason)
        )
        return 0
    else:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        print("claimed %s for %r at %s" % (task_id, args.claimant, data["claimed_at"]))
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


# --------------------------------------------------------------- status ----

def cmd_status(args):
    if args.task_id:
        task_id = normalize_task_id(args.task_id)
        lock = read_lock(task_id)
        if lock is None:
            print("%s: unclaimed" % task_id)
        else:
            print(
                "%s: claimed by %r at %s"
                % (task_id, lock["claimant"], lock["claimed_at"])
            )
        return 0

    os.makedirs(LOCKS_DIR, exist_ok=True)
    lock_ids = sorted(
        name[: -len(".lock")]
        for name in os.listdir(LOCKS_DIR)
        if name.endswith(".lock")
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
            "%s: claimed by %r at %s%s"
            % (task_id, lock["claimant"], lock["claimed_at"], dangling)
        )
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

    if changed:
        with _common_md_lock():
            with open(COMMON_MD, "w") as f:
                f.writelines(new_lines)
    return changed


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
    lock = read_lock(task_id)
    if lock is not None and lock["claimant"] != args.as_:
        if not args.force:
            print(
                "error: %s already claimed by %r at %s (use --force --reason "
                "TEXT to override if you judge this stale)"
                % (task_id, lock["claimant"], lock["claimed_at"]),
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
        print(
            "warning: moving %s despite a claim mismatch (held by %r), "
            "reason: %s" % (task_id, lock["claimant"], args.reason),
            file=sys.stderr,
        )
    elif lock is None:
        print(
            "warning: %s is unclaimed -- proceeding without a claim check"
            % task_id,
            file=sys.stderr,
        )

    try:
        current_state, filename = find_task_file(task_id)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 1

    src_path = os.path.join(TASKS_DIR, current_state, filename)
    dst_path = os.path.join(TASKS_DIR, target_state, filename)
    src_rel = os.path.relpath(src_path, REPO_ROOT)
    dst_rel = os.path.relpath(dst_path, REPO_ROOT)

    with open(src_path, "r") as f:
        content = f.read()

    target_status_text = STATE_TO_STATUS[target_state]
    status_match = STATUS_LINE_RE.search(content)
    current_status_text = (
        status_match.group(0)[len("- Status:") :].strip() if status_match else None
    )
    need_status_rewrite = current_status_text != target_status_text
    need_file_move = current_state != target_state

    if need_status_rewrite:
        if status_match is None:
            print(
                "warning: no '- Status:' line found in %s -- Status not rewritten"
                % src_path,
                file=sys.stderr,
            )
        else:
            new_content = STATUS_LINE_RE.sub(
                "- Status: %s" % target_status_text, content, count=1
            )
            with open(src_path, "w") as f:
                f.write(new_content)

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
            return 1

    registry_path_cell = "`%s`" % dst_rel.replace(os.sep, "/")
    registry_changed = update_registry_row(task_id, target_status_text, registry_path_cell)

    released = False
    if target_state == "DONE" and lock is not None and not args.keep_claim:
        os.remove(lock_path(task_id))
        released = True

    if not need_file_move and not need_status_rewrite and not registry_changed:
        print("%s already in %s with Status: %s -- no-op" % (task_id, target_state, target_status_text))
    else:
        print(
            "moved %s -> %s (Status: %s)%s%s"
            % (
                task_id,
                target_state,
                target_status_text,
                ", registry updated" if registry_changed else "",
                ", claim released" if released else "",
            )
        )
    return 0


# --------------------------------------------------------- commit-guard ----

def cmd_commit_guard(args):
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    staged = set(line for line in proc.stdout.splitlines() if line)
    expected = set(args.expect)

    unexpected = sorted(staged - expected)
    missing = sorted(expected - staged)

    if unexpected:
        print(
            "error: staged index contains paths not in --expect: %s"
            % ", ".join(unexpected),
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

    print("ok: staged index exactly matches --expect (%d path(s))" % len(expected))
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

    p_release = sub.add_parser("release", help="release a task's claim (idempotent)")
    p_release.add_argument("task_id")
    p_release.add_argument("--claimant", help="expected current claimant; mismatch warns unless --strict")
    p_release.add_argument("--strict", action="store_true", help="fail instead of warn on claimant mismatch")
    p_release.set_defaults(func=cmd_release)

    p_status = sub.add_parser("status", help="show current claim(s)")
    p_status.add_argument("task_id", nargs="?")
    p_status.set_defaults(func=cmd_status)

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

    p_guard = sub.add_parser(
        "commit-guard",
        help="refuse (read-only check) unless the staged index exactly matches --expect",
    )
    p_guard.add_argument(
        "--expect",
        nargs="+",
        required=True,
        metavar="PATH",
        help="exact set of paths expected to be staged for the next commit",
    )
    p_guard.set_defaults(func=cmd_commit_guard)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
