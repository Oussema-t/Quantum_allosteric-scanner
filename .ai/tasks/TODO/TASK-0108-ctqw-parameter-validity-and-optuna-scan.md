# TASK-0108 CTQW/propagator parameter validity + Optuna floor/ceiling scan (parent)

## Context

- ID: TASK-0108
- Title: Thin coordinator for two related but independently-stateful
  slices of work, per explicit user request: (a) [[TASK-0109]] — do
  `time_averaged_ctqw`/`ground_state_relaxation`/`haken_strobl`'s
  numerical parameters (`t_max`, `n_steps`, `gamma`) have any validity
  check at all, on any protein, ever? (Answer, verified against the real
  code before filing this: **no**.) (b) [[TASK-0110]] — an Optuna-based
  parameter scan on the real mandatory targets, apo-only (floor) vs.
  holo-informed (ceiling).
- Status: TODO
- Owner: Architect/Planner (this task is a coordinator only — see
  `.ai/tasks/README.md`'s subtask convention: "the parent file stays a
  thin coordinator... holds shared decisions/constraints... but not the
  implementation detail itself")
- Claimed By: —
- Claimed At: —
- Source: direct user request, 2026-07-15 — "I don't seem to remember
  any checks for the validity of its parameters that were used in any of
  the proteins," followed by an explicit 4-point scope (tests for
  parameter validity + power laws; literature citations; Optuna
  apo-scan=floor / holo-scan=ceiling).
- Crit Ref: the user's suspicion was confirmed by direct code inspection
  before this task was filed, not assumed — `propagators.py`'s
  `time_averaged_ctqw` has zero checks that `n_steps` resolves `H`'s
  fastest oscillation or that `t_max` is long enough relative to the
  spectral gap to have converged. The same fixed `t_max=15.0`/
  `n_steps=500` literal is threaded through every call site in
  `analysis.py`, `ceiling.py`, and `run_challenge.py`'s `T_MAX`/`N_STEPS`
  constants, applied identically to KRAS_G12C (169 residues), BCR_ABL1
  (451), and CARDIAC_MYOSIN (950+) — three very differently-sized
  systems. `H_new`'s own potential terms give it a protein-specific,
  non-bounded spectrum (observed minimum eigenvalues of -1.99/-2.76/
  -4.21/-4.99 across different real and synthetic runs this session), so
  "normalized Laplacians have bounded spectra" does not rescue this.
  [[TASK-0102]] already did a one-off, manual version of the right check
  (computed BCR_ABL1's spectral gap, showed `t_max=15-20` converges
  *for that target*) — this task generalizes that into something
  systematic, applied before any operator's output is trusted on any
  target.

## Shared decisions and constraints (read by both subtasks)

- **Scope boundary between the two subtasks**: TASK-0109 answers "is a
  given `(H, t_max, n_steps)` combination numerically valid," using only
  synthetic systems + literature — no real PDB data, no ground truth, no
  new dependency. TASK-0110 answers "what parameter values are actually
  best on the real targets," using Optuna against real structures — real
  network access, real compute, and a new dependency (`optuna`, not
  currently installed — confirmed via `pip show optuna` before filing).
  Do not blur the two: TASK-0109 must not require network access:
  TASK-0110 must not invent its own ad hoc convergence criterion instead
  of using TASK-0109's.
- **Neither subtask is a Tier-2 operator-selection act** — per
  [[TASK-0100]]'s architecture decision, using ground truth to pick a
  "best" parameter value on N=3 mandatory targets is exactly the
  multiple-comparisons risk that decision already gated. TASK-0110's
  "ceiling" scan is diagnostic/descriptive (same status as [[TASK-0046]]'s
  ceiling search, which it directly extends) — it does not change
  `run_challenge.py`'s live defaults on its own authority.
- **New dependency discipline**: `optuna` is not in any current
  manifest — `requirements.txt` (repo root) is explicitly backend-only
  ("Quantum Allosteric Scanner — backend dependencies"); the research
  package (`__WORK_IN_PROGRESS__/src/allostery`) has no dependency
  manifest of its own at all (checked `pyproject.toml` — pytest config
  only). TASK-0110 must add one (or extend an existing file) rather than
  relying on an ambient `pip install`, and must flag this gap explicitly
  rather than silently assume a manifest exists.

## Dependency

- [[TASK-0109]], [[TASK-0110]] — the two subtasks. TASK-0110 should read
  TASK-0109's power-law characterization before choosing what parameter
  *range* to hand Optuna (soft dependency — not a hard block, since an
  Optuna search over a plausible range can start independently, but a
  well-informed range is cheaper than a blind one).
- [[TASK-0102]] — the one-off precedent both subtasks generalize/extend.
- [[TASK-0046]] — the existing ceiling-search precedent TASK-0110 extends
  to CTQW's own numerical parameters (as opposed to `H_new`'s physical
  potential-weight parameters, which TASK-0046 already covers).

## Open Questions

- The user's exact framing ("Apo scan => floor. Holo scan => ceiling.")
  is given a specific interpretation in TASK-0110 (see that file) —
  flagged there for confirmation before a large compute run is launched
  on the wrong objective.

## Done

(not yet — parent closes when both children are Done)
