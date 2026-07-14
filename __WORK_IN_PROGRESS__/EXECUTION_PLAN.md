# Execution Plan — sequenced, mapped to task IDs

State verified on the `bartosz` branch snapshot: **252 tests passing, 0 real failures**;
all science stubs implemented (`baselines` 180, `coarse` 260, `pathways` 174, `viz` 365);
seam + invariance protocols adopted (TASK-0050/0051); no `w[6:]` index-slicing bug in the
physics core. Ordering is by **dependency and risk**, not task number.

Legend: **[EXISTS]** = filed before this plan · **[FILED]** = created *from* this plan
(TASK-0070–0086, all 17 filed 2026-07-12, commit `9fdeb2f`) — no `[NEW]` remains outstanding.

## ⚠️ 2026-07-13 correction — read before dispatching anything in Phase 5

`__WORK_IN_PROGRESS__/REVIEW-2026-07-13-proximity-confound-and-propagator-semantics.md`
found, **executed against real code** (not inferred), that the headline AUCs TASK-0079.005
produced (`RESULTS.md`) are confounded by distance-from-seed: on a synthetic reproduction,
a pure Euclidean-distance baseline (AUC 0.966) **beats** the CTQW score (0.914) on a
proximal pocket, and both collapse on a distal one. Cross-target, the one mandatory target
with a genuinely *distal* pocket (BCR_ABL1) is the one at chance — the signature of a
proximity detector on a challenge whose premise is *distal* regulation. A second, separate
finding shows `propagators.heat` on `H_new` is not classical diffusion (it returns
`H_new`'s ground-state density; the retracted TASK-0091 dephasing-sweep framing rested on
this misunderstanding).

