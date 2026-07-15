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

- Outcome: re-run the ceiling search on KRAS_G12C (TASK-0046's own real
  cross-check target) with either (a) a space-filling design (Sobol or
  Latin hypercube) at a matched or larger trial budget, or (b) a real
  optimizer (Optuna/TPE, reusing TASK-0110's new dependency if it lands
  first), and report whether the near-chance ceiling finding is confirmed
  or overturned.
- In Scope:
  - implement or wire in one alternative search strategy over
    `ceiling.py`'s existing `_PARAM_RANGES`/`_N_LOW_CHOICES` — reuse
    `consistency_score` as the objective unchanged, this task only
    changes how the parameter space is sampled, not what's being scored.
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

- [ ] Choose search strategy (Sobol/LHS vs. Optuna) and justify the
      choice briefly in Done.
- [ ] Run on KRAS_G12C, matched or larger budget than TASK-0046's 60.
- [ ] Report new best result vs. TASK-0046's 0.5250; state agreement or
      disagreement explicitly.
- [ ] If disagreement found, flag `TASK-0082` (competence map) since it
      is instructed to read TASK-0046's ceiling number directly.

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
