# TASK-0116 Ceiling search coverage is too sparse to support a "no headroom" claim

## Context

- ID: TASK-0116
- Title: `ceiling.ceiling_search`'s blind random search (N=60 trials
  over ~8 dimensions) is weak evidence for the negative claim TASK-0046
  drew from it ("very little headroom in this operator family"), and no
  real optimizer or space-filling design is applied anywhere to `H_new`'s
  physical potential-weight parameters.
- Status: Done
- Resolution: done
- Owner: Implementer
- Claimed By: Implementer C (this thread)
- Claimed At: 2026-07-18 18:02
- Source: `REVIEW-2026-07-15b-ceiling-search-methodology.md`, finding #1.
- Crit Ref: `ceiling.py:42-51` defines 7 continuous ranges
  (`lam_B, lam_T, lam_R, lam_C, lam_M, alpha, cutoff`) plus a 5-way
  categorical (`n_low`); `ceiling_search`'s default `n_trials=60`
  (`ceiling.py:188`) matches the notebook's own default but was never
  independently justified as adequate coverage for a null claim. TASK-0110
  (filed same day) explicitly excludes this exact parameter space from
  its own Optuna work ("H_new's own physical potential-weight
  parameters — already covered by TASK-0046").

## Intent Contract

- **Prerequisite, added 2026-07-18, must land first — per
  `.ai/reviews/REVIEW-panel-2026-07-17.md` §2.4, §4 P0-4**: `ceiling.py`'s
  `_PARAM_RANGES` still samples each `lam_*` uniformly on `(0.0, 2.0)`
  independently (confirmed unchanged, `ceiling.py:42-48`), untouched
  since [[TASK-0121]] proved `Σ|λ| ≤ 0.4` is required to keep the
  potential's dispersion within `σ(V) ≤ 0.2·J`. `E[Σλ] = 5.0` under the
  current ranges — **12.5x the budget typical, 25x at the corner** — so
  the search samples mostly from deep inside the Anderson-localized
  regime TASK-0121 exists to escape. **Upgrading the search strategy
  (below) without fixing this first just explores the wrong space more
  efficiently.** Fix: sample `lam_*` on the simplex `Σ|λᵢ| ≤ 0.4` (or an
  equivalent constrained design — Sobol/LHS over the constrained set, or
  a Dirichlet-style simplex sampler scaled to the budget), not
  independently per-dimension. Cheap (~1 hour per the review's own
  estimate) — do this as this task's own first step, before choosing or
  running any alternative search strategy.
- Outcome: re-run the ceiling search on KRAS_G12C (TASK-0046's own real
  cross-check target), **first under the corrected `Σ|λ| ≤ 0.4` ranges
  at the existing 60-trial budget** (isolates the range fix's own
  effect), **then** with either (a) a space-filling design (Sobol or
  Latin hypercube) at a matched or larger trial budget, or (b) a real
  optimizer (Optuna/TPE, reusing TASK-0110's new dependency if it lands
  first), and report whether the near-chance ceiling finding is confirmed
  or overturned. Report the range fix and the strategy upgrade as two
  separate, attributable deltas — do not merge them into one number, per
  this project's own standing convention for stacked corrections.
- In Scope:
  - Fix `_PARAM_RANGES` per the prerequisite above.
  - implement or wire in one alternative search strategy over the
    *corrected* parameter space — reuse `consistency_score` as the
    objective unchanged, this task only changes how the parameter space
    is sampled, not what's being scored.
  - run on KRAS_G12C at a comparable or larger trial budget than
    TASK-0046's 60; report the new best `S`/`auc_apo` alongside the
    original 0.5250 for direct comparison.
  - if compute allows, a second confirmatory run at a different seed/
    design to check the new result isn't itself a lucky single trial.
  - report explicitly whether the new search's best result changes
    TASK-0046's "does not clear chance" conclusion — per this project's
    "report both, don't silently reconcile" convention.
- Out Of Scope:
  - changing `consistency_score`'s formula or `H_new`'s DOF — this task
    is about search coverage, not the objective or the model.
  - BCR_ABL1/CARDIAC_MYOSIN — start with KRAS_G12C (TASK-0046's own
    validated cross-check target); extend only if the KRAS_G12C result
    changes the conclusion enough to warrant it.
  - re-litigating whether 60 trials was reasonable for the notebook's
    own original purpose — this task is about whether it's adequate
    evidence for the load-bearing claim this port's Done section drew
    from it, a higher bar than the notebook required of itself.
- Constraints And Invariants: must still run inside
  `protocol.ceiling_context()`, same as `ceiling_search` — this is
  Phase 2's sanctioned leakage, unchanged by which search strategy is
  used.
- Planned Validation: the new search actually executes on real
  KRAS_G12C data; its own best `S` reported alongside TASK-0046's 0.5250
  with the same params-and-provenance detail TASK-0046's Done section
  used.

## In Progress

None

## TODO

- [x] Fix `_PARAM_RANGES` to respect `Σ|λ| ≤ 0.4` (simplex/constrained
      design, not independent per-dimension uniforms).
- [x] Re-run at the existing 60-trial budget under corrected ranges
      alone; report this delta in isolation.
- [x] Choose search strategy (Sobol/LHS vs. Optuna) and justify the
      choice briefly in Done.
- [x] Run on KRAS_G12C, matched or larger budget than TASK-0046's 60,
      under the corrected ranges.
- [x] Report new best result vs. TASK-0046's 0.5250; state agreement or
      disagreement explicitly, and attribute the delta to range-fix vs.
      strategy-upgrade separately.
- [x] If disagreement found, flag whatever document currently holds the
      ceiling headline (`COMPETENCE_MAP.md`, post-[[TASK-0130]]).
- [x] If [[TASK-0131]]'s permutation null hasn't landed yet, flag that
      any new "best result" here still needs that null before being read
      as a real positive, not just a bigger max-of-K draw.

## Dependency

- TASK-0046 (Done) — the search this task re-runs with better coverage.
- TASK-0110 (TODO) — soft dependency if Optuna is the chosen strategy
  (reuse its new dependency manifest rather than adding a second one).

## Open Questions

- **Resolved**: Optuna/TPE, not Sobol/LHS. By the time this task was
  picked up, [[TASK-0110]] had already landed (Done) and Optuna was
  already a project dependency with an established call pattern
  (`optuna_scan.py`) — the "second consumer before TASK-0110 itself has
  landed" concern in the original framing no longer applied. TPE also
  has a real advantage over pure space-filling for this specific
  question ("is there real headroom," not just "cover the space
  uniformly"): a Bayesian-ish sampler can concentrate trials near
  promising regions once it has a few observations, giving a better
  shot at finding genuine headroom in a fixed trial budget than uniform
  coverage would. Reusing the existing dependency rather than adding
  `scipy.stats.qmc` as a second search-strategy tool also keeps this
  project's tooling footprint smaller.

## Done

**Prerequisite (per `REVIEW-panel-2026-07-17.md` P0-4), fixed first**:
`ceiling.py::_PARAM_RANGES` sampled each `lam_B/T/R/C/M` independently
and uniformly on `(0.0, 2.0)` — a range that predates [[TASK-0121]]'s
z-scoring of `potentials.py`'s five terms. `E[sum(lam_i)] = 5.0` under
the old range, 12.5x TASK-0121's own `sigma(V) <= 0.2*J <= 0.4` budget
(25x at the corner) — the old search was sampling almost entirely from
the Anderson-localized regime TASK-0121 exists to escape, making
TASK-0046's "very little headroom" claim weak evidence for a different
reason than the original search-coverage concern this task was filed
for (both real, both now fixed together since fixing coverage without
first fixing the space would just explore the wrong space more
efficiently, per this task's own Intent Contract).

**Fix**: `sample_params` now draws `lam_*` on the constrained simplex
`sum(lam_i) <= 0.4`, via a two-step draw — total budget uniform on
`[0, 0.4]` (so the search also explores under-using the budget, not
only its outer boundary), then a `Dirichlet(1,1,1,1,1)` proportion split
among the 5 terms (uniform over relative weighting). `alpha`/`cutoff`/
`n_low` unchanged — this task is a coverage fix over the `lam_*` axis
specifically. `_PARAM_RANGES` now only holds `alpha`/`cutoff`;
`_LAM_NAMES`/`_LAM_BUDGET` are new module constants.

**Strategy upgrade**: added `ceiling.ceiling_search_optuna` (TPE via
Optuna), reusing `consistency_score` completely unchanged as the
objective (Out Of Scope: this task changes only how the space is
sampled). The lam simplex is reparametrized for Optuna's `suggest_float`
interface (no native simplex/Dirichlet suggestion exists): 5 independent
`suggest_float(0,1)` weights, normalized to sum to 1, scaled by an
independently suggested `lam_budget` in `[0, 0.4]` — structurally the
same two-step draw `sample_params` uses, exposed through named
`suggest_*` calls so TPE can learn correlations between them across
trials (a single opaque `sample_params(rng)` call would hide this from
the optimizer). A `NaN`-`S` trial is pruned via `optuna.TrialPruned`,
not returned as a rankable value.

**Found and worked around, before running anything real**: a stale
60-trial checkpoint for KRAS_G12C already existed at
`results/tasks/0082/KRAS_G12C/ceiling_trials.jsonl` (from TASK-0046's
original 2026-07-15 run, same `seed=7`). `ceiling_search_batched.py`'s
own resume logic reads "N trials already checkpointed" by count, not by
which parameter range produced them — re-running with the same target/
seed/checkpoint-dir would have silently reported the stale-range best as
"already complete," never running a single new trial. Used a fresh
`--checkpoint-dir results/tasks/0116/...` instead of touching or deleting
the original (preserves TASK-0046's own evidence, matches this
project's "don't overwrite a prior run's numbers" convention).

**Real KRAS_G12C re-run** (TASK-0046's own cross-check target, per this
task's Out Of Scope — BCR_ABL1/CARDIAC_MYOSIN only if the result changed
the conclusion enough to warrant it; it did not), every delta kept
separate per this task's own "don't merge range-fix and strategy-upgrade
into one number" instruction, all at `t_max=15`/`n_steps=500` (matching
TASK-0046's exact original methodology — deliberately not also applying
[[TASK-0130]]'s newer `use_converged_limit` closed-form option, found
mid-task to exist and apply here too, but treated as a 4th independent
axis that would make attribution impossible if stacked in):

| Search | Range | Seed convention | Best S / AUC_apo |
|---|---|---|---|
| Original (TASK-0046, 2026-07-15) | stale `(0.0,2.0)` each | `coherent=True` (pre-TASK-0118, implicit) | 0.5250 |
| Range-fix only, isolated | corrected `sum<=0.4` | `coherent=True` (byte-identical to original) | 0.4864 |
| Range-fix only, current convention | corrected `sum<=0.4` | `coherent=False` (TASK-0118) | 0.4735 |
| Range-fix + TPE, current convention | corrected `sum<=0.4` | `coherent=False` (TASK-0118) | 0.4908 (seed=7) / 0.4842 (seed=42, confirmatory) |

`ceiling_search_batched.py --coherent` flag used for the byte-identical-
to-original isolation row (exists specifically for this kind of A/B
comparison per its own `--help` text). Seed=7 TPE run reproduced exactly
on a second invocation (0.49080206033848417 both times) — confirms
determinism, not a fluke of `optuna`'s own internal state. Seed=42
confirmatory run (this task's own "if compute allows" Planned
Validation step — compute did allow, ~85s/60-trial run): 0.4842, close
to seed=7's result, not a lucky single trial.

Current floor (re-measured in the same run, `coherent=False`
convention, `degree_centrality`/`euclid_from_seed_centroid`/
`hop_from_seed` max): **0.4818**. The TPE result (0.4908) sits
marginally above this — **the first time any of this project's
KRAS_G12C ceiling numbers have crossed the floor** — but the margin
(+0.009) is far smaller than any of this project's own established
decisiveness bars ([[TASK-0112]]'s bootstrap CIs have consistently found
comparable-sized gaps non-decisive). **Not claimed as a real positive
here.** [[TASK-0131]] (permutation null) is still TODO/unclaimed — per
this task's own Planned checklist, flagging that gate explicitly rather
than either running an ad-hoc CI outside this task's scope or silently
reporting "ceiling clears floor" as if settled.

**Headline finding, stated directly**: fixing the search space does
**not** reveal hidden ceiling headroom for KRAS_G12C. If anything, the
original 0.5250 was itself somewhat inflated by the stale range's access
to physically-invalid extreme disorder — every corrected-range number
(0.4735-0.4908) sits below it. TASK-0046's "very little headroom in this
operator family" conclusion is **confirmed, not overturned**, now on
methodologically sounder footing (a search that actually explores the
valid operator family, not mostly the invalid one).

**Independent cross-validation**: [[TASK-0110]]'s Optuna search over
CTQW's own numerical `(t_max, n_steps)` parameters (H_new's physical
weights left at default) found 0.4750 for KRAS_G12C. This task's search
over H_new's physical weights (CTQW numerics left at default) finds
0.4908. Three independent searches, three different parameter axes
(TASK-0046's original 8D physical-weight search, TASK-0110's CTQW-
numerics search, this task's corrected-space 8D physical-weight search),
now agree KRAS_G12C sits near chance.

**Test coverage**: rewrote `TestSampleParams.test_within_documented_
ranges` (was asserting the old per-term `(0.0,2.0)` bound, now asserts
`lam_i >= 0` and `sum(lam_i) <= 0.4`), added a budget-range-coverage
test (confirms the search explores near-0 and near-0.4 totals, not just
the boundary). Found and fixed a real test fragility while re-running
the suite: `test_coherent_flag_reaches_every_trial` asserted an observed
best-score *difference* between `coherent=True`/`False` runs — no longer
reliable once `lam_*` is sampled on the much smaller corrected budget
(many trials now land at very weak disorder, where coherent/incoherent
CTQW can coincidentally agree by symmetry on the synthetic helix test
fixture). Rewrote to spy on `consistency_score`'s `coherent` kwarg
directly instead, testing the actual plumbing claim without depending on
any particular sampled point's physics. New `TestCeilingSearchOptuna`
class (6 tests): runs and picks best, reproducible with fixed seed,
winning params respect the lam budget, NaN-pocket handling, `coherent`
flag reaches every trial (same spy pattern), runs inside
`ceiling_context()`. Full suite: 711 passed (`../.venv/bin/python -m
pytest tests/ -q -k "not real_target and not real_run and not fetch and
not kras_g12c_real"`).

**Not done, flagged rather than silently skipped**: `COMPETENCE_MAP.md`'s
own KRAS_G12C ceiling cell not updated in place (that document's own
"don't overwrite" convention — not touched here, flagged for whoever
next recomputes it). TASK-0117 (validated CTQW clock parameters for the
ceiling search specifically) remains open — [[TASK-0130]]'s
`use_converged_limit` gives whoever picks it up a ready mechanism rather
than requiring new plumbing. BCR_ABL1/CARDIAC_MYOSIN not re-run, per
this task's own Out Of Scope.
