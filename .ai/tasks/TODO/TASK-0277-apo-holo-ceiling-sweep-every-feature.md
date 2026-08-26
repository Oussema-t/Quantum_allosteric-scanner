# TASK-0277 — Apo↔holo ceiling sweep across every feature this register has ever scored

- Status: TODO
- Assignee: unassigned (suggest whoever finishes [[TASK-0275]] — it is the same machinery at wider scope)
- Priority: **High — but sequence it after [[TASK-0275]] and [[TASK-0276]], see Sequencing**
- Filed: 2026-08-26 by Reviewer
- Related: [[TASK-0275]], [[TASK-0276]], [[TASK-0254]], [[TASK-0256]], [[TASK-0259]], [[TASK-0260]], [[TASK-0263]], [[TASK-0266]], [[TASK-0269]], [[TASK-0274]]

## The observation

**Every feature this register has ever scored has been computed on apo, and
none has an apo↔holo ceiling measurement.** [[TASK-0275]] covers the five
potential terms plus CTQW; [[TASK-0276]] asks the existence question at the
discrimination level. Neither covers the rest of the stack.

That leaves us unable to answer a simple question about our own results: **is
the apo penalty uniform across features, or concentrated in particular ones?**

- **Concentrated in the dynamical features** (CTQW, `V_C`, `dcc_low`,
  `prs_low`, classical diffusion) ⇒ dynamics specifically needs the bound
  conformation, and the Phase 2 target is conformational generation.
- **Uniform across everything** ⇒ it is a global conformational problem, not a
  feature-specific one, and no feature choice will fix it.

Those imply different Phase 2 proposals. We currently cannot tell them apart.

## Features to sweep, with leakage grade — the grades are the design

Leakage is **not uniform**, and a blanket holo run would produce meaningless
numbers for several of these. Grade before running, and carry the grade into
every reported number.

| feature | source | holo arm | grade |
|---|---|---|---|
| `degree_centrality`, `euclid_from_seed_centroid`, `hop_from_seed` | `baselines.py` | run | imprint-only |
| `V_B`, `V_T`, `V_R`, `V_C`, `V_M` | `potentials.py` | **[[TASK-0275]] owns these — do not duplicate** | imprint-only |
| CTQW (`time_averaged_ctqw_converged`) | `propagators.py` | **[[TASK-0275]] owns this** | imprint-only |
| `dcc_low`, `prs_low` | `lowmode_predictor.py` | run | imprint-only |
| classical diffusion (`ground_state_relaxation`) | [[TASK-0256]] | run | imprint-only |
| frustration | [[TASK-0268]] | run | imprint-only |
| SASA | [[TASK-0266]] | run, **flagged** | moderate — burial changes materially on binding |
| **fpocket** | [[TASK-0163]] | **exclude, or report separately as maximally leaky** | severe — cavity detector, holo cavity is drug-shaped |
| **P2Rank** | [[TASK-0260]] | **exclude, same reason** | severe |
| **PocketMiner** | [[TASK-0269]] | **exclude, same reason** | severe |
| conservation, chemistry | [[TASK-0274]] | **no holo flavour exists** | see below |

### Conservation and chemistry have no holo flavour — and that is itself a result

Both are **sequence- and residue-type-derived**, so they take *identical*
values on apo and holo. Their contribution cannot improve with a better
conformation, by construction.

**State this explicitly in the write-up.** It independently confirms that
[[TASK-0274]]'s negative (conservation −0.08%, p=0.6946; chemistry −0.35%,
p=0.6492) is **not** a conformation problem — those features had every
structural advantage already and still contributed nothing. That closes an
objection nobody has raised yet, cheaply.

## Scope

- [ ] Compute each non-excluded feature on both apo and holo for
      [[TASK-0243]]'s frozen set, scored against the **same** pocket label
      (label from holo as always — only the feature-side coordinates change).
- [ ] Report the per-feature **apo AUC, holo AUC, and gap**, with the leakage
      grade in the same row. One table; that table is the deliverable.
- [ ] **Test the central question**: is the gap concentrated in the dynamical
      features or uniform? Use a cluster-robust comparison of gap
      distributions between the dynamical group and the static group, not an
      eyeball read.
- [ ] Stratify every gap by crypticity ([[TASK-0254]] part B: 9 of 20 targets
      ≥80% open). The prediction inherited from [[TASK-0275]]: gaps should
      concentrate on cryptic targets. **If the gap is uniform across cryptic
      and open, crypticity is not what the apo penalty is made of** — and
      [[TASK-0259]]'s ρ=−0.771 needs re-reading.
- [ ] Cluster-robust significance throughout ([[TASK-0261]], 13 clusters).
- [ ] Reconcile against [[TASK-0275]] and [[TASK-0276]] before reporting. If
      this sweep finds large holo gains while [[TASK-0276]] finds no
      allosteric-vs-orthosteric separation in holo, the features are tracking
      the drug's imprint rather than allostery — and **that tension is the
      finding**, not something to resolve in favour of the nicer number.

## Sequencing

**Run after [[TASK-0275]] and [[TASK-0276]] land.** 0275 owns the potential
terms and CTQW; duplicating them here wastes compute and risks two
inconsistent numbers for the same quantity in `RESULTS.md`. 0276's existence
result determines how this sweep's gaps should be interpreted at all.

If either is still in flight, this task's non-overlapping features
(`dcc_low`, `prs_low`, classical diffusion, frustration, geometry) can be run
independently — but do not publish the consolidated table until all three
reconcile.

## Acceptance

- [ ] One consolidated table: feature × {apo AUC, holo AUC, gap, leakage
      grade, crypticity-stratified gap}.
- [ ] An explicit verdict on concentrated-vs-uniform, with a cluster-robust
      p-value.
- [ ] The conservation/chemistry no-holo-flavour observation stated, with its
      consequence for [[TASK-0274]]'s negative.
- [ ] Explicit reconciliation with [[TASK-0275]] and [[TASK-0276]].
- [ ] `RESULTS.md`, every holo number labelled a ceiling.

## Constraint

**Nothing from the holo arm is predictive performance.** These are ceilings
measured with the answer partially in hand. Any number from this task that
appears in `documentation/PHASE1_SUBMISSION_DRAFT.md` or
`documentation/CTQW_CONTRIBUTION_BRIEF.html` must carry that label in the same
sentence — a holo AUC quoted without its flavour would be the most damaging
single error this register could ship, because it would look like a result we
do not have.
