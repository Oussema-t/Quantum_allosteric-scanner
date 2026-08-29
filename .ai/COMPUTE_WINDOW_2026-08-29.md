# Compute window 2026-08-29 → Sunday 2026-08-30 — lane assignment

Last compute window before the repo owner returns to the Phase 1
write-up ([[TASK-0184]]) on Sunday. Three lanes, chosen so they **cannot
collide** on files, on the GIT-COMMIT lock, or on the machine.

## Dependency graph

```
LANE 1  TASK-0290  deterministic active site + min_A recompute   [CRITICAL PATH]
           │  posts: recompute diff (targets whose min_A moved)
           ├──────────────► LANE 2  TASK-0293  LOTO druggability/size
           │                         (build + provisional run NOW,
           │                          re-run on the diff)
           └──────────────► TASK-0288 Finding F wording, TASK-0184

LANE 3  TASK-0294  bare-except audit        [independent of both]
```

## Lane 1 — TASK-0290 (critical path, one implementer)

**Owns exclusively:** `backend/active_site.py`,
`results/tasks/0258_allosteric_distance_taxonomy/pocket_taxonomy.json`.

Fix the non-determinism (disk cache) **and** the silent downgrade
(distinguish "no annotation" from "call failed"), propagate `source`
through `prep()`, then recompute `min_A` **and** `max_A` for all 33
targets and diff against the committed taxonomy.

**Post the diff as soon as it exists** — Lane 2 is waiting on it.

**Do not** pin to whichever tier reproduces the current numbers. If a
target crosses the 1.5 Å or near/far boundary, that is a result.

## Lane 2 — TASK-0293 (parallel, one implementer)

**Read-only on `backend/`.** Build the LOTO harness for a **single
pre-specified arm** (`druggability / size`), reproduce the published
0.16486 as a control, run it, and label the output **PROVISIONAL**.

**Known dependency:** `DHPS_GC7` and `NAMPT_NPA1R` are 2 of the frozen 20
*and* are among the three targets measured as unstable. Re-run on Lane 1's
corrected taxonomy before any verdict.

**One arm only.** No `druggability / size^k` family, no mid-run variants.

## Lane 3 — TASK-0294 (independent, no compute)

Read-only audit of bare `except Exception` across the scientific path.
Report a table; **fix nothing**. Must not touch `backend/active_site.py`
(Lane 1 owns it) and must not contend for the machine.

## Shared-resource protocol

- **GIT-COMMIT is a serial lock.** Claim, `commit-guard --expect`, commit,
  release. Do not hold it across a long compute run.
- Stage only your own paths. If another lane's files appear staged,
  `git restore --staged` them — never commit another lane's work.
- `__WORK_IN_PROGRESS__/results/` is gitignored; key evidence JSONs are
  force-added, matching the TASK-0282 precedent.

## Explicitly NOT in this window

- Rewording TASK-0288 Finding F in the brief or [[TASK-0184]] — the brief
  is under collaborator review and Finding F's numbers move with Lane 1.
- Any new descriptor hunt. TASK-0287/0288 closed that line: pocket
  location is not predictable at any structural scale measured, and
  Findings A–E there are **not** gated on Lane 1.
