# TASK-0171 Spectrum-preserving Hamiltonian reduction (Krylov / Schur complement) with a retention proof

## Context

- ID: TASK-0171
- Title: replace/augment the current naive community-merge coarse-graining
  with a **controlled** reduction that provably preserves the transport
  signal — Krylov subspace projection (exact for the seeded walk) and
  Löwdin/Feshbach–Schur partitioning (exact elimination of the discarded
  residues) — and report a quantitative retention metric.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: raised by the orchestrating collaborator (Oussama), 2026-07,
  asking how to compress H so that only transport-relevant residues are
  retained (originally proposed via partial trace / density matrix — see
  the correction below).
- Priority: **P1 — this closes a stated challenge requirement that the
  current code does not meet.**
- Renumbering note: originally filed as TASK-0158; renumbered to 0171
  because `results_task0158_compact_null/` had already claimed 0158.

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
   (Concretely: `Tr_B(sigma_x ⊗ sigma_x) = sigma_x · Tr(sigma_x) = 0` —
   the entire interaction vanishes.)

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

- [ ] Verify the Löwdin / Feshbach / Novo citations directly.
- [ ] Implement Krylov (Lanczos) projection from the active-site seed.
- [ ] Implement Schur-complement / Löwdin elimination, diagonal retained.
- [ ] Synthetic gate: planted long-range coupling survives reduction?
- [ ] Retention report: spectral error, dynamical fidelity, and ranking
      rho / AUC delta vs compression ratio.
- [ ] Head-to-head vs existing `coarse.py` Louvain/spectral baseline.
- [ ] Report the compression ratio at which the ranking breaks — that
      number is the answer to the challenge's "prove it retains the
      signal" requirement, whichever way it comes out.

## Dependency

- [[TASK-0094]] (Done) — proximity floor.
- [[TASK-0112]] (Done) — bootstrap CI.
- [[TASK-0130]] (Done) — converged propagator this reduces.
- `coarse.py` (Done, Phase 4) — the baseline this must beat, and the
  module whose diagonal-dropping behaviour motivated this task.

## Open Questions

- Krylov dimension m: fixed, or chosen by residual tolerance? State and
  justify.
- Schur complement is energy-dependent — evaluate at a fixed reference
  energy (state which, and why) or self-consistently? Implementer's call.
- Should the retention report use the converged observable or a finite-t
  one? Converged is the shipped readout; state the choice.

## Done

(not yet)
