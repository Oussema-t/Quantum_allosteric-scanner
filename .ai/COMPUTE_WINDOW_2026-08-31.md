# Compute window 2026-08-31 — four lanes

Phase 1 deadline **2026-09-15**. [[TASK-0184]] is the critical path;
everything below either feeds it or is Phase-2 groundwork.

## Dependency graph

```
LANE A  TASK-0306  six-measure meta-classifier      [light compute, self-contained]
           └─ GATED: redundancy test first. If the six measures are as
              correlated as our 61 rules were (TASK-0301), STOP and report.

LANE B  TASK-0304  CASBench annotations + ingestion + re-run 0299/0300
           │  [HEAVY compute; owns the cohort config and all 0282 re-runs]
           └──────► feeds TASK-0306's protein-level splits and TASK-0307

LANE C  TASK-0303  ENM mode shift as a STANDALONE ranker   [moderate compute]
           └─ then TASK-0302  sibling-conformer persistence [heavy]
              Both are TASK-0301's "independent signal" candidates and
              share tooling, so they belong to one implementer in sequence.

LANE D  TASK-0307  submission evidence pack          [no compute]
           └─ audit only; feeds TASK-0184 directly
```

## The one collision, and how it is resolved

[[TASK-0303]] as originally filed would add mode shift to
`task0282_pocket_selection_sweep.METRICS`. **Lane B re-runs that exact
script on the extended cohort.** Two implementers editing and running the
same file in the same window produces results on a moving target.

**Resolution: Lane C does NOT touch `task0282` this window.** Mode shift
is implemented and evaluated **standalone** — its own ranker, its own
independence check against druggability and pocket size. Integration into
`METRICS` happens only after Lane B's cohort lands, as a follow-up.
[[TASK-0303]]'s scope has been amended accordingly.

## Exclusive ownership

| lane | owns exclusively |
|---|---|
| A | `results/tasks/0306_*`, the S3–S6 xlsx parsing |
| B | `config/` cohort files, `results/tasks/0304_*`, **all `task0282` runs** |
| C | `results/tasks/0303_*`, `results/tasks/0302_*` |
| D | `results/tasks/0307_*` — **read-only everywhere else** |

## Machine contention

Lanes B and C are both heavy (many structures × fpocket / eigendecomposition).
**Lane B has priority** — it is on the critical path for both A and D.
Lane C should start with the mode-shift port (cheap) and defer
[[TASK-0302]]'s sibling sweep until B's ingestion finishes.

## Shared-resource protocol

- **GIT-COMMIT is a serial lock.** claim → `commit-guard --expect-empty` →
  stage → `commit-guard --expect` → commit → release. Never hold it across
  a long run.
- Stage only your own paths. If another lane's files appear staged,
  `git restore --staged` them.
- `__WORK_IN_PROGRESS__/results/` is gitignored; key evidence JSONs are
  force-added, matching the [[TASK-0282]] precedent.
- **Run `python3 .ai/tools/claim.py` from the repo root** — it resolves
  relative to cwd and fails confusingly from `__WORK_IN_PROGRESS__`.

## Standing rules, learned the hard way this week

1. **Cluster-robust or it does not count.** Four selection procedures have
   now been destroyed by pseudo-replication ([[TASK-0282]], [[TASK-0293]],
   [[TASK-0299]], [[TASK-0300]]). CASBench is 314 structures over 33
   proteins — **split by protein, never by structure.**
2. **Every negative needs a positive control.** [[TASK-0305]]'s negative is
   only interpretable because their own scores beat random on the same
   metric at p=5e-9. A null from an untested design is not a finding.
3. **In-sample gains are guilty until proven innocent.** Two separate
   in-sample wins (0.267, 0.2649) have evaporated under held-out scoring.
4. **Report the number that moves against you.** [[TASK-0298]] found the
   ceiling collapses; [[TASK-0299]] found it read as a CTQW win and said so.

## Explicitly NOT in this window

- Editing `CTQW_CONTRIBUTION_BRIEF.html` or [[TASK-0184]] — Lane D audits,
  it does not apply.
- Re-opening [[TASK-0287]]/[[TASK-0288]] Findings A–E. Closed, and not
  affected by the chain fix.
- New pocket-ranker sweeps on the 13-cluster cohort ([[TASK-0301]]:
  "the binding constraint is 13 clusters, not the feature set").
