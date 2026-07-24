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


def _raw_arrays(c):
    """The three raw per-residue descriptor arrays, computed ONCE per structure. The |nDCC|
    coupling is the O(N³) part (full GNM covariance) — precompute it so the bootstrap
    noise-floor never recomputes it per resample (that dominated /api/connectivity-change)."""
    return {
        "msf": np.asarray(c["msf"], float),
        "coupling": _abs_coupling(c),
        "slow": _slow_participation(c),
    }


def _mean_desc(arrays, idx):
    """Seed-mean of the precomputed raw descriptor arrays over residue indices `idx`."""
    return {k: float(np.mean(arrays[k][idx])) for k in arrays}


def _site_descriptors_raw(c, idx):
    """Raw, unit-fixed descriptors — for the apo↔holo comparison (no z-score baseline, so
    the shift reflects the residues, not a changed protein-wide normalisation).
    msf high = flexible (inverse rigidity); coupling = |nDCC| row-sum; slow = mode participation."""
    return _mean_desc(_raw_arrays(c), np.asarray(idx, int))


def _bootstrap_floor(arrays, n_seed, n_boot=200, seed=0):
    """2σ noise floor of the RAW seed-mean descriptors under random-residue sampling of the
    SAME size — the significance threshold (replaces a fixed d_z constant). Operates on the
    precomputed per-residue arrays (no O(N³) recompute per sample)."""
    rng = np.random.default_rng(seed)
    N = len(arrays["msf"])
    n_seed = max(1, min(int(n_seed), N - 1))
    samp = [_mean_desc(arrays, rng.choice(N, n_seed, replace=False)) for _ in range(n_boot)]
    return {k: float(np.std([s[k] for s in samp])) for k in samp[0]}


def _raw_shift(idx_a, idx_h, arrays_a, arrays_h, n_boot=200):
    """Raw apo→holo descriptor shift at a residue set + 2σ significance per descriptor.
    `arrays_a`/`arrays_h` are precomputed per-structure raw arrays (see `_raw_arrays`)."""
    idx_a, idx_h = np.asarray(idx_a, int), np.asarray(idx_h, int)
    if len(idx_a) == 0 or len(idx_h) == 0:
        return None
    da, dh = _mean_desc(arrays_a, idx_a), _mean_desc(arrays_h, idx_h)
    delta = {k: dh[k] - da[k] for k in da}
    fa = _bootstrap_floor(arrays_a, len(idx_a), n_boot)
    fb = _bootstrap_floor(arrays_h, len(idx_h), n_boot)
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

    # raw, significance-gated shift at the active-site READOUT and at the DRUG pocket.
    # Precompute the per-structure raw arrays ONCE (the O(N³) coupling) and reuse them for
    # both the active-site and pocket shifts — this is the fix for the slow endpoint.
    arrays_a, arrays_h = _raw_arrays(ca), _raw_arrays(ch)
    act = _raw_shift(sa, sh, arrays_a, arrays_h, n_boot)
    pkt = _raw_shift(pa, ph, arrays_a, arrays_h, n_boot)
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


def _coords_on(s, common):
    pos = {int(r): i for i, r in enumerate(s["resnums"])}
    return np.array([s["coords"][pos[int(r)]] for r in common], float)


# Quality gates for auto-discovered conformers (overridable — not tuned to any target).
# A same-protein conformer shares MOST of the apo's residues and superposes with a
# reasonable Cα RMSD; a different construct / wrong chain / gross outlier fails one of
# these. Defaults sit in the empirically-observed gap between valid KRAS conformers
# (≥90% overlap, ≤~7 Å after loop flexibility) and the 1KZP outlier (68% overlap, 14 Å).
MIN_OVERLAP_FRAC = 0.80     # ≥80% of the apo's residues must be present (else wrong protein/chain)
MAX_ALIGN_RMSD = 10.0       # Å — reject gross mis-alignment even at high overlap


def _rmsd_on(coords_by_resnum, st, resnums):
    """Kabsch Cα RMSD between a reference (dict resnum→coord) and `st`, on shared `resnums`."""
    pos = {int(r): j for j, r in enumerate(st["resnums"])}
    A = np.array([coords_by_resnum[int(r)] for r in resnums], float)
    C = np.array([st["coords"][pos[int(r)]] for r in resnums], float)
    return float(np.sqrt(((_kabsch_rotate(C, A) - A) ** 2).sum(1).mean()))


