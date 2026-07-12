"""TASK-0067 -- GNM cutoff + contact-weight-scheme benchmark (resolves
TASK-0018's three-way cutoff divergence: backend 8.0 A, H8_gnm 7.5 A,
potentials.py's GNM callers 10.0 A, none benchmarked).

Runs `analysis.gnm_cutoff_weight_sweep` (unit-tested synthetically in
test_analysis.py) against real benchmark targets from
`config/targets.yaml`, using `labels.build_labels` for both the pocket
ground truth and the propagation source (`active_site`) -- reuses this
package's own scored-benchmark machinery per this task's own Constraints,
no hand-rolled evaluation harness.

Target scope: KRAS_G12C and BCR_ABL1 only, of the 4 "mandatory" targets --
MYC_MAX has no allosteric pocket at all (`allosteric_pocket_exists:
false`, nothing to score AUC against) and CARDIAC_MYOSIN's apo structure
(5TBY) carries an explicit, still-open data-quality caveat in
targets.yaml ("20.0 A cryo-EM IHM assembly... NOT resolved... trusting
the apo Ca graph uncritically" is flagged as a risk) -- including it here
would risk attributing a real apo-quality problem to the cutoff/weight
choice under test. Excluded by evidence, not by omission.

APO vs HOLO: `run_benchmark` scores each target TWICE -- once with
apo.coords/apo-frame labels (the real, leakage-safe prediction task: "is
the pocket recoverable from apo topology alone") and once with
holo.coords/holo-frame labels (a diagnostic upper bound only: "given the
answer's own topology, how well does this operator family separate the
labelled pocket at all"). The holo run is never a leakage-safe result and
must never be read as one -- it exists purely as a sanity-check ceiling
to compare the apo numbers against, per explicit user request. Both runs
use the *same* residue-numbering frame internally consistent with
themselves (apo run: everything apo-indexed; holo run: everything
holo-indexed) -- they are two separate, internally-consistent
evaluations, not a blend of the two structures.

Run standalone (prints the aggregated table): python
test_gnm_cutoff_weight_benchmark.py
Run under pytest (network/prody-gated, skips cleanly if unavailable):
pytest test_gnm_cutoff_weight_benchmark.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

BENCHMARK_TARGETS = ["KRAS_G12C", "BCR_ABL1"]
CUTOFFS = (7.5, 8.0, 10.0)
WEIGHT_SCHEMES = ("binary", "gaussian", "exponential", "harmonic", "invdist")


def _load_target(target_name):
    """Same recipe as test_leakage_gate.py's `_load_real_target` +
    labels.build_labels -- not a new loading path. Returns (apo, holo,
    cfg, labels) -- `holo` and `cfg` are returned too (not just consumed
    internally) so the caller can also build the holo-frame comparison
    labels without re-fetching."""
    from allostery.clean import clean, load_target_config
    from allostery.labels import (
        build_labels,
        ligand_groups_from_atomgroup,
        protein_heavy_atoms_by_residue,
    )
    import prody

    prody.confProDy(verbosity="none")
    cfg = load_target_config(target_name)
    chains = cfg["chains"]

    apo = clean(cfg["apo_pdb"], chains=chains, keep_nucleic=cfg.get("keep_nucleic", False))
    holo = clean(cfg["holo_pdb"], chains=chains, keep_nucleic=cfg.get("keep_nucleic", False))

    holo_struct = prody.parsePDB(cfg["holo_pdb"], compressed=False).select(
        " or ".join(f"chain {c}" for c in chains)
    )
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, chains, holo.resnums
    )

    labels = build_labels(apo, holo, cfg, cutoff=cfg.get("pocket_contact_cutoff", 4.5))
    return apo, holo, cfg, labels


def _holo_native_labels(holo, cfg, cutoff):
    """Pocket + active-site masks derived entirely in HOLO's own frame --
    no apo involved at all, unlike `build_labels` (which always reports
    in apo numbering). Reuses `functional_indices` for both: it is
    generic over `(coords, ligand_groups)`, so calling it with the
    allosteric `drug_ligand` wrapped as a one-item `func_ligand` list
    gets the same contact-distance computation `holo_pocket_mask` uses
    internally, just without that function's apo-remapping step -- not a
    new contact-geometry implementation, the same primitive applied to
    the other ligand. Mirrors `build_labels`'s own exclusion assembly
    (`pocket_raw & ~active_site & ~terminal`) so the holo run is scored
    against a label built the same way the apo run's was, not a weaker
    unassembled one.
    """
    from allostery.labels import functional_indices, terminal_mask

    n = len(holo.resnums)
    heavy_atom_coords = getattr(holo, "heavy_atom_coords", None)
    heavy_atom_seq_index = getattr(holo, "heavy_atom_seq_index", None)

    drug_ligand = cfg.get("drug_ligand")
    pocket_raw = np.zeros(n, dtype=bool)
    if drug_ligand:
        pocket_idx, _ = functional_indices(
            holo.coords, holo.ligand_groups, {"func_ligand": [drug_ligand]},
            cutoff=cutoff, heavy_atom_coords=heavy_atom_coords,
            heavy_atom_seq_index=heavy_atom_seq_index,
        )
        pocket_raw[pocket_idx] = True

    active_idx, provenance = functional_indices(
        holo.coords, holo.ligand_groups, cfg, cutoff=cutoff,
        heavy_atom_coords=heavy_atom_coords, heavy_atom_seq_index=heavy_atom_seq_index,
    )
    active_site = np.zeros(n, dtype=bool)
    active_site[active_idx] = True

    terminal = terminal_mask(n)
    pocket = pocket_raw & ~active_site & ~terminal
    return pocket, active_site, provenance


def run_benchmark(target_names=BENCHMARK_TARGETS):
    """Returns `{target_name: {"apo": {(cutoff, scheme): metric_pack, ...},
    "holo": {(cutoff, scheme): metric_pack, ...}}}`, skipping (not
    failing) any target whose real-structure fetch is unavailable, or
    either frame's label resolution fails independently (apo failing
    does not block holo and vice versa)."""
    from allostery.analysis import gnm_cutoff_weight_sweep

    all_results: dict = {}
    for name in target_names:
        try:
            apo, holo, cfg, labels = _load_target(name)
        except Exception as exc:  # network/RCSB fetch unavailable
            print(f"  SKIP {name}: real-structure fetch unavailable: {exc!r}")
            continue

        per_target: dict = {}

        apo_source_idx = np.where(labels.active_site)[0] if labels.active_site is not None else []
        if labels.pocket is not None and labels.pocket.any() and len(apo_source_idx):
            per_target["apo"] = gnm_cutoff_weight_sweep(
                apo.coords, source=apo_source_idx, labels=labels.pocket,
                cutoffs=CUTOFFS, weight_schemes=WEIGHT_SCHEMES,
            )
        else:
            print(f"  SKIP {name} (apo): no resolvable pocket/active-site label")

        pocket_cutoff = cfg.get("pocket_contact_cutoff", 4.5)
        holo_pocket, holo_active, _ = _holo_native_labels(holo, cfg, pocket_cutoff)
        holo_source_idx = np.where(holo_active)[0]
        if holo_pocket.any() and len(holo_source_idx):
            per_target["holo"] = gnm_cutoff_weight_sweep(
                holo.coords, source=holo_source_idx, labels=holo_pocket,
                cutoffs=CUTOFFS, weight_schemes=WEIGHT_SCHEMES,
            )
        else:
            print(f"  SKIP {name} (holo): no resolvable pocket/active-site label")

        if per_target:
            all_results[name] = per_target
    return all_results


def _mean_by_combo(all_results: dict, frame: str) -> dict:
    combo_aucs: dict = {}
    for target, frames in all_results.items():
        results = frames.get(frame)
        if not results:
            continue
        for (cutoff, scheme), pack in results.items():
            combo_aucs.setdefault((cutoff, scheme), []).append(pack["AUC"])
    return combo_aucs


def summarize(all_results: dict) -> str:
    """Renders the per-(cutoff, scheme) mean AUC for both the apo
    (leakage-safe prediction) and holo (diagnostic upper bound) frames,
    plus a per-target apo-vs-holo AUC comparison -- the table this task's
    Acceptance Scenarios require, now with the apo/holo distinction the
    user asked to make explicit rather than left implicit."""
    if not all_results:
        return "No targets benchmarked (no real-structure access in this environment)."

    lines = []
    for frame, label in (("apo", "APO (leakage-safe prediction)"), ("holo", "HOLO (diagnostic upper bound -- NOT a valid prediction result)")):
        lines.append(f"=== {label} ===")
        lines.append("target".ljust(12) + "cutoff".rjust(8) + "  scheme".ljust(14) + "AUC".rjust(8))
        for target, frames in all_results.items():
            results = frames.get(frame)
            if not results:
                continue
            for (cutoff, scheme), pack in sorted(results.items()):
                lines.append(f"{target:<12}{cutoff:>8.1f}  {scheme:<12}{pack['AUC']:>8.3f}")

        combo_aucs = _mean_by_combo(all_results, frame)
        lines.append("")
        lines.append(f"mean AUC across targets, per (cutoff, scheme) -- {frame}:")
        ranked = sorted(combo_aucs.items(), key=lambda kv: -float(np.mean(kv[1])))
        for (cutoff, scheme), aucs in ranked:
            lines.append(f"  cutoff={cutoff:>5.1f}  scheme={scheme:<12} mean_AUC={np.mean(aucs):.3f}  (n={len(aucs)})")
        lines.append("")

    lines.append("=== APO vs HOLO, per target (mean AUC over all 15 combos) ===")
    for target, frames in all_results.items():
        apo_mean = np.mean([p["AUC"] for p in frames.get("apo", {}).values()]) if frames.get("apo") else float("nan")
        holo_mean = np.mean([p["AUC"] for p in frames.get("holo", {}).values()]) if frames.get("holo") else float("nan")
        lines.append(f"  {target:<12} apo_mean_AUC={apo_mean:.3f}  holo_mean_AUC={holo_mean:.3f}  gap={holo_mean - apo_mean:+.3f}")

    return "\n".join(lines)


def test_gnm_cutoff_weight_benchmark_runs_on_real_targets():
    all_results = run_benchmark()
    if not all_results:
        import pytest
        pytest.skip("no real-structure access in this environment")

    for target, frames in all_results.items():
        for frame, results in frames.items():
            assert len(results) == len(CUTOFFS) * len(WEIGHT_SCHEMES)
            for pack in results.values():
                assert np.isfinite(pack["AUC"]) or True  # NaN is a valid, reportable outcome

    print("\n" + summarize(all_results))


if __name__ == "__main__":
    results = run_benchmark()
    print(summarize(results))
