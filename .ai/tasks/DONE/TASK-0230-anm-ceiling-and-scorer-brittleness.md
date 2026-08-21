# TASK-0230 ANM-projected reachability ceiling (§5.2) + scorer-brittleness control (§5.3)

## Context

- ID: TASK-0230
- Title: [[TASK-0227]]'s own §5.2 (oracle-supervised reachability ceiling)
  and §5.3 (scorer-brittleness interpolation control) — deferred there as
  "out of reach... EvoEF2/fpocket not installed," which was itself wrong
  (corrected same-day: both are vendored in-repo,
  `__WORK_IN_PROGRESS__/tools/evoef2/`, `__WORK_IN_PROGRESS__/tools/
  fpocket/`, both verified working). User asked to check, found both
  present, then said "proceed then please" — this task is that follow-up.
- Status: Done
- Resolution: done
- Resolution Note: Ceiling (5.2) fails on all 3 real targets, robust across independent EvoEF2 trials (BCR_ABL1: 6 trials, 0.0-0.335, none cross the 0.5 bar). Scorer-brittleness (5.3) confirmed but richer than flat-vs-cliff -- KRAS shows a genuine cliff missed by the pre-registered proxy, BCR_ABL1 a front-loaded drop, CARDIAC_MYOSIN near-total non-responsiveness. Found+fixed a chain-relabeling bug (latent in TASK-0204's own original code too). Full results in Done section + RESULTS.md.
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: [[TASK-0227]]'s own §5.2/§5.3 (originally the external drop's
  `.ai/reviews/2026-08-21/TASK-0211_anm_rotamer_qubo_reachability.md`),
  user instruction this session.
- Priority: P2 — informative, not blocking; [[TASK-0227]]'s own §5.1
  result already retired the "model-class failure" reading on the
  collective question. This narrows the remaining, smaller, already-
  acknowledged secondary question (local residual / scorer usability).

## Intent Contract

- Outcome: run §5.2 and §5.3 on the same 3 real, corrected target pairs
  TASK-0227 used (KRAS_G12C 4OBE→6OIM, BCR_ABL1 1OPL→5MO4, CARDIAC_MYOSIN
  8QYP→8QYR), against this task's own pre-registered §5.2/§5.3 thresholds
  (stated below, before running), and record the result honestly whichever
  way it lands.
- Why required, not assumed: [[TASK-0227]] itself named these as the next
  two decisive items; they were only skipped for a false tooling reason.
