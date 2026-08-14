# TASK-0172 Spectrum-preserving Hamiltonian reduction (Krylov / Schur complement) with a retention proof

## Context

- ID: TASK-0172
- Title: replace/augment the current naive community-merge coarse-graining
  with a **controlled** reduction that provably preserves the transport
  signal — Krylov subspace projection (exact for the seeded walk) and
  Löwdin/Feshbach–Schur partitioning (exact elimination of the discarded
  residues) — and report a quantitative retention metric.
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: raised by the orchestrating collaborator (Oussama), 2026-07,
  asking how to compress H so that only transport-relevant residues are
  retained (originally proposed via partial trace / density matrix — see
  the correction below).
- Priority: **P1 — this closes a stated challenge requirement that the
  current code does not meet.**
- **Renumbered from TASK-0158, 2026-07-28**: this task was originally
  filed as TASK-0158, colliding with the already-existing, already-Done,
  heavily-cross-linked `TASK-0158-compact-null-fix-and-rerun.md`
  (permutation-null correction, `PANEL_REVIEW_2026-07-25.md` §2.3). A
  first attempt to fix this (commit `9670af0`) renumbered it to
  TASK-0171, which itself collided with a concurrently-filed, unrelated
  TASK-0171 (reverse-direction coupling test, HOLO comparison) and was
  reverted (`8f76102`). Found via a full repo-wide collision scan,
  requested after that revert — confirmed via grep that no other file
  anywhere references this content under either TASK-0158 or TASK-0171;
  every existing "TASK-0158" cross-link in the repo (14 other files)
  refers unambiguously to the compact-null-fix task, so this rename
  requires no cross-link updates elsewhere. Content otherwise unchanged.

## Why this is not already done

`coarse.py` implements Louvain / spectral community detection plus a
greedy merge to an `n_target` node budget, and `trotter_cost` for the
NISQ feasibility estimate. That is a **lossy, uncontrolled** reduction:

- `_graph_weights()` calls `np.fill_diagonal(W, 0.0)` — every diagonal
  site-energy term (V_B, V_T, V_R, V_C, V_M) is **discarded** before
  coarse-graining. The reduced object is a pure coupling graph, not a
  reduction of `H`.
- `_coarsen_graph()` sums inter-cluster edge weights. This preserves
  neither the spectrum nor the seeded dynamics; nothing bounds the error.
- There is **no fidelity/retention metric anywhere in the module.**

The challenge statement requires the opposite: participants *"should also
demonstrate a method for coarse-graining the protein structure and prove
that this compression retains the essential topological signal."* We
currently coarse-grain but do not prove retention. This task supplies the
proof, or shows it fails.

## Correction to the original framing — read before implementing

The reduction was originally proposed as a **partial trace / reduced
density matrix**. That is not applicable here, for two structural
reasons:

1. Partial trace is defined on a **tensor-product** Hilbert space
   `H_A ⊗ H_B`. The single-particle walk lives on
   `span{|1>,...,|N>} = C^N`, a **direct sum** of site states — there is
   no tensor factor to trace out.
2. Partial trace acts on **density matrices (states)**, not on
   Hamiltonians. `Tr_B(H)` discards the coupling block `H_AB` outright,
   which is exactly the information allosteric communication lives in.

The correct tools are:

- **Löwdin / Feshbach–Schur partitioning.** Split residues into a kept
  set P and an eliminated set Q:
  `H = [[H_PP, H_PQ], [H_QP, H_QQ]]`, giving the exact effective operator
  `H_eff(E) = H_PP + H_PQ (E - H_QQ)^{-1} H_QP`.
  This reproduces exactly those eigenvalues of H whose eigenstates have
  support on P; the eliminated residues survive as energy-dependent
  corrections rather than being deleted. Note that naive truncation
  `H -> H_PP` (deleting rows/columns) is the crude limit that loses the
  coupling — and is closer to what `coarse.py` currently does.
  (Löwdin 1962, *J. Math. Phys.* 3, 969, DOI 10.1063/1.1724312;
  Feshbach 1962, *Ann. Phys.* 19, 287, DOI 10.1016/0003-4916(62)90221-X
  — **verify both before building**.)
