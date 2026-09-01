# TASK-0312 — The observed CTQW active→pocket vs pocket→active asymmetry: artifact, bug, or category error?

- Status: Done
- Priority: Medium — cheap, and it retires a standing observation rather than letting it be built on
- Filed: 2026-09-01 by Reviewer thread
- Revised: 2026-09-01 by Reviewer thread — hypothesis set corrected from two to
  three after a synthetic control (below) excluded H2 outright and showed the
  originally-proposed fix for H1 is a no-op on the statistic actually reported
- Related: [[TASK-0162]], [[TASK-0171]], [[TASK-0308]], [[TASK-0118]], [[TASK-0140]]

## The claim to test

It has been observed in this project that the CTQW propagates differently
seeded from the active site toward the pocket than from the pocket toward
the active site.

**For our Hamiltonian, that should be impossible.** `H_new` is real and
symmetric (contact matrix plus diagonal potentials) and — verified, not
assumed — **seed-independent**: `reverse_direction_coupling_test_holo.py`
builds `H_new` once from coords and propagates both directions on that same
operator (lines 126–131). For the converged/decoherent limit this pipeline
actually reports, the pairwise transfer kernel is

```
M_ij = Σ_B (P_B)_ij²        P_B = spectral projector on degenerate block B
```

`P_B` is a real symmetric projector, so `M_ij = M_ji` exactly, for all `i, j`.
**Site-to-site transfer is exactly symmetric; there is no directionality
available**, at any seed placement, at any seed-set size.

## What the reported statistic actually is

This is the correction that reframes the whole task. `TASK-0162`/`TASK-0171`
do **not** report the set-level transfer scalar. Per
`reverse_direction_coupling_test_holo.py:139-146`, each direction produces a
**score vector over the whole protein**, and three separate quantities are
derived:

| Quantity | Forward | Reverse | Constrained by `M = Mᵀ`? |
|---|---|---|---|
| set-level transfer scalar | `Σ_{i∈A,j∈P} M_ij / \|A\|` | same sum `/ \|P\|` | **yes** — ratio is exactly `\|P\|/\|A\|` |
| `auc_forward` vs `auc_reverse` | `AUC(M[A,:], pocket_label)` | `AUC(M[P,:], active_label)` | **no** |
| `background_spearman_rho` | `ρ(M[A,bg], M[P,bg])` | — | **no** |

Rows 2 and 3 compare **two different rows of a symmetric matrix, against two
different label vectors**. Symmetry constrains `M_AP = M_PA`; it says nothing
about how `A` and `P` each view some third residue `j`. A rank correlation
below 1 on the background set is therefore *guaranteed* and carries **zero**
information about time-reversal symmetry.

## The three hypotheses

1. **Normalisation artifact.** True, and exact — but **only for the set-level
   scalar**, which is not what was reported. Seeding from `S` and reading at
   `T` divides by `|S|`; the reverse divides by `|T|`; the ratio is exactly
   `|T|/|S|`. **Status: confirmed exactly by the control below.**
   *The originally-proposed remedy — "divide both directions by the same
   quantity" — is a no-op on the statistic that was actually reported.*
   Spearman is invariant under positive rescaling. Do not re-run it expecting
   a change.
2. **Implementation defect** in the propagator or the seeding.
   **Status: EXCLUDED on synthetic topology** — `max |M − Mᵀ| = 1.11e-16`,
   machine precision. Not yet re-confirmed on real target topologies.
3. **Category error (the live hypothesis).** The asymmetry is real, is
   correctly computed, and does not mean what it was read to mean. It measures
   whether the active site and the pocket have similar *views* of the rest of
   the protein — a substantive question about protein structure — and not
   directionality of transport. **If this holds, the directionality reading
   must be retired as meaningless, not as arithmetically explained.**

## Control already run (2026-09-01, synthetic)

60-node random contact graph, real symmetric seed-independent `H`,
`time_averaged_ctqw_converged`, `|S| = 20`, `|T| = 12`:

```
max |M − M.T|             : 1.11e-16            ← propagator clean (H2 excluded)
set S→T / T→S ratio       : 0.600000 = |T|/|S|  ← H1 exact
bg spearman rho           : 0.077176
  after matched rescaling : 0.077176            ← proposed H1 fix is a NO-OP
coherent, matched norm    : 4.0825 vs 3.9807    ← 2.5% residual, seeds only
```

## Scope

- [x] Repeat the `max |M − Mᵀ|` control on 2–3 **real** target topologies
      (`build_H_new` on KRAS_G12C, BCR_ABL1). Synthetic passing is necessary,
      not sufficient — a real spectrum has the near-degenerate structure that
      `degenerate_tol` grouping acts on. If it fails, stop and debug.
- [x] Confirm on real targets that the set-level scalar ratio is exactly
      `|T|/|S|`, closing H1.
- [x] Decide H3 explicitly: state in `RESULTS.md` and in `TASK-0162`/
      `TASK-0171`'s Done sections that `background_spearman_rho` and the
      forward/reverse AUC pair are **not** tests of transport directionality,
      and that no directional claim may be sourced to them.
- [x] **Audit the `coherent=` default.** `time_averaged_ctqw_converged`
      defaults to `coherent=True` (`propagators.py:1016`). Under coherent
      seeding the seed set is one superposition and cross-seed interference
      survives matched normalisation (2.5% above) — it *looks* like
      directionality and is not. The two reverse-direction scripts pass
      `coherent=False` explicitly and are safe. Grep every other call site for
      a missing `coherent=` kwarg and record which convention each took.

## Out of scope

- Re-litigating `TASK-0162`/`TASK-0171`'s AUC numbers. They are what they are;
  this task governs only what may be *concluded* from them.

