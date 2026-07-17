# TASK-0110 Optuna parameter scan on real targets — apo scan (floor) vs. holo scan (ceiling)

## Context

- ID: TASK-0110
- Title: Use Optuna (new dependency) to search CTQW/propagator numerical
  parameters (`t_max`, `n_steps`, and `haken_strobl`'s `gamma` where
  applicable) on the real mandatory targets — an apo-only scan
  establishing a "floor," and a holo/label-informed scan establishing a
  "ceiling," per explicit user request.
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: subtask of [[TASK-0108]], per explicit user request ("Optuna
  search for target systems. Apo scan => floor. Holo scan => ceiling.").

## Intent Contract — **interpretation flagged for confirmation before a large run starts**

The user's framing is terser than this task needs to execute safely;
this is my read of it, stated explicitly rather than silently assumed:

- **Apo scan ("floor")**: Optuna searches `t_max`/`n_steps`/`gamma`
  using an objective computed **without any pocket-label ground truth**
  — i.e., [[TASK-0109]]'s convergence-quality criterion (minimize
  numerical error / find the cheapest parameters that still pass
  convergence) rather than AUC. This is safe to run with no leakage
  concern (no label read at all) and establishes the *minimum valid
  parameter regime* usable in a real, undisclosed-answer deployment —
  "floor" in the sense of "the honest, non-cheating baseline parameter
  choice," analogous in spirit to `baselines.py`'s floor (a
  non-optimized-against-the-answer reference point), not identical to it.
- **Holo scan ("ceiling")**: Optuna searches the same parameters using
  real pocket-label AUC as the objective — the same concept as
  [[TASK-0046]]'s `ceiling_search`, but for CTQW's *numerical* parameters
  specifically (as opposed to `H_new`'s physical potential-weight DOF,
  which TASK-0046 already covers), and using a real optimizer (Optuna's
  default TPE sampler) instead of blind random search.
- **If this reading is wrong**, correct it before the real-target run
  starts — this is real compute + a new dependency, worth confirming the
  objective before spending either.

- Status: TODO
- In Scope:
  - add `optuna` as a new dependency for the research package — flagged
    explicitly (per [[TASK-0108]]'s shared Constraints: no dependency
    manifest currently exists for `__WORK_IN_PROGRESS__/src/allostery`;
    `requirements.txt` at repo root is backend-only). Create or extend
    whatever manifest is appropriate; do not rely on an ambient
    `pip install` alone.
  - an apo-only Optuna study per mandatory target (KRAS_G12C, BCR_ABL1,
    CARDIAC_MYOSIN), objective = [[TASK-0109]]'s convergence-quality
    metric, searching over a range informed by TASK-0109's synthetic
    power-law characterization (soft dependency — start with a
    reasonable range if TASK-0109 isn't done yet, but revisit the range
    once it is).
  - a holo-informed Optuna study per mandatory target, objective = real
    AUC against `labels.build_labels(...)`'s pocket, same parameter
    space.
  - report both studies' best trial + the full trial history (Optuna's
    own `study.trials_dataframe()` or equivalent) per target — per this
    project's "an honest NO is a publishable result" convention, a study
    that finds no real headroom (matching [[TASK-0046]]'s KRAS_G12C
    finding) is a valid, reportable outcome, not a failure to hide.
  - reuse `run_challenge.py`'s existing fetch/clean glue and
    `frozen_context`/labeling accessors where the holo scan needs
    ground-truth labels — do not re-derive fetch/label logic.
- Out Of Scope:
  - **this is explicitly Tier-1 diagnostic work, not Tier-2 operator/
    parameter selection** — per [[TASK-0100]]'s architecture decision,
    do not wire either scan's "best" result into `run_challenge.py`'s
    live defaults; that would require the same `frozen_context`/
    `leave_one_protein_out` gating TASK-0100 already mandated for any
    selection act, and is explicitly a separate, future task if the
    scans' results warrant it.
  - `H_new`'s own physical potential-weight parameters — already covered
    by [[TASK-0046]]; this task is CTQW's numerical parameters only.
  - inventing a new convergence criterion — use [[TASK-0109]]'s.