def _load_best_chain(pdb_id, apo_resset, chain_hint=None, max_chains=8):
    """Return (structure, chain, overlap) for the chain of `pdb_id` whose residue numbers
    best overlap the apo residue set — so complexes (e.g. antibody-bound 3GFT) resolve to
    OUR protein's chain, not blindly chain A. Parses the file ONCE. (None, None, 0) if none."""
    from .rcsb import chain_summary
    try:
        chains = [c["chain"] for c in chain_summary(pdb_id)][:max_chains]
    except Exception:
        chains = []
    if chain_hint and chain_hint not in chains:
        chains = [chain_hint] + chains
    if not chains:
        chains = [chain_hint or "A"]
    st = load_structure(pdb_id, ",".join(chains))
    if st is None:
        return (None, None, 0)
    chain_arr = np.asarray([str(x) for x in st["chains"]])
    resn = np.asarray([int(r) for r in st["resnums"]], int)
    coords = np.asarray(st["coords"], float)
    bfac = np.asarray(st["bfac"], float)
    best_ch, best_ov = None, 0
    for ch in dict.fromkeys(chain_arr.tolist()):          # unique, order-preserving
        ov = len(apo_resset & set(resn[chain_arr == ch].tolist()))
        if ov > best_ov:
            best_ch, best_ov = ch, ov
    if best_ch is None:
        return (None, None, 0)
    m = chain_arr == best_ch
    return ({"resnums": resn[m], "coords": coords[m], "bfac": bfac[m], "chains": chain_arr[m]},
            best_ch, best_ov)


def _auto_intermediates(apo_pdb, chain, apo, holo, holo_pdb, k, pool_cap=12,
                        min_overlap_frac=MIN_OVERLAP_FRAC, max_align_rmsd=MAX_ALIGN_RMSD):
    """Auto-pick k real, well-aligning structures of the SAME protein, ordered apo→holo.

    For each candidate we (1) pick the chain that actually matches our protein (max residue
    overlap), (2) REJECT it if it shares <min_overlap_frac of the apo's residues or its
    best-fit Cα RMSD to apo exceeds max_align_rmsd (wrong construct / wrong chain / gross
    outlier), then (3) order survivors by progress = RMSD→apo / (RMSD→apo + RMSD→holo) and
    pick k spread evenly. Returns (chosen[{pdb_id, chain, progress}], rejected[{pdb_id, reason}])."""
    from .discovery import same_protein_entries
    pool = [p for p in same_protein_entries(apo_pdb, max_n=40) if p != str(holo_pdb).upper()]
    apo_resset = set(int(r) for r in apo["resnums"])
    holo_resset = set(int(r) for r in holo["resnums"])
    apo_pos = {int(r): apo["coords"][i] for i, r in enumerate(apo["resnums"])}
    holo_pos = {int(r): holo["coords"][i] for i, r in enumerate(holo["resnums"])}
    n_apo = max(len(apo_resset), 1)
    accepted, rejected, loaded = [], [], 0
    for pid in pool:
        if loaded >= pool_cap:
            break
        st, ch, ov = _load_best_chain(pid, apo_resset, chain)
        if st is None:
            continue
        loaded += 1
        if ov / n_apo < min_overlap_frac:            # different protein / construct / wrong chain
            rejected.append({"pdb_id": pid, "reason": f"only {ov}/{n_apo} residues shared "
                             f"({ov / n_apo:.0%} < {min_overlap_frac:.0%})"})
            continue
        shared_a = sorted(apo_resset & set(int(r) for r in st["resnums"]))
        r_apo = _rmsd_on(apo_pos, st, shared_a)
        if r_apo > max_align_rmsd:                   # gross mis-alignment
            rejected.append({"pdb_id": pid, "reason": f"poor alignment to apo "
                             f"({r_apo:.1f} Å > {max_align_rmsd:.0f} Å)"})
            continue
        shared_h = sorted(holo_resset & set(int(r) for r in st["resnums"]))
        r_holo = _rmsd_on(holo_pos, st, shared_h) if len(shared_h) >= 10 else r_apo
        accepted.append({"pdb_id": pid, "chain": ch,
                         "progress": r_apo / (r_apo + r_holo + 1e-9), "rmsd_apo": round(r_apo, 2)})
    accepted.sort(key=lambda d: d["progress"])
    if k >= len(accepted):
        chosen = accepted
    else:
        chosen, used = [], set()
        for t in np.linspace(0.0, 1.0, k + 2)[1:-1]:          # interior progress targets
            cand = [d for d in accepted if d["pdb_id"] not in used]
            if not cand:
                break
            b = min(cand, key=lambda d: abs(d["progress"] - t))
            used.add(b["pdb_id"]); chosen.append(b)
        chosen.sort(key=lambda d: d["progress"])
    return chosen, rejected


