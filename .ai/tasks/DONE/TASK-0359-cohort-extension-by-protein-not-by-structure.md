# TASK-0359 — Limited cohort extension by distinct protein, not by structure

- Status: Done
- Owner: **Implementer B**
- Priority: **High — but hard-capped by the 2026-09-15 deadline; see Budget**
- Filed: 2026-09-09 by Reviewer thread (id via `claim.py reserve-next`)
- Done: 2026-09-09
- Related: [[TASK-0308]], [[TASK-0310]], [[TASK-0350]], [[TASK-0357]], [[TASK-0358]], [[TASK-0337]], [[HYP-P13]], [[HYP-P6]], [[HYP-P7]], [[HYP-P28]]

## Why: our power is limited by proteins, and we have been adding structures

Every quantum-arm null in this register — [[TASK-0350]]'s coherent/decoherent
result, [[TASK-0357]]'s single-delay run, [[TASK-0358]]'s eleven-point scan — is
computed on the **same 108 structures in 76 clusters**. That is **1.42 structures
per cluster**: the cohort is already nearly one-structure-per-protein, so adding
more *structures* buys almost no independent information while inflating the row
count that cluster-permutation has to discount.

**What limits every one of those p-values is the number of distinct proteins, not
the number of structures.** An extension that adds PDB entries for proteins we
already have makes the cohort look bigger and tests nothing new.

### The specific question this unblocks

The external `allosteric` branch reports a family-level effect (+0.107, p=0.007)
that this register cannot reproduce at any delay. Their own document contains the
signature that would explain it:

> *CAS0002 dominance: 28 of 91 distal structures are one protein. Without it CTQW
> 0.617 -> 0.501.*

One family carrying an effect is exactly the "the observable separates **proteins**
rather than **sites within a protein**" failure mode — and leave-one-family-out
does not protect against it, because holding a family out does not remove a
per-family baseline offset from the families that remain. **Testing that requires
more independent proteins. It cannot be answered by more structures of the ones we
have.**

## Intent Contract

- **Outcome:** a cohort extended along the axis that actually carries power —
  distinct proteins — plus the first test of whether our observables separate
  proteins rather than sites.
- **In scope:**
  1. **Add distinct proteins only.** Selection key is the protein (UniProt
     accession / sequence cluster), **not** the PDB entry. A candidate whose
     protein is already represented in the 108 is **rejected**, however good the
     structure. Target: **+40 to +60 distinct proteins**, drawn from the benchmark
     sources already in use — no new benchmark, no new label convention.
  2. **Audit the additions the same way the existing cohort was audited.** 40 of
     40 ASBench structures in the current cohort carry a ligand at the scored
     site; new entries are **not** assumed clean. Apply the existing contamination
     audit and report the contaminated fraction of the extension separately from
     the fraction of the original — do not merge them into one number.
  3. **Re-run exactly two things on the extended cohort**, both existing validated
     code paths, nothing new built:
     - [[TASK-0350]]'s coherent vs decoherent comparison.
     - [[TASK-0358]]'s tau-scan **anchor point only** (`f=1`), signed and unsigned,
       not the full eleven-point scan.
  4. **The protein-vs-site separation test** — the one genuinely new measurement:
     does the score separate *proteins from each other* better than it separates
     *sites within a protein*? State the statistic before running it. A score that
     discriminates protein identity but not within-protein site location is a
     classifier, not a locator, and every family-level p-value in this register
     inherits the finding.
- **Out of scope:**
  - Rebuilding the `allosteric` branch's 435 MIN_HOP=2 structures. Still not worth
    it, and [[TASK-0358]] made it their experiment to run, not ours.
  - Adding structures for proteins already present, for any reason.
  - Reselecting the operator (Tier-2-gated, [[TASK-0100]]).
  - The held `+0.031`. Unchanged.
- **Constraints and invariants:** same labels, same scoring, same cluster-
  permutation convention ([[TASK-0337]]); the original 108 must reproduce their
  committed numbers **unchanged** within the extended cohort before any pooled
  number is quoted.
