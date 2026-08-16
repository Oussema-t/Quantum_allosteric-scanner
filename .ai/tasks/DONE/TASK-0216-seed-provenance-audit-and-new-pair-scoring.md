# TASK-0216 Seed-provenance audit, and scoring TASK-0215's new pairs against it

## Context

- ID: TASK-0216
- Title: audit whether `labels.functional_indices`' active-site seed is real
  across the register, fix what's fixable, and score [[TASK-0215]]'s new
  valid pairs (both static and coupled-search) under the same lens.
- Status: Done
- **Filed retroactively, 2026-08-16, Implementer A.** This work was done
  2026-08-13 (commit `a75c802`, `RESULTS.md`'s own "Seed provenance — 9 of
  13 targets were seeded at graph hubs" section) but never given its own
  task file — only a claim lock (`Reviewer-thread (Opus)`, session
  `634bc05e`, 2026-08-13 17:06) existed, and two of its own artifacts
  (`scripts/task0216_task0201_rerun_real_seed.py` and
  `results_task0216_new_pair_scoring/task0201_rerun_real_seed.json`) were
  never committed at all, despite already being cited by path in
  [[TASK-0217.003]]'s own committed Done section. This file reconstructs
  the task from its own already-committed evidence (`RESULTS.md`'s section,
  the committed scripts' own docstrings, `config/candidate_targets_task0216
  .yaml`'s own header) plus the two orphaned artifacts, filed as one
  complete record rather than left split across a stale lock and an
  undocumented commit. The original claim (session `634bc05e`) is stale —
  not among any currently live peer session, matching the same pattern
  [[TASK-0217]]'s own stale claim was overridden under, with the same
  user authorization to close out orphaned work from that session.
- Owner: Implementer (original thread unattributed beyond the session ID
  above; this filing does not claim authorship of the analysis, only of
  documenting and completing its record)
- Claimed By: —
- Claimed At: —
- Source: found while scoring [[TASK-0215]]'s new pairs — a silent fallback
  in the core label pipeline surfaced as a side effect of unrelated work,
  not a planned audit.
- Priority: **P0** — the fallback silently affected 9 of 13 register targets,
  including the register's one surviving positive (PTP1B `dcc_low`,
  [[TASK-0201]]).
- Dependency: [[TASK-0215]] (Leg B new-protein sourcing — supplies the 6 new
  candidate pairs scored here); [[TASK-0209]] (VALID-rule validity, already
  applied to the new pairs by TASK-0215); [[TASK-0213]] (coupled-search
  solver, re-run here on the new pairs). Feeds [[TASK-0217]] (.001's
  array-correspondence bug and .003's seed-provenance closure both build on
  the diagnosis here).

## Why this matters

`labels.functional_indices` resolves the active site by matching
`target_config["func_ligand"]` codes against the holo entry's ligand
groups. When nothing matches, it silently returned the 5 highest-degree
contact-graph residues — a topological proxy, not a functional site —
**without warning**. Any active-site-seeded observable computed on a
fallback target is therefore a function of graph degree, and
`baselines.degree_centrality` is itself one of the three proximity-floor
baselines, so the observable and the floor it is checked against share a
construction and the comparison stops being independent.

## Intent Contract

- Outcome: a provenance audit of every register target's active-site seed
  (real vs. fallback), fixes where the cause is a curable `targets.yaml`
  data error, a loud warning where it is not, and a scoring pass on
  [[TASK-0215]]'s 6 new valid pairs under the corrected lens.
- In Scope:
  - Audit all 13 register targets with a holo structure for real vs.
    fallback seed resolution.
  - Where the cause is `func_ligand` holding a human-readable description
    instead of a PDB chem-comp code, correct it against the holo entry's
    *actual* ligand set (not from memory), preserving the original in a
    new `func_ligand_original` field with a `func_ligand_note`.
  - Where no functional ligand exists at all, set `func_ligand: []`
    explicitly and note that the active site must come from UniProt.
  - Make `functional_indices` raise a `RuntimeWarning` on fallback, naming
    the declared value and both hazards (mechanistic misread; shared
    construction with the degree floor) — it can no longer pass silently.
  - Recompute PTP1B's `dcc_low` (the register's one surviving positive)
    under the real UniProt seed, whole-graph AUC, reported side by side
    with the fallback configuration — explicitly *not* claimed comparable
    to [[TASK-0201]]'s own stratified statistic (different quantity).
  - Score [[TASK-0215]]'s 6 new candidate pairs (`config/
    candidate_targets_task0216.yaml`, deliberately kept separate from
    `targets.yaml` — not promoted, no curated pocket label, no mechanism
    validation) on: (leg A) floor/CTQW/`dcc_low` under whichever seed each
    pair can support; (leg B) [[TASK-0213]]'s coupled-search solver at
    20×25.
  - Recompute [[TASK-0201]]'s own actual statistic (stratified
    well-powered-max AUC, graph-walk permutation null, same `FINAL_N_REPS`/
    bar) under the corrected PTP1B seed — the whole-graph AUC above is a
    different, non-comparable quantity, and this is the one that actually
    answers whether the published positive survives.
- Out Of Scope:
  - Promoting any of TASK-0215's 6 candidate pairs into `targets.yaml`.
  - Re-scoring every seeded observable on every fallback target (scoped to
    the cells above).
- Constraints:
  - `targets.yaml` corrections against real RCSB/holo data, never from
    memory.
  - Additive: preserve the original (wrong) `func_ligand` value alongside
    the fix, not overwritten silently.

## TODO

- [x] Audit all 13 targets for real vs. fallback seed resolution.
- [x] Fix the 6 targets whose `func_ligand` held a description instead of
      a code.
- [x] Flag the 3 targets with no functional ligand at all; set `[]`.
- [x] Make the fallback raise a `RuntimeWarning`, not pass silently.
- [x] Recompute PTP1B's `dcc_low` under the real seed (whole-graph AUC).
- [x] Score TASK-0215's 6 new pairs, leg A (static) and leg B (coupled
      search).
- [x] Recompute TASK-0201's own actual statistic under the corrected seed.

## Done

**2026-08-13 (original work) / 2026-08-16 (this filing).**

### Provenance audit — 9 of 13 targets on the fallback

| Seed resolves | Targets |
|---|---|
| REAL | KRAS_G12C (`GDP`), BCR_ABL1 (`NIL`), CARDIAC_MYOSIN (`ADP`), PFK (`F6P`/`ATP`) |
| FALLBACK | PTP1B, GLUCOKINASE, ATCase, CASPASE1, CASPASE7, HEMOGLOBIN, TAR_RECEPTOR, GLYCOGEN_PHOSPHORYLASE, GROEL_SUBUNIT |

Cause, visible in `targets.yaml` itself: `func_ligand` held human-readable
descriptions rather than PDB chem-comp codes (`'Glucose'` for code `GLC`,
`'substrate'`, `'O2'`/`'heme'`, `'Pi'`/`'G1P'`, `'Asp'`). PTP1B's own entry
was self-describing: `'pTyr / active-site Cys215 (descriptive marker, not
a ligand code)'`.

**Fixes landed** (`config/targets.yaml`, committed `a75c802`):
1. 6 codes corrected against each holo entry's actual ligand set (`GLC`,
   `PAL`, `HEM`+`OXY`, `ASP`, `LLP`, `ADP` — for GLUCOKINASE, ATCase,
   HEMOGLOBIN, TAR_RECEPTOR, GLYCOGEN_PHOSPHORYLASE, GROEL_SUBUNIT
   respectively), originals preserved in `func_ligand_original` +
   `func_ligand_note`. GLYCOGEN_PHOSPHORYLASE's is flagged a judgment call
   (`LLP` cofactor vs. `GLS` inhibitor).
