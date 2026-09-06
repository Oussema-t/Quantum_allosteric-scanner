# TASK-0329 — The apo-ligand veto protection is label-adjacent: run the leakage gate

- Status: Done
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

## Done (2026-09-06, Implementer B)

**Headline: real, measurable leakage, decisively shown two independent ways
— on the SAME cohort [[TASK-0327]]/[[TASK-0328]] already measured
(`origin/allosteric` @ `f257789`, local worktree, nothing pushed
upstream).**

### Direct mechanism test (the decisive evidence — no counterfactual re-run needed)

A property of the veto decision itself, not a re-scored walk: of the
pockets the current veto keeps, how often is that survival attributable
**only** to the ligand exception (low PocketMiner accessibility, saved
purely by ligand contact) — compared between the TRUE (drug) pocket and
every OTHER candidate in the same protein (a paired, within-protein
design, so it isn't confounded by which proteins happen to have
ligands):

| | exception-only survivors | rate |
|---|---|---|
| TRUE (drug) pocket | 10/74 | **13.5%** |
| Every OTHER candidate | 10/313 | **3.2%** |

**The true pocket is 4.2x more likely than an arbitrary candidate to
depend specifically on the ligand exception to survive the veto.** This
is exactly the label-adjacency this task was filed to check for, shown
directly rather than inferred.

### Minimum contract: exception removed / label-independent proxy

Real PocketMiner accessibility was re-run fresh — no per-residue score
for this exact 138-structure cohort was ever committed anywhere in the
`allosteric` branch's own history (`git log --all` on every
`pm_out`/`.resnums.json` path, zero hits) — using the already-vendored
Docker image ([[TASK-0269]]/[[TASK-0285]]), 132/138 structures exported,
123/132 scored, 103/132 usable after a resnum-alignment check (9 failed
inside PocketMiner itself, matching that tool's own established
per-structure error handling; 20 more had a harmless off-by-a-few
residue-count mismatch against this task's own CA export and were
excluded rather than force-aligned). Ligand contact was computed fresh
from raw apo-PDB HETATM records (4.5 Å, `build_veto_hpc.py`'s own
JUNK-exclusion list) rather than trusted from `apo_bound_ligands.json`
alone — that summary file is missing 28/138 proteins entirely
(CASBench/CryptoBench rows, confirmed by direct lookup).

**Reconstruction validated, not assumed**: predicted keep
(accessibility-high OR ligand-contact) vs. round-2's own real surviving
pockets agrees on 82.3% of 623 checked pocket-decisions (91 proteins
with usable PocketMiner + ligand data). Not perfect — a fresh PocketMiner
run and an independently-computed ligand-contact set will not
byte-for-byte reproduce whichever exact run produced the original
`veto_keep.json` — disclosed as a real limitation on the arms below,
not smoothed over.

| arm | n | pooled-cell hit rate | drug pocket survives veto |
|---|---|---|---|
| A: current (ligand-aware) veto, as actually run | 67 | **14.6%** | — |
| A′: same, RECON SUBSET (fair baseline for B/C) | 65 | 14.5% | — |
| B: accessibility-only (exception removed) | 82 | **11.2%** | 78.0% |
| C: accessibility at matched retention rate | 82 | 11.8% | 69.5% |

**A → B/C is a ~3-point drop, ~20% relative** — consistent with, and a
second independent confirmation of, the direct-mechanism finding above.
A′ tracking A closely (14.5% vs 14.6%) confirms the RECON subset isn't a
biased sub-sample driving this.

### Second arm: ligand-free vs. ligand-present subset

18/91 proteins have no ligand contacting any candidate pocket at all
(exception structurally vacuous there); 73/91 have at least one.
**Underpowered and not directionally confirmatory** — disclosed
honestly rather than only reporting the arm that fits the headline:
ligand-free (n=9 scoreable) hit rate 20.2%, ligand-present (n=56) hit
rate 13.5%. Read at face value this points the *opposite* way from
"ligand presence inflates the number" — but n=9 is far too small to
draw a real conclusion, and this raw split confounds ligand-presence
with whichever proteins happen to lack one (protein identity/difficulty,
not controlled here). **The direct-mechanism test above is the
trustworthy evidence; this arm is reported per the task's own Intent
Contract, not because it independently confirms anything.**

### A real upstream data-consistency finding, flagged for Oussema

`veto_keep.json`'s own "10" entry disagrees with what `pocketsweep.py`'s
actual round-2 run carried forward for at least one protein
(`ASB_1W25`: pocket 1 listed as kept in `veto_keep.json`, absent from
round 2's own real `pockets`). Found while validating the "best member
wins" reduction ([[TASK-0327]]'s own identity) against `veto_keep.json`
directly (68-89% agreement, unexpectedly low) — re-validated against
round-2's own real `pockets` list instead (97-99% agreement for 10 of
14 score families; `residLOG`/`residLOG_dX`/`residRAW`/`residRAW_dX`
never validate above ~87%, some per-round rescaling not chased down,
excluded from every arm above). Round-2's own real output, not
`veto_keep.json`, is what every number in this Done section is
validated against.

### Constraints honored

Retained-candidate count (n, kept-fraction) reported alongside every
accuracy number throughout, per this task's own Constraint. Nothing on
the `allosteric` branch was pushed or altered — read-only worktree,
removed after use. No veto redesign attempted or proposed (Out Of
Scope) — this task measures the current rule; a recommendation (narrow
or remove the exception, or disclose the leakage explicitly wherever
this veto's numbers are quoted) is Oussema's call, not implemented here.

**Scripts**: `scripts/task0329_apo_ligand_veto_leakage.py`. **Data**:
`results/tasks/0329_apo_ligand_veto_leakage/{veto_leakage_result.json,
chain_resolution.json,pocketminer_io/}`.

**Moved TODO/IN_PROGRESS -> DONE.**
