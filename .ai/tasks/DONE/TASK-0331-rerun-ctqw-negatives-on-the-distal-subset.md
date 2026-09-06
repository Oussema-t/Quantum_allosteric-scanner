# TASK-0331 — Re-run this register's CTQW negatives on the distal subset: our own scope defect

- Status: Done
- Owner: **Reviewer thread** (this is our defect, not upstream's)
- Priority: High — it qualifies negatives the submission currently leads with
- Filed: 2026-09-06 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0320]], [[TASK-0325]], [[TASK-0310]], [[TASK-0287]], [[HYP-P8]], [[HYP-P13]]

## The defect, stated against our own work

[[TASK-0320]] and [[TASK-0325]] ran on the **unfiltered** ASBench cohort — 105
structures, no distality filter. Two independent measurements now say most of
that cohort cannot test a propagation method at all:

- Collaborator's unified benchmark (1233 structures, 5 datasets, cluster-level):
  only **23%** of curated allosteric sites and **7%** of drug-contact pockets
  are genuinely distal (hop ≥ 2, > 12 Å). The cryptic datasets
  (CryptoBench / CryptoSite / PocketMiner) have **median hop = 0** — the pockets
  sit essentially at the active site. **Cryptic ≠ distal, now measured.**
- `allosteric/README.md` on the same benchmark: *"only 13% of targets have an
  allosteric site far enough from the active site to test propagation at all —
  for the rest, 'finding' it demonstrates proximity."*

**A propagation method evaluated where there is nothing to propagate across is
being tested off-target.** Our negatives inherit that scope limit and we should
say so before a reviewer says it for us.

Residualising on proximity partly covers it — where sites are proximal,
proximity explains them and CTQW ≈ proximity is the expected result, which is
what [[TASK-0310]] measured (best residual 0.5598 across 7 observables). But on
a genuinely distal subset the question is **reopened, not settled.**

## Intent Contract

- Outcome: [[TASK-0320]]'s reverse-seeded arms and [[TASK-0325]]'s gate ablation
  re-run on the distal subset only — the collaborator's `curated_allosteric`
  distal subset (~95 structures, ASBench-led at 45% distal) is the honest
  denominator. Report alongside the full-cohort numbers, not instead of them.
- Why required, not assumed: the direction of the effect is genuinely unknown.
  Distal sites are where a walk *should* have room to work, and they are also
  where the cohort is smallest and the statistics weakest. Both outcomes are
  publishable; the current silence is not.
- In Scope: both scripts take a cohort filter cleanly; the walk is the
  expensive part and it is ~16 min for 105 structures, so a ~95-structure
  re-run is cheap. Add the distal flag to the stored per-structure rows so the
  split is auditable afterwards.
