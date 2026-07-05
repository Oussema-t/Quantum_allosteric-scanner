#!/usr/bin/env python3
"""Report a task's claim status and on-disk location in one command.

Built for TASK-0025 as the worked example for command-hygiene: replaces
the ad hoc chain

    python3 .ai/tools/claim.py status && echo ... && find .ai/tasks \\
        -iname "TASK-0024*" && echo ... && ls .ai/tasks/TODO \\
        .ai/tasks/IN_PROGRESS .ai/tasks/DONE

(reproduced this session, see .ai/reference/CAPABILITIES.md) with a single
whitelisted invocation. Reuses claim.py's own lock-reading and disk-scan
logic directly (same directory import) rather than re-deriving it or
shelling out to a second process.

No third-party dependencies -- stdlib only.

Usage:
    task_locate.py TASK-0024
    task_locate.py 26.1
"""

import sys

import claim as _claim


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: task_locate.py <TASK-ID>", file=sys.stderr)
        return 2

    task_id = _claim.normalize_task_id(argv[0])
    lock = _claim.read_lock(task_id)
    on_disk = _claim.disk_task_ids()

    print("%s:" % task_id)
    if lock is None:
        print("  claim:  unclaimed")
    else:
        print("  claim:  %r at %s" % (lock["claimant"], lock["claimed_at"]))

    path = on_disk.get(task_id)
    if path is None:
        print("  file:   not found under TODO/IN_PROGRESS/DONE")
    else:
        state = path.split("/")[2] if path.count("/") >= 2 else "?"
        print("  file:   %s" % path)
        print("  state:  %s" % state)

    return 0


if __name__ == "__main__":
    sys.exit(main())
