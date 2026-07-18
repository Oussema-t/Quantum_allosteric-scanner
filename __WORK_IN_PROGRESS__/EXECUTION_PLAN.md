# Execution Plan — sequenced, mapped to task IDs

State verified on the `bartosz` branch snapshot: **252 tests passing, 0 real failures**;
all science stubs implemented (`baselines` 180, `coarse` 260, `pathways` 174, `viz` 365);
seam + invariance protocols adopted (TASK-0050/0051); no `w[6:]` index-slicing bug in the
physics core. Ordering is by **dependency and risk**, not task number.

Legend: **[EXISTS]** = filed before this plan · **[FILED]** = created *from* this plan
(TASK-0070–0086, all 17 filed 2026-07-12, commit `9fdeb2f`) — no `[NEW]` remains outstanding.

## ⚠️ 2026-07-16 correction — supersedes Phase 1B's own headline reversals; read this first

`.ai/reviews/REVIEW-panel-2026-07-16-v2.md` (multidisciplinary panel, reconciling two
adversarial reviews of Phase 1B's own conclusions) found that **every current
floor/ceiling/actual number is gauge-contaminated by three unfixed physical units**, and
neither the existing negative claim ("KRAS is a proximity detector," "ceiling below floor")
nor a competing positive claim floated by another thread ("+0.042 headroom") is supported —
both splice numbers across incompatible conventions. The three unfixed units:

1. **The seed** — `run_challenge.py` uses a single residue (a TASK-0090 crash workaround);
   `ceiling_search_batched.py` uses the full active-site array. Worth ≈±0.3 AUC on real
   data (KRAS: 0.78 scalar vs. 0.45 array), and it moves the *floor* together with the
   *score* — collapsing the site to one point manufactures the very proximity confound it
   appears to reveal. **No `INV-XXXX` record owns this.**
2. **The clock** — `t_max=15` is applied identically to every operator regardless of energy
   scale; at that t, even a disorder-free walk has barely left the seed.
3. **The potential's scale** — the five diagonal terms are not commensurate (`V_R`=88.8% of
   variance, `V_C`/`V_M`=0.1% each) — a normalization bug, not a modeling choice.

**Independently, and more fundamentally**: the panel's own executed check shows a bare,
disorder-free normalized Laplacian seeded at one residue correlates with distance-from-seed
at ρ=+0.83 and never drops below ~0.5 at *any* propagation time. **No Hamiltonian in this
register can clear a proximity floor while the scored quantity is "occupation seeded at the
active site" — the fix is a different observable, not a better operator.**

**New blocking phase inserted below: [Phase 1C](#phase-1c--panel-review-v2-gauge-fixes--observable-correction-blocking-2026-07-16).**
It supersedes Phase 1B's own headline framing wherever the two disagree (see each Phase 1C
row for the specific correction) and gates every floor/ceiling/actual number in
`COMPETENCE_MAP.md`/`RESULTS.md` until the P0 items land. Tasks filed: **TASK-0118–0127**
(10 new), plus **TASK-0090 escalated to P0** (root cause of the seed confound) and
**TASK-0106 flagged** (a backwards PR-direction narrative bug in its own Done section, not
yet re-derived). Full detail, evidence, and priority ordering: `.ai/reviews/REVIEW-panel-2026-07-16-v2.md`.

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

## Progress tracker (Phases 0–6 + 1B + 1C, the scored/critical-path work — 82 IDs referenced)

**Reconciled 2026-07-17** (Architect/Planner status review) by cross-checking every
`TASK-00xx` ID referenced anywhere in the phase tables below against its actual location in
`.ai/tasks/{DONE,TODO,IN_PROGRESS}/` (script-verified, not hand-counted) — supersedes the
2026-07-16 snapshot. Since that snapshot: **TASK-0108 landed Done** (the parent/coordinator
task closed once both its subtasks, TASK-0109/0110, landed); **TASK-0129/0130 filed**
(combined seed+clock re-run; `time_averaged_ctqw` convergence-infeasibility fix). `.ai/COMMON.md`'s
Active Work Registry remains the canonical, continuously-updated source — re-check there
(or re-run the cross-check) before trusting this table for dispatch decisions; it will
drift again as soon as the next task lands.

| Done | In Progress | TODO | Total distinct IDs referenced |
|---|---|---|---|
| 52 (TASK-0004, 0005, 0018, 0037, 0046, 0047, 0050, 0052, 0055, 0056, 0058, 0063, 0064, 0066, 0067, 0068, 0070, 0071, 0074, 0075, 0079, 0080, 0081, 0082, 0088, 0090, 0091, 0092, 0093, 0094, 0095, 0096, 0097, 0099, 0100, 0101, 0102, 0103, 0104, 0105, 0106, 0108, 0109, 0110, 0112, 0118, 0119, 0120, 0121, 0125, 0128, 0129) | 1 (TASK-0023) | 29 (TASK-0015, 0021, 0022, 0040, 0044, 0054, 0072, 0073, 0076, 0077, 0078, 0083, 0084, 0085, 0086, 0087, 0089, 0098, 0113, 0114, 0115, 0116, 0117, 0122, 0123, 0124, 0126, 0127, 0130) | 82 |