2. 3 targets genuinely have no functional ligand at all — PTP1B (holo
   1T49 holds only drug `892` + MG), CASPASE1, CASPASE7. Set to `[]` with
   a note that their active sites must come from UniProt (later actually
   wired in by [[TASK-0217.003]]).
3. `labels.functional_indices` now emits a `RuntimeWarning` on fallback.

### PTP1B under a real seed — whole-graph AUC, not yet the comparable statistic

UniProt gives PTP1B's catalytic site as **[181, 215–221, 262]** — Cys215
plus the P-loop, identical on apo 1SUG and holo 1T49.

| | seed | pocket | max floor | `dcc_low` k=10 (whole-graph AUC) |
|---|---|---|---|---|
| fallback (what the register used) | [51, 87, 210, 214, 221] | 4 | 0.700 | 0.522 — below floor |
| real (UniProt catalytic site) | [181, 215–221, 262] | 4 | 0.701 | 0.389 — below floor |

Seed overlap: 1 residue of 9. Δ(whole-graph AUC) = −0.133. **Explicitly
not** a refutation of [[TASK-0201]] — that result used a stratified
well-powered-max AUC against a graph-walk permutation null, a different,
non-comparable statistic. What this leg establishes is that the seed
correction materially changes the score field at all.

### TASK-0215's new pairs — leg A (static scoring)

