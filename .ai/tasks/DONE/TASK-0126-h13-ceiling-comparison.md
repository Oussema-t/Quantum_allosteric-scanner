# TASK-0126 Run H13 (or its N×N projection) through the ceiling search

## Context

- ID: TASK-0126
- Title: `.claude/hypotheses/ceiling.md`'s own "minimum set" names H13
  (alongside H8 and degree centrality) as a required ceiling-search
  candidate. [[TASK-0046]]'s real ceiling search only ever searched
  `H_new`'s own 8-parameter DOF — H13 was never included. Run it (or its
  N×N projection, per HYP-P5 in `hypotheses/physics.md`) through the
  same ceiling-search methodology.
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: independently flagged twice — by this Architect/Planner
  thread on 2026-07-16 (before this review landed) and confirmed by
  `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §5 P2-9 ("your own docs
  call this required").
- Priority: **P2 — weeks 4-6.**

## Intent Contract

- Outcome: H13 (the full 3N×3N ANM Hessian, "the physically richest
  operator" per `HAMILTONIANS.md`) is run through [[TASK-0046]]'s ceiling
  search methodology — either via a documented scalar N×N projection
  (fast, may discard orientational information) or by extending the
  propagators to accept 3N×3N and post-summing to per-residue occupation
  (preserves orientational coupling) — per HYP-P5's own two options.
  Compared against `H_new`'s already-established ceiling on all 3
  mandatory targets.
- Why this matters: `ceiling.md` calls this comparison "required for
  scientific rigor" — without it, choosing `H_new` over H13 remains an
  untested assumption, not a result, regardless of how the seed/clock/
  potential gauge fixes ([[TASK-0118]]/[[TASK-0119]]/[[TASK-0121]])
  resolve `H_new`'s own numbers.
- In Scope:
  - Implement whichever H13 projection option is chosen (Option A:
    scalar trace-of-3x3-blocks projection; Option B: 3N×3N propagator
    extension) — state the choice and why, per HYP-P5's own guidance
    (if H13 beats H_new, Option B — the orientation-preserving one — is
    the defensible choice going forward; if not, Option A's cheaper
    approximation is sufficient and should be documented as a confirmed
    finding, not just an assumption).
  - Run through the same ceiling-search methodology as [[TASK-0046]]/
    [[TASK-0082]] (same DOF-search discipline, same `ceiling_context()`
    gating), on all 3 mandatory targets.
  - Use whatever seed/clock convention [[TASK-0118]]/[[TASK-0119]] have
    settled by the time this task runs — do not reintroduce the seed-
    cardinality confound by seeding H13 differently from `H_new`.
- Out Of Scope:
  - Reselecting the submission operator based on this result alone —
    Tier-2 gated per [[TASK-0100]], same as every other operator-family
    result in this register.
- Constraints And Invariants: report H13's ceiling number with the same
  caveats [[TASK-0116]]/[[TASK-0117]] already attached to `H_new`'s
  (search density, parameter validity) — do not present H13's number as
  more settled than `H_new`'s own, which is still under active
  reconciliation.
- Planned Validation: direct AUC comparison, H13 vs. `H_new`, same
  targets, same seed/clock convention, same search methodology.

## In Progress

None

## TODO

- [x] Decide projection option (A: scalar N×N; B: 3N×3N propagator
      extension) — state why in Done.
- [x] Implement chosen option.
- [x] Run through TASK-0046/0082's ceiling-search methodology, all 3
      mandatory targets (where feasible — see Done).
- [x] Compare against `H_new`'s established ceiling; report the result
      whichever way it comes out.

## Dependency

- Should use whatever seed/clock convention [[TASK-0118]]/[[TASK-0119]]
  settle — soft ordering, not a hard block if this task starts first
  (in which case, flag which convention was used and re-check later).
- [[TASK-0046]]/[[TASK-0082]] (Done) — reuses their methodology directly.

## Open Questions

- Option A vs. B (scalar projection vs. 3N×3N propagator extension) —
  not pre-decided; Implementer's call per HYP-P5's own guidance, state
  the choice and why in Done.

## Done

**Implemented both options — not a real choice, because Option A collapses to an
existing operator.** Checked, not assumed: `H_scalar[i,j] = trace(H13[3i:3i+3,
3j:3j+3])` was implemented and compared via `np.allclose` (max diff 1.8e-15) against
`H2_combinatorial_laplacian` on this repo's actual `H13_3N_anm_hessian` construction.
They are numerically identical, because every off-diagonal 3×3 block of `H13` is
`-outer(r, r)` for a *unit* bond vector `r`, and `trace(outer(r, r)) = |r|² = 1`
regardless of direction — the literal Option A formula discards *all* orientational
information (not "some," as HYP-P5/IMP-H7's own text hedged), reducing to an operator
already in the 96-cell sweep. Running a "new" Option A function would have silently
duplicated `H2`'s own existing ceiling number. Instead:

- **Ran `H2`** (= Option A, by the proof above) through a real cutoff-only ceiling
  search, for completeness/traceability rather than reusing the 96-cell sweep's single
  default-cutoff value.
- **Ran `H14_anm_pinv_trace`** (pre-existing, TASK-0096) alongside it — the codebase's
  own actual non-trivial scalar reduction of H13 (pseudo-inverse trace of the 3×3
  blocks, the standard ANM cross-correlation quantity, Bahar/Atilgan/Erman 1997) — a
  far more meaningful "Option A in spirit" than the degenerate literal formula.
- **Implemented Option B properly**: `propagators.py` gained `residue_source_to_3n`,
  `reduce_3n_occupation`, `ctqw_3n_native`, `time_averaged_ctqw_3n_native`,
  `time_averaged_ctqw_converged_3n_native` — pure wrapper functions around the
  existing, *unmodified* `ctqw`/`time_averaged_ctqw`/`time_averaged_ctqw_converged`
  (all three are already dimension-agnostic; no core propagator refactor was needed,
  contrary to what HYP-P5/IMP-H7's own text anticipated). 3 spatial DOF per seed
  residue are excited with equal weight; occupation is reduced back to per-residue by
  summing each residue's 3 components. 13 new tests in `test_propagators.py`, all pass
  (35/35 in the file).
- **New script**: `scripts/h13_ceiling_comparison.py`, with `cutoff_only_ceiling_search`
  — `ceiling.ceiling_search`'s own discipline (`ceiling_context()` gating, real random
  search, per-trial exception handling) scaled down to a 1-dimensional `cutoff` search,
  since H2/H14/H13-native all take only `(coords, cutoff=...)`, unlike `H_new`'s
  8-dimensional space.

**Mid-task convention change, real and worth recording, not glossed over**: this
script was originally written against the TASK-0129 combined seed+clock convention
(full active-site array, `coherent=False`, per-operator `t*`/`n*` from
`min_adequate_t_max`/`min_adequate_n_steps`). While running it, **TASK-0130 landed
concurrently** and replaced `time_averaged_ctqw`'s finite-`t_max` numerical
time-average with `time_averaged_ctqw_converged`'s exact infinite-time closed form
project-wide. Two real things were found on the old path before the switch, kept here
for the record:

- **A rigid-body-nullspace bug in `min_adequate_t_max`**: a first feasibility probe on
  KRAS_G12C's H13-native operator produced `t*=9.8e14`, `n*=3.15e15` — astronomically,
  physically meaningless. Root cause: `H13_3N_anm_hessian` has 6 exact rigid-body
  translation/rotation zero modes at the bottom of its spectrum (`w[0]`-`w[5]` all ≈0,
  lowest 10 eigenvalues measured as `[-2.2e-15, -1.8e-15, -6.6e-16, 1.9e-16, 4.6e-16,
  5.5e-16, 1.35e-2, ...]`); `min_adequate_t_max`'s `gap = w[1]-w[0]` assumes `w[0]` is
  the true ground state, and its `inf` safety net only catches an *exactly* zero gap,
  not two near-machine-precision-degenerate rigid-body modes. Documented as a permanent
  caveat in `min_adequate_t_max`'s own docstring
  (`__WORK_IN_PROGRESS__/src/allostery/propagators.py:598-613`), pointing at the
  `count(w < 1e-8*max(|w|,1))` skip-the-nullspace fix pattern (TASK-0005/TASK-0128's
  own established threshold) for any future caller who feeds it a similar operator —
  **not fixed inside the shared function itself** (out of scope, would touch several
  other tasks' dependency; `H2`/`H14`'s own single trivial Laplacian zero mode is
  unaffected, `w[1]` is already their true first gap by construction). This caveat
  remains true and useful independent of which convention this script itself now uses.
- **A real feasibility wall on the finite-`t_max` path**: H13-native's `O(n_steps ×
  n_seed)` incoherent-mixture time loop measured 43.6s/trial for KRAS_G12C (3N=507),
  and **1888s for a single BCR_ABL1 trial (3N=1353)** — a full 60-trial search would
  have taken ~31.5 hours; CARDIAC_MYOSIN (3N=2850) was not even attempted. This is why
  the script switched conventions rather than accepting an incomplete 3-target result.

**Switching to `time_averaged_ctqw_converged` (no `t_max`/`n_steps`, a one-shot
spectral sum) removed the time-stepping loop entirely and made the full 3-target,
3-operator search tractable for the first time** — measured ~400x speedup on
KRAS_G12C's H13-native (0.25s/trial vs. the old 43.6s/trial). `time_averaged_ctqw_
converged`'s own degenerate-eigenvalue grouping (TASK-0130) also transparently absorbs
H13's rigid-body nullspace — no separate skip-the-nullspace step was needed on this
path at all (see `time_averaged_ctqw_converged_3n_native`'s own docstring and
`TestCtqw3nNative::test_converged_variant_absorbs_rigid_body_nullspace_without_error`).
CARDIAC_MYOSIN's H13-native still took ~38s/trial (2310s for 60 trials, the 2850×2850
eigh is real work) but that is a session-scale cost, not an infeasible one.

### Results (vs. `H_new`'s TASK-0130 closed-form ceiling)

| Target | `H_new` ceiling | H2 (=Option A) | H14 (pinv-trace) | H13-native (Option B) |
|---|---|---|---|---|
| KRAS_G12C | 0.6288 | 0.5390 @ cutoff=9.56 | 0.5732 @ cutoff=7.60 | 0.5026 @ cutoff=11.54 |
| BCR_ABL1 | 0.6671 | 0.6444 @ cutoff=11.54 | **0.7174 @ cutoff=6.29 (+0.0503)** | 0.6466 @ cutoff=12.53 (−0.0205) |
| CARDIAC_MYOSIN | 0.8297 | 0.8054 @ cutoff=6.47 | 0.7703 @ cutoff=6.73 | **0.8513 @ cutoff=6.03 (+0.0216)** |

All 60-trial `cutoff_only_ceiling_search` runs, `coherent=False`, TASK-0118/INV-0006's
full active-site-array seed convention, `time_averaged_ctqw_converged`'s exact
infinite-time limit — the current canonical convention for every operator in this
table, `H_new` included.

**Per IMP-H7's own decision protocol** (implement A; if it doesn't beat `H_new`, still
implement and check B before concluding H13 isn't worth pursuing; only if B also
doesn't beat `H_new` is `H_new` confirmed as baseline): Option A (=H2) does not beat
`H_new` on any target — the protocol's own step 4 applies uniformly, so Option B was
run and checked on all 3. **The result is genuinely mixed, not a clean confirm-or-
reject**: Option B does not beat `H_new` on KRAS_G12C (worst of the three candidates
there) or BCR_ABL1 (close, −0.0205), but **does beat `H_new` on CARDIAC_MYOSIN**
(+0.0216) — the one target where H13's full 3N×3N orientational detail actually helped
over the scalar reductions. Per the protocol's own step 3 ("if H13-scalar beats
H_new → implement Option B; re-compare") and step 5 ("only if H13 Option B also does
not beat H_new → confirm H_new as baseline"), the honest reading is: **`H_new` is not
uniformly confirmed as the best available operator** — H13-native is a real, checked
candidate for CARDIAC_MYOSIN specifically, not confirmed as generally superior, and not
dismissed either. This is a target-dependent result, not a global verdict either way.

**`H14_anm_pinv_trace` beats `H_new`'s ceiling on BCR_ABL1** (+0.0503) but not on
KRAS_G12C or CARDIAC_MYOSIN under this convention — a narrower finding than an earlier
draft of this section found under the since-superseded TASK-0129 finite-`t_max`
convention (which had shown H14 beating `H_new` on all 3 targets; not reproduced under
the closed form, the clock-gauge removal changed which comparisons cross which
thresholds, same kind of effect TASK-0129/TASK-0130's own headline findings already
documented for `H_new` itself). `H14` is already implemented, already Tier-A, already
in the operator registry. Worth a dedicated look at BCR_ABL1 specifically, not a
project-wide reselection signal.

**Caveats, matching TASK-0116/0117's own attached to `H_new`'s numbers**: these are
single 60-trial random cutoff searches, not exhaustive; H14's and H13-native's numbers
carry the same search-density caveat `H_new`'s ceiling numbers do, and have not been
through the same parameter-validity audit TASK-0108 ran for `H_new`. Not more settled
than `H_new`'s own numbers, which remain under active reconciliation elsewhere in this
register (`H_new`'s own actual-vs-floor result is still not a statistically decided
win on any target, per TASK-0130's own bootstrap-CI finding — this task did not touch
that question).

Files touched: `__WORK_IN_PROGRESS__/src/allostery/propagators.py` (Option B wrapper
functions incl. the closed-form variant + `min_adequate_t_max` docstring caveat),
`__WORK_IN_PROGRESS__/tests/test_propagators.py` (13 new tests), `__WORK_IN_PROGRESS__/
scripts/h13_ceiling_comparison.py` (new).
