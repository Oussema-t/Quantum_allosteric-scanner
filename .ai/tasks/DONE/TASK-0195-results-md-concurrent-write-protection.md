# TASK-0195 `RESULTS.md` has no concurrent-write protection — two silent losses already in history

## Context

- ID: TASK-0195
- Title: extend the project's existing claim/lock discipline to `RESULTS.md`'s
  shared tables, and replace row-number cross-references with task-ID ones so
  a renumber cannot silently invalidate a pointer.
- Status: Done
- Owner: Toolsmith (with Architect/Planner on the convention half)
- Claimed By: —
- Claimed At: —
- Source: Architect/Planner incident report, 2026-08-03 (open-questions rows
  47–53 lost in the [[TASK-0171]] merge, recovered in `61b8096`); Reviewer
  thread, 2026-08-03, finding F3 (the [[TASK-0167.003]] section lost the same
  way, not yet recovered — see [[TASK-0191]]).
- Priority: **P1 — two confirmed silent losses in one week, on the document
  that is the submission's primary synthesis, with cross-machine concurrent
  work now the norm.**
- Dependency: [[TASK-0065]] (SCQ, Done), [[TASK-0024]]/[[TASK-0107]] (claim
  tooling, Done) — this task extends existing mechanisms rather than inventing
  one.

## Why this matters

Two distinct silent losses, both in `RESULTS.md`, both inside one week:

1. **Open-questions rows 47–53** — two independent lines of work
   ([[TASK-0182]], [[TASK-0185]]) both landed at row 51; a later batch built
   against an older snapshot ([[TASK-0015]]/[[TASK-0167.002]]/[[TASK-0155]]/
   [[TASK-0171]]) overwrote rows 47–53 on merge, taking out eight tasks' index
   entries plus a cross-reference note. **It merged clean — no conflict
   markers, nothing to catch it at commit time.** Recovered from `f5430de` and
   renumbered 52–59 (`61b8096`). [[TASK-0182]]'s own citation pointed at "row
   51" — accurate when written, silently invalidated by the collision.
2. **The [[TASK-0167.003]] section** — written, deliberately withheld from
   commit `92aa669` to avoid clobbering a concurrent thread's uncommitted
   `RESULTS.md` edit, follow-up never filed, content now gone. See
   [[TASK-0191]].

Neither was catastrophic: the `.ai/tasks/DONE/` records survived intact in
both cases. **That is the point** — the underlying ledger is protected and the
synthesis is not.

This is the same failure class `Q-0001` and [[TASK-0107]] already document for
`COMMON.md`, and that file got protection ([[TASK-0017]] claim columns,
[[TASK-0024]] claim tool, [[TASK-0045]] atomic ID reservation). `RESULTS.md`
has **none** — no claim, no lock, no numbering authority — despite being
edited by every thread that closes a task, now across machines.

Two independent weaknesses, and they need different fixes:

- **Write collisions** on a large append-mostly file that merges clean.
- **Positional cross-references**: `RESULTS.md` cites its own open questions
  by row number. Row numbers are not stable identifiers. Every renumber
  silently invalidates every pointer to them, with no way to detect it.

## Intent Contract

- Outcome: (a) a lightweight, whitelisted mechanism that makes a concurrent
  `RESULTS.md` edit visible before it merges; (b) a stated convention that
  cross-references cite task IDs, not row numbers; (c) a check that catches a
  dangling or positional reference.
- Why required, not assumed: two losses in one week, both silent, both
  merging clean. Convention alone did not prevent either — the withheld
  section in loss #2 was a thread *following* good practice and losing the
  content anyway.
- In Scope:
  - **Convention (cheap, do first):** cross-references cite `[[TASK-XXXX]]`,
    never "row N". Where a row number is genuinely needed, pair it with the
    task ID so a renumber degrades to a stale-but-traceable pointer rather
    than a silently-wrong one. Sweep the existing open-questions table and
    [[TASK-0182]]'s citation.
  - **Tooling (evaluate, then build the smallest thing that works):** extend
    `claim.py` with a whole-file resource claim covering `RESULTS.md` —
    [[TASK-0024.001]] already exists for exactly this and is TODO. Consider
    closing it here rather than duplicating it.
  - **Detection:** a check (test or pre-commit) that every `[[TASK-XXXX]]`
    reference in `RESULTS.md` resolves to a real file in `.ai/tasks/`, and
    that no open-questions row number is cited from outside its own table.
  - Assess whether the open-questions table should move to append-only with
    **stable, never-reused** IDs — the same discipline `claim.py reserve-next`
    already enforces for task numbers. Renumbering on collision is what turned
    loss #1 into invalidated pointers.
