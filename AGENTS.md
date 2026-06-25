# AGENTS.md

Onboarding for any AI coding agent working on the **Quantum Allosteric Scanner**.

**Start here:** read **[CLAUDE.md](CLAUDE.md)** (concise agent briefing), then
**[ARCHITECTURE.md](ARCHITECTURE.md)** (diagrams + change log) and
**[SOFTWARE.md](SOFTWARE.md)** (full API + science reference). These three files are the
single source of truth and are kept in sync with the code on every commit.

Quick facts:
- Backend: Python **3.9**, FastAPI (`backend/`). Frontend: vanilla JS + 3Dmol.js + Plotly
  (`frontend/`). Live on Render (auto-deploys on push to `main`).
- Conventions and the run/test workflow are in CLAUDE.md — **follow them**, and update
  ARCHITECTURE.md + SOFTWARE.md in the same commit as any code change.
