# TASK-0112 Wire block-bootstrap CI into headline AUC reporting

## Context

- ID: TASK-0112
- Title: `metrics.block_bootstrap_ci` exists and is used by `select.py`'s
  LOPO path, but is never called anywhere in the chain that produces
  `RESULTS.md`'s headline numbers — every floor-vs-score comparison in
  the pipeline is currently a bare point estimate.
- Status: TODO
- Owner: Implementer
- Source: `REVIEW-2026-07-15-execution-plan-gap-audit.md`, finding #1.
- Crit Ref: confirmed by direct code inspection before filing —
  `grep -rn block_bootstrap_ci __WORK_IN_PROGRESS__/src` shows only
  `metrics.py` (definition) and `select.py` (LOPO); `grep -inE
  "ci|bootstrap|±|confidence" __WORK_IN_PROGRESS__/RESULTS.md` returns
  zero hits. Phase 1B's own headline-overturning finding (KRAS_G12C
  0.779 vs. proximity floor 0.798, TASK-0094) is a margin of 0.019 on
  N≈20-30 pocket residues — currently reported as a decided
  `BEATS_CHANCE_NOT_FLOOR` verdict with no CI attached to either side.

## Intent Contract

- Outcome: every AUC that currently drives a `classify_failure`
  category or appears as a headline number in `RESULTS.md` is reported
  with a `block_bootstrap_ci` interval alongside it, and any
  floor-vs-score comparison states whether the two intervals overlap,
  not just which point estimate is larger.
- In Scope:
  - wire `block_bootstrap_ci` into `diagnostics.classify_failure`'s
    score-vs-floor comparison (the exact comparison TASK-0094/TASK-0058
    built) — report the CI on both the scored operator and the floor
    baseline, not just the scored operator.
  - re-run the comparisons already recorded as settled in `RESULTS.md`
    (KRAS_G12C vs. its euclid floor; BCR_ABL1 CTQW vs. floor; BCR_ABL1
    GSR vs. floor) with CIs attached; report explicitly whether any
    verdict changes from "clears/doesn't clear" to "statistically
    indistinguishable from the floor."
  - add the CI to `report.verdict_template`'s rendered output wherever
    an AUC is shown.
  - do not change `classify_failure`'s category *names* or ordering —
    this task adds an uncertainty annotation to existing verdicts, it
    is not a re-design of the taxonomy.
- Out Of Scope:
  - re-running TASK-0094/TASK-0101's full sweeps from scratch — reuse
    their already-computed scores/labels where the CI can be computed
    from cached data; only re-run live if the cached per-residue score
    arrays aren't available.
  - changing `block_bootstrap_ci`'s own implementation (block size,
    resampling scheme) unless it's found to be broken — this task wires
    an existing, tested function in, it does not redesign it.
- Constraints And Invariants: `block_bootstrap_ci`'s docstring already
  states it "preserves local spatial correlation in the residue
  ordering" — use it as documented, do not swap in a naive i.i.d.
  bootstrap that would understate the true variance on spatially
  correlated pocket labels.
- Planned Validation: a synthetic case where the true floor/score gap
  is known to be within noise (CI must overlap) and one where it's known
  to be decisive (CI must not overlap), proving the wiring is sensitive
  in both directions — not just plumbed through.

## In Progress

None

## TODO

- [ ] Wire `block_bootstrap_ci` into `classify_failure`'s floor
      comparison (both operator and floor scores).
- [ ] Add CI rendering to `report.verdict_template`.
- [ ] Re-run KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN's already-recorded
      floor comparisons with CIs; report overlap/non-overlap explicitly
      for each.
- [ ] Synthetic sensitivity test (known-overlap + known-decisive cases).
- [ ] Update `RESULTS.md` additively (this doc's own no-silent-overwrite
      convention) with whichever verdicts change once CIs are attached.

## Dependency

- `metrics.block_bootstrap_ci` (exists, TASK done previously — no code
  blocker).
- Should land before Phase 5.2 (TASK-0082, competence map synthesis) —
  a floor/ceiling/headroom table built on point estimates without CIs
  would inherit this same gap at the level meant to be the submission's
  central claim.

## Open Questions

- None — scope is fully specified; which cached score arrays are
  available vs. need a live re-run is this task's own discovery, not
  pre-decided here.

## Done

(not yet)
