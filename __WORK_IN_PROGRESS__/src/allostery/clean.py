"""Phase 0b – deterministic structure cleanup.

Driven by config/targets.yaml so every cleaning decision is reproducible
without PyMOL or manual intervention.

Key guarantees
--------------
- Only one model (MODEL 1 / first ATOM block) is kept.
- Alternate locations: only the 'A' alt-loc (or highest occupancy) is kept.
- Insertion codes are stripped; residues are flagged in the quality report.
- Waters, common ions, and crystallographic cofactors are removed.
- Nucleic acid is retained only when keep_nucleic=True (MYC_MAX).
- The resulting Cα graph's connectivity is checked and reported via
  `warnings`/`CleanResult.warnings`; `clean()` itself never raises on a
  disconnected graph, deliberately (TASK-0038, see `_assert_connected`'s
  own docstring) — a caller gets a `CleanResult` back either way, so a
  single bad chain break doesn't abort a run before quality metadata can
  be inspected. Disconnection *is* enforced as a hard error downstream,
  independently of this module: `superpose.py`'s ANM rigid-body-nullspace
  check raises when the contact graph it operates on is disconnected
  (TASK-0005's original regression) — that is the real gate, not this
  one. (Corrected 2026-08-14, TASK-0038 — this line previously claimed
  "disconnected graphs are an error," contradicting `_assert_connected`'s
  actual warn-only behavior; the earlier `PLAN.md` Phase 0 gate language
  this also referenced no longer exists in the repo.)
- Quality metadata (resolution, B-factor stats, gap list) is returned alongside
  the clean coordinates.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import yaml


# Residue names that are NOT structural protein/nucleic residues
_COMMON_SOLVENTS = {"HOH", "WAT", "H2O", "DOD", "D2O"}
_COMMON_IONS = {
    "MG", "ZN", "CA", "NA", "CL", "K", "MN", "FE", "CU", "CO",
    "NI", "CD", "HG", "PB", "SO4", "PO4", "GOL", "EDO", "PEG",
    "ACT", "ACE", "FMT", "DMS", "MPD", "TRS", "BME",
}


@dataclass
class CleanResult:
    pdb_id: str
    coords: np.ndarray          # (N, 3) Cα/P coordinates
    resnums: np.ndarray         # (N,) residue numbers (original numbering)
    resnames: list[str]         # 3-letter residue names
    chain_ids: list[str]        # chain IDs
    resolution: float | None    # crystallographic resolution in Å, None if unavailable
    bfactors: np.ndarray        # (N,) per-residue Cα B-factor (TASK-0008: build_H_new/H10 need the full array, not just b_mean/b_std)
    b_mean: float               # mean B-factor of Cα atoms
    b_std: float                # std of B-factors
    gap_pairs: list[tuple[int, int]]  # (res_i, res_j) pairs where |resnum gap| > 1
    insertion_code_residues: list[str]  # residues that had insertion codes (flagged)
    warnings: list[str] = field(default_factory=list)

    @property
    def n_residues(self) -> int:
        return len(self.resnums)


def load_target_config(target_name: str, config_path: str | Path | None = None) -> dict:
    """Load a single target's config dict from targets.yaml."""
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "targets.yaml"
    with open(config_path) as f:
        data = yaml.safe_load(f)
    targets = data.get("targets", {})
    if target_name not in targets:
        raise KeyError(
            f"Unknown target '{target_name}'. Available: {list(targets.keys())}"
        )
    return targets[target_name]


