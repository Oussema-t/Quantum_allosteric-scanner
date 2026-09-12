#!/usr/bin/env python3
"""Merge APPROVED blocks from ADDITIONS.md into a COPY of the proposal.

    python3 submission/tools/merge_additions.py [--out <file>] [--dry-run]

The verbatim copy of his V4 is never modified. Output is a new file, so
`diff` always shows exactly what we added.
"""
import re, sys, argparse
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / "phase1"

def parse(md):
    blocks = []
    for chunk in re.split(r"^### (?=ADD-)", md, flags=re.M)[1:]:
        head, _, body = chunk.partition("\n---\n")
        title = head.splitlines()[0].strip()
        meta = dict(re.findall(r"^(\w+):\s*(.+)$", head, flags=re.M))
        blocks.append({"title": title, "status": meta.get("status", "PENDING").strip(),
                       "section": meta.get("section", "?").strip(),
                       "anchor": meta.get("anchor", "").strip(),
                       # NOTE: do NOT truncate at "\n### " -- the regex split above already
                       # ends each chunk at the next ADD- block, and a body may legitimately
                       # contain "### " subsections (Appendix B has B.0 / B.1).
                       "text": body.strip()})
    return blocks

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, default=HERE / "PHASE1_SUBMISSION_V4.md")
    ap.add_argument("--additions", type=Path, default=HERE / "ADDITIONS.md")
    ap.add_argument("--out", type=Path, default=HERE / "PHASE1_SUBMISSION_V4_MERGED.md")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    doc = a.base.read_text()
    blocks = parse(a.additions.read_text())
    approved = [b for b in blocks if b["status"].upper() == "APPROVED"]
    print("blocks: %d total, %d approved" % (len(blocks), len(approved)))
    if not approved:
        print("nothing approved -- no output written"); return 0

    applied, failed = [], []
    for b in approved:
        if b["anchor"] == "__END__":
            doc = doc.rstrip() + "\n\n" + b["text"] + "\n"; applied.append(b); continue
        i = doc.find(b["anchor"])
        if i < 0:
            failed.append(b); continue
        end = doc.find("\n", i + len(b["anchor"]))
        end = len(doc) if end < 0 else end
        doc = doc[:end] + "\n\n" + b["text"] + "\n" + doc[end:]
        applied.append(b)

    for b in applied: print("  APPLIED  %-46s -> %s" % (b["title"][:46], b["section"]))
    for b in failed:  print("  FAILED   %-46s  anchor not found: %r" % (b["title"][:46], b["anchor"][:60]))
    if a.dry_run:
        print("dry run -- nothing written"); return 1 if failed else 0
    a.out.write_text(doc)
    print("wrote %s (+%d lines over base)" % (a.out, len(doc.splitlines()) - len(a.base.read_text().splitlines())))
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
