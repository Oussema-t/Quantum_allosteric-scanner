# TASK-0188 Spatial contact-graph hop-cutoff robustness sweep

## Context

- ID: TASK-0188
- Title: check whether TASK-0186's per-target hop-distance findings (and
  TASK-0177's C6 distality criterion, which reuses the same metric) are
  stable across the contact-graph cutoff, or are themselves a knob-choice
  artifact inherited from a benchmark that was never testing this question.
- Status: Done
- Owner: Implementer
- Claimed By: Architect -- reserved for drafting only, release/re-claim via
  `claim.py` when a thread actually starts the run
- Claimed At: 2026-08-01 09:09
- Source: orchestrating collaborator (Bartosz), 2026-08-01: *"have the
  numbers like 4.5A, 8A for cutoffs been empirically (or any other
  non-arbitrary way) arrived at?"* -- investigation for that question
  (recorded in TASK-0186/COMMON.md) found the 8.0 A contact-graph cutoff
  used by both TASK-0186 and TASK-0177's C6 was benchmarked once
  (TASK-0067), but for a **different metric** (GNM-eigendecomposition AUC)
  over a **narrower, higher range** (7.5/8.0/10.0 A only) than what
  TASK-0186 actually needs it for (BFS hop-count / distality). No task has
  checked whether hop-count-based findings are cutoff-robust.
- Priority: **P1.** Cheap (no new machinery -- `hop_from_seed`/
  `contact_matrix` already take `cutoff` as a parameter, this is a sweep
  script, not new code) and directly de-risks two just-shipped/in-flight
  results: TASK-0186's per-target hop distributions (in `RESULTS.md` row
  47) and TASK-0177's C6 (still being built).
- Suggested Follow-Up: **[[TASK-0182]]**, same thread. No dependency at all
  (fully independent hardware/resource work) -- suggested purely as a
  sequencing convenience: this task is small and fast, a good first pick
  for a newly spun-up thread before moving to 0182's larger, multi-day
  scope. Recorded 2026-08-01 (Architect).

## Why this matters -- the 8.0 A hop-graph cutoff was never actually tested for this