def clean(
    pdb_id: str,
    chains: list[str] | None = None,
    keep_nucleic: bool = False,
) -> CleanResult:
    """Fetch and clean a PDB structure, returning a CleanResult.

    Parameters
    ----------
    pdb_id : str
        PDB accession code.
    chains : list[str] | None
        Chains to keep (None = all protein chains).
    keep_nucleic : bool
        If True, nucleic-acid residues are retained (P atom as representative).
    """
    import prody

    prody.confProDy(verbosity="none")
    # altloc="all" (TASK-0039): prody's own default (altloc="A") silently
    # drops every non-'A' conformer at parse time, before any occupancy
    # comparison is possible -- confirmed directly (8QYR's own B/C-labeled
    # atoms, real occupancy data, are invisible under the default). "all"
    # keeps every alt-loc as a distinct atom record (same coordset, not a
    # second model), so the block below can actually compare them.
    try:
        struct = prody.parsePDB(pdb_id, altloc="all", compressed=False)
    except prody.proteins.pdbfile.PDBParseError:
        # TASK-0276: legacy PDB text format cannot represent a 5-character
        # extended chemical-component ID (RCSB's newer convention once the
        # classic 3-character alphabet was exhausted, e.g. A1L9E/A1H5U) --
        # the fixed-width HETATM columns overflow and corrupt the
        # coordinate fields for EVERY atom in the file, not just the
        # offending ligand's, so even a protein-only parse fails (confirmed
        # directly: 9UOH, 8S8C). Falls back to mmCIF -- prody's AtomGroup
        # from parseMMCIF supports the same getAltlocs/getChids/getResnums/
        # getIcodes/select methods the rest of this function already calls,
        # so nothing below this block needs to change. `format="cif"` must
        # be fetched via the ALREADY-wrapped `prody.fetchPDB` (this
        # package's own `pdb_cache/` folder default) rather than
        # `parseMMCIF(pdb_id)` directly -- that function's own internal
        # fetch call bypasses the folder default entirely (TASK-0273's own
        # finding), scattering files into cwd.
        cif_path = prody.fetchPDB(pdb_id, format="cif", compressed=False)
        struct = prody.parseMMCIF(cif_path, altloc="all")
    if struct is None:
        raise ValueError(f"prody failed to parse '{pdb_id}'")

    warn_list: list[str] = []

    # --- Alternate location handling: highest-occupancy conformer per
    # residue, 'A' as tiebreak/fallback (TASK-0039 -- matches this
    # module's own docstring guarantee, previously unconditional 'A'). ---
    alt_locs = struct.getAltlocs()
    if alt_locs is not None and any(a not in ("", " ", "\x00") for a in alt_locs):
        chids_al = struct.getChids()
        resnums_al = struct.getResnums()
        occ_al = struct.getOccupancies()

        by_res: dict[tuple[str, int], dict[str, list[float]]] = {}
        for i in range(len(alt_locs)):
            a = alt_locs[i]
            if a in ("", " ", "\x00"):
                continue
            key = (str(chids_al[i]), int(resnums_al[i]))
            by_res.setdefault(key, {}).setdefault(str(a), []).append(
                float(occ_al[i]) if occ_al is not None else float("nan")
            )

        chosen_label: dict[tuple[str, int], str] = {}
        non_a_flagged: list[str] = []
        for key, label_occ in by_res.items():
            labels = list(label_occ.keys())
            if len(labels) == 1:
                chosen_label[key] = labels[0]
                continue
            means = {lab: float(np.mean(vals)) for lab, vals in label_occ.items()}
            if any(np.isnan(v) for v in means.values()):
                best = "A" if "A" in labels else sorted(labels)[0]
            else:
                max_val = max(means.values())
                tied = [lab for lab, v in means.items() if v == max_val]
                best = "A" if "A" in tied else sorted(tied)[0]
            chosen_label[key] = best
            if best != "A":
                chain, resnum = key
                non_a_flagged.append(f"{chain}{resnum}(altloc={best})")

        keep_mask = np.ones(len(alt_locs), dtype=bool)
        for i in range(len(alt_locs)):
            a = alt_locs[i]
            if a in ("", " ", "\x00"):
                continue
            key = (str(chids_al[i]), int(resnums_al[i]))
            if str(a) != chosen_label.get(key, "A"):
                keep_mask[i] = False
        struct = struct[np.where(keep_mask)[0]]

        warn_list.append(
            f"{pdb_id}: alternate locations detected; kept the highest-occupancy "
            "conformer per residue ('A' as tiebreak/fallback)."
        )
        if non_a_flagged:
            warn_list.append(
                f"{pdb_id}: {len(non_a_flagged)} residue(s) kept a non-'A' alt-loc "
                f"as the highest-occupancy conformer: {non_a_flagged[:5]}"
                f"{'...' if len(non_a_flagged) > 5 else ''}"
            )

    # --- Select protein (+ optional nucleic), specific chains ---
    type_sel = "protein"
    if keep_nucleic:
        type_sel = "protein or nucleic"

    chain_part = ""
    if chains:
        chain_part = " and (" + " or ".join(f"chain {c}" for c in chains) + ")"

    struct_clean = struct.select(f"({type_sel}){chain_part}")
    if struct_clean is None:
        raise ValueError(
            f"No residues selected in {pdb_id} with type='{type_sel}' chains={chains}"
        )

    # --- Insertion code detection (flag, do not discard) ---
    icode_residues: list[str] = []
    try:
        icodes = struct_clean.getIcodes()
        if icodes is not None:
            flagged = set()
            for atom, ic in zip(struct_clean, icodes):
                if ic not in ("", " ", "\x00"):
                    key = f"{atom.getChid()}{atom.getResnum()}{ic}"
                    if key not in flagged:
                        icode_residues.append(key)
                        flagged.add(key)
            if icode_residues:
                warn_list.append(
                    f"{pdb_id}: {len(icode_residues)} residues with insertion codes: "
                    f"{icode_residues[:5]}{'...' if len(icode_residues) > 5 else ''}"
                )
    except Exception:
        pass

    # --- Extract Cα (and P for nucleic) ---
    ca_sel = "name CA"
    if keep_nucleic:
        ca_sel = "name CA or (nucleic and name P)"

    ca_atoms = struct_clean.select(ca_sel)
    if ca_atoms is None or len(ca_atoms) == 0:
        raise ValueError(f"No Cα/P atoms after cleaning {pdb_id}")

    coords = ca_atoms.getCoords().astype(np.float64)
    resnums = ca_atoms.getResnums().astype(np.int32)
    resnames = ca_atoms.getResnames().tolist()
    chain_ids = ca_atoms.getChids().tolist()

    # --- B-factor statistics ---
    bfacs = ca_atoms.getBetas()
    if bfacs is not None:
        bfactors = bfacs.astype(np.float64)
        b_mean = float(np.mean(bfacs))
        b_std = float(np.std(bfacs))
        if b_std < 0.1:
            warn_list.append(
                f"{pdb_id}: B-factors nearly constant (std={b_std:.3f}) – "
                "possibly a homology model or degenerate entry."
            )
    else:
        bfactors = np.full(len(coords), np.nan)
        b_mean, b_std = float("nan"), float("nan")
        warn_list.append(f"{pdb_id}: B-factors unavailable.")

    # --- Resolution ---
    resolution: float | None = None
    try:
        header = prody.parsePDBHeader(pdb_id)
        resolution = float(header.get("resolution", 0.0)) or None
        if resolution is not None and resolution > 3.5:
            warn_list.append(
                f"{pdb_id}: resolution {resolution:.1f} Å > 3.5 Å – reduced reliability."
            )
    except Exception:
        pass

    # --- Gap detection: consecutive Cα pairs in same chain with |resnum| > 1 ---
    gap_pairs: list[tuple[int, int]] = []
    for i in range(len(resnums) - 1):
        if chain_ids[i] == chain_ids[i + 1]:
            delta = int(resnums[i + 1]) - int(resnums[i])
            if delta > 1:
                gap_pairs.append((int(resnums[i]), int(resnums[i + 1])))
    if gap_pairs:
        warn_list.append(
            f"{pdb_id}: {len(gap_pairs)} residue gaps in sequence numbering "
            f"(first 3: {gap_pairs[:3]}). Virtual bonds will bridge these."
        )

    # --- Connectivity check: Laplacian nullspace dim must equal 1 ---
    _assert_connected(coords, pdb_id, warn_list)

    return CleanResult(
        pdb_id=pdb_id,
        coords=coords,
        resnums=resnums,
        resnames=resnames,
        chain_ids=chain_ids,
        resolution=resolution,
        bfactors=bfactors,
        b_mean=b_mean,
        b_std=b_std,
        gap_pairs=gap_pairs,
        insertion_code_residues=icode_residues,
        warnings=warn_list,
    )


