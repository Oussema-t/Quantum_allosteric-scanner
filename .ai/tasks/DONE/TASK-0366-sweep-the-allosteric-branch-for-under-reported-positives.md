# TASK-0366 — Sweep the `allosteric` branch for positives that never reached us, verified at source

- Status: Done
- Owner: **Explorer or Reviewer** (read-only; no compute)
- Done: 2026-09-10, Implementer B
- Priority: **High — 5 days to 2026-09-15, and it is the cheapest remaining route to a positive result**
- Filed: 2026-09-10 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0365]], [[TASK-0360]], [[TASK-0327]], [[TASK-0336]], [[TASK-0348]]

## Why: we already caught one, by accident

[[TASK-0365]] read `origin/allosteric`'s own committed files instead of the
summary we had been given, and found the summary **understated their own work in
three places**. The important one:

> We were told *"AI recommender, exact-winner accuracy 0.107 vs 0.137 baseline —
> negative."* Their `allosteric/results/ml_model/README.md` labels that figure
> **"earlier tests"**. The current results are two models, and **Model 1 is a
> positive**: topology → MIN_HOP separates near from distal at **AUC 0.793**, and
> running the walk at its predicted distance beats a fixed choice across the
> cohort (**0.924** against 0.901). Only Model 2 is the negative.

**A positive result was sitting in that branch, reported to us as a negative, and
we found it only because we went to check a different number.** That is not a
criticism of anyone — summaries compress, and the compression happened to drop the
half that helps. It is a reason to look systematically rather than by accident.

Also found in the same pass: the ML cohort is **597 proteins / 380 families**, not
the 630/399 quoted elsewhere; and the funnel ablation's AUC half (0.576 → **0.626**
*rising* while strict hits fall 48 → 6) was never mentioned to us at all.

## Intent Contract

- **Outcome:** a classified inventory of every result on `origin/allosteric` —
  **positive / negative / neutral**, and **present / absent from our submission** —
  with each entry traced to the artifact that produces it.
- **In scope:**
  1. Read every write-up under `allosteric/results/`: `ALL_RESULTS_SUMMARY.md`,
     `BRANCH_COMPARISON.md`, and the per-directory `RESULTS.md` / `README.md` in
     `centrality_ablation`, `challenge_targets`, `classical_comparison`,
     `full_run_1022`, `ml_model`, `pocket_seeded_sweep`, `proximity_floor`,
     `seeded_classical`, `veto_pipeline`.
  2. **For anything that looks positive, verify it against the raw artifact in the
     same directory before recording it as positive.** A number quoted in a
     write-up is a claim, not a measurement — this is the whole lesson of the
     Model 1 case and of [[TASK-0348]]'s ρ≈0.95.
  3. Record for each: the cohort (proteins **and** families — they differ between
     their own results), the metric, whether a null or baseline was used, and the
     file that produces it.
  4. Flag anything **positive and absent from our submission** as a candidate for
     the remaining space, ranked by how cheaply it can be stated.
- **Out of scope:**
  - Re-running their pipelines. Read-only.
  - Judging their methodology. We are inventorying what exists and whether it is
    supported by its own artifact.
  - Editing the submission. This task produces the inventory; the Team Lead
    decides what goes in.
- **Constraints and invariants:**
  - **Every entry cites `file:line` or a path.** An unsourced entry is not an
    entry.
  - Where a write-up and its artifact disagree, **record both and say which is
    which** — do not silently prefer either.
  - Where a result is positive but rests on a selected cell, a single family, or
    an unmatched cohort, **say so in the same row**. [[TASK-0336]] and the CAS0002
    concentration are the standing examples of exactly that failure.

## Planned Validation

Re-derive [[TASK-0365]]'s own three findings from the branch as a calibration
check — Model 1's 0.793/0.924, the 597/380 cohort, and the 0.576 → 0.626 funnel
figure. If the procedure cannot recover those three, it will not find anything
else reliably, and the task stops there.

## Pre-registered expectation

Recorded before looking, and two-sided. **Most of that branch is negative** — that
is the whole shape of both registers, and finding little is the likely outcome and
a fine one. But we have a demonstrated instance of a positive lost in compression,
one page of body space and one of appendix space, and five days. **If a second
under-reported positive exists, this is the only systematic way we will find it;
if none does, we learn that the inventory is complete and can say so.**

## Budget

Capped at one working session. Read-only, no compute. If time runs out, report
the directories covered and the ones not reached — a partial inventory that names
its own gaps is useful; a complete-looking one that quietly skipped three
directories is not.

## Dependency

- [[TASK-0365]] (Done) — the three findings this task calibrates against, and the
  reason it exists.
- `origin/allosteric` — fetchable; the branch is on the same remote.

