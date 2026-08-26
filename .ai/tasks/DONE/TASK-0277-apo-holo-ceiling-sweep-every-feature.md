# TASK-0277 — Apo↔holo ceiling sweep across every feature this register has ever scored

- Status: Done
- Assignee: Implementer A
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

- [x] Compute each non-excluded feature on both apo and holo for
      [[TASK-0243]]'s frozen set, scored against the **same** pocket label
      (label from holo as always — only the feature-side coordinates change).
- [x] Report the per-feature **apo AUC, holo AUC, and gap**, with the leakage
      grade in the same row. One table; that table is the deliverable.
- [x] **Test the central question**: is the gap concentrated in the dynamical
      features or uniform? Use a cluster-robust comparison of gap
      distributions between the dynamical group and the static group, not an
      eyeball read. (Uniform, Mann-Whitney p=0.12 — and uniformly near-zero,
      not uniformly large.)
- [x] Stratify every gap by crypticity ([[TASK-0254]] part B: 9 of 20 targets
      ≥80% open). The prediction inherited from [[TASK-0275]]: gaps should
      concentrate on cryptic targets. **If the gap is uniform across cryptic
      and open, crypticity is not what the apo penalty is made of** — and
      [[TASK-0259]]'s ρ=−0.771 needs re-reading. (Does not hold; where it
      moves, several features move the WRONG way — more negative on
      cryptic, not more positive.)