def assert_genotype_identity(target_name: str, cfg: dict, role: str, result: CleanResult) -> None:
    """TASK-0354: raises if a loaded structure's own residue identity
    contradicts targets.yaml's recorded genotype/apo verdict for this
    target -- a real, twice-repeated mistake (TASK-0270): a wrong-genotype
    PDB id (4OBE, RCSB-confirmed wild-type at residue 12, not G12C) was
    proposed and used as KRAS_G12C's apo structure, not caught until a
    downstream result (the register's own KRAS_G12C floor-clear) turned
    out not to survive on the correct genotype. The organisers' own
    suggested replacement (8S8C) repeated the same class of mistake in
    the other direction (genuinely G12C, but holo not apo) before 4LDJ was
    settled on -- see that target's own `apo_pdb` comment for the full
    incident.

    Wired into `clean_from_config` itself, same precedent
    `assert_functional_provenance_allowed` (labels.py, TASK-0231) set for
    a build-time assertion: every real caller is protected the moment a
    wrong-genotype structure is actually loaded (proposing a substitution
    interactively, or a live pipeline run), not only whichever test
    happens to check the field directly -- exactly the gap TASK-0231 found
    for `func_ligand` and this task's own filing found again here (a
    pinned `test_kras_g12c_anchors` regression test had gone stale and red
    for 2+ weeks, unnoticed, checking the very genotype this guards).

    `genotype_check` is optional per-target config -- absent (the common
    case; most targets carry no such concern) is a silent no-op. It names
    ONE residue identity to verify, not a pocket-residue list: distinct in
    kind from this file's own HARD RULE against hand-transcribed pocket
    residues, which is about the *derived allosteric pocket*, not a
    single, well-defined mutation-identity fact used only to catch a
    wrong-structure proposal.

    Deliberately does not restate the reasoning in its own error message
    (this task's own Constraint, to prevent the two from drifting apart)
    -- points at targets.yaml's own comment for the *why*.
    """
    check = cfg.get("genotype_check")
    if not check or check.get("role", "apo") != role:
        return
    chain = check["chain"]
    resnum = check["residue"]
    expect = check["expect_resname"]
    match = [
        i
        for i, (c, n) in enumerate(zip(result.chain_ids, result.resnums))
        if c == chain and int(n) == resnum
    ]
    if not match:
        raise ValueError(
            f"{target_name}: genotype_check names chain {chain} residue "
            f"{resnum}, not found in {role} structure {result.pdb_id} "
            f"(chain {chain} may be absent, or this residue was cleaned/"
            "gapped out) -- cannot verify identity. See targets.yaml's own "
            f"{role}_pdb comment for {target_name}."
        )
    actual = result.resnames[match[0]]
    if actual != expect:
        raise ValueError(
            f"{target_name}: {role} structure {result.pdb_id} residue "
            f"{chain}{resnum} is {actual}, expected {expect}. See "
            f"targets.yaml's own {role}_pdb comment for {target_name} for "
            f"why this residue is checked ({check.get('reason_ref', 'no reason_ref recorded')})."
        )


