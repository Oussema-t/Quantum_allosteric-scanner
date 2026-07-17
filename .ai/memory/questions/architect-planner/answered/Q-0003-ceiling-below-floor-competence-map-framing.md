# Q-0003 Does the ceiling-below-floor finding change the floor/ceiling/headroom framing itself?

## Context

- ID: Q-0003 (architect-planner addressee folder)
- Status: Answered
- Addressee: Architect/Planner
- Raised By: Implementer C, 2026-07-15
- Related: [[TASK-0046]] (ceiling coordinate-descent search, Done),
  [[TASK-0082]] (competence map synthesis, in progress), [[TASK-0094]]
  (proximity floor, Done). Shared-memory pitfall filed alongside this
  question: `.ai/memory/shared/pitfalls.md` P-0002.

## Question

KRAS_G12C's real ceiling (a 60-trial random search over `H_new`'s entire
physical-scalar space, answer key in hand throughout, CTQW propagation)
scores 0.5239–0.5250 AUC — **below** that same target's proximity floor
(0.798). Every point in the searched parameter space, evaluated against
the real labeled pocket, loses to a baseline that only knows distance
from the seed. This is not "actual doesn't clear floor" (TASK-0093's
already-reported finding) — it is "the best case of the entire operator
family, fully informed, doesn't clear floor either."

Two questions this raises that are above my pay grade as the implementer
who found it:

1. **Does this call the floor/ceiling/headroom framing itself into
   question for `H_new`/CTQW on this target** — i.e. is "headroom" a
   meaningful quantity to keep reporting for KRAS_G12C at all, given the
   denominator (`ceiling - floor`) is negative? Or is this scoped to
   KRAS_G12C specifically (BCR_ABL1's ceiling, 0.6118, *does* clear its
   own floor, 0.565 — just barely, and the *actual* pipeline result,
   0.525, does not) and the framework is fine elsewhere?
2. **Does a ceiling this low change how confidently Phase 2's "gates
   before build" logic should be read for KRAS_G12C** — `PLAN.md`'s own
   framing treats a low optimized-AUC (~0.53, already documented) as
   evidence the answer isn't recoverable from apo topology via this
   operator family. This finding is stronger than that: it shows the
   *entire searched space* is dominated by geometry, not just the
   default point. Is that worth promoting from "consistent with the
   existing near-chance finding" to its own headline claim in whatever
   document ends up being the submission's central narrative?

## Background

TASK-0046 (this session, 2026-07-14/15) ported notebook §8's
"interpretable parameter optimization" (a blind random search over
`(lam_B, lam_T, lam_R, lam_C, lam_M, alpha, cutoff, n_low_modes)`, 60
trials, seed=7) into `ceiling.ceiling_search`, run inside
`protocol.ceiling_context()`. Real KRAS_G12C cross-check:
`AUC_apo` at the best of 60 trials = 0.5239–0.5250 (two independent real
runs, tiny floating-point/BLAS-threading divergence between them, not a
methodology difference — both squarely "near chance", matching
`PLAN.md`'s own pre-existing qualitative finding "optimized AUC_apo on
KRAS ~= 0.53"). TASK-0094's real proximity floor for this same target
(same apo data, same source, same cutoff) is 0.798
(`euclid_from_seed_centroid`/`hop_from_seed`/`degree_centrality`, the
max of the three).

This was discovered while assembling TASK-0082's competence map (the
floor/ceiling/actual/headroom table) — `headroom = (actual - floor) /
(ceiling - floor)` produces a negative-denominator, meaningless fraction
for KRAS_G12C when computed mechanically. Filed as its own pitfall
(P-0002) rather than silently patched into a number, per this session's
own discipline. TASK-0082 itself is proceeding by reporting this
explicitly (no fraction, the finding stated in words) for KRAS_G12C's
row — this question is about whether that's *also* the right call for
how the finding gets framed in whatever narrative document the
submission ultimately uses, which is an Architect-level source-of-truth
decision, not an implementer one.

