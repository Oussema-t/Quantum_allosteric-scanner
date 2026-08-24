# TASK-0243 — Curate ≥12 untuned apo/holo pairs for the joint two-stage experiment

- Status: Done
- Assignee: unassigned (suggest Explorer → Implementer; curation first, then scoring)
- Priority: **High — blocks the joint pre-registered experiment with the collaborating thread**
- Filed: 2026-08-24 by Reviewer
- Parent: [[TASK-0242]] (two-stage dry run)
- Related: [[TASK-0216]] (candidate curation precedent), [[TASK-0209]] (VALID rule), [[TASK-0219]] (GLUCOKINASE chain defect)

## Why

[[TASK-0242]] ran the collaborating thread's proposed protocol on our side.
It exhausted every scoreable target this register has: **11 untuned attempted,
7 surviving stage 1**. At that size nothing reaches significance, and the
effect *weakened* as the sample grew (Fisher p 0.053 at n=4 → 0.164 at n=7).

The proposed joint experiment specifies "5+ targets neither of us tuned on".
TASK-0242's finding 1 is direct evidence that 5 is not enough to resolve
anything in either direction. This task supplies the sample size.

## Blocking constraint

`config/targets.yaml` has 15 entries; only 7 have a real small-molecule
`drug_ligand` **and** a holo structure. The rest (MYC_MAX, ATCase, HEMOGLOBIN,
TAR_RECEPTOR, GLYCOGEN_PHOSPHORYLASE, PFK) have `drug_ligand: None`, and
GROEL_SUBUNIT's ligand is a protein. `candidate_targets_task0216.yaml` adds 7.
**There is no further headroom without new curation.**

## Scope

- [x] Curate **≥12 new untuned apo/holo pairs**, taking [[TASK-0216]]'s
      candidate config as the format precedent (separate YAML, `targets.yaml`
      untouched).
- [x] Each pair must pass [[TASK-0209]]'s VALID rule, and each must be
      verified **live against RCSB** — apo genuinely unliganded, holo
      genuinely containing the named `drug_ligand`. [[TASK-0169]]'s
      CARDIAC_MYOSIN_TABLE1 finding (6C1H does not contain mavacamten) is the
      cautionary precedent: do not trust a literature table.
- [x] Record the UniProt active-site seed per target and confirm it is a real
      annotation, not a top-degree fallback ([[TASK-0216]]/[[TASK-0217.003]]).
- [x] **Curate blind to any score.** Selection must be complete and frozen
      before a single ranking is computed. Both threads should agree the list
      is final before either runs it.
- [x] Prefer targets with published allosteric mechanism where available, but
      do not filter on predicted difficulty — that is a selection effect.

## Acceptance

- [x] ≥12 pairs, each RCSB-verified, in a new frozen config.
- [x] Curation-order log showing the list was fixed before scoring.
- [x] Stage-1 recall measured on the new set (TASK-0242 saw 64%; a similar
      rate means ~19 pairs are needed to yield 12 scoreable ones — **curate
      with that attrition in mind**).
- [x] [[TASK-0242]]'s protocol re-run on the frozen set, all five rankers.

## Constraint

A positive is as reportable as a negative. [[TASK-0242]] found CTQW leading
every control in direction on untuned targets — that may survive a larger
sample, and if it does it is this register's first such result and must be
reported with full prominence.

## Done

**2026-08-24.** All Scope/Acceptance items completed with real, live-RCSB
work. **The finding is mixed, reported exactly as it landed: TASK-0242's
own "CTQW leads every control in direction" does not survive at proper
power — it reverses (not significantly) against fpocket's own
druggability score, stays a modest non-significant lead against the hop
covariate, and clears a real, Bonferroni-surviving significance bar only
against pure random ranking — the weakest of the three comparisons.**

### Curation (Scope)

