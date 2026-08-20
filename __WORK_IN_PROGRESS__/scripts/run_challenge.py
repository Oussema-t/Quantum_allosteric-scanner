#!/usr/bin/env python3
"""TASK-0079.004 -- one-command end-to-end challenge run orchestrator.

Given a target name (a `config/targets.yaml` key), fetches + cleans the
apo/holo structures, runs the FROZEN-gated verdict pipeline
(`protocol.run_frozen_verdict`, TASK-0079.003), assembles the N x N
connectivity matrix and top-5 hit list (`pathways.edge_propensity_to_matrix`
/ `report.assemble_hit_list`, TASK-0079.002), renders the methodological
report (`report.verdict_template`), and writes the three required
deliverables -- plus a fourth, `verdict.json`, the full assembled/stamped
results dict (including `_diagnosis`), since TASK-0079.005's own Intent
Contract needs that on disk for manual inspection, not just in memory --
to `__WORK_IN_PROGRESS__/results/<target_name>/`.

TASK-0180: also clusters the top-scoring residues into spatially
deduplicated sites (`sites.cluster_sites` -- fixes `assemble_hit_list`'s
own no-dedup defect, see that module's docstring), attaches a `"sites"`
key to `hit_list.json` additively (existing residue-level keys byte-
identical, pinned by `test_run_challenge.py`), and writes a fifth
deliverable, `end_to_end.json` (+ one appended `RESULTS.md` section) --
the apo -> predicted-pocket -> verified-in-holo statement, every clause
filled or explicitly marked unavailable.

Orchestration glue only: this script does not reimplement any part of the
FROZEN-gating (that is `protocol.run_frozen_verdict`'s job, tested in
isolation, TASK-0079.003's own Constraint) and does not invent a new
operator search space -- the candidates offered to `select_frozen_config`
here are just `H_new`/`H10` at the target's own configured `enm_cutoff`,
the same default-parameter pair `analysis.benchmark` already compares. A
real coordinate-descent search over more variants is TASK-0046's job, out
of this script's scope.

Holo-side enrichment (`AUC_holo_Hnew_optimised`, `mean_rho_apo_holo`,
`mean_jacc20`) is deliberately not wired here: it requires a holo-frame
pocket/active-site mapping and a matching holo-side operator built from
the same recipe as the winning apo candidate -- `run_frozen_verdict`
already supports it if a caller supplies `holo_H`/`holo_source`/
`holo_labels`, but building that mapping correctly is real, untested
scope of its own (arguably TASK-0015's holo-direction module), not
something to improvise inline here. Those three keys are simply absent
from the rendered report, per `verdict_template`'s own "a missing key
renders N/A" design -- not a crash, not a guess.

Seed residue: a target's assembled active site (`labels.Labels.active_site`)
is typically several residues (every `func_ligand` contact). This script
uses the **full active-site array**, scored via `propagators.time_averaged_
ctqw_converged`'s **incoherent statistical mixture** (`coherent=False`) --
the one seed convention declared for every scored call site in this
codebase (TASK-0118, `.ai/invariants/INV-0006`). The headline occupation
itself is the exact infinite-time closed form (TASK-0130), not a finite-
time snapshot -- see TASK-0159's own Done section for why. Previously used a
single representative seed index (TASK-0090: `select.unsupervised_score`'s
scoring path crashed on a multi-index source, `ballistic_exponent`'s BFS
assumed a scalar seed) -- TASK-0090 fixed that crash; TASK-0118 then
widened this script back to the full array and adopted the incoherent
mixture (a coherent equal-amplitude superposition across active-site
residues asserts a specific relative quantum phase between them with no
biophysical basis, per `REVIEW-panel-2026-07-16-v2` Sec.5 P0-1). Candidate
*selection* (`select_frozen_config`/`unsupervised_score`) still uses the
coherent superposition internally -- that label-free heuristic was tested
and tuned against it, and TASK-0118's own scope is the *reported* AUCs,
not `select.py`'s internal ranking machinery; see `protocol.
run_frozen_verdict`'s own docstring for this exact boundary.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

# See sweep_operators.py's identical block for why: must run before
# `import numpy`, caps this process's BLAS threads so concurrent heavy
# jobs on this shared machine don't oversubscribe and stall each other
# (found 2026-07-14 running this script alongside sweep_operators.py).
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.analysis import consensus_ranking  # noqa: E402
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, fpocket_baseline, hop_from_seed  # noqa: E402
from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.hamiltonians import build_H_new, build_H10  # noqa: E402
from allostery.labels import (  # noqa: E402
    build_labels,
    functional_indices,
    ligand_groups_from_atomgroup,
    protein_heavy_atoms_by_residue,
)
from allostery.pathways import edge_propensity, edge_propensity_to_matrix  # noqa: E402
from allostery.propagators import quantum_connectivity_matrix, time_averaged_ctqw_converged  # noqa: E402
from allostery.protocol import run_frozen_verdict  # noqa: E402
from allostery.report import assemble_hit_list, no_ground_truth_report, verdict_template  # noqa: E402
from allostery.sites import (  # noqa: E402
    cluster_sites,
    end_to_end_record,
    site_chance_level,
    site_hit_metrics,
    site_knob_sweep,
    site_proximity_floor,
)
from allostery.superpose import compute_learnability  # noqa: E402

def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results"
DEFAULT_CUTOFF = 10.0  # analysis.py's own default, used only if a target's config omits enm_cutoff
DEFAULT_POCKET_CUTOFF = 4.5


def _leak_check_n_perm_for(n_residues: int) -> int:
    """TASK-0218: GATE-B4 (`diagnostics.detect_permutation_leak`), wired
    into this real run via `run_frozen_verdict`'s own `leak_check_n_perm`.
    Real per-call cost is dominated by `time_averaged_ctqw`'s
    eigendecomposition, ~O(N^3) -- measured at 0.37s/call on KRAS_G12C
    (N=169); scaling that to CARDIAC_MYOSIN-size (N~950) implies ~66s for
    a SINGLE permutation. A fixed `n_perm` across every target size is
    therefore either wasteful (small targets) or prohibitive (large
    ones) -- tiered by N instead, a coarse, explicitly-stated choice, not
    a validated cost model derived from more than one real measurement."""
    if n_residues <= 250:
        return 30
    if n_residues <= 500:
        return 10
    return 3

# TASK-0159: the headline CTQW occupation (candidates_builder's own winner,
# run_frozen_verdict's benchmark()/quantum_vs_classical() ctqw side) now
# uses time_averaged_ctqw_converged -- the exact infinite-time closed form
# (TASK-0130) -- instead of a finite-time snapshot, since TASK-0110 measured
# the old T_MAX=15.0/N_STEPS=500 pair as 145,000x-3,950,000x too short to
# have actually converged, and TASK-0146 showed this truncation flips a
# real target's own floor-clearing verdict. The old `T_MAX`/`N_STEPS`
# module constants are deleted, not left as dead code, per this task's own
# Intent Contract -- this renamed pair is a genuinely different, still-
# correct-as-is use: `select_frozen_config`'s own blind candidate-ranking
# heuristic (`unsupervised_score`, TASK-0118's own established, deliberately
# untouched scope boundary -- selection is not the reported score),
# `ground_state_relaxation`'s single-snapshot relaxation-convergence time
# (an unrelated, still-finite-by-design criterion), and `ablation()`'s own
# per-term diagnostic (`most_impactful_term` in verdict.json -- a mechanism
# finding, not a scored AUC; extending that one function to the converged
# form is a real, separate follow-up, not done here -- see this task's own
# Done section for why).
SELECTION_GSR_ABLATION_T = 15.0
SELECTION_GSR_ABLATION_N_STEPS = 500


def _load_apo_holo(target_name: str, target_config: dict):
    """Fetch + clean apo/holo, attach holo's ligand_groups/heavy-atom data.

    Same real recipe `test_labels.py::_load_real_target` and
    `test_analysis.py`'s real-KRAS test already establish and pass against
    live RCSB data -- not reinvented here.
    """
    import prody

    apo = clean_from_config(target_name, role="apo")
    holo = clean_from_config(target_name, role="holo")

    prody.confProDy(verbosity="none")
    holo_id = target_config["holo_pdb"]
    chains = target_config.get("chains") or sorted(set(holo.chain_ids))
    chain_sel = " or ".join(f"chain {c}" for c in chains)
    holo_struct = prody.parsePDB(holo_id, compressed=False).select(chain_sel)
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, chains, holo.resnums
    )
    return apo, holo


def _make_candidates_builder(apo, source, cutoff: float):
    """Zero-arg builder for `select_frozen_config`/`run_frozen_verdict` --
    only ever reads `apo.coords`/`apo.bfactors` (plain, already-in-hand
    arrays), never a gated accessor, so it is leak-safe by construction,
    not merely by the gate catching it."""

    def build_candidates():
        H_new = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
        H10 = build_H10(apo.coords, apo.bfactors, cutoff=cutoff)
        return [
            {"H": H_new, "source": source, "t": SELECTION_GSR_ABLATION_T, "name": "H_new_default"},
            {"H": H10, "source": source, "t": SELECTION_GSR_ABLATION_T, "name": "H10_disorder_suppressed"},
        ]

    return build_candidates


def _jsonify(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, (np.floating, np.integer)):
            out[k] = v.item()
        elif isinstance(v, np.ndarray):
            out[k] = v.tolist()
        else:
            out[k] = v
    return out


def run_target_no_ground_truth(target_name: str, target_config: dict, output_dir: Path, run_start: float) -> dict:
    """TASK-0080: c-Myc/1NKP branch -- `holo_pdb: null`,
    `allosteric_pocket_exists: false`. No AUC, no ceiling, no proximity
    floor -- none of those are computable without a labeled holo pocket,
    which this target's own config declares does not exist. Consensus
    ranking across 4 independent operators (`analysis.consensus_ranking`)
    plus `baselines.fpocket_baseline`'s theoretical docking viability are
    this target's entire holo-free evidence, per this task's own Intent
    Contract ("no AUC, no ceiling; report prediction + confidence
    honestly").

    Still produces the same three physical deliverable *files* as the
    normal path (connectivity matrix, hit list, report) so downstream
    consumers (TASK-0082's competence map, the frontend) have a
    consistent per-target output shape to read -- their *content* is
    honestly different (no `verdict.json` `_diagnosis`/AUC keys; the
    hit list is consensus-ranked, not AUC-validated).
    """
    import prody

    target_dir = output_dir / target_name

    _log(f"{target_name}: [no-ground-truth path] fetching + cleaning apo...")
    t0 = time.monotonic()
    apo = clean_from_config(target_name, role="apo")
    _log(f"{target_name}: apo ready in {time.monotonic() - t0:.1f}s (N={len(apo.resnums)})")
    cutoff = float(target_config.get("enm_cutoff", DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))

    # No ligand_groups exist for this target (no holo, no bound-ligand
    # structure fetched at all) -- functional_indices' own documented
    # tier-2 fallback (top-5 contact-degree residues, "least informative,
    # signals no resolvable functional ligand") fires here by design, not
    # as a bug this branch works around. func_ligand=["DNA"] never matches
    # an empty ligand_groups list.
    active_idx, provenance = functional_indices(apo.coords, [], target_config, cutoff=pocket_cutoff)
    _log(f"{target_name}: seed resolved via {provenance!r} ({len(active_idx)} residues)")

    _log(f"{target_name}: consensus ranking across 4 operators (H_new/H10/H2/H14, "
         f"the expensive eigendecomposition stage)...")
    t0 = time.monotonic()
    consensus = consensus_ranking(
        apo.coords, apo.bfactors, active_idx, cutoff=cutoff,
        t_max=SELECTION_GSR_ABLATION_T, n_steps=SELECTION_GSR_ABLATION_N_STEPS, k=5,
    )
    _log(f"{target_name}: consensus ranking done in {time.monotonic() - t0:.1f}s")

    _log(f"{target_name}: fetching local PDB + running fpocket for docking viability...")
    t0 = time.monotonic()
    prody.confProDy(verbosity="none")
    try:
        pdb_path = prody.fetchPDB(target_config["apo_pdb"], compressed=False)
        docking = fpocket_baseline(pdb_path) if pdb_path else {"error": "prody.fetchPDB returned no local path"}
    except Exception as exc:
        docking = {"error": f"could not fetch a local PDB file for fpocket: {exc!r}"}
    _log(f"{target_name}: docking viability done in {time.monotonic() - t0:.1f}s -- "
         f"{'error: ' + docking['error'] if 'error' in docking else str(len(docking.get('pockets', []))) + ' pocket(s)'}")

    # Connectivity matrix: the consensus operator with the highest total
    # cross-operator agreement contribution (H_new_default, this pipeline's
    # own primary operator elsewhere) -- one concrete propagation graph for
    # the matrix deliverable; the *ranking* deliverable (hit list) is the
    # actual consensus-across-operators output, not this single matrix.
    _log(f"{target_name}: building connectivity matrix...")
    t0 = time.monotonic()
    H_new = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    propensity = edge_propensity(H_new, active_idx)
    matrix = edge_propensity_to_matrix(propensity, n=len(apo.resnums))
    # TASK-0160: the dense, symmetric, all-pairs quantum connectivity
    # matrix (challenge Sec.5) -- reuses the same eigendecomposition
    # `quantum_connectivity_matrix` needs, no second diagonalization.
    w_qcm, v_qcm = np.linalg.eigh(H_new)
    q_matrix = quantum_connectivity_matrix(w=w_qcm, v=v_qcm)
    _log(f"{target_name}: connectivity matrix done in {time.monotonic() - t0:.1f}s")

    hit_indices = np.asarray(consensus["consensus_ranked_indices"])
    hit_scores = consensus["mean_occupancy"][hit_indices]

    report_text = no_ground_truth_report(target_name, consensus, docking, resnums=apo.resnums)

    _log(f"{target_name}: writing deliverables to {target_dir}...")
    target_dir.mkdir(parents=True, exist_ok=True)
    np.savez(target_dir / "connectivity_matrix.npz", matrix=matrix, resnums=apo.resnums)
    np.savez(target_dir / "quantum_connectivity_matrix.npz", matrix=q_matrix, resnums=apo.resnums)
    with open(target_dir / "hit_list.json", "w") as f:
        json.dump({
            "indices": hit_indices.tolist(),
            "resnums": apo.resnums[hit_indices].tolist(),
            "scores": hit_scores.tolist(),
            "consensus_count": consensus["consensus_count"][hit_indices].tolist(),
        }, f, indent=2)
    with open(target_dir / "report.txt", "w") as f:
        f.write(report_text)
    with open(target_dir / "verdict.json", "w") as f:
        json.dump({
            "no_ground_truth": True,
            "reason": "holo_pdb is null / allosteric_pocket_exists: false",
            "operators": consensus["operators"],
            "consensus_count": consensus["consensus_count"].tolist(),
            "docking": docking,
        }, f, indent=2)

    _log(f"{target_name}: DONE (no-ground-truth path) in {time.monotonic() - run_start:.1f}s total")
    return {"target": target_name, "ok": True, "diagnosis": "NO_GROUND_TRUTH"}


def run_target(target_name: str, output_dir: Path) -> dict:
    """Run the full pipeline for one target.

    Never raises past this function -- a failed target is logged and
    reflected in `error.txt` under its own output directory, so a
    multi-target run continues past one bad target rather than aborting
    the whole batch (Intent Contract's error-handling requirement).
    Returns a small status dict for the caller's summary.
    """
    target_dir = output_dir / target_name
    run_start = time.monotonic()
    try:
        target_config = load_target_config(target_name)

        # TASK-0080: a target with no holo structure at all (c-Myc/1NKP)
        # cannot go through the AUC/ceiling path below -- _load_apo_holo
        # itself raises on a null holo_pdb (clean_from_config's own
        # ValueError). Route to the dedicated no-ground-truth branch
        # before any holo-dependent call is attempted, not after one fails.
        if target_config.get("holo_pdb") is None:
            return run_target_no_ground_truth(target_name, target_config, output_dir, run_start)

        cutoff = float(target_config.get("enm_cutoff", DEFAULT_CUTOFF))
        pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))

        _log(f"{target_name}: fetching + cleaning apo/holo...")
        t0 = time.monotonic()
        apo, holo = _load_apo_holo(target_name, target_config)
        _log(f"{target_name}: apo/holo ready in {time.monotonic() - t0:.1f}s (N={len(apo.resnums)})")

        _log(f"{target_name}: building labels...")
        t0 = time.monotonic()
        labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
        _log(f"{target_name}: labels built in {time.monotonic() - t0:.1f}s")
        if labels_obj.pocket is None:
            raise RuntimeError(
                f"no resolvable drug_ligand for {target_name!r} -- "
                "build_labels returned pocket=None, cannot score a pocket label"
            )

        # Full active-site array, incoherent statistical mixture -- the one
        # declared seed convention (TASK-0118, INV-0006), used everywhere
        # a scored quantity is computed. This script previously used a
        # single representative seed index (TASK-0090: select.py's
        # candidate-scoring path crashed on a multi-index source) --
        # TASK-0090 fixed that crash, and TASK-0118's own real 3-target
        # sweep (scripts/seed_convention_sweep.py) confirmed this seed
        # choice is not a gauge (KRAS_G12C AUC spread 0.326 across
        # conventions, decisively above the panel's own 0.1 "this is a
        # real signal, not invariant" threshold) -- so a *declared*
        # convention, not an invariance claim, is what removes the
        # apples-to-oranges comparison the review's central finding
        # identified (floor/actual used a single index while
        # ceiling_search_batched.py already used the full array).
        active_site_idx = np.where(labels_obj.active_site)[0]
        if len(active_site_idx) == 0:
            raise RuntimeError(
                f"no active-site residues resolved for {target_name!r} -- "
                "build_labels returned an empty active_site mask"
            )
        source = np.sort(active_site_idx)
        # TASK-0094 (REVIEW-2026-07-13 P1-A): degree_centrality alone is not
        # the confounding variable -- proximity to the propagation seed is.
        # classify_failure takes the max AUC across all three, so a target
        # must beat the strongest trivial explanation available, not just
        # graph degree.
        floor_scores = [
            degree_centrality(apo.coords, cutoff=cutoff),
            euclid_from_seed_centroid(apo.coords, source),
            hop_from_seed(apo.coords, source, cutoff=cutoff),
        ]
        candidates_builder = _make_candidates_builder(apo, source, cutoff)

        # TASK-0150: closes SEAM-0007 (TASK-0059) for a real caller -- the
        # learnability-gate verdict (superpose.compute_learnability, the
        # pocket-restricted-CO-corrected successor to scripts/learnability_
        # gate.py's own original computation) is computed here and passed
        # to run_frozen_verdict below so it lands inline in this run's own
        # verdict.json, not only in that separate script's own output.
        # Caught locally, not left to crash the whole target: this is a
        # diagnostic riding alongside the real score, and TASK-0059's own
        # `learnability=None` default already means "simply not attached"
        # is a fully supported, non-error state -- an unexpected failure
        # here must degrade to that same state, not abort a target whose
        # actual AUC/hit-list computation would otherwise have succeeded.
        _log(f"{target_name}: computing learnability gate...")
        try:
            learnability = compute_learnability(
                apo, holo, target_config, labels_obj.pocket, anm_cutoff=cutoff,
            )
            _log(f"{target_name}: learnability={learnability['verdict']}")
        except Exception as exc:
            _log(f"{target_name}: learnability gate failed ({exc!r}), omitting from verdict")
            learnability = None

        leak_n_perm = _leak_check_n_perm_for(len(apo.resnums))
        _log(f"{target_name}: running frozen verdict (candidate selection + scoring, the expensive eigendecomposition stage; GATE-B4 leak check at n_perm={leak_n_perm})...")
        t0 = time.monotonic()
        result = run_frozen_verdict(
            target_name, candidates_builder,
            apo.coords, apo.bfactors, source, labels_obj.pocket,
            cutoff=cutoff, t_max=SELECTION_GSR_ABLATION_T, n_steps=SELECTION_GSR_ABLATION_N_STEPS,
            floor_scores=floor_scores, coherent=False,
            learnability=learnability, use_converged_limit=True,
            leak_check_n_perm=leak_n_perm,
        )
        _log(f"{target_name}: frozen verdict done in {time.monotonic() - t0:.1f}s -- diagnosis={result.get('_diagnosis')}")

        # TASK-0218 (closes the gap TASK-0087 found): a hard failure, not
        # a warning buried in logs -- raises so the existing per-target
        # try/except in run_target writes error.txt and the target is
        # never reported as a clean success, per this task's own
        # Intent Contract ("a positive detection is a hard failure").
        leak_check = result.get("_leak_check")
        if leak_check is not None and leak_check.get("leak_detected"):
            raise RuntimeError(
                f"{target_name}: GATE-B4 leak check FIRED -- perm_mean="
                f"{leak_check['perm_mean']:.3f} > threshold={leak_check['threshold']} "
                f"at n_perm={leak_check['n_perm']}. The winning candidate's own "
                "scoring step tracks shuffled labels -- this result is not trustworthy "
                "and must be investigated before use, not silently reported."
            )

        winner_H = candidates_builder()[result["_winner_index"]]["H"]
        # TASK-0160: one eigendecomposition, reused for both the winner's
        # own (seeded) occupation and the new dense, all-pairs quantum
        # connectivity matrix -- no second diagonalization.
        w_winner, v_winner = np.linalg.eigh(winner_H)
        winner_occ = time_averaged_ctqw_converged(source=source, coherent=False, w=w_winner, v=v_winner)
        q_matrix = quantum_connectivity_matrix(w=w_winner, v=v_winner)

        propensity = edge_propensity(winner_H, source)
        matrix = edge_propensity_to_matrix(propensity, n=len(apo.resnums))

        hits = assemble_hit_list(winner_occ, labels_obj, resnums=apo.resnums, k=5)
        report_text = verdict_template(result, provenance="frozen")

        # TASK-0180: spatially deduplicated sites, on top of the same
        # winner_occ/source/labels_obj.pocket already computed above --
        # additive only, nothing above this point is touched. TASK-0177's
        # consensus label is still In Progress (no frozen labels exist
        # yet, confirmed by reading that task file) -- this uses the
        # incumbent `labels_obj.pocket` (the `pocket_contact_cutoff`
        # contact label, per this task's own stated fallback) and records
        # that provenance explicitly, not silently.
        _log(f"{target_name}: clustering top-scoring residues into sites...")
        t0 = time.monotonic()
        site_result = cluster_sites(apo.coords, winner_occ, resnums=apo.resnums)
        site_hit = site_hit_metrics(site_result["top_sites"], labels_obj.pocket, apo.coords)
        chance = site_chance_level(apo.coords, len(apo.resnums), labels_obj.pocket)
        proximity_floor = site_proximity_floor(apo.coords, source, labels_obj.pocket)
        knob_spread = site_knob_sweep(apo.coords, winner_occ, labels_obj.pocket)
        _log(
            f"{target_name}: site clustering done in {time.monotonic() - t0:.1f}s -- "
            f"{len(site_result['top_sites'])} site(s), knob_spread={knob_spread['verdict']}"
        )

        # TASK-0225: the residue-level proximity floor (degree/euclid/hop
        # baseline, via classify_failure -- already computed above as part
        # of `result`, not recomputed here) was reachable only via
        # `end_to_end.json`'s own `residue_level` key, written further
        # below. A top-5 hit list with no floor next to it is exactly the
        # defect this register criticises in the `main` branch demo --
        # attached here too, additive, same run, so the two files cannot
        # disagree (both read the identical `result` object).
        residue_level_floor = {
            "auc": result.get("AUC_apo_Hnew_optimised"),
            "diagnosis": result.get("_diagnosis"),
            "floor_ci": result.get("_diagnosis_floor_ci"),
            "score_ci": result.get("_diagnosis_score_ci"),
            "ci_overlap": result.get("_diagnosis_ci_overlap"),
        }

        target_dir.mkdir(parents=True, exist_ok=True)
        np.savez(target_dir / "connectivity_matrix.npz", matrix=matrix, resnums=apo.resnums)
        np.savez(target_dir / "quantum_connectivity_matrix.npz", matrix=q_matrix, resnums=apo.resnums)
        with open(target_dir / "hit_list.json", "w") as f:
            json.dump({
                "residue_level_floor": residue_level_floor,
                "indices": hits["indices"].tolist(),
                "resnums": hits["resnums"].tolist() if hits["resnums"] is not None else None,
                "scores": hits["scores"].tolist(),
                # TASK-0180: additive-only key -- indices/resnums/scores
                # above stay byte-identical, pinned by
                # test_run_challenge.py::test_residue_level_keys_unchanged_by_site_addition.
                "sites": {
                    "top_sites": site_result["top_sites"],
                    "hit_metrics": site_hit,
                    "chance_level": chance,
                    "proximity_floor": proximity_floor["hit_metrics"],
                    "knob_spread": knob_spread,
                },
            }, f, indent=2)
        with open(target_dir / "report.txt", "w") as f:
            f.write(report_text)
        verdict_json = _jsonify(result)
        with open(target_dir / "verdict.json", "w") as f:
            json.dump(verdict_json, f, indent=2)

        residue_level = {
            "AUC_apo_Hnew_optimised": verdict_json.get("AUC_apo_Hnew_optimised"),
            "diagnosis": verdict_json.get("_diagnosis"),
            "diagnosis_score_ci": verdict_json.get("_diagnosis_score_ci"),
            "diagnosis_floor_ci": verdict_json.get("_diagnosis_floor_ci"),
            "diagnosis_ci_overlap": verdict_json.get("_diagnosis_ci_overlap"),
        }
        end_to_end = end_to_end_record(
            target_name=target_name,
            apo_pdb=target_config.get("apo_pdb"),
            holo_pdb=target_config.get("holo_pdb"),
            label_source=f"incumbent_{pocket_cutoff}A_contact",
            cluster_result=site_result,
            site_hit=site_hit,
            chance=chance,
            floor=proximity_floor["hit_metrics"],
            knob_spread=knob_spread,
            residue_level=residue_level,
        )
        with open(target_dir / "end_to_end.json", "w") as f:
            json.dump(end_to_end, f, indent=2)
        # Appended to output_dir's own RESULTS.md, not the repo-root file
        # -- keeps each run's own summary alongside its own outputs and
        # (deliberately) keeps a bare `run_target` call, including every
        # test in this suite, from mutating the checked-in root
        # RESULTS.md as a side effect. Merging a run's summary into the
        # root file is a separate, human-reviewed step.
        with open(output_dir / "RESULTS.md", "a") as f:
            f.write(f"\n## {target_name}\n\n{end_to_end['statement']}\n")

        _log(f"{target_name}: DONE in {time.monotonic() - run_start:.1f}s total")
        return {"target": target_name, "ok": True, "diagnosis": result.get("_diagnosis")}

    except Exception as exc:
        target_dir.mkdir(parents=True, exist_ok=True)
        with open(target_dir / "error.txt", "w") as f:
            f.write(f"{target_name}: FAILED\n\n{traceback.format_exc()}")
        _log(f"{target_name}: FAILED after {time.monotonic() - run_start:.1f}s -- {exc!r}")
        return {"target": target_name, "ok": False, "error": str(exc)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", required=True, help="one or more config/targets.yaml keys")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="print which targets would run (and validate their config) without executing",
    )
    args = parser.parse_args(argv)

    if args.dry_run:
        for name in args.target:
            try:
                load_target_config(name)
                print(f"{name}: OK (config resolves)")
            except Exception as exc:
                print(f"{name}: CONFIG ERROR -- {exc}")
        return 0

    results = [run_target(name, args.output_dir) for name in args.target]
    for r in results:
        status = "OK" if r["ok"] else "FAILED"
        detail = r.get("diagnosis") or r.get("error")
        print(f"{r['target']}: {status} -- {detail}")

    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
