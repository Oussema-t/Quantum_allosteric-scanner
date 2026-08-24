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

## Addendum — the stronger (full-displacement) ceiling + a geometry-sanity
check, requested by the user after reviewing the above (2026-08-21)

User's follow-up, verbatim in spirit: is the §5.2 negative real, or did we
under-power it (only k=50 modes, never the full true displacement) — and
does the rigid-per-residue-translation approximation itself produce
structures EvoEF2/fpocket can actually trust? Both real, unanswered gaps
this task's own first pass left open. Addressed directly, not deferred
again.

**Method**: `run_5_2_stronger` (same script, extended) — the FULL,
untruncated true apo→holo displacement (not k=50-projected) as the same
rigid per-residue translation, then EvoEF2 `SideChainRepack` (4
independent trials per target, matching the robustness discipline already
used for BCR_ABL1), fpocket-scored. Added `_compute_stability` (EvoEF2
`ComputeStability`, parses `Total` energy and `interS_vdwrep` — steric
repulsion, the direct clash signal) at native apo, the k=50-projected
pre-repack structure, the full-displacement pre-repack structure, and
each post-repack trial — the geometry-sanity check the first pass didn't
run.

| target | native apo `vdwrep` | k=50 pre-repack `vdwrep` | full pre-repack `vdwrep` | full pre-repack druggability | post-repack `vdwrep` (mean) | post-repack druggability (4 trials) |
|---|---|---|---|---|---|---|
| KRAS_G12C | 84.1 | 399.2 (4.7×) | **1014.8 (12.1×)** | 0.79 (crosses bar) | ≈524.9 (6.2×) | 0.129, 0.247, 0.247, 0.214 |
| BCR_ABL1 | 300.1 | 511.0 (1.7×) | 876.0 (2.9×) | 0.487 | ≈906.4 (3.0×) | 0.23, 0.432, 0.23, 0.432 |
| CARDIAC_MYOSIN | 335.6 | 585.4 (1.7×) | 1014.3 (3.0×) | 0.005 | ≈1042.9 (3.1×) | 0.21, 0.12, 0.004, 0.169 |

**Finding, and it's the load-bearing one: the full-displacement structure
is severely clash-distorted before anyone even looks at druggability** —
3–12× native apo's own steric repulsion energy, worst on KRAS_G12C, whose
pre-repack druggability (0.79, crosses the bar) is exactly the target
with the worst clash (12.1×). That "positive" reading is far more likely
a geometric artifact — a badly overlapping, non-physical cavity that
fpocket's geometric detector mistakes for an open pocket — than a real
signal, and treating it as evidence the pocket "opens" would be a
mistake. EvoEF2's `SideChainRepack` (side chains only, no backbone
relaxation) recovers *some* of the clash (KRAS: 1014.8→524.9) but never
gets close to native apo's own relaxed state (84.1) on any target — a
real backbone-torsion-level distortion from the rigid-translation
approximation that side-chain repacking alone cannot fix.

**Answering the user's two questions directly**:
- *Did we under-power it?* Yes, partially — but supplying the full
  displacement instead of k=50 modes did **not** flip any target to a
  clean positive. All 12 repacked trials (4 × 3 targets) stayed below the
  0.5 bar (closest: BCR_ABL1, max 0.432). The "positive" pre-repack
  readings are the clash artifact described above, not evidence the
  under-powering was hiding a real signal.
- *Is the rigid-translation approximation trustworthy enough to believe
  either a positive or a negative from it?* **No — confirmed directly,
  not merely suspected.** Every displaced structure, before or after
  repacking, sits 1.7×–12× above native apo's own steric-repulsion energy.
  The ceiling experiment (both the original k=50 version and this
  stronger one) is confounded by its own backbone-placement method:
  a negative from this pipeline is genuinely ambiguous between "the
  pocket doesn't open" and "our backbone approximation is too crude to
  tell." Reported as an open confound, not resolved here — the honest
  next step (not attempted, real scope, real tooling gap) would be a
  torsion-based or energy-minimized backbone placement instead of a
  rigid whole-residue translation, before this ceiling question can be
  answered cleanly.

**Bearing on Phase 2 plausibility (the user's own framing — "any Phase 2
plausibility relies on SOME working approach")**: this task's own data,
across both passes, does not supply a working approach at the pocket-
opening/repacking layer — every variant tried here, generous or not,
stays negative or produces an artifact rather than a trustworthy
positive. [[TASK-0227]]'s own §5.1 result (collective apo→holo motion IS
well-captured by a *static, non-adaptive* low-mode subspace, 0.58–0.90
overlap on real targets, no rigid-translation step involved, no
repacking involved — a cleaner, less confounded method than anything in
this task) remains the strongest positive evidence in the program for
the "collective part is reachable" half of the question. This task's own
data narrows, rather than closes, the *local* half: not "closed," but
"not shown open by any method tried here, and the method itself is not
yet trustworthy enough to fully believe that negative."

## Addendum 2 — a real energy calculation, tested directly: does
minimization itself explain the closed result? (2026-08-22)

