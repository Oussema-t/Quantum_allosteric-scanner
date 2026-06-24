# Quantum Allosteric Scanner — Software Reference

**Team AuraQu · Cleveland Clinic / Global Quantum + AI Challenge 2026**

This document is the single source of truth for the software: what it does, its
architecture, every API endpoint, the science behind each feature, conventions, and how
to test it / generate prompts for Claude. **Keep it updated with every change.**

> Maintenance rule: whenever backend modules, endpoints, response fields, frontend
> behavior, or conventions change, update the relevant section here in the same commit.

- **Live app:** https://quantum-allosteric-scanner.onrender.com
- **Login (HTTP Basic Auth):** username `jury` · password `QAS@CC` (`/api/health` is open)
- **Repo:** https://github.com/Oussema-t/Quantum_allosteric-scanner
- **Last doc update reflects:** chem_comp-driven ligand classifier + PDB export (`pdb_text`)

---

## 1. Purpose

Over 85% of disease proteins are "undruggable" — no deep active-site pocket. The only
strategy is **allostery**: a distal pocket that, when bound, shuts down the active site
from a distance. This tool ingests protein structures and, in two phases:

1. **Data foundation (current):** pull the right structures from RCSB, complete them,
   detect active sites (UniProt), map all bound drugs and their binding sites, run a
   structure-based dynamics analysis (GNM), and visualize everything for biologists.
2. **Quantum solving (future):** a continuous-time quantum walk on the residue contact
   network that propagates a signal *from the active site* and ranks distal residues by
   dynamic connectivity → the top-5 predicted allosteric sites. The science is prototyped
   in a research notebook (the source of truth) and ported faithfully.

Key principle: the **active site is the anchor/source**; the **allosteric site is distal**
to it. A validated allosteric drug should bind a pocket with **no overlap** with the
active site.

---

## 2. Tech stack

- **Backend:** Python 3.9, FastAPI + uvicorn, numpy/scipy, BioPython, scikit-learn,
  networkx. Serves the API and the static frontend.
- **Frontend:** vanilla HTML/CSS/JS, **3Dmol.js** (3D structures) + **Plotly** (charts).
  No build step.
- **Hosting:** Render free tier (`render.yaml` Blueprint), public URL, HTTP Basic Auth.
  Free tier sleeps after ~15 min idle (first request cold-starts in ~30–60 s).
- **Data sources:** RCSB PDB (coordinates, REMARK 465 missing residues, HETATM ligands,
  Data API, Search API) and UniProt (curated Active/Binding-site residues). Linked via
  the UniProt accession resolved from RCSB.

---

## 3. Architecture

### Backend (`backend/`)
| Module | Responsibility |
|---|---|
| `data_layer.py` | RCSB fetch (`files.rcsb.org`); parse Cα coords + B-factors per chain; `coarse_grain`, `res_indices`, `align_by_resnum`, `sources_from_resnums` |
| `rcsb.py` | Structure intel: chains, ligands/drugs + binding sites, missing residues (REMARK 465), entry title/method/resolution; drug/cofactor/ion classification; `drug_bearing_chain`, `chain_resnums`, chem-comp names via Data API |
| `discovery.py` | UniProt resolution (`get_uniprot`); RCSB Search for holo structures (`find_holo_candidates`); `complete_apo` (fill missing residues — Kabsch-align holo onto apo, borrow real coords where resolved, else interpolate, all flagged) |
| `active_site.py` | Auto-detect active site: UniProt Active/Binding features mapped to PDB author numbering via a unique resolved-window offset + residue-name verification; fallback to ligand pocket, then PDB SITE records |
| `analysis.py` | GNM site potentials `V_B/V_T/V_R/V_C/V_M` (notebook §5b); `site_potential_shift` (apo→holo Δ §5c + Cα displacement/coordination change §5d via Kabsch) |
| `compare.py` | Kabsch superpose holo onto apo; per-residue Cα displacement; `resolve_compare_chains` (drug-bearing holo chain + matching apo chain) |
| `pipeline.py` | `build_view`: orchestrates load (+ optional completion) → per-residue payload + active-site detection + GNM analysis; reports missing-chain errors |
| `main.py` | FastAPI app; Basic-Auth + no-cache middleware; all endpoints; serves frontend |

