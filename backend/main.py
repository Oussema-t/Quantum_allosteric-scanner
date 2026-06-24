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
from .rcsb import structure_intel, ligands_and_sites
from .discovery import find_holo_candidates
from .compare import align_and_compare, resolve_compare_chains
from .active_site import detect_active_site
from .analysis import site_potential_shift, connectivity_change

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
    cutoff: float = 8.0          # GNM contact-network coupling cutoff (Å)
    active_site_mode: str = "benchmark"   # "benchmark" | "auto" (UniProt)


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


@app.get("/api/analysis-shift")
def analysis_shift(apo: str, holo: str, apo_chain: str = "A", holo_chain: str = None,
                   target_name: str = None, cutoff: float = 8.0):
    """GNM site potentials for apo and holo + the apo->holo shift on shared residues.
    The active site is taken from the benchmark metadata or auto-detected on the apo."""
    apo = apo.strip().upper()
    holo = holo.strip().upper()
    if apo == holo:
        raise HTTPException(422, f"cannot compute an apo→holo shift for {apo} against "
                                 f"itself — provide a distinct apo and holo")
    # use the holo chain that actually bears the drug + the matching apo chain
    res = resolve_compare_chains(apo, holo, apo_chain)
    if res is None:
        raise HTTPException(422, f"no drug/ligand found in any chain of {holo} — cannot "
                                 f"pick a drug-bound chain to compare against")
    achain, hchain = res["apo_chain"], res["holo_chain"]
    site = []
    if target_name:
        cfg = resolve_systems().get(target_name)
        if cfg:
            site = list(cfg.get("catalytic", []))
    if not site:
        try:
            site = detect_active_site(apo, achain).get("active_site", [])
        except Exception:
            site = []
    try:
        result = site_potential_shift(apo, achain, holo, hchain, site_resnums=site,
                                      cutoff=_clamp_cutoff(cutoff))
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(422, f"shift analysis failed: {e}")
    result["chains_used"] = {"apo_chain": achain, "holo_chain": hchain,
                             "drug_code": res["drug_code"]}
    # mark exactly where the drug binds in the holo (drug-bearing chain)
    try:
        ligs = ligands_and_sites(holo, hchain)
        drug_ligs = [l for l in ligs if l["is_drug"]]
        result["drug_site"] = sorted(set(r for l in drug_ligs for r in l["binding_site"]))
        result["drug_codes"] = [l["code"] for l in drug_ligs]
    except Exception:
        result["drug_site"] = []
        result["drug_codes"] = []
    return result


@app.get("/api/connectivity-change")
def connectivity_change_ep(apo: str, holo: str, apo_chain: str = "A", holo_chain: str = None,
                           target_name: str = None, cutoff: float = 8.0):
    """apo→holo network reorganization (DDM, contact rewiring, ΔDCC) + coords for the
    morph animation. Holo chain auto-resolved to the drug-bearing chain."""
    apo, holo = apo.strip().upper(), holo.strip().upper()
    if apo == holo:
        raise HTTPException(422, f"cannot compute connectivity change for {apo} vs itself")
    res = resolve_compare_chains(apo, holo, apo_chain)
    if res is None:
        raise HTTPException(422, f"no drug/ligand found in any chain of {holo}")
    achain, hchain = res["apo_chain"], res["holo_chain"]
    try:
        drug_ligs = [l for l in ligands_and_sites(holo, hchain) if l["is_drug"]]
        drug_site = sorted(set(r for l in drug_ligs for r in l["binding_site"]))
    except Exception:
        drug_site = []
    try:
        out = connectivity_change(apo, achain, holo, hchain,
                                  cutoff=_clamp_cutoff(cutoff), site_resnums=drug_site)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(422, f"connectivity-change failed: {e}")
    out["chains_used"] = {"apo_chain": achain, "holo_chain": hchain,
                          "drug_code": res["drug_code"]}
    out["drug_site"] = drug_site
    return out


@app.get("/api/active-site")
def active_site(pdb_id: str, chains: str = "A", holo: str = None):
    """Auto-detect the active/functional site for any protein: UniProt curated
    residues, else the ligand binding site, else PDB SITE records."""
    try:
        return detect_active_site(pdb_id.strip().upper(), chains, holo_pdb=holo)
    except Exception as e:
        raise HTTPException(422, f"active-site detection failed for {pdb_id}: {e}")


@app.get("/api/drug-site")
def drug_site_lookup(holo: str, chains: str = None):
    """Residues where the drug binds in the holo (drug-bearing chain) — to overlay on
    the apo (same residue numbering) when viewing the GNM analysis."""
    holo = holo.strip().upper()
    try:
        from .rcsb import drug_bearing_chain
        hchain, _ = drug_bearing_chain(holo)
        ch = hchain or ((chains or "").split(",")[0].strip() or None)
        drug_ligs = [l for l in ligands_and_sites(holo, ch) if l["is_drug"]]
        residues = sorted(set(r for l in drug_ligs for r in l["binding_site"]))
        return {"holo": holo, "chain": ch, "drug_site": residues,
                "drug_codes": [l["code"] for l in drug_ligs]}
    except Exception as e:
        raise HTTPException(422, f"drug-site lookup failed for {holo}: {e}")


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
    apo, holo = apo.strip().upper(), holo.strip().upper()
    if apo == holo:
        raise HTTPException(422, f"cannot compare {apo} against itself — apo and holo "
                                 f"are the same structure (provide a different apo/holo)")
    # use the holo chain that actually bears the drug + the matching apo chain
    res = resolve_compare_chains(apo, holo, apo_chain)
    if res is None:
        raise HTTPException(422, f"no drug/ligand found in any chain of {holo} — cannot "
                                 f"pick a drug-bound chain to compare against")
    try:
        out = align_and_compare(apo, res["apo_chain"], holo, res["holo_chain"])
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(422, f"comparison failed: {e}")
    out["drug_code"] = res["drug_code"]
    return out


def _clamp_cutoff(c):
    """Keep the GNM coupling cutoff physically sensible (very small fragments the
    network, very large over-connects it)."""
    try:
        return max(5.0, min(14.0, float(c)))
    except (TypeError, ValueError):
        return 8.0


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
            cutoff=_clamp_cutoff(req.cutoff),
            active_site_mode=req.active_site_mode,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))


# serve the frontend at "/"
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
