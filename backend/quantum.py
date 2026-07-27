"""
Phase 2 — quantum solving. Slice 1: GRAPH-TRAP DIAGNOSTIC (notebook §2c).

Before seeding a continuous-time quantum walk (CTQW) at the active site, map where a
walker would STALL — localized "dead-end" modes of the transport operator. This is a
PRE-FLIGHT connectivity/failure diagnostic, NOT allosteric-site discovery.

Two layers, honestly separated:
  1. OPERATOR-LEVEL traps — localized eigenstates of the graph operator H (high inverse
     participation ratio, small participation) whose amplitude is confined away from their
     output neighbours. A property of H's eigenVECTORS alone (no time evolution, no seed).
     By its own audit a plain node-degree threshold reproduces most of the set, so this is
     reported as a CLASSICAL connectivity diagnostic with a degree baseline + a
     degree-matched dynamical (time-averaged-return) gate.
  2. SEED-COUPLED traps — which of those dead-ends the walk SEEDED AT THE ACTIVE SITE
     actually feeds. A localized mode φ_k stalls the active-site walk only in proportion to
     the seed's overlap with it; the long-time trapped probability at node j is
     Σ_k |⟨j|φ_k⟩|² |⟨φ_k|ψ0⟩|²  (standard CTQW limiting distribution). We restrict that
     sum to the localized modes → the traps the ACTUAL active-site walk hits. [OUR framing;
     grounded, not from a single paper — flagged as such.]

Scope caveats (fact-checked 2026-07-26, adversarial multi-agent):
  * "trap" here = a Hermitian localized eigenstate, NOT the absorbing-sink meaning common in
    the CTQW literature — relabelled "stall / localized dead-end" in user text.
  * "boundary-confinement" is a PROBABILITY (|v|²) ratio, NOT a signed-amplitude dark-state
    test (a real dark state needs coherent cancellation).
  * finite protein graphs show FINITE-SIZE / disorder-induced localization, NOT a true
    (thermodynamic-limit) Anderson transition.
  * near-degenerate multiplets are excluded (the eigenbasis is arbitrary inside them; the
    Hadamard/average-mixing formula is basis-dependent there).

References (corrected):
  * participation ratio / IPR: Bell & Dean, Discuss. Faraday Soc. 50, 55 (1970);
    generalized IPR: Wegner, Z. Phys. B 36, 209 (1980); review: Kramer & MacKinnon,
    Rep. Prog. Phys. 56, 1469 (1993).  [replaces a mis-cited "Thouless, J.Phys.C 7 (1974)"]
  * CTQW localization on disordered networks: Mülken & Blumen, Phys. Rep. 502, 37 (2011).
  * localization vs coordination number (Anderson model): Abou-Chacra, Anderson & Thouless,
    J. Phys. C 6, 1734 (1973)  — W_c ∝ K ln K; holds for uncorrelated on-site disorder, NOT
    universal (flat-band lattices are a counterexample).
  * time-averaged CTQW / average mixing: Godsil, J. Combin. Theory A 120, 1649 (2013).
"""
from typing import Optional, List

import numpy as np
from scipy.spatial.distance import cdist

# ── exposed, overridable diagnostic thresholds (no magic numbers baked into logic) ──
TRAP_DEGEN_TOL = 1e-3       # near-degeneracy: eigenvalue gap below this × spectral range
TRAP_IPR_QTILE = 0.90       # a state is "localized" if its IPR is in the top 10%
TRAP_MAX_PARTIC = 8.0       # …and it occupies ≤ this many nodes (participation = 1/IPR)
TRAP_SUPPORT_FR = 0.25      # a node is in a state's "support" if p ≥ this × the state's peak p
TRAP_LEAK_MAX = 0.35        # max boundary-confinement (prob on output neighbours / on support)
TRAP_PERIPH_QT = 0.25       # "peripheral" trap = degree in the bottom quartile
TRAP_EXCLUDE_NEARDEGEN = True
TRAP_DYN_CTRL = 20          # degree-matched control sample for the dynamical gate
TRAP_DYN_TIMES = np.linspace(0.5, 40.0, 60)
TRAP_CUTOFF_SWEEP = [6.0, 7.0, 8.0, 10.0, 12.0]


# ── transport operator (notebook §2/§2b, ported verbatim) ───────────────────────────
def contact_weight(coords, cutoff, power=1.0):
    """Weighted Cα contact graph: W_ij = 1/D_ij^power for D_ij < cutoff, else 0."""
    D = cdist(coords, coords)
    np.fill_diagonal(D, np.inf)
    return np.where(D < cutoff, 1.0 / (D ** power), 0.0)