## Staged Files

- [2026-09-10 23:13] `.ai/COMMON.md` -- V4 fixes / 0366
- [2026-09-10 23:13] `.ai/tasks/TODO/TASK-0366-sweep-the-allosteric-branch-for-under-reported-positives.md` -- V4 fixes / 0366
- [2026-09-10 23:13] `__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V4.md` -- V4 fixes / 0366
- [2026-09-10 23:13] `__WORK_IN_PROGRESS__/documentation/SUBMISSION_VERSION_LEDGER.md` -- V4 fixes / 0366

## Planned Validation — calibration against TASK-0365's own three findings

All three recovered exactly from `origin/allosteric`'s raw files, before the sweep began:
- `allosteric/results/ml_model/README.md`: Model 1 near/distal AUC **0.793**, best-cell-at-
  predicted-distance **0.924** vs always-MIN_HOP=1 **0.901**, cohort **597/380** — all match verbatim.
- `allosteric/results/classical_comparison/UNCONSTRAINED_AND_SITE_LEVEL.md`: funnel figure for
  closeness centrality **0.626** (unconstrained) → **0.576** (with funnel) — matches (TASK-0365
  quoted the same pair as "0.576 → 0.626").

Procedure recovers all three. Proceeded.

## Done (2026-09-10, Implementer B)

**Full coverage of every directory in scope. One large, verified, currently-unreconciled
contradiction between the two branches' own headline coherence claims; three smaller positives
absent from V4; one prior positive already retracted by the branch itself and never fixed in its
own per-directory writeup.**

### Method

Every write-up in scope read from `origin/allosteric` (fetched, read via `git show`, never
checked out — read-only per this task's own Out of Scope). For each candidate positive, the
**raw JSON artifact was pulled and independently recomputed** in this repo's own venv (not just
trusted from prose) — the same discipline TASK-0365 itself demonstrated on the Model 1 numbers.

### 1. THE HEADLINE FINDING — the two branches' coherence conclusions directly contradict, and
   theirs is independently verified

`allosteric/results/seeded_classical/README.md` (corroborated verbatim by
`classical_comparison/RESULTS.md` and `classical_comparison/UNCONSTRAINED_AND_SITE_LEVEL.md` —
three independent write-ups, same number): on 630 proteins / 399 families, an active-site-seeded
CTQW (`e^{-iHt}`, amplitudes) is compared against its **exact classical twin**, the heat kernel
`e^{-Lt}` (same Laplacian, same seed, same time-averaging grid, probabilities instead of
amplitudes — the only variable that differs).

