# Task classification ledger — TASK-0326

**Status: FULL SWEEP COMPLETE (344/344 non-meta tasks classified).**
Pilot (39 tasks) was signed off 2026-09-04 by the repo owner directly
(commit `ebdeb88`) with a standing rule for every `NO-HYP` draft, pilot
and full-sweep alike: **a finding earns its own new hypothesis only if
it is a genuinely different claim or mechanism — not if it only
sharpens, extends the evidence for, or adds a second instance of a
claim an existing hypothesis already makes.** That sign-off resolved
the pilot's own two flagged calls (Draft 2 → new id, cross-referencing
HYP-P14; Draft 4 → fold into HYP-P13, not a new id) and authorized the
full sweep. This file now covers all of it.

**The full sweep was run by 6 parallel Explore agents** (~51 tasks
each), briefed with the same classification scheme, the same
register cheat-sheet, and the same verification discipline (grep the
register files, read the surrounding context, don't credit a
`HYP-<id>` match on incidental/methodology-reuse citations). Each
agent's raw table + drafts is preserved verbatim below; I did not
re-derive their classifications, only compiled, cross-referenced for
duplicates, and applied the standing rule to produce a landing
disposition for every `NO-HYP` draft (see "Disposition" section).

**Landing has NOT happened yet.** Given the volume this sweep
surfaced (82 `NO-HYP` tasks across ~40 draft groups, several times
the pilot's own proportion — see "Distribution" below for why), and
one genuinely consequential discovery along the way (`search_complexity.md`'s
own headline "one surviving positive" claim appears to be stale — see
"Flag: a claim, not just a citation, may need correcting" below),
mechanically editing `physics.md`/`search_complexity.md` in ~20 places
without a further check-in felt like a bigger step than the sign-off's
own scope contemplated (it reviewed 5 drafts in detail, not ~40). The
disposition table is a recommendation, not yet applied.

## Distribution (full corpus, 344 tasks)

| bucket | pilot (n=39) | full sweep (n=305) | combined (n=344) |
|---|---|---|---|
| `ENG` | 27 (69%) | 177 (58%) | 204 (59%) |
| `HYP-<id>` | 6 (15%) | 52 (17%) | 58 (17%) |
| `NO-HYP` | 6/5 groups (15%) | 76/~40 groups (25%) | 82/~45 groups (24%) |
| `UNCLASSIFIED` | 0 | 0 | 0 |

**Why `NO-HYP` is proportionally higher in the full sweep than the
pilot** (15%→25%): not a calibration drift — the corpus is
chronologically ordered, and the project's early phase (roughly
TASK-0001–0100) is infrastructure-heavy (module implementation,
tooling, scaffold), while the back half (roughly TASK-0200–0325) is a
sustained, dense run of scientific investigation as the project
searched for and then progressively ruled out signal. The pilot's
stratified every-9th sample landed proportionally fewer of those dense
science clusters than a denser sample of the same range would. `ENG`
still did not quietly absorb real science anywhere in the full sweep
either (every agent flagged and read full files for borderline cases,
same discipline as the pilot's own spot-checks) — the shift is a real
feature of the corpus's chronology, not overclaiming.

**`UNCLASSIFIED` stayed at 0/344** across the whole corpus. Not
because every case was easy — several agents flagged genuinely
close calls (see disposition notes) — but because a specific read of
the Done section always settled it one way or the other.

## Flag: a claim, not just a citation, may need correcting

`search_complexity.md`'s own introduction states, uncontested since
2026-08-05/06: *"The one surviving positive: PTP1B `dcc_low` k=10,
p=0.0027 vs bar 0.003125... under a null built specifically because
the previous one structurally could not reach real pocket geometry."*

TASK-0216 (2026-08-13, in this sweep) found `labels.functional_indices`
silently fell back to the 5 highest-degree contact-graph residues (the
same construction as the `degree_centrality` proximity-floor baseline)
on 9 of 13 register targets — **including PTP1B, the one target
carrying this exact positive.** Re-running the identical statistic
under PTP1B's real, UniProt-derived active-site seed collapses it
completely: AUC 1.000→0.598, p 0.00275→0.567, no `k` in the sweep
survives its own bar. TASK-0217 (parent, same date) states the
consequence directly: *"the register's honest surviving-positive count
is therefore zero, not one."*

This is not a missing-citation gap the checker (`hyp_register_check.py`)
would ever catch — it is `search_complexity.md`'s own currently-live
prose asserting something a later, real measurement contradicts. Flagging
prominently rather than silently fixing (out of this task's own scope,
and a content edit to a hypothesis file's core claim deserves the same
review this whole task's other landings are getting) — an Architect or
the repo owner should look at this one specifically, independent of
whatever happens with the `NO-HYP` disposition table below.

## Method (unchanged from the pilot, applied by all 6 agents)

Read title + `- Status:` line + full Done section (or equivalent —
several older/newer files use `## Findings`/`## Result`/`## Resolution`
instead) for every task. For `HYP-<id>` candidates: grep all 4 register
files, read the surrounding context, and only credit the match if the
citation is deciding that hypothesis's own claim — not incidental
methodology reuse (the recurring "trap case" every agent was briefed
on and multiple caught: e.g. TASK-0260 is cited inside `HYP-P13` only
for its crypticity-stratification code, not its own actual headline
finding about external SOTA predictors).

## Full ledger (344 tasks)

### Pilot (39 tasks, Architect-signed-off 2026-09-04)

| task | class | evidence / reasoning |
|---|---|---|
| TASK-0001 | `ENG` | Scaffold bootstrap — repo-local scope, deliverable-shape, directory-model decisions. No scientific claim. |
| TASK-0010 | `ENG` | Implements `report.py` (hit-list, jaccard, verdict template) per notebook spec. Code deliverable, not a claim test. |
| TASK-0019 | `ENG` | Commit-packaging + a git-index race incident with a concurrent thread. Process/infra. |
| TASK-0026 | `ENG` | Parent/coordinator for capability-runner-recovery subtasks. Infra. |
| TASK-0030 | `ENG` | Extracts shared `kabsch_fit`/`kabsch_align` helper. Pure refactor/dedup, byte-identical output confirmed. |
| TASK-0039 | `ENG` | `clean.py` alt-loc parsing bug fix (ProDy default drops non-`'A'` records). Data-layer bug fix, no allostery claim. |
| TASK-0048 | `ENG` | Code review of `protocol.py`/`select.py`. Review process, not a science finding. |
| TASK-0057 | `ENG` | SE(3)/permutation-invariance verification of `pathways.py`'s implementation. Code-correctness, not mechanism. **Spot-checked in full.** |
| TASK-0066 | `ENG` | Extracts shared `_kirchhoff_eigh`/`_normalized_dcc` helper. Refactor/dedup. |
| TASK-0075 | `ENG` | Builds `cumulative_overlap_gate` (GO/NO_GO/UNSTABLE reporting function). Tooling for a gate, not itself a claim. |
| TASK-0079.005 | `ENG` | Runs the end-to-end pipeline on 3 mandatory targets; raw output feeds TASK-0091/0092/0093, which are the actual analyses. Orchestration run. |
| TASK-0088 | `ENG` | `stamp_provenance`/`verify_frozen_stamp` guard (SEAM-0004 fix). Safety-rail infra. |
| TASK-0097 | `ENG` | Adds an honesty disclosure that `time_averaged_ctqw` is the decoherent limit. Documentation of an already-established fact (TASK-0095), not itself deciding one. |
| TASK-0106 | **`HYP-P6`** | CTQW-trapping reproduction across `H10`/`H2`/`H_new` at scaled λ. Cited in `physics.md`, inside the `HYP-P6` section. |
| TASK-0115 | `ENG` | Names the "repeated-exposure" risk, places it in `INVARIANCE_PROTOCOL.md`. Process/methodology rule, not a physics claim. |
| TASK-0124 | `ENG` | Re-anchors CARDIAC_MYOSIN's holo structure (8QYP vs a relayed 9GZ1 lead). Data-curation decision. |
| TASK-0133 | **`HYP-P8`** | Random-patch control for the learnability gate — finds KRAS_G12C's corrected pocket-restricted CO would flip its verdict. Cited in `physics.md`, inside `HYP-P8`. **Spot-checked in full.** |
| TASK-0142 | **`HYP-P12`, `H2.1`** | H2/L1 half of the quantum-Betti bridge — title names `HYP-P12` directly; also `reference_register.md`'s own `H2.1` row. |
| TASK-0151 | **`NO-HYP`** (draft P1) | `dcc_low`'s CARDIAC_MYOSIN positive generalizes to PTP1B; transport's BCR_ABL1 positive doesn't generalize. Genuinely uncaptured. |
| TASK-0160 | `ENG` | Implements `quantum_connectivity_matrix` with correctness proofs. Operator-construction code. |
| TASK-0167.002 | **`NO-HYP`** (draft P2) | No target reaches 80% detection power for a planted signal at any strength tested. Uncited. |
| TASK-0178 | `ENG` | Implements `allostery.response` module + validates to 1.6e-13. Infrastructure the H4.x family runs on. |
| TASK-0188 | `ENG` | Hop-distance cutoff robustness sweep — QA audit of existing claims. **Spot-checked in full.** |
| TASK-0197 | `ENG` | `claim.py stage` cannot stage deletions — tooling bug fix. |
| TASK-0206 | `ENG` | fpocket binary drift across two build machines. Reproducibility/infra. **Spot-checked in full.** |
| TASK-0215 | `ENG` | Sources 6 new VALID apo/holo pairs from RCSB (Leg B). Dataset construction. |
| TASK-0220 | `ENG` | Calibration check of `quantum_seed_readiness`'s `SAFE` threshold. **Spot-checked in full.** |
| TASK-0229 (parent) | **`HYP-P13`; `H1`, `H2.2`, `H4.1`(partial), `H6.2`(partial), `H7`, `H9`, `H10`, `H11`, `H15.1`/`H15.2`(partial)** | Closing synthesis over `.001`-`.007`, each subtask already maps to a `reference_register.md` row. |
| TASK-0231 | `ENG` | Mutation-tests the suite's own config-level blind spot. Test-infrastructure QA. |
| TASK-0240 | `ENG` | Builds `assert_criterion_reachable` diagnostics guard. Infra. |
| TASK-0250 | **`H16.1`** | GNM-vs-B-factor model-validity check. Title names H16.1 directly. |
| TASK-0260 | **`NO-HYP`** (draft P3, with 0269) | Tests whether PocketMiner/CryptoSite/P2Rank/FTMap-FTSite close the residual. Cited only for methodology reuse elsewhere. |
| TASK-0269 | **`NO-HYP`** (draft P3, with 0260) | Runs PocketMiner for real — doesn't close the residual. |
| TASK-0278 | **`NO-HYP`** (draft P4 — **fold into HYP-P13 per sign-off**) | Occupancy ≠ allosteric effect: BCR-ABL1's MYR-held-open apo, stripping control, worse PKR instance. |
| TASK-0287 | **`HYP-P14`** | Its `fpocket druggability` row is cited directly in `physics.md`'s `HYP-P14` evidence table. |
| TASK-0296 | `ENG` | Regenerates 6 stale KRAS golden test fixtures. Test-fixture maintenance. |
| TASK-0305 | **`NO-HYP`** (draft P5) | Every arm at-or-below random at top-5 retrieval on real ASBench; CTQW significantly worse than random. **Spot-checked in full.** |
| TASK-0315 | `ENG` | Re-derives `terms_block` vs `ctqw`/`geometry`; finds a reproducibility discrepancy. QA audit of an existing comparator. |
| TASK-0324 | `ENG` | Applies TASK-0323's proposed verdict lines. Process work. |

### Full sweep — batch 1/6 (TASK-0002–0051)

| task | class | evidence / reasoning |
|---|---|---|
| TASK-0002 | `ENG` | AI-scaffold hygiene review. Process/coordination. |
| TASK-0003 | `ENG` | Builds/reconciles `targets.yaml` config data. Data curation. |
| TASK-0004 | `ENG` | Implements `labels.py`; fixes two code bugs during validation. Not a mechanism claim. |
| TASK-0005 | `ENG` | Implements `superpose.py`; one-off KRAS smoke-test, later superseded by TASK-0120/0133/0139 (HYP-P8). |
| TASK-0006 | `ENG` | Implements `protocol.py` DEV/FROZEN firewall + LOPO generator. |
| TASK-0007 | `ENG` | Implements `select.py`; synthetic-graph characterization, not a protein claim. |
| TASK-0008 | `ENG` | Implements `analysis.py`, reproducing PLAN.md's already-stated findings as regression tests. |
| TASK-0009 | `ENG` | Implements `diagnostics.py` failure-mode classifier. |
| TASK-0011 | `ENG` | Implements `baselines.py`. Code deliverable. |
| TASK-0012 | `ENG` | Implements `pathways.py`. Code deliverable. |
| TASK-0013 | `ENG` | Implements `coarse.py`. Tooling for a future NISQ study. |
| TASK-0014 | `ENG` | Implements `viz.py`. Explicitly "not scored." |
| TASK-0015 | `NO-HYP` (draft F1) | Zero admissible apo-only ANM-mode perturbation (7/7 targets) ever creates a graph shortcut to the pocket. |
| TASK-0016 | `ENG` | Test-coverage gap for `heat()`; superseded by TASK-0095. |
| TASK-0017 | `ENG` | Claim-column convention for the task registry. |
| TASK-0018 | `ENG` | Architecture reconciliation of `backend/` vs `allostery/`. |
| TASK-0020 | `ENG` | Product feature/endpoint intent inventory audit. |
| TASK-0021 | `ENG` | (TODO) Backend API Playwright test-suite plan. |
| TASK-0022 | `ENG` | (TODO) Frontend tiered Playwright test-suite plan. |
| TASK-0023 | `ENG` | YAGNI/scope-creep review against the challenge rubric. |
| TASK-0024 | `ENG` | Builds `claim.py` atomic claim/lock CLI tool. |
| TASK-0024.001 | `ENG` | (TODO) Whole-file resource locks. |
| TASK-0024.002 | `ENG` | (TODO) Git rename-detection edge case fix. |
| TASK-0025 | `ENG` | Command-hygiene policy doc + Claude Skill. |
| TASK-0026.001 | `ENG` | Builds `capability-runner.sh` dispatcher. |
| TASK-0026.002 | `ENG` | (TODO) Remaining packaging/maintenance rows. |
| TASK-0026.003 | `ENG` | (TODO) Capabilities-doc honesty pass. |
| TASK-0026.004 | `ENG` | (In Progress) Builds `pytest_local.py` wrapper. |
| TASK-0026.005 | `ENG` | Fixes `pytest_local.py`'s venv-resolution bug. |
| TASK-0027 | `ENG` | Adds `claim.py move` subcommand. |
| TASK-0028 | `ENG` | Adds `GIT-COMMIT` lock + `commit-guard`. |
| TASK-0029 | `ENG` | Adds scoped `claim.py stage` subcommand. |
| TASK-0031 | `ENG` | Widens `data_layer.py::fetch()`'s exception handling. Bug fix. |
| TASK-0032 | `ENG` | Adds HTML-escaping for RCSB strings. Security fix. |
| TASK-0033 | `ENG` | Confirms `quantum_seed_readiness` thresholds correct-by-design. Code-correctness review. |
| TASK-0034 | `ENG` | (TODO) Reconcile RCSB-fetch error-handling philosophy. |
| TASK-0035 | `ENG` | Performance fix, 13.7x speedup, bit-identical output. |
| TASK-0036 | `ENG` | (TODO) Surface a warning when `complete_apo` skips alignment. |
| TASK-0037 | `ENG` | Flags H11/H12 duplicates; superseded by TASK-0096. |
| TASK-0038 | `ENG` | Docstring-vs-behavior fix in `clean.py`. |
| TASK-0040 | `ENG` | Performance fix, ~2x speedup, bit-identical output. |
| TASK-0041 | `ENG` | `solve_ivp` success-flag check; RK45 never fails in real range — robustness gap, not a physics finding. |
| TASK-0042 | `ENG` | Hook-enforces `GIT-COMMIT` via a `PreToolUse` hook. |
| TASK-0043 | `ENG` | Git-history branch split. |
| TASK-0044 | `ENG` | (TODO) Python-version convention reconciliation. |
| TASK-0045 | `ENG` | Adds atomic `claim.py reserve-next`. |
| TASK-0046 | *(documented in `ceiling.md`, no register action needed)* | `H_new`'s own fully-optimized ceiling on KRAS_G12C (AUC≈0.525) falls below the proximity floor (0.798) — the first `ceiling < floor` case. Already recorded in `ceiling.md`'s own 2026-07-15 status update in full; `ceiling.md` is prose-narrative, not `HYP-<id>`-schemed, so there is nothing to land. |
| TASK-0047 | `ENG` | Adds missing integration + regression tests. Test-coverage engineering. |
| TASK-0049 | `ENG` | (TODO, proposal only) Backend/frontend decomposition plan. |
| TASK-0050 | `ENG` | Adopts the Seam Protocol. |
| TASK-0051 | `ENG` | Adopts the Invariance Protocol. |

### Full sweep — batch 2/6 (TASK-0052–0103)

| task | class | evidence / reasoning |
|---|---|---|
| TASK-0052 | `ENG` | Reconciles `test_leakage_gate.py` against the real API. |
| TASK-0053 | `ENG` | First Seam Protocol sweep. |
| TASK-0054 | `ENG` | SE(3)-joint-rotation regression test. |
| TASK-0055 | `ENG` | Verifies `provenance="frozen"` enforcement gap; files TASK-0088. |
| TASK-0056 | `ENG` | Phase-4 code review. |
| TASK-0058 | `ENG` | Wires `floor_scores`/`BEATS_CHANCE_NOT_FLOOR` into `classify_failure`. |
| TASK-0059 | `ENG` | Wires `learnability_verdict` into `run_frozen_verdict`. |
| TASK-0060 | `ENG` | (TODO) `claim.py question` tooling design. |
| TASK-0061 | `ENG` | (TODO) `claim.py add` tooling design. |
| TASK-0062 | `ENG` | (TODO) Incident-reporting registry design. |
| TASK-0063 | `ENG` | Widens `get_functional_indices` via `**kwargs`. |
| TASK-0064 | `ENG` | Wires `select.unsupervised_score` into a FROZEN-loop consumer. |
| TASK-0065 | `ENG` | Builds the Stage-Commit-Queue tooling. |
| TASK-0067 | `NO-HYP` (fold candidate — context for `HYP-P4`) | GNM cutoff × weight-scheme benchmark: no cutoff effect, harmonic weighting beats binary/gaussian by ~0.11-0.16 AUC (n=2, thin). `physics.md` itself already flags this as confounded/non-isolating for HYP-P4. |
| TASK-0068 | `NO-HYP` (fold candidate — extends `HYP-P11`) | Real NISQ noise sim: coherent CTQW ties/beats ENAQT at every depth/error-rate point. Same direction as HYP-P11's own claim, different method (hardware noise model vs. γ-sweep). |
| TASK-0069 | `ENG` | (TODO) `pytest_local.py` venv-resolution bug report. |
| TASK-0070 | `ENG` | Implements `build_labels` assembly. |
| TASK-0071 | `ENG` | Ports a permutation-null leak detector. |
| TASK-0072 | `ENG` | Golden-value cross-tree drift test. |
| TASK-0073 | `ENG` | Registers SEAM-0013/0014. |
| TASK-0074 | `ENG` | Golden-output characterization tests. |
| TASK-0076 | `ENG` | (TODO) `git mv` proposal. |
| TASK-0077 | `ENG` | (TODO) Unified CI proposal. |
| TASK-0078 | `ENG` | (TODO) Dissolve `__WORK_IN_PROGRESS__/` proposal. |
| TASK-0079 | `ENG` | Parent orchestrator; findings feed TASK-0091/0092/0093. |
| TASK-0079.001 | `ENG` | Writes `assemble_verdict_results`. |
| TASK-0079.002 | `ENG` | Writes hit-list/matrix assembly. |
| TASK-0079.003 | `ENG` | Writes `run_frozen_verdict` composition. |
| TASK-0079.004 | `ENG` | Writes `run_challenge.py`; files TASK-0090. |
| TASK-0080 | `ENG` | No-ground-truth reporting branch for c-Myc/1NKP. |
| TASK-0081 | `NO-HYP` (fold candidate — extends `HYP-P8`) | 2 new ASD targets corroborate the proximity-confound pattern (PTP1B AUC=0.2497 anti-correlated; CASPASE7 0.7130, beats chance not floor). |
| TASK-0082 | `ENG` | Assembles the competence map from already-computed numbers. |
| TASK-0083 | `ENG` | Versioned result-artifact contract. |
| TASK-0084 | `ENG` | (TODO) Backend endpoints proposal. |
| TASK-0085 | `ENG` | (TODO) Frontend visualization proposal. |
| TASK-0086 | `ENG` | (TODO) Execution/trigger-path proposal. |
| TASK-0087 | `ENG` | Firewall design decision (cooperative gate, not hard seal); files TASK-0218. |
| TASK-0089 | `ENG` | GAUGE/KNOB/SIGNAL classification for `select.py`. |
| TASK-0090 | `ENG` | Fixes a real BFS crash. |
| TASK-0091 | *(superseded by TASK-0102/`HYP-P8`, no separate entry)* | BCR_ABL1 GSR score clears floors by the widest margin but 0/16 pocket residues in top-20/30 — diffuse, not sharp. |
| TASK-0092 | *(superseded by TASK-0102/`HYP-P8`, no separate entry)* | Apo/holo diagnostic points to the propagator as bottleneck; later reinterpreted. |
| TASK-0093 | `HYP-P8` | Named directly in `physics.md`'s HYP-P8 status update as convergent evidence. |
| TASK-0094 | `NO-HYP` (fold candidate — foundational to `HYP-P8`) | Zero of 3 mandatory targets clear their own proximity floor apo-only. Precedes and underlies TASK-0093/0102/0104's own HYP-P8 citations, but isn't itself the cited source. |
| TASK-0095 | `ENG` | Renames `heat`→`ground_state_relaxation`, corrects framing. |
| TASK-0096 | `ENG` | Implements H11/H12/H14 operators. |
| TASK-0098 | `ENG` | Amends `INVARIANCE_PROTOCOL.md`'s SIGNAL classification. |
| TASK-0099 | `HYP-P7` | Real dephasing sweep, `COHERENCE_NOT_SIGNIFICANT` — decides HYP-P7's own claim via a complementary method to TASK-0105 (the file's named citation). |
| TASK-0100 | `ENG` | Architecture decision on sweep tiering. |
| TASK-0101 | `HYP-P1` | Cited directly in `physics.md`'s HYP-P1 status update. |
| TASK-0102 | `HYP-P8` | Cited directly in `physics.md`'s HYP-P8 status update. |
| TASK-0103 | `NO-HYP` (fold candidate — methodology support for `HYP-P8`) | Synthetic dumbbell double-dissociation (GSR tracks well-depth, CTQW tracks coupling) — the interpretive tool used to read TASK-0102/HYP-P8. |

### Full sweep — batch 3/6 (TASK-0104–0161)

| task | class | evidence / reasoning |
|---|---|---|
| TASK-0104 | `HYP-P8` | Re-frames BCR_ABL1's GSR as a structural-prior artifact. Cited directly in `physics.md`. |
| TASK-0105 | `HYP-P7` | Real 3-target ENAQT γ-sweep. Cited directly in `physics.md`. |
| TASK-0107 | `ENG` | New `claim.py resolve` subcommand. |
| TASK-0108 | `ENG` | Thin coordinator; closure once TASK-0109/0110 land. |
| TASK-0109 | `HYP-P6` | Builds the `t≈1/Δλ` validity tool. Cited in `physics.md`'s HYP-P6. |
| TASK-0110 | `HYP-P6` | Clock is 145,000x-3,950,000x too short. Cited directly in `physics.md`. |
| TASK-0111 | `ENG` | Performance refactor, byte-identical output. |
| TASK-0112 | `ENG` | Wires `block_bootstrap_ci` into headline reporting. |
| TASK-0113 | `ENG` | Re-runs the cutoff sweep against the headline operator; QA audit. |
| TASK-0114 | `ENG` | Pocket-label cutoff sensitivity sweep. |
| TASK-0116 | `ENG` | Fixes `ceiling.py`'s range bug; confirms TASK-0046. |
| TASK-0117 | `ENG` | Obsolete once TASK-0130 landed. |
| TASK-0118 | `NO-HYP` (draft F2) | Seed-cardinality gauge fix: seed cardinality (not coherence) dominates AUC variance. |
| TASK-0119 | `HYP-P6` | Per-operator clock fix; cited directly in `physics.md`. |
| TASK-0120 | `HYP-P8` | The first direct test of HYP-P8's own claim. Title literally "(HYP-P8)". |
| TASK-0121 | *(documented in ledger only; explicitly non-decisive per `physics.md`)* | Fixes an 88%-one-term normalization bug in `H_new`'s potential. `physics.md` states directly this does NOT decide HYP-P2 or HYP-P3. |
| TASK-0122 | `NO-HYP` (fold candidate — extends `HYP-P14`'s observable family) | `mode_coparticipation` mostly fails to decorrelate from distance, clears floor 1/3 targets. |
| TASK-0123 | `NO-HYP` (fold candidate — extends `HYP-P14`) | Register-wide distance-stratified AUC; no cell survives Bonferroni. |
| TASK-0125 | `ENG` | Verification-only; no bug found. |
| TASK-0126 | `HYP-P5` | Runs H13/H14 through the ceiling search. Cited directly in `physics.md`. |
| TASK-0127 | `NO-HYP` (fold candidate — extends `HYP-P8`) | 2 more ASD targets replicate the non-decisive pattern on unseen data. |
| TASK-0128 | `ENG` | Bug fix (`n_zero!=6` assertion). |
| TASK-0129 | `NO-HYP` (draft F2) | Combined seed+clock fix reverses CARDIAC_MYOSIN's only surviving positive. |
| TASK-0130 | `NO-HYP` (draft F2) | Closed-form infinite-time propagator; shipped `t_max=15` far from converged. |
| TASK-0131 | *(documented in `ceiling.md`, no register action needed)* | Ceiling-search permutation null: CARDIAC_MYOSIN's headroom is winner's-curse noise (55th pctile); KRAS_G12C marginal (p=0.045 uncorrected). Same status as TASK-0046 — belongs in `ceiling.md`'s own narrative, already discussed there. |
| TASK-0132 | `NO-HYP` (fold candidate — extends `HYP-P13`'s "geometry is the signal" row) | Published GNM transfer-entropy classical baseline: 0/3 floor-clears, underperforms `H_new`/CTQW. Same cluster as TASK-0163/0200. |
| TASK-0134 | `ENG` | CPU-time verification + long-job convention. |
| TASK-0135 | `ENG` | Reproducibility audit + `runlog.py`. |
| TASK-0136 | `NO-HYP` (new candidate) | Percolation/edge-connectivity: all 3 mandatory targets show broad, redundant (68-76 edge-disjoint routes) connectivity — not a bottleneck. A genuinely distinct topological claim, no clean existing home. |
| TASK-0137 | `ENG` | Citation-verification audit. |
| TASK-0138 | `ENG` | Ceiling-search scrutiny of H14; doesn't survive. |
| TASK-0139 | `HYP-P8` | Resolves KRAS_G12C to `AMBIGUOUS`. Cited directly in `physics.md`. |
| TASK-0140 | `HYP-P9`, `HYP-P14` | Chiral circulation — title says "(HYP-P9)". Cited in both sections. |
| TASK-0141 | `HYP-P11`, `HYP-P14` | ENAQT sweep — title says "(HYP-P11)". Cited in both sections. |
| TASK-0143 | `HYP-P10` | Graph-openness premise test — title says "(HYP-P10)". Cited directly. |
| TASK-0144 | `ENG` | Bug fix: empty correspondence on chain-letter mismatch. |
| TASK-0145 | `HYP-P14` | Cited directly in HYP-P14's observable-family list. |
| TASK-0146 | `HYP-P14` | Cited directly in HYP-P14's observable-family list. |
| TASK-0147 | `HYP-P14` | Cited directly in HYP-P14's observable-family list. |
| TASK-0148 | `HYP-P14` | Cited directly in HYP-P14's observable-family list. |
| TASK-0149 | **`NO-HYP` — merges into pilot draft P1** | `dcc_low` CARDIAC_MYOSIN positive, real-target run. Same claim as pilot Draft 1 — do not duplicate. Note: TASK-0158 later removed its Bonferroni survival under a corrected null; carry that caveat into Draft P1's own writeup. |
| TASK-0150 | `HYP-P8` | Wires the corrected verdict into `run_challenge.py`. Cited directly in `physics.md`. |
| TASK-0152 | `ENG` | Extends the random-patch null to 2 more targets. Not itself cited. |
| TASK-0153 | `ENG` | Extends the holo-diagnostic methodology; diagnostic-only. |
| TASK-0154 | `ENG` | Gates `claim.py stage` on `GIT-COMMIT`. |
| TASK-0155 | *(documented in ledger; superseded/resolved by TASK-0270)* | KRAS_G12C's positive is a lucky draw (median AUC=chance across 10 structures) and the configured apo (4OBE) is wild-type, not G12C. The genotype defect this surfaced was later fixed by TASK-0270 (4LDJ) — the finding is historically real but its own remediation already landed, so no separate hypothesis needed for a now-fixed data-integrity bug. |
| TASK-0156 | *(already captured in `search_complexity.md`'s closed-routes table)* | GRAPE control-effort observable: chance-level on all 3 targets. |
| TASK-0157 | `HYP-P14` | Cited directly in HYP-P14's observable-family list. |
| TASK-0158 | `ENG` | Fixes a project-wide permutation-null anti-conservative bias; re-runs affected tasks. |
| TASK-0159 | `ENG` | Re-points `run_challenge.py` at the converged propagator. |
| TASK-0161 | `ENG` | Pure enumeration/arithmetic (multiplicity accounting). |

### Full sweep — batch 4/6 (TASK-0162–0217.002)

| task | class | evidence / reasoning |
|---|---|---|
| TASK-0162 | `HYP-P13` | Cited directly as HYP-P13's own discussed counter-evidence point. |
| TASK-0163 | `NO-HYP` (fold candidate — extends `HYP-P13`'s "geometry is the signal" row) | fpocket beats floor and CTQW on 2/3 mandatory targets. Same cluster as TASK-0132/0200. |
| TASK-0164 | `ENG` | Config-resolution logistics; "0 of 6 resolvable." |
| TASK-0165 | `ENG` | Spatial-block bootstrap CI methodology. |
| TASK-0166 | `NO-HYP` (fold candidate — extends `HYP-P14`'s observable family) | GNM low-mode entropy: zero significant signal, correlates with the proximity confound. |
| TASK-0167 | **`NO-HYP` — merges into pilot draft P2** | Parent's own headline (no target reaches 80% detection power) — same finding as TASK-0167.002. |
| TASK-0167.001 | `ENG` | Builds `allostery.plant` machinery. Tool construction. |
| TASK-0167.003 | `NO-HYP` (fold candidate — extends pilot draft P2 as a methodology footnote) | Compact-null geometric mismatch: real pockets sit at 97th-100th percentile of the null's own draw distribution; structurally unreachable for 2 targets. |
| TASK-0168 | `NO-HYP` (fold candidate — extends `HYP-P14`'s observable family) | Mechanism-discriminating plant: channel family replicates, ensemble family doesn't generalize. |
| TASK-0169 | `ENG` | Pure documentation consolidation. |
| TASK-0170 | `NO-HYP` (fold candidate — extends `HYP-P8`) | Literature-curated PTP1B ground truth sharpens the negative (2/3 observables score *below* floor). |
| TASK-0171 | `NO-HYP` (fold candidate — extends `HYP-P13`, directly relevant to TASK-0312's symmetry proof) | Holo-native rerun: real, large apo-vs-holo gap; caveat (from TASK-0312) that this must not be read as directionality evidence. |
| TASK-0172 | `ENG` | Spectrum-preserving Hamiltonian reduction. Algorithmic infra. |
| TASK-0176 | `ENG` | (TODO) Coordinator/planning file, no Done section. |
| TASK-0177 | `ENG` | Consensus holo-pocket label construction. Benchmark curation. |
| TASK-0180 | `ENG` | Site-level clustering + end-to-end runner. |
| TASK-0181 | *(already captured in `search_complexity.md`'s closed-routes table)* | Selection-as-QUBO Phase A: 0/3 strict wins. |
| TASK-0182 | *(already contextually captured near H10/H11)* | Hardware resource accounting: all 4 targets `FAULT_TOLERANT_ONLY`. |
| TASK-0183 | `ENG` | Phase-2 sprint plan; "no computation." |
| TASK-0184 | `ENG` | (TODO) Phase-1 submission-writing task. |
| TASK-0185 | *(already captured in `search_complexity.md`'s closed-routes table)* | Backbone-layer pocket opening not rare (1-8 draws/hit). |
| TASK-0186 | `NO-HYP` (fold candidate — extends `HYP-P8`) | Hop-distance generalization audit: min hop=1 on 6/7 targets, wide variance. |
| TASK-0187 | `NO-HYP` (fold candidate — same cluster as TASK-0015, extends `HYP-P8`) | ENM-induced shortcut hypothesis FAILS on PTP1B specificity test. Consolidate with TASK-0015 (same "apo perturbation doesn't create a shortcut" theme). |
| TASK-0189 | `ENG` | Bonferroni-family bug fix in a collection script. |
| TASK-0190 | `NO-HYP` (fold candidate — extends pilot draft P2, paired with TASK-0167.003) | Real-pocket-Rg-matched null: `dcc_low` still fails; compact null structurally can't reach real pocket Rg for 2/3 targets. |
| TASK-0191 | `ENG` | `RESULTS.md` synthesis repair; "no scientific number re-derived." |
| TASK-0192 | `ENG` | Propagates a known genotype-mismatch finding into documents. |
| TASK-0193 | `ENG` | Fixes stale narrative in `COMPETENCE_MAP.md`. |
| TASK-0194 | `ENG` | `ARCHITECTURE.md` change-log catch-up. |
| TASK-0195 | `ENG` | Concurrent-write protection tooling. |
| TASK-0196 | `ENG` | `pytest_local.py` `--file` selector. |
| TASK-0198 | `ENG` | Duplicate-tracked-file guard. |
| TASK-0199 | `HYP-P13` | "28 observables collapse to effective rank ~3" — cited verbatim in HYP-P13's own table. |
| TASK-0200 | `NO-HYP` (fold candidate — extends `HYP-P13`'s "geometry is the signal" row) | Dynamics is a strict, asymmetric subset of static cavity geometry. Same cluster as TASK-0132/0163. |
| TASK-0201 | `HYP-S6` | Cited directly inside HYP-S6's own "predictive half" discussion. |
| TASK-0202 | `ENG` | Merge/rebase-conflict protocol adoption. |
| TASK-0203 | `NO-HYP` (fold candidate — extends `HYP-S6`) | PTP1B "mechanism triangle": rules out the ensemble/mode reading of the register's one positive. |
| TASK-0204 | `HYP-S1` | This task IS the deciding measurement for HYP-S1's own claim. |
| TASK-0205 | `ENG` | Documentation refresh; "re-deriving no number." |
| TASK-0207 | `NO-HYP` (fold candidate — extends `HYP-P14`) | PCA axis labeling: PC1 is the proximity-confound axis. |
| TASK-0208 | `HYP-S2`, `HYP-S3`, `HYP-S4`, `HYP-S5`, `HYP-S6` | Directly cited deciding multiple HYP-S sections. |
| TASK-0209 | `HYP-P13` | Cited directly within HYP-P13's own text; the "VALID" gate reused throughout `reference_register.md`. |
| TASK-0210 | `HYP-S1` | Named as "Owner" of HYP-S1's own open question. |
| TASK-0211 | `NO-HYP` (fold candidate — extends `HYP-P14`) | Ensemble contact-covariance observable is not a 4th independent axis. |
| TASK-0212 | `ENG` | Invalidated as filed before measurement ran; zero science performed. |
| TASK-0213 | `HYP-P13` | Cited within HYP-P13's own text twice. |
| TASK-0214 | *(documented in ledger only; process/data-curation finding)* | Apo re-selection (Leg A) recovers 0/5 INVALID targets — the blocking half is the holo side. |
| TASK-0216 | **`NO-HYP` (new — see "Flag" section above, also candidate correction to `search_complexity.md`)** | Seed-provenance audit: PTP1B's `dcc_low` positive collapses under the real seed (AUC 1.000→0.598). |
| TASK-0217 | **`NO-HYP` (new — same as TASK-0216, parent synthesis)** | "The register's honest surviving-positive count is zero, not one." |
| TASK-0217.001 | `ENG` | Fixes a real array-correspondence bug (10/13 targets). |
| TASK-0217.002 | `ENG` | Criterion-reachability + positive-control audit. |

### Full sweep — batch 5/6 (TASK-0217.003–0267)

| task | class | evidence / reasoning |
|---|---|---|
| TASK-0217.003 | `ENG` | Provenance/seed-fallback bug fix (PTP1B). |
| TASK-0217.004 | `ENG` | Metric-construct audit; finds `backbone_explained` confound. |
| TASK-0218 | `ENG` | Wires the leak detector into the real pipeline. |
| TASK-0219 | `ENG` | Fixes a GLUCOKINASE chain-letter config bug. |
| TASK-0221 | `ENG` | Organizer-communication/admin task. |
| TASK-0222 | `ENG` | Runs both mandated/substituted Cardiac Myosin pairs for compliance. |
| TASK-0223 | `ENG` | Stale-restage bug fix. |
| TASK-0224 | `ENG` | Writes `WORKFLOW.md`. |
| TASK-0225 | `ENG` | Regenerates §5 deliverables; fixes a missing-floor bug. |
| TASK-0226 | `H4.1`, `H4.2`, `H7`, `H8.1`/`H8.2`, `H16.2` | Explicitly cited in `reference_register.md` deciding all five rows. |
| TASK-0227 | `NO-HYP` (fold candidate — same cluster as TASK-0228/0230/0234/0235) | ANM-subspace reachability of apo→holo motion. |
| TASK-0228 | `NO-HYP` (fold candidate — same cluster) | Pocket-restricted static/adaptive ANM overlap. |
| TASK-0229.001 | `H9` | Cited deciding H9's PARTIAL status. |
| TASK-0229.002 | `H10`, `H11` | Cited deciding H10/H11 TESTED status. |
| TASK-0229.003 | `H6.2` | Cited deciding H6.2. |
| TASK-0229.004 | `H1` | Cited deciding H1 TESTED. |
| TASK-0229.005 | `H2.2` | Cited deciding H2.2. |
| TASK-0229.006 | `H4.1` (partial) | Cited (with TASK-0226) deciding H4.1. |
| TASK-0229.007 | `H7`, `H15.1`/`H15.2` | Cited deciding H7(b) and H15.1/H15.2. |
| TASK-0230 | `NO-HYP` (fold candidate — same cluster as TASK-0227/0228) | ANM-projected reachability ceiling + scorer-brittleness control. |
| TASK-0232 | `ENG` | Registry-hygiene: files 3 missing seam records. |
| TASK-0233 | `HYP-P13` | Cited directly deciding HYP-P13's premise-plausibility fragment. |
| TASK-0234 | `NO-HYP` (fold candidate — same cluster) | Names then retires a quantum-Gibbs-sampling proposal (collective layer not rare, no mixing bottleneck). |
| TASK-0235 | `NO-HYP` (fold candidate — same cluster) | Local-Kabsch backbone placement flips BCR_ABL1's ceiling. |
| TASK-0236 | `ENG` | DOI-verifies two mechanism citations. |
| TASK-0237 | `ENG` | Assesses a collaborator Hamiltonian cell via an existing finding. |
| TASK-0238 | `ENG` | Independent HIV1_RT run + null/floor strictness characterization. |
| TASK-0239 | `ENG` | Refreshes stale citations across 5 documents. |
| TASK-0241 | `ENG` | QA audit debunking TASK-0235's "decisive" claim (was n=1 not n=4). |
| TASK-0243 | `NO-HYP` (fold candidate — same cluster as 0244/0245/0246/0249/0254/0255/0257/0259/0263/0266) | Curated 22-pair re-run: CTQW's "leads every control" reverses vs. fpocket_drug. |
| TASK-0244 | `NO-HYP` (fold candidate — same cluster) | Operator's advantage fully consistent with pure proximity-to-seed. |
| TASK-0245 | `NO-HYP` (fold candidate — same cluster) | Cross-validated variance attribution: CTQW median +1%, unexplained 67%. |
| TASK-0246 | `NO-HYP` (fold candidate — same cluster) | Hop is the strongest single baseline on 5/9 targets. |
| TASK-0247 | `HYP-P13` | Cited directly in HYP-P13's own supporting-evidence table. |
| TASK-0248 | `ENG` | Reconciles `reference_register.md` STATUS fields. |
| TASK-0249 | `NO-HYP` (fold candidate — same cluster) | Composite classical baseline decisively beats CTQW. |
| TASK-0251 | `H5.1`/`H5.2` | Cited deciding H5.1/H5.2. |
| TASK-0252 | `H6.1`, `H4.3`, `H4.4` | Cited deciding all three. |
| TASK-0253 | `ENG` | Audits TASK-0243's frozen set; fixes a silent-NaN bug. |
| TASK-0254 | `NO-HYP` (fold candidate — same cluster) | fpocket in the variance stack (unexplained 67%→29%); 45% already open in apo. |
| TASK-0255 | `NO-HYP` (fold candidate — same cluster) | MIN_HOP calibration: hop-2 candidates as close as 2.09 Å. |
| TASK-0256 | `ENG` | Classical-diffusion-parity arm; test not achievable on real data. |
| TASK-0257 | `NO-HYP` (fold candidate — same cluster) | Two ENM-improvement rungs don't fix FAIL targets. |
| TASK-0259 | `NO-HYP` (fold candidate — same cluster) | ENM-validity subgroup test fails in the reverse direction. |
| TASK-0261 | `ENG` | Corrects pseudo-replication (20 rows/13 structures); re-derives p-values. |
| TASK-0262 | `ENG` | Rejects adopting a proposed allosteric-site taxonomy. |
| TASK-0263 | `NO-HYP` (fold candidate — same cluster) | H_new's own potential terms beat CTQW itself (0.751 vs 0.575). |
| TASK-0264 | `NO-HYP` (new — directly answers `HYP-S1`'s own open question; recommend as a dated update to HYP-S1, not a new id) | Treewidth of coupled backbone+rotamer cryptic-opening instances stays modest (median 5-6). |
| TASK-0265 | `NO-HYP` (new candidate) | Pocket labels cannot express ligand-dependent allostery (Jaccard 0.4-1.0); BCR-ABL1 mechanism ligand-chemotype-agnostic. Distinct construct-validity claim, no clean existing home. |
| TASK-0266 | `NO-HYP` (fold candidate — same cluster) | SASA burial control roughly halves CTQW's already-non-significant cryptic lean. |
| TASK-0267 | `ENG` | Decision-only: declines a further null given TASK-0266's negative. |

### Full sweep — batch 6/6 (TASK-0268–0325)

| task | class | evidence / reasoning |
|---|---|---|
| TASK-0268 | `HYP-P13` | Pre-registered frustration test; decisive negative. Cited by name in `physics.md`. |
| TASK-0270 | `ENG` | Organiser-sanctioned structure substitutions (fixes TASK-0155's genotype defect). |
| TASK-0271 | `HYP-P13` | Filed/run explicitly as a HYP-P13 test by an independent route. Cited in `physics.md`. |
| TASK-0272 | `ENG` | Propagates the KRAS genotype swap into stale documents. |
| TASK-0273 | `NO-HYP` (new candidate) | Crystallographic label noise real but NOT the cause of the unexplained residual. |
| TASK-0274 | `NO-HYP` (new candidate) | Conservation and residue-chemistry blocks: both null. |
| TASK-0275 | `NO-HYP` (fold candidate — same cluster as TASK-0277) | V_C dominates H_new's potential terms; CTQW's added-last marginal over V_C n.s. in apo. |
| TASK-0276 | `NO-HYP` (fold candidate — same cluster as TASK-0279/0281) | Real holo-side V_C signature separates allosteric from orthosteric sites. |
| TASK-0277 | `NO-HYP` (fold candidate — same cluster as TASK-0275) | 8 more features swept apo vs holo; uniformly near-zero ceiling gap. |
| TASK-0279 | `NO-HYP` (fold candidate — same cluster as TASK-0276/0281) | BCR-ABL1 inert-vs-efficacious pair: V_C higher on the *inert* pocket. |
| TASK-0280 | `H6.2` | Directly tested/updated `reference_register.md`'s H6.2 row. |
| TASK-0281 | `NO-HYP` (fold candidate — same cluster as TASK-0276/0279) | Pre-registered "capacity to couple" rescue hypothesis DIES on independent data. |
| TASK-0282 | `ENG` | Pocket-level selection-rule sweep; cited only as pseudo-replication background. |
| TASK-0283 | `ENG` | Traces a P@5 discrepancy to a stale deliverable directory. |
| TASK-0284 | `HYP-P14` | Finding B is a named row in HYP-P14's own evidence table. |
| TASK-0285 | `ENG` | Dockerizes fpocket/EvoEF2/P2Rank/PocketMiner images. |
| TASK-0286 | `ENG` | Three domain-parser attempts, all fail sanity check — no result. |
| TASK-0288 | `NO-HYP` (fold candidate — same cluster as TASK-0291/0304, "Finding F") | ~32% of "allosteric" pockets are covalently/peptide-bond adjacent to the active site. |
| TASK-0289 | `ENG` | Defect record: active-site detection non-determinism. |
| TASK-0290 | `ENG` | Fixes the TASK-0289 defect; recomputes 33 targets, 0/33 moved. |
| TASK-0291 | `NO-HYP` (fold candidate — same cluster, "Finding F") | fpocket's "multi-pocket" output mostly a clustering artifact. |
| TASK-0292 | `ENG` | Diagnoses why druggability-based selection underperforms. |
| TASK-0293 | `ENG` | LOTO-validates the `druggability/size` rule; FAILS. |
| TASK-0294 | `ENG` | Read-only audit of 44 `except Exception` sites. |
| TASK-0295 | `ENG` | Data-integrity audit; no exposure found. |
| TASK-0297 | `ENG` | Fixes a chain-agnostic residue-matching bug; corrects Finding F's count. |
| TASK-0298 | `ENG` | Fixes the chain-agnostic fpocket-parsing bug across 11 sites. |
| TASK-0299 | `ENG` | Forensic reassessment: "CTQW beats classical ceiling" is a pseudo-replication artifact. |
| TASK-0300 | `ENG` | Diagnoses pseudo-replication in the rule-selection criterion itself. |
| TASK-0301 | `ENG` | Two parameter-free meta-selectors both fail. |
| TASK-0302 | `HYP-P14` | Named row ("sibling persistence") in HYP-P14's evidence table. |
| TASK-0303 | `HYP-P14` | Named row (ENM mode-shift doesn't reproduce) in HYP-P14's evidence table. |
| TASK-0304 | `NO-HYP` (fold candidate — same cluster, "Finding F") | Independently reproduces Finding F on ASBench/CASBench (422/145 structures). |
| TASK-0306 | `HYP-P14` | Extensively/directly cited in HYP-P14's "Secondary route" paragraph. |
| TASK-0307 | `ENG` | Verify-only submission-claims audit. |
| TASK-0309 | `NO-HYP` (fold candidate — same cluster as TASK-0311/0316) | Site-distance modality battery: low-mean component is Finding F's point mass. |
| TASK-0310 | `HYP-P9` | Directly and explicitly closes HYP-P9 in `physics.md`. |
| TASK-0311 | `NO-HYP` (fold candidate — same cluster) | Regression reframing: floor/continuum split predictable, continuum mostly not. |
| TASK-0312 | `HYP-P13` | Proves the CTQW kernel is exactly symmetric. Cited as a 2026-09-03 addendum inside HYP-P13. |
| TASK-0313 | `HYP-P14` | Verifies Silverman's implementation/power. Cited/quoted as the basis for a HYP-P14 bullet's withdrawal. |
| TASK-0314 | `ENG` | Reconciles AUC-vs-P@5 metric confusion + multiplicity audit. |
| TASK-0316 | `NO-HYP` (fold candidate — same cluster as TASK-0309/0311; **retracted, see status**) | "Multimodal in every cohort" — retracted 2026-09-02 by TASK-0319's bug fix. |
| TASK-0317 | `NO-HYP` (new candidate) | Three applicability descriptors don't predict which of six detection measures fires. |
| TASK-0318 | `NO-HYP` (new candidate) | Existing contact-graph+seed feature span reaches a ~0.60 residual ranking ceiling. |
| TASK-0319 | `ENG` | Finds/fixes a `random_state` re-seeding bug in the modality LRT. |
| TASK-0320 | `HYP-P9` | Cited alongside TASK-0310 in HYP-P9's "CLOSED" status line. |
| TASK-0321 | `ENG` | Decision brief on register consultation rates — the task that spawned this whole sweep. |
| TASK-0322 | `ENG` | Builds the register status index + staleness/uncited-claim checker. |
| TASK-0323 | `ENG` | Audits Done tasks for unwritten verdicts. |
| TASK-0325 | `NO-HYP` (new candidate) | Predictor-consensus gate does the pocket-selection work; CTQW adds nothing within-gate. |
| TASK-0327 | `HYP-P18` | **Landed directly** (2026-09-06, per the repo owner's own reminder to check for missing hypotheses before Critic review) — PASSer (external, actively-maintained SOTA pocket ranker) decisively beats both chance and this project's own veto pipeline on leakage-correct held-out data; extends HYP-P18's "does the field's own SOTA also fail here" question with an opposite-flavoured answer for a different tool. See HYP-P18's own 2026-09-06 addendum for the full caveat (Oussema/Reviewer-thread cross-check still pending). |
| TASK-0328 | `ENG` | pocketsweep.py seed/null-shape fixes; explicitly self-checked against this same reminder and correctly found no new hypothesis needed (reuses TASK-0158/190/201's existing compactness-null principle). |
| TASK-0331 | `NO-HYP` (fold candidate — extends HYP-P14) | Distal-only ASBench subset (n=45) cannot detect proximity, its own dominant confound (p=0.89 vs. full-cohort p=0.00035) — the CTQW result there is UNDETERMINED for lack of power, not a sharper negative. Not landed (incremental caveat on an already-well-evidenced claim, not a new mechanism). |
| TASK-0333 | `ENG` | Reproducibility artifact pack (container, pinned env, seeding convention, structured logs) — pure packaging, no scientific claim. |
| TASK-0334 | `HYP-P25` (new) | **Landed directly** (2026-09-06) — the veto pipeline's below-chance pocket pick (TASK-0327) is a measured proximity-anticorrelation (Spearman rho −0.40 to −0.61, all p<0.002, n=44-96) with the truth pocket's own distance from the active site, not an unexplained "subtracts value" defect; PASSer (non-distance-based) shows no such correlation (specificity control clears, all p>0.17). Genuinely distinct mechanism from HYP-P9 (reverse-seeded/gated construction) — cross-referenced, not merged. |
| TASK-0336 | `HYP-P13` | **Folded, not new** (2026-09-06) — the 1022-protein full run's headline classical comparison (CTQW beats every descriptor 69 vs ≤25, distal 19 vs 1) was a max-over-221/884-cells statistic scored against a single fixed classical ranking, on two different candidate pocket sets and two different truth definitions. Matched (one candidate set = round 2's own stored pockets, one truth definition, one pre-registered CTQW cell, TASK-0328's own pocket-block null applied to every arm): CTQW clears 4/276 families (0/48 distal) — fewer than 3 of 5 plain classical descriptors (5/276 each); the distal margin is exactly 0 for every arm after matching. Same claim as HYP-P13's existing "fpocket beats every observable" row, now shown on the one dataset that looked like an exception. |

## Disposition — applying the standing rule to every `NO-HYP` draft

Grouped by claim cluster, not one row per task (this task's own
Constraint). **Recommendation only — not applied.** "Fold" means a
dated status update inside the named existing hypothesis's own
section, citing the new task(s); "New" means a fresh `## HYP-Pxx`/
`## HYP-Sxx` entry; "Ceiling.md" means the finding belongs in that
file's own narrative style (it already hosts un-schemed status
updates, e.g. TASK-0046/TASK-0110); "Already captured" means no
action — an existing framing table already names the task.

| # | claim cluster | source tasks | recommended disposition |
|---|---|---|---|
| 1 | dcc_low/transport generalization | 0151, 0145, 0149, 0168(partial) | **New** (pilot-approved) |
| 2 | Detection power / LOD of the pipeline itself | 0167.002, 0167, 0167.001(infra only), 0167.003, 0190 | **New** (pilot-approved), fold 0167.003/0190's compact-null-geometry finding in as an extension paragraph |
| 3 | External SOTA predictors don't close the residual | 0260, 0269 | **New** (pilot-approved) |
| 4 | Occupancy ≠ allosteric effect (BCR-ABL1 MYR) | 0278 | **Fold → HYP-P13** (Architect-directed) |
| 5 | ASBench enrichment-vs-retrieval reframing | 0305 | **New** (pilot-approved) |
| 6 | Apo-only perturbation/sampling never creates a pocket shortcut | 0015, 0187 | **Fold → HYP-P8** (dynamical extension of the same "apo lacks the signal" claim; consolidate both tasks into one dated update) |
| 7 | Ceiling can fall below floor even fully optimized; ceiling headroom is often winner's-curse noise | 0046, 0131 | **Ceiling.md** — already recorded there in full for 0046; add 0131 alongside it as the same document's own follow-up, no `HYP-<id>` needed |
| 8 | Classical/geometric baselines beat CTQW; dynamics adds nothing beyond static cavity geometry | 0132, 0163, 0200 | **Fold → HYP-P13**'s existing "fpocket beats every observable" evidence row — extend it to cite all three |
| 9 | Seed/clock gauge fixes eliminate the pipeline's surviving positives | 0118, 0129, 0130 | **Ceiling.md or HYP-P6/HYP-P8** — mixed-mechanism cluster (clock is HYP-P6's own subject, already cited there via 0109/0110/0119; seed-cardinality is closer to HYP-P8). Recommend splitting: 0118/0129 → fold into HYP-P8 (seed-driven collapse of the one surviving positive), 0130 → already effectively HYP-P6 territory (closed-form propagator), add as a footnote there. |
| 10 | H_new's own potential-term decomposition (V_C dominance, no apo→holo ceiling gain) | 0121(non-decisive, documented only), 0275, 0277 | **Fold → HYP-P2/HYP-P3** as explicit "still untested, but see this adjacent decomposition" context, OR **New** minor hypothesis specifically about V_C's dominance — leaning New given HYP-P2/P3 explicitly disclaim deciding this |
| 11 | mode_coparticipation / distance-stratified AUC / PCA-axis-is-proximity / ensemble-covariance-not-independent — register-wide observable-family negatives | 0122, 0123, 0166, 0168, 0203, 0207, 0211 | **Fold → HYP-P14**'s own observable-family evidence table — extend the existing list (currently 0140/0141/0145/0146/0147/0148/0157/0284/0302/0303/0306) with these 7 |
| 12 | Generalization-set corroboration of the proximity confound | 0081, 0127, 0170, 0186 | **Fold → HYP-P8** as additional corroborating targets |
| 13 | Percolation/redundant (non-bottleneck) apo connectivity | 0136 | **New** — genuinely distinct topological claim |
| 14 | Reachability of collective apo→holo motion; retired quantum-Gibbs-sampling proposal | 0227, 0228, 0230, 0234, 0235 | **New**, one hypothesis covering the cluster (physics.md style) |
| 15 | The CTQW/H_new operator's own potential terms + fpocket + burial together saturate near the register's real ceiling; CTQW itself adds nothing beyond them | 0243, 0244, 0245, 0246, 0249, 0254, 0255, 0257, 0259, 0263, 0266 | **Fold → HYP-P14** as a major dated update — this cluster is, on inspection, essentially HYP-P14's own core claim reached via an independent, earlier (2026-08-24/25) measurement lineage. **Flag for Architect**: HYP-P14 (filed 2026-09-01) does not currently cite any of these 11 tasks despite making the same claim — worth checking whether HYP-P14's own text should absorb this evidence directly. |
| 16 | Treewidth of the coupled backbone+rotamer cryptic-opening search stays modest | 0264 | **Fold → HYP-S1** as a dated status update (directly answers HYP-S1's own named open question; its status line hasn't reflected this since 2026-08-12) |
| 17 | Pocket labels can't express ligand-dependent allostery; BCR-ABL1 mechanism is ligand-agnostic | 0265 | **New** — distinct construct-validity claim |
| 18 | Finding F: covalent/peptide-bond-adjacency confound in distal-allostery benchmarks | 0288, 0291, 0304 | **New** — the strongest external-validity result in the sweep, deserves its own prominent entry, not a footnote anywhere |
| 19 | Modality/population structure of site-distance is undetermined; floor/continuum regression split | 0309, 0311, 0316(retracted, see below) | **New**, with 0316's own retraction (by 0319) stated explicitly in the same entry so a future reader doesn't cite the retracted headline |
| 20 | Discriminator B: per-measure applicability descriptors don't predict which measure fires | 0317 | **New** |
| 21 | Existing feature span already reaches a ~0.60 residual ceiling | 0318 | **New**, but flag thematic overlap with cluster #15/HYP-P14 for the Architect — same "headroom is bounded and already-explained" theme from yet another angle |
| 22 | Reverse-seeded CTQW: the predictor gate does the work, not the walk | 0325 | **New** |
| 23 | The register's one surviving positive is a seed-construction artifact | 0216, 0217 | **New, urgent — see "Flag" section above.** This is a correction to `search_complexity.md`'s own live prose, not just a missing citation. |
| 24 | V_C separates allosteric from orthosteric sites but tracks occupancy/capacity, not efficacy | 0276, 0279, 0281 | **New** |
| 25 | Crystallographic label noise is real but not AUC-limiting | 0273 | **New** (or fold into cluster #18/Finding-F as a related benchmark-validity note — either defensible) |
| 26 | Conservation/residue-chemistry contribute no signal | 0274 | **New** (minor) — or fold into cluster #15/HYP-P14's feature-sweep evidence |

**Not itemized above** (already resolved without a landing decision):
TASK-0091/0092 (superseded by TASK-0102), TASK-0155 (superseded by
TASK-0270), TASK-0156/0181/0182/0185 (already captured in existing
framing tables), TASK-0214 (process/data-curation, not really a
hypothesis).

## Landing applied (2026-09-04, after "resume please")

The disposition table above was applied in full:

- **`physics.md`**: `HYP-P8` extended (6 fold-ins: TASK-0094, TASK-0015/
  TASK-0187, TASK-0118/TASK-0129, TASK-0081/TASK-0127/TASK-0170/
  TASK-0186); `HYP-P9` extended (TASK-0325 folded in as a continuation
  of the already-cited TASK-0320); `HYP-P13` extended (TASK-0278 per
  the Architect's own directive, plus TASK-0132/TASK-0163/TASK-0200
  added to the "fpocket beats every observable" evidence row); `HYP-P14`
  substantially extended (5 new evidence-table rows, the observable-
  family list widened by 3, and a major new status-update block folding
  in the whole TASK-0243–TASK-0266 arc plus TASK-0318 — the independent,
  earlier-dated measurement lineage the disposition table flagged as
  converging on HYP-P14's own claim). Ten new hypotheses landed:
  `HYP-P15` through `HYP-P24` (clusters 1, 2, 3, 5, 13, 17, 18, 19, 20,
  22, 23, 24 from the disposition table above — several were merged
  together where the same task cluster decided more than one, so 10
  entries cover more than 10 source clusters).
- **`search_complexity.md`**: `HYP-S1` extended (TASK-0264, a second
  independent structural answer to its own long-open question);
  the "Correction, 2026-09-04" block added near the file's own top,
  striking through the "one surviving positive" claim per the urgent
  flag above and replacing it with TASK-0216/TASK-0217's finding, with
  a cross-reference note added inside `HYP-S6`'s own text; the
  `HYP-P13` cross-reference section extended with the TASK-0227/0228/
  0230/0234/0235 cluster, closing the section's own previously-open
  "measurable via TASK-0228 §6.2" question directly rather than minting
  a new id (cluster 14 from the disposition table, landed as a
  fold-in once the exact fit was found, not a new `HYP-S8`).
- No new `reference_register.md` rows — nothing in the disposition
  table fit that scheme (it is specifically for hypotheses drawn from
  the challenge's own bibliography).
- `.claude/hypotheses/INDEX.md` regenerated; `hyp_register_check.py`
  re-run clean (no crash, 18/18 tests still pass; remaining staleness
  findings are citations from meta/process tasks about the register
  itself — TASK-0321/0322/0323/0326 — not new scientific findings, a
  known limitation of the staleness heuristic's self-citation blind
  spot, not chased further here).

**Not landed as new/fold-in content** (per the disposition table's own
"documented in ledger only" / "already captured" / "superseded"
entries): TASK-0046/TASK-0131 (already in `ceiling.md`'s own prose);
TASK-0067/TASK-0121 (explicitly non-decisive per the file's own
existing text); TASK-0091/TASK-0092 (superseded by TASK-0102);
TASK-0155 (superseded by TASK-0270); TASK-0156/TASK-0181/TASK-0182/
TASK-0185 (already in existing framing tables); TASK-0214 (process/
data-curation, not a hypothesis).

## Follow-up landing, 2026-09-06 — TASK-0327 (post-sweep, not in the original 344)

Four tasks postdate this sweep (TASK-0327, 0328, 0331, 0333 — added to
the main classification table above). Per the repo owner's own explicit
reminder to check for missing hypotheses/references before Critic
review, TASK-0327's finding (PASSer, an external SOTA pocket ranker,
decisively beats this project's own veto pipeline on leakage-correct
held-out data) was landed directly as a dated addendum inside
**`HYP-P18`** (extends, not a new id — same "does the field's own SOTA
also fail here" question HYP-P18 already asks, answered oppositely for
a different tool; see that hypothesis's own text for the full citation
list and the explicit caveat that Oussema/Reviewer-thread's own
cross-check of TASK-0327's numbers is still outstanding). TASK-0331's
smaller finding (the ASBench distal-only subset cannot detect its own
proximity confound, so CTQW there is underpowered rather than negative)
was left ledger-tracked only, not landed — an incremental caveat on an
already-extensively-evidenced claim, not a new mechanism, per the
standing rule. TASK-0328/0333 are process/engineering, no register
change. No missing or unclear paper references were found in any of
the four — TASK-0327's own PASSer citations (Xiao/Tian/Tao, 2 papers +
1 preprint-published pair) were already live-verified against the
publisher/PMC before that task's own Done section was written, and
HYP-P11's existing ENAQT citations (Mohseni/Rebentrost/Caruso/Viciani)
were already in place, checked, not found missing.

## Follow-up landing, 2026-09-06 — TASK-0334

Filed by Reviewer thread as a direct follow-up to TASK-0327: turn the
below-chance pipeline result into a tested mechanism rather than leaving
it as an unexplained negative. Read-only join of TASK-0327's own stored
artifacts against `allosteric/datasets/pocket_distance.csv` (vendored;
verified byte-identical to TASK-0331's source commit). Result: the
pipeline's per-protein hit rate on the truth pocket anti-correlates with
that pocket's own distance from the active site (Spearman rho −0.40 to
−0.61, all 8 combinations tested p<0.002, power checked and cleared at
n=44-96), while PASSer — the non-distance-based external baseline —
shows no such correlation (all p>0.17), ruling out "distal proteins are
just universally harder" as the explanation. Landed as a new hypothesis,
**`HYP-P25`**, per the standing rule: this is a genuinely different
mechanism from HYP-P9's "predictor gate does the discriminating work"
finding (a different construction, reverse-seeded and gated; HYP-P25's
pipeline is the forward, gate-independent CTQW score) — cross-referenced
in both directions, not folded together. One Outcome item from the
filing (distance from active site to the pipeline's actual wrong pick,
on a miss) could not be measured — `pocket_distance.csv` only carries
(active site, truth pocket) distances, not per-candidate-pocket
geometry, and getting the latter needs a PDB refetch the task's own
Constraints ruled out; stated as an open limitation in HYP-P25's own
text, not smoothed over. `INDEX.md` regenerated after this landing.