def normalized_laplacian(W):
    """L = I − D^(−½) W D^(−½); isolated nodes kept inert (no NaN). (§2)"""
    W = W.copy()
    np.fill_diagonal(W, 0.0)
    d = W.sum(1)
    nz = d > 1e-12
    dinv = np.zeros_like(d)
    dinv[nz] = 1.0 / np.sqrt(d[nz])
    A = (dinv[:, None] * W) * dinv[None, :]
    L = np.eye(len(d)) - A
    L[~nz, :] = 0.0
    L[:, ~nz] = 0.0
    return L


def build_hamiltonian(coords, bfac, family, p):
    """Graph Hamiltonian family (notebook §2). Default GNM = normalized Laplacian of the
    weighted contact graph (the project's benchmark operator base). The B-factor/disorder
    families add a diagonal site potential. ANM/LMS (3N Hessian) are not ported here."""
    N = len(coords)
    cutoff = p["cutoff"]
    bn = (bfac - bfac.min()) / (np.ptp(bfac) + 1e-9)          # 0 rigid .. 1 disordered
    D = cdist(coords, coords)
    np.fill_diagonal(D, np.inf)
    if family == "GNM":
        return normalized_laplacian(contact_weight(coords, cutoff, p.get("power", 1.0)))
    if family == "GNM_bfactor":
        Bm = bfac[:, None] + bfac[None, :] + 1e-2
        return normalized_laplacian((D < cutoff).astype(float) / Bm)
    if family == "H10_disorder_supp":
        W = contact_weight(coords, cutoff, p.get("power", 1.0))
        return normalized_laplacian(W) + np.diag(p.get("mu", 1.0) * bn)
    if family == "H10B_disorder_bfactor":
        rij = 1.0 / (bfac[:, None] + bfac[None, :] + 1e-2)
        return normalized_laplacian((D < cutoff).astype(float) * rij) + np.diag(p.get("mu", 0.5) * bn)
    if family == "rigidity_laplacian":
        rij = 2.0 / (bfac[:, None] + bfac[None, :] + 1e-2)
        return normalized_laplacian((D < cutoff).astype(float) * rij)
    if family == "terminal_suppressed":
        W = contact_weight(coords, cutoff, p.get("power", 1.0))
        f = p.get("term_frac", 0.08)
        k = max(1, int(f * N))
        pot = np.zeros(N)
        pot[:k] = p.get("mu", 1.0)
        pot[-k:] = p.get("mu", 1.0)
        return normalized_laplacian(W) + np.diag(pot)
    raise ValueError(f"unsupported/unported Hamiltonian family: {family}")


def spectral_filter(H, lam_exp, lam_ln):
    """NES spectral filter (notebook §2b): reshapes eigenVALUES, leaves eigenVECTORS intact.
    Note: since traps are a property of the eigenvectors, this is INERT for trap detection
    (verified) — kept for fidelity/future tuning; with lam=0 it is exactly the identity."""
    w, V = np.linalg.eigh(H)
    mx = np.abs(w).max() + 1e-12
    nw = np.abs(w) / mx
    w2 = w * np.exp(-lam_exp * nw ** 2) * (1 + lam_ln * np.log1p(nw))
    return (V * w2) @ V.T


