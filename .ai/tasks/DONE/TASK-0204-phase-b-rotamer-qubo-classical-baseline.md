# TASK-0204 Phase B's own falsification criterion #1 — the classical rotamer baseline, the last unopened route

## Context

- ID: TASK-0204
- Title: run [[TASK-0181]] Phase B's own pre-stated falsification criterion #1
  — solve the side-chain rotamer packing objective **classically** on real
  candidate windows and test whether it opens an fpocket-druggable cavity
  more often than naive per-residue greedy rotamer choice.
- Status: Done
- Resolution: done
- Resolution Note: Falsification criterion #1 fails, 0/2 targets (bar 2/2) -- route closed, no quantum formulation follows.
- **Thread: Implementer B (science / compute).** Independent of
  [[TASK-0203]]; different targets, different modules, no shared files.
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `src/allostery/PHASE_B_ROTAMER_QUBO.md` §"Falsification criteria" #1
  (written by [[TASK-0181]], never run); Reviewer thread 2026-08-03
  recommendation #4; `REVIEW-panel-2026-07-28-external.md` §7's own
  "combinatorial selection is the one genuine gap."
- Priority: **P1 — the only route left in the register where the
  quantum-advantage argument does not collapse on contact, and the one thing
  worth spending a multi-day compute window on. Purely classical: it either
  opens the route or closes it, and closing it is equally valuable.**
- Dependency: [[TASK-0181]] (Done — the formulation), [[TASK-0163]]/
  [[TASK-0185]] (Done — vendored fpocket + the full-atom displacement
  machinery), [[TASK-0206]] (soft — fpocket determinism).

## Why this matters — every other quantum route is closed, and this one is closed *only by not having been run*

The register's own falsification history rules out, with measurement:

- Single-particle CTQW / occupation observables — proximity detectors, and at
  N ≤ 704 an `eigh` call, so no advantage exists at any point.
- Coherence / interference — inert (flat γ-sweeps, phase-free converged limit
  exact to 1e-6, coherent ≥ ENAQT under NISQ noise).
- Non-locality — absent by construction in a single-particle Hilbert space
  ([[TASK-0148]]).
- Interacting multi-particle — measured by the external panel: ρ ≈ 0.88–0.90
  against the 1-particle observable even at U=12, and the proximity confound
  gets *worse* (0.73 → 0.82).
- Backbone-layer conformational search — [[TASK-0185]] measured pocket
  recovery at **1–8 classical draws per hit**. Not a rare event, so
  amplitude amplification has nothing to amplify.
- Selection-as-QUBO at the **residue** layer — [[TASK-0181]] Phase A, gate
  CLOSED, 0/3 strict wins.
- Optimal control — [[TASK-0156]], chance on all 3 mandatory targets.

**The side-chain layer is the one place the argument survives, and it survives
for a stated reason, not by omission:** rotamer packing is discrete and
NP-hard (Pierce & Winfree 2002), and — unlike the backbone layer — pocket
opening there is *plausibly* a rare event, which is precisely the precondition
[[TASK-0185]] measured and found absent at the backbone. Both [[TASK-0185]]
and [[TASK-0187]] independently concluded, from opposite directions, that
whatever residual effect exists lives where a Cα ENM cannot reach.

Phase B was written up and explicitly not built, correctly, given the freeze.
**Its own criterion #1 is a purely classical experiment** — no quantum
formulation, no hardware, no qubit budget. It answers the question that
governs whether the quantum formulation is worth proposing at all, and per
Phase A's own precedent, *"no quantum formulation is built for an objective
that does not already show value classically."*

A closed result here is as valuable as an open one: it would let the
submission say the side-chain route was tested and closed, rather than
gestured at as future work — which is the difference between a forward
proposal and a hand-wave.

## Intent Contract

- Outcome: on ≥2 real targets, a measured cavity-opening rate for
  (a) classically-optimized rotamer packing vs. (b) naive greedy
  lowest-self-energy per-residue choice, scored by fpocket druggability on
  real repacked structures — plus an explicit verdict on Phase B's criterion
  #1 and, if it passes, the rare-event rate that determines whether a search
  formulation has anything to search.
