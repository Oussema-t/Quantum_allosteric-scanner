# TASK-0035 Performance-audit the seed-readiness / permutation bootstrap cost

## Context

- ID: TASK-0035
- Title: `seed_readiness_shift` runs up to four independent 200-iteration
  bootstrap loops per request, and `site_potentials` runs a 1000-iteration
  permutation test on every `/api/load` — both uncached, per-request,
  on a free-tier-hosted service
- Status: TODO
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

- [ ] Measure current latency on the largest verified benchmark target
      (local dev server, not production, to avoid cold-start noise).
- [ ] If acceptable: record the measurement here and close as "confirmed
      non-issue," no code change.
- [ ] If not acceptable: implement GNM-context reuse in
      `seed_readiness_shift` first (cheapest, most contained fix).
- [ ] Re-measure after any change.

## Dependency

- None.

## Open Questions

- What's an acceptable latency bar for these two endpoints, given Render
  free-tier's own cold-start behavior is already a known, separately
  mitigated concern (`eb15785`'s keep-warm ping)? Worth a number from
  whoever owns the product side, rather than an assumed threshold.

## Done

(not yet)