- **Krylov subspace projection.** Since every run seeds at the active
  site `|s>`, the entire seeded dynamics is confined to
  `K_m = span{|s>, H|s>, H^2|s>, ..., H^{m-1}|s>}`, typically far smaller
  than N and **exact** for that walk at fixed m. This is the natural
  reduction for this project specifically, because the seed is fixed.
  (Novo et al. 2015, *Sci. Rep.* 5, 13304, DOI 10.1038/srep13304 — cited
  in the project's own multi-source lit review; verify before building.)

## Circularity guard — non-negotiable

The original request was to *"preserve only the residues with high
allosteric potential."* **Selecting the retained subspace using a
predicted allosteric score, then scoring allosteric prediction on the
reduced system, is circular** and would be caught by this project's own
leakage apparatus.

Subspace selection MUST be label-blind. Permitted criteria: Krylov
(purely dynamical, generated from the active-site seed), lowest-GNM-mode
subspace, graph community structure, or energy-window selection. **Not
permitted:** any per-residue score that is, or correlates with, the
observable being validated.

## Intent Contract

- Outcome: (1) a Krylov projection and a Schur-complement reduction of
  the existing `H_new`, both label-blind; (2) a **retention report** for
  each, at several compression ratios, versus the existing Louvain/
  spectral baseline in `coarse.py`.
- Why required, not assumed: the challenge requires proof of signal
  retention under coarse-graining; the current module provides
  compression with no error control and silently drops the diagonal.
  Whether the ranking survives compression is untested.
- In Scope:
  - Verify the Löwdin/Feshbach/Novo citations directly before
    implementing against them.
  - Implement Krylov projection (Lanczos on the seeded vector, H is
    real-symmetric) and Schur-complement elimination on the existing
    `H_new`, **retaining the diagonal potential terms** (unlike
    `_graph_weights`).
  - **Retention metrics (the deliverable):**
    (a) spectral: max/mean eigenvalue error of the reduced operator vs
        the full operator over the retained band;
    (b) dynamical: fidelity of `e^{-iHt}|s>` projected onto the retained
        subspace vs the full evolution;
    (c) **ranking: Spearman rho between the full-H residue ranking and
        the reduced-H ranking, and the change in AUC/P@5** — this is the
        one that actually matters for the submission claim.
  - Sweep compression ratio (N -> N/2, N/4, ... down to the ~12-16 node
    NISQ budget in `coarse.py`) and report where the ranking breaks.
  - Compare all three (Krylov, Schur, existing Louvain) on the same
    targets and the same axes.
- Out Of Scope:
  - Partial trace / reduced density matrix — not applicable (see above).
  - Any label-dependent subspace selection (see circularity guard).
  - **VQE on the reduced Hamiltonian.** VQE targets *ground states*; a
    single-particle `H` is an `N x N` matrix whose ground state comes
    from classical eigendecomposition in `O(N^3)` — microseconds at
    N ~ 100. VQE would add variational error for zero advantage. If a
    quantum-hardware demonstration is wanted, the honest vehicle is
    **Trotterised time evolution of the reduced H** (which `trotter_cost`
    already estimates), not VQE.
  - Reselecting the submission operator (Tier-2-gated, [[TASK-0100]]).
- Constraints And Invariants: reduction is applied to an **apo-derived**
  H only (same caller obligation `coarse.py` documents); the retained
  subspace is chosen by a label-blind rule fixed and stated before
  scoring; Hermiticity asserted after reduction.
- Planned Validation: synthetic gate first — on a graph with a known
  planted long-range coupling, does the reduced operator preserve the
  planted signal that naive Louvain merging destroys? Then real targets.

## In Progress

None

## TODO

- [x] Verify the Löwdin / Feshbach / Novo citations directly -- all 3
      confirmed against the real papers (see Done).
- [x] Implement Krylov (Lanczos) projection from the active-site seed --
      built via direct matrix powers + QR, not the three-term Lanczos
      recurrence; same invariant subspace, verified not just asserted
      (see Done for the Implementer's-call justification).
- [x] Implement Schur-complement / Löwdin elimination, diagonal retained
      -- built (`allostery.reduce.schur_complement`), fixed reference
      energy E=0.0.
- [x] Synthetic gate: planted long-range coupling survives reduction? --
      yes, both methods, on TASK-0103's own dumbbell fixture.
- [x] Retention report: spectral error, dynamical fidelity, and ranking
      rho / AUC delta vs compression ratio -- done, all 3 mandatory
      targets, 6 compression points each bracketing the active-site size.
- [x] Head-to-head vs existing `coarse.py` Louvain/spectral baseline --
      done; a real normalization bug caught and fixed in the Louvain
      scoring path before trusting its numbers (see Done).
- [x] Report the compression ratio at which the ranking breaks -- **at
      m <= n_active, sharply, for block-seed Krylov, on all 3 targets**;
      Schur has no equivalent sharp break (floors gracefully at
      n_active) but is not universally better than the full system
      (loses on BCR_ABL1). Full numbers in Done/RESULTS.md.

## Dependency

- [[TASK-0094]] (Done) — proximity floor.
- [[TASK-0112]] (Done) — bootstrap CI.
- [[TASK-0130]] (Done) — converged propagator this reduces.
- `coarse.py` (Done, Phase 4) — the baseline this must beat, and the
  module whose diagonal-dropping behaviour motivated this task.

## Open Questions

- Krylov dimension m: fixed, or chosen by residual tolerance? **Resolved
  (Implementer's call): fixed, swept over a small explicit grid** ({10,
  14, 18, 24, 32, 50}) chosen to bracket each target's own active-site
  size, not a residual-tolerance adaptive scheme -- a residual-tolerance
  stopping rule would have masked exactly the "budget consumed by seed
  alone" finding this task's own sweep needed to see directly (a fixed
  grid crossing the threshold shows the sharp break; an adaptive
  tolerance-driven m would have auto-inflated past it without
  surfacing why).
