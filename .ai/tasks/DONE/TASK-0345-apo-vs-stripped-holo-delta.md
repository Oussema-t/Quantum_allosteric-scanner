# TASK-0345 — Measure the apo vs stripped-holo delta: the number nobody reports

- Status: Done
- Owner: **Implementer** — triggerable unattended
- Priority: High — it converts a submission row from "not reported" into a result
- Filed: 2026-09-07 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0329]], [[TASK-0331]], [[TASK-0320]], [[TASK-0305]]
- Feeds: `PHASE1_SUBMISSION_V2` §2 component (b) and the §4 impact table

## The claim being tested

Leading cryptic-pocket methods report 89.8% / 98.1% on ASBench / CASBench. Those
evaluations run on **ligand-removed holo** structures, not on genuine apo
depositions. Removing a ligand does not close a pocket — the side-chain
conformation stays open — so a method scored that way is being handed a pocket
that a real apo structure would not contain.

**We have found no report of the delta between the two.** If it is large, every
published cryptic-pocket accuracy number is measuring an easier task than the
one the field believes it is measuring. That is the single most transferable
result available to us before Phase 2, and it is cheap.

## Why it is cheap — measured, not estimated

Timed in this repo against the vendored binary: **5.43 s per fpocket run** on
cached structures. 100 pairs × 3 states = 300 runs ≈ **27 minutes of compute**.
PDB fetches dominate the rest and many are already cached.

The pairs exist: the unified 1233-protein benchmark identified **1042 clean
apo→holo pairs** (CryptoBench / CryptoSite / PocketMiner). These carry no active
site — irrelevant here, because this measurement needs only the pocket, not a
seed. **The cohort that was useless for propagation is exactly the right cohort
for this.**

## Intent Contract

- Outcome: for ≥ 100 apo/holo pairs, pocket detection scored in three states —
  **(1)** genuine apo, **(2)** holo with ligand stripped, **(3)** holo as
  deposited — at the annotated site. Report the (2) − (1) delta: this is the
  headline. Report (3) as the ceiling.
- Metric: fpocket druggability and cavity rank at the annotated site, plus a
  binary "site detected at all". Reuse `task0242.fpocket_candidates` — same
  vendored binary, same `(chain, resnum)` keying as every other result here; do
  not write a second parser.
- Constraints And Invariants:
  - **Cluster by protein and report cluster-robust statistics**, not per-structure
    — this register has lost four selection procedures to pseudo-replication and
    one recent result to exactly this ([[TASK-0337]]).
  - State the ligand-stripping rule precisely: HETATM removal is not
    apo-isation, and [[TASK-0329]] measured that stripping changes fpocket
    druggability in both directions (1DKU 1.000 → 0.427; 1B86 0.460 → 0.962).
    **That variance is part of the finding**, not noise to average away.
  - Deterministic seeds and a fixed structure list written to disk before the
    run, so the cohort cannot drift between re-runs.
  - If the delta is ~zero, **say so** — that is equally publishable and it
    retires our own §2(b) proposal rather than embarrassing us in Phase 2.
- Planned Validation: a handful of pairs scored by hand against the automated
  output before the full run. And a positive control: state (3), deposited holo,
  must score highest of the three; if it does not, the scoring is wrong.

## Note

This is the one experiment in the current plan whose result is interesting
whichever way it lands, and whose cost is under an hour. It should run first.

## Done