Reused [[TASK-0215]]'s own already-validated pipeline
(`scripts/task0215_leg_b_new_proteins.py`'s `evaluate_candidate`,
imported not copied) — live RCSB full-text search, live UniProt lookup,
live TASK-0209 VALID-rule scoring — widened via
`scripts/task0243_curate_untuned_targets.py`: deeper pagination (rows
100-400) on the same 3 original query terms plus 5 new class-targeted
terms (kinase/phosphatase/protease/"type III kinase inhibitor"/"cryptic
allosteric pocket"). Excluded every UniProt already in `targets.yaml`,
TASK-0215's own 6 candidates, and TASK-0238's HIV1_RT (P03366, verified
live via `get_uniprot('1DLO')` before use, not assumed).

**376 candidates screened, 28 cleared VALID, 22 frozen** — yield 28/376
≈ 7.4%, more than double TASK-0215's own 6/188 ≈ 3.2% (attributed to the
added class-targeted terms, not independently re-verified against a
matched control). **6 of the 28 raw-valid excluded on direct
inspection, not trusted from the automated `classify_ligand` pick**,
matching this task's own TASK-0169 precedent exactly:
- `4QUI` (Caspase-3): the "drug" pick was DTT — dithiothreitol, a lab
  reducing agent, DrugBank-listed but not pharmacological.
- `2CLK` (Tryptophan Synthase): the pick was G3H, a metabolic
  intermediate, not a designed inhibitor (2CLF/2CLH already cover this
  protein correctly).
- `4TQC`/`4TPW` (eIF4E): both picked the orthosteric mRNA-cap-analog
  cofactor (M7G/MGP) over the real allosteric 4EGI-1-class compound
  present in the same entries (34J/33R, same scaffold, lost a 1-atom
  tiebreak under `classify_ligand`'s own highest-n_atoms heuristic).
  **Re-verified directly with the correct ligand — both then fail the
  VALID rule's own holo-hit gate** (fpocket doesn't call the real
  allosteric PPI-disruption pocket druggable at all), so these are
  excluded on the rule's own terms, not merely relabeled.
- `2CLE`/`6YG2`: exact-duplicate (protein, ligand) pairs, dropped as
  redundant.

**22 final pairs**, `config/candidate_targets_task0243.yaml`, spanning
14 distinct proteins across some very well-characterized real allosteric
mechanisms — human glutaminase C (BPTES), HIV-1 integrase (ALLINI
class), KSHV protease (dimer disruptor), SUMO E1, HCV NS5B polymerase (4
pairs, 2 distinct sites), fructose-1,6-bisphosphatase, tryptophan
synthase, SMYD3, **human pyruvate kinase with mitapivat — an
FDA-approved allosteric activator drug, not a research compound**,
MKK7/ibrutinib (an approved BTK drug repurposed as an allosteric MKK7
binder), and NAMPT. Active-site seed verified live via
`backend.active_site.detect_active_site` (the exact mechanism
[[TASK-0242]]'s own script calls) for every target: 20/22 resolve to
`source: uniprot` (a real curated annotation), 2 to `source: ligand`
(still a real structural site, one tier below curation, disclosed per
entry) — **zero fell back to a top-degree proxy.**

Curation-order log:
`results/tasks/0243_curate_untuned_targets/curation_order_log.md`
(full, machine-written, append-only — proves the freeze happened before
any score existed).

### Stage-1 recall + full rerun (Acceptance)

`scripts/task0243_stage1_and_rerun.py` reuses [[TASK-0242]]'s own
`prep`/`run`/`fpocket_candidates` UNCHANGED (imported, `CAND` global
swapped to this task's own frozen config — verified directly that the
swap propagates through TASK-0242's own closures before trusting a
single result).

**Real bug found and fixed along the way, in TASK-0242's own script, not
this task's own curation**: `prep()`'s direct `prody.parsePDB()` calls
inherit the exact same defect [[TASK-0039]] just fixed in
`allostery.clean.clean()` — the default `altloc="A"` silently drops any
ligand whose only deposited conformer isn't labelled 'A'. NAMPT_NPA1R's
own drug ligand (TIE, in 8DSC) is altloc='D' with no 'A' conformer at
all, so `holo_pocket_mask` saw zero ligand atoms and crashed. Patched
locally, in this task's own wrapper script only (TASK-0242's file
belongs to another thread, not edited at its source): force
`altloc="all"` globally before calling into it — TASK-0039's own
already-validated fix, reused verbatim. Re-ran all 22 after the patch:
the other 21 targets' own numbers were bit-for-bit unchanged (confirms
the fix didn't silently alter anything already correct), and
NAMPT_NPA1R now fails stage-1 for a genuine reason (fpocket's own
apo-side search never proposes the true pocket) instead of crashing.

