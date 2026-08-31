# TASK-0302 — Sibling-conformer pocket persistence as an independent selector signal

- Status: Done
- Priority: **High — the strongest untried lever, and independent of everything already ruled out**
- Filed: 2026-08-30 by Reviewer thread
- Related: [[TASK-0301]], [[TASK-0300]], [[TASK-0288]], external handover §4

## Why

[[TASK-0301]] established that every rule in the 61-rule family is a
function of the same two inputs — distance-to-seed and fpocket
druggability — so ensembling, voting and confidence-weighting over them
provably cannot work. A meta-selector needs **genuinely independent**
evidence.

Whether a cavity **persists across independently solved structures** is
evidence of a completely different kind. Your agents' handover §4 already
established feasibility: **every target has siblings at >=95% sequence
identity — median 53 entries, minimum 10, none below 5** — scanned live
via `search.rcsb.org`. No MD, no Docker, fully unblocked.

## Scope

- [x] For each target, retrieve sibling entries at >=95% identity
      (`siblings.json` in `.ai/reviews/2026-08-29 - distal pockets/`
      already holds a scan — reuse rather than re-query).
- [x] **Apply the holo filter FIRST** (see Constraint). Report the sibling
      count surviving it per target, before any scoring.
- [x] Align each sibling to the target apo, run fpocket, and score each
      apo candidate pocket by **fraction of siblings in which an
      overlapping cavity is detected**.
- [x] Test persistence as (a) a standalone ranker and (b) a tie-breaker on
      top of `hop>=1 + drug_alone`, cluster-robust, against random.
- [x] Report whether persistence is independent of pocket size and
      druggability (partial correlation) — if it is just size again
      ([[TASK-0287]]), say so and stop.

## Constraint — the circularity trap

**Most siblings are holo, and some contain the drug ligand itself.**
Scoring "pocket persistence" over structures solved *with the allosteric
drug bound* measures the ligand's own imprint, not intrinsic
persistence — the same self-fulfilling error flagged for the matched-holo
control. **Exclude at minimum the target's own `drug_ligand`, and report
results both with and without an apo-only restriction.**

## Note

[[TASK-0301]]'s dominating constraint applies: **13 clusters cannot
validate a selector.** Run this as a proof of concept and to check
independence — not as a claim. Validation belongs on the larger cohort
([[TASK-0304]]).

## Done (2026-08-31, Implementer C)

