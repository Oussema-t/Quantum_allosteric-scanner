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