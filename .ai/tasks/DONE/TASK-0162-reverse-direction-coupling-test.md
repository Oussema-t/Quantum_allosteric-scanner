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
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread), force-claimed 2026-07-28 from
  Implementer C (per direct user request)
- Claimed At: 2026-07-25 10:20 (original), 2026-07-28 (force-claim)
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

- [x] Confirm holo-labeled pocket residues can serve as a seed set under
      the existing seed-construction convention; state any adaptation
      needed.
- [x] Re-run `time_averaged_ctqw_converged`, `dcc_low`/`prs_low`,
      `transport.T_E`/`R_eff` with seed/candidate roles swapped, all 3
      mandatory targets.
- [x] Forward-vs-reverse comparison table + asymmetry statistic.
- [x] `RESULTS.md` section; report whichever outcome, don't select for a
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
  **Answered: ran both, within this task's own scope.** All 5
  observables are closed-form/direct linear algebra (no finite-time
  simulation) -- the full 5-target run took under a minute of wall time,
  making deferral unjustified once the 3-mandatory-target run itself
  was that fast.

## Done

**2026-07-28, Implementer B (force-claimed from Implementer C per direct
user request).** Built and executed as scoped, extended to the
generalization set (see Open Question above).

**New `scripts/reverse_direction_coupling_test.py`**: reuses
`time_averaged_ctqw_converged`, `prs_low`/`dcc_low` (k_modes=20, this
project's own established default -- not a fresh per-direction k-sweep,
a deliberate scope choice, not an oversight), `effective_resistance_
from_source` (on `H2_combinatorial_laplacian`), and `transmission_
from_source` (E=0, on `H_new`) completely unmodified -- only the seed/
label assignment swaps between FORWARD (source=active_site,
label=pocket) and REVERSE (source=pocket, label=active_site).
`labels.build_labels`'s own `pocket`/`active_site` masks are guaranteed
disjoint by construction (confirmed directly with an assertion in the
script, not merely assumed from reading the docstring) -- no adaptation
was needed for the pocket set to serve as a seed under the existing
convention.

**Real, decisive asymmetry, all 25 target x observable cells (5
observables x 5 targets -- 3 mandatory + PTP1B/CASPASE7)**: forward
clears its own [[TASK-0094]] proximity floor in 10/25 cells (40%),
reverse in only 4/25 (16%), both directions in only 2/25 (8%) --
KRAS_G12C `dcc_low` (fwd 0.522/rev 0.632) and BCR_ABL1 `T(E=0)` on
`H_new` (fwd 0.636/rev 0.726), reverse *stronger* than forward in both.
**The single starkest cell is this project's own strongest whole-graph
result**: CARDIAC_MYOSIN `prs_low` forward AUC 0.836 (clears floor
0.568) collapses to reverse AUC 0.321 (anti-correlated, below its own
floor 0.674) -- reported plainly, not smoothed over, since this is the
project's own headline single-cell finding.

**Background asymmetry statistic** (Spearman rho between forward/reverse
score vectors, restricted to residues in neither pocket nor active_site
-- this task's own explicit design choice, justified in the script's own
docstring: correlating the full N-residue vectors would mostly measure
each labeled set's own trivial self-occupancy in its own seeded
direction, not real coupling): mostly strongly positive (mean 0.61,
median 0.73, range -0.44 to 0.95) -- the asymmetry concentrates in the
labeled sets specifically; the rest of the protein's own coupling
structure is largely reciprocal even on cells with a large labeled-set
AUC collapse (e.g. CARDIAC_MYOSIN `prs_low`'s own background rho=0.90
despite its 0.836-vs-0.321 collapse). Exactly 1/25 cells (`dcc_low`,
BCR_ABL1) shows real background anti-correlation (rho=-0.44).

**No previously-reported verdict changed**: forward numbers reproduce
every already-published value exactly (e.g. KRAS_G12C `ctqw_converged`
0.5901, identical to [[TASK-0130]]/[[TASK-0159]]'s own number) -- an
implicit consistency check on this task's own script, not just an
assumption. Reverse is a new measurement, not a correction to an old one.

**Real scale effect found on the generalization set, stated not
buried**: PTP1B/CASPASE7 both have only 5 active-site residues (vs.
14-18-residue pocket sets), producing a much higher reverse floor
(0.90-0.91 vs. 0.56-0.62 on the 3 mandatory targets) -- a 5-residue
positive-label set is trivially easy for distance/degree baselines to
nail from a nearby larger seed region. CASPASE7's `R_eff` reverse
(0.906) is the one generalization-set cell that clears this elevated
bar.

**Deliberate scope boundary, stated not silently dropped**: no
permutation-null gate was applied to the reverse cells specifically --
this task's own Out of Scope is pure re-application of existing scoring
with roles swapped, not new statistical machinery. A Bonferroni-corrected
reverse-direction verdict is a natural, separate follow-up.

**Full test suite**: 971 passed, 2 xfailed, 0 failed (no new library
code -- this task is pure re-application, per its own Out of Scope, so
no new unit tests were added; the full suite confirms nothing broke).

Full detail: `RESULTS.md`'s "Reverse-direction coupling test" section,
open-questions row 45,
`RESULTS/results_task0162_reverse_direction/reverse_direction_coupling_test.json`.