`scripts/task0216_score_new_pairs.py`, `results_task0216_new_pair_scoring
/results.json`. Only 2 of 6 candidate pairs have a derivable real seed
(TEM-1's two pairs have no functional ligand at all — a coverage gap,
stated not worked around, per `config/candidate_targets_task0216.yaml`'s
own header):

| Target | floor | CTQW | `dcc_low` k=10 |
|---|---|---|---|
| GLUR2_ANIRACETAM | 0.811 | 0.735 (below) | 0.295 |
| GLUK1_BPAM | 0.761 | 0.796 (clears, +0.035) | 0.323 |

`dcc_low` scores 0.295/0.323 on the first two instances where its seed is
real — far below floor and below chance, reached by a different route
from the PTP1B finding and pointing the same way.

### TASK-0215's new pairs — leg B (coupled search)

Re-running [[TASK-0213]]'s solver at 20×25 on the new pairs; only the 2
TEM-1 pairs pass the firewall and are interpretable (GLUR2_ANIRACETAM and
FPPS_YF0282 invert; GLUR2_TRU and GLUK1_BPAM error on an apo/holo length
mismatch and a degenerate ANM spectrum respectively):

| Target | successes / 20 | firewall |
|---|---|---|
| TEM1_BLA_CBT | 0/20 | ok |
| TEM1_BLA_FTA | 0/20 | ok |

Combined with [[TASK-0213]]: **KRAS_G12C 13/65 (20%), PTP1B 0/65, TEM1_CBT
0/20, TEM1_FTA 0/20 — 1 of 4 easy, 3 of 4 not.** [[TASK-0213]]'s CLOSED
verdict was correctly applied to its own pre-registered 2-target rule, but
KRAS_G12C now looks like the outlier rather than PTP1B, and the
generalization of "search is not the bottleneck" is materially weaker than
that verdict reads on its own.

### TASK-0201's own statistic, recomputed under the corrected seed — the previously-orphaned step

`scripts/task0216_task0201_rerun_real_seed.py`,
`results_task0216_new_pair_scoring/task0201_rerun_real_seed.json` — run
2026-08-13, **committed here for the first time** (this filing). Reuses
[[TASK-0201]]'s own harness byte-for-byte (`graph_walk_matched_null_rerun
.py`'s `graph_walk_null`, `K_MODES_GRID`, `FINAL_N_REPS=20_000`,
`PERM_SEED`, the same `0.05/16` bar) — only the seed's three entry points
(`source`, `shells`, `pocket`) change, all together, all from the real
UniProt site:

| k | fallback AUC | fallback p | real AUC | real p | bar |
|---|---|---|---|---|---|
| 5 | 0.704 | 0.33735 | 0.569 | 0.56825 | 0.003125 |
| 10 | **1.000** | **0.00275** | **0.598** | **0.567** | 0.003125 |
| 15 | 0.955 | 0.02385 | 0.822 | 0.17605 | 0.003125 |
| 20 | 0.955 | 0.02795 | 0.776 | 0.2846 | 0.003125 |

Fallback configuration reproduces the published p=0.0027 to within re-run
RNG noise (wiring check). **Under the real seed, no k survives at any
level.** This is the measurement `RESULTS.md`'s own "PTP1B under a real
seed" section named as outstanding and not yet done — it had, in fact,
already been run; the result was simply never committed or written back
into that section. [[TASK-0217.003]] later independently re-derived this
exact result from fresh code (byte-identical: AUC 0.5980392156862745, p
0.56725) before this gap was noticed, which is how it surfaced.

### Not attempted

- Promoting any of TASK-0215's 6 candidate pairs into `targets.yaml`.
- Re-scoring every seeded observable on the other 7 fallback targets
  beyond PTP1B's own headline cell.
- Root-causing why this task's own step-5 script and result were never
  committed alongside the rest of its work — flagged, not chased
  ([[TASK-0217.003]]'s own "Not attempted" section already made the same
  call for the same gap).
