"""TASK-0284, Finding A + Finding B -- reproduce, as committed code, the two
findings the Reviewer filed from a transient probe: (A) the near/far
allosteric-site-distance split is a real bimodality in the data (1D k-means,
silhouette, the raw gap, Shapiro on log(min_A)), not an artefact of
[[TASK-0258]]'s own stated bin edges; (B) eight standard structural
descriptors (size, shape, secondary structure, global stiffness, fold
topology, packing) are all silent against it.

Reuses, does not re-derive: `task0258_allosteric_distance_taxonomy`'s own
`min_A` per target (re-run fresh here against live `config/*.yaml`, not the
possibly-stale stored artifact -- see `_ensure_taxonomy` below);
`task0242_two_stage_dryrun.prep` for the apo Cα trace, active-site seed and
config per target; `allostery.potentials.gnm_context` for the GNM
Kirchhoff eigendecomposition (lambda_1, degree, contact matrix) instead of
rebuilding a fourth independent one (TASK-0040's own shared-context
rationale, reused verbatim).

SECONDARY STRUCTURE, disclosed: no DSSP binary and no biotite (P-SEA) are
available in this environment (checked directly -- `mkdssp`/`dssp` not on
PATH, `pip install biotite` fails to build against this venv's numpy/
python3.13; a plain `pip install biotite` hung resolving dependencies and
was killed rather than left to run indefinitely). Helix/sheet fraction is
instead a coarse per-residue Ramachandran-region classifier on ProDy's own
`calcPhi`/`calcPsi` (single-residue regions, no i,i+4 hydrogen-bond check --
noisier than DSSP, expected to UNDER-separate helix from loop at ends of
helices). This is a null result in the source filing already; the purpose
here is an independent, reproducible number of the same rough kind, not a
publication-grade SS assignment -- stated plainly, not hidden.

CONTACT ORDER: Plaxco/Simons/Baker 1998's own definition, CO = (1 / (N *
n_contacts)) * sum_{contacts i<j, same chain} |resnum_i - resnum_j|,
restricted to same-chain contacts (a cross-chain "sequence separation" is
not meaningful) using each target's actual apo Cα contact graph
(`enm_cutoff` per target, matching every other GNM quantity in this
register rather than an independent cutoff choice).
"""
from __future__ import annotations
import json, sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import prody
prody.confProDy(verbosity="none")

# Import-order discipline (TASK-0273/0276/0258's own established fix): the
# altloc="all" prody.parsePDB patch must be composed BEFORE allostery's own
# folder-defaulting patch runs, or the folder default is silently dropped.
from task0255_hop_angstrom_calibration import min_heavy_atom_dist_to_seed  # noqa: F401
from task0242_two_stage_dryrun import prep, CAND
from task0258_allosteric_distance_taxonomy import measure as t0258_measure, MANDATORY
from allostery.potentials import gnm_context

FROZEN = _ROOT / "config" / "candidate_targets_task0243.yaml"
OUT = _ROOT / "results/tasks/0284_two_populations"
BONFERRONI_ALPHA = 0.05 / 8


def _load_targets():
    import yaml
    targets = list(CAND)
    if FROZEN.exists():
        fz = yaml.safe_load(FROZEN.read_text()).get("targets") or {}
        CAND.update(fz)
        targets = list(fz) + [t for t in targets if t not in fz]
    targets = targets + [t for t in MANDATORY if t not in targets]
    return targets