**Update, same day, discovered after this question was drafted**: a
separate Architect/Critic-overlay pass (`REVIEW-2026-07-15-execution-
plan-gap-audit.md`, `REVIEW-2026-07-15b-ceiling-search-methodology.md`)
independently reached this exact task and filed two directly relevant
gaps — [[TASK-0116]] (the 60-trial blind random search this finding
rests on is weak evidence for a *negative* claim specifically, though
adequate for a positive one) and [[TASK-0117]] (the ceiling search
shares every other headline AUC's unvalidated `t_max`/`n_steps`), plus
[[TASK-0112]] (no CI on any number in this competence map at all). None
of the three retract the ceiling-below-floor number; they change how
confidently it can be framed. `COMPETENCE_MAP.md` (`__WORK_IN_PROGRESS__/`)
has been updated to carry this caveat inline everywhere the finding is
stated. **This softens question 1 above**: the answer may simply be
"wait for TASK-0116/0117, then re-ask" rather than a framing decision
to make now on the current evidence. Still worth an explicit answer,
since "wait" vs. "the null-result framing is fine even under this much
search-coverage uncertainty" are different Architect-level calls with
different implications for what the submission draft can safely claim
in the meantime.

**Update 2026-07-16, [[TASK-0118]]: the finding this question is built on no longer
holds as stated.** `REVIEW-panel-2026-07-16-v2` (§2.1) found that the 0.5239–0.5250
ceiling and the 0.798 floor cited above were computed under two *different* seed
conventions (`ceiling_search_batched.py` used the full active-site array;
`run_challenge.py`'s floor/actual used a single representative index, a
[[TASK-0090]] crash workaround) — not a real floor-vs-ceiling comparison. TASK-0118
fixed the crash, declared one convention (full active-site array, incoherent mixture),
and re-ran both: under the corrected convention, KRAS_G12C's ceiling (0.5269) **does**
clear its floor (0.4818), by +0.045. "The best case of the entire operator family,
fully informed, doesn't clear floor either" is retracted — it was an artifact of the
gauge, not a property of the operator family. Full numbers: `COMPETENCE_MAP.md`'s
KRAS_G12C section, `.ai/invariants/INV-0006`.

This resolves Question 1 above in a specific way worth stating plainly for whoever
formally closes this question: **the floor/ceiling/headroom framing itself was never
the problem** — it correctly surfaced a real inconsistency (via P-0002's negative-
denominator symptom) that traced back to the seed gauge, not to the framing being
wrong for this target. Question 2 (how confidently to read a low ceiling) is now
moot for KRAS_G12C specifically (the ceiling isn't low relative to its floor anymore),
but the underlying TASK-0116/0117 concerns (search coverage, clock validation) still
apply to the *new* ceiling number exactly as they applied to the old one — not resolved
by this correction, just now aimed at a different number.

## Answer

**Closing, per TASK-0118's own 2026-07-16 update above.**

1. **The floor/ceiling/headroom framing itself was never the problem.** It correctly
   surfaced a real inconsistency — the negative-denominator symptom (P-0002) was the
   framework doing its job, not evidence the framework is wrong for this operator family.
   The actual defect was a seed-convention mismatch between two code paths
   (`ceiling_search_batched.py`'s full array vs. `run_challenge.py`'s single-index crash
   workaround), not a property of `H_new`/CTQW on KRAS_G12C. Keep the framing as-is going
   forward; no redesign warranted.
2. **Question 2 (how confidently to read a low ceiling) is moot for KRAS_G12C specifically**
   — under the corrected, single, declared convention (TASK-0118: full active-site array,
   incoherent mixture), the ceiling (0.5269) clears the floor (0.4818) by +0.045. There is
   no low-ceiling-below-floor number left to read cautiously for this target. The
   underlying TASK-0116/0117 concerns (search coverage, clock validation) still apply to
   this *new* ceiling number, unresolved by this closure — they were never specific to the
   old, gauge-contaminated one.
3. **One thing this closure does not settle, flagged for whoever next touches
   `COMPETENCE_MAP.md`**: TASK-0118's own re-run and TASK-0119's independent per-operator
   clock fix landed concurrently and were never combined (see [[TASK-0129]], filed
   2026-07-16/17 to do exactly that). The +0.045 KRAS_G12C margin above is real under
   TASK-0118's seed fix alone, computed at the old shared `t_max=15` — not yet the
   pipeline's fully gauge-fixed state. Read it as "the seed-only correction," not "the
   final number."

## Action

No code/task-design action needed beyond what's already in flight — [[TASK-0116]]/
[[TASK-0117]] (ceiling search coverage/clock validation, still TODO) and [[TASK-0129]]
(combined seed+clock re-run, filed this session) carry the remaining open threads forward.
Filed straight to `answered/`, matching [[Q-0001]]/[[Q-0002]]'s precedent for questions that
resolve without a distinct new follow-up task of their own.
