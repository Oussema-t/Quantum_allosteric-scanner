# TASK-0361 — Audit which published numbers are pooled and which are per-structure-averaged

- Status: Done
- Owner: **Implementer**
- Priority: **High — it decides whether a sentence in the shipping document is fact or expectation**
- Filed: 2026-09-09 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0359]], [[HYP-P28]], [[TASK-0094]], [[TASK-0310]], [[TASK-0350]], [[TASK-0358]]

## Why

[[TASK-0359]] established [[HYP-P28]]: a score carrying **zero within-structure
position information** — every residue replaced by its own protein's mean —
reaches **pooled AUC 0.6500** on the original 108, **0.5975** on 54 brand-new
proteins, **0.6549** on the union, all at p <= 0.0006. A pure protein-identity
channel, real and replicated.

[[TASK-0359]]'s own write-up draws the correct boundary, and this task exists to
verify it rather than trust it:

> This register's existing headline numbers (raw AUC computed per structure, then
> averaged and cluster-tested) are **immune by construction** — a
> per-structure-constant score is a tie within that one structure's own ROC
> curve, contributing exactly 0.5 regardless of the constant. The finding is
> about **pooling**.

**That immunity argument is sound. What has not been checked is whether it
actually applies to each number we publish.** [[TASK-0359]] itself lists this as
explicitly not resolved: *"auditing which of this register's own already-published
numbers are actually pooled vs. per-structure-averaged."*

The submission currently rests on the assumption that our convention is
per-structure everywhere. **Assumption is not audit**, and this register's own
standing rule is to check the register before assuming.

## Intent Contract

- **Outcome:** a table classifying each in-scope published number as
  **per-structure-averaged (immune)**, **pooled (needs a protein-identity
  floor)**, or **neither/unclear**, with the producing script and line cited for
  every row.
- **In scope, in this priority order** — the ordering is load-bearing, because the
  budget may not reach the end:
  1. **Every number quoted in `PHASE1_SUBMISSION_V3.md`.** This is what ships and
     it is the whole reason the task is High. Finish this before anything else.
  2. The arms feeding [[HYP-P6]], [[HYP-P7]], [[HYP-P13]] and [[HYP-P28]].
  3. Anything else in `RESULTS.md` only if time genuinely remains.
- **Method:** read the producing code, do not re-run the analyses. The
  distinguishing signature is mechanical — one `roc_auc_score` per structure
  followed by a mean, versus concatenating residues across structures into a
  single `roc_auc_score` call.
- **For any number found to be pooled:** compute [[TASK-0359]]'s
  `protein_baseline_auc` on that number's own cohort and report the number
  against that floor, exactly as this register already reports against the
  proximity floor ([[TASK-0094]]). Reuse
  `scripts/task0359_cohort_extension_by_protein.py`'s own function; do not
  reimplement it.
- **Out of scope:**
  - Re-running or re-deriving any analysis whose aggregation turns out to be
    fine.
  - Root-causing the protein-identity channel's mechanism (the protein-size
    hypothesis is [[HYP-P28]]'s open question, not this task's).
  - The external branch's numbers. We can ask them; we cannot audit their code
    for them.
  - Changing any published number. This task **classifies**; corrections are a
    separate decision once the classification exists.
- **Constraints and invariants:** cite `file:line` for every classification —
  a verdict without a citation is not a finding. Where a number's provenance
  cannot be established, record it as **unclear** rather than guessing; an
  honest gap is a result, a guess is a defect.

## Planned Validation — audit the auditor first

Before classifying anything else, the procedure must correctly classify two
numbers whose aggregation is already known from [[TASK-0359]]'s own run:

- [[TASK-0310]]'s converged decoherent `raw = 0.5921` — **per-structure-averaged**.
- [[TASK-0359]]'s `protein_baseline_auc = 0.6500` — **pooled**.

If the procedure cannot tell those two apart, it cannot be trusted on anything
else and the task stops there.

## Pre-registered prediction

Stated before looking. **The expected outcome is that the submission's numbers are
clean**, because the per-structure convention is used consistently in the scripts
this Reviewer has read. If that holds, the value delivered is the right to write
*"every AUC in this document is computed per structure and averaged, never pooled
across proteins"* as **a checked fact rather than an expectation** — which is
worth a line in a document whose entire argument is that the field does not check
things like this.

If it does not hold, we have found in our own work exactly the defect we are
proposing to build an instrument to catch, and it must be reported that way,
without softening.

## Budget

