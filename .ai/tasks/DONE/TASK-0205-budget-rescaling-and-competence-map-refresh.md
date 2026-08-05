# TASK-0205 The multiplicity budget got one of its two corrections, and `COMPETENCE_MAP.md` is stale for the third time

## Context

- ID: TASK-0205
- Title: apply [[TASK-0199]]'s effective-rank rescaling to the multiplicity
  budget paragraph, refresh `COMPETENCE_MAP.md` with the four results it is
  missing, and add a standing rule so this stops recurring.
- Status: Done
- **Thread: Architect/Planner (synthesis / narrative).** Same thread as
  [[TASK-0207]] — both are `RESULTS.md`/`COMPETENCE_MAP.md` edits and must not
  be split across threads while three threads are writing concurrently.
- Owner: Architect/Planner
- Claimed By: —
- Claimed At: —
- Source: Reviewer thread, 2026-08-05, findings H1 and H2.
- Priority: **P1 — both defects are in documents [[TASK-0184]] pulls from
  directly, and the freeze is imminent.**
- Dependency: [[TASK-0199]], [[TASK-0201]], [[TASK-0200]], [[TASK-0190]]
  (all Done).

## Why this matters

**H1 — the budget paragraph received one of the two corrections it needed.**
`RESULTS.md`'s multiplicity-budget section currently argues:

> *"Zero confirmed positives against an expected ~18.3 is a stronger position
> than zero against ~11.3."*

Both halves are now wrong, and only one was fixed:

- **"Zero"** — no longer true. [[TASK-0201]]'s PTP1B `dcc_low` survival is
  **correctly** flagged in a caveat block immediately below. Handled well.
- **"~18.3"** — not the right denominator. [[TASK-0199]] measured that the 28
  observable types collapse to effective rank ~3, a **~9× redundancy factor**,
  and its own Done section computes the rescaled expectation at **~2**. Its
  verdict sentence states this explicitly. **That correction never reached the
  budget section.**

The direction matters: zero-against-~2 is a **substantially weaker** claim
than zero-against-~18.3, and the paragraph's whole rhetorical move ("more
cells makes the claim stronger") is exactly what the redundancy finding
undercuts — more *non-independent* cells do not strengthen it. This is the
paragraph a referee will check the arithmetic on.

**H2 — `COMPETENCE_MAP.md` is stale for the third time in three weeks.**
Zero mentions of [[TASK-0190]], [[TASK-0199]], [[TASK-0200]], or
[[TASK-0201]]. Its per-target rows do not know that PTP1B now carries the
program's only surviving positive.

This is now a **pattern, not an incident**: [[TASK-0193]] fixed its stale
per-target narratives, [[TASK-0192]] added the [[TASK-0155]] genotype caveat
it was missing, and it has gone stale again within days. The document that
carries the submission's central per-target claim is systematically the last
thing updated. Fixing the content again without fixing the process buys ~4
days.

## Intent Contract

- Outcome: a budget paragraph that states both corrections, a
  `COMPETENCE_MAP.md` current as of the latest result, and a stated rule
  binding future tasks to update it.
- Why required, not assumed: three catch-up tasks in three weeks on the same
  document is a process defect, and the budget arithmetic is a headline
  number in a document about to be frozen.
- In Scope:
  - **Budget paragraph**: add the [[TASK-0199]] rescaling alongside the
    existing [[TASK-0201]] caveat, in the same no-silent-overwrite shape.
    State the honest combined reading: the observed count is no longer zero
    **and** the expectation it is measured against is ~2, not ~18.3. Do not
    soften either half.
  - **`COMPETENCE_MAP.md`**: add [[TASK-0190]]/[[TASK-0199]]/[[TASK-0200]]/
    [[TASK-0201]]. Minimum bar — PTP1B's row must state the surviving
    positive with its bar, CI, and the null it was measured against; the
    document-level caveat block must carry [[TASK-0199]]'s effective-rank
    finding and [[TASK-0200]]'s strict-subset verdict.
  - **The standing rule** (the part that stops the recurrence): a one-line
    convention in `.ai/COMMON.md` — *any task whose result changes a
    per-target verdict, floor, actual, or headline number updates
    `COMPETENCE_MAP.md` in the same commit*, mirroring `CLAUDE.md`
    convention #7's shape for `ARCHITECTURE.md`. Cheap, and it is the same
    mechanism that keeps the product docs honest.
  - Consider whether the rule is enforceable by the [[TASK-0042]] hook or a
    test rather than convention alone. Recommend, do not build here.
- Out Of Scope:
  - Re-deriving any number. Every figure needed already exists in a Done task.
  - A full cell-by-cell re-derivation of the 366-cell count folding in both
    cross-observable and within-family redundancy — [[TASK-0199]] explicitly
    named that as a follow-up it did not build, and it stays out of scope
    here. The illustrative proportional rescaling is what lands.
  - Deciding how PTP1B's positive is *framed* in the submission — that is
    [[TASK-0184]]'s call. This task makes the documents accurate, not
    persuasive.
- Constraints And Invariants:
  - `git pull --rebase` immediately before editing `RESULTS.md`, per
    [[TASK-0202]]'s protocol. Three threads are writing concurrently and this
    file has lost content twice.
  - `claim.py scq-enter` before staging.
  - No-silent-overwrite: both corrections are additive caveats, not rewrites
    of the original text.
  - The corrections move the program's headline **against** it. State them
    plainly; the register's credibility is built on exactly this.
- Planned Validation:
  - After editing, re-read the budget paragraph cold: does it now state the
    observed count and the expectation consistently, without a reader having
    to reconcile a caveat against a contradicting sentence above it?
  - `grep` `COMPETENCE_MAP.md` for each of the four task IDs — all present.
  - Confirm the new convention line is in `.ai/COMMON.md`'s Current Rules,
    where a new thread will actually read it.