# ── operator-level trap detection (notebook §2c, math unchanged) ─────────────────────
def find_ctqw_traps(H, degen_tol=TRAP_DEGEN_TOL, localize_quantile=TRAP_IPR_QTILE,
                    max_participation=TRAP_MAX_PARTIC, support_frac=TRAP_SUPPORT_FR,
                    leak_max=TRAP_LEAK_MAX, exclude_near_degenerate=TRAP_EXCLUDE_NEARDEGEN,
                    top_k=None):
    """Localized 'stall' modes of Hermitian H. IPR/support/boundary-confinement math is the
    audited §2c; optional exclusion of basis-arbitrary near-degenerate multiplets."""
    H = np.asarray(H, float)
    N = H.shape[0]
    assert np.allclose(H, H.T, atol=1e-8), "transport operator must be Hermitian"
    Abool = (np.abs(H - np.diag(np.diag(H))) > 1e-12).astype(float)
    w, V = np.linalg.eigh(H)
    P = V ** 2                                               # P[i,k] = |⟨i|φ_k⟩|²
    ipr = (P ** 2).sum(0)
    pr = 1.0 / np.maximum(ipr, 1e-300)
    scale = (w[-1] - w[0]) + 1e-12
    gaps = np.diff(w)
    grp = np.concatenate([[0], np.cumsum(gaps > degen_tol * scale)])
    _, counts = np.unique(grp, return_counts=True)
    near_degenerate = counts[grp] > 1
    localized = (ipr >= np.quantile(ipr, localize_quantile)) & (pr <= max_participation)
    if exclude_near_degenerate:
        localized = localized & (~near_degenerate)
    peakP = P[P.argmax(0), np.arange(N)]
    S = (P.T >= support_frac * peakP[:, None])              # (states, nodes) support mask
    supp_w = (S * P.T).sum(1)
    boundary = ((S @ Abool) > 0) & (~S)
    boundary_amp = (boundary * P.T).sum(1)
    boundary_confinement = boundary_amp / np.maximum(supp_w, 1e-300)
    trapping = localized & (boundary_confinement <= leak_max)
    trap_strength = (S[trapping] * P.T[trapping]).sum(0)
    tn = np.where(trap_strength > 0)[0]
    order = tn[np.argsort(trap_strength[tn])[::-1]]
    if top_k:
        order = order[:int(top_k)]
    return dict(eigvals=w, IPR=ipr, PR=pr, near_degenerate=near_degenerate,
                degree=Abool.sum(1), Abool=Abool, trap_nodes=order,
                trap_strength=trap_strength, boundary_confinement=boundary_confinement,
                trapping=trapping, P=P, S=S,
                n_trapping_states=int(trapping.sum()),
                n_near_degenerate=int(near_degenerate.sum()),
                median_gap=float(np.median(gaps)), degen_tol_abs=float(degen_tol * scale))


def trap_return_prob(H, times=TRAP_DYN_TIMES):
    """Time-averaged CTQW return probability per node: mean_t |U(t)_ii|² (vectorized)."""
    w, V = np.linalg.eigh(H)
    P = V ** 2
    occ = np.zeros(len(w))
    for t in times:
        occ += np.abs(P @ np.exp(-1j * w * float(t))) ** 2 / len(times)
    return occ


def dynamical_gate(occ, degree, trap_nodes, n_ctrl=TRAP_DYN_CTRL, seed=0):
    """Keep traps whose time-avg return beats a DEGREE-MATCHED (deg ±1) random control."""
    rng = np.random.default_rng(seed)
    N = len(occ)
    keep = []
    for i in trap_nodes:
        pool = np.array([j for j in range(N) if abs(degree[j] - degree[i]) <= 1 and j != i])
        ctrl = occ[rng.choice(pool, min(n_ctrl, len(pool)), replace=False)].mean() if len(pool) else np.inf
        if occ[i] > ctrl:
            keep.append(int(i))
    return keep


# ── seed-coupling to the active site (OUR framing — grounded, flagged) ───────────────
def seed_trap_coupling(r, seed_idx):
    """Which operator-level traps the ACTIVE-SITE-seeded walk actually feeds.

    Long-time trapped probability at node j from seed ψ0 = Σ_k |⟨j|φ_k⟩|²|⟨φ_k|ψ0⟩|²; we
    restrict k to the localized (trapping) modes and use the app's incoherent seed
    convention (mean over active-site residues), consistent with the average-mixing
    seed-readiness already in analysis.py. Returns per-node seed-fed trap strength."""
    seed_idx = np.asarray(seed_idx, int)
    kk = np.where(r["trapping"])[0]
    if len(seed_idx) == 0 or len(kk) == 0:
        return None
    P = r["P"]
    s_k = P[np.ix_(seed_idx, kk)].mean(0)                   # mean active-site weight on each trap mode
    Sk = r["S"][kk]                                         # (nk, nodes)
    Pk = P[:, kk].T                                         # (nk, nodes)
    seed_trap_strength = (s_k[:, None] * Sk * Pk).sum(0)    # (nodes,)
    return dict(seed_trap_strength=seed_trap_strength, mode_seed_overlap=s_k, trap_mode_idx=kk)


def _stability_band(H):
    """Trap-set robustness across thresholds → stable-core vs threshold-dependent + Jaccard."""
    default = set(find_ctqw_traps(H)["trap_nodes"].tolist())
    sets = []
    for lm in (0.25, 0.35, 0.45):
        for mp in (6.0, 8.0, 10.0):
            sets.append(set(find_ctqw_traps(H, leak_max=lm, max_participation=mp)["trap_nodes"].tolist()))
    core = set.intersection(*sets) if sets else set()
    union = set.union(*sets) if sets else set()
    jac = [len(s & default) / max(1, len(s | default)) for s in sets]
    return core, union, (min(jac), max(jac))


