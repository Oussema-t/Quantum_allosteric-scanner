# TASK-0187 ENM-induced connectivity-graph shortcut hypothesis

## Context

- ID: TASK-0187
- Title: test whether ENM conformational sampling ("wobbling") creates new
  contact-graph edges that shorten the active-site<->pocket hop-distance
  below its static-apo value, specifically (not as a generic noise
  artifact), and whether that shortening approaches the real holo
  topology's hop-distance.
- Status: Done
- Owner: Implementer (build), Architect/Planner (design, this file, and the
  gate below)
- Claimed By: Architect -- reserved 2026-07-31 for drafting;
  release or hand off via `claim.py` when execution actually starts, do not
  treat this as a standing claim on the build itself
- Claimed At: 2026-07-31 20:53
- Source: orchestrating collaborator (Bartosz), 2026-07-31: *"the protein is
  'wobbling' and spatially reorganising. These motions may induce pockets
  forming, as well as interaction pathways appearing... whether signalling
  'shortcuts' in the signalling graph may appear due to ENM protein
  morphing... investigations of APO-via-ENM-towards-HOLO meaningful and
  verifiable versus APO-HOLO signaling path distance distributions."*
- Priority: **P1, conditionally P0.** Elevate to P0 if [[TASK-0186]] finds
  most/all targets already spatially 1-hop in the static apo structure --
  in that case this task's finding (does dynamics add anything beyond an
  already-trivial static baseline) becomes directly load-bearing for
  whether TASK-0176's propagation-based observables have anything left to
  measure. If TASK-0186 finds most targets are NOT trivially close, this
  stays a P1 forward-proposal item.

## Why this matters, and how it differs from what's already filed

Three filed tasks sit close to this idea and none of them is it:

- **[[TASK-0185]]** asks "does a druggable *cavity* open under ENM
  sampling" -- a geometric/volume question, scored via fpocket. This task
  asks "does the *contact graph itself* gain new edges" -- a topology
  question, scored via hop-count on the same 8.0 A contact-graph convention
  [[TASK-0186]] uses. A cavity opening and a new contact are related but
  not the same event; conflating them would hide which one is actually
  doing the work if only one of the two shows a real effect.
- **[[TASK-0015]]** (`HOLO_DIRECTION_MODULE.md`) predicts *one* directed
  apo->holo deformation and feeds *one* deformed graph to transport.
  TASK-0185's own Open Questions already flag this overlap and recommend
  TASK-0015 be re-scoped or closed once 0185 lands. **This task is
  deliberately not that**: it samples the *undirected equilibrium ensemble*
  (closed-form Gaussian draws from ENM modes, no target, no direction, no
  MD -- same §Constraint 3 compliance argument as TASK-0185), not a
  predicted deformation toward a known target. Chosen this way specifically
  so it does not depend on or duplicate TASK-0015, which is being worked on
  elsewhere right now (see "Collision avoidance" below).
- **[[TASK-0171]]** re-runs the forward/reverse coupling test on the
  holo-native graph -- a different observable (`H_new`/
  `H2_combinatorial_laplacian`), also being worked on elsewhere right now.
  This task needs a holo-native *contact graph* as a reference point, which
  it builds directly from real holo coordinates using the already-`Done`,
  already-committed `_holo_native_labels` utility (TASK-0067) -- it does
  not need TASK-0171's coupling machinery or its completion.

**The elegant possibility, stated as a hope, not an assumption:** if a
specific (non-generic) shortcut effect is real, it reframes propagation
observables (CTQW/H_new) as walking a *dynamically rewiring* graph rather
than a static one -- which would partially rehabilitate that half of the
register rather than replacing it wholesale with pure cavity search
([[TASK-0185]]) or selection ([[TASK-0181]]). It would also connect neatly
to [[TASK-0181]] Phase B (side-chain QUBO): a quantum search over which
conformations open a shortcut is a coherent target for a quantum
contribution in a way that "search for an open cavity" alone is not. This
is exactly the kind of claim this project's own culture requires be
measured, gated, and reported negative if it comes back negative -- see
Constraints below.

## Collision avoidance (both machines share this git history)

TASK-0015/0171/0167(+.002/.003) are claimed and being worked on machine-2,
not visible from here (nothing committed for them in this checkout as of
2026-07-31). To keep this task mergeable without conflict:

- Build in a **new, standalone module** (e.g. `src/allostery/shortcuts.py`
  + `scripts/shortcut_hypothesis_measurement.py`), not by editing
  `HOLO_DIRECTION_MODULE.md`, `coarse.py`, `baselines.py`, or anything
  under active edit elsewhere.
