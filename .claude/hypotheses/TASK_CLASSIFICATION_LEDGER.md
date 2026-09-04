# Task classification ledger — TASK-0326

**Status: PILOT ONLY (39/345 tasks).** Do not treat as complete or
authoritative. Per TASK-0326's own Planned Validation, this pilot's
bucket distribution and 7 spot-checked classifications (5 required +
2 extra, after one reclassification on close read — see below) are
reported here for Architect sign-off **before** the full ~306-task
sweep runs. No hypothesis file has been edited from this pass — all
`NO-HYP` drafts below are proposed, not landed, matching [[TASK-0323]]'s
own precedent of not self-authorizing new register content.

## How the pilot was sampled

Stratified, not cherry-picked: every 9th task file from the full,
numerically-sorted list of all 345 `.ai/tasks/{TODO,IN_PROGRESS,DONE}/
TASK-*.md` files (`NR%9==1`) → 39 tasks, spanning TASK-0001 through
TASK-0324, all three status directories represented in roughly their
real proportion (35 DONE, 1 IN_PROGRESS, 1 TODO — TASK-0026 — matching
the corpus's own ~92% DONE share).

## Bucket distribution (pilot, n=39)

| bucket | count | share |
|---|---|---|
| `ENG` | 27 | 69% |
| `HYP-<id>` | 6 | 15% |
| `NO-HYP` | 6 (5 draft groups — TASK-0260/TASK-0269 share one claim) | 15% |
| `UNCLASSIFIED` | 0 | 0% |

Not systematically miscalibrated on this read: `ENG` is large but not
total (real science is not being silently absorbed — 12 of 39 tasks
carry a genuine tested claim), and `UNCLASSIFIED` is empty because every
task's Done section (or equivalent — two used `## Findings`/`## Result`
instead, see Method) was specific enough to decide, not because
ambiguous cases were forced into a confident-looking bucket without
reading them (see the TASK-0278 reclassification below — a real
ambiguous case was caught, not smoothed over).

## Method

Extracted title + `- Status:` line + `## Why this exists` (or
equivalent) + first ~1200 chars of the Done section (or equivalent
heading — two pilot tasks, TASK-0287 and TASK-0305, use `## Findings`/
`## Result` instead of `## Done`; found and read directly, not silently
skipped) for all 39 in one pass. `HYP-<id>` candidates were confirmed
by grepping the task id against `physics.md`/`search_complexity.md`/
`reference_register.md`/`ceiling.md` directly — a citation hit was
verified in context (which `## HYP-Pn` section it falls inside), not
assumed from the grep alone, since a task can be cited under a
hypothesis for unrelated methodology reuse rather than for deciding
that hypothesis's own claim (see TASK-0260 below).

**Planned Validation (5 required, 7 run)**: read the full file for
TASK-0057, TASK-0206 (`ENG`), TASK-0133 (`HYP-P8`), TASK-0278 (`NO-HYP`
after reclassification), TASK-0305 (`NO-HYP`) — the required 5, mixed
across 3 of the 4 buckets (`UNCLASSIFIED` has no pilot members to
check) — then two more (TASK-0220, TASK-0188, both `ENG`) after the
TASK-0278 reclassification below, to widen the check rather than trust
the remaining excerpt-only calls uncritically.

