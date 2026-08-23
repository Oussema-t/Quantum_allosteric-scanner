#!/usr/bin/env python3
"""TASK-0226 -- PDB-retest of the external drop's observable-family
proximity-confound claim, on real challenge targets.

Source: `.ai/reviews/2026-08-21/TASK-0210_observable_family_confound.md`
(external session, no repo access, no rcsb.org egress -- every number in
that drop was run on bundled non-target structures, prody/MDAnalysisTests
test data). This script re-runs the same method on real apo targets with
real annotated active-site seeds and a real SASA burial control, per that
drop's own Section 5 "PDB-RETEST instructions for repo agents".

**Claim under test**: the proximity confound is a property of seed-
referencing scoring on a static contact graph -- not of the CTQW
propagator, not of quantumness, and not of the correlation-vs-entropy
distinction.

**Targets**: KRAS_G12C (4OBE), BCR_ABL1 (1OPL), CARDIAC_MYOSIN, PTP1B
(1SUG), MYC_MAX/c-Myc (1NKP). CARDIAC_MYOSIN uses `targets.yaml`'s current
`apo_pdb: 8QYP` (TASK-0124's substitution for the drop's own stale "5TBY"
reference -- 5TBY was replaced project-wide in this register; using the
live config keeps this consistent with every other real-target script in
the repo, not the drop's own outdated citation).

**Seeds**: real annotated active/catalytic sites via
`labels.functional_indices(coords, [], target_config, cutoff=...)` --
the exact call `run_challenge.py`'s own no-ground-truth path uses --
replacing the drop's radial-percentile draws entirely, per Section 5's
explicit instruction.

**Burial control**: real per-residue absolute SASA (freesasa,
Shrake-Rupley) on the apo structure alone, `burial = -SASA` (higher =
more buried), replacing the drop's crude centroid-distance proxy.

**Observable groups** (a real cost/fidelity tradeoff, stated up front,
not discovered mid-run):

1. *Per-seed-residue replicates* (cheap; ported directly from the drop's
   own `real_pdb_confound.py`, reusing one cached spectral decomposition
   of this script's own Laplacian per target): `CTQW_adj_T5`,
   `CTQW_adj_T25`, `heat_T5`, `MRW_commute`, `GNM_corr_seed`,
   `GNM_corr_low10` (the drop's own 10-mode port), `dMSF_at_seed`. One
   replicate per real active-site residue (mirrors the drop's own
   per-seed-replicate design, drawing from the real active site instead
   of a random radial-percentile pool).
2. *Seed-blind, computed once per target*: `dS_vib_global`, `slow1_minima`
   (new -- see below). Correlated against every per-seed-residue distance
   vector, exactly as the drop's own script does for `dS_vib_global`.
3. *Full-active-site-set, once per target* (production-matching, cost-
   driven): `prs_low`, `dcc_low` (this repo's own canonical
   `lowmode_predictor` implementations -- k_modes=20, distinct from
   group-1's `GNM_corr_low10` port -- see "resolves" note below),
   `chiral_circ` (`chiral.chiral_circulation_score`), `transmission_E0`
   (`transport.transmission_from_source`, this task's own reading of the
   drop's "ref [7] ENM impulse-response energy transport" request --
   Landauer-Buttiker T(E=0) on the plain GNM Laplacian, already an
   established project observable, TASK-0145). Each of these three
   internally rebuilds an O(N) or O(N^3) spectral object that does NOT
   depend on which individual seed residue is queried (`prs_low`/
   `dcc_low` rebuild ANM/GNM modes fresh per call; `chiral`/`transmission`
   redo an O(N^3) eigendecomposition per call) -- calling them once per
   active-site *residue* (15-25x per target) rather than once per active-
   site *set* would cost 15-25x for no additional information, and would
   also depart from how these functions are actually invoked everywhere
   else in this project's own pipeline (always the full active-site set,
   never single residues). Scored against `baselines.euclid_from_seed_
   centroid`'s own established seed-centroid-distance convention, not a
   per-seed distance vector.

`slow1_minima` (new, ref [16] in the drop's own bibliography, "seed-blind,
modal" family, no existing repo implementation found): this script's own
straightforward reading -- the lowest non-trivial GNM (Kirchhoff) mode's
amplitude, negated in magnitude (`score = -|mode_1|`), so residues near
that mode's node/hinge score highest. Ref [16] itself is Erman B., "The
Gaussian network model: precise prediction of residue fluctuations and
application to binding problems," Biophys J 2006;91:3589-3599 (challenge
bibliography, `documentation/REFERENCES.md` row 16) -- that paper's own
stated finding is exactly this: binding sites sit at minima of the
slowest modes. (An earlier draft of this docstring cited "Gerstein &
Krebs 1998" from memory instead -- checked directly, per
`.ai/reference/PAPER_CITATION_PROTOCOL.md`, and found imprecise: that
1998 paper is the Database of Macromolecular Motions catalog, not a
slow-mode/hinge paper; the actual normal-mode/hinge connection in that
lineage is Krebs et al., Proteins 2002;48:682-695, a different citation
this project has no independent need for once ref [16] already covers
the claim directly. Corrected here rather than left uncited.) This
script's own `score = -|mode_1|` is still this task's own operational
proxy for ref [16]'s concept, not independently verified against that
paper's exact method -- mirroring how `dS_vib_global` is already flagged
in the drop itself as "harmonic proxy, not genuine EAM."

**Resolves** (drop Section 4.3, "load-bearing... discrepancy"): the drop's
own `GNM_corr_low10` (10-mode port, its own hand-rolled math) stayed
confounded (0.870) on non-target structures where this repo's own
`prs_low` collapses to ~0.08 elsewhere. This script runs BOTH on the same
5 real targets side by side -- not assumed to agree, reported either way.

Provenance for every real number below: this script, real network fetch
(RCSB via `clean.clean_from_config`), no mocking. Run:
    ../.venv/bin/python3 scripts/task0226_observable_family_confound_pdb_retest.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np
from scipy.linalg import eigh
from scipy.sparse.csgraph import connected_components, shortest_path
from scipy.stats import rankdata, spearmanr

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.chiral import chiral_circulation_score  # noqa: E402
from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.consensus_labels import load_apo_holo_full  # noqa: E402
from allostery.hamiltonians import contact_matrix, laplacian  # noqa: E402
from allostery.labels import functional_indices  # noqa: E402
from allostery.lowmode_predictor import dcc_low, prs_low  # noqa: E402
from allostery.transport import transmission_from_source  # noqa: E402

import prody  # noqa: E402
import freesasa  # noqa: E402

prody.confProDy(verbosity="none")

TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "PTP1B", "MYC_MAX"]
CUT = 8.5       # matches the drop's own contact-graph cutoff
STIFF = 3.0     # matches the drop's own perturbation magnitude (drop Sec.6.5: not swept)
LOWMODE_CUTOFF = 8.5  # kept consistent with CUT for this retest's own internal comparability
K_MODES = 20

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results" / "tasks" / "0226_observable_family_confound"


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def pspear(x, y, z) -> float:
    """Spearman partial correlation of x vs y controlling z, via linear
    de-trending of ranks against rank(z) -- the drop's own method, ported
    verbatim (not re-derived) for exact comparability to its numbers."""
    rx, ry, rz = rankdata(x), rankdata(y), rankdata(z)
    resid = lambda a: a - np.polyval(np.polyfit(rz, a, 1), rz)
    return float(np.corrcoef(resid(rx), resid(ry))[0, 1])


def sasa_burial(apo, apo_raw, apo_chains: list) -> tuple:
    """Real per-residue absolute SASA on the apo structure alone.
    Returns (burial, n_missing) where burial = -SASA (higher = more
    buried). A handful of residues can go unmapped (insertion codes,
    freesasa's own residue-string quirks) -- filled with the chain-wide
    median, count reported rather than silently dropped (keeps every
    array shape aligned with `apo.resnums`, required downstream)."""
    chain_sel = " or ".join(f"chain {c}" for c in apo_chains)
    sel = apo_raw.select(f"({chain_sel}) and protein")
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "apo.pdb"
        prody.writePDB(str(p), sel)
        s = freesasa.Structure(str(p), options={"hetatm": False})
        areas = freesasa.calc(s).residueAreas()

    sasa = np.full(len(apo.resnums), np.nan)
    for i, (chain, resnum) in enumerate(zip(apo.chain_ids, apo.resnums)):
        chain_areas = areas.get(chain)
        if chain_areas is None:
            continue
        area = chain_areas.get(str(int(resnum)))
        if area is not None:
            sasa[i] = area.total
    n_missing = int(np.isnan(sasa).sum())
    if n_missing:
        sasa[np.isnan(sasa)] = np.nanmedian(sasa)
    return -sasa, n_missing


def slow1_minima_score(Lap: np.ndarray, w: np.ndarray, V: np.ndarray) -> np.ndarray:
    """This task's own proxy for ref [16]'s 'slow-mode minima' -- the
    lowest non-trivial GNM mode's amplitude, negated (higher score =
    closer to that mode's hinge/node). See module docstring."""
    nz = np.flatnonzero(w > 1e-8)
    m1 = V[:, nz[0]]
    return -np.abs(m1)


def compute_target(target_name: str) -> tuple:
    target_config = load_target_config(target_name)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", 4.5))

    # Real active-site resolution requires HOLO's own ligand_groups/heavy-atom
    # data cross-mapped into apo space -- `functional_indices` with an empty
    # `ligand_groups` list (this script's first draft) silently degrades every
    # target with a real func_ligand into the top-degree topological-proxy
    # fallback (caught by inspecting `provenance` on the first real run, not
    # assumed correct). `load_apo_holo_full` (consensus_labels.py) is the
    # existing, already-debugged apo+holo loader that does this correctly --
    # reused here rather than re-deriving. MYC_MAX has no holo at all
    # (`holo_pdb: null`), so it takes the same empty-ligand_groups path
    # `run_target_no_ground_truth` uses for it -- a genuine absence, not a
    # resolution failure.
    if target_config.get("holo_pdb"):
        apo, holo, apo_raw, holo_raw, apo_chains, holo_chains = load_apo_holo_full(
            target_name, target_config
        )
        active_idx, provenance = functional_indices(
            apo.coords,
            holo.ligand_groups,
            target_config,
            cutoff=pocket_cutoff,
            heavy_atom_coords=getattr(holo, "heavy_atom_coords", None),
            heavy_atom_seq_index=getattr(holo, "heavy_atom_seq_index", None),
            heavy_atom_resnames=holo.resnames,
            coords_resnames=apo.resnames,
            coords_resnums=apo.resnums,
        )
    else:
        apo = clean_from_config(target_name, role="apo")
        apo_raw = prody.parsePDB(target_config["apo_pdb"], compressed=False)
        apo_chains = target_config.get("apo_chains") or target_config.get("chains") or sorted(set(apo.chain_ids))
        active_idx, provenance = functional_indices(
            apo.coords, [], target_config, cutoff=pocket_cutoff, coords_resnums=apo.resnums,
        )

    co = apo.coords.astype(float)
    N = len(co)
    active_idx = np.atleast_1d(np.asarray(active_idx, dtype=int))

    D = np.linalg.norm(co[:, None] - co[None], axis=-1)
    A = contact_matrix(co, cutoff=CUT, weight="binary")
    for i in range(N - 1):  # sequence-adjacency connectivity fix-up, matches the drop's own method
        A[i, i + 1] = A[i + 1, i] = 1.0
    nc, _ = connected_components(A)
    deg = A.sum(1)
    Lap = laplacian(A)
    gdist = shortest_path(A, unweighted=True)

    burial, n_missing_sasa = sasa_burial(apo, apo_raw, apo_chains)

    w, V = eigh(Lap)
    nz = w > 1e-8
    Cov = (V[:, nz] / w[nz]) @ V[:, nz].T
    idx10 = np.flatnonzero(nz)[:10]
    Cl = (V[:, idx10] / w[idx10]) @ V[:, idx10].T
    wa, Va = eigh(A)
    Lpi = np.linalg.pinv(Lap)
    vol = float(deg.sum())
    bandwidth = float(w.max() - w.min())
    gamma_lead = 0.1 * bandwidth
    eta_reg = 1e-6 * bandwidth

    # --- seed-blind observables + the per-j perturbed-covariance columns
    # dMSF_at_seed needs, all computed once per target (one eigh(L2) per
    # residue j, not per (j, seed) pair -- an earlier draft nested this
    # inside the seed loop, which for CARDIAC_MYOSIN (N=704, ~20 active-
    # site seeds) meant ~14,000 redundant N x N eigendecompositions instead
    # of 704. `active_idx` columns of the perturbed covariance diagonal are
    # kept (not the full (N,N) `diagP`, per the drop's own memory concern
    # for large real targets), since dMSF_at_seed is only ever queried at
    # a real active-site seed. ---
    base_ld = float(np.sum(np.log(w[nz])))
    dS = np.zeros(N)
    diagP_active = np.zeros((N, len(active_idx)))  # diagP_active[j, s] = perturbed Cov[seed_s, seed_s] when residue j is stiffened
    for j in range(N):
        sh = np.append(np.flatnonzero(A[j]), j)
        Ap = A.copy()
        ix = np.ix_(sh, sh)
        Ap[ix] = Ap[ix] * STIFF
        np.fill_diagonal(Ap, 0.0)
        L2 = laplacian(Ap)
        w2, V2 = eigh(L2)
        n2 = w2 > 1e-8
        dS[j] = -0.5 * (float(np.sum(np.log(w2[n2]))) - base_ld)
        diagP_active[j] = np.einsum("ik,ik->i", V2[active_idx][:, n2] / w2[n2], V2[active_idx][:, n2])
    slow1 = slow1_minima_score(Lap, w, V)

    _log(f"{target_name}: N={N}, comps={nc}, active_site n={len(active_idx)} "
         f"(provenance={provenance!r}), sasa_missing={n_missing_sasa}")

    rows = []
    for s_pos, seed in enumerate(active_idx.tolist()):
        ed = D[seed]
        es = Va[seed]
        sc = {}
        for T in (5.0, 25.0):
            ts = np.linspace(0.1, T, 60)
            p = np.zeros(N)
            for t in ts:
                p += np.abs(Va @ (np.exp(-1j * wa * t) * es)) ** 2
            sc[f"CTQW_adj_T{int(T)}"] = p / len(ts)
        sc["heat_T5"] = V @ (np.exp(-w * 5.0) * V[seed])  # = expm(-Lap*5)[seed], via cached eigenbasis
        sc["MRW_commute"] = -vol * (Lpi[seed, seed] + np.diag(Lpi) - 2 * Lpi[seed])
        sc["GNM_corr_seed"] = Cov[seed] / np.sqrt(np.abs(np.diag(Cov) * Cov[seed, seed]))
        sc["GNM_corr_low10"] = Cl[seed] / np.sqrt(np.abs(np.diag(Cl) * Cl[seed, seed]))
        sc["dMSF_at_seed"] = Cov[seed, seed] - diagP_active[:, s_pos]
        sc["dS_vib_global"] = dS
        sc["slow1_minima"] = slow1

        for k, v in sc.items():
            rows.append(dict(
                target=target_name, seed=int(seed), obs=k, group="per_seed",
                rho_gd=float(spearmanr(v, gdist[seed]).statistic),
                rho_ed=float(spearmanr(v, ed).statistic),
                rho_burial=float(spearmanr(v, burial).statistic),
                partial=pspear(v, ed, burial),
            ))

    # --- full-active-site-set observables, once per target ---
    ed_full = np.linalg.norm(co - co[active_idx].mean(0), axis=1)
    gd_full = gdist[active_idx].min(axis=0)
    full_sc = {
        "prs_low": prs_low(co, active_idx, cutoff=LOWMODE_CUTOFF, k_modes=K_MODES),
        "dcc_low": dcc_low(co, active_idx, cutoff=LOWMODE_CUTOFF, k_modes=K_MODES),
        "chiral_circ": chiral_circulation_score(co, active_idx, cutoff=CUT),
        "transmission_E0": transmission_from_source(
            Lap, active_idx, E=0.0, gamma_lead=gamma_lead, eta_reg=eta_reg
        ),
    }
    for k, v in full_sc.items():
        rows.append(dict(
            target=target_name, seed=None, obs=k, group="full_set",
            rho_gd=float(spearmanr(v, gd_full).statistic),
            rho_ed=float(spearmanr(v, ed_full).statistic),
            rho_burial=float(spearmanr(v, burial).statistic),
            partial=pspear(v, ed_full, burial),
        ))

    meta = dict(name=target_name, N=N, comps=int(nc), active_site=active_idx.tolist(),
                provenance=provenance, n_missing_sasa=n_missing_sasa,
                apo_pdb=target_config["apo_pdb"])
    return rows, meta


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_rows, all_meta = [], []
    for name in TARGETS:
        t0 = time.monotonic()
        rows, meta = compute_target(name)
        all_rows.extend(rows)
        all_meta.append(meta)
        _log(f"{name}: done in {time.monotonic() - t0:.1f}s")

    out_path = OUTPUT_DIR / "real_pdb_confound.json"
    json.dump(dict(meta=all_meta, rows=all_rows), open(out_path, "w"), indent=1)
    _log(f"wrote {out_path}")

    obs = sorted({x["obs"] for x in all_rows})
    n_replicates_per_seed = len({(x["target"], x["seed"]) for x in all_rows if x["group"] == "per_seed"})
    print(f"\nn_per-seed-replicates = {n_replicates_per_seed} across {len(all_meta)} real targets\n")
    print(f"{'observable':18s} {'group':10s} {'|partial rho(ed|burial)|':>26s} {'|rho_ed|':>10s} {'rho_burial':>11s}")
    print("-" * 80)
    for o in obs:
        cell = [x for x in all_rows if x["obs"] == o]
        grp = cell[0]["group"]
        p = np.abs([x["partial"] for x in cell])
        e = np.abs([x["rho_ed"] for x in cell])
        b = np.array([x["rho_burial"] for x in cell])
        if grp == "per_seed":
            print(f"{o:18s} {grp:10s} {p.mean():14.3f} +- {p.std():.3f} [{p.min():.2f},{p.max():.2f}]"
                  f" {e.mean():8.3f} {b.mean():11.3f}  (n={len(cell)})")
        else:
            print(f"{o:18s} {grp:10s} {p.mean():14.3f} {'':>15s}"
                  f" {e.mean():8.3f} {b.mean():11.3f}  (n={len(cell)}, per-target)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