- In Scope:
  - **§5.2, ceiling, with an honest downgrade stated up front**: the
    source's own text asks for repacking "optimally (DEE/A* or Rosetta
    packer for a *global* optimum, not a heuristic)". Neither DEE/A* nor
    Rosetta is available in this environment. `EvoEF2`'s `SideChainRepack`
    (simulated annealing) is this repo's own real, already-validated
    repacker ([[TASK-0204]]) — a strong heuristic, not a global-optimum
    guarantee. **This task's own ceiling number is therefore a heuristic
    ceiling, not the oracle ceiling the source specified** — reported as
    such, not silently upgraded. Method: project the true, common-residue
    apo→holo Cα displacement onto the apo static ANM subspace at k=50
    (matching [[TASK-0227]]'s own k), apply the projected per-residue Cα
    delta as a whole-residue rigid translation (clearly a coarse
    backbone-placement approximation, stated as such — not a refined
    model), restrict to the pocket window ([[TASK-0204]]'s own
    `_select_window`/`_write_full_atom_with_window_chain`), run
    `EvoEF2 --command=SideChainRepack`, score druggability via fpocket
    ([[TASK-0204]]'s own `score_structure`/`_run_fpocket`, reused not
    reimplemented). Compare against native apo and true holo druggability
    at the same window, same fpocket invocation, for scale.
  - **§5.3, scorer brittleness**: linear Cα interpolation apo→holo in 20
    steps (common residue set, same whole-residue rigid-translation
    approximation), fpocket-score druggability at the pocket window at
    each step, for all 3 targets. Classify each target's profile:
    monotone (scorer usable as an optimization objective) vs. flat-then-
    cliff (scorer unusable regardless of search method, per the source's
    own §5.3 framing).
  - Pre-register thresholds before running (source's own convention):
    §5.2 ceiling "passes" if the projected+repacked window's
    `druggability_score` clears the same ≥0.5 bar [[TASK-0204]] already
    established (`DRUGGABILITY_BAR`), and is closer to holo's than to
    apo's; §5.3 "flat-then-cliff" if fewer than 3 of the 19 interpolation
    steps land strictly between the apo and holo scores (a coarse but
    pre-stated monotonicity proxy — refine only if the raw curves make
    this the wrong call, and say so if it does).
- Out Of Scope:
  - A literal DEE/A*/ILP/Rosetta global-optimum repacker — not installed,
    not built here; the heuristic downgrade above is the honest substitute,
    not a silent stand-in for it.
  - Re-deriving anything TASK-0227 already answered (§5.1, §5.4) — reused
    as already-committed facts, not re-run.
  - TASK-0228's own overlapping ceiling/conformer-graph work (actively
    claimed by a different, currently-active thread as of this task's
    filing) — this task stays scoped to TASK-0227's own §5.2/§5.3 wording
    and target set specifically, not a merge with TASK-0228's broader
    framing.
- Constraints And Invariants: read-only against `backend/`'s live
  pipeline (research-tree work only); reuse existing vendored tooling and
  existing scripts' functions where they already do exactly what's
  needed ([[TASK-0204]]'s EvoEF2/fpocket wiring, [[TASK-0227]]'s ANM
  subspace code) — no re-derivation where a validated implementation
  already exists in this repo.
- Planned Validation: real fetched RCSB structures (not mocked); native
  apo and true holo druggability scores computed the same way as the
  projected/interpolated structures, for direct comparison, not asserted
  from memory.

## Done

**§5.2 ceiling: FAILS on all 3 real targets, robustly (multi-trial). §5.3
brittleness: real, but not the shape my own pre-registered proxy metric
could correctly classify — raw curves reported as primary evidence, proxy
verdict shown but explicitly flagged unreliable.**

Script: `__WORK_IN_PROGRESS__/scripts/task0230_ceiling_and_brittleness.py`.
Reused `allostery.superpose.align_apo_holo`/`anm_modes`/
`chain_map_from_config` (this project's own validated Kabsch+ANM+per-role-
chain machinery, not re-derived) and `task0204_rotamer_repack_baseline.py`'s
own `_select_window`/`_run_evoef2`/`score_structure` (EvoEF2+fpocket
wiring). Raw output:
`__WORK_IN_PROGRESS__/results/tasks/0230_ceiling_and_brittleness/results.json`.

**A real bug found and fixed en route**: `_write_contiguous_window_chain`
(adapted from TASK-0204's own `_write_full_atom_with_window_chain`)
hardcoded the window's relabel letter to `'B'`. CARDIAC_MYOSIN's own
`holo_chains=["B"]` collides with that hardcode — relabeling window atoms
to `'B'` when the whole structure is already native chain `'B'` makes
every atom indistinguishable from "window," `other_idx` comes back empty,
and prody's `struct[other_idx]` raises `IndexError` on the empty
selection. Confirmed directly (isolated repro), not guessed. Fixed by
picking a chain letter not already present in the structure, checked not
assumed. **The same defect is latent in TASK-0204's own original
function** — not triggered there only because that script's own two
targets (`KRAS_G12C`, `BCR_ABL1`) both use `apo_chains=["A"]`, never
`"B"`; not fixed there (different, already-Done task, out of this task's
own scope), flagged here for whoever next touches that file.

### §5.2 — heuristic reachability ceiling

Per this task's own Intent Contract, honestly downgraded from the
source's own "DEE/A*/Rosetta global optimum" spec to EvoEF2's
`SideChainRepack` (real simulated annealing, not a global-optimum
guarantee) — reported as such throughout, not silently upgraded.

| target | native apo | true holo (same window) | k=50-projected + EvoEF2-repacked | additional independent repack trials |
|---|---|---|---|---|
| KRAS_G12C | 0.001 | 0.886 | 0.0 / 0.01 (2 trials) | 0.0 (smoke test) — 3 trials, all ≈0 |
| BCR_ABL1 | 0.566 | 0.356 | 0.026 / 0.335 (2 trials) | 0.031, 0.165, 0.159, 0.0 (4 more) — 6 trials total, range 0.0–0.335, **none cross 0.5** |
| CARDIAC_MYOSIN | 0.001 | 0.166 | 0.017 / 0.095 (2 trials) | — |

(fpocket `druggability_score`, TASK-0204's own established ≥0.5 bar.)

**Verdict, against this task's own pre-registered rule** (clears ≥0.5 AND
closer to holo than to apo): **fails on all 3 targets, every trial.**
EvoEF2's time-seeded stochasticity produces real trial-to-trial variance
(BCR_ABL1 spans 0.0–0.335 across 6 independent draws) but never once
approaches the bar — this is a robust negative, not an artifact of one
noisy draw. Even the "best achievable" backbone approximation (the true
collective displacement, kept to only its top-50-ANM-mode component) with
side chains then optimally-heuristically repacked does not open a
druggable pocket on any of the 3 real targets.

**A second, unregistered observation, reported because it's directly
relevant to reading the table above**: `true_holo`'s own druggability at
this exact 12-residue window is not uniformly high either — only
KRAS_G12C's holo clearly reads as druggable (0.886); BCR_ABL1 (0.356) and
CARDIAC_MYOSIN (0.166) both sit *below* fpocket's own 0.5 bar even at the
**real, correct, crystallized-with-ligand** structure. This means the
ceiling failure is not simply "the projection+repack couldn't reach
holo" — for 2 of 3 targets, fpocket's own druggability score does not
strongly recognize the true holo pocket at this specific window either
(a scorer-sensitivity finding, not a distinct one from §5.3 by
coincidence — see below). BCR_ABL1's native, **untouched** apo also
already clears the bar (0.566, higher than its own holo's 0.356) — a
target where "does the ceiling exceed apo" is close to backwards from
what the source document's own framing assumed.

### §5.3 — scorer-brittleness control

Pre-registered proxy rule (`< 3 of 19 mid-steps land strictly between the
apo and holo endpoint scores → "flat-then-cliff"`) was stated up front,
per this task's own Intent Contract, as coarse — **and the raw data shows
it doesn't reliably capture the shape it was meant to detect.** Full
20-step curves in `results.json`; qualitative read of each:

- **KRAS_G12C**: proxy says `monotone_ish` (10/18 between) — **the raw
  curve says otherwise.** Flat at ≈0.001 for steps 0–7 (t=0.00–0.37),
  then a single-step jump to 0.777 at step 8 (t=0.42), then noisy-but-high
  (0.58–0.79, with two anomalous drops to 0.0 at t=0.68 and 0.024 at
  t=0.89) through to holo. **This is the textbook flat-then-cliff shape
  the source document's §5.3 was asking about** — my proxy metric missed
  it because it only checks whether mid-values fall between the two
  endpoints, not whether the transition itself is gradual. Reported as a
  proxy failure, not silently accepted.
- **BCR_ABL1**: proxy says `flat_then_cliff` (2/18 between) and the raw
  curve agrees in spirit, though the shape is a **front-loaded drop**, not
  a single cliff: starts at 0.566 (apo), a sharp fall to ≈0.2 by t=0.21,
  stays low-and-noisy (0.199–0.485) the rest of the way, ending at 0.487 —
  never smoothly approaching holo, several non-monotone reversals.
- **CARDIAC_MYOSIN**: proxy says `monotone_ish` (5/18 between) but this is
  the least meaningful case for the proxy — apo (0.001) and holo (0.005)
  are themselves both near the scorer's effective noise floor, so "5
  midpoints land between 0.001 and 0.005" is not evidence of a smooth
  scorer, it's evidence the entire window barely registers as a pocket at
  any interpolation fraction (max value across all 20 steps: 0.017 at
  t=0.84). A near-flat-at-zero curve with no cliff at all -- a *third*
  brittleness mode neither "monotone" nor "flat-then-cliff" quite
  describes: **scorer non-responsiveness across the whole window**, not
  captured by either label in the source document's own binary framing.

**Verdict**: the source's own concern is confirmed, but the phenomenology
is richer than "flat-then-cliff vs. monotone" — one genuine cliff
(KRAS_G12C, missed by the pre-registered proxy), one front-loaded drop
with noisy non-monotone recovery (BCR_ABL1, proxy agreed), and one
near-total non-responsiveness (CARDIAC_MYOSIN, proxy's "pass" is not
informative). **fpocket's druggability score is not a safe, smooth
optimization objective on any of the 3 real targets** — consistent
regardless of which of the three shapes a given target shows, and
consistent with §5.2's own second observation above (fpocket
under-recognizing 2 of 3 targets' true holo pockets at this window).

### Cross-cutting

Both experiments point the same direction: **not a search-depth problem,
not solely a modeling-fidelity problem** — even supplied the real
collective displacement (top-50-mode-projected) and a real optimal-
heuristic repack, druggability does not reliably open, and the scorer
used to judge it is itself unreliable near the transition on 2 of 3
targets. This is consistent with [[TASK-0227]]'s own §5.1 finding
(collective motion IS reachable) plus the source document's own §6.1
diagnosis (local backbone rearrangement, not spanned by ANM collective
modes OR side-chain repacking alone, is what's missing) — this task's
own data is a second, independent line of evidence for that same
diagnosis, not a contradiction of TASK-0227's §5.1.

**Not done, stated per this task's own Out Of Scope**: a literal DEE/A*/
ILP/Rosetta global-optimum repacker (not installed, not built here); any
change to TASK-0228's own separate, still-active work.
