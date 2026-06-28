"""
GNM site-potential analysis (notebook §5b) — adapted to this app's structures.

From the Cα contact network we build the Gaussian Network Model (GNM / Kirchhoff
operator) and derive five per-residue "site-potential" descriptors. Each is
z-scored across the protein so they're comparable, and (when an active site is
known) we report how elevated each term is AT the site vs the bulk — the biological
signal that flags allosteric/cryptic pockets.

  V_B  B-factor flexibility     crystallographic mobility (high = flexible)
  V_T  terminal / exposure      chain-end proximity + solvent exposure proxy
  V_R  rigidity                 high degree + clustering, low fluctuation (rigid core)
  V_C  dynamic coupling         GNM covariance — how dynamically correlated a residue is
  V_M  slow-mode participation  involvement in the slowest collective (global) modes

This is structure-based only (the elastic-network hypothesis); no MD, no quantum.
"""
import numpy as np
from scipy.spatial.distance import cdist

from .data_layer import load_structure, res_indices


def _z(x):
    x = np.asarray(x, float)
    s = x.std()
    return (x - x.mean()) / (s + 1e-9) if s > 0 else np.zeros_like(x)


def _coordination(coords, cutoff):
    """Per-residue coordination number (contacts within cutoff)."""
    D = cdist(coords, coords)
    return ((D < cutoff) & (D > 1e-8)).sum(1).astype(float)


def _kabsch_rotate(mobile, ref):
    """Rotate `mobile` (N,3) onto `ref` (N,3) by least squares; return aligned mobile."""
    mc = mobile - mobile.mean(0)
    rc = ref - ref.mean(0)
    U, _S, Vt = np.linalg.svd(mc.T @ rc)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    return mc @ R.T + ref.mean(0)


def gnm_context(coords, bfac, cutoff=8.0):
    """Kirchhoff (GNM) operator and the quantities the five terms are built from."""
    N = len(coords)
    D = cdist(coords, coords)
    A = ((D < cutoff) & (D > 1e-8)).astype(float)
    deg = A.sum(1)
    K = np.diag(deg) - A                          # Kirchhoff = GNM operator
    w, U = np.linalg.eigh(K)
    nz = w > 1e-9
    winv = np.zeros_like(w)
    winv[nz] = 1.0 / w[nz]
    msf = ((U ** 2) * winv).sum(1)                # mean-square fluctuation (high = flexible)
    tri = np.diag(A @ A @ A)
    with np.errstate(invalid="ignore", divide="ignore"):
        clust = np.where(deg > 1, tri / (deg * (deg - 1)), 0.0)
    return dict(N=N, A=A, deg=deg, U=U, nz=nz, winv=winv, msf=msf,
                clust=clust, beta=np.asarray(bfac, float), eigs=w)


def V_Bfactor(c):
    b = c["beta"].astype(float)
    if np.allclose(b, 0):
        return np.zeros(c["N"])
    return _z((b - b.min()) / (b.max() - b.min() + 1e-9))


def V_terminal(c, n_term=8, rsa_cut=18):
    N = c["N"]
    pos = np.arange(N)
    t_term = np.exp(-np.minimum(pos, N - 1 - pos) / n_term)   # chain termini
    rsa = np.clip(1.0 - c["deg"] / rsa_cut, 0, 1)             # exposure proxy
    return _z(0.5 * t_term + 0.5 * rsa)


def V_rigidity(c):
    return _z(_z(c["deg"]) + _z(c["clust"]) + (-_z(c["msf"])))


def V_covariance(c):
    Cov = (c["U"] * c["winv"]) @ c["U"].T          # GNM covariance = Kirchhoff pseudo-inverse
    d = np.sqrt(np.clip(np.diag(Cov), 1e-12, None))
    nDCC = Cov / np.outer(d, d)
    np.fill_diagonal(nDCC, 0.0)
    return _z(np.abs(nDCC).sum(1))


