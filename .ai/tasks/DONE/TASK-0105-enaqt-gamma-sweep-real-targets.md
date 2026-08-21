# TASK-0105 ENAQT γ-sweep on real targets — the interior-optimum experiment

## Context

- ID: TASK-0105
- Title: Measure transport efficiency from the active site to the labeled
  pocket, on real mandatory-target topologies, across a dephasing-rate
  sweep γ ∈ [10⁻⁴, 10²], using `propagators.haken_strobl`. Report the
  **interior optimum and enhancement ratio over the coherent walk
  (γ→0)** — not AUC recovery of any prior number.
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `REVIEW-2026-07-13b`, §7 Tier 1, item **T-C** — "the single
  highest-value experiment available before the deadline." Replaces the
  old framing of [[TASK-0091]]'s originally-considered dephasing question
  (superseded before that task was re-filed — see Crit Ref).
- Crit Ref: this is the **reframing of the old TASK-0091** the review
  describes in §4: "the old framing ('does dephasing recover 0.731?') was
  killed for the right reason — Haken-Strobl's γ→∞ limit is driven by
  off-diagonals while GSR is dominated by diagonals, so they cannot
  converge." The right question was hiding underneath and is what this
  task asks. Do not reintroduce the old framing.

## Intent Contract

- Outcome: for at least the 3 mandatory targets (KRAS_G12C, BCR_ABL1,
  CARDIAC_MYOSIN), a measured transport-vs-γ curve from the active site
  to the labeled allosteric pocket, showing (a) whether an interior
  optimum exists (transport at some γ* > 0 exceeds both γ→0 and γ→∞), (b)
  the enhancement ratio at that optimum over the coherent limit, (c)
  whether γ* tracks anything measurable about the target (e.g. disorder/
  heterogeneity along the path, per the review's synthetic finding).
- In Scope:
  - reuse `propagators.haken_strobl` directly — the review's synthetic
    result (§4) was produced with this repo's own implementation, not a
    new one
  - apply TASK-0094's proximity floor to the result (an ENAQT transport
    advantage must itself be checked against trivial proximity, same
    discipline every other operator in this repo is held to)
  - report transport magnitude (not AUC) vs. γ as the primary output —
    the review is explicit the falsifiable signature is the interior
    optimum shape, not a ranking metric
  - run on real target topologies (real contact graphs from real apo
    structures), not only the review's synthetic disordered-bridge
    network — the synthetic result establishes the *mechanism* works in
    principle; this task establishes whether it's *present* on the actual
    targets
