# TASK-0378 — Is KRAS's number stable? Ten re-runs, but varying the thing that could actually differ

- Status: TODO
- Owner: **Implementer**
- Priority: **High. Cheap, and it either rules out a whole class of explanation or finds a defect in the scoring path.**
- Filed: 2026-09-12 by Reviewer thread (id via `claim.py reserve-next`)
- Source: Team Lead, 2026-09-12 — *"re-run KRAS 10 times and see if the results are stable… those back-and-forth flips just don't seem right"*
- Related: [[TASK-0155]], [[TASK-0102]], [[TASK-0124]], [[TASK-0350]], [[TASK-0376]], [[TASK-0270]]

## The instinct is right. The naive version of the test is not

Something does keep moving on KRAS, and it is worth pinning down. But a plain
"run it ten times" will almost certainly return the **identical** number ten
times, because the scoring path looks deterministic:

- `propagators.py:91` — the occupation observable is `p = np.abs(amplitudes) ** 2`,
  **sign-safe by construction**, so `eigh`'s arbitrary per-eigenvector sign cannot
  move it.
- The only RNG in `propagators.py` is line 1137 and it is **explicitly seeded**;
  `protocol.py:581`'s leak check likewise takes an explicit seed.

**So run it ten times anyway — but the run must vary what could differ, or it
measures nothing.** Ten identical calls in one process is not a stability test; it
is a test that Python is deterministic.

## The one real hazard: degenerate subspaces

`time_averaged_ctqw_converged` carries `degenerate_tol: float = 1e-6`.

**Within a degenerate (or near-degenerate) eigen-subspace, `eigh` returns an
arbitrary orthonormal basis.** Only the *summed projector* over that subspace is
invariant; the individual `|v_k|²` terms are **not** invariant under rotations
inside it. A different LAPACK build, a different thread count, or a different
machine can legitimately return a different basis for the same matrix — and any
per-mode quantity would then move without anything being wrong with the input.

**That is a mechanism that would produce exactly the "back-and-forth flips" the
Team Lead is describing**, and it is checkable.

## In scope

1. **Ten re-runs that actually vary something.** Same structure (`4LDJ`), same
   config, but sweep: `OMP_NUM_THREADS` / `OPENBLAS_NUM_THREADS` /
   `MKL_NUM_THREADS` ∈ {1, 2, 4, 8}, fresh process each time, and at least one
   run in a separate interpreter invocation. Record the full observable vector,
   not just the AUC — **an AUC can be stable while the ranking underneath moves.**
2. **Compare exactly.** Byte-identical is the expected and desired answer. Report
   max absolute deviation across runs for the AUC, the score vector, and the
   **top-5 residue set** (Jaccard). Any variation at all is a finding, not noise.
3. **Measure the degeneracy directly.** For `4LDJ`'s `H_new`, report the
   eigenvalue gap spectrum: how many gaps fall below `degenerate_tol` (1e-6 of
   bandwidth), and the smallest few. **If there are no near-degenerate pairs the
   hazard is absent and we can say so with a number** rather than an argument.
4. **If and only if variation is found**: establish whether it comes from the
   degenerate subspace by re-running with `degenerate_tol` varied, and report
   which observables are affected. Do not fix anything in this task — measure,
   then file.

## Out of scope

- **Re-measuring the sources of spread that are already measured.** They are not
  what this task is for, and it should say so in its own report so the two are
  not conflated (see below).
- Any change to the shipped KRAS number, structure, or residues.
- fpocket. [[TASK-0376]] already re-ran it fresh against `4LDJ`.

## The flips are real, and they already have named causes

Stated here so this task's result is read against them rather than instead of
them. **None of these is run-to-run noise** — every one is a *choice* moving the
answer, which is a different and more interesting problem:

| source | measured spread | where |
|---|---|---|
| **Apo draw** | ten true-G12C apo structures give AUC **0.408–0.595**, median 0.482 | [[TASK-0155]] |
| **Structure swap** | fpocket **0.835 → 0.420** on the `4OBE`→`4LDJ` swap; cardiac apo substitution moved AUC by **0.27** | [[TASK-0270]]/[[TASK-0376]], [[TASK-0124]] |
| **Clock** | **46%** of structures flip resid-AUC *sign* between `T=15` and the converged limit | [[TASK-0350]] |
| **Seed set** | 70–75% of biologically arbitrary single-residue seeds reproduce BCR_ABL1's headline | [[TASK-0102]] |

**If this probe comes back perfectly deterministic — the likely outcome — that is
worth having.** It converts "the numbers jump around" into "the numbers are
exactly reproducible and the *input choice* is what moves them," which is a
sharper and more defensible statement, and it is already what the submission
argues.

## Planned Validation

Run 1 must reproduce the committed KRAS values **exactly** —
`score_auc = 0.5136485966935793`, floor `hop_from_seed = 0.5288350634371395`
([[TASK-0376]]'s own artifact) — before any comparison across runs is trusted. If
run 1 does not match the committed number, the harness is wrong and the task
stops there rather than reporting a spread that is really a setup error.

## Pre-registered prediction

**Deterministic, to the last digit, across all ten.** Stated so a surprise is
legible as a surprise. If it is not deterministic, that is a defect in the
scoring path and it outranks everything else currently open.
