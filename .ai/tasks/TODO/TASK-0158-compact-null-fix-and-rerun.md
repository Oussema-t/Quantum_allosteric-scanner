# TASK-0158 Fix the anti-conservative permutation null (compact vs. scattered) and re-run every affected result

## Context

- ID: TASK-0158
- Title: `PANEL_REVIEW_2026-07-25.md` §2.3 (the review's single most
  consequential finding, with an attached, reproduced-in-repo executed
  audit — see `scripts/null_audit.py`/`null_audit2.py`) demonstrates that
  every permutation null in this project draws a uniformly **scattered**
  same-size subset (`rng.choice(N, size=pocket_size, replace=False)`),
  but real pockets are spatially **compact**. On the project's own
  `dcc_low`/`prs_low` machinery, this makes the null anti-conservative by
  **4.8× at α=0.05, rising to 42× at α=0.001** — with a white-noise
  negative control confirming the effect is real (0× inflation) and
  specific to smooth spatial score fields interacting with compact
  labels, not a test-construction artifact.
- Status: TODO
- Owner: Implementer
- Claimed By: Implementer A (this thread)
- Claimed At: 2026-07-25 10:21
- Source: `PANEL_REVIEW_2026-07-25.md` §2.3/W1, `null_audit.py`/
  `null_audit2.py` (relocated to `scripts/`, re-verified running in this
  session — see commit message for the exact reproduced numbers).
  [[TASK-0143]] independently discovered the underlying fact ("real
  pockets are far more compact than random same-size subsets") in
  2026-07-22 but never connected it to the *other* nulls in the program
  — this task is that connection, made explicit and acted on.
- Priority: **P0.** Per the review's own pre-registered framing (§5.3):
  *"If a spatially-matched compact null removes `dcc_low`'s significance
  on both CARDIAC_MYOSIN and PTP1B, we report the program as a complete
  negative result... not a predictor."* This decides whether the
  submission has a positive to report at all — every other analysis
  decision and the entire write-up depend on the answer. Do this first.

## Intent Contract

- Outcome: a `compact_patch(coords, size, rng)` null-draw function
  (4-line reference already in `null_audit.py` — nearest-neighbour draw
  from a random seed residue; add radius-of-gyration matching as a
  documented option, per the review's own "optionally match the real
  pocket's radius of gyration" note) lands in `src/allostery/` (natural
  home: alongside `baselines.py` or a new small module — Implementer's
  own call, state the reasoning), replacing the scattered
  `rng.choice(...)` draw **wherever a null is used to certify a positive
  result**, and every affected task's headline number is re-run and
  re-reported under the corrected null, additively (superseded numbers
  preserved, not overwritten — this project's own established
  discipline, TASK-0150's own recent precedent for what NOT to falsely
  claim about preservation).
- Why required: the review's own pre-registered falsification statement
  (§5.3) makes this the load-bearing prerequisite for every claim the
  6-pager could make about a surviving positive result.
- In Scope:
  - New compact-draw null function, tested against `null_audit.py`'s own
    reproduced numbers (a regression test: the corrected null should
    show ~0× inflation on the white-noise control, matching the audit).
  - Re-run, under the corrected null, **every task the review names**:
    [[TASK-0149]] (`dcc_low`/`prs_low` real-target), [[TASK-0151]]
    (generalization-set check), [[TASK-0142]] (H2 half's own
    matched-spread null), [[TASK-0133]]/[[TASK-0139]] (learnability
    patch control), [[TASK-0152]] (CARDIAC_MYOSIN/GLUCOKINASE
    learnability null).
  - Report each affected headline number under both nulls side by side
    — scattered (as originally reported) and compact (corrected) — so
    the delta is visible, not just the corrected number in isolation.
  - Explicitly test and report the pre-registered falsification
    statement's own two named cells: does `dcc_low`'s significance
    survive on CARDIAC_MYOSIN **and** PTP1B under the compact null.
- Out Of Scope:
  - Re-deriving any observable's own scoring logic — only the null
    changes.
  - [[TASK-0145]]'s transport results — those use a **scattered**,
    whole-graph null (not the stratified/well-powered-shell-max
    construction the review's audit specifically targets); re-derive
    whether the same defect applies before assuming it does (state the
    reasoning either way, don't silently skip or silently include it).
- Constraints And Invariants:
  - Superseded (scattered-null) numbers preserved in `RESULTS.md`, not
    deleted — same discipline as every prior gauge correction this
    project has made (TASK-0118→0130→0124, per the review's own §2.1
    praise for exactly this pattern).
  - The corrected null must be validated against the white-noise
    negative control before being trusted on any real result (per the
    audit's own methodology — confirms the fix targets the right
    mechanism, not just changes the number).
- Planned Validation: `null_audit.py`'s own reproduced inflation table,
  re-run against the *corrected* null (expect ~1× at every α, matching
  the white-noise-control row); then each of the 5 dependent tasks'
  headline verdict re-reported, flagged PASS/FAIL/DOWNGRADED explicitly.

## TODO

- [ ] Build `compact_patch(...)`, with optional radius-of-gyration
      matching; unit test against `null_audit.py`'s own reproduced
      inflation numbers.
- [ ] Re-run [[TASK-0149]]'s real-target `dcc_low`/`prs_low` stratified
      nulls under the corrected draw.
- [ ] Re-run [[TASK-0151]]'s generalization-set check under the
      corrected draw.
- [ ] Re-run [[TASK-0142]]'s H2 matched-spread null under the corrected
      draw.
- [ ] Re-run [[TASK-0133]]/[[TASK-0139]]'s learnability patch-control
      null under the corrected draw.
- [ ] Re-run [[TASK-0152]]'s CARDIAC_MYOSIN/GLUCOKINASE null under the
      corrected draw (coordinate with whichever thread is running
      TASK-0152 itself — don't duplicate work, check its Done status
      first).
- [ ] Evaluate (state reasoning, don't skip silently) whether
      [[TASK-0145]]'s transport null is exposed to the same defect.
- [ ] Write and answer the pre-registered falsification statement
      (§5.3) explicitly in `RESULTS.md`.
- [ ] `RESULTS.md` section: side-by-side scattered-vs-compact table for
      every re-run cell.

## Dependency

- [[TASK-0149]], [[TASK-0151]], [[TASK-0142]], [[TASK-0133]],
  [[TASK-0139]], [[TASK-0152]] (all Done or in-flight) — the results this
  task re-tests, not re-derives.
- [[TASK-0143]] (Done) — the original, independent discovery of pocket
  compactness this task generalizes.
- `scripts/null_audit.py`/`null_audit2.py` — the reproduced audit and
  reference `compact_patch()` implementation.

## Open Questions

- Whether [[TASK-0145]]'s transport observables (whole-graph AUC,
  scattered null, no stratification) are exposed to the same
  spatial-autocorrelation mechanism, or whether the mechanism is
  specific to the stratified/well-powered-shell-max construction the
  audit tested — resolve by direct check (run the audit's own
  methodology against `transport.T_E`'s score field), don't assume
  either way.
- Radius-of-gyration matching: exact matching tolerance, and whether it
  meaningfully changes the corrected null's own distribution relative to
  the simpler nearest-neighbour draw — characterize, report either way.

## Done

(not yet)
