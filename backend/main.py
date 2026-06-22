"""
FastAPI service for the Cleveland Clinic Quantum Allosteric Scanner (Team AuraQu).

DATA FOUNDATION phase — this build is about getting the right structural data and
visualizing it. Quantum allosteric prediction will be layered on later.

Endpoints
---------
GET  /api/health            liveness probe
GET  /api/targets           benchmark systems + their metadata
GET  /api/holo-finder       all holo (drug-bound) structures of the same protein
GET  /api/structure         structure intel: chains, drugs + sites, missing residues
POST /api/load              load a structure for visualization (+ optional completion)
GET  /                      serves the frontend (static)
"""
import base64
import os
import secrets
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import Response
from pydantic import BaseModel, Field

from .pipeline import build_view
from .systems import resolve_systems
from .rcsb import structure_intel
from .discovery import find_holo_candidates
from .compare import align_and_compare

app = FastAPI(title="Cleveland Clinic Quantum Allosteric Scanner", version="0.2.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# ── login gate (HTTP Basic Auth) ────────────────────────────────────────────
APP_USERNAME = os.environ.get("APP_USERNAME", "jury")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "QAS@CC")
_REALM = 'Basic realm="Quantum Allosteric Scanner"'


def _authorized(request: Request) -> bool:
    if not APP_PASSWORD or request.url.path == "/api/health":
        return True
    header = request.headers.get("Authorization", "")
    if header.startswith("Basic "):
        try:
            user, _, pw = base64.b64decode(header[6:]).decode("utf-8").partition(":")
            return (secrets.compare_digest(user, APP_USERNAME)
                    and secrets.compare_digest(pw, APP_PASSWORD))
        except Exception:
            return False
    return False


@app.middleware("http")
async def gate_and_cache(request: Request, call_next):
    # login gate
    if not _authorized(request):
        return Response(status_code=401, headers={"WWW-Authenticate": _REALM})
    resp = await call_next(request)
    # never let the browser cache the frontend assets (avoids stale JS after deploys)
    if not request.url.path.startswith("/api"):
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return resp


FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")


class LoadRequest(BaseModel):
    pdb_id: str = Field(..., description="RCSB PDB id, e.g. 4OBE")
    chains: str = "A"
    source_residues: Optional[List[int]] = None
    target_name: Optional[str] = None
    complete: bool = False
    holo_pdb: Optional[str] = None
    holo_chain: Optional[str] = None


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "quantum-allosteric-scanner"}


@app.get("/api/targets")
def targets():
    """Benchmark systems with the metadata the UI needs to prefill a structure."""
    sys = resolve_systems()
    out = []
    for name, c in sys.items():
        out.append({
            "name": name,
            "disease": c.get("disease"),
            "target_class": c.get("target_class"),
            "site_name": c.get("site_name"),
            "apo": c.get("apo"),
            "holo": c.get("holo"),
            "holo_challenge": c.get("holo_challenge"),
            "chain": c.get("chain"),
            "active_site": c.get("catalytic"),
            "verified": c.get("verified", False),
        })
    return {"targets": out}


@app.get("/api/holo-finder")
def holo_finder(apo_pdb: str, chains: str = None, target_name: str = None):
    """Find all ligand-bound (holo) structures of the same protein as `apo_pdb`,
    drug-bound first, for completing/visualizing the apo."""
    try:
        return find_holo_candidates(apo_pdb.strip().upper(), target_name=target_name)
    except Exception as e:
        raise HTTPException(422, f"holo search failed for {apo_pdb}: {e}")


@app.get("/api/structure")
def structure(pdb_id: str, chains: str = None):
    """Biologist-facing structure intel: chains, ligands/drugs + binding sites,
    missing residues, title/organism/resolution."""
    try:
        return structure_intel(pdb_id.strip().upper(), chains)
    except Exception as e:
        raise HTTPException(422, f"could not read structure {pdb_id}: {e}")


@app.get("/api/compare")
def compare(apo: str, holo: str, apo_chain: str = "A", holo_chain: str = None):
    """Superimpose holo onto apo and report per-residue Cα displacement; returns both
    structures (holo aligned into the apo frame) for an overlay view."""
    try:
        return align_and_compare(apo.strip().upper(), apo_chain,
                                 holo.strip().upper(), holo_chain)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(422, f"comparison failed: {e}")


@app.post("/api/load")
def load(req: LoadRequest):
    """Load a structure for visualization (optionally completing missing residues)."""
    try:
        return build_view(
            pdb_id=req.pdb_id.strip().upper(),
            chains=req.chains,
            source_residues=req.source_residues,
            target_name=req.target_name,
            complete=req.complete,
            holo_pdb=req.holo_pdb,
            holo_chain=req.holo_chain,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))


# serve the frontend at "/"
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
