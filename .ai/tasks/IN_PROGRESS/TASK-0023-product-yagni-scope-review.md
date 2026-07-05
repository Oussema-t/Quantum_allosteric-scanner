# TASK-0023 YAGNI / scope-creep review of the Product feature backlog vs. challenge rubric

## Context

- ID: TASK-0023
- Title: Score every shipped `backend/`/`frontend/` feature (per
  TASK-0020's inventory) against the challenge rubric and the stated
  3-phase roadmap; flag anything with no defensible link as scope-creep,
  and propose a going-forward gate so new features need one before they're
  built
- Status: In Progress
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

**Handoff note (2026-07-05, Architect/Planner thread — contributed note, not a
claim override; TASK-0023 remains claimed by Intent-Inferrer per Context
above):** reviewed this task and its input at the user's request and
recommend splitting the work as follows so the Intent-Inferrer thread isn't
re-deriving context it already produced:

- **Slice 1 (Intent-Inferrer / General Critic role — do this part):** score
  every feature. Your own `.ai/reviews/PRODUCT_INTENT_MAP.md` §3 already has
  the 4 seed "unclear" items pre-analyzed with reasoning that leans
  `scope-creep-candidate` (items 1/3), a documentation gap rather than creep
  (item 2, `seed_readiness`), and `plausible-but-unstated` (item 4) — turn
  those leanings into this task's formal scored table rather than
  re-investigating from scratch. Then sweep the remaining ~16
  `ARCHITECTURE.md` change-log entries not already covered by §3 for
  stated-but-rubric-unlinked features (per this task's Intent Contract,
  "additionally sweep" bullet). **Stop here** — write the scored table +
  one-line reasoning into this task's own Done section (still fine to leave
  the file in `TODO/` until the full task closes).
- **Slice 2 (Architect/Planner — this thread will do this part after Slice 1
  lands):** draft the going-forward `CLAUDE.md` contribution-gate rule text,
  and file/register the follow-up `TASK-XXXX` for whatever gets scored
  `scope-creep-candidate` (likely batchable into one task — 3 of the 4 seed
  items share the "illustrative animation/morph" theme). Not Slice 1's job
  per this task's own Constraint ("draft only, do not edit CLAUDE.md
  unilaterally").
- **Non-blocking caveat, inherited from TASK-0020:** the six-criterion rubric
  (`PLAN-01.07.26.md` Week 3) was never confirmed against a primary
  challenge-rules doc. Proceed anyway and label verdicts provisional, same as
  `PRODUCT_INTENT_MAP.md` already does — don't stall Slice 1 on it.

## TODO