User's own follow-up: can a real energy calculation help interpret these
structures, and would that help the actual challenge? Answer: yes to
both, tested directly rather than argued abstractly — and it surfaces
real, target-dependent signal, not a uniform effect.

**Method**: EvoEF2 `RepairStructure` (a lighter-touch, whole-structure
side-chain adjustment pass — flips/rotates residues to optimize hydrogen
bonds, distinct from `SideChainRepack`'s full simulated-annealing energy
minimization) run on the full-displacement pre-repack structure, scored
both alone and followed by a window-focused `SideChainRepack`, using the
same `_compute_stability`/`score_structure` machinery as Addendum 1.

| target | full-displ. pre-repack (raw) | + RepairStructure alone | + RepairStructure → SideChainRepack |
|---|---|---|---|
| KRAS_G12C | 0.79 (`vdwrep` 1014.8) | **0.726** (`vdwrep` 297.0) | 0.004 (`vdwrep` 285.7) |
| BCR_ABL1 | 0.487 (`vdwrep` 876.0) | 0.032 (`vdwrep` 523.2) | 0.325 (`vdwrep` 551.9) |
| CARDIAC_MYOSIN | 0.005 (`vdwrep` 1014.3) | 0.001 (`vdwrep` 623.8) | 0.0 (`vdwrep` 757.2) |

**Real, target-dependent signal, not a uniform pattern — reported as
such, not oversold.** Only KRAS_G12C shows the effect cleanly: a
lightly-relaxed state (`RepairStructure` alone, `vdwrep` down 3.4× from
raw but still ~3.5× native apo) stays apparently open (0.726), and
*only once side chains are genuinely energy-minimized* (`SideChainRepack`,
real simulated annealing) does the pocket collapse (0.004) — at
essentially the same clash level as the `RepairStructure`-alone state
(285.7 vs 297.0 `vdwrep` — barely different), so the closure tracks
**which rotamers get chosen**, not just how relaxed the structure is.
BCR_ABL1 and CARDIAC_MYOSIN never show strong openness at any relaxation
level, consistent with (not a new instance of) the earlier finding that
fpocket doesn't strongly recognize even their *true holo* structures at
this window — the scorer-sensitivity caveat from the main Done section,
not a new confound.

**Why this is directly relevant to the challenge, not just to this
task's own methodology**: KRAS_G12C's own pattern — an unrelaxed or
lightly-relaxed state reads as open, a genuinely energy-minimized one
reads as closed, at comparable clash levels — is a real-target,
directly-measured instance of the source document's own §6.1 diagnosis:
**"QUBO returns a minimum; cryptic pockets are excited states... 
minimising energy over backbone⊕rotamers returns the apo structure."**
That was a theoretical objection in the source document; this is one
real target where it's now an observed result, not just an argument.
**Bearing on a QUBO/quantum-optimization formulation**: if the
optimization objective is bare energy minimization over rotamers (or
rotamers+backbone), it will systematically return the closed state —
matching exactly what was measured here — regardless of whether the
solver is classical or quantum, and regardless of solver quality. A
quantum speedup on the *wrong* objective is not a path to a working
approach. The source document's own proposed fix (§6.1: score = minimum
energy cost to open a druggable pocket at site j, a constrained
formulation with a pocket-volume term, not bare minimization) is the
one this result actually argues for — and remains untested here, real
scope, not attempted in this task.

