"""
FastAPI service for the Quantum Allosteric Scanner.

Endpoints
---------
GET  /api/health            liveness probe
GET  /api/targets           benchmark systems + their metadata
GET  /api/families          available Hamiltonian families + propagators
POST /api/scan              run a scan -> connectivity matrix + hit list
GET  /                      serves the frontend (static)
"""
import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .hamiltonian import FAMILIES
from .pipeline import run_scan, PROPAGATORS
from .systems import resolve_systems
from .data_layer import load_structure
from .validation import validate_target, score_against_live

app = FastAPI(title="Quantum Allosteric Scanner", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")


class ScanRequest(BaseModel):
    pdb_id: str = Field(..., description="RCSB PDB id, e.g. 4OBE")
    chains: str = "A"
    source_residues: Optional[List[int]] = None
    family: str = "GNM"
    propagator: str = "ctqw"
    cutoff: float = 8.0
    gamma: float = 1.0
    coarse_k: int = 1
    top_k: int = 5
    target_name: Optional[str] = None
    pocket_mode: str = "full"


class ValidateRequest(BaseModel):
    target_name: str = Field(..., description="benchmark key, e.g. KRAS_G12C")
    family: str = "GNM"
    propagator: str = "ctqw"
    cutoff: float = 8.0
    gamma: float = 1.0
    coarse_k: int = 1
    top_k: int = 5
    pocket_mode: str = "full"


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "quantum-allosteric-scanner"}


@app.get("/api/families")
def families():
    return {"families": FAMILIES, "propagators": sorted(PROPAGATORS)}


@app.get("/api/targets")
def targets():
    """Benchmark systems with the metadata the UI needs to prefill a scan."""
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
            "known_top5": c.get("top5_holo"),
            "known_top5_named": c.get("top5_holo_named"),
            "verified": c.get("verified", False),
        })
    return {"targets": out}


@app.post("/api/scan")
def scan(req: ScanRequest):
    if req.family not in FAMILIES:
        raise HTTPException(400, f"unknown family '{req.family}'")
    if req.propagator not in PROPAGATORS:
        raise HTTPException(400, f"unknown propagator '{req.propagator}'")
    try:
        return run_scan(
            pdb_id=req.pdb_id.strip().upper(),
            chains=req.chains,
            source_residues=req.source_residues,
            family=req.family,
            propagator=req.propagator,
            cutoff=req.cutoff,
            gamma=req.gamma,
            coarse_k=req.coarse_k,
            top_k=req.top_k,
            target_name=req.target_name,
            pocket_mode=req.pocket_mode,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/api/validate")
def validate(req: ValidateRequest):
    """Blind benchmark: scan the APO structure, then validate the prediction against
    the HOLO drug-bound ground truth (frozen-vs-live pocket + AUC/P@k)."""
    if req.family not in FAMILIES:
        raise HTTPException(400, f"unknown family '{req.family}'")
    if req.propagator not in PROPAGATORS:
        raise HTTPException(400, f"unknown propagator '{req.propagator}'")
    systems = resolve_systems(pocket_mode=req.pocket_mode)
    cfg = systems.get(req.target_name)
    if cfg is None:
        raise HTTPException(404, f"unknown target '{req.target_name}'")
    try:
        scan = run_scan(
            pdb_id=cfg["apo"], chains=cfg["chain"], family=req.family,
            propagator=req.propagator, cutoff=req.cutoff, gamma=req.gamma,
            coarse_k=req.coarse_k, top_k=req.top_k, target_name=req.target_name,
            pocket_mode=req.pocket_mode,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))

    report = validate_target(cfg, scan)

    # independent AUC/P@k vs the live-derived pocket (re-load apo to get coords)
    if report.get("live_pocket"):
        apo = load_structure(cfg["apo"], cfg["chain"])
        if apo is not None:
            live_metrics = score_against_live(scan, apo, report["live_pocket"])
            if live_metrics:
                report["live_metrics"] = live_metrics

    return {"target": req.target_name, "apo": cfg["apo"], "scan": scan,
            "validation": report}


# serve the frontend at "/"
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