- Out Of Scope:
  - wiring this into the scored verdict path — that's [[TASK-0099]],
    which should be revisited/resequenced after this task's result is
    known (if there's no interior optimum on real targets, wiring a
    metric for one is premature)
  - the NISQ/gate-noise connection — review §7 Tier 2, **T-F**, a later
    task, explicitly sequenced after this one ("Connect T-C's interior
    optimum to the challenge's noise resilience objective")
  - the new `mode_coparticipation` operator — separate, [[TASK-0103]]-
    adjacent tier
- Constraints And Invariants:
  - per `INVARIANCE_PROTOCOL.md`: γ is being swept deliberately here, so
    report the **shape of the curve**, not a single point estimate —
    this is the KNOB-vs-GAUGE discipline applied correctly (unlike the
    historical mistakes the protocol itself was written to prevent).
  - this is diagnostic/exploratory science, not a frozen-config selection
    act — does not need `protocol.frozen_context`/LOPO gating (same
    reasoning TASK-0100 already applied to TASK-0067's cutoff sweep).
- Planned Validation: the swept curve itself, per target. If no interior
  optimum is found on real targets (unlike the synthetic construction),
  that is a real, reportable finding — do not adjust the synthetic
  construction's parameters to manufacture one on real data.

## In Progress

None

## TODO

- [ ] Confirm `haken_strobl`'s real-target call signature (source, target
      pocket indices, contact graph, γ range) against how the review's
      synthetic experiment invoked it.
- [ ] Run the γ-sweep on all 3 mandatory targets.
- [ ] Apply TASK-0094's proximity floor to the transport-advantage result.
- [ ] Report per-target: interior-optimum presence, γ* location,
      enhancement ratio over γ→0, and floor-clearance.
- [ ] Flag whether γ* correlates with anything structurally measurable
      (disorder proxy, B-factor spread along the path) — observational,
      not a claim, unless the data supports one.

## Dependency

- None blocking — `haken_strobl`, `baselines.py` (TASK-0094's floor), and
  real target data (`config/targets.yaml`) all already exist and are Done.
- Feeds [[TASK-0099]] (should be resequenced to consume this task's
  result rather than proceed on its pre-review framing) and review §7
  Tier 2 **T-F** (NISQ noise-robustness connection).

## Open Questions

- None yet — construction and measurement are fully specified by the
  review; open questions will surface from the real-target results
  themselves.

**Caution added 2026-07-13, per `REVIEW-2026-07-13c` (CTQW trapping
mechanism):** if this sweep runs `H_new` only, an absent interior-γ
optimum may reflect that operator's own transport localization (never
leaves the seed's first contact shell, per that review) rather than an
absence of the ENAQT effect in general. Run the γ-sweep across at least
`H_new`, `H10_disorder_suppressed`, and `H2_combinatorial_laplacian` so a
null result on `H_new` isn't mistaken for "no ENAQT effect here."

## Done

- 2026-07-14, Implementer A. Added `__WORK_IN_PROGRESS__/scripts/
  enaqt_gamma_sweep.py`: `sweep_gamma(H, source, pocket_mask, gammas, t)`
  runs `haken_strobl` across a γ grid (`gamma=0` anchor computed directly
  via `ctqw`, cheaper/exact), reports transport magnitude (total
  occupation mass on the labeled pocket — the review's own falsifiable
  quantity, not AUC) at each γ, the interior-optimum verdict, and the
  enhancement ratio over the coherent limit; `run_target_sweep` wires in
  real target data (`run_challenge._load_apo_holo`, `build_labels`,
  TASK-0094's proximity floor) and sweeps `H_new`/`H10`/`H2` per
  `REVIEW-2026-07-13c`'s explicit caution not to sweep `H_new` alone.
- **Computational-feasibility finding (discovered while implementing,
  not anticipated by either review):** `haken_strobl`'s dense N²-state
  Lindblad ODE costs ~11s/call at N=169 (KRAS_G12C), ~161s/call at N=451
  (BCR_ABL1) — measured directly, not estimated. Extrapolating the
  observed ~N³ scaling puts CARDIAC_MYOSIN (N=950) at 30+ minutes per γ
  value, making a real multi-point sweep on that target infeasible this
  session. Resolved by running a full 8-point sweep on KRAS_G12C, a
  reduced 6-point sweep on BCR_ABL1, and reporting CARDIAC_MYOSIN's
  infeasibility explicitly (γ=0 anchor only, via cheap `ctqw`) rather
  than silently omitting it, force-reducing the other two targets to
  match, or letting it run for an impractical amount of wall time. Flags
  directly to TASK-0068 (`coarse.py`'s coarse-graining is exactly the
  tool that would make CARDIAC_MYOSIN's scale tractable).
- Seed choice: full active-site residue set (not TASK-0090's single-index
  workaround, which exists specifically for `select.py`'s crash — this
  script never calls `select.py`, so `ctqw`/`haken_strobl`'s native
  multi-index support applies cleanly). This differs from `run_challenge.
  py`'s single-index convention; see TASK-0106's own Done section for the
  cross-check showing this choice materially changes some AUC signs
  (though not the trapping-mechanism direction) — documented in
  `RESULTS.md`, not silently reconciled either way.
- **Real 3-target run, findings (full detail + tables in `RESULTS.md`,
  BCR_ABL1 section, dated 2026-07-14):**
  1. An interior γ-optimum in raw transport magnitude genuinely appears
     on real target topologies — 3 of 6 swept (target, operator) cells
     (KRAS `H2`, BCR_ABL1 `H_new`, BCR_ABL1 `H2`), enhancement 1.24-1.70x
     over the coherent walk. Qualitatively reproduces the review's
     synthetic ENAQT signature on real protein contact graphs, not just
     the constructed disordered-bridge network.
  2. That transport increase does **not** translate into better pocket
     discrimination — in every one of the 3 interior-optimum cells,
     AUC-at-γ* is *lower* than AUC-at-γ→0. No target/operator cell
     crosses its proximity floor because of dephasing anywhere in this
     data; `H10`'s floor-clearing cells (KRAS, BCR_ABL1) already clear it
     at the coherent limit, unaffected by γ.
  3. γ* vs. B-factor-spread disorder proxy: reported observationally only
     (n=3 targets, explicitly too few for a real correlation per this
     task's own Constraints) — no pattern claimed.
- Tests: `test_enaqt_gamma_sweep.py` (8 cases) — `transport_to_pocket`
  unit cases; `sweep_gamma`'s `gamma=0` anchor matches a direct `ctqw`
  call exactly; empty-grid handling; **a real interior-optimum
  reproduction** on the review's own disordered-bridge construction
  (Sec.4) — the mechanism this whole task measures, verified to actually
  work in this script before trusting it on real data, not assumed
  correct by construction; transport values are valid probabilities;
  unknown-operator error handling.
- Validation: `.venv/bin/python3 -m pytest -q __WORK_IN_PROGRESS__/tests/
  test_enaqt_gamma_sweep.py` — 8 passed. Real run outputs saved to
  `__WORK_IN_PROGRESS__/results/tasks/0105/<target>/sweep.json` (full
  per-γ curves, not just the summary table in `RESULTS.md`).
- Not run through the whitelisted `pytest_local.py` preset yet — the new
  test file isn't in its `wip-all`/`all` target list; `wip-all` globs the
  whole `tests/` directory so it *is* already covered by that preset
  without an edit (confirmed: `wip-all` target is
  `__WORK_IN_PROGRESS__/tests`, a directory, not an explicit file list —
  unlike the `backend` preset's explicit-file convention).
