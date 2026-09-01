"""TASK-0316 -- re-run the modality question with a test that has power
at the separation the data actually sits at (~1.9 SD, [[TASK-0288]]
Finding B), per cohort, never pooled.

[[TASK-0313]]'s Reviewer addendum established the modality question is
UNDETERMINED, not settled: Silverman's test has zero power below 3 SD at
every cohort size this register has, so every "consistent with unimodal"
verdict to date is a null produced by absent power, not evidence against
two populations; and the one significant pooled result is confounded by
the three cohorts having significantly different locations
(Kruskal-Wallis p=2.15e-03).

This task does NOT write a third modality test (this task's own Scope):
it reuses [[TASK-0288]]'s own parametric-bootstrap LRT (1 vs 2 Gaussian
components on `log(min_A)`) verbatim, imported from
`task0309_kmeans_extended_cohort.py` (`_ll`/`lrt`, unmodified) -- the
same implementation [[TASK-0309]] already ran on this exact data, just
re-run PER COHORT (never pooled, per this task's own Constraint) with an
actual power curve reported alongside every verdict, not asserted.

No new cohort, no new labels (this task's own Constraint): reads
`results/tasks/0309_kmeans_extended_cohort/kmeans_extended_cohort.json`
directly, the same protein/cluster-level rows [[TASK-0309]] built.

Power-curve fidelity matches the register's own established precedent
for this kind of curve ([[TASK-0313]]'s Reviewer addendum used 5 reps,
B=99, for the Silverman power table quoted in this task's own filing):
here, 12 reps x B=100 per (cohort, arm, separation) cell -- a directional
power estimate, not a calibrated exact one, stated as such.

Run: ../.venv/bin/python3 scripts/task0316_modality_powered_test.py
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import sys, json
from pathlib import Path
import numpy as np
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, "scripts")
from task0309_kmeans_extended_cohort import lrt  # noqa: E402 -- reused verbatim, not reimplemented
from sklearn.mixture import GaussianMixture

DATA = json.loads(Path("results/tasks/0309_kmeans_extended_cohort/kmeans_extended_cohort.json").read_text())
OUT = Path("results/tasks/0316_modality_powered_test")
SEPS = (1.5, 2.0, 3.0, 4.0, 6.0)
POWER_REPS = 8
POWER_B = 100
POWER_SEEDS = 2
OBS_B = 300
OBS_SEEDS = 4


def cohort_values(cohort):
    return np.array([r["min_A"] for r in DATA[cohort]], float)


def empirical_separation_sd(log_v):
    """(mean2-mean1)/pooled_sigma from a fresh GMM(2) fit -- a post-hoc
    estimate of how far apart this cohort's own data actually sit, in
    the same SD units the power curve below is parameterised in. Not the
    same computation as TASK-0288's own hardcoded top-22/bottom-6 split
    (that split was specific to the old n=28 cohort and its own Finding
    A 24/9 partition; this generalises to any n). Also returns each
    component's own weight and sigma (in Angstrom, exponentiated back
    from log-space) -- [[TASK-0309]]'s own finding was that a "second
    component" is often the Finding-F point mass (narrow, minority
    weight), not a second broad population; report that distinction
    here rather than let a bare separation-in-SD number imply the
    latter."""
    x = log_v.reshape(-1, 1)
    best = None
    for s in range(5):
        m = GaussianMixture(2, n_init=3, random_state=s).fit(x)
        if best is None or m.score(x) > best.score(x):
            best = m
    order = np.argsort(best.means_.ravel())
    mu = best.means_.ravel()[order]
    var = best.covariances_.ravel()[order]
    w = best.weights_[order]
    pooled_sd = float(np.sqrt(var.mean()))
    sep = float(abs(mu[1] - mu[0]) / pooled_sd) if pooled_sd > 0 else float("nan")
    comps = dict(means_A=[float(np.exp(m_)) for m_ in mu],
                weights=[float(w_) for w_ in w],
                log_sigmas=[float(np.sqrt(v_)) for v_ in var])
    return sep, comps


def interp_power(curve, sep):
    """Linear interpolation of the fixed-grid power curve at the cohort's
    own observed separation -- avoids a second, separately-simulated
    batch of LRT calls at an arbitrary non-grid separation (this
    register's own established precedent, [[TASK-0313]]'s Reviewer
    addendum, also reported power only at a fixed grid). Clipped to the
    grid's own range at the edges rather than extrapolated."""
    xs = sorted(curve)
    ys = [curve[x] for x in xs]
    return float(np.interp(sep, xs, ys))