- Out Of Scope:
  - Splitting `RESULTS.md` into per-task files. Tempting, large, and it would
    lose the single-document synthesis value the project deliberately built.
    Name it as an option; do not do it here.
  - Hook enforcement — [[TASK-0042]] owns that.
- Constraints And Invariants:
  - Extend existing mechanisms. This scaffold already has three overlapping
    coordination tools; a fourth parallel one is a worse outcome than the bug.
  - The convention half must land even if the tooling half is deferred — it is
    free and it prevents the more insidious of the two failure modes.
- Planned Validation:
  - Replay loss #1: does the proposed mechanism actually surface it? A
    protection that would not have caught the incident that motivated it is
    not worth landing. **Demonstrate this, do not assert it.**
  - The dangling-reference check must fail against a deliberately broken
    reference before it passes against the real file.

## In Progress

—

## TODO

- [x] Convention: task-ID cross-references. Write it into `.ai/COMMON.md`.
- [x] Sweep the open-questions table + [[TASK-0182]]'s "row 51" citation.
- [x] Evaluate closing [[TASK-0024.001]] here vs. separately.
- [x] Build the dangling/positional-reference check; failing-first.
- [x] Replay loss #1 against the mechanism. Report honestly if it would not have caught it.
- [x] Decide + record: stable never-reused open-question IDs, or keep renumbering?

## Dependency

- [[TASK-0024.001]] (TODO) — whole-file resource locks. Likely subsumes the
  tooling half.
- [[TASK-0065]] (Done) — SCQ visibility.
- [[TASK-0191]] — the loss this task is meant to prevent recurring.
- [[TASK-0202]] (In Progress) — cross-linked, not a dependency: adopts the
  general merge-conflict resolution protocol as the *manual process* that
  applies until this task's own tooling fix lands. This task remains the
  deeper, `RESULTS.md`-specific fix (task-ID cross-references, a
  staleness/lock mechanism) — TASK-0202 does not substitute for it.

## Open Questions

