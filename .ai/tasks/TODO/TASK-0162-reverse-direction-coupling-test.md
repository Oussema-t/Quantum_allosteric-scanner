# TASK-0162 Reverse-direction coupling test — seed at the pocket, score coupling into the active site

## Context

- ID: TASK-0162
- Title: `PANEL_REVIEW_2026-07-25.md` §2.4/V5 — every observable in the
  program seeds at the active site and asks where signal goes. But
  allosteric coupling is measured **pocket→active-site** in real
  experiments (that is the direction that matters therapeutically: does
  binding at the candidate site perturb the active site), and this
  reverse direction has never been computed here. The forward and
  reverse directions are not symmetric under a non-normal operator or a
  multi-residue incoherent-mixture seed, so this is a genuinely
  different, previously-untested measurement, not a relabeling of an
  existing one.
- Status: TODO
- Owner: Implementer
- Claimed By: Implementer C (this thread)
- Claimed At: 2026-07-25 10:20
- Source: `PANEL_REVIEW_2026-07-25.md` §2.4, §4 action item 5, V5.
- Priority: **P1** — the review's own estimate is 1–2 days, uses
  existing machinery unchanged, and either outcome (asymmetric or
  symmetric coupling) is a real, publishable finding.

## Intent Contract

- Outcome: for each of the 3 mandatory targets (and, time permitting,
  the generalization set), re-run the program's own best-performing
  observables (at minimum: `time_averaged_ctqw_converged`, `dcc_low`/
  `prs_low`, `transport.T_E`/`R_eff`) with the seed and scored-candidate
  roles swapped — seed at the (holo-labeled) pocket residues, score
  coupling into the active-site residues — and report whether the
  reverse-direction score differs from the forward-direction score
  already on record, and by how much.
- Why required: (1) tests a genuinely different biological hypothesis —
  bidirectional vs. unidirectional coupling; (2) is the direction real
  allosteric experiments actually measure; (3) is a real asymmetry test
  for the incoherent-mixture multi-residue seed convention this project
  already uses — a non-normal operator can genuinely produce different
  forward/reverse transport, and this has never been checked.
- In Scope:
  - Reuse each observable's existing scoring function unmodified — only
    the seed/candidate-set assignment swaps.
  - Report forward vs. reverse side by side per target × observable;
    an explicit asymmetry measure (e.g., correlation or rank-difference
    between forward and reverse score vectors restricted to the common
    residue set).
  - State plainly whether reverse-direction scoring changes any
    already-reported verdict (AUC against the *same* pocket label,
    scored the other way — this is not a new label, just a new
    seed/candidate split).
- Out Of Scope:
  - Any new observable — pure re-application of existing scoring
    functions with roles swapped.
  - The ensemble/entropic mechanism ([[TASK-0166]]) — a related but
    distinct untested mechanism, not this task's scope.
- Constraints And Invariants: use the existing seed convention (full
  active-site array, `coherent=False`) mirrored onto the pocket side —
  state explicitly if the pocket label's own cardinality/shape makes a
  direct mirror awkward (e.g., very large pocket sets) and how it was
  handled.
- Planned Validation: forward-vs-reverse comparison table per target ×
  observable; explicit asymmetry statistic; report whichever way it
  comes out — symmetric coupling is itself informative (supports a
  reciprocal-channel picture), as is a real asymmetry (supports a
  directional-channel picture, or reveals a seed-construction artifact).

## TODO

- [ ] Confirm holo-labeled pocket residues can serve as a seed set under
      the existing seed-construction convention; state any adaptation
      needed.
- [ ] Re-run `time_averaged_ctqw_converged`, `dcc_low`/`prs_low`,
      `transport.T_E`/`R_eff` with seed/candidate roles swapped, all 3
      mandatory targets.
- [ ] Forward-vs-reverse comparison table + asymmetry statistic.
- [ ] `RESULTS.md` section; report whichever outcome, don't select for a
      preferred story.

## Dependency

- [[TASK-0130]] (Done) — converged propagator, reused.
- [[TASK-0149]] (Done) — `dcc_low`/`prs_low`, reused.
- [[TASK-0145]] (Done) — `transport.T_E`/`R_eff`, reused.

## Open Questions

- Whether to also run this against the generalization set
  (PTP1B/CASPASE7) within this task's own scope or defer to a follow-up
  — Implementer's own call given the 1–2 day estimate; state the
  decision.

## Done

(not yet)