**What this does not resolve**: `RepairStructure` is still a side-chain-
only adjustment (its own log output: "we optimize side chain of residue
..." for every residue) — no backbone/torsion relaxation happens at any
point in this addendum. The core confound from Addendum 1 (crude rigid-
translation backbone placement, `vdwrep` still 3–7× native apo even
after the best relaxation tried here) stands, unresolved, on all 3
targets.

## Addendum 3 — [[TASK-0235]]'s backbone-placement fix updates this task's
own "ceiling fails on all 3 targets" verdict per target, not as a block
(2026-08-24)

[[TASK-0235]] built the fix Addendum 1/2 both named as the real remaining
gap (a local-sliding-window-Kabsch backbone placement instead of rigid
per-residue translation) and re-ran this task's own ceiling experiment
with it. Result is real but sharply target-dependent, not a blanket
reversal — recorded here so this task's own verdict isn't read as still
current where it no longer is:

- **BCR_ABL1: reversed.** Every one of 4 post-repack trials now clears
  the 0.5 druggability bar (0.656–0.725) — this task's own original
  finding (max 0.432, 0/4) was an artifact of the rigid-translation
  backbone confound this addendum already flagged as unresolved, not
  evidence the pocket doesn't open.
- **CARDIAC_MYOSIN: partially reversed.** 1 of 4 trials now clears the
  bar (0.603, previously max 0.21) — a real but noisy signal, not a
  clean flip.
- **KRAS_G12C: unchanged, and now independently explained, not just
  observed.** Still 0/4 with the corrected backbone method.
  [[TASK-0235]]'s own harmonic local-residual ΔG estimate (extending
  [[TASK-0233]]'s machinery to full mode coverage) found KRAS_G12C's
  own local residual costs ~33 additional thermal units beyond the
  collective k=50 part (`exp(-ΔG)`≈4.6×10⁻¹⁶) — astronomically costly
  under the harmonic model, independent of and consistent with the
  ceiling result rather than merely correlated with it.

This task's own headline framing ("the ceiling fails on all 3 targets,
robustly") should be read as superseded for BCR_ABL1 and partially for
CARDIAC_MYOSIN — the underlying real numbers above stand unedited, but
the geometry-confound caveat this task itself raised turned out to be
load-bearing for 2 of 3 targets, not just a theoretical concern. Full
comparison table: [[TASK-0235]]'s own Done section.

## Addendum 4 — Addendum 3's "4/4" does not survive proper power;
"supersedes" downgraded to "modest, same-direction, unproven" ([[TASK-0241]],
2026-08-24)

[[TASK-0241]] found Addendum 3's own BCR_ABL1 "4/4" claim did not reproduce
(3/4 on a same-commit re-run) and, more fundamentally, that TASK-0235's own 4
trials shared one byte-identical input structure — effective n=1 for the
backbone, with the observed spread being downstream EvoEF2/fpocket seed
jitter, not conformational sampling. Re-established properly rather than
either discarded or re-asserted:

**Experiment A — pure repacking jitter, one fixed BCR_ABL1 backbone, N=20
independent EvoEF2 trials per method** (`task0241_reproducibility_and_
jitter.py`, real, not simulated): bare druggability-bar rate old **4/20
(20%)** vs new **15/20 (75%)** — Fisher exact **p=0.0012**, genuinely
significant. On identical geometry, the new backbone repacks into a
bare-bar-clearing pocket far more often than the old one; the originally
published "4/4" was an ordinary draw from this real ~75% process (binomial
P(4 of 4)=0.316, P(3 of 4)=0.422 — the 4/4→3/4 discrepancy between the
original run and [[TASK-0241]]'s reproduction is exactly what n=4 sampling
noise on a ~75% process looks like, not evidence either run is wrong).
**Under the register's own strict `_is_hit` (overlap≥0.5 AND druggability
≥0.5), the same fixed geometry hits only 1/20 (5%) old vs 3/20 (15%) new —
Fisher p=0.605, not significant.** The bare-bar metric substantially
overstates the effect; `_is_hit` is the criterion that should be reported.

**Experiment B — real re-run, all 3 targets × both methods, N=20 trials
each, independent small (σ=0.15Å) per-trial structural perturbation of the
displacement field** (not just repacking-seed jitter — addresses [[TASK-0241]]'s
own "the 4 trials are not 4 samples" finding directly): BCR_ABL1's `_is_hit`
rate is **1/20 (5%) old vs 4/20 (20%) new — 4× higher, same direction as
claimed, but Fisher p=0.342, not significant at this N.** Druggability
medians (0.516 old vs 0.617 new) likewise don't clear significance
(Mann-Whitney p=0.882). KRAS_G12C and CARDIAC_MYOSIN: no significant
difference either target, consistent with both this task's own and
[[TASK-0235]]'s own already-honest characterization of those two as closed
or noisy, not flipped.

**Mechanism question resolved, not left contradictory**: `vdwrep`
(pairwise steric clash) and `overlap_frac` (fpocket cavity-shape/location
match) move independently across targets — BCR_ABL1: vdwrep −2.1%,
overlap_frac **+12.3%**; KRAS_G12C: vdwrep **−46.5%**, overlap_frac only
+11.4%; CARDIAC_MYOSIN: vdwrep −6.0%, overlap_frac **−12.3%** (opposite
sign). This is the reconciliation [[TASK-0241]] proposed as testable rather
than assumed: coherent local side-chain/backbone rotation reshapes cavity
geometry at near-constant pairwise clash energy, so a method's effect on
`vdwrep` and its effect on `overlap_frac`/druggability are not the same
claim and should not be read as corroborating each other automatically.

**Verdict**: Addendum 3's "BCR_ABL1: reversed" is downgraded to
**"a real, same-direction, statistically unproven trend"** — not
re-asserted, not discarded. The local-Kabsch method's fixed-geometry
advantage on the bare bar is real and significant (Experiment A); under
the stricter criterion this project's own `_is_hit` defines, and under
real structural resampling, the same trend persists in direction but not
yet in significance at n=20/arm. KRAS_G12C and CARDIAC_MYOSIN's readings
stand as before. **No justification for relaxing to bare `any_trial_
crosses_bar` (this task's own original choice, [[TASK-0235]] inherited it)
exists anywhere in either task's record** — recommended, not yet applied
project-wide: report `_is_hit` as the primary ceiling criterion going
forward. Full data: `results/tasks/0241_reproducibility_and_jitter/`,
`.ai/tasks/DONE/TASK-0241-task0235-ceiling-flip-does-not-reproduce.md`.
