"""Phase 1b -- apo/holo superposition, cryptic-openness gate, and ANM
mode-projection (Tama-Sanejouand cumulative overlap).

This is the single most important physical gate in the pipeline: whether
the apo->holo pocket-opening direction is even present in the apo
structure's low-frequency modes. Everything downstream (ceiling, LOPO, the
holo-direction module) is conditioned on this module's per-target verdict.

Legal to see holo here -- this module characterizes known apo/holo pairs,
per HOLO_DIRECTION_MODULE.md's leakage firewall ("using holo to
characterize the method... is legal; using holo to parameterize the
predictor is not"). Nothing computed here may leak into a per-target
scoring knob later.

Kabsch/SVD alignment is *ported* (not imported) from backend/geometry.py
(TASK-0030's dedup of backend/analysis.py::_kabsch_rotate and
backend/discovery.py::_kabsch) -- allostery/ is an independent research
package and must not import from backend/, a live FastAPI service, or vice
versa (TASK-0018).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# ---------------------------------------------------------------------------
# Kabsch/SVD alignment (ported from backend/geometry.py, TASK-0030)
# ---------------------------------------------------------------------------

def kabsch_fit(mobile: np.ndarray, ref: np.ndarray):
    """Least-squares rotation aligning `mobile` (N,3) onto `ref` (N,3).

    Returns (R, mobile_centroid, ref_centroid) such that
    aligned = (X - mobile_centroid) @ R.T + ref_centroid.
    """
    mc, rc = mobile.mean(0), ref.mean(0)
    H = (mobile - mc).T @ (ref - rc)
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    return R, mc, rc


def kabsch_apply(coords, R, mobile_centroid, ref_centroid):
    """Apply a fit from `kabsch_fit` to any (M, 3) coordinate array."""
    return (coords - mobile_centroid) @ R.T + ref_centroid


def kabsch_align(mobile, ref, apply_to=None):
    """Fit mobile->ref and return the aligned copy of `apply_to`
    (defaults to `mobile` itself)."""
    R, mc, rc = kabsch_fit(mobile, ref)
    return kabsch_apply(mobile if apply_to is None else apply_to, R, mc, rc)


# ---------------------------------------------------------------------------
# Common Ca correspondence + superposition
# ---------------------------------------------------------------------------

def common_residues_by_resnum(apo, holo):
    """Indices (into apo.coords, holo.coords) of (chain, resnum) pairs
    present in both structures, in matching order.

    Deliberately NOT sequence alignment -- that is labels.py's job
    (TASK-0004). This is the independent, numbering-based correspondence
    the Intent Contract calls for, so that a disagreement against
    labels.holo_pocket_mask's sequence-alignment pocket mask is a
    geometric red flag caught by two different methods, not circular
    validation of the same method against itself.
    """
    apo_key = {
        (c, int(r)): i for i, (c, r) in enumerate(zip(apo.chain_ids, apo.resnums))
    }
    apo_idx, holo_idx = [], []
    for j, (c, r) in enumerate(zip(holo.chain_ids, holo.resnums)):
        i = apo_key.get((c, int(r)))
        if i is not None:
            apo_idx.append(i)
            holo_idx.append(j)
    return np.array(apo_idx, dtype=int), np.array(holo_idx, dtype=int)


@dataclass
class Alignment:
    """Kabsch fit of holo onto apo's frame, plus RMSD diagnostics."""

    R: np.ndarray
    mobile_centroid: np.ndarray
    ref_centroid: np.ndarray
    apo_idx: np.ndarray              # common-set indices into apo.coords
    holo_idx: np.ndarray             # common-set indices into holo.coords (matching order)
    aligned_holo_coords: np.ndarray  # ALL of holo.coords, transformed into apo's frame
    rmsd_overall: float
    rmsd_per_chain: dict


