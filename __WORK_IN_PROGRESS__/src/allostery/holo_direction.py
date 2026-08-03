"""Holo-direction module (TASK-0015, spec: `HOLO_DIRECTION_MODULE.md`).

Predicts the *direction* of the apo->holo conformational change from the
apo structure alone, generates a small family of admissible deformed
graphs, and (once Step 2's gate clears) runs transport on each -- goal is
to recover statically-hidden shortcuts in the active-site->pocket graph
distance (the active site and pocket are distal by this project's own
definition, so this is a path-shortening/shortcut test, not a test for a
direct new edge between the two labeled sets themselves). Steps 0-2 only;
Steps 3-5 are explicitly gated on Step 2's own per-target verdict (the
spec's own "First action") and are Out Of Scope for this module until
that gate has been run and recorded, per `HOLO_DIRECTION_MODULE.md`'s own
"do not build Steps 3-5 before Step 2" instruction.

Reuses `superpose.py`'s already-built, already-validated machinery
throughout rather than reinventing it: `anm_modes` (ANM eigendecomposition,
TASK-0005), `calibrate_kappa` (B-factor-matched spring constant,
TASK-0005), `align_apo_holo`/`restricted_cumulative_overlap` (Tama-
Sanejouand CO(m), pocket-restricted, TASK-0133/TASK-0150's corrected
form -- the same quantity `compute_learnability` already reports for
every mandatory target).
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from .baselines import hop_from_seed
from .superpose import align_apo_holo, anm_modes, calibrate_kappa, restricted_cumulative_overlap


# ---------------------------------------------------------------------------
# Step 0 -- frozen perturbation protocol (pre-registered before touching
# any holo data for tuning purposes; iterating this dict until a
# competence map looks good is leakage through protocol selection, the
# exact risk this step exists to prevent -- see module docstring).
# ---------------------------------------------------------------------------

PERTURBATION_PROTOCOL = {
    # "site-selection rule" / "number of sites" (spec's Step 0 wording,
    # inherited loosely from PRS's residue-level framing) -- Step 1's own
    # concrete recipe is mode-space, not residue-force-space, so this is
    # interpreted here as "which modes span the admissible deformation
    # subspace," not literal per-residue force sites. Stated explicitly
    # rather than silently picked, per this project's own convention for
    # interpretive choices in an underspecified filing.
    "mode_selection": "lowest n_modes non-trivial ANM eigenmodes (anm_modes, "
                       "TASK-0005) -- within the spec's own 5-20 range, narrowed "
                       "to 10 to keep the family in the tens-not-exponential "
                       "regime Step 1 requires",
    "n_modes": 10,
    "anm_cutoff": 10.0,
    # Amplitude range: multiples of a per-mode "thermal unit" amplitude
    # a_k^(1) = sqrt(1 / (kappa * lambda_k)). Derivation: calibrate_kappa
    # matches the unit-kappa MSF (summed over modes) to the real B-factor
    # mean, i.e. this package's own established, apo-only, already-built
    # convention already implies an implicit kT=1 equipartition scale.
    # Under that scale each mode carries kT/2 = 0.5 (unitless) of elastic
    # energy on average (mode_energetics' own E_k = 0.5*kappa*lambda_k*a_k^2
    # formula), so a_k^(1) is exactly the amplitude giving E_k=0.5 -- one
    # half-unit of thermal energy, zero new free parameters invented.
    "amplitude_scales": (0.5, 1.0, 2.0),
    "perturbation_form": "single-mode +/- excitation at each amplitude scale "
                          "(PRS/LRT convention: one mode at a time, not a "
                          "combinatorial sign product across modes -- Atilgan "
                          "& Atilgan 2009's own construction)",
    # Step 3's actual optimization objective -- declared now, computed only
    # in Step 3 (Out of Scope for this module until Step 2 clears). Never
    # holo-derived, per the leakage firewall.
    "objective_step3": "fpocket cavity-openness (baselines.fpocket_baseline)",
    "integrity_constraints": {
        "max_ca_spacing_deviation": 0.5,       # Angstrom, off the nominal 3.8 A neighbor spacing
        "min_ca_ca_nonbonded_distance": 3.0,   # Angstrom, clash threshold for non-sequential pairs
        "max_global_rmsd_from_apo": 5.0,       # Angstrom
    },
}


# ---------------------------------------------------------------------------
# Step 1 -- admissible deformation family
# ---------------------------------------------------------------------------

def _integrity_ok(coords_ref: np.ndarray, coords_new: np.ndarray, protocol: dict) -> Optional[str]:
    """Checks the 3 integrity constraints Step 1 names; returns None if
    all pass, else a short string naming which failed (first failure
    only -- callers just need to know whether to keep the candidate)."""
    c = protocol["integrity_constraints"]

    seq_dist_ref = np.linalg.norm(coords_ref[1:] - coords_ref[:-1], axis=1)
    seq_dist_new = np.linalg.norm(coords_new[1:] - coords_new[:-1], axis=1)
    if np.any(np.abs(seq_dist_new - seq_dist_ref) > c["max_ca_spacing_deviation"]):
        return "ca_spacing_violated"

    n = len(coords_new)
    diff = coords_new[:, None, :] - coords_new[None, :, :]
    dist = np.sqrt((diff ** 2).sum(axis=2))
    i, j = np.triu_indices(n, k=2)  # exclude sequential neighbors (i+1) from the clash check
    if np.any(dist[i, j] < c["min_ca_ca_nonbonded_distance"]):
        return "steric_clash"

    rmsd = float(np.sqrt(((coords_new - coords_ref) ** 2).sum(axis=1).mean()))
    if rmsd > c["max_global_rmsd_from_apo"]:
        return "rmsd_exceeded"

    return None


def build_deformation_family(coords: np.ndarray, b_mean: float, protocol: dict = PERTURBATION_PROTOCOL) -> dict:
    """Generate the admissible deformed-graph family G_1...G_m (Step 1).

    Returns `{"admissible": [...], "rejected": [...], "eigvals", "eigvecs",
    "kappa"}`. Each entry in `admissible`/`rejected` is
    `{"mode", "sign", "scale", "coords" (admissible only), "rmsd",
    "elastic_energy", "reject_reason" (rejected only)}`. Never raises on a
    single candidate failing integrity -- that is an expected, recorded
    outcome (a per-candidate reject), not a module failure; only a
    genuine `anm_modes`/`calibrate_kappa` error (e.g. TASK-0128's
    rigid-body-nullspace check) propagates.
    """
    n_modes = protocol["n_modes"]
    cutoff = protocol["anm_cutoff"]
    eigvals, eigvecs = anm_modes(coords, cutoff=cutoff, n_modes=n_modes)
    kappa = calibrate_kappa(coords, b_mean, cutoff=cutoff, n_modes=n_modes)

    N = len(coords)
    admissible, rejected = [], []
    for k in range(eigvals.shape[0]):
        lam_k = eigvals[k]
        a1_k = np.sqrt(1.0 / (kappa * lam_k))
        v_k = eigvecs[:, k].reshape(N, 3)
        for scale in protocol["amplitude_scales"]:
            for sign in (1.0, -1.0):
                amp = sign * scale * a1_k
                coords_new = coords + amp * v_k
                rmsd = float(np.sqrt(((coords_new - coords) ** 2).sum(axis=1).mean()))
                energy = 0.5 * kappa * lam_k * (amp ** 2)
                entry = dict(mode=k, sign=sign, scale=scale, rmsd=rmsd, elastic_energy=energy)
                reason = _integrity_ok(coords, coords_new, protocol)
                if reason is None:
                    entry["coords"] = coords_new
                    admissible.append(entry)
                else:
                    entry["reject_reason"] = reason
                    rejected.append(entry)

    return dict(admissible=admissible, rejected=rejected, eigvals=eigvals, eigvecs=eigvecs, kappa=kappa)


# ---------------------------------------------------------------------------
# Step 2 -- GO/NO-GO gate (mandatory, run on all training targets before
# any Step 3-5 or circuit work; see module docstring)
# ---------------------------------------------------------------------------

def go_no_go_gate(
    apo, holo, target_config: dict, active_site_mask: np.ndarray, pocket_mask: np.ndarray,
    family: dict, *, co_threshold: float = 0.5, cutoff: float = 10.0,
    chain_map: Optional[dict] = None,
) -> dict:
    """Per-target Step 2 verdict: two independent, never-collapsed
    components.

    1. **Overlap** -- pocket-restricted CO(m) at m=`family`'s own
       `n_modes` (reuses `restricted_cumulative_overlap`, TASK-0133's
       corrected zero-padded form -- the same quantity
       `compute_learnability` already reports for every mandatory target,
       recomputed here at this module's own `n_modes` for apples-to-apples
       against `family`, which was built at that same mode count; not
       necessarily equal to the project's already-published n_modes=20
       number).
    2. **Shortcut** -- does any admissible candidate in `family` shorten
       the graph-hop distance between the active site and the pocket
       relative to the apo graph? The active site and the pocket are
       **distal by this project's own definition** (`CLAUDE.md`'s own
       "active site is the anchor, allosteric site is distal"), so
       requiring a *direct* new active-site<->pocket edge is far too
       strict and not what this test should mean -- what matters is
       whether a new edge *anywhere* in the graph (not necessarily
       touching either labeled set) creates a shortcut that reduces the
       shortest path between them, exactly per HOLO_DIRECTION_MODULE.md's
       own transport framing (Step 4 runs CTQW/ENAQT on the deformed
       *graph*, not on a hand-picked pair of residues). Reuses
       `baselines.hop_from_seed`'s already-tested multi-source BFS
       (binary contact graph, same `cutoff` convention as the rest of the
       register) rather than reimplementing shortest-path logic.

    GO requires **both**: CO clearing `co_threshold` alone means the holo
    direction is inside the admissible manifold in *some* generic sense,
    but not that it specifically shortens the active-site<->pocket path;
    conversely a shortcut with no real overlap support is not evidence
    either. Returns both components plus the combined verdict -- never a
    single collapsed boolean, per this project's own "grid, not a point
    estimate" convention (`cumulative_overlap_gate`'s own precedent).
    """
    alignment = align_apo_holo(apo, holo, chain_map=chain_map)
    eigvecs = family["eigvecs"]
    in_common = np.zeros(len(pocket_mask), dtype=bool)
    in_common[alignment.apo_idx] = True
    measurable_pocket = np.where(pocket_mask & in_common)[0]

    if len(measurable_pocket) == 0:
        co_final = float("nan")
        co_curve = None
    else:
        co_curve = restricted_cumulative_overlap(apo, alignment, eigvecs, measurable_pocket)
        co_final = float(co_curve[-1]) if len(co_curve) else float("nan")

    active_idx = np.where(active_site_mask)[0]
    pocket_idx = np.where(pocket_mask)[0]

    apo_hop = -hop_from_seed(apo.coords, active_idx, cutoff=cutoff)  # negate hop_from_seed's own "-dist" convention back to real hop counts
    apo_hop_min = float(apo_hop[pocket_idx].min())

    shortcut_candidates = []
    best_hop_min = apo_hop_min
    for entry in family["admissible"]:
        deformed_hop = -hop_from_seed(entry["coords"], active_idx, cutoff=cutoff)
        hop_min = float(deformed_hop[pocket_idx].min())
        best_hop_min = min(best_hop_min, hop_min)
        if hop_min < apo_hop_min:
            shortcut_candidates.append(dict(mode=entry["mode"], sign=entry["sign"], scale=entry["scale"],
                                             apo_hop_min=apo_hop_min, deformed_hop_min=hop_min,
                                             hop_reduction=apo_hop_min - hop_min))

    shortcut_found = len(shortcut_candidates) > 0
    co_go = bool(np.isfinite(co_final) and co_final >= co_threshold)

    if co_go and shortcut_found:
        verdict = "GO"
    elif not co_go and not shortcut_found:
        verdict = "NO_GO"
    else:
        verdict = "PARTIAL"  # the two components disagree -- a real, reportable outcome, not forced either way

    return dict(
        verdict=verdict,
        co_final=co_final,
        co_curve=co_curve.tolist() if co_curve is not None else None,
        co_go=co_go,
        co_threshold=co_threshold,
        n_measurable_pocket=len(measurable_pocket),
        apo_hop_min=apo_hop_min,
        best_hop_min=best_hop_min,
        shortcut_found=shortcut_found,
        n_candidates_with_shortcut=len(shortcut_candidates),
        shortcut_candidates=shortcut_candidates,
        n_admissible=len(family["admissible"]),
        n_rejected=len(family["rejected"]),
    )
