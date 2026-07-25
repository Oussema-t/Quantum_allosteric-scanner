"""Tail resolution: the repo's strongest claims sit at p<=0.001-0.006 with
Bonferroni bars of 0.0083 / 0.0031. Does the scattered-vs-compact null
mismatch reach that far into the tail, or only inflate near p~0.05?

Also: does the mismatch persist when the observable is NOT smooth
(a sanity check that this is about spatial autocorrelation of the score
field, not an artifact of the test construction)?

Delivered 2026-07-25 via `PANEL_REVIEW_2026-07-25.md` §2.3 (external
reviewer, no repo write access); relocated here from `.ai/reviews/
2026-07-25/` unmodified except for the `sys.path` line below, same fix
as `null_audit.py`. No other line changed.
"""
import sys
from pathlib import Path
import numpy as np

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from allostery.lowmode_predictor import dcc_low
from allostery.metrics import stratified_auc
from allostery.baselines import hop_from_seed
from null_audit import make_globule, compact_patch, scattered_patch, well_powered_max


def main():
    N, POCKET, CUTOFF = 500, 14, 10.0
    N_SCATTER, N_COMPACT = 2000, 500

    coords = make_globule(N, seed=1)
    rng = np.random.default_rng(7)
    c0 = rng.integers(N)
    source = np.argsort(np.linalg.norm(coords - coords[c0], axis=1))[:8]
    shells = -hop_from_seed(coords, source, cutoff=CUTOFF)

    score_smooth = dcc_low(coords, source, cutoff=CUTOFF, k_modes=20)
    score_white = np.random.default_rng(9).normal(size=N)  # spatially uncorrelated control

    for label, score in (("dcc_low (smooth field)", score_smooth),
                         ("white noise (control)", score_white)):
        a = []
        rA = np.random.default_rng(101)
        for _ in range(N_SCATTER):
            lab = np.zeros(N, int); lab[scattered_patch(coords, POCKET, rA)] = 1
            v = well_powered_max(stratified_auc(score, lab, shells))
            if np.isfinite(v): a.append(v)
        a = np.asarray(a)

        b = []
        rB = np.random.default_rng(202)
        for _ in range(N_COMPACT):
            lab = np.zeros(N, int); lab[compact_patch(coords, POCKET, rB)] = 1
            v = well_powered_max(stratified_auc(score, lab, shells))
            if np.isfinite(v): b.append(v)
        b = np.asarray(b)

        # p-value the repo's scattered null assigns to each pure-null compact pocket
        p_assigned = np.array([(a >= x).mean() for x in b])

        print(f"\n=== {label} ===")
        print(f"  scattered null: median={np.median(a):.3f}  "
              f"99th={np.percentile(a,99):.3f}  max={a.max():.3f}  n={len(a)}")
        print(f"  compact   null: median={np.median(b):.3f}  "
              f"99th={np.percentile(b,99):.3f}  max={b.max():.3f}  n={len(b)}")
        for thr in (0.05, 0.0167, 0.0083, 0.0031, 0.001):
            frac = float((p_assigned <= thr).mean())
            print(f"    pure-null COMPACT pockets called p<={thr:<7g}: "
                  f"{frac:.4f}   (nominal {thr:g})  -> inflation x{frac/thr:.1f}")


if __name__ == "__main__":
    main()