def align_apo_holo(apo, holo) -> Alignment:
    """Kabsch-superpose holo onto apo using the common (chain, resnum) Ca
    set, then report per-chain RMSD on that same set.

    This catches register/numbering errors independently of labels.py's
    sequence-alignment label mapping (Intent Contract) -- a large RMSD here
    on a target where labels.py reports a clean pocket map is itself a
    finding worth surfacing, not something to silently paper over.
    """
    apo_idx, holo_idx = common_residues_by_resnum(apo, holo)
    if len(apo_idx) < 3:
        raise ValueError(
            f"only {len(apo_idx)} common (chain, resnum) Ca pair(s) between "
            f"apo and holo -- Kabsch needs >=3 non-collinear points."
        )
    mobile = holo.coords[holo_idx]
    ref = apo.coords[apo_idx]
    R, mc, rc = kabsch_fit(mobile, ref)
    aligned_holo_coords = kabsch_apply(holo.coords, R, mc, rc)

    per_point_rmsd = np.sqrt(((aligned_holo_coords[holo_idx] - ref) ** 2).sum(axis=1))
    rmsd_overall = float(np.sqrt((per_point_rmsd ** 2).mean()))

    apo_chains_common = np.asarray(apo.chain_ids)[apo_idx]
    rmsd_per_chain = {}
    for chain in sorted(set(apo_chains_common.tolist())):
        sel = apo_chains_common == chain
        rmsd_per_chain[chain] = float(np.sqrt((per_point_rmsd[sel] ** 2).mean()))

    return Alignment(
        R=R,
        mobile_centroid=mc,
        ref_centroid=rc,
        apo_idx=apo_idx,
        holo_idx=holo_idx,
        aligned_holo_coords=aligned_holo_coords,
        rmsd_overall=rmsd_overall,
        rmsd_per_chain=rmsd_per_chain,
    )


# ---------------------------------------------------------------------------
# 3D pocket cross-map (independent check on labels.py's sequence-alignment map)
# ---------------------------------------------------------------------------

def geometric_pocket_mask(apo, holo, alignment: Alignment, ligand_code: str, cutoff: float = 4.5):
    """Pocket mask on apo numbering, derived by pure 3D coincidence -- no
    sequence alignment anywhere in this function.

    The holo ligand's own coordinates are transformed into apo's frame via
    `alignment`'s Kabsch fit, then apo Ca atoms within `cutoff` of any
    (transformed) ligand heavy atom are flagged directly. Independent of
    labels.holo_pocket_mask's sequence-alignment method by construction --
    see `pocket_cross_map` for the agreement check this enables.

    Returns None (flagged, not guessed) if `ligand_code` isn't found among
    `holo.ligand_groups` -- mirrors labels.py's pick_drug/holo_pocket_mask
    "never guess" contract.
    """
    ligand = next((g for g in holo.ligand_groups if g.resname == ligand_code), None)
    if ligand is None:
        return None
    aligned_ligand_coords = kabsch_apply(
        ligand.coords, alignment.R, alignment.mobile_centroid, alignment.ref_centroid
    )
    diff = apo.coords[:, np.newaxis, :] - aligned_ligand_coords[np.newaxis, :, :]
    dist = np.sqrt((diff ** 2).sum(axis=2))
    return dist.min(axis=1) < cutoff


def pocket_cross_map(sequence_mask, geometric_mask):
    """Agreement/disagreement between labels.py's sequence-alignment pocket
    mask and this module's independent 3D-geometric one.

    Disagreement (residues flagged by one method but not the other) is a
    label bug caught geometrically, not a modeling failure -- reported, not
    resolved by silently picking one side.
    """
    if sequence_mask is None or geometric_mask is None:
        return dict(
            sequence_mask=sequence_mask,
            geometric_mask=geometric_mask,
            agreement=None,
            only_in_sequence=np.array([], dtype=int),
            only_in_geometric=np.array([], dtype=int),
        )
    union = sequence_mask | geometric_mask
    inter = sequence_mask & geometric_mask
    agreement = float(inter.sum() / union.sum()) if union.any() else 1.0
    return dict(
        sequence_mask=sequence_mask,
        geometric_mask=geometric_mask,
        agreement=agreement,
        only_in_sequence=np.where(sequence_mask & ~geometric_mask)[0],
        only_in_geometric=np.where(geometric_mask & ~sequence_mask)[0],
    )