def V_modeparticipation(c, n_low=10):
    idx = np.where(c["nz"])[0][:n_low]
    return _z((c["U"][:, idx] ** 2).sum(1))


TERMS = [
    ("V_B", "B-factor flexibility", V_Bfactor),
    ("V_T", "terminal / exposure", V_terminal),
    ("V_R", "rigidity", V_rigidity),
    ("V_C", "dynamic coupling", V_covariance),
    ("V_M", "slow-mode participation", V_modeparticipation),
]


def site_potentials(coords, bfac, resnums, cutoff=8.0, site_idx=None):
    """Per-residue z-scored site potentials + optional pocket-vs-bulk enrichment."""
    c = gnm_context(coords, bfac, cutoff)
    terms = {k: fn(c) for k, _lab, fn in TERMS}
    out = {
        "cutoff": cutoff,
        "resnums": [int(r) for r in resnums],
        "labels": {k: lab for k, lab, _ in TERMS},
        "terms": {k: [round(float(v), 4) for v in vals] for k, vals in terms.items()},
        "l_eigs": [round(float(x), 4) for x in c["eigs"]],   # Kirchhoff/Laplacian spectrum
    }
    if site_idx is not None and len(site_idx):
        site_idx = np.asarray(site_idx, int)
        N = c["N"]
        n_site = len(site_idx)
        nb = N - n_site
        rng = np.random.default_rng(0)
        n_perm = 1000
        enr, sig = {}, {}
        for k, vals in terms.items():
            v = np.asarray(vals, float)
            total, site_sum = v.sum(), v[site_idx].sum()
            obs = site_sum / n_site - ((total - site_sum) / nb if nb else 0.0)
            # permutation null: random residue sets of the same size as the active site
            null = np.empty(n_perm)
            for p in range(n_perm):
                ps = v[rng.choice(N, n_site, replace=False)].sum()
                null[p] = ps / n_site - ((total - ps) / nb if nb else 0.0)
            pval = float((np.abs(null) >= abs(obs)).mean())
            enr[k] = round(float(obs), 3)
            sig[k] = {"p": round(pval, 4), "sig": bool(pval < 0.05)}
        out["enrichment"] = enr
        out["enrichment_sig"] = sig
    return out


# ── CTQW source-readiness (notebook §5h / §5i) ──────────────────────────────
# Is the active site a safe SEED for a quantum walk? The CTQW propagator e^{-iHt}
# runs on the SAME Kirchhoff/Laplacian operator the GNM is built from, so the GNM
# connectivity + rigidity of the seed predict whether a walk launched there
# propagates to distal pockets or stays trapped.

def _ctqw_build_H(coords, R_c=8.0, r0=7.0):
    """Distance-weighted Laplacian on the Cα graph (§5f): Gaussian edges
    w=exp(-(r/r0)²) cut at R_c, H = D − W (real-symmetric → e^{-iHt} unitary)."""
    D = cdist(coords, coords)
    within = (D < R_c) & (D > 1e-8)
    W = np.where(within, np.exp(-(D / r0) ** 2), 0.0)
    np.fill_diagonal(W, 0.0)
    H = np.diag(W.sum(1)) - W
    return 0.5 * (H + H.T)


def _average_mixing_matrix(H, degen_tol=1e-6):
    """Godsil average mixing matrix M̂ = Σ_r E_r∘E_r (§5f): the time-averaged
    |e^{-iHt}|² — immune to the destructive interference of a single-t snapshot."""
    w, V = np.linalg.eigh(H)
    N = H.shape[0]
    V2 = V ** 2
    if N < 2 or np.all(np.diff(w) > degen_tol):
        return V2 @ V2.T
    M = np.zeros((N, N))
    i = 0
    while i < N:
        j = i + 1
        while j < N and (w[j] - w[i]) <= degen_tol:
            j += 1
        Vg = V[:, i:j]
        P = Vg @ Vg.T
        M += P * P
        i = j
    return M