- ~~Is a lock the right shape at all for an append-mostly file?~~ **Resolved
  — yes, but only a content-hash-checked one, not a git-ancestry one.**
  Reconstructed the actual mechanics of loss #1 from git history (`f5430de`,
  `a0f4dff`, `38a22f5`, `61b8096`) rather than assuming: `38a22f5`'s own
  commit message states directly that two other threads' `RESULTS.md` edits
  were "sitting only in the working tree, uncommitted" when its own splice
  began. Checked whether a git-ancestry staleness check (comparing a
  claimant's declared base commit to current HEAD) would have caught this:
  it would not have — every commit in the sequence was, by construction,
  correctly based on its true immediate git parent (`f5430de` is an ancestor
  of `38a22f5`; `a0f4dff` is an ancestor of `f5430de`'s own parent). A pure
  rebase-only, single-branch history cannot be "behind" its own parent, so
  an ancestry check would have reported clean the entire time. The actual
  divergence was purely at the working-tree level, invisible to git until
  commit. That means a **held claim taken before editing** (serializing
  access, exactly the `GIT-COMMIT` pattern already in use) directly
  addresses the real failure mode — a second thread attempting to start
  editing while the first holds the claim gets a loud, immediate error
  instead of silently colliding. Built and demonstrated both: (1) the claim
  itself, via [[TASK-0024.001]]'s general resource-id support (any
  digit-free claim argument, e.g. `RESULTS.md`, normalizes to
  `RESOURCE-<sanitized>` instead of erroring — verified end-to-end: claim,
  status, release, and `move`/`resolve` correctly refusing the non-task id);
  (2) `claim.py check-staleness <path>`, a content-sha256 snapshot taken at
  claim time (`cmd_claim`, when the raw argument is itself a real path) and
  compared against the file's current on-disk content — demonstrated live:
  claim a scratch file → `check-staleness` reports clean → the file is
  edited out from under the claim → `check-staleness` reports `STALE`
  (exit 1) and explains why. Deliberately content-based, not
  ancestry-based, given the finding above — this is the one piece of the
  original hypothesis this task's own filing got backwards, recorded
  honestly per the Planned Validation instruction rather than silently
  building the originally-assumed design.
- ~~Should the answer just be a hard convention — never edit `RESULTS.md`
  without an immediately-preceding `git pull --rebase`?~~ **Resolved — no,
  a convention alone was already shown insufficient** (loss #2, the
  withheld [[TASK-0167.003]] section, was a thread *following* good
  practice and losing the content anyway — Context section above). The
  claim + `check-staleness` pair above is the mechanical enforcement;
  `git pull --rebase` discipline remains necessary for real cross-machine
  divergence ([[TASK-0202]]'s protocol) but does not substitute for it.
- **Renumbering vs. stable never-reused open-question IDs — decided: keep
  renumbering.** The original loss made row numbers load-bearing pointers;
  once citations are task-ID-based (this task's own convention change) and
  mechanically checked (`check_references.py`), a row number is a
  best-effort locator only, and a renumber degrades to
  stale-but-traceable rather than silently wrong — the failure mode a
  stable-ID scheme would exist to prevent no longer has the blast radius
  it did. A dedicated stable-ID namespace (e.g. `Q-0001`, mirroring
  `claim.py reserve-next`'s TASK-number discipline) is a real, larger
  structural change and is not built here, per this task's own Constraint
  ("this scaffold already has three overlapping coordination tools; a
  fourth parallel one is a worse outcome than the bug"). Recommended as
  the next step only if a citation-pairing gap recurs after this task,
  not built pre-emptively.

## Done

**2026-08-16.** All three Intent Contract outcomes shipped: (a) a claim
mechanism making a concurrent `RESULTS.md`/`COMMON.md` edit visible before
it lands (not merges — see the resolved Open Question above for why "before
it merges" was the wrong frame); (b) the task-ID-not-row-number citation
convention, written into `.ai/COMMON.md`'s Current Rules; (c) a mechanical
dangling/positional-reference check.

**What shipped:**
1. `.ai/tools/claim.py`'s `normalize_task_id` widened to accept any
   digit-free claim argument as a literal resource id
   (`RESOURCE-<SANITIZED>`, namespaced so it can never collide with a real
   `TASK-XXXX` id) instead of erroring — closes [[TASK-0024.001]] as part of
   this task rather than duplicating it. `is_task_id` correctly returns
   `False` for these, so `move`/`resolve` refuse them cleanly and
   `status`'s no-arg listing displays them without a spurious "no task
   file" warning — both paths already existed for `GIT-COMMIT` and needed
   no further change. The `--hitl-override` gate stays scoped to
   `SPECIAL_RESOURCE_IDS` (`GIT-COMMIT` only), not generalized — verified
   by reading `cmd_claim`'s gate condition, unchanged.
2. `claim.py check-staleness <path>` (new subcommand) + a content-sha256
   snapshot recorded by `cmd_claim` whenever the raw claim argument is
   itself a readable path. Verified end-to-end (see resolved Open Question
   above for the full replay-based justification for this specific,
   content-hash design over the originally-assumed ancestry-based one).
3. `.ai/tools/check_references.py` (new): two independent checks against
   `RESULTS.md` (or any path given) — (1) every `[[TASK-XXXX]]` citation
   resolves to a real task file on disk (`claim.disk_task_ids()`, the same
   ground truth `claim.py` itself uses), with one explicit, documented
   exception (`TASK-9000`, the `val-9xxx` branch's deliberately
   out-of-register placeholder id — an allowlist in code, not a loosened
   check, so the exception stays auditable); (2) every bare `row N`
   reference shares its blank-line-delimited paragraph with a real
   `TASK-XXXX` token. Failing-first per the Planned Validation requirement:
   a synthetic fixture with a dangling `[[TASK-9999]]` and an unpaired
   `row 5` was built and confirmed caught (2 findings, exit 1) before
   running clean against the real file (exit 0).
4. `RESULTS.md` line ~6644 fixed — the one real unpaired "row 33" reference
   found by the sweep (all other `row N` occurrences already had a
   `TASK-XXXX` token within their own paragraph; [[TASK-0182]]'s specific
   "row 51" citation named in this task's own filing was already corrected
   by [[TASK-0191]]'s earlier recovery work, confirmed by direct reading
   rather than re-fixing something already fixed).
5. `.ai/COMMON.md`'s Current Rules gained the `RESULTS.md` claim +
   citation convention entry, cross-referencing this task, right after the
   [[TASK-0202]] merge-conflict-protocol entry it's meant to eventually
   reduce reliance on (that protocol remains the correct manual fallback
   for real cross-machine git divergence — a different failure mode from
   the one this task addresses).

**Implementer's-call decisions:**
- Scoped `check-staleness`'s content-hash snapshot to only fire when the
  raw claim argument is itself a real, readable path (not every claim) —
  keeps `TASK-XXXX`/`GIT-COMMIT` claims exactly as before, zero behavior
  change for the majority of existing `claim.py` usage.
- Did not attempt to make the dangling-reference check part of a hook
  ([[TASK-0042]] owns hook enforcement generally, and this task's own Out
  Of Scope explicitly excludes hook enforcement) — `check_references.py`
  is a standalone script, run manually or from a future hook, not wired
  into one here.
- Did not build a stable never-reused open-question ID scheme — see the
  resolved Open Question above for the reasoning; recommended, not built.

**Not done, and why:**
- `RESULTS.md`/`COMMON.md` claims are not yet actually held during *this
  task's own* edits to those files in the conventional claim-first order —
  the convention and tooling were built and then applied to this task's
  own edits retroactively rather than claim-first throughout, since the
  mechanism didn't exist yet at the start of this session. `git diff`
  against `HEAD` was checked before every edit to both files instead
  (this session's established discipline) and confirmed clean each time —
  no actual collision occurred, but this is not a substitute for using the
  now-built mechanism going forward.
- No CI/hook wiring for `check_references.py` — a manual check today,
  per the Out Of Scope note above.

**Validation:** `python3 .ai/tools/check_references.py` → clean on the real
`RESULTS.md` (0 findings) after the line-6644 fix, and correctly non-zero
against a deliberately broken synthetic fixture before that. `claim.py`'s
existing `.ai/tools/test_claim.py` (regression coverage from
[[TASK-0198]]) gained a `TestResourceIdSupport` class (5 tests: claim/
status/release round-trip on a digit-free resource id; a second claim on
the same resource id refused; `move`/`resolve` refusing a resource id;
a digit-bearing argument still resolving as `TASK-XXXX`, a regression
guard on the pre-existing behavior) and a `TestCheckStaleness` class
(4 tests: clean immediately after claim; drift correctly detected and
reported `STALE`; a missing claim refused with a clear message; a
non-path resource id like `GIT-COMMIT` reporting "nothing to compare"
rather than crashing or false-flagging) — all subprocess-driven against
an isolated scratch repo, this file's own established pattern, never the
real project repo. New `.ai/tools/test_check_references.py` (7 tests)
copies both `check_references.py` and `claim.py` into its own scratch
repo (needed for true isolation — `disk_task_ids()` otherwise resolves
against whatever repo `claim.py` was imported from) and directly verified
against a task id present only in the scratch fixture (`TASK-8001`,
confirmed absent from the real repo) that the check is not silently
validating against real project data. `.ai/tools/test_claim.py`: 15
passed. `.ai/tools/test_check_references.py`: 7 passed. Full
`__WORK_IN_PROGRESS__` suite (unaffected by this task, run for
regression coverage on the broader repo): 1196 passed, 1 skipped, 3
xfailed.

**Addendum, same session, an unplanned live demonstration:** while this
task's own edits to `claim.py`/`COMMON.md`/`test_claim.py` sat
uncommitted (correctly *not* staged, per the discipline this task itself
documents — waiting for a concurrently-held `GIT-COMMIT` claim to
release), the peer session holding it (`Implementer B`, [[TASK-0198]])
committed first. Their `git add` on those same three shared files staged
whatever was in the working tree at that moment — which, since this
task's own edits live in the same physical files, included this task's
own uncommitted `RESULTS.md`-protection changes too. Commit `a9295a6`
("TASK-0198: guard claim.py chained transitions...") therefore also
carries this task's `normalize_task_id` widening, `check-staleness`, the
`content_sha256` snapshot, this task's `COMMON.md` rule, and this task's
two new `test_claim.py` classes — correct in content (re-verified: both
test files still pass in full against the post-commit state, 22/22), but
misattributed to a commit message that doesn't mention them. Not
rewritten here (no history rewrite without explicit instruction) — noted
plainly instead, because it is directly relevant evidence for this task's
own subject matter: a real, un-staged-for-effect example of a shared-file
edit landing in the wrong place through nobody's individual fault, one
`git add`, no malice, no missed check. Two honest implications: (1) had
this task's own new `check-staleness`/claim discipline actually been used
on `claim.py`/`COMMON.md` themselves while editing them (dogfooding,
not just building), this specific mix-up would not have prevented it
either — a bare `git add <path>` still stages the whole file regardless
of who holds which claim, since nothing currently *enforces* the claim
before `git add`, it is convention only; (2) `commit-guard --expect
<path>` verifies the staged *path list* matches what you declared, not
that the staged *diff* is scoped to only your own intended change — a
real, previously undocumented gap, since a legitimately-expected path can
still carry someone else's mixed-in content. Recommended, not built
here (would expand this task's own scope past its Constraint): a
`commit-guard` mode that also diffs each expected path's staged content
against a caller-supplied "this is what I intended to change" set, for
paths known to be claim-protected.
