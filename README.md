# Cleveland Clinic · Quantum Allosteric Scanner — Team AuraQu

**Quantum simulation of allosteric signal propagation to identify cryptic druggable pockets.**
Cleveland Clinic — Global Quantum + AI Challenge 2026.

> ### 🌐 Live demo
> **➡️ [ Launch the app ](https://quantum-allosteric-scanner.onrender.com)** &nbsp;·&nbsp; login — **username:** `jury` &nbsp; **password:** `QAS@CC`
>
> Hosted on Render's free tier; the first visit after idle may take ~30–60 s to wake.

Over 85% of disease-causing proteins are considered *undruggable* — they lack the deep
active-site pockets that classical small-molecule drugs need. The only viable strategy for
these targets is **allostery**: finding hidden distal pockets that, when bound, shut down
the active site from a distance.

This tool ingests protein structures from the [RCSB PDB](https://www.rcsb.org), assembles
a clean, complete structural picture (apo + all drug-bound holo forms, missing residues
filled, all binding sites mapped), and visualizes it for biologists. On that foundation, a
**quantum signal-propagation** model (a continuous-time quantum walk on the residue contact
network, predicted *ab initio* from topology — no classical MD) will rank candidate
allosteric/cryptic pockets. This build delivers the data foundation; quantum prediction follows.

---

## Current phase — data foundation

Build the right structural data first, visualize it for biologists, then layer
quantum allosteric prediction on top. This build does the **data + visualization**:

- **Holo discovery** — from an apo PDB id, find every drug-bound (holo) structure of
  the same protein in RCSB, drug-bound first.
- **Apo completion** — fill the apo's missing (unresolved) residues with real holo
  coordinates where available, interpolation otherwise, all flagged.
- **Structure intelligence** — chains, bound drugs/ligands + their binding sites,
  active site, missing residues, resolution/method/title.
- **3D view** — biologist-friendly: white background, color by chain or flexibility,
  active site, drugs, and modeled residues highlighted.

> Quantum prediction (continuous-time quantum walk on the residue contact network)
> was prototyped and is preserved in git history; it will be reintroduced on top of
> this data foundation.

## Architecture

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for diagrams (component map, module
dependencies, request flows) and **[SOFTWARE.md](SOFTWARE.md)** for the full reference.

```
backend/   FastAPI service
  systems.py      validated benchmark metadata (apo/holo, pockets, active sites)
  data_layer.py   RCSB fetch + Cα / B-factor extraction
  rcsb.py         structure intel: chains, ligands/drugs + sites, missing residues
  discovery.py    holo search (RCSB) + apo completion (fill missing residues)
  pipeline.py     data-view loader: PDB id -> per-residue payload for the viewer
  main.py         REST API + serves the frontend
frontend/  3Dmol.js viewer + structure-intelligence panel (no build step)
```

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Then open <http://localhost:8000> and log in with `jury` / `QAS@CC`.

## Deploy (public URL)

The app is configured for one-click deploy to [Render](https://render.com) via
[`render.yaml`](render.yaml):

1. Sign in to Render and authorize access to this (private) GitHub repo.
2. **New + → Blueprint →** select `Oussema-t/Quantum_allosteric-scanner`.
3. Render reads `render.yaml`, builds, and publishes a public `https://…onrender.com`
   URL that **auto-redeploys on every push to `main`**.

The login is set by the `APP_USERNAME` / `APP_PASSWORD` environment variables
(defaults `jury` / `QAS@CC`); change them in `render.yaml` or the Render dashboard
to rotate the password. Set `APP_PASSWORD` to empty to disable the gate.

## Roadmap

1. **Data foundation (current)** — holo discovery, apo completion, structure
   intelligence, biologist-grade 3D visualization.
2. **Quantum allosteric prediction** — reintroduce the continuous-time quantum walk
   on the residue contact network to rank candidate allosteric/cryptic pockets, on
   top of the cleaned, completed structures.
3. **Validation & reporting** — score predictions against known allosteric pockets;
   export the methodological report and hit list.
