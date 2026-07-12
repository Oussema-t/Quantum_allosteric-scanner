# Execution Plan — sequenced, mapped to task IDs

State verified on the `bartosz` branch snapshot: **252 tests passing, 0 real failures**;
all science stubs implemented (`baselines` 180, `coarse` 260, `pathways` 174, `viz` 365);
seam + invariance protocols adopted (TASK-0050/0051); no `w[6:]` index-slicing bug in the
physics core. Ordering is by **dependency and risk**, not task number.

Legend: **[EXISTS]** = already filed · **[NEW]** = must be created (one-liner intent at the end)

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

| # | Task | Why now |
|---|---|---|
| 0.1 | **[NEW] TASK-0070 — pocket label exclusion assembly** | **Oldest live defect.** Nothing assembles `pocket & ~functional & ~terminal`; `labels` owns ingredients, `protocol` gates them, `analysis` consumes the raw mask. Survived four reviews *because no task owns it* — it is a seam, not a module. Blocks 0.2, 0.3, and every honest AUC. |
| 0.2 | **[EXISTS] TASK-0052** — reconcile leakage-gate contract | Gate is green on self-validating guards but its 3 contract tests are still `xfail`. Acceptance for TASK-0004/0006 was **0 xfail**. Needs 0.1 to bind `build_labels`. |
| 0.3 | **[EXISTS] TASK-0047** — foundation review gap bridging | Commits the network-gated KRAS integration test (apo 4OBE / holo 6OIM). The 21/21 match is still a **docstring claim**. |
| 0.4 | **[EXISTS] TASK-0063** — `functional_indices` gate parameter gap | Plumbing so a FROZEN caller reaches `functional_indices` without bypassing the gate. Same seam as 0.1 — do together. |

> **Decision required inside 0.1:** KRAS **Cys12** — in or out of the pocket label?
> `targets.yaml` says exclude; sotorasib (MOV) is covalent at Cys12 so it enters the
> MOV-derived contact set. Pick one and record it. Do not inherit it by omission.

---

## Phase 1 — Make the verdicts honest

The verdict layer was built **before** its denominator. `classify_failure` anchors on
AUC-vs-chance (0.5); `verdict_template` compares against the **H10 operator**. Neither is a
triviality floor. `baselines.py` now exists — wire it in.

| # | Task | Why now |
|---|---|---|
| 1.1 | **[EXISTS] TASK-0058** — wire baseline floor into `classify_failure` | Turns "beats chance" into "beats degree / betweenness / distance-to-active". Without it **no verdict the pipeline emits is honest.** |
| 1.2 | **[EXISTS] TASK-0055** — `optimised` AUC freeze-provenance check | Verifies headline AUCs come from the frozen/DEV path, not the old label-tuned notebook route. If not, the report layer silently re-imports the §8 leak. |
| 1.3 | **[EXISTS] TASK-0064** — wire unsupervised score into frozen loop | Completes the label-free selection path. |
| 1.4 | **[NEW] TASK-0071 — permutation-null leak detector** | The firewall *prevents* known leak vectors; nothing *detects* an unforeseen one. Shuffle labels, re-run, flag anything still scoring. Home: `diagnostics.py`. Verified reference implementation exists. |
| 1.5 | **[EXISTS] TASK-0056** — phase-4 review (diagnostics/report/baselines/pathways) | Same lens the phase-3 review applied, on the four newest modules. |

---

## Phase 2 — Pin the physics so the trees cannot drift (the real "dedup")

Dedup means *one implementation of each shared primitive, ported into both trees, numbers
pinned*. **Resolve the constant before extracting the helper.**

| # | Task | Why in this order |
|---|---|---|
| 2.1 | **[EXISTS] TASK-0067** — GNM cutoff + weight-scheme benchmark | **Confirmed live divergence:** `backend` uses **8.0 Å**; `hamiltonians.py` defaults to **10.0 Å** (12.0 for some variants). *The app and the research pipeline currently answer the same question differently.* Extracting a helper first would make the wrong number official. |
| 2.2 | **[EXISTS] TASK-0066** — shared Kirchhoff + DCC helper | Extract binary-Kirchhoff context + DCC + z-score; port into both trees (not cross-imported), one test suite. **Must land 2.1's chosen constant.** |
| 2.3 | **[NEW] TASK-0072 — golden-value cross-tree drift test** | The anti-drift mechanism 2.2 needs: fix a reference structure, assert both trees produce **numerically identical** output. Without it "ported" decays back into "duplicated" — exactly how 8.0 vs 10.0 happened. |
| 2.4 | **[EXISTS] TASK-0040** — potentials shared GNM context | Same family as 2.2. |
| 2.5 | **[NEW] TASK-0073 — register cross-tree seams** | `.ai/seams/` records (owner + seam-test) for the shared primitive and the cutoff constant, per the adopted SEAM_PROTOCOL. The green bar then remembers the boundary — mechanism, not discipline. |

