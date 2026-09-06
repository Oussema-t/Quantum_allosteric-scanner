"""Audit: is the project's permutation null (uniform scattered same-size
subset) valid for a *spatially compact* pocket label?

Every null in this repo -- TASK-0123's stratified-AUC null, TASK-0133's
"random-patch" control, TASK-0142's void null, TASK-0149/0151's lowmode
null -- draws `rng.choice(N, size=pocket_size, replace=False)`: a
uniformly SCATTERED subset. Real pockets are spatially CONTIGUOUS.
TASK-0143 independently discovered real pockets are far more compact than
random same-size subsets, but that finding was never propagated to the
other nulls.

If the scored observable is a smooth spatial field, a contiguous patch has
correlated scores and therefore a systematically more extreme rank
statistic than a scattered set of the same size. That would make every
p-value in this project anti-conservative.

Test on a protein-like globule with the project's own dcc_low observable
and its own stratified_auc / well-powered-max machinery.

Delivered 2026-07-25 via `PANEL_REVIEW_2026-07-25.md` §2.3 (external
reviewer, no repo write access); relocated here from `.ai/reviews/
2026-07-25/` unmodified except for the `sys.path` line below, which
hardcoded the reviewer's own sandbox path -- replaced with this repo's
standard relative convention (see `learnability_gate_patch_control.py`)
so the script actually runs here. No other line changed.

Citation added later (2026-09-06), not part of the original drop above --
the general principle this file's `compact_patch()` implements (a null
for spatially/serially correlated data must draw contiguous blocks, not
i.i.d. points, or it understates the true null variance) is Kunsch 1989
(Ann Stat 17:1217-1241, doi:10.1214/aos/1176347265) and, in the
cluster-permutation-testing form, Maris & Oostenveld 2007 (J Neurosci
Methods 164:177-190, doi:10.1016/j.jneumeth.2007.03.024) -- see
`documentation/REFERENCES.md`. Cited as the source of the general method
this file already applies, not the source of any number in it (this
project's own citation protocol) -- reused again in [[TASK-0328]]'s
pocket-block null.
"""
import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from allostery.lowmode_predictor import dcc_low, prs_low
from allostery.metrics import stratified_auc
from allostery.baselines import hop_from_seed


def make_globule(n=500, seed=0):
    """Self-avoiding-ish compact chain: a protein-like Ca point cloud."""
    rng = np.random.default_rng(seed)
    pts = [np.zeros(3)]
    for _ in range(n - 1):
        for _try in range(200):
            step = rng.normal(size=3)
            step /= np.linalg.norm(step)
            cand = pts[-1] + 3.8 * step
            # confine to a globule of radius ~ n^(1/3)*2.2 A
            if np.linalg.norm(cand) < 2.2 * n ** (1 / 3) * 1.6:
                d = np.linalg.norm(np.asarray(pts) - cand, axis=1)
                if d.min() > 3.2:
                    break
        pts.append(cand)
    return np.asarray(pts)


def compact_patch(coords, size, rng):
    """Spatially contiguous same-size label: a real pocket's geometry."""
    c = rng.integers(len(coords))
    d = np.linalg.norm(coords - coords[c], axis=1)
    return np.argsort(d)[:size]


def scattered_patch(coords, size, rng):
    """What every null in the repo actually draws."""
    return rng.choice(len(coords), size=size, replace=False)


def well_powered_max(strat, min_pos=3):
    cand = {s: v for s, v in strat.items() if v["n_pos"] >= min_pos and np.isfinite(v["auc"])}
    if not cand:
        return np.nan
    return max(cand[s]["auc"] for s in cand)


def main():
    N = 500
    POCKET = 14          # comparable to real pocket sizes (7-18 in the repo)
    NREP = 400
    CUTOFF = 10.0

    coords = make_globule(N, seed=1)
    rng = np.random.default_rng(7)

    # seed = a compact "active site" of 8 residues, as in the real pipeline
    c0 = rng.integers(N)
    source = np.argsort(np.linalg.norm(coords - coords[c0], axis=1))[:8]

    shells = -hop_from_seed(coords, source, cutoff=CUTOFF)

    print(f"N={N} pocket={POCKET} seed_size={len(source)} "
          f"n_shells={len(np.unique(shells))}")

    for obs_name, obs in (("dcc_low", dcc_low), ("prs_low", prs_low)):
        score = obs(coords, source, cutoff=CUTOFF, k_modes=20)

        # Null A: scattered (the convention actually used in the repo)
        a = []
        rA = np.random.default_rng(101)
        for _ in range(NREP):
            lab = np.zeros(N, int)
            lab[scattered_patch(coords, POCKET, rA)] = 1
            v = well_powered_max(stratified_auc(score, lab, shells))
            if np.isfinite(v):
                a.append(v)

        # Null B: spatially compact (what a real pocket actually looks like)
        b = []
        rB = np.random.default_rng(202)
        for _ in range(NREP):
            lab = np.zeros(N, int)
            lab[compact_patch(coords, POCKET, rB)] = 1
            v = well_powered_max(stratified_auc(score, lab, shells))
            if np.isfinite(v):
                b.append(v)

        a, b = np.asarray(a), np.asarray(b)
        # The key number: where does a TYPICAL compact null pocket sit
        # against the SCATTERED null the repo would compare it to?
        p_of_median_compact = float((a >= np.median(b)).mean())
        frac_compact_sig = float((np.array([(a >= x).mean() for x in b]) < 0.05).mean())

        print(f"\n--- {obs_name} ---")
        print(f"  scattered null (used in repo): median={np.median(a):.3f} "
              f"95th={np.percentile(a,95):.3f} n={len(a)}")
        print(f"  compact null (realistic):      median={np.median(b):.3f} "
              f"95th={np.percentile(b,95):.3f} n={len(b)}")
        print(f"  p-value the repo would assign to a MEDIAN pure-null compact pocket: "
              f"{p_of_median_compact:.3f}")
        print(f"  fraction of pure-null COMPACT pockets the repo's null calls "
              f"p<0.05: {frac_compact_sig:.3f}   (nominal = 0.05)")


if __name__ == "__main__":
    main()
