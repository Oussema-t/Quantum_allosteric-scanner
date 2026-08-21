# TASK-0127 Extend the ASD generalization set and make it the reported headline

## Context

- ID: TASK-0127
- Title: [[TASK-0081]] ran 2 of 4 candidate ASD targets (PTP1B,
  CASPASE7 — the other 2 failed independent RCSB verification). Extend
  to 2-4 *additional* unseen targets and reframe the generalization set
  as the submission's **reported headline result**, not an appendix —
  per the panel, this is the direct mitigation for repeated-exposure
  overfitting risk across ~15 review cycles on the same 3 answer keys.
- Status: Done
- Resolution: done
- Owner: Implementer
- Claimed By: Implementer C (this thread)
- Claimed At: 2026-07-18 16:05
- Source: `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §3 (Weaknesses #9),
  §5 P2-10. Cross-references `.ai/tasks/TODO/TASK-0115-repeated-exposure-generalization-gate.md`
  (names this exact mitigation).
- Priority: **P2 — weeks 4-6.**

## Intent Contract

- Outcome: (1) 2-4 additional ASD-database targets, independently
  RCSB-verified (same discipline TASK-0081 already established: real
  chain-ID/ligand confirmation before use, not trusted from
  `config/targets.yaml`'s existing draft guesses) — targets genuinely
  never scored against by any of this project's prior review cycles;
  (2) full pipeline run against each, under whatever seed/clock/
  potential-gauge fixes ([[TASK-0118]]/[[TASK-0119]]/[[TASK-0121]]) have
  landed by then; (3) `RESULTS.md`/submission framing restructured so
  this generalization set — not the 3 mandatory targets' repeatedly-
  reviewed numbers — is the headline evidence of whether a real signal
  exists, per [[TASK-0115]]'s own reasoning (code-level `frozen_context`/
  LOPO gates multiple-comparisons abuse; nothing gates the ~15 human
  review cycles that have now looked at the same 3 answer keys).
- Why this is P2, not P0/P1: it depends on the gauge fixes
  ([[TASK-0118]]/[[TASK-0119]]/[[TASK-0121]]) actually landing first —
  running a generalization set through a still-gauge-contaminated
  pipeline would just reproduce the same undetermined state on more
  targets, not resolve anything.
- In Scope:
  - RCSB-verify 2-4 new ASD candidates (reuse `config/targets.yaml`'s
    remaining draft pool from TASK-0081's own sourcing, or find new
    ones if that pool is exhausted of usable candidates).
  - Run the full pipeline against each, under the post-P0/P1-fix
    pipeline state.
  - Restructure `RESULTS.md`'s framing: generalization-set results as
    the headline, the 3 mandatory targets' numbers as supporting detail
    with their gauge-contamination history stated plainly.
- Out Of Scope:
  - Building the gauge fixes themselves — this task consumes their
    output, does not re-derive it.
  - Any GLUCOKINASE/TAR_RECEPTOR-style config-schema fixes ("chains"
    field not expressing multi-structure chain differences) unless they
    turn out to block a needed new candidate — cross-reference
    `.ai/memory/questions/code-reviewer/open/Q-0001-...md` if so, don't
    silently reopen that question here.
- Constraints And Invariants: every new candidate must be independently
  RCSB-verified before use — do not repeat trusting `targets.yaml`'s
  draft guesses uncritically, per TASK-0081's own hard-won lesson (the
  YAML unquoted-numeric-ligand-code bug, the two candidates that failed
  verification).
- Planned Validation: full real runs against all new targets, reported
  with the same floor/ceiling/actual discipline as the 3 mandatory
  targets — no lighter-touch reporting standard for the "headline" set
  than for the original one.

## In Progress

None

## TODO

- [x] Identify and independently RCSB-verify 2-4 new ASD candidates.
- [x] Run full pipeline against each (post-gauge-fix pipeline state).
- [x] Restructure `RESULTS.md` framing: generalization set as headline,
      mandatory-target numbers as supporting detail with contamination
      history stated.

## Dependency

- Soft-hard: should not start in earnest until [[TASK-0118]]/[[TASK-0119]]
  (and ideally [[TASK-0121]]) have landed — running this against a still-
  gauge-contaminated pipeline reproduces the same problem on more data.
- [[TASK-0081]] (Done) — the 2 already-verified targets (PTP1B,
  CASPASE7) are this task's starting point, not redone.
- [[TASK-0115]] (TODO) — same underlying motivation; coordinate rather
  than duplicate scope if TASK-0115 is picked up around the same time.

## Open Questions

- **Resolved**: TASK-0081's remaining draft pool (6 candidates: ATCase,
  CASPASE1, HEMOGLOBIN, TAR_RECEPTOR, GLYCOGEN_PHOSPHORYLASE, PFK) had
  exactly 1 independently-verifiable candidate (CASPASE1). A 2nd came
  not from sourcing a brand-new target but from resolving GLUCOKINASE's
  already-known, already-diagnosed schema blocker (Q-0001) — the task's
  own text explicitly permits touching that "if it turns out to block a
  needed new candidate," which it did once the draft pool was otherwise
  exhausted. No target was sourced from scratch. See Done for the full
  per-candidate verification findings.

## Done

**Dependency check, before starting**: [[TASK-0118]] (seed gauge),
[[TASK-0119]] (clock), [[TASK-0121]] (potential renormalization) all
confirmed Done in `.ai/COMMON.md` before this task was claimed — not
assumed from working-tree state, checked via `git log`/registry status,
per this session's own established discipline after an earlier mistaken
assumption on a different task.

**RCSB-verified the remaining draft pool (6 candidates), same discipline
TASK-0081 established** (fetch apo/holo directly via `prody.parsePDB`,
inspect real chain composition and hetero ligand records — never trust
either source doc):

| Target | Result |
|---|---|
| **CASPASE1** | Verified clean. `chains=[A,B]` (same dimer-interface mechanism class as CASPASE7); holo (2FQQ) clean, ligand F1G (19 atoms, chain B) confirmed present. Apo (1ICE) has 3 chains (A=167 res, B=88 res, T=3 res); chain T is the bound peptide-aldehyde active-site inhibitor Ac-YVAD-CHO (hetero ACE+ASA) — excluded naturally by `chains=[A,B]`, flagged as a data-quality caveat (apo isn't ligand-free at the orthosteric site) but doesn't corrupt the allosteric-pocket label (derived from holo contacts + UniProt annotation, not apo's own ligands). **Used.** |
| **GLUCOKINASE** | Verified clean, but blocked on a real schema gap TASK-0081 already found and raised as `Q-0001` (2026-07-15): apo (1V4S) chain A, holo (3H1V) chain X, both real, `targets.yaml`'s single `chains` field can't express a per-role mapping. Resolved this task (see below). **Used.** |
| **ATCase** | Fails. 6AT1/4KH1 deposited structures have only 4 of the full dodecamer's 12 chains (2 catalytic C3 trimers + 3 regulatory R2 dimers) — the regulatory subunits carrying the CTP/UTP allosteric site are entirely absent from these entries. 4KH1's only ligand (PAL/PALA) is a catalytic-site transition-state analog, not a regulatory-site ligand. Confirms v2's own warning directly rather than trusting it; real biological-assembly-expansion work needed, out of scope. Not used. |
| **HEMOGLOBIN** | Fails, worse than the config's own flagged concern. Neither 2HHB (apo) nor 1HHO (holo) has BPG (the target ligand) in its hetero records at all — no `drug_ligand` resolvable, same failure mode as TAR_RECEPTOR. Also confirmed 2HHB is the full alpha2beta2 tetramer (4 chains) while 1HHO's asymmetric unit only has 2 — an apo/holo assembly mismatch on top of the missing ligand. Not used. |
| **GLYCOGEN_PHOSPHORYLASE** | Fails, a new finding not anticipated by v2's own warning. Both 1GPY/1A8I are actually single-chain depositions (~820 res, chain A only) — the "functional dimer" concern is a biological-assembly fact, not a deposition fact, so multi-chain handling per se was not the real blocker. The real problem: "apo" (1GPY) already has G6P bound — G6P and the intended allosteric ligand AMP are competing effectors at the *same* regulatory site (both stabilize the T-state). "Holo" (1A8I) has GLS (glucose) instead, at the catalytic site, not the AMP/G6P site. Neither structure is clean apo/holo for the pocket of interest. Not used. |
| **PFK** | Fails, more severely than the config's own organism-transfer concern. Apo (1PFK, ~320 res/chain) and holo (3O8L, ~748 res/chain) differ enough in size that they may not be the same protein at all (3O8L looks like a different, larger PFK isoform). Independent of that, "apo" 1PFK already has FBP bound (the intended allosteric activator) on both chains; "holo" 3O8L's only ligand is PO4, not FBP/ADP. Not used; would need correct apo/holo PDB IDs re-sourced from scratch, out of this task's verify-the-draft-pool scope. |

Ended at 2 *new* targets (4 total with PTP1B/CASPASE7), not 4 new, for
the same reason TASK-0081 itself ended at 2 instead of 4 — the failures
above are real and substantive, each different, not backfilled with a
weaker pick to hit a round number.

**Resolved `Q-0001` (GLUCOKINASE's apo/holo chain-letter mismatch)**:
added optional `apo_chains`/`holo_chains` per-role override fields.
`clean.py::clean_from_config` now reads `cfg.get(f"{role}_chains",
cfg.get("chains"))` instead of always reading the shared `chains` field
— additive, backward-compatible by construction (falls back to `chains`
when the override is absent, so every one of the other 13 targets'
configs, which only ever set `chains`, is completely unaffected).
`run_challenge.py::_load_apo_holo`'s own separate holo-ligand-parsing
call site needed no change: it already falls back to
`sorted(set(holo.chain_ids))` when `target_config.get("chains")` is
falsy, and `holo.chain_ids` correctly reflects the post-`holo_chains`-
filtered structure once `clean_from_config` applies the fix — verified
this by reading the call site, not assumed. New `tests/test_clean.py`
(5 tests, no network dependency — `load_target_config`/`clean`
monkeypatched, chain-selection logic tested in isolation): shared-field
fallback, per-role override for each role independently, mixed
override/fallback (one role set, one not), missing-pdb-id still raises.
Moved `Q-0001` from `open/` to `answered/` with the resolution.

**Re-ran PTP1B/CASPASE7 under the current pipeline** (their TASK-0081
verdicts predated all 3 gauge fixes — confirmed by inspecting the old
`verdict.json`: `most_impactful_term: V_R` on both, no
`_diagnosis_score_ci`/`_diagnosis_floor_ci` fields at all, i.e. pre-
[[TASK-0112]] too). This task's own Intent Contract explicitly requires
"run under whatever seed/clock/potential-gauge fixes have landed by
then" — re-running was not optional.

**Real runs, all 4 targets** (`run_challenge.py --target <name>`, live
RCSB fetch, `results/tasks/0127/<target>/`):

| Target | N | Pocket size | Actual AUC | Max floor (95% CI) | CI overlap | Diagnosis | most_impactful_term |
|---|---|---|---|---|---|---|---|
| PTP1B | 298 | 14 | 0.2050 | 0.4847 [0.242, 0.591] | Yes | `BEATS_CHANCE_NOT_FLOOR` | V_C |
| CASPASE7 | 461 | 7 | 0.6463 | 0.7542 [0.575, 0.959] | Yes | `BEATS_CHANCE_NOT_FLOOR` | V_T |
| CASPASE1 | 255 | 6 | 0.8119 | 0.9070 [0.776, 0.976] | Yes | `BEATS_CHANCE_NOT_FLOOR` | V_B |
| GLUCOKINASE | 448 | 17 | 0.7713 | 0.8531 [0.767, 0.921] | Yes | `BEATS_CHANCE_NOT_FLOOR` | V_C |

All four deliverables (connectivity matrix, hit list, report, verdict)
verified directly for all 4 targets: matrices symmetric/zero-diagonal
at the correct `(N,N)` shape; hit lists have 5 real resnums each.

**Headline finding**: 4/4 generalization targets land in
`BEATS_CHANCE_NOT_FLOOR` with overlapping score/floor 95% CIs — none
statistically decisive, the same pattern this project has found
repeatedly on the mandatory set, now confirmed on targets no review
cycle has ever seen. PTP1B remains anti-correlated with its true pocket
(0.205, well below 0.5, on a genuinely distal ~20 A site) — the same
finding TASK-0081 reported, confirmed (slightly strengthened, was
0.2497) under the fully gauge-fixed pipeline. `most_impactful_term` is
never `V_R` on any of the 4 targets (V_C/V_T/V_B/V_C) — independent
cross-validation of [[TASK-0121]] on data that task's own real-target
check (KRAS_G12C, BCR_ABL1) never touched.

**Ceiling intentionally not computed for any of the 4 targets.**
Found, while preparing to run it, that `ceiling.py::_PARAM_RANGES`
still samples each `lam_*` uniformly on `(0.0, 2.0)` — the pre-
[[TASK-0121]] scale. Since [[TASK-0121]] z-scored every potential term
to std 1, this range permits a combined-potential disorder up to
`sum|lam_i| = 10`, ~25x this project's own `sigma(V) <= 0.2*J = 0.4`
bound. A ceiling search against that range would not measure this
operator family's real headroom; it would search back into the
disorder regime TASK-0121 just fixed, likely finding pathologically
localized operators. Checked whether this was already known before
touching anything: yes — `REVIEW-panel-2026-07-17.md` P0-4 names this
exact gap ("`ceiling.py::_PARAM_RANGES`... TASK-0121's own bound applied
to the one place that ignores it") and [[TASK-0116]] already carries
"Fix `_PARAM_RANGES` to respect `sigma|lam| <= 0.4`" as its own explicit
TODO item. Fixing it here would duplicate TASK-0116's scope and (since
another thread had `ceiling.py` under active concurrent edit for
[[TASK-0130]] at the time) risk a real staging collision. Ran 3
exploratory trials on CASPASE1 to confirm the stale range empirically
(sampled `lam_B=1.25, lam_T=1.79, ...` — old-scale values), then removed
that checkpoint (gitignored scratch, not committed) rather than leave a
stale-range checkpoint file a future TASK-0116 run might mistake for
valid progress under the same seed. **Floor + actual only, matching
TASK-0081's own original precedent for this exact target set** — not a
lighter-touch standard invented here. Re-run ceiling for all 4
generalization targets once TASK-0116 lands.

**Restructured `RESULTS.md`'s framing**, consistent with the document's
own "append new runs as new dated sections, never delete/reorder a
prior run's numbers" convention (a full reorder was avoided as both
unsafe under concurrent editing by other threads and unnecessary to
achieve the actual goal): added a "reading order" note directly after
the document's intro, before the first dated section, explicitly
directing a reader to the generalization set as headline evidence and
the mandatory-3 targets as supporting/mechanistic detail with their
repeated-exposure history stated plainly. Added a new dated section
("ASD generalization set — headline evidence") with the full 4-target
table, findings, and the ceiling-deferral explanation, placed
chronologically per the doc's own convention (before "Index of open
questions"). New open-questions row #14.

**Not done, flagged rather than silently skipped**: `COMPETENCE_MAP.md`
has its own "Generalization targets" section (updated by TASK-0081
originally) that should get these same 4 rows — not touched here since
another thread had it under active concurrent, unrelated edit at
staging time; flagged for whoever next touches that file. Ceiling
numbers for all 4 targets, deferred to [[TASK-0116]] (above). Full
submission/rubric-writeup document restructuring beyond `RESULTS.md`
itself was not attempted — no such document exists yet in this repo
(same gap TASK-0081 itself flagged and left open).
