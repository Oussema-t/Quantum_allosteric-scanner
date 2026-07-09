#!/usr/bin/env python3
"""agents-tools/capability-runner.sh -- capability dispatcher (TASK-0026.001)

Kept as capability-runner.sh, not renamed to .py: .ai/reference/
CAPABILITIES.md already references this exact path in 16+ rows as the
"Current Provider" for the whole Commit Packager capability set --
renaming is TASK-0026.003's job (a CAPABILITIES.md honesty/correction
pass, after both build subtasks land), not this one's. Implemented in
Python (stdlib only) for the same reason .ai/tools/claim.py is: a bare
executable with a shebang works regardless of file extension, and JSON
output plus deterministic sorting is far less fragile here than in POSIX
shell.

Argument/exit-code contract:
    capability-runner.sh <capability-name> [--json] [capability-specific flags]
    exit 0 -- success
    exit 2 -- unknown capability name, malformed flags (argparse's own
              usage-error exit, same as every other tool in this repo),
              or an underlying git command failed

Capabilities implemented in this slice (TASK-0026.001 -- see
.ai/reference/CAPABILITIES.md for the full row descriptions):
    repo.vcs.staged-files    [--json]
    repo.vcs.changed-files   --scope all|staged [--json]
    repo.packaging.snapshot  [--include-working-tree] [--json]

repo.vcs.current-branch / repo.vcs.short-status / repo.vcs.staged-diff-stat
are deliberately NOT separate top-level capability names here --
CAPABILITIES.md's own Provider column already documents them as fields
surfaced through repo.packaging.snapshot's composite output, not
standalone subcommands. This implementation matches that as written; add
standalone providers for them only after updating CAPABILITIES.md first
(TASK-0026.003), not preemptively.

No third-party dependencies -- stdlib only.
"""

import argparse
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _git(*args):
    # type: (*str) -> str
    """Run git with args from REPO_ROOT; return stdout stripped. Exit 2 on failure."""
    proc = subprocess.run(
        ["git"] + list(args),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(
            "error: git %s failed: %s" % (" ".join(args), proc.stderr.strip()),
            file=sys.stderr,
        )
        sys.exit(2)
    return proc.stdout.strip("\n")


def _current_branch():
    # type: () -> str
    return _git("branch", "--show-current")


def _staged_files():
    # type: () -> list
    out = _git("diff", "--staged", "--name-only")
    return sorted(line for line in out.splitlines() if line)


def _unstaged_modified_files():
    # type: () -> list
    out = _git("diff", "--name-only")
    return sorted(line for line in out.splitlines() if line)


def _untracked_files():
    # type: () -> list
    out = _git("ls-files", "--others", "--exclude-standard")
    return sorted(line for line in out.splitlines() if line)


def _short_status_lines():
    # type: () -> list
    out = _git("status", "--short")
    return out.splitlines() if out else []


def _staged_diff_stat():
    # type: () -> dict
    """Structured stat over staged changes: filesChanged/insertions/deletions + raw --stat text."""
    numstat = _git("diff", "--staged", "--numstat")
    files_changed = 0
    insertions = 0
    deletions = 0
    for line in numstat.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added, deleted = parts[0], parts[1]
        files_changed += 1
        if added.isdigit():
            insertions += int(added)
        if deleted.isdigit():
            deletions += int(deleted)
    raw = _git("diff", "--staged", "--stat")
    return {
        "filesChanged": files_changed,
        "insertions": insertions,
        "deletions": deletions,
        "raw": raw,
    }


# ------------------------------------------------------------- capabilities --

def cap_staged_files(args):
    files = _staged_files()
    if args.json:
        print(json.dumps(files))
    else:
        if not files:
            print("(no staged files)")
        for f in files:
            print(f)
    return 0


def cap_changed_files(args):
    if args.scope == "staged":
        files = _staged_files()
    else:
        files = sorted(
            set(_staged_files())
            | set(_unstaged_modified_files())
            | set(_untracked_files())
        )
    if args.json:
        print(json.dumps(files))
    else:
        if not files:
            print("(no changed files)")
        for f in files:
            print(f)
    return 0


def cap_packaging_snapshot(args):
    snapshot = {
        "branch": _current_branch(),
        "staged": {
            "files": _staged_files(),
            "diffStat": _staged_diff_stat(),
        },
    }
    if args.include_working_tree:
        snapshot["workingTree"] = {"shortStatus": _short_status_lines()}

    if args.json:
        print(json.dumps(snapshot, indent=2))
        return 0

    print("branch: %s" % snapshot["branch"])
    print("staged files (%d):" % len(snapshot["staged"]["files"]))
    for f in snapshot["staged"]["files"]:
        print("  %s" % f)
    stat = snapshot["staged"]["diffStat"]
    print(
        "staged diff stat: %d file(s) changed, +%d/-%d"
        % (stat["filesChanged"], stat["insertions"], stat["deletions"])
    )
    if args.include_working_tree:
        wt_lines = snapshot["workingTree"]["shortStatus"]
        print("working tree short status (%d):" % len(wt_lines))
        for line in wt_lines:
            print("  %s" % line)
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="capability", required=True)

    p_staged = sub.add_parser(
        "repo.vcs.staged-files", help="list staged file paths (sorted, deterministic)"
    )
    p_staged.add_argument("--json", action="store_true")
    p_staged.set_defaults(func=cap_staged_files)

    p_changed = sub.add_parser(
        "repo.vcs.changed-files", help="list the complete changed-file set"
    )
    p_changed.add_argument("--scope", choices=["all", "staged"], default="all")
    p_changed.add_argument("--json", action="store_true")
    p_changed.set_defaults(func=cap_changed_files)

    p_snapshot = sub.add_parser(
        "repo.packaging.snapshot",
        help="composite branch/staged-diff/working-tree snapshot",
    )
    p_snapshot.add_argument("--include-working-tree", action="store_true")
    p_snapshot.add_argument("--json", action="store_true")
    p_snapshot.set_defaults(func=cap_packaging_snapshot)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
