# Merge Conflict Protocol

*Every incident this protocol responds to was a clean `git status` right up until
it wasn't — divergence found late, or a "successful" merge that silently dropped
real content because git never saw a textual conflict to flag.*

## Why this exists

This is a multi-machine, multi-thread repo (`CLAUDE.md`'s own "the user sometimes
edits on GitHub" + this scaffold's concurrent Implementer/Architect threads) with
two genuinely hot shared files — `.ai/COMMON.md`'s Active Work Registry and
`__WORK_IN_PROGRESS__/RESULTS.md`'s dated findings/open-questions table — both
append-only ledgers that many threads write to independently, often without a
commit in between. That combination has already produced three distinct, real
failure modes, not hypothetical ones:

1. **Whole-file collision on `COMMON.md`.** A blanket `git add`/write from one
   thread overwrote another thread's concurrent, unrelated edit to the same file
   — no merge involved at all, just two threads writing the same file without
   coordination. Root-caused in `.ai/memory/questions/toolsmith/answered/
   Q-0001-*.md`; TASK-0107 found a second live instance during its own
   validation. Fixed at the tooling level by `claim.py`'s surgical single-row
   staging (`stage`/`move`/`resolve`) — the actual defense is *not writing the
   whole file* in the first place, not a merge strategy.
2. **Silent content loss on `RESULTS.md` with no conflict markers at all.** Two
   independent lines of work both inserted at open-questions row 51; a later
   commit sequence from a separate machine, built against an older snapshot of
   the file, overwrote rows 47-53 (plus a cross-reference note) when it landed —
   recovered in `61b8096`, renumbered 52-59. This is the dangerous case: git's
   line-based merge had no reason to flag a conflict, because from its
   perspective one side's edit simply superseded a stale base. **A clean merge
   is not proof nothing was lost when the ledger's own insertion point is
   effectively "the end of a growing table."** `TASK-0195` is the deeper,
   still-open tooling fix (task-ID cross-references instead of row numbers, a
   staleness/lock mechanism for this file specifically) — this protocol is the
   process-level defense that applies *now*, before that tooling exists.
3. **`claim.py move` leaving a duplicate tracked file** when a task transits two
   states without an intervening commit (`TASK-0189`, then `TASK-0073`,
   independently, same session) — not a merge-conflict failure mode exactly, but
   the same family of "the working tree was right, the index/HEAD silently
   wasn't" defect. `TASK-0198` is the open root-cause investigation. Named here
   because the detection step below (verify counts, don't just trust a clean
   `git status`) is the same discipline that catches this too.

## Detection — check before you assume you're in sync

- `git fetch origin` first, always — a local branch's tracking info
  (`git branch -vv`) can silently go stale across a long session; this protocol
  was written after a real divergence sat unnoticed until directly asked about
  (11 local commits ahead, 1 remote commit behind, found only when the user
  pointed at VS Code's own git log view).
- `git branch -vv` after fetching — read `ahead`/`behind` literally. `ahead only`
  is the common, safe case (ready to push once rebased if `behind` is nonzero
  too). `behind only` means a plain fast-forward pull is sufficient. **`ahead`
  *and* `behind` both nonzero is the real case this protocol is for.**

## Pre-check — verify before you rebase, don't guess

Before running an actual rebase (which touches the working tree and rewrites
commit hashes), preview whether it would even conflict, non-destructively:

```
git merge-tree --write-tree <local-branch> <remote-branch>
```

- **Exit 0, single tree SHA printed, nothing else**: a clean three-way merge is
  possible — no textual conflict on any file. Safe to proceed to the rebase
  below with real confidence, not an assumption.
- **Nonzero exit / conflict hunks printed**: a real conflict exists. Do not
  attempt to resolve it inside `merge-tree`'s own output — that command is a
  preview, not a working resolution step. Proceed to rebase and resolve
  in-place (below), now knowing which files need hand attention before you
  start, not discovered mid-rebase.

This command touches nothing — no working-tree changes, no ref updates. Safe to
run at any time, including mid-task, as a standing sanity check.

## Resolution order — rebase, not merge

**Always `git fetch` + rebase local commits onto the remote, never a merge
commit**, per `CLAUDE.md`'s own convention. Reasons specific to this repo, not
generic git style preference: every commit here is scoped to one task
(`TASK-XXXX: ...`), and a merge commit would bury that one-task-one-commit
correspondence inside a merge node that has no task of its own. Rebase replays
each local commit on top of the remote's, preserving the per-task history a
reader (or `git log --oneline -- <path>`, used constantly throughout this
scaffold) depends on.

Only rebase commits **not yet pushed** — rewriting hashes for commits someone
else may have already fetched/based work on is the actual destructive case
`CLAUDE.md`'s git-safety rules warn about. If in doubt whether a commit has
been seen elsewhere, ask before rewriting it.

## If a real conflict lands on `COMMON.md` or `RESULTS.md` specifically

**Both are append-only ledgers. The correct resolution for a genuine conflict on
either is almost always "keep both sides," never "pick one."** A conflict here
means two threads added *different* rows/sections that happened to land at the
same anchor point (usually: both appending at what each side believed was the
current end of a table) — it is not, in the normal case, two threads disagreeing
about the *same* row's content. Concrete rule:

- **Never** resolve with `git checkout --ours` / `--theirs` on these two files —
  either one silently discards a real, wanted row. If you catch yourself reaching
  for either flag on `COMMON.md`/`RESULTS.md`, stop and hand-merge instead.
- Hand-merge by keeping both sides' inserted lines, in whichever order is
  least disruptive to renumbering (for `RESULTS.md`'s numbered open-questions
  table specifically: append the "losing" side's rows *after* the "winning"
  side's, renumbered to continue sequentially — exactly the recovery pattern
  `61b8096` already used — never overwrite an existing row's number).
  If a `TASK-XXXX` row number collision is the actual cause (two threads filed
  the same id), that is a numbering bug to fix at the source
  (`claim.py reserve-next`), not something to paper over in the merge.
- **Verify by count, not by "no conflict markers remain."** After resolving,
  confirm the row/section count only *increased* relative to both parent sides
  — `grep -c '^| TASK-' .ai/COMMON.md` and the equivalent for `RESULTS.md`'s
  numbered table — before committing the resolution. A merge that "looks clean"
  but silently dropped a row is exactly incident #2 above, and it will not
  announce itself.

## `GIT-COMMIT` claim covers the whole rebase-and-push window

Extend the existing claim discipline (`.ai/COMMON.md`'s Current Rules,
TASK-0028/TASK-0042): claim `GIT-COMMIT` before starting the rebase, not only
before an individual `git commit`. A rebase touches every commit in the local
range and the eventual push is the shared-state action other threads need
warned about — the claim should cover that entire window, released only after
the push succeeds (or the rebase is abandoned).

## After resolving: re-verify before pushing

- Row/section counts (above) for any ledger file touched.
- `python3 .ai/tools/claim.py sync --check` — confirms `COMMON.md`'s claim
  columns still match the lock files after the rebase touched that file.
- If any `__WORK_IN_PROGRESS__/src` or `backend/` file was part of the
  conflict: `python3 .ai/tools/pytest_local.py all --json` — a conflict
  resolution is code, and code that "resolved cleanly" by inspection has not
  been tested until it's actually run.
- Only then: push, with `GIT-COMMIT` still held, released immediately after.

## What this protocol does not cover

- The actual tooling fix for `RESULTS.md`'s row-number fragility
  ([[TASK-0195]], open) — this protocol is the manual process that applies
  until that lands, not a substitute for it.
- The `claim.py move` duplicate-file defect ([[TASK-0198]], open) — a related
  but distinct failure mode, not a merge conflict.
- Conflicts on files *not* shaped like an append-only ledger (e.g. two threads
  editing the same function's body) — ordinary line-level conflict resolution
  applies there; "keep both sides" is specifically a ledger-file rule, not a
  general one. Don't over-apply it to source code.
