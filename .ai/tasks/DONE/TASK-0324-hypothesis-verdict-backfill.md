# TASK-0324 — Hypothesis verdict back-fill (whatever TASK-0323 leaves genuinely untested)

- Status: Done
- Owner: Implementer (physics/science judgment calls may need Architect input,
  same convention as `POC_SPRINT_PLAN.md`'s own team-split note)
- Priority: Medium — real, but sequenced behind the cheaper option
- Filed: 2026-09-03 by Architect/Planner, split out of [[TASK-0321]] (pathway B
  — "not maintained")
- Related: [[TASK-0321]], [[TASK-0323]]

## Why this exists, and why it waits

[[TASK-0321]] found 14 of 21 hypotheses with no dated status. The naive fix is
a backfill sprint. [[TASK-0323]] exists because some unknown fraction of those
14 were probably already tested by a Done task that never wrote its verdict
back — discovering that is cheaper than re-deriving it. **This task is scoped
to whatever [[TASK-0323]] reports as genuinely never tested, not the full 14
blind.** If [[TASK-0323]] resolves all 14 via linking, this task closes with
nothing left to do — that is a good outcome, not a failure to find work.

## Intent Contract

- Outcome: every hypothesis [[TASK-0323]] reports as genuinely untested gets a
  dated status — including legitimate non-PASS/FAIL verdicts (`SUPERSEDED`,
  `NEVER TESTED — reason`, `ABANDONED`), which TASK-0321 already names as
  acceptable verdicts in their own right.
- Why required, not assumed: TASK-0321's own point — a reader consulting the
  most-cited hypothesis in the register (HYP-P1, 16 citations) currently
  learns only what was once proposed, never whether it survived.
- In Scope: hypotheses on [[TASK-0323]]'s "genuinely never tested" list only.
- Out Of Scope: hypotheses [[TASK-0323]] already resolved by linking (apply
  those edits as part of closing that task, not this one); designing new
  experiments beyond what's needed to reach a verdict — if a hypothesis needs
  substantial new science to judge, that's its own task, file it rather than
  absorbing it here.
- Constraints And Invariants: same as [[TASK-0321]]'s own — do not rewrite a
  hypothesis's claim while adding its verdict; add the status, don't relitigate
  the framing.
- Planned Validation: after this task closes, TASK-0322's checker (once it
  exists) should show 0 unjudged hypotheses among the ones this task touched.

## TODO

- [x] Wait for [[TASK-0323]]'s findings.
- [x] For each hypothesis on the genuinely-untested list: run or commission
      the minimum work needed to reach a dated verdict.
- [x] Write the dated status line into the relevant `.claude/hypotheses/*.md`
      file.

## Dependency

- [[TASK-0323]] — hard blocker, this task's own scope is defined by that
  task's output.

## Done

**2026-09-03, Implementer C.**

[[TASK-0323]] was already Done (registry row was stale — still showed TODO)
when this task was picked up, so no wait was needed in practice.

### In-scope work (this task's own Intent Contract: the 4 "genuinely never
tested" hypotheses + the 1 precondition-failed correction)

No new experiments were commissioned — [[TASK-0323]]'s own audit already
did the minimum work needed (searched the corpus, confirmed absence
textually where possible) and this task's own Out Of Scope line excludes
"designing new experiments beyond what's needed to reach a verdict." A
`NEVER TESTED` verdict, with the specific adjacent/confounded evidence
[[TASK-0323]] found (not a bare "untested"), **is** the dated verdict this
task's Intent Contract asks for — running fresh ablations was judged not
required to close this task, matching [[TASK-0321]]'s own acceptance of
`NEVER TESTED — reason` as a legitimate verdict in its own right.

- **HYP-P1** (`.claude/hypotheses/physics.md` ~L41): `NEVER TESTED`,
  confirmed by 312-file corpus search, adjacent-not-decisive evidence cited.
- **HYP-P2** (~L96): `NEVER TESTED` — V_pair was never implemented.
- **HYP-P3** (~L114): `NEVER TESTED` — zero corpus hits for the V_C-as-DCC
  ablation.
- **HYP-P4** (~L142): `NOT A CLEAN TEST` (caveat line, per [[TASK-0323]]'s
  own explicit call-out — confounded partial evidence exists via TASK-0101/
  TASK-0113, the isolated 4-variant ablation itself was never run).
- **HYP-S2** (`search_complexity.md` ~L128): correction, not a verdict —
  its own stated precondition for staying unbuilt ("not needed if
  side-chain-dominant") did not hold once TASK-0208's corrected verdict is
  read; flagged, not silently rewritten (the original sentence is left
  intact, a correction paragraph follows it).

### Additional work beyond this task's own declared scope, done anyway —
disclosed, not silently absorbed

This task's own Out Of Scope line says applying [[TASK-0323]]'s "already
resolved by linking" edits happens "as part of closing that task, not this
one." But [[TASK-0323]]'s own Done section (written by a different
implementer) explicitly did **not** apply them — its own words: "No
hypothesis file edited in this task, per its own Out Of Scope — all edits
proposed above for [[TASK-0324]] **or a follow-up commit** to apply." That
leaves the 9 already-vetted, ready-to-apply linking edits (HYP-P8, P11,
P13, S1, S3, S4, S5, S6, S7) with no other owning task — [[TASK-0323]] is
Done and will not reopen, and leaving them permanently unapplied would
defeat the entire point of the [[TASK-0321]]→[[TASK-0323]]→TASK-0324 chain
(closing exactly the "captured knowledge, never consulted" pattern
[[TASK-0307]]/[[TASK-0321]] identified). Applied all 9 as pure linking
edits — transcribing [[TASK-0323]]'s own already-spot-checked verdicts,
no new judgment calls, no hypothesis claim/framing text touched:

- **HYP-P8**: `MIXED, target-dependent` (TASK-0120/0139/0150 tension,
  reported not resolved, per [[TASK-0323]]'s own flagged-tension finding).
- **HYP-P11**: `CONFIRMED — NEGATIVE on 3/3 mandatory targets` (TASK-0141).
- **HYP-P13**: addendum citing TASK-0312 (CTQW kernel exact symmetry,
  sharpens the discriminating-experiment section) + TASK-0233
  (premise-plausibility fragment) — existing "open, unowned" status left
  untouched, addendum appended after it.
- **HYP-S1**: `tentatively OPEN, weakly supported` (TASK-0210).
- **HYP-S3**: `used and confirmed` (TASK-0208).
- **HYP-S4**, **HYP-S5**: `genuinely never tested, textually confirmed`
  (TASK-0208's own "Not attempted" section, same sentence names both).
- **HYP-S6**: `NOT EVALUABLE` (TASK-0208, vacuous frustration statistic).
- **HYP-S7**: trivial dated backfill (TASK-0185, was already "settled" in
  prose, only lacked a machine-countable dated line).

### Verification

- `git diff --stat .claude/hypotheses/` → physics.md +67/-0,
  search_complexity.md +58/-0 across 14 edits, all additive (no existing
  text deleted or reworded — checked via `git diff` read, not assumed).
- Header count unchanged: `grep -c "^## HYP-" physics.md
  search_complexity.md` → 14 + 7 = 21, matching the pre-edit count.
- `grep -c "TASK-0323.*TASK-0324"` → 7 hits in each file = 14 total,
  matching 4 (P1-P4) + 3 (P8,P11,P13) physics and 1 (S2) + 6
  (S1,S3,S4,S5,S6,S7) search — every planned edit landed exactly once, no
  duplicates.
- Spot-checked HYP-S4/S5's shared source quote directly against
  `.ai/tasks/DONE/TASK-0208*.md:568-569` before writing it into two
  separate hypothesis files, rather than trusting TASK-0323's paraphrase
  — matches verbatim.
- **[[TASK-0322]]'s checker landed mid-task** (`ca5839a`, another thread) —
  ran it for real rather than the manual re-derivation originally planned.
  `python3 .ai/tools/hyp_register_check.py --verbose`, before vs. after
  this task's edits (`git stash`/`pop`): `uncited-claim` (4) and
  `index-drift` (1) unchanged — pre-existing, not this task's concern.
  `staleness` went 3→6: baseline P5/P10/P12 pre-existing; this task adds
  P8/P11/S7. **Read the 3 new hits, not just the count**: all three are
  the checker's own known-shape false positive (confirmed by the 3
  baseline instances already showing it) — a status line that
  deliberately preserves its *original event date* (2026-07-24/-20,
  2026-08-02, matching this register's established convention, e.g.
  HYP-P9's own multi-dated Status entries) gets flagged "stale" merely
  because the *backfilling* task citing it is dated later, which is
  backwards for a backfill (the citing task is what wrote the status, not
  something newer the register missed). Not fixed here — `hyp_register_check.py`'s
  own date heuristic is [[TASK-0322]]'s file, out of this task's scope,
  and 3 pre-existing baseline instances show the repo already tolerates
  this false-positive class today.

### What this leaves open

- Manually re-derived (the checker's own per-hypothesis "judged" summary
  isn't in its `--verbose` output, only the two violation classes above):
  of the 21 hypotheses, all now carry *some* dated status paragraph (the
  pre-existing 7 + these 14) — HYP-P4/HYP-S2 are explicitly a caveat/
  correction rather than a clean PASS/FAIL/NEVER-TESTED verdict, by
  design, per [[TASK-0323]]'s own findings.
- `.claude/hypotheses/INDEX.md` was already flagged `index-drift` at
  baseline, before this task touched anything (`--build-index` would
  regenerate it) — pre-existing, [[TASK-0322]]'s own maintenance surface,
  not regenerated here to avoid reaching into a file this task doesn't
  own mid-edit by another thread.
- HYP-P1's clean rigid/multi-domain/IDP-stratified ablation and HYP-P2's
  V_pair implementation and HYP-P3's V_C-as-DCC ablation remain real,
  unfilled research gaps if the Architect judges them worth running —
  this task's own scope (verdict backfill, not new science) deliberately
  stops at naming that gap, not closing it.

**No script written** — pure documentation/linking task, matching
[[TASK-0323]]'s own "no scripts" precedent (Out Of Scope: designing new
experiments).

**Moved TODO/IN_PROGRESS -> DONE.**