- Constraints And Invariants:
  - **Power first.** With ~95 structures and far fewer independent clusters,
    state the detectable effect size *before* interpreting a null — this
    register has already published one "no signal" that was really "no power"
    ([[TASK-0313]]'s addendum). If the distal subset cannot detect proximity
    itself as a positive control, it cannot rule anything out, and that is the
    finding.
  - Keep the two truth types separate (curated_allosteric vs drug_contact) —
    they have different distal fractions (23% vs 7%) and pooling them hides it.
  - The ligand-contamination caveat from [[TASK-0329]] applies here too.
- Planned Validation: proximity as positive control must clear on the distal
  subset before any CTQW number from it is interpreted.

## Consequence for the submission

Wherever the draft states a CTQW negative on ASBench, it needs the denominator
attached: *measured on a cohort in which most annotated sites are not distal.*
That is a stronger, more precise claim than the unqualified negative — and it
sets up the distal subset as the honest test, which is a Phase-2 hook rather
than an omission.

## Done (2026-09-06, Implementer D)

Full results: `results/tasks/0331_distal_subset_rerun/distal_subset_rerun.json`.
Script: `scripts/task0331_distal_subset_rerun.py`.

**References** (both live-verified via Crossref, not re-derived from memory
— [[TASK-0304]]'s own original sourcing, restated here directly since this
task's entire denominator rests on them and a standalone reader should not
have to chase an internal link for it):
- **ASBench** — Wu, N., Strömich, L., Yaliraki, S.N. (2022). "Prediction of
  allosteric sites and signaling: Insights from benchmarking datasets."
  *Patterns* 3(1):100408. DOI: 10.1016/j.patter.2021.100408.
- **CASBench** — Zlobin, A.S., Suplatov, D.A., Kopylov, K.E., Švedas, V.K.
  (2019). "CASBench: A Benchmarking Set of Proteins with Annotated Catalytic
  and Allosteric Sites in Their Structures." *Acta Naturae* 11(1):74-80.
  DOI: 10.32607/20758251-2019-11-1-74-80.

**Distal set, vendored not re-derived**: `origin/allosteric` branch @ `f257789`,
`allosteric/datasets/pocket_distance.csv`, filtered to `source=='asbench' &
truth_type=='curated_allosteric' & is_distal==True` — 49 distinct PDBs, 44.95%
of ASBench's 109 curated_allosteric rows, matching the filing's own "ASBench-
led at 45% distal" to the second decimal. `truth_type` separation (Constraint)
is satisfied by construction: this register's ASBench truth (`allosteric_
residues`) has only ever been `curated_allosteric` — it has never scored
against the collaborator's `drug_contact` cohort, so there is nothing to pool.
The `hop≥2 AND >12 Å` distal threshold itself is the collaborator's own
operational definition, not drawn from either paper above — neither ASBench
nor CASBench's own publications specify a distality cutoff in Ångströms; this
register's independent calibration ([[TASK-0255]]) landed on a similar but
not identical bar (external suggestion 15–20 Å). Stated plainly rather than
implied: the 12 Å figure is a working definition, not a literature constant,
and the two independent calibrations agree on order of magnitude, not on
the exact number.

**No re-run of fpocket or the walk** — both are filter-invariant (TASK-0320's
own symmetry identity), so this is a post-filter of the per-structure/per-
candidate dumps `task0320b_reverse_seeded_asbench.py` already wrote, same
pattern TASK-0325 itself used. 45/49 distal PDBs (43 distinct, 2 carry a
second annotated site) have rows in the existing 105-structure dump; the other
6 were never in that run at all (not in the TASK-0305 KEEP set, N>MAXN, or
excluded for the same reasons as the rest of that 105/118 run — not
re-diagnosed here). `is_distal` written onto every row of the full 105-row
set for auditability (Scope), not just the retained subset.

**Power first (Constraint) — and this is the finding.** On the n=45/35-protein
distal subset, proximity itself — the one signal this register has reliably
detected everywhere else — does **not** clear significance: median rho
+0.0643, 19/35 proteins positive, Wilcoxon p=**0.89**. Full cohort, same
statistic: median +0.1514, p=0.00035. **The distal subset cannot detect its
own dominant confound, so it cannot rule anything in or out.** Per the task's
own Constraint, that is the finding, not a caveat on the finding.

Reported anyway, explicitly flagged uninterpretable: CTQW raw median −0.0049
(p=0.45, was +0.109/p=0.005 full-cohort), CTQW|proximity median −0.0511
(p=0.15, was −0.015/p=0.36 full-cohort). Permuted-label null still centres on
zero for both (as it must — it is a null, not a power source). **Not** a
sharper negative than the full-cohort one — a null result from an underpowered
design, indistinguishable from "nothing to detect at this n."

**TASK-0325's gate ablation, same subset**: qualitatively unchanged from the
full cohort — the gate (top-K druggability) still does essentially all of the
retention work (26.7%/46.7%/84.4% vs full cohort's 34.3%/46.7%/82.9% at
top-3/5/half), CTQW still does not beat random-within-gate or fpocket
druggability at any gate width, and `nres`/`drug` remain the strongest
selectors throughout. The top-3 gate's own per-arm rho is undefined (n<4
candidates after filtering, same `ConstantInputWarning`/`nan` the full cohort
already produces at that gate — not new to the subset).

**Ligand-contamination caveat carried forward, not resolved** ([[TASK-0329]],
still TODO): every row here, distal or not, was scored by running fpocket on
the deposited (ligand-bound) structure. Both the subset and full-cohort
numbers share that defect equally, so the *comparison* between them is not
confounded by it, but neither number is a clean measurement of distality
alone — TASK-0329 is the task that would fix the input, not this one.

**Verdict for the submission**: the honest sentence is *"on the ~45-structure
genuinely-distal subset of ASBench, this register's design cannot detect
proximity itself, so the CTQW result there is undetermined, not negative —
distinct from the well-powered full-cohort negative, which stands."* Both
numbers belong in the draft together, per the Intent Contract's own framing:
this is a Phase-2 power problem (bigger distal cohort needed, e.g. pooling
in CASBench's own 46 distal structures — untouched here, task0320b/0325 never
scored CASBench and extending to it is a new run, not a filter, so out of
this task's scope) — not a settled negative and not evidence CTQW works on
distal sites either.
