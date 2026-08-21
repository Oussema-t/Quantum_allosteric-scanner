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
- Status: Done (2026-07-25) — falsification statement fires: dcc_low's significance removed on both CARDIAC_MYOSIN and PTP1B under the compact null
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

- [x] Build `compact_patch(...)`, with optional radius-of-gyration
      matching; unit test against `null_audit.py`'s own reproduced
      inflation numbers.
- [x] Re-run [[TASK-0149]]'s real-target `dcc_low`/`prs_low` stratified
      nulls under the corrected draw.
- [x] Re-run [[TASK-0151]]'s generalization-set check under the
      corrected draw.
- [x] Re-run [[TASK-0142]]'s H2 matched-spread null under the corrected
      draw.
- [x] Re-run [[TASK-0133]]/[[TASK-0139]]'s learnability patch-control
      null under the corrected draw.
- [x] Re-run [[TASK-0152]]'s CARDIAC_MYOSIN/GLUCOKINASE null under the
      corrected draw (TASK-0152 confirmed Done, unclaimed, before
      starting — no coordination conflict).
- [x] Evaluate (state reasoning, don't skip silently) whether
      [[TASK-0145]]'s transport null is exposed to the same defect. —
      Yes, more severely (7.0x/242x vs 4.8x/42x); NOT re-run itself,
      per this task's own Out Of Scope.
- [x] Write and answer the pre-registered falsification statement
      (§5.3) explicitly in `RESULTS.md`.
- [x] `RESULTS.md` section: side-by-side scattered-vs-compact table for
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

**Headline: the pre-registered falsification statement (§5.3) fires. Under the
corrected null, `dcc_low`'s Bonferroni-significance is removed on both
CARDIAC_MYOSIN and PTP1B — the review's own pre-declared condition for reporting
this program's strongest observable family as a negative result. Additionally,
direct empirical check finds TASK-0145's transport null (explicitly Out of Scope
for re-running here) is exposed to the SAME defect, more severely, not exempt as
its own construction might suggest.**

### `compact_patch` built and validated

New `src/allostery/nulls.py`: `compact_patch(coords, size, rng)` (ported verbatim
from `null_audit.py`'s own reference implementation — nearest-Euclidean-neighbours
of a random seed residue), `compact_patch_from_pool` (pool-restricted variant, a
drop-in replacement for this project's prior `rng.choice(pool, size, replace=False)`
convention wherever seed/active-site residues are excluded from the draw), and
`compact_patch_matched` (radius-of-gyration-matched rejection sampling, the
review's own suggested extension, mirroring `closure.matched_spread_null`'s
established convention). 9 new tests (`tests/test_nulls.py`), including a direct
reproduction of `null_audit2.py`'s own 4.8x inflation number (confirmed: >3x,
matches) and confirmation that a **compact-vs-compact** comparison (the actual
fix) restores near-nominal calibration on the identical `dcc_low` smooth-field
case that showed the inflation — 1.36x at α=0.05, 0x at α≤0.0083 (2000/500
replicates), vs. 4.8x–42x for scattered-vs-compact.

### Every named task re-run under the corrected null, side by side (additive)

New `scripts/compact_null_rerun.py` reuses each family's own already-established
scoring machinery unmodified (`prs_low`/`dcc_low`, `void_score`,
`restricted_cumulative_overlap`) — only the null-draw step changes, computed both
ways per cell so the delta is visible, not just the corrected number in isolation.
Full detail: `results/tasks/0158_compact_null/compact_null_rerun.json`.

**Lowmode (TASK-0149 + TASK-0151's own generalization-set targets, 5 targets × 2
observables × 4 k_modes = 40 cells):**

| Target | `dcc_low` best k | scattered p (as reported) | compact p (corrected) |
|---|---|---|---|
| CARDIAC_MYOSIN | k=20 | 0.000 | **0.060** |
| CARDIAC_MYOSIN | k=10 | 0.004 | 0.137 |
| PTP1B | k=10 | 0.001 | **0.019** |
| PTP1B | k=15 | 0.001 | 0.059 |
| KRAS_G12C | any k | 0.788–0.999 | 0.795–0.968 (never close) |
| BCR_ABL1 | any k | 0.780–0.928 | 0.603–0.660 (never close) |
| CASPASE7 | any k | 0.135–0.376 | 0.282–0.424 (never close) |