- Constraints And Invariants:
  - N=3 mandatory targets — per [[TASK-0100]], report per-target results
    plainly rather than pooling into one cross-target "best" number; a
    3-point optimization landscape is not a robust generalization claim
    regardless of which objective is used.
  - `ceiling_context()` (per [[TASK-0046]]'s precedent) should wrap the
    holo-informed scan's trials, matching this project's existing
    DEV/FROZEN state-machine discipline even for non-selection diagnostic
    work that reads ground truth.
- Planned Validation: both studies actually run to completion on all 3
  mandatory targets (or documented per-target if one is skipped and
  why), with the full trial history available for inspection — not just
  a single best-value summary.

## In Progress

None

## TODO

None -- see Done below.

## Dependency

- [[TASK-0109]] — soft dependency (informs search range; not a hard
  block).
- [[TASK-0046]] (Done) — the existing ceiling-search precedent this
  extends to a different parameter axis; its KRAS_G12C real result is
  this task's cross-check target.
- [[TASK-0100]] — governs what this task's results are and aren't
  allowed to justify (Tier-1 only).

## Open Questions

- Exact Optuna sampler/pruner choice (TPE default vs. something else) —
  not pre-decided; Implementer's call, state the choice and why in Done.
- Where the new `optuna` dependency manifest should live — flagged in
  [[TASK-0108]]'s shared Constraints as a real gap (no existing
  research-package manifest), not pre-decided here.
- **Added 2026-07-15, `REVIEW-2026-07-15b-ceiling-search-methodology.md`
  finding #1:** [[TASK-0116]] wants the same kind of real-optimizer
  upgrade this task brings for CTQW's numerical parameters, but applied
  to `ceiling.py`'s `H_new` physical-weight space instead — explicitly
  out of *this* task's scope (see Out Of Scope above). Once this task's
  Optuna wiring/dependency manifest lands and is proven on real targets,
  [[TASK-0116]] can likely reuse it directly rather than standing up a
  second Optuna integration point. Not a reason to widen this task's own
  scope now — flagged for whoever picks up TASK-0116 next.

## Done

**Interpretation confirmed** per this task's own flagged reading (apo
scan = convergence-objective floor, holo scan = AUC-objective ceiling,
both diagnostic Tier-1 per TASK-0100) -- not contradicted by anything
found while implementing.

**Dependency**: `optuna` (4.9.0) added to a new `[project]` table in
`__WORK_IN_PROGRESS__/pyproject.toml` (TASK-0108's own flagged gap: no
manifest existed for this package before this task), alongside the full
ambient third-party import set already in use (numpy/scipy/scikit-learn/
networkx/pyyaml/prody/matplotlib, confirmed by grepping every import
statement across `src/allostery/*.py`, not guessed). No version pins
(this package has never been pinned; retrofitting the rest is out of
scope, flagged not silently done).

**Sampler**: Optuna's default TPE (`optuna.samplers.TPESampler`), fixed
`seed=7` for reproducibility -- no reason found to prefer a different
sampler; TPE's own warm-up/exploit behavior is exactly what a black-box,
non-differentiable objective like this needs.

### Implementation (`src/allostery/optuna_scan.py`, `tests/test_optuna_scan.py`, 11 tests)

**Search reparameterization (a real design correction, found by testing,
not assumed in advance):** an initial version searched `t_max` and
`n_steps` independently. Since `propagators.check_convergence`'s
Nyquist bound on `n_steps` scales linearly with `t_max`, independent
sampling almost never lands in the jointly-valid region within a
practical trial budget (measured: 0/30 converged trials on a synthetic
test case). Fixed by deriving `n_steps = ceil(min_adequate_n_steps
(t_max) * oversample)` from TASK-0109's own closed-form prescription and
searching only `t_max` + a small `oversample >= 1.0` margin -- Nyquist
is satisfied by construction, so the search only has to find where the
*gap-based* criterion holds. Also found and fixed: an additive
unconverged-trial penalty (`+1e6`) is not reliably larger than a real
target's own converged cost (which can itself be in the trillions, see
below) -- switched to a penalty anchored on the search range's own
worst-case valid cost, verified by direct testing to always dominate.

