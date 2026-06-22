# Deploying the Quantum Allosteric Scanner

The app deploys to [Render](https://render.com) (free tier) and serves at a public
`https://…onrender.com` URL that auto-redeploys on every push to `main`.

## Easiest: Blueprint (Render reads everything from `render.yaml`)

1. Render → **New +** → **Blueprint**.
2. Select repo **`Oussema-t/Quantum_allosteric-scanner`**, branch **`main`**,
   Blueprint Path **`render.yaml`**.
3. Click **Apply**. Render builds (~2–3 min) and gives you the public URL.

If Render says *"render.yaml not found on main"*, it cached the repo from before the
file existed — push any new commit (or click **Retry** a minute later) and it will
re-scan.

## Manual fallback: Web Service

If the Blueprint is uncooperative, create the service by hand instead:

- Render → **New +** → **Web Service** → select the repo, branch `main`.
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Instance Type:** Free · **Health Check Path:** `/api/health`
- **Environment variables:**
  - `APP_USERNAME` = `jury`
  - `APP_PASSWORD` = `QAS@CC`
  - `PYTHON_VERSION` = `3.11.9`
- **Create Web Service.**

## Login

The deployed site is protected by HTTP Basic Auth — **username `jury`, password
`QAS@CC`** by default. Change `APP_PASSWORD` (in `render.yaml` or the Render
dashboard) to rotate it; set it empty to disable the gate.

## Notes

- Render's free tier sleeps after ~15 min idle; the first request then cold-starts
  in ~30–60 s. Subsequent requests are fast.
- PDB files are fetched from RCSB on demand and cached on the instance.