def _abs_coupling(c):
    """Absolute GNM dynamic coupling per residue (pre-z-score form of V_C):
    row-sum of |normalised cross-correlation|. High = coupled to the whole protein."""
    Cov = (c["U"] * c["winv"]) @ c["U"].T
    d = np.sqrt(np.clip(np.diag(Cov), 1e-12, None))
    nDCC = Cov / np.outer(d, d)
    np.fill_diagonal(nDCC, 0.0)
    return np.abs(nDCC).sum(1)


def _slow_participation(c, n_low=3):
    """Raw participation in the n_low slowest NON-zero GNM modes (unit-fixed)."""
    idx = np.where(c["nz"])[0][:n_low]
    return (c["U"][:, idx] ** 2).sum(1)


def _site_descriptors_z(c, idx):
    """z-scored descriptors — for cross-RESIDUE ranking within one structure."""
    return {
        "rigidity": round(float(np.mean(V_rigidity(c)[idx])), 2),
        "coupling": round(float(np.mean(V_covariance(c)[idx])), 2),
        "slow": round(float(np.mean(V_modeparticipation(c)[idx])), 2),
    }


def _site_descriptors_raw(c, idx):
    """Raw, unit-fixed descriptors — for the apo↔holo comparison (no z-score baseline, so
    the shift reflects the residues, not a changed protein-wide normalisation).
    msf high = flexible (inverse rigidity); coupling = |nDCC| row-sum; slow = mode participation."""
    return {
        "msf": float(np.mean(c["msf"][idx])),
        "coupling": float(np.mean(_abs_coupling(c)[idx])),
        "slow": float(np.mean(_slow_participation(c)[idx])),
    }


def _bootstrap_floor(c, n_seed, n_boot=200, seed=0):
    """2σ noise floor of the RAW seed-mean descriptors under random-residue sampling of the
    SAME size — the significance threshold (replaces a fixed d_z constant)."""
    rng = np.random.default_rng(seed)
    N = len(c["msf"])
    n_seed = max(1, min(int(n_seed), N - 1))
    samp = [_site_descriptors_raw(c, rng.choice(N, n_seed, replace=False)) for _ in range(n_boot)]
    return {k: float(np.std([s[k] for s in samp])) for k in samp[0]}


def _raw_shift(idx_a, idx_h, c_a, c_h, n_boot=200):
    """Raw apo→holo descriptor shift at a residue set + 2σ significance per descriptor."""
    idx_a, idx_h = np.asarray(idx_a, int), np.asarray(idx_h, int)
    if len(idx_a) == 0 or len(idx_h) == 0:
        return None
    da, dh = _site_descriptors_raw(c_a, idx_a), _site_descriptors_raw(c_h, idx_h)
    delta = {k: dh[k] - da[k] for k in da}
    fa = _bootstrap_floor(c_a, len(idx_a), n_boot)
    fb = _bootstrap_floor(c_h, len(idx_h), n_boot)
    thr = {k: 2.0 * float(np.sqrt(fa[k] ** 2 + fb[k] ** 2)) for k in da}
    sig = {k: bool(abs(delta[k]) > thr[k]) for k in da}
    return {
        "apo": {k: round(da[k], 3) for k in da},
        "holo": {k: round(dh[k], 3) for k in dh},
        "delta": {k: round(delta[k], 3) for k in delta},
        "thr": {k: round(thr[k], 3) for k in thr},
        "sig": sig,
    }