**One real reclassification, from the spot-check itself**: TASK-0278
was first read (from its ~1200-char excerpt: "Written up as a dated
addendum to TASK-0209's own file") as a linking extension of TASK-0209,
already cited under `HYP-P13`. The full file shows a materially larger,
standalone claim — a decisive MYR-computational-stripping control
proving the confound is structural (backbone conformation) not
removable by deleting a ligand's atoms, plus a register-wide
pocket-window-overlap classification rule that found a **worse**,
previously unflagged instance (PKR_MITAPIVAT/PKR_AG946's `7FS3`,
91–92% overlap). Reclassified `HYP-P13` → `NO-HYP` (own draft below).
Kept as a direct demonstration that excerpt-only classification is not
reliable enough for the full sweep without spot-checking — exactly
what this task's own Planned Validation step exists to catch before
scaling up.

## Ledger

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
| TASK-0106 | **`HYP-P6`** | CTQW-trapping reproduction across `H10`/`H2`/`H_new` at scaled λ. Cited in `physics.md` L252-366, inside the `HYP-P6` section (propagation-time principledness). |
| TASK-0115 | `ENG` | Names the "repeated-exposure" risk, places it in `INVARIANCE_PROTOCOL.md`. Process/methodology rule, not a physics claim. |
| TASK-0124 | `ENG` | Re-anchors CARDIAC_MYOSIN's holo structure (8QYP vs a relayed 9GZ1 lead). Data-curation decision. |
| TASK-0133 | **`HYP-P8`** | Random-patch control for the learnability gate's CO(20) half — finds KRAS_G12C's corrected pocket-restricted CO would flip its verdict to `UNLEARNABLE_FROM_APO`. Cited in `physics.md` L512, inside `HYP-P8` (apo graph does not contain the signal). **Spot-checked in full — confirmed, richer than the excerpt showed.** |
| TASK-0142 | **`HYP-P12`, `H2.1`** | H2/L1 half of the quantum-Betti bridge — title names `HYP-P12` directly; H2 half is also `reference_register.md`'s own `H2.1` row (same finding, other namespace). Both already correctly cited. |
| TASK-0151 | **`NO-HYP`** (draft 1) | `dcc_low`'s CARDIAC_MYOSIN positive generalizes cleanly to PTP1B; the transport observable's BCR_ABL1 positive does not generalize to PTP1B or CASPASE7. Real, decided, dated (2026-07-24) generalization result. Zero hits grepping TASK-0151 across all 4 register files — genuinely uncaptured. |
| TASK-0160 | `ENG` | Implements `quantum_connectivity_matrix` (P_∞(i,j)) with correctness proofs (symmetry, row-sum). Operator-construction code, used by later analyses, not itself a claim. |
| TASK-0167.002 | **`NO-HYP`** (draft 2) | Under the project's own corrected permutation null, no target reaches 80% detection power for a planted signal at any strength tested (up to ~4× background). Real, dated (2026-07-28), statistically decided finding about the pipeline's own detection sensitivity. Uncited anywhere in the register. Possible thematic overlap with `HYP-P14`'s later (2026-09-01) headroom framing — flagged for Architect judgment on merge vs. keep-distinct, not decided here. |
| TASK-0178 | `ENG` | Implements `allostery.response` (coupling-free-energy module) + validates against an external reference prototype to 1.6e-13. Infrastructure the H4.x family later runs on — the decisions live in those later-citing tasks (already captured in `reference_register.md`), not here. |
| TASK-0188 | `ENG` | Hop-distance cutoff robustness sweep — tests whether prior claims (TASK-0186/TASK-0177's C6) are cutoff-fragile. Parameter-robustness/QA audit of existing claims, not a new mechanism claim. **Spot-checked in full.** |
| TASK-0197 | `ENG` | `claim.py stage` cannot stage deletions — tooling bug fix. |
| TASK-0206 | `ENG` | fpocket binary drift across two build machines (git-identity root cause). Reproducibility/infra; explicitly "no verdict changes... a magnitude, not a finding." **Spot-checked in full.** |
| TASK-0215 | `ENG` | Sources 6 new VALID apo/holo pairs from RCSB (Leg B). Dataset construction, feeds later hypothesis tests, not itself one. |
| TASK-0220 | `ENG` | Calibration check of `quantum_seed_readiness`'s `SAFE` threshold — resolves "is `PARTIAL` the honest ceiling" as a diagnostic-tool calibration question, not an allostery-mechanism claim. **Spot-checked in full.** |
| TASK-0229 (parent) | **`HYP-P13`; `H1`, `H2.2`, `H4.1`(partial), `H6.2`(partial), `H7`, `H9`, `H10`, `H11`, `H15.1`/`H15.2`(partial)** | Closing synthesis over `.001`–`.007`. Each subtask already maps to a `reference_register.md` row (`.001`→H9, `.002`→H10/H11, `.003`→H6.2, `.004`→H1, `.005`→H2.2, `.006`→H4.1, `.007`→H7/H15). Parent itself also cited directly in `physics.md`'s `HYP-P13` section (L834-1047, via `.003`/`.006`). All already captured — listed here for completeness of the ledger, not as a new finding. |
| TASK-0231 | `ENG` | Mutation-tests the suite's own config-level blind spot; builds 4 guards. Test-infrastructure QA. |
| TASK-0240 | `ENG` | Builds `assert_criterion_reachable` diagnostics guard. Infra. |
| TASK-0250 | **`H16.1`** | GNM-vs-B-factor model-validity check, all 15 real targets. Title names H16.1 directly; already the exact citation in `reference_register.md`'s H16.1 row. |
| TASK-0260 | **`NO-HYP`** (draft 3, with TASK-0269) | Tests whether PocketMiner/CryptoSite/P2Rank/FTMap-FTSite close the register's own residual. Cited in `physics.md`'s `HYP-P13` section (L949, L1037) — but only for *methodology reuse* ("TASK-0260's own crypticity stratification"), never for this task's own actual headline claim. Genuinely uncaptured. |
| TASK-0269 | **`NO-HYP`** (draft 3, with TASK-0260) | Runs PocketMiner for real (the untested half of TASK-0260) — does not close the residual. Same claim family as TASK-0260, one draft. |
| TASK-0278 | **`NO-HYP`** (draft 4) | Occupancy ≠ allosteric effect: BCR-ABL1's "apo" (`1OPL`) is held open by myristic acid in the same pocket asciminib later binds allosterically; MYR-stripping control shows the confound is structural, not removable by deleting the ligand's atoms; the same classification rule found a worse instance (PKR_MITAPIVAT/AG946, `7FS3`, 91-92% overlap) not in the task's own original filing. **Reclassified from an initial `HYP-P13` read — see Method.** |
| TASK-0287 | **`HYP-P14`** | ICC variance decomposition + within-protein stratified positive-control design for "at what scale is pocket location encoded." Its `fpocket druggability` row is cited directly in `physics.md`'s `HYP-P14` supporting-evidence table. |
| TASK-0296 | `ENG` | Regenerates 6 stale KRAS golden test fixtures after the `apo` PDB changed. Test-fixture maintenance. |
| TASK-0305 | **`NO-HYP`** (draft 5) | On real ASBench ground truth, every arm (incl. CTQW) is at-or-below random at top-5 retrieval, CTQW significantly worse than random; the field's own "84% accuracy" SOTA is an enrichment statistic, not a retrieval one (SOTA itself only 1/11 on retrieval). Decisive, dated (2026-08-31), uncited anywhere in the register. **Spot-checked in full.** |
| TASK-0315 | `ENG` | Re-derives the `terms_block` vs. `ctqw`/`geometry` comparison, finds a reproducibility discrepancy (p=0.049 vs. previously-cited 0.019, traced to one target's drifted values). QA/reproducibility audit of an existing comparator (TASK-0263's own claim), not a new claim of its own. |
| TASK-0324 | `ENG` | Applies TASK-0323's proposed verdict lines (register maintenance). Process work, not new science. |

## `NO-HYP` drafts — proposed, not landed

Same evidentiary bar the register already holds itself to (cite the
specific deciding task and its actual result). Grouped by claim, not
one-per-task, per this task's own Constraint (TASK-0260/TASK-0269
share one draft).

### Draft 1 — `dcc_low`/transport generalization (search_complexity.md style)

**Claim.** `dcc_low`'s cryptic-pocket signal, first found on
CARDIAC_MYOSIN, generalizes cleanly to a second, independent target
(PTP1B) under the register's own strict correction. The transport
observable's BCR_ABL1 positive does not generalize to either PTP1B or
CASPASE7 under the same correction (CASPASE7 shows an
uncorrected-significant hint in the same direction, not a clean
replication).

**Status, 2026-07-24 (TASK-0151, extending TASK-0145/TASK-0149/
TASK-0168): TESTED — mixed, real, and informative.** `dcc_low` is
arguably the strongest single robust result in the register at the
time this was run.

### Draft 2 — detection power / limit of detection (physics.md style, general methodology)

**Claim.** Under this project's own corrected, compact permutation
null, no target reaches 80% statistical power to detect a planted
allosteric-strength signal at any strength tested (up to ~4× background
conductance) — a limit on this pipeline's own detection sensitivity,
independent of whether a real signal exists to find.

**Status, 2026-07-28 (TASK-0167.002): TESTED.** Under the (now
superseded) scattered null, LOD ≈2× background on 2/3 targets — the gap
between the two null conventions is itself the measured cost of
TASK-0158's correction. **Flag for Architect**: possible overlap with
`HYP-P14`'s later (2026-09-01) headroom/confound framing — same general
theme (the pipeline can't detect what it's looking for), different
specific mechanism (statistical power vs. proximity confound). Merge,
cross-reference, or keep distinct — not decided here.

### Draft 3 — external SOTA cryptic-pocket predictors do not close the residual (physics.md style)

**Claim.** Purpose-built cryptic/allosteric-pocket predictors
(PocketMiner, CryptoSite, P2Rank, FTMap/FTSite) do not significantly
close this register's own residual gap when run on real targets;
PocketMiner specifically, unblocked and run for real (not merely cited
from its paper), does not close it either.

**Status, 2026-08-25/26 (TASK-0260, TASK-0269): TESTED — negative.**

### Draft 4 — occupancy ≠ allosteric effect (physics.md style, cross-references HYP-P13)

**Claim.** A pocket being open and ligand-occupied in a crystal
structure is not sufficient evidence of an allosteric *effect* — the
mechanism must distinguish occupancy from function. BCR-ABL1's
registered "apo" structure (`1OPL`) is held open by myristic acid
(`MYR`), a non-therapeutic fatty-acid ligand occupying the same
myristoyl pocket asciminib later binds to produce the actual allosteric
effect. Computationally stripping `MYR`'s atoms does not close the
pocket (fpocket AUC and window classification are unchanged) — the
confound is the crystallised backbone conformation itself, not
removable post hoc.

**Status, 2026-08-26 (TASK-0278, extending TASK-0209's `hetatm_audit`):
TESTED.** A register-wide pocket-window-overlap classification rule
(applied to all 29 apo structures) found a worse, previously unflagged
instance: PKR_MITAPIVAT/PKR_AG946's shared apo (`7FS3`) has 91-92%
window overlap with a named allosteric modulator, not remediated (not
a mandatory target, flagged for follow-up). **Cross-reference**:
`HYP-P13`'s existing text already discusses BCR-ABL1's MYR/asciminib
contrast in prose (citing TASK-0209, not TASK-0278) — this draft is the
sharper, structurally-decisive half of that same story (the stripping
control, the worse PKR instance) that HYP-P13's text does not yet
carry. Architect call: fold into HYP-P13 as an update, or land as its
own id — both are defensible, not decided here.

### Draft 5 — enrichment vs. retrieval reframing on ASBench (physics.md or search_complexity.md style)

**Claim.** On real ASBench ground truth (108 structures, both sites
field-annotated, bypassing every labelling defect this register has
found in its own benchmark), none of this project's observables beat
random at top-5 residue retrieval, and CTQW is significantly *worse*
than random (anti-correlated, not merely uninformative). The field's
own widely-cited "84% accuracy" SOTA number is a set-level enrichment
statistic, not a top-k retrieval statistic — under the identical
retrieval metric, the SOTA method itself retrieves a true-site residue
in its top 5 on only 1 structure in 11 (9.3%).

**Status, 2026-08-31 (TASK-0305): TESTED — decisive negative +
reinterpretation.** Priority flagged by its own filing as "the cleanest
negative this register has produced." Feeds TASK-0306's meta-classifier
directly.

## Not done — awaiting Architect sign-off before continuing

Per this task's own Planned Validation gate: the full ~306-task sweep,
compiling/finalizing the `NO-HYP` drafts above for landing, and
re-running TASK-0322's checker/index after any register additions —
none of these proceed until the Architect (or the repo owner) confirms
this pilot's bucket split and method are not systematically
miscalibrated.

**Signed off 2026-09-04 — see [[TASK-0326]]'s own "Architect sign-off"
section for the full reasoning.** Pilot approved. Drafts 1, 3, 5: land as
new hypotheses. Draft 2: land as a new hypothesis, cross-referencing
HYP-P14. Draft 4: do NOT land separately — fold into HYP-P13 as a dated
update instead (it sharpens/extends HYP-P13's own already-stated
BCR-ABL1/MYR claim rather than bearing a different one). Standing rule for
the rest of the sweep: a `NO-HYP` finding gets its own id only if it is a
genuinely different claim or mechanism, not merely a sharper or better-
evidenced version of an existing hypothesis.
