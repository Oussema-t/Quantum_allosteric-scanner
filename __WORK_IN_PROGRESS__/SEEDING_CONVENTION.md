# Seeding convention (TASK-0333)

Repo-wide convention for this research pipeline (`__WORK_IN_PROGRESS__/`),
so a future script's determinism can be checked by inspection rather than
by re-deriving whether it happens to be reproducible.

## The rule

1. **Every scikit-learn estimator gets an explicit `random_state=`.** Never
   the class default (`None`). A fixed integer is fine — sklearn's own
   `check_random_state` treats an int as "seed a fresh generator with
   this," which is deterministic across processes (unlike passing an
   already-instantiated `numpy.random.RandomState`/`Generator` object into
   a loop that calls `.sample()`/`.fit()` many times — see the pitfall
   below).
2. **Every `numpy` random draw goes through `np.random.default_rng(<seed>)`**,
   never the legacy global `np.random.seed(...)` + bare `np.random.*`
   calls (global state is a well-known source of cross-import ordering
   bugs).
3. **`PYTHONHASHSEED` is set explicitly, not left to the environment.**
   `Dockerfile.pipeline` sets `ENV PYTHONHASHSEED=0`;
   `scripts/run_reproducible_headline.py` sets it explicitly in the
   subprocess environment for the same reason, for anyone running outside
   the container. This matters only for scripts that iterate a bare
   `set`/`dict` keyed by `str` (or another hash-randomized type) without
   an enclosing `sorted()` — checked case-by-case below, not assumed
   universal.
4. **A bootstrap/permutation loop's null must be freshly drawn per
   iteration, not fixed once and reused.** See the pitfall below — this
   is the single most expensive-to-debug violation found in this
   register so far.

## A real pitfall, found and fixed by [[TASK-0319]] — read before writing a bootstrap loop

`task0309_kmeans_extended_cohort.py`'s own `lrt()` originally built its
null-generating model once (`GaussianMixture(k1, ..., random_state=0)`)
and called `.sample()` on it inside a `for` loop expecting each call to
advance the generator. **It does not**: `GaussianMixture.sample()` calls
`sklearn.utils.check_random_state(self.random_state)` fresh on every
invocation, and a plain **int** `random_state` is re-seeded from scratch
every time it is checked — not advanced. Every "different" bootstrap
replicate inside that loop was **bit-identical**. Verified directly:
58/60 null draws at n=26 were the exact same sample. The resulting test
was anti-conservative by more than 10x (68% false-positive rate at
n=26, not 5%) and drove a real wrong headline finding
([[TASK-0316]]'s original "multimodal in every cohort," retracted by
[[TASK-0319]] the next day).

**Fix**: pass an *instance*, not an int —
`random_state=np.random.RandomState(seed)` — which sklearn reuses and
advances across repeated calls on the same object, rather than
re-seeding. If you write a bootstrap/permutation loop that calls
`.sample()`, `.fit()`, or any other randomized method on the **same
fitted object** more than once expecting different draws, this is the
first thing to check.

## Known non-compliant call site, not fixed by this task

`pocketsweep.py:386` seeds its permutation null from `abs(hash(str))`,
with `PYTHONHASHSEED` unset in that code path — a stored p-value from
that script cannot currently be regenerated. **Owned by [[TASK-0328]]**,
not this task (this task owns the requirement/convention above; that
task owns the actual fix). Do not mark this pipeline "fully
seed-compliant" until TASK-0328 lands.

## Verified compliant

`scripts/task0318_input_space_ceiling.py`'s `HistGradientBoostingClassifier`
(`random_state=0`) and its own `cluster_sign_flip_test_generic`
(`np.random.default_rng(seed)`, `seed=0` default) — reproduced
byte-for-byte in a clean venv, see `REPRODUCIBILITY.md`.