# ---------------------------------------------------------------------------
# Cryptic-openness gate
# ---------------------------------------------------------------------------

def cryptic_openness_gate(
    apo,
    holo,
    alignment: Alignment,
    pocket_mask_apo: np.ndarray,
    rmsd_threshold: float = 3.0,
):
    """Per-residue apo->holo Ca displacement at the pocket, restricted to
    residues with a common (chain, resnum) correspondence (residues in the
    mask with no such correspondence can't be measured and are counted, not
    silently zeroed).

    Large mean displacement at the pocket -> "pocket absent from apo
    topology" -- KRAS_G12C's Switch-II pocket is the textbook expected-low
    case (ALGORITHM_REGISTER.md's Tama-Sanejouand entry), reported as a
    finding, never used to drop the target silently. Both the continuous
    score and the hard boolean verdict are returned (TASK-0005's Open
    Question recommends storing both).
    """
    apo_idx, holo_idx = alignment.apo_idx, alignment.holo_idx
    in_common = np.zeros(len(pocket_mask_apo), dtype=bool)
    in_common[apo_idx] = True
    measurable = pocket_mask_apo & in_common
    n_unmeasurable = int((pocket_mask_apo & ~in_common).sum())

    if not measurable.any():
        return dict(
            pocket_rmsd_mean=float("nan"),
            pocket_rmsd_max=float("nan"),
            pocket_open_in_apo=None,
            n_pocket_residues=0,
            n_unmeasurable=n_unmeasurable,
            threshold=rmsd_threshold,
        )

    apo_to_holo = dict(zip(apo_idx.tolist(), holo_idx.tolist()))
    measurable_apo = np.where(measurable)[0]
    measurable_holo = np.array([apo_to_holo[i] for i in measurable_apo])

    disp = np.sqrt(
        ((alignment.aligned_holo_coords[measurable_holo] - apo.coords[measurable_apo]) ** 2).sum(axis=1)
    )

    return dict(
        pocket_rmsd_mean=float(disp.mean()),
        pocket_rmsd_max=float(disp.max()),
        pocket_open_in_apo=bool(disp.mean() <= rmsd_threshold),
        n_pocket_residues=int(measurable.sum()),
        n_unmeasurable=n_unmeasurable,
        threshold=rmsd_threshold,
    )


# ---------------------------------------------------------------------------
# ANM modes + Tama-Sanejouand cumulative overlap
# ---------------------------------------------------------------------------

def anm_modes(coords: np.ndarray, cutoff: float = 10.0, n_modes: int = 20):
    """Lowest `n_modes` non-trivial ANM eigenmodes (discards the near-zero
    rigid-body translation/rotation modes).

    Reuses hamiltonians.H13_3N_anm_hessian -- confirmed to be a proper 3N x
    3N ANM Hessian (TASK-0005's Open Question) rather than rederiving ANM
    from scratch.

    Returns (eigvals, eigvecs); eigvecs has shape (3N, n_modes) -- column k
    is the flattened 3N eigenvector for eigvals[k], ascending order, with
    the near-zero rigid-body modes already dropped.
    """
    from .hamiltonians import H13_3N_anm_hessian

    H = H13_3N_anm_hessian(coords, cutoff=cutoff)
    w, v = np.linalg.eigh(H)
    n_zero = int((w < 1e-8).sum())
    if n_zero != 6:
        raise ValueError(
            f"expected exactly 6 near-zero rigid-body ANM modes (3 "
            f"translation + 3 rotation), found {n_zero} -- a disconnected "
            "contact graph has extra zero modes (independent rigid motion "
            "of each disconnected piece); check contact-graph connectivity."
        )
    end = min(n_zero + n_modes, len(w))
    return w[n_zero:end], v[:, n_zero:end]