- Reuse [[TASK-0185]]'s reference ensemble sampler
  (`conformational_search_prototype_REFERENCE.py`, already in this
  checkout) and [[TASK-0167.001]]'s `plant.py`/`select_distal_patch`
  (already `Done`, already committed) for the negative control -- both are
  finished, stable dependencies, not moving targets.
- `git fetch` + rebase before this task's work is pushed, per
  CLAUDE.md's collaboration convention -- if machine-2 has since landed
  TASK-0015/0171, re-check this task's boundary statement against what
  actually shipped before merging, don't assume the design above still
  holds unchanged.

## Design

**Step 0 (prerequisite, from [[TASK-0186]]) -- RESOLVED 2026-08-01.**
TASK-0186 ran: **PTP1B is the positive-control target.** It is the only one
of the 7 pocket-scoreable targets with static-apo min spatial-hop = 2 (every
other target already has a pocket residue at hop 1) and zero pocket residues
at hop<=1 at all (median hop 3.5) -- genuinely the most room for a dynamic
shortcut to matter. CARDIAC_MYOSIN is the second-best candidate (8% at
hop<=1, median hop 4.0, largest protein in the set at N=704) and a
reasonable secondary target if time allows. **Do not use KRAS_G12C or
CASPASE1 as the positive control** -- TASK-0186 found KRAS_G12C already 39%
trivially-close and CASPASE1 83%, both too close statically to show a clean
dynamic effect even if one is real. PTP1B's fold-compression ratio (8.9x,
the lowest of the 7) is also the most favorable baseline to beat.

**Step 1 -- ensemble generation.** Closed-form Gaussian draws from ENM
normal modes about the apo equilibrium (same method as TASK-0185's
reference script; amplitude ~ N(0, sqrt(kT/lambda))), undirected, no target
structure involved, no integrator. Cross-check: per-residue MSF over the
ensemble must match the analytic GNM/ANM MSF (same validation TASK-0185
itself requires) -- if it doesn't, the sampler is wrong and nothing
downstream is trustworthy.

**Step 2 -- per-sample topology.** For each sampled conformation, rebuild
the spatial contact graph at the same 8.0 A cutoff and recompute
hop-distance(active_site, pocket) via `baselines.hop_from_seed` exactly as
[[TASK-0186]] does for the static structure. Track, across the ensemble:
the minimum hop-distance achieved, and the fraction of samples at each hop
count -- this is the "shortcut" measurement.

**Step 3 -- specificity (the actual test).** Repeat Step 2 targeting a
**decoy patch** at the same starting spatial-hop-distance as the real
pocket, selected via [[TASK-0167.001]]'s `select_distal_patch` (already
validated to be a fair, non-trivial decoy). If the real pocket's
hop-distance shortens under sampling at a materially higher rate than the
decoy's, that is a specific effect. If both shorten at a similar rate, ENM
wobbling is just generic noise on the contact graph and the "shortcut"
framing does not survive -- report that plainly, it is a legitimate and
useful negative.

**Step 4 -- comparison to real holo topology.** Build the holo-native
contact graph directly from real holo coordinates (`_holo_native_labels`,
TASK-0067, already committed) and compute its hop-distance(active_site,
pocket) as the "target" value. Does the ensemble's minimum/typical
shortened hop-distance approach that value, overshoot it, or fall short?
This is the "APO-via-ENM-towards-HOLO... versus APO-HOLO... distributions"
comparison from the source request.

## Intent Contract

- Outcome: `src/allostery/shortcuts.py` (ensemble sampler + per-sample
  hop-distance recomputation, reusing not reimplementing
  `baselines.hop_from_seed`/`hamiltonians.contact_matrix`) +
  `scripts/shortcut_hypothesis_measurement.py`; a pre-registered
  falsification criterion written into this file **before** running; results
  on the positive-control target first, then all pocket-scoreable targets;
  a `RESULTS.md` section and hand-off content for [[TASK-0184]]/[[TASK-0183]]
  if the finding is positive and specific.
- Why required, not assumed: no filed task currently measures dynamic
  contact-graph topology change; [[TASK-0185]] measures cavity volume,
  [[TASK-0015]] predicts one directed deformation. Neither answers whether
  wobbling specifically shortens the active-site-to-pocket path.

