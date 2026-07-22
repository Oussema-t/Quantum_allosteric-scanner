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
from typing import Dict, Optional

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

def chain_map_from_config(target_config: dict) -> Optional[Dict[str, str]]:
    """Holo-chain -> apo-chain remap for `common_residues_by_resnum`/
    `align_apo_holo`, derived from a target config's TASK-0127
    `apo_chains`/`holo_chains` per-role override (TASK-0144).

    Returns `None` (today's exact by-resnum-and-letter behavior) unless
    both fields are set on the config -- every existing target that only
    sets the shared `chains` field is unaffected.
    """
    apo_chains = target_config.get("apo_chains")
    holo_chains = target_config.get("holo_chains")
    if not apo_chains or not holo_chains:
        return None
    return dict(zip(holo_chains, apo_chains))


def common_residues_by_resnum(apo, holo, chain_map: Optional[Dict[str, str]] = None):
    """Indices (into apo.coords, holo.coords) of (chain, resnum) pairs
    present in both structures, in matching order.

    Deliberately NOT sequence alignment -- that is labels.py's job
    (TASK-0004). This is the independent, numbering-based correspondence
    the Intent Contract calls for, so that a disagreement against
    labels.holo_pocket_mask's sequence-alignment pocket mask is a
    geometric red flag caught by two different methods, not circular
    validation of the same method against itself.

    `chain_map` (TASK-0144): optional holo-chain -> apo-chain letter
    remap, for targets (TASK-0127's `apo_chains`/`holo_chains` override)
    where the same biological chain is deposited under different author
    chain letters in apo vs. holo (e.g. GLUCOKINASE: apo chain A, holo
    chain X). Defaults to `None`, which is byte-identical to the previous
    behavior (match holo's own chain letter verbatim against apo's).
    """
    apo_key = {
        (c, int(r)): i for i, (c, r) in enumerate(zip(apo.chain_ids, apo.resnums))
    }
    apo_idx, holo_idx = [], []
    for j, (c, r) in enumerate(zip(holo.chain_ids, holo.resnums)):
        apo_chain = chain_map.get(c, c) if chain_map else c
        i = apo_key.get((apo_chain, int(r)))
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


def align_apo_holo(apo, holo, chain_map: Optional[Dict[str, str]] = None) -> Alignment:
    """Kabsch-superpose holo onto apo using the common (chain, resnum) Ca
    set, then report per-chain RMSD on that same set.

    This catches register/numbering errors independently of labels.py's
    sequence-alignment label mapping (Intent Contract) -- a large RMSD here
    on a target where labels.py reports a clean pocket map is itself a
    finding worth surfacing, not something to silently paper over.

    `chain_map` (TASK-0144): see `common_residues_by_resnum`; pass
    `chain_map_from_config(target_config)` for targets that use TASK-0127's
    `apo_chains`/`holo_chains` override, otherwise omit (default `None`
    is the previous, unaffected behavior).
    """
    apo_idx, holo_idx = common_residues_by_resnum(apo, holo, chain_map=chain_map)
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


def background_rmsd(apo, holo, alignment: Alignment, pocket_mask_apo: np.ndarray) -> dict:
    """Per-residue apo->holo Ca displacement for the *non*-pocket
    ("background") residues in the common correspondence set -- the
    comparison `cryptic_openness_gate`'s own fixed-threshold verdict does
    not provide (TASK-0120): is the pocket's displacement large in
    absolute terms, or merely large relative to how much the rest of the
    structure moves anyway (e.g. a globally flexible/multi-domain
    target)? `REVIEW-panel-2026-07-16-v2.md` Sec.6's kill criterion is
    pocket RMSD *relative to* background RMSD, not pocket RMSD alone --
    this function supplies the missing half of that comparison, mirroring
    `cryptic_openness_gate`'s own structure exactly (same common-set
    restriction, same unmeasurable-residue accounting) rather than a
    second, differently-shaped computation.
    """
    apo_idx, holo_idx = alignment.apo_idx, alignment.holo_idx
    in_common = np.zeros(len(pocket_mask_apo), dtype=bool)
    in_common[apo_idx] = True
    background = (~pocket_mask_apo) & in_common

    if not background.any():
        return dict(
            background_rmsd_mean=float("nan"),
            background_rmsd_max=float("nan"),
            n_background_residues=0,
        )

    apo_to_holo = dict(zip(apo_idx.tolist(), holo_idx.tolist()))
    background_apo = np.where(background)[0]
    background_holo = np.array([apo_to_holo[i] for i in background_apo])

    disp = np.sqrt(
        ((alignment.aligned_holo_coords[background_holo] - apo.coords[background_apo]) ** 2).sum(axis=1)
    )

    return dict(
        background_rmsd_mean=float(disp.mean()),
        background_rmsd_max=float(disp.max()),
        n_background_residues=int(background.sum()),
    )