def morph_frames(apo_pdb, apo_chain, holo_pdb, holo_chain=None, inter_pdbs=None,
                 n_frames=None, cutoff=8.0, max_n=400):
    """Real apo→intermediate→holo keyframes for the 3D graph animation.

    The node/edge set is the CANONICAL apo∩holo residue set (same residues, same cutoff as
    the connectivity graph) so straight-line and real modes are directly comparable. Each
    intermediate only REPOSITIONS the residues it actually contains (Kabsch-aligned to apo);
    residues a given PDB lacks follow the apo→holo interpolation for that frame, so the graph
    never loses nodes/edges or fragments. Intermediates are AUTO-discovered for the same
    protein when `n_frames` > 2; `inter_pdbs` is an optional explicit override."""
    apo = load_structure(apo_pdb, apo_chain)
    holo = load_structure(holo_pdb, holo_chain or apo_chain)
    if apo is None or holo is None:
        raise ValueError(f"could not load apo {apo_pdb} or holo {holo_pdb}")
    apo_resset = set(int(r) for r in apo["resnums"])
    inter_ids = [str(p).strip().upper() for p in (inter_pdbs or []) if str(p).strip()]
    auto_selected, rejected, inter_specs = [], [], []      # inter_specs = [(pid, chain)]
    if inter_ids:                                          # explicit override
        for pid in inter_ids:
            st, ch, ov = _load_best_chain(pid, apo_resset)  # still pick the matching chain
            if st is None:
                raise ValueError(f"could not load intermediate {pid}")
            inter_specs.append((pid, ch))
    elif n_frames and int(n_frames) > 2:                   # auto-discover (chain-checked + QC-gated)
        chosen, rejected = _auto_intermediates(
            apo_pdb, apo_chain, apo, holo, holo_pdb, int(n_frames) - 2)
        inter_specs = [(d["pdb_id"], d["chain"]) for d in chosen]
        auto_selected = [{"pdb_id": d["pdb_id"], "chain": d["chain"],
                          "progress": round(d["progress"], 2)} for d in chosen]

    # canonical set = apo ∩ holo (identical nodes/edges to the connectivity graph)
    common = np.array(sorted(apo_resset & set(int(r) for r in holo["resnums"])), int)
    if len(common) < 10:
        raise ValueError(f"only {len(common)} residues shared between apo and holo — need ≥10")
    if len(common) > max_n:
        common = common[np.unique(np.linspace(0, len(common) - 1, max_n).astype(int))]
    ref = _coords_on(apo, common)                          # apo endpoint (frame 0)
    holo_c = _kabsch_rotate(_coords_on(holo, common), ref)  # holo endpoint, aligned to apo

    inter_states = []
    for pid, ch in inter_specs:
        st = load_structure(pid, ch)
        if st is not None:
            inter_states.append((pid, st))

    K = len(inter_states) + 2
    frames = [np.round(ref, 3).tolist()]
    labels = [f"apo ({str(apo_pdb).upper()})"]
    coverage = []
    for k, (pid, st) in enumerate(inter_states, start=1):
        p = k / (K - 1)
        C = (1.0 - p) * ref + p * holo_c                   # residues this PDB lacks follow the line
        posmap = {int(r): j for j, r in enumerate(st["resnums"])}
        present = [i for i, r in enumerate(common) if int(r) in posmap]
        if len(present) >= 3:                              # place its real residues (aligned to apo)
            sub = np.array([st["coords"][posmap[int(common[i])]] for i in present], float)
            sub_al = _kabsch_rotate(sub, ref[present])
            for j, i in enumerate(present):
                C[i] = sub_al[j]
        frames.append(np.round(C, 3).tolist())
        labels.append(pid)
        coverage.append({"pdb_id": pid, "covered": len(present), "of": int(len(common))})
    frames.append(np.round(holo_c, 3).tolist())
    labels.append(f"holo ({str(holo_pdb).upper()})")

    return {
        "resnums": [int(r) for r in common], "cutoff": cutoff,
        "frames": frames, "frame_labels": labels, "auto_selected": auto_selected,
        "rejected": rejected, "coverage": coverage,
        "n_frames": len(frames), "n_shared": int(len(common)),
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