- [x] Wait for / pull TASK-0020's `unclear`-purpose list as the seed
      backlog (if TASK-0020 hasn't landed yet when this is picked up, do a
      lighter-weight version by reading `ARCHITECTURE.md`'s change log
      directly — don't block entirely on TASK-0020). **Done: TASK-0020
      landed; used its §3 seed list as the base.**
- [x] Locate and confirm the authoritative challenge rubric (same open
      question as TASK-0020 — resolve once, reuse in both). **Not
      resolved — per the Architect/Planner handoff note above, proceeding
      with the provisional rubric, all verdicts labeled accordingly.**
- [x] Score every change-log-derived feature: `clearly-serves` /
      `plausible-but-unstated` / `scope-creep-candidate` + one-line why +
      recommendation. **Done — see Done section (Slice 1 complete).**
- [ ] Draft the going-forward contribution-gate rule text (see Intent
      Contract) for user sign-off — do not apply it unilaterally.
      **Slice 2 — Architect/Planner thread, per handoff note.**
- [ ] For every `scope-creep-candidate`, open (or propose opening) a
      follow-up TASK for the actual simplify/remove action — this task
      records, doesn't execute. **Slice 2 — Architect/Planner thread.**

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

**Slice 1 (Intent-Inferrer) — scored feature table.** All verdicts
provisional per the unconfirmed-rubric caveat inherited from TASK-0020.
Phase-① core (extraction, completion, active-site detection, GNM
analysis, drug-chain-aware comparison) excluded by this task's own
Constraint — not re-litigated below.

| # | Feature (change-log lines) | Verdict | Reasoning | Recommendation |
|---|---|---|---|---|
| 1 | 3D contact-graph animation cluster: 2D→3D upgrade (06-25) + real-structures mode, auto-discovered intermediates, region-selector integration, node-set bug fix (4× 06-28) | **scope-creep-candidate** | Heaviest engineering cluster in the whole change log (6 log entries); explicitly labeled illustrative in its own UI copy ("not a simulated trajectory"); no rubric criterion or roadmap phase claims it. Auto-discovering and RMSD-ordering intermediate PDBs is real algorithmic work spent on a decoration. | simplify — keep a static/linear morph as the visual, drop the real-structures auto-discovery machinery unless Slice 2 finds a stated reason |
| 2 | `backend/rcsb_extract.py` (303 lines, new module, 06-28) + `biotite`/`gemmi` added to `requirements.txt` | **scope-creep-candidate (strongest)** | New finding, not in TASK-0020's seed list. Verified by grep: no file in `backend/` imports it — only self-referenced in its own docstring. The change-log entry itself says "Not yet wired into the API." Two pinned dependencies ship to every Render deploy for code nothing calls. | remove (or wire it to a stated consumer) — this is dead weight in production, the clearest YAGNI violation found |
| 3 | `seed_readiness`/`_ctqw_build_H` quantum-seed-readiness feature (2× 06-28) | **plausible-but-unstated** | Real physics (§5h/§5i, data-driven, not hardcoded), and per TASK-0018/TASK-0020 it's the *only* Product-code touchpoint on the "Hybrid" rubric criterion — potentially valuable, but that positioning has never been written down anywhere, and it quietly makes "② quantum solving not built yet" stale. | keep, but document — this is a documentation gap, not creep; frame it explicitly as a Hybrid-criterion demonstration in `ARCHITECTURE.md`/`SOFTWARE.md` |
| 4 | Straight-line morph (`morphwrap`/`morphplay`/`morphslider`, pre-existing, folds into the connectivity-change help text) | **scope-creep-candidate (low cost)** | Same illustrative-only category as #1, but cheap (a plain linear interpolation, no auto-discovery). Possibly redundant with #1's `protgraph` animation — both render an apo→holo contact-network transition in the same panel; unclear if `morphwrap` is a deliberate lightweight fallback or leftover from before `graphwrap` was built. | keep as-is if #1 is simplified/removed (becomes the sole illustrative view, low-cost); if #1 is kept, Slice 2 should confirm whether the two are actually redundant before proposing anything |
| 5 | Connectivity-change region selector, independent X/Y custom-interval fields (06-25 + 06-28 extension) | **plausible-but-unstated** | More configurability than any other panel offers; purpose (sub-blocking large matrices) is real but the free-text independent-axis interval parsing is more surface area than a single shared "region" selector would need. | simplify — consider one shared region selector instead of independent X/Y, unless a concrete use case for independent axes is stated |
| 6 | Keep-warm cron + in-memory RCSB/UniProt cache (06-28) | clearly-serves | Direct Feasibility payoff (avoids Render free-tier cold starts, cuts repeat-load latency) — infra, not a jury-facing feature, but a real one. | no action needed |
| 7 | Fix: benchmark-target select no longer auto-extracts (06-28) | clearly-serves | Correctness/UX fix on core Phase-① flow, not new scope. | no action needed |
| 8 | Connectivity-change + GNM panel "how to read these values" guides (2× 06-25) | clearly-serves | Directly supports jury legibility of the core science (Problem/Impact, Team) — in-app documentation, not a new capability. | no action needed |
| 9 | GNM permutation-significance (p-value) + Laplacian-spectrum histogram (06-25) | clearly-serves | Adds statistical rigor to the core GNM result (Validation) — strengthens an existing core feature, not scope creep. | no action needed |
| 10 | Fix 3D ligand-label anchoring to centroid (06-25) | clearly-serves | Bug fix on an existing display feature. | no action needed |
| 11 | COLLABORATION.md + dated change-log convention; CLAUDE.md/AGENTS.md onboarding docs (undated) | not applicable | Team/process documentation, not a Product feature — outside this task's feature-scoring frame (arguably serves the Team rubric criterion directly, but isn't a backend/frontend feature to score for creep). | no action needed |
| 12 | Active-site source toggle (benchmark\|auto); GNM cutoff exposed as a parameter; ligand classifier + `pdb_text` export; `resolve_compare_chains`; `site_potential_shift` (§5c/§5d) (undated, core-adjacent) | clearly-serves | Each is a direct extension of core Phase-① science/validation (lets a user probe robustness, fixes real drug-selection bugs, enables exports) — Technical/Validation, not creep. | no action needed |
| 13 | "Pivoted to data-foundation: removed quantum/validation modules" (undated) | clearly-serves (positive example) | A deliberate *removal* of premature scope — worth citing to Slice 2 as the precedent this project already has for exercising the same discipline the going-forward rule wants to formalize. | no action needed — cite as precedent |

**Summary:** 3 scope-creep-candidates (items 1, 2, 4), 2 plausible-but-unstated
(items 3, 5), rest clearly-serves or not-applicable. Item 2
(`rcsb_extract.py`) is the single cleanest, most concrete finding — dead
code + unused dependencies in a deployed service, independent of any
rubric-interpretation question.

Handing off to Slice 2 (Architect/Planner thread): draft the
`CLAUDE.md` contribution-gate rule text, and file the follow-up TASK(s)
for items 1/2/4 (the illustrative-animation cluster, likely batchable)
and item 2 separately (it's a removal, not a simplify, and has zero
dependency on the rubric-confirmation question — could land immediately).
