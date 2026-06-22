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

This tool ingests a static protein structure from the [RCSB PDB](https://www.rcsb.org) and
simulates **quantum signal propagation** (a continuous-time quantum walk on the residue
contact network) to rank residues by their dynamic connectivity to the active site — a
probability map of candidate allosteric/cryptic pockets. No classical MD trajectories are
used; the dynamics are predicted *ab initio* from topology (the elastic-network hypothesis).

---

## What it produces

- **Connectivity matrix** — an *N×N* matrix where entry `(i, j)` is the quantum
  connectivity strength between residue *i* and residue *j*.
- **Hit list** — the top-5 predicted allosteric residues, seeded from the active site.
- **3D map** — the protein colored by connectivity, with the predicted pockets highlighted.

## Architecture

```
backend/   FastAPI service — ported verbatim from the research notebook
  systems.py      validated benchmark metadata (apo/holo, pockets, top-5)
  data_layer.py   RCSB fetch + Cα / B-factor extraction
  hamiltonian.py  9 elastic-network Hamiltonian families + normalized Laplacian
  transport.py    quantum (CTQW / Green) + classical (heat) propagators
  scoring.py      source-seeded scoring, top-5, AUC vs known pockets
  pipeline.py     orchestrator: PDB id -> connectivity matrix + hit list
  main.py         REST API + serves the frontend
frontend/  3Dmol.js viewer + Plotly heatmap + hit list (no build step)
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

## Scientific method

The contact network of Cα atoms defines a graph Laplacian *H* (the system "Hamiltonian").
Signal propagation from the active-site residues is simulated as a **continuous-time
quantum walk**, whose time-averaged transition probability `⟨|U(t)|²⟩` (or its
dephased / Green's-function variant) defines the connectivity matrix. Residues that
accumulate high connectivity to the active site — yet are spatially distant — are the
candidate allosteric sites. See the methodological notes in each module.

## Status

Increment 1: data layer + quantum core + API + 3D frontend (single-structure scan).
Roadmap: apo→holo validation · Hamiltonian optimization · gate-level NISQ circuits ·
noise resilience · report export.
