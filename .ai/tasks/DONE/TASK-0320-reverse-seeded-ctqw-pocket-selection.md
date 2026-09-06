# TASK-0320 — Reverse-seeded CTQW (pocket → active site) as a pocket-selection method

- Status: Done
- Priority: Medium — a collaborator question, cheap to answer, and it either opens a new arm or closes one with an argument
- Filed: 2026-09-03 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0287]], [[TASK-0282]], [[TASK-0305]], [[TASK-0308]], [[TASK-0310]], [[TASK-0312]], [[TASK-0319]]

## The question, as asked

From the collaborator: compare a CTQW seeded at the **active site** against one
seeded at the **candidate pockets**, measuring how much amplitude reaches the
active site — and use that as an additional pocket / allosteric-site guessing
method.

## The algebra, settled before anything was run

`H_new` is real symmetric and **seed-independent** (built once from coordinates;
[[TASK-0312]] verified the converged kernel `M_ij = Σ_B (P_B)²_ij` is symmetric
to **1.11e-16**). Therefore, for a candidate pocket `P` and active site `A`:

```
transfer(P → A) = (|A|/|P|) · Σ_{i∈P} p_A(i) = |A| · mean_{i∈P} p_A(i)
```

where `p_A` is the ordinary **forward** occupation seeded at the active site.
Verified numerically to machine precision (ratio came out **20.0000 = |A|**
exactly).

`|A|` is constant within a structure, so **ranking candidate pockets by
reverse-seeded transfer is identically ranking them by mean forward CTQW
occupation.** The reverse direction contributes no information.

**What is genuinely untested, and why this task exists rather than closing on
the algebra alone:**

1. **Aggregation.** This register scored CTQW at *residue* level (P@5,
   per-residue AUC). Mean-per-candidate-pocket is a different statistic, and
   mean vs sum differs by candidate size — the dominant confound [[TASK-0287]]
   found in fpocket druggability. Both are scored.
2. **Task level.** Selecting among fpocket candidates is not ranking residues.

**Pre-registered prediction** (recorded before either run): CTQW residualises to
proximity ([[TASK-0308]]/[[TASK-0310]]), and [[TASK-0287]] measured that
distance-to-seed does *not* select the true pocket among fpocket candidates
(0.393 raw p=0.065; 0.478 conditioned p=0.70), because every target has
candidates sitting on its own active site. So this should fail the same way.

## Arm A — frozen set (n=19 targets / 13 clusters). DONE, and it could not adjudicate

`scripts/task0320_reverse_seeded_pocket_ranking.py`, reusing
`task0282_pocket_selection_sweep.build_target` unchanged (it already computes
`mean(ctqw_full[ii])` per candidate — no propagator call re-implemented).

| arm | top-1 hit | median rank of best | mean EH |
|---|---|---|---|
| `ctqw_mean` (= reverse transfer) | **0.0%** | 15.0 | 0.0162 |
| `ctqw_sum` | 10.5% | 9.0 | 0.0408 |
| `prox_min_euclid` | 10.5% | 17.0 | 0.0305 |
| `fpocket_drug` | **21.1%** | 11.0 | **0.0969** |
| random | — | 20.0 | 0.0287 |

**A pseudo-replication trap, caught:** row-level Wilcoxon gave rho +0.146,
**p=0.0070** residualised — apparently significant. Cluster-robust
([[TASK-0261]], 13 clusters) it is **p=0.067**. The duplicated rows name
themselves: `HCV_NS5B_VRX`/`VR1` both rho=+0.0354, `POO`/`CMF` both −0.0577.
Fifth selection procedure in this register to hit this.

**Why this arm cannot settle the question:** proximity itself — the confound
known to dominate every residue-level score here — scores median rho **+0.24 at
cluster-p 0.36**. *A design that cannot detect proximity cannot rule anything
out.* Underpowered, not a clean negative — the [[TASK-0288]] vs Silverman
distinction, applied to ourselves.

## Arm B — ASBench. DONE, and it adjudicates

`scripts/task0320b_reverse_seeded_asbench.py`. Same question, ~5× the
independent units, which is the power Arm A lacks.

- **Seeds**: ASBench's **own** `active_residues` annotations
  (`results/tasks/0304_asbench_casbench/asbench_annotations.json`), not our
  `detect_active_site` — the field's labels, so the seed choice is not ours.