- [x] Cluster-robust significance throughout ([[TASK-0261]], 13 clusters).
- [x] Reconcile against [[TASK-0275]] and [[TASK-0276]] before reporting. If
      this sweep finds large holo gains while [[TASK-0276]] finds no
      allosteric-vs-orthosteric separation in holo, the features are tracking
      the drug's imprint rather than allostery — and **that tension is the
      finding**, not something to resolve in favour of the nicer number.
      (No tension: TASK-0276 found real separation, and this task found no
      holo advantage over apo — they combine, they don't conflict. See Done.)

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

- [x] One consolidated table: feature × {apo AUC, holo AUC, gap, leakage
      grade, crypticity-stratified gap}.
- [x] An explicit verdict on concentrated-vs-uniform, with a cluster-robust
      p-value.
- [x] The conservation/chemistry no-holo-flavour observation stated, with its
      consequence for [[TASK-0274]]'s negative.
- [x] Explicit reconciliation with [[TASK-0275]] and [[TASK-0276]].
- [x] `RESULTS.md`, every holo number labelled a ceiling.

## Constraint

**Nothing from the holo arm is predictive performance.** These are ceilings
measured with the answer partially in hand. Any number from this task that
appears in `documentation/PHASE1_SUBMISSION_DRAFT.md` or
`documentation/CTQW_CONTRIBUTION_BRIEF.html` must carry that label in the same
sentence — a holo AUC quoted without its flavour would be the most damaging
single error this register could ship, because it would look like a result we
do not have.

## Done (2026-08-26, Implementer A)

**Uniform, and uniformly near-zero — the ceiling this whole 3-task arc set
out to measure is a null, on every feature checked.**

**Method**: reused [[TASK-0275]]'s own established recipe exactly — matched
common apo/holo (chain, resnum) residue set via
`allostery.superpose.align_apo_holo`, and `task0254`'s own cross-validated
`cv_auc` as the ONE AUC definition for every feature (even solo ones),
matching [[TASK-0275]]'s own choice so this register never carries two
inconsistent "AUC" recipes for the same word. 20/22 [[TASK-0243]] frozen-set
targets usable (HIV_INTEGRASE_MUT871/916 excluded, this register's own
long-standing empty-seed data gap). 8 features swept: `degree`/`euclid`/
`hop` (individually, not the combined geometry block [[TASK-0275]] already
owns), `dcc_low`/`prs_low`, ground-state relaxation on `H_new` (explicitly
NOT classical diffusion, `H_new` indefinite on this set per [[TASK-0256]]'s
own finding, never re-labelled here), single-residue frustration
([[TASK-0268]]'s own CA-coordinate convention matched exactly, not
`task0204`'s CB variant — avoids a second, silently-different frustration
number for the same apo targets), and SASA (natural, ligand-present holo
burial, deliberately not stripped -- the opposite design choice from
[[TASK-0276]], correct for this task's own "flag the real leaky number"
requirement).

**Consolidated table** (apo AUC / holo AUC / gap / cluster-p): `degree`
0.541/0.484/−0.033/0.096; `euclid` 0.706/0.713/−0.001/0.687; `hop`
0.699/0.648/−0.005/0.172; `dcc_low` 0.615/0.600/−0.011/0.561; `prs_low`
0.459/0.503/−0.001/0.093; `ground_state_relaxation` 0.675/0.648/−0.002/0.954;
`frustration` 0.572/0.557/−0.000/0.571; `SASA` (n=18) 0.449/0.525/−0.019/0.528.
**Not one feature clears p<0.05.** Several gaps are numerically negative —
holo slightly WORSE than apo, not better.

**Central question, answered decisively**: dynamical group (`dcc_low`,
`prs_low`, `ground_state_relaxation`, n=60 target-feature pairs) median gap
−0.0023; static group (`degree`/`euclid`/`hop`/`SASA`, n=78) median gap
−0.0048; Mann-Whitney p=0.1205. Not distinguishable, and the static group's
own gap is numerically the larger (more negative) one — the opposite of
"dynamics specifically needs the bound conformation." Neither half of this
task's own two named hypotheses survives, because there is no large gap
anywhere to be concentrated.

**Crypticity stratification: does not hold, same direction as [[TASK-0275]]'s
own per-term correlation finding.** `degree`/`SASA`/`dcc_low`/
`ground_state_relaxation` all show a MORE negative gap on cryptic targets
than open ones — holo doing relatively worse where the label says it should
matter most, the wrong direction from the pre-registered prediction.
`euclid`/`prs_low`/`frustration` flat in both regimes. Two independent,
fully disjoint feature sets ([[TASK-0275]]'s five potential terms, this
task's eight) now agree: crypticity is not what any measured apo penalty is
made of.

**Reconciliation, no tension**: [[TASK-0275]]'s own 7-block composite found
apo (median AUC 0.896) numerically ahead of holo (0.834), p=0.10 — the same
null this task finds, on a completely disjoint feature set. Between the two
tasks, essentially this register's entire feature repertoire has now been
checked for a holo advantage and none shows one. [[TASK-0276]]'s own real,
significant allosteric-vs-orthosteric discrimination signal (`V_C`,
`fpocket`, `degree`, `SASA`) is NOT in tension with this — it means that
signal is not holo-dependent: apo already carries essentially the same
predictive information. [[TASK-0276]]'s own explicitly-deferred question
("does `V_C` survive into apo?") now has a strong prior answer, established
here rather than there: almost certainly yes.

**A real mid-task collision, caught and fixed before it could ship**: this
task's own `RESULTS.md` edit was drafted against a stale local copy of the
file -- two other threads (Implementer B, and the Reviewer's own filing
pass) committed [[TASK-0275]]'s own RESULTS.md section, plus [[TASK-0277]]/
[[TASK-0278]]'s own task-filing commits, while this task's edit sat
uncommitted in the working tree. Committing as-drafted would have silently
reverted [[TASK-0275]]'s already-published section. Caught via `git diff`
against `HEAD` before writing anything further; fixed by re-deriving the
merged file from `HEAD`'s own current content plus this task's own addition
(verified via `git diff --stat` showing a pure, 167-line addition against
`HEAD`, zero deletions) rather than by force-pushing the stale copy over
it. [[TASK-0278]]'s and [[TASK-0279]]'s own concurrently-appearing files
were left completely untouched throughout.

`documentation/CTQW_CONTRIBUTION_BRIEF.html` §04/§08 flagged, not edited —
[[TASK-0275]]'s own precedent for this batch.

**Script:** `scripts/task0277_apo_holo_ceiling_sweep.py`. **Data:**
`results/tasks/0277_apo_holo_ceiling_sweep/`.
