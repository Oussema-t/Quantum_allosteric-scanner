# Competence Map — TASK-0082

**The submission's central claim, per `EXECUTION_PLAN.md` Phase 5 item 5.2: "We close
X% of the gap knowing the answer would close, on these targets; ~0 on those, and here
is why." A per-target honest NO is a publishable result, not a failure to hide.**

This document synthesizes, per target: **floor** (the strongest trivial baseline the
score must beat — `baselines.degree_centrality`/`euclid_from_seed_centroid`/
`hop_from_seed`, [[TASK-0094]]), **ceiling** (the best AUC a 60-trial random search over
`H_new`'s entire physical-scalar space can reach *with the answer key in hand*,
[[TASK-0046]]), **actual** (the real, frozen-gated, blind-selected pipeline's headline
AUC, [[TASK-0079.005]]), and **headroom** (`(actual − floor) / (ceiling − floor)`, the
fraction of the floor-to-ceiling gap the actual pipeline closes) — for every mandatory
target, plus c-Myc's dedicated no-ground-truth row ([[TASK-0080]]).

**This document does not compute any of these numbers itself** (Out Of Scope, per this
task's own Intent Contract) — every value below is read from an already-real, already-
tested run and cited to its source. Where a number does not exist yet for a target (the
gated tasks below), that gap is stated explicitly, not filled with an estimate.

> **Caveat, added per this task's own Dependency section (2026-07-15,
> `REVIEW-2026-07-15`/`REVIEW-2026-07-15b`, filed the same day this document was first
> written): every number below is a bare point estimate with no confidence interval
> ([[TASK-0112]], open) — no floor-vs-score margin here should be read as a *decided*
> result yet. That finding additionally rests on a 60-trial blind random search over an
> ~8-dimensional space, flagged as weak evidence for a *negative* claim specifically
> (though adequate for a positive one) ([[TASK-0116]], open), and on the same unvalidated
> `t_max=15`/`n_steps=500` every other headline AUC in this project already carries as an
> open question ([[TASK-0117]]/[[TASK-0108]]/[[TASK-0109]]/[[TASK-0110]], open). None of
> this retracts the numbers — it is the difference between "the strongest evidence
> currently gathered says X" and "X is settled."**
>
> **Status update, 2026-07-19**: [[TASK-0112]] is Done and wired directly into this
> document's current (TASK-0130) numbers; [[TASK-0116]] is Done (`_PARAM_RANGES`
> corrected); [[TASK-0117]] is moot (TASK-0130 removed the clock parameter it was about);
> the sparse-search concern this caveat raised for TASK-0116 now has a real, quantitative
> answer per target via [[TASK-0131]]'s permutation null (see that section below) rather
> than remaining a qualitative flag. This top-level caveat is kept for the historical
> record of what was unknown when this document was first written, not as this document's
> current uncertainty inventory — see the "Open items" section near the end for that.**