### Frontend (`frontend/`)
- `index.html` — horizontal control toolbar ("① Data Extraction & Analysis"), full-width
  3Dmol viewer (white bg) with a caption, Structure Intelligence panel, GNM analysis panel.
- `app.js` — all logic; module-level state (`LAST`, `CURRENT_ANALYSIS`, active-site
  provenance flags). No framework.
- `style.css` — dark theme, responsive.

---

## 4. API reference

All endpoints require Basic Auth (`jury:QAS@CC`) except `/api/health`. Base URL is the
site root (same origin serves the frontend).

### `GET /api/health`
Liveness. No auth. → `{"status":"ok","service":"quantum-allosteric-scanner"}`

### `GET /api/targets`
Benchmark systems for the dropdown. →
`{"targets":[{name, disease, target_class, site_name, apo, holo, holo_challenge, chain, active_site[], verified}]}`

### `POST /api/load`
Load a structure for visualization (+ optional apo completion).
Body: `{pdb_id, chains="A", source_residues?:int[], target_name?, complete?:bool, holo_pdb?, holo_chain?, cutoff?:float=8.0, active_site_mode?:"benchmark"|"auto"="benchmark"}`  (`cutoff` = GNM coupling cutoff Å, clamped 5–14; `active_site_mode="auto"` forces UniProt auto-detection even for benchmark targets)
Returns: `{pdb_id, chains, n_residues, active_site[], active_site_name, active_site_source
("benchmark"|"uniprot"|"ligand"|"pdb_site"|"manual"|"none"), active_site_detail,
residues:[{resnum, chain, bfactor, bnorm, is_source, modeled}], completion(null|summary),
bfactor_range:[min,max], analysis:{cutoff, resnums[], labels{}, terms{V_B,V_T,V_R,V_C,V_M},
enrichment{}}, pdb_text}`. `pdb_text` is the Cα structure **as visualized** (completed
coords included); **modeled (filled) residues are flagged** occupancy=0.00 / B-factor=999.00
and listed in `REMARK 470` so they're spottable when coloring by that column.
Errors (422): `chain(s) 'X' not found in PDB. Available chains: ...` / `could not load PDB from RCSB — check the PDB ID`.

### `GET /api/drug-site?holo=&chains=`
Residues where the drug binds in the holo (drug-bearing chain), to overlay on the
apo (same numbering) while viewing the GNM analysis. Returns `{holo, chain,
drug_site:int[], drug_codes[]}`.

### `GET /api/structure?pdb_id=&chains=`
Structure intelligence. Returns `{pdb_id, summary{title, method, resolution,
deposited_residues}, chains:[{chain, n_residues, first, last}], ligands:[{code, name,
chain, resnum, n_atoms, category("drug"|"cofactor"|"ligand"|"solvent/ion"), is_drug,
binding_site:int[], binding_site_full:[{chain,resnum}]}], drugs:[...], missing_residues:[{chain,resnum,resname}], n_missing}`.
**Ligand classification** is driven by the RCSB chem_comp record: a curated additive
blocklist + an aliphatic-chain heuristic (high H:C, long carbon chain, few heteroatoms)
catch ions/buffers/cryo/detergents/lipids → `solvent/ion`; cofactors (ATP/GTP/NAD/…) →
`cofactor`; an organic non-additive is `drug` if it has a drug-DB cross-ref (DrugBank/Pharos)
**or** heavy-atom count ≥ 30, else `ligand` (visible, `is_drug=False`). NB: DrugBank ref
alone is unreliable (some drugs lack it; some additives have it).

### `GET /api/holo-finder?apo_pdb=&chains=&target_name=`
All ligand-bound (holo) structures of the same protein, drug-bound first. Returns
`{apo, uniprot, benchmark_holo:{holo, holo_challenge, ligand, ligand_name, chain}|null,
candidates:[{pdb_id, title, resolution, ligands[], drugs[], has_drug, drug_names{}}]}`

### `GET /api/active-site?pdb_id=&chains=&holo=`
Auto-detect active/functional site. Returns `{active_site:int[], source, detail, uniprot?}`.

