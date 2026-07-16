# TASK-0122 Build `mode_coparticipation`: a less distance-confounded observable

## Context

- ID: TASK-0122
- Title: `mode_coparticipation` was proposed by
  `REVIEW-2026-07-13b-operator-falsification-negative-controls.md` §6
  and never built (confirmed absent by grep). Build it, gate it through
  the dumbbell 2x2 negative-control matrix ([[TASK-0103]]) and real
  labels, and pair it with [[TASK-0121]]'s potential renormalization —
  it does not work as a standalone fix.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §2.5, §5 P1-6.
- Priority: **P1 — weeks 2-4**, paired with [[TASK-0121]].

## Intent Contract

- Outcome: a new observable, `mode_coparticipation` (or equivalent name),
  seed-dependent and **not distance-monotone by construction** — the
  right shape for an allosteric-channel detector, unlike raw CTQW/GSR
  occupation (per §2.3, occupation-of-a-walk-seeded-at-a-point is
  monotonically decreasing in distance from that point, for *any*
  operator, at *any* time — this is why a different observable, not a
  better Hamiltonian, is the fix).
- **Hard, quantified dependency the panel already measured [EXECUTED] —
  do not skip this ordering**: on a **clean** normalized Laplacian
  (no disorder, no potential), co-participation (CP) is the
  *least*-confounded observable in the register (`|ρ|` with distance
  ≈ **0.18**, vs. 0.28 for shipped CTQW in the same geometry). But on
  the **current, un-renormalized `H_new`**, CP inherits the operator's
  own localization and is *worse* than CTQW (`|ρ|` ≈ **0.50**). **Build
  this only after [[TASK-0121]] lands**, or measure CP on both the
  current and renormalized `H_new` and report the difference explicitly
  — do not report a bare CP number without stating which `H_new`
  (renormalized or not) produced it.
- **Necessary but not sufficient — state this explicitly in Done**: low
  distance-correlation is necessary but not sufficient to find a real
  pocket. Whether CP actually *enriches* for true pocket residues (not
  just decorrelates from distance) is untested and must be gated through
  the dumbbell matrix (does it track coupling, not the well — same
  falsification lens as GSR/CTQW got in TASK-0103) and real labels
  (does it beat the proximity floor on real targets) before it is
  claimed as a fix, not just a cleaner metric.
- In Scope:
  - Implement `mode_coparticipation` per REVIEW-13b §6's original
    specification.
  - Measure `|ρ|` with distance on (a) a clean Laplacian, (b) current
    `H_new`, (c) renormalized `H_new` (post-[[TASK-0121]]) — reproduce
    the panel's 0.18/0.50 comparison points as a validation gate before
    trusting any further result.
  - Gate through [[TASK-0103]]'s dumbbell 2x2 matrix (does CP track
    coupling, not the well).
  - Score against real labels on all 3 mandatory targets, checked
    against the proximity floor ([[TASK-0094]]), same discipline as
    every other observable in this register.
- Out Of Scope:
  - The potential renormalization itself — [[TASK-0121]]'s scope, this
    task consumes its output.
  - Reselecting the submission operator/observable based on this task's
    result alone — Tier-2 gating (per [[TASK-0100]]) applies the same
    way it does to every other candidate.
- Constraints And Invariants: report per-observable, per-operator-variant
  distance-correlation numbers explicitly labeled by which `H_new`
  variant produced them — never a bare "CP is less confounded" claim
  without that label, given the panel's own finding that the answer
  flips sign depending on it.
- Planned Validation: the dumbbell-matrix gate + real-target proximity-
  floor check, both required before any claim that CP finds real pockets
  (as opposed to merely decorrelating from distance).

## In Progress

None

## TODO

- [ ] Implement `mode_coparticipation` per REVIEW-13b §6.
- [ ] Reproduce the panel's clean-Laplacian (0.18) vs. current-H_new
      (0.50) distance-correlation comparison as a validation gate.
- [ ] Re-measure on renormalized `H_new` (post-[[TASK-0121]]).
- [ ] Gate through [[TASK-0103]]'s dumbbell matrix.
- [ ] Score against real labels, all 3 targets, checked against the
      proximity floor.

## Dependency

- Hard: [[TASK-0121]] must land first (or this task measures both
  variants and reports the contrast explicitly).
- [[TASK-0103]] (dumbbell matrix, Done) — reused, not rebuilt.
- [[TASK-0094]] (proximity floor, Done) — reused for the real-label check.

## Open Questions

- Exact functional form of `mode_coparticipation` (which modes, what
  co-participation metric) — REVIEW-13b §6 is the cited source spec;
  Implementer's call on any remaining implementation detail, state it
  in Done.

## Done

(not yet)