def clean_from_config(target_name: str, role: str = "apo") -> CleanResult:
    """Convenience wrapper: load target config and call clean().

    Parameters
    ----------
    target_name : str
        Key in config/targets.yaml (e.g. 'KRAS_G12C').
    role : {'apo', 'holo'}
        Which PDB structure to load.
    """
    cfg = load_target_config(target_name)
    if cfg.get("quarantine"):
        warnings.warn(
            f"Target '{target_name}' is quarantined: {cfg.get('quarantine_reason', '')}",
            UserWarning,
            stacklevel=2,
        )
    pdb_key = f"{role}_pdb"
    pdb_id = cfg.get(pdb_key)
    if pdb_id is None:
        raise ValueError(
            f"Target '{target_name}' has no '{pdb_key}' defined in config."
        )
    # TASK-0127 / Q-0001: an apo/holo pair can legitimately use different
    # chain letters for the same biological chain (GLUCOKINASE: apo 1V4S is
    # chain A, holo 3H1V is chain X -- both source docs were individually
    # correct, for different structures). `{role}_chains` is an optional
    # per-role override; falls back to the shared `chains` field when absent
    # so every pre-existing target config (which only ever set `chains`) is
    # completely unaffected -- additive, not a breaking schema change.
    chains = cfg.get(f"{role}_chains", cfg.get("chains"))
    keep_nucleic = cfg.get("keep_nucleic", False)
    result = clean(pdb_id, chains=chains, keep_nucleic=keep_nucleic)
    # TASK-0354: build-time genotype/identity guard, see assert_genotype_
    # identity's own docstring -- no-op for the large majority of targets
    # that carry no `genotype_check`.
    assert_genotype_identity(target_name, cfg, role, result)
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _assert_connected(
    coords: np.ndarray,
    pdb_id: str,
    warn_list: list[str],
    cutoff: float = 10.0,
) -> None:
    """Check that the Cα contact graph (at cutoff Å) has exactly one component.
    Warns rather than raises so callers can decide how to handle it --
    deliberate (TASK-0038, confirmed against this module's own docstring
    2026-08-14): a single bad chain break should not abort a clean() run
    before quality metadata can be inspected. The real hard gate on a
    disconnected structure lives downstream, independently of this
    function -- `superpose.py`'s ANM rigid-body-nullspace check raises on
    it (TASK-0005).
    """
    import networkx as nx

    n = len(coords)
    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    dist = np.sqrt((diff ** 2).sum(axis=2))
    adj = (dist < cutoff) & (dist > 0)
    G = nx.from_numpy_array(adj.astype(float))
    n_comp = nx.number_connected_components(G)
    if n_comp != 1:
        warn_list.append(
            f"{pdb_id}: Cα contact graph at {cutoff} Å has {n_comp} connected "
            "components. Check for chain breaks or missing loops."
        )