- **Planned Validation:** the 108 original structures, scored inside the extended
  cohort, must reproduce [[TASK-0358]]'s committed `f=1` values (signed raw 0.5031
  / rho -0.0157 / resid 0.5018; unsigned raw 0.5797 / rho 0.3466 / resid 0.5287).
  If they do not, the extension has changed something it should not have, and the
  task stops there.

## Pre-registration (written 2026-09-09, before any scoring code ran)

### Source for the +40/+60 proteins: CASBench, not a new ASBench pull

`casbench_annotations.json` ([[TASK-0304]]'s own live scrape, 91 CAS entries /
82 resolvable proteins / 2871 structures) is already fetched and already used
in this register (Finding-F distance check, `task0304_casbench_finding_f.py`)
-- reusing it is not a new benchmark. Its own `catalytic_residues` field maps
onto this register's "active site" role and `allosteric_residues` maps onto
the truth label -- same `"RESNAME NUM CHAIN"` token format ASBench's own
`allosteric_residues` already uses, parsed by the SAME `pa()` regex, not a new
convention. CASBench's structures were never previously run through
`build_H_new`/CTQW scoring (only through the Finding-F distance calc) -- this
is a first use for that purpose, disclosed here, not implied to be pre-tested.

### Dedup method: name-alias, not string match alone

