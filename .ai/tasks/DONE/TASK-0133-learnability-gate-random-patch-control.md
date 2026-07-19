# TASK-0133 Learnability gate control: does a random patch also score high on cumulative overlap?

## Context

- ID: TASK-0133
- Title: [[TASK-0120]]'s `learnability_verdict` requires pocket RMSD ≥
  1.5x background **AND** CO(20) < 0.5 to call a target
  `UNLEARNABLE_FROM_APO`. The conjunction is doing real work but is
  untested against a control: does cumulative overlap onto the apo ANM's
  lowest 20 modes discriminate "spans *this pocket's* displacement" from
  "spans *any* displacement" at all? Compute CO(20) for a random
  16-residue patch on each target and compare to the real pocket's own
  CO(20).
- Status: Done
- Resolution: done
- Owner: Implementer
- Claimed By: Implementer C (this thread)
- Claimed At: 2026-07-19 20:02
- Source: `.ai/reviews/REVIEW-panel-2026-07-17.md` §5.2. Estimated cost:
  half a day.
- Priority: **P1.** Directly qualifies whether TASK-0120's headline
  (`LEARNABLE` on all 3 targets) means what it currently reads as
  meaning.

## Intent Contract

- Outcome: `superpose.background_rmsd`/`cumulative_overlap` (both
  already exist, per TASK-0120's own Done section) applied to a random
  16-residue patch per target (same patch size as this project's own
  real pockets, for comparability — confirm each target's real pocket
  size before choosing 16, per TASK-0120's own table, and use the real
  size if it differs), repeated across multiple random draws to get a
  distribution, not a single patch. Compare the real pocket's CO(20)
  against this random-patch distribution.
- Why this matters, stated precisely (per the review's own framing): if
  a random patch *also* scores 0.58-0.79 (the range TASK-0120 measured
  for the real pockets), then CO(20) is measuring how much of *any*
  displacement the soft-mode subspace spans — a property of the apo
  structure's own flexibility, not of the pocket specifically — and
  TASK-0120's `LEARNABLE` verdict would need to be read as "the soft
  modes are broadly expressive" rather than "the soft modes specifically
  encode this pocket's opening." If the real pocket scores measurably
  higher than the random-patch distribution, that supports the current
  reading as-is.
- **This does not retract TASK-0120's own measurement** (the RMSD/CO
  numbers themselves are unaffected) — it is a control on the
  *interpretation* of the CO half of the conjunction, per this project's
  own discipline of not reading a passing test as validation until the
  discriminating control has actually been run (the exact lesson of
  `pitfalls.md` P-0001).
- In Scope:
  - All 3 mandatory targets, multiple random-patch draws per target
    (report how many and why — enough for a real distribution, not a
    single anecdote).
  - Direct comparison: real-pocket CO(20) vs. random-patch CO(20)
    distribution, reported explicitly (not just "higher" or "lower" —
    the actual numbers and spread).
  - Update [[TASK-0120]]'s own `RESULTS.md` section additively with
    this control's result, per this project's no-silent-overwrite
    convention.
- Out Of Scope:
  - Changing `learnability_verdict`'s own threshold logic — this task
    is a control/measurement, not a redesign; if the control changes how
    the verdict should be read, that's a follow-up decision for whoever
    reads this task's result, not this task's own call.
  - BCR_ABL1's own already-flagged nuance (fails the RMSD half, not
    reached via the CO half at all per TASK-0120's own Done section) —
    unaffected by this control, which is specifically about the CO
    half's discriminating power.
- Constraints And Invariants: random patches must be drawn from the same
  common apo/holo correspondence set TASK-0120 already restricts to (not
  from the full residue set, which could include residues where the
  original measurement itself was unmeasurable).
- Planned Validation: the comparison itself is this task's validation —
  report the real pocket's percentile within the random-patch
  distribution per target, mirroring the same "percentile within a null"
  framing [[TASK-0131]] uses for the ceiling.

## In Progress

None

## TODO

- [x] Draw multiple random same-size patches per target from the common
      correspondence set; compute CO(20) for each.
- [x] Compare real-pocket CO(20) against the random-patch distribution,
      per target.
- [x] Report the real pocket's percentile within that distribution.
- [x] Update `RESULTS.md`'s learnability-gate section additively.

## Dependency

- [[TASK-0120]] (Done) — reuses its own `background_rmsd`/
  `cumulative_overlap` machinery directly, no new implementation needed
  beyond the patch-sampling loop itself.

## Open Questions

- **Resolved**: 1000 replicates/target. Unlike [[TASK-0131]]'s 200-
  replicate permutation null (each replicate a full `ceiling_search`
  re-run, genuinely expensive), each replicate here is a single cheap
  projection against an already-computed ANM eigenbasis (the expensive
  3N×3N eigendecomposition happens once per target, not once per
  replicate) — 1000 draws cost seconds, not the ~117 minutes TASK-0131's
  own null needed, so there was no reason to economize. Standard error
  on the reported percentiles at n=1000 is ~1.5 percentage points,
  precise enough to distinguish "borderline" from "decisive."

## Done

**Before implementing, checked a premise the task's own text takes for
granted**: does `learnability_gate.py`'s reported `CO(20)` (0.638/0.794/
0.584) actually measure the *pocket's* displacement, as this task's own
Intent Contract assumes ("the real pocket's CO(20)")? Checked directly
against real data, not assumed: `delta_r`'s length in that script is
`3 * len(alignment.apo_idx)` (166/429/709 — the *entire* common apo/holo
correspondence set), not `3 * n_pocket_residues` (18/16/13). **TASK-0120's
reported CO(20) is a whole-structure conformational-change overlap, not
a pocket-specific one.** This matters directly for this task's own
design: a whole-structure number is one value per target, constant
regardless of which residues you'd call "the pocket" — comparing it
against a distribution of per-patch numbers would silently compare two
different quantities. This finding is reported in `RESULTS.md`/
`EXECUTION_PLAN.md` alongside [[TASK-0120]]'s own numbers, additively,
per this project's no-silent-overwrite convention.

