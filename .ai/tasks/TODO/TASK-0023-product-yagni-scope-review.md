# TASK-0023 YAGNI / scope-creep review of the Product feature backlog vs. challenge rubric

## Context

- ID: TASK-0023
- Title: Score every shipped `backend/`/`frontend/` feature (per
  TASK-0020's inventory) against the challenge rubric and the stated
  3-phase roadmap; flag anything with no defensible link as scope-creep,
  and propose a going-forward gate so new features need one before they're
  built
- Status: TODO
- Owner: General Critic
- Claimed By: Intent-Inferrer (this thread)
- Claimed At: 2026-07-04 15:10
- Source: user request, 2026-07-04 session — "my fear is that some of the
  functionality implemented is not actually bringing the whole repo ahead
  in the means of the challenge, more blindly flailing around implementing
  all kinds of functionality — missing the YAGNI approach... If there
  isn't a clear intent to use a functionality and a clear verifiable
  hypothesis on why we could need it — we shouldn't be implementing it in
  the first place."
- Scope: `ARCHITECTURE.md`'s change log (the de facto Product feature
  census — dozens of dated entries, one person's worth of rapid
  incremental UI/analysis additions) cross-referenced against
  TASK-0020's inventory and the challenge rubric

## Intent Contract

- Outcome: a scored list — one row per Product feature — of
  `clearly-serves-the-challenge` / `plausible-but-unstated` /
  `scope-creep-candidate`, each with the one-line reasoning, plus a
  recommendation (`keep` / `simplify` / `remove` / `no action needed`).
  Not a unilateral deletion pass — a decision record the team (and future
  agents) can act on deliberately.
- In Scope:
  - every `unclear`-purpose item from TASK-0020's inventory gets scored
    here first (that's the direct backlog for this task)
  - additionally sweep `ARCHITECTURE.md`'s change log for features that
    *do* have a stated purpose in the log entry itself, but where that
    purpose doesn't trace to any of the six rubric criteria (Problem/
    Impact, Technical, Feasibility, Validation, Hybrid, Team) or the
    ①/②/③ roadmap — e.g. UI polish/animation modes are worth checking
    against "does this demonstrate something the jury scores, or is it
    demo polish for its own sake"
  - draft the text of a going-forward contribution rule ("every new
    Product feature/endpoint states, in its commit message or a linked
    task, which rubric criterion or roadmap phase it serves") as a
    proposed addition to `CLAUDE.md`'s numbered conventions — **draft
    only, do not edit `CLAUDE.md` unilaterally**, that file is durable
    project policy and multiple threads currently touch this repo; put
    the proposed convention text in this task's Done section for explicit
    user sign-off
- Out Of Scope:
  - actually removing or refactoring any flagged feature — that becomes
    its own follow-up TASK per flagged item (or a batch task), same
    "record the decision, a separate task executes it" split TASK-0018
    already uses for its convergence question
  - re-scoring `__WORK_IN_PROGRESS__/src/allostery` features against
    YAGNI — `ALGORITHM_REGISTER.md` already *is* that rigor pass for the
    research pipeline (its 1-5 rating scale is exactly this exercise,
    already done, well); this task is the Product-side equivalent that
    doesn't exist yet, not a redo of the research-side one
  - second-guessing rubric weights themselves — take the rubric as given
- Constraints And Invariants:
  - evidence-first: every `scope-creep-candidate` verdict must cite the
    specific `ARCHITECTURE.md` change-log line or `SOFTWARE.md` section
    the feature comes from, not a vibe.
  - do not flag anything from Phase ① data-foundation core (extraction,
    completion, active-site detection, GNM analysis, drug-chain-aware
    comparison — `SOFTWARE.md` §10 already calls these "done" and
    foundational) as scope-creep by default; the fear expressed is about
    incremental additions on top of that core, not the core itself.
- Planned Validation: this task's output is a decision document (its own
  Done section) — validation is "every `ARCHITECTURE.md` change-log entry
  has a verdict," not a test suite.

## In Progress

None

## TODO

- [ ] Wait for / pull TASK-0020's `unclear`-purpose list as the seed
      backlog (if TASK-0020 hasn't landed yet when this is picked up, do a
      lighter-weight version by reading `ARCHITECTURE.md`'s change log
      directly — don't block entirely on TASK-0020).
- [ ] Locate and confirm the authoritative challenge rubric (same open
      question as TASK-0020 — resolve once, reuse in both).
- [ ] Score every change-log-derived feature: `clearly-serves` /
      `plausible-but-unstated` / `scope-creep-candidate` + one-line why +
      recommendation.
- [ ] Draft the going-forward contribution-gate rule text (see Intent
      Contract) for user sign-off — do not apply it unilaterally.
- [ ] For every `scope-creep-candidate`, open (or propose opening) a
      follow-up TASK for the actual simplify/remove action — this task
      records, doesn't execute.

## Dependency

- TASK-0020 (Product intent inventory) — primary input; soft dependency
  (can start from `ARCHITECTURE.md` directly if TASK-0020 is delayed).
- Cross-reference, don't duplicate: `ALGORITHM_REGISTER.md` (the
  research-side version of this same rigor exercise, already done).

## Open Questions

- Same rubric-source question as TASK-0020 — resolve once, apply to both;
  don't let the two tasks independently guess at slightly different rubric
  text.
- Should the going-forward contribution gate be enforced anywhere
  mechanically (e.g. a PR template checkbox) or stay a documented
  convention like everything else in this scaffold? Recommend documented
  convention only for now, consistent with TASK-0017's explicit choice of
  soft/advisory enforcement over tooling — revisit if it's routinely
  ignored.

## Done

(not yet)
