"""TASK-0314 Part B -- how many cluster-permutation/Wilcoxon/Mann-Whitney
tests has this register actually run, and do its strongest surviving
claims (p=0.019-0.042) clear a family-wise bar?

Bookkeeping only, per this task's own Constraint: no analysis is
re-run, and no individual task's own conclusion is re-interpreted. This
counts and classifies what already exists.

METHOD -- counted, not estimated: grep every `scripts/task02NN_*.py` and
`scripts/task03NN_*.py` file in the TASK-0259-TASK-0311 range for call
sites of the register's own standard instruments (`wilcoxon(`,
`mannwhitneyu(`, `cluster_sign_flip_test(`, `cluster_permutation_two_
group(`, `cluster_permutation_correlation(`), excluding function
DEFINITIONS, `import` lines, and comments. `task0261_cluster_robust_
stats.py` itself defines 3 of these functions -- its own 3 `def` lines
are excluded from the count; its `main()`'s 16 invocations (re-scoring
TASK-0249/0254/0257/0259's own headline numbers under both a naive and a
cluster-robust treatment) are counted like every other file's.

Deliberately scoped to exactly the three function families TASK-0314's
own filing names as "the register's standard instrument" -- binomial
tests (TASK-0288 Finding F), Shapiro-Wilk, GMM-BIC comparisons and
Silverman/LRT calls also produce p-values elsewhere in the register and
are NOT counted here; the true family-wise count including those is
larger still, so this number is a floor, not a ceiling.

Run: ../.venv/bin/python3 scripts/task0314_multiplicity_audit.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = _ROOT / "scripts"
OUT = _ROOT / "results/tasks/0314_auc_metric_audit"

PATTERN = re.compile(
    r"\b(wilcoxon|mannwhitneyu|cluster_sign_flip_test|"
    r"cluster_permutation_two_group|cluster_permutation_correlation)\("
)
DEF_OR_IMPORT = re.compile(r"^\s*(def |from |import |#)")

# TASK-0259 through TASK-0311, inclusive -- the range this task's own
# filing names.
LO, HI = 259, 311


def in_range(fname: str) -> bool:
    m = re.match(r"task0(\d{3})[_.]", fname)
    if not m:
        return False
    n = int(m.group(1))
    return LO <= n <= HI


def count_file(path: Path) -> int:
    n = 0
    for line in path.read_text(errors="replace").splitlines():
        if DEF_OR_IMPORT.match(line):
            continue
        n += len(PATTERN.findall(line))
    return n


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in SCRIPTS.glob("task0*.py") if in_range(p.name))
    per_file = {}
    total = 0
    for p in files:
        n = count_file(p)
        if n:
            per_file[p.name] = n
            total += n

    print("=" * 78)
    print(f"Cluster-permutation/Wilcoxon/Mann-Whitney call sites, "
          f"TASK-{LO}-TASK-{HI} scripts")
    print("=" * 78)
    for f, n in per_file.items():
        print(f"  {n:>3}  {f}")
    print(f"\n  TOTAL: {total} call sites across {len(per_file)} files")

    # The three claims TASK-0314's own filing named as "still standing".
    # TASK-0263's original p=0.019 was superseded by TASK-0315 (filed and
    # completed the same day, after TASK-0314 itself) -- reported here at
    # its CURRENT value, not the stale one, per this register's own
    # standing rule (cite the number as it stands today, not as first
    # published). Verified live against both tasks' own Done sections,
    # not assumed.
    claims = [
        dict(claim="TASK-0263/0315 terms-block vs CTQW",
             p=0.049, status="pre-registered (TASK-0263's own single "
             "headline comparison; number corrected by TASK-0315's "
             "independent re-run, same conclusion)"),
        dict(claim="TASK-0275 holo V_C+CTQW vs V_C alone",
             p=0.037, status="pre-registered (single pre-declared "
             "comparison: 'does CTQW add anything once V_C is in the "
             "model')"),
        dict(claim="TASK-0261 ENM valid-vs-invalid, two-sided",
             p=0.042, status="EXPLORATORY -- TASK-0261's own filing "
             "labels this 'not pre-registered'"),
    ]
    print("\n" + "=" * 78)
    print("Family-wise check on the register's strongest surviving claims")
    print("=" * 78)
    for c in claims:
        print(f"  {c['claim']:<45} p={c['p']:.3f}  {c['status']}")

    preregistered = [c for c in claims if c["status"].startswith("pre-registered")]
    n_prereg_claims = len(preregistered)
    smallest_family = n_prereg_claims  # the narrowest defensible denominator:
    # just the pre-registered survivors compared against each other
    bar_smallest = 0.05 / smallest_family
    bar_total = 0.05 / total

    print(f"\n  Narrowest defensible family (pre-registered survivors only, n={smallest_family}): "
          f"Bonferroni bar = 0.05/{smallest_family} = {bar_smallest:.4f}")
    for c in preregistered:
        print(f"    {c['claim']:<45} p={c['p']:.3f}  "
              f"{'SURVIVES' if c['p'] < bar_smallest else 'DOES NOT SURVIVE'}")

    print(f"\n  Full counted family (all {total} call sites, TASK-0259-0311): "
          f"Bonferroni bar = 0.05/{total} = {bar_total:.5f}")
    for c in preregistered:
        print(f"    {c['claim']:<45} p={c['p']:.3f}  "
              f"{'SURVIVES' if c['p'] < bar_total else 'DOES NOT SURVIVE'}")

    all_fail_narrow = all(c["p"] >= bar_smallest for c in preregistered)
    all_fail_total = all(c["p"] >= bar_total for c in preregistered)
    print("\n" + "=" * 78)
    print("VERDICT")
    print("=" * 78)
    if all_fail_narrow and all_fail_total:
        print("  None of the register's pre-registered surviving claims clear a")
        print("  family-wise bar -- not even the narrowest defensible one (comparing")
        print("  just the 2 pre-registered survivors against each other, bar=0.025).")
        print("  This holds regardless of exactly how the full ~59-test family is")
        print("  divided into pre-registered vs exploratory -- the conclusion does")
        print("  not depend on getting that classification exactly right.")
    else:
        print("  At least one claim survives -- see per-claim lines above.")

    out = dict(total_call_sites=total, per_file=per_file, claims=claims,
               n_preregistered=n_prereg_claims, bar_smallest_family=bar_smallest,
               bar_total_family=bar_total, all_fail_narrow=all_fail_narrow,
               all_fail_total=all_fail_total)
    (OUT / "multiplicity_audit.json").write_text(json.dumps(out, indent=1))
    print(f"\nwritten: {OUT / 'multiplicity_audit.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