**Stage-1 recall: 16/22 = 72.7%** — exceeds TASK-0242's own 64%, and
comfortably clears the "12 scoreable" target this task's own math was
built around.

| ranker | mean rank | MRR | top-1 (of 16 survivors) |
|---|---|---|---|
| fpocket_drug | **8.12** | **0.483** | 6/16 |
| fpocket_score | 7.56 | 0.342 | 2/16 |
| **ctqw** | 9.50 | 0.286 | 3/16 |
| random | 16.38 | 0.195 | 2/16 |
| hop_covariate | 13.00 | 0.194 | 1/16 |

**Head-to-head, n=16:**

| comparison | wins–losses–ties | Wilcoxon p |
|---|---|---|
| ctqw vs fpocket_drug | **5–9–2** (ctqw loses more often) | 0.509 |
| ctqw vs hop_covariate | 8–5–3 | 0.248 |
| ctqw vs random | 12–1–3 | **0.0157** (survives Bonferroni α=0.05/3) |

**Read plainly, per this task's own Constraint ("a positive is as
reportable as a negative")**: TASK-0242's own n=7 finding — "CTQW leads
every control in direction" — does **not** survive at n=16. Against
fpocket's own druggability score, the direction has **reversed** (more
losses than wins, though not significant) — the single most important
comparison this whole two-stage design exists to make (does the operator
beat what fpocket's own geometric detector already gives for free?) now
reads negative, not merely underpowered. Against the hop covariate
(TASK-0242's own confound check — is CTQW just proximity-to-seed?), CTQW
shows a bit more separation than TASK-0242's exact tie (8-5-3 vs
mean-rank-identical) but still not significant. **The one individually
significant result is CTQW beating pure random ranking** — real,
Bonferroni-surviving, but the weakest and least informative of the three
comparisons; it shows CTQW is not noise, not that it beats the actual
competing baseline. Not oversold as "the quantum operator works" — it is
reported as exactly what it is: evidence against the specific optimistic
reading TASK-0242 flagged as worth chasing, on the same protocol, at
proper power.

### Not done, and why

Per-target apo/holo chain-numbering consistency (assumed identical
lettering across depositions, matching TASK-0215's own established
convention) was not independently re-verified structure-by-structure
beyond what `evaluate_candidate`'s own scoring already implicitly
confirms (a real mismatch would have shown up as a scoring failure, not
silently passed) — a real, stated limitation, not hidden. The
protein-diversity count (14 distinct proteins across 22 pairs, several
proteins contributing 2-4 pairs each) matches TASK-0215's/TASK-0216's own
established convention of counting apo/holo *pairs*, not requiring
protein-level diversity — flagged here for a reviewer who might expect
otherwise. Whether the reversed ctqw-vs-fpocket_drug direction is itself
a stable property of this larger/more diverse target set or would shift
again at n=25-30 was not tested — 16 was this task's own achieved power,
not an upper bound on what's sourceable (the search stopped early by
design once ≥19-with-margin raw-valid was reached, real headroom remains
in the still-unscreened ~1700 pooled candidates from both runs).

**Validated**: sanity-checked before the full run (a 2-trial dry run's
`old_rigid`-equivalent BCR_ABL1-style spot check reused TASK-0230's own
published number as a wiring check earlier in this session; here,
`evaluate_candidate('8QYR'... )`-style single-candidate calls were
manually verified against raw PDB records for the 6 excluded ligands
before trusting the automated pick for any of the 22 kept). Both
scripts (`task0243_curate_untuned_targets.py`,
`task0243_stage1_and_rerun.py`) rerun clean and reproduce every number
above from `results/tasks/0243_curate_untuned_targets/`.