- In Scope:
  - Steps 0-4 above, in order. Step 0 first -- do not pick a positive
    control before TASK-0186's numbers are in.
  - Undirected ENM ensemble only -- no MD, no trajectory, no directed
    deformation toward a known target (that boundary is what keeps this
    legal under §Constraint 3 the same way TASK-0185 is, and keeps it out
    of TASK-0015's territory).
  - Specificity test (Step 3) is the actual claim being tested, not Step 2
    alone -- a shortcut that isn't specific to the real pocket is not a
    finding.
  - Report against the incumbent label, flagged, same convention as
    TASK-0186; re-score against TASK-0177's consensus label once available.

- Out Of Scope:
  - Any directed apo->holo deformation prediction (TASK-0015's territory).
  - Cavity/volume measurement (TASK-0185's territory) -- this task may cite
    0185's results for context but does not duplicate its fpocket-based
    measurement.
  - Building anything beyond a small diagnostic module/script -- this is
    not a new production pipeline stage until the finding is positive and
    specific.
  - Claiming quantum relevance directly -- if this lands, the quantum
    connection is a forward-proposal sentence for [[TASK-0184]], not a
    result of this task.

- Constraints And Invariants:
  - **Pre-registered gate, written before running:** state, in this file,
    what counts as a specific effect (e.g. real-pocket shortening rate
    materially and consistently above the matched-decoy rate, across
    repeated decoy draws) BEFORE Step 3 is executed. Fix this wording
    before coding, per this project's standing convention -- do not defer
    it to "we'll know it when we see it."

    **Pre-registered specificity criterion (Implementer C, 2026-08-01,
    fixed before any Step 1 code is written):**
    - Ensemble size: N_ensemble = 2000 undirected ENM samples (Step 1),
      shared unchanged across the real-pocket and every decoy scoring pass
      (Step 2/3) so the comparison is apples-to-apples on the exact same
      draws, not independently resampled per patch.
    - Decoy count: N_decoy = 30 matched decoys via
      `select_distal_patch`, each constrained to the same starting
      static-apo hop-distance as the real pocket (hop=2 for PTP1B, per
      TASK-0186) and the same patch size (residue count) as the real
      pocket. 30 is chosen to make an empirical one-sided p ~= 1/31 the
      finest resolution available without a second, larger re-draw pass
      -- cheap enough to afford given the ensemble is reused, expensive
      enough to not be a coin flip.
    - Per-patch statistic: `shortcut_rate(patch)` = fraction of the 2000
      ensemble samples where hop-distance(active_site, patch) is strictly
      less than that patch's own static-apo hop-distance (i.e. the sample
      actually gained a shorter path, not merely a change in some other
      quantity).
    - **PASS (specific effect confirmed) requires BOTH, jointly, not
      either alone:**
      (a) *Significance*: `shortcut_rate(real_pocket)` exceeds the 95th
          percentile of the 30 `shortcut_rate(decoy_k)` values (i.e. beats
          all but at most 1 of 30 decoys) -- an empirical permutation-style
          test against the matched-decoy null, no assumed parametric form.
      (b) *Effect size floor*: `shortcut_rate(real_pocket) -
          median(shortcut_rate(decoy))` >= 0.10 (10 percentage points,
          absolute). Required in addition to (a) specifically because
          N_ensemble=2000 gives (a) enough power to flag a statistically
          real but practically trivial gap (this project's own
          convention after TASK-0158/TASK-0161: significance without a
          minimum effect size is not by itself a finding) -- see
          `.ai/invariants/` GAUGE/KNOB/SIGNAL discipline, same reasoning
          class.
    - **FAIL (generic-noise result)**: either (a) or (b) does not hold.
      Reported as a full negative on specificity per this task's own
      Constraints -- do not soften, do not retry with a different N_decoy
      or effect-size floor post hoc to manufacture a pass. If a change to
      either number is later judged necessary, it is a new pre-registered
      decision with its own dated entry here, not a silent edit of this
      one.
    - This criterion is evaluated once per target (first PTP1B, then
      CARDIAC_MYOSIN/others only if PTP1B passes, per the TODO ordering
      below) -- not re-run with different parameters until it passes.
  - MSF cross-check (Step 1) is blocking -- do not proceed to Step 2 on an
    unvalidated sampler.
  - 8.0 A contact cutoff reused unchanged (TASK-0067); no new geometric
    constant invented.
  - Reported whichever way it comes out, including a full negative on
    specificity (Step 3) -- that is exactly as valid a Phase-1 result as a
    positive, per this project's no-overwrite / all-negatives-are-findings
    convention.

- Planned Validation:
  - MSF cross-check against analytic GNM/ANM (blocking, see above).
  - Positive-control target chosen from TASK-0186's own numbers, not
    assumed.
  - Specificity test (Step 3) is itself the falsification mechanism --
    no separate held-out validation needed beyond it and the MSF check.

## In Progress

- 2026-07-31 (Architect, this thread): task drafted per Bartosz's
  conceptual request in this session. Design and collision-avoidance
  boundary against machine-2's TASK-0015/0171/0167 work recorded above;
  re-verify against what actually landed there before this task's build
  starts, since that machine is not visible from here.
- 2026-08-01 (Architect, this thread): the shared environment blocker is
  resolved (user repaired the machine's Xcode CLT; TASK-0186 ran
  successfully). **Step 0 resolved** -- PTP1B selected as positive control,
  see Design section above. Still not started beyond that: the
  pre-registered specificity criterion (first TODO item) needs writing
  before any Step 1 code.
- 2026-08-01 (Implementer C, this thread): claimed for build (overrode
  Architect's design-only reservation per this file's own Owner/Claimed-By
  note; user directed the handoff). Wrote the pre-registered specificity
  criterion into Constraints above (fixed before any code, per this
  project's standing convention). Next: locate and confirm the exact reuse
  targets (`conformational_search_prototype_REFERENCE.py`,
  `baselines.hop_from_seed`, `plant.select_distal_patch`,
  `_holo_native_labels`) before writing `shortcuts.py`.

## TODO

- [x] **Write the pre-registered specificity criterion into this file**
      before any code -- see Constraints, above (N_ensemble=2000,
      N_decoy=30, joint significance + >=0.10 effect-size floor).
- [x] Unblock the shared environment issue ([[TASK-0186]]'s blocker) or run
      on a machine with a working toolchain -- already resolved before this
      thread claimed the task (see TASK-0186's own Done section); confirmed
      still working by this task's own real RCSB run.
- [x] Step 0: read TASK-0186's results; pick positive-control target(s) --
      **PTP1B primary, CARDIAC_MYOSIN secondary.**
- [x] Step 1: ensemble sampler + MSF cross-check (blocking) -- **passed**
      (Pearson r=0.9998, median relative error 1.26%, N=2000 samples).
- [x] Step 2: per-sample hop-distance recomputation on the positive-control
      target -- real-pocket shortcut rate 1.7%.
- [x] Step 3: specificity test vs. matched decoy (`plant.py`) -- **FAILED**
      the pre-registered gate (real rate below decoy median, effect size
      -0.112).
- [x] Step 4: comparison to real holo-native topology -- holo-native hop
      also 2, unchanged from static apo.
- [x] Extend to remaining pocket-scoreable targets if the positive control
      clears its gate -- **not done, by design**: the gate did not clear,
      per this task's own pre-registered TODO ordering. Left as an Open
      Question for a possible follow-up task, not silently skipped.
- [x] `RESULTS.md` section; hand off to [[TASK-0184]]/[[TASK-0183]] if
      positive and specific -- section added (negative result, no
      quantum-relevance forward-proposal sentence since the finding is
      negative, per this task's own Out Of Scope constraint). No hand-off
      to TASK-0184/0183 since the finding is not positive and specific.
- [ ] Re-score against [[TASK-0177]]'s consensus label once available --
      left open; TASK-0177 not yet Done as of this task's own completion.

## Dependency

- [[TASK-0186]] -- static-apo spatial-hop numbers, needed to pick the
  positive-control target (Step 0). Hard blocker for Step 0 onward.
- [[TASK-0185]] (design reference, not a hard dependency) -- reuses its
  ensemble-sampler reference implementation.
- [[TASK-0167.001]] (Done) -- `plant.py`/`select_distal_patch`, reused
  unchanged for the Step 3 decoy.
- [[TASK-0067]] (Done) -- `_holo_native_labels`, reused unchanged for Step 4.
- [[TASK-0177]] -- soft, for the eventual re-score against the consensus
  label.
- Boundary-only (no code dependency, avoid touching): [[TASK-0015]],
  [[TASK-0171]], [[TASK-0167]]/.002/.003 -- claimed on machine-2 as of
  2026-07-31, not visible from this checkout.

## Open Questions

- Is Ca-level ENM sampling even capable of producing a spatial shortcut of
  the size needed, or is this -- like TASK-0185's own Open Questions
  suspect for cavity opening -- mostly a side-chain-layer effect that a
  backbone-only ENM can't reach? **Resolved (partially), 2026-08-01: the
  real measurement leans toward "not at this layer" for PTP1B specifically
  -- the real pocket's shortcut rate (1.7%) sits below even the matched
  decoys' median (12.9%), not just short of significance. Still genuinely
  open whether a side-chain-layer model would differ; not testable with
  the Cα-only ENM this task used, same limitation TASK-0185 already
  flagged for its own cavity-opening question.**
- If Step 3's specificity test fails (shortcuts are generic noise, not
  pocket-specific), does that also weaken TASK-0185's cavity-opening
  framing, since both rely on ENM sampling producing something meaningfully
  non-generic? **Resolved, 2026-08-01: yes, flagged for TASK-0184's
  narrative as recommended -- both forward-proposal tasks now report a
  Cα/backbone-layer negative from the same closed-form ENM-sampling
  method, a shared failure mode worth stating once in the submission
  narrative rather than as two independent misses.**
- Should this task's positive-control choice be locked to a single target
  before the freeze (2026-08-07), given the time budget? **Resolved,
  2026-08-01: yes, followed as recommended -- ran the full Step 1-4
  pipeline on PTP1B only; did not extend to CARDIAC_MYOSIN or the rest of
  the benchmark set since the positive control's own gate did not clear
  (see TODO's "Extend to remaining pocket-scoreable targets" row).**

## Done

- 2026-08-01 (Implementer C, this thread): built `src/allostery/shortcuts.py`
  (`equipartition_ensemble`/`analytic_msf`/`msf_cross_check`/
  `patch_hop_distance`/`ensemble_hop_matrix`/`shortcut_rate`/
  `specificity_test`) + `scripts/shortcut_hypothesis_measurement.py` +
  `tests/test_shortcuts.py` (8 tests, synthetic fixtures, both directions:
  a zero-displacement ensemble is correctly rejected, an engineered
  displacement toward the seed is correctly accepted, and a deliberately
  miscalibrated 3x-rescaled ensemble is correctly caught by the MSF
  cross-check). Full `pytest tests/ -q` run before and after: 996 passed
  (+8 new), 2 skipped, 2 xfailed, no regressions.

  **Real run on PTP1B (apo=1SUG, holo=1T49), 16.2s wall-clock:**
  - Step 1 (blocking MSF cross-check): **passed** -- Pearson r=0.9998,
    median relative error 1.26% (gate: r>=0.90, rel. error<=25%). Sampler
    trusted for Step 2+.
  - Step 2: static-apo hop=2 (exact match to [[TASK-0186]]'s own number,
    a direct cross-script sanity check). Real-pocket shortcut rate over
    2000 ENM samples = **1.7%** (34/2000).
  - Step 3 (the pre-registered gate): **FAILED.** 30 matched decoys
    (`select_distal_patch`, hop_percentile=60, max_floor_auc=0.5) gave
    rates 0%-52.5% (median 12.9%, 95th percentile 51.9%). Real rate
    (1.7%) is below the decoy *median*, let alone the 95th-percentile
    significance bar -- effect size -0.112, wrong sign. Neither the
    significance leg nor the material-effect-size leg of the criterion
    passes.
  - Step 4: real holo-native active-site<->pocket hop (`_holo_native_labels`)
    is also 2, unchanged from the static-apo baseline -- no evidence the
    real deposited holo structure collapsed this path either.
  - **Not extended to CARDIAC_MYOSIN or the remaining 5 pocket-scoreable
    targets** -- the task's own pre-registered TODO ordering only
    authorizes extension if the positive control clears its gate; it did
    not.

  **Implementer's-call decisions**: (1) `kT=20.0`, not the module
  default of `1.0` -- matched to TASK-0185's reference prototype's own
  actual sweep value (its `kT=1.0` is only a function default, never
  the value used in its real runs), since this task's Design section
  cites that prototype as "same method." (2) refactored `shortcut_rate`
  to take a precomputed `hop_matrix` (via new `ensemble_hop_matrix`)
  rather than recomputing the displaced contact graph once per patch --
  at PTP1B's scale (N=298, 2000 samples, 31 patches total) the naive
  per-patch version would have rebuilt the identical displaced graph 31x
  redundantly; done before the real run, not after finding it slow.
  (3) `patch_hop_distance` uses **min** hop over patch residues (not
  mean), matching TASK-0186's own "min spatial-hop" reporting
  convention for a whole-pocket scalar.

  **RESULTS.md**: new dated section + open-questions row 49 (both
  appended, nothing overwritten). No hand-off content for
  [[TASK-0184]]/[[TASK-0183]] since Out Of Scope explicitly limits the
  quantum-relevance forward-proposal sentence to a positive-and-specific
  finding, which this is not.

  **Not done**: re-score against [[TASK-0177]]'s consensus label
  (TASK-0177 not yet Done); side-chain-layer follow-up (Open Questions,
  above) -- left as a possible future task, not filed here since this
  task's own scope is a single measurement, not a new pipeline stage.