**Built a genuinely pocket-restricted CO(m)**: new
`superpose.restricted_cumulative_overlap(apo, alignment, eigvecs,
residue_idx)`. **Found and fixed a real bug in the obvious
implementation before trusting it on real data**: the first version
reused `cumulative_overlap`'s existing slice-eigenvector-and-renormalize
approach (`_projection_coefficients`), restricted to `residue_idx`. This
silently breaks `CO(m) <= 1` (Bessel's inequality, which any genuine
"overlap fraction" must satisfy) once `residue_idx` is a small fraction
of the whole structure -- confirmed on a controlled synthetic case
(3-of-50 residues) before ever running it on real targets: `CO(20) =
1.47`, mathematically impossible for a real overlap fraction. Real
pocket-sized subsets (13-18 of 166-709) gave up to `1.64` under this
first version. Root cause: renormalizing a mostly-truncated eigenvector
slice to unit length inflates it, and the resulting "modes" are no
longer orthonormal — a fine approximation when `cumulative_overlap`'s
only prior use case (the whole/near-whole common set, a handful of
missing residues) barely truncates anything, but invalid for a small
subset. **Fix**: zero-pad the residue subset's own displacement into the
full `3N`-length ANM coordinate space and project directly onto the
*untouched* (still globally orthonormal) eigenvectors — no slicing, no
renormalization. Bessel's inequality then guarantees `CO(m) <= 1` for
*any* subset size, verified directly on the same 3-of-50 synthetic case
(`CO(20) = 0.34`) and pinned as a regression test
(`test_stays_bounded_by_one_for_a_small_subset_of_a_large_structure`)
before re-running on real targets.

**Real run, all 3 mandatory targets**
(`scripts/learnability_gate_patch_control.py`, live fetch, 1000 random
same-sized patches per target drawn from the common correspondence set,
`seed=7`, `results_task0133/learnability_gate_patch_control.json`):