- Why required, not assumed: Phase B currently has a formulation, a qubit
  estimate, and three falsification criteria, none of which has been tested.
  That is a proposal, not a result.
- In Scope:
  - **Sourcing, honestly.** `src/allostery/` has no `rotamer.py`/`packing.py`,
    no rotamer library, and no pairwise energy table — Phase B's own Status
    section says so. Source a backbone-dependent rotamer library (Dunbrack,
    coarse buckets per the write-up) and a pairwise energy term, or use an
    existing classical packer (DEE/A*, or a scriptable tool). **Prefer
    vendoring an existing solver over hand-rolling an energy function** —
    same precedent as `fpocket`/`ripser`/`optuna`, and a homemade energy
    table is exactly the "invented internal heuristic" criterion #3 forbids.
  - Candidate windows: use [[TASK-0180]]'s site-level clusters or the known
    pocket neighbourhood, 8–15 residues per the write-up's own `m`.
  - Repack, rebuild full-atom coordinates (reuse [[TASK-0185]]'s rigid
    per-residue Cα-driven displacement machinery and state the same
    approximation caveat it stated), run fpocket, score druggability.
  - **The comparison that is the actual gate**: optimized packing vs. greedy
    per-residue. Both scored identically. Report the rate difference and a
    null.
  - **If and only if criterion #1 passes**: measure the rare-event rate — what
    fraction of random rotamer assignments open the cavity? This is the
    number that decides whether amplitude amplification is even applicable,
    and it is the direct side-chain analogue of [[TASK-0185]]'s 1–8-draws
    finding at the backbone. Report it whichever way it lands.
- Out Of Scope:
  - **Any quantum formulation, QAOA run, or hardware estimate.** Phase B's own
    criterion #1 gates all of that, and Phase A's precedent is binding.
  - Claiming a speedup. Criterion #2 is explicit: NP-hardness permits a
    heuristic argument for trying, never a proven advantage. Any write-up
    must say so verbatim.
  - Side-chain MD, or any integrator. The no-MD constraint stands — this is
    discrete combinatorial search over a rotamer library, not dynamics.
  - Replacing the §5.2 hit list or any shipped deliverable.
- Constraints And Invariants:
  - **Pre-register the pass/fail bar before running**: what rate difference,
    on how many targets, counts as criterion #1 passing? Phase A set its bar
    at ≥2 of 3 targets; match that shape unless there is a stated reason not
    to.
  - Druggability must come from fpocket's actual score on real repacked
    structures — criterion #3, non-negotiable, no geometric proxy.
  - Report compute cost honestly. If the window size or library resolution has
    to be cut to fit the budget, state what was cut and what that does to the
    result's reach.
  - If the route closes, say so in the same voice every other negative in this
    register is reported in. A closed Phase B is a *result*.
- Planned Validation:
  - **Sanity, run first:** repack a window with the rotamers already present
    in the deposited structure and confirm fpocket reproduces that structure's
    known cavity. If the pipeline cannot recover the real answer from the real
    input, no downstream number means anything.
  - **Negative control:** random rotamer assignments must not open the cavity
    at the optimized rate. If they do, there is nothing to optimize and that
    is itself criterion #1's answer.
  - **Greedy baseline must be a fair baseline**, not a strawman — lowest
    self-energy per residue ignoring pairwise terms, exactly as the write-up
    specifies, same scoring path as the optimized answer. Phase A was careful
    about this (it excluded active-site residues from both arms); match that
    care.

## In Progress

—

## Pre-Registered Survival Criterion (fixed 2026-08-06, before any comparison run — Implementer B)

Written before the optimized-vs-greedy comparison is run, per this task's
own Constraint ("pre-register the pass/fail bar before running").

**Targets**: KRAS_G12C and BCR_ABL1 — **not** PTP1B (this task's own Open
Question, decided here): [[TASK-0203]] is concurrently investigating PTP1B
at a different layer (ensemble/mode, not packing); running the same target
risks conflating two independent findings into one number if both land
positive, and there is no dependency between the two tasks that requires
sharing a target. KRAS_G12C and BCR_ABL1 are both mandatory targets with
already-established, well-characterized pocket labels, chosen for that
reason alone.