`prs_low` shows the identical pattern (CARDIAC_MYOSIN scattered p=0.001–0.006 →
compact p=0.104–0.126; never significant anywhere else either way).

**Answering the pre-registered falsification statement directly**: CARDIAC_MYOSIN's
`dcc_low` no longer clears even *uncorrected* α=0.05 at any k under the compact
null (min 0.060) — its Bonferroni-survival (against TASK-0149's own 6-comparison
bar, α=0.00833) is unambiguously gone. PTP1B's `dcc_low` at k=10 (p=0.019) still
clears uncorrected α=0.05 but not TASK-0151's own 16-comparison Bonferroni bar
(α=0.00313) — its Bonferroni-survival is also gone. **Read against the standard
both findings were originally reported under (Bonferroni-surviving), the
falsification statement's condition — "removes `dcc_low`'s significance on both
CARDIAC_MYOSIN and PTP1B" — is met.** PTP1B's k=10 cell is the one place a hint
survives uncorrected scrutiny; everywhere else, nothing does.

**Persistent H2 (TASK-0142, 3 targets):** all 3 already sat well short of
significance under the scattered null (p=0.229/0.537/1.000); the compact null
weakens every one further (p=0.486/0.353/0.777) — reinforces the existing FAIL
verdict, does not change it.

**Learnability patch control (TASK-0133/TASK-0139/TASK-0152, 4 targets):**
scattered-null numbers reproduced exactly as originally reported (KRAS_G12C
93.0th/p=0.070, CARDIAC_MYOSIN 85.7th/p=0.143, GLUCOKINASE 89.9th/p=0.101,
BCR_ABL1 37.3rd/p=0.627 — confirms this re-run's own methodology is faithful).
Under the compact null every percentile softens further (KRAS_G12C 65.7th/p=0.343,
CARDIAC_MYOSIN 73.8th/p=0.262, GLUCOKINASE 83.3rd/p=0.167, BCR_ABL1 29.3rd/p=0.707)
— none were ever significant at α=0.05 even under the biased scattered null, so
this reinforces the existing `AMBIGUOUS`/non-decisive readings, does not flip any
verdict.

### Transport (TASK-0145): evaluated as instructed, NOT re-run (Out of Scope) — found MORE exposed, not exempt

Direct empirical check (this task's own Open Question, resolved): built
`transport.transmission_from_source(L, source, E=0.0)` on `null_audit.py`'s own
globule fixture and ran the identical scattered-vs-compact comparison on the
**whole-graph AUC** construction transport actually uses (no stratification).
**Result: 7.0x inflation at α=0.05, rising to 242x at α=0.001 — worse than the
stratified construction's 4.8x/42x, not exempt from the defect as the
non-stratified construction might suggest.** Mechanism: the stratified/
well-powered-max construction actually provides *some* protection (controlling
for hop-distance shell removes part of the spatial-autocorrelation problem); a
plain whole-graph AUC has no such protection and is fully exposed. **Per this
task's own Out-Of-Scope, TASK-0145's own real BCR_ABL1 finding (`T(E=0)` on L,
p=0.003) is NOT re-run here** — this is a live, real, and now more urgent
open item than the filing text anticipated, flagged explicitly for a follow-up
task rather than silently addressed beyond this task's own stated scope.

### Radius-of-gyration matching (Open Question, resolved)

`compact_patch_matched` built and tested (rejection sampling, ±35% tolerance
matching `closure.matched_spread_null`'s own default) — not applied to the
production re-runs above, since none of the 6 named dependent tasks' own original
null constructions matched pocket shape/spread in the first place (matching
`compact_patch`'s own unmatched draw to each task's own prior, unmatched
convention keeps the comparison apples-to-apples: "same construction, corrected
geometry," not "corrected geometry plus a new constraint no one asked for").
Available for a future task that wants it.

**Full test suite**: 950 passed, 2 xfailed, 0 failed.