> **SUPERSEDED 2026-07-16 by [[TASK-0118]] — the table below is a full recompute, not an
> edit of the old one. `REVIEW-panel-2026-07-16-v2` (§2.1) found that the numbers this
> document previously reported were gauge-contaminated: `run_challenge.py`'s floor/actual
> used a single representative seed residue (a [[TASK-0090]] crash workaround), while
> `ceiling_search_batched.py`'s ceiling already used the full active-site array —
> **floor/actual and ceiling were never comparable**, despite this document's prior text
> asserting "apples-to-apples within each row." TASK-0118 fixed the crash's root cause
> ([[TASK-0090]]), measured the real spread this caused on all 3 mandatory targets
> (KRAS_G12C: 0.326 AUC swing across seed conventions — [[INV-0006]]), declared **one**
> convention (full active-site array, incoherent statistical mixture — `propagators.ctqw`'s
> new `coherent=False`), and re-ran floor/ceiling/actual for every mandatory target under
> it. **The old numbers are not deleted** — see `git log` on this file, or
> [[TASK-0046]]/[[TASK-0082]]'s own Done sections, for the pre-TASK-0118 values (KRAS_G12C
> floor=0.798/ceiling=0.524/actual=0.779; BCR_ABL1 floor=0.565/ceiling=0.612/actual=0.525;
> CARDIAC_MYOSIN floor=0.764/ceiling=0.819/actual=0.786) — they are superseded, not wrong
> arithmetic; they were computed correctly under an inconsistent convention. Per this
> project's own no-silent-overwrite convention (TASK-0104's precedent) and TASK-0118's own
> explicit instruction ("report whatever the single-convention re-run actually finds — do
> not pre-decide it is a positive or a negative"): the KRAS_G12C "ceiling below floor"
> headline is **retracted** — under the one correct convention, the ceiling now clears the
> floor, same qualitative shape as BCR_ABL1. This is **not** a new positive claim for the
> *actual* (shipped) result, which still does not clear its floor for either target.**

> **SUPERSEDED AGAIN, 2026-07-17/18 by [[TASK-0129]] — combined with the clock fix
> ([[TASK-0119]]), landed concurrently with TASK-0118 but never combined with it until
> now.** TASK-0118 fixed the seed but left every number at the old shared `t_max=15`;
> TASK-0119 fixed the clock (`t* = -ln(tol)/gap` per operator) but left the old
> single-index seed. **Every number in the TASK-0118 table immediately above is
> therefore itself still gauge-contaminated — by the clock, not the seed.** TASK-0129
> re-ran floor/ceiling/actual (`scripts/combined_competence_map_rerun.py`) and the
> 96-cell operator sweep (`scripts/fix_clock_operator_sweep.py`, extended in place) under
> **both** fixes at once. Headline: **CARDIAC_MYOSIN's "actual clears its own floor,
> +75.1% headroom" does not survive** — it was an artifact of the still-too-short shared
> clock (`t_max=15` vs. `H_new`'s own true `t*=198`); under the correct clock, actual
> (0.7912) sits fractionally *below* its own floor (0.7921, margin −0.0009). **No
> mandatory target's shipped actual result cleanly clears its own floor under the fully
> corrected convention** — KRAS_G12C and BCR_ABL1's actual results are statistically
> indistinguishable from chance or below floor (unchanged in kind from before); real
> ceiling-vs-floor headroom exists for all three targets (a genuine, real finding — the
> operator family *can* discriminate above trivial proximity somewhere in its parameter
> space, on every target), but the shipped default configuration reaches it on none of
> them. Old numbers are not deleted — see the TASK-0118 table and prose immediately
> below, kept intact, now itself marked superseded rather than rewritten in place.

> **SUPERSEDED A THIRD TIME, 2026-07-18 by [[TASK-0130]] — the clock parameter itself is
> gone, not just corrected.** TASK-0129 (immediately above) still carried a `t*`/`t_max`
> to derive per operator; TASK-0110 had already found `time_averaged_ctqw`'s own
> literature-grounded convergence criterion for that clock is computationally infeasible
> to satisfy on real targets (145,000x-3,950,000x the shipped `t_max=15` default — a
> single call did not return after 2+ hours). TASK-0130 replaced `time_averaged_ctqw`'s
> finite-time approximation with its exact infinite-time closed form
> (`propagators.time_averaged_ctqw_converged`, `sum_k |v_k(j)|^2|v_k(source)|^2`,
> generalized to handle degenerate eigenspaces correctly per a real correctness bug the
> plain index formula would silently have — see that task's Done section) for every
> headline number's "ctqw" side — **there is no `t_max`/`t*`/`n_steps` left to choose,
> derive, or disclose for this quantity at all.** Re-ran floor/ceiling/actual (all 3
> mandatory targets) and the 96-cell operator sweep under this convention, both wired to
> [[TASK-0112]]'s bootstrap CI directly (not a separate pass). **Headline: KRAS_G12C's
> point-estimate diagnosis flips from `NO_SIGNAL_IN_APO` to `NO_FAILURE_DETECTED`** —
> actual (0.5901) now clears its own floor (0.4818) by a real point-estimate margin
> (+73.7% headroom) — **but the 95% CI still overlaps the floor's own CI
> (`ci_overlap=True`), so this is not a statistically decided win**, only a genuine change
> in the point estimate once the last unmeasured gauge (the clock) is removed rather than
> merely fixed. BCR_ABL1 and CARDIAC_MYOSIN's actual results remain statistically
> indistinguishable from their own floors under this convention too (both
> `ci_overlap=True`) — **no mandatory target's shipped actual result is a statistically
> decided win over its own floor**, the same qualitative conclusion as TASK-0129's, now
> reached with zero remaining clock-gauge uncertainty. Old numbers (TASK-0129's own table,
> immediately below) are not deleted.

---

## Mandatory targets — floor / ceiling / actual / headroom

**Recomputed 2026-07-18 under [[TASK-0130]]'s closed-form fix — `time_averaged_ctqw`'s
exact infinite-time limit (`propagators.time_averaged_ctqw_converged`), full-array
incoherent-mixture seed (unchanged from TASK-0118/0129). No `t_max`/`t*`/`n_steps` column
below: there is no finite-time clock parameter left for this quantity at all — the whole
column TASK-0129's own table below carried (`t*`) no longer exists as a concept. All
numbers carry a 95% block-bootstrap CI ([[TASK-0112]]), wired in directly.**

| Target | Floor [95% CI] | Ceiling [95% CI] | Actual (AUC) [95% CI] | Diagnosis | Headroom | CI overlaps floor? |
|---|---|---|---|---|---|---|
| KRAS_G12C | 0.4818 [0.333, 0.675] | 0.6288 [0.466, 0.773] | 0.5901 [0.373, 0.748] | `NO_FAILURE_DETECTED` | **+73.7%** (point estimate clears floor) | **Yes** — not statistically decided |
| BCR_ABL1 | 0.5817 [0.414, 0.720] | 0.6671 [0.530, 0.784] | 0.5266 [0.381, 0.662] | `NO_SIGNAL_IN_APO` | **−64.5%** | Yes |
| CARDIAC_MYOSIN | 0.7921 [0.577, 0.913] | 0.8297 [0.615, 0.926] | 0.7272 [0.549, 0.853] | `BEATS_CHANCE_NOT_FLOOR` | **−173.0%** | Yes |

**Headline: KRAS_G12C's point-estimate diagnosis changes** (`NO_SIGNAL_IN_APO` under
TASK-0129 -> `NO_FAILURE_DETECTED` here) — the actual result's point estimate now clears
its own floor by a real margin, a genuine change once the clock gauge is fully removed
rather than merely corrected. **This is not yet a statistically decided win**: the actual
and floor 95% CIs still overlap substantially. BCR_ABL1 and CARDIAC_MYOSIN show the same
qualitative shape as TASK-0129 (actual does not clear floor, CIs overlap either way) — the
closed form did not manufacture a different story for either. Every ceiling still clears
its own floor as a point estimate (real headroom exists in `H_new`'s physical-scalar space
for all three targets), but every ceiling-vs-floor CI overlaps too — none of the three is
a statistically decided ceiling-over-floor margin either, a caveat TASK-0129's own table
did not carry (pre-TASK-0112-wiring for this specific script). Sources:
- **This recompute (all columns + CI)**: `results_task0130_competence/
  closed_form_competence.json` (`scripts/closed_form_competence_map_rerun.py`) —
  standalone script calling `protocol.run_frozen_verdict`/`ceiling.ceiling_search` with
  the new `use_converged_limit=True` option (TASK-0130, ADD-only on both functions and on
  `analysis.benchmark`/`analysis.quantum_vs_classical`/`analysis.operator_sweep`/
  `ceiling.consistency_score`), same "standalone, does not touch live pipeline defaults"
  discipline as TASK-0129's own script.
- **96-cell operator-level cross-check**: `results_task0130_competence/
  closed_form_sweep.json`/`sweep_report.md` (`scripts/closed_form_operator_sweep.py`)
  independently reproduces KRAS_G12C's `H_new`/`ctqw` AUC to 3 decimals (0.590 both
  places) via a separate code path (`analysis.operator_sweep`, not `run_frozen_verdict`).
- **BCR_ABL1 CTQW-trapping reproduction (TASK-0106) under the closed form**: `results_
  task0130_competence/trapping_reproduction_closed_form.json` — a real, unflagged finding
  worth stating plainly: at the true infinite-time limit, `H_new_default`'s participation
  ratio (0.0079) is no longer distinguishable in kind from `H10`/`H2`'s (0.0077-0.0079) —
  the localization/trapping *contrast* between `H_new` and the transport-preserving
  baselines that TASK-0106/TASK-0119 measured at finite `t_max`/`t*` (PR 0.299 vs.
  comparable) largely washes out once every eigenmode has had time to contribute. This
  does not retract TASK-0119's own finding (real and gauge-robust *at the timescale it
  measured*) — it shows that timescale is not the converged/infinite-time endpoint, a
  distinct fact worth a dedicated read rather than silently reconciling the two numbers.