**Independently reproduced from the raw per-protein artifact** (`seeded_classical/sc_{0..7}.json`,
all 8 shards, 630/630 scored, this task's own recomputation, not transcribed):

```
mean CTQW = 0.5999   mean heat kernel = 0.5124
wins/losses/ties (paired, n=630) = 407 / 218 / 5
Wilcoxon signed-rank p = 2.25e-12          (README states 2.3e-12 — matches)
distal subset (n=91): CTQW 0.617 vs heat kernel 0.275  (below chance)
vs proximity (-hop): 325/297, Wilcoxon p = 0.124        (README: "tie, not beaten" — matches)
```

**This is a well-powered, independently-verified, large-n result: coherent CTQW amplitudes beat
the identical construction run with classical probabilities, p=2.3e-12, on 630 proteins.**

**It directly contradicts this register's own headline**: [[TASK-0350]]'s own committed numbers
(`HYP-P7`) are classical diffusion **0.6012** > coherent CTQW **0.5997** > decoherent CTQW
**0.5921** — classical diffusion *wins* on our 108-structure cohort, the opposite ordering. The
`allosteric` branch's own `seeded_classical/README.md` flags this explicitly, unprompted, in its
own text: *"This CONTRADICTS the conclusion drawn on the bartosz branch... The two analyses use
different cohorts, different baselines and different nulls, and must be reconciled before
submission."* **That reconciliation has not happened. V4 states only our own negative
(`grep` for "heat kernel" / "2.3e-12" / "630 protein" in `PHASE1_SUBMISSION_V4.md`: zero
matches).**

**What is NOT resolved here, because it is not this task's job**: which comparison is more valid
— ours (decoherent-vs-coherent CTQW, converged/time-averaged, ASBench 108/76) or theirs
(coherent-CTQW-vs-heat-kernel-twin, MIN_HOP=1-filtered pipeline output, 630/399) — are genuinely
different constructions (different graphs, different candidate-selection funnels, different
operators compared). Both are internally sound measurements of different questions. **Flagging
the contradiction and its cost of silence is this task's job; adjudicating it is the Team Lead's
and whichever thread owns HYP-P7 next.**

### 2. BCR_ABL1 / asciminib — a real hit on the submission's own motivating example, absent from the submission

`allosteric/results/challenge_targets/README.md`: the trained recommender applied to BCR_ABL1
(not in the 630-protein training set) — best of 6 recommended configurations (harm/adj +
neg_dD_mean, MIN_HOP=4) scores **AUC 0.900, P@5 0.80**, with 4 of the top-5 ranked residues
genuine asciminib contacts in the myristoyl pocket. `PHASE1_SUBMISSION_V4.md` cites asciminib by
name in its own opening motivation (`grep` line 9) but never states this result — zero matches
for "0.900", "myristoyl", or "BCR_ABL1" as a result anywhere in the document.

**Caveated, in the same row, per this task's own Constraint**: this is 1 of 6 recommended
configurations (rank 4 by the recommender's own confidence weight, 7%; the top-weighted pick, 51%
confidence, scores AUC 0.140 — "the shortlist works, the weighting does not," their own words),
and 1 of 3 attempted targets: KRAS_G12C was blocked (PASSer's server errors on every KRAS
structure tried) and HIV1_RT scored a moderate AUC 0.679 with no top-5 hit. **Not a sweep win —
a best-of-6-on-one-target hit**, honestly stated that way.

### 3. Site-level pocket ranking — modest, verified, absent

`classical_comparison/UNCONSTRAINED_AND_SITE_LEVEL.md` §1 (matches `ALL_RESULTS_SUMMARY.md` §3
verbatim): ranking pockets (not residues) by best-member score, 626 proteins with >1 candidate
pocket, mean 3.9 pockets/protein (random ≈26% top-1). CTQW: top-1 37% (proximity 38%, one-point
gap, noise), **top-3 86% (best of 7 methods)**, **mean rank 2.12 (best)**. Absent from V4.

### 4. hpc_search.py residue classifier — real number, but selection-bias-prone and not the
   configuration predictor V4 already cites

`ml_model/README.md`'s own Files section, one line: "a separate 440-config search for a
residue-level allosteric classifier... best CV AUC 0.654, 35 families P@5≥0.8." **Independently
recomputed from all 8 `search_{0..7}.json` shards (440/440 configs present)**: the
`cells+stats+topo` / RandomForest config the README names gives AUC **0.6538**, fam8 **35** —
matches exactly. **Caveat, stated because the branch's own register applies this exact discipline
elsewhere and this entry should get the same treatment**: this is the max over a 440-config
hyperparameter search with **no stated null/chance correction** — the same selection-bias
mechanism `ALL_RESULTS_SUMMARY.md` §1 itself applies to the 884-configuration CTQW sweep ("73% of
the sweep's headline is chance"). The single highest-AUC config in the same search
(`cells+topo`/RF, AUC 0.6575) clears only 26 families, not 35 — the README's own pick optimizes
the family-count criterion, not AUC, a second, undisclosed selection step. **Also a naming
collision worth flagging, not resolving**: `hpc_search.py`'s own docstring calls this a search
"for Model 2," while the README text calls it "a different model, not the configuration
predictor" — the two documents disagree on what this experiment even is. Lowest-priority of the
four candidates; flagged with its own caveats attached, not recommended without them.

### 5. A positive already retracted by the branch itself, and the stale writeup that still states it

`proximity_floor/README.md` (undated relative to the others, but clearly earlier): claims CTQW
beats the proximity floor decisively on distal targets, **0.617 vs 0.227, 83/91 proteins (91%),
sign test p=5.8e-09** — a strong, dramatic positive, if true.

**It is not true as stated, and the branch's own later documents say so.** `ALL_RESULTS_SUMMARY.md`
§3 and `BRANCH_COMPARISON.md` §1.4 (both dated 2026-09-09, after `proximity_floor/README.md`):
*"I read an AUC backwards. 0.227 on distal means the REVERSED predictor scores 0.773. Family
level on distal: CTQW 0.507 vs reversed proximity 0.722, CTQW wins 14/53. The distal claim died
here."* Mechanism, verified directly from `proximity_floor.py:49`: `floor=roc_auc_score(y,-h)` —
closer-is-truth, which is the wrong direction to test on a subset defined as *far* from the
active site; the fair floor for that subset is the reversed direction (farther-is-truth, AUC =
1 − 0.227 = 0.773), against which the corrected CTQW number loses.

**`proximity_floor/README.md` itself was never updated** — it still reads as a decisive win to
anyone who opens that one file instead of the two summary documents. **Recorded here so nobody
downstream re-discovers and re-reports the retracted number as if it were live.** Not a candidate
for our submission in either direction — already a dead claim on their own side.

### Full inventory table

| # | finding | file | verified how | present in V4? | verdict |
|---|---|---|---|---|---|
| 1 | CTQW beats classical heat-kernel twin, p=2.3e-12, n=630 | `seeded_classical/README.md` + 2 corroborating write-ups | independently recomputed from `sc_{0..7}.json`, exact match | **absent** — contradicts our own HYP-P7 | flag for reconciliation, highest priority |
| 2 | Model 1 (topology→MIN_HOP), AUC 0.793 / 0.924 vs 0.901 | `ml_model/README.md` | Planned Validation calibration, exact match | **present** (added by [[TASK-0365]]) | resolved, no action |
| 3 | BCR_ABL1/asciminib hit, AUC 0.900, P@5 0.80 | `challenge_targets/README.md` | read directly, internally cross-checked against the same file's own caveats | **absent** | candidate, caveated (best-of-6, 1 of 3 targets) |
| 4 | Site-level: CTQW best top-3 (86%), best mean rank | `classical_comparison/UNCONSTRAINED_AND_SITE_LEVEL.md` | 2 independent write-ups agree verbatim | **absent** | candidate, modest |
| 5 | hpc_search residue classifier, AUC 0.654, 35 families | `ml_model/README.md` Files section | independently recomputed from `search_{0..7}.json`, exact match | **absent** | candidate, selection-bias caveat attached |
| 6 | Funnel ablation, closeness 0.626→0.576 | `classical_comparison/UNCONSTRAINED_AND_SITE_LEVEL.md` | Planned Validation calibration, exact match | **present** (added by [[TASK-0365]]) | resolved, no action |
| 7 | Proximity floor "0.617 vs 0.227, p=5.8e-09" distal win | `proximity_floor/README.md` | traced the retraction in 2 later branch documents + the script's own formula | absent, **and should stay absent — retracted by the source branch itself** | do not cite |
| 8 | Two-source phase interference, +0.107 p=0.007 | `ALL_RESULTS_SUMMARY.md` §4 | already known; cohort-match explicitly out of scope in [[TASK-0357]]/[[TASK-0358]]/[[TASK-0359]] | n/a — standing, disclosed gap | no new action |
| 9 | Headline configuration counts (884-sweep, veto-pipeline family counts) | `veto_pipeline/README.md`, `full_run_1022/README.md` | cross-checked against `ALL_RESULTS_SUMMARY.md`, self-consistent, includes their own null-correction | already summarized at the level V4 needs | no new action |
| 10 | AI recommender Model 2, QMI, chiral-analog tests — all negative | `ml_model/README.md`, `ALL_RESULTS_SUMMARY.md` §4 | read, internally consistent | negatives; nothing to add | no action |

### Directories covered — full coverage, none skipped

`ALL_RESULTS_SUMMARY.md`, `BRANCH_COMPARISON.md`, `centrality_ablation/RESULTS.md`,
`challenge_targets/README.md`, `classical_comparison/RESULTS.md` +
`UNCONSTRAINED_AND_SITE_LEVEL.md`, `full_run_1022/README.md`, `ml_model/README.md` +
`hpc_search.py` + `search_{0..7}.json`, `pocket_seeded_sweep/README.md`,
`proximity_floor/README.md` + `proximity_floor.py`, `seeded_classical/README.md` +
`seeded_classical.py` + `sc_{0..7}.json`, `veto_pipeline/README.md`. **Every directory named in
this task's own Scope, reached.**

### Constraints honored

Every entry above cites a `file`/`file:line`. Disagreements between write-ups (finding #7)
recorded as both, with dates and which is which, not silently resolved to one. Selection/cohort
caveats stated in the same row as the positive they qualify (findings #3, #5), not left implicit.
No pipeline re-run, no methodology judgment beyond checking internal consistency, no submission
edit made — the inventory is delivered; the Team Lead decides what travels into V4/V5.

### Not done / explicitly out of scope

- Did not verify `veto_pipeline`'s per-family-winner Hamiltonian breakdown or `full_run_1022`'s
  MIN_HOP-sweep counts against their own raw `.json.gz` shards (large, gzipped, would have
  consumed most of the session budget for entries #9/#10, already independently cross-checked
  across two summary documents and not flagged as candidates).
- Did not adjudicate finding #1 (which cohort/construction is the fairer test) — flagged, not
  resolved, per this task's own Out of Scope ("judging their methodology").
- Did not edit `PHASE1_SUBMISSION_V4.md` or `SUBMISSION_VERSION_LEDGER.md` — per this task's own
  Out of Scope; those two files appear in Staged Files only because another concurrent commit
  (V4 fixes) touched them, not because this task changed them.

**Files**: none produced — read-only task, per its own Owner/Out-of-Scope. Full inventory lives
in this Done section.
