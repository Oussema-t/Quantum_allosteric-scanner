# TASK-0112 Wire block-bootstrap CI into headline AUC reporting

## Context

- ID: TASK-0112
- Title: `metrics.block_bootstrap_ci` exists and is used by `select.py`'s
  LOPO path, but is never called anywhere in the chain that produces
  `RESULTS.md`'s headline numbers — every floor-vs-score comparison in
  the pipeline is currently a bare point estimate.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-17 12:50
- Source: `REVIEW-2026-07-15-execution-plan-gap-audit.md`, finding #1.
- Correction to this task's own filing (checked directly, not assumed):
  the Context claim above ("used by `select.py`'s LOPO path") is
  inaccurate — `grep -rn block_bootstrap_ci src/` shows it referenced
  only in a `select.py` docstring comment (about a shared default `rng`
  seed convention, a different function), never actually imported or
  called there. Before this task, `block_bootstrap_ci` was called
  nowhere outside its own definition and tests. Does not change this
  task's real scope (still nowhere in the headline-reporting chain).
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

**(1) `diagnostics.classify_failure(return_ci=True)`** — new `FailureClassification`
dataclass (`category`, `score_ci`, `floor_ci`, `ci_overlap`). `return_ci=False`
(default, every pre-existing call site — `protocol.py`, `analysis.py`,
all of `test_diagnostics.py`/`test_seam_0005_baseline_floor.py`) is
byte-identical to pre-TASK-0112 behavior, checked directly (full suite
green before touching anything else) — this task's own Constraint against
changing category names/ordering is satisfied by construction: the
original decision logic is untouched, only wrapped by a small `_result()`
helper that optionally attaches CI. `score_ci` uses `metrics.
block_bootstrap_ci` on the real `scores`/`labels`; `floor_ci` uses it on
the single *winning* floor candidate (`max(floor_aucs)`, the same one
`BEATS_CHANCE_NOT_FLOOR`'s own point-estimate check already selects) —
not an average across candidates. `OPERATOR_DEGENERATE`/`LABEL_SUSPECT`/
`INSUFFICIENT_RESOLUTION` always return `score_ci=None` (no well-formed
AUC exists yet to bootstrap). `ci_overlap` is reported *alongside*
`category`, never used to change it, per this task's Constraint.

**(2) Wired into `protocol.run_frozen_verdict`**: `_diagnosis` stays a
bare `str` (every existing reader untouched); three new, additive keys
(`_diagnosis_score_ci`, `_diagnosis_floor_ci`, `_diagnosis_ci_overlap`) on
the assembled results dict. Confirmed `stamp_provenance`/JSON
serialization (`verdict.json`) both pass the new tuple-valued keys
through unchanged (`test_run_challenge.py` green, no special-casing
needed — Python tuples serialize as JSON arrays natively).

**(3) `report.verdict_template`**: found while implementing that
`_diagnosis` itself was never rendered in this template at all before
this task (checked directly, not assumed) — added a new block rendering
`_diagnosis` + both CIs + an explicit overlap statement ("statistically
indistinguishable from the floor" / "statistically distinguishable"),
missing-key-renders-N/A per this module's own existing convention, not a
crash.

**(4) Real re-run, all three comparisons this task names**
(`scripts/bootstrap_ci_headline_rerun.py`, live fetch — no cached raw
per-residue score array existed for any of these; `verdict.json`/
`reproduction.json` only ever stored the scalar AUC, per this task's own
Out Of Scope allowance for exactly this case). Same `T_MAX=15.0` as the
originally-recorded numbers (deliberately *not* combined with TASK-0119's
per-operator clock fix — conflating two corrections in one re-run would
make it impossible to attribute which change moved which number):

| Target | Comparison | Score AUC [CI] | Floor AUC [CI] | Overlap? |
|---|---|---|---|---|
| KRAS_G12C | `H_new` ctqw vs `euclid_from_seed_centroid` | 0.779 [0.594, 0.932] | 0.798 [0.637, 0.936] | **YES** |
| BCR_ABL1 | `H_new` ctqw vs `hop_from_seed` | 0.525 [0.325, 0.684] | 0.565 [0.425, 0.697] | **YES** |
| BCR_ABL1 | `H_new` ground_state vs `hop_from_seed` | 0.731 [0.556, 0.866] | 0.565 [0.425, 0.697] | **YES** |

**Headline finding: all three named comparisons overlap** — including
BCR_ABL1's `ground_state_relaxation` result, previously described in
`RESULTS.md` as clearing its floor "decisively" (the widest margin
measured for any mandatory target). No `category` changed (per this
task's own Constraint — `BEATS_CHANCE_NOT_FLOOR`/`NO_SIGNAL_IN_APO`/
`NO_FAILURE_DETECTED` are unchanged from the pre-CI point estimates), but
none of the three verdicts are statistically decisive at 95% confidence
on these targets' real positive counts. Reported as two separate facts,
not merged: the *point-estimate* category still stands as the deterministic
taxonomy verdict; the *uncertainty* annotation says none of them would
survive a referee asking "how sure are you." `RESULTS.md` corrected
additively at both sites (KRAS_G12C's 0.779-vs-0.798 paragraph, BCR_ABL1's
"clears... decisively" paragraph) — original text preserved, per this
doc's own no-silent-overwrite convention.

**(5) Tests**: `tests/test_diagnostics.py::TestClassifyFailureBootstrapCI`
(7 new) — default-path backward-compatibility, technical-failure
categories never get a CI, the two Planned-Validation sensitivity cases
(decisive separation → CI must not overlap; noise-level gap → CI must
overlap, both passing, proving the wiring is sensitive in both
directions not just plumbed through), winning-floor-candidate selection,
and `ci_rng` reproducibility. Full local run: `test_diagnostics.py` (38),
`test_protocol.py`, `test_report.py`, `test_run_challenge.py`,
`test_ground_state_relaxation_guard.py` (137 total) — all green.

**Not attempted, explicitly out of this task's own scope**: wiring CI
into `analysis.operator_sweep`'s 96-cell Tier-1 sweep — not named in this
task's own In Scope list (only `classify_failure`, the three named
`RESULTS.md` re-runs, and `verdict_template` are), and would multiply a
96-cell sweep by ~2000 extra bootstrap-AUC computations per cell for a
descriptive-only harness TASK-0100's own tiering already excludes from
frozen/submission scoring; re-running TASK-0094/TASK-0101's full sweeps
from scratch (this task's own Out Of Scope); changing
`block_bootstrap_ci`'s own implementation (also explicitly out of scope
— used exactly as documented).
