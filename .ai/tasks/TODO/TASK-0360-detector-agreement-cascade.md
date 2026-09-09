# TASK-0360 — The detector-agreement cascade: fpocket vs PASSer vs PocketMiner on identical structures

- Status: TODO
- Owner: **Implementer**
- Priority: **High — cheap, purely classical, and it strengthens the one thing we are actually selling**
- Filed: 2026-09-09 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0306]], [[TASK-0304]], [[TASK-0336]], [[TASK-0327]], [[TASK-0163]], [[TASK-0325]]

## The idea: our own headline finding, applied to a second domain

[[TASK-0306]]/[[TASK-0304]] decomposed the field's "84% recovery" figure and found
it is a **disjunction over six noisy tests**:

| detected by | count |
|---|---|
| >= 1 of 6 | 99/118 = **83.9%** |
| >= 3 of 6 | 68/118 = 57.6% |
| all 6 | 21/118 = **17.8%** |

That result is already in the submission, and it is the concrete evidence behind
the certifying-benchmark proposal.

**Nobody has asked the same question of the pocket detectors themselves.** We use
fpocket. The `allosteric` branch uses PASSer. Both branches use PocketMiner
somewhere. If "recovered by at least one detector" is far above "recovered by all
three", then detector choice is a large, measurable source of variance — and the
same archaeology the submission complains about applies to pocket detection, not
just to the six statistical measures.

### Why this is worth doing now, with six days left

1. **It generalises our strongest finding** from one benchmark's six tests to a
   second, independent domain. A referee who suspects the 84% decomposition is a
   one-off cannot say that twice.
2. **It answers the branch cohort dispute sideways and without argument.** The
   open question between branches is "PASSer or fpocket?". If the two detectors
   agree on most structures, the dispute is minor and either choice is defensible.
   If they do not, that disagreement *is* the finding, and it is quantified rather
   than negotiated.
3. **It feeds Phase-2 component (a) directly.** The certifying benchmark's job is
   to make this distinction automatic rather than archaeological. This is that
   distinction, measured.
4. **It carries no quantum claim at all**, so it cannot weaken or complicate any
   of the nulls.

## Intent Contract

- **Outcome:** the agreement cascade across pocket detectors on one shared
  structure set — recovered by >= 1, >= 2, all — plus pairwise agreement, reported
  in exactly the form [[TASK-0306]] used for the six statistical measures.
- **In scope:**
  1. **Detectors:** `fpocket` (vendored, `__WORK_IN_PROGRESS__/tools/fpocket/`,
     version-pinned per [[TASK-0206]]), **PASSer** (API, and a 399 KB cache exists
     on the `allosteric` branch — reuse it, do not re-fetch what is cached), and
     **PocketMiner** (ported; a Dockerfile exists on the `allosteric` branch and
     [[TASK-0163]] ran it in an isolated repo). `p2rank` has a Dockerfile too
     (`REPRODUCIBILITY.md`) — include it as a fourth **only if** it costs under an
     hour, otherwise state it was skipped and why.
  2. **One structure set, one truth definition, one overlap rule, for every
     detector.** This is [[TASK-0336]]'s lesson and it is the whole task: that
     comparison died last time because two arms were scored against different
     candidate sets with different multiplicity. Any detector that cannot be run
     on a given structure drops that structure **for every arm**, not just its own.
  3. Report the cascade, pairwise Jaccard between detectors, and the count of
     structures where exactly one detector fires — the "78 in between" analogue.
  4. State the per-detector coverage (how many structures each could be run on at
     all) **separately** from its hit rate. A detector that skips hard structures
     looks better than it is.
- **Out of scope:**
  - Any CTQW or quantum arm. This task touches none of them.
  - Re-tuning, re-ranking, or selecting a detector for the pipeline.
  - Building a meta-classifier over detectors — that is [[TASK-0306]]'s pattern and
    a separate question. Measure the cascade first.
- **Constraints and invariants:** detector versions pinned and recorded; the
  overlap/truth rule written down once before scoring and applied identically;
  cached PASSer results used as-is rather than re-queried, with the cache's own
  provenance stated.
- **Planned Validation:** fpocket must reproduce its own committed numbers from
  [[TASK-0163]]/[[TASK-0206]] on the overlapping structures before any
  cross-detector number is trusted. If the vendored binary has drifted again,
  that is the finding and the task stops there.

## Pre-registered prediction

Two-sided, written before running. **If the cascade is shallow** (detectors mostly
agree), the fpocket-vs-PASSer cohort dispute is a small effect and we should say so
plainly — that is a useful, deflationary result. **If it is steep** (an
at-least-one figure far above the all-three figure), it reproduces the 84% -> 17.8%
pattern in a second domain and materially strengthens the benchmark proposal.
Neither outcome is a point scored against the other branch.

## Budget

Capped. Detector runs plus scoring should be well under a day; the expensive part
is PocketMiner setup, which already exists in two places. If setup alone exceeds
half a day, report the two-detector cascade (fpocket vs PASSer) and disclose
PocketMiner as not run rather than delivering nothing.

## Dependency

- [[TASK-0306]] (Done) — the cascade format and `scripts/task0306_six_measure_meta_classifier.py`.
- [[TASK-0336]] (Done) — why matched candidate sets and matched multiplicity are
  load-bearing, and what happens when they are not.
- [[TASK-0163]]/[[TASK-0206]] (Done) — the fpocket binary, its pin, and its
  committed numbers.
- [[TASK-0327]] (Done) — the PASSer cache and the pocket-score convention it uses.

## Staged Files

- [2026-09-09 21:13] `.ai/tools/submission_build_latex.py` -- glyph map: tau, langle, rangle
- [2026-09-09 21:13] `__WORK_IN_PROGRESS__/documentation/2026-09-09-allosteric-branch-message-DRAFT.md` -- addendum on their joint experiment design
- [2026-09-09 21:13] `.ai/tasks/TODO/TASK-0360-detector-agreement-cascade.md` -- the task file itself
