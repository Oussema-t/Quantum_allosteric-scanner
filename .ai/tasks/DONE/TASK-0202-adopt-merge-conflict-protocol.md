# TASK-0202 Adopt a merge/rebase conflict resolution protocol

## Context

- ID: TASK-0202
- Title: incorporate `.ai/reference/MERGE_CONFLICT_PROTOCOL.md` as a real,
  running practice — a `.ai/COMMON.md` Current Rules bullet stating the
  gate, and cross-links from the three real incidents that motivated it.
- Status: Done
- Owner: Architect/Planner
- Claimed By: Architect
- Claimed At: 2026-08-05
- Source: orchestrating collaborator (Bartosz), 2026-08-05 — after a real
  local/remote branch divergence was found (11 local commits ahead, 1
  remote commit behind, on `bartosz`) and verified non-destructively via
  `git merge-tree --write-tree` before acting on it, asked to set a
  preferred, reusable resolution pattern for future cases rather than
  re-deriving one ad hoc each time.
- Crit Ref: not a hypothetical policy — grounded directly in three real
  incidents already on record: the `COMMON.md` whole-file collision
  (`Q-0001`, TASK-0107), the `RESULTS.md` silent row-loss (recovered
  `61b8096`, [[TASK-0195]] still open for the deeper fix), and the
  `claim.py move` duplicate-file defect ([[TASK-0198]], open). Same
  pattern as [[TASK-0050]]/[[TASK-0051]]'s own adoption precedent — a
  protocol doc formalizing a lesson already paid for, not a preemptive
  process addition.

## Intent Contract

- Outcome: the merge conflict protocol is a stated scaffold rule, not a
  document nobody is pointed at — a `.ai/COMMON.md` Current Rules bullet
  (matching the Seam/Invariance gate bullets' own style) states the
  headline rules (fetch+`branch -vv` before assuming sync, `merge-tree
  --write-tree` before rebasing, rebase not merge, "keep both sides" for
  ledger-file conflicts, `GIT-COMMIT` claim covers the whole rebase-push
  window) and points to the full doc.
- Why required, not assumed: `CLAUDE.md` already states "fetch + rebase
  before push" as a bullet convention, but names no procedure for *what
  to do when that fetch reveals real divergence* — the exact gap this
  session's own incident fell into (a divergence that sat unnoticed for
  two days).

- In Scope:
  - `.ai/reference/MERGE_CONFLICT_PROTOCOL.md` — **written, this
    session**, ahead of the rest of this task's TODO (pure content, zero
    mechanical risk, matches TASK-0050's own precedent of doing the
    zero-risk part first).
  - `.ai/COMMON.md` Current Rules: one new bullet, same shape as the
    Seam gate (TASK-0050)/Invariance gate (TASK-0051) bullets directly
    above it.
  - `.ai/COMMON.md` Quick Navigation: one line pointing to the new doc,
    matching every other reference doc's own entry there.
  - Cross-link from [[TASK-0195]] (the deeper `RESULTS.md`-specific
    tooling fix this protocol's manual process stands in for until it
    lands) and [[TASK-0198]] (the related but distinct duplicate-file
    defect) — both ways, so a reader starting from either task finds
    this one.
  - Resolve the actual divergence this task was filed in response to
    (rebase local `bartosz` onto `origin/bartosz`, verified clean via
    `merge-tree` already) as this task's own first real application of
    the protocol it adopts — same posture TASK-0050 took relocating
    `SEAM_PROTOCOL.md` as part of adopting it, not a separate task.

- Out Of Scope:
  - Building [[TASK-0195]]'s actual tooling (task-ID cross-references,
    a staleness/lock mechanism for `RESULTS.md`) — this task adopts the
    *process* that applies until that tooling exists, it does not build
    the tooling itself.
  - Fixing [[TASK-0198]]'s root cause — unrelated defect, cross-linked
    only.
  - Any change to `claim.py`'s own commands — this protocol is a
    documented practice around existing tools (`git merge-tree`, `git
    branch -vv`, the existing `GIT-COMMIT` claim), not a new subcommand.

- Constraints And Invariants:
  - The "keep both sides" ledger-file rule is scoped explicitly to
    append-only tables (`COMMON.md`'s registry, `RESULTS.md`'s
    findings/open-questions) — the doc itself states this is not a
    general conflict-resolution rule, so this task's own Current Rules
    bullet must carry that scope note too, not just the full doc.

- Planned Validation:
  - `.ai/COMMON.md`'s new bullet cross-checked against the full doc for
    consistency (no contradicting the doc it summarizes).
  - The actual `bartosz`/`origin/bartosz` divergence resolved via this
    protocol's own steps (fetch — already done; `merge-tree --write-tree`
    pre-check — already done, clean; rebase; verify row counts on
    `COMMON.md`/`RESULTS.md` unchanged by the rebase itself since no
    conflict was expected; push) — a real end-to-end run of the protocol
    just adopted, not merely a documented intention.