def learnability_verdict(
    pocket_rmsd_mean: float,
    background_rmsd_mean: float,
    co_final: float,
    *,
    rmsd_ratio_threshold: float = 1.5,
    co_threshold: float = 0.5,
    co_percentile: Optional[float] = None,
    significance_alpha: float = 0.05,
) -> dict:
    """TASK-0120 -- `REVIEW-panel-2026-07-16-v2.md` Sec.6's learnability
    kill criterion, made precise: **pocket RMSD >> background RMSD AND
    low cumulative overlap -> `UNLEARNABLE_FROM_APO`**, otherwise
    `LEARNABLE`. The panel states ">>"qualitatively; this function's own
    choice (stated here, not hidden) is `pocket/background ratio >=
    rmsd_ratio_threshold` (default 1.5, this task's own pick -- not
    derived from literature, analogous in spirit to
    `cumulative_overlap_gate`'s own `co_threshold=0.5` default, which
    *is* reused here rather than re-chosen, since that quantity already
    has an established convention in this codebase).

    Both conditions are required, not either alone: a large pocket RMSD
    by itself could just mean the whole structure is globally flexible
    (background also large, ratio near 1) -- not evidence the pocket
    specifically is cryptic. A low CO by itself does not distinguish a
    genuinely anharmonic opening from measurement noise on an already-
    small displacement. Requiring both is what makes this a *relative*,
    two-independent-methods verdict rather than either measurement read
    in isolation.

    `co_final` must be `superpose.restricted_cumulative_overlap`'s
    pocket-restricted quantity, **not** the whole-structure `cumulative_
    overlap` TASK-0120's own original script computed (TASK-0139:
    resolved in favor of the restricted quantity -- the RMSD half of
    this same conjunction is already pocket-vs-background, i.e. region-
    specific by design; a whole-structure CO answers "does the soft-mode
    subspace span *some* substantial motion somewhere," not "does it
    span *this pocket's* motion," a different and easier question than
    the one Sec.6's kill criterion actually asks). Both call sites in
    this codebase have been updated to pass the restricted quantity as
    of TASK-0139.

    `co_percentile` (TASK-0139, optional, ADD-only -- `None` preserves
    this function's exact pre-TASK-0139 behavior): the real pocket's
    percentile within a same-target, same-size random-patch null
    distribution (`scripts/learnability_gate_patch_control.py`,
    TASK-0133's own control). When supplied, replaces the bare
    `co_final < co_threshold` comparison with a two-tailed significance
    test against that null -- `co_threshold=0.5` was never itself
    validated against *any* real null (TASK-0120's own admission: "not
    derived from literature"; confirmed by re-reading `cumulative_
    overlap_gate`, the only other consumer, which also never validated
    it against a null), so once a real null is available for a specific
    target, testing against it directly is the more principled
    criterion, not a redundant extra check layered on top of the bare
    threshold:
      - `co_percentile >= 1 - significance_alpha` (real pocket
        significantly *above* the null -- genuinely better explained by
        the soft-mode subspace than a same-sized random region) ->
        `co_low=False`, contributes toward `LEARNABLE`, regardless of
        where `co_final` sits relative to `co_threshold`.
      - `co_percentile <= significance_alpha` (real pocket significantly
        *below* the null -- genuinely more anharmonic than a typical
        same-sized region) -> `co_low=True`, contributes toward
        `UNLEARNABLE_FROM_APO`.
      - Otherwise (neither tail significant): the CO evidence is
        genuinely inconclusive -- if `rmsd_much_greater` is also true
        (the only case where the CO half's value matters at all, since
        `rmsd_much_greater=False` already forces `LEARNABLE`
        unconditionally), verdict is `AMBIGUOUS`, a real third category
        distinct from both `LEARNABLE` and `UNLEARNABLE_FROM_APO` --
        per this project's own "an honest don't-know is a publishable
        result" convention, rather than a bare-threshold comparison
        forcing a binary call the statistics underneath it don't
        support.
    """
    ratio = (
        pocket_rmsd_mean / background_rmsd_mean
        if background_rmsd_mean > 1e-9 else float("inf")
    )
    rmsd_much_greater = ratio >= rmsd_ratio_threshold

    ambiguous = False
    if co_percentile is None:
        co_low = co_final < co_threshold
    else:
        significantly_high = co_percentile >= 1.0 - significance_alpha
        significantly_low = co_percentile <= significance_alpha
        if significantly_low:
            co_low = True
        elif significantly_high:
            co_low = False
        else:
            co_low = False  # not affirmatively low -- see `ambiguous` below
            ambiguous = rmsd_much_greater

    if ambiguous:
        verdict = "AMBIGUOUS"
    elif rmsd_much_greater and co_low:
        verdict = "UNLEARNABLE_FROM_APO"
    else:
        verdict = "LEARNABLE"

    return dict(
        verdict=verdict,
        pocket_rmsd_mean=pocket_rmsd_mean,
        background_rmsd_mean=background_rmsd_mean,
        rmsd_ratio=ratio,
        rmsd_much_greater=rmsd_much_greater,
        co_final=co_final,
        co_low=co_low,
        rmsd_ratio_threshold=rmsd_ratio_threshold,
        co_threshold=co_threshold,
        co_percentile=co_percentile,
        significance_alpha=significance_alpha,
        ambiguous=ambiguous,
    )


