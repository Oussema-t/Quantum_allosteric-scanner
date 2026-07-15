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
is typically several residues (every `func_ligand` contact), and
`analysis.benchmark`/`ablation`/`quantum_vs_classical` all accept a
multi-index seed fine. `select.unsupervised_score` does not -- a real,
reproducible crash (`ballistic_exponent`'s BFS assumes a scalar seed,
filed as TASK-0090, not fixed here; that module is Done/owned elsewhere
and this script's job is to wire existing pieces, not patch them
mid-orchestration). This script therefore uses a single representative
seed index (the first, sorted, active-site residue) throughout its own
pipeline -- consistently for candidate selection *and* scoring, so the
"default" and "optimised" AUC numbers stay comparable (seeded the same
way), rather than picking a multi-index seed for scoring and a
different scalar for selection. Delete this workaround once TASK-0090
lands and widen back to the full active-site array.
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
from allostery.propagators import time_averaged_ctqw  # noqa: E402
from allostery.protocol import run_frozen_verdict  # noqa: E402
from allostery.report import assemble_hit_list, no_ground_truth_report, verdict_template  # noqa: E402

def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results"
DEFAULT_CUTOFF = 10.0  # analysis.py's own default, used only if a target's config omits enm_cutoff
DEFAULT_POCKET_CUTOFF = 4.5
T_MAX = 15.0
N_STEPS = 500


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
            {"H": H_new, "source": source, "t": T_MAX, "name": "H_new_default"},
            {"H": H10, "source": source, "t": T_MAX, "name": "H10_disorder_suppressed"},
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
    consensus = consensus_ranking(apo.coords, apo.bfactors, active_idx, cutoff=cutoff, t_max=T_MAX, n_steps=N_STEPS, k=5)
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
    _log(f"{target_name}: connectivity matrix done in {time.monotonic() - t0:.1f}s")

    hit_indices = np.asarray(consensus["consensus_ranked_indices"])
    hit_scores = consensus["mean_occupancy"][hit_indices]

    report_text = no_ground_truth_report(target_name, consensus, docking, resnums=apo.resnums)

    _log(f"{target_name}: writing deliverables to {target_dir}...")
    target_dir.mkdir(parents=True, exist_ok=True)
    np.savez(target_dir / "connectivity_matrix.npz", matrix=matrix, resnums=apo.resnums)
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

        # Single representative seed index, not the full active-site array --
        # see this script's own module docstring ("Seed residue") for why
        # (TASK-0090: select.py's candidate-scoring path crashes on a
        # multi-index source).
        active_site_idx = np.where(labels_obj.active_site)[0]
        if len(active_site_idx) == 0:
            raise RuntimeError(
                f"no active-site residues resolved for {target_name!r} -- "
                "build_labels returned an empty active_site mask"
            )
        source = int(np.sort(active_site_idx)[0])
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

        _log(f"{target_name}: running frozen verdict (candidate selection + scoring, the expensive eigendecomposition stage)...")
        t0 = time.monotonic()
        result = run_frozen_verdict(
            target_name, candidates_builder,
            apo.coords, apo.bfactors, source, labels_obj.pocket,
            cutoff=cutoff, t_max=T_MAX, n_steps=N_STEPS,
            floor_scores=floor_scores,
        )
        _log(f"{target_name}: frozen verdict done in {time.monotonic() - t0:.1f}s -- diagnosis={result.get('_diagnosis')}")

        winner_H = candidates_builder()[result["_winner_index"]]["H"]
        winner_occ = time_averaged_ctqw(winner_H, T_MAX, source=source, n_steps=N_STEPS)

        propensity = edge_propensity(winner_H, source)
        matrix = edge_propensity_to_matrix(propensity, n=len(apo.resnums))

        hits = assemble_hit_list(winner_occ, labels_obj, resnums=apo.resnums, k=5)
        report_text = verdict_template(result, provenance="frozen")

        target_dir.mkdir(parents=True, exist_ok=True)
        np.savez(target_dir / "connectivity_matrix.npz", matrix=matrix, resnums=apo.resnums)
        with open(target_dir / "hit_list.json", "w") as f:
            json.dump({
                "indices": hits["indices"].tolist(),
                "resnums": hits["resnums"].tolist() if hits["resnums"] is not None else None,
                "scores": hits["scores"].tolist(),
            }, f, indent=2)
        with open(target_dir / "report.txt", "w") as f:
            f.write(report_text)
        with open(target_dir / "verdict.json", "w") as f:
            json.dump(_jsonify(result), f, indent=2)

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
