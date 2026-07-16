# TASK-0120 Learnability gate (HYP-P8): is the pocket even in the apo topology?

## Context

- ID: TASK-0120
- Title: For each mandatory target, Kabsch-superpose holo onto apo,
  measure per-residue apo→holo RMSD at the labeled pocket vs.
  background, compute Tama-Sanejouand cumulative overlap of the
  apo→holo displacement onto the apo ANM's low-frequency modes, and
  classify each target learnable / cryptic-structural.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §1.3, §4, §5 P0-3,
  §6. Originally `HYP-P8` in `.claude/hypotheses/physics.md` (2026-06-21,
  never executed). The panel calls this "the highest information-per-hour
  experiment available" and "one afternoon of Kabsch + RMSD."
- Priority: **P0 — this week.**

## Intent Contract

- Outcome: a per-target learnability verdict, computed, not assumed:
  1. Kabsch/SVD superposition of holo onto apo (reuse `superpose.py`'s
     existing alignment machinery — do not re-derive).
  2. Per-residue apo→holo Cα RMSD, compared at the labeled pocket
     residues vs. background (non-pocket) residues.
  3. Tama-Sanejouand cumulative overlap: project the apo→holo
     displacement vector onto the apo ANM's low-frequency mode
     subspace; report the cumulative overlap fraction.
  4. Classify: **pocket RMSD ≫ background RMSD AND low cumulative
     overlap → "unlearnable from apo topology, report as the finding"**
     (per the panel's own kill criterion, §6); otherwise "learnable,"
     with the actual numbers stated, not just the binary label.
- Why this matters beyond diagnosis: per the panel's §4 biological
  assessment, **if HYP-P8 holds for KRAS specifically**, "the apo graph
  does not encode this pocket" becomes a publishable, challenge-relevant
  finding that reframes the whole submission — KRAS's Switch-II pocket
  is the textbook cryptic case (opens only on binding), and this
  measurement decides whether that's a property of the *problem*
  (unlearnable from apo, a legitimate finding) rather than of the
  *method* (an operator/observable failure). This is prior to every
  other finding in Phase 1B/1C — run it regardless of what
  [[TASK-0118]]/[[TASK-0119]] find, not sequenced behind them.
- In Scope: all 3 mandatory targets (KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN)
  — CARDIAC_MYOSIN's result should be read alongside [[TASK-0124]]'s
  structural-quality finding (5TBY), not in place of it.
- Out Of Scope:
  - Re-deriving alignment/superposition machinery — reuse `superpose.py`.
  - Any change to the CTQW/GSR scoring pipeline itself — this is purely
    a structural-comparison diagnostic, independent of operator or
    propagator choice.
- Constraints And Invariants: no ground-truth pocket label leakage risk
  here beyond what `build_labels`/`superpose.py` already handle — this
  task reads holo structure directly (same as every other apo/holo
  comparison in this pipeline), not the CTQW scoring path.
- Planned Validation: report per-target RMSD-at-pocket vs.
  RMSD-at-background and cumulative-overlap numbers directly, with the
  learnable/cryptic-structural classification stated as a conclusion
  from those numbers, not asserted independently of them.

## In Progress

None

## TODO

- [ ] Kabsch-superpose apo/holo per target (reuse `superpose.py`).
- [ ] Per-residue apo→holo RMSD, pocket vs. background, per target.
- [ ] Tama-Sanejouand cumulative overlap of Δr onto apo ANM low-freq modes.
- [ ] Classify each target learnable / cryptic-structural; state the
      numbers, not just the label.
- [ ] Cross-reference the KRAS_G12C result explicitly against the
      panel's §4 biological framing (Switch-II is built from the
      catalytic region — active and allosteric sites overlap).

## Dependency

- None — explicitly no dependency, can start immediately (per the
  panel's own sequencing: "no quantum; your own docs say it must
  precede the ceiling you already ran").
- Its result should be read alongside [[TASK-0118]]/[[TASK-0119]]'s
  re-runs once available, but does not need to wait for them.

## Open Questions

- None yet — scope is fully specified by the panel's own method
  description; specifics (overlap-fraction threshold, RMSD significance
  test) are this task's own job to determine and state in Done.

## Done

(not yet)