**2026-09-07/08, Implementer A.** No blocker found before picking this up
(all 4 related tasks Done, `task0242.fpocket_candidates` imports and runs
cleanly, `tools/fpocket/bin/fpocket`'s Docker wrapper works). Script:
`apo_holo_delta.py` + `analyze.py`, same results directory.

### Cohort — smaller than the filing assumed, stated directly

The filing's "1042 clean apo→holo pairs" figure describes the
collaborator's own unified benchmark, not what is actually vendored in
this repo. `cryptosite_pairs.json` (21) + `pocketminer_pairs.json` (86)
= 107 nominal pairs; 31 PocketMiner entries have no holo counterpart
(rigid/negative-control proteins) or an ambiguous chain spec, excluded
before fetching anything (76 left); 13 more excluded for a `drug_code`
with zero actual ligand contacts in the deposited holo file — **63
validated pairs**, not ≥100. CryptoBench (the dataset that would supply
most of the gap) is deliberately not vendored anywhere in this repo
(`allosteric/README.md`: download from OSF `10.17605/OSF.IO/PZ4A9`) —
not fetched here, a stated scope reduction. 63 is still enough to decide
the question decisively (see Result).

### A real bug caught by Planned Validation before the full run

`task0242.fpocket_candidates` resolves its own `<stem>_out/` output
directory relative to the `work` argument (`cwd` for the underlying
Docker-wrapped fpocket call), **not** relative to the input PDB file's
own directory. The first hand-checked pair returned "no info file" for
all three states until each state's PDB was written directly inside its
own per-state work subdirectory rather than a shared parent — fixed
before the full run, not discovered after.

### Method

Truth pocket derived fresh per pair (not read from `operator_worklist.json`,
which only pre-computed this for 42/107 of these entries): protein
residues within 4.5 Å (this repo's own `pocket_contact_cutoff` default)
of any heavy atom of the named `drug_code` ligand in the holo structure.
Mapped onto the apo structure assuming shared PDB numbering — **checked,
not assumed**: every pair passed a residue-identity gate (≥80%
three-letter-code agreement at the resnums both chains share, ≥50%
of truth resnums present in the apo chain at all) before being scored;
pairs failing this were excluded, not silently misjoined. Three states,
same chain, same `fpocket_candidates` call: (1) genuine apo, (2) holo
with the ligand computationally stripped (HETATM removed, standard/
modified-residue records kept), (3) holo as deposited (unfiltered).

### Planned Validation

3 pairs hand-checked before the full run: all 3 showed the expected
ordering (deposited ≥ stripped ≥ apo, rank 1 in every state) and a real,
positive (2)−(1) delta (+0.019, +0.198, +0.309) — the effect was visible
before the batch run even started.

### Result — the headline number

63 pairs, 59 distinct proteins (checked — near-zero cluster concentration,
this register's own cluster-robustness discipline since [[TASK-0337]] is
satisfied trivially here, not by construction of the analysis).

| | apo (1) | stripped-holo (2) | deposited-holo (3) |
|---|---|---|---|
| detection rate (site found at all) | 96.8% | 100% | 100% |
| mean best druggability at the site | 0.392 | 0.590 | 0.733 |
| mean best rank among candidates | 2.29 | 1.33 | — |

**Headline delta (2)−(1): mean +0.199, median +0.184.** Wilcoxon
signed-rank p=2.6e-4; sign-flip permutation p<1e-4 (B=10000); bootstrap
95% CI on the mean **[+0.102, +0.296]**, excluding zero by a wide margin.
Same sign in both source cohorts (cryptosite +0.247, pocketminer +0.174).

**Positive control**: holds in aggregate (mean/median strictly ordered
apo < stripped < deposited) and in 48/63 (76%) of individual pairs. 15
individual violations spot-checked (3 shown in full in
`analysis_result.json`) look like genuine fpocket score sensitivity to
exact atom composition — rank frequently unchanged even when the raw
score moves — not a detection failure or a parsing bug. Not chased
further than the spot check; disclosed rather than smoothed over.

**Read plainly: a computationally ligand-stripped holo structure looks
~0.2 druggability points more druggable, and ranks nearly a full
position higher, than a genuinely independent apo structure of the same
protein. The delta is real, not ~zero — this task's own Constraint to
"say so" if it were zero does not apply.**

### Landed

New hypothesis **`HYP-P26`** in `physics.md` — a genuinely distinct
external-benchmark-validity mechanism from [[HYP-P21]] (covalent/
peptide-bond-adjacency labeling defect) and from [[HYP-P8]]/[[HYP-P9]]
(confounds internal to this register's own walk), not a fold-in.
Citations verified live before use: Cimermancic et al. 2016, *J. Mol.
Biol.* 428(4):709-719, DOI: 10.1016/j.jmb.2016.01.029 (CryptoSite);
Meller et al. 2023, *Nat. Commun.* 14:1177, DOI:
10.1038/s41467-023-36699-3 (PocketMiner) — cited as the source of the
structure pairs used, not re-tested as papers. `INDEX.md` regenerated;
`hyp_register_check.py` 18/18 tests pass.

### Not done / explicitly out of scope

- CryptoBench not fetched (see Cohort section) — the natural next step
  if a larger cohort is wanted; this task's own ≥100 floor was not met
  literally, disclosed rather than rounded up.
- Did not test whether the same gap holds for learned/ML predictors
  (PocketMiner, PASSer) rather than geometric fpocket — those were
  partly trained on stripped-holo input and might behave differently;
  untested here.
- Did not chase the 15 positive-control violations beyond a 3-pair spot
  check.
- Did not touch `PHASE1_SUBMISSION_V2` — feeding this into §2(b)/§4 is
  for whoever owns that document's drafting pass.

**Files**: `__WORK_IN_PROGRESS__/results/tasks/0345_apo_vs_stripped_holo_delta/
{apo_holo_delta.py,analyze.py,frozen_cohort.json,apo_holo_delta_result.json,
analysis_result.json,cs_pairs.json,pm_pairs.json}`.