# ---------------------------------------------------------------------------
# ANM modes + Tama-Sanejouand cumulative overlap
# ---------------------------------------------------------------------------

def _check_anm_rigid_body_nullspace(H: np.ndarray, w: np.ndarray, n_zero: int) -> None:
    """TASK-0128 -- validates `n_zero`, replacing the original `!= 6`
    hardening (TASK-0005) with the `>= 6`-plus-connectivity-check that
    task's own Open Question anticipated ("a genuinely multi-chain/
    floppy-linker target... might legitimately have more than 6 near-zero
    -but-not-exactly-zero modes without being 'disconnected' in the error
    sense -- worth revisiting this strictness once a multi-chain target is
    actually run through this module").

    That target has now actually been run: BCR_ABL1 (`n_zero=7`) and
    CARDIAC_MYOSIN (`n_zero=10`), both real, connected structures (not the
    disconnected-graph bug `!= 6` was built to catch). Diagnosed directly,
    not assumed: in both cases the "extra" eigenvalues sit at true
    machine-precision zero (~1e-16, indistinguishable from the 6 trivial
    modes), then jump 5-9 orders of magnitude to the real low-frequency
    spectrum -- not a smooth continuum blending into the zero cluster,
    which rules out "numerical near-degeneracy at the 1e-8 threshold" as
    the explanation. The corresponding eigenvectors localize almost
    entirely onto a small, compact residue segment (BCR_ABL1: ~10
    residues; CARDIAC_MYOSIN: all 4 extra modes on the same ~17-residue
    segment) -- the well-known artifact of a purely central-force
    (distance-only, no angular term) ANM model: a locally under-
    constrained substructure (e.g. a weakly-coupled loop, or -- for
    CARDIAC_MYOSIN specifically -- plausibly connected to that target's
    own independently-documented 5TBY low-resolution/under-constrained
    caveat) can have exact zero-energy internal rotational modes without
    the structure being disconnected at all. This is genuine physical
    (or data-quality) softness, not a bug in `eigh` or in this function.

    The regression `!= 6` was actually built to catch (TASK-0005: a
    synthetic disconnected two-cluster graph silently passing under a
    naive `n_zero < 6` check, when it should raise) is preserved exactly:
    a disconnected graph's `n_zero` is *always* checked against real
    connectivity below, not just counted. `n_zero < 6` remains an
    unconditional bug (fewer than the mandatory 3 translation + 3
    rotation modes cannot happen for a real ANM Hessian and signals
    something is broken upstream) and still raises immediately, no
    connectivity check needed.
    """
    if n_zero < 6:
        raise ValueError(
            f"expected at least 6 near-zero rigid-body ANM modes (3 "
            f"translation + 3 rotation), found {n_zero} -- fewer than the "
            "mandatory minimum; something is broken upstream of this "
            "eigendecomposition, not a connectivity or floppiness question."
        )
    if n_zero > 6:
        from .diagnostics import operator_diagnostics

        n_components = operator_diagnostics(H)["n_components"]
        if n_components != 1:
            raise ValueError(
                f"found {n_zero} near-zero ANM modes (>6) AND the contact "
                f"graph has {n_components} disconnected components (via "
                "operator_diagnostics on this Hessian) -- this is "
                "TASK-0005's original disconnected-graph regression "
                "(independent rigid motion of each piece), not TASK-0128's "
                "single-connected-structure floppiness case; do not proceed "
                "with a single global rigid-body-nullspace assumption."
            )


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
    _check_anm_rigid_body_nullspace(H, w, n_zero)
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


