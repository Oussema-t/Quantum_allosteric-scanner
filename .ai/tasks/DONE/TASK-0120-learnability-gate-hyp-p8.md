# TASK-0120 Learnability gate (HYP-P8): is the pocket even in the apo topology?

## Context

- ID: TASK-0120
- Title: For each mandatory target, Kabsch-superpose holo onto apo,
  measure per-residue apo→holo RMSD at the labeled pocket vs.
  background, compute Tama-Sanejouand cumulative overlap of the
  apo→holo displacement onto the apo ANM's low-frequency modes, and
  classify each target learnable / cryptic-structural.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-17 23:11
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

**(1) `superpose.background_rmsd`/`learnability_verdict`** (new) — most
of this task's machinery already existed (`align_apo_holo`, `anm_modes`,
`cumulative_overlap`, `cryptic_openness_gate`), confirmed by reading
`superpose.py` in full before writing anything. The one missing piece:
`cryptic_openness_gate` computes pocket RMSD against a fixed threshold,
never against background (non-pocket) RMSD — the actual comparison the
panel's kill criterion needs. `background_rmsd` mirrors
`cryptic_openness_gate`'s exact structure (same common-set restriction,
same unmeasurable-residue accounting). `learnability_verdict` makes the
panel's qualitative "pocket RMSD >> background RMSD AND low cumulative
overlap" precise: `ratio >= 1.5` (this task's own stated choice, not
derived) `AND co_final < 0.5` (reused from `cumulative_overlap_gate`'s
own existing default, not re-chosen) → `UNLEARNABLE_FROM_APO`, both
conditions required (reasoning in the function's own docstring — RMSD
alone can't distinguish "cryptic pocket" from "globally floppy
structure"; CO alone can't distinguish "genuinely anharmonic" from
"noise on a small displacement").

**(2) Real run, all 3 mandatory targets** (`scripts/learnability_gate.py`,
live fetch, `results_task0120/learnability_gate.json`):

| Target | N (common) | Pocket RMSD | Background RMSD | Ratio | CO(20) | Verdict |
|---|---|---|---|---|---|---|
| KRAS_G12C | 169 (166) | 1.863 Å | 0.820 Å | 2.27 | 0.638 | `LEARNABLE` |
| BCR_ABL1 | 451 (429) | 0.362 Å | 0.734 Å | 0.49 | blocked | `PARTIAL_RMSD_ONLY` |
| CARDIAC_MYOSIN | 950 (709) | 4.168 Å | 3.161 Å | 1.32 | blocked | `PARTIAL_RMSD_ONLY` |

**Headline finding: contradicts the panel's own stated expectation for
KRAS_G12C, reported as such, not softened.** The panel calls KRAS "the
textbook cryptic case" and predicts HYP-P8 should hold there. Measured:
pocket RMSD is real and 2.27x background (clears the ratio bar), but
cumulative overlap onto the apo ANM's lowest 20 modes is 0.638 — well
above the 0.5 low-overlap bar. The apo→holo direction *is* substantially
spanned by the soft-mode subspace. Per this task's own kill criterion
(both conditions required), KRAS_G12C classifies `LEARNABLE`, not
`UNLEARNABLE_FROM_APO`.

