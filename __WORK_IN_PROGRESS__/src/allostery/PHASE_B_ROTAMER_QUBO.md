# TASK-0181 Phase B — side-chain rotamer packing as QUBO (write-up only, not built)

Ships regardless of Phase A's gate outcome (task's own Priority line: Phase B is
"forward-proposal content only," not conditioned on Phase A winning). Phase A
(this task's classical backbone-selection probe) came back **CLOSED**
(`.ai/tasks/DONE/TASK-0181-*.md` Done section: 0/3 mandatory targets, canonical
weight point, 8-restart search) — consistent with, not contradicting, the
premise below: the backbone/topology layer is where Phase A looked, and where
[[TASK-0185]]'s own measurement already found pocket opening is *not* rare
under ENM-mode sampling (p = 0.24–0.69). Side-chain rotamer packing is a
structurally different, discrete combinatorial layer that Phase A's continuous
backbone score never touches.

## Why this layer, not the backbone

Pierce & Winfree (2002) established protein side-chain placement (fixed
backbone, discrete rotamer library, pairwise energy) as NP-hard — a real
complexity-class claim, not framing. Cryptic pockets are frequently a
side-chain repacking event on an already-favorable backbone conformation, not
a backbone conformational change per se — the backbone search Phase A probes
and the rotamer search here are genuinely different questions.

## Encoding

**Variables.** One-hot rotamer assignment per residue: for residue `i` with
`n_i` discrete rotamer states (a backbone-dependent rotamer library, e.g.
Dunbrack), binary variable `x_{i,r}` for `r in {1..n_i}`, constrained
`sum_r x_{i,r} = 1` (exactly one rotamer chosen per residue) via a standard
one-hot penalty `lambda * (sum_r x_{i,r} - 1)^2`.

**Objective** (energy to minimize, so the QUBO sign convention is the
negative of Phase A's maximization):

```
E(x) = sum_i sum_r  E_self(i, r) * x_{i,r}
     + sum_{i<j} sum_{r,s}  E_pair(i, r, j, s) * x_{i,r} * x_{j,s}
     - mu * CavityOpening(x)
     + lambda * sum_i (sum_r x_{i,r} - 1)^2
```

- `E_self(i, r)`: rotamer `i,r`'s own internal energy (backbone-dependent
  rotamer library probability, converted to an energy via `-kT log(p)`,
  standard Dunbrack-library convention) plus its pairwise energy against the
  fixed (non-repacked) rest of the structure.
- `E_pair(i, r, j, s)`: pairwise interaction energy between rotamer `r` at
  residue `i` and rotamer `s` at residue `j` (van der Waals + electrostatic,
  a standard rotamer-packing pairwise table — this repo's own `potentials.py`
  GNM/ENM energetics are the wrong tool here; a real rotamer library and a
  pairwise energy function, e.g. a Lennard-Jones + Coulomb table over rotamer
  pairs, is out-of-repo scope to build, cited as a dependency, not invented).
- `CavityOpening(x)`: a druggability-shaped constraint reward — the candidate
  cavity volume/shape induced by a given rotamer assignment must meet
  fpocket's own druggability criteria (the same bar Phase A benchmarked
  against, `baselines.fpocket_baseline`, TASK-0163) — `mu` weights how much
  the objective rewards opening a druggable cavity vs. minimizing raw packing
  energy.
- The one-hot penalty term keeps the assignment physically valid (`lambda`
  large enough that violating one-hot is never energetically favorable versus
  any real assignment change — standard QUBO constraint-encoding practice,
  the same principle Phase A's `selection.py` deliberately avoided needing
  by enforcing its cardinality constraint structurally instead; here a
  penalty is the standard approach since "exactly one rotamer per residue" is
  a per-variable-group constraint, not a global cardinality one, and rotamer
  QUBOs are conventionally encoded this way in the literature).

**Which residues are repackable.** Not the whole protein — a *candidate ENM
deformation* (a backbone conformation sampled the way [[TASK-0185]]'s own
conformational-search framing already does) plus a spatial window around a
Phase-A-flagged or literature-flagged candidate site defines the repackable
residue set. This keeps the qubit count tractable (below) and matches the
actual biology (cryptic pocket opening is local, not global repacking).

## Qubit count estimate

