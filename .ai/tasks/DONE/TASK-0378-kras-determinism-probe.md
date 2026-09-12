# TASK-0378 — Is KRAS's number stable? Ten re-runs, but varying the thing that could actually differ

- Status: Done
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

## Done (2026-09-12, Implementer C)

**Pre-registered prediction holds for every decision-relevant quantity;
holds almost, but not quite literally, to the last digit for the raw
occupation vector — reported precisely, not rounded up.**

### Setup — ten runs, each a genuinely fresh process

`OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS`/
`NUMEXPR_NUM_THREADS`/`VECLIB_MAXIMUM_THREADS` ∈ [1,2,4,8,1,2,4,8,1,2],
each run a real `subprocess` spawn (`task0378_kras_determinism_child.py`),
not a loop in one interpreter — thread-count env vars are read at
process/BLAS-init time only, so a loop would have tested nothing, exactly
the naive-version failure this task was filed to avoid. All 10 runs are
independently in a separate interpreter invocation, clearing the
"at least one" bar by 10x.

### Planned Validation — passed exactly before any cross-run comparison

Run 1: `score_auc = 0.5136485966935793`, floor `hop_from_seed =
0.5288350634371395` — both equal [[TASK-0376]]'s committed values to
every printed digit (`==`, not a tolerance check).

### Result — reproducible at every decision-relevant precision

| quantity | max deviation across all 10 runs |
|---|---|
| `score_auc` | **0.0** (exact) |
| floor AUC | **0.0** (exact) |
| top-5 residue set | identical in all 10 (min pairwise Jaccard 1.000) |
| full `winner_occ` vector | 4.7e-15 (not literally byte-identical) |

AUC, floor, and ranking — everything a decision is ever made on — are
bit-for-bit identical across all 10 runs and all 4 thread counts. The
raw per-residue vector differs at the 4.7e-15 level: ordinary
floating-point non-associativity from a different BLAS summation order
at different thread counts, not a defect, ~10 orders of magnitude below
anything that could move an AUC's third decimal. Reported as a genuine,
if practically inert, deviation rather than rounded up to "byte-identical"
— this task's own filed Constraint says any variation is a finding.

### Degenerate-subspace hazard — measured directly, absent on this structure

`4LDJ`'s winner Hamiltonian (N=170): **0 of 169 eigenvalue gaps** fall
below the shipped `degenerate_tol` (1e-6 × bandwidth = 2.147e-6 absolute).
Smallest real gap: 1.44e-4 — **67x above the threshold**. Stated with a
number, per this task's own instruction, not left as an argument.

### Item 4 — variation was found (at the 1e-15 level), so the degenerate_tol follow-up ran

Per this task's own "if and only if variation is found," the 4.7e-15
`winner_occ` deviation counted as variation and triggered a fixed-thread
(1), `degenerate_tol`-swept follow-up (0, 1e-10, 1e-8, 1e-6, 1e-4, 1e-2):

| `degenerate_tol` | `score_auc` | top-5 |
|---|---|---|
| 0, 1e-10, 1e-8, 1e-6 (shipped) | 0.5136485966935793 (identical) | unchanged |
| 1e-4 | 0.5151864667436 | unchanged |
| 1e-2 | 0.4975009611688 | **changed entirely** |

Confirms the mechanism is real in principle — a tolerance set two-plus
orders of magnitude above the shipped default does move the answer,
because it starts grouping the real 1.44e-4 gap — but the **production
default sits three orders of magnitude below where any effect starts**,
consistent with the direct gap measurement above. Nothing was changed;
this is the "measure, then file" instruction, not a fix.

### Read against the already-named causes, per this task's own framing

**The pre-registered prediction holds where it matters**: KRAS's number
is exactly reproducible, and the input choice — not run-to-run noise, not
thread count, not the degenerate-subspace hazard, on this structure — is
what moves it. Apo draw ([[TASK-0155]]), structure swap
([[TASK-0270]]/[[TASK-0376]]), clock ([[TASK-0350]]), and seed set
([[TASK-0102]]) remain the real, already-measured sources of spread; this
task rules out a fifth candidate rather than finding a sixth.

### Out of scope, honored

Did not re-measure the four already-named spread sources. Did not change
the shipped KRAS number, structure, or residues. Did not touch fpocket.

### Landed

New hypothesis **HYP-P30** in `physics.md`. `INDEX.md` regenerated;
`hyp_register_check.py` shows only pre-existing staleness flags, none
from this entry.

**Files**: `__WORK_IN_PROGRESS__/scripts/task0378_kras_determinism_child.py`,
`__WORK_IN_PROGRESS__/scripts/task0378_kras_determinism_probe.py`. **Data**:
`__WORK_IN_PROGRESS__/results/tasks/0378_kras_determinism_probe/
{summary.json,run_*.json,tol_run_*.json,run_log.txt}`.
