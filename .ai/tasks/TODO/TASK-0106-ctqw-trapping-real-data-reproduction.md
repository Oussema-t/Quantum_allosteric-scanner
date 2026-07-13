# TASK-0106 Reproduce the CTQW-trapping finding on real BCR_ABL1 data

## Context

- ID: TASK-0106
- Title: `REVIEW-2026-07-13c` (synthetic-network mechanism test) found that
  `H_new`'s diagonal potentials (V_B/V_T/V_R/V_C/V_M) cause Anderson-like
  transport localization — the walk never leaves the seed's first contact
  shell — and that on a synthetic distal pocket, transport-preserving
  operators (`H10`, `H2`) score 0.58-0.59 AUC where `H_new` scores 0.12
  (anti-correlated) and a pure proximity baseline scores exactly 0. This
  task is the **real-data gate** the review itself requires before that
  finding changes any claim.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/REVIEW-2026-07-13c-ctqw-trapping-mechanism.md`,
  verifying a colleague's hypothesis (2026-07-13) that CTQW's proximity-
  like scoring is caused by trapping, not merely descriptive of it.
- Crit Ref: makes a specific, falsifiable, cheap prediction: on BCR_ABL1
  (1OPL apo / 5MO4 holo), CTQW through `H10_disorder_suppressed`,
  `H2_combinatorial_laplacian`, and `H_new` at reduced λ should beat
  `H_new`'s recorded 0.525 and should clear that target's proximity floor
  (0.565, per TASK-0094). `RESULTS.md` already records
  `AUC_apo_H10_baseline` = 0.558 vs `H_new` = 0.525 on this exact target —
  previously read as a noise-level gap ([[TASK-0093]]); this task checks
  whether the sign is real and whether it clears the floor properly
  scored (the recorded 0.558 was not evaluated against the floor as its
  own headline number).

## Intent Contract

- Outcome: a real-data answer to whether the synthetic mechanism
  (trapping degrades distal detection) reproduces on BCR_ABL1's actual
  topology and actual labeled pocket — the explicit gate the review
  requires before this changes any reported claim.
- In Scope:
  - fetch real BCR_ABL1 data (1OPL apo / 5MO4 holo, per `config/
    targets.yaml`) — this task requires network access the review's own
    session did not have
  - run `time_averaged_ctqw` through `H10_disorder_suppressed`,
    `H2_combinatorial_laplacian`, and `H_new` at reduced λ (at minimum
    λ=0.25, matching the review's synthetic sweep point), alongside the
    existing `H_new` default for direct comparison
  - report AUC on the real labeled pocket for each, checked against
    TASK-0094's proximity floor for this target (0.565)
  - report the same transport diagnostic the review used (⟨hop from
    seed⟩ or participation ratio at a fixed t) alongside AUC, not AUC
    alone — this is a mechanism claim, not just a leaderboard entry
  - this is **Tier-1 descriptive measurement only** (per TASK-0100's own
    tiering) — it does not select a new submission operator by itself
- Out Of Scope:
  - reselecting the submission operator — that decision is Tier-2-gated
    ([[TASK-0100]]), requires `frozen_context`/`leave_one_protein_out`
    across all 3 mandatory targets, and is explicitly not this task's
    call even if this task's result is strongly suggestive
  - running this on KRAS_G12C/CARDIAC_MYOSIN — BCR_ABL1 only, since it's
    the target both the review and the existing `RESULTS.md` gap concern;
    extending to the other 2 mandatory targets is a natural follow-up but
    not required to answer this task's specific question
  - amending `RESULTS.md`'s claims — that's a follow-up once this task's
    result is known, not this task itself
- Constraints And Invariants:
  - this is diagnostic measurement, not a frozen-config selection act —
    does not need `frozen_context`/LOPO gating (same reasoning already
    applied to TASK-0067/TASK-0100's Tier 1).
  - report the result **whichever way it comes out** — if the synthetic
    finding does NOT reproduce on real BCR_ABL1 topology, that is exactly
    as reportable as if it does (matches this project's "an honest NO is
    a publishable result" convention).
- Planned Validation: the measured AUCs + transport diagnostics
  themselves. Success is "the question is answered with real data," not
  "the synthetic finding is confirmed."

## In Progress

None

## TODO

- [ ] Fetch real BCR_ABL1 (1OPL/5MO4) data.
- [ ] Run `time_averaged_ctqw` through `H10`, `H2`, `H_new`(λ=0.25),
      `H_new`(default) on the real contact graph.
- [ ] Score each against the real labeled pocket; report AUC + transport
      diagnostic (⟨hop⟩ or PR) for each.
- [ ] Check each against TASK-0094's proximity floor for this target
      (0.565).
- [ ] Report whether the synthetic mechanism finding reproduces, and flag
      any deviation (e.g. if the real gap is smaller/larger/absent) as a
      finding in its own right, not a failure to force-match the
      synthetic result.

## Dependency

- `.ai/reviews/REVIEW-2026-07-13c-ctqw-trapping-mechanism.md` — the
  synthetic finding this task reproduces or falsifies on real data.
- [[TASK-0094]] (Done) — the proximity floor this task checks against.
- [[TASK-0093]] — reads this task's result before finalizing its own
  reconciliation; do not close TASK-0093 assuming this task's answer.
- [[TASK-0100]] — governs what this task's result is and isn't allowed
  to justify (Tier-1 measurement only, no operator reselection).

## Open Questions

- None yet — the prediction, targets, and comparison operators are fully
  specified by the review.

## Done

(not yet)
