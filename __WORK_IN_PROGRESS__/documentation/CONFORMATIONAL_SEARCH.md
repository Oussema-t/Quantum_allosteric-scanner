# Conformational-search reformulation of cryptic-pocket prediction

TASK-0185. Written to be lifted into [[TASK-0184]]'s Technical Approach
section. Status: **reformulation stated, one real-data measurement run,
mixed result reported honestly — not a pipeline, not built beyond this
one measurement, per this task's own Out Of Scope.**

## The reformulation

A cryptic pocket is *defined* by absence in the apo structure. Every
static apo scorer in this project's register (~40 observables, 226 scored
cells) ranks residues on a structure in which the target feature is not
present. That is a simpler explanation of the register's own pattern than
any mechanism hypothesis tested to date — see this task's filing (Context
section, `.ai/tasks/DONE/TASK-0185-conformational-search-reformulation.md`)
for the supporting table (BCR_ABL1 pre-formed / apo-holo pocket RMSD ratio
0.49 / fpocket AUC 0.8596 [superseded 2026-08-06, [[TASK-0206]]: 0.8618,
same reading — a since-unreproducible machine-specific binary build, see
`RESULTS.md`'s "fpocket binary drift" section] vs. KRAS_G12C genuinely
cryptic-but-overlapping the active site).

Reframing the problem as **search over an ENM-generated conformational
ensemble for structures in which the pocket forms** inverts [[TASK-0163]]'s
most damaging finding: fpocket (2009, purely geometric, no dynamics)
beating this project's own observables on 2/3 mandatory targets stops
being a competitor result and becomes **the oracle a search procedure is
built against** — "search conformational space for the structure where
fpocket fires," not "out-score fpocket on the static apo structure."

**Legality.** §Constraint 3 forbids classical MD trajectories as inputs,
not conformational sampling. The ensemble used here (and in
[[TASK-0187]]) is closed-form: amplitude_k ~ N(0, sqrt(kT/lambda_k)) drawn
directly in ANM mode space, no integrator, no trajectory. Challenge
reference [1] (Zheng 2023, fast conformational sampling guided by
coarse-grained normal modes) is this method; reference [2] (CrypToth) is
the mixed-solvent-MD version of the same idea, not used here.

## The measurement

**Question**: does the known holo pocket appear in any ENM-sampled apo
conformation, at what frequency, and is that frequency specific to the
real pocket (vs. a matched random distal patch)?

**Method.** Reuses `allostery.shortcuts.equipartition_ensemble` /
`msf_cross_check` ([[TASK-0187]]) for the sampler and its blocking MSF
gate, and `allostery.plant.select_distal_patch` ([[TASK-0167.001]]) for
the negative-control decoy. New in this task (a single script, not a
module — `scripts/conformational_search_measurement.py`, per this task's
own "not a build" scope): a rigid per-residue Cα-driven translation that
moves every atom of residue `(chain, resnum)` by that residue's own ANM
displacement vector, producing a full-atom structure the already-vendored
fpocket ([[TASK-0163]], `tools/fpocket/bin/fpocket`) can read. This is an
approximation — bond lengths and side-chain conformation are held fixed,
only rigid-body position moves — stated explicitly, not hidden. Per
sample: run fpocket, take the best-overlapping detected cavity's fraction
of real-pocket (or decoy) residues covered; "hit" = that fraction >= 0.5.

100 ENM samples per target (n_modes=20, kT=20, 8.0 Å ENM cutoff — same
convention as [[TASK-0067]]/[[TASK-0187]]), MSF cross-check run first and
blocking (all 3 targets passed cleanly, Pearson r=0.993-1.000, median
relative error 5.7-7.6%, well inside the r>=0.90/rel.error<=25% gate).
0 fpocket errors across all 300 main-run samples.

**Positive control (run first, per this task's own Planned Validation):**
BCR_ABL1's static apo structure alone already covers 87.5% of the real
pocket via fpocket (matches [[TASK-0163]]'s own high static AUC for this
pre-formed pocket); the ensemble's real-pocket hit rate is 80.0%. The
procedure clearly finds an already-open pocket at high frequency — the
method is validated before trusting anything else.

**Real-data hit rates (n=100 samples/target, 0.5 overlap-fraction
threshold), real pocket vs. matched distal decoy:**

| Target | static apo overlap | real hit rate | decoy hit rate | real mean overlap | decoy mean overlap |
|---|---|---|---|---|---|
| BCR_ABL1 (positive control) | 0.875 | **0.800** | 0.510 | 0.654 | 0.461 |
| KRAS_G12C | 0.611 | **0.500** | 0.370 | 0.485 | 0.444 |
| CARDIAC_MYOSIN | 0.923 | 0.200 | 0.190 | 0.398 | 0.391 |

**Reading, honestly reported per target:**
- **BCR_ABL1**: real clearly beats decoy (0.800 vs 0.510, gap 0.29) —
  specific, but the decoy rate itself is not small. BCR_ABL1 is a large,
  cavity-rich multi-domain kinase construct (37 fpocket-detected cavities
  on the static structure alone, [[TASK-0163]]); a "distal" patch (defined
  only by hop-distance from the active site, not by druggability) still
  frequently lands near *some* detected cavity. Real specificity is
  present, not absolute.
- **KRAS_G12C**: real beats decoy by a smaller margin (0.500 vs 0.370, gap
  0.13) — consistent with this target's own established partial
  crypticity ([[TASK-0169]]).
- **CARDIAC_MYOSIN**: **no specificity** — real (0.200) and decoy (0.190)
  are statistically indistinguishable at this sample size. A clean
  negative for this target specifically. (Static-structure overlap is
  high, 0.923, but that is a single point, not the ensemble's own
  frequency — the two numbers answer different questions and should not
  be conflated; see Open Questions.)

**n_modes sweep (BCR_ABL1 only, N=60/point, reproducing the original
synthetic-toy-model rarity measurement on real data — an implementer's
scope-narrowing to one target given the ~1-day budget, stated explicitly
rather than silently limited):**

| n_modes | real hit rate | decoy hit rate |
|---|---|---|
| 5 | 0.983 | 0.400 |
| 20 (main run) | 0.800 | 0.510 |
| 40 | 0.783 | 0.200 |

Real-pocket recovery stays high (0.78-0.98) across the whole tested mode
range — **pocket opening/recovery is not a rare event on real data
either**, corroborating the original synthetic-toy-model finding
(`conformational_search_prototype_REFERENCE.py`: p(cleft opens) = 0.244
at n_modes=5, rising to 0.694 at n_modes=40) on a real target instead of
a two-lobe synthetic fold. This is the measurement that "moves the
quantum claim" (see below): a Grover-style rare-event search argument
requires the target event to be rare, and on every real target measured
here, recovering the real pocket via ENM sampling is common (20-98% per
100-600 draws), not astronomically rare. Interestingly, the
real-vs-decoy specificity *gap* is not monotonic in n_modes (0.583 at
n_modes=5, 0.290 at n_modes=20, 0.583 at n_modes=40) — reported as
observed, not smoothed into a story the data doesn't clearly tell.

## Where the quantum claim is, and is not, defensible

**Not defensible: backbone-layer rare-event search.** The intuitive
argument (conformational space is astronomically large, pocket-open
states are rare, amplitude amplification gives 1/√p against classical
1/p) fails at measurement, on both the synthetic toy model and all three
real mandatory targets measured here. Recovering the real pocket via
closed-form ENM sampling costs on the order of 1-8 classical draws per
hit on the best case (BCR_ABL1, real hit rate 0.8) and is not
dramatically worse even on the weakest case (CARDIAC_MYOSIN, hit rate
0.2, ~5 draws per hit) — none of this is a regime where quantum search
offers a defensible advantage. A conjunctive druggability-constraint
version (volume band + buriedness + specificity + energy budget) is
rarer (the synthetic reference's own JOINT p ≈ 0.00267, ~375 classical
draws, amplitude-amplification ~19) but still cheap and still not a
credible quantum-advantage claim a reviewer would accept.

**Where it may be defensible: the side-chain layer.** Backbone motion is
ENM-tractable — continuous, ~10-40 dimensional, and (per this
measurement) dense with target-hitting states, not sparse. Cryptic
pockets do not open by backbone breathing alone; they open by
**side-chain repacking**, and side-chain placement over rotamer libraries
is discrete and NP-hard (Pierce & Winfree 2002, *Protein Engineering*),
with an existing QUBO literature for annealers. **The full formulation
(encoding, qubit count, falsification criteria) is [[TASK-0181]] Phase B's
own deliverable, in progress concurrently on another thread as of this
writing** — deliberately not duplicated here to avoid two diverging
specs; this document states only the boundary and the forward pointer,
per this task's own Intent Contract instruction to cross-reference rather
than re-derive.

## Boundary against [[TASK-0015]] / `HOLO_DIRECTION_MODULE.md`

That module predicts the apo→holo *deformation direction* from apo and
feeds one deformed graph to transport — a single directed prediction, no
ensemble. This task samples the *undirected equilibrium ensemble* and
asks whether the pocket appears anywhere in it — no direction prediction,
no transport step. **Recommendation carried over from this task's own
filing**: this task subsumes the motivation for TASK-0015; TASK-0015
should be re-scoped or closed rather than the register carrying two
overlapping specs. Not actioned here (TASK-0015 is claimed on a different
machine/thread as of TASK-0185's own filing) — flagged for
[[TASK-0184]]'s narrative and whoever owns TASK-0015 next.

## What this does not claim

- Not quantum. The reformulation and this measurement are entirely
  classical. Only the side-chain layer (above) carries a forward quantum
  claim, and that claim is a proposal, not a result.
- Not a retraction of the register's existing 226 scored cells — the
  reformulation explains the pattern, it does not invalidate the
  arithmetic.
- Not a working pipeline. This is one measurement script
  (`scripts/conformational_search_measurement.py`), run once, reported
  once — building a persistent search pipeline is explicitly out of this
  task's scope before the freeze.

## Full numbers

`results/tasks/0185_conformational_search/results.json`,
`results/tasks/0185_conformational_search/run.jsonl` (RunLogger).
