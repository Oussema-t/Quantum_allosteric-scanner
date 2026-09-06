# TASK-0329 — The apo-ligand veto protection is label-adjacent: run the leakage gate

- Status: TODO
- Owner: **Oussema** (owns the veto) — Reviewer thread supplies the ASBench measurement
- Priority: High — it protects the headline config's best candidates
- Filed: 2026-09-06 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0317]], [[TASK-0325]], [[TASK-0320]], [[TASK-0328]], [[TASK-0254]]

## The rule under test

Stage 4 vetoes pockets PocketMiner predicts stay closed, **except** pockets
whose residues contact a ligand already bound in the apo file
(`apo_bound_ligands.json`) — "those are demonstrably open".

The exception uses **ligand occupancy in the input to protect a candidate**,
and ligand location is adjacent to the label. The upstream README already
concedes the size of it: *"the apo-ligand protection partly leaks: ~50% of
these 'apo' structures already have the effector bound. On truly empty sites
the veto gain will be smaller."*

[[TASK-0317]] deliberately ran on `asbench_without_ligand` as its primary
condition rather than the with-ligand variant. This rule reverses that choice.

## What this register measured independently, and why it is worse than it looks

Sampling the ASBench structures actually fetched by [[TASK-0320]]:
**40 / 40 carry non-solvent HETATM ligands**, median 2 distinct, and they are
the textbook effectors — FBP on 1A3W, AMP+FDP on 1FRP, TRP on 1I7S, GTP on
1JLR. `task0320b_reverse_seeded_asbench.py:96` writes the deposited structure
into fpocket verbatim; nothing strips HETATM anywhere in this register's
ASBench path either. **This is a shared defect, not an upstream one.**

**Stripping the ligand does not fix it.** fpocket, deposited vs HETATM-stripped:

| pdb | candidates dep → strip | max druggability dep → strip |
|---|---|---|
| 1B86 | 35 → 37 | 0.460 → **0.962** |
| 1DKU | 33 → 33 | **1.000 → 0.427** |
| 1G3L | 97 → 97 | 0.774 → **0.342** |

Detection is stable; scoring swings hard **in both directions**. So fpocket does
consume HETATM — but removing atoms does not close a pocket, because the
*conformation* stays holo. Only a genuine apo structure of the same protein
fixes this. Anyone planning "strip the ligands" as the remedy should see this
table first.

## Intent Contract

- Outcome: a leakage gate, reported before any veto number is claimed again.
  Minimum: re-run the headline config with the apo-ligand exception **removed**,
  and separately with the exception replaced by a label-independent proxy
  (e.g. PocketMiner accessibility percentile alone). The gap between those and
  the current number is the leakage.
- Second arm, if the cohort allows: restrict to the ~50% of structures the
  README identifies as *not* already effector-bound, and report the veto gain
  there. That subset is the only place the veto's claimed mechanism can be
  tested cleanly.
- Constraints: report the retained-candidate count alongside every accuracy
  number. A veto that discards the true pocket caps the metric regardless of
  what ranks inside it — [[TASK-0325]] measured a top-3 gate discarding the
  true pocket in **65.7%** of structures, and round 2 here already loses 58 of
  138 proteins ([[TASK-0328]]).
- Out Of Scope: redesigning the veto. This task measures the current one.

## Note

The register-wide question this raises is bigger than one rule: **no ASBench
result in this register was computed on ligand-free input.** That does not
damage the negatives — contamination inflates positives — but it does mean
every *comparative* baseline measured on ASBench (notably [[TASK-0320]]'s
"raw cavity size is the best selector at 17.1%") is measured on ligand-open
pockets and favours geometric methods. Those specific claims need the caveat
attached wherever they are quoted, including in the submission draft.