## Note

If H1 and H3 hold together — as the mathematics says they must — then genuine
directionality requires **breaking time-reversal symmetry**, i.e. **complex
hopping amplitudes** (a chiral quantum walk / synthetic gauge phase). That is
not a re-analysis of what we have; it is a different Hamiltonian, and it
connects directly to [[TASK-0310]]'s lead candidate and to [[TASK-0140]].

The reason H3 matters more than H1: the two-hypothesis framing implied that a
*corrected normalisation* could still rescue a directional signal from the
existing data. It cannot. No re-analysis of a real symmetric `H` can produce
directionality, because the quantity is symmetric to machine precision.

## Done (2026-09-01, Implementer B)

**All three hypotheses now closed on real target topology, not just the
60-node synthetic control.** `scripts/task0312_ctqw_seed_asymmetry.py`
builds `M` directly from `H_new`'s own spectral decomposition
(`M = Sum_B P_B**2`, same `degenerate_tol=1e-6` default and holo-native
active-site/pocket labelling as [[TASK-0171]]'s own script, reused not
re-derived) on KRAS_G12C (N=167), BCR_ABL1 (N=429), and CARDIAC_MYOSIN
(N=709) — three targets, not the two named in Scope, since the third
was cheap and a real spectrum's near-degenerate structure is exactly
what needed checking on more than one topology:

| target | N | max\|M−Mᵀ\| | fwd/rev ratio | \|pocket\|/\|active\| | matches |
|---|---|---|---|---|---|
| KRAS_G12C | 167 | 0.000e+00 | 0.944444 | 0.944444 | yes |
| BCR_ABL1 | 429 | 0.000e+00 | 0.615385 | 0.615385 | yes |
| CARDIAC_MYOSIN | 709 | 0.000e+00 | 0.722222 | 0.722222 | yes |

**H2 (implementation defect): EXCLUDED**, now confirmed on real
topology — `max|M-Mᵀ|` is exactly 0.0 (not merely machine-epsilon) on
every target tested. `degenerate_tol` grouping does not introduce any
asymmetry on a real, near-degenerate spectrum.

**H1 (normalisation artifact): CONFIRMED exactly**, on real topology —
the forward/reverse set-level scalar ratio equals `|pocket|/|active|` to
1e-9 relative tolerance (effectively exact; the residual is pure
floating-point summation order, not a real deviation) on all three
targets. Whole run: three eigendecompositions plus two O(N²) matrix
constructions, **under 3 seconds wall-clock, well within this task's own
"cheap" priority** — no memory or load concern at all, unlike the
compute-heavy tasks running concurrently in this window.

**H3 (category error): decided, addenda added to both source tasks**.
[[TASK-0162]] and [[TASK-0171]]'s own Done sections each got a dated
note (not an edit to their original conclusions, which were never
directionality claims to begin with and stand unchanged): neither
`background_spearman_rho` nor the forward/reverse AUC pair may be read
as evidence of transport directionality going forward. `RESULTS.md`
gets the same statement in its own new section (see below).

**`coherent=` audit — grepped every call site of
`time_averaged_ctqw_converged` across `src/` and `scripts/` (not a
sample)**:

- The default itself (`propagators.py:1016`) is `coherent=True`, as
  stated in this task's own filing.
- Two library-level wrapper functions (`allostery.analysis`'s
  `H_new_vs_ctqw`-family functions, `allostery.ceiling`'s trial runner)
  keep their own `coherent: bool = True` default and pass it straight
  through — a caller of *those* functions who doesn't override it
  inherits the same convention one level removed. Not traced further
  (out of this task's own scope, which governs `TASK-0162`/`TASK-0171`'s
  observable directly, not every downstream consumer of these wrappers).
- **Every production analysis script found** that calls
  `time_averaged_ctqw_converged` with a genuinely multi-residue `source`
  passes `coherent=False` explicitly — this is the dominant, established
  convention across `task0238`–`task0310` (30+ scripts checked), matching
  [[TASK-0118]]'s panel-recommended convention, not an exception.
- **One exception found**: `scripts/hardware_feasibility_verdict.py:79`
  calls `time_averaged_ctqw_converged(H_full, source=active_idx_full)`
  with `active_idx_full` a multi-residue array and no `coherent=` kwarg
  — silently coherent. That script measures coarse-graining fidelity
  retention (Spearman rho between full and coarse-grained occupation),
  not directionality, so this default is unlikely to matter for its own
  conclusion, but it is undisclosed there and flagged here for whoever
  owns that script next, not fixed in this task (Out of Scope: no new
  observable/re-analysis beyond what closes H1–H3).
- Every other bare-`source=` call site checked (test files, `analysis.py`
  internal calls) either uses a scalar source (identical under either
  convention, per the function's own docstring) or is itself a
  passthrough of an outer `coherent` parameter, not a silent default.

**Verdict**: the asymmetry is real, correctly computed where
`coherent=False` was used, and is a **category error**, not a bug or a
fixable normalisation issue. `background_spearman_rho`/forward-reverse
AUC measure whether the active site and the pocket have similar *views*
of the rest of the protein — a real, substantive structural question —
not transport directionality. Genuine directionality would require
breaking time-reversal symmetry (complex hopping amplitudes), which is a
different Hamiltonian, not a re-analysis of this one — connecting
forward, undiminished, to [[TASK-0310]] and [[TASK-0140]] per this
task's own Note.

**Script**: `scripts/task0312_ctqw_seed_asymmetry.py`. **Data**:
`results/tasks/0312_ctqw_seed_asymmetry/ctqw_seed_asymmetry.json`.

**Moved TODO/IN_PROGRESS -> DONE.**
