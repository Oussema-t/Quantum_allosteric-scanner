# CLAUDE.md — agent onboarding for the Quantum Allosteric Scanner

You are working on the **Cleveland Clinic Quantum Allosteric Scanner** (Team AuraQu),
a web app for the Global Quantum + AI Challenge 2026. **Read these two files first —
they are the source of truth and are kept in sync with the code:**

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — diagrams (system map, module dependencies,
  request flows) + a change log (newest first).
- **[SOFTWARE.md](SOFTWARE.md)** — full reference: every API endpoint with params/returns,
  the science per feature, benchmark targets, conventions, and how to test.

## What it is (1 paragraph)
Ingests protein structures from RCSB PDB, completes them, detects active sites (UniProt),
maps drugs + binding sites, and runs structure-based dynamics analysis (GNM) — to find
**allosteric (distal) druggable pockets**. Two phases: **① data foundation (current)** →
**② quantum solving** (a continuous-time quantum walk seeded from the active site, ranks
distal residues — not built yet) → ③ literature comparison. Principle: the **active site
is the anchor**; the **allosteric site is distal** to it.

## Stack & layout
- **Backend** (`backend/`): Python **3.9**, FastAPI + uvicorn, numpy/scipy, BioPython.
  Modules: `data_layer` (RCSB fetch + Cα), `rcsb` (chains/ligands/missing-res/chem_comp
  classify), `discovery` (UniProt + holo search + `complete_apo`), `active_site`
  (UniProt→PDB), `analysis` (GNM §5b/§5c/§5d + connectivity-change §8d), `compare`
  (Kabsch + drug-bearing chain), `pipeline.build_view` (orchestrator), `main` (API + serves
  frontend).
- **Frontend** (`frontend/`): vanilla HTML/CSS/JS, **3Dmol.js** + **Plotly**, no build step.
- **Hosting**: Render (auto-deploys on push). Live:
  https://quantum-allosteric-scanner.onrender.com · login `jury` / `QAS@CC`.

## Conventions (MUST follow)
1. **Python 3.9** — use `typing.Optional`/`List`, never `X | None` at runtime.
2. **Port science from the research notebook** (the source of truth); cite the section
   (e.g. §5b) in comments. Don't invent formulas.
3. **Validate against benchmark targets** (KRAS_G12C, BCR_ABL1, PTP1B, …).
4. **ADD-only** API changes where possible; don't break existing response shapes.
5. Frontend assets are **no-cache**; remind the user to hard-refresh after deploy.
6. **Git**: the user sometimes edits on GitHub — always `git fetch` + rebase before push.
   Every push auto-deploys to Render (~2–3 min). Commit: imperative subject + bullet body
   + `Co-Authored-By` trailer.
7. **Keep docs in sync**: update `ARCHITECTURE.md` (+ a **dated, signed** change-log line:
   `- YYYY-MM-DD · <name> · <summary>`) and `SOFTWARE.md` in the **same commit** as any
   change to modules / endpoints / response fields / frontend behavior / conventions.
8. **Multi-person repo** — follow [COLLABORATION.md](COLLABORATION.md): `git pull --rebase`
   before starting; `git fetch` + rebase before pushing. On a fresh session, read the
   change log + `git log` to learn what teammates changed, and re-read modified files.

## Run & test locally
```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
uvicorn backend.main:app --port 8000        # API calls need:  -u jury:QAS@CC
```
Smoke-test endpoints with curl + a python one-liner on a real benchmark protein; for
frontend changes confirm assets serve and grep the served JS/HTML for the new markers.