For a repackable window of `m` residues, each with a typical backbone-
dependent rotamer library size `n ~= 10-20` states (Dunbrack library, coarse
buckets), the one-hot encoding needs `m * n` binary variables. A druggable
cryptic pocket window is typically 8-15 residues (comparable to
[[TASK-0180]]'s own site size, `min_cluster_size=2` up to whatever a real
cluster resolves to) — `m=12, n=15` gives **180 qubits** for the variables
alone, before any ancilla/penalty-term auxiliary qubits a hardware embedding
would add (a fully-connected 180-variable QUBO's minor embedding on
current fixed-topology annealing hardware typically needs several times that
in physical qubits — an honest range to state is "180 logical qubits,
likely 500-1500+ physical qubits after embedding," not a single number
claimed as exact).

## Falsification criteria

Stated up front, per this project's own standing practice (every other
route in this register — ENAQT, chirality, persistent H2, entanglement
entropy, spectral coherence, multi-particle walks — was ruled out by a
pre-stated falsification check, not declared a win by default):

1. **Classical baseline first, same discipline as Phase A.** Before any
   quantum formulation is attempted, solve the identical rotamer QUBO
   classically (simulated annealing over the same one-hot-encoded search
   space, or an existing classical rotamer packer like a Dead-End
   Elimination/A* solver if available) on real candidate windows. If the
   classically-best rotamer assignment does not open a cavity meeting
   fpocket's druggability bar more often than a naive greedy rotamer choice
   (lowest-self-energy rotamer per residue, ignoring pairwise terms — the
   rotamer-packing analogue of Phase A's own "greedy top-k"), this route is
   closed the same way Phase A's own gate closed it: **no quantum
   formulation is built for an objective that does not already show value
   classically.**
2. **No proven speedup claim, ever.** NP-hardness permits a heuristic
   argument for trying a QAOA/annealing approach, never a proven quantum
   advantage — QAOA has no general performance guarantee on this or any
   NP-hard instance class. Any write-up of this route must say so
   explicitly, matching Phase A's own Out-Of-Scope line verbatim.
3. **Real druggability, not a geometric proxy.** `CavityOpening(x)` must be
   validated against `fpocket`'s actual druggability score on real repacked
   structures (or a physically comparable cavity-detection tool), not an
   internal geometric heuristic invented for this objective alone — the same
   "the bar that actually matters" standard Phase A held itself to
   (TASK-0163's 0.8348/0.8596 fpocket numbers — superseded 2026-08-06,
   [[TASK-0206]]: use 0.7910/0.8618, the current pinned/authoritative
   set, `tools/fpocket/PROVENANCE.json`, when this validation is built).

## Status

> ## ⛔ CLOSED ON COMPLEXITY GROUNDS (2026-08-06, reformulated TASK-0204)
>
> **The gating question was wrong, and the corrected one closes this route
> more decisively than any biological result could.** Raised by the
> orchestrating user: even a clean pass on criterion #1 would not support a
> quantum route if the instance solves classically in seconds.
>
> Side-chain packing on a fixed backbone is a pairwise MRF. Exact
> minimization costs `O(m·n^(tw+1))` — **treewidth**, not variable count —
> not the naive `O(n^m)` this document's own 180-qubit estimate is built on.
> Measured on real structures (4 targets, m=8–80, cutoff swept), then
> validated by actually solving the instances exactly (bucket elimination,
> correctness-gated against brute force on 3 enumerable cases):
>
> | Target | m=12 `tw` | naive `n^m` | **exact solve, wall clock** |
> |---|---|---|---|
> | KRAS_G12C | 3 | 1e14.1 | **0.002 s** |
> | BCR_ABL1 | 4 | 1e14.1 | **0.009 s** |
> | CARDIAC_MYOSIN | 2 | 1e14.1 | **0.001 s** |
> | PTP1B | 5 | 1e14.1 | **0.159 s** |
>
> **The exact global optimum of a real druggable-pocket window is found in
> milliseconds.** The `1e14` search space is an illusion created by counting
> variables instead of measuring the interaction graph. The qubit estimate
> below is a faithful *encoding size* and is not evidence of hardness.
>
> A genuine hard regime does exist, but only at m≈50–80 (`tw` 9–23) — most
> of a domain, not a pocket. This document's own scope (m=8–15) sits
> entirely inside the tractable regime.
>
> Same argument shape the register already accepts for Grover/HHL/QML and
> single-particle CTQW. Full record: TASK-0204's "REFORMULATED" section.
>
> ## ⚠️ UNTESTED — the CLOSED verdict below is RETRACTED (2026-08-06)
>
> [[TASK-0204]] was reopened by the Reviewer thread the same day it closed.
> Three independent defects were found, each sufficient alone to void the
> verdict. **This route is untested, not closed.** The text below is kept
> unedited for the record, per this project's no-silent-overwrite convention.
>
> 1. **The gate could not return `pass` for any data.**
>    `opt_rate > (1.0 if greedy_hit else 0.0)` — but `opt_rate` is a fraction
>    of 8 trials, maximum 1.0. On any target whose greedy hit (BCR_ABL1 did),
>    no result could clear it, including a perfect 8/8. The bar required 2/2,
>    so criterion #1 was unfalsifiable in the positive direction before a
>    single trial ran.
> 2. **There was no positive control.** Only the *apo* structure was scored,
>    where a cryptic pocket is closed by definition. The holo structure was
>    loaded but never scored. Built and run since
>    (`scripts/task0204_positive_control.py`): the holo control **passes on
>    KRAS_G12C** (overlap 1.000, druggability 0.886 — vs. its apo's 0.001, the
>    real cryptic signal) and **FAILS on BCR_ABL1** (0.356, below the 0.5 bar
>    and below that target's own apo at 0.566). Every BCR_ABL1 number in the
>    table below is uninterpretable.
> 3. **The conjunctive criterion is dominated by an overlap leg that any
>    repacking destroys.** On KRAS_G12C holo — cavity definitively open —
>    repacking drops overlap 1.000 → 0.417 (greedy) / 0.250 (SA median) while
>    druggability *stays high* at 0.827–0.941. The **random** arm, which
>    minimizes nothing, collapses identically — refuting the "SA packs tighter"
>    mechanism claimed below. The common factor is repacking, not optimization.
>
> Supporting: total runtime 73.3 s, of which 33.6 s is `sleep()`; no seed
> control (wall-clock-second seeding only); P(0 of 8) = 0.52 / 0.83 under the
> observed per-leg marginals, so 0/8 was the modal outcome under any
> hypothesis.
>
> Full record and the requirements for a valid rerun: [[TASK-0204]]'s own
> "Reopened" section.

**CLOSED — falsification criterion #1 run and failed, 2026-08-06 ([[TASK-0204]]).**

`[[TASK-0204]]` sourced a real classical packer (vendored, MIT-licensed
EvoEF2, `tools/evoef2/`, minimally patched to expose greedy/random
single-pass rotamer choice alongside its own shipped simulated-annealing
optimizer — no hand-rolled energy function, per criterion #3) and ran the
classical baseline this Status section previously said had not been built.

Pre-registered bar: optimized (`SideChainRepack`, 8 seeded trials) hit-rate
must strictly exceed greedy's (`GreedyRepack`, 1 deterministic trial) single
hit/miss, on **both** KRAS_G12C and BCR_ABL1 (2/2). Measured:

| Target | native sanity | greedy | optimized (8 trials) | random (8 trials) | passes? |
|---|---|---|---|---|---|
| KRAS_G12C | miss (drug=0.001) | miss | 0/8 (0.0) | 0/8 (0.0) | No |
| BCR_ABL1 | **hit** (drug=0.566) | **hit** | 0/8 (0.0) | 0/8 (0.0) | No |

**Criterion #1 fails, 0/2 (bar was 2/2).** On BCR_ABL1 the ceiling case
applies explicitly (greedy already hits, optimized does not exceed rate
1.0 — a fail per this task's own pre-registered rule, not read as an
automatic pass). Notably, SA-optimized repacking scored *worse* than the
naive greedy baseline on BCR_ABL1 (0/8 vs. 1/1) — energy minimization over
the full rotamer objective (self + pairwise terms across the window plus
EvoEF2's own automatically-included repack shell) tends to pack side chains
*tighter*, which is not the same objective as opening an fpocket-druggable
cavity; nothing here suggests the optimizer was mis-run.

Per criterion #1's own stated consequence and Phase A's binding precedent:
**no quantum formulation is built for this objective.** Rare-event-rate
measurement (the amplitude-amplification precondition) was gated on
criterion #1 passing and is therefore not applicable — a closed result, not
an open question. Full trial-level numbers:
`results/tasks/0204_rotamer_repack_baseline/results.json`; task file:
`.ai/tasks/DONE/TASK-0204-*.md`; `RESULTS.md` §"Phase B rotamer-QUBO
classical baseline — criterion #1 closes the route".