### Permutation null for the ceiling ([[TASK-0131]]) — decides whether "ceiling clears floor" is real signal or the winner's curse

**The competence map's only nonnegative claim, tested directly.** Every ceiling number
above is the **maximum** AUC over 60 blind random draws against the real pocket label — a
maximum over K noisy draws is upward-biased by construction (the winner's curse / look-
elsewhere effect), independent of whether real signal exists in the operator family. This
section runs the identical 60-trial search protocol (`ceiling.ceiling_search(use_
converged_limit=True, coherent=False)` — the actual TASK-0130 procedure that produced the
ceiling numbers above, not the now-superseded finite-`t_max` script the task was
originally filed against) against **permuted** pocket labels (same size, shuffled
identity), 200 replicates per target, and reports each target's real ceiling-minus-floor
margin as a percentile of its own null.

| Target | Real margin | Null median | Null SD | Null max | Percentile | One-sided p (n=200) | Bonferroni-corrected (x3) |
|---|---|---|---|---|---|---|---|
| KRAS_G12C | 0.1470 | 0.0545 | 0.0512 | 0.1941 | 95.5th | **0.045** | 0.135 |
| BCR_ABL1 | 0.0854 | 0.0316 | 0.0568 | 0.1450 | 90.0th | 0.100 | 0.300 |
| CARDIAC_MYOSIN | 0.0375 | 0.0326 | 0.0453 | 0.1546 | 55.0th | 0.450 | 1.000 |

**Headline, real and not uniform across targets — the three "ceiling clears floor" margins
do not carry the same evidentiary weight**:
- **CARDIAC_MYOSIN's headroom claim is fully explained by the winner's-curse bias alone.**
  Its real margin (0.0375) sits at the 55th percentile of pure noise doing the identical
  60-trial max-search procedure against a same-sized random label — indistinguishable from
  what a genuinely null operator family produces. The "+0.064" (TASK-0129) / real-margin-
  0.0375 (TASK-0130) headroom this document has carried since TASK-0082 was never
  meaningful evidence of real capacity in `H_new`'s parameter space for this target.
- **KRAS_G12C's margin is real, uncorrected-significant (p=0.045), but does not survive a
  naive Bonferroni correction for testing 3 targets (p=0.135).** The strongest of the
  three by a real margin — worth flagging as the one target where genuine headroom in the
  operator family is plausible, not asserted as decided. 200 replicates give p-value
  resolution of 0.005 (vs. the review's own preliminary 12-replicate estimate's ~0.083) —
  precise enough to place this specific number, not just its bulk.
- **BCR_ABL1 is intermediate and inconclusive** (p=0.10, 0.30 corrected) — above the null's
  median but not distinguishable from noise at any conventional threshold.

**This does not change any diagnosis category** (`NO_FAILURE_DETECTED`/`NO_SIGNAL_IN_APO`/
`BEATS_CHANCE_NOT_FLOOR` above are `classify_failure`'s point-estimate verdicts on
*actual* vs. floor/chance, a different comparison than ceiling-vs-floor) — it changes how
confidently the *ceiling* numbers specifically should be read as "real headroom exists in
this operator family" vs. "an artifact of taking a maximum over 60 tries." Full null
distributions: `results_task0131_permutation_null/permutation_null.json`
(`scripts/ceiling_permutation_null.py`).

**Correction to `REVIEW-2026-07-15b-ceiling-search-methodology.md`'s own text** (per this
task's own In Scope, additive not silent): that review's Finding 1 argued "a single lucky
trial clearing the floor is real regardless of how the rest of the space looks," correct
for an *existence* claim but not for the *maximum-over-K* statistic this document actually
reports — see the dated correction appended to that file directly.

### TASK-0129's own table (combined seed+clock fix, superseded above) — kept for the old-vs-new record, no longer this document's current state

**Recomputed 2026-07-17/18 under [[TASK-0129]]'s combined fix (TASK-0118's full-array
incoherent-mixture seed AND TASK-0119's per-operator `t*`, together) — see the
SUPERSEDED notices above for the pre-TASK-0129 numbers. `t*` below is `H_new`'s own
default-config spectral gap, applied uniformly to both benchmark candidates and every
ceiling trial (a stated simplification — see `scripts/combined_competence_map_rerun.py`'s
own docstring and this task's Done section for why, and `H10`'s own, not separately
computed, `t*`).**

| Target | Floor | Ceiling | Actual (AUC) | Diagnosis | Headroom | `t*` (H_new) |
|---|---|---|---|---|---|---|
| KRAS_G12C | 0.4818 | 0.6034 | 0.5442 | `NO_SIGNAL_IN_APO` | **+51.3%** (numerically above floor, but statistically indistinguishable from chance) | 127 |
| BCR_ABL1 | 0.5817 | 0.6716 | 0.5305 | `NO_SIGNAL_IN_APO` | **−57.0%** | 123 (see reproducibility caveat below) |
| CARDIAC_MYOSIN | 0.7921 | 0.8558 | 0.7912 | `BEATS_CHANCE_NOT_FLOOR` | **−1.4%** — misses its own floor by 0.0009, essentially a tie, not a win | 198 |