def _res_indices(resnums, wanted):
    resnums = np.asarray(resnums)
    want = set(int(r) for r in (wanted or []))
    return np.array([i for i, r in enumerate(resnums) if int(r) in want], int)


def graph_trap_scan(coords, bfac, resnums, seed_resnums=None, cutoff=8.0, family="GNM",
                    power=1.0, lam_exp=0.0, lam_ln=0.0, do_stability=True, do_cutoff_sweep=True):
    """Full §2c graph-trap diagnostic for ONE structure, seeded at the active site.

    Returns a JSON-serializable payload: operator-level traps + degree baseline + dynamical
    gate + near-degeneracy audit + (if seed given) the seed-coupled traps the active-site
    walk actually feeds + optional threshold-stability + cutoff-sweep."""
    coords = np.asarray(coords, float)
    bfac = np.asarray(bfac, float)
    resnums = np.asarray(resnums)
    N = len(coords)
    params = {"cutoff": float(cutoff), "power": power}
    H = spectral_filter(build_hamiltonian(coords, bfac, family, params), lam_exp, lam_ln)
    r = find_ctqw_traps(H)
    deg = r["degree"]
    tn = list(r["trap_nodes"])
    periph = float(np.quantile(deg, TRAP_PERIPH_QT)) if N else 0.0

    # classical baseline: are the traps just the lowest-degree nodes?
    low = set(np.argsort(deg)[:max(1, len(tn))].tolist())
    baseline_overlap = len(set(tn) & low)
    # dynamical gate vs degree-matched control
    occ = trap_return_prob(H)
    validated = dynamical_gate(occ, deg, tn)

    def rn(idxs):
        return [int(resnums[i]) for i in idxs]

    out = {
        "n_residues": int(N), "family": family, "cutoff": float(cutoff),
        "resnums": [int(x) for x in resnums],
        "eigvals": [round(float(x), 5) for x in r["eigvals"]],
        "ipr": [round(float(x), 5) for x in r["IPR"]],
        "near_degenerate": [bool(x) for x in r["near_degenerate"]],
        "degree": [int(x) for x in deg],
        "trap_strength": [round(float(x), 5) for x in r["trap_strength"]],
        "trap_nodes": rn(tn),
        "trap_nodes_peripheral": rn([i for i in tn if deg[i] <= periph]),
        "dyn_gate_pass": rn(validated),
        "baseline_overlap": baseline_overlap, "n_flagged": len(tn),
        "n_trapping_states": r["n_trapping_states"],
        "n_near_degenerate": r["n_near_degenerate"],
        "near_degen_pct": round(100.0 * r["n_near_degenerate"] / max(1, N), 1),
        "degen_tol_abs": round(r["degen_tol_abs"], 6),
        "median_gap": round(r["median_gap"], 6),
        "spectral_filter_inert_for_traps": True,
    }

    # seed-coupled traps (the active-site walk's actual dead-ends)
    seed_idx = _res_indices(resnums, seed_resnums)
    out["active_site"] = sorted(int(x) for x in (seed_resnums or []))
    sc = seed_trap_coupling(r, seed_idx) if len(seed_idx) else None
    if sc is not None:
        sts = sc["seed_trap_strength"]
        order = np.argsort(sts)[::-1]
        seeded = [int(i) for i in order if sts[i] > 0]
        out["seed_trap_strength"] = [round(float(x), 6) for x in sts]
        out["seed_trap_nodes"] = rn(seeded)                       # traps the active-site walk feeds
        out["seed_reaches_traps"] = int(len(seeded))
    else:
        out["seed_trap_strength"] = None
        out["seed_trap_nodes"] = []
        out["seed_reaches_traps"] = 0

    if do_stability:
        core, union, (jlo, jhi) = _stability_band(H)
        out["stable_core"] = rn(sorted(core))
        out["threshold_dependent"] = int(len(union) - len(core))
        out["jaccard_band"] = [round(jlo, 3), round(jhi, 3)]
    if do_cutoff_sweep:
        sweep = []
        for c0 in TRAP_CUTOFF_SWEEP:
            Hc = spectral_filter(build_hamiltonian(coords, bfac, family, {"cutoff": c0, "power": power}),
                                 lam_exp, lam_ln)
            rc = find_ctqw_traps(Hc)
            sweep.append({"cutoff": float(c0), "n_traps": int(len(rc["trap_nodes"])),
                          "near_degen_pct": round(100.0 * rc["n_near_degenerate"] / max(1, N), 1)})
        out["cutoff_sweep"] = sweep
    return out