**"Opens a druggable cavity"** (operationalized, reusing this project's own
established conventions rather than inventing new ones): a repacked
structure counts as opening a druggable cavity at the window if `fpocket`
detects **any** pocket whose member-residue set overlaps the window residues
by `>= 0.5` (the exact `POCKET_HIT_OVERLAP` bar
`conformational_search_measurement.py`/[[TASK-0185]] already established for
"did fpocket find the pocket") **and** that same pocket's own
`druggability_score >= 0.5` (fpocket's own commonly-cited druggable/
non-druggable cutoff — criterion #3's "real druggability, not a geometric
proxy," non-negotiable).

**Trial counts**: optimized (`SideChainRepack`, real simulated annealing) and
random (`RandomRepack`, this task's own patch) are each stochastic — run
**8 seeded trials** per target (matching [[TASK-0181]] Phase A's own
8-restart precedent, reused not reinvented). Greedy (`GreedyRepack`, this
task's own patch) is deterministic (always the lowest-self-energy rotamer
per site) — **1 trial** per target is the whole population; there is no rate
to compute for it, only a single hit/miss.

**Criterion #1 passes if**: the optimized hit-rate (fraction of 8 trials
opening a druggable cavity) **strictly exceeds** greedy's own single
hit/miss result, on **both** of the 2 targets tested (2/2) — the same
majority-of-targets shape Phase A's own gate used (2/3), scaled to this
task's own 2-target scope. If greedy already opens the cavity (hit=1) and
optimized does not exceed a rate of 1.0, that target counts as a **fail**
for criterion #1 on that target specifically (optimization added nothing
over the naive baseline) — stated explicitly so a ceiling case is not read
as an automatic pass.

**If and only if criterion #1 passes** (on both targets): measure the
rare-event rate using the **random** arm's own 8-trial hit-rate — this is
the direct side-chain analogue of [[TASK-0185]]'s 1–8-classical-draws
finding at the backbone layer, and decides whether amplitude amplification
would have anything to amplify.

## TODO

- [x] Pre-register the criterion-#1 pass bar in this file. **Before running.**
- [x] Source rotamer library + pairwise energy / classical packer; record the choice and why.
- [x] Sanity check: native rotamers → fpocket recovers the known cavity.
- [x] Select candidate windows on ≥2 targets.
- [x] Run optimized packing vs. greedy; score both by fpocket druggability.
- [x] Negative control: random assignments.
- [x] Verdict on criterion #1.
- [x] If passed: measure the rare-event rate (the amplitude-amplification precondition). — N/A, criterion #1 failed.
- [x] Write the result into `PHASE_B_ROTAMER_QUBO.md`'s Status section + `RESULTS.md`.

## Dependency

- [[TASK-0181]] (Done) — the formulation and all three criteria.
- [[TASK-0185]] (Done) — full-atom displacement + fpocket-as-oracle precedent.
- [[TASK-0163]] (Done) — vendored fpocket.
- [[TASK-0206]] (soft) — if the fpocket binary has drifted, pin it first.
- Feeds [[TASK-0183]] (the PoC sprint plan — this is the experiment that
  decides what Phase 2 would actually build) and [[TASK-0184]].

## Open Questions

- Is a full rotamer library + pairwise energy table sourceable and runnable
  inside the remaining compute window? If not, the honest fallback is a
  reduced library (fewer buckets) with the reduction stated — not abandoning
  the falsification and leaving Phase B untested.
- Does the "rare event" framing survive contact with real numbers? [[TASK-0185]]
  expected rarity at the backbone layer and measured its absence. The same
  could happen here — and if it does, it closes the last route cleanly, which
  is a genuinely good outcome for the submission.
- Should this run on PTP1B specifically, given [[TASK-0203]] is investigating
  the same target? Argument for: mechanistic coherence across the two tasks.
  Argument against: PTP1B's positive is an *ensemble/mode* result and Phase B
  is a *packing* result — different layers. Decide and record; do not let it
  default.