def _ss_fractions(pdb_id: str, chains: list, keep: set) -> dict:
    """Coarse Ramachandran-region helix/sheet fraction -- see module
    docstring for why (no DSSP/biotite available)."""
    st = prody.parsePDB(pdb_id, compressed=False)
    hv = st.getHierView()
    n_h = n_s = n_tot = 0
    for c in chains:
        try:
            ch = hv[c]
        except Exception:
            ch = None
        if ch is None:
            continue
        for res in ch.iterResidues():
            if (c, res.getResnum()) not in keep:
                continue
            try:
                phi = float(prody.calcPhi(res))
                psi = float(prody.calcPsi(res))
            except Exception:
                continue
            n_tot += 1
            if -100 <= phi <= -30 and -67 <= psi <= -7:
                n_h += 1
            elif -180 <= phi <= -45 and (psi >= 90 or psi <= -150):
                n_s += 1
    if n_tot == 0:
        return dict(helix_fraction=float("nan"), sheet_fraction=float("nan"), ss_coverage=0.0)
    return dict(helix_fraction=n_h / n_tot, sheet_fraction=n_s / n_tot,
                ss_coverage=n_tot / max(len(keep), 1))


def _contact_order(A: np.ndarray, resnums: np.ndarray, chain_ids: np.ndarray) -> float:
    n = len(resnums)
    iu, ju = np.triu_indices(n, k=1)
    contact = A[iu, ju] > 0
    same_chain = chain_ids[iu] == chain_ids[ju]
    m = contact & same_chain
    if not m.any():
        return float("nan")
    sep = np.abs(resnums[iu][m].astype(float) - resnums[ju][m].astype(float))
    return float(sep.sum() / (n * m.sum()))


def descriptors_for(t: str) -> dict:
    cfg, apo, seed, pocket = prep(t)
    coords = np.asarray(apo.coords)
    resnums = np.asarray(apo.resnums)
    chain_ids = np.asarray(apo.chain_ids)
    n = len(coords)
    cen = coords.mean(axis=0)
    rg = float(np.sqrt(np.mean(np.sum((coords - cen) ** 2, axis=1))))
    compactness = rg / (n ** (1.0 / 3.0))

    cut = float(cfg.get("enm_cutoff", 8.0))
    ctx = gnm_context(coords, cut)
    w = ctx["w"]
    nz = w > 1e-9
    lam1 = float(w[nz].min()) if nz.any() else float("nan")
    mean_degree = float(ctx["degree"].mean())
    co = _contact_order(ctx["A"], resnums, chain_ids)

    # use chains actually present in the parsed apo structure, not cfg's
    # declared apo_chains -- DHPS_GC7 found live to declare a chain ('B')
    # absent from 1RLZ as deposited, crashing ProDy's HierView lookup
    present_chains = sorted(set(chain_ids.tolist()))
    keep = set(zip(chain_ids.tolist(), resnums.tolist()))
    ss = _ss_fractions(cfg["apo_pdb"], present_chains, keep)

    return dict(target=t, N=n, Rg=rg, compactness=compactness,
                gnm_lambda1=lam1, contact_order=co, mean_degree=mean_degree,
                **ss)


