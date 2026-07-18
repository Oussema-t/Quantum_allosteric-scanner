# Shared Pitfalls

Add repeated failure patterns, false assumptions, or tool traps that should not be rediscovered.

## P-0001 — "Invariant on our test set" is a trigger, not a green light

- Pattern: a metric/scorer passes every test in the suite, and that gets read as
  verification. It only proves the suite didn't sample the transformation that breaks it.
- Evidence (this repo): two real bugs — ANM cumulative overlap moving 0.34→0.90 under a
  global rigid rotation (mode selection by index `w[6:]` instead of by eigenvalue, silently
  wrong when the contact graph was rank-deficient), and a "covariant vector invariant" that
  was only invariant under the Clifford subgroup, not generic SU(2) (4× drift). Both were
  invisible to every per-structure/per-frame unit test that existed at the time; both died
  to a ~12-line metamorphic test once someone ran the group instead of assuming it.
- Corollary: the discriminating test is almost never the first one you reach for — it's the
  symmetry that feels too obvious to check. And multi-turn agreement (human or agent, many
  rounds of confident prose) is not verification; neither bug above was caught by discussion,
  only by execution.
- How to apply: see [[INVARIANCE_PROTOCOL]] (`.ai/reference/INVARIANCE_PROTOCOL.md`) — every
  reported quantity needs its GAUGE/KNOB/SIGNAL transformation table classified *before* it's
  reportable, not after a bug is found the hard way.
- Source: `__WORK_IN_PROGRESS__/SUGGESTION.md` (absorbed here, [[TASK-0051]] — file removed
  as a freestanding doc since its content is now this entry plus `INVARIANCE_PROTOCOL.md`'s
  own "Rule of engagement" section, not a separate thing to keep in sync).

## P-0002 — A computed "ceiling" is not automatically above the floor

- Pattern: a floor/ceiling/headroom framing (`ceiling = best score reachable with the
  labels in hand`) is set up assuming `ceiling >= floor` by construction — that a
  fully-informed, label-using search can always at least match a trivial baseline it has
  no special access to. This is not guaranteed, and was not checked before being assumed.
- Evidence (this repo, [[TASK-0046]]/[[TASK-0082]], 2026-07-14): a real 60-trial random
  search over `H_new`'s entire physical-scalar space (`ceiling.ceiling_search`, CTQW
  propagation, the answer key in hand throughout) produced KRAS_G12C's ceiling AUC =
  0.5239–0.5250 — **below** that same target's proximity floor (0.798,
  `euclid_from_seed_centroid`/`hop_from_seed`/`degree_centrality`, [[TASK-0094]]). Every
  point in the searched 8-dimensional parameter space, evaluated against the real labeled
  pocket, scored worse than a baseline that only knows Euclidean/graph distance from the
  seed. The operator family's best case does not clear geometry, not just its default
  case.
- Corollary: `headroom = (actual - floor) / (ceiling - floor)` silently produces a
  meaningless (here, negative-denominator) number when this happens — the formula does
  not fail loudly, it just outputs a fraction nobody should read as "% of the gap closed."
  Check `ceiling > floor` explicitly, per target, before computing or reporting headroom
  — do not assume the ceiling search's access to labels made this check unnecessary.
