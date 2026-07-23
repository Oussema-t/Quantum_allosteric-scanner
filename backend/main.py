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

from . import result_cache
from .pipeline import build_view
from .systems import resolve_systems
from .rcsb import structure_intel, ligands_and_sites
from .discovery import find_holo_candidates
from .compare import align_and_compare, resolve_compare_chains
from .active_site import detect_active_site
from .analysis import (site_potential_shift, connectivity_change, seed_readiness_shift,
                       morph_frames)

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


def _cache_or_compute(params, compute):
    """Return a cached result (add-only `cached` flag) or compute + store it. Only a
    successful return is cached; a raised HTTPException propagates uncached. RCSB data is
    immutable per PDB id, so a hit equals recomputing — nothing scientific changes."""
    hit = result_cache.get(params)
    if hit is not None:
        return {**hit, "cached": True} if isinstance(hit, dict) else hit
    out = compute()
    if isinstance(out, dict):
        result_cache.set(params, out)
        return {**out, "cached": False}
    result_cache.set(params, out)
    return out


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "quantum-allosteric-scanner", **result_cache.info()}


# alias used by external keep-warm pings / uptime monitors
@app.get("/healthz")
def healthz():
    return {"status": "ok", **result_cache.info()}


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
    apo_pdb = apo_pdb.strip().upper()

    def _c():
        try:
            return find_holo_candidates(apo_pdb, target_name=target_name)
        except Exception as e:
            raise HTTPException(422, f"holo search failed for {apo_pdb}: {e}")
    return _cache_or_compute({"op": "holo_finder", "apo": apo_pdb, "target_name": target_name}, _c)


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
    sparams = {"op": "analysis_shift", "apo": apo, "holo": holo, "apo_chain": apo_chain,
               "holo_chain": holo_chain, "target_name": target_name, "cutoff": _clamp_cutoff(cutoff)}
    shit = result_cache.get(sparams)
    if shit is not None:
        return {**shit, "cached": True}
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
    result_cache.set(sparams, result)
    result["cached"] = False
    return result


@app.get("/api/connectivity-change")
def connectivity_change_ep(apo: str, holo: str, apo_chain: str = "A", holo_chain: str = None,
                           target_name: str = None, cutoff: float = 8.0):
    """apo→holo network reorganization (DDM, contact rewiring, ΔDCC) + coords for the
    morph animation. Holo chain auto-resolved to the drug-bearing chain."""
    apo, holo = apo.strip().upper(), holo.strip().upper()
    if apo == holo:
        raise HTTPException(422, f"cannot compute connectivity change for {apo} vs itself")
    cparams = {"op": "connectivity", "apo": apo, "holo": holo, "apo_chain": apo_chain,
               "holo_chain": holo_chain, "target_name": target_name,
               "cutoff": _clamp_cutoff(cutoff)}
    chit = result_cache.get(cparams)
    if chit is not None:
        return {**chit, "cached": True}
    res = resolve_compare_chains(apo, holo, apo_chain)
    if res is None:
        raise HTTPException(422, f"no drug/ligand found in any chain of {holo}")
    achain, hchain = res["apo_chain"], res["holo_chain"]
    try:
        drug_ligs = [l for l in ligands_and_sites(holo, hchain) if l["is_drug"]]
        drug_site = sorted(set(r for l in drug_ligs for r in l["binding_site"]))
    except Exception:
        drug_site = []
    # active site for overlay (benchmark metadata, else auto-detected)
    active = []
    if target_name:
        cfg = resolve_systems().get(target_name)
        if cfg:
            active = list(cfg.get("catalytic", []))
    if not active:
        try:
            active = detect_active_site(apo, achain).get("active_site", [])
        except Exception:
            active = []
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
    out["active_site"] = sorted(set(active))
    # §5h/§5i: is the active site a safe quantum-walk seed, and how does the drug
    # shift it (activation vs deactivation)? Best-effort — never fails the request.
    try:
        out["seed_readiness"] = seed_readiness_shift(
            apo, achain, holo, hchain,
            site_resnums=out["active_site"], drug_resnums=drug_site,
            cutoff=_clamp_cutoff(cutoff))
    except Exception:
        out["seed_readiness"] = None
    result_cache.set(cparams, out)
    out["cached"] = False
    return out