def quantum_seed_readiness(coords, bfac, resnums, site_idx, cutoff=8.0,
                           R_c=8.0, r0=7.0, distal_ang=12.0, modeled_mask=None):
    """§5h — audit whether the active site is a safe quantum-walk seed.

    Per active-site residue we flag weak seeds (low degree / weak coupling / floppy /
    interpolated coords); the set-level DISTAL-REACH is read from the real average-
    mixing matrix (fraction of walk amplitude landing > distal_ang Å from the site).
    Thresholds are RELATIVE to this protein's own quartiles. Returns None if empty."""
    site_idx = np.asarray(site_idx, int)
    coords = np.asarray(coords, float)
    N = len(coords)
    if N == 0 or len(site_idx) == 0:
        return None
    c = gnm_context(coords, bfac, cutoff)
    deg, msf = c["deg"], c["msf"]
    cpl = _abs_coupling(c)
    rig = V_rigidity(c)
    deg_lo = max(3.0, float(np.percentile(deg, 25)))   # poorly embedded
    cpl_lo = float(np.percentile(cpl, 25))             # weakly coupled
    msf_hi = float(np.percentile(msf, 75))             # floppy (low rigidity)

    H = _ctqw_build_H(coords, R_c, r0)
    M = _average_mixing_matrix(H)
    transfer = M[site_idx, :].mean(0)
    dmin = cdist(coords, coords[site_idx]).min(1)
    distal = dmin > distal_ang
    off = np.ones(N, bool)
    off[site_idx] = False
    denom = transfer[off].sum() + 1e-12
    distal_reach = float(transfer[distal & off].sum() / denom)
    # size-invariant: how much the walk concentrates on distal residues vs a uniform spread
    # (replaces hard-coded 0.05/0.15 cutoffs — works for an 88-mer or a 950-mer alike)
    distal_baseline = float((distal & off).sum()) / max(int(off.sum()), 1)
    distal_enrich = float(distal_reach / (distal_baseline + 1e-12))

    rows = []
    for i in site_idx:
        reasons = []
        if deg[i] == 0:
            reasons.append("isolated (not in contact network)")
        elif deg[i] < deg_lo:
            reasons.append(f"low connectivity (degree {int(deg[i])})")
        if cpl[i] < cpl_lo:
            reasons.append("weak dynamic coupling")
        if msf[i] > msf_hi:
            reasons.append("floppy (low rigidity)")
        is_mod = bool(modeled_mask[i]) if modeled_mask is not None else False
        if is_mod:
            reasons.append("interpolated coordinates")
        rows.append({
            "resnum": int(resnums[i]), "degree": int(deg[i]),
            "coupling": round(float(cpl[i]), 3), "rigidity": round(float(rig[i]), 2),
            "msf": round(float(msf[i]), 3), "modeled": is_mod,
            "status": "weak" if reasons else "good", "reasons": "; ".join(reasons),
        })
    n_total = len(rows)
    n_good = sum(r["status"] == "good" for r in rows)
    frac = n_good / n_total if n_total else 0.0
    recommend = [r["resnum"] for r in rows if r["status"] == "good"]
    if n_good == 0 or frac < 0.34 or distal_enrich < 0.5:
        verdict = "RISKY"
    elif frac >= 0.60 and distal_enrich >= 1.2:
        verdict = "SAFE"
    else:
        verdict = "PARTIAL"
    reach_word = ("concentrates on distal" if distal_enrich >= 1.2
                  else "spreads ~uniformly" if distal_enrich >= 0.5 else "stays local")
    detail = (f"{n_good}/{n_total} reliable seeds; distal-reach {distal_enrich:.2f}× vs "
              f"uniform ({reach_word}).")
    return {
        "verdict": verdict, "detail": detail,
        "distal_reach": round(distal_reach, 3), "distal_enrich": round(distal_enrich, 3),
        "frac_good": round(frac, 2), "n_good": n_good, "n_total": n_total,
        "recommend_seed": recommend, "per_residue": rows,
        "descriptors": _site_descriptors_z(c, site_idx),
        "descriptors_raw": {k: round(v, 3) for k, v in _site_descriptors_raw(c, site_idx).items()},
        "_gnm": c,   # internal: reused by seed_readiness_shift (stripped before serialization)
    }


