# Product intent map — backend endpoints + frontend controls vs. rubric/roadmap

**Produced by:** TASK-0020, 2026-07-04. **Status:** first pass — see caveats below before treating any rubric-linkage cell as settled.

**Purpose.** One place to answer "what does this app do and why" without reading `app.js` line by line, and to name every feature whose reason to exist isn't actually written down anywhere. Feeds TASK-0023 (YAGNI/scope-creep scoring) directly — the "unclear" list at the bottom is that task's input backlog.

**Caveat — rubric source unconfirmed.** The six criteria below (Problem/Impact 25, Technical 25, Feasibility 20, Validation 15, Hybrid 5, Team 10) are quoted from `.ai/tasks/PLANS/PLAN-01.07.26.md` Week 3, not from a primary challenge-rules document found in this repo. Treat every rubric-linkage cell as **provisional** until a human confirms that's the authoritative, current rubric.

**Completeness check performed:** every route in `backend/main.py`'s route table appears below (11 endpoints + the static mount); every `id=` referenced by `frontend/app.js` (44 unique ids, grepped directly) has a matching element in `frontend/index.html` — no orphaned JS-only or HTML-only controls found.

---

## 1. Backend endpoints (`backend/main.py`)

No drift found between this table and `SOFTWARE.md` §4 — both list the same 11 endpoints.

