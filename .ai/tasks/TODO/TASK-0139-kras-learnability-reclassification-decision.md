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
- Status: TODO
- Owner: Implementer / Architect (a real classification decision, not
  purely mechanical — flag for Architect input if the evidence remains
  genuinely ambiguous after the work below)
- Claimed By: —
- Claimed At: —
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

- [ ] Determine which CO quantity `learnability_verdict`'s own original
      design intent specifies (re-read TASK-0120's Intent Contract).
- [ ] Decide, with stated reasoning, whether pocket-restricted or
      whole-structure CO is the correct quantity for this conjunction.
- [ ] If pocket-restricted: resolve the p≈0.07 ambiguity to a real
      classification (`LEARNABLE`/`UNLEARNABLE_FROM_APO`/`AMBIGUOUS`),
      or state explicitly why it can't be resolved further.
- [ ] Check whether `co_threshold=0.5` needs recalibration for the
      pocket-restricted quantity, or explicitly flag as not done.
- [ ] Propagate the final decision into every document currently citing
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

(not yet)