---

## Phase 3 — WIP graduation (do in parts; each part is independently safe)

`__WORK_IN_PROGRESS__/` is a *staging* name, not an architecture. The package inside it is
green (252 tests). "Work in progress" invites the question *"when does it stop being in
progress?"* — the honest answer is **it already has**. Graduate it. Three mechanical steps,
each a separate MR, none changing behaviour.

| # | Task | Content |
|---|---|---|
| 3.1 | **[NEW] TASK-0076 — graduation part 1: promote the package** | `git mv __WORK_IN_PROGRESS__/src/allostery → allostery/` at repo top level, sibling to `backend/`. Update imports + test paths. **No behaviour change; suite must stay 252-green before and after.** Pure `git mv` + import rewrite. |
| 3.2 | **[NEW] TASK-0077 — graduation part 2: one CI, one green bar** | Single CI workflow runs `backend/` + `allostery/` suites together. Ends the "two test worlds" split and makes the repo-wide bar real (the standards-memo commitment). |
| 3.3 | **[NEW] TASK-0078 — graduation part 3: dissolve the folder** | Remaining `__WORK_IN_PROGRESS__` contents to their permanent homes (`config/targets.yaml` → `config/`, notebooks → `notebooks/`, planning docs → `documentation/`), then **delete the folder**. Nothing "dangling" remains. |

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

| # | Task | Why now |
|---|---|---|
| 4.1 | **[EXISTS] TASK-0021** — backend API test baseline | Smoke floor: `/api/health`, `/api/targets`, `/api/load` + the two documented 422s. Converts the standards commitment from *assigned* to *started*. |
| 4.2 | **[NEW] TASK-0074 — characterization tests for `backend/analysis.py`** | Golden-output tests pinning the **current** live surface (`gnm_context`, `site_potentials`, `quantum_seed_readiness`, `connectivity_change`) *before* convergence touches it. Safety net for TASK-0066. |
| 4.3 | **[EXISTS] TASK-0054** — SE(3) invariance regression test | The metamorphic gauge test, applied to **both** trees. Catches the class of bug unit tests structurally cannot see. |
| 4.4 | **[EXISTS] TASK-0022** — frontend UI tiered test coverage | After the API floor exists. |
| 4.5 | **[EXISTS] TASK-0044** — Python version reconciliation | Docs say 3.9 / `typing.Optional`; runtime is **3.11.9**, `biotite` needs ≥3.10. Shared root docs. Cheap — do before the next standards meeting so the stated rules are true. |

---

## Phase 5 — Advance the research (the scored content)

This is what the submission is actually judged on. Everything above exists to make these
numbers *defensible*; this phase produces them.