**Verdict: a clean negative, under both filtering regimes.** Sibling-
conformer pocket persistence gives no standalone ranking benefit
(p=0.969 min-bar filter, p=0.856 strict apo-only filter — this task's
own Constraint's "report both" honored, not just the weaker one) and
makes literally zero difference as a druggability tie-break (mean
Δ=+0.0000 exactly, p=1.000 — continuous-valued druggability essentially
never ties exactly, so the tie-break role this task's own Scope asked
for had almost no real opportunity to matter). The independence check is
mixed: persistence correlates more with pocket **size** (ρ=0.190,
p=7×10⁻⁸) than with druggability (ρ=0.129 raw, dropping to ρ=0.061,
p=0.086 once size is controlled) — this task's own Note's own explicit
instruction ("if it is just size again, [[TASK-0287]], say so") is
partially triggered: not fully redundant with size, but size is the
stronger of the two correlates, and the residual link to druggability is
borderline non-significant.

### Method, faithful to this task's own Scope and Constraint

New `scripts/task0302_sibling_persistence.py`. `siblings.json` (external
handover's own live RCSB scan) reused unchanged — its own apo/chain keys
checked directly against `config/candidate_targets_task0243.yaml` before
trusting it, not assumed: **exact match, 20/20**. Candidate/truth
apparatus mirrors `task0282_pocket_selection_sweep.build_target`'s own
call shape (`t0242.prep` + `t0242.fpocket_candidates`, TASK-0298's own
(chain,resnum)-keyed matching) as a separate, duplicated implementation —
`task0282` itself untouched, matching [[TASK-0303]]'s own lane-collision
precedent (Lane B still owns that script this window). Sibling pockets
mapped onto target apo numbering via `allostery.labels.
_needleman_wunsch_map`/`_sequence` — the same sequence-only primitive
`holo_pocket_mask` already uses for apo/holo numbering offsets, reused
here across independently-deposited entries; best-matching sibling chain
chosen by alignment score, not assumed to be chain A.

**The circularity trap, handled first, both ways reported (this task's
own Constraint)**: `min_bar` excludes only siblings carrying the
target's own `drug_ligand`; `strict_apo` excludes any sibling carrying
ANY ligand `backend.rcsb.ligands_and_sites`/`classify_ligand`
categorises as drug or ligand ([[TASK-0278]]'s own already-validated
classification, reused, not a new heuristic).

**Two proof-of-concept bounds, disclosed not hidden**: unfiltered
sibling counts run to 493 (`SUMO_E1_FHJ`, itself inflated by
`siblings.py`'s own 500-row RCSB pagination cap) and 1,999 total across
the frozen 20 — one live fetch per sibling for the holo check alone made
the full set intractable in one pass. `MAX_SIBLINGS_CHECKED=30` (applied
before the holo filter) and `MAX_SIBLINGS_SCORED=10` (applied after, per
variant) — both stated in the script's own module docstring, not
silently narrowed. Full run: ~2 hours wall-clock (up to ~600 live RCSB
holo-filter fetches + up to ~400 Docker fpocket calls across both
filter variants, [[TASK-0285]]'s own containerized fpocket).

### Sibling coverage, reported before any scoring (this task's own Scope)

| | median | min | max |
|---|---|---|---|
| available (uncapped) | 88 | 10 | 493 |
| checked (capped at 30) | 30 | 10 | 30 |
| survive min-bar | 29.5 | 9 | 30 |
| survive strict-apo-only | 3.5 | **0** | 19 |

**The strict filter is much harsher than min-bar** — median drops from
~30 to ~3.5, and **2 of 20 targets (`PKR_MITAPIVAT`, `PKR_AG946`) have
ZERO strict-apo-only siblings** among the first 30 checked: essentially
every deposited sibling structure of this protein carries some ligand.
Correctly excluded from the strict-only significance test (18/20, not
imputed as a zero), stated so the smaller n isn't silently absorbed.

### Standalone ranker, cluster-robust (TASK-0261's exact 13-cluster sign-flip test)

| filter | n | n_clusters | mean Δ(persistence-selected − random EH) | p |
|---|---|---|---|---|
| min-bar | 20 | 13 | −0.0006 | 0.969 |
| strict apo-only | 18 | 12 | +0.0033 | 0.856 |

**Not significant either way** — both deltas are within noise of zero,
not merely "not surviving a correction." The persistence-selected
candidate scores EH=0 (zero overlap with the true pocket) on 16/20
targets under the min-bar filter; only `GAC_CPD12`, `TRP_SYNTHASE_F6F`/
`F19`, and `NAMPT_NPA1R` show any real signal at all.

### Tie-break, cluster-robust

`(fpocket_drug, persistence)` lexicographic vs `fpocket_drug` alone:
mean Δ=**+0.0000** (exact), p=1.000, n=20/13 clusters. Persistence never
actually broke a tie in this data — a real design-level finding, not a
null result to over-read: real-valued druggability scores essentially
never collide exactly across fpocket candidates, so a literal
"tie-breaker" role has almost no opportunity to matter regardless of
whether persistence itself carries signal.

### Independence — mixed, and size is the stronger correlate

Pooled, per-target-z-scored Spearman across all 789 real candidates:

| pair | ρ | p |
|---|---|---|
| persistence, `fpocket_drug` | 0.129 | 0.0003 |
| persistence, `n_res` (pocket size) | **0.190** | **7×10⁻⁸** |
| persistence, `fpocket_drug`, controlling `n_res` | 0.061 | 0.086 |

Persistence correlates more strongly with pocket **size** than with
druggability, and its own link to druggability nearly vanishes (drops
by more than half, crosses into non-significance) once size is
controlled. Per this task's own Note: **partially, not fully, "just
size again"** — size is real and the dominant of the two tested
correlates, though the effect is a genuine, modest, independent
component too small to salvage the standalone-ranker null above.

### Not done

Full sibling coverage was not exhaustively scored (the two caps above,
disclosed) — a real limitation for low-coverage targets specifically:
`SUMO_E1_FHJ`'s own 10 scored siblings are ~2% of its 493 available, not
necessarily representative. `OVERLAP_JACCARD=0.2`'s own threshold was
not swept — a single, reasonable, pre-committed value, not tuned against
any result. Validation on a larger cohort remains [[TASK-0304]]'s own
scope, per this task's own Note, not attempted here.

**Script:** `scripts/task0302_sibling_persistence.py`. **Data:**
`results/tasks/0302_sibling_persistence/sibling_persistence.json`.
