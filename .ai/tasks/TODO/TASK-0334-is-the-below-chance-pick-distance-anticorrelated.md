# TASK-0334 — Is the pipeline's below-chance pocket pick distance-anti-correlated? Turn a negative into a mechanism

- Status: TODO
- Owner: **Implementer A** (built `reference_arms.py`; owns the pocket-level metric)
- Priority: High — it is the difference between "the walk subtracts value" and a publishable mechanism
- Filed: 2026-09-06 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0327]], [[TASK-0320]], [[TASK-0310]], [[TASK-0331]], [[HYP-P9]], [[HYP-P21]]

## Why

[[TASK-0327]] measured the pipeline at **8.9% pre-veto against a random-order
null of 18.4%** on held-out data — below chance — and read it as the CTQW stage
"actively subtracting value". That phrasing treats an anti-correlation as a
defect. It is more likely a **mechanism**, and this register already holds the
pieces: the walk tracks proximity (ρ(ctqw, proximity) = **+0.808** at candidate
level, [[TASK-0320]]), and where the annotated site is genuinely distal a
proximity score must *anti*-predict it.

**Unverified inference, which is exactly why this is a task.** If it holds,
"the walk measures distance, and distance anti-predicts distal truth" is a
result. If it does not, the below-chance number needs a different explanation
and "subtracts value" cannot stand either.

## Intent Contract

- Outcome: for each protein in [[TASK-0327]]'s held-out set, the distance from
  the active site to (a) the pocket the pipeline ranks #1, (b) the true drug
  pocket, (c) a random candidate. Report the correlation between the
  pipeline's pocket rank and pocket-to-active-site distance.
- Prediction, stated before the run: the pipeline's #1 pick is **closer** to
  the active site than the true pocket, and its rank correlates negatively
  with distance. A null result refutes the proximity-mechanism reading.
- In Scope: read-only over stored artifacts — `s14_r{1,2}_k10_h2_*.json` carries
  `ranks`, `seed_resnum`, `seed_pocket`, `pockets`; the `allosteric` branch's
  `pocket_distance.csv` ([[TASK-0331]] already vendored it) carries the
  distances. No walk re-run, no PDB refetch.
- Constraints: use [[TASK-0327]]'s **held-out** cohort definition
  (`LEAKY_SOURCES = {"asbench"}` only) — ASBench is PASSer's training data and
  pooling it back in reintroduces the confound that task corrected for twice.
  Report the full-cohort number alongside, not instead.
- Planned Validation: the *true* pocket's own distance distribution must match
  `pocket_distance.csv`'s `is_distal` flag on the same rows. If it does not,
  the join is wrong and no correlation from it is trustworthy.

## Consequence

Whichever way it lands, [[TASK-0332]] needs the answer before the submission
states anything about why the walk fails. "Subtracts value" is currently in a
Done file and will be quoted.