| Target | Pocket size | Restricted pocket CO(20) | Whole-structure CO(20) (TASK-0120) | Random-patch CO(20) mean±std | Percentile | One-sided p |
|---|---|---|---|---|---|---|
| KRAS_G12C | 18 | 0.458 | 0.638 | 0.341 ± 0.075 | 93.0th | ≈0.070 |
| BCR_ABL1 | 16 | 0.175 | 0.794 | 0.199 ± 0.059 | 37.3th | ≈0.627 |
| CARDIAC_MYOSIN | 13 (1 unmeasurable of 14) | 0.044 | 0.584 | 0.074 ± 0.032 | 12.6th | ≈0.874 |

**Headline, stated directly**: this control's discriminating power only
actually matters for **KRAS_G12C** — the one target whose
`learnability_verdict` genuinely depends on the CO half of the
conjunction (BCR_ABL1 fails `rmsd_much_greater` outright at ratio
0.49<1.5; CARDIAC_MYOSIN at 1.32<1.5 — both `LEARNABLE` purely on the
RMSD half regardless of CO). For KRAS_G12C, the properly-restricted
pocket CO (0.458) is **below** `learnability_verdict`'s own
`co_threshold=0.5` — the opposite side of the threshold from the
whole-structure proxy (0.638) that produced TASK-0120's original
`LEARNABLE` verdict. Combined with KRAS_G12C's already-clearing RMSD
ratio (2.27 >= 1.5), using this corrected CO in place of the
whole-structure one would flip the conjunction to
`UNLEARNABLE_FROM_APO` — reversing the headline for the panel's own
"textbook cryptic case."

**Not silently reclassified, and not fully decisive either way — the
random-patch control's own answer is nuanced, reported as such**:
KRAS_G12C's restricted pocket CO (0.458) is real and elevated relative
to the null (93rd percentile, random-patch mean 0.341 ± 0.075) — the
pocket is not indistinguishable from a random same-sized region — but a
one-sided p≈0.07 does not clear this project's own established
significance bar (uncorrected 0.05, [[TASK-0131]]'s own precedent for
what counts as decisive here). Neither "0.638, comfortably above
threshold, LEARNABLE" (the original whole-structure reading) nor "0.458,
below threshold, UNLEARNABLE" (a flip using the corrected number) is
fully supported by the evidence on its own — a fixed 0.5 threshold
applied to either quantity is doing more work than the statistics
underneath it decisively support for this specific target. Per this
task's own Out Of Scope, `learnability_verdict`'s threshold logic is not
changed here; this is the concrete, numeric finding for whoever next
revisits KRAS_G12C's classification to act on.

BCR_ABL1 and CARDIAC_MYOSIN's real pockets score **below** their own
random-patch medians (37th and 13th percentile respectively) — the
opposite of "broadly expressive, no discrimination." This does not
change either target's verdict (both are RMSD-determined), but is a
real, target-specific finding worth recording on its own: CO *does*
discriminate between regions on these two targets, just not in the
pocket-favoring direction, and this asymmetry (KRAS elevated, the other
two depressed relative to random) is itself informative about how
differently-behaved these three targets' apo dynamics are.

**Test coverage**: `tests/test_superpose.py::TestRestrictedCumulativeOverlap`
(5 tests) — matches `cumulative_overlap` exactly when the subset is the
full common set (a strict-generalization sanity check), differs from
the whole-structure number for a genuinely local displacement, raises
on a residue with no holo correspondence, output length matches
`n_modes`, and (the load-bearing one) stays bounded by 1 for a small
subset of a large structure — the exact real bug found above, pinned as
a permanent regression test, not just a one-off manual check. Full
suite: re-ran and confirmed green (see this session's own full-suite
log; no regressions from either `superpose.py` change).

**Not done, flagged rather than silently skipped**: `learnability_
verdict`'s own threshold/conjunction logic is unchanged, per this
task's own Out Of Scope — the KRAS_G12C reclassification question is
reported, not decided, here. BCR_ABL1/CARDIAC_MYOSIN's own CO-vs-random
asymmetry (scoring below their random-patch medians) is recorded but not
investigated further — a real, secondary finding this task's own scope
didn't require chasing to a mechanism.