## In Progress

—

## TODO

- [x] `git fetch` + `git branch -vv` per [[TASK-0202]]'s protocol — clean,
      `bartosz` exactly matched `origin/bartosz` at the time of editing, no
      rebase needed.
- [x] Budget paragraph: add the [[TASK-0199]] rescaling caveat, additive,
      alongside the existing [[TASK-0201]] caveat, plus a combined-reading
      capstone paragraph so a reader doesn't have to reconcile the two
      caveats against the contradicting headline sentence above them
      unassisted.
- [x] `COMPETENCE_MAP.md`: add 0190 / 0199 / 0200 / 0201 — a new dated
      "Status update" entry in the document-level caveat block (all three
      findings) plus a dedicated PTP1B addendum.
- [x] PTP1B row: state the surviving positive with bar, CI, and null —
      done, explicitly scoped as a different observable family from the
      table row's own `H_new`/CTQW number (not superseding it).
- [x] Standing rule into `.ai/COMMON.md` Current Rules.
- [x] Recommend (not build) hook/test enforcement — recorded directly in
      the new Current Rules bullet: a TASK-0042-style hook or a
      RESULTS.md-vs-COMPETENCE_MAP.md citation-check test, if this recurs
      a fourth time. Judgment stated: convention #7 alone already failed
      five times on ARCHITECTURE.md before TASK-0194, which is real
      evidence against "convention is enough," recorded rather than
      ignored.
- [x] Cold re-read of the budget paragraph as acceptance — reads
      coherently: original claim, both caveats, then a combined reading
      that states the honest net position without leaving the
      reconciliation to the reader.

## Dependency

- [[TASK-0199]], [[TASK-0200]], [[TASK-0201]], [[TASK-0190]] (all Done).
- [[TASK-0202]] (In Progress) — the merge protocol this task follows.
- Feeds [[TASK-0184]].

## Open Questions

- Should the budget section be restructured so the current number is at the
  top and the history below — the shape `COMPETENCE_MAP.md` already uses
  successfully for its own superseded tables? It has now accreted two
  caveat blocks under a headline sentence that contradicts both.
  **Recommendation confirmed after doing the edit: yes** — the combined-
  reading capstone paragraph added here is a workaround for the section's
  current bottom-loaded shape, not a fix to it. Left as a separate small
  task (not filed here, per this task's own Out Of Scope on restructuring)
  since it's pure reformatting of already-correct content, lower urgency
  than the two content corrections this task actually needed to land
  before the freeze.
- Is convention enough for `COMPETENCE_MAP.md`, given convention #7 was
  missed five times running on `ARCHITECTURE.md` before [[TASK-0194]]? That
  precedent argues for the hook. **Judgment recorded: no, convention alone
  is not enough**, on the ARCHITECTURE.md precedent directly — stated as
  such in the new `.ai/COMMON.md` bullet itself, with the recommended next
  step (hook or citation-check test) named rather than left implicit. Not
  built here — this task's own scope is the content fix and stating the
  rule, per its own In Scope wording ("recommend, do not build here").

## Done

**2026-08-05, Architect.**

**H1 fixed**: `RESULTS.md`'s multiplicity-budget section now carries both
corrections. Added a new `TASK-0199` caveat block (effective rank ~3 of
28, ~9× redundancy, rescaled expectation ~18.3 → ~2), additive alongside
the existing `TASK-0201` caveat, plus a combined-reading capstone
paragraph stating the honest net position (observed count no longer
zero, and the expectation it's measured against is ~2, not ~18.3) so a
cold reader doesn't have to reconcile two caveats against a contradicting
headline sentence unassisted. No existing text edited or removed —
purely additive, per this project's no-silent-overwrite convention.

**H2 fixed**: `COMPETENCE_MAP.md` updated in two places — a new dated
"Status update, 2026-08-05" entry in the document-level caveat block
covering all three findings (TASK-0199's redundancy, TASK-0201's PTP1B
flip, TASK-0200's strict-subset verdict), and a dedicated PTP1B addendum
in the generalization-targets section stating the surviving `dcc_low`
cell's exact bar, CI, and null construction — explicitly scoped as a
different observable family from that section's own `H_new`/CTQW table
row, not superseding it. `TASK-0190` cited alongside `TASK-0201` (the
prior null's structural Rg ceiling is why the earlier reading was
unreliable, not just superseded). All four dependency task IDs confirmed
present via direct grep (2 occurrences each for 0190/0199/0200, 5 for
0201) before considering this done, not assumed from having written them.

**Standing rule added**: `.ai/COMMON.md` Current Rules gained a
`COMPETENCE_MAP.md` currency bullet (any per-target-verdict-changing
result updates that document in the same commit, mirroring `CLAUDE.md`
convention #7's own shape), with the enforcement judgment recorded
directly in the bullet rather than left as a separate note: convention
alone already failed on `ARCHITECTURE.md` (5 misses before TASK-0194), so
a hook or citation-check test is named as the likely next step if this
recurs a fourth time — recommended, not built, per this task's own scope.

**Both Open Questions answered** with a recorded judgment rather than
left open — see that section above.

**Process note**: followed [[TASK-0202]]'s own protocol as this task's
own Constraint required — `git fetch`/`branch -vv` before editing found
`bartosz` exactly in sync with `origin/bartosz` (no rebase needed), and
`claim.py scq-enter` was used before staging (see commit history) given
three threads writing concurrently to these same files this session.

Full validation: cold re-read of the budget paragraph (coherent, stated
above); `grep` confirmed all four task IDs in `COMPETENCE_MAP.md`; the new
Current Rules bullet cross-checked against the full edit for consistency.