- How to apply: any target's floor/ceiling/headroom row must state whether `ceiling >
  floor` held *before* a headroom percentage is computed; if not, report that fact as the
  finding (a stronger, more informative "honest NO" than a degenerate fraction would be),
  per [[TASK-0082]]'s own competence-map framing.
- Cross-reference: [[Q-0003]] (`.ai/memory/questions/architect-planner/open/`) — raised to
  the Architect/Planner: does this finding call into question whether a floor/ceiling/
  headroom framing is the right lens for this operator family at all, or is it scoped to
  this one target?
- **Note, same day**: an independent Architect/Critic-overlay pass
  (`REVIEW-2026-07-15b-ceiling-search-methodology.md`) reached this same finding and
  filed [[TASK-0116]] (60 blind random draws over ~8 dimensions is weak evidence for a
  *negative* claim specifically) and [[TASK-0117]] (unvalidated `t_max`/`n_steps`,
  shared with every other headline AUC in this project). This pitfall's "check `ceiling
  > floor` before reporting headroom" lesson stands regardless; whether *this specific
  instance* (`ceiling < floor` for KRAS_G12C) survives denser search / validated
  propagator parameters is now separately tracked by those two tasks, not yet resolved.
- **Resolution, 2026-07-16 ([[TASK-0118]]):** the specific instance *did not survive* --
  but not for either reason above. `REVIEW-panel-2026-07-16-v2` found the ceiling
  (0.524) and floor (0.798) that triggered this pitfall's own negative-denominator
  discovery had been computed under two *different* seed conventions
  (`ceiling_search_batched.py`'s full active-site array vs. `run_challenge.py`'s
  single-index crash workaround, [[TASK-0090]]) -- not a real ceiling-vs-floor
  comparison at all. This pitfall's own lesson ("check `ceiling > floor` explicitly")
  is one level too shallow on its own: it caught the negative-denominator *symptom*
  correctly, but the root cause was a silent unit mismatch between the two operands,
  not a genuine floor-ceiling inversion. Under one corrected convention, KRAS_G12C's
  ceiling (0.5269) clears its floor (0.4818) by +0.045 -- full numbers:
  `COMPETENCE_MAP.md`, `.ai/invariants/INV-0006`. **Extended corollary**: before
  trusting *any* cross-quantity comparison (ceiling vs. floor, apo vs. holo, old run
  vs. new run), confirm both sides were computed under the same gauge/convention, not
  just that the comparison's arithmetic is well-defined -- a negative or nonsensical
  result is one symptom of a unit mismatch, but a plausible-looking result can hide
  the same mismatch just as easily.

## P-0003 — Spot-check a new metric's own KNOB parameters before shipping its classification, not just its unit tests

- Pattern: a newly-wired reported quantity passes its own synthetic + real-target
  unit tests (correct arithmetic, correct wiring into the schema) and gets treated
  as done, without checking whether its *classification* (not just its output value)
  is stable across the project's already-known-live KNOBs (`t_max`, seed/source
  cardinality) — the exact gap [[INVARIANCE_PROTOCOL]] exists to close, but easy
  to skip when a task's own Intent Contract didn't explicitly demand it.
- Evidence (this repo, [[TASK-0099]], 2026-07-16): `coherence_sensitivity` (wiring
  `dephasing_sweep` into the verdict schema) landed with passing tests using
  `t_max=8` copied from an older, pre-review test's recipe — not re-derived or
  cross-checked. `REVIEW-panel-2026-07-16-v2` (written independently, same day)
  flagged `t_max` as an unfixed, unregistered gauge project-wide ("a precondition
  for the physics, not hygiene"). Direct spot-check on real KRAS_G12C data across
  `t_max ∈ {8, 25, 100}` (12x range) found: the *classification*
  (`COHERENCE_NOT_SIGNIFICANT`) held at every point, but the *absolute* per-gamma
  AUC's chance/floor diagnosis did not (`BEATS_CHANCE_NOT_FLOOR` at `t=8` vs.
  `NO_SIGNAL_IN_APO` at `t=25`/`100`) — the task's own narrow claim survived; a
  claim about the raw numbers would not have. The default was corrected to
  `t=25` (matching [[TASK-0105]]'s already-established, unrelated-task
  precedent for the exact same propagator) on this basis.
- Corollary: passing tests verify the *mechanism* is wired correctly; they do not
  verify the *conclusion* is robust to the project's own known-unstable knobs
  unless a test specifically sweeps them. A metric can be correctly computed and
  still report a conclusion that only holds at one arbitrary, uninvestigated
  parameter value.
- How to apply: before reporting a new classification/verdict quantity as done,
  identify which of the project's already-known KNOBs (check open reviews and
  `.ai/invariants/` first) plausibly touch its inputs, and spot-check the
  *classification*, not just the value, across a real (not synthetic-only) range
  before trusting it — cheap when the target is small (KRAS_G12C: ~1-20s/call),
  and the check itself becomes the KNOB row in that quantity's `INV-XXXX` record
  ([[INV-0007]] here) rather than a one-off comment.

## P-0004 — A `t→infinity` reference built from `|eigenvector|^2` silently assumes a sign that isn't there

- Pattern: writing a "true limit" test oracle for an `exp(-Ht)`-style relaxation by
  squaring the dominant eigenvector's components (`v[:,0]**2`, always non-negative,
  looks like a safe probability-density construction) instead of using what the real
  propagator actually computes and clips.
- Evidence (this repo, [[TASK-0109]], 2026-07-15): `ground_state_relaxation`'s real
  `t->infinity` limit is `clip(v[:,0] * <v_0|p0>, 0, None)`, renormalized — the
  *sign* of the overlap `<v_0|p0>` (which half of the eigenvector survives clipping)
  matters, and squaring throws that information away. A convergence-battery script's
  own test oracle used `v[:,0]**2` and produced an apparently-impossible result (total
  -variation distance to the "true" state *plateauing* around 0.31 instead of decaying
  to 0 as `t` grew) for every case where the overlap happened to be negative — read
  at first glance as a possible defect in `ground_state_relaxation` itself. Direct
  check (`ground_state_relaxation(H, t=1000)` against both candidate references)
  showed TV=0.31 against the squared reference and TV=7e-17 (machine precision)
  against the sign-correct one — the propagator was right; the test oracle was wrong.
- Corollary: whenever a "ground truth" reference for a relaxation/imaginary-time
  propagator is built independently of the function under test, re-derive it from the
  *same* formula the propagator actually evaluates (including any clip/sign step),
  not from a property (non-negativity, normalization) that merely looks sufficient.
  An eigenvector is only defined up to an overall sign — do not assume a convenient
  one.
- How to apply: before trusting an "analytic"/"true-limit" oracle in a new test,
  check it against the real function's own output at an extreme parameter value
  (very large `t`, very small `tol`, etc.) on at least one concrete case — the
  agreement (or lack of it) is cheap to check and catches exactly this class of bug
  before it's read as a finding about the code under test rather than the test itself.

## P-0005 — "Did not return within N hours" is not evidence of computational infeasibility without CPU-time, only wall-clock

- Pattern: a long-running compute call is left running in a shared/multi-tenant
  sandbox; it hasn't finished after N wall-clock hours; this is reported as "genuinely
  computing, not hung" (checked via process state, e.g. Linux `R`) and read as evidence
  the underlying computation is impractically expensive. Process state at a single
  checkpoint proves the process was *actively scheduled at that moment* — it does not
  prove *continuous* execution for the full elapsed wall-clock interval. A process can
  be starved by concurrent contention for long stretches (already proven real in this
  repo, see below) or, in an environment capable of it, suspended and resumed, and still
  show as actively running at the one moment someone checks. Wall-clock elapsed time and
  CPU-seconds actually consumed are different quantities, and only the second one is
  evidence about the computation's real cost.
- Evidence (this repo): two independent, related findings, neither of which by itself
  proves the general pattern, but together make it a real, standing risk rather than a
  hypothetical one — (1) [[TASK-0111]] found a *different* timing measurement in this
  same shared sandbox was inflated by "6 other concurrent Claude Code sessions" running
  at the same time (confirmed via `ps aux`), and explicitly distinguished a "controlled,
  same-moment" benchmark (trustworthy) from a "naive wall-clock timing of a real-network
  test in this environment" (not reproducible enough to serve as a real measurement) —
  this is the identical confound-class, already caught once, for a *different* claim.
  (2) [[TASK-0110]]'s "a single `time_averaged_ctqw` call did not return after 2+ hours"
  finding (cited downstream as evidence of computational infeasibility by
  `.ai/invariants/INV-0005-propagator-time-parameters.md` and [[TASK-0130]]) checked
  process state (`R`, not hung) at the point it was killed, but did not log CPU-seconds
  consumed (`resource.getrusage`/`/usr/bin/time`) across the full interval — so the
  *shape* of P-0005's risk applies to it directly, unverified either way. Raised
  2026-07-18 by the orchestrating user, who correctly noted the specific unruled-out
  case ("computer went to sleep, was woken after 1.5h, resumed") — plausible in general,
  though this repo's own evidence points more directly at contention (1) as the
  demonstrated mechanism in *this* sandbox specifically, not sleep/suspend, which is
  unconfirmed either way for this environment.
- Corollary: this is not just a one-off measurement-hygiene note — it is a structural
  gap in how this project (and its agent threads generally) handle long-running
  compute. An in-session synchronous wait that times out is not a computational-cost
  measurement; it is a session-length measurement wearing a computational-cost
  measurement's clothes. Declaring "infeasible" from it, without CPU-time
  corroboration, risks the same shape of error P-0001/P-0002 already named for other
  quantities: a plausible-looking number that was never actually checked against the
  thing it claims to measure.
- How to apply: (1) any claim that a computation "did not complete in N [wall-clock]
  time" must report CPU-time consumed over the same interval before being cited
  elsewhere as an infeasibility finding — if CPU-time is unavailable for a past claim,
  say so explicitly rather than silently treating wall-clock as a proxy. (2) for a
  genuinely long job (expected minutes-to-hours), default to detached/background
  execution with periodic CPU-time logging rather than an agent session blocking
  synchronously and giving up at an arbitrary point — an agent's own context/session
  boundary is not evidence about the computation's real feasibility, and a job that
  outlives one session is not thereby infeasible. (3) consider explicit hand-off to a
  human-in-the-loop to kick off and monitor a job expected to run past a session's
  practical attention span, rather than an agent either blocking in-session or silently
  declining to start something long — see [[TASK-0134]], filed to both re-verify the
  specific TASK-0110 claim with real CPU-time instrumentation and propose a reusable
  long-job/background-monitoring convention for this project generally.