### `GET /api/compare?apo=&holo=&apo_chain=A&holo_chain=`
Superimpose holo onto apo (Kabsch) and report per-residue Cα displacement.
**The holo chain is auto-resolved to the drug-bearing chain; the apo chain is matched by
residue correspondence (prefers same id, A↔A).** `holo_chain` is effectively ignored.
Returns `{apo_pdb, holo_pdb, apo_chain, holo_chain, rmsd, n_aligned, max_disp,
displacements:[{resnum,disp}], apo_text(PDB), holo_text_aligned(PDB), drug_code}`.
Errors (422): self-comparison (`apo==holo`); `no drug/ligand found in any chain of HOLO`.

### `GET /api/analysis-shift?apo=&holo=&apo_chain=A&holo_chain=&target_name=&cutoff=8.0`
GNM site potentials for apo and holo + the apo→holo shift (§5c) and structural change (§5d).
Same drug-bearing-chain resolution as `/api/compare`. Returns `{labels{}, active_site[],
apo:{resnums, terms, labels, enrichment}, holo:{...}, delta:{resnums, terms, labels,
enrichment}, structural:{resnums, ca_displacement[], d_coordination[], ca_rmsd, max_disp}|null,
n_shared, chains_used:{apo_chain, holo_chain, drug_code}, drug_site:int[], drug_codes[]}`.
Errors (422): self-comparison; no drug-bearing chain.

---

## 5. The science (per feature)

- **PDB extraction** — Cα coordinates + B-factors per chain; the contact network of Cα
  atoms drives everything (elastic-network hypothesis; no MD).
- **Missing residues** — read from REMARK 465 (the deposited unresolved list).
- **Apo completion** (`complete_apo`) — Kabsch-align holo onto apo on shared Cα, then for
  each missing residue: copy the **real holo Cα** if resolved there, else **interpolate**
  between flanking residues. All filled residues flagged `modeled` and drawn in 3D.
- **Active-site detection** — UniProt `Active site` + `Binding site` features, mapped from
  UniProt numbering to PDB author numbering via a unique resolved-window offset with
  residue-name verification. Fallbacks: ligand binding site → PDB SITE records → none.
- **Drug-bearing chain** — the protein chain with the most contacts to a drug ligand;
  comparison aligns the apo to *that* chain (A↔A by correspondence).
- **GNM site potentials (§5b)** — Kirchhoff operator from the contact graph; five z-scored
  per-residue descriptors:
  - `V_B` B-factor flexibility · `V_T` terminal/exposure · `V_R` rigidity ·
    `V_C` dynamic coupling (GNM covariance) · `V_M` slow-mode participation.
  - "active site − bulk" enrichment flags which property marks the functional region.
- **apo→holo shift (§5c)** — each structure z-scored within itself, then per-residue
  Δ(holo−apo) on shared residues → how drug binding reshapes the dynamics.
- **Cα displacement + coordination change (§5d)** — Kabsch-aligned per-residue Cα movement
  (Å) and Δ contact number (holo−apo) → where the structure physically moves/repacks.
- **Active ∩ drug intersection** — overlap of active-site and drug-binding residues →
  verdict: orthosteric (overlap) vs allosteric/distal (no overlap).

---

## 6. Benchmark targets

| Key | Protein | apo | holo | Drug | Site |
|---|---|---|---|---|---|
| KRAS_G12C | KRAS G12C (GTPase) | 4OBE | 6OIM | Sotorasib (MOV) | Switch-II pocket |
| BCR_ABL1 | BCR-ABL1 (kinase) | 1OPL | 5MO4 | Asciminib (AY7) | Myristoyl pocket |
| CARDIAC_MYOSIN | β-cardiac myosin | 5TBY | 6C1H (challenge) / 8QYR (validation) | Mavacamten (XB2) | Mavacamten site |
| MYC_MAX | c-Myc (IDP) | 1NKP | none | — | none (discovery only) |
| PTP1B | PTP1B (phosphatase) | 1SUG | 1T49 | BB inhibitor (892) | Allosteric BB site |
| GLUCOKINASE | Glucokinase | 1V4S | 3H1V | GKA (TK1) | GKA site |

---

## 7. Frontend features

- **① Data Extraction & Analysis** toolbar: benchmark target, PDB id + chain(s),
  active-site residues (auto-detected, provenance-tracked), Find holo, holo picker,
  Complete-apo toggle, Find & visualize, Compare, Compute shift.