@app.get("/api/morph-frames")
def morph_frames_ep(apo: str, holo: str, apo_chain: str = "A", holo_chain: str = None,
                    n_frames: int = 4, cutoff: float = 8.0):
    """Real keyframes for the 3D graph animation. The protein is already chosen, so the
    intermediate structures are AUTO-discovered (other PDB entries of the same protein,
    ordered apo→holo); the user only picks how many frames (`n_frames`, 2–8)."""
    apo, holo = apo.strip().upper(), holo.strip().upper()
    if apo == holo:
        raise HTTPException(422, f"apo and holo are the same entry ({apo})")
    n_frames = max(2, min(int(n_frames), 8))
    mparams = {"op": "morph_frames", "apo": apo, "holo": holo, "apo_chain": apo_chain,
               "holo_chain": holo_chain, "n_frames": n_frames, "cutoff": _clamp_cutoff(cutoff)}
    mhit = result_cache.get(mparams)
    if mhit is not None:
        return {**mhit, "cached": True}
    res = resolve_compare_chains(apo, holo, apo_chain)
    achain = res["apo_chain"] if res else apo_chain
    hchain = res["holo_chain"] if res else (holo_chain or apo_chain)
    try:
        out = morph_frames(apo, achain, holo, hchain, n_frames=n_frames,
                           cutoff=_clamp_cutoff(cutoff))
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(422, f"morph-frames failed: {e}")
    result_cache.set(mparams, out)
    out["cached"] = False
    return out


@app.get("/api/active-site")
def active_site(pdb_id: str, chains: str = "A", holo: str = None):
    """Auto-detect the active/functional site for any protein: UniProt curated
    residues, else the ligand binding site, else PDB SITE records."""
    pdb_id = pdb_id.strip().upper()

    def _c():
        try:
            return detect_active_site(pdb_id, chains, holo_pdb=holo)
        except Exception as e:
            raise HTTPException(422, f"active-site detection failed for {pdb_id}: {e}")
    return _cache_or_compute({"op": "active_site", "pdb_id": pdb_id, "chains": chains, "holo": holo}, _c)


@app.get("/api/drug-site")
def drug_site_lookup(holo: str, chains: str = None):
    """Residues where the drug binds in the holo (drug-bearing chain) — to overlay on
    the apo (same residue numbering) when viewing the GNM analysis."""
    holo = holo.strip().upper()

    def _c():
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
    return _cache_or_compute({"op": "drug_site", "holo": holo, "chains": chains}, _c)


@app.get("/api/structure")
def structure(pdb_id: str, chains: str = None):
    """Biologist-facing structure intel: chains, ligands/drugs + binding sites,
    missing residues, title/organism/resolution."""
    pdb_id = pdb_id.strip().upper()

    def _c():
        try:
            return structure_intel(pdb_id, chains)
        except Exception as e:
            raise HTTPException(422, f"could not read structure {pdb_id}: {e}")
    return _cache_or_compute({"op": "structure", "pdb_id": pdb_id, "chains": chains}, _c)