- Schur complement is energy-dependent — evaluate at a fixed reference
  energy or self-consistently? **Resolved (Implementer's call): fixed,
  E=0.0**, matching `transport.transmission_from_source`'s own
  established "DC/zero-bias limit" convention in this codebase, not
  invented fresh or tuned against any result. The approximation cost of
  this choice is measured directly, not just acknowledged: spectral
  error stays ~0.01 for Ritz values near E=0 but grows to ~5 for Ritz
  values far from it (KRAS_G12C, m=24) -- reported as observed.
- Should the retention report use the converged observable or a
  finite-t one? **Resolved: converged** (`time_averaged_ctqw_converged`,
  `coherent=False`) -- the shipped readout, matching every other real
  retention/detection script in this register
  (`positive_control_detection_curve.py` etc.), stated explicitly rather
  than left implicit.
- **New, raised by this task's own testing, not anticipated in the
  filing**: does the block-seed budget-consumption problem generalize
  beyond this project's own multi-residue seeding convention, i.e. would
  a real deployment choosing a single representative active-site residue
  (rather than the full incoherent-mixture block) avoid it? **Partially
  answered**: yes, directly confirmed on KRAS_G12C at m=10 (single-seed
  Krylov reaches rho=0.56/AUC=0.612 where the block-seed version is
  completely uninformative) -- but this would be a real, stated deviation
  from TASK-0118's own established incoherent-mixture seeding convention,
  not evaluated here as a proposal, flagged for whoever next revisits
  that convention.

## Done

**2026-08-14, Implementer C.**

Citations verified directly against the real papers before building
(this task's own explicit Constraint): Löwdin 1962, *J. Math. Phys.*
3(5), 969-982, "Studies in Perturbation Theory IV" -- confirmed, matches
the projection-operator/partitioning-technique construction this task
uses. Feshbach 1962, *Ann. Phys.* 19(2), 287-313, "A Unified Theory of
Nuclear Reactions II" -- confirmed, the origin of the effective-operator
formalism applied here by analogy to a single-particle graph Hamiltonian.
Novo, Chakraborty, Mohseni, Neven & Omar 2015, *Sci. Rep.* 5, 13304,
"Systematic Dimensionality Reduction for Quantum Walks" -- confirmed,
its own "invariant Krylov subspace generated from a seed node" is
exactly this task's Krylov construction. No citation errors found (this
project's own established citation-integrity checking, per the
Implementer spin-up brief, found none to correct here).

**Built** (`src/allostery/reduce.py`, new module): `krylov_basis` (direct
matrix powers + QR deflation, not the three-term block-Lanczos
recurrence -- the same invariant subspace by definition, a deliberate
scale-justified simplification, verified empirically via 17 new tests
rather than just asserted equivalent), `reduce_krylov`,
`lift_krylov_eigvecs`; `schur_complement` (fixed reference energy E=0.0,
`eta_reg`-style regularization matching `transport.
transmission_from_source`'s own convention, `retain_idx` sorted
internally -- a real bug this sorting fixes, see below),
`lift_schur_eigvecs`. Both retain the diagonal potential terms `coarse.
_graph_weights` drops.

**Test suite** (`tests/test_reduce.py`, 17 tests, all passing):
orthonormality; seed vectors provably in span(Q); reduced operator
symmetry; exactness when the subspace is provably the whole space (fixed
by seeding from every node, not relying on a single-vector seed's
algebraic rank, which is NOT guaranteed full-rank in general -- caught
directly when an initial version of this test assumed it was and failed);
graceful degradation of ranking correlation under genuine truncation;
Schur's own exactness at a planted eigenvalue equal to the reference
energy, and its lift's exact eigenvector reconstruction there; the
honest converse -- a real, nonzero residual for a Ritz value far from the
reference energy, confirming the approximation-cost caveat isn't just
asserted; the dumbbell synthetic gate (TASK-0103's own 44-node fixture,
ported not re-derived) confirming both methods preserve a planted
long-range coupling signal.

**Two real bugs found and fixed before trusting any real-target number**:
(1) `schur_complement`/`lift_schur_eigvecs` did not sort `retain_idx`
internally -- a caller passing residues in a non-ascending order (e.g.
`ACTIVE + BRIDGE + DRUG + DECOY`, a natural way to assemble a retained
set) got a silently permuted `H_eff` whose row/column `i` no longer
matched original residue `i`, corrupting any index-based scoring against
it. Caught directly: the dumbbell test's own Schur smoke test failed
with a wrong AUC until this was found and fixed; both functions now sort
`retain_idx` ascending internally, a fixed, predictable convention.
(2) the real-target script's Louvain-baseline scoring broadcast each
cluster's raw occupation value to every member residue -- copying, not
dividing, which inflates the "distribution"'s total sum by cluster size
and produced Bhattacharyya coefficients above 1 (impossible for two
genuine probability distributions, caught directly from an out-of-range
number, not assumed correct because the script ran without error).
Fixed: divide by cluster size before broadcasting.

**Real, load-bearing structural finding, not anticipated in this task's
own filing**: a block-Krylov seed of `n_seed` residues consumes `n_seed`
Ritz dimensions per round-robin power step. At this project's real
active-site sizes (KRAS_G12C 18, BCR_ABL1 26, CARDIAC_MYOSIN 18) and the
~12-16 node NISQ compression budget `coarse.py`/`ALGORITHM_REGISTER.md`
§H both target, **the seed block alone meets or exceeds that entire
budget on all 3 mandatory targets**, before any distal, potentially
pocket-relevant structure can be reached.

**Real-target retention report** (`scripts/
spectrum_preserving_reduction.py`, all 3 mandatory targets, m in
{10,14,18,24,32,50} bracketing each target's own n_active, three axes --
spectral Ritz error, Bhattacharyya occupation fidelity, Spearman rho +
AUC/P@5 delta vs. the real pocket label):

- **Block-seed Krylov breaks sharply, not gradually, at m<=n_active on
  all 3 targets** -- reduced occupation is exactly constant on every
  non-seed residue below that threshold (Spearman rho undefined, AUC
  exactly 0.5), because the seed block's own power-0 vectors already
  exhaust the budget. This is the direct answer to this task's own
  "report the compression ratio at which the ranking breaks" ask.
- **Confirmed a block-seed artifact, not a Krylov limitation**: a
  supplementary single-representative-seed check on KRAS_G12C reaches
  rho=0.56, AUC=0.612 at the identical m=10 the block-seed version fails
  completely at, closely tracking that single seed's own full-system
  reference (0.662) -- see Open Questions for the convention tension
  this exposes.
- **Schur beats the existing Louvain baseline on 2/3 targets,
  decisively on KRAS_G12C** (ΔAUC +0.038 to +0.148 at every tested m,
  vs. Louvain's constant -0.307) **and loses on BCR_ABL1** (ΔAUC
  consistently negative, -0.080 to -0.194) -- reported as a genuine,
  unforced cross-target inconsistency. Schur's spectral error stays
  small (~0.01) near the E=0 reference energy but grows large (up to
  5.05) far from it -- the approximation-cost caveat, measured not just
  stated. Schur's own ranking rho is non-monotonic in compression size
  on every target even as ΔAUC generally improves -- overall shape
  correlation and specific pocket-discriminative power are shown to be
  different properties.
- **Louvain (existing baseline) is the least reliable of the three**:
  its natural resolution on these graphs (~10-15 communities) means most
  tested `n_target` values produce zero forced merging (the identical
  partition returned regardless of requested budget, reported plainly),
  its ranking is sometimes anti-correlated with the true occupation
  (rho -0.03 to -0.11 on 2 targets at the smallest cluster counts), and
  its AUC swings are the largest and least consistent of the three
  methods tested (-0.415 to +0.297).

**Verdict on the challenge's own "prove retention" requirement**: mixed,
reported honestly. A controlled reduction (Schur) does measurably beat
the existing lossy baseline on the majority of mandatory targets and
gives a real, quantified retention number instead of none -- but it is
not uniformly better, and the other controlled method (Krylov, in this
project's own established multi-residue block-seed convention) fails
outright at the compression scale the NISQ resource study actually
needs. No submission-operator change made (Tier-2-gated, [[TASK-0100]],
out of this task's own scope) -- this is a retention measurement, not a
recommendation to swap `run_challenge.py`'s own coarse-graining step.

**RESULTS.md**: new dated section + open-questions row 74 (both
appended). Full `pytest tests/ -q`: 1164 passed, 1 skipped, 3 xfailed,
0 failed (includes this task's own 17 new tests).

**Re-verified against a concurrent fix landed mid-task, not assumed
compatible**: [[TASK-0217.001]] (another thread, same day) fixed a real
array-correspondence bug in `labels.functional_indices` affecting
`active_site`/`pocket` on 10 of 13 targets including KRAS_G12C/BCR_ABL1
-- both targets this task's own retention report depends on for its seed
and label. Before committing, re-ran `spectrum_preserving_reduction.py`
against the current (fixed) `labels.py`: all 3 targets reproduced their
already-reported `n_active`/full-AUC values bit-for-bit
(KRAS_G12C 0.6189640035118525, BCR_ABL1/CARDIAC_MYOSIN unchanged too) --
this task's own exact call path (`build_labels` -> `functional_indices`
with the new cross-structure resname translation wired in) turns out to
be a no-op for these 3 targets specifically (apo/holo correspondence is
already index-aligned for them), unlike [[TASK-0217.001]]'s own cited
`test_fpocket_pin.py` case. Checked directly, not inferred from the fix
being "additive."

**Not done, explicitly out of scope or descoped**: partial trace /
reduced density matrix (not applicable, stated in this task's own
filing); VQE on the reduced Hamiltonian (out of scope, this task's own
filing); self-consistent (energy-dependent) Schur evaluation (Open
Questions, fixed-E chosen instead); extending the real-target sweep
beyond the 3 mandatory targets or beyond m=50 (a real, stated time-budget
scope call, not a compute-cost necessity -- each real-target cell costs
well under a second).