**Note on the growing total:** the plan's scope keeps genuinely growing, not drifting —
Phase 1B added ~20 IDs (TASK-0091–0106), the 2026-07-15 gap audits added TASK-0108–0117,
Phase 1C (2026-07-16) added TASK-0118–0127, and the same day's TASK-0099/TASK-0090 work
added TASK-0128. TASK-0004/0018/0037/0050/0088 are referenced in prose (superseded-by
notes, architectural-premise citations) rather than owning a distinct live Status cell of
their own; TASK-0090 now owns 1C.1's Status cell directly (Done). Included above for
completeness of the cross-check, not because they're all separate rows.

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
| 1B.5 | **[UPDATED] TASK-0093 — KRAS AUC reconciliation, now against the proximity floor** | The 8.0 vs 10.0 Å cutoff changes the contact graph's distance-decay from the seed — a candidate mechanism for the AUC gap that has nothing to do with real allosteric sensitivity. Every factorial combination must now be checked against 1B.1's floor, not just chance. **Hard blocked on 1B.1 — now Done, unblocked.** | **Done.** Full 2×2×2 factorial (cutoff × pocket-label × source), read against TASK-0106's real-data result as planned. **Zero of 8 combinations clear the proximity floor** — including the real run's own headline 0.7792 (floor 0.7976, margin -0.018). **New dominant driver found, not one of the 3 originally-scoped variables**: seed cardinality (full active-site array vs. `run_challenge.py`'s single-index workaround) swings AUC from ~0.44-0.53 to ~0.78-0.82 on its own — bigger than the cutoff/pocket-label/frame axes this task was filed to test. See `physics.md`'s new cross-cutting seed-gauge finding. |
| 1B.6 | **[FILED] TASK-0097 — name the "quantum metric" honestly** | `time_averaged_ctqw` is the decoherent/infinite-time-average limit (a spectral overlap quantity), not a coherent walk. Reporting honesty; can run in parallel with 1B.7 once 1B.1–1B.3 land. | **Done** (commit `bc41f09`). `[NOTE]` disclosure added to `verdict_template` before any AUC renders; second methodology paragraph added to `RESULTS.md`; 3 new tests including a durable `RESULTS.md`-content check. |
| 1B.7 | **[FILED] TASK-0098 — amend INVARIANCE_PROTOCOL's SIGNAL class** | Protocol-level generalization: SIGNAL must beat the domain's strongest trivial confounder (distance-from-seed here), not just chance. Third instance of the same unexecuted-gauge-symmetry pattern (after SE(3) rotation, SU(2)/Clifford-frame) — see the review's Meta section. Can run in parallel with 1B.6. | TODO |
| 1B.8 | **[FILED] TASK-0099 — wire a genuine coherence metric into the scored verdict** | Audit (2026-07-13, prompted by a direct user question against 1B.6's finding) confirmed: **nothing phase-dependent currently reaches any reported AUC.** `ctqw`/`haken_strobl` are correctly implemented, real quantum evolutions — but every scored number traces only to `time_averaged_ctqw`/`ground_state_relaxation`, both phase-averaged. `dephasing_sweep` exists, is tested, and has **zero call sites** in the reported pipeline. Promote it (calibrated γ, all 3 mandatory targets, checked against 1B.1's floor) so at least one reported number would change under phase randomization. **Hard blocked on 1B.1 — now Done, unblocked.** | **Done, 2026-07-16.** `analysis.coherence_sensitivity` wired into `assemble_verdict_results`/`verdict_template` (3 new headline keys + a decision-support prose line). Real 3-target attempt: **KRAS_G12C** — flat sweep (`auc_range`=0.0155), doesn't even clear chance → `COHERENCE_NOT_SIGNIFICANT`, cross-checked under a second independent source convention. **BCR_ABL1/CARDIAC_MYOSIN — blocked, not silently skipped**: `calibrate_kappa`/`anm_modes` require exactly 6 rigid-body ANM modes; BCR_ABL1 has 7, CARDIAC_MYOSIN has 10 — both raise. TASK-0005 had already predicted this exact failure mode for multi-chain/floppy-linker targets; now actually hit. Filed **[[TASK-0128]]** to resolve the root cause. **TASK-0128 Done, 2026-07-18**: root cause was neither disconnection nor numerical noise — both targets' extra eigenvalues sit at true machine-precision zero then jump 5-9 orders of magnitude to the real spectrum, localized to a small compact residue segment each (the known central-force-ANM under-constrained-substructure artifact). Widened `n_zero!=6` → `n_zero>=6` + a connectivity check (disconnected case still raises). BCR_ABL1 re-run: fully unblocked, matches KRAS's `COHERENCE_NOT_SIGNIFICANT` exactly — **2/3 mandatory targets now confirm this project's coherence-adds-nothing finding, not 1/3.** CARDIAC_MYOSIN's calibration unblocked; full sweep still not-run for a separate, pre-existing `haken_strobl` cost reason. |
| 1B.9 | **[FILED] TASK-0100 — decide the operator-sweep architecture** (Architect decision) | We have 14 named operators (1B.3 added `H14`) but no harness ever runs more than 2 (`H_new`/`H10`) against a real target. Routed to the Architect per explicit user instruction — "otherwise I do not understand how we would possibly pass the challenge." | **Done.** Decided: library fn `analysis.operator_sweep` + thin `scripts/sweep_operators.py`, **not** `run_challenge.py` (keeps the submission orchestrator a reported decision, not a search — same line already drawn for TASK-0046). Two-tier rating: **Tier 1** (descriptive — floor-cleared + AUC + apo/holo consistency, no frozen-gate) vs. **Tier 2** (selection — replacing `H_new`/`H10` as submission operator — hard-gated through `select_frozen_config`/`leave_one_protein_out`, N=3 flagged as thin). Three operator tiers: **A** (`H_new`, `H10`, `H14` — selection-eligible) vs. **B** (`H1`-`H9`, `H11`-`H13` — descriptive-only, never intended as submission candidates). Floor-failing operators recorded, not deleted (Tier A failing all 3 targets disqualifies it from Tier 2; Tier B failing is just recorded context). **Resequencing resolved**: TASK-0091/TASK-0093/TASK-0099 confirmed NOT blocked — none is an operator-selection act, all diagnose the already-chosen `H_new`. **Follow-up 2026-07-15:** this decision's Tier-2 gate stops code-level multiple-comparisons abuse; it can't gate the ~15 human review cycles this project has already run against the same 3 targets — see TASK-0115, complementary to this gate, not a duplicate. |
| 1B.10 | **[FILED] TASK-0101 — operator sweep Tier-1 harness** | Executes 1B.9's decision: `analysis.operator_sweep` + `scripts/sweep_operators.py`, all 14+2 operators × 3 mandatory targets, Tier-1 (descriptive) only — no operator selection. **Amended 2026-07-13**: scores each operator through **both** `time_averaged_ctqw` and `ground_state_relaxation` (16 ops × 2 propagators × 3 targets = 96 cells, per 1B.4's finding that propagator choice — not just operator choice — was what separated BCR_ABL1's chance and floor-clearing results) — and must run **in chunkable, resumable, parallelizable parts** (`--target`/`--operator`/`--propagator` filters, per-cell files, `--force` to recompute one suspicious cell, `--aggregate` to merge partial runs from multiple machines). | **Done.** Real 96-cell sweep complete (KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN). Found+fixed a real bug in `operator_sweep`: `classify_failure` was called without `H`/`bfactors`, silently disabling `OPERATOR_DEGENERATE`/`INSUFFICIENT_RESOLUTION` for every cell. Separately, **2026-07-15**: `LARGE_N_THRESHOLD=800` (in effect for the first full sweep) was found to have no derivation anywhere in its cited notebook source and was corrected to 1000 per explicit user direction (full account: `diagnostics.py`'s own comment). Both fixes force-recomputed together. **Register-wide finding**: 20 of 96 cells clear TASK-0094's proximity floor, 11 of them via `ctqw` — all 11 on CARDIAC_MYOSIN (`H2`/`H3`/`H4`/`H5`/`H6`/`H8`/`H10`/`H11`/`H12`/`H_new`/`build_H10`, all `NO_FAILURE_DETECTED`); the other 9 floor-clears (KRAS_G12C 2 + BCR_ABL1 4 + CARDIAC_MYOSIN's remaining 3) are all `ground_state`. Whether `REVIEW-2026-07-13c`'s CTQW-trapping mechanism still explains CARDIAC_MYOSIN's many ctqw floor-clears (vs. KRAS/BCR_ABL1's zero) is unresolved — flagged, not answered, by this task. `H14` never clears the floor anywhere (real negative result, recorded not dropped). Tier-2 selection explicitly not attempted, per this task's own scope. Full detail: `.ai/tasks/DONE/TASK-0101-operator-sweep-tier1-harness.md`, `RESULTS.md`'s CARDIAC_MYOSIN section. |
| 1B.11 | **[FILED] TASK-0102 — is 1B.4's finding seed-dependent, or a fixed-minimum artifact?** | User's question, 2026-07-13: does `ground_state_relaxation` genuinely couple to the seed, or does `exp(-Ht)` at `t_max=15` simply converge to `H`'s global ground state regardless of source — meaning "the minimum has to be somewhere, and on BCR_ABL1 it happens to sit nearer the pocket"? Real-data seed-invariance check first (cheap, reuses 1B.4's cached data), then a synthetic discriminating network (engineered minimum away-from vs. coupled-to a "drug site") if needed. Not blocking, but 1B.10's ground-state column should be read alongside this task's finding. | **Done.** Genuinely mixed evidence, resolved to a clear practical answer: a 6-seed correlation check shows real seeds *do* produce different occupation shapes (rules out literal seed-independence), but a broader 40-seed sample shows 70-75% of arbitrary, biologically-uninformed seeds clear the proximity floor and land within 0.02 of the real active site's own AUC (0.7315) — the score is dominated by `H_new`'s fixed ground-state shape (94.5% of relative weight at `t_max=15`), not active-site-specific coupling. **TASK-0091's 0.7315 must not be read as confirmed allosteric signal.** Synthetic discriminating network (part c) not built — not needed, per this task's own "build only if ambiguous" constraint. |
| 1B.12 | **[FILED] TASK-0103 — dumbbell 2×2 negative-control test suite** | Permanent, synthetic (no PDB/network) regression test implementing `REVIEW-2026-07-13b`'s well×coupling control matrix — the test that would have caught 1B.4's causal misattribution. Asserts `ground_state_relaxation` follows the well, `ctqw`/transport follows the coupling. **No dependency — start anytime.** | **Done.** `test_dumbbell_negative_control.py`, 10 tests. Reproduced the review's decisive double dissociation cleanly (C2: GSR=0.000/CTQW=1.000; C3: GSR=1.000/CTQW=0.000, 5 seeds each). Found and fixed a real bug in the first prototype (deterministic construction silently averaged 5 identical "seeds") before locking in assertions. Registered as the reusable harness (`build_dumbbell_network`/`auc_to_drug`, public) for future falsification tasks. |
| 1B.13 | **[FILED] TASK-0104 — re-frame the GSR/BCR_ABL1 claim** | `RESULTS.md`/1B.4's text currently frames 0.7315 as (diffuse) allosteric signal. Correct to "apo-computable structural prior for cryptic pockets," citing TASK-0103's evidence. **Number unchanged, claim corrected — cheap.** | **Done.** `RESULTS.md` corrected additively (TASK-0095/TASK-0102's prior corrections left standing, per that doc's own no-overwrite convention) — new block cites `REVIEW-2026-07-13b`'s dumbbell control matrix and TASK-0103's now-passing regression test by name, states the corrected claim verbatim ("apo-computable structural prior... detectable without reference to the active site"), records the operator-register verdict (`ground_state_relaxation` = RETAINED-NARROWED). TASK-0091's hit-list-diffuseness finding confirmed preserved, not deleted. Also fixed one stray pre-rename "heat" mention in the CARDIAC_MYOSIN section. No code/analysis re-run, per this task's own Constraint. |
| 1B.14 | **[FILED] TASK-0105 — ENAQT γ-sweep on real targets** | Replaces the killed dephasing question underneath TASK-0099 (1B.8). Measure transport magnitude vs. γ ∈ [10⁻⁴, 10²] on all 3 mandatory targets; report interior-optimum presence and enhancement ratio over the coherent walk, not AUC recovery. Per `REVIEW-2026-07-13c`, sweep across `H_new`/`H10`/`H2` — not `H_new` alone, or a null result may reflect that operator's own transport localization rather than an absence of ENAQT. **"The single highest scientific upside in the repo" per the review. No dependency — start anytime.** | **Done.** Real 3-target sweep (reduced grid on BCR_ABL1, γ=0 anchor only on CARDIAC_MYOSIN — `haken_strobl`'s ~N³ cost makes a full sweep there infeasible this session, reported not hidden). Interior-γ transport optimum genuinely reproduces on real protein topology (3 of 6 cells, 1.24-1.7x enhancement over coherent). **But AUC-at-γ* is lower than AUC-at-γ→0 in every one of those cells** — the transport gain never translates into better pocket discrimination on any real target tested. Refines HYP-P7 (`physics.md`): coherence measurably matters for transport, not (yet, anywhere) for pocket-finding. |
| 1B.15 | **[FILED] TASK-0106 — reproduce the CTQW-trapping finding on real BCR_ABL1 data** | `REVIEW-2026-07-13c`'s synthetic finding (transport-preserving operators beat `H_new` on a distal pocket by a wide margin) is a mechanism test only — this task is the real-data gate the review requires before it changes any claim. Predicts `H10`/`H2`/`H_new`(reduced λ) beat `H_new`'s recorded 0.525 on BCR_ABL1 and clear its 0.565 floor. Tier-1 descriptive only, per TASK-0100 — does not itself justify reselecting the submission operator. | **Done.** Trapping mechanism reproduces cleanly on real data (`H_new`'s participation-ratio 5-6x lower than `H10`/`H2`, ⟨hop⟩ a quarter of theirs), confirmed in both seed conventions. The predicted AUC consequence reproduces **only for `H10`** (0.558 > 0.525, now confirmed real not noise) — not for `H2` or reduced-λ `H_new` (both scored lower, opposite the review's prediction). **None of the 4 operators clear the real proximity floor (0.565).** Verdict: mixed, reported as such. **Real seed-convention finding, not anticipated when filed**: the full active-site array (vs. `run_challenge.py`'s single-index convention) flips `H_new` from lowest- to highest-scoring of the four operators (0.567) — first place this GAUGE choice visibly flipped a sign; see `physics.md`. |

**Non-finding, recorded so it isn't re-litigated:** the review also tested whether
ground-state localization (`heat`) is *immune* to the proximity confound, as an external
reviewer had proposed. It is **not** — `heat`'s synthetic distal-pocket AUC is 0.048, as
anti-correlated as CTQW's 0.035. BCR_ABL1's real 0.731 remains a genuine, unexplained
result that 1B.4 must test, not an already-proven exception.

---

## Phase 1C — Panel review v2: gauge fixes + observable correction (BLOCKING, 2026-07-16)

Inserted after `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` reconciled two adversarial
reviews of Phase 1B's own conclusions and found the seed/clock/potential-scale gauges
unfixed underneath every headline number. **This phase supersedes Phase 1B's own framing
wherever the two disagree** (each row states the correction) and gates every
floor/ceiling/actual number until the P0 rows land. Sequencing follows the review's own §5
priority ordering (P0 → P1 → P2) — do not reorder without a stated reason.

| # | Task | Why in this order | Status |
|---|---|---|---|
| 1C.1 | **[ESCALATED] TASK-0090 — fix `select.py`'s multi-index crash** | Root cause of the seed confound: `run_challenge.py`'s single-residue seed exists *because* of this bug. Hard-blocks 1C.2. Escalated from ordinary backlog to P0 by the panel review — do not defer further. | **Done (2026-07-16).** Fixed `_hop_distances_from_source` (multi-source BFS; was silently *wrong*, not crashing) and `source_specificity`'s `others` exclusion set (the actual crash site — this task's own Intent Contract had wrongly marked that function "already correct", checked by execution and fixed anyway). Real KRAS_G12C validation: full 18-residue active-site array through `unsupervised_score`, no crash, finite differentiated scores. `run_challenge.py`'s workaround itself intentionally left in place — removing it is 1C.2's job, not duplicated here. |
| 1C.2 | **[FILED] TASK-0118 — fix the seed gauge; register invariant; re-run floor/ceiling/actual** | The panel's #1 priority. Single vs. array seeding: occupation Spearman only 0.61, real KRAS swing 0.78→0.45. **Retracts "ceiling below floor" as `undetermined→recomputed`, not a new positive** — the competing "+0.042 headroom" claim splices two different runs and is equally unsupported. Corrects `COMPETENCE_MAP.md` directly. | **Done (2026-07-16).** Declared convention: full active-site array, incoherent mixture (`propagators.ctqw`'s new `coherent=False`) — real sweep confirmed KNOB not GAUGE (KRAS_G12C AUC spread 0.326, [[INV-0006]]). Re-ran floor/ceiling/actual all 3 targets: KRAS_G12C ceiling now clears floor (+0.045, retracting "ceiling below floor"); BCR_ABL1 unchanged shape; CARDIAC_MYOSIN actual now clears floor too (+75.1%) but confounded by an unrelated `LARGE_N_THRESHOLD` change and still gated on [[TASK-0124]]'s 5TBY data-quality question. `COMPETENCE_MAP.md` fully recomputed, old numbers preserved not deleted. |
| 1C.3 | **[FILED] TASK-0119 — fix the clock: per-operator `t*` from spectral gap** | `t_max=15` isn't comparable across operators and is too short (disorder-free walk still concentrated near seed, PR≈9/169). **Corrects Phase 1B's/REVIEW-13c's own trapping claim in the other direction**: the panel's gauge-fixed re-run shows `H_new`'s localization is real and survives (PR 1.3→3.8 vs. bare Laplacian's 14.7→83.7) — not a units artifact as an adversarial review argued. Also fixes a backwards PR-direction narrative bug in TASK-0106's own Done section. | **Done.** `t*=-ln(tol)/gap` (TASK-0109's `min_adequate_t_max`), re-ran TASK-0101's 96-cell sweep + TASK-0106's BCR_ABL1 reproduction. Found+fixed a real MemoryError (n_steps blew up to 3.1B on a near-degenerate gap, capped at 5000). **Two separate findings, not merged**: (a) ranking shift — most of CARDIAC_MYOSIN's `ctqw` floor-clears do NOT survive (narrows TASK-0109's "20/96, 11 via ctqw" headline down to essentially `H_new`/`H10`/`build_H10` only); BCR_ABL1 gains 3 new floor-clears. (b) localization survives — `H_new`'s `ipr` stays ~6-10x `H10`/`H2`'s even at each operator's own proper `t*`, confirming the panel's own re-measurement, not a clock artifact. **Also resolved, not just flagged**: TASK-0106's PR-direction question — the panel's own "backwards" correction was itself mistaken (conflated `metrics.ipr` with `analysis._transport_participation_ratio`, verified-opposite conventions, new regression test `test_transport_diagnostics_convention.py`); TASK-0106's original narrative was correct for the metric it actually used. **Caveat**: computed under the pre-TASK-0118 single-scalar seed (TASK-0118 landed, uncommitted, mid-task) — a further re-run under both fixes combined is still needed before either is submission-final. |
| 1C.4 | **[FILED] TASK-0120 — learnability gate (HYP-P8)** | "The highest information-per-hour experiment available" per the panel — Kabsch + RMSD + Tama-Sanejouand overlap, one afternoon, no quantum, no dependency. If KRAS's Switch-II pocket proves largely absent from apo topology, that reframes the whole submission as a finding rather than a failure. **Run regardless of 1C.2/1C.3's outcome — do not sequence behind them.** | **Done.** New `superpose.background_rmsd`/`learnability_verdict`. **Result contradicts the panel's own prediction for KRAS_G12C**: pocket RMSD is real (2.27x background) but cumulative overlap (0.638) is well above the 0.5 low-overlap bar — the apo→holo direction *is* spanned by the soft ANM modes, so KRAS classifies `LEARNABLE`, not cryptic-structural. Does not conflict with the panel's separate Switch-II/active-site-overlap point (different claim, same target). BCR_ABL1's pocket moves *less* than background (ratio 0.49) — consistent with its "structural prior" framing (TASK-0104). **Update 2026-07-18, TASK-0128's fix to the shared `anm_modes` helper also unblocked CO for the other 2 targets**: BCR_ABL1 CO(20)=0.794, CARDIAC_MYOSIN CO(20)=0.584 — both above the 0.5 bar, both independently confirm `LEARNABLE` (their RMSD ratios, 0.49/1.32, already implied it). All 3 mandatory targets now have complete RMSD+CO numbers, all classify `LEARNABLE`. Full detail: `RESULTS.md`'s "Learnability gate" section. |
| 1C.5 | **[EXISTS] TASK-0112 — wire `block_bootstrap_ci` into every headline AUC** | Panel P0-4. Every reversal this week (0.779/0.798, 0.525/0.565, ceiling/floor) is a bare point estimate on 16-21 positives; expect several to become "indistinguishable," which is more defensible than a false precision. | **Done.** `diagnostics.classify_failure(return_ci=True)` (new `FailureClassification`, default path byte-identical) + `verdict_template` rendering. Real re-run, all 3 named comparisons, same `T_MAX=15.0` as the original numbers: KRAS_G12C 0.779 [0.594,0.932] vs floor 0.798 [0.637,0.936]; BCR_ABL1 ctqw 0.525 [0.325,0.684] vs floor 0.565 [0.425,0.697]; BCR_ABL1 ground_state 0.731 [0.556,0.866] vs floor 0.565 [0.425,0.697]. **All three overlap** — the panel's own prediction confirmed, including BCR_ABL1 GSR's previously "decisive +0.166" margin. Categories unchanged (point-estimate taxonomy preserved per this task's own Constraint); `RESULTS.md` corrected additively at both sites. |
| 1C.6 | **[FILED] TASK-0121 — renormalize the 5-term potential** | `V_R`=88.8% of variance, `V_C`/`V_M`=0.1% each — a normalization bug, not physics. Retro-explains 3 previously-reported "findings" (`most_impactful_term=V_R`, ground state on low-diagonal residues, failure to beat degree centrality). **Distinct from the proximity confound** (occupation↔degree ρ=only 0.20) — this fix alone will not resolve 1C.2/1C.8. | **Done (2026-07-18).** All 5 terms in `potentials.py` z-scored (mean 0, std 1); `build_H_new` `lam_*` re-derived to `0.08/0.16/0.08/0.04/0.04` (same 1:2:1:0.5:0.5 ratio) so `sigma(V) <= 0.2*J` provably holds on any target (Minkowski triangle inequality, `J<=2` universal). Real-data confirmation (KRAS_G12C, BCR_ABL1): variance share now 15.4%/61.5%/15.4%/3.8%/3.8% (V_C/V_M up 38x from 0.1%); `H_new` still correctly indefinite on both. Re-ran `analysis.ablation`: `most_impactful_term` flips `V_R`→**`V_B`** on both targets, `V_R` now among the *least* impactful — confirms the old finding was the scale bug, not physics. Side-measurement: the renormalization also measurably weakens (not eliminates) the separate proximity confound (ρ_euclid 0.71-0.83→0.22-0.47) — flagged, not claimed as fixing 1C.2/1C.8. Full numbers: `RESULTS.md`'s TASK-0121 section. |
| 1C.7 | **[FILED] TASK-0122 — build `mode_coparticipation`** | Proposed by REVIEW-13b §6, never built. Least-confounded observable on a *clean* Laplacian (\|ρ\|≈0.18) but *worse* than CTQW on the current disordered `H_new` (\|ρ\|≈0.50). **Hard blocked on 1C.6** — do not build/evaluate before the potential is renormalized. | TODO |
| 1C.8 | **[FILED] TASK-0123 — distance-stratified evaluation** | Whole-graph AUC structurally cannot distinguish "found the pocket" from "found distance" (§2.3's own table: ρ(occ,−dist) never below ~0.5 at any t). Distance-matched-decoy AUC is the only way a real signal inside a confounded shell becomes visible. No dependency, can start immediately. | TODO |
| 1C.9 | **[FILED] TASK-0124 — re-anchor or retire CARDIAC_MYOSIN** | The only current positive (0.786, floor-cleared) rests on 5TBY — a 20 Å docked homology model with non-crystallographic B-factors and unverified chain assignment. If it doesn't survive scrutiny, the submission currently has **zero** clean positives across all 3 mandatory targets. | TODO |
| 1C.10 | **[FILED] TASK-0126 — H13 (or its N×N projection) through the ceiling search** | `.claude/hypotheses/ceiling.md`'s own "minimum set" calls this required; TASK-0046 never ran it. Independently flagged by this Architect/Planner thread the same day, before the panel review confirmed it. | TODO |
| 1C.11 | **[FILED] TASK-0127 — extend the ASD generalization set; make it the reported headline** | Mitigates ~15 human review cycles over the same 3 answer keys — `frozen_context` gates code-level multiple comparisons, nothing gates the reviewers. **Soft-blocked on 1C.2/1C.3/1C.6** — running this against a still-gauge-contaminated pipeline just reproduces the same undetermined state on more targets. | **Done (2026-07-18).** All 3 blockers (1C.2/1C.3/1C.6) landed. Extended the set from 2 to 4: verified 2 new targets (CASPASE1, same dimer-interface mechanism as CASPASE7; GLUCOKINASE, required a real `apo_chains`/`holo_chains` schema fix to `clean_from_config`, resolving `Q-0001`), checked 4 more candidates and found real, substantive reasons each fails (not backfilled). Re-ran PTP1B/CASPASE7 under the current fully-fixed pipeline (their TASK-0081 numbers predated all 3 gauge fixes). All 4: `BEATS_CHANCE_NOT_FLOOR`, overlapping score/floor CIs, `most_impactful_term` never `V_R` (independent cross-check of TASK-0121). `RESULTS.md` restructured: new reading-order note at the top points to the generalization set as headline evidence; new dated section with the full 4-target table. Ceiling intentionally deferred for all 4 -- `ceiling.py::_PARAM_RANGES` is still pre-TASK-0121-scale (TASK-0116's scope, not fixed here). |
| 1C.12 | **[FILED] TASK-0125 — verify c-Myc/1NKP resnum numbering** | `keep_nucleic: true` risks the hit list silently reporting DNA nucleotide indices as residues — cheap check, real reputational risk if wrong ("a referee will spot 'residue 943' instantly"). | **Done (2026-07-18).** Verified — no bug. Two independent checks (production `clean_from_config` pipeline trace + raw `prody.parsePDB('1NKP')` cross-check, new `scripts/verify_cmyc_resnums.py`) confirm all 5 hit-list residues are real amino acids with correct native 1NKP numbering, zero DNA leakage. Secondary finding, not pursued: `keep_nucleic: true` is a no-op for MYC_MAX specifically — `chains: ["A","B"]` already excludes the DNA chains regardless, so the conflation risk this task checks for structurally can't occur here. |
| 1C.13 | **[EXISTS] TASK-0054 — SE(3) invariance regression** | Panel P2-12, re-affirmed as still relevant alongside the other gauge fixes. | TODO |
| 1C.14 | **[FILED] TASK-0129 — combined seed+clock re-run** | 1C.2 (TASK-0118) and 1C.3 (TASK-0119) landed independently, same day, neither combined with the other — every number either reports is fixed on only one axis. **Now the single highest-priority open item**: neither `COMPETENCE_MAP.md` recompute is the pipeline's actual current state until this lands. **Hard unblocked** — both dependencies Done. | **Done (2026-07-18).** Extended `fix_clock_operator_sweep.py` in place; new `combined_competence_map_rerun.py`; added `coherent` to `analysis.operator_sweep`. **Headline: CARDIAC_MYOSIN's TASK-0118-only positive (+75.1% headroom) does not survive the clock fix** — combined actual AUC 0.7912 lands 0.0009 below its own floor (cross-validated via 2 independent code paths). No mandatory target's shipped actual clears its own floor under the fully corrected convention; real ceiling headroom exists for all three, reached by none. Flagged not resolved: tension with TASK-0110's BCR_ABL1 short-`t_max` finding (0.5829 at `t_max=2.39`, better than either convergence-motivated `t*`), and a spectral-gap reproducibility discrepancy vs TASK-0119's own recorded BCR_ABL1 value. `COMPETENCE_MAP.md` fully recomputed (2nd SUPERSEDED layer, old numbers preserved). |
| 1C.15 | **[FILED] TASK-0130 — `time_averaged_ctqw`'s own convergence criterion is computationally infeasible** | TASK-0110 found `min_adequate_t_max(kind="time_averaged_ctqw")` prescribes `n_steps` in the millions on all 3 real targets — a single call didn't return after 2+ hours. Fix: compute the infinite-time closed form directly (already known to match at Spearman 0.9998) instead of chasing a bigger practical cap. Not blocking 1C.14. | TODO |

**Scaffold hygiene found and fixed while reconciling this phase, 2026-07-16/17**: two
concurrent threads (TASK-0099, TASK-0109) both claimed `INV-0005` for unrelated invariants.
Renumbered TASK-0099's file to `INV-0007` (the propagator-time-parameters one already had
more cross-references by full filename); fixed the two bare-`INV-0005` mentions that meant
it (`.ai/COMMON.md`, `.ai/memory/shared/pitfalls.md`). No content changed.

**[[Q-0003]] formally closed** (was left open pending this Architect/Planner call, per
TASK-0118's own Done section): the floor/ceiling/headroom framing was never the problem —
the negative-denominator symptom correctly surfaced the seed-convention mismatch, not a
flaw in the framework itself. Full closure text in `.ai/memory/questions/architect-planner/answered/`.

**What this phase explicitly does NOT conclude (per the review's own corrections, do not
re-litigate)**: `mode_coparticipation` does not work as a standalone fix (1C.7 depends on
1C.6); potential renormalization does not by itself fix the proximity confound (1C.6 ≠
1C.8); the CTQW-trapping mechanism is real and gauge-robust, not a clock artifact (1C.3
corrects the *comparison*, not the *localization finding*); and fixing the seed gauge
produces `undetermined`, not a new positive (1C.2's own scope explicitly forbids reporting
a "+0.042" style claim).

**Strengths the panel confirmed independently worth foregrounding in the submission,
not fixing**: the falsification apparatus itself (proximity floor, dumbbell matrix,
permutation null, GAUGE/KNOB/SIGNAL protocol) generalizes past this challenge and is the
actual Innovation claim; the 6C1H validation-table correction (proof the challenge's own
Table 1 lacks mavacamten) is currently "buried in a YAML comment" and should be promoted to
a headline in `RESULTS.md` — no task filed for this, it's a reporting/framing change for
whoever assembles the final submission narrative, not a science task.

---

## Phase 2 — Pin the physics so the trees cannot drift (the real "dedup")

Dedup means *one implementation of each shared primitive, ported into both trees, numbers
pinned*. **Resolve the constant before extracting the helper.**

| # | Task | Why in this order | Status |
|---|---|---|---|
| 2.1 | **[EXISTS] TASK-0067** — GNM cutoff + weight-scheme benchmark | **Confirmed live divergence:** `backend` uses **8.0 Å**; `hamiltonians.py` defaults to **10.0 Å** (12.0 for some variants). *The app and the research pipeline currently answer the same question differently.* Extracting a helper first would make the wrong number official. | **Done.** Real benchmark (`analysis.gnm_cutoff_weight_sweep`, heat-kernel scoring) run against KRAS_G12C + BCR_ABL1 (CARDIAC_MYOSIN excluded — `targets.yaml` itself flags its apo structure's data quality as unresolved; MYC_MAX excluded — no pocket to score). **Primary run is APO-only** — the operator/heat-kernel computation reads `apo.coords` exclusively; `holo` is used only to derive the ground-truth pocket label via `build_labels`, never blended into the topology. A **second, separate HOLO run** (holo-native coords + holo-native labels, per explicit user request for comparison) was added: the apo/holo AUC gap is tiny (KRAS +0.009, BCR_ABL1 -0.020) — an order of magnitude smaller than the cutoff/weight-scheme spread (0.164), meaning near-chance performance is not an apo-vs-holo artifact; the ceiling for this operator family is genuinely low on these targets, holo topology in hand or not. **Cutoff: no significant difference** across 7.5/8.0/10.0 Å (mean AUC 0.42-0.43, within noise) — `backend`'s 8.0 Å default does not need to change. **Weight scheme: harmonic modestly but consistently beats binary/gaussian** (wins 3/3 per-cutoff, ~0.11-0.16 AUC), not acted on (n=2 too thin to justify changing `H8_gnm`'s convention). All AUCs near/below chance, consistent with `PLAN.md`'s documented near-chance finding for these targets. 3 synthetic tests + 1 real network-gated benchmark test (apo+holo), 424 passed, 0 failed. **Follow-up 2026-07-15:** this benchmark used the raw GNM Kirchhoff, not `H_new` — see TASK-0113. |
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
| 5.2 | **[FILED] TASK-0082 — competence map synthesis** | The per-target floor / ceiling / headroom table — **the strategic differentiator**. "We close X% of the gap knowing the answer would close, on these targets; ~0 on those, and here is why." A per-target honest NO is a publishable result, not a failure to hide. | **Done** (`COMPETENCE_MAP.md`). Produced BCR_ABL1/CARDIAC_MYOSIN's ceiling numbers as part of this task (TASK-0046 only covered KRAS_G12C): BCR_ABL1 ceiling=0.6118, CARDIAC_MYOSIN ceiling=0.8188. **Headline: none of the 3 mandatory targets has a clean, floor-clearing, resolution-clean, headroom-positive result.** KRAS's ceiling (0.524) sits below its own floor (0.798) — the strongest negative result this framework can express. BCR_ABL1's actual (0.525) sits below its own floor (0.565) though a real, modest, unclaimed ceiling-floor gap exists (0.612 vs 0.565). CARDIAC_MYOSIN's only positive headroom (40.7%) is invalidated by its own `INSUFFICIENT_RESOLUTION` flag. **Still open per the follow-up below**: TASK-0112 (Done 2026-07-17) found every headline comparison it checked (KRAS_G12C, both BCR_ABL1 propagators) has an overlapping 95% CI — this table's own floor/ceiling/actual numbers have not yet had that same CI wired in and should be assumed similarly non-decisive until they are; ceiling column still not fully settled (TASK-0116/0117, still TODO) — read this table's numbers as directionally real, not final. |
| 5.3 | **[EXISTS] TASK-0068** — NISQ noise-model simulation | Directly scored ("noise resilience"): Trotterized simulation under gate noise, testing whether ENAQT is more noise-robust than coherent CTQW. Needs `coarse.py` (done) for qubit feasibility. | **Done.** Qiskit + Aer, real gate-model Trotterized XY-walk circuit + depolarizing/amplitude-damping noise model. Real run (KRAS_G12C, `H_new`, 10-qubit Louvain coarse-graining): swept depth×error-rate×coherent-vs-ENAQT (γ=0.3). **Coherent ties or beats ENAQT at every single point tested, never loses** — a real, honest negative answer, consistent with TASK-0105's finding that dephasing doesn't help AUC. Scope: 1 target/1 operator/1 coarse-graining method only — not generalized. |
| 5.4 | **[EXISTS] TASK-0015** — holo-direction module | LRT / PRS / two-state ANM / NMFF, gated by cumulative overlap. | TODO **(gated pending Phase 1B)** |
| 5.5 | **[FILED] TASK-0075 — knob-spread reporting for the overlap gate** | Per INVARIANCE_PROTOCOL: cutoff / variant / `k` / reference are **KNOBs, not gauge**. On a toy case the same motion swung **0.067–0.860** across an 18-combo grid, flipping go/no-go in 15 of 18. The gate must emit a **spread** and return `UNSTABLE` when knobs decide the verdict — never a point estimate. | TODO. **Follow-up 2026-07-15:** its own synthetic reproduction independently confirmed the same knob-instability pattern; a second, unrelated threshold (the 4.5 Å pocket-label cutoff, which defines ground truth itself) has never been checked the same way — see TASK-0114. |
| 5.6 | **[EXISTS] TASK-0046** — ceiling coordinate-descent search | Completes the floor/ceiling/headroom triple. | **Done** (KRAS_G12C only — BCR_ABL1/CARDIAC_MYOSIN produced under 5.2/TASK-0082 instead). Ported as blind random search (60 trials) — notebook's own "coordinate-descent" section title over-claims; the cell body has no per-coordinate stepping. Real result: KRAS_G12C ceiling = 0.5239-0.5250, **below** its proximity floor (0.798). **Scope gap found 2026-07-15, no owning task yet**: only searched `H_new`'s own 8-parameter DOF — `ceiling.md`'s own "minimum set" requires H8/H13/degree-centrality as candidates too; the H13-vs-H_new comparison it calls "required for scientific rigor" (HYP-P5) has never been run. Two more open caveats: search coverage (TASK-0116, TODO) and CTQW parameter validity (TASK-0117, TODO) — before 5.2 should read any of this as settled. **TASK-0110 (Done, 2026-07-17) cross-checked this exact number** on a different parameter axis (CTQW's numerical `t_max`/`n_steps` via Optuna, same full-array/coherent seed convention, `H_new`'s physical weights left at default): best practical (honestly-sampled) AUC = 0.4750, closely agreeing with this row's 0.5239-0.5250 — two independent optimizers on two different axes, same near-chance conclusion for KRAS_G12C. |
| 5.7 | **[FILED] TASK-0080 — c-Myc / 1NKP application** | Required minimum-set target with **no holo ground truth** — scored on consensus + theoretical docking viability. Needs its own handling: no AUC, no ceiling; report prediction + confidence honestly. | **Done.** New `run_target_no_ground_truth` branch (previously crashed into an undifferentiated `error.txt`). `analysis.consensus_ranking` — cross-operator agreement (4 operators) on the same apo topology, no holo needed. `report.no_ground_truth_report` states explicitly why no AUC/ceiling exists rather than rendering a blank metric. |
| 5.8 | **[FILED] TASK-0081 — generalization set (ASD targets)** | The brief **highly encourages** extra targets to demonstrate robustness/scalability. Pull 2–4 from the Allosteric Database with known sites. Cheap once 5.1 is a one-command run; directly feeds "Technical Approach / Innovation". | **Done, 2 of 4 candidates used, not 4** — the other 2 failed independent RCSB verification (GLUCOKINASE: apo/holo chain IDs don't match either source doc's guess, raised to Code Reviewer; TAR_RECEPTOR: holo structure has zero hetero ligand records at all). PTP1B and CASPASE7 verified and run for real. Found+fixed a real YAML bug along the way: unquoted numeric ligand code (`892`) silently failed every downstream string comparison. **Follow-up 2026-07-15:** see TASK-0115 — this generalization set is now load-bearing for whether any `RESULTS.md` claim is submission-final, not just "encouraged extra evidence," given the project's own repeated-exposure review history. |
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

### 2026-07-15 batch — from REVIEW-2026-07-15 (execution-plan gap audit) and REVIEW-2026-07-15b (ceiling-search methodology)

An Architect/Critic-overlay read-only audit of this plan and its recently-delivered tasks,
run per direct user request ("discover gaps... parameter sweeps? proof of validity?").
Found no P0/P1 code defects — this was a plan-level audit, not a code review — but
identified six gaps with no prior task coverage, all filed and cross-linked into the
existing tasks/rows they affect rather than left standalone:

- **TASK-0112 — wire `metrics.block_bootstrap_ci` into headline AUC reporting.** The
  function is implemented and used by `select.py`'s LOPO path, but never reaches
  `classify_failure`/`verdict_template`/`RESULTS.md` — every floor-vs-score verdict in this
  plan (including Phase 1B's own headline-overturning ones) is currently a bare point
  estimate with no confidence interval. Cross-linked into 5.2 (TASK-0082).
- **TASK-0113 — re-run TASK-0067's cutoff/weight-scheme sweep against the actual headline
  operator.** TASK-0067's own Done section already states it used "the raw GNM Kirchhoff
  only... not `H_new`" — a caveat that never carried into this plan's Phase 2.1 summary line
  ("backend's 8.0 Å default does not need to change"), which reads as covering the headline
  operator when it doesn't. Cross-linked into 2.1 (TASK-0067).
- **TASK-0114 — pocket-label ligand-contact cutoff (4.5 Å) sensitivity sweep.** A second,
  distinct threshold from the GNM graph cutoff — this one defines ground truth itself
  (`holo_pocket_mask`) — never checked for the same knob-instability TASK-0075 already
  proved real for the overlap gate. Cross-linked into 5.5 (TASK-0075) and 0.3 (TASK-0047,
  whose pinned 4.5 Å KRAS_G12C fixture is the direct cross-check target).
- **TASK-0115 — name and gate the repeated-exposure risk across the review cycle itself.**
  `frozen_context`/TASK-0100's LOPO gate prevents *code-level* multiple-comparisons abuse;
  it cannot gate the ~15 *human* review cycles this project has run, each looking at the
  same 3 targets' true labels before deciding what to rename/re-scope/re-frame. Ties any
  `RESULTS.md` claim's finality to 5.8 (TASK-0081)'s generalization set landing first, not
  just "encouraged extra evidence." Cross-linked into 5.8 (TASK-0081) and 1B.9 (TASK-0100).
- **TASK-0116 — ceiling search coverage may be too sparse for its own negative claim.**
  `ceiling.ceiling_search` (5.6/TASK-0046) is blind random search, N=60, over ~8 dimensions
  — weak evidence for the *negative* claim drawn from it ("very little headroom"). Sharpened
  same day by [[Q-0003]]/`P-0002` (`.ai/memory/shared/pitfalls.md`): the reported ceiling
  (~0.525) sits **below** the known-achievable default-parameter score (0.779) inside that
  same search space — though that comparison itself turned out to use a different CTQW
  source convention (see Note below), so it is not yet a clean proof the search under-covers,
  only a reason to treat the ceiling number as unresolved rather than settled either way.
- **TASK-0117 — ceiling search shares every headline AUC's unvalidated CTQW parameters.**
  `consistency_score`'s `t_max=15`/`n_steps=500` are the exact literals TASK-0108/0109/0110
  exist to validate; TASK-0046's real 60-trial KRAS_G12C run used them unchecked. Hard-blocked
  on TASK-0109. Both TASK-0116/0117 cross-linked into 5.6 (TASK-0046) and 5.2 (TASK-0082).
  **TASK-0109 landed Done 2026-07-15**: `propagators.check_convergence`/`min_adequate_t_max`/
  `min_adequate_n_steps` exist and are tested (`tests/test_propagator_convergence.py`) —
  TASK-0117 is now unblocked on the tool existing, but applying it to `ceiling.consistency_
  score`'s real `t_max=15`/`n_steps=500` literals is still TASK-0117's own job, not done here.
  **TASK-0110 landed Done 2026-07-16-17** and directly informs TASK-0117 without closing
  it: an Optuna search over `time_averaged_ctqw`'s own `(t_max, n_steps)` on all 3 mandatory
  targets, using `min_adequate_t_max(kind="time_averaged_ctqw")` (the AAKV all-pairs-min-gap
  criterion TASK-0109 itself flagged as "fragile... blows up on near-degenerate spectra" --
  TASK-0119 deliberately avoided this specific criterion, using `ground_state_relaxation`'s
  simpler 2-eigenvalue-gap one instead). Confirms the fragility was real, on real data, not
  hypothetical: the closed-form-required `t_max` is **145,000x-3,950,000x** the current
  default (KRAS_G12C 320,000x; BCR_ABL1 145,000x; CARDIAC_MYOSIN 3,950,000x), and the
  correspondingly huge `n_steps` (millions) makes `time_averaged_ctqw`'s O(n_steps) Python
  loop **computationally infeasible** to evaluate even once (measured directly: a real call
  did not return after 2+ hours). A capped "practical/honestly-sampled" ceiling scan
  (restricted to the `t_max` range where `n_steps` stays tractable, which always includes
  the current default) found: KRAS_G12C 0.4750 (near chance, **cross-validates TASK-0046's
  independent 0.5250** -- same seed convention, different parameter axis, same conclusion);
  BCR_ABL1 **0.5829 at t_max=2.39** (smaller, not larger, than the default -- a real,
  unexploited headroom finding, distinct from every other result in this section); CARDIAC_
  MYOSIN 0.8149 (inherits that target's existing 5TBY data-quality caveat, not a new
  positive). TASK-0117's own job (applying this to `ceiling.py`'s literal `t_max=15`
  defaults and re-running TASK-0046's specific 60-trial search) is still open -- this is
  real-data evidence for that task to consume, not a substitute for doing it. Full detail:
  `.ai/tasks/DONE/TASK-0110-optuna-apo-holo-parameter-scan.md`,
  `results_task0110/<target>/scan.json`.

**Note, same day, found while preparing this batch for shipping**: a live cross-check of
TASK-0116 against `run_challenge.py` (the actual source of the reported 0.779) found the
ceiling search (`ceiling.py`) and the headline run seed CTQW from **different** conventions
for the same active site — `ceiling.py` uses the full multi-residue `active_site` array,
`run_challenge.py` reduces it to one representative residue (`source =
int(np.sort(active_site_idx)[0])`, a crash workaround per TASK-0090, not a physics choice).
Documented in `.ai/memory/shared/glossary.md` (Protein → Site → Residue/Cα → Atom hierarchy)
and raised to [[Q-0003]]. Not yet resolved into its own task — flagged here so it isn't lost
before TASK-0116/0117 land.

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
1B.15) → 1B.13 → [1C.1 → 1C.2, 1C.3 (parallel), 1C.4 (parallel, no dep)] → 1C.5 → 5.2 →
6.1** — the minimum chain that yields *one leakage-clean, floor-anchored,
mechanism-understood, gauge-fixed, honestly-reported result*, packaged in the artifact
contract so it can be shown.

**Updated 2026-07-16 (afternoon):** **1C.1 (TASK-0090), 1C.2 (TASK-0118), and 1C.3
(TASK-0119) all landed 2026-07-16** — `select.py`'s multi-index crash is fixed; the seed
gauge is fixed (one declared convention: full active-site array, incoherent mixture) with
floor/ceiling/actual re-run for all 3 mandatory targets under it; the clock is
independently fixed (`t* = -ln(tol)/gap` per operator's own spectral gap). **`COMPETENCE_
MAP.md`'s "ceiling below floor" headline is retracted** — KRAS_G12C's ceiling now clears
its floor (+0.045) under the seed fix alone; the *actual* shipped result still does not,
same shape as BCR_ABL1. **Real gap, flagged not silently glossed over: TASK-0118 and
TASK-0119 landed concurrently (claimed the same minute, by different threads) and were
NOT combined into one re-run** — `COMPETENCE_MAP.md`'s current numbers use TASK-0118's
seed fix at the *old* `t_max=15` clock, not TASK-0119's per-operator `t*`. This is exactly
the scenario this document's own prior text anticipated ("if both land around the same
time, the final headline re-run should use both fixes together and say so explicitly, not
silently attribute a combined effect to only one") — a combined seed+clock re-run is now
the next concrete step, not yet done by either task. **1C.4 (TASK-0120, the learnability
gate) is Done (2026-07-17)** — real result, contradicts the panel's own prediction for
KRAS_G12C (see that row for the full number: `LEARNABLE`, not cryptic-structural).
**1C.5 (TASK-0112, bootstrap CI) is Done (2026-07-17)** — the combined seed+clock re-run,
when it lands, should ship with error bars from the first run rather than retrofitting
them, now that the wiring exists. 5.2 (competence map) has been updated per 1C.2's
landing (seed-only), but must not be re-read as fully settled — TASK-0112's own finding
(every comparison it checked has an overlapping CI) has not yet been applied to this
table's own numbers, TASK-0116/0117 remain open, a combined seed+clock re-run is still
outstanding, and
CARDIAC_MYOSIN's new floor-clearing result is explicitly gated on 1C.9 (TASK-0124)'s
still-open 5TBY data-quality question.

**Updated 2026-07-16/17 (Architect/Planner status review):** the "combined seed+clock
re-run" this section names above is now filed as **1C.14 (TASK-0129)** — currently the
single highest-priority open task on the critical path, hard-unblocked (both dependencies
Done). Separately, **TASK-0110** (Optuna scan, landed 2026-07-16/17) found `time_averaged_
ctqw`'s own literature-grounded convergence criterion is computationally infeasible on
real data (prescribed `n_steps` in the millions; a real call didn't return after 2+ hours)
— filed as **1C.15 (TASK-0130)**, not blocking 1C.14. A scaffold hygiene defect (two
concurrent threads both claiming `INV-0005`) was found and fixed the same pass (see Phase
1C's own note above); **[[Q-0003]]** is formally closed.

**Updated 2026-07-18: 1C.14 (TASK-0129) is Done — the combined seed+clock re-run
landed.** This is the load-bearing result Phase 1C exists to produce: under the fully
corrected convention (one seed convention, one per-operator clock, together),
**CARDIAC_MYOSIN's positive result — the only mandatory-target actual-clears-floor
result at any point in this project's history — did not survive.** All three mandatory
targets now read the same way: real ceiling-vs-floor headroom exists in `H_new`'s
physical-scalar space, the shipped default configuration reaches it on none of them.
`COMPETENCE_MAP.md` is current as of this update. Two items found and flagged, not
resolved (out of TASK-0129's own scope, "does not design a third fix"): TASK-0110's
BCR_ABL1 short-`t_max` finding is in real tension with the per-operator clock's own
prescription (shorter beats longer), and a BCR_ABL1 spectral-gap reproducibility
question against TASK-0119's own recorded number. Neither blocks reading the headline
above as this project's current, honestly-reported state.

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