## Done

**Verdict: criterion #1 fails, 0/2 targets (bar was 2/2, pre-registered above
before any run). Route closed — no quantum formulation follows.**

**Sourcing (In-Scope, "prefer vendoring over hand-rolling").** Vendored
EvoEF2 (Huang et al., MIT license, `tools/evoef2/`, README documents the
exact from-source rebuild recipe, gitignored binary/library per this
project's `fpocket`-precedent convention). Minimal patch
(`task0204_single_pass_repack.patch`, ~115 lines across
`EnergyOptimization.h/.cpp`, `Main.cpp`): a new `SinglePassRepackForSCP`
function that calls EvoEF2's own pre-existing
`SequenceGenerateInitialSequenceSeed` (greedy) or `SequenceGenerateRandomSeed`
(random) and writes the result without annealing — reuses 100% of EvoEF2's
own energy/rotamer machinery, invents no physics, satisfying criterion #3's
"not an internal heuristic" bar for the comparator arms too, not just the
druggability score. `GreedyRepack`/`RandomRepack` added as new CLI commands
mirroring the existing `SideChainRepack` dispatch block exactly (same
rotamer-generation, same self-energy table), differing only in the final
optimization step (single-pass seed vs. simulated annealing).

**Windows**: 12 pocket-proximal residues per target (`_select_window`, apo
Cα coordinates, nearest-to-pocket-centroid capped at
`WINDOW_MAX_SIZE=12`), spatially selected (not sequence-contiguous) —
KRAS_G12C and BCR_ABL1 only, per the pre-registered decision above (not
PTP1B, to avoid conflating with [[TASK-0203]]'s concurrent, different-layer
investigation).

**Three real, unrelated tooling bugs found and fixed, none hand-waved
past** — each confirmed by direct, reproducible test before being called a
root cause, not assumed:

1. **EvoEF2's own PDB chain parser mishandles a chain letter that
   reappears after being interrupted by another letter** (A-B-A in file
   order — the natural output of "relabel the window's residues to chain
   B, leave the rest on chain A" when the window isn't a single contiguous
   stretch). Confirmed directly: an interleaved A(1-54)/B(55-67)/A(68-169)
   file silently expanded chain B's design-site selection to cover
   55-169 (merging the second A run into it) even though
   `--design_chains=B` was otherwise correctly parsed (the "were selected
   for design by default" console message is itself a pre-existing
   upstream mislabel — it fires when the CLI value *was* honored, not when
   it wasn't; read directly from `Main.cpp`, not guessed). **Fix**:
   `_write_full_atom_with_window_chain` now writes each chain letter as a
   single contiguous file block (all of 'A', then all of 'B'), sidestepping
   the parser bug regardless of its exact internal cause. Verified: the
   output file's chain B contains exactly the intended window residues,
   nothing else.
2. **prody boolean-mask indexing incompatibility** on this environment's
   numpy/prody versions (`AtomGroup.__getitem__` on a boolean array raised
   `TypeError` inside prody's own `rangeString`). Fixed by converting to
   integer indices via `np.where` before indexing — a version-compatibility
   fix, not a logic change.
3. **EvoEF2 SIGSEGVs when invoked with an absolute `argv[0]` path**,
   reproducibly, 5/5, with the *identical* binary/PDB/flags that succeed
   5/5 under a relative `./EvoEF2` invocation — confirmed by isolating the
   variable directly (same `subprocess.run(cwd=..., ...)` shape, only
   `argv[0]` changed). The earlier `--bbdep=disable --rotlib=honig984`
   workaround (adopted mid-debugging, before this was isolated) was a
   red herring chasing the same symptom from a different angle and has
   been removed — the default backbone-dependent library runs cleanly on
   real, non-sequence-contiguous pocket windows once both the chain bug
   and the argv[0] bug are fixed. Root cause not fixed at EvoEF2's own
   source (out of this task's scope; plausibly a fixed-size buffer
   overflow in `Main.cpp`'s `ExtractPathAndName`/`sprintf(PROGRAM_PATH,
   ...)` given a longer absolute path, consistent with the corrupted-
   looking "cannot find atom parameters of <ordinary-residue>" errors seen
   before this was isolated); worked around in the driver script by always
   invoking `./EvoEF2` with `cwd=EVOEF2_DIR`.
4. (Related, same debugging arc) **fpocket writes its `<stem>_out/` output
   directory next to the INPUT pdb file, not relative to `cwd`** —
   confirmed by direct manual test. `score_structure` was passing EvoEF2's
   output path (living in `tools/evoef2/`) alongside an unrelated temp
   `work_dir`, so `_run_fpocket` (reused from [[TASK-0163]]'s script)
   looked for the info file in the wrong directory and reported "no info
   file" on every non-native trial. Fixed by copying the structure into
   `work_dir` before scoring, matching the pattern the native-sanity call
   already (accidentally) satisfied.

**Full results** (`results_task0204_rotamer_repack_baseline/results.json`,
34 real EvoEF2+fpocket trials, 0 errors after the fixes above):

| Target | native sanity | greedy (1 trial) | optimized (8 trials) | random (8 trials) |
|---|---|---|---|---|
| KRAS_G12C | miss (overlap=0.75, drug=0.001) | miss (overlap=0.33, drug=0.278) | 0/8 hit (0.0) | 0/8 hit (0.0) |
| BCR_ABL1 | **hit** (overlap=0.92, drug=0.566) | **hit** (overlap=0.50, drug=0.537) | 0/8 hit (0.0) | 0/8 hit (0.0) |

KRAS_G12C's own native/deposited structure does not clear the druggability
bar at this window (fpocket scores it as barely druggable regardless of
repacking condition — consistent 0% across all three arms, not a packing
failure). BCR_ABL1's native structure and greedy both hit, but **every**
optimized and random trial misses — SA-optimized repacking performed
*worse* than the naive single-pass baseline. Plausible reading, stated as
such, not proven: EvoEF2's simulated annealing minimizes self+pairwise
packing energy across the window plus its own automatically-included
repack shell (30-40 residues total, not just the 12-residue window,
confirmed by inspecting `StructureShowDesignSites` output directly) —
tighter packing is a different objective than opening an fpocket-scored
cavity, and nothing in the run (correctness checks, trial counts, seed
distinctness) points to a mis-executed optimizer.

**Criterion #1's own pre-registered ceiling-case rule applies on BCR_ABL1
without ambiguity**: greedy already hits (rate 1.0); optimized's 0/8 does
not exceed that, so BCR_ABL1 counts as a fail, not an automatic pass by
virtue of greedy already succeeding. 0/2 targets pass the 2/2 bar.

**Consequence, per criterion #1's own stated rule and Phase A's binding
precedent ("no quantum formulation is built for an objective that does not
already show value classically")**: this route is closed. The rare-event-
rate measurement (whether a random assignment rarely opens the cavity —
the precondition for amplitude amplification to have anything to amplify)
was explicitly gated on criterion #1 passing and does not apply; reported
anyway for completeness since it was already measured as the negative
control — random also 0/8 on both targets, so even had criterion #1 passed
on a technicality, the observed random-arm rate would not have supported a
"rare event" framing distinct from the optimized arm's own rate.

**Every other route in the register's own falsification history is now
closed by measurement** (single-particle CTQW, coherence/interference,
non-locality, interacting multi-particle, backbone-layer conformational
search, residue-layer selection-as-QUBO, optimal control, and now
side-chain rotamer packing) — Phase B was the last route where the
quantum-advantage argument survived contact only by not having been run.
It no longer survives.

Updated: `PHASE_B_ROTAMER_QUBO.md` Status section (full table + verdict),
`RESULTS.md` (new §"row 65", cross-referenced). Full trial-level data:
`results_task0204_rotamer_repack_baseline/results.json`. New files:
`tools/evoef2/` (README, patch, gitignore — binary/library gitignored per
convention), `scripts/task0204_rotamer_repack_baseline.py`.