def _projection_coefficients(delta_r: np.ndarray, eigvecs: np.ndarray, common_idx: np.ndarray):
    """c_k = (unit-renormalized, common-subset-restricted eigvec_k) . delta_r.

    `eigvecs` are full 3N-length ANM eigenvectors (from `anm_modes`);
    `delta_r` is only defined over `common_idx` residues (apo numbering), so
    each eigenvector is first sliced to that same subset and renormalized to
    unit length before projecting -- a standard practical approximation when
    apo/holo have numbering gaps (ProDy's calcOverlap does the same),
    documented here rather than silently assumed.
    """
    n_common = len(common_idx)
    if delta_r.shape[0] != 3 * n_common:
        raise ValueError("delta_r must be a flat 3*len(common_idx) vector")

    block_idx = np.empty(3 * n_common, dtype=int)
    block_idx[0::3] = 3 * common_idx
    block_idx[1::3] = 3 * common_idx + 1
    block_idx[2::3] = 3 * common_idx + 2

    v_blocks = eigvecs[block_idx, :]              # (3*n_common, n_modes)
    norms = np.linalg.norm(v_blocks, axis=0)
    safe_norms = np.where(norms > 1e-12, norms, 1.0)
    v_hat = v_blocks / safe_norms
    c = v_hat.T @ delta_r                          # (n_modes,)
    c = np.where(norms > 1e-12, c, 0.0)
    return c


def cumulative_overlap(delta_r: np.ndarray, eigvecs: np.ndarray, common_idx: np.ndarray) -> np.ndarray:
    """Tama-Sanejouand (2001) cumulative overlap CO(m) for m = 1..n_modes.

    CO(m) = ||sum_{k<=m} (delta_r . v_k) v_k|| / ||delta_r||

    HOLO_DIRECTION_MODULE.md Step 2's go/no-go gate -- low CO means the
    apo->holo direction is not spanned by the soft ANM modes, i.e. a
    genuinely cryptic/anharmonic opening (KRAS_G12C's Switch-II pocket is
    the textbook expected-low case) is the *correct* result, not a test
    failure or a bug in this function.
    """
    c = _projection_coefficients(delta_r, eigvecs, common_idx)
    delta_norm = np.linalg.norm(delta_r)
    if delta_norm < 1e-12:
        return np.zeros(len(c))
    return np.sqrt(np.cumsum(c ** 2)) / delta_norm


# ---------------------------------------------------------------------------
# kappa calibration + per-mode elastic energy / relaxation timescale
# ---------------------------------------------------------------------------

def calibrate_kappa(coords: np.ndarray, b_mean: float, cutoff: float = 10.0, n_modes=None) -> float:
    """Global scalar ANM spring constant matching this structure's
    unit-kappa flexibility scale to its experimental mean B-factor.

    Only clean.py's CleanResult.b_mean/b_std (aggregate statistics) are
    available here -- not a per-residue B-factor array -- so this is a
    single global mean-matching calibration, not a per-residue regression
    (a regression would need CleanResult to expose per-residue B-factors,
    which it does not; flagged as an Open Question in TASK-0005 rather than
    extending clean.py's schema, which is out of this task's scope).

    kappa = mean(unit-kappa ANM MSF) / b_mean. This package works in
    unitless Ca-network scores throughout, not absolute physical units, so
    no kT / (8 pi^2 / 3) prefactor is applied -- kappa is only meaningful as
    a relative scale within this module (energy/timescale comparisons
    across modes of the *same* target), not as a real spring constant.
    """
    from .hamiltonians import H13_3N_anm_hessian

    if b_mean is None or b_mean <= 0:
        raise ValueError("b_mean must be a positive number to calibrate kappa against")

    N = len(coords)
    H = H13_3N_anm_hessian(coords, cutoff=cutoff)
    w, v = np.linalg.eigh(H)
    n_zero = int((w < 1e-8).sum())
    if n_zero != 6:
        raise ValueError(
            f"expected exactly 6 near-zero rigid-body ANM modes, found "
            f"{n_zero} -- check contact-graph connectivity."
        )
    end = len(w) if n_modes is None else min(n_zero + n_modes, len(w))
    w_nz = w[n_zero:end]
    v_nz = v[:, n_zero:end]

    v3 = v_nz.reshape(N, 3, -1)                    # (N, 3, n_modes)
    per_mode_sq = (v3 ** 2).sum(axis=1)            # (N, n_modes)
    msf_unit = (per_mode_sq / w_nz).sum(axis=1)    # (N,) unit-kappa MSF

    return float(msf_unit.mean() / b_mean)


