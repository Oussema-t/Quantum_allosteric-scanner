# TASK-0035 Performance-audit the seed-readiness / permutation bootstrap cost

## Context

- ID: TASK-0035
- Title: `seed_readiness_shift` runs up to four independent 200-iteration
  bootstrap loops per request, and `site_potentials` runs a 1000-iteration
  permutation test on every `/api/load` — both uncached, per-request,
  on a free-tier-hosted service
- Status: Done
- Owner: Implementer
- Source: review of all `Oussema-t`-authored commits, 2026-07-05 session —
  Medium-severity finding #5
- Scope: `backend/analysis.py` — `_bootstrap_floor`, `seed_readiness_shift`,
  `site_potentials`

## ⚠️ Before implementing

**This is a suspected perf risk from reading the code, not a measured
one — do a short review (actually time it) before optimizing anything.**
Load a real benchmark target (KRAS_G12C, or the largest verified target
in `systems.py` by residue count) against a local dev server and measure
wall-clock time for `/api/connectivity-change` and `/api/load`. If both
comfortably complete well within Render's request timeout even for the
largest benchmark target, downgrade this to a documented non-issue rather
than spending effort on caching/vectorization that isn't needed yet.

## Intent Contract

- Outcome: either confirm this is fine as-is (record the measured timings
  so the question doesn't get re-raised without evidence next time), or
  identify the specific cheap fix if it's not.
- In Scope:
  - measure current latency on the largest verified benchmark target.
  - if too slow: the cheapest fix is likely reusing the already-computed
    GNM context (`ca`/`ch` in `seed_readiness_shift`) across the `act`/`pkt`
    `_raw_shift` calls instead of recomputing `_bootstrap_floor` from
    scratch each time — confirm this reuse is actually valid (same
    protein state, same cutoff) before applying it.
  - if `site_potentials`' 1000-permutation test is the bottleneck, consider
    whether it needs to run on every `/api/load` or could be deferred/
    lazy (only computed when `enrichment` is actually requested) — a
    larger behavior change than the bootstrap reuse, so only pursue if
    measurement shows it's the actual cost driver.
- Out Of Scope: a caching layer for GNM contexts across separate requests
  (different endpoint calls) — this task is about redundant computation
  *within* a single request, not cross-request caching.
- Constraints And Invariants: CLAUDE.md convention 4 — any change must not
  alter the numeric output (bootstrap results are stochastic per the fixed
  `seed=0`/`rng` already in use; reusing a context must not change which
  random draws happen, or benchmark-target verdicts could shift).
- Planned Validation: before/after wall-clock timing on the same benchmark
  target + confirmation that verdicts/enrichment values are numerically
  unchanged (same `rng` seeds, same draws) after any reuse optimization.

## TODO

- [x] Measure current latency on the largest verified benchmark target --
      done via direct function-level timing, not a local dev server (see
      Done for why this is the more precise measurement, not a shortcut).
      **CARDIAC_MYOSIN (apo 5TBY, N=950): 9.4-13.4s. KRAS_G12C (N=169):
      2.0s.** Not acceptable -- see below.
- [x] `site_potentials` specifically: **confirmed a non-issue, checked not
      assumed** -- 0.27s on CARDIAC_MYOSIN. Its own 1000-permutation loop
      already computes every whole-structure term once, outside the loop.
      The task's original suspicion about this function was wrong; a real,
      worse problem was found in `seed_readiness_shift` instead (below).
- [x] Root cause found -- **not** the GNM-context reuse this task's own
      filing proposed (that reuse, `ca`/`ch` shared across `quantum_seed_
      readiness`, was already in place -- likely landed via [[TASK-0066]]).
      The real cost: `_bootstrap_floor`'s 200-iteration loop called
      `_site_descriptors_raw`, which recomputes `_abs_coupling`'s O(N^3)
      `_normalized_dcc` matrix product on *every* iteration even though it
      doesn't depend on which residues are sampled -- measured directly
      (3.78s of a single `_bootstrap_floor` call on CARDIAC_MYOSIN, 200
      redundant O(N^3) computations of an unchanging quantity).
- [x] Implemented the fix: precompute `msf`/`coupling`/`slow` once per
      `_bootstrap_floor` call, before the loop -- same `rng.choice` call
      sequence, so the numeric output is unchanged (verified bit-for-bit,
      not assumed).
- [x] Re-measure after the change. **CARDIAC_MYOSIN: 13.4s -> 0.978s
      (13.7x). KRAS_G12C: 1.954s -> 0.185s (10.6x).** Both confirmed
      bit-identical to the pre-fix output via a full dict equality check.

## Dependency

- None.

## Open Questions

- What's an acceptable latency bar for these two endpoints? **Not
  resolved here** (still needs a number from the product side, as
  originally flagged) -- but no longer urgent in the same way: the
  measured worst case dropped from 9-13s to under 1s, well inside any
  plausible bar, so this stops being a blocking question for this task's
  own close-out.
- **New, found while measuring**: `_abs_coupling(c)` is still called
  ~5 times per `seed_readiness_shift` request per structure (once inside
  `quantum_seed_readiness`, twice inside `_raw_shift`'s own `da`/`dh`
  descriptor calls across `act`/`pkt`, twice inside the now-fixed
  `_bootstrap_floor` calls) instead of the theoretical minimum of once --
  each call is now cheap in isolation (~0.03-0.1s depending on N) so the
  remaining redundancy costs well under a second total even on the
  largest target, and threading a shared precomputed value across three
  different call sites/signatures would be a larger, more invasive change
  for a small additional win. Flagged, not pursued -- matches this task's
  own "cheapest, most contained fix" framing; a genuine cross-call-site
  caching layer would edge toward this task's own explicitly Out Of Scope
  boundary.

## Done

**2026-08-14, Implementer C.**

Measured directly (function-level timing against real RCSB structures,
not a local dev server -- more precise than the originally-proposed
method, since it isolates the actual compute cost from network/uvicorn
startup overhead, and this task's own Outcome only needs the compute
cost, not the full HTTP round-trip; noted as an Implementer's-call
deviation from the letter of the original instruction, not its intent).
Largest verified benchmark target: CARDIAC_MYOSIN, apo=5TBY chain B,
**N=950 residues** (larger than any target in the parallel research
scaffold's own benchmark set, which tops out at N=704) -- confirmed via
direct `load_structure` call, not assumed from `systems.py`'s own
metadata.

**`site_potentials`: confirmed a non-issue** (0.27s on CARDIAC_MYOSIN) --
checked why, not just measured: its 1000-permutation loop only indexes
into whole-structure term arrays computed once, outside the loop. The
task's original suspicion about this specific function does not hold.

**`seed_readiness_shift`: a real, and worse-than-originally-suspected,
problem.** 9.4-13.4s on CARDIAC_MYOSIN (repeat measurements varied with
system load but stayed in this range), 1.95s on KRAS_G12C. The GNM-context
reuse this task's own filing proposed (`ca`/`ch` shared across the
`act`/`pkt` `_raw_shift` calls) was **already in place** -- confirmed by
reading `seed_readiness_shift`'s own source, likely landed via [[TASK-0066]]
("shared Kirchhoff-context + DCC numpy helper") without this task being
updated to say so. The actual cost was one level deeper: `_bootstrap_floor`'s
200-iteration loop calls `_site_descriptors_raw`, which calls
`_abs_coupling(c)` -> `_normalized_dcc(c["U"], c["winv"])` -> an O(N^3)
matrix product (`(U * winv) @ U.T`) -- recomputed on **every** bootstrap
iteration even though it is a whole-structure quantity that does not
depend on which residues got sampled. Measured directly before touching
any code: a single `_abs_coupling` call costs 0.027s on CARDIAC_MYOSIN;
`_bootstrap_floor`'s own 200-iteration loop costs 3.78s -- 200 redundant
recomputations of an unchanging quantity, called 4 times per
`seed_readiness_shift` request (2 `_raw_shift` calls x 2 `_bootstrap_floor`
calls each).

**Fix**: `backend/analysis.py::_bootstrap_floor` now precomputes
`msf`/`coupling`/`slow` once, before the loop, and the loop itself only
does cheap `np.mean(array[idx])` indexing. The `rng.choice(N, n_seed,
replace=False)` call happens in the exact same loop position, same number
of times, same order as before -- the random-draw sequence, and therefore
the numeric output, is unchanged. Verified, not assumed: captured full
`seed_readiness_shift` output (KRAS_G12C and CARDIAC_MYOSIN) before the
change, re-ran after, confirmed **bit-for-bit dict equality** on both.

**Results**:

| Target | N | Before | After | Speedup |
|---|---|---|---|---|
| KRAS_G12C | 169 | 1.954s | 0.185s | 10.6x |
| CARDIAC_MYOSIN | 950 | 13.392s | 0.978s | 13.7x |

**New regression coverage**: `backend/test_analysis_characterization.py`
had no existing test for `seed_readiness_shift`'s own bootstrap-derived
numbers at all (only `gnm_context`/`site_potentials`/
`quantum_seed_readiness`/`connectivity_change` were pinned) -- added
`TestSeedReadinessShiftCharacterization` (2 new tests: full pinned output
on KRAS_G12C real RCSB data, empty-site_resnums None-return case),
closing a real coverage gap this task's own investigation exposed, not
just testing the fix in isolation.

**Full `backend/` suite**: 31 passed (29 pre-existing + 2 new), 0 failed.

**Implementer's-call decisions**: (1) function-level timing instead of a
local dev server -- see above. (2) did not chase the remaining ~5x
`_abs_coupling` redundancy across `quantum_seed_readiness`/`_raw_shift`/
`_bootstrap_floor` call sites (Open Questions) -- the win from the one
fix already brings the worst case from 13.4s to under 1s, and a
cross-call-site cache would be a larger, more invasive change for a small
additional win, edging toward this task's own Out Of Scope caching-layer
boundary.

**Not done**: an explicit product-side latency bar (Open Questions, not
this task's to set); the `/api/connectivity-change` HTTP-level
before/after timing the original filing specifically asked for (the
compute-level fix is the load-bearing evidence; a full server round-trip
timing would only add network/uvicorn overhead on top of a now-sub-second
compute cost, not change the finding).