def main():
    from scipy.stats import spearmanr, mannwhitneyu, shapiro
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    targets = _load_targets()
    OUT.mkdir(parents=True, exist_ok=True)

    rows = []
    for t in targets:
        try:
            m = t0258_measure(t)
            if "error" in m:
                rows.append(m)
                continue
            d = descriptors_for(t)
            m.update(d)
            rows.append(m)
        except Exception as e:
            rows.append({"target": t, "error": f"{type(e).__name__}: {e}"})

    ok = [r for r in rows if "error" not in r]
    print(f"n={len(ok)} scoreable ({len(rows) - len(ok)} unusable)\n")

    # ---------------- Finding A: bimodality ----------------
    min_a = np.array([r["min_A"] for r in ok])
    names = [r["target"] for r in ok]
    km = KMeans(n_clusters=2, n_init=10, random_state=0).fit(min_a.reshape(-1, 1))
    labels = km.labels_
    means = [min_a[labels == k].mean() for k in (0, 1)]
    near_k = int(np.argmin(means))
    near_mask = labels == near_k
    far_mask = ~near_mask
    sil = silhouette_score(min_a.reshape(-1, 1), labels)
    near_vals = np.sort(min_a[near_mask]); far_vals = np.sort(min_a[far_mask])
    gap = float(far_vals[0] - near_vals[-1])
    sh_stat, sh_p = shapiro(np.log(min_a))

    print("### Finding A: 1D k-means (k=2) on min_A ###")
    print(f"  silhouette = {sil:.3f}")
    print(f"  near: n={near_mask.sum()}  range {near_vals[0]:.2f}-{near_vals[-1]:.2f} A")
    print(f"  far:  n={far_mask.sum()}  range {far_vals[0]:.2f}-{far_vals[-1]:.2f} A")
    print(f"  gap = {gap:.2f} A  (between {near_vals[-1]:.2f} and {far_vals[0]:.2f})")
    print(f"  Shapiro on log(min_A): stat={sh_stat:.4f}  p={sh_p:.4f}")

    # data-derived near/far, and TASK-0258's own bin-derived near/far
    # (min_A >= 12.0 -> intermediate/remote), reported side by side per
    # this task's own explicit instruction to state both.
    bin_far_mask = min_a >= 12.0
    print(f"\n  cf. TASK-0258's own bin edges (min_A>=12.0 -> far): "
          f"n_far={bin_far_mask.sum()}, n_near={(~bin_far_mask).sum()}")

    # ---------------- Finding B: eight descriptors ----------------
    props = ["N", "Rg", "compactness", "helix_fraction", "sheet_fraction",
              "gnm_lambda1", "contact_order", "mean_degree"]
    print("\n### Finding B: eight descriptors vs min_A (Spearman) and near-vs-far (Mann-Whitney) ###")
    print(f"  Bonferroni alpha (0.05/8) = {BONFERRONI_ALPHA:.5f}\n")
    stats_out = {}
    for p in props:
        vals = np.array([r[p] for r in ok], dtype=float)
        finite = np.isfinite(vals)
        rho, p_sp = spearmanr(min_a[finite], vals[finite])
        # data-derived split
        try:
            u_stat, p_mw = mannwhitneyu(vals[finite & near_mask], vals[finite & far_mask])
        except Exception:
            u_stat, p_mw = float("nan"), float("nan")
        # TASK-0258 bin-derived split
        try:
            _, p_mw_bin = mannwhitneyu(vals[finite & ~bin_far_mask], vals[finite & bin_far_mask])
        except Exception:
            p_mw_bin = float("nan")
        sig = "*" if p_sp < BONFERRONI_ALPHA else " "
        print(f"  {p:<16} rho={rho:+.3f}  p_spearman={p_sp:.4f}{sig}  "
              f"p_MW(data-split)={p_mw:.4f}  p_MW(bin-split)={p_mw_bin:.4f}  n={finite.sum()}")
        stats_out[p] = dict(rho=float(rho), p_spearman=float(p_sp),
                             p_mw_data_split=float(p_mw), p_mw_bin_split=float(p_mw_bin),
                             n=int(finite.sum()))

    survives = [p for p in props if stats_out[p]["p_spearman"] < BONFERRONI_ALPHA]
    print(f"\n  survives Bonferroni: {survives if survives else 'NONE'}")

    result = dict(
        n_scoreable=len(ok), n_unusable=len(rows) - len(ok),
        finding_a=dict(silhouette=float(sil), n_near=int(near_mask.sum()),
                        n_far=int(far_mask.sum()),
                        near_range=[float(near_vals[0]), float(near_vals[-1])],
                        far_range=[float(far_vals[0]), float(far_vals[-1])],
                        gap_A=gap, shapiro_stat=float(sh_stat), shapiro_p=float(sh_p),
                        bin_derived_n_far=int(bin_far_mask.sum())),
        finding_b=stats_out,
        rows=rows,
        near_targets=[names[i] for i in range(len(names)) if near_mask[i]],
        far_targets=[names[i] for i in range(len(names)) if far_mask[i]],
    )
    (OUT / "bimodality_and_nulls.json").write_text(json.dumps(result, indent=1))
    print(f"\n  written: {OUT / 'bimodality_and_nulls.json'}")


if __name__ == "__main__":
    raise SystemExit(main())