**`t_max_range` is adaptive per target**, anchored on `propagators.
min_adequate_t_max` (TASK-0109) rather than a fixed guessed constant --
directly implements `REVIEW-panel-2026-07-16-v2.md` §2.2/§5 P0#2 ("set
t* per operator from its spectral gap... t_max=15 is hardcoded... 100x
too short"). A fixed range risked never bracketing the true converged
region for a real small-gap `H_new`, which would have made the whole
floor scan vacuous.

**`max_n_steps` cap (found necessary by direct measurement, not
anticipated when this task was filed):** `time_averaged_ctqw` evaluates
its time grid in an explicit Python loop, O(n_steps). A first real run
against KRAS_G12C at the gap-prescribed `t_max` (~4.8e6) needed
`n_steps~1.3e7` -- a single call did not return after 2+ hours (measured
directly; the process was still in state `R`, genuinely computing, not
hung). Every holo ceiling scan below therefore runs twice: an
**aspirational** pass over the full adaptive range (capped at
`max_n_steps=20,000`, every trial's occupation is Nyquist-*aliased* when
capped, flagged per-trial via `n_steps_capped`) and a **practical** pass
restricted to the `t_max` range genuinely reachable without capping
(computed from `H`'s own bandwidth), which also always includes `t_max=
1` so the currently-shipped default (`t_max=15`) sits inside the
searched range, not silently excluded (an earlier version's practical
range started at 150, excluding it -- caught by inspection, fixed).

### Real 3-target run (live RCSB, real compute, `scripts/optuna_parameter_scan.py`)

**Seed convention, stated explicitly:** the full active-site array (not
TASK-0090's old scalar workaround -- this script never calls
`select.py`), scored via `time_averaged_ctqw`'s default `coherent=True`
(equal-amplitude coherent superposition) -- matching [[TASK-0046]]'s own
real-run convention exactly, deliberately, for a valid apples-to-apples
cross-check (see below). **Caveat, not silently absorbed:** `TASK-0118`
landed *during* this task (concurrent thread) and has since declared
`coherent=False` (incoherent statistical mixture) the project's
canonical convention for every scored call site (`run_challenge.py`,
`.ai/invariants/INV-0006`), per the same panel review's §2.1/Hidden
Assumptions ("a coherent 18-residue superposition asserts phase
coherence with no biophysical basis"). This task's own numbers below are
**not** computed under that now-canonical convention -- re-running under
`coherent=False` is flagged as a natural follow-up (also updates the
seed-choice axis, not just t_max/n_steps, so it is out of this task's
own scope to fold in in-flight), not chased mid-task.

| Target | N | Closed-form `t_max` | Closed-form `n_steps` | Floor: Optuna best cost | Aspirational ceiling AUC (100% capped, unreliable) | **Practical ceiling AUC** | at `t_max` |
|---|---|---|---|---|---|---|---|
| KRAS_G12C | 169 | 4.82e6 | 1.28e7 | 6.28e13 (closed-form: 6.20e13) | 0.4687 | **0.4750** | 278.8 |
| BCR_ABL1 | 451 | 2.18e6 | 7.06e6 | 1.56e13 (closed-form: 1.54e13) | 0.4889 | **0.5829** | 2.39 |
| CARDIAC_MYOSIN | 950 | 5.92e7 | 2.00e8 | 1.20e16 (closed-form: 1.18e16) | 0.7676 | **0.8149** | 7.67 |

Floor-scan Optuna best cost matches the closed-form prescription within
1.3-2.5% for all three targets -- a real, independent cross-check that
`apo_floor_scan`'s search and `check_convergence`'s own analytic
criterion agree, not just two functions that happen to both exist.

**Headline finding #1 -- the clock is not merely short, it is
5-7 orders of magnitude short, and the gap grows with system size.**
Current pipeline default (`t_max=15`, `n_steps=500`) vs. the smallest
`t_max` at which `time_averaged_ctqw`'s own decoherent-limit criterion
holds (`tol=1%`): KRAS_G12C needs `t_max` ~**320,000x** larger;
BCR_ABL1 ~**145,000x**; CARDIAC_MYOSIN ~**3,950,000x**. This directly
confirms and quantifies `REVIEW-panel-2026-07-16-v2`'s P0#2 ("t_max=15
is hardcoded... 100x too short") -- the true gap is far larger than that
review's own order-of-magnitude estimate, discovered here by actually
computing it per target rather than estimating.

**Headline finding #2 -- genuine convergence is currently computationally
infeasible, not just unperformed.** Every single trial in every
aspirational-range ceiling scan (100% across all 3 targets) hit the
`n_steps` cap -- meaning the gap-prescribed `t_max`/`n_steps` pair
cannot be evaluated at all with `time_averaged_ctqw`'s current O(n_steps)
Python-loop implementation in practical wall-clock time. "Fix the clock"
(the review's own P0#2 framing) is therefore not a parameter change one
can simply apply -- it requires either an algorithmic change to
`time_averaged_ctqw` (e.g. exploiting that the true infinite-time limit
has a cheap closed form, `sum_k |v_k(j)|^2|v_k(source)|^2`, no time loop
needed -- `RESULTS.md`'s own existing note that `time_averaged_ctqw` is
"effectively decoherent," Spearman 0.9998 to that exact limit at the
current operating point, per the panel review §1.1) or accepting a
`t_max` far short of true convergence. This is a new, load-bearing
finding this task's own real-target run produced, not anticipated when
filed.

**Headline finding #3 -- per-target practical-ceiling results, and what
they mean:**
- **KRAS_G12C**: practical ceiling 0.4750, near chance. **Cross-checked
  against [[TASK-0046]]'s independent real KRAS_G12C ceiling (0.5250)**
  -- same target, same full-array/coherent seed convention, *different*
  parameter axis (TASK-0046 searched `H_new`'s physical potential
  weights at fixed `t_max=15`; this task searches `t_max`/`n_steps` at
  fixed default physical weights). **Agreement, not disagreement**: both
  land near chance (0.47-0.53), a real cross-validation from two
  independent optimizers on two different axes sharing only the seed
  convention -- under this convention, KRAS_G12C shows no recoverable
  ceiling on either axis, individually or (by implication) jointly.
- **BCR_ABL1**: practical ceiling 0.5829 at `t_max=2.39` -- notably
  *smaller* than the current default (15), and a real, non-trivial
  headroom finding (a smaller propagation time discriminates the pocket
  better than the current default under this seed convention). Reported
  as a genuine, unexpected result, not folded into the "everything is
  near chance" pattern the other two targets show -- worth a dedicated
  follow-up (this task's own Out Of Scope forbids wiring it into
  `run_challenge.py`'s live defaults directly; that is a Tier-2
  selection act per TASK-0100).
- **CARDIAC_MYOSIN**: practical ceiling 0.8149 at `t_max=7.67`. High,
  but inherits every caveat this target already carries independent of
  this task (`REVIEW-panel-2026-07-16-v2` §1.2/§4: apo 5TBY is "the
  worst structure in the set," a 20 A cryo-EM docked homology model;
  `INSUFFICIENT_RESOLUTION` self-flagged by `classify_failure` for
  N=950). Not a new positive result -- a numerical-parameter-axis
  confirmation of an already-known, already-caveated one.

**Compute notes**: floor scans are near-instant (<2s per target,
including 200 trials each) since `check_convergence`/`min_adequate_n_
steps` never re-decompose `H` per trial (the precomputed eigenvalue
array is reused throughout, unlike the ceiling scans). Aspirational
ceiling scans cost 60-1400s depending on target size (`time_averaged_
ctqw` still re-decomposes `H` per trial -- see `optuna_scan.py`'s own
module docstring for why this per-trial cost was accepted rather than
optimized around). Practical ceiling scans are fast (9-70s) since their
`n_steps` stay near the cap boundary at most, not deep past it.

**Tests**: `tests/test_optuna_scan.py`, 11 cases (all synthetic/offline,
no network) -- `.venv/bin/python3 -m pytest -q tests/test_optuna_scan.py`,
11 passed.

**Out of scope, not attempted**: wiring any result into `run_challenge.
py`'s live defaults (Tier-2, TASK-0100); the `haken_strobl` `gamma`
axis ("where applicable" per this task's own Title) -- the primary
headline propagator throughout this pipeline is `time_averaged_ctqw`,
never `haken_strobl` (zero call sites in the reported pipeline per
TASK-0099's own finding), so `gamma` was not searched; re-running under
TASK-0118's now-canonical `coherent=False` convention (flagged above).