- **Truth**: ASBench's own `allosteric_residues`; the target candidate is the
  one best *recalling* that set ([[TASK-0282]]'s oracle definition, reused).
- **Structures**: the [[TASK-0305]] `KEEP` set, Cα-only, first altloc, N ≤ 3000.
- **Operator**: `build_H_new(coords, bfactors, cutoff=8.0)`;
  `time_averaged_ctqw_converged(..., coherent=False)`.
- **Candidates**: vendored `tools/fpocket/bin/fpocket` via
  `t0242.fpocket_candidates`, keyed on (chain, resnum) per [[TASK-0298]].
- **Clustering**: by protein.

**Stated deviation from Arm A, a judgement call not an inherited default:**
proximity here is **Cα**-space distance to the nearest seed residue, where Arm A
used heavy-atom (`min_heavy_atom_dist_to_seed`). The contact graph, `H_new` and
the walk are all Cα-based; a heavy-atom control would mix resolutions between
the score and the thing controlling it, which is the confound this test exists
to remove. Consequence: the two arms are not perfectly comparable on that axis.

### Result — n = 105 structures / 75 proteins, clustered by protein

| arm | top-1 hit | median rank of best | recall @ top |
|---|---|---|---|
| `n_res` (pocket size alone) | **17.1%** | 7 | 0.1739 |
| `fpocket_drug` | 16.2% | 6 | **0.1793** |
| `ctqw_sum` | 8.6% | 7 | 0.0944 |
| `prox_min` | 7.6% | 14 | 0.0726 |
| **`ctqw_mean`** (= reverse transfer) | **1.9%** | 17 | 0.0287 |
| random | — | 28 | 0.0294 |

| arm | median rho | positive | Wilcoxon p | |
|---|---|---|---|---|
| proximity — **power check** | +0.1514 | 55/75 | **0.00035** | detected |
| fpocket druggability | +0.0986 | 59/75 | **4.5e-07** | detected |
| ctqw raw | +0.1091 | 50/75 | 0.0050 | detected |
| **ctqw residualised on proximity** | **−0.0150** | 36/75 | **0.36** | **vanishes** |

`rho(ctqw, proximity) = +0.808` at candidate level — a *purer* distance proxy
than the +0.735 measured at residue level ([[TASK-0308]]).

**Negative control (permuted-label null, 200 reps, whole pipeline re-run):**
null centres on zero for both arms (−0.0007 ± 0.0167 / −0.0001 ± 0.0169).
Raw CTQW: 0/200 null reps reach the observed value. Residualised CTQW sits at
the 81st percentile of its own null — unremarkable. **Both controls pass, so
this is a measured absence, not a blunt instrument.**

**Verdict: reverse-seeded CTQW does not select allosteric pockets.** Its entire
candidate-ranking signal is proximity to the seed it was launched from. The
strongest selector in the whole table is raw cavity size — [[TASK-0287]]'s size
confound again.

**Scope correction, 2026-09-06 ([[TASK-0335]]), added before critic review —
this Arm B measurement is narrower than "reverse-seeded CTQW does not select
allosteric pockets" reads.** The 105-structure / 75-protein cohort above is
the unfiltered ASBench cohort, since found to be (a) predominantly
non-distal — only ~45% of ASBench's own curated-allosteric pairs are
genuinely distal at all ([[TASK-0331]]), and (b) scored on the deposited,
ligand-bound structures, not ligand-free ones — **all 40 sampled structures
carry a bound ligand** ([[TASK-0329]]). Neither defect is unique to this
task (both are shared by every ASBench result in this register, [[TASK-0329]]
itself says so) and neither *creates* this arm's negative — a propagation
score losing to raw cavity size does not become a propagation score winning
once the cohort is fixed. But it does mean **the "raw cavity size at 17.1%"
row specifically is measured on ligand-open pockets, a regime that favours
a purely geometric selector by construction** (the cavity is already open in
the input), and should not be read as cavity size's ceiling on genuinely
apo, closed pockets. The corrected sentence for the submission: *on the
unfiltered, ligand-open ASBench cohort, at pocket selection, reverse-seeded
CTQW loses to raw cavity size — not "CTQW cannot select allosteric pockets"
in general.* Not weakened as a negative (per [[TASK-0335]]'s own
Constraint) — this measurement stands exactly as run; only its stated scope
is corrected.

## A process finding, worth more than the result

The collaborator brief's first draft listed *complex hopping amplitudes / a
chiral walk* as an open route. **[[HYP-P9]] had recorded it FAIL on 2026-07-23**,
and `src/allostery/chiral.py` implements exactly that (Peierls substitution,
complex-Hermitian `H`). The claim was written from inference rather than from
the hypothesis register — in a file this same session had already edited. Caught
by the repo owner, not by us.

Two corrections landed: the brief's §6 now reads *closed*, and [[HYP-P9]]'s own
status has been brought current with [[TASK-0310]]'s residualised re-test, which
it had never absorbed. **The hypothesis register is under-consulted when briefs
are written, and stale on the newest evidence when it is consulted.** That is a
scaffold problem, not a physics one, and it is the more valuable finding here.

## Scope

- [x] Verify the symmetry identity numerically before running anything.
- [x] Arm A, frozen set, cluster-robust.
- [x] Arm B, ASBench, clustered by protein.
- [x] **Negative control** — permuted-label null, both arms, null centres on zero.
- [x] Collaborator brief: `documentation/REVERSE_CTQW_BRIEF.html`, covering
      script, seed choice, Hamiltonian, structures, and how both baselines were
      computed — plus worked explainers for residualisation and significance.
- [x] [[HYP-P9]] brought current.

## Constraints

- **Cluster-robust or it does not count.** Arm A already produced a false
  positive at row level.
- **Report the power check.** Any negative must state whether the design could
  detect proximity; without that, "no effect" and "no power" are not separated.
- Do not re-implement the propagator or the candidate apparatus — reuse
  [[TASK-0282]]'s and [[TASK-0242]]'s.

## Note

The honest framing for the collaborator is that the *direction* was never the
variable — it is algebraically fixed — but the *question behind it* (does
CTQW-derived amplitude select a pocket, at pocket rather than residue level) had
not been asked, and is worth the run. That distinction is the answer, not a
deflection of it.