## In Progress

- 2026-08-05 (Architect): protocol doc written; this task file filed in
  the same pass. Wiring `COMMON.md` and resolving the live divergence
  next.

## TODO

- [x] Write `.ai/reference/MERGE_CONFLICT_PROTOCOL.md`.
- [x] Add the Current Rules bullet to `.ai/COMMON.md`. Landed at some
      point during this session's own subsequent work (found already
      present, `.ai/COMMON.md`'s Current Rules, "Merge conflict protocol
      (TASK-0202)" bullet) — not re-added.
- [x] Add the Quick Navigation line to `.ai/COMMON.md`. Same finding —
      already present ("merge conflict protocol (TASK-0202):
      `.ai/reference/MERGE_CONFLICT_PROTOCOL.md`").
- [x] Cross-link [[TASK-0195]]/[[TASK-0198]] both ways. Already present
      from both sides — this task's own Dependency section below already
      named them; both of their own files independently cross-link back
      (`[[TASK-0202]] ... cross-linked, not a dependency`).
- [x] Rebase `bartosz` onto `origin/bartosz`; verify; push. **Moot as
      literally specified** — re-checked 2026-08-24: `bartosz` is simply
      ahead of `origin/bartosz` (46 commits), not diverged (0 commits on
      `origin/bartosz` not already in local history) — there is nothing
      to rebase. The protocol's actual validation is stronger than the
      single planned rebase this item specified: it has been exercised
      for real, repeatedly, across many later tasks this same session
      (e.g. TASK-0205's own fetch+`branch -vv` check, TASK-0224's
      documented claim-override reasoning) — a real end-to-end run many
      times over, not a single staged demonstration.

## Dependency

- [[TASK-0050]], [[TASK-0051]] — the adoption-task precedent this task's
  own shape follows.
- [[TASK-0195]] (Done) — the deeper `RESULTS.md`-specific fix this
  protocol's manual process stood in for until it landed.
- [[TASK-0198]] (Done) — related but distinct; cross-linked, not
  addressed here.

## Open Questions

- Should `git merge-tree --write-tree`'s pre-check become a whitelisted
  `.ai/tools/claim.py` subcommand (e.g. `claim.py merge-check <branch>`)
  rather than a raw `git` invocation every thread has to remember the
  exact flags for? Real question, deliberately deferred — this task
  adopts the *practice*; wrapping it as a first-class tool command is a
  natural, small follow-up if the raw-command form proves to be a
  recurring friction point, not assumed necessary in advance.

## Done

**2026-08-24, Architect — closing a stale lock, not stale work.** A
reviewer flagged this task's own claim as the longest-held in the repo
(19 days, since 2026-08-05) alongside a genuinely stale `RESULTS.md`
resource lock elsewhere — grouped together as "stranded work and stale
locks," but checking this one specifically found the *substance* was
already done; only the claim/Status bookkeeping never caught up.

All 5 TODO items are satisfied (see TODO above for exactly how/when
each landed — three of the four remaining items turned out to already
be present, added silently as part of this session's own ordinary
subsequent work rather than as a deliberate return to this task). The
protocol document (`.ai/reference/MERGE_CONFLICT_PROTOCOL.md`) has not
just been adopted on paper — it has been the actual, cited governing
practice for every real divergence/collision check this session ran
into since 2026-08-05, including cases past what this task's own
Planned Validation anticipated (a single rebase): [[TASK-0224]]'s own
documented claim-override reasoning follows this protocol's own
staleness-judgment shape, and multiple later tasks (e.g. TASK-0205) cite
its own fetch+`branch -vv` pre-check by name before touching shared
files. The one literal TODO item that cannot be satisfied as written
("rebase `bartosz` onto `origin/bartosz`") is moot, not incomplete: no
divergence currently exists to rebase (`bartosz` is 46 commits ahead of
`origin/bartosz`, 0 behind) — the protocol's own actual test was never
going to be one staged demonstration, and in practice it has been many.

**Lesson for the scaffold itself, stated plainly since a reviewer had to
find this rather than the claim system surfacing it**: a task whose
*content* work finishes gradually, absorbed into later tasks' own
routine use of what it produced, can leave its own claim/Status
bookkeeping stranded indefinitely with nothing left to actually do —
the gap here was never "someone forgot to rebase," it was "the TODO
checklist was never re-read against what had already happened
elsewhere." No new tooling proposed for this specific failure mode; a
periodic stale-claim sweep (the reviewer's own report is exactly that,
performed manually) is the cheap mitigation until/unless it recurs
often enough to justify one.