def seed_readiness_shift(apo_pdb, apo_chain, holo_pdb, holo_chain=None,
                         site_resnums=None, drug_resnums=None, cutoff=8.0, n_boot=200):
    """§5i — apo vs holo seed readiness + a drug-mechanism hypothesis. Fully data-driven:

      * the DRUG POCKET is the drug-binding residues passed in (computed from the holo
        structure upstream — `rcsb.ligands_and_sites`), not a hardcoded list;
      * ORTHOSTERIC vs ALLOSTERIC is auto-detected from geometry (does the pocket overlap /
        sit within contact range of the active site?);
      * the shift uses RAW, unit-fixed descriptors (no z-score baseline drift);
      * SIGNIFICANCE comes from a per-structure BOOTSTRAP NOISE FLOOR (2σ), not a fixed d_z.

    Rule (one rule for both topologies): rigidify the DRUG-binding site AND the active site
    loses coupling OR shows a global mode reorganisation → DEACTIVATION (inhibitor). For an
    orthosteric drug the drug site IS the active site, so it reduces to rigidify+decouple."""
    site_resnums = list(site_resnums or [])
    if not site_resnums:
        return None
    apo = load_structure(apo_pdb, apo_chain)
    holo = load_structure(holo_pdb, holo_chain or apo_chain)
    if apo is None or holo is None:
        return None
    sa = res_indices(apo, site_resnums)
    sh = res_indices(holo, site_resnums)
    if len(sa) == 0 or len(sh) == 0:
        return None
    ra = quantum_seed_readiness(apo["coords"], apo["bfac"], apo["resnums"], sa,
                                cutoff, modeled_mask=apo.get("modeled"))
    rh = quantum_seed_readiness(holo["coords"], holo["bfac"], holo["resnums"], sh,
                                cutoff, modeled_mask=holo.get("modeled"))
    if ra is None or rh is None:
        return None
    ca, ch = ra.pop("_gnm"), rh.pop("_gnm")          # internal contexts; strip before return

    # drug pocket (structure-derived, passed in) → indices in each state
    pocket = sorted(set(int(r) for r in (drug_resnums or [])))
    pa, ph = res_indices(apo, pocket), res_indices(holo, pocket)

    # orthosteric vs allosteric — AUTO from geometry (holo coords)
    sep, topology = None, "unknown"
    if len(ph) and len(sh):
        sep = float(cdist(holo["coords"][ph], holo["coords"][sh]).min())
        overlap = len(set(pocket) & set(int(r) for r in site_resnums))
        topology = "orthosteric" if (overlap > 0 or sep <= cutoff) else "allosteric"

    # raw, significance-gated shift at the active-site READOUT and at the DRUG pocket
    act = _raw_shift(sa, sh, ca, ch, n_boot)
    pkt = _raw_shift(pa, ph, ca, ch, n_boot)
    reach_shift = round(rh["distal_enrich"] - ra["distal_enrich"], 3)

    # rigidify = raw MSF drops significantly; decouple = raw coupling drops significantly
    pkt_rig = bool(pkt and pkt["sig"]["msf"] and pkt["delta"]["msf"] < 0)
    act_rig = bool(act["sig"]["msf"] and act["delta"]["msf"] < 0)
    act_dec = bool(act["sig"]["coupling"] and act["delta"]["coupling"] < 0)
    act_cpl = bool(act["sig"]["coupling"] and act["delta"]["coupling"] > 0)
    act_slow = bool(act["sig"]["slow"])              # significant slow-mode reorganisation
    if (pkt_rig or act_rig) and (act_dec or act_slow):
        mechanism = "DEACTIVATION"
        mech_detail = ("rigidifies the drug-binding site + the active site loses coupling / "
                       "shows a global mode shift (inhibitor-like)")
    elif act_cpl and not act_rig and not pkt_rig:
        mechanism = "ACTIVATION"
        mech_detail = "raises coupling at the active site without rigidifying the drug site"
    else:
        mechanism = "AMBIGUOUS"
        mech_detail = "no significant rigidify + decouple pattern above the noise floor"

    return {
        "active_site": sorted(set(int(r) for r in site_resnums)),
        "topology": topology,
        "drug_active_sep": round(sep, 1) if sep is not None else None,
        "n_pocket": len(pocket),
        "apo": ra, "holo": rh,
        "active_shift": act, "pocket_shift": pkt, "reach_shift": reach_shift,
        "mechanism": mechanism, "mechanism_detail": mech_detail,
    }


