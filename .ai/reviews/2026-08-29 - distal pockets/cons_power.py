"""How strong would a conservation filter have had to be for arms 2/3 to see it?

A null is only informative if the test had power. Under H0 the true pocket's
conservation percentile is U(0,1), so Fisher's method over K cluster-collapsed
percentiles is exact-ish. Find the largest uniform percentile p0 that would
still clear alpha=0.05 at each K actually available.
"""
import numpy as np
from scipy.stats import chi2

ALPHA = 0.05


def fisher_p(ps):
    ps = np.clip(np.asarray(ps, float), 1e-12, 1.0)
    return float(chi2.sf(-2 * np.log(ps).sum(), 2 * len(ps)))


print("=" * 78)
print("Minimum detectable conservation effect, by number of clusters")
print("=" * 78)
print("  A 'perfect' negative filter puts the true pocket at percentile p0 in")
print("  every cluster. Largest p0 still reaching p<0.05:\n")
print(f"  {'K':>3}{'max p0':>10}{'= true pocket in top':>24}")
for K in (4, 5, 6, 9, 10, 13):
    lo, hi = 1e-6, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if fisher_p([mid] * K) < ALPHA:
            lo = mid
        else:
            hi = mid
    print(f"  {K:>3}{lo:>10.3f}{f'{lo*100:.0f}% of candidates':>24}")

print()
print("=" * 78)
print("Observed vs detectable")
print("=" * 78)
obs = {
    ("default", "open", 4): 0.401,
    ("default", "cryptic", 5): 0.690,
    ("default", "ALL", 9): 0.467,
    ("-m 2.8", "open", 4): 0.333,
    ("-m 2.8", "cryptic", 6): 0.658,
    ("-m 2.8", "ALL", 10): 0.620,
}
print(f"  {'setting':<10}{'stratum':<9}{'K':>3}{'median pct':>12}"
      f"{'need <=':>10}{'verdict':>26}")
for (s, strat, K), med in obs.items():
    lo, hi = 1e-6, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if fisher_p([mid] * K) < ALPHA:
            lo = mid
        else:
            hi = mid
    v = "detectable" if med <= lo else "far from any signal"
    print(f"  {s:<10}{strat:<9}{K:>3}{med:>12.3f}{lo:>10.3f}{v:>26}")

print()
print("  Note the direction: a negative filter needs LOW percentiles. Cryptic")
print("  medians are 0.66-0.69, i.e. on the wrong side of chance entirely.")
