#!/usr/bin/env python3
"""TASK-0195: dangling / positional-reference check for append-heavy docs.

Two independent checks, run against one or more markdown files (defaults to
`__WORK_IN_PROGRESS__/RESULTS.md`, the file this task was filed about):

1. **Dangling.** Every `[[TASK-XXXX[.NNN]]]` citation must resolve to a task
   file that actually exists on disk right now (TODO/IN_PROGRESS/DONE) --
   the same ground truth `claim.py`'s own `disk_task_ids()` uses.
2. **Positional.** Every bare `row N` / `rows N-M` reference (the fragile
   kind: renumbering the open-questions table silently invalidates it) must
   share its paragraph with at least one real `TASK-XXXX` token -- so a
   reader (or a future automated check) can re-locate the claim even after
   the row number drifts. This is the convention already followed almost
   everywhere in RESULTS.md (`[[TASK-XXXX]] (row NN)` or a bare `TASK-XXXX`
   nearby); this check makes it mechanical instead of a hand sweep.

Paragraphs are blank-line-delimited blocks -- markdown table rows are each
their own paragraph-equivalent line, and every open-questions table row
already ends with its own `[[TASK-XXXX]], ...]` cell, so table rows trivially
pass.

Exit 0 with no output if clean. Exit 1 and print one `file:line: message`
per finding otherwise -- suitable for a pre-commit-style check.
"""
from __future__ import print_function

import re
import sys
import os

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)
import claim  # noqa: E402  (local import, path set above)

TASK_ID_TOKEN_RE = re.compile(r"TASK-\d{4}(?:\.\d{3})?")
CITATION_RE = re.compile(r"\[\[(TASK-\d{4}(?:\.\d{3})?)\]\]")
ROW_REF_RE = re.compile(r"\brows?\s+\d+\b", re.IGNORECASE)

DEFAULT_TARGETS = [
    os.path.join("__WORK_IN_PROGRESS__", "RESULTS.md"),
]

# Deliberately out-of-register ids: `[[TASK-XXXX]]`-shaped, but pointing at
# work that intentionally has no `.ai/tasks/` file (e.g. an isolated
# validation program on a separate branch, kept outside the normal
# claim/registry machinery on purpose). One entry so far: TASK-9000, the
# placeholder id used in RESULTS.md's own text for the `val-9xxx` branch's
# propagator-validation program ("a separate branch ... deliberately
# outside this register"). Extend this set, with a one-line reason each,
# rather than loosening the dangling check itself.
KNOWN_EXTERNAL_IDS = frozenset(["TASK-9000"])


def _paragraphs(lines):
    # type: (list) -> list
    """Yield (start_line_1indexed, [lines]) for each blank-line-delimited block."""
    blocks = []
    current = []
    start = None
    for i, line in enumerate(lines, start=1):
        if line.strip() == "":
            if current:
                blocks.append((start, current))
                current = []
                start = None
        else:
            if start is None:
                start = i
            current.append(line)
    if current:
        blocks.append((start, current))
    return blocks


def check_file(path, known_task_ids):
    # type: (str, dict) -> list
    findings = []
    with open(path, "r") as f:
        lines = f.read().splitlines()

    # 1. Dangling citations -- checked per line, independent of paragraphing.
    for lineno, line in enumerate(lines, start=1):
        for match in CITATION_RE.finditer(line):
            task_id = match.group(1)
            if task_id in KNOWN_EXTERNAL_IDS:
                continue
            if task_id not in known_task_ids:
                findings.append(
                    "%s:%d: dangling reference [[%s]] -- no task file on disk"
                    % (path, lineno, task_id)
                )

    # 2. Positional row-refs with no task-id anchor anywhere in their paragraph.
    for start, block in _paragraphs(lines):
        text = "\n".join(block)
        has_anchor = bool(TASK_ID_TOKEN_RE.search(text))
        if has_anchor:
            continue
        for i, line in enumerate(block):
            for match in ROW_REF_RE.finditer(line):
                findings.append(
                    "%s:%d: positional reference %r has no TASK-XXXX anchor "
                    "anywhere in its paragraph"
                    % (path, start + i, match.group(0))
                )
    return findings


def main(argv):
    targets = argv or DEFAULT_TARGETS
    known_task_ids = claim.disk_task_ids()
    all_findings = []
    for path in targets:
        all_findings.extend(check_file(path, known_task_ids))
    for finding in all_findings:
        print(finding)
    if all_findings:
        print("%d finding(s)" % len(all_findings), file=sys.stderr)
        return 1
    print("clean: %s" % ", ".join(targets))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