def restricted_cumulative_overlap(
    apo, alignment: Alignment, eigvecs: np.ndarray, residue_idx: np.ndarray,
) -> np.ndarray:
    """CO(m) for one residue subset's own apo->holo displacement,
    zero-padded into the full ANM coordinate space (TASK-0133) --
    **not** `cumulative_overlap`'s own renormalize-a-sliced-eigenvector
    approach, which is invalid for a small subset (see below).

    **Not the same quantity `learnability_gate.py`'s own reported
    `CO(20)` computes.** That script's `delta_r`/`common_idx` cover the
    *entire* common (chain, resnum) correspondence set (166-709 residues
    depending on target) -- a whole-structure conformational-change
    overlap, not a pocket-specific one, confirmed directly against real
    data (`len(delta_r) == 3 * len(alignment.apo_idx)`, not
    `3 * n_pocket_residues`). This function computes the *region-
    specific* CO(m) TASK-0133's own random-patch control needs to be a
    type-correct comparison: TASK-0120's whole-structure CO(20) is one
    number per target, constant regardless of which residues you'd call
    "the pocket" -- comparing it against a distribution of per-patch
    numbers would be comparing two different quantities.

    **Real, load-bearing finding (TASK-0133): does NOT delegate to
    `cumulative_overlap` for the restricted case.** `cumulative_overlap`/
    `_projection_coefficients` slice each eigenvector down to
    `residue_idx` and renormalize the slice to unit length -- a fine
    approximation when `residue_idx` is the full or near-full common set
    (a handful of missing residues), which is `cumulative_overlap`'s own
    only prior use in this codebase, but it silently breaks Bessel's
    inequality (`CO(m) <= 1` by construction) once `residue_idx` is a
    small fraction of the structure: renormalizing a mostly-truncated
    eigenvector slice inflates it, and the resulting "modes" are no
    longer orthonormal. Confirmed directly, not assumed: a 3-of-50-residue
    synthetic subset gives `CO(20) = 1.47`, and real pocket-sized subsets
    (13-18 of 166-709 residues) give values up to 1.64 -- both
    mathematically impossible for a genuine overlap fraction.

    This function instead zero-pads `residue_idx`'s displacement into the
    *full* `3N`-length coordinate space and projects onto the untouched,
    still-orthonormal `eigvecs` directly (`c_k = v_k . delta_r_padded`,
    no renormalization) -- Bessel's inequality then guarantees
    `CO(m) <= 1` for *any* subset size, verified directly on the same
    3-of-50 case above (`CO(20) = 0.34`). Physically: "how much of this
    subset's own displacement, treated as zero elsewhere, does the global
    low-frequency subspace explain" -- a well-posed question for any
    region size, unlike the renormalized-slice version.

    `residue_idx` must be a subset of `alignment.apo_idx` (every index
    must have a holo correspondence) -- raises if not, rather than
    silently dropping residues.
    """
    apo_idx, holo_idx = alignment.apo_idx, alignment.holo_idx
    apo_to_holo = dict(zip(apo_idx.tolist(), holo_idx.tolist()))
    residue_idx = np.asarray(residue_idx)
    missing = [int(i) for i in residue_idx if i not in apo_to_holo]
    if missing:
        raise ValueError(
            f"restricted_cumulative_overlap: {len(missing)} residue(s) have no "
            f"holo correspondence in this alignment (not in alignment.apo_idx): "
            f"{missing[:10]}{'...' if len(missing) > 10 else ''}"
        )
    holo_subset = np.array([apo_to_holo[int(i)] for i in residue_idx])
    disp = alignment.aligned_holo_coords[holo_subset] - apo.coords[residue_idx]

    n_full = eigvecs.shape[0] // 3
    delta_padded = np.zeros(3 * n_full)
    block_idx = np.empty(3 * len(residue_idx), dtype=int)
    block_idx[0::3] = 3 * residue_idx
    block_idx[1::3] = 3 * residue_idx + 1
    block_idx[2::3] = 3 * residue_idx + 2
    delta_padded[block_idx] = disp.ravel()

    delta_norm = np.linalg.norm(delta_padded)
    if delta_norm < 1e-12:
        return np.zeros(eigvecs.shape[1])
    c = eigvecs.T @ delta_padded
    return np.sqrt(np.cumsum(c ** 2)) / delta_norm


# ---------------------------------------------------------------------------
# TASK-0075 -- knob-spread go/no-go gate over cumulative_overlap
# ---------------------------------------------------------------------------

