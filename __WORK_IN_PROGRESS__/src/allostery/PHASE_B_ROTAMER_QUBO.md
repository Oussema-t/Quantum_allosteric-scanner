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
   (TASK-0163's 0.8348/0.8596 fpocket numbers).

## Status

Formulation only, per this task's own In-Scope bullet ("state the encoding...
qubit count, and falsification criteria... Do not build it"). Not implemented.
No rotamer library, pairwise energy table, or cavity-detection integration
exists in this repository as of this writing (`src/allostery/` has no
`rotamer.py`/`packing.py` module) — a future task would need to source or
build all three before Phase B's classical baseline (falsification criterion
1) could even be run.
