# TASK-0116 Ceiling search coverage is too sparse to support a "no headroom" claim

## Context

- ID: TASK-0116
- Title: `ceiling.ceiling_search`'s blind random search (N=60 trials
  over ~8 dimensions) is weak evidence for the negative claim TASK-0046
  drew from it ("very little headroom in this operator family"), and no
  real optimizer or space-filling design is applied anywhere to `H_new`'s
  physical potential-weight parameters.
- Status: TODO
- Owner: Implementer
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

- [ ] Fix `_PARAM_RANGES` to respect `Σ|λ| ≤ 0.4` (simplex/constrained
      design, not independent per-dimension uniforms).
- [ ] Re-run at the existing 60-trial budget under corrected ranges
      alone; report this delta in isolation.
- [ ] Choose search strategy (Sobol/LHS vs. Optuna) and justify the
      choice briefly in Done.
- [ ] Run on KRAS_G12C, matched or larger budget than TASK-0046's 60,
      under the corrected ranges.
- [ ] Report new best result vs. TASK-0046's 0.5250; state agreement or
      disagreement explicitly, and attribute the delta to range-fix vs.
      strategy-upgrade separately.
- [ ] If disagreement found, flag whatever document currently holds the
      ceiling headline (`COMPETENCE_MAP.md`, post-[[TASK-0130]]).
- [ ] If [[TASK-0131]]'s permutation null hasn't landed yet, flag that
      any new "best result" here still needs that null before being read
      as a real positive, not just a bigger max-of-K draw.

## Dependency

- TASK-0046 (Done) — the search this task re-runs with better coverage.
- TASK-0110 (TODO) — soft dependency if Optuna is the chosen strategy
  (reuse its new dependency manifest rather than adding a second one).

## Open Questions

- Sobol/LHS (no new dependency, `scipy.stats.qmc` already available via
  the existing scipy dependency) vs. Optuna (matches TASK-0110's choice,
  but adds a second consumer of that new dependency before TASK-0110
  itself has landed) — Implementer's call, state the choice and why.

## Done

(not yet)
