# TASK-0139 Resolve KRAS_G12C's learnability verdict: whole-structure CO said LEARNABLE, pocket-restricted CO disagrees

## Context

- ID: TASK-0139
- Title: [[TASK-0120]]'s headline `LEARNABLE` verdict for KRAS_G12C
  (CO(20)=0.638, directly refuting the panel review's own "textbook
  cryptic case" prediction — called out as "the single best piece of
  news in the repo") was computed from a **whole-structure** cumulative
  overlap, not a pocket-restricted one. [[TASK-0133]] built the properly
  pocket-restricted version (`superpose.restricted_cumulative_overlap`,
  catching and fixing a real Bessel's-inequality violation in the naive
  first implementation) and found KRAS_G12C's actual pocket CO(20) =
  **0.458 — below `learnability_verdict`'s own 0.5 threshold**, the
  opposite side of the conjunction from the whole-structure number that
  produced `LEARNABLE`. Elevated relative to a random-patch null (93rd
  percentile) but at one-sided p≈0.07, not decisive by this project's
  own established bar (uncorrected 0.05, [[TASK-0131]]'s own precedent).
  TASK-0133 explicitly left this "reported, not decided."
- Status: Done
- Owner: Implementer / Architect (a real classification decision, not
  purely mechanical — flag for Architect input if the evidence remains
  genuinely ambiguous after the work below)
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-20
- Source: [[TASK-0133]]'s own Done section, 2026-07-19.
- Priority: **P0.** This is not one more honest-negative confirmation —
  it's a live contradiction sitting under this project's most-cited
  positive reframe. Whatever a Phase 1 proposal says about KRAS's
  learnability needs to be said correctly, and right now the project
  itself doesn't have a single consistent answer.

## Intent Contract

- Outcome: a resolved, stated position on KRAS_G12C's learnability
  classification, backed by whichever of the following actually
  settles it — not a coin flip between two numbers:
  1. **Decide which CO quantity `learnability_verdict` should actually
     use** — whole-structure (TASK-0120's original) or pocket-restricted
     (TASK-0133's correction). Argue this from first principles, not
     from whichever answer is more convenient: the panel's own kill
     criterion (§1.3/§6.5 of `REVIEW-panel-2026-07-16-v2.md`) asks
     whether "the apo→holo direction lives inside the low-mode
     subspace" — for a *pocket-opening* question specifically, the
     pocket-restricted quantity is the more literal reading of that
     question (does the low-mode subspace span *this region's*
     motion), while the whole-structure number answers a different,
     easier question (does the low-mode subspace span *some*
     substantial motion somewhere). State which this project's own
     `learnability_verdict` conjunction was designed to ask (check
     [[TASK-0120]]'s own Intent Contract for what it originally
     specified) before deciding which implementation matches that
     intent.
  2. **If the pocket-restricted quantity is the correct one** (the more
     defensible reading per the reasoning above): either (a) get real
     statistical resolution on the p≈0.07 result — e.g. more random-
     patch replicates than TASK-0133's 1000 (unlikely to move a
     percentile much, diminishing returns) or a sharper test than a
     raw percentile (e.g. is 0.458 vs. a 0.5 threshold even the right
     comparison, or should the threshold itself be revisited given it
     was calibrated against the whole-structure quantity, not this
     one) — or (b) accept the result is genuinely inconclusive and
     report KRAS_G12C as **`AMBIGUOUS`/`UNDETERMINED`**, a real, honest
     third category distinct from both `LEARNABLE` and
     `UNLEARNABLE_FROM_APO` — per this project's own "an honest
     don't-know is a publishable result" convention, rather than
     forcing a binary call the data doesn't support.
  3. **Propagate the decision everywhere KRAS_G12C's `LEARNABLE`
     classification is currently cited** — `RESULTS.md`,
     `EXECUTION_PLAN.md`, `.claude/hypotheses/physics.md`'s HYP-P8
     entry, and any submission-narrative draft that has already used
     this finding — additively, per the no-silent-overwrite convention,
     not a silent flip.
- In Scope:
  - The threshold-recalibration question in 2(a) above, at least as an
    explicit consideration (was `co_threshold=0.5` ever validated
    against the pocket-restricted quantity specifically, or only
    inherited from the whole-structure one) — even if the answer is
    "not re-derived, out of scope, flag for later," state that
    explicitly rather than silently reusing 0.5 without checking.
  - BCR_ABL1/CARDIAC_MYOSIN's own analogous numbers (both are
    RMSD-determined regardless of which CO is used, per TASK-0133's own
    finding) — confirm this remains true, do not assume it without the
    one-line check.
- Out Of Scope:
  - Re-deriving `restricted_cumulative_overlap`'s own implementation —
    already built and tested by TASK-0133, reuse directly.
  - Any change to the CTQW/GSR scoring pipeline — this is a structural-
    learnability question only, per TASK-0120's own original scope.
- Constraints And Invariants: whatever this task decides must be a
  single, stated, defensible position — not both numbers left standing
  side by side with no resolution, which is the exact state this task
  exists to close.
- Planned Validation: the reasoning in outcome (1) above is itself the
  main validation — a future reader should be able to see *why* one
  quantity was chosen over the other, not just which one won.

## In Progress

None

## TODO

- [x] Determine which CO quantity `learnability_verdict`'s own original
      design intent specifies (re-read TASK-0120's Intent Contract).
- [x] Decide, with stated reasoning, whether pocket-restricted or
      whole-structure CO is the correct quantity for this conjunction.
      Decided: pocket-restricted.
- [x] If pocket-restricted: resolve the p≈0.07 ambiguity to a real
      classification (`LEARNABLE`/`UNLEARNABLE_FROM_APO`/`AMBIGUOUS`),
      or state explicitly why it can't be resolved further. Resolved:
      `AMBIGUOUS`.
- [x] Check whether `co_threshold=0.5` needs recalibration for the
      pocket-restricted quantity, or explicitly flag as not done.
      Recalibrated: replaced by a direct significance test against
      TASK-0133's own random-patch null when available.
- [x] Propagate the final decision into every document currently citing
      KRAS_G12C's `LEARNABLE` verdict, additively.

## Dependency

- [[TASK-0120]] (Done) — the original verdict this task revisits.
- [[TASK-0133]] (Done) — the corrected quantity and its own numbers,
  reused directly.
- [[TASK-0131]] — the project's own precedent for what counts as a
  decisive p-value here.

## Open Questions

- None — the ambiguity itself is this task's subject, not an
  unspecified scope gap.

## Done

**2026-07-20, Implementer B.** Resolved both open questions from first
principles, applied the resolution to the real, already-computed
TASK-0120/0133 numbers, and propagated the decision everywhere
KRAS_G12C's prior `LEARNABLE` verdict was cited. **KRAS_G12C reclassifies
`AMBIGUOUS`** — neither `LEARNABLE` (TASK-0120's original) nor
`UNLEARNABLE_FROM_APO` (the panel's own prediction) is supported by the
evidence at this project's own significance bar.

### (1) Which CO quantity — decided in favor of pocket-restricted

Argued, not picked for convenience: `learnability_verdict`'s RMSD half
is already a region-specific comparison (pocket vs. background, per
TASK-0120's own Intent Contract). A whole-structure CO answers "does
the low-mode subspace span *some* substantial motion somewhere,"
structurally a different and easier question than the panel's own §6
kill criterion ("does the apo→holo direction [for this pocket] live
inside the low-mode subspace"). Mixing a region-specific RMSD half with
a whole-structure CO half inside one AND-conjunction was never
internally consistent — a large, well-explained motion elsewhere in the
structure could mask a genuinely anharmonic pocket opening. Both real
call sites (`scripts/learnability_gate.py`,
`scripts/learnability_gate_patch_control.py`) already compute the
restricted quantity via TASK-0133's own
`restricted_cumulative_overlap`; `learnability_verdict`'s own docstring
updated to state this as the required input, not left implicit.

### (2) Whether `co_threshold=0.5` needs recalibration — yes, replaced
by a direct null test where available

Checked directly, not assumed: re-read `cumulative_overlap_gate` (the
only other consumer of `co_threshold=0.5` in this codebase) — it also
never validates the threshold against any null, whole-structure or
restricted. TASK-0120's own Done section already admits it: "not
derived from literature." TASK-0133 built exactly the null this
threshold was always missing (1000-replicate random-patch CO
distribution per target). New `superpose.learnability_verdict(...,
co_percentile: Optional[float] = None, significance_alpha: float =
0.05)` (ADD-only — `None` default reproduces every pre-existing call
byte-for-byte, verified by test):
- `co_percentile` supplied and in the upper tail
  (`>= 1 - significance_alpha`) -> `co_low=False`, real evidence the
  pocket is significantly better mode-spanned than a typical same-sized
  region.
- In the lower tail (`<= significance_alpha`) -> `co_low=True`, real
  evidence of significantly more anharmonic behavior than typical.
- Neither tail -> the CO evidence is inconclusive; if the RMSD half has
  already cleared its own bar, the verdict is `AMBIGUOUS` (a real third
  category, not a forced binary call) rather than defaulting to
  whichever side of the un-validated bare threshold `co_final` happens
  to land on.

### Applied to real data, programmatically (new
`scripts/resolve_kras_learnability.py`)

No new expensive computation — loads TASK-0120's own
`results/tasks/0120/learnability_gate.json` and TASK-0133's own
`results/tasks/0133/learnability_gate_patch_control.json` directly and
reruns the corrected `learnability_verdict` on the exact same,
already-verified real numbers:

| Target | RMSD ratio | Clears? | Restricted CO(20) | Percentile in null | Original | **Resolved** |
|---|---|---|---|---|---|---|
| KRAS_G12C | 2.27 | Yes | 0.458 | 93.0th | `LEARNABLE` | **`AMBIGUOUS`** |
| BCR_ABL1 | 0.49 | No | 0.175 | 37.3th | `LEARNABLE` | `LEARNABLE` (unchanged) |
| CARDIAC_MYOSIN | 1.32 | No | 0.044 | 12.6th | `LEARNABLE` | `LEARNABLE` (unchanged) |

Confirms, programmatically rather than by re-asserting TASK-0133's own
prose, this task's own In-Scope check: BCR_ABL1/CARDIAC_MYOSIN's
verdicts never depend on which CO quantity or criterion is used (both
already fail `rmsd_much_greater` outright) — `resolution_depends_on_
co_at_all=False` for both in the script's own output.

### Tests

New `tests/test_superpose.py::TestLearnabilityVerdictCoPercentile` (7
tests): default-`None` byte-identical to every pre-existing call;
KRAS_G12C's own real numbers reproduced directly and resolve to
`AMBIGUOUS` (not a synthetic-only check); significantly-elevated
percentile overrides a low raw CO to `LEARNABLE`; significantly-
depressed percentile overrides a high raw CO to `UNLEARNABLE_FROM_APO`;
an inconclusive percentile does not produce `AMBIGUOUS` when the RMSD
half has already failed (matches BCR_ABL1/CARDIAC_MYOSIN's real
situation); alpha-boundary edge case; percentile/alpha reported in
output. Full `test_superpose.py` suite (72 tests) and full repo suite
green.

### Docs updated additively

- `RESULTS.md`: new `[RESOLVED 2026-07-20, TASK-0139]` block appended to
  the "Learnability gate" section (after TASK-0133's own block, which
  stays intact); open-questions rows 12 and 17 both updated in place
  with a dated resolution note, per this table's own established
  in-place-edit convention.
- `EXECUTION_PLAN.md`: new row 1C.21 for this task; row 1C.4 (TASK-0120)
  gets one more dated update line pointing to it.
- `.claude/hypotheses/physics.md`: `HYP-P8` entry gets a dated
  `Superseded for KRAS_G12C` block after its existing 2026-07-17
  resolution text (kept intact) — notes this reading is actually closer
  to HYP-P8's own original spirit (real partial structural-change
  support, mode-spanning genuinely undecided) than either the panel's
  "textbook cryptic" prediction or TASK-0120's "LEARNABLE" reading.

### Not attempted / left for a follow-up task

- Did not modify `scripts/learnability_gate.py`/`learnability_gate_
  patch_control.py` themselves to auto-compute and wire the corrected
  verdict end-to-end in one live run — the real, already-verified
  numbers those two scripts produced were sufficient to resolve the
  classification via the new `resolve_kras_learnability.py` script;
  wiring a single combined live script is a real, deferred convenience
  improvement, not required to reach a decision.
- Did not attempt to increase random-patch replicate count beyond
  TASK-0133's own 1000 to chase tighter resolution on the p≈0.07 result
  — per this task's own Outcome 2(a), diminishing returns on a
  percentile-based test at this sample size; the corrected criterion
  (test against the null directly, accept `AMBIGUOUS` when
  inconclusive) was judged the better use of effort than a bigger
  replicate count aimed at forcing significance either way.
- Did not re-open or re-derive `rmsd_ratio_threshold=1.5`'s own
  provenance — unaffected by this task's scope (RMSD is not the
  ambiguous half for KRAS_G12C; its ratio, 2.27, clears the bar
  cleanly).

**Permutation-null correction, 2026-07-25 ([[TASK-0158]]):** the underlying
random-patch null ([[TASK-0133]]) was re-run under a corrected spatially
compact draw — KRAS_G12C's own reading softens from 93.0th/p=0.070 to
65.7th/p=0.343, was never significant either way, no verdict change here.
See [[TASK-0133]]'s own Done section / `RESULTS.md` open-questions row 38.