- **3D viewer:** white background; caption stating apo/holo + chain(s) (or both in compare);
  color by chain / flexibility / GNM term; show drugs (labeled), active site (teal),
  modeled residues (orange), drug-binding residues (purple), optional surface;
  **Export PDB** button (downloads the visualized structure with modeled residues flagged;
  in compare mode exports both apo and aligned-holo).
- **Structure Intelligence panel:** chains, ligands/drugs + binding sites, missing residues
  (collapsible), completion summary.
- **GNM Site-potential analysis panel:** mode selector (Loaded / Holo / apo→holo Δ),
  enrichment cards, five per-residue profile charts (full residue axis) + §5d Cα
  displacement & Δ coordination charts in Δ mode, active-site (red) + drug-site (purple)
  markers, drug∩active-site verdict, exports (CSV / JSON / PNG). The apo/loaded view also
  overlays where the drug binds (fetched from the known holo) on the charts + 3D.

---

## 8. Conventions & gotchas

1. **Python 3.9** — no `X | None` unions at runtime; use `typing.Optional`/`List`.
2. **Port science from the notebook**, citing the section (e.g. §5b) in comments; don't
   invent formulas.
3. **Validate against benchmarks** (e.g. detected active sites should match curated lists;
   ΔV_R should peak at the known pocket).
4. **UniProt→PDB numbering** can differ — always map + verify residue names.
5. **apo/holo are different coordinate frames** — Kabsch-align before borrowing coords.
6. **Frontend assets are no-cache** (middleware); tell the user to hard-refresh after deploy.
7. **Git:** the user sometimes edits on GitHub — always `git fetch` + rebase before push.
   Every push auto-deploys to Render (~2–3 min). Commit messages: imperative subject +
   bullet body + `Co-Authored-By` trailer.
8. Auth via env vars `APP_USERNAME` / `APP_PASSWORD` (defaults `jury` / `QAS@CC`).

---

## 9. Dev & test workflow

```bash
cd Quantum_allosteric-scanner
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --port 8000        # local server
# every API call needs:  -u jury:QAS@CC
```

- **Backend change:** smoke-test the endpoint with curl + a python one-liner on a real
  benchmark protein; check expected values.
- **Frontend change:** confirm assets serve; grep served JS/HTML for new markers.
- **Keep edits surgical;** don't disturb working behavior (metadata, holo-finder, drug
  classification, binding lookup, GNM analysis).
- **Commit + push** (after fetch/rebase) → Render redeploys → hard-refresh.

### Writing a Claude test prompt (website-only)
Give Claude the live URL + login and concrete API cases with expected outputs. Note that a
website-only Claude can exercise the **API** (backend behavior) but not click the JS UI;
test UI-only logic by reasoning over `app.js` or with a headless browser. Example expected
results to assert:
- `GET /api/compare?apo=4OBE&holo=6OIM` → 200, `apo_chain=A holo_chain=A drug_code=MOV
  rmsd≈1.36 n_aligned≈166`.
- `GET /api/compare?apo=6OIM&holo=6OIM` → 422 "cannot compare 6OIM against itself".
- `GET /api/compare?apo=4OBE&holo=1NKP` → 422 "no drug/ligand found in any chain of 1NKP".
- `POST /api/load {"pdb_id":"1HHP","chains":"B"}` → 422 "chain(s) 'B' not found in 1HHP.
  Available chains: A".
- `POST /api/load {"pdb_id":"1HHP","chains":"A"}` → 200, `active_site` includes 25 (Asp25).

---

## 10. Roadmap

1. **Data foundation (current)** — done: extraction, completion, active-site detection,
   structure intel, GNM analysis (§5b/§5c/§5d), drug-chain-aware comparison, exports.
2. **② Quantum solving** — continuous-time quantum walk on the contact network seeded from
   the active site; rank distal residues by dynamic connectivity → top-5 allosteric sites;
   validate against known pockets (AUC / P@5).
3. **③ Literature comparison** — LLM + live retrieval (PubMed / Semantic Scholar / ASD) to
   compare predicted allosteric residues against the latest published sites, with verified
   citations.