TASK-0067 swept {7.5, 8.0, 10.0} A and scored via classical heat-kernel AUC
against the pocket label -- it found "no significant difference in the
tested range" and 8.0 A was retained on that basis. TASK-0186 and TASK-0177's
C6 both then reused 8.0 A **for a structurally different metric** (BFS
hop-count / distality) that TASK-0067 never scored at all, and neither
tested cutoffs below 7.5 A. This is exactly the "reuse an existing constant
without re-deriving it" pattern this project's own conventions warn about
([[TASK-0180]]'s Constraints: *"No new geometric constant without
derivation"*) -- except in reverse: an *existing* constant, derived for one
purpose, silently inherited for a structurally different one.

This is not a hypothetical concern. TASK-0114 already found the sibling
4.5 A pocket-label cutoff sits on "a still-moving slope, not a stable
plateau" at the residue-set level even though downstream verdicts were
comparatively stable -- and TASK-0075's cumulative-overlap gate is a
concrete precedent for a similarly-shaped threshold flipping verdicts
15/18 times across a grid. A hop-count metric is, if anything, *more*
sensitive to cutoff than a continuous AUC score: dropping one edge near
the active site can change a residue's hop-count by a full integer, not a
smooth fraction. **TASK-0186's most striking number -- CASPASE1 at 83% of
its pocket within 1 hop, worse than KRAS_G12C -- is exactly the kind of
result that should not be trusted until it survives a cutoff sweep.**

## Intent Contract

- Outcome: for each of the 7 pocket-scoreable targets, spatial-hop
  distributions (min/median/frac<=1/frac<=2, same statistics TASK-0186
  already reports) at a small cutoff grid -- recommend {6.0, 6.5, 7.0, 7.5,
  8.0, 8.5, 9.0} A, extending *below* TASK-0067's tested floor of 7.5 A as
  well as slightly above 8.0 A. Reported as a per-target sensitivity table,
  plus an explicit statement of which (if any) of TASK-0186's headline
  claims (the 6/7 min-hop=1 finding; CASPASE1's 83%; PTP1B's 0%) survive
  unchanged across the grid.
- Why required, not assumed: 8.0 A has real benchmark backing for AUC-based
  GNM scoring (TASK-0067); it has **zero** backing for hop-count-based
  distality, which is a different question asked of the same graph.

- In Scope:
  - `scripts/hop_distance_cutoff_sweep.py` -- reuses
    `hop_distance_generalization_audit.py`'s already-working target-loading
    code (`_load_apo_holo`, `build_labels`) verbatim, sweeping only the
    `cutoff` argument to `hop_from_seed`. No source-code changes anywhere
    -- `hop_from_seed`/`contact_matrix` already accept `cutoff` as a
    parameter (confirmed directly before filing this task).
  - Connectivity check per cutoff (a real risk at low cutoffs in
    principle): confirmed on KRAS_G12C before filing that the graph stays
    a single connected component with zero isolated nodes from 5.0 A
    upward (backbone-adjacent Cα pairs at ~3.8 A guarantee this) --
    re-verify this holds on the larger/sparser targets (CARDIAC_MYOSIN,
    N=704) too, don't assume KRAS_G12C's result generalizes.
  - Report against the incumbent label, same caveat as TASK-0186 (must
    re-run against TASK-0177's consensus label once available).

- Out Of Scope:
  - Changing the shipped 8.0 A default anywhere in production code --
    characterization only, same posture TASK-0067/TASK-0114 took for their
    own cutoffs.
  - The 4.5 A pocket-label cutoff -- already covered by TASK-0114 (Done,
    4.0-5.5 A) and TASK-0177's own planned C1 (3.5-6.0 A, in progress).
    Do not duplicate that sweep here.
  - Re-deriving TASK-0067's AUC-based finding -- this task is hop-count
    only, a different scoring question on the same graph.

- Constraints And Invariants:
  - No new geometric constant invented -- the grid brackets the existing
    7.5/8.0/10.0 A values already in use, extended only as far as the
    connectivity check supports.
  - Reuse the exact target-loading path TASK-0186 validated (sanity-checked
    against TASK-0169), not a re-derivation.

- Planned Validation:
  - Connectivity check per cutoff per target (not just KRAS_G12C) --
    blocking if any target fragments at a tested cutoff; report and
    exclude that cutoff for that target rather than silently proceeding
    on a disconnected graph.
  - Cross-check: the 8.0 A row of this sweep must reproduce TASK-0186's
    already-published numbers exactly (same code path, same label) -- a
    regression check on this task's own script, not a new finding.

## In Progress

None

## TODO

- [x] Connectivity check across all 7 targets at the low end of the grid
      (not just KRAS_G12C, done above). All 7 targets stay a single
      connected component, zero isolated nodes, across the entire 6.0-9.0 A
      grid -- including CARDIAC_MYOSIN (N=704), the largest/sparsest target.
      No cutoff had to be excluded.
- [x] Sweep script, reusing TASK-0186's loader.
      `scripts/hop_distance_cutoff_sweep.py` -- imports `TARGETS`,
      `DEFAULT_POCKET_CUTOFF`, `_load_apo_holo` from
      `hop_distance_generalization_audit.py` verbatim, no re-derivation.
- [x] Run across all 7 targets x 7 cutoffs.
      `results_task0188_hop_cutoff_sweep/results.json`.
- [x] 8.0 A row cross-check against TASK-0186 (must match exactly).
      Confirmed bit-for-bit on all 7 targets (min/mean/median/max/
      frac_le_1/frac_le_2/frac_le_3).
- [x] State explicitly which TASK-0186 headline claims survive the sweep
      and which don't. See RESULTS.md row 48 / Done section below.
- [x] `RESULTS.md` entry (new row, append-only, cross-referencing row 47).
      Row 48.
- [ ] **Follow-up (blocked on TASK-0177):** re-run against the consensus
      label once available.

## Dependency

- [[TASK-0186]] (Done) -- the finding this stress-tests; script reused
  directly.
- [[TASK-0067]] (Done) -- the 8.0 A value's original (differently-scoped)
  benchmark.
- [[TASK-0177]] -- soft, for the eventual re-score against the consensus
  label.

## Open Questions

- Does this also matter for TASK-0187's shortcut hypothesis (which reuses
  the same 8.0 A hop metric for its Step 2/3 measurements)? Yes in
  principle -- flag for TASK-0187 to cross-check its own headline finding
  against this task's grid once both exist, not blocking either task on
  the other.
- Should the grid extend above 10.0 A too, matching TASK-0067's own upper
  bound? Lower priority -- the concerning direction is downward (a sparser
  graph inflates hop-counts, which would *understate* triviality, the
  opposite of TASK-0186's concern); recommend a light upper check (10.0 A)
  but focus the grid below 8.0 A.

## Done

- 2026-08-01 (Implementer D): built `scripts/hop_distance_cutoff_sweep.py`,
  ran all 7 pocket-scoreable targets x {6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0} A,
  results in `results_task0188_hop_cutoff_sweep/results.json`, written up as
  `RESULTS.md` row 48.
  - **Connectivity**: single connected component, zero isolated nodes, on
    all 7 targets at every tested cutoff, including CARDIAC_MYOSIN (N=704).
    No exclusions needed.
  - **8.0 A regression check**: bit-for-bit match against TASK-0186's
    published `results_task0186_hop_distance_audit/results.json` on all 7
    targets, all statistics.
  - **Headline-claim survival, per the pre-existing Intent Contract
    question**:
    - "6/7 targets have min spatial-hop = 1" -- **cutoff-fragile**. Only
      true for cutoff >= 8.0 A. BCR_ABL1's min hop is 2 (not 1) at every
      tested cutoff <= 7.5 A, so below 8.0 A it is 5/7, not 6/7. Every other
      target's min-hop=1/PTP1B's min-hop=2 status is stable across the
      whole grid.
    - CASPASE1's "83% at hop<=1" -- **magnitude cutoff-fragile, ranking
      robust**. The 83% figure only holds at cutoff >= 7.5 A; it is 50% at
      6.0 A and 67% at 6.5-7.0 A. CASPASE1 is nonetheless the single
      highest-frac<=1 target at every tested cutoff (i.e. "more trivial
      than KRAS_G12C" survives as a ranking claim even though the point
      estimate does not).
    - PTP1B's "0% at hop<=1" -- **fully robust**. Exactly 0.0 at all 7
      tested cutoffs -- the strongest non-trivial-target claim in row 47
      is also the one cutoff choice cannot manufacture or erase.
  - Practical implication for downstream consumers ([[TASK-0177]]'s C6,
    [[TASK-0187]]'s shortcut-hypothesis Step 2/3, which reuse the same
    8.0 A hop metric): treat the exact "6/7" count and CASPASE1's "83%" as
    `cutoff=8.0A`-conditional numbers, not target-intrinsic ones; PTP1B's
    non-triviality and CASPASE1's relative-worst-case ranking can be stated
    without that qualifier.
  - Follow-up item (re-score against TASK-0177's consensus label) left open
    below, blocked on that task as noted.