def _dcc(coords, cutoff):
    """GNM dynamic cross-correlation (normalized covariance = Kirchhoff pseudo-inverse)."""
    D = cdist(coords, coords)
    A = ((D < cutoff) & (D > 1e-8)).astype(float)
    K = np.diag(A.sum(1)) - A
    w, U = np.linalg.eigh(K)
    nz = w > 1e-9
    winv = np.zeros_like(w)
    winv[nz] = 1.0 / w[nz]
    Cov = (U * winv) @ U.T
    s = np.sqrt(np.clip(np.diag(Cov), 1e-12, None))
    return Cov / np.outer(s, s)


def connectivity_change(apo_pdb, apo_chain, holo_pdb, holo_chain=None, cutoff=8.0,
                        site_resnums=None, max_n=400, r0=7.0):
    """apo→holo network reorganization on shared residues (notebook §8d), topology only:
      * DDM    distance-difference matrix  ΔD_ij = |r_ij|_holo − |r_ij|_apo
      * rewire binary contacts gained (+1) / lost (−1) at the cutoff
      * ΔDCC   change in GNM dynamic cross-correlation (allosteric coupling)
    Returns the matrices (down-sampled to max_n for display), summary stats computed on
    the FULL set, and the apo + Kabsch-aligned holo coords for the browser morph."""
    apo = load_structure(apo_pdb, apo_chain)
    holo = load_structure(holo_pdb, holo_chain or apo_chain)
    if apo is None or holo is None:
        raise ValueError(f"could not load apo {apo_pdb} or holo {holo_pdb}")
    common = np.intersect1d(apo["resnums"], holo["resnums"])
    if len(common) < 10:
        raise ValueError(f"only {len(common)} common residues between {apo_pdb}/{holo_pdb} "
                         f"— need ≥10 to compute the connectivity change")
    ia = np.array([np.where(apo["resnums"] == r)[0][0] for r in common])
    ib = np.array([np.where(holo["resnums"] == r)[0][0] for r in common])
    Ca, Ch = apo["coords"][ia], holo["coords"][ib]
    n = len(common)
    Chk = _kabsch_rotate(Ch, Ca)                       # aligned holo, for the morph

    Da, Dh = cdist(Ca, Ca), cdist(Ch, Ch)
    DDM = Dh - Da
    Aa = (Da < cutoff) & (Da > 1e-8)
    Ah = (Dh < cutoff) & (Dh > 1e-8)
    rewire = Ah.astype(int) - Aa.astype(int)
    dDCC = _dcc(Ch, cutoff) - _dcc(Ca, cutoff)

    mob = np.sqrt((DDM ** 2).mean(1))                  # per-residue reorganization
    hot = np.argsort(mob)[::-1][:5]
    summary = {
        "n_shared": int(n),
        "ddm_max": round(float(np.abs(DDM).max()), 2),
        "contacts_formed": int((rewire > 0).sum() // 2),
        "contacts_broken": int((rewire < 0).sum() // 2),
        "mean_abs_ddcc": round(float(np.abs(dDCC).mean()), 3),
        "most_reorganized": [int(common[i]) for i in hot],
    }

    # down-sample matrices/coords for the payload if large (summary stays on full set)
    if n > max_n:
        idx = np.unique(np.linspace(0, n - 1, max_n).astype(int))
    else:
        idx = np.arange(n)
    sub = np.ix_(idx, idx)
    site = set(int(r) for r in (site_resnums or []))
    common_sub = [int(common[i]) for i in idx]
    site_positions = [k for k, r in enumerate(common_sub) if r in site]

    return {
        "apo": apo_pdb, "holo": holo_pdb, "cutoff": cutoff, "r0": r0,
        "n_shared": int(n), "downsampled": bool(n > max_n),
        "resnums": common_sub,
        "site_positions": site_positions,
        "summary": summary,
        "ddm": np.round(DDM[sub], 2).tolist(),
        "rewire": rewire[sub].astype(int).tolist(),
        "ddcc": np.round(dDCC[sub], 3).tolist(),
        "apo_coords": np.round(Ca[idx], 3).tolist(),
        "holo_coords": np.round(Chk[idx], 3).tolist(),
    }


def site_potential_shift(apo_pdb, apo_chain, holo_pdb, holo_chain=None,
                         site_resnums=None, cutoff=8.0):
    """Site potentials for apo and holo, plus the apo->holo shift on shared residues
    (notebook §5c). Each structure is z-scored within itself, then subtracted, so the
    shift captures how the drug binding reshapes the dynamic network per residue."""
    apo = load_structure(apo_pdb, apo_chain)
    holo = load_structure(holo_pdb, holo_chain or apo_chain)
    if apo is None or holo is None:
        raise ValueError(f"could not load apo {apo_pdb} or holo {holo_pdb}")

    site = list(site_resnums or [])
    a = site_potentials(apo["coords"], apo["bfac"], apo["resnums"], cutoff,
                        site_idx=res_indices(apo, site) if site else None)
    h = site_potentials(holo["coords"], holo["bfac"], holo["resnums"], cutoff,
                        site_idx=res_indices(holo, site) if site else None)

    keys = list(a["terms"].keys())
    a_map = {k: dict(zip(a["resnums"], a["terms"][k])) for k in keys}
    h_map = {k: dict(zip(h["resnums"], h["terms"][k])) for k in keys}
    shared = sorted(set(a["resnums"]) & set(h["resnums"]))

    delta_terms = {k: [round(h_map[k][r] - a_map[k][r], 4) for r in shared] for k in keys}
    siteset = set(site)
    sidx = [i for i, r in enumerate(shared) if r in siteset]
    bidx = [i for i, r in enumerate(shared) if r not in siteset]
    delta_enr = {}
    if sidx:
        for k in keys:
            v = np.array(delta_terms[k], float)
            delta_enr[k] = round(float(v[sidx].mean()
                                       - (v[bidx].mean() if bidx else 0.0)), 3)

    # §5d: apo->holo Cα displacement (Kabsch) + coordination-number change
    structural = None
    if len(shared) >= 5:
        a_idx = {int(r): i for i, r in enumerate(apo["resnums"])}
        h_idx = {int(r): i for i, r in enumerate(holo["resnums"])}
        P = np.array([apo["coords"][a_idx[r]] for r in shared], float)   # apo
        Q = np.array([holo["coords"][h_idx[r]] for r in shared], float)  # holo
        disp = np.linalg.norm(P - _kabsch_rotate(Q, P), axis=1)
        deg_a = _coordination(apo["coords"], cutoff)
        deg_h = _coordination(holo["coords"], cutoff)
        dcoord = np.array([deg_h[h_idx[r]] - deg_a[a_idx[r]] for r in shared], float)
        structural = {
            "resnums": shared,
            "ca_displacement": [round(float(x), 3) for x in disp],
            "d_coordination": [round(float(x), 1) for x in dcoord],
            "ca_rmsd": round(float(np.sqrt((disp ** 2).mean())), 3),
            "max_disp": round(float(disp.max()), 3),
        }

    return {
        "labels": a["labels"],
        "active_site": sorted(siteset),
        "apo": a,
        "holo": h,
        "delta": {"resnums": shared, "terms": delta_terms,
                  "labels": a["labels"], "enrichment": delta_enr},
        "structural": structural,
        "n_shared": len(shared),
    }