Every ceiling now clears its own floor (KRAS +0.122, BCR_ABL1 +0.090, CARDIAC_MYOSIN
+0.064) — real, if modest, headroom exists in `H_new`'s physical-scalar space for **all
three** mandatory targets under the fully corrected convention. **None of the three
shipped actual results reach it.** All three columns are CTQW-propagated, `H_new`-family
numbers throughout (floor, ceiling, and actual all use `time_averaged_ctqw`, never a mix
with `ground_state_relaxation`/"heat"), and share one seed convention *and* one clock
convention within each row. Sources:
- **This recompute (all three columns + `t*`)**: `results_task0129_competence/
  combined_competence.json` (`scripts/combined_competence_map_rerun.py`) — a standalone
  script calling `protocol.run_frozen_verdict`/`ceiling.ceiling_search` directly with the
  combined-fix parameters, deliberately *not* an edit to `run_challenge.py`'s or
  `ceiling_search_batched.py`'s own live defaults (TASK-0119's own Done section already
  treated promoting a research clock into the live pipeline as "a separate, follow-up
  decision," and TASK-0129's own Out Of Scope forbids "building any new fix" — this
  script applies two already-built ones together without touching either live script).
- **96-cell operator-level cross-check**: `results_task0129/combined_sweep.json`/
  `report.md` (`scripts/fix_clock_operator_sweep.py`) independently reproduces
  CARDIAC_MYOSIN's `H_new`/`ctqw` combined AUC to 4 decimals (0.7912 both places) via a
  completely separate code path (`analysis.operator_sweep`, not `run_frozen_verdict`) —
  cross-validates the headline finding is not a bug in one script.

### TASK-0118's own table (seed-only, still `t_max=15`) — kept for the old-vs-new record, no longer this document's current state

| Target | Floor | Ceiling | Actual (AUC) | Diagnosis | Headroom |
|---|---|---|---|---|---|
| KRAS_G12C | 0.4818 | 0.5269 | 0.4614 | `NO_SIGNAL_IN_APO` | −45.3% (actual below floor; ceiling clears floor, +0.045) |
| BCR_ABL1 | 0.5817 | 0.6057 | 0.5608 | `BEATS_CHANCE_NOT_FLOOR` | −86.9% (actual below floor; ceiling clears floor by +0.024) |
| CARDIAC_MYOSIN | 0.7921 | 0.8439 | 0.8310 | `NO_FAILURE_DETECTED` | +75.1% — **did not survive the clock fix, see TASK-0129 table above** |

TASK-0118's own sources for the table directly above:
- **Floor**: computed fresh this recompute, same `degree_centrality`/
  `euclid_from_seed_centroid`/`hop_from_seed` stack ([[TASK-0094]]), max of the three,
  under the new full-array source (`scripts/seed_convention_sweep.py`'s own floor
  computation, cross-checked against a direct re-derivation — both agree to 6 decimals).