**New blocking phase inserted below: [Phase 1B](#phase-1b--proximity-confound--propagator-semantics-correction-blocking-2026-07-13).**
It gates every current headline number and every task downstream of one (5.2/5.3/5.4/5.6/5.8
below, each annotated). **Do not report, or build further on, any AUC in the current
`RESULTS.md` as allosteric signal until it clears TASK-0094's proximity floor.**

**Addendum, same day, prompted by a direct user question:** an end-to-end audit (traced
`run_frozen_verdict` down to every function it calls) found that **no reported number in
this pipeline currently depends on quantum phase/coherence at all** — `ctqw`/`haken_strobl`
are correctly implemented, real quantum evolutions, but every scored AUC is built only from
`time_averaged_ctqw` (phase-averaged by construction) and `ground_state_relaxation`
(real-valued, no oscillation). This is a risk to the submission's core "quantum" premise,
not just a labeling gap — see **TASK-0099** (Phase 1B.8), filed to wire the
already-implemented-but-never-reported `dephasing_sweep` into the scored path.

## ⚠️ 2026-07-13(b)/(c) correction — supersedes part of 1B.4, resequences 1B.8

Two further same-day reviews **directly revise 1B.4's own conclusion**, which currently
reads "real, floor-clearing result" for BCR_ABL1's `ground_state_relaxation`=0.7315.

`REVIEW-2026-07-13b-operator-falsification-negative-controls.md`, executed as a 2×2 control
matrix (well location × coupling strength, varied independently on a constructed dumbbell
network), found GSR **tracks the well, not the coupling** — it scores the *decoy* lobe 1.000
and the truly-coupled lobe 0.000 when the two cues are put in conflict. **The number stands;
the causal claim does not.** BCR_ABL1's 0.7315 is real, floor-clearing, and genuinely
distal — but it is evidence of a soft, well-connected *structural prior* (a cryptic-pocket
signature), not of allosteric signal propagation from the active site. Filed:
**TASK-0103** (permanent negative-control test, the regression that would have caught this)
and **TASK-0104** (re-frame the claim in `RESULTS.md`/1B.4 itself — do not retract the
number). The review also identifies dephasing-assisted transport (ENAQT, `haken_strobl`) as
the one surviving genuinely-quantum, genuinely coupling-tracking signal, with a measured
interior-γ optimum on synthetic disordered networks — filed **TASK-0105**, which
**resequences TASK-0099 behind it** (1B.8 below is corrected to reflect this).

`REVIEW-2026-07-13c-ctqw-trapping-mechanism.md` (verifying a colleague's hypothesis)
explains the *mechanism* behind the original 07-13 proximity confound (P1-A): `H_new`'s
diagonal potentials (V_B/V_T/V_R/V_C/V_M) cause Anderson-like transport localization in
CTQW — the walk never leaves the seed's first contact shell (participation ratio 0.024 vs.
0.414 on the bare Laplacian). Proximity-like scoring is *caused* by this, not merely
correlated with it. On a synthetic distal pocket, transport-preserving operators (`H10`,
`H2`) score 0.58–0.59 AUC where `H_new` scores 0.12 (anti-correlated) — with a real-data
sign match already sitting in `RESULTS.md` (BCR_ABL1: `H10`=0.558 vs `H_new`=0.525,
previously read as noise in 1B.5/TASK-0093). Filed **TASK-0106**, the explicit real-data
reproduction gate the review requires before this changes any claim. Also amends **1B.10**
(TASK-0101 must report a transport diagnostic, not AUC alone) and flags **1B.5**
(TASK-0093 should read TASK-0106's result before finalizing).

**Neither review is a basis to reselect the submission operator** — that remains
Tier-2-gated per **TASK-0100** (1B.9), unaffected by either finding.

## Progress tracker (Phases 0–6 + 1B, the scored/critical-path work — 50 tasks)

**Snapshot as of 2026-07-13 (later same day, post-07-13b/c) — this is a point-in-time copy,
not a live view.** `.ai/COMMON.md`'s Active Work Registry is the canonical,
continuously-updated source — re-check there (or regenerate this table) before trusting it
for dispatch decisions.

| Done | In Progress | TODO | Total |
|---|---|---|---|
| 19 (TASK-0070, TASK-0052, TASK-0047, TASK-0058, TASK-0063, TASK-0055, TASK-0064, TASK-0071, TASK-0056, TASK-0067, TASK-0079, TASK-0074, TASK-0066, TASK-0094, TASK-0095, TASK-0097, TASK-0096, TASK-0100, TASK-0091) | 0 | 31 (+4: TASK-0103, TASK-0104, TASK-0105, TASK-0106) | 50 |

**To refresh this snapshot:** each task file's own `- Status:` line is authoritative
(`.ai/COMMON.md`'s registry mirrors it). One-line check for any ID:
`grep -h "^- Status:" .ai/tasks/*/TASK-0070*.md` (swap the glob per ID), or read the
`Status` column directly in `.ai/COMMON.md`'s Active Work Registry table, which already
covers every ID below. `python3 .ai/tools/claim.py status` additionally shows which IDs
are currently *claimed* (about to move) even before their `Status:` line changes.

Per-phase tables below carry a **Status** column (Done / In Progress / TODO, same
snapshot time). Phase 7 (deferred scaffold hygiene) is tracked separately, at the end.

---

## Architectural premise (read this first — it corrects TASK-0018's scope)

TASK-0018 concluded **"port, don't cross-import"**: `backend/` is a live Render service and
cannot inherit `allostery/`'s firewall/LOPO machinery or heavy deps (prody, fpocket clients).
That verdict **stands**. But TASK-0018 assumed `backend/` was a self-contained interactive
tool. It is not: **`backend/` + `frontend/` are the execution and presentation layer for the
research results** — the thing that triggers a run and *shows* the N×N connectivity matrix,
the top-5 hit list, and the honest verdict. They are the submission's face, not a PoC.

These two facts are reconciled by one decision, and it is the keystone of this plan:

> **The research package emits versioned result artifacts. The backend serves artifacts;
> it never recomputes science in the request path.**

`backend/` still imports **nothing** from `allostery/` — it reads a JSON/NPZ contract.
That keeps the cold-start budget, keeps the firewall out of the web tier, and lets the
frontend be built in parallel with the science. The contract (TASK-0083) is therefore an
**early** decision even though delivery is late work.

---

## Phase 0 — Correctness on code already marked DONE (blocking)

Defects in *shipped, reviewed, tested* code. Everything downstream inherits them.

| # | Task | Why now | Status |
|---|---|---|---|
| 0.1 | **[FILED] TASK-0070 — pocket label exclusion assembly** | **Oldest live defect.** Nothing assembles `pocket & ~functional & ~terminal`; `labels` owns ingredients, `protocol` gates them, `analysis` consumes the raw mask. Survived four reviews *because no task owns it* — it is a seam, not a module. Blocks 0.2, 0.3, and every honest AUC. | **Done** (commit `5970bc5`). `build_labels()` landed in `labels.py`, asserts the exclusion invariant; `protocol.get_pocket_mask` now returns the assembled label, not the raw mask. KRAS Cys12 decision recorded: excluded via the general `~active_site` rule, no special-casing needed (verified against real 4OBE/6OIM data). |
| 0.2 | **[EXISTS] TASK-0052** — reconcile leakage-gate contract | Gate is green on self-validating guards but its 3 contract tests are still `xfail`. Acceptance for TASK-0004/0006 was **0 xfail**. Needs 0.1 to bind `build_labels`. | **Done** (commit `fb9a2eb`). All 3 CONTRACT stubs rewritten against the real API (0 xfail, 12/12 passing both under `pytest` and standalone). `SEAM-0003` closed to VERIFIED. Real gap found verifying `frozen_context`/`assert_readable` vs. the `_SealedLabels` reference spec — it's an opt-in/cooperative gate, not a hard data-seal (`labels.py`/`superpose.py` called directly bypass it) — filed as **TASK-0087**, not fixed here (out of this task's scope). |
| 0.3 | **[EXISTS] TASK-0047** — foundation review gap bridging | Commits the network-gated KRAS integration test (apo 4OBE / holo 6OIM). The 21/21 match is still a **docstring claim**. | **Done** (commit `e4410a0`). TASK-0070 had landed in the interim and partially subsumed this (its Cys12/exclusion real-target tests), but not fully — neither used `load_target_config` nor pinned `holo_pocket_mask`'s raw recovery against `backend/systems.py`. Added the remaining piece: a `load_target_config`-driven KRAS_G12C test pinning the 21/21 heavy-atom recovery against `pocket_full[4.5]` exactly (the docstring claim is now a real regression check, verified against live 4OBE/6OIM data), plus the P3 indel test for `_needleman_wunsch_map` (genuine insertion/deletion, not just re-numbering — first attempt's single-residue assumption was wrong, adjacent synthetic-helix residues sit inside the contact cutoff, redesigned around two discriminating residues). 33/33 passing with `prody` + live network, 30/33 with a clean skip path without it. No production code touched. |
| 0.4 | **[EXISTS] TASK-0063** — `functional_indices` gate parameter gap | Plumbing so a FROZEN caller reaches `functional_indices` without bypassing the gate. Same seam as 0.1 — do together. | **Done** (commit `f702f33`). `get_functional_indices` widened to `**kwargs` (matching `get_superpose_report`'s pattern) instead of an explicit parameter list, forwarding `heavy_atom_coords`/`heavy_atom_seq_index` to `labels.functional_indices`. New regression test proves the two approximations genuinely diverge through the gated wrapper itself, not just in `labels.py`'s own tests. `test_protocol.py` (24/24) + `test_select.py` (14/14) unchanged. |

> **Decision required inside 0.1:** KRAS **Cys12** — in or out of the pocket label?
> `targets.yaml` says exclude; sotorasib (MOV) is covalent at Cys12 so it enters the
> MOV-derived contact set. Pick one and record it. Do not inherit it by omission.
> **Resolved:** excluded, via the general `~active_site` rule (Cys12 is also a GDP-contact
> functional residue, so the exclusion falls out automatically — no KRAS-specific case
> needed). See TASK-0070's Open Questions for the full verification.

---

## Phase 1 — Make the verdicts honest

The verdict layer was built **before** its denominator. `classify_failure` anchors on
AUC-vs-chance (0.5); `verdict_template` compares against the **H10 operator**. Neither is a
triviality floor. `baselines.py` now exists — wire it in.

| # | Task | Why now | Status |
|---|---|---|---|
| 1.1 | **[EXISTS] TASK-0058** — wire baseline floor into `classify_failure` | Turns "beats chance" into "beats degree / betweenness / distance-to-active". Without it **no verdict the pipeline emits is honest.** | **Done**. `floor_scores` param + new `BEATS_CHANCE_NOT_FLOOR` category added to `classify_failure`, checked after the existing chance check, before `NO_FAILURE_DETECTED`; `floor_scores=None` default verified byte-identical to prior behavior. `SEAM-0005` closed to VERIFIED. `test_seam_0005_baseline_floor.py`'s `xfail` removed, passes for real; 4 new direct unit tests in `test_diagnostics.py`. 398 passed, 0 failed. |
| 1.2 | **[EXISTS] TASK-0055** — `optimised` AUC freeze-provenance check | Verifies headline AUCs come from the frozen/DEV path, not the old label-tuned notebook route. If not, the report layer silently re-imports the §8 leak. | **Done.** Finding: the leak is real, not hypothetical — `verdict_template`'s `provenance="frozen"` is a free-text keyword with no read of `protocol.current_context()` anywhere in `report.py`; confirmed empirically (outside any `frozen_context`, a claimed-frozen render suppresses the DEV banner regardless). `SEAM-0004` left **OPEN** at verification time (evidence recorded, not auto-flipped VERIFIED) with a cross-module seam-test (`xfail(strict=True)`, same convention as SEAM-0005 pre-fix). Fix filed as **TASK-0088**, now **Done**: `protocol.stamp_provenance`/`verify_frozen_stamp` add an unforgeable-in-practice token, issued only from inside a real `frozen_context`, that `verdict_template` now requires (in addition to `provenance == "frozen"`) to render unbannered. `SEAM-0004` closed to VERIFIED. 426 passed (was 410). Same precedent as TASK-0052 → TASK-0087 (TASK-0087 itself still TODO, unclaimed). |
| 1.3 | **[EXISTS] TASK-0064** — wire unsupervised score into frozen loop | Completes the label-free selection path. | **Done.** `protocol.select_frozen_config(build_candidates, held_out_target)` added -- takes a *callable*, not a pre-built candidate list, so both construction and scoring run inside `frozen_context`, catching a leaky candidate-builder, not just a leaky scoring call. Lives in `protocol.py` itself, alongside the other gated accessors. `SEAM-0009` closed to VERIFIED (2 seam-tests). `INV-0004` seeded for `select.py`'s reported quantities, `TASK-0089` filed as its owner. 405 passed (was 402). |
| 1.4 | **[FILED] TASK-0071 — permutation-null leak detector** | The firewall *prevents* known leak vectors; nothing *detects* an unforeseen one. Shuffle labels, re-run, flag anything still scoring. Home: `diagnostics.py`. Verified reference implementation exists. | **Done.** Reference located: `test_leakage_gate.py`'s GATE-B4 (not the research notebook — grepped, nothing there). Ported `permutation_null`/`detect_permutation_leak` into `diagnostics.py`, `PERM_LEAK_THRESHOLD=0.60` carried over verbatim. Both acceptance scenarios validated against this package's real production scorer (`build_H_new` + `time_averaged_ctqw`) on a synthetic structure — deliberately not KRAS_G12C, which `PLAN.md` documents as near-chance even honestly, so not a "known real signal" case. 5 new tests; 407 passed, 0 failed. |
| 1.5 | **[EXISTS] TASK-0056** — phase-4 review (diagnostics/report/baselines/pathways) | Same lens the phase-3 review applied, on the four newest modules. | **Done** (commit `94470e7`). No P0/P1 in any of the four modules' own code. Found and closed **SEAM-0011** (new): `classify_failure`'s `floor_scores` had never been exercised against real `baselines.py` output, only hand-built arrays — 3 new tests added using a real `degree_centrality` call on a deliberately-confounded fixture, marked VERIFIED. Re-scoped **SEAM-0008**: not a `report.py` bug — its "renders, doesn't assemble" boundary is deliberate; reassigned the real owner to **TASK-0079** (its own "orchestrate the pipeline stages" scope is the missing assembly step), cross-linked into that task directly, stayed OPEN. SEAM-0004/0005 already independently closed by TASK-0055/0058 before this review started — spot-checked, not re-litigated; SEAM-0004 additionally observed being actively fixed live by a concurrent TASK-0088 mid-review. Full record: `.ai/reviews/REVIEW-2026-07-12-phase4-diagnostics-report-baselines-pathways.md`. |

---

## Phase 1B — Proximity confound & propagator-semantics correction (BLOCKING, 2026-07-13)

Inserted after `__WORK_IN_PROGRESS__/REVIEW-2026-07-13-proximity-confound-and-propagator-semantics.md`
found that TASK-0079.005's real headline AUCs are confounded by distance-from-seed, and
that TASK-0091's original framing rested on a false premise about `propagators.heat`'s
semantics. **This phase gates every current headline number** (see banner at the top of
this document) and supersedes the original Phase 5 framing wherever noted. Sequencing
below matches the review's own "Sequencing" section exactly — do not reorder.

| # | Task | Why in this order | Status |
|---|---|---|---|
| 1B.1 | **[FILED] TASK-0094 — proximity baselines into the floor** | **Do this first.** Add `euclid_from_seed_centroid`/`hop_from_seed` to `baselines.py`, wire into `floor_scores`/`classify_failure`, re-run all mandatory targets. Real evidence: a pure distance baseline (AUC 0.966) beats CTQW (0.914) on a proximal pocket; both collapse on a distal one. **Decides whether we have a result at all.** | **Done** (commits `8d7370b`/`b217c21`). `classify_failure`'s floor now takes the **max** across `degree_centrality`/`euclid_from_seed_centroid`/`hop_from_seed`. Real re-run: KRAS_G12C (0.779) does **not** clear the floor (euclid baseline alone scores 0.798) → `BEATS_CHANCE_NOT_FLOOR`, confirming the review's suspicion. BCR_ABL1 stays `NO_SIGNAL_IN_APO`. CARDIAC_MYOSIN clears the floor but `INSUFFICIENT_RESOLUTION` fires first. |
| 1B.2 | **[FILED] TASK-0095 — correct propagator semantics** | Cheap, and stops a false physical claim from propagating into the submission. `heat(H_new)` is `H_new`'s ground-state density (Spearman 0.998 vs `\|ground state\|²`), not classical diffusion — rename, guard against indefinite operators, correct `RESULTS.md`/report framing. | **Done.** Renamed `heat`→`ground_state_relaxation` everywhere; added `_warn_if_indefinite` guard (warn by default, `strict=True` raises); corrected `analysis.py`/`report.py`/`RESULTS.md` framing (BCR_ABL1's old claim struck through, marked `[CORRECTED]`, per this doc's own no-silent-overwrite convention). Verified no numeric change on genuinely-PSD operators against an independent `scipy.linalg.expm` reference. |
| 1B.3 | **[FILED] TASK-0096 — delete or implement phantom H11/H12** | Cheap, removes an audit liability. Both verified (`np.allclose`) identical to `H6`/unweighted-contact Laplacian despite docstrings claiming anisotropic weighting. Independent of 1B.1/1B.2, can run in parallel with them. | **Done.** Decision: implement both (per-operator call, not both-implement/both-delete by default) — a sweep proving them useless is itself a useful result. Both ported verbatim from `notebooks/H_new_engineering (4) CLEAN.ipynb` (never-ported real formulas, distinct from H6/unweighted-Laplacian). Added `H14_anm_pinv_trace` (new research operator, global-ANM analogue to H12's local one) explicitly so a future sweep — see 1B.9/1B.10 — can judge them empirically. |
| 1B.4 | **[RE-FILED] TASK-0091 — does `H_new`'s ground state localize on *distal* pockets?** | The one open scientific question from the review that is not proximity in disguise. Original dephasing-sweep framing **retracted** (structurally could not converge to `heat(H_new)`'s value — see 1B.2). Re-filed to test BCR_ABL1's real 0.731 directly against 1B.1's proximity floor. **Hard blocked on 1B.1 and 1B.2 — both now Done, unblocked.** | **Done — real, floor-clearing result, causal claim superseded 2026-07-13(b).** BCR_ABL1's `ground_state_relaxation`=0.7315 clears the proximity floor decisively (max floor 0.565, margin +0.166) on a genuinely distal (~32 Å) pocket; localization is diffuse (0/30 top-k hit precision, aggregate enrichment only). **The causal claim is now corrected, not retracted**: `REVIEW-2026-07-13b` (2×2 well×coupling control matrix) shows this quantity tracks the well, not the coupling — a structural-prior/cryptic-pocket signature, not allosteric communication. See **TASK-0103** (the negative-control test) and **TASK-0104** (the `RESULTS.md` re-frame). TASK-0102's seed-invariance caveat (below) is a separate, already-Done check and stands as-is. |
| 1B.5 | **[UPDATED] TASK-0093 — KRAS AUC reconciliation, now against the proximity floor** | The 8.0 vs 10.0 Å cutoff changes the contact graph's distance-decay from the seed — a candidate mechanism for the AUC gap that has nothing to do with real allosteric sensitivity. Every factorial combination must now be checked against 1B.1's floor, not just chance. **Hard blocked on 1B.1 — now Done, unblocked.** | TODO. **Amended 2026-07-13(c)**: `REVIEW-2026-07-13c` gives a mechanistic reason (CTQW transport localization from `H_new`'s diagonal potentials) to expect this same pattern on BCR_ABL1 too (`H10`=0.558 vs `H_new`=0.525, previously read as noise) — read **TASK-0106**'s real-data reproduction before finalizing this task's own reconciliation. |
| 1B.6 | **[FILED] TASK-0097 — name the "quantum metric" honestly** | `time_averaged_ctqw` is the decoherent/infinite-time-average limit (a spectral overlap quantity), not a coherent walk. Reporting honesty; can run in parallel with 1B.7 once 1B.1–1B.3 land. | **Done** (commit `bc41f09`). `[NOTE]` disclosure added to `verdict_template` before any AUC renders; second methodology paragraph added to `RESULTS.md`; 3 new tests including a durable `RESULTS.md`-content check. |
| 1B.7 | **[FILED] TASK-0098 — amend INVARIANCE_PROTOCOL's SIGNAL class** | Protocol-level generalization: SIGNAL must beat the domain's strongest trivial confounder (distance-from-seed here), not just chance. Third instance of the same unexecuted-gauge-symmetry pattern (after SE(3) rotation, SU(2)/Clifford-frame) — see the review's Meta section. Can run in parallel with 1B.6. | TODO |
| 1B.8 | **[FILED] TASK-0099 — wire a genuine coherence metric into the scored verdict** | Audit (2026-07-13, prompted by a direct user question against 1B.6's finding) confirmed: **nothing phase-dependent currently reaches any reported AUC.** `ctqw`/`haken_strobl` are correctly implemented, real quantum evolutions — but every scored number traces only to `time_averaged_ctqw`/`ground_state_relaxation`, both phase-averaged. `dephasing_sweep` exists, is tested, and has **zero call sites** in the reported pipeline. Promote it (calibrated γ, all 3 mandatory targets, checked against 1B.1's floor) so at least one reported number would change under phase randomization. **Hard blocked on 1B.1 — now Done, unblocked.** | **Resequenced 2026-07-13(b) — do NOT start yet.** `REVIEW-2026-07-13b` shows this task's own framing ("does dephasing recover a specific AUC") is exactly the ill-posed question the review's §4 dismantles. **Now blocked on TASK-0105** (ENAQT γ-sweep on real targets, measuring transport magnitude/interior-optimum shape) — TASK-0099 should wire whatever TASK-0105 actually finds, not proceed on its pre-review framing. |
| 1B.9 | **[FILED] TASK-0100 — decide the operator-sweep architecture** (Architect decision) | We have 14 named operators (1B.3 added `H14`) but no harness ever runs more than 2 (`H_new`/`H10`) against a real target. Routed to the Architect per explicit user instruction — "otherwise I do not understand how we would possibly pass the challenge." | **Done.** Decided: library fn `analysis.operator_sweep` + thin `scripts/sweep_operators.py`, **not** `run_challenge.py` (keeps the submission orchestrator a reported decision, not a search — same line already drawn for TASK-0046). Two-tier rating: **Tier 1** (descriptive — floor-cleared + AUC + apo/holo consistency, no frozen-gate) vs. **Tier 2** (selection — replacing `H_new`/`H10` as submission operator — hard-gated through `select_frozen_config`/`leave_one_protein_out`, N=3 flagged as thin). Three operator tiers: **A** (`H_new`, `H10`, `H14` — selection-eligible) vs. **B** (`H1`-`H9`, `H11`-`H13` — descriptive-only, never intended as submission candidates). Floor-failing operators recorded, not deleted (Tier A failing all 3 targets disqualifies it from Tier 2; Tier B failing is just recorded context). **Resequencing resolved**: TASK-0091/TASK-0093/TASK-0099 confirmed NOT blocked — none is an operator-selection act, all diagnose the already-chosen `H_new`. |
| 1B.10 | **[FILED] TASK-0101 — operator sweep Tier-1 harness** | Executes 1B.9's decision: `analysis.operator_sweep` + `scripts/sweep_operators.py`, all 14+2 operators × 3 mandatory targets, Tier-1 (descriptive) only — no operator selection. **Amended 2026-07-13**: scores each operator through **both** `time_averaged_ctqw` and `ground_state_relaxation` (16 ops × 2 propagators × 3 targets = 96 cells, per 1B.4's finding that propagator choice — not just operator choice — was what separated BCR_ABL1's chance and floor-clearing results) — and must run **in chunkable, resumable, parallelizable parts** (`--target`/`--operator`/`--propagator` filters, per-cell files, `--force` to recompute one suspicious cell, `--aggregate` to merge partial runs from multiple machines). | TODO |
| 1B.11 | **[FILED] TASK-0102 — is 1B.4's finding seed-dependent, or a fixed-minimum artifact?** | User's question, 2026-07-13: does `ground_state_relaxation` genuinely couple to the seed, or does `exp(-Ht)` at `t_max=15` simply converge to `H`'s global ground state regardless of source — meaning "the minimum has to be somewhere, and on BCR_ABL1 it happens to sit nearer the pocket"? Real-data seed-invariance check first (cheap, reuses 1B.4's cached data), then a synthetic discriminating network (engineered minimum away-from vs. coupled-to a "drug site") if needed. Not blocking, but 1B.10's ground-state column should be read alongside this task's finding. | TODO |
| 1B.12 | **[FILED] TASK-0103 — dumbbell 2×2 negative-control test suite** | Permanent, synthetic (no PDB/network) regression test implementing `REVIEW-2026-07-13b`'s well×coupling control matrix — the test that would have caught 1B.4's causal misattribution. Asserts `ground_state_relaxation` follows the well, `ctqw`/transport follows the coupling. **No dependency — start anytime.** | **Done.** `test_dumbbell_negative_control.py`, 10 tests. Reproduced the review's decisive double dissociation cleanly (C2: GSR=0.000/CTQW=1.000; C3: GSR=1.000/CTQW=0.000, 5 seeds each). Found and fixed a real bug in the first prototype (deterministic construction silently averaged 5 identical "seeds") before locking in assertions. Registered as the reusable harness (`build_dumbbell_network`/`auc_to_drug`, public) for future falsification tasks. |
| 1B.13 | **[FILED] TASK-0104 — re-frame the GSR/BCR_ABL1 claim** | `RESULTS.md`/1B.4's text currently frames 0.7315 as (diffuse) allosteric signal. Correct to "apo-computable structural prior for cryptic pockets," citing TASK-0103's evidence. **Number unchanged, claim corrected — cheap.** | **Done.** `RESULTS.md` corrected additively (TASK-0095/TASK-0102's prior corrections left standing, per that doc's own no-overwrite convention) — new block cites `REVIEW-2026-07-13b`'s dumbbell control matrix and TASK-0103's now-passing regression test by name, states the corrected claim verbatim ("apo-computable structural prior... detectable without reference to the active site"), records the operator-register verdict (`ground_state_relaxation` = RETAINED-NARROWED). TASK-0091's hit-list-diffuseness finding confirmed preserved, not deleted. Also fixed one stray pre-rename "heat" mention in the CARDIAC_MYOSIN section. No code/analysis re-run, per this task's own Constraint. |
| 1B.14 | **[FILED] TASK-0105 — ENAQT γ-sweep on real targets** | Replaces the killed dephasing question underneath TASK-0099 (1B.8). Measure transport magnitude vs. γ ∈ [10⁻⁴, 10²] on all 3 mandatory targets; report interior-optimum presence and enhancement ratio over the coherent walk, not AUC recovery. Per `REVIEW-2026-07-13c`, sweep across `H_new`/`H10`/`H2` — not `H_new` alone, or a null result may reflect that operator's own transport localization rather than an absence of ENAQT. **"The single highest scientific upside in the repo" per the review. No dependency — start anytime.** | TODO |
| 1B.15 | **[FILED] TASK-0106 — reproduce the CTQW-trapping finding on real BCR_ABL1 data** | `REVIEW-2026-07-13c`'s synthetic finding (transport-preserving operators beat `H_new` on a distal pocket by a wide margin) is a mechanism test only — this task is the real-data gate the review requires before it changes any claim. Predicts `H10`/`H2`/`H_new`(reduced λ) beat `H_new`'s recorded 0.525 on BCR_ABL1 and clear its 0.565 floor. Tier-1 descriptive only, per TASK-0100 — does not itself justify reselecting the submission operator. | TODO |

**Non-finding, recorded so it isn't re-litigated:** the review also tested whether
ground-state localization (`heat`) is *immune* to the proximity confound, as an external
reviewer had proposed. It is **not** — `heat`'s synthetic distal-pocket AUC is 0.048, as
anti-correlated as CTQW's 0.035. BCR_ABL1's real 0.731 remains a genuine, unexplained
result that 1B.4 must test, not an already-proven exception.

---

## Phase 2 — Pin the physics so the trees cannot drift (the real "dedup")

Dedup means *one implementation of each shared primitive, ported into both trees, numbers
pinned*. **Resolve the constant before extracting the helper.**

| # | Task | Why in this order | Status |
|---|---|---|---|
| 2.1 | **[EXISTS] TASK-0067** — GNM cutoff + weight-scheme benchmark | **Confirmed live divergence:** `backend` uses **8.0 Å**; `hamiltonians.py` defaults to **10.0 Å** (12.0 for some variants). *The app and the research pipeline currently answer the same question differently.* Extracting a helper first would make the wrong number official. | **Done.** Real benchmark (`analysis.gnm_cutoff_weight_sweep`, heat-kernel scoring) run against KRAS_G12C + BCR_ABL1 (CARDIAC_MYOSIN excluded — `targets.yaml` itself flags its apo structure's data quality as unresolved; MYC_MAX excluded — no pocket to score). **Primary run is APO-only** — the operator/heat-kernel computation reads `apo.coords` exclusively; `holo` is used only to derive the ground-truth pocket label via `build_labels`, never blended into the topology. A **second, separate HOLO run** (holo-native coords + holo-native labels, per explicit user request for comparison) was added: the apo/holo AUC gap is tiny (KRAS +0.009, BCR_ABL1 -0.020) — an order of magnitude smaller than the cutoff/weight-scheme spread (0.164), meaning near-chance performance is not an apo-vs-holo artifact; the ceiling for this operator family is genuinely low on these targets, holo topology in hand or not. **Cutoff: no significant difference** across 7.5/8.0/10.0 Å (mean AUC 0.42-0.43, within noise) — `backend`'s 8.0 Å default does not need to change. **Weight scheme: harmonic modestly but consistently beats binary/gaussian** (wins 3/3 per-cutoff, ~0.11-0.16 AUC), not acted on (n=2 too thin to justify changing `H8_gnm`'s convention). All AUCs near/below chance, consistent with `PLAN.md`'s documented near-chance finding for these targets. 3 synthetic tests + 1 real network-gated benchmark test (apo+holo), 424 passed, 0 failed. |
| 2.2 | **[EXISTS] TASK-0066** — shared Kirchhoff + DCC helper | Extract binary-Kirchhoff context + DCC + z-score; port into both trees (not cross-imported), one test suite. **Must land 2.1's chosen constant.** | **Done.** `backend/analysis.py::_kirchhoff_eigh`/`_normalized_dcc` (shared by `gnm_context`/`_dcc`/`V_covariance`/`_abs_coupling` — the latter two found mid-task, same duplicated block, not just the two originally named); ported analogue in `potentials.py` (shared by `_gnm_msf`/`V_C`/`V_M`; `V_R` unchanged, benefits via `_gnm_msf`). No cutoff/default changed (2.1's "no significant difference, 8.0 Å stays" honored as-is). Verified byte-identical pre/post via scoped `git stash` diffs on real KRAS_G12C data (backend) and a synthetic helix (allostery), not just formula argument. TASK-0074 (hard-rule prerequisite, found and landed first mid-task — see that row) confirms no silent drift into the live service. 17 new tests (11 backend, 6 allostery); 488 passed, 0 failed. |
| 2.3 | **[FILED] TASK-0072 — golden-value cross-tree drift test** | The anti-drift mechanism 2.2 needs: fix a reference structure, assert both trees produce **numerically identical** output. Without it "ported" decays back into "duplicated" — exactly how 8.0 vs 10.0 happened. | TODO |
| 2.4 | **[EXISTS] TASK-0040** — potentials shared GNM context | Same family as 2.2. | TODO |
| 2.5 | **[FILED] TASK-0073 — register cross-tree seams** | `.ai/seams/` records (owner + seam-test) for the shared primitive and the cutoff constant, per the adopted SEAM_PROTOCOL. The green bar then remembers the boundary — mechanism, not discipline. | TODO |

---

## Phase 3 — WIP graduation (do in parts; each part is independently safe)

`__WORK_IN_PROGRESS__/` is a *staging* name, not an architecture. The package inside it is
green (252 tests). "Work in progress" invites the question *"when does it stop being in
progress?"* — the honest answer is **it already has**. Graduate it. Three mechanical steps,
each a separate MR, none changing behaviour.

| # | Task | Content | Status |
|---|---|---|---|
| 3.1 | **[FILED] TASK-0076 — graduation part 1: promote the package** | `git mv __WORK_IN_PROGRESS__/src/allostery → allostery/` at repo top level, sibling to `backend/`. Update imports + test paths. **No behaviour change; suite must stay 252-green before and after.** Pure `git mv` + import rewrite. | TODO |
| 3.2 | **[FILED] TASK-0077 — graduation part 2: one CI, one green bar** | Single CI workflow runs `backend/` + `allostery/` suites together. Ends the "two test worlds" split and makes the repo-wide bar real (the standards-memo commitment). | TODO |
| 3.3 | **[FILED] TASK-0078 — graduation part 3: dissolve the folder** | Remaining `__WORK_IN_PROGRESS__` contents to their permanent homes (`config/targets.yaml` → `config/`, notebooks → `notebooks/`, planning docs → `documentation/`), then **delete the folder**. Nothing "dangling" remains. | TODO |

End state: `backend/` (service) · `allostery/` (research) · `config/` · `tests/` · one CI.
Two packages, one repo, **no cross-import**, shared primitives kept honest by golden tests.

---

## Phase 4 — Backend test floor

Measured: **`backend/` has 3 tests in 1 file (`geometry` only) across 2,785 LOC.** Nine
modules have **zero** tests, including `analysis.py` (646 lines).

> **Hard rule: 4.1 and 4.2 land BEFORE any Phase-2 code touches `backend/`.** Convergence
> into an untested live service with no golden values is how a deployed app silently changes
> its numbers. Convention 4 ("ADD-only, don't break response shapes") is only *enforceable*
> if a test would catch the break.

| # | Task | Why now | Status |
|---|---|---|---|
| 4.1 | **[EXISTS] TASK-0021** — backend API test baseline | Smoke floor: `/api/health`, `/api/targets`, `/api/load` + the two documented 422s. Converts the standards commitment from *assigned* to *started*. | TODO |
| 4.2 | **[FILED] TASK-0074 — characterization tests for `backend/analysis.py`** | Golden-output tests pinning the **current** live surface (`gnm_context`, `site_potentials`, `quantum_seed_readiness`, `connectivity_change`) *before* convergence touches it. Safety net for TASK-0066. | **Done**. `backend/test_analysis_characterization.py`, 8 tests, real KRAS_G12C network fetch, values pinned 2026-07-12. Confirmed to genuinely land *before* TASK-0066 (not just nominally): re-ran against the unmodified pre-TASK-0066 `analysis.py` via a scoped `git stash`, 8/8 passed identically. Committed as its own, earlier commit. |
| 4.3 | **[EXISTS] TASK-0054** — SE(3) invariance regression test | The metamorphic gauge test, applied to **both** trees. Catches the class of bug unit tests structurally cannot see. | TODO |
| 4.4 | **[EXISTS] TASK-0022** — frontend UI tiered test coverage | After the API floor exists. | TODO |
| 4.5 | **[EXISTS] TASK-0044** — Python version reconciliation | Docs say 3.9 / `typing.Optional`; runtime is **3.11.9**, `biotite` needs ≥3.10. Shared root docs. Cheap — do before the next standards meeting so the stated rules are true. | TODO |

---

## Phase 5 — Advance the research (the scored content)

This is what the submission is actually judged on. Everything above exists to make these
numbers *defensible*; this phase produces them.

> **⚠️ 2026-07-13:** rows 5.2/5.3/5.4/5.6/5.8 below consume or extend 5.1's headline AUCs,
> which [Phase 1B](#phase-1b--proximity-confound--propagator-semantics-correction-blocking-2026-07-13)
> found are confounded by distance-from-seed. Each is annotated **(gated pending Phase
> 1B)** — do not start until TASK-0094 (and, for 5.3, TASK-0095's corrected propagator
> semantics) land. Their own Status stays TODO; the gate is a dependency note, not a
> status change.

| # | Task | Why | Status |
|---|---|---|---|
| 5.1 | **[FILED] TASK-0079 — end-to-end challenge run** (split into **.001–.005** subtasks 2026-07-12) | Produce the three **required deliverables** for every mandatory target (KRAS 4OBE→6OIM, BCR-ABL1 1OPL→5MO4, CARDIAC_MYOSIN; MYC_MAX deferred to TASK-0080): the **N×N connectivity matrix**, the **top-5 ranked hit list**, and the **methodological report**. Currently no single command produces them. This is the submission artifact. | **Done, but headline numbers ⚠️ provisionally confounded — see Phase 1B.** All 5 subtasks landed (`.004` found+filed **TASK-0090**, a real `select.py` multi-index-source crash, worked around not fixed inline). **`.005`'s live run against all 3 mandatory targets is complete** — every deliverable produced and Acceptance-Scenario-checked for real, against live RCSB data. Full narrative in **`__WORK_IN_PROGRESS__/RESULTS.md`**. Headline: KRAS_G12C (AUC 0.779) and CARDIAC_MYOSIN (AUC 0.786, self-flagged `INSUFFICIENT_RESOLUTION`) both scored above this repo's "near chance" expectation, while BCR_ABL1 (AUC 0.525, `NO_SIGNAL_IN_APO`) matched it — except BCR_ABL1's classical heat kernel scored 0.731 on the *same* operator. **REVIEW-2026-07-13 found this pattern (adjacent pockets score well, the one distal pocket is at chance) is the signature of a proximity detector** — none of these AUCs may be reported as allosteric signal until TASK-0094's proximity floor clears them (Phase 1B). Follow-ups reframed: **TASK-0093** (updated, now against the proximity floor), **TASK-0091** (re-filed, dephasing-sweep framing retracted), **TASK-0092** (unaffected, still open). |
| 5.2 | **[FILED] TASK-0082 — competence map synthesis** | The per-target floor / ceiling / headroom table — **the strategic differentiator**. "We close X% of the gap knowing the answer would close, on these targets; ~0 on those, and here is why." A per-target honest NO is a publishable result, not a failure to hide. | TODO **(gated pending Phase 1B — floor/ceiling/headroom numbers are meaningless until proximity-cleared)** |
| 5.3 | **[EXISTS] TASK-0068** — NISQ noise-model simulation | Directly scored ("noise resilience"): Trotterized simulation under gate noise, testing whether ENAQT is more noise-robust than coherent CTQW. Needs `coarse.py` (done) for qubit feasibility. | TODO (claimed by Implementer A, 07-12 00:25 — not yet moved) **(gated pending Phase 1B — built on an unconfirmed headline result)** |
| 5.4 | **[EXISTS] TASK-0015** — holo-direction module | LRT / PRS / two-state ANM / NMFF, gated by cumulative overlap. | TODO **(gated pending Phase 1B)** |
| 5.5 | **[FILED] TASK-0075 — knob-spread reporting for the overlap gate** | Per INVARIANCE_PROTOCOL: cutoff / variant / `k` / reference are **KNOBs, not gauge**. On a toy case the same motion swung **0.067–0.860** across an 18-combo grid, flipping go/no-go in 15 of 18. The gate must emit a **spread** and return `UNSTABLE` when knobs decide the verdict — never a point estimate. | TODO |
| 5.6 | **[EXISTS] TASK-0046** — ceiling coordinate-descent search | Completes the floor/ceiling/headroom triple. | TODO **(gated pending Phase 1B, feeds 5.2)** |
| 5.7 | **[FILED] TASK-0080 — c-Myc / 1NKP application** | Required minimum-set target with **no holo ground truth** — scored on consensus + theoretical docking viability. Needs its own handling: no AUC, no ceiling; report prediction + confidence honestly. | TODO |
| 5.8 | **[FILED] TASK-0081 — generalization set (ASD targets)** | The brief **highly encourages** extra targets to demonstrate robustness/scalability. Pull 2–4 from the Allosteric Database with known sites. Cheap once 5.1 is a one-command run; directly feeds "Technical Approach / Innovation". | TODO **(gated pending Phase 1B — no point generalizing a proximity detector)** |
| 5.9 | **[EXISTS] TASK-0037** — H11/H12 anisotropic not implemented | Known gap in the operator register. | Superseded by **TASK-0096** (Phase 1B.3) — same finding, now with a concrete fix-or-delete task |

---

## Phase 6 — Results delivery: backend + frontend as the research vehicle

The reframing: these are not a lightweight PoC. They **trigger, execute, and show** the
research. The artifact contract is what lets that happen without dragging the research
machinery into the web tier.

| # | Task | Why | Status |
|---|---|---|---|
| 6.1 | **[FILED] TASK-0083 — result artifact contract** ⚠️ **decide EARLY** | Define the versioned artifact `allostery` emits and `backend` consumes: N×N connectivity matrix (NPZ), ranked residues + scores, per-target verdict (GO / NO / **UNSTABLE**) with knob-spread, floor/ceiling/headroom, frozen-config **hash**, provenance. This one decision keeps `backend` free of `allostery` imports and unblocks frontend work **in parallel** with the science. Filed early even though 6.2–6.4 are late. | TODO |
| 6.2 | **[FILED] TASK-0084 — backend results API** | ADD-only endpoints serving precomputed artifacts (`/api/results/{target}`, `/api/connectivity/{target}`, `/api/verdict/{target}`). **No science in the request path** — read, validate against the contract, serve. Respects convention 4 and the Render cold-start budget. | TODO |
| 6.3 | **[FILED] TASK-0085 — frontend research visualization** | The scored "interpretability / 3D visualization" objective: top-5 predicted pockets on the 3Dmol structure, the **N×N connectivity heatmap**, the competence panel (floor / method / ceiling bars), and an explicit **UNSTABLE** state when the knobs decide the verdict. Honesty rendered, not hidden. | TODO |
| 6.4 | **[FILED] TASK-0086 — execution/trigger path** | Decide and implement how a run is launched: offline batch producing artifacts (**preferred** — no compute in the request path, works on free-tier Render) vs. an async job queue. Records the decision; the artifact contract makes either viable. | TODO |

---

## Phase 7 — Deferred / scaffold hygiene (must not displace Phases 0–1)

`TASK-0023` (YAGNI review, IN_PROGRESS) currently exempts the scaffold from its own lens.
Finish it, apply it to the scaffold, and **freeze scaffold-as-product work** — the
lock/registry/packaging/ripeness tooling scores zero on the challenge rubric.

Keep here: 0024.001, 0024.002, 0026, 0026.002, 0026.003, 0026.004 (**In Progress**,
Toolsmith, claimed 07-06 21:14), 0042, 0060, 0061, 0062, 0065, 0069 (claimed by
Implementer B 07-12 00:50, not yet moved).
Cheap, real product cleanups: 0034, 0036, 0038, 0039, **0041** (Haken–Strobl `solve_ivp`
success check — a real robustness bug), 0049. All TODO unless noted otherwise above.

*Not tracked in the Phases 0–6 progress tracker above — this bucket is explicitly
lower priority and must not displace it (see this phase's own heading).*

---

## Task files created from this plan (2026-07-12, commit `9fdeb2f`) — one-liner intents

All 17 below now exist under `.ai/tasks/TODO/` (except TASK-0070, moved to
`.ai/tasks/IN_PROGRESS/` the same session). This section is kept as authorship record;
current status lives in the per-phase tables above and in `.ai/COMMON.md`.

### 2026-07-13 batch — from REVIEW-2026-07-13-proximity-confound-and-propagator-semantics.md

- **TASK-0094 — Proximity baselines into the floor.** `euclid_from_seed_centroid`/
  `hop_from_seed` into `baselines.py`, wired into `floor_scores`/`classify_failure`;
  re-run all mandatory targets. Blocks every current headline number.
- **TASK-0095 — Correct propagator semantics.** Rename `heat`→`ground_state_relaxation`
  (or equivalent), guard against indefinite-operator misuse, correct all downstream framing.
- **TASK-0096 — Delete or implement phantom H11/H12.** Both verified identical to
  H6/unweighted-Laplacian despite docstring claims of anisotropic weighting.
- **TASK-0097 — Name the quantum metric honestly.** `time_averaged_ctqw` is the decoherent
  spectral-overlap limit, not a coherent walk — say so in the report.
- **TASK-0098 — Amend INVARIANCE_PROTOCOL's SIGNAL class.** Must beat the domain's
  strongest trivial confounder (distance-from-seed), not just chance.
- **TASK-0091 (re-filed) / TASK-0093 (updated)** — see Phase 1B above; both hard-blocked
  on TASK-0094 (now Done, unblocked).
- **TASK-0099 (later same day) — wire a coherence metric into the scored verdict.** Filed
  per direct user question after auditing TASK-0097's finding: promote `dephasing_sweep`
  (implemented, tested, never wired into the reported path) into the verdict schema for
  all 3 mandatory targets, checked against TASK-0094's proximity floor, so at least one
  reported number would change under phase randomization.
- **TASK-0100 (Architect decision, Done) / TASK-0101 (follow-up)** — routed to the
  Architect per explicit user instruction ("otherwise I do not understand how we would
  possibly pass the challenge"). Decided: sweep lives as a library fn + thin script, not
  `run_challenge.py`; two-tier rating (descriptive vs. selection, the latter hard-gated
  through LOPO); three operator tiers (A: selection-eligible, B: descriptive-only).
  TASK-0101 executes the Tier-1 harness only.
- **TASK-0101 amended / TASK-0102 (new), same day** — per user direction: TASK-0101 now
  scores every operator through both propagators (not CTQW alone) and must support
  chunked/resumable/parallel runs. TASK-0102 filed to test whether TASK-0091's BCR_ABL1
  finding is genuine active-site coupling or a seed-independent artifact of `H`'s fixed
  ground state — real-data check first, synthetic discriminating network if needed.
  TASK-0099 and TASK-0092 got small clarifying cross-references (ENAQT ≠ ground-state
  question; holo comparison extended to the ground-state propagator, with the caveat that
  holo agreement alone doesn't discriminate a shared static artifact from real signal).

### 2026-07-13(b)/(c) batch — from REVIEW-2026-07-13b (well-vs-coupling falsification) and REVIEW-2026-07-13c (CTQW trapping mechanism)

- **TASK-0103 — Dumbbell 2×2 negative-control test suite.** Permanent, synthetic regression
  test for the well×coupling confound; the test that would have caught 1B.4's causal
  misattribution. No dependency.
- **TASK-0104 — Re-frame the GSR/BCR_ABL1 claim.** `RESULTS.md`/1B.4 corrected from
  "allosteric signal" to "structural prior for cryptic pockets" — number unchanged.
- **TASK-0105 — ENAQT γ-sweep on real targets.** Replaces TASK-0099's pre-review framing;
  measures transport magnitude and interior-γ-optimum shape across `H_new`/`H10`/`H2`, not
  AUC recovery of any one operator.
- **TASK-0106 — Reproduce the CTQW-trapping finding on real BCR_ABL1 data.** The explicit
  real-data gate `REVIEW-2026-07-13c` requires before its synthetic finding (transport
  operators beat `H_new` on a distal pocket) changes any claim.
- **Resequenced**: TASK-0099 now blocked on TASK-0105 (was: unblocked). **Amended**:
  TASK-0101 (1B.10) must report a transport diagnostic (⟨hop⟩/participation ratio), not AUC
  alone; TASK-0093 (1B.5) should read TASK-0106 before finalizing.
- Both review files relocated `__WORK_IN_PROGRESS__/` → `.ai/reviews/`, the established
  home for `REVIEW-*.md` (matches `REVIEW-2026-07-07`/`-07-11`/`-07-12` already there).

**Correctness**
- **TASK-0070 — Pocket label exclusion assembly.** Add the `build_labels` step assembling `pocket & ~functional & ~terminal`, assert `pocket ∩ active_site == ∅`, record an explicit KRAS Cys12 in/out decision, and give the exclusion **one named seam-owner** so it stops falling between `labels`/`protocol`/`analysis`.
- **TASK-0071 — Permutation-null leak detector.** Add a label-permutation null to `diagnostics.py` as the catch-all leakage *detector* backstopping the *preventive* firewall: shuffle labels, re-run, flag any score still above chance.

**Dedup / drift**
- **TASK-0072 — Golden-value cross-tree drift test.** Pin a reference structure and assert `backend/` and `allostery/` produce numerically identical outputs for every shared primitive, so ported code cannot silently diverge again (as 8.0 Å vs 10.0 Å already did).
- **TASK-0073 — Register cross-tree seams.** `.ai/seams/` records (owner + seam-test) for the shared Kirchhoff/DCC primitive and the GNM cutoff constant, so the green bar enforces the boundary mechanically.

**WIP graduation**
- **TASK-0076 — Graduation part 1: promote the package.** `git mv __WORK_IN_PROGRESS__/src/allostery → allostery/` at top level, update imports and test paths; behaviour-neutral, suite green before and after.
- **TASK-0077 — Graduation part 2: one CI, one green bar.** Single workflow running `backend/` and `allostery/` suites together, ending the two-test-worlds split.
- **TASK-0078 — Graduation part 3: dissolve the folder.** Move remaining `__WORK_IN_PROGRESS__` contents to permanent homes (`config/`, `notebooks/`, `documentation/`) and delete the folder.

**Backend floor**
- **TASK-0074 — Characterization tests for `backend/analysis.py`.** Golden-output tests pinning the current live public surface *before* any convergence touches it — the prerequisite safety net for TASK-0066.

**Research**
- **TASK-0079 — End-to-end challenge run.** One command producing, per target, the three required deliverables: N×N connectivity matrix, top-5 ranked hit list, methodological report.
- **TASK-0080 — c-Myc / 1NKP application.** Handle the no-holo-ground-truth target: no AUC/ceiling; emit prediction, consensus rationale, and docking viability with honest confidence.
- **TASK-0081 — Generalization set (ASD targets).** Run the frozen pipeline on 2–4 extra Allosteric-Database targets to evidence robustness and scalability, as the brief encourages.
- **TASK-0082 — Competence map synthesis.** Assemble the per-target floor/ceiling/headroom table into the submission's central claim — the honest per-target competence map.
- **TASK-0075 — Knob-spread reporting for the overlap gate.** Make the cumulative-overlap go/no-go emit a spread across the (cutoff × variant × k × reference) grid and return `UNSTABLE` when modeling choices flip the verdict.

**Delivery**
- **TASK-0083 — Result artifact contract.** Define the versioned artifact `allostery` emits and `backend` consumes (connectivity matrix, ranked hits, verdict + knob-spread, floor/ceiling/headroom, frozen-config hash, provenance) — the decision that lets backend serve research results without importing the research package.
- **TASK-0084 — Backend results API.** ADD-only endpoints serving precomputed artifacts; validate against the contract; **no science in the request path**.
- **TASK-0085 — Frontend research visualization.** 3Dmol top-5 pockets, N×N connectivity heatmap, floor/method/ceiling competence panel, explicit `UNSTABLE` state — the scored interpretability objective.
- **TASK-0086 — Execution/trigger path.** Decide and implement offline-batch (preferred) vs async-job execution so runs are launchable without heavy compute in the web request path.

---

## Critical path to 15 Sept

**0.1 → 0.2 → 1.1 → 1.2 → 5.1 → [1B.1 → 1B.2 → 1B.3 → (1B.4, 1B.5)] → 1B.12 → (1B.14,
1B.15) → 1B.13 → 5.2 → 6.1** — the minimum chain that yields *one leakage-clean,
floor-anchored, mechanism-understood, honestly-reported result*, packaged in the artifact
contract so it can be shown.

**Updated 2026-07-13:** 5.1 is Done, but its output is not yet trustworthy as reported —
Phase 1B is now load-bearing on the critical path, inserted between 5.1 and 5.2. **1B.1
(TASK-0094) is the single highest-priority open task in this plan**: per the review, it
"decides whether we have a result." Do not let Phase 2/3/4 (team-standards track) or the
rest of Phase 5 (5.3/5.4/5.6/5.8, all gated) draw attention away from it.

**Updated 2026-07-13(b)/(c):** 1B.4's own result is now itself gated — its causal claim,
not its number, is under revision. **1B.12 (TASK-0103) and 1B.14 (TASK-0105) have no
dependencies and should run immediately, in parallel** — they are the cheapest, most
falsifiable next steps in the entire plan. 1B.15 (TASK-0106) is the real-data gate before
1B.5/1B.13 can be finalized honestly. 1B.13 (TASK-0104, the `RESULTS.md` correction) is
nearly free and should land as soon as 1B.12 gives it something to cite. None of this
reopens Tier-2 operator selection (TASK-0100) — that gate is unaffected.

**Retraction on record:** earlier guidance (pre-2026-07-13) to prioritize TASK-0091 as
filed is withdrawn — see Phase 1B.4. Its dephasing-sweep framing could not have answered
the question it was built to answer (TASK-0095's finding), and would have produced a
plausible, confidently-wrong causal claim if run as originally scoped.

**Second retraction on record, 2026-07-13(b):** 1B.4's own Done conclusion ("real,
floor-clearing... genuinely distal signal") is likewise not to be read as evidence of
allosteric communication until 1B.13 lands — it is real, floor-clearing evidence of a
*structural prior*, a different and more modest claim. Do not let this row's original
wording propagate into `RESULTS.md` or a submission draft unmodified.

Decide **6.1 (artifact contract) early** even though 6.2–6.4 are late: it is the seam
between research and delivery, and fixing it now lets the frontend and the science advance
in parallel instead of serially. This is unaffected by the 2026-07-13 correction — the
artifact contract's shape (GO/NO/UNSTABLE + knob-spread) already accommodates "this AUC is
geometry, not signal" as a reportable outcome.

Phase 2/3/4 (dedup, graduation, backend floor) is the **team-standards** track — real, and
the cutoff divergence makes it a *correctness* issue rather than hygiene — but it must not
preempt the Phase 0–1 chain, and now must not preempt Phase 1B either, if time gets short.