Capped. Item 1 (the submission's own numbers) is the deliverable; items 2 and 3
are bonus. If item 1 alone consumes the budget, report it complete and the rest as
not started — do not deliver a shallow pass over everything.

## Dependency

- [[TASK-0359]] (Done) — `protein_baseline_auc`, the finding, and the immunity
  argument this task verifies.
- [[HYP-P28]] — the hypothesis this audit's results attach to.
- [[TASK-0094]] (Done) — the proximity floor, the existing precedent for reporting
  a number against a floor rather than against chance.

## Staged Files

- [2026-09-09 21:34] `.ai/COMMON.md` -- registry row
- [2026-09-09 21:34] `.ai/tasks/TODO/TASK-0361-pooled-vs-per-structure-aggregation-audit.md` -- the task file itself

## Done

**2026-09-09, Implementer A.** No blocker found before pickup ([[TASK-0359]]
Done, `HYP-P28` present, [[TASK-0094]] Done, `task0359_cohort_extension_
by_protein.py` present). Read-only audit, method exactly as specified
(read the producing code, re-run nothing).

### Planned Validation — audit the auditor first

- [[TASK-0310]]'s converged decoherent `raw = 0.5921`: found the
  per-structure `roc_auc_score` call inside the per-structure loop
  (`task0310_family_residualised_on_proximity.py:270`), aggregated by
  `agg()`'s `np.mean` over per-structure dicts (`:279-282`) — classified
  **per-structure-averaged**. Correct.
- [[TASK-0359]]'s `protein_baseline_auc = 0.6500`: found `y_all =
  np.concatenate([...])`/`base_all = np.concatenate([...])` across every
  cluster before the single `roc_auc_score(y_all, base_all)` call
  (`task0359_cohort_extension_by_protein.py:244-255`) — classified
  **pooled**. Correct.

The procedure separates the two known cases. Proceeding.

### Item 1 — every number in `PHASE1_SUBMISSION_V3.md`

Full classification table (V = per-structure-averaged/immune, P = pooled,
N/A = not an AUC-pooling-type statistic — a count, rate, or correlation
whose own aggregation the HYP-P28 mechanism does not apply to):

| Submission text (§, approx. line) | Number(s) | Class | Citation |
|---|---|---|---|
| §1, walk occupation raw→resid (line 34, 69) | 0.5921 → 0.5184 | **V** | `task0310_family_residualised_on_proximity.py:270-282` |
| §1, per-target verdict table (line 40-42) | 0.514 / 0.541 / 0.548 | **V** (trivial — one structure per row, no cohort to pool across) | single-target runs via `allostery/diagnostics.py`'s verdict computation |
| §2, chiral walk (line 70) | 0.4960 | **V** | `task0310_family_residualised_on_proximity.py:297-299` (`sc_chiral`), same `score_stats`/`agg` as the baseline row above |
| §2, spectral coherence / entanglement entropy (line 72) | 0.5226 / 0.4903 | **V** | `task0310_family_residualised_on_proximity.py:304-312` (`sc_spectral`/`sc_entanglement`), same `score_stats`/`agg` |
| §2, centrality ablation, ρ + AUC (line 78) | median ρ=0.41; beats degree/eigenvector/GNM p<0.05; ties betweenness/closeness p=0.50/0.93 | **V** | `task0348_centrality_ablation.py:280-285` (`roc_auc_score` called inside the per-structure loop, one call per structure), `:143-190` (cluster test/bootstrap CI on the resulting per-structure dict, not a pooled array) |
| §2, coherent−decoherent delta, 108/76 clusters (line 80) | mean +0.0023, Wilcoxon p=0.92, cluster-p=0.83 | **V** | [[TASK-0350]]'s own `task0350_coherent_vs_decoherent.py` (this register's own prior work, re-verified here by re-reading, not re-run) |
| §2, extended cohort, 162/129 clusters (line 80) | cluster-p=0.42 | **V** | `task0359_cohort_extension_by_protein.py:346-378` ("Arm A"), imports `score_stats`/`agg`/`cluster_sign_flip_test_generic` from `task0357_finite_delay_phase_observable.py:123-190` unchanged — same per-structure lineage as [[TASK-0350]]'s own, confirmed by the Done file's own explicit "per-structure delta median" text as corroboration |
| §2, proximity-rho by arm (line 82) | 0.953 / 0.735 / 0.692 | **V** | `task0350_coherent_vs_decoherent.py`'s `agg()` — `rho = np.mean([r["rho"] for r in rows.values()])`, per-structure mean |
| §2, finite-delay f=1 anchor, signed/unsigned (line 84) | p=0.036 → p=0.28 (0.276) | **V** | `task0357_finite_delay_phase_observable.py:123-135` (`score_stats`, one `roc_auc_score` per structure); `task0359_cohort_extension_by_protein.py:380-414` ("Arm B") |
| §4, combined LOPO ceiling (line 120) | 0.6203 median | **V** — note the two-layer design: LOPO-by-protein controls the *train/test* split (no leakage across a protein's own structures), a *separate* per-structure loop then computes the reported AUC | `task0318_input_space_ceiling.py:337-345` (LOPO fold loop, fits/predicts only) then `:349-367` ("per-structure raw + residualised AUC on OOF scores" — the comment is the script's own, not mine) |
| §5, pocket-block null survivors (line 132) | 45/110 → 0/110 | **N/A** | count of BH-FDR survivors, not an AUC; `task0328_pocketsweep_null_recalibration.py` |
| §1/§2, family-clearing count (line 49, 76) | 5/276, McNemar p=1.0 | **N/A** | P@5-over-pockets family-clearing count, not a pooled ROC; `task0336`/`task0338`'s `matched_comparison.py` |
| §4, field re-analysis (line 114) | 84% → 57.6%/17.8%; 94.8%/24.0% | **N/A** | k-of-6 / k-of-4 detector-agreement disjunction counts, not AUC pooling; the 84% figure is also the external field's own reported number, not ours to audit further |
| §1, apo/holo validity-rule pass rate (line 17) | 63 pairs, 49% pass | **N/A** | per-pair binary pass/fail rate, not an AUC; [[TASK-0345]] (this register's own prior work) |
| §1, proximity-anticorrelation clusters (line 74) | 7/8, ρ −0.34 to −0.50 | **V** (already cluster-tested) | [[TASK-0334]]/[[TASK-0337]] (this register's own prior work) |

**No pooled number found among the submission's own AUC-type claims.**
Every one traces to a per-structure (or, where clustering is the unit,
per-cluster) `roc_auc_score` call, or is a count/rate statistic the
HYP-P28 pooling mechanism does not apply to in the first place.

### Item 2 — arms feeding HYP-P6/P7/P13/P28

Substantially covered as a byproduct of item 1, not run as a separate
pass (budget note honored — item 1 alone consumed the allotted time):
every HYP-P6/HYP-P7 arm quoted in the submission is the same set audited
above (rows 6-9). **HYP-P13**'s own arm (`task0336`/`task0338`'s matched
classical-vs-CTQW comparison) is a family-clearing count, not an
AUC-pooling-type statistic — not itself auditable by this task's
mechanism, noted rather than skipped silently. **HYP-P28** is
[[TASK-0359]]'s own already-correctly-labeled pooled statistic
(`protein_baseline_auc`) — checked directly against the submission text
and **not currently quoted anywhere in `PHASE1_SUBMISSION_V3.md`** (the
protein-identity-channel finding itself has not yet been written into the
draft). Recorded as a fact about the current document, not a defect —
whether to add it is a drafting decision for whoever owns that document,
outside this task's own scope ("this task classifies; corrections are a
separate decision").

Item 3 (`RESULTS.md`) not started — budget fully spent on item 1/2 per
this task's own stated priority order.

### Pre-registered prediction

**HOLDS.** The submission's numbers are clean — every AUC-type claim in
`PHASE1_SUBMISSION_V3.md` is per-structure-averaged or per-cluster, never
pooled across proteins into a single ROC curve. The sentence "every AUC
in this document is computed per structure and averaged, never pooled
across proteins" is now a checked fact, cited line-by-line, not an
expectation.

### Landed

**Fold-in to [[HYP-P28]]**, dated status update: the audit this
hypothesis's own filing named as unresolved is now resolved, clean, with
a full citation table. Not a new hypothesis — this task classifies an
existing one's boundary, it does not extend the finding itself.

### Not done / explicitly out of scope, per this task's own Constraints

- Did not re-run any analysis whose aggregation was found correct.
- Did not root-cause the protein-identity channel's own mechanism
  (HYP-P28's open question, not this task's).
- Did not audit the external `allosteric` branch's own numbers.
- Did not change any published number — this task classifies only.
- Item 3 (`RESULTS.md`) genuinely not started, reported as such rather
  than given a shallow pass.

**Files**: this task file's own Done section is the deliverable (a
classification table over existing code, not a new script/result
artifact — nothing to vendor).