| Endpoint | Purpose | Roadmap phase | Rubric linkage | Confidence |
|---|---|---|---|---|
| `GET /api/health` | Liveness probe (also pinged by a keep-warm cron, per ARCHITECTURE.md 2026-06-28) | infra | Feasibility (uptime) | stated |
| `GET /api/targets` | Serve the 6 curated benchmark targets for the dropdown | ① | Validation (benchmark framework), Problem/Impact (real disease targets) | stated |
| `GET /api/holo-finder` | Find drug-bound structures of the same protein, to complete/compare the apo | ① | Technical, Feasibility | stated |
| `POST /api/load` | Core structure load + optional apo completion — the central data-foundation feature | ① (core, per `SOFTWARE.md` §10 "done") | Technical, Problem/Impact | stated |
| `GET /api/structure` | Structure intel: chains, ligands/drugs + sites, missing residues | ① (core) | Technical, Problem/Impact | stated |
| `GET /api/active-site` | Auto-detect the active/functional site (UniProt → ligand pocket → PDB SITE fallback) | ① (core) | Technical (anchors the project's stated "active site is the anchor" principle) | stated |
| `GET /api/drug-site` | Drug-binding residues, overlaid on the apo GNM view | ① (core) | Technical, Validation (orthosteric/allosteric verdict) | stated |
| `GET /api/compare` | Kabsch superpose apo/holo + per-residue Cα displacement | ① (core) | Technical, Validation | stated |
| `GET /api/analysis-shift` | GNM site potentials (§5b) for apo/holo + apo→holo Δ (§5c/§5d) | ① (core) | Technical (core method), Validation (benchmark alignment) | stated |
| `GET /api/connectivity-change` | DDM / contact rewiring / ΔDCC (§8d) + morph coords **+ bundled `seed_readiness` (§5h/§5i, CTQW-flavored)** | ① presentation, **but `seed_readiness`'s `_ctqw_build_H` is a real, already-live slice of ② quantum solving** | Technical; `seed_readiness` specifically is the *only* Product-code touchpoint on **Hybrid** today | ① part: stated. `seed_readiness` positioning: **unclear** — see §3 |
| `GET /api/morph-frames` | Real-structure keyframes (auto-discovered intermediate PDBs, RMSD-progress ordered) for the 3D contact-graph animation | presentation only | **unclear** — see §3 | unclear |
| `GET /` (static mount) | Serves `frontend/` | infra | — | stated |

**Finding to flag (already surfaced by TASK-0018, repeating here since it's directly relevant to intent legibility):** `connectivity-change`'s `seed_readiness`/`_ctqw_build_H` means the project's own framing ("② Quantum solving — not built yet," `ARCHITECTURE.md` §6, `SOFTWARE.md` §1) is **stale** — a partial, quantum-walk-flavored feature is already live in the Product. Worth a doc correction independent of this task's scope (TASK-0018 already tracks it).

---

## 2. Frontend controls (`frontend/index.html` + `app.js`), grouped by panel

### ① Data Extraction & Analysis (control bar)
`target`, `pdb`, `chains`, `cutoff`, `sitemode`, `source`, `load`, `findholo`, `holo`, `complete`, `compare` — all core Phase-① data-foundation UI, purpose stated directly in `SOFTWARE.md` §7 and in-UI labels/tooltips. **Confidence: stated.** Rubric: Technical, Problem/Impact.

### 3D viewer
`colorby` (chain / flexibility / GNM terms), `opt-ligands`, `opt-active`, `opt-surface`, `exportpdb` — core visualization + export, stated purpose, Phase ①. Rubric: Technical, Problem/Impact.

### Structure intelligence panel
`structinfo` (display only) — stated, Phase ①, core.

### GNM site-potential analysis panel
`computeshift`, `analysismode`, `exportcsv`/`exportjson`/`exportpng`, `enrichment`/`enrichbar`/`lspectrum`/`druginter`/`analysischarts` (charts) — presentation of the core GNM science (§5b/§5c/§5d), purpose stated in the panel's own extensive in-app help text. Phase ①. Rubric: Technical, Validation.

### Connectivity-change panel (largest single feature cluster)
- `connbtn`, `ddmplot`/`rewireplot`/`ddccplot` — core §8d presentation, stated (own in-app help box), Phase ①.
- `connX`/`connY`/`connXint`/`connYint`/`connapply`/`connreset` (region selector, free-text custom intervals per axis) — purpose stated (lets the user sub-block the matrices), but granularity (independent X/Y, free-text interval parsing) is more configurability than the other panels offer. **Flag: plausible-but-unstated whether this level of control is worth its complexity — TASK-0023 call.**
- `seedwrap`/`seedbody` (quantum-seed readiness card) — see finding above; real science, undocumented rubric positioning. **Flag: unclear.**
- `morphplay`/`morphslider` (straight-line apo→holo morph) — illustrative only, per the UI's own hint text ("illustrative morph, not a simulated trajectory"). **Flag: unclear** whether decorative-morph engineering effort is rubric-justified.
- `graphmode`/`graphnframes`/`graphapply`/`graphplay`/`graphslider` (3D contact-graph animation, real-structures vs. linear motion, auto-discovered intermediate structures via RMSD-progress ordering) — per `ARCHITECTURE.md`'s 2026-06-28 entries, this is the single largest recent engineering investment (auto-discovery, region-selector integration, frame morphing, motion-mode toggle). Explicitly labeled illustrative in its own UI copy ("not a simulated trajectory"). **Flag: strongest scope-creep candidate** — significant effort behind a decorative animation with no stated tie to any rubric criterion.

---

## 3. Unclear-purpose items (input backlog for TASK-0023)

1. `GET /api/morph-frames` + `graphmode`/`graphnframes`/`graphapply`/`graphplay`/`graphslider`/`graphwrap` — 3D contact-graph real-structures animation. Heaviest engineering cluster with no stated rubric link.
2. `seed_readiness` / `_ctqw_build_H` (bundled in `connectivity-change`) — real physics, but its relationship to the "Hybrid" rubric criterion and to the project's own "quantum not built yet" framing is undocumented and possibly stale.
3. `morphplay`/`morphslider` (straight-line morph) — same illustrative-only category as #1, smaller effort.
4. `connX`/`connY`/`connXint`/`connYint` region-selector granularity — plausible but unstated whether independent-axis custom intervals earn their complexity.

---

## Open items (for the user, not resolved by this task)

- Confirm the six-criterion rubric quoted above against the actual challenge rules document — this map's rubric-linkage column is only as good as that source.
- Decide whether to keep this map live (updated alongside `ARCHITECTURE.md`'s change log going forward) or treat it as a one-time snapshot.