- **Ceiling**: `results_task0118_ceiling/<target>/ceiling_trials.jsonl` (fresh checkpoint
  directory — deliberately *not* resuming `results_task0082/`'s old, `coherent=True`-only
  checkpoints, which would have silently mixed conventions within one "completed" trial
  set), 60 real trials each, `ceiling.ceiling_search`/`ceiling_search_batched.py --seed 7`,
  `coherent=False` (this script's own new default), `protocol.ceiling_context()`.
- **Actual**: `results_task0118/<target>/verdict.json`'s `AUC_apo_Hnew_optimised`, a fresh
  `run_challenge.py` run (full active-site array, `coherent=False`, single-index
  workaround removed).
- **Diagnosis**: `verdict.json`'s own `_diagnosis` field, this time genuinely
  authoritative (floor-aware — `floor_scores` is passed into this recompute's
  `run_frozen_verdict` call, unlike whatever produced the stale field the old table's
  own text warned about).

### KRAS_G12C — "ceiling below floor" is retracted; the actual result is still below floor

**[[TASK-0118]], 2026-07-16: retracted.** The pre-recompute claim ("the ceiling itself
does not clear the floor... the strongest form of honest NO this competence map can
report") rested on comparing a single-index floor/actual (0.798/0.779) against a
full-array ceiling (0.524) — two different seed conventions, not a real floor-vs-ceiling
comparison. Under the one declared convention (full active-site array, incoherent
mixture), **the ceiling (0.5269) does clear the floor (0.4818), by +0.045** — real,
if modest, headroom exists in `H_new`'s physical-scalar space for this target after all.
This is **not** a new positive claim for the submission: the *actual*, shipped
default-parameter result (0.4614) remains below its own floor (`NO_SIGNAL_IN_APO`,
statistically indistinguishable from chance) — the operator family has headroom the
shipped configuration does not reach, the same shape BCR_ABL1 already showed. TASK-0116's
open question (is 60 blind draws over ~8 dimensions adequate search coverage) and
TASK-0117's (is `t_max=15`/`n_steps=500` validated) both still apply to this recomputed
ceiling exactly as they applied to the old one — neither is resolved by this recompute,
and [[Q-0003]] (whether floor/ceiling/headroom is even the right lens here) is answered
in one direction by this correction (the framing itself was sound; the seed gauge
feeding it was not) but the CI/search-coverage/clock questions remain genuinely open.

**Pre-TASK-0118 numbers, preserved for the record, not endorsed**: floor=0.798,
ceiling=0.524–0.525, actual=0.779, headroom "undefined (ceiling < floor)". See the
SUPERSEDED notice above and `git log` on this file for the full prior text.

**[[TASK-0129]], 2026-07-17/18, combined with the clock fix**: floor=0.4818 (unchanged
by the clock), ceiling=0.6034 (up from 0.5269 — a longer, correctly-converged `t*=127`
finds a *better* ceiling here, not a worse one, unlike CARDIAC_MYOSIN below), actual=
0.5442 (up from 0.4614). Actual is now numerically *above* its own floor (+51.3%
headroom, arithmetically) but `classify_failure`'s chance check fires first
(`|0.5442−0.5|=0.044 < 0.05` tolerance) — `NO_SIGNAL_IN_APO`, statistically
indistinguishable from chance, not a clean floor-clearing win. Read together with
CARDIAC_MYOSIN below: **the clock fix does not push every target's numbers the same
direction** — it revealed real headroom here, and erased an apparent positive there.

### BCR_ABL1 — actual scores below its own floor (recomputed, same shape as before)

**[[TASK-0118]], 2026-07-16: numbers recomputed, qualitative finding unchanged.**
Headroom is a well-defined but negative fraction: the shipped pipeline's actual CTQW
result (0.5608) is *worse* than the strongest trivial proximity baseline (0.5817) for
this target — consistent with `BEATS_CHANCE_NOT_FLOOR`. The ceiling here (0.6057) *does*
clear the floor, by a modest margin (+0.024, down from the pre-recompute +0.047 —
same qualitative shape, smaller margin under the corrected convention) — so there is, in
principle, real headroom in this operator family for this target; the shipped
default-parameter configuration simply does not reach it. **Separately** (not part of
this headroom calculation, a different propagator entirely, and *not* re-run by
TASK-0118 — `ground_state_relaxation`'s multi-index source was already correctly an
incoherent classical mixture before this task, see [[INV-0006]]'s KNOB row): 
`ground_state_relaxation` on the same `H_new` operator scores 0.7315, clearing the same
floor decisively (margin +0.166) — but per [[TASK-0104]]'s already-corrected framing,
that is a structural-prior/cryptic-pocket signature (the well, not the coupling —
[[TASK-0103]]'s dumbbell negative control), not allosteric communication, and is not
folded into this CTQW-based headroom row.

**[[TASK-0129]], 2026-07-17/18, combined with the clock fix**: floor unchanged (0.5817),
ceiling=0.6716 (up from 0.6057), actual=0.5305 (down slightly from 0.5608, still
`NO_SIGNAL_IN_APO`) — same qualitative shape as TASK-0118 alone (actual below floor,
real ceiling headroom), numbers shifted, conclusion unchanged.

**Reproducibility flag, found while computing this target's `t*` (not chased further —
out of this task's own scope, a numerical-stability question, not a seed/clock-fix
question):** `H_new`'s spectral gap for BCR_ABL1, freshly computed twice in the current
environment via two independent code paths (`combined_competence_map_rerun.py` and
`fix_clock_operator_sweep.py`), agrees with itself (`gap=0.0374`, `t*=123.1`) but
**disagrees with [[TASK-0119]]'s own recorded value for the same nominal quantity**
(`gap=0.1933`, `t*=23.8`) — `coords`/`bfactors`/`cutoff` were confirmed byte-identical
between the current and TASK-0119's own `_prepare_target` call, so this is not a data
difference; likely explained by BCR_ABL1's `H_new` ground state sitting in a genuine
near-continuum (the lowest 8 eigenvalues are packed within a span of ~0.14, each
consecutive gap only 0.016–0.05 apart) rather than an isolated, well-separated minimum
— making *which* pair of eigenvalues numerically resolves as "the gap" fragile to
environmental numerical variation (BLAS threading/reduction order) for this specific
operator/target, not a bug in either computation. Flagged, not resolved — a genuine
open question about the gap-based `t*` prescription's own robustness on a
near-degenerate spectrum, orthogonal to this task's seed+clock combination work.

**Correction, 2026-07-19 ([[TASK-0135]], [[INV-0008]]):** the "BLAS
threading/reduction order" attribution above was never directly tested
and is now refuted by one. A real, controlled test (3 independent fresh
computations, plus `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/
`MKL_NUM_THREADS` varied `1/2/4/8`) found this exact quantity
reproduces to 14+ significant figures regardless of thread count —
environmental variation of that kind is real but ~11 orders of
magnitude too small to produce this row's 5.2x discrepancy. The real
explanation traces to [[TASK-0102]]'s cached `H_new` object (2026-07-13,
5 days before [[TASK-0121]] changed `build_H_new`'s defaults, among
other intervening code changes) — a stale-object/code-version mismatch,
not run-to-run nondeterminism. Moot for this document's own current
numbers either way: [[TASK-0130]] deleted the gap-based clock entirely.

**Reconciliation with [[TASK-0110]]'s BCR_ABL1 short-`t_max` finding** (practical
ceiling AUC=0.5829 at `t_max=2.39`, found by an Optuna search over `t_max`/`n_steps` at
`H_new`'s *default* physical parameters, `coherent=True`, per that task's own
Constraints): **in tension, not agreement.** TASK-0110's own AUC-optimal time (2.39) is
roughly 10–50x shorter than either estimate of `H_new`'s numerically-adequate
convergence time on this target (23.8 or 123.1, per the discrepancy above) — and this
task's own combined result at the *longer*, convergence-correct time scores
*worse* (0.5305, `coherent=False`) than TASK-0110's short-time optimum. Read together:
**propagating BCR_ABL1's `H_new` operator toward its true decoherent limit does not
improve discrimination — it may actively hurt it**, and the best-discriminating time
point found so far (2.39) is far shorter than what any convergence criterion this
project has built would prescribe. Not reconciled here (would require a real `coherent=
False` re-run of TASK-0110's own `t_max`/`n_steps` Optuna search, a distinct piece of
work — "building a new fix," explicitly out of this task's own scope) — reported as an
open, unexplained tension for a future task to resolve, exactly as this task's own
Intent Contract asked for ("report the relationship explicitly, don't silently
reconcile or silently ignore the discrepancy").

### CARDIAC_MYOSIN — now clears its own floor, but for two confounded reasons, neither of which is a clean win

**[[TASK-0118]], 2026-07-16: diagnosis changed from `INSUFFICIENT_RESOLUTION` to
`NO_FAILURE_DETECTED`, for two independent reasons — read both before treating this as
a positive result.**

1. **The seed-convention fix itself** (this task): actual AUC moved from 0.786 (old,
   single-index) to 0.8310 (new, full-array incoherent mixture) — a real change, cited
   in the table above.
2. **An unrelated, pre-existing fact discovered while re-running this target**:
   `diagnostics.LARGE_N_THRESHOLD` was raised from 800 to 1000 on 2026-07-14 (see that
   constant's own code comment — "explicit user direction," no task ID assigned, no
   science claim, purely a computational-scaling ceiling), which alone flips this
   target's `INSUFFICIENT_RESOLUTION` flag off (N=950 < 1000) **regardless of the seed
   fix** — this document's own "40.7% headroom, invalidated before it can be read"
   framing had already gone stale before TASK-0118 touched anything, simply not yet
   propagated here.

**What this does and does not license claiming**: the arithmetic is real — floor=0.7921,
ceiling=0.8439, actual=0.8310, headroom=+75.1%, and the actual result genuinely clears
its own floor now. But this target's apo structure (5TBY) still carries its own
independent, pre-existing data-quality caveat (`config/targets.yaml`: 20 Å cryo-EM IHM
assembly, non-crystallographic B-factors, unverified chain assignment against a 6-chain
complex) — `REVIEW-panel-2026-07-16-v2` Sec.1.2 names this exact structure as "the worst
structure in the set" and explicitly warns against building the submission's one positive
on it. **[[TASK-0124]]** (re-anchor or retire CARDIAC_MYOSIN) already exists to resolve
this open question and is the right place to decide whether this number is reportable at
all, not this document. Until TASK-0124 lands, this row is reported factually, flagged,
and not endorsed as the submission's clean positive.

**[[TASK-0129]], 2026-07-17/18: the positive above does not survive the clock fix — a
third, decisive reason, on top of the two already flagged.** `H_new`'s own true
convergence time for this target is `t*=198` (`n*=158` steps), far longer than the
shared `t_max=15` every number above still used. Under the correct clock (still combined
with TASK-0118's seed fix — floor unchanged at 0.7921, since floor doesn't depend on the
clock): **actual AUC drops to 0.7912, landing 0.0009 *below* its own floor**
(`BEATS_CHANCE_NOT_FLOOR`, not `NO_FAILURE_DETECTED`) — headroom flips from +75.1% to
−1.4%. Independently cross-checked via a completely separate code path
(`analysis.operator_sweep`'s own `H_new`/`ctqw` cell, `results_task0129/
combined_sweep.json`): **0.7912, matching to 4 decimals** — not a fluke of one script.
The ceiling (0.8558) still clears the floor by a real margin (+0.064), so headroom
exists in the operator family, same story as KRAS_G12C/BCR_ABL1 now — this target no
longer stands apart as "the one target with a floor-clearing actual result," it joins
the other two. **All three of this section's own reasons for caution (seed, `LARGE_N_
THRESHOLD`, and now the clock) point the same direction**: nothing about CARDIAC_MYOSIN's
apparent positive survived closer scrutiny. The 5TBY data-quality caveat and
[[TASK-0124]] remain the right place to resolve whether this target is usable at all —
now academic for the *headroom* question specifically (there is none to defend), still
live for whether this target should appear in the submission in any form.

---

## c-Myc / 1NKP — no ground truth (per [[TASK-0080]])

No floor, ceiling, actual, or headroom exists or is computed for this target — it has no
holo structure (`holo_pdb: null`) and no labeled allosteric pocket
(`allosteric_pocket_exists: false`), both by this target's own `config/targets.yaml`
status, not a scoring gap. Per this project's own convention, this absence is reported
explicitly rather than an empty row.

| Quantity | Value |
|---|---|
| Consensus top hit | residue 943, 3/4 independent operators agree (top-5) |
| Confidence | moderate — best cross-operator agreement is 3/4, not unanimous |
| Theoretical docking viability | unavailable — `fpocket` binary not installed in this environment |

Full narrative: `results_task0080/MYC_MAX/report.txt` (real run, 2026-07-15,
`run_challenge.py --target MYC_MAX`).

---

## Generalization targets (ASD, [[TASK-0081]])

Two targets, real network-gated runs, `config/targets.yaml`'s already-curated ASD
candidate pool (`TASK-0003`) — not the mandatory-set targets this session's ~15 prior
review cycles have already seen (per `REVIEW-2026-07-15`'s TASK-0115 finding: this is
the concrete mitigation for that repeated-exposure risk, not just bonus coverage). No
ceiling search run for either (out of TASK-0081's own scope; `ceiling_search_batched.py`
could extend to these targets cheaply if wanted later).

| Target | N | Pocket size | Actual AUC | Max floor | Diagnosis |
|---|---|---|---|---|---|
| PTP1B | 298 | 14 | **0.2497** (anti-correlated) | 0.4847 | `BEATS_CHANCE_NOT_FLOOR` |
| CASPASE7 | 461 | 7 | 0.7130 | 0.7565 | `BEATS_CHANCE_NOT_FLOOR` |

Neither clears its own floor — the same category as KRAS_G12C's mandatory-set result.
PTP1B is a genuinely distal allosteric site (~20 A from the catalytic residue, the
config's own `objective` field) and scores well below 0.5, not merely near it —
independent, cross-target corroboration of this project's central pattern (adjacent
pockets score artificially high via seed-proximity; distal pockets score at or below
chance) on a target none of this project's prior review history has examined. Full
selection rationale (including two ASD candidates that failed independent RCSB
verification and were not used) in `.ai/tasks/DONE/TASK-0081-generalization-set-asd-
targets.md`.

---

## Cross-target reading

**Recomputed 2026-07-18/19 ([[TASK-0130]] closed form + [[TASK-0131]] permutation null —
supersedes the TASK-0129-only reading immediately below, kept for the record.)** Under the
closed form (no clock parameter left at all), the actual-vs-floor picture is qualitatively
similar to TASK-0129's own reading, with one real change: **KRAS_G12C's point-estimate
diagnosis now clears its own floor** (`NO_SIGNAL_IN_APO` -> `NO_FAILURE_DETECTED`), though
not at a statistically decided level (its 95% CI still overlaps the floor's). The bigger
change is on the *ceiling* side, where TASK-0129's own headline — "real headroom exists in
`H_new`'s physical-scalar space for all three targets" — **does not survive contact with a
null.** TASK-0131's 200-replicate permutation null (identical search procedure, permuted
labels) found:

- **KRAS_G12C**: ceiling clears floor by +0.147, at the 95.5th percentile of pure noise
  doing the same procedure (p=0.045 uncorrected, 0.135 Bonferroni-corrected for 3 targets)
  — the one target where genuine headroom is plausible, not decided.
- **BCR_ABL1**: ceiling clears floor by +0.085, 90th percentile (p=0.10) — inconclusive,
  above the null's median but not distinguishable from noise at any conventional threshold.
- **CARDIAC_MYOSIN**: ceiling clears floor by +0.038, only the **55th percentile** of pure
  noise (p=0.45) — **statistically indistinguishable from what the identical 60-trial
  max-search procedure produces against a same-sized random label.** This target's
  "headroom" claim, carried in this document since TASK-0082, was never real evidence of
  operator-family capacity — it was the winner's-curse bias inherent in reporting a
  maximum over 60 draws.

**The honest headline is now target-specific, not uniform**: `H_new` under CTQW
propagation shows real, if unconfirmed-at-Bonferroni-correction, headroom over trivial
seed-proximity for KRAS_G12C specifically; BCR_ABL1 is inconclusive; CARDIAC_MYOSIN's
apparent headroom is a search-bias artifact, not a property of the operator family. The
shipped default-parameter configuration reaches none of this headroom regardless of
target. Full detail: the "Mandatory targets" table and "Permutation null" section above.

### TASK-0129's own cross-target reading (combined seed+clock fix, superseded above) — kept for the old-vs-new record, no longer this document's current state

**Recomputed 2026-07-17/18 ([[TASK-0129]], combined seed + clock fix — supersedes the
2026-07-16/[[TASK-0118]]-only reading immediately below, kept for the record.)** Under
the fully corrected convention, **no mandatory target's actual, shipped result clears
its own floor** — CARDIAC_MYOSIN's apparent positive, the one exception under the
seed-only fix, does not survive the clock fix. Real headroom exists in `H_new`'s
physical-scalar space for **all three** targets (every ceiling clears its own floor),
reached by **none** of them:

- **KRAS_G12C**: ceiling clears the floor (+0.122); actual is numerically above its
  floor but chance-indistinguishable (`NO_SIGNAL_IN_APO`).
- **BCR_ABL1**: ceiling clears the floor (+0.090); actual is chance-indistinguishable
  and below floor (`NO_SIGNAL_IN_APO`). In tension with [[TASK-0110]]'s own finding
  that a much *shorter* `t_max` (2.39) scores better than either convergence-motivated
  estimate — reported, not resolved, see this target's own section above.
- **CARDIAC_MYOSIN**: ceiling clears the floor (+0.064); actual now misses its own
  floor by 0.0009 (`BEATS_CHANCE_NOT_FLOOR`) — the seed-only fix's positive was an
  artifact of the still-too-short shared clock, confirmed by two independent code paths.

Per `PLAN.md`'s own "gates before build" framing, the honest headline **as of the
evidence gathered 2026-07-17/18** is narrower again, for the same reason it narrowed
the first time: not because the operator changed, but because two more gauges (this
time, the clock) turned out to still be contaminating what looked like real numbers.
**`H_new` under CTQW propagation, evaluated under one consistent seed convention and
one consistent, per-operator-correct clock, has real headroom over trivial seed-
proximity in its own physical-scalar space on all three mandatory targets — and the
shipped default-parameter configuration reaches that headroom on precisely zero of
them.** This is the strongest, most internally-consistent negative result this
competence map has produced so far, and — per this project's own honest-NO convention —
is reported as such, not softened. It is consistent with, not contradicted by, BCR_ABL1's
separate `ground_state_relaxation` finding (0.7315, floor-clearing), which
[[TASK-0104]] already reframes as a structural-prior signature rather than a
communication signal (and which this task did not re-run — `ground_state_relaxation`'s
own multi-index handling was already the incoherent convention, [[INV-0006]], and its
own clock question is [[TASK-0119]]'s and this task's shared, not yet separately
addressed for that propagator). **This headline should not be presented as final in a
submission draft while TASK-0112/0116/0117/0124 are open** (per the caveat at the top of
this document) — every one of those open questions applies to these newer numbers
exactly as it applied to the superseded ones, and the honest-NO framing this project
already practices means updating this document again without ceremony if stronger
evidence changes the picture.

### Pre-TASK-0129 cross-target reading ([[TASK-0118]] only, seed fix without the clock fix) — superseded, kept for the record

Under the seed-only fix, no mandatory target's actual result cleared its own floor
except CARDIAC_MYOSIN (+75.1% headroom, `NO_FAILURE_DETECTED`) — which TASK-0129 above
found does not survive combining the clock fix. KRAS_G12C (+0.045 ceiling margin) and
BCR_ABL1 (+0.024 ceiling margin) read qualitatively the same then as now; only
CARDIAC_MYOSIN's reading changed.

---

## Open items

- **Closed-form re-run — done, closes every clock-gauge item below** ([[TASK-0130]],
  2026-07-18). `time_averaged_ctqw`'s exact infinite-time limit
  (`propagators.time_averaged_ctqw_converged`) replaces the finite-`t_max` approximation
  for every headline number's "ctqw" side — there is no `t_max`/`t*`/`n_steps` clock
  parameter left for this quantity at all. This makes the next three items (TASK-0110/
  BCR_ABL1 short-`t_max` tension, the BCR_ABL1 spectral-gap reproducibility flag, and
  TASK-0117) **moot, not resolved-in-place**: the specific numerical questions they raised
  (which `t_max` to trust, which of two disagreeing gap measurements is right) no longer
  have an object to be about, since no `t_max`/gap is computed for this quantity anymore.
  Kept below for the historical record, each marked moot rather than deleted, per this
  document's own no-silent-overwrite convention. [[TASK-0112]]'s bootstrap CI is now wired
  directly into this document's own headline numbers (see the TASK-0130 table above) — not
  a separate open item anymore for *this specific* recompute, though TASK-0112's own
  broader rollout to every other headline AUC in the repo remains its own task.
- **Combined seed+clock re-run — done** ([[TASK-0129]], 2026-07-17/18, closes the item
  that used to be here). [[TASK-0118]] and [[TASK-0119]] landed concurrently and were
  not combined; TASK-0129 re-ran floor/ceiling/actual and the 96-cell operator sweep
  under both fixes together. Headline: CARDIAC_MYOSIN's seed-only-fix positive did not
  survive; no mandatory target's actual result clears its own floor under the fully
  corrected convention. See the SUPERSEDED notice and per-target sections above.
- **TASK-0110/BCR_ABL1 short-`t_max` tension — MOOT as of [[TASK-0130]]** (2026-07-18: no
  `t_max` is computed for `time_averaged_ctqw` anymore; kept below for the record).
  Originally flagged, not resolved ([[TASK-0129]]):
  TASK-0110's own AUC-optimal `t_max=2.39` for BCR_ABL1 scores *better* (0.5829,
  `coherent=True`) than either estimate of `H_new`'s numerically-adequate convergence
  time (23.8 or 123.1, themselves disagreeing — see below) scores under the combined
  fix (0.5305, `coherent=False`) — propagating longer appears to hurt discrimination
  here, not help it. Would need a real `coherent=False` re-run of TASK-0110's own
  Optuna search to properly reconcile; out of this task's own scope ("does not design a
  third fix").
- **`H_new`'s BCR_ABL1 spectral gap — reproducibility question — MOOT as of
  [[TASK-0130]]** (2026-07-18: no gap-derived `t*` is computed for `time_averaged_ctqw`
  anymore; kept below for the record). Originally flagged, not resolved ([[TASK-0129]]):
  freshly computed twice in the current environment (`gap=0.0374`,
  `t*=123.1`), consistent with itself but disagreeing with [[TASK-0119]]'s own recorded
  value for the identical computation (`gap=0.1933`, `t*=23.8`) on byte-identical input
  data. Plausibly explained by a genuine near-continuum in this operator/target's low
  spectrum (8 eigenvalues packed within a 0.14 span) making "the gap" numerically
  fragile — not chased further, a numerical-stability question orthogonal to this task's
  own seed+clock scope. **[[TASK-0135]] (2026-07-19) directly tested "numerically
  fragile to environment" and refuted it** (14+ significant figures reproducible across
  thread counts) — see the corrected entry above and [[INV-0008]] for the real,
  most-likely explanation (a stale cached object across a code-version gap, not
  environmental nondeterminism).
- **TASK-0112 — wired in directly as of [[TASK-0130]]** (2026-07-18): every number in
  this document's own current (TASK-0130) table above carries a 95% block-bootstrap CI,
  computed in the same recompute pass, not a separate afterthought. Originally open: no
  confidence interval on any number in this document — `metrics.block_bootstrap_ci`
  exists and is used by `select.py`'s LOPO path but was not wired into any headline AUC
  this document cites.
- **TASK-0116 — Done** (`_PARAM_RANGES`/`sample_params` corrected to the constrained
  simplex, already the current shipped code — this bullet was itself stale, corrected
  here). Coverage sparsity (60 blind draws over an ~8-dimensional space) remains a real
  property of the search, but [[TASK-0131]] (below) now directly answers the question this
  sparsity originally raised — not "is 60 samples enough coverage," but "is the reported
  maximum distinguishable from what 60 samples of pure noise would produce" — per target,
  with a real null distribution rather than a qualitative flag. See TASK-0131's own
  section above: real for KRAS_G12C (p=0.045 uncorrected), not for CARDIAC_MYOSIN (p=0.45).
  A denser/space-filling search remains a legitimate follow-up if a *tighter* ceiling
  estimate is wanted (this task's own Out Of Scope explicitly did not redesign the search),
  but the "is the current number meaningful at all" question is now answered, not open.
- **TASK-0117 — MOOT as of [[TASK-0130]]** (2026-07-18: no `n_steps`/`t_max` is derived
  for `time_averaged_ctqw` anymore, so there is no clock-derived numerical parameter left
  to wrap in a CI for this quantity; kept below for the record). Originally open: the
  ceiling search's own numerical parameters (`n_steps` derived from `H_new`'s own `n*`,
  per the TASK-0129 recompute) still lacked a formal confidence-interval wrapper — the
  search-*coverage* question (TASK-0116, above) is distinct — see that bullet's own
  2026-07-19 update (TASK-0131) — unaffected by TASK-0130.
- **TASK-0124** (open): CARDIAC_MYOSIN's apo structure (5TBY, 20 Å docked homology model)
  still carries its own unresolved data-quality caveat — now the *only* remaining
  question for this target, since TASK-0129 already found it has no headroom to defend
  even setting the structure question aside.
- **Q-0003 — fully closed as of [[TASK-0130]]** (`.ai/memory/questions/architect-planner/
  answered/Q-0003-...md`): the floor/ceiling/headroom framing has now been exercised
  under three successive gauge corrections (seed, clock, and full clock-removal) and held
  up each time — it correctly surfaces what the data says at each stage, including this
  stage's own new finding (KRAS_G12C's point estimate now clears its floor, but the CI
  says this isn't decided yet) without needing further redesign. TASK-0116 (ceiling
  search coverage) remains its own separate, still-open question — never part of what
  Q-0003 asked.
- **`H10`'s own `t*` not separately computed — MOOT as of [[TASK-0130]]** (2026-07-18: no
  `t*` is computed for either operator anymore under the closed form; kept below for the
  record). Originally flagged ([[TASK-0129]]): the competence-map axis applied `H_new`'s
  own default-config `t*` uniformly to both benchmark candidates and every ceiling trial
  — a materially different `H10` `t*` was not ruled out and not checked.
- **TASK-0081**: generalization-set rows, not yet run (and not re-run under TASK-0118's
  convention — out of scope, flagged as a gap for whoever picks up TASK-0081/0127 next).
- **TASK-0083** (result artifact contract, not yet started): this document is a plain
  markdown synthesis, not yet expressed in whatever versioned artifact shape TASK-0083
  eventually defines (GO/NO/UNSTABLE + knob-spread, per `EXECUTION_PLAN.md`'s own
  description of that task) — reconcile once TASK-0083 lands, per this task's own Open
  Question ("what document/artifact format... decide when TASK-0083 is scoped").
