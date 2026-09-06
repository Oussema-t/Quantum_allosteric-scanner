# TASK-0331 — Re-run this register's CTQW negatives on the distal subset: our own scope defect

- Status: TODO
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
