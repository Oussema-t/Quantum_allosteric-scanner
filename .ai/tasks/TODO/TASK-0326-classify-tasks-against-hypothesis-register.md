# TASK-0326 — Classify every task against the hypothesis register, draft the missing hypotheses

- Status: TODO
- Owner: Explorer (classification pass) → Architect/Planner (reviews NO-HYP
  drafts before they become register content, same review gate [[TASK-0323]]
  used) → Implementer (applies the reviewed drafts)
- Priority: High
- Filed: 2026-09-03 by Architect/Planner, at the repo owner's direct request
- Related: [[TASK-0321]] (the original write-mostly finding), [[TASK-0322]]
  (checker/index), [[TASK-0323]]/[[TASK-0324]] (the narrower precedent this
  generalizes), [[TASK-0307]] (same shape in the submission drafts)

## Why this exists

Discussing [[TASK-0321]]'s numbers, the repo owner asked directly: of ~344
tasks and only ~39 registered hypotheses (21 `HYP-P*`/`HYP-S*` +
18 rows in `reference_register.md`'s own scheme) cited by roughly 50-60 tasks
total, what were the *other* ~85% of tasks actually doing? [[TASK-0323]]
already answered this for the narrow case of matching a task to one of the 14
*originally-unjudged* hypotheses. This task generalizes that to the whole
corpus and adds the piece [[TASK-0323]] didn't attempt: **a task can test a
real, genuine, decided scientific claim that was never named as a hypothesis
at all, before or after the fact.** Those claims currently exist only as prose
inside individual task files — this task surfaces them as hypotheses in their
own right, not just links to existing ones.

**Do not assume most tasks are missing hypotheses.** A large fraction of the
344 are pure engineering/process work (bug fixes, path sweeps, claim/lock
cleanup, doc-sync) with no scientific claim to name. Overclaiming the
un-hypothesized-science bucket would just be a second write-mostly register.

## Intent Contract

- Outcome: a durable, tracked ledger — one row per task file — classifying
  each into exactly one of:
  - **`HYP-<id>`** — this task tested/decided a claim matching an existing
    hypothesis (either scheme). Cite the specific id(s); a task may map to
    more than one.
  - **`NO-HYP`** — this task tested a genuine, specific scientific claim or
    mechanism, and no existing hypothesis (either scheme) captures it. Each
    `NO-HYP` task gets a **proposed draft hypothesis stub** (claim, in the
    register's own existing style; dated status already filled in, since the
    deciding task already exists; citation to the deciding task(s)) —
    proposed, not silently added to the live register.
  - **`ENG`** — infrastructure/process/tooling work; no scientific claim to
    classify. No draft owed.
  - **`UNCLASSIFIED`** — genuinely ambiguous after a real read; needs a human
    (Architect or the repo owner) judgment call. Keep this bucket honest and
    small — it is not a place to dump anything effortful.
- Why required, not assumed: the repo owner's own framing — hypotheses
  "written into the task itself, but never named 'this is a hypothesis'" are
  currently invisible to the register, the checker, and anyone reading the
  register cold. This is the mechanism that finds them.
- In Scope: all 344 task files (`.ai/tasks/{TODO,IN_PROGRESS,DONE}/*.md`).
  Start with a **pilot of 30-40 tasks** (a mix of eras and apparent kinds —
  don't cherry-pick only-obvious cases) to validate the four-way scheme and
  the ledger format before committing to the full sweep; report the pilot's
  own bucket distribution before continuing, so the Architect can sanity-check
  the split is not systematically miscalibrated (e.g. `UNCLASSIFIED` too
  large, or `ENG` quietly absorbing real science).
- Out Of Scope: writing `NO-HYP` drafts directly into
  `.claude/hypotheses/*.md` — propose them in the ledger (or a staging file),
  reviewed before landing, matching [[TASK-0323]]'s own precedent of not
  self-authorizing new register content. Re-litigating any `HYP-<id>`
  classification already recorded by [[TASK-0323]]/[[TASK-0324]] for the
  original 14 — trust that work, don't redo it.
- Constraints And Invariants:
  - A `NO-HYP` draft needs the same evidentiary bar the register already
    holds itself to — cite the specific deciding task and its actual result,
    not a paraphrase from memory.
  - Where multiple tasks bear on the same un-named claim (a family, not one
    task), propose ONE hypothesis citing all of them — don't fragment one
    claim into several near-duplicate drafts.
  - The ledger itself must be easy to regenerate/audit later — a flat table
    (task id | classification | evidence/one-line reasoning | draft ref if
    NO-HYP) is sufficient; don't over-engineer the format before the pilot
    proves it out.
- Planned Validation: after the pilot, spot-check 5 classifications (mixed
  across all 4 buckets) against the actual task file content before trusting
  the scheme at full scale.

## TODO

- [ ] Decide and record the ledger's location (suggest under
      `.claude/hypotheses/`, since it's fundamentally register tooling, but
      an Architect call — don't block the pilot on this, a scratch location
      is fine until the format is proven).
- [ ] Pilot: 30-40 tasks, mixed eras/kinds, all four buckets populated or
      explicitly absent-and-why. Report the distribution.
- [ ] Full sweep: remaining ~300-310 tasks.
- [ ] Compile `NO-HYP` drafts, grouped by claim (not one-per-task where
      several tasks share a claim).
- [ ] Hand drafts to Architect/Planner for review before any land in the live
      register.
- [ ] Once approved, an Implementer applies them (new `## HYP-` entries or
      new `reference_register.md`-style rows, whichever scheme fits each
      claim — some `NO-HYP` claims may be methodology/statistics findings
      that fit neither existing file cleanly; flag rather than force a fit).
- [ ] Re-run [[TASK-0322]]'s checker/index after any register additions land.

## Dependency

- [[TASK-0323]] — reuse its classification of the 14 originally-unjudged
  hypotheses rather than re-deriving it.
- [[TASK-0322]]'s checker — the tool this task's output should ultimately be
  validated against once new hypotheses land.

## Done

(not yet)
