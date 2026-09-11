#!/usr/bin/env python3
"""Check a proposed addition against the proposal for repetition and contradiction.

    python3 submission/tools/check_addition.py <addition.md> [--base <proposal.md>]

REPEAT   a number in the addition already appears in the base for the same topic
CONFLICT the same named quantity carries a different number in each
NEW      no match in the base -- genuinely additive

Topic keys are the words around a number, so "identity floor 0.65" and "identity
floor 0.771" collide while "0.65" elsewhere does not. Judgement still required:
this flags candidates, it does not decide.
"""
import re, sys, argparse
from pathlib import Path

NUM = re.compile(r"(?<![\w.])(\d+\.\d+|\d{1,5})(?![\w.])")
STOP = set("the a an of in on for to and or is are was were with by at as that this it its "
           "we our their they than from be been not no any all each per over under".split())

def sentences(md):
    md = re.sub(r"\*\*|\*|`|~~", "", md)
    out = []
    for line in md.splitlines():
        if line.startswith("#"): continue
        for s in re.split(r"(?<=[.;:])\s+", line):
            s = s.strip(" |-")
            if s and NUM.search(s): out.append(s)
    return out

def topics(s):
    """content words near each number -> the quantity it describes"""
    w = [x.lower().strip(".,;:()[]%") for x in s.split()]
    keys = set()
    for i, t in enumerate(w):
        if NUM.fullmatch(t.strip("+-")):
            ctx = [x for x in w[max(0, i-6):i+4] if x and x not in STOP and not NUM.fullmatch(x.strip("+-"))]
            for c in ctx:
                if len(c) > 3: keys.add(c)
    return keys

def nums(s): return set(NUM.findall(s))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("addition", type=Path)
    ap.add_argument("--base", type=Path,
                    default=Path(__file__).resolve().parents[1] / "phase1/PHASE1_SUBMISSION_V4.md")
    a = ap.parse_args()
    base = sentences(a.base.read_text())
    base_idx = [(s, topics(s), nums(s)) for s in base]
    add = sentences(a.addition.read_text())
    verdicts = {"REPEAT": 0, "CONFLICT": 0, "NEW": 0}
    for s in add:
        st, sn = topics(s), nums(s)
        best, hits = None, []
        for bs, bt, bn in base_idx:
            shared = st & bt
            if len(shared) >= 2:
                hits.append((len(shared), bs, bn, shared))
        if not hits:
            verdicts["NEW"] += 1; continue
        hits.sort(reverse=True, key=lambda h: h[0])
        _, bs, bn, shared = hits[0]
        kind = "REPEAT" if sn & bn else "CONFLICT"
        verdicts[kind] += 1
        print("%-8s  %s" % (kind, s[:120]))
        print("          base: %s" % bs[:120])
        print("          shared terms: %s | addition %s vs base %s\n"
              % (", ".join(sorted(shared)[:5]), sorted(sn), sorted(bn)))
    print("-" * 60)
    print("  NEW %d   REPEAT %d   CONFLICT %d   (of %d numeric sentences)"
          % (verdicts["NEW"], verdicts["REPEAT"], verdicts["CONFLICT"], len(add)))
    print("  CONFLICT must be resolved or labelled as a second cohort before merging.")
    return 1 if verdicts["CONFLICT"] else 0

if __name__ == "__main__":
    sys.exit(main())