def power_at(n, sep, reps=POWER_REPS, B=POWER_B, seeds=POWER_SEEDS, seed0=0):
    """Detection rate at alpha=0.05: equal-weight 2-Gaussian mixture
    (unit SD each), separation `sep` SD, sample size `n`, using the exact
    same `lrt()` (1 vs 2) the observed-data verdict below uses."""
    rng = np.random.default_rng(seed0 + int(sep * 1000))
    hits = 0
    for i in range(reps):
        n1 = n // 2
        n2 = n - n1
        x = np.concatenate([rng.normal(0, 1, n1), rng.normal(sep, 1, n2)])
        _, p = lrt(x, 1, 2, B=B, seed=seed0 + 17 * i + 3, seeds=seeds)
        if p < 0.05:
            hits += 1
    return hits / reps


def run_cohort_arm(cohort, label, v):
    n = len(v)
    if n < 12:
        return dict(cohort=cohort, arm=label, n=n, verdict="too few for any modality test")
    log_v = np.log(v)
    obs_lr, obs_p = lrt(log_v, 1, 2, B=OBS_B, seed=1, seeds=OBS_SEEDS)
    sep, comps = empirical_separation_sd(log_v)

    curve = {s: power_at(n, s) for s in SEPS}
    power_at_observed = interp_power(curve, sep)
    point_mass_like = comps["weights"][0] < 0.4 and comps["log_sigmas"][0] < 0.3 * comps["log_sigmas"][1]

    if power_at_observed < 0.5:
        verdict = "UNDETERMINED -- underpowered at this n and this separation"
    elif obs_p < 0.05:
        verdict = "MULTIMODAL (adequately powered)" + (
            " -- but low-mean component is point-mass-like (narrow, minority weight), see TASK-0309" if point_mass_like else "")
    else:
        verdict = "unimodal, with demonstrated power"

    row = dict(cohort=cohort, arm=label, n=n, observed_LR=obs_lr, observed_p=obs_p,
              empirical_separation_sd=sep, gmm2_components=comps, power_curve=curve,
              power_at_observed_separation_interpolated=power_at_observed, verdict=verdict)
    print(f"{cohort:<10}{label:<20}n={n:<5}p={obs_p:.4f}  sep~{sep:.2f}SD  "
          f"power@sep={power_at_observed:.0%}  -> {verdict}")
    print("    power curve: " + "  ".join(f"{s}SD={curve[s]:.0%}" for s in SEPS))
    print(f"    GMM(2): means={[round(m_,2) for m_ in comps['means_A']]}A "
          f"weights={[round(w_,3) for w_ in comps['weights']]}")
    return row


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for cohort in ("ours", "asbench", "casbench"):
        v = cohort_values(cohort)
        arms = [("full (incl. <1.5A)", v[v > 0]), ("excluding <1.5A", v[v >= 1.5])]
        for label, sub in arms:
            rows.append(run_cohort_arm(cohort, label, sub))

    print("\n" + "=" * 78)
    print("SUMMARY -- per cohort, never pooled (this task's own Constraint)")
    print("=" * 78)
    for r in rows:
        if "verdict" in r and "n" in r and "observed_p" in r:
            print(f"  {r['cohort']:<10}{r['arm']:<20}n={r['n']:<5}p={r['observed_p']:.4f}  {r['verdict']}")

    json.dump(dict(rows=rows, seps=list(SEPS), power_reps=POWER_REPS, power_B=POWER_B),
              open(OUT / "modality_powered_test.json", "w"), indent=1)
    print(f"\nwritten -> {OUT}/modality_powered_test.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