def mode_energetics(
    delta_r: np.ndarray,
    eigvals: np.ndarray,
    eigvecs: np.ndarray,
    common_idx: np.ndarray,
    kappa: float,
    zeta: float = 1.0,
):
    """Per-mode elastic energy and *relaxation* timescale for the observed
    apo->holo transition.

    E_k     = 1/2 * kappa * lambda_k * c_k^2      (elastic energy stored in mode k)
    tau_k   = zeta / (kappa * lambda_k)            (overdamped relaxation time)

    Reports the overdamped relaxation time, not the underdamped oscillation
    period, per PLAN.md's explicit correction ("underdamped period is a
    lower bound only"). `zeta` is an arbitrary friction-coefficient unit --
    this package has no absolute time/length calibration, so `tau_k` is only
    meaningful relative to other modes of the *same* target at the same
    `zeta`, not as real seconds.
    """
    c = _projection_coefficients(delta_r, eigvecs, common_idx)
    elastic_energy = 0.5 * kappa * eigvals * c ** 2
    relaxation_time = zeta / (kappa * eigvals)
    return dict(
        coefficients=c,
        elastic_energy=elastic_energy,
        relaxation_time=relaxation_time,
    )


# ---------------------------------------------------------------------------
# One-call orchestrator
# ---------------------------------------------------------------------------

def run_superpose(apo, holo, target_config: dict, n_modes: int = 20, cutoff: float = 10.0, rmsd_threshold: float = 3.0):
    """Full per-target Phase 1b report: alignment, pocket cross-map, the
    cryptic-openness gate, ANM mode-projection/CO(m), kappa calibration, and
    per-mode energetics/timescales -- the report protocol.py (TASK-0006)
    consumes.
    """
    from .labels import holo_pocket_mask

    alignment = align_apo_holo(apo, holo)
    ligand_code = target_config.get("drug_ligand")

    seq_mask = holo_pocket_mask(apo, holo, ligand_code, cutoff=4.5) if ligand_code else None
    geo_mask = (
        geometric_pocket_mask(apo, holo, alignment, ligand_code, cutoff=4.5)
        if ligand_code
        else None
    )
    cross_map = pocket_cross_map(seq_mask, geo_mask)

    gate = None
    if seq_mask is not None and seq_mask.any():
        gate = cryptic_openness_gate(
            apo, holo, alignment, seq_mask, rmsd_threshold=rmsd_threshold
        )

    eigvals, eigvecs = anm_modes(apo.coords, cutoff=cutoff, n_modes=n_modes)
    delta_r = (
        alignment.aligned_holo_coords[alignment.holo_idx] - apo.coords[alignment.apo_idx]
    ).ravel()

    co = cumulative_overlap(delta_r, eigvecs, alignment.apo_idx)
    kappa = calibrate_kappa(apo.coords, apo.b_mean, cutoff=cutoff)
    energetics = mode_energetics(delta_r, eigvals, eigvecs, alignment.apo_idx, kappa)

    return dict(
        alignment=alignment,
        pocket_cross_map=cross_map,
        openness_gate=gate,
        cumulative_overlap=co,
        kappa=kappa,
        mode_energetics=energetics,
    )