**(3) Cross-referenced against the panel's §4 biological framing, per
this task's own TODO item** — the panel's separate point (Switch-II is
built from the catalytic Switch-II region, so active and allosteric
sites geometrically overlap on this target, meaning "no method scores
cleanly on it") is a labeling/observable-design claim, not a structural-
learnability claim, and this measurement neither confirms nor refutes
it. Both can be independently true: the apo structure may span the
opening direction (this measurement) while the pocket definition itself
overlaps the active site in a way that confounds any proximity-seeded
scoring method (the panel's separate point, already corroborated
elsewhere in this project by TASK-0094's proximity-floor findings on
KRAS specifically). Whoever next writes a submission narrative about
KRAS's failure should cite the correct one of these two claims — they
have different evidence and are not interchangeable.

**(4) BCR_ABL1's pocket moves *less* than background** (ratio 0.49) —
the opposite signature from a cryptic opening. Cross-checked against
this project's own prior finding: consistent with, not contradicting,
TASK-0104's "apo-computable structural prior" re-framing of this
target's `ground_state_relaxation` result — a pocket that is already
comparatively rigid/pre-formed in the apo structure is exactly what a
low relative pocket RMSD would look like. The RMSD half of the kill
criterion already fails here on its own (ratio <1.5), independent of
the blocked CO half.

**(5) CARDIAC_MYOSIN's numbers are confounded by its own independent
5TBY data-quality issue**, per this task's own In Scope note (read
alongside TASK-0124, not in place of it) — largest background RMSD of
the three (3.16 Å), lowest apo/holo common-correspondence coverage
(709/950, vs. KRAS's 166/169 and BCR_ABL1's 429/451), and the largest
overall alignment RMSD (3.75 Å vs. 1.36 Å / 0.98 Å). Ratio (1.32) is
reported, not over-interpreted as a clean structural-biology result.

**(6) Cumulative overlap blocked for BCR_ABL1/CARDIAC_MYOSIN by a real,
separately-filed gap, not worked around inline** — `superpose.anm_modes`'
exactly-6-near-zero-rigid-body-mode assertion raises on both
(`n_zero=7`/`10`), confirmed live this run, matching [[TASK-0128]]'s own
prior finding via TASK-0099. That task's scope is determining *why*
(floppiness vs. genuine disconnection) before touching the assertion —
real diagnostic work this task does not preempt with an inline widening,
which risks reintroducing the disconnected-graph false-pass TASK-0005
originally fixed. `scripts/learnability_gate.py` degrades gracefully
instead (`try`/`except ValueError` around only the `anm_modes` call,
pocket/background RMSD unaffected, `co_blocked_reason` records the exact
exception, `verdict="PARTIAL_RMSD_ONLY_CO_BLOCKED"`) rather than
crashing the whole target or silently dropping it.

**(7) `RESULTS.md`/`physics.md` updated additively** — new "Learnability
gate (HYP-P8)" section in `RESULTS.md` with the full cross-target
writeup and a new open-questions row (#12); `physics.md`'s `HYP-P8`
entry gets a dated resolution block noting this is the *first direct*
test of that hypothesis's own narrow claim (the 2026-07-15 "HYP-P8 is
now strongly supported" status-update bullet was built from *indirect*
evidence about scoring-pipeline artifacts — seed sensitivity, proximity
confounds, localization — a different, broader claim than "is the pocket
in the apo topology," conflated in that earlier note). Original text
preserved at both sites, per each document's own no-silent-overwrite
convention.

**(8) Tests**: `tests/test_superpose.py::TestBackgroundRmsd` (3),
`::TestLearnabilityVerdict` (5) — full suite (46 tests) green.

**Not attempted, explicitly out of this task's own scope**: fixing
TASK-0128's `anm_modes` assertion (separate task, real diagnostic work);
re-deriving any alignment/ANM machinery (reused `superpose.py`
throughout); any change to the CTQW/GSR scoring pipeline (this is a
purely structural diagnostic, independent of operator/propagator
choice, per this task's own Out Of Scope).

**Addendum 2026-07-18**: [[TASK-0128]] fixed `anm_modes`' shared
assertion (same day it was filed) — since this task's own blocked
cumulative-overlap computation called that exact function, the fix
unblocked it as a direct consequence, not a separate re-run. Re-ran
`scripts/learnability_gate.py`: BCR_ABL1 CO(20)=0.794, CARDIAC_MYOSIN
CO(20)=0.584, both above the 0.5 threshold — both were already
`LEARNABLE` on the RMSD half alone, and the now-complete CO half
confirms it rather than changing anything. **All 3 mandatory targets
now have complete RMSD+CO numbers and all classify `LEARNABLE`.**
`RESULTS.md`'s "Learnability gate" section and open-questions row #12
updated additively; original at-first-run numbers preserved, not
deleted.
