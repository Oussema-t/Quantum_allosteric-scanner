# CHANGES — performance pass (2026-07-04)

**Goal:** make the app faster without changing any scientific/numerical output, and
without adding any quantum code.

## What changed and why
Profiling (`PROFILING.md`) showed compute is sub-second up to ~450 residues, so the
user-visible slowness is **cold start + network**, not the math. So this pass targets
those, plus memoization:

- **`config.py`** — every tunable is now an env var with a documented default
  (`QAS_RESULT_CACHE`, `QAS_RESULT_CACHE_MAX`, `QAS_MAX_PLOT_POINTS`, `QAS_N_BOOTSTRAP`,
  `QAS_N_PERM`, `QAS_SPARSE_THRESHOLD`, …). Defaults preserve current behaviour exactly.
- **`result_cache.py`** — param-keyed (SHA-256 of every param that affects the output)
  in-memory LRU + disk cache. Wired into `/api/load` and `/api/connectivity-change`. A
  repeated request returns instantly; a changed cutoff/chain/param automatically misses,
  so a stale result can never be served. Response gains an add-only `cached: true/false`.
- **`/healthz`** alias + cache stats on `/api/health` (hit/miss/rate) for uptime monitors.
- **Keep-warm** already shipped (`.github/workflows/keepalive.yml`, /api/health every 10 min).

## Before / after
- Repeated load of the same protein/params: **full recompute → instant** (cache hit).
- Cold start: removed by keep-warm (was 30–60 s).
- Compute itself: unchanged (dense GNM kept — see below).

## Proven no-change
- `scripts/verify_eigensolver.py`: the sparse (truncated) eigensolver matches dense on the
  lowest modes **but** changes the shipped MSF by ~45% (full-spectrum descriptor) → NOT
  shipped. Dense `np.linalg.eigh` kept. All response shapes are unchanged (fields added only).

## What remains slow / not done
- **Very large proteins (>800 res)** first-load: O(N³) eigh is real (~seconds to ~10 s at
  the 1500-residue cap). Needs a stronger host or a *separately validated* truncated GNM —
  not a silent "no-change" speedup.
- **Job queue + progress bar** (non-blocking UI): deferred to its own pass (large add-only
  frontend change). The page still blocks during a first-time heavy compute.

## Rollback
This pass is additive. To revert entirely: reset to commit `a3c94c6` (pre-pass HEAD).