@app.get("/api/compare")
def compare(apo: str, holo: str, apo_chain: str = "A", holo_chain: str = None):
    """Superimpose holo onto apo and report per-residue Cα displacement; returns both
    structures (holo aligned into the apo frame) for an overlay view."""
    apo, holo = apo.strip().upper(), holo.strip().upper()
    if apo == holo:
        raise HTTPException(422, f"cannot compare {apo} against itself — apo and holo "
                                 f"are the same structure (provide a different apo/holo)")
    cmpparams = {"op": "compare", "apo": apo, "holo": holo, "apo_chain": apo_chain,
                 "holo_chain": holo_chain}
    cmphit = result_cache.get(cmpparams)
    if cmphit is not None:
        return {**cmphit, "cached": True}
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
    result_cache.set(cmpparams, out)
    out["cached"] = False
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
    # result cache: key on EVERY param that affects the output (RCSB data is immutable,
    # so a hit is identical to recomputing). Add-only: response gains a `cached` flag.
    params = {"op": "load", "pdb_id": req.pdb_id.strip().upper(), "chains": req.chains,
              "source_residues": req.source_residues, "target_name": req.target_name,
              "complete": req.complete, "holo_pdb": req.holo_pdb, "holo_chain": req.holo_chain,
              "cutoff": _clamp_cutoff(req.cutoff), "active_site_mode": req.active_site_mode}
    hit = result_cache.get(params)
    if hit is not None:
        return {**hit, "cached": True}
    try:
        out = build_view(
            pdb_id=params["pdb_id"], chains=req.chains, source_residues=req.source_residues,
            target_name=req.target_name, complete=req.complete, holo_pdb=req.holo_pdb,
            holo_chain=req.holo_chain, cutoff=params["cutoff"],
            active_site_mode=req.active_site_mode,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))
    result_cache.set(params, out)
    return {**out, "cached": False}


# ── background pre-warm: load the challenge targets into the cache after boot ─────
# Runs in a daemon thread so it never blocks startup or real requests. Warms the full
# structures (so any later cutoff is a network-free sub-second recompute) + the default
# results (so the first click on a benchmark target is instant). Nothing is truncated.
import threading
import time
import logging

from .config import config

_log = logging.getLogger("qas.prewarm")


def _prewarm():
    time.sleep(config.PREWARM_DELAY_S)
    systems = resolve_systems()
    n = 0
    for name, cfg in systems.items():
        apo, holo, chain = cfg.get("apo"), cfg.get("holo"), cfg.get("chain", "A")
        if not apo:
            continue
        for cut in config.PREWARM_CUTOFFS:
            try:                                        # visualization + GNM analysis
                load(LoadRequest(pdb_id=apo, chains=chain, target_name=name, cutoff=cut)); n += 1
            except Exception as e:                      # a broken target must not stop the rest
                _log.info("prewarm load %s@%s failed: %s", name, cut, e)
            if holo:
                try:                                    # connectivity change (DDM/rewiring/ΔDCC + morph + seed)
                    connectivity_change_ep(apo=apo, holo=holo, apo_chain=chain,
                                           target_name=name, cutoff=cut); n += 1
                except Exception as e:
                    _log.info("prewarm connectivity %s@%s failed: %s", name, cut, e)
                try:                                    # apo→holo site-potential shift (§5c/§5d)
                    analysis_shift(apo=apo, holo=holo, apo_chain=chain,
                                   target_name=name, cutoff=cut); n += 1
                except Exception as e:
                    _log.info("prewarm shift %s@%s failed: %s", name, cut, e)
        if holo:
            try:                                        # apo↔holo displacement (cutoff-independent)
                compare(apo=apo, holo=holo, apo_chain=chain); n += 1
            except Exception as e:
                _log.info("prewarm compare %s failed: %s", name, e)
            if config.PREWARM_MORPH:                     # real-structures animation (network-heavy)
                cut0 = config.PREWARM_CUTOFFS[0] if config.PREWARM_CUTOFFS else 8.0
                try:
                    morph_frames_ep(apo=apo, holo=holo, apo_chain=chain,
                                    n_frames=config.PREWARM_MORPH_FRAMES, cutoff=cut0); n += 1
                except Exception as e:
                    _log.info("prewarm morph %s failed: %s", name, e)
    _log.info("prewarm complete: %d results cached", n)


if config.PREWARM_ENABLED:
    threading.Thread(target=_prewarm, name="qas-prewarm", daemon=True).start()


# serve the frontend at "/"
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