Token-overlap between the 76 ASBench protein names and CASBench's 82 flags 33
candidate pairs; several are false positives (shared generic words like
"kinase" or "activated" -- e.g. `Mitogen-Activated Protein Kinase Kinase 1/2/4`
are MAP2Ks, a different gene from MAPK14/MAPK8) and at least two real
duplicates the token match misses entirely on spelling (`Aspartate
Transcarbamoylase` / `Aspartate carbamoyltransferase`; `Phosphotyrosine
Phosphatase 1B` / `Tyrosine-protein phosphatase non-receptor type 1`, i.e.
PTP1B -- one of this project's own mandatory benchmark targets). Adjudicated
by hand against gene identity, not by the token score. **Excluded as
already-represented** (26): 6-Phosphofructokinase Isozyme I, Acetylglutamate
Kinase, Anthranilate synthase, Bovine Seminal Ribonuclease, Casein Kinase II,
Chorismate Mutase, Copper-Containing Nitrite Reductase, Cyclin-Dependent
Kinase 2, D-3-Phosphoglycerate Dehydrogenase, Fructose-1,6-Bisphosphatase,
Glucosamine-6-Phosphate Synthase (= GFAT, alias of
`Glutamine--fructose-6-phosphate aminotransferase`), Glutamate Racemase,
Kinesin-like Protein KIF11, L-Asparaginase, Mitogen-Activated Protein Kinase
8, Mitogen-activated protein kinase 14, Myosin 2, NAD-Dependent Malic Enzyme,
Parathion hydrolase, Pyruvate Dehydrogenase Kinase, Pyruvate Kinase,
Tyrosine-protein kinase ABL1, Uracil Phosphoribosyltransferase, Aspartate
Transcarbamoylase, Dihydrodipicolinate Synthase (= 4-hydroxy-
tetrahydrodipicolinate synthase), Phosphotyrosine Phosphatase 1B (= PTP1B).
**Kept as genuinely distinct** despite a flagged token overlap: Cytochrome
P450 / P450 2B4 (different isoform from the existing CYP3A4), Fructose-1,6-
Bisphosphate Aldolase (different enzyme from the bisphosphatase), MAP2K
1/2/4, Phosphofructokinase-2 (PFK-2, bifunctional, different enzyme from
PFK-1), Proto-oncogene tyrosine-protein kinase Src (different gene from
ABL1), Pyruvate Decarboxylase (different from indole-3-pyruvate
decarboxylase), Tyrosine-protein Kinase ABL2 (different paralog from ABL1).
Remaining candidate pool: **56 proteins** -- inside the +40/+60 target without
needing a second source; if fewer than 40 resolve structurally, that is
reported, not backfilled from a weaker source under time pressure.

### Structure resolution, deterministic, one PDB per protein

Per candidate protein, its CASBench PDB entries are tried in ascending PDB-ID
order until one satisfies every existing cohort gate unchanged: `ca()` fetch
(TASK-0350's own parser), `1 <= N <= 3000`, both residue sets resolve to
>=1 array position each, eligibility mask (`~terminal_mask(0.05) & ~seed`)
leaves `0 < y.sum() < len(y)`, and `build_H_new`/`normalised_laplacian_alpha`/
`hop_from_seed` all succeed -- the exact filter `task0350_coherent_vs_
decoherent.py`'s own cohort loop already applies, unmodified. First protein
found workable, one structure only (matches the existing cohort's near-1:1
ratio; the task's own Why section is explicitly about not adding more
structures per protein). A protein with zero workable PDBs among its
CASBench entries is dropped and counted, not substituted.

### The protein-vs-site separation statistic, defined before it is computed

The failure mode named in this task's own Why section (CAS0002 dominance) is
a **pooled, non-per-structure-normalised** number being carried by one
protein's absolute score *level*, not by within-protein site *location*. The
existing register statistic (`raw_auc`, computed separately per structure
then averaged) is already immune to this by construction -- it cannot be the
test. The new statistic has to expose exactly the channel LOFO does not
close: **can a classifier that sees only *which protein* a residue came from
-- zero within-structure position information -- predict the true-site label
above chance, pooled across the whole cohort?**

Defined: for every eligible residue in every structure, replace its CTQW
score with its OWN structure's mean eligible-score (a pure protein-identity
signal, constant within a structure). Pool every (protein-mean-score, y)
pair across the full extended cohort into one array and compute
`roc_auc_score` on it -- call this **`protein_baseline_auc`**. A per-structure
constant score is a tie within that structure (contributes nothing to a
single-structure AUC, which is why the existing statistic can't see this) but
pooling breaks the tie the moment two structures have different constants
AND different positive fractions -- exactly the leakage channel. Significance
via the same cluster sign-flip convention, permuting which protein's
mean-score-rank pairs with which protein's label-rate. `protein_baseline_auc`
computed separately for (a) the original 108 alone, (b) the extension alone,
(c) pooled -- reported as three numbers, not one, since the mechanism could be
present in one and not the other. `protein_baseline_auc` significantly above
0.5 is itself the finding this task exists to surface, regardless of what the
two re-run arms show.

## Pre-registered prediction

Recorded before the run, and deliberately two-sided. If the nulls hold on a cohort
with ~50% more independent proteins, they get materially stronger and the
submission can say so. If the protein-vs-site test shows our scores separate
proteins better than sites, that is a **finding about every family-level number in
this register**, ours included — not a point scored against the other branch.

## Budget — read before claiming

Six days to the deadline. **This task is capped, not open-ended.** If protein
selection and the contamination audit alone consume more than one working day,
stop and report the extension as filed-but-unrun rather than delivering a
half-audited cohort. A contaminated extension is worse than no extension, because
every pooled number would inherit the contamination silently.

## Dependency

- [[TASK-0358]] (Done) — the harness, the anchor values, and the reason this is
  the right axis.
- [[TASK-0308]]/[[TASK-0310]] (Done) — the existing cohort and its scoring.
- Contamination audit convention — the 40/40 ASBench finding this extension must
  not quietly undo.

## Staged Files

- [2026-09-09 20:26] `__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V3.md` -- rewrite the QAOA non-proposal; name the two surviving quantum routes
- [2026-09-09 20:26] `__WORK_IN_PROGRESS__/documentation/2026-09-09-allosteric-branch-message-DRAFT.md` -- message draft to the allosteric branch, not sent
- [2026-09-09 20:26] `.ai/COMMON.md` -- registry row
- [2026-09-09 20:26] `.ai/tasks/TODO/TASK-0359-cohort-extension-by-protein-not-by-structure.md` -- the task file itself

## Done (2026-09-09, Implementer B)

**All three parts delivered inside the one-day budget. The extension holds
(+54 proteins, 70% more independent clusters); both re-run nulls hold or
strengthen; the new protein-vs-site test fires — decisively, on real data,
in this register's own cohort, not hypothetically.**

### Selection: 54 new distinct proteins, CASBench, hand-adjudicated dedup

Source: `casbench_annotations.json` ([[TASK-0304]]'s own live CASBench
scrape, already fetched, reused here for CTQW scoring for the first time —
disclosed as a new use, not implied pre-tested). 82 CASBench proteins carry
both site types; 26 excluded as already-represented by hand-adjudicated
name/gene identity against the existing 76 (token-overlap flagged 33
candidates, several false positives on generic words like "kinase", and
caught two real duplicates the token match missed on spelling alone —
`Aspartate Transcarbamoylase`/`carbamoyltransferase` and `Phosphotyrosine
Phosphatase 1B` = PTP1B, one of this project's own mandatory targets — see
the pre-registration above for the full exclude/keep list and reasoning).
56 candidates; one PDB per protein, tried in ascending PDB-ID order against
the SAME cohort gates `task0350`'s own loop uses, unmodified. **54/56
resolved** — 2 unresolved (Carbamoyl Phosphate Synthetase 0/10 usable,
GroEL 0/42 usable, both large multimeric assemblies that never satisfied
`N<=3000` or the other gates). **54 new proteins, inside the +40/+60
target, without needing a second source.**

**A real hang, caught and fixed before it cost real time** (the standing
rule this register adopted after [[TASK-0348]]'s own 2-hour incident): the
first run of this script stalled >60s on GroEL with zero progress — traced
to `backend.data_layer.fetch`'s own bare `urllib.request.urlretrieve`, no
timeout, the exact landmine `task0304_casbench_finding_f.py`'s own docstring
already diagnosed on this same CASBench data. Killed at the first sign of
a stall (not left to run 2 hours to confirm), fixed with the SAME bounded-
timeout local override that script and [[TASK-0329]] already established
(`requests.get(timeout=20)`, monkeypatched into the imported module rather
than editing `backend/` itself — a shared, live-deployed module), plus a
30 MB pre-download size cap. Rerun completed cleanly, GroEL resolving its
own "unresolvable" verdict in 2s instead of hanging.

### Contamination audit — extension is cleaner than the original by this measure

Same convention [[TASK-0329]]/[[TASK-0346]] established (non-JUNK HETATM
within 4.5 A of the TRUTH/allosteric residues specifically, JUNK list
reused verbatim), **reported separately, not merged**:

| cohort | n | carries a ligand at the truth site |
|---|---|---|
| original 108 (recomputed here) | 108 | 87 (80.6%) |
| extension | 54 | 23 (42.6%) |

**Does not reproduce [[TASK-0329]]'s own quoted "40/40" and is not meant
to** — that number was a 40-structure sample checked for ANY non-solvent
HETATM anywhere in the deposited file (its own text: "carry non-solvent
HETATM ligands"), a looser, whole-structure test; this audit is the
stricter "within 4.5 A of the annotated site" version [[TASK-0346]]'s own
generalisation already used, run here on the full 108, not a 40-sample.
Not reconciled further — a different measurement, not a contradicted one.
**The finding that matters: additions are not assumed clean, and by this
measure the new proteins are meaningfully cleaner (42.6% vs 80.6%) than
the existing cohort, not dirtier** — the audit this task's own Constraint
required did its job.

### Arm A: TASK-0350's decisive test, union cohort — null holds

Planned Validation: original-108 subset of the union reproduces
[[TASK-0308]]/[[TASK-0350]]'s committed decoherent numbers to <4e-5
(raw 0.5921, resid 0.5184) — **PASSES**. Union (n=162, 129 clusters):
decoherent raw=0.5771 resid=0.5115; coherent raw=0.5718 resid=0.5041;
per-structure delta median=−0.00507, cluster-permutation **p=0.425** —
non-significant, same verdict as the 76-cluster run, now on ~70% more
independent proteins. Folded into [[HYP-P7]] as a dated Status update.

### Arm B: TASK-0358's f=1 anchor, union cohort — signed null holds; unsigned "spike" washes out exactly as predicted

Planned Validation: original-108 subset reproduces [[TASK-0358]]'s
committed f=1 numbers to <5e-5 on every one of 6 values (signed +
unsigned, raw/rho/resid) — **PASSES**. Union: **SIGNED** raw=0.5004
resid=0.4969 cluster-p=0.822 (flat, as before). **UNSIGNED** raw=0.5483
resid=0.5111 **cluster-p=0.276** — this is the decisive extra evidence
[[TASK-0358]]'s own "isolated spike, zero neighbour support" diagnosis
for the earlier unsigned p=0.036 predicted: adding 54 independent
proteins should dilute an artifact but not wash out a real signal, and
the significance is gone (0.036 → 0.276), not strengthened. Folded into
[[HYP-P6]] as a further dated Status update.

### Arm C: `protein_baseline_auc` — the new measurement, and it fires

The statistic pre-registered above, run exactly as specified, before any
number was seen: replace every eligible residue's score with its own
protein cluster's mean eligible score (zero within-structure position
information), pool across the cohort, AUC against the true label,
cluster-permutation significance (20000 draws).

| cohort | n clusters | n residues | `protein_baseline_auc` | p |
|---|---|---|---|---|
| original 108 | 76 | 96,977 | **0.6500** | <5e-5 |
| extension | 54 | 33,983 | **0.5975** | 0.0006 |
| union | 129 | 130,960 | **0.6549** | <5e-5 |

**A "classifier" that knows only which protein a residue came from —
nothing about where in the structure — separates true from false sites
at AUC 0.65 pooled, comparable in size to this register's own genuine
per-structure CTQW performance (raw_auc ~0.58-0.59).** This is not a
property of the original 108 alone that a bigger cohort would dilute:
it reproduces independently on the 54 brand-new proteins (p=0.0006) and
does not shrink on the union (0.6500 → 0.6549, if anything larger).
**The CAS0002 failure mode this task set out to test is real, and it is
present in this register's own cohort, not only the external branch's.**

**What this does and does not indict, stated plainly so it isn't
misread:** this register's existing headline numbers (`raw_auc` computed
per structure, then averaged/cluster-tested) are immune to this by
construction — a per-structure-constant score ties within that
structure's own ROC curve and contributes exactly 0.5, whatever the
constant. This is a finding about **pooling**: any family-level number,
here or elsewhere, computed by lumping residues from many proteins into
one ROC curve rather than averaging per-structure AUCs is vulnerable to
a real, sizeable protein-identity channel with zero site-specific
content — large enough by itself to explain an effect the size of the
external branch's own +0.107/+0.114 claims. Landed as new **HYP-P28**
(distinct mechanism from every existing entry — none names pooled-AUC
identity leakage specifically). A plausible mechanism (protein size
mechanically shrinking both the positive fraction and, if it also lowers
mean occupancy, the baseline) is disclosed as **Inference, not verified**
in HYP-P28's own text — not chased further, out of this task's budget.

### Doc updates

`PHASE1_SUBMISSION_V3.md`: the "108 structures in 76 protein clusters"
coherence-null sentence and the "closed nine candidate advantage routes"
finite-delay sentence both extended with the union-cohort result in the
same sentence, not a separate paragraph, per this register's own
convention of updating the number in place rather than appending caveats.

### Not done / explicitly out of scope (disclosed, not dropped)

- The cohort-matched comparison to the external branch's own 276/399-
  family numbers — still out of scope, [[TASK-0358]]'s own call, unchanged.
- The held secondary amplitudes-vs-probabilities arm (+0.031) — Reviewer's
  hold unchanged.
- Root-causing `protein_baseline_auc`'s own mechanism (protein-size
  confound vs. something else) — flagged as the natural next step, not
  run here.
- Auditing which of this register's OWN already-published numbers (or the
  external branch's) are actually computed by pooling vs. per-structure
  averaging — a document-by-document check, not made here.

**Files**: `scripts/task0359_cohort_extension_by_protein.py` (new).
**Data**: `results/tasks/0359_cohort_extension_by_protein/
{checkpoint.jsonl,run_log.txt,stdout.log,cohort_extension_result.json}`.