def cumulative_overlap_gate(
    delta_r: np.ndarray,
    common_idx: np.ndarray,
    reference_coords: dict,
    *,
    cutoffs=(8.0, 10.0, 12.0),
    n_modes_list=(10, 20, 30),
    co_threshold: float = 0.5,
) -> dict:
    """GO / NO_GO / UNSTABLE verdict on HOLO_DIRECTION_MODULE.md's Step 2
    barrier-penetrability test, swept over the knobs
    `INVARIANCE_PROTOCOL.md`/`INV-0001` name as KNOB-not-GAUGE: ANM
    `cutoff`, mode count `n_modes`, and reference-conformer choice (which
    structure's ANM modes `delta_r` is projected onto -- `reference_coords`
    is `{name: coords}`, e.g. `{"apo": apo.coords}` or several candidate
    reference conformers).

    No single-point-estimate version of this gate exists anywhere in this
    codebase to preserve compatibility with (checked directly: `superpose.
    cumulative_overlap` itself returns only the raw, unthresholded CO(m)
    curve; `run_superpose` never applies a threshold to it) -- this is the
    first verdict built on top of it, built spread-aware from the start
    per this task's own Intent Contract, not upgraded from a prior
    point-estimate implementation.

    **`(cutoff x variant x k x reference)` from this task's own Context**
    collapses to `(cutoff x n_modes x reference)` here: no ANM "variant"
    axis (an alternate Hessian weighting scheme, analogous to
    `hamiltonians.py`'s `H1`-`H14` operator family) exists anywhere in
    `anm_modes`/`H13_3N_anm_hessian` to sweep -- confirmed by reading both
    functions, not assumed. Flagged as a real, currently-absent knob
    rather than silently dropped or invented; a future `anm_variant`
    parameter on `anm_modes` would extend this gate's grid with one more
    nested loop, no restructuring needed.

    `delta_r`/`common_idx` are held fixed across the sweep -- Tama-
    Sanejouand's Δr is the *observed* apo->holo displacement, not itself a
    knob; only the ANM modes it is projected onto (cutoff/n_modes/which
    reference structure) vary. CO(m) is read at `m = n_modes` (the last
    entry of `cumulative_overlap`'s cumulative curve, i.e. "all swept
    modes included") for each combination.

    Verdict: `GO` if every combination's CO clears `co_threshold`, `NO_GO`
    if none do, `UNSTABLE` if the threshold decision depends on which
    combination was run -- per this task's Acceptance Scenarios, a mixed
    grid must never collapse to a single GO/NO-GO point estimate.

    Returns `{"verdict", "co_min", "co_max", "spread", "n_combos",
    "n_go", "threshold", "grid"}` -- `grid` is the full per-combination
    list (`reference`/`cutoff`/`n_modes`/`co`/`go`), the actual evidence
    behind the verdict, not just the summary.
    """
    grid = []
    for ref_name, coords in reference_coords.items():
        for cutoff in cutoffs:
            for n_modes in n_modes_list:
                try:
                    eigvals, eigvecs = anm_modes(coords, cutoff=cutoff, n_modes=n_modes)
                except ValueError:
                    # Disconnected contact graph at this cutoff -- a real,
                    # reportable combination outcome, not a crash (mirrors
                    # this module's own "record, don't hide" convention
                    # for cryptic_openness_gate's unmeasurable residues).
                    grid.append(dict(reference=ref_name, cutoff=cutoff, n_modes=n_modes,
                                      co=float("nan"), go=None))
                    continue
                co_curve = cumulative_overlap(delta_r, eigvecs, common_idx)
                co_final = float(co_curve[-1]) if len(co_curve) else float("nan")
                go = bool(co_final >= co_threshold) if np.isfinite(co_final) else None
                grid.append(dict(reference=ref_name, cutoff=cutoff, n_modes=n_modes, co=co_final, go=go))

    finite = [g for g in grid if g["go"] is not None]
    if not finite:
        return dict(verdict="NO_GO", co_min=float("nan"), co_max=float("nan"), spread=float("nan"),
                    n_combos=len(grid), n_go=0, threshold=co_threshold, grid=grid)

    cos = [g["co"] for g in finite]
    co_min, co_max = min(cos), max(cos)
    n_go = sum(1 for g in finite if g["go"])
    if n_go == len(finite):
        verdict = "GO"
    elif n_go == 0:
        verdict = "NO_GO"
    else:
        verdict = "UNSTABLE"

    return dict(
        verdict=verdict, co_min=co_min, co_max=co_max, spread=co_max - co_min,
        n_combos=len(grid), n_go=n_go, threshold=co_threshold, grid=grid,
    )


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
    _check_anm_rigid_body_nullspace(H, w, n_zero)
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

    alignment = align_apo_holo(apo, holo, chain_map=chain_map_from_config(target_config))
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
