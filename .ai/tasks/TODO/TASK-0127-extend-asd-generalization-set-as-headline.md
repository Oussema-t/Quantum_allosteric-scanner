# TASK-0127 Extend the ASD generalization set and make it the reported headline

## Context

- ID: TASK-0127
- Title: [[TASK-0081]] ran 2 of 4 candidate ASD targets (PTP1B,
  CASPASE7 — the other 2 failed independent RCSB verification). Extend
  to 2-4 *additional* unseen targets and reframe the generalization set
  as the submission's **reported headline result**, not an appendix —
  per the panel, this is the direct mitigation for repeated-exposure
  overfitting risk across ~15 review cycles on the same 3 answer keys.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §3 (Weaknesses #9),
  §5 P2-10. Cross-references `.ai/tasks/TODO/TASK-0115-repeated-exposure-generalization-gate.md`
  (names this exact mitigation).
- Priority: **P2 — weeks 4-6.**

## Intent Contract

- Outcome: (1) 2-4 additional ASD-database targets, independently
  RCSB-verified (same discipline TASK-0081 already established: real
  chain-ID/ligand confirmation before use, not trusted from
  `config/targets.yaml`'s existing draft guesses) — targets genuinely
  never scored against by any of this project's prior review cycles;
  (2) full pipeline run against each, under whatever seed/clock/
  potential-gauge fixes ([[TASK-0118]]/[[TASK-0119]]/[[TASK-0121]]) have
  landed by then; (3) `RESULTS.md`/submission framing restructured so
  this generalization set — not the 3 mandatory targets' repeatedly-
  reviewed numbers — is the headline evidence of whether a real signal
  exists, per [[TASK-0115]]'s own reasoning (code-level `frozen_context`/
  LOPO gates multiple-comparisons abuse; nothing gates the ~15 human
  review cycles that have now looked at the same 3 answer keys).
- Why this is P2, not P0/P1: it depends on the gauge fixes
  ([[TASK-0118]]/[[TASK-0119]]/[[TASK-0121]]) actually landing first —
  running a generalization set through a still-gauge-contaminated
  pipeline would just reproduce the same undetermined state on more
  targets, not resolve anything.
- In Scope:
  - RCSB-verify 2-4 new ASD candidates (reuse `config/targets.yaml`'s
    remaining draft pool from TASK-0081's own sourcing, or find new
    ones if that pool is exhausted of usable candidates).
  - Run the full pipeline against each, under the post-P0/P1-fix
    pipeline state.
  - Restructure `RESULTS.md`'s framing: generalization-set results as
    the headline, the 3 mandatory targets' numbers as supporting detail
    with their gauge-contamination history stated plainly.
- Out Of Scope:
  - Building the gauge fixes themselves — this task consumes their
    output, does not re-derive it.
  - Any GLUCOKINASE/TAR_RECEPTOR-style config-schema fixes ("chains"
    field not expressing multi-structure chain differences) unless they
    turn out to block a needed new candidate — cross-reference
    `.ai/memory/questions/code-reviewer/open/Q-0001-...md` if so, don't
    silently reopen that question here.
- Constraints And Invariants: every new candidate must be independently
  RCSB-verified before use — do not repeat trusting `targets.yaml`'s
  draft guesses uncritically, per TASK-0081's own hard-won lesson (the
  YAML unquoted-numeric-ligand-code bug, the two candidates that failed
  verification).
- Planned Validation: full real runs against all new targets, reported
  with the same floor/ceiling/actual discipline as the 3 mandatory
  targets — no lighter-touch reporting standard for the "headline" set
  than for the original one.

## In Progress

None

## TODO

- [ ] Identify and independently RCSB-verify 2-4 new ASD candidates.
- [ ] Run full pipeline against each (post-gauge-fix pipeline state).
- [ ] Restructure `RESULTS.md` framing: generalization set as headline,
      mandatory-target numbers as supporting detail with contamination
      history stated.

## Dependency

- Soft-hard: should not start in earnest until [[TASK-0118]]/[[TASK-0119]]
  (and ideally [[TASK-0121]]) have landed — running this against a still-
  gauge-contaminated pipeline reproduces the same problem on more data.
- [[TASK-0081]] (Done) — the 2 already-verified targets (PTP1B,
  CASPASE7) are this task's starting point, not redone.
- [[TASK-0115]] (TODO) — same underlying motivation; coordinate rather
  than duplicate scope if TASK-0115 is picked up around the same time.

## Open Questions

- Whether TASK-0081's remaining draft ASD pool has enough independently-
  verifiable candidates, or whether new ones need sourcing from scratch
  — Implementer's call, state findings in Done either way.

## Done

(not yet)