| # | Task | Why |
|---|---|---|
| 5.1 | **[NEW] TASK-0079 — end-to-end challenge run** | Produce the three **required deliverables** for every mandatory target (KRAS 4OBE→6OIM, BCR-ABL1 1OPL→5MO4, Myosin, + c-Myc): the **N×N connectivity matrix**, the **top-5 ranked hit list**, and the **methodological report**. Currently no single command produces them. This is the submission artifact. |
| 5.2 | **[NEW] TASK-0082 — competence map synthesis** | The per-target floor / ceiling / headroom table — **the strategic differentiator**. "We close X% of the gap knowing the answer would close, on these targets; ~0 on those, and here is why." A per-target honest NO is a publishable result, not a failure to hide. |
| 5.3 | **[EXISTS] TASK-0068** — NISQ noise-model simulation | Directly scored ("noise resilience"): Trotterized simulation under gate noise, testing whether ENAQT is more noise-robust than coherent CTQW. Needs `coarse.py` (done) for qubit feasibility. |
| 5.4 | **[EXISTS] TASK-0015** — holo-direction module | LRT / PRS / two-state ANM / NMFF, gated by cumulative overlap. |
| 5.5 | **[NEW] TASK-0075 — knob-spread reporting for the overlap gate** | Per INVARIANCE_PROTOCOL: cutoff / variant / `k` / reference are **KNOBs, not gauge**. On a toy case the same motion swung **0.067–0.860** across an 18-combo grid, flipping go/no-go in 15 of 18. The gate must emit a **spread** and return `UNSTABLE` when knobs decide the verdict — never a point estimate. |
| 5.6 | **[EXISTS] TASK-0046** — ceiling coordinate-descent search | Completes the floor/ceiling/headroom triple. |
| 5.7 | **[NEW] TASK-0080 — c-Myc / 1NKP application** | Required minimum-set target with **no holo ground truth** — scored on consensus + theoretical docking viability. Needs its own handling: no AUC, no ceiling; report prediction + confidence honestly. |
| 5.8 | **[NEW] TASK-0081 — generalization set (ASD targets)** | The brief **highly encourages** extra targets to demonstrate robustness/scalability. Pull 2–4 from the Allosteric Database with known sites. Cheap once 5.1 is a one-command run; directly feeds "Technical Approach / Innovation". |
| 5.9 | **[EXISTS] TASK-0037** — H11/H12 anisotropic not implemented | Known gap in the operator register. |

---

## Phase 6 — Results delivery: backend + frontend as the research vehicle

The reframing: these are not a lightweight PoC. They **trigger, execute, and show** the
research. The artifact contract is what lets that happen without dragging the research
machinery into the web tier.

| # | Task | Why |
|---|---|---|
| 6.1 | **[NEW] TASK-0083 — result artifact contract** ⚠️ **decide EARLY** | Define the versioned artifact `allostery` emits and `backend` consumes: N×N connectivity matrix (NPZ), ranked residues + scores, per-target verdict (GO / NO / **UNSTABLE**) with knob-spread, floor/ceiling/headroom, frozen-config **hash**, provenance. This one decision keeps `backend` free of `allostery` imports and unblocks frontend work **in parallel** with the science. Filed early even though 6.2–6.4 are late. |
| 6.2 | **[NEW] TASK-0084 — backend results API** | ADD-only endpoints serving precomputed artifacts (`/api/results/{target}`, `/api/connectivity/{target}`, `/api/verdict/{target}`). **No science in the request path** — read, validate against the contract, serve. Respects convention 4 and the Render cold-start budget. |
| 6.3 | **[NEW] TASK-0085 — frontend research visualization** | The scored "interpretability / 3D visualization" objective: top-5 predicted pockets on the 3Dmol structure, the **N×N connectivity heatmap**, the competence panel (floor / method / ceiling bars), and an explicit **UNSTABLE** state when the knobs decide the verdict. Honesty rendered, not hidden. |
| 6.4 | **[NEW] TASK-0086 — execution/trigger path** | Decide and implement how a run is launched: offline batch producing artifacts (**preferred** — no compute in the request path, works on free-tier Render) vs. an async job queue. Records the decision; the artifact contract makes either viable. |

---

## Phase 7 — Deferred / scaffold hygiene (must not displace Phases 0–1)

`TASK-0023` (YAGNI review, IN_PROGRESS) currently exempts the scaffold from its own lens.
Finish it, apply it to the scaffold, and **freeze scaffold-as-product work** — the
lock/registry/packaging/ripeness tooling scores zero on the challenge rubric.

Keep here: 0024.x, 0026.x, 0042, 0060, 0061, 0062, 0065, 0069.
Cheap, real product cleanups: 0034, 0036, 0038, 0039, **0041** (Haken–Strobl `solve_ivp`
success check — a real robustness bug), 0049.

---

## New tasks to create — one-liner intents

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

**0.1 → 0.2 → 1.1 → 1.2 → 5.1 → 5.2 → 6.1** — the minimum chain that yields
*one leakage-clean, floor-anchored, honestly-reported result*, packaged in the artifact
contract so it can be shown.

Decide **6.1 (artifact contract) early** even though 6.2–6.4 are late: it is the seam
between research and delivery, and fixing it now lets the frontend and the science advance
in parallel instead of serially.

Phase 2/3/4 (dedup, graduation, backend floor) is the **team-standards** track — real, and
the cutoff divergence makes it a *correctness* issue rather than hygiene — but it must not
preempt the Phase 0–1 chain if time gets short.